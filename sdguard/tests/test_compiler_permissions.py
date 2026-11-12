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


def plan_for(data: dict[str, Any] | None = None) -> Any:
    return plan_claude_code(RuleSet.model_validate(data or example()))


def test_block_rule_is_written_with_its_source() -> None:
    plan = plan_for()
    assert "Read(/.env)" in plan.deny
    assert plan.sources["Read(/.env)"] == ["R-001"]


def test_self_protection_entries_are_always_present() -> None:
    data = example()
    data["rules"] = []
    assert plan_for(data).deny == sorted(SELF_PROTECTION_DENY)


def test_self_protection_is_anchored_at_the_project_root() -> None:
    assert all("(/" in entry for entry in SELF_PROTECTION_DENY)
    assert "Read(/.claude/settings.json)" in SELF_PROTECTION_DENY
    assert "Read(/.claude/hooks/**)" in SELF_PROTECTION_DENY


def test_other_agents_targets_are_ignored() -> None:
    assert "read_file(.env)" not in plan_for().deny


def test_warn_rule_with_permission_target_is_skipped() -> None:
    data = example()
    data["rules"][0]["enforcement"] = "warn"
    plan = plan_for(data)
    assert plan.skipped == ["R-001"]
    assert "Read(/.env)" not in plan.deny


def test_merge_keeps_user_settings_and_entry_order() -> None:
    existing: dict[str, Any] = {
        "model": "keep-me",
        "permissions": {"allow": ["Bash(uv run pytest)"], "deny": ["Write(/b)", "Read(/a)"]},
        "hooks": {"PreToolUse": []},
    }
    result = merge_claude_settings(existing, plan_for())
    assert result.settings["model"] == "keep-me"
    assert result.settings["hooks"] == {"PreToolUse": []}
    assert result.settings["permissions"]["allow"] == ["Bash(uv run pytest)"]
    deny = result.settings["permissions"]["deny"]
    assert deny[:2] == ["Write(/b)", "Read(/a)"]  # user's order kept, ours appended
    assert "Read(/.env)" in deny
    assert existing["permissions"]["deny"] == ["Write(/b)", "Read(/a)"]  # input not changed


def test_merge_is_idempotent() -> None:
    plan = plan_for()
    first = merge_claude_settings({}, plan)
    second = merge_claude_settings(first.settings, plan, first.added)
    assert second.settings == first.settings
    assert second.added == first.added
    assert second.removed == []


def test_entry_of_a_dropped_rule_is_removed() -> None:
    first = merge_claude_settings({}, plan_for())
    data = example()
    data["rules"][0]["enforcement"] = "warn"  # R-001 no longer blocks
    second = merge_claude_settings(first.settings, plan_for(data), first.added)
    assert "Read(/.env)" not in second.settings["permissions"]["deny"]
    assert "Read(/.env)" in second.removed


def test_user_entry_that_matches_ours_is_kept() -> None:
    existing = {"permissions": {"deny": ["Read(/.env)"]}}
    first = merge_claude_settings(existing, plan_for())
    assert "Read(/.env)" not in first.added  # the user wrote it, not sdguard
    data = example()
    data["rules"][0]["enforcement"] = "warn"
    second = merge_claude_settings(first.settings, plan_for(data), first.added)
    assert "Read(/.env)" in second.settings["permissions"]["deny"]


@pytest.mark.parametrize(
    ("existing", "message"),
    [
        ([], "JSON object"),
        (None, "JSON object"),
        ({"permissions": 5}, "'permissions'"),
        ({"permissions": {"deny": "Read(/.env)"}}, "list of strings"),
    ],
)
def test_merge_rejects_unexpected_settings(existing: Any, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        merge_claude_settings(existing, plan_for())


def run(tmp_path: Path, *extra: str) -> tuple[int, Path]:
    settings = tmp_path / ".claude" / "settings.json"
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(settings), *extra])
    return code, settings


def test_cli_writes_settings_and_state(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, settings = run(tmp_path)
    assert code == 0
    assert "Read(/.env)" in json.loads(settings.read_text())["permissions"]["deny"]
    state = json.loads((tmp_path / ".sdguard" / "permissions.claude.json").read_text())
    assert "Read(/.env)" in state["added"]
    assert "R-001" in capsys.readouterr().err
    assert not list(settings.parent.glob("*.tmp"))  # no leftover temporary file


def test_cli_dry_run_prints_only_json_on_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, settings = run(tmp_path, "--dry-run")
    assert code == 0
    assert not settings.exists()
    out = capsys.readouterr().out
    assert "Read(/.env)" in json.loads(out)["permissions"]["deny"]


def test_cli_reports_an_invalid_rule_file(tmp_path: Path) -> None:
    bad = tmp_path / "rules.json"
    bad.write_text(json.dumps({"schema_version": "0.1"}))
    code = main(["permissions", "--rules", str(bad), "--settings", str(tmp_path / "s.json")])
    assert code == 2


def test_cli_reports_a_rule_file_that_is_not_utf8(tmp_path: Path) -> None:
    bad = tmp_path / "rules.json"
    bad.write_bytes(b"\xff\xfe\x00")
    code = main(["permissions", "--rules", str(bad), "--settings", str(tmp_path / "s.json")])
    assert code == 2


def test_cli_leaves_a_broken_settings_file_alone(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"permissions": {"deny": "Read(/.env)"}}))
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(settings)])
    assert code == 2
    assert json.loads(settings.read_text()) == {"permissions": {"deny": "Read(/.env)"}}


def test_cli_reports_a_settings_path_that_is_a_folder(tmp_path: Path) -> None:
    folder = tmp_path / "settings.json"
    folder.mkdir()
    code = main(["permissions", "--rules", str(EXAMPLE), "--settings", str(folder)])
    assert code == 2
