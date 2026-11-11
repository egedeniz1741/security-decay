import shutil
from pathlib import Path

import pytest

from sdguard.compiler.semgrep_validation import count_examples, find_semgrep, validate_semgrep
from sdguard.contracts.rules import Rule, ValidationStatus

FIXTURES = Path(__file__).parent / "fixtures" / "compiler" / "semgrep"
RULE = FIXTURES / "R-002.yaml"
EXAMPLES = FIXTURES / "R-002.py"

needs_semgrep = pytest.mark.skipif(find_semgrep() is None, reason="semgrep is not installed")

ONLY_FSTRINGS = """
rules:
  - id: R-002
    message: weak rule
    severity: ERROR
    languages: [python]
    pattern: $DB.execute(f"...", ...)
"""

EVERY_EXECUTE = """
rules:
  - id: R-002
    message: too broad
    severity: ERROR
    languages: [python]
    pattern: $DB.execute(...)
"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_examples_are_counted_from_annotations() -> None:
    assert count_examples(EXAMPLES) == (3, 5)


@needs_semgrep
def test_correct_rule_is_verified() -> None:
    validation = validate_semgrep(RULE, EXAMPLES)
    assert validation.status is ValidationStatus.VERIFIED
    assert (validation.good_examples, validation.bad_examples) == (3, 5)
    assert validation.message is None


@needs_semgrep
def test_verified_result_can_be_enforced_in_a_rule() -> None:
    validation = validate_semgrep(RULE, EXAMPLES)
    rule = Rule.model_validate(
        {
            "id": "R-002",
            "source": {
                "file": "AGENTS.md",
                "line": 15,
                "text": "SQL queries must be parameterized.",
            },
            "category": "code",
            "cwe": ["CWE-89"],
            "targets": {
                "semgrep": {
                    "rule_path": "semgrep/R-002.yaml",
                    "test_path": "semgrep/tests/R-002.py",
                }
            },
            "validation": validation.model_dump(),
            "enforcement": "block",
            "coverage": "full",
        }
    )
    assert rule.is_enforced


@needs_semgrep
def test_rule_that_misses_bad_examples_fails(tmp_path: Path) -> None:
    rule = write(tmp_path, "R-002.yaml", ONLY_FSTRINGS)
    validation = validate_semgrep(rule, EXAMPLES)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "bad example not detected" in validation.message


@needs_semgrep
def test_rule_that_flags_good_examples_fails(tmp_path: Path) -> None:
    rule = write(tmp_path, "R-002.yaml", EVERY_EXECUTE)
    validation = validate_semgrep(rule, EXAMPLES)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "false alarm" in validation.message


@needs_semgrep
def test_broken_rule_file_fails(tmp_path: Path) -> None:
    rule = write(tmp_path, "R-002.yaml", "rules: [this is not a rule")
    validation = validate_semgrep(rule, EXAMPLES)
    assert validation.status is ValidationStatus.FAILED


def test_examples_without_good_cases_fail(tmp_path: Path) -> None:
    examples = write(tmp_path, "R-002.py", "# ruleid: R-002\ndb.execute(f'{x}')\n")
    validation = validate_semgrep(RULE, examples, semgrep=find_semgrep() or "semgrep-missing")
    assert validation.status in {ValidationStatus.FAILED, ValidationStatus.NOT_ATTEMPTED}
    if find_semgrep() is not None:
        assert validation.status is ValidationStatus.FAILED


def test_missing_semgrep_is_not_attempted(tmp_path: Path) -> None:
    missing = str(tmp_path / "no-semgrep-here")
    assert shutil.which(missing) is None
    validation = validate_semgrep(RULE, EXAMPLES, semgrep=missing)
    assert validation.status is ValidationStatus.NOT_ATTEMPTED
