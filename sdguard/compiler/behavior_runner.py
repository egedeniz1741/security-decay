"""Where compiled behavior tests are validated.

A behavior rule compiles to a pytest file and reference applications, all written by the
LLM. Validating it means running that code, so it never runs directly on the developer's
machine (docs/plan/01_MIMARI.md §2.1, CLAUDE.md):

- ``DockerRunner`` (default) runs the validation in a container with no network, no
  capabilities and a read-only root file system. The sdguard package is mounted read-only;
  the image only needs Python, pydantic, pytest and the app's libraries
  (``docker/sdguard-validate.Containerfile``).
- ``LocalRunner`` runs it in the current process tree, but only when the process is already
  network-less (only the ``lo`` interface): inside such a container, or in the tests.
- ``DisabledRunner`` does not run anything; behavior rules stay unverified, hence advice.

Every runner returns a ``Validation``; an environment problem (no Docker, missing image)
is ``not_attempted``, never ``verified``.
"""

import json
import shutil
import socket
import subprocess  # noqa: S404  # runs docker with a fixed argument list
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

import sdguard
from sdguard.compiler.pytest_validation import _TIMEOUT_SECONDS, validate_pytest
from sdguard.contracts.rules import Validation, ValidationStatus

SANDBOX_HINT = (
    "behavior tests are written by the LLM and only run without network; "
    "use --behavior-runner docker"
)


def non_loopback_interfaces() -> list[str]:
    return sorted(name for _, name in socket.if_nameindex() if name != "lo")


def _not_attempted(message: str, good: int, bad: int, attempts: int) -> Validation:
    return Validation(
        status=ValidationStatus.NOT_ATTEMPTED,
        good_examples=good,
        bad_examples=bad,
        attempts=attempts,
        message=message,
    )


class BehaviorRunner(Protocol):
    def validate(
        self, test: Path, secure: Sequence[Path], insecure: Sequence[Path], *, attempts: int
    ) -> Validation: ...


@dataclass(frozen=True)
class DisabledRunner:
    reason: str = "behavior validation was turned off (--behavior-runner none)"

    def validate(
        self, test: Path, secure: Sequence[Path], insecure: Sequence[Path], *, attempts: int
    ) -> Validation:
        return _not_attempted(self.reason, len(secure), len(insecure), attempts)


@dataclass(frozen=True)
class LocalRunner:
    """Run in this process tree; refuses unless the network is already gone."""

    require_isolation: bool = True
    timeout: int = _TIMEOUT_SECONDS

    def validate(
        self, test: Path, secure: Sequence[Path], insecure: Sequence[Path], *, attempts: int
    ) -> Validation:
        if self.require_isolation and (interfaces := non_loopback_interfaces()):
            return _not_attempted(
                f"network interfaces present ({', '.join(interfaces)}); {SANDBOX_HINT}",
                len(secure),
                len(insecure),
                attempts,
            )
        return validate_pytest(test, secure, insecure, attempts=attempts, timeout=self.timeout)


@dataclass(frozen=True)
class DockerRunner:
    """Run ``sdguard.compiler.pytest_validation`` in a network-less container.

    All paths must lie inside ``work_dir``, which is mounted read-only at ``/work``.
    """

    work_dir: Path
    image: str = "sdguard-validate:latest"
    cli: str = "docker"
    timeout: int = _TIMEOUT_SECONDS

    def command(
        self, test: Path, secure: Sequence[Path], insecure: Sequence[Path], *, attempts: int
    ) -> list[str]:
        root = self.work_dir.resolve()
        package = Path(sdguard.__file__).resolve().parent

        def inside(path: Path) -> str:
            return "/work/" + path.resolve().relative_to(root).as_posix()

        return [
            self.cli, "run", "--rm",
            "--network", "none",
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--read-only",
            "--tmpfs", "/tmp:rw,size=256m,mode=1777",  # noqa: S108  # inside the container
            "--pids-limit", "256",
            "--memory", "1g",
            "--user", "65534:65534",
            "-v", f"{root}:/work:ro",
            "-v", f"{package}:/opt/sdguard-src/sdguard:ro",
            "-e", "PYTHONPATH=/opt/sdguard-src",
            "-e", "PYTHONDONTWRITEBYTECODE=1",
            "-e", "HOME=/tmp",
            self.image,
            "python", "-P", "-m", "sdguard.compiler.pytest_validation", inside(test),
            "--secure", *[inside(p) for p in secure],
            "--insecure", *[inside(p) for p in insecure],
            "--attempts", str(attempts),
            "--timeout", str(self.timeout),
        ]  # fmt: skip

    def validate(
        self, test: Path, secure: Sequence[Path], insecure: Sequence[Path], *, attempts: int
    ) -> Validation:
        good, bad = len(secure), len(insecure)
        cli = shutil.which(self.cli)
        if cli is None:
            return _not_attempted(f"{self.cli} was not found; {SANDBOX_HINT}", good, bad, attempts)
        command = self.command(test, secure, insecure, attempts=attempts)
        command[0] = cli
        # The container's unprivileged user must be able to enter the mounted folder; it
        # holds only the attempt's generated files (see compile._readable).
        self.work_dir.chmod(0o755)
        budget = self.timeout * (good + bad) + 60
        try:
            completed = subprocess.run(  # noqa: S603  # fixed argument list, no shell
                command, capture_output=True, text=True, timeout=budget
            )
        except subprocess.TimeoutExpired:
            return Validation(
                status=ValidationStatus.FAILED,
                good_examples=good,
                bad_examples=bad,
                attempts=attempts,
                message=f"the validation container did not finish within {budget}s",
            )
        except OSError as exc:
            return _not_attempted(f"{self.cli} could not be started: {exc}", good, bad, attempts)
        lines = completed.stdout.strip().splitlines()
        try:
            return Validation.model_validate(json.loads(lines[-1]))
        except (IndexError, json.JSONDecodeError, ValidationError):
            detail = (completed.stderr or completed.stdout).strip().splitlines()[-1:] or [""]
            return _not_attempted(
                f"the validation container failed (exit {completed.returncode}): {detail[0][:300]}",
                good,
                bad,
                attempts,
            )
