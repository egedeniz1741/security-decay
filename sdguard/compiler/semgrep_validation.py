"""Validate a compiled Semgrep rule against its good and bad examples.

A Semgrep target is only enforced when ``semgrep --test`` agrees with the annotations
in its test file: every ``# ruleid: <id>`` line (bad example) must be reported and no
``# ok: <id>`` line (good example) may be reported. Only annotations that name a rule of
the rule file count, so a typo such as ``# ruleid: R-02`` cannot make an untested rule
look tested. The result is a ``Validation`` from the rule format contract, so an
unverified rule can never be marked as enforced.
"""

import json
import os
import re
import shutil
import subprocess  # noqa: S404  # runs the local semgrep binary with fixed arguments
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sdguard.contracts.rules import Validation, ValidationStatus

# "# ruleid: R-002" or "# ok: R-002, R-003". todoruleid/todook are known gaps, not examples.
_ANNOTATION = re.compile(r"#\s*(?P<kind>ruleid|ok)\s*:\s*(?P<ids>[\w.\-]+(?:\s*,\s*[\w.\-]+)*)")
# Rule ids in a Semgrep rule file ("- id: R-002"). A light parse is enough here:
# semgrep itself rejects a malformed file, and the report is cross-checked below.
_RULE_ID = re.compile(r"^\s*-\s*id\s*:\s*['\"]?(?P<id>[\w.\-]+)", re.MULTILINE)
_TIMEOUT_SECONDS = 120


def read_annotations(test_path: Path) -> tuple[Counter[str], Counter[str]]:
    """Return (good, bad) example counts per rule id from a Semgrep test file."""
    good: Counter[str] = Counter()
    bad: Counter[str] = Counter()
    for match in _ANNOTATION.finditer(test_path.read_text(encoding="utf-8")):
        target = bad if match["kind"] == "ruleid" else good
        for rule_id in match["ids"].split(","):
            target[rule_id.strip()] += 1
    return good, bad


def rule_ids(rule_path: Path) -> list[str]:
    return [match["id"] for match in _RULE_ID.finditer(rule_path.read_text(encoding="utf-8"))]


def find_semgrep(name: str = "semgrep") -> str | None:
    """Resolve a command name or path: PATH first, then next to the running interpreter."""
    found = shutil.which(name)
    if found:
        return found
    candidate = Path(sys.executable).parent / name
    return str(candidate) if candidate.is_file() else None


def validate_semgrep(
    rule_path: Path,
    test_path: Path,
    *,
    attempts: int = 1,
    semgrep: str | None = None,
) -> Validation:
    """Run ``semgrep --test`` for one rule file and turn the outcome into a ``Validation``."""
    good = bad = 0

    def result(status: ValidationStatus, message: str | None = None) -> Validation:
        return Validation(
            status=status,
            good_examples=good,
            bad_examples=bad,
            attempts=attempts,
            message=message,
        )

    try:
        ids = rule_ids(rule_path)
        good_by_id, bad_by_id = read_annotations(test_path)
    except (OSError, UnicodeDecodeError) as exc:
        return result(ValidationStatus.FAILED, f"cannot read the rule or test file: {exc}")
    if not ids:
        return result(ValidationStatus.FAILED, "the rule file names no rule id")

    good = sum(good_by_id[i] for i in ids)
    bad = sum(bad_by_id[i] for i in ids)
    unknown = sorted((set(good_by_id) | set(bad_by_id)) - set(ids))
    if unknown:
        return result(
            ValidationStatus.FAILED,
            f"test file annotates rule ids that are not in the rule file: {', '.join(unknown)}",
        )
    missing = [i for i in ids if good_by_id[i] < 1 or bad_by_id[i] < 1]
    if missing:
        return result(
            ValidationStatus.FAILED,
            "every rule needs at least one '# ok:' and one '# ruleid:' example; "
            f"missing for {', '.join(missing)}",
        )

    binary = find_semgrep(semgrep or "semgrep")
    if binary is None:
        return result(ValidationStatus.NOT_ATTEMPTED, "semgrep is not installed")

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
    except OSError as exc:
        return result(ValidationStatus.NOT_ATTEMPTED, f"semgrep could not be started: {exc}")

    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError:
        report = None
    if not isinstance(report, dict):
        detail = (completed.stderr or completed.stdout).strip().splitlines()[-1:] or ["no output"]
        return result(
            ValidationStatus.FAILED,
            f"semgrep --test failed (exit {completed.returncode}): {detail[0]}",
        )
    if report.get("config_with_errors"):
        return result(ValidationStatus.FAILED, "semgrep could not load the rule file")

    problems = _collect_problems(report, ids)
    if problems:
        return result(ValidationStatus.FAILED, "; ".join(problems))
    if completed.returncode != 0:
        return result(ValidationStatus.FAILED, f"semgrep --test exited with {completed.returncode}")
    return result(ValidationStatus.VERIFIED)


def _collect_problems(report: dict[str, Any], ids: list[str]) -> list[str]:
    """Describe missed bad examples, flagged good examples and rules semgrep did not test."""
    problems: list[str] = []
    checks: dict[str, Any] = {}
    results = report.get("results")
    if isinstance(results, dict):
        for config in results.values():
            if isinstance(config, dict) and isinstance(config.get("checks"), dict):
                checks.update(config["checks"])

    for rule_id in ids:
        check = checks.get(rule_id)
        if not isinstance(check, dict):
            problems.append(f"{rule_id}: semgrep did not test this rule")
            continue
        if check.get("errors"):
            problems.append(f"{rule_id}: semgrep reported errors")
        expected_any = False
        matches = check.get("matches")
        for match in (matches or {}).values() if isinstance(matches, dict) else []:
            expected = set(match.get("expected_lines", []))
            reported = set(match.get("reported_lines", []))
            expected_any = expected_any or bool(expected)
            missed = sorted(expected - reported)
            extra = sorted(reported - expected)
            if missed:
                problems.append(f"{rule_id}: bad example not detected at line(s) {missed}")
            if extra:
                problems.append(f"{rule_id}: false alarm at line(s) {extra}")
        if not expected_any:
            problems.append(f"{rule_id}: semgrep found no '# ruleid:' example for this rule")
        if not check.get("passed", False) and not problems:
            problems.append(f"{rule_id}: semgrep --test did not pass")
    return problems
