"""Evaluation of a session's turns, and its turn records (02_DENEY_ALTYAPISI.md §2 step d, §4).

    python -m harness.runner evaluate data/raw/<run_id>                  # turns.jsonl
    python -m harness.runner evaluate data/raw/<run_id> --out again.jsonl
    python -m harness.runner compare turns.jsonl again.jsonl            # pilot criterion 3

Each valid turn's commit comes out of the run's git directory and is evaluated from scratch:
- in a fresh evaluation container without network (eval_inside.py): the functional tests on
  one app, every exploit of the turn on its own app;
- Gitleaks counts secrets in the turn's files (pinned image, no network).

The evaluation depends on the commit alone, so two evaluations of a run must agree. Semgrep,
the measurement ledger and hallucinated packages are not built yet and stay null.
Per-check details (failed checks, exploit outcomes, app log) go to ``<out>.details.jsonl``.
"""

import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from harness.runner.container import Engine
from harness.runner.facts import RunMeta, TurnFacts
from harness.runner.record import turn_record
from harness.runner.scenarios import SCENARIOS
from harness.runner.session import REPO, runner_commit
from sdguard.contracts.turns import (
    Evaluation,
    ExploitResult,
    Functional,
    InconclusiveExploit,
    TurnRecord,
    primary_outcome,
)

EVAL_IMAGE = "sd-eval:latest"
GITLEAKS_IMAGE = (
    "ghcr.io/gitleaks/gitleaks:v8.30.1"
    "@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f"
)
EVAL_FLAGS = [
    "--network", "none", "--cap-drop", "ALL", "--read-only",
    "--security-opt", "no-new-privileges",
    "--tmpfs", "/tmp:rw,size=256m,mode=1777",  # noqa: S108  # a tmpfs inside the container
    "--pids-limit", "256", "--memory", "1g",
]  # fmt: skip


def checkout(run_dir: Path, commit: str, dest: Path) -> Path:
    """The turn's files as committed (the agent cannot have changed them since)."""
    archive = subprocess.run(  # noqa: S603
        ["git", f"--git-dir={run_dir / 'repo.git'}", "archive", "--format=tar", commit],  # noqa: S607
        capture_output=True, check=True,
    ).stdout  # fmt: skip
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")
    (dest / "code").mkdir(exist_ok=True)  # no code at all: the app does not start
    return dest


def run_inside(
    engine: Engine, tree: Path, turn: int, scenario: str, app_env: dict[str, str]
) -> dict[str, Any]:
    args = ["run", "--rm", *EVAL_FLAGS, "-v", f"{tree / 'code'}:/src/code:ro"]
    for package in ("harness", "sdguard"):
        args += ["-v", f"{REPO / package}:/opt/sd/{package}:ro"]
    for key, value in sorted(app_env.items()):
        args += ["-e", f"{key}={value}"]
    args += [
        "-w", "/opt/sd", EVAL_IMAGE,
        "/opt/harness/bin/python", "-E", "-s", "-m", "harness.runner.eval_inside",
        "--turn", str(turn), "--scenario", scenario,
    ]  # fmt: skip
    out = engine.run(args, timeout=900)
    if out.returncode != 0:
        raise RuntimeError(f"evaluation of turn {turn} failed: {out.stderr[-1000:]}")
    result: dict[str, Any] = json.loads(out.stdout)
    return result


def secret_findings(engine: Engine, tree: Path) -> list[dict[str, Any]]:
    out = engine.run(
        ["run", "--rm", "--network", "none", "--cap-drop", "ALL", "--read-only",
         "-v", f"{tree}:/scan:ro", GITLEAKS_IMAGE,
         "dir", "/scan", "--no-banner", "--report-format", "json", "--report-path", "-",
         "--exit-code", "0"],
        timeout=300,
    )  # fmt: skip
    if out.returncode != 0:
        raise RuntimeError(f"gitleaks failed: {out.stderr[-500:]}")
    findings: list[dict[str, Any]] = json.loads(out.stdout or "[]")
    return findings


def build_evaluation(inside: dict[str, Any], secrets: int, packages: list[str]) -> Evaluation:
    checks = inside["functional"]
    functional = Functional(passed=sum(1 for c in checks if c["passed"]), total=len(checks))
    exploits: list[ExploitResult] = []
    inconclusive: list[InconclusiveExploit] = []
    for e in inside["exploits"]:
        if e["outcome"] == "inconclusive":
            inconclusive.append(InconclusiveExploit(id=e["id"], cwe=e["cwe"], primary=e["primary"]))
        else:  # the same mapping as harness.exploits.base.Exploit.to_result
            exploits.append(
                ExploitResult(
                    id=e["id"],
                    cwe=e["cwe"],
                    success=e["outcome"] == "success",
                    applicable=e["outcome"] != "not_applicable",
                    primary=e["primary"],
                )
            )
    return Evaluation(
        functional=functional,
        exploits=exploits,
        inconclusive_exploits=inconclusive,
        secure_and_correct=primary_outcome(functional, exploits, inconclusive),
        sast=None,
        ledger=None,
        packages_installed=packages,
        hallucinated_packages=None,
        secrets_in_code=secrets,
    )


def evaluate_run(engine: Engine, run_dir: Path, out: Path, force: bool = False) -> list[TurnRecord]:
    if out.exists() and not force:
        raise FileExistsError(f"{out} exists; pass --force or another --out")
    meta = RunMeta.model_validate_json((run_dir / "run.json").read_text())
    app_env: dict[str, str] = json.loads((run_dir / "app-env.json").read_text())
    scenario = SCENARIOS[meta.scenario]
    evaluator = runner_commit()
    records: list[TurnRecord] = []
    details: list[dict[str, Any]] = []
    for n in range(1, scenario.turns + 1):
        facts_file = run_dir / f"turn-{n}" / "facts.json"
        if not facts_file.exists():
            break  # the session stopped earlier
        facts = TurnFacts.model_validate_json(facts_file.read_text())
        evaluation = None
        if not facts.invalid_reasons:
            with tempfile.TemporaryDirectory(prefix="sd-eval-") as tmp:
                tree = checkout(run_dir, facts.commit, Path(tmp))
                inside = run_inside(engine, tree, n, scenario.baxbench, app_env)
                findings = secret_findings(engine, tree)
            evaluation = build_evaluation(inside, len(findings), facts.packages_installed)
            details.append(
                {
                    "turn": n,
                    "evaluator_commit": evaluator,
                    "app_started": inside["app_started"],
                    "failed_checks": [c for c in inside["functional"] if not c["passed"]],
                    "exploits": inside["exploits"],
                    "secret_rules": sorted(f.get("RuleID", "") for f in findings),
                    "app_log": inside["app_log"],
                }
            )
        records.append(turn_record(meta, facts, evaluation))
    out.write_text("".join(r.model_dump_json() + "\n" for r in records))
    out.with_suffix(".details.jsonl").write_text("".join(json.dumps(d) + "\n" for d in details))
    return records


def compare(a: Path, b: Path) -> list[str]:
    """Turns whose evaluations differ between two evaluations of the same run."""

    def evaluations(path: Path) -> dict[int, Any]:
        records = [TurnRecord.model_validate_json(line) for line in path.read_text().splitlines()]
        return {r.turn: r.evaluation.model_dump() if r.evaluation else None for r in records}

    left, right = evaluations(a), evaluations(b)
    return [
        f"turn {t}: {left.get(t)} != {right.get(t)}"
        for t in sorted(set(left) | set(right))
        if left.get(t) != right.get(t)
    ]
