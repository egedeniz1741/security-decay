import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

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


def test_secure_and_correct_follows_its_definition() -> None:
    exploit = {"id": "sqli-login", "cwe": "CWE-89", "success": True}
    with pytest.raises(ValidationError, match="secure_and_correct must be true exactly when"):
        Evaluation.model_validate(evaluation(exploits=[exploit]))
    with pytest.raises(ValidationError, match="secure_and_correct must be true exactly when"):
        Evaluation.model_validate(evaluation(functional={"passed": 11, "total": 12}))
    insecure = Evaluation.model_validate(evaluation(exploits=[exploit], secure_and_correct=False))
    assert not insecure.secure_and_correct


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
