"""Validate a compiled Semgrep rule against its good and bad examples.

A Semgrep target is only enforced when ``semgrep --test`` agrees with the annotations
in its test file: every ``# ruleid: <id>`` line (bad example) must be reported and no
``# ok: <id>`` line (good example) may be reported. The result is a ``Validation``
from the rule format contract, so an unverified rule can never be marked as enforced.
"""

import json
import os
import re
import shutil
import subprocess  # noqa: S404  # runs the local semgrep binary with fixed arguments
import sys
from pathlib import Path

from sdguard.contracts.rules import Validation, ValidationStatus

_BAD = re.compile(r"#\s*ruleid:")
_GOOD = re.compile(r"#\s*ok:")
_TIMEOUT_SECONDS = 120


def count_examples(test_path: Path) -> tuple[int, int]:
    """Return (good, bad) example counts from the annotations in a Semgrep test file."""
    text = test_path.read_text(encoding="utf-8")
    return len(_GOOD.findall(text)), len(_BAD.findall(text))


def find_semgrep() -> str | None:
    """Locate the semgrep binary: PATH first, then next to the running interpreter."""
    found = shutil.which("semgrep")
    if found:
        return found
    candidate = Path(sys.executable).parent / "semgrep"
    return str(candidate) if candidate.exists() else None


def validate_semgrep(
    rule_path: Path,
    test_path: Path,
    *,
    attempts: int = 1,
    semgrep: str | None = None,
) -> Validation:
    """Run ``semgrep --test`` for one rule file and turn the outcome into a ``Validation``."""
    good, bad = count_examples(test_path)

    def result(status: ValidationStatus, message: str | None = None) -> Validation:
        return Validation(
            status=status,
            good_examples=good,
            bad_examples=bad,
            attempts=attempts,
            message=message,
        )

    binary = semgrep or find_semgrep()
    if binary is None or not Path(binary).exists():
        return result(ValidationStatus.NOT_ATTEMPTED, "semgrep is not installed")
    if good < 1 or bad < 1:
        return result(
            ValidationStatus.FAILED,
            f"test file needs at least one '# ok:' and one '# ruleid:' example "
            f"(found {good} ok, {bad} ruleid)",
        )

    command = [binary, "--test", "--json", "--config", str(rule_path), str(test_path)]
    env = {**os.environ, "SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0"}
    try:
        completed = subprocess.run(  # noqa: S603  # fixed argument list, no shell
            command, capture_output=True, text=True, timeout=_TIMEOUT_SECONDS, env=env
        )
    except subprocess.TimeoutExpired:
        return result(
            ValidationStatus.FAILED, f"semgrep --test timed out after {_TIMEOUT_SECONDS}s"
        )

    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        detail = (completed.stderr or completed.stdout).strip().splitlines()[-1:] or ["no output"]
        return result(ValidationStatus.FAILED, f"semgrep --test failed: {detail[0]}")

    if report.get("config_with_errors"):
        return result(ValidationStatus.FAILED, "semgrep could not load the rule file")

    problems = _collect_problems(report)
    if problems:
        return result(ValidationStatus.FAILED, "; ".join(problems))
    return result(ValidationStatus.VERIFIED)


def _collect_problems(report: dict[str, object]) -> list[str]:
    """Describe every bad example that was missed and every good example that was flagged."""
    problems: list[str] = []
    results = report.get("results")
    if not isinstance(results, dict) or not results:
        return ["semgrep --test returned no results"]
    for config in results.values():
        for rule_id, check in config.get("checks", {}).items():
            if check.get("errors"):
                problems.append(f"{rule_id}: semgrep reported errors")
            for matches in check.get("matches", {}).values():
                expected = set(matches.get("expected_lines", []))
                reported = set(matches.get("reported_lines", []))
                missed = sorted(expected - reported)
                extra = sorted(reported - expected)
                if missed:
                    problems.append(f"{rule_id}: bad example not detected at line(s) {missed}")
                if extra:
                    problems.append(f"{rule_id}: false alarm at line(s) {extra}")
            if not check.get("passed", False) and not problems:
                problems.append(f"{rule_id}: semgrep --test did not pass")
    return problems
