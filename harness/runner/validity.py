"""Why a turn is invalid, from facts the agent does not control.

A Claude Code turn ends with a ``result`` event; its ``is_error`` and answer decide, never
the process exit code alone (the R19 lesson from Antigravity).
"""

from typing import Any

from harness.runner import fingerprint
from harness.runner.stream import Stream
from sdguard.contracts.turns import InvalidReason


def invalid_reasons(
    stream: Stream,
    *,
    expected_contamination: dict[str, Any],
    expected_version: str,
    timed_out: bool,
    integrity_changes: list[str],
) -> list[InvalidReason]:
    reasons: set[InvalidReason] = set()
    if timed_out or stream.result is None or stream.result.get("is_error"):
        reasons.add(InvalidReason.INFRA_ERROR)  # crash, timeout, quota, auth or API error
    elif not stream.answer.strip():
        reasons.add(InvalidReason.EMPTY_RESPONSE)
    if stream.init is None:
        reasons.add(InvalidReason.INFRA_ERROR)
    else:
        if fingerprint.differences(fingerprint.contamination(stream.init), expected_contamination):
            reasons.add(InvalidReason.FINGERPRINT_MISMATCH)
        if stream.init.get("claude_code_version") != expected_version:
            reasons.add(InvalidReason.AGENT_VERSION_CHANGED)
    if integrity_changes:
        reasons.add(InvalidReason.PROTECTED_FILE_CHANGED)
    return [r for r in InvalidReason if r in reasons]
