"""The LLM step of the compiler, behind a small interface.

The compiler asks the model for JSON that matches a pydantic model and checks the answer
locally again; the model's output is never trusted because a schema was sent with it.

``ClaudeCli`` runs the user's own Claude Code as a subprocess (``claude -p``), so the user's
subscription is used and no API key is needed (docs/plan/01_MIMARI.md §2.1). The call is
built so that the model can only answer:

- ``--tools ""``: no built-in tools, so the model cannot read, write or run anything;
- ``--strict-mcp-config`` without ``--mcp-config``: no MCP servers;
- ``--setting-sources project`` from an empty temporary folder: neither the user's hooks,
  plugins and permission settings nor a project ``CLAUDE.md`` are loaded;
- ``--no-session-persistence``: nothing is written to the session history;
- ``--system-prompt``: the compiler's instructions replace the default coding-agent prompt.

Spike 06 (Claude Code 2.1.318, Haiku, n = 1 per step; spikes/claude-code/06-derleme-cagrisi):
- every flag above exists;
- the answer arrives in ``structured_output`` (and as the same JSON text in ``result``);
- with ``--tools ""`` the only tool left is Claude Code's own ``StructuredOutput``; asked to
  run ``ls /``, the model could not and answered 0;
- nothing was written to the empty working folder.
The parser still accepts the answer as JSON text in ``result`` in case a version drops
``structured_output``.

The subscription token never passes through sdguard: the child process inherits the
environment and finds its own login. Nothing from the environment is logged.
"""

import json
import re
import shutil
import subprocess  # noqa: S404  # runs the user's claude CLI with a fixed argument list
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

_TIMEOUT_SECONDS = 300
# Errors after which every further call fails the same way, so compiling stops.
_FATAL_MARKERS = ("not logged in", "please run /login", "usage limit", "rate limit", "credit")
_FENCED_JSON = re.compile(r"^\s*```(?:json)?\s*(?P<body>.*?)\s*```\s*$", re.DOTALL)


class LlmError(RuntimeError):
    """The model could not be asked, or did not answer with valid JSON."""


class LlmUnavailable(LlmError):
    """The model cannot be reached at all (no CLI); retrying a rule will not help."""


@dataclass(frozen=True)
class LlmReply:
    data: dict[str, Any]
    model: str
    duration_s: float
    cost_usd: float | None = None
    usage: dict[str, Any] = field(default_factory=dict)


class Llm(Protocol):
    @property
    def model(self) -> str: ...

    def ask(self, system: str, prompt: str, schema: type[BaseModel]) -> LlmReply:
        """Ask once; raise ``LlmError`` on failure. The reply's data matches ``schema``."""
        ...


def parse_structured(result: dict[str, Any], schema: type[BaseModel]) -> dict[str, Any]:
    """Take the structured answer out of a ``claude -p --output-format json`` result."""
    if result.get("is_error") or result.get("subtype") not in (None, "success"):
        detail = str(result.get("result") or result.get("subtype") or "unknown error")
        lowered = detail.lower()
        if any(marker in lowered for marker in _FATAL_MARKERS):
            raise LlmUnavailable(f"claude cannot answer now: {detail[:300]}")
        raise LlmError(f"claude reported an error: {detail[:300]}")
    answer: Any = result.get("structured_output")
    if answer is None:
        text = result.get("result")
        if not isinstance(text, str):
            raise LlmError("claude returned neither structured_output nor a text result")
        fenced = _FENCED_JSON.match(text)
        try:
            answer = json.loads(fenced["body"] if fenced else text)
        except json.JSONDecodeError as exc:
            raise LlmError(f"the answer is not JSON: {exc}") from exc
    if not isinstance(answer, dict):
        raise LlmError("the answer is not a JSON object")
    try:
        return schema.model_validate(answer).model_dump(mode="json")
    except ValidationError as exc:
        raise LlmError(f"the answer does not match the schema: {exc}") from exc


@dataclass(frozen=True)
class ClaudeCli:
    """``claude -p`` with structured output and no tools."""

    model: str = "sonnet"
    binary: str = "claude"
    timeout: int = _TIMEOUT_SECONDS

    def command(self, system: str, prompt: str, schema: type[BaseModel]) -> list[str]:
        return [
            self.binary,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(schema.model_json_schema(), separators=(",", ":")),
            "--system-prompt",
            system,
            "--model",
            self.model,
            "--tools",
            "",
            "--strict-mcp-config",
            "--setting-sources",
            "project",
            "--no-session-persistence",
        ]

    def ask(self, system: str, prompt: str, schema: type[BaseModel]) -> LlmReply:
        binary = shutil.which(self.binary)
        if binary is None:
            raise LlmUnavailable(f"{self.binary!r} was not found on PATH")
        command = self.command(system, prompt, schema)
        command[0] = binary
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="sdguard-llm-") as empty:
            try:
                completed = subprocess.run(  # noqa: S603  # fixed argument list, no shell
                    command,
                    cwd=empty,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    stdin=subprocess.DEVNULL,
                )
            except subprocess.TimeoutExpired as exc:
                raise LlmError(f"claude did not answer within {self.timeout}s") from exc
            except OSError as exc:
                raise LlmUnavailable(f"claude could not be started: {exc}") from exc
        duration = time.monotonic() - started
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            last = (completed.stderr or completed.stdout).strip().splitlines()[-1:] or [""]
            raise LlmError(
                f"claude exited with {completed.returncode} without a JSON result: {last[0][:300]}"
            ) from exc
        if not isinstance(result, dict):
            raise LlmError("claude's result is not a JSON object")
        data = parse_structured(result, schema)
        cost = result.get("total_cost_usd")
        usage = result.get("usage")
        return LlmReply(
            data=data,
            model=self.model,
            duration_s=round(duration, 2),
            cost_usd=float(cost) if isinstance(cost, int | float) else None,
            usage=usage if isinstance(usage, dict) else {},
        )
