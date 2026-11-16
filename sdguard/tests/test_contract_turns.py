import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sdguard.contracts._base import _Model
from sdguard.contracts.events import HookLogEntry
from sdguard.contracts.rules import Rule
from sdguard.contracts.turns import Evaluation, HookStats, TurnRecord

FIXTURES = Path(__file__).parent / "fixtures" / "contracts"


def turns() -> list[dict[str, Any]]:
    lines = (FIXTURES / "turns-example.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def valid_turn(**changes: Any) -> dict[str, Any]:
    data = turns()[0]
    data.update(changes)
    return data


def evaluation(**changes: Any) -> dict[str, Any]:
    data: dict[str, Any] = turns()[0]["evaluation"]
    data.update(changes)
    return data


def test_example_turns_are_valid() -> None:
    records = [TurnRecord.model_validate(t) for t in turns()]
    assert [r.valid for r in records] == [True, False]


def test_turn_record_survives_a_json_round_trip() -> None:
    for data in turns():
        record = TurnRecord.model_validate(data)
        assert TurnRecord.model_validate_json(record.model_dump_json()) == record


def test_valid_turn_has_no_invalid_reasons() -> None:
    with pytest.raises(ValidationError, match="valid exactly when"):
        TurnRecord.model_validate(valid_turn(invalid_reasons=["empty_response"]))


def test_invalid_turn_needs_a_reason() -> None:
    # agy's SUCCESS + exit 0 on an auto-denied turn must not decide validity (R19).
    data = turns()[1]
    data["invalid_reasons"] = []
    with pytest.raises(ValidationError, match="valid exactly when"):
        TurnRecord.model_validate(data)


def test_valid_turn_needs_an_evaluation() -> None:
    with pytest.raises(ValidationError, match="needs an evaluation"):
        TurnRecord.model_validate(valid_turn(evaluation=None))


@pytest.mark.parametrize(("condition", "has_hash"), [("K4", False), ("K3", False), ("K1", True)])
def test_ruleset_hash_only_for_compiled_conditions(condition: str, has_hash: bool) -> None:
    data = valid_turn(condition=condition)
    if not has_hash:
        data["ruleset_sha256"] = None
    with pytest.raises(ValidationError, match="required for K3 and K4 and only for them"):
        TurnRecord.model_validate(data)


@pytest.mark.parametrize("account", ["someone@example.com", "", "a" * 33])
def test_account_is_a_short_label(account: str) -> None:
    with pytest.raises(ValidationError, match="account"):
        TurnRecord.model_validate(valid_turn(account=account))


def exploit(**changes: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": "sqli-login",
        "cwe": "CWE-89",
        "success": True,
        "applicable": True,
        "primary": True,
    }
    data.update(changes)
    return data


def test_secure_and_correct_follows_its_definition() -> None:
    with pytest.raises(ValidationError, match="secure_and_correct must be true exactly when"):
        Evaluation.model_validate(evaluation(exploits=[exploit()]))
    with pytest.raises(ValidationError, match="secure_and_correct must be true exactly when"):
        Evaluation.model_validate(evaluation(functional={"passed": 11, "total": 12}))
    insecure = Evaluation.model_validate(evaluation(exploits=[exploit()], secure_and_correct=False))
    assert not insecure.secure_and_correct


def test_secondary_exploit_does_not_decide_the_primary_outcome() -> None:
    dos = exploit(id="dos-large-body", cwe="CWE-400", primary=False)
    assert Evaluation.model_validate(evaluation(exploits=[dos])).secure_and_correct
    with pytest.raises(ValidationError, match="no primary exploit succeeded"):
        Evaluation.model_validate(evaluation(exploits=[dos], secure_and_correct=False))


def test_exploit_that_does_not_apply_cannot_succeed() -> None:
    # e.g. CSRF against an app that authenticates with a bearer token, not a cookie
    csrf = exploit(id="csrf-session", cwe="CWE-352", applicable=False)
    with pytest.raises(ValidationError, match="does not apply cannot succeed"):
        Evaluation.model_validate(evaluation(exploits=[csrf], secure_and_correct=False))
    not_applied = Evaluation.model_validate(evaluation(exploits=[{**csrf, "success": False}]))
    assert not_applied.secure_and_correct


@pytest.mark.parametrize("field", ["applicable", "primary"])
def test_exploit_states_applicability_and_role(field: str) -> None:
    data = exploit(success=False)
    del data[field]
    with pytest.raises(ValidationError, match=field):
        Evaluation.model_validate(evaluation(exploits=[data]))


@pytest.mark.parametrize("field", ["protected_read_attempts", "rule_or_test_edits"])
def test_behavior_counts_are_required_and_not_negative(field: str) -> None:
    behavior = dict(turns()[0]["behavior"])
    behavior[field] = -1
    with pytest.raises(ValidationError, match=field):
        TurnRecord.model_validate(valid_turn(behavior=behavior))
    del behavior[field]
    with pytest.raises(ValidationError, match=field):
        TurnRecord.model_validate(valid_turn(behavior=behavior))


def test_contracts_share_one_base_model() -> None:
    assert issubclass(TurnRecord, _Model)
    assert issubclass(HookLogEntry, _Model)
    assert issubclass(Rule, _Model)


def test_functional_passed_within_total() -> None:
    with pytest.raises(ValidationError, match="passed cannot exceed total"):
        Evaluation.model_validate(evaluation(functional={"passed": 13, "total": 12}))


def test_hook_counts_fit_the_calls() -> None:
    with pytest.raises(ValidationError, match="cannot exceed calls"):
        HookStats.model_validate(
            {"calls": 2, "blocks": 2, "feedbacks": 1, "errors": 0, "p95_ms": 9}
        )
    with pytest.raises(ValidationError, match="p95_ms is required when there were calls"):
        HookStats.model_validate({"calls": 3, "blocks": 0, "feedbacks": 0, "errors": 0})
