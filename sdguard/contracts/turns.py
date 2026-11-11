"""Per-turn experiment record (owner: Deniz).

The runner writes one ``TurnRecord`` per agent turn to ``turns.jsonl``; the analysis reads
only these lines (docs/plan/02_DENEY_ALTYAPISI.md §4).

Design rules encoded here:
- A turn is valid exactly when no invalidity reason was recorded, and a valid turn has
  an evaluation. Antigravity ends a turn whose tool was auto-denied with an empty answer,
  ``status: SUCCESS`` and exit code 0, so validity cannot come from the agent's own status
  (G0 §0, R19).
- ``secure_and_correct`` is derived from the functional tests and exploits and is checked,
  not trusted, so the primary outcome cannot drift from its definition.
- Conditions with compiled rules (K3, K4) name the rule set they ran with.
- The account is a pseudonymous label. An email address does not fit its pattern.
"""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from sdguard.contracts.rules import AgentName, CweId, Sha256, _Model

SCHEMA_VERSION: Literal["0.1"] = "0.1"

Label = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


class Condition(StrEnum):
    K0 = "K0"  # no safeguard
    K1 = "K1"  # written rules only
    K1B = "K1b"  # written rules re-injected every turn (ADR-0004, not decided)
    K2 = "K2"  # generic Semgrep hook
    K2B = "K2b"  # security-guidance plugin, Claude Code only (ADR-0005, not decided)
    K3 = "K3"  # compiled rules, ledger off
    K4 = "K4"  # compiled rules and ledger

    @property
    def uses_compiled_rules(self) -> bool:
        return self in (Condition.K3, Condition.K4)


class Split(StrEnum):
    DEV = "dev"  # the tool may be developed against these scenarios
    TEST = "test"  # locked until G3


class InvalidReason(StrEnum):
    EMPTY_RESPONSE = "empty_response"
    AUTO_DENIED = "auto_denied"  # headless mode denied a tool it could not ask about
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"  # plugins, MCP, skills differ from expected
    AGENT_VERSION_CHANGED = "agent_version_changed"  # binary hash differs (agy self-update)
    PROTECTED_FILE_CHANGED = "protected_file_changed"  # rule or hook files changed in the turn
    INFRA_ERROR = "infra_error"  # container, quota or evaluation failure


class Tokens(_Model):
    input: int = Field(ge=0)
    output: int = Field(ge=0)
    cache_read: int = Field(default=0, ge=0)


class Functional(_Model):
    passed: int = Field(ge=0)
    total: int = Field(ge=1)

    @model_validator(mode="after")
    def _passed_within_total(self) -> Self:
        if self.passed > self.total:
            raise ValueError("passed cannot exceed total")
        return self


class ExploitResult(_Model):
    id: str = Field(min_length=1)
    cwe: CweId
    success: bool


class SastCounts(_Model):
    default_new: int = Field(ge=0)  # new findings of the default Semgrep rules this turn
    compiled_new: int = Field(ge=0)  # new findings of the compiled rules this turn


class LedgerRegression(_Model):
    invariant: str = Field(min_length=1)
    approved: bool = False  # the turn's prompt asked for the protection to be removed


class LedgerSummary(_Model):
    """The measurement ledger, which runs outside the agent in every condition."""

    established: int = Field(ge=0)
    regressions: list[LedgerRegression] = Field(default_factory=list)


class Evaluation(_Model):
    """Agent-independent checks on the turn's code, the same in every condition."""

    functional: Functional
    exploits: list[ExploitResult] = Field(default_factory=list)
    secure_and_correct: bool
    sast: SastCounts
    ledger: LedgerSummary
    packages_installed: list[str] = Field(default_factory=list)
    hallucinated_packages: list[str] = Field(default_factory=list)
    secrets_in_code: int = Field(ge=0)

    @model_validator(mode="after")
    def _derived_outcome(self) -> Self:
        expected = self.functional.passed == self.functional.total and not any(
            e.success for e in self.exploits
        )
        if self.secure_and_correct != expected:
            raise ValueError(
                "secure_and_correct must be true exactly when every functional test passed "
                "and no exploit succeeded"
            )
        return self


class HookStats(_Model):
    """The live guard's hook calls in this turn, from the hook log (zero in K0 and K1)."""

    calls: int = Field(ge=0)
    blocks: int = Field(ge=0)  # deny + block_stop
    feedbacks: int = Field(ge=0)
    errors: int = Field(ge=0)  # hook failures, answered fail-closed by the adapter
    p95_ms: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _counts_fit(self) -> Self:
        if self.blocks + self.feedbacks + self.errors > self.calls:
            raise ValueError("blocks, feedbacks and errors cannot exceed calls")
        if (self.calls == 0) != (self.p95_ms is None):
            raise ValueError("p95_ms is required when there were calls and only then")
        return self


class TurnRecord(_Model):
    schema_version: Literal["0.1"] = SCHEMA_VERSION
    run_id: str = Field(min_length=1)
    scenario: str = Field(pattern=r"^S\d+$")
    split: Split
    condition: Condition
    agent: AgentName
    agent_version: str = Field(min_length=1)
    model: str = Field(min_length=1)
    account: Label
    session_id: str = Field(min_length=1)
    rep: int = Field(ge=1)
    turn: int = Field(ge=1)
    seed: int
    started_at: AwareDatetime
    duration_s: float = Field(ge=0)
    tokens: Tokens
    est_cost_usd: float | None = Field(default=None, ge=0)  # not every agent reports one
    config_fingerprint: Sha256
    ruleset_sha256: Sha256 | None = None
    valid: bool
    invalid_reasons: list[InvalidReason] = Field(default_factory=list)
    evaluation: Evaluation | None = None
    hook: HookStats
    permission_denials: int = Field(ge=0)

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.valid == bool(self.invalid_reasons):
            raise ValueError("a turn is valid exactly when it has no invalid_reasons")
        if self.valid and self.evaluation is None:
            raise ValueError("a valid turn needs an evaluation")
        if self.condition.uses_compiled_rules != (self.ruleset_sha256 is not None):
            raise ValueError("ruleset_sha256 is required for K3 and K4 and only for them")
        return self
