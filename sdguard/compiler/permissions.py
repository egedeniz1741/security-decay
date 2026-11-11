"""Permission layer: write compiled ``block`` rules into the agent's own permission settings.

Only Claude Code is supported for now. The Antigravity permission format is still open
(see PR #8). Nothing here calls an LLM; the input is an already validated ``RuleSet``.

The permission layer can only deny, so only rules with ``enforcement: block`` are written.
A ``warn`` rule with a permission target is reported back as skipped.

Whether Claude Code applies ``Read(...)`` deny rules to Bash commands such as ``cat`` and
``grep`` is not verified in our spikes. Until it is, the guard hook covers Bash; a rule
that relies on the permission layer alone keeps that path in ``known_gaps``.
"""

from dataclasses import dataclass, field
from typing import Any

from sdguard.contracts.rules import AgentName, Enforcement, RuleSet

# The agent must not change or read the tool's own state (docs/plan/01_MIMARI.md §1, rule 5).
# In the G0 spikes the agent listed and read its hook settings before starting work, so
# reading them is denied too, not only editing.
SELF_PROTECTION_DENY: tuple[str, ...] = (
    "Read(./.sdguard/**)",
    "Edit(./.sdguard/**)",
    "Read(./.claude/settings.json)",
    "Edit(./.claude/settings.json)",
    "Read(./.claude/settings.local.json)",
    "Edit(./.claude/settings.local.json)",
    "Read(./.claude/hooks/**)",
    "Edit(./.claude/hooks/**)",
)


@dataclass(frozen=True)
class PermissionPlan:
    """What the permission layer will write, and why."""

    deny: list[str]
    sources: dict[str, list[str]] = field(default_factory=dict)  # deny entry -> rule ids
    skipped: list[str] = field(default_factory=list)  # warn rules with permission targets


def plan_claude_code(ruleset: RuleSet) -> PermissionPlan:
    """Collect Claude Code deny entries from the rule set, plus the self-protection entries."""
    sources: dict[str, list[str]] = {entry: ["sdguard"] for entry in SELF_PROTECTION_DENY}
    skipped: list[str] = []
    for rule in ruleset.enforced:
        targets = [t for t in rule.targets.permissions if t.agent is AgentName.CLAUDE_CODE]
        if not targets:
            continue
        if rule.enforcement is not Enforcement.BLOCK:
            skipped.append(rule.id)
            continue
        for target in targets:
            for entry in target.deny:
                sources.setdefault(entry, []).append(rule.id)
    return PermissionPlan(deny=sorted(sources), sources=sources, skipped=skipped)


def merge_claude_settings(existing: dict[str, Any], plan: PermissionPlan) -> dict[str, Any]:
    """Return a copy of ``.claude/settings.json`` with the plan's deny entries added.

    Keys and deny entries written by the user stay as they are. An entry that is both in
    the user's ``allow`` list and in our deny list stays in both: Claude Code gives deny
    precedence, so the rule still holds.
    """
    merged = dict(existing)
    permissions = dict(merged.get("permissions") or {})
    current = permissions.get("deny") or []
    if not isinstance(current, list) or not all(isinstance(e, str) for e in current):
        raise ValueError("permissions.deny in the existing settings must be a list of strings")
    permissions["deny"] = sorted(set(current) | set(plan.deny))
    merged["permissions"] = permissions
    return merged
