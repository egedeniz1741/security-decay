"""The turn record (``sdguard/contracts/turns.py``) from the session's facts and the evaluation."""

from harness.runner.facts import RunMeta, TurnFacts
from sdguard.contracts.turns import Evaluation, TurnRecord


def turn_record(meta: RunMeta, facts: TurnFacts, evaluation: Evaluation | None) -> TurnRecord:
    return TurnRecord(
        run_id=meta.run_id,
        scenario=meta.scenario,
        split=meta.split,
        condition=meta.condition,
        agent=meta.agent,
        agent_version=facts.agent_version or meta.expected_agent_version,
        model=facts.model or meta.model,
        account=meta.account,
        session_id=facts.session_id or "unknown",  # a turn that crashed before its init event
        rep=meta.rep,
        turn=facts.turn,
        seed=meta.seed,
        started_at=facts.started_at,
        duration_s=facts.duration_s,
        tokens=facts.tokens,
        est_cost_usd=facts.est_cost_usd,
        config_fingerprint=facts.config_fingerprint,
        ruleset_sha256=None,  # K3 and K4 come with the adapter (D4)
        valid=not facts.invalid_reasons,
        invalid_reasons=facts.invalid_reasons,
        evaluation=evaluation,
        hook=facts.hook,
        permission_denials=facts.permission_denials,
        behavior=facts.behavior,
    )
