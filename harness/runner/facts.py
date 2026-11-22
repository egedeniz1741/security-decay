"""What the session half writes to ``data/raw/<run_id>/``; evaluation and ``turns.jsonl`` read it.

These are runner-internal files, not a shared contract: the turn record
(``sdguard/contracts/turns.py``) is built from them together with the evaluation.
"""

from pydantic import AwareDatetime, Field

from sdguard.contracts._base import _Model
from sdguard.contracts.rules import AgentName, Sha256
from sdguard.contracts.turns import (
    Behavior,
    Condition,
    HookStats,
    InvalidReason,
    Label,
    Split,
    Tokens,
)


class RunMeta(_Model):
    run_id: str
    scenario: str
    scenario_name: str
    split: Split
    condition: Condition
    agent: AgentName
    account: Label
    rep: int = Field(ge=1)
    seed: int
    model: str  # as requested; each turn records the model the agent reported
    image: str
    image_id: str
    expected_agent_version: str
    engine: str  # "podman" or "docker"
    settings_sha256: Sha256
    protected_paths_sha256: Sha256
    prompts_sha256: dict[int, Sha256]
    runner_commit: str  # the repo's HEAD, with "+dirty" for uncommitted changes
    started_at: AwareDatetime


class Preflight(_Model):
    """The init event of a run without login, before any quota is spent."""

    contamination_diff: list[str]
    agent_version: str | None

    @property
    def passed(self) -> bool:
        return not self.contamination_diff


class Smoke(_Model):
    """R24: the condition's permissions are in effect (allowed command ran, denied one did not)."""

    allowed_ran: bool
    denied_blocked: bool

    @property
    def passed(self) -> bool:
        return self.allowed_ran and self.denied_blocked


class TurnFacts(_Model):
    turn: int = Field(ge=1)
    session_id: str | None
    started_at: AwareDatetime
    duration_s: float = Field(ge=0)
    exit_code: int | None
    timed_out: bool
    stopped_after_result: bool  # a background task kept claude running after its answer
    model: str | None  # from the init event
    agent_version: str | None
    tokens: Tokens
    est_cost_usd: float | None
    config_fingerprint: Sha256
    contamination_diff: list[str]
    environment_diff: list[str]  # recorded, does not invalidate
    integrity_changes: list[str]
    invalid_reasons: list[InvalidReason]
    permission_denials: int = Field(ge=0)
    behavior: Behavior
    hook: HookStats
    commit: str
    changed_files: list[str]
    packages_installed: list[str]  # name==version added during the turn
    masked_secrets: int = Field(ge=0)  # token occurrences replaced in logs and files
