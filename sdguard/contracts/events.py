"""Agent event and guard decision format (owner: Deniz).

An adapter turns one hook call of an agent (Claude Code, Antigravity CLI) into an ``Event``.
The guard engine answers with a ``Decision``, and the adapter turns that back into the
agent's own hook output. Every call is logged as one ``HookLogEntry`` line.

Design rules encoded here (docs/plan/01_MIMARI.md §1, findings of the G0 spikes):
- There is no "allow" decision. "No opinion" is ``noop`` and leaves the call to the
  agent's own permission rules. An explicit allow skips them in Antigravity (G0 01H).
- Each event kind only accepts the actions the agents can carry out for it.
- Every decision other than ``noop`` names at least one finding, and a finding that comes
  from a compiled rule names its ``rule_id``.
- Findings carry no free text taken from the code. The message to the agent is built from
  a fixed template (rule id, file, line), so code cannot speak to the agent (R21).
"""

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import AfterValidator, AwareDatetime, Field, JsonValue, model_validator

from sdguard.contracts.rules import (
    AgentName,
    CweId,
    RelativePath,
    RuleId,
    Sha256,
    _Model,
)

SCHEMA_VERSION: Literal["0.1"] = "0.1"


def _absolute(path: str) -> str:
    """Accept only absolute POSIX paths: agents and the experiment run on Linux."""
    if not PurePosixPath(path).is_absolute():
        raise ValueError("path must be absolute")
    return path


AbsolutePath = Annotated[str, Field(min_length=1), AfterValidator(_absolute)]


class EventKind(StrEnum):
    SESSION_START = "session_start"  # before the first turn's first tool call
    PRE_TOOL = "pre_tool"  # before a tool call runs
    POST_TOOL = "post_tool"  # after a tool call ran
    TURN_END = "turn_end"  # the agent wants to finish the turn


class ToolKind(StrEnum):
    """What a tool call does, independent of the agent's tool name.

    The adapter maps tool names to kinds. Seen in the G0 spikes: Claude Code ``Read`` is
    ``read`` and ``Bash`` is ``command``; Antigravity ``read_file`` is ``read``,
    ``write_file`` and ``edit_file`` are ``write``, ``run_command`` is ``command``.
    """

    READ = "read"
    WRITE = "write"
    COMMAND = "command"
    URL = "url"
    MCP = "mcp"
    OTHER = "other"  # unknown tool; the engine must not assume it is harmless


class ToolCall(_Model):
    name: str = Field(min_length=1)  # the agent's own name: "Bash", "edit_file"
    kind: ToolKind
    paths: list[AbsolutePath] = Field(default_factory=list)  # files the arguments name
    command: str | None = None
    args: dict[str, JsonValue] = Field(default_factory=dict)  # as the agent sent them

    @model_validator(mode="after")
    def _command_only_for_commands(self) -> Self:
        if (self.kind is ToolKind.COMMAND) != (self.command is not None):
            raise ValueError("command is required for kind 'command' and only for it")
        return self


class Event(_Model):
    """One hook call, normalized.

    Hooks do not send a turn number, and Antigravity has no session start hook. The adapter
    keeps ``turn_idx`` and ``stop_attempt`` in its own session state and emits
    ``session_start`` itself when it sees a session for the first time.
    """

    schema_version: Literal["0.1"] = SCHEMA_VERSION
    agent: AgentName
    session_id: str = Field(min_length=1)
    turn_idx: int = Field(ge=1)
    kind: EventKind
    cwd: AbsolutePath  # workspace root
    tool: ToolCall | None = None
    changed_files: list[RelativePath] = Field(default_factory=list)  # relative to cwd
    stop_attempt: int = Field(default=0, ge=0)  # earlier turn_end events in this turn

    @model_validator(mode="after")
    def _fields_match_kind(self) -> Self:
        has_tool = self.kind in (EventKind.PRE_TOOL, EventKind.POST_TOOL)
        if has_tool != (self.tool is not None):
            raise ValueError("tool is required for pre_tool and post_tool and only for them")
        if self.kind in (EventKind.SESSION_START, EventKind.PRE_TOOL) and self.changed_files:
            raise ValueError(f"{self.kind} cannot have changed files")
        if self.kind is not EventKind.TURN_END and self.stop_attempt:
            raise ValueError("stop_attempt is only counted for turn_end")
        return self


class FindingKind(StrEnum):
    FORBIDDEN_ACTION = "forbidden_action"  # a tool call an action rule forbids
    RULE_VIOLATION = "rule_violation"  # code that breaks a compiled code or behavior rule
    PROTECTION_LOST = "protection_lost"  # the ledger saw a protection drop below its best
    NEW_SAST = "new_sast"  # a default Semgrep finding that no compiled rule covers


class FindingSource(StrEnum):
    GUARD = "guard"  # the engine's own check on a tool call
    SEMGREP = "semgrep"
    PYTEST = "pytest"
    LEDGER = "ledger"


class Finding(_Model):
    kind: FindingKind
    source: FindingSource
    rule_id: RuleId | None = None
    invariant: str | None = Field(default=None, min_length=1)  # ledger key: "auth GET /admin"
    cwe: list[CweId] = Field(default_factory=list)
    file: RelativePath | None = None
    line: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _check_links(self) -> Self:
        from_rule = self.kind in (FindingKind.FORBIDDEN_ACTION, FindingKind.RULE_VIOLATION)
        if from_rule != (self.rule_id is not None):
            raise ValueError("rule_id is required for rule findings and only for them")
        if (self.kind is FindingKind.PROTECTION_LOST) != (self.invariant is not None):
            raise ValueError("invariant is required for protection_lost and only for it")
        if self.line is not None and self.file is None:
            raise ValueError("a line needs a file")
        return self


class DecisionAction(StrEnum):
    NOOP = "noop"  # no opinion: the agent's own permission rules decide
    DENY = "deny"  # do not run the tool call
    FEEDBACK = "feedback"  # tell the agent, let it continue
    BLOCK_STOP = "block_stop"  # do not let the agent finish the turn


# Antigravity has no feedback channel after a tool call (G0 02P); its adapter queues
# post_tool feedback and delivers it with PostInvocation or Stop.
ALLOWED_ACTIONS: dict[EventKind, frozenset[DecisionAction]] = {
    EventKind.SESSION_START: frozenset({DecisionAction.NOOP, DecisionAction.FEEDBACK}),
    EventKind.PRE_TOOL: frozenset({DecisionAction.NOOP, DecisionAction.DENY}),
    EventKind.POST_TOOL: frozenset({DecisionAction.NOOP, DecisionAction.FEEDBACK}),
    EventKind.TURN_END: frozenset(
        {DecisionAction.NOOP, DecisionAction.FEEDBACK, DecisionAction.BLOCK_STOP}
    ),
}


class Decision(_Model):
    action: DecisionAction
    findings: list[Finding] = Field(default_factory=list)
    agent_message: str | None = Field(default=None, min_length=1)
    ruleset_sha256: Sha256 | None = None  # rule set in force; None when there is none (K0-K2)
    elapsed_ms: float = Field(ge=0)

    @model_validator(mode="after")
    def _check_action(self) -> Self:
        if self.action is DecisionAction.NOOP:
            if self.agent_message is not None:
                raise ValueError("noop sends no message to the agent")
        else:
            if not self.findings:
                raise ValueError(f"a '{self.action}' decision must name at least one finding")
            if self.agent_message is None:
                raise ValueError(f"a '{self.action}' decision needs an agent_message")
        if self.ruleset_sha256 is None and any(f.rule_id for f in self.findings):
            raise ValueError("a finding with a rule_id needs the decision's ruleset_sha256")
        return self


class HookLogEntry(_Model):
    """One line of the hook log: what the agent sent and what the guard answered."""

    at: AwareDatetime
    event: Event
    decision: Decision

    @model_validator(mode="after")
    def _action_fits_event(self) -> Self:
        if self.decision.action not in ALLOWED_ACTIONS[self.event.kind]:
            raise ValueError(
                f"'{self.decision.action}' is not a valid answer to a {self.event.kind} event"
            )
        return self
