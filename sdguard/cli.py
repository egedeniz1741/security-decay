"""Command-line entry point for sdguard."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from sdguard import __version__
from sdguard.compiler.permissions import merge_claude_settings, plan_claude_code
from sdguard.contracts.rules import RuleSet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdguard",
        description="Security rule compiler and protection ledger for coding agents.",
    )
    parser.add_argument("--version", action="version", version=f"sdguard {__version__}")
    commands = parser.add_subparsers(dest="command")

    permissions = commands.add_parser(
        "permissions", help="write block rules into Claude Code's permission settings"
    )
    permissions.add_argument("--rules", type=Path, required=True, help="compiled rule set (JSON)")
    permissions.add_argument(
        "--settings",
        type=Path,
        default=Path(".claude/settings.json"),
        help="Claude Code settings file to update (default: .claude/settings.json)",
    )
    permissions.add_argument(
        "--state",
        type=Path,
        default=None,
        help="where sdguard records the entries it added "
        "(default: .sdguard/permissions.claude.json next to .claude/)",
    )
    permissions.add_argument(
        "--dry-run", action="store_true", help="print the result instead of writing it"
    )
    return parser


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_atomically(path: Path, text: str) -> None:
    """Write via a temporary file so an interrupted run never leaves a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def run_permissions(rules: Path, settings: Path, state: Path | None, dry_run: bool) -> int:
    # Default state file: <project>/.sdguard/permissions.claude.json next to .claude/.
    state = state or settings.parent.parent / ".sdguard" / "permissions.claude.json"
    try:
        ruleset = RuleSet.model_validate_json(rules.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        print(f"sdguard: cannot load rule set {rules}: {exc}", file=sys.stderr)
        return 2
    try:
        existing = _read_json(settings, {})
        previous = _read_json(state, {}).get("added", [])
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
        print(f"sdguard: cannot read {settings} or {state}: {exc}", file=sys.stderr)
        return 2

    plan = plan_claude_code(ruleset)
    try:
        result = merge_claude_settings(existing, plan, previous)
    except ValueError as exc:
        print(f"sdguard: cannot update {settings}: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(result.settings, indent=2, ensure_ascii=False) + "\n"

    # The report goes to stderr so that --dry-run output can be redirected to a file.
    for entry in plan.deny:
        print(f"deny    {entry:<40} {', '.join(plan.sources[entry])}", file=sys.stderr)
    for entry in result.removed:
        print(f"remove  {entry} (no longer in the rule set)", file=sys.stderr)
    for rule_id in plan.skipped:
        print(f"skip    {rule_id}: permission targets need enforcement 'block'", file=sys.stderr)

    if dry_run:
        print(text, end="")
        return 0
    try:
        _write_atomically(settings, text)
        _write_atomically(state, json.dumps({"added": result.added}, indent=2) + "\n")
    except OSError as exc:
        print(f"sdguard: cannot write {settings}: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {settings}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "permissions":
        return run_permissions(args.rules, args.settings, args.state, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
