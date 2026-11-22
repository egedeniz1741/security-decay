"""The container CLI, Docker or podman, through the subset both understand.

Flags follow harness/docker/README.md. The argument lists are built by pure functions so
they can be tested without a container engine.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum

SETTINGS_IN_CONTAINER = "/etc/sd/settings.json"
TOKEN_ENV = "CLAUDE_CODE_OAUTH_TOKEN"  # noqa: S105  # a variable name, not a token
PODMAN_SECRET = "sd-claude-oauth"  # noqa: S105  # a secret's name, not its value


class LoginSource(StrEnum):
    ENV = "env"  # the runner's own environment, passed by name only
    PODMAN = "podman"  # the podman secret


@dataclass(frozen=True)
class Engine:
    cli: str
    is_podman: bool

    def run(
        self, args: list[str], *, timeout: float | None = None, input: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603  # fixed argument lists, never a shell
            [self.cli, *args], capture_output=True, text=True, timeout=timeout, input=input
        )


def detect(cli: str | None = None) -> Engine:
    """``cli`` or $SD_CONTAINER_CLI, else docker, else podman."""
    path = (
        cli
        or os.environ.get("SD_CONTAINER_CLI")
        or shutil.which("docker")
        or shutil.which("podman")
    )
    if not path:
        raise RuntimeError("neither docker nor podman found")
    # podman's Docker compatibility wrapper answers `--version` as "docker version ..."
    version = subprocess.run([path, "version"], capture_output=True, text=True)  # noqa: S603
    is_podman = "podman" in (version.stdout + os.path.realpath(path)).lower()
    return Engine(path, is_podman)


def agent_run_args(
    engine: Engine,
    *,
    name: str,
    image: str,
    work_dir: str,
    settings_file: str,
    env: dict[str, str],
    login: LoginSource,
) -> list[str]:
    """``run`` arguments for a session's agent container; the token never appears in them."""
    args = [
        "run", "-d", "--name", name,
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", "512", "--memory", "2g",
        "-v", f"{work_dir}:/work",
        "-v", f"{settings_file}:{SETTINGS_IN_CONTAINER}:ro",
    ]  # fmt: skip
    if engine.is_podman:
        # rootless podman: without this the agent user cannot write to the mounted /work
        args += ["--userns", "keep-id:uid=1000,gid=1000"]
    if login is LoginSource.PODMAN:
        args += ["--secret", f"{PODMAN_SECRET},type=env,target={TOKEN_ENV}"]
    else:
        args += ["-e", TOKEN_ENV]
    for key, value in sorted(env.items()):
        args += ["-e", f"{key}={value}"]
    return [*args, image]


def claude_args(
    *,
    prompt: str,
    model: str,
    session_id: str | None,
    permission_mode: str,
    timeout_s: int,
) -> list[str]:
    """The ``claude -p`` command of one turn (02_DENEY_ALTYAPISI.md §2 step 5a)."""
    args = ["timeout", str(timeout_s), "claude", "-p", prompt]
    if session_id:
        args += ["--resume", session_id]
    return [
        *args,
        "--model", model,
        "--settings", SETTINGS_IN_CONTAINER,
        "--permission-mode", permission_mode,
        "--output-format", "stream-json", "--verbose",
    ]  # fmt: skip
