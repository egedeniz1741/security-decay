"""Validate compiled deny entries against good and bad example tool calls.

A permission rule is trusted only when its deny entries stop every bad example (a tool
call the written rule forbids) and none of the good examples (a nearby call the rule
allows). The entries are matched with a model of each agent's permission matcher. The
model is deliberately **narrow**: where the documentation leaves room, it assumes the
entry matches less, never more. A rule can therefore look weaker than it is, but it can
never be marked as enforced for a call the agent would actually allow.

Claude Code (permissions documentation; spike 05 for ``Read(/.env)``):
- ``Read(path)`` applies to the Read tool. The documentation says Read rules also apply
  "best effort" to Grep and Glob; that is not relied on here.
- ``Edit(path)`` applies to Edit and Write ("all built-in tools that edit files");
  ``Write(path)`` only to Write.
- Paths follow gitignore patterns. A leading ``/`` is the project root; the compiler only
  writes root-anchored paths, because ``./`` and bare paths depend on the working folder.
- ``Bash(prefix:*)`` and ``Bash(prefix *)`` match a command that starts with the prefix as
  whole words; ``Bash(command)`` matches exactly that command. Shell operators (``&&``,
  pipes) are not modelled, so an example must be a single command.
- A bare tool name (``Bash``) denies every call of that tool.

Antigravity (spikes 06C, 06G): ``read_file(path)`` and ``write_file(path)`` match exactly one
path relative to the project root, or ``*`` for every file. Other actions are not modelled
yet, so a rule that needs them fails validation instead of being trusted.
"""

import posixpath
import re
from collections.abc import Callable, Sequence
from functools import cache

from sdguard.compiler.schemas import ToolCall
from sdguard.contracts.rules import Validation, ValidationStatus

_ENTRY = re.compile(r"^(?P<name>[A-Za-z_]+)(?:\((?P<spec>[^()]+)\))?$")
_CLAUDE_APPLIES_TO: dict[str, frozenset[str]] = {
    "Read": frozenset({"Read"}),
    "Edit": frozenset({"Edit", "Write"}),
    "Write": frozenset({"Write"}),
    "Bash": frozenset({"Bash"}),
    "Grep": frozenset({"Grep"}),
    "Glob": frozenset({"Glob"}),
}
_FILE_TOOLS = frozenset({"Read", "Grep", "Glob", "Edit", "Write"})
_AGY_APPLIES_TO: dict[str, frozenset[str]] = {
    "read_file": frozenset({"Read"}),
    "write_file": frozenset({"Edit", "Write"}),
}


class UnsupportedEntry(ValueError):
    """The entry is valid for the agent but cannot be checked by this model."""


def normalize_path(path: str) -> str:
    """A project-relative POSIX path without ``./`` or a leading ``/``."""
    clean = posixpath.normpath(path.replace("\\", "/").lstrip("/"))
    return "" if clean == "." else clean


@cache
def _glob_regex(pattern: str) -> re.Pattern[str]:
    """gitignore-style pattern (already relative to the root) as a full-match regex."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("/**", i) and i + 3 == len(pattern):
            out.append("(?:/.*)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out))


def _path_matches(spec: str, target: str) -> bool:
    if not spec.startswith("/") or spec.startswith("//"):
        raise UnsupportedEntry(
            f"path {spec!r} must start with a single '/' (the project root); "
            "'./', bare, '//' and '~/' paths depend on where the agent was started"
        )
    pattern = spec[1:].rstrip("/")
    if spec.endswith("/") and not spec.endswith("**/"):
        pattern += "/**"  # "dir/" means everything inside dir
    return _glob_regex(pattern).fullmatch(normalize_path(target)) is not None


def _command_matches(spec: str, command: str) -> bool:
    command = " ".join(command.split())
    for suffix in (":*", " *"):
        if spec.endswith(suffix):
            prefix = " ".join(spec[: -len(suffix)].split())
            return command == prefix or command.startswith(prefix + " ")
    if "*" in spec:
        raise UnsupportedEntry(f"Bash pattern {spec!r}: only a trailing ':*' or ' *' is modelled")
    return command == " ".join(spec.split())


def claude_code_denies(entry: str, call: ToolCall) -> bool:
    """Whether the Claude Code deny ``entry`` stops ``call`` under the narrow model."""
    match = _ENTRY.match(entry)
    if match is None:
        raise UnsupportedEntry(f"{entry!r} is not 'Tool' or 'Tool(spec)'")
    name, spec = match["name"], match["spec"]
    applies = _CLAUDE_APPLIES_TO.get(name)
    if applies is None:
        raise UnsupportedEntry(f"{entry!r}: tool {name!r} is not modelled")
    if call.tool not in applies:
        return False
    if spec is None:
        return True
    if name == "Bash":
        return _command_matches(spec, call.target)
    if name in ("Grep", "Glob"):
        raise UnsupportedEntry(f"{entry!r}: patterns for {name} are not modelled")
    return _path_matches(spec, call.target)


def antigravity_denies(entry: str, call: ToolCall) -> bool:
    match = _ENTRY.match(entry)
    if match is None or match["spec"] is None:
        raise UnsupportedEntry(f"{entry!r} is not 'action(target)'")
    applies = _AGY_APPLIES_TO.get(match["name"])
    if applies is None:
        raise UnsupportedEntry(f"{entry!r}: action {match['name']!r} is not modelled yet")
    if call.tool not in applies:
        return False
    target = match["spec"]
    return target == "*" or normalize_path(target) == normalize_path(call.target)


def _describe(call: ToolCall) -> str:
    return f"{call.tool}({call.target})"


def _check_agent(
    agent: str,
    entries: Sequence[str],
    denies: Callable[[str, ToolCall], bool],
    must_deny: Sequence[ToolCall],
    must_allow: Sequence[ToolCall],
) -> list[str]:
    problems: list[str] = []

    def denied(call: ToolCall) -> bool:
        return any(denies(entry, call) for entry in entries)

    try:
        for call in must_deny:
            if not denied(call):
                problems.append(f"{agent}: bad example {_describe(call)} is not denied")
        for call in must_allow:
            if denied(call):
                problems.append(f"{agent}: good example {_describe(call)} is denied too")
    except UnsupportedEntry as exc:
        problems.append(f"{agent}: {exc}")
    return problems


def validate_permissions(
    claude_code_deny: Sequence[str],
    antigravity_deny: Sequence[str],
    must_deny: Sequence[ToolCall],
    must_allow: Sequence[ToolCall],
    *,
    attempts: int = 1,
) -> tuple[Validation, list[str]]:
    """Check the deny entries of both agents against the same examples.

    Claude Code entries must stop every bad example and no good one. Antigravity has no
    wildcards, so its entries usually cannot stop every bad example (a ``.env`` in a
    subfolder): they must stop at least one bad file example and no good one, and every bad
    example they miss is returned as a known gap instead of being hidden.
    """
    problems: list[str] = []
    gaps: list[str] = []
    if any(call.tool in ("Grep", "Glob") for call in [*must_deny, *must_allow]):
        problems.append(
            "Grep and Glob examples cannot be checked; describe folder-wide searches in "
            "known_gaps instead"
        )
    problems += _check_agent(
        "claude-code", claude_code_deny, claude_code_denies, must_deny, must_allow
    )
    if antigravity_deny:
        file_bad = [c for c in must_deny if c.tool in _FILE_TOOLS]
        file_good = [c for c in must_allow if c.tool in _FILE_TOOLS]
        try:
            missed = [
                c for c in file_bad if not any(antigravity_denies(e, c) for e in antigravity_deny)
            ]
            wrong = [
                c for c in file_good if any(antigravity_denies(e, c) for e in antigravity_deny)
            ]
        except UnsupportedEntry as exc:
            problems.append(f"antigravity: {exc}")
        else:
            problems += [f"antigravity: good example {_describe(c)} is denied too" for c in wrong]
            if file_bad and len(missed) == len(file_bad):
                problems.append("antigravity: the entries stop none of the bad examples")
            gaps += [f"Antigravity: {_describe(c)} is not denied." for c in missed]
    validation = Validation(
        status=ValidationStatus.FAILED if problems else ValidationStatus.VERIFIED,
        good_examples=len(must_allow),
        bad_examples=len(must_deny),
        attempts=attempts,
        message="; ".join(problems) or None,
    )
    return validation, gaps
