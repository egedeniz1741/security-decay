"""What the agent was started with, from its ``system/init`` event.

The init event is split in two (harness/docker/README.md, V3a and V8):
- contamination fields: plugins, MCP servers, auto memory, sub-agents, output style. They are
  the same with and without a login, and a difference from the condition's expected values
  makes the turn ``fingerprint_mismatch`` (ADR-0003, R4).
- environment fields: tool, skill and command lists. Logging in adds entries, and account
  side feature rollouts may change them, so they are recorded and compared but do not
  invalidate a turn.

``config_fingerprint`` hashes both together with the settings, the protected path list and
the image, so two turns with the same fingerprint ran in the same configuration.
"""

import hashlib
import json
from typing import Any

CONTAMINATION_FIELDS = ("plugins", "mcp_servers", "memory_paths", "agents", "output_style")
ENVIRONMENT_FIELDS = ("tools", "skills", "slash_commands")


def _names(items: Any, key: str) -> list[str]:
    return sorted(str(i.get(key)) if isinstance(i, dict) else str(i) for i in items or [])


def contamination(init: dict[str, Any]) -> dict[str, Any]:
    return {
        "plugins": _names(init.get("plugins"), "source"),
        "mcp_servers": _names(init.get("mcp_servers"), "name"),
        "memory_paths": init.get("memory_paths"),
        "agents": sorted(init.get("agents") or []),
        "output_style": init.get("output_style"),
    }


def environment(init: dict[str, Any]) -> dict[str, list[str]]:
    return {f: sorted(init.get(f) or []) for f in ENVIRONMENT_FIELDS}


def differences(actual: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Names of the fields whose values differ."""
    return sorted(k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))


def config_fingerprint(
    init: dict[str, Any], *, settings_sha256: str, protected_paths_sha256: str, image_id: str
) -> str:
    payload = {
        "contamination": contamination(init),
        "environment": environment(init),
        "claude_code_version": init.get("claude_code_version"),
        "model": init.get("model"),
        "permission_mode": init.get("permissionMode"),
        "cwd": init.get("cwd"),
        "settings_sha256": settings_sha256,
        "protected_paths_sha256": protected_paths_sha256,
        "image_id": image_id,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()
