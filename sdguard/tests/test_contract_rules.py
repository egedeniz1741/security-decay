import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sdguard.contracts.rules import (
    AgentName,
    PermissionTarget,
    Rule,
    RuleSet,
    ruleset_json_schema,
)

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"
SCHEMA_FILE = Path(__file__).parent.parent / "contracts" / "schema" / "ruleset.schema.json"


def example() -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / "ruleset-example.json").read_text())
    return data


def rule(index: int, **changes: Any) -> dict[str, Any]:
    data: dict[str, Any] = example()["rules"][index]
    data.update(changes)
    return data


def test_example_ruleset_is_valid() -> None:
    ruleset = RuleSet.model_validate(example())
    assert [r.id for r in ruleset.enforced] == ["R-001", "R-002", "R-003"]
    assert [r.id for r in ruleset.advisory] == ["R-004"]


def test_ruleset_survives_a_json_round_trip() -> None:
    ruleset = RuleSet.model_validate(example())
    assert RuleSet.model_validate_json(ruleset.model_dump_json()) == ruleset


def test_checked_in_json_schema_is_up_to_date() -> None:
    # Regenerate with: uv run python -m sdguard.contracts.export_schema
    assert json.loads(SCHEMA_FILE.read_text()) == ruleset_json_schema()


def test_unverified_rule_cannot_be_enforced() -> None:
    data = rule(1, validation={"status": "failed", "attempts": 3})
    with pytest.raises(ValidationError, match="not verified must not be enforced"):
        Rule.model_validate(data)


def test_vague_rule_can_only_be_advice() -> None:
    data = rule(1, category="vague")
    with pytest.raises(ValidationError, match="vague rule can only be advice"):
        Rule.model_validate(data)


def test_enforced_rule_needs_a_target() -> None:
    data = rule(1, targets={})
    with pytest.raises(ValidationError, match="needs at least one compiled target"):
        Rule.model_validate(data)


def test_partial_coverage_must_name_its_gaps() -> None:
    data = rule(0, known_gaps=[])
    with pytest.raises(ValidationError, match="must list what is not covered"):
        Rule.model_validate(data)


def test_advice_only_rule_has_no_coverage() -> None:
    data = rule(3, coverage="full")
    with pytest.raises(ValidationError, match="coverage must be 'none'"):
        Rule.model_validate(data)


def test_verified_needs_good_and_bad_examples() -> None:
    data = rule(1, validation={"status": "verified", "good_examples": 2, "bad_examples": 0})
    with pytest.raises(ValidationError, match="at least one good and one bad example"):
        Rule.model_validate(data)


def test_duplicate_rule_ids_are_rejected() -> None:
    data = example()
    data["rules"][1]["id"] = "R-001"
    with pytest.raises(ValidationError, match="duplicate rule ids: R-001"):
        RuleSet.model_validate(data)


def test_rule_source_must_be_a_listed_file() -> None:
    data = example()
    data["rules"][0]["source"]["file"] = "CLAUDE.md"
    with pytest.raises(ValidationError, match="missing from sources: CLAUDE.md"):
        RuleSet.model_validate(data)


@pytest.mark.parametrize("bad_path", ["/etc/passwd", "../outside.yaml", "semgrep/../../x.yaml"])
def test_artifact_paths_must_stay_inside_the_sdguard_folder(bad_path: str) -> None:
    data = rule(1, targets={"semgrep": {"rule_path": bad_path, "test_path": "semgrep/tests/t.py"}})
    with pytest.raises(ValidationError):
        Rule.model_validate(data)


def test_unknown_fields_are_rejected() -> None:
    data = rule(1, severity="high")
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Rule.model_validate(data)


@pytest.mark.parametrize(
    "entry",
    ["Read(/.env)", "Bash(cat:*)", "WebFetch", "mcp__github__create_issue", "Edit(/src/**)"],
)
def test_valid_claude_code_deny_entries(entry: str) -> None:
    PermissionTarget(agent=AgentName.CLAUDE_CODE, deny=[entry])


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("read(/.env)", "unknown tool"),
        ("Reed(/.env)", "unknown tool"),
        ("Read(/.env", "is not 'Tool' or 'Tool\\(spec\\)'"),
        ("Read()", "is not 'Tool' or 'Tool\\(spec\\)'"),
    ],
)
def test_invalid_claude_code_deny_entries(entry: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        PermissionTarget(agent=AgentName.CLAUDE_CODE, deny=[entry])


@pytest.mark.parametrize(
    "entry", ["read_file(.env)", "write_file(/work/app.py)", "command(rm)", "read_file(*)"]
)
def test_valid_antigravity_deny_entries(entry: str) -> None:
    PermissionTarget(agent=AgentName.ANTIGRAVITY, deny=[entry])


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("edit_file(app.py)", "unknown action 'edit_file'"),  # tool name, not action (06G)
        ("run_command(cat .env)", "unknown action 'run_command'"),
        ("read_file(.env.*)", "take no wildcards"),  # silently ignored by agy (06C)
        ("read_file", "is not 'action\\(target\\)'"),
    ],
)
def test_invalid_antigravity_deny_entries(entry: str, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        PermissionTarget(agent=AgentName.ANTIGRAVITY, deny=[entry])


def test_duplicate_deny_entries_are_rejected() -> None:
    with pytest.raises(ValidationError, match="unique"):
        PermissionTarget(agent=AgentName.ANTIGRAVITY, deny=["read_file(.env)", "read_file(.env)"])
