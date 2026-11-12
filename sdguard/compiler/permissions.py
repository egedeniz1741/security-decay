"""Permission layer: write compiled ``block`` rules into the agent's own permission settings.

Only Claude Code is supported for now; the Antigravity layer follows spike 06 (PR #12).
Nothing here calls an LLM; the input is an already validated ``RuleSet``.

The permission layer can only deny, so only rules with ``enforcement: block`` are written.
A ``warn`` rule with a permission target is reported back as skipped.

sdguard remembers which deny entries it added (a state file under ``.sdguard/``). On the
next run it removes those before adding the new plan, so a rule that was dropped or
downgraded does not leave its entry behind. Entries the user wrote are never touched.

Whether Claude Code applies ``Read(...)`` deny rules to Bash commands such as ``cat`` and
``grep`` is not verified in our spikes. Until it is, the guard hook covers Bash; a rule
that relies on the permission layer alone keeps that path in ``known_gaps``.
"""

from dataclasses import dataclass, field
from typing import Any

from sdguard.contracts.rules import AgentName, Enforcement, RuleSet

# The agent must not change or read the tool's own state (docs/plan/01_MIMARI.md §1, rule 5).
# In the G0 spikes the agent listed and read its hook settings before starting work, so
# reading them is denied too, not only editing. A leading "/" is relative to the project
# root in project settings, so the entries hold when Claude starts in a subfolder ("./"
# would be relative to the working directory). Taken from the permissions docs, not
# verified by a spike.
SELF_PROTECTION_DENY: tuple[str, ...] = (
    "Read(/.sdguard/**)",
    "Edit(/.sdguard/**)",
    "Read(/.claude/settings.json)",
    "Edit(/.claude/settings.json)",
    "Read(/.claude/settings.local.json)",
    "Edit(/.claude/settings.local.json)",
    "Read(/.claude/hooks/**)",
    "Edit(/.claude/hooks/**)",
)


@dataclass(frozen=True)
class PermissionPlan:
    """What the permission layer will write, and why."""

    deny: list[str]
    sources: dict[str, list[str]] = field(default_factory=dict)  # deny entry -> rule ids
    skipped: list[str] = field(default_factory=list)  # warn rules with permission targets


@dataclass(frozen=True)
class MergeResult:
    settings: dict[str, Any]
    added: list[str]  # entries sdguard added; stored so the next run can remove them
    removed: list[str]  # entries an earlier run added that the plan no longer has


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


def _string_list(value: Any, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(e, str) for e in value):
        raise ValueError(f"{where} must be a list of strings")
    return value


def merge_claude_settings(
    existing: Any, plan: PermissionPlan, previously_added: list[str] | None = None
) -> MergeResult:
    """Return a copy of ``.claude/settings.json`` with the plan's deny entries in place.

    ``previously_added`` are the entries an earlier run added (from the state file). They
    are taken out first; then every plan entry the user does not already have is appended.
    The user's own entries keep their order, duplicates included. An entry in both the
    user's ``allow`` list and our deny list stays in both: deny takes precedence in Claude
    Code, so the rule still holds.
    """
    if not isinstance(existing, dict):
        raise ValueError("the settings file must contain a JSON object")
    merged = dict(existing)
    permissions = merged.get("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError("'permissions' in the settings file must be an object")
    permissions = dict(permissions)
    current = _string_list(permissions.get("deny", []), "permissions.deny")
    ours_before = set(_string_list(previously_added or [], "the sdguard state file"))

    user_entries = [entry for entry in current if entry not in ours_before]
    user_set = set(user_entries)
    added = [entry for entry in plan.deny if entry not in user_set]
    removed = sorted(ours_before - set(plan.deny) - user_set)

    permissions["deny"] = user_entries + added
    merged["permissions"] = permissions
    return MergeResult(settings=merged, added=added, removed=removed)
