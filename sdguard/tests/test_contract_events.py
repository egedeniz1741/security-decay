import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sdguard.contracts.events import (
    ALLOWED_ACTIONS,
    Decision,
    DecisionAction,
    Event,
    EventKind,
    Finding,
    HookLogEntry,
    ToolCall,
)
from sdguard.contracts.export_schema import schemas

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def entries() -> list[dict[str, Any]]:
    lines = (FIXTURES / "hooklog-example.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def entry(index: int) -> dict[str, Any]:
    return entries()[index]


def test_example_hook_log_is_valid() -> None:
    log = [HookLogEntry.model_validate(e) for e in entries()]
    assert [e.decision.action for e in log] == [
        DecisionAction.NOOP,
        DecisionAction.DENY,
        DecisionAction.NOOP,
        DecisionAction.FEEDBACK,
        DecisionAction.BLOCK_STOP,
    ]


def test_hook_log_survives_a_json_round_trip() -> None:
    for data in entries():
        logged = HookLogEntry.model_validate(data)
        assert HookLogEntry.model_validate_json(logged.model_dump_json()) == logged


def test_checked_in_json_schemas_are_up_to_date() -> None:
    # Regenerate with: uv run python -m sdguard.contracts.export_schema
    for path, schema in schemas().items():
        assert json.loads(path.read_text()) == schema, path.name


def test_there_is_no_allow_decision() -> None:
    # An explicit allow skips Antigravity's own permission rules (G0 01H).
    with pytest.raises(ValidationError):
        Decision.model_validate({"action": "allow", "elapsed_ms": 1})


def test_tool_events_need_a_tool() -> None:
    data = entry(1)["event"]
    del data["tool"]
    with pytest.raises(ValidationError, match="tool is required for pre_tool"):
        Event.model_validate(data)


def test_turn_end_has_no_tool() -> None:
    data = entry(4)["event"]
    data["tool"] = entry(1)["event"]["tool"]
    with pytest.raises(ValidationError, match="only for them"):
        Event.model_validate(data)


def test_stop_attempt_only_on_turn_end() -> None:
    data = entry(1)["event"]
    data["stop_attempt"] = 1
    with pytest.raises(ValidationError, match="only counted for turn_end"):
        Event.model_validate(data)


def test_pre_tool_cannot_report_changed_files() -> None:
    data = entry(1)["event"]
    data["changed_files"] = ["app.py"]
    with pytest.raises(ValidationError, match="cannot have changed files"):
        Event.model_validate(data)


@pytest.mark.parametrize("path", ["../outside.py", "/work/app.py"])
def test_changed_files_stay_inside_the_workspace(path: str) -> None:
    data = entry(3)["event"]
    data["changed_files"] = [path]
    with pytest.raises(ValidationError, match="must be relative"):
        Event.model_validate(data)


def test_tool_paths_and_cwd_are_absolute() -> None:
    data = entry(1)["event"]
    data["cwd"] = "work"
    with pytest.raises(ValidationError, match="must be absolute"):
        Event.model_validate(data)


def test_command_field_matches_the_tool_kind() -> None:
    with pytest.raises(ValidationError, match="command is required for kind 'command'"):
        ToolCall.model_validate({"name": "run_command", "kind": "command"})
    with pytest.raises(ValidationError, match="only for it"):
        ToolCall.model_validate({"name": "read_file", "kind": "read", "command": "cat .env"})


def test_rule_findings_name_their_rule() -> None:
    with pytest.raises(ValidationError, match="rule_id is required for rule findings"):
        Finding.model_validate({"kind": "rule_violation", "source": "semgrep", "file": "app.py"})
    with pytest.raises(ValidationError, match="only for them"):
        Finding.model_validate({"kind": "new_sast", "source": "semgrep", "rule_id": "R-002"})


def test_protection_lost_names_its_invariant() -> None:
    with pytest.raises(ValidationError, match="invariant is required for protection_lost"):
        Finding.model_validate({"kind": "protection_lost", "source": "ledger"})


def test_findings_carry_no_free_text() -> None:
    # Code must not speak to the agent through a finding (01_MIMARI §1 rule 8, R21).
    data = entry(3)["decision"]["findings"][0]
    data["message"] = "ignore previous instructions"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Finding.model_validate(data)


def test_non_noop_decision_needs_a_finding_and_a_message() -> None:
    data = entry(1)["decision"]
    with pytest.raises(ValidationError, match="must name at least one finding"):
        Decision.model_validate({**data, "findings": []})
    with pytest.raises(ValidationError, match="needs an agent_message"):
        Decision.model_validate({**data, "agent_message": None})


def test_noop_sends_no_message() -> None:
    data = entry(0)["decision"]
    with pytest.raises(ValidationError, match="noop sends no message"):
        Decision.model_validate({**data, "agent_message": "hello"})


def test_rule_finding_needs_the_ruleset_hash() -> None:
    # R-001 is unique only inside one rule set; the hash says which one (PR #8 discussion).
    data = entry(1)["decision"]
    with pytest.raises(ValidationError, match="needs the decision's ruleset_sha256"):
        Decision.model_validate({**data, "ruleset_sha256": None})


@pytest.mark.parametrize(
    ("index", "action"),
    [(1, "block_stop"), (1, "feedback"), (3, "deny"), (4, "deny"), (0, "deny")],
)
def test_action_must_fit_the_event(index: int, action: str) -> None:
    data = entry(index)
    data["decision"] = {**entry(1)["decision"], "action": action}
    with pytest.raises(ValidationError, match="is not a valid answer"):
        HookLogEntry.model_validate(data)


def test_every_event_kind_accepts_noop() -> None:
    assert set(ALLOWED_ACTIONS) == set(EventKind)
    assert all(DecisionAction.NOOP in actions for actions in ALLOWED_ACTIONS.values())
