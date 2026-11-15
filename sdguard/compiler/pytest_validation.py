"""Validate a compiled behavior test against secure and insecure reference applications.

A behavior rule ("a user only sees their own orders") cannot be checked by looking at
code patterns; it compiles to a pytest file that exercises the running application.
The test is only trusted when it tells the two kinds of reference application apart:

- on every **secure** reference application all tests pass (good examples), and
- on every **insecure** one at least one test fails **with an assertion** (bad examples).

A test that crashes on the insecure application has not shown that it detects the
weakness, so a crash does not count as detection.

Running the validation executes the compiled test and the reference applications. The
compiled test comes from an LLM, so in the experiment this must run inside the
network-less container, never directly on a developer machine.
"""

import json
import os
import subprocess  # noqa: S404  # runs pytest with fixed arguments
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from sdguard.contracts.rules import Validation, ValidationStatus
from sdguard.testing import APP_DIR_ENV, RESULT_FILE_ENV

_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class AppRun:
    """Outcome of the compiled test file against one reference application."""

    app_dir: Path
    outcomes: dict[str, str] = field(default_factory=dict)  # test id -> passed/assertion/error
    problem: str | None = None  # the run itself failed (timeout, collection error, no tests)

    @property
    def all_passed(self) -> bool:
        return self.problem is None and all(v == "passed" for v in self.outcomes.values())

    @property
    def detected(self) -> bool:
        return self.problem is None and "assertion" in self.outcomes.values()

    def tests_with(self, outcome: str) -> list[str]:
        return sorted(t.rsplit("::", 1)[-1] for t, v in self.outcomes.items() if v == outcome)


def run_against(test_path: Path, app_dir: Path, *, timeout: int = _TIMEOUT_SECONDS) -> AppRun:
    """Run the compiled test file against one application in a separate pytest process."""
    if not (app_dir / "app.py").is_file():
        return AppRun(app_dir, problem=f"{app_dir} has no app.py")
    with tempfile.TemporaryDirectory(prefix="sdguard-pytest-") as tmp:
        work = Path(tmp)
        (work / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")  # ignore repo config
        result_file = work / "result.json"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "sdguard.testing",
            "-p",
            "no:cacheprovider",
            "-c",
            str(work / "pytest.ini"),
            "--rootdir",
            str(work),
            str(test_path.resolve()),
        ]
        env = {
            **os.environ,
            APP_DIR_ENV: str(app_dir.resolve()),
            RESULT_FILE_ENV: str(result_file),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        try:
            completed = subprocess.run(  # noqa: S603  # fixed argument list, no shell
                command, cwd=work, capture_output=True, text=True, timeout=timeout, env=env
            )
        except subprocess.TimeoutExpired:
            return AppRun(app_dir, problem=f"pytest timed out after {timeout}s")
        except OSError as exc:
            return AppRun(app_dir, problem=f"pytest could not be started: {exc}")
        try:
            data = json.loads(result_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            tail = (completed.stdout + completed.stderr).strip().splitlines()[-1:] or ["no output"]
            return AppRun(app_dir, problem=f"pytest did not report results: {tail[0]}")

    outcomes = data.get("outcomes") if isinstance(data, dict) else None
    if not isinstance(outcomes, dict):
        return AppRun(app_dir, problem="pytest reported results in an unexpected format")
    if data.get("collect_errors"):
        return AppRun(app_dir, outcomes, problem="the test file could not be collected")
    if not outcomes:
        return AppRun(app_dir, problem="the test file contains no tests")
    return AppRun(app_dir, {str(k): str(v) for k, v in outcomes.items()})


def validate_pytest(
    test_path: Path,
    secure_apps: Sequence[Path],
    insecure_apps: Sequence[Path],
    *,
    attempts: int = 1,
    timeout: int = _TIMEOUT_SECONDS,
) -> Validation:
    """Check that the compiled test passes every secure app and catches every insecure one."""
    good, bad = len(secure_apps), len(insecure_apps)

    def result(status: ValidationStatus, message: str | None = None) -> Validation:
        return Validation(
            status=status,
            good_examples=good,
            bad_examples=bad,
            attempts=attempts,
            message=message,
        )

    if not test_path.is_file():
        return result(ValidationStatus.FAILED, f"test file {test_path} does not exist")
    if good < 1 or bad < 1:
        return result(
            ValidationStatus.FAILED,
            "needs at least one secure and one insecure reference application "
            f"(got {good} secure, {bad} insecure)",
        )

    problems: list[str] = []
    for app_dir in secure_apps:
        run = run_against(test_path, app_dir, timeout=timeout)
        if run.problem:
            problems.append(f"secure app {app_dir.name}: {run.problem}")
        elif not run.all_passed:
            failing = run.tests_with("assertion") + run.tests_with("error")
            problems.append(f"secure app {app_dir.name}: false alarm in {', '.join(failing)}")
    for app_dir in insecure_apps:
        run = run_against(test_path, app_dir, timeout=timeout)
        if run.problem:
            problems.append(f"insecure app {app_dir.name}: {run.problem}")
        elif not run.detected:
            crashed = run.tests_with("error")
            detail = f"; crashed instead: {', '.join(crashed)}" if crashed else ""
            problems.append(f"insecure app {app_dir.name}: weakness not detected{detail}")

    if problems:
        return result(ValidationStatus.FAILED, "; ".join(problems))
    return result(ValidationStatus.VERIFIED)
