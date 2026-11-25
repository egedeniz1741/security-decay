"""Shapes of the model's answers, sent as ``--json-schema`` and checked again locally.

These are internal to the compiler, not a contract between components: the contract is
the ``RuleSet`` the compiler writes (``sdguard/contracts/rules.py``).
"""

from typing import Literal

from pydantic import Field

from sdguard.contracts._base import _Model
from sdguard.contracts.rules import CweId, RuleCategory

CoverageClaim = Literal["full", "partial"]


class ClassifiedRule(_Model):
    source_line: int = Field(ge=1, description="line number of the candidate it comes from")
    text: str = Field(min_length=1, description="one atomic rule, as a short imperative")
    category: RuleCategory
    cwe: list[CweId] = Field(default_factory=list, max_length=3)


class Classification(_Model):
    rules: list[ClassifiedRule]
    not_security: list[int] = Field(
        default_factory=list, description="lines of candidates that are not security rules"
    )


class ToolCall(_Model):
    """A tool call an agent might make, used as a good or bad example of a deny rule."""

    tool: Literal["Read", "Grep", "Glob", "Edit", "Write", "Bash"]
    target: str = Field(
        min_length=1,
        description="file path relative to the project root for file tools, "
        "the full command line for Bash",
    )


class ActionTranslation(_Model):
    claude_code_deny: list[str] = Field(min_length=1)
    antigravity_deny: list[str] = Field(default_factory=list)
    must_deny: list[ToolCall] = Field(min_length=1, description="bad examples")
    must_allow: list[ToolCall] = Field(min_length=1, description="good examples")
    coverage: CoverageClaim
    known_gaps: list[str] = Field(default_factory=list)


class CodeTranslation(_Model):
    semgrep_rule: str = Field(min_length=1, description="the complete Semgrep YAML file")
    semgrep_test: str = Field(min_length=1, description="the annotated Python test file")
    coverage: CoverageClaim
    known_gaps: list[str] = Field(default_factory=list)


class BehaviorTranslation(_Model):
    test_file: str = Field(min_length=1, description="the complete pytest file")
    secure_app: str = Field(min_length=1, description="app.py of a secure reference app")
    insecure_apps: list[str] = Field(
        min_length=1, max_length=3, description="app.py of insecure reference apps"
    )
    coverage: CoverageClaim
    known_gaps: list[str] = Field(default_factory=list)


Translation = ActionTranslation | CodeTranslation | BehaviorTranslation
