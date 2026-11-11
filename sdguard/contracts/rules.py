"""Rule format produced by the compiler (owner: Ege).

The compiler reads security rules from agent instruction files (AGENTS.md, CLAUDE.md)
and writes one ``RuleSet``. The guard engine, the agent adapters and the CI action read it.

Design rules encoded here (docs/plan/01_MIMARI.md §1, findings of the G0 spikes):
- A rule that could not be verified with good and bad examples is never enforced.
- A vague rule can only be advice.
- A rule that is enforced only in part must say what it misses (``known_gaps``).
"""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

SCHEMA_VERSION: Literal["0.1"] = "0.1"


def _inside_project(path: str) -> str:
    """Reject absolute paths and paths that climb out with ``..``."""
    if path.startswith(("/", "\\")) or ".." in path.replace("\\", "/").split("/"):
        raise ValueError("path must be relative and must not contain '..'")
    return path


RuleId = Annotated[str, Field(pattern=r"^R-\d{3,}$")]
CweId = Annotated[str, Field(pattern=r"^CWE-\d+$")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
RelativePath = Annotated[str, Field(min_length=1), AfterValidator(_inside_project)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AgentName(StrEnum):
    CLAUDE_CODE = "claude-code"
    ANTIGRAVITY = "antigravity"


class RuleCategory(StrEnum):
    """What kind of thing the rule constrains."""

    ACTION = "action"  # what the agent may do: "do not read .env"
    CODE = "code"  # what the code must look like: "SQL queries must be parameterized"
    BEHAVIOR = "behavior"  # what the running app must do: "users only see their own orders"
    VAGUE = "vague"  # cannot be checked: "validate inputs"


class Enforcement(StrEnum):
    """What happens when the rule is violated."""

    BLOCK = "block"  # deny the tool call, or do not let the agent finish the turn
    WARN = "warn"  # tell the agent, let it continue
    ADVISE = "advise"  # only add the rule text to the agent's context


class ValidationStatus(StrEnum):
    VERIFIED = "verified"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class Coverage(StrEnum):
    """How much of the written rule the compiled checks really enforce."""

    FULL = "full"
    PARTIAL = "partial"
    NONE = "none"


class SourceRef(_Model):
    """Where the rule was written."""

    file: RelativePath
    line: int = Field(ge=1)
    text: str = Field(min_length=1)


class PermissionTarget(_Model):
    """Deny rules for one agent's own permission system."""

    agent: AgentName
    deny: list[str] = Field(min_length=1)


class SemgrepTarget(_Model):
    rule_path: RelativePath
    test_path: RelativePath


class PytestTarget(_Model):
    test_path: RelativePath


class Targets(_Model):
    """Artifacts the rule was compiled to. Paths are relative to the ``.sdguard/`` folder."""

    permissions: list[PermissionTarget] = Field(default_factory=list)
    semgrep: SemgrepTarget | None = None
    pytest: PytestTarget | None = None

    @property
    def is_empty(self) -> bool:
        return not self.permissions and self.semgrep is None and self.pytest is None


class Validation(_Model):
    """Result of checking the compiled artifacts against good and bad examples."""

    status: ValidationStatus
    good_examples: int = Field(default=0, ge=0)
    bad_examples: int = Field(default=0, ge=0)
    attempts: int = Field(default=0, ge=0)
    message: str | None = None

    @model_validator(mode="after")
    def _verified_needs_examples(self) -> Self:
        if self.status is ValidationStatus.VERIFIED and (
            self.good_examples < 1 or self.bad_examples < 1
        ):
            raise ValueError("a verified rule needs at least one good and one bad example")
        return self


class CompiledBy(_Model):
    agent: AgentName
    model: str = Field(min_length=1)
    compiled_at: AwareDatetime


class Rule(_Model):
    id: RuleId
    source: SourceRef
    category: RuleCategory
    cwe: list[CweId] = Field(default_factory=list)
    targets: Targets = Field(default_factory=Targets)
    validation: Validation
    enforcement: Enforcement
    coverage: Coverage
    known_gaps: list[str] = Field(default_factory=list)

    @property
    def is_enforced(self) -> bool:
        return self.enforcement is not Enforcement.ADVISE

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.category is RuleCategory.VAGUE and self.is_enforced:
            raise ValueError("a vague rule can only be advice")
        if self.is_enforced:
            if self.targets.is_empty:
                raise ValueError("an enforced rule needs at least one compiled target")
            if self.validation.status is not ValidationStatus.VERIFIED:
                raise ValueError("a rule that is not verified must not be enforced")
            if self.coverage is Coverage.NONE:
                raise ValueError("an enforced rule cannot have coverage 'none'")
        elif self.coverage is not Coverage.NONE:
            raise ValueError("an advice-only rule enforces nothing: coverage must be 'none'")
        if self.coverage is Coverage.PARTIAL and not self.known_gaps:
            raise ValueError("partial coverage must list what is not covered in known_gaps")
        return self


class SourceFile(_Model):
    """An instruction file the rules were read from, pinned by content hash."""

    path: RelativePath
    sha256: Sha256


class RuleSet(_Model):
    """Everything the compiler produced for one project."""

    schema_version: Literal["0.1"] = SCHEMA_VERSION
    sources: list[SourceFile] = Field(min_length=1)
    compiled_by: CompiledBy
    rules: list[Rule]

    @model_validator(mode="after")
    def _check_rules(self) -> Self:
        ids = [rule.id for rule in self.rules]
        duplicates = sorted({rule_id for rule_id in ids if ids.count(rule_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate rule ids: {', '.join(duplicates)}")
        known_files = {source.path for source in self.sources}
        unknown = sorted({r.source.file for r in self.rules if r.source.file not in known_files})
        if unknown:
            raise ValueError(f"rules refer to files missing from sources: {', '.join(unknown)}")
        return self

    @property
    def enforced(self) -> list[Rule]:
        return [rule for rule in self.rules if rule.is_enforced]

    @property
    def advisory(self) -> list[Rule]:
        return [rule for rule in self.rules if not rule.is_enforced]


def ruleset_json_schema() -> dict[str, object]:
    """JSON Schema of ``RuleSet``, used as the structured-output schema for the compiler."""
    return RuleSet.model_json_schema()
