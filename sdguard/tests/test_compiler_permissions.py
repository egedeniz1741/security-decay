import json
from pathlib import Path
from typing import Any

import pytest

from sdguard.cli import main
from sdguard.compiler.permissions import (
    SELF_PROTECTION_DENY,
    merge_claude_settings,
    plan_claude_code,
)
from sdguard.contracts.rules import RuleSet

EXAMPLE = Path(__file__).parent / "fixtures" / "contracts" / "ruleset-example.json"


def example() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(EXAMPLE.read_text())
    return data


def test_block_rule_is_written_with_its_source() -> None:
    plan = plan_claude_code(RuleSet.model_validate(example()))
    assert "Read(./.env)" in plan.deny
    assert plan.sources["Read(./.env)"] == ["R-001"]


def test_self_protection_entries_are_always_present() -> None:
    data = example()
    data["rules"] = []
    plan = plan_claude_code(RuleSet.model_validate(data))
    assert plan.deny == sorted(SELF_PROTECTION_DENY)


def test_other_agents_targets_are_ignored() -> None:
    plan = plan_claude_code(RuleSet.model_validate(example()))
    assert "read_file(.env)" not in plan.deny


def test_warn_rule_with_permission_target_is_skipped() -> None:
    data = example()
    data["rules"][0]["enforcement"] = "warn"
    plan = plan_claude_code(RuleSet.model_validate(data))
    assert plan.skipped == ["R-001"]
    assert "Read(./.env)" not in plan.deny


def test_merge_keeps_user_settings_and_entries() -> None:
    existing: dict[str, Any] = {
        "model": "keep-me",
        "permissions": {"allow": ["Bash(uv run pytest)"], "deny": ["Read(./secrets/**)"]},
        "hooks": {"PreToolUse": []},
    }
    plan = plan_claude_code(RuleSet.model_validate(example()))
    merged = merge_claude_settings(existing, plan)
    assert merged["model"] == "keep-me"
    assert merged["hooks"] == {"PreToolUse": []}
    assert merged["permissions"]["allow"] == ["Bash(uv run pytest)"]
    assert "Read(./secrets/**)" in merged["permissions"]["deny"]
    assert "Read(./.env)" in merged["permissions"]["deny"]
    assert existing["permissions"]["deny"] == ["Read(./secrets/**)"]  # input not changed


def test_merge_is_idempotent() -> None:
    plan = plan_claude_code(RuleSet.model_validate(example()))
    once = merge_claude_settings({}, plan)
    assert merge_claude_settings(once, plan) == once


def test_merge_rejects_a_broken_deny_list() -> None:
    plan = plan_claude_code(RuleSet.model_validate(example()))
    with pytest.raises(ValueError, match="list of strings"):
        merge_claude_settings({"permissions": {"deny": "Read(./.env)"}}, plan)


def test_cli_writes_settings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    settings = tmp_path / ".claude" / "settings.json"
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(settings)])
    assert code == 0
    written = json.loads(settings.read_text())
    assert "Read(./.env)" in written["permissions"]["deny"]
    out = capsys.readouterr().out
    assert "R-001" in out


def test_cli_dry_run_does_not_write(tmp_path: Path) -> None:
    settings = tmp_path / ".claude" / "settings.json"
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(settings), "--dry-run"])
    assert code == 0
    assert not settings.exists()


def test_cli_reports_an_invalid_rule_file(tmp_path: Path) -> None:
    bad = tmp_path / "rules.json"
    bad.write_text(json.dumps({"schema_version": "0.1"}))
    code = main(["permissions", "--rules", str(bad), "--settings", str(tmp_path / "s.json")])
    assert code == 2


def test_agent_cannot_read_its_hook_settings() -> None:
    plan = plan_claude_code(RuleSet.model_validate(example()))
    assert "Read(./.claude/settings.json)" in plan.deny
    assert "Read(./.claude/hooks/**)" in plan.deny


def test_cli_reports_a_broken_settings_file(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"permissions": {"deny": "Read(./.env)"}}))
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(settings)])
    assert code == 2
    assert json.loads(settings.read_text()) == {"permissions": {"deny": "Read(./.env)"}}
