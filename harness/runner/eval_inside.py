"""One turn's evaluation, inside the network-less evaluation container.

    cd /opt/sd && /opt/harness/bin/python -E -s -m harness.runner.eval_inside --turn N ...

The turn's code is mounted read-only at /src/code. The app runs from a copy in /tmp with
BaxBench's Python and the session's environment; the agent's own database and uploads are
not carried over (harness/prompts/credit_card_service/README.md). The functional tests run
against one fresh app, every exploit of the turn against its own fresh app. One JSON object
goes to stdout.

The run refuses to start unless loopback is the only network interface, so exploits cannot
leave the sandbox even if the container was started with a network (CLAUDE.md).
"""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from harness.functional import credit_card_service

APP_PYTHON = "/usr/local/bin/python"  # BaxBench's packages; the evaluators use /opt/harness
APP_PORT = 5000
START_TIMEOUT_S = 20
FUNCTIONAL: dict[str, Callable[[str, int, tuple[str, str]], list[Any]]] = {
    "CreditCardService": credit_card_service.run,
}


def require_loopback_only() -> None:
    names = sorted(name for _, name in socket.if_nameindex())
    if names != ["lo"]:
        raise SystemExit(f"refusing to evaluate: network interfaces {names}, expected only lo")


def _port_open() -> bool:
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", APP_PORT)) == 0


@contextmanager
def app(code: Path, env: dict[str, str], log: list[str]) -> Iterator[bool]:
    """Start a fresh copy of the app; yields whether it opened its port."""
    tmp = Path(tempfile.mkdtemp(prefix="sd-app-"))
    work = tmp / "code"
    shutil.copytree(code, work, ignore=shutil.ignore_patterns("db.sqlite3", "__pycache__"))
    if (work / "uploads").is_dir():
        shutil.rmtree(work / "uploads")
    (work / "uploads").mkdir()
    out = tmp / "app.log"
    with out.open("wb") as sink:
        proc = subprocess.Popen(  # noqa: S603  # fixed argument list, no shell
            [APP_PYTHON, "app.py"],
            cwd=work,
            env={"PATH": os.environ.get("PATH", ""), "HOME": str(tmp), **env},
            stdout=sink,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        started = False
        deadline = time.monotonic() + START_TIMEOUT_S
        while time.monotonic() < deadline and proc.poll() is None:
            if _port_open():
                started = True
                break
            time.sleep(0.2)
        try:
            yield started
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
            for _ in range(50):  # the next app needs the port
                if not _port_open():
                    break
                time.sleep(0.1)
    log.append(out.read_text(errors="replace")[-2000:])
    shutil.rmtree(tmp, ignore_errors=True)


def evaluate(
    code: Path, scenario: str, turn: int, env: dict[str, str], run_exploits: bool
) -> dict[str, Any]:
    base_url = f"http://127.0.0.1:{APP_PORT}"
    admin = (env.get("ADMIN_USERNAME", ""), env.get("ADMIN_PASSWORD", ""))
    logs: list[str] = []
    with app(code, env, logs) as started:
        checks = FUNCTIONAL[scenario](base_url, turn, admin)
    exploits = []
    if run_exploits:
        from harness.exploits import scenarios  # noqa: F401  # registers the exploits
        from harness.exploits.base import Outcome, Target, exploits_for

        for exp in exploits_for(scenario, turn):
            with app(code, env, logs) as up:
                outcome = exp.attempt(Target(base_url)) if up else Outcome.INCONCLUSIVE
            exploits.append(
                {"id": exp.id, "cwe": exp.cwe, "primary": exp.primary, "outcome": outcome.value}
            )
    return {
        "turn": turn,
        "app_started": started,
        "functional": [c.__dict__ for c in checks],
        "exploits": exploits,
        "app_log": logs[0] if logs else "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--scenario", default="CreditCardService", choices=sorted(FUNCTIONAL))
    parser.add_argument("--code", type=Path, default=Path("/src/code"))
    parser.add_argument("--no-exploits", action="store_true")
    args = parser.parse_args(argv)
    require_loopback_only()
    keys = ("APP_SECRET", "ADMIN_USERNAME", "ADMIN_PASSWORD")
    env = {k: os.environ[k] for k in keys if k in os.environ}
    result = evaluate(args.code, args.scenario, args.turn, env, not args.no_exploits)
    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
