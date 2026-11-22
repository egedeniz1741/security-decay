"""Command line: ``python -m harness.runner <command>``.

    session   run one session, write data/raw/<run_id>/, then evaluate it
    expect    record a condition's expected init fields (harness/conditions/<K>/expected.json)
    evaluate  evaluate a finished session again and write its turn records
    compare   compare two evaluations of the same session (pilot criterion 3)

The login token comes from $CLAUDE_CODE_OAUTH_TOKEN if set, otherwise from the podman secret
``sd-claude-oauth`` (harness/docker/README.md).
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from harness.runner.container import PODMAN_SECRET, TOKEN_ENV, LoginSource, detect
from harness.runner.evaluate import compare, evaluate_run
from harness.runner.scenarios import PROMPTS_DIR, SCENARIOS
from harness.runner.session import DATA_DIR, Config, Session, record_expected
from sdguard.contracts.turns import Condition

AGENT_CONTAINERFILE = Path(__file__).resolve().parents[1] / "docker" / "agent-claude.Containerfile"


def pinned_claude_version() -> str:
    match = re.search(r"^ARG CLAUDE_CODE_VERSION=(\S+)$", AGENT_CONTAINERFILE.read_text(), re.M)
    if not match:
        raise RuntimeError(f"no CLAUDE_CODE_VERSION in {AGENT_CONTAINERFILE}")
    return match.group(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m harness.runner")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("session", "expect"):
        p = sub.add_parser(name)
        p.add_argument("--condition", required=True, choices=[c.value for c in Condition])
        p.add_argument("--account", required=True, help="pseudonymous label, e.g. acct-a")
        p.add_argument("--scenario", default="S1", choices=sorted(SCENARIOS))
        p.add_argument("--rep", type=int, default=1)
        p.add_argument("--seed", type=int, default=0)
        p.add_argument("--model", default="claude-sonnet-5-5", help="full model id")
        p.add_argument("--image", help="default: sd-agent-claude:<pinned version>")
        p.add_argument("--prompts-dir", type=Path, default=PROMPTS_DIR)
        p.add_argument("--out", type=Path, default=DATA_DIR)
        p.add_argument("--turn-timeout", type=int, default=1500, help="seconds per turn")
    sub.choices["session"].add_argument("--no-evaluate", action="store_true")
    ev = sub.add_parser("evaluate")
    ev.add_argument("run_dir", type=Path)
    ev.add_argument("--out", type=Path, help="default: <run_dir>/turns.jsonl")
    ev.add_argument("--force", action="store_true", help="overwrite --out")
    cmp = sub.add_parser("compare")
    cmp.add_argument("a", type=Path)
    cmp.add_argument("b", type=Path)
    args = parser.parse_args(argv)

    if args.command == "compare":
        diffs = compare(args.a, args.b)
        print("\n".join(diffs) or "evaluations agree")
        return 1 if diffs else 0
    engine = detect()
    if args.command == "evaluate":
        records = evaluate_run(
            engine, args.run_dir, args.out or args.run_dir / "turns.jsonl", args.force
        )
        print(f"{len(records)} turn records")
        return 0
    if os.environ.get(TOKEN_ENV):
        login = LoginSource.ENV
    elif engine.is_podman and engine.run(["secret", "inspect", PODMAN_SECRET]).returncode == 0:
        login = LoginSource.PODMAN
    else:
        parser.error(f"no login: set {TOKEN_ENV} or create the podman secret {PODMAN_SECRET}")
    version = pinned_claude_version()
    cfg = Config(
        scenario=SCENARIOS[args.scenario],
        condition=Condition(args.condition),
        rep=args.rep,
        seed=args.seed,
        account=args.account,
        model=args.model,
        image=args.image or f"sd-agent-claude:{version}",
        expected_version=version,
        engine=engine,
        login=login,
        out_root=args.out.resolve(),
        prompts_dir=args.prompts_dir.resolve(),
        turn_timeout_s=args.turn_timeout,
    )
    if args.command == "expect":
        print(json.dumps(record_expected(cfg), indent=2, sort_keys=True))
        return 0
    status = Session(cfg).run()
    run_dir = cfg.out_root / cfg.run_id
    print(f"{cfg.run_id}: {status.state} ({status.turns_completed} turns) {status.detail}")
    if status.turns_completed and not args.no_evaluate:
        records = evaluate_run(engine, run_dir, run_dir / "turns.jsonl")
        print(f"{len(records)} turn records in {run_dir / 'turns.jsonl'}")
    print(f"output: {run_dir}")
    return 0 if status.state == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
