"""Reading Claude Code's ``--output-format stream-json`` output.

Only the fields the runner needs are read: the ``system/init`` event, the final ``result``
event, every tool call (sub-agents included) with its result, and the permission denials.
Lines that are not JSON objects are skipped; a crashed process leaves a partial stream.
"""

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    is_error: bool
    text: str


@dataclass
class Stream:
    init: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: dict[str, ToolResult] = field(default_factory=dict)

    @property
    def session_id(self) -> str | None:
        for event in (self.result, self.init):
            if event and event.get("session_id"):
                return str(event["session_id"])
        return None

    @property
    def denials(self) -> list[dict[str, Any]]:
        return list((self.result or {}).get("permission_denials") or [])

    @property
    def answer(self) -> str:
        return str((self.result or {}).get("result") or "")


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(c.get("text", "")) for c in content if isinstance(c, dict) and "text" in c
        )
    return ""


def parse(text: str) -> Stream:
    stream = Stream()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init" and stream.init is None:
            stream.init = event
        elif kind == "result":
            stream.result = event
        elif kind in ("assistant", "user"):
            for block in (event.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    stream.tool_calls.append(
                        ToolCall(
                            str(block.get("id")), str(block.get("name")), block.get("input") or {}
                        )
                    )
                elif block.get("type") == "tool_result":
                    stream.tool_results[str(block.get("tool_use_id"))] = ToolResult(
                        bool(block.get("is_error")), _text(block.get("content"))
                    )
    return stream
