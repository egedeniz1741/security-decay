import stat
from pathlib import Path

import pytest

from sdguard.compiler.semgrep_validation import (
    find_semgrep,
    read_annotations,
    rule_ids,
    validate_semgrep,
)
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


def fake_semgrep(tmp_path: Path, stdout: str) -> str:
    script = tmp_path / "fake-semgrep"
    script.write_text(f"#!/bin/sh\nprintf '%s' '{stdout}'\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return str(script)


def test_examples_are_counted_per_rule_id() -> None:
    good, bad = read_annotations(EXAMPLES)
    assert (good["R-002"], bad["R-002"]) == (4, 7)
    assert rule_ids(RULE) == ["R-002"]


@needs_semgrep
def test_correct_rule_is_verified() -> None:
    validation = validate_semgrep(RULE, EXAMPLES)
    assert validation.status is ValidationStatus.VERIFIED, validation.message
    assert (validation.good_examples, validation.bad_examples) == (4, 7)
    assert validation.message is None


@needs_semgrep
def test_command_name_is_resolved_on_path() -> None:
    assert validate_semgrep(RULE, EXAMPLES, semgrep="semgrep").status is ValidationStatus.VERIFIED


@needs_semgrep
def test_verified_result_goes_into_a_partial_rule() -> None:
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
            # Verified on its examples, but known patterns are still missed or over-reported.
            "coverage": "partial",
            "known_gaps": [
                "Queries built step by step (q += name) are not detected.",
                "A variable on the left of % (template % value) is not detected.",
                "False alarm: two constant strings joined with +.",
                "False alarm: a query variable reassigned to a constant before execute.",
            ],
        }
    )
    assert rule.is_enforced


@needs_semgrep
def test_rule_that_misses_bad_examples_fails(tmp_path: Path) -> None:
    validation = validate_semgrep(write(tmp_path, "R-002.yaml", ONLY_FSTRINGS), EXAMPLES)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "bad example not detected" in validation.message


@needs_semgrep
def test_rule_that_flags_good_examples_fails(tmp_path: Path) -> None:
    validation = validate_semgrep(write(tmp_path, "R-002.yaml", EVERY_EXECUTE), EXAMPLES)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "false alarm" in validation.message


@needs_semgrep
def test_broken_rule_file_fails(tmp_path: Path) -> None:
    rule = write(tmp_path, "R-002.yaml", "rules:\n  - id: R-002\n    pattern: [broken\n")
    assert validate_semgrep(rule, EXAMPLES).status is ValidationStatus.FAILED


def test_annotation_with_a_wrong_rule_id_fails(tmp_path: Path) -> None:
    text = EXAMPLES.read_text().replace("# ruleid: R-002", "# ruleid: R-02")
    validation = validate_semgrep(RULE, write(tmp_path, "R-002.py", text))
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "R-02" in validation.message


def test_examples_without_good_cases_fail(tmp_path: Path) -> None:
    examples = write(tmp_path, "R-002.py", "# ruleid: R-002\ndb.execute(f'{x}')\n")
    validation = validate_semgrep(RULE, examples)
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "missing for R-002" in validation.message


def test_missing_test_file_fails(tmp_path: Path) -> None:
    validation = validate_semgrep(RULE, tmp_path / "nope.py")
    assert validation.status is ValidationStatus.FAILED


def test_missing_rule_file_fails(tmp_path: Path) -> None:
    validation = validate_semgrep(tmp_path / "nope.yaml", EXAMPLES)
    assert validation.status is ValidationStatus.FAILED


def test_test_file_that_is_not_utf8_fails(tmp_path: Path) -> None:
    examples = tmp_path / "R-002.py"
    examples.write_bytes(b"\xff\xfe# ruleid: R-002\n")
    assert validate_semgrep(RULE, examples).status is ValidationStatus.FAILED


def test_missing_semgrep_is_not_attempted(tmp_path: Path) -> None:
    validation = validate_semgrep(RULE, EXAMPLES, semgrep=str(tmp_path / "no-semgrep-here"))
    assert validation.status is ValidationStatus.NOT_ATTEMPTED


def test_semgrep_that_cannot_run_is_not_attempted(tmp_path: Path) -> None:
    not_executable = write(tmp_path, "semgrep", "not a program")
    validation = validate_semgrep(RULE, EXAMPLES, semgrep=str(not_executable))
    assert validation.status is ValidationStatus.NOT_ATTEMPTED


@pytest.mark.parametrize("stdout", ["[]", '"text"', "not json"])
def test_unexpected_semgrep_output_fails(tmp_path: Path, stdout: str) -> None:
    validation = validate_semgrep(RULE, EXAMPLES, semgrep=fake_semgrep(tmp_path, stdout))
    assert validation.status is ValidationStatus.FAILED


def test_report_without_the_rule_fails(tmp_path: Path) -> None:
    validation = validate_semgrep(RULE, EXAMPLES, semgrep=fake_semgrep(tmp_path, '{"results": {}}'))
    assert validation.status is ValidationStatus.FAILED
    assert validation.message is not None
    assert "did not test this rule" in validation.message
