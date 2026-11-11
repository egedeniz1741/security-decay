"""Command-line entry point for sdguard."""

import argparse
import json
import sys
from pathlib import Path

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
        "--dry-run", action="store_true", help="print the result instead of writing it"
    )
    return parser


def run_permissions(rules: Path, settings: Path, dry_run: bool) -> int:
    try:
        ruleset = RuleSet.model_validate_json(rules.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as exc:
        print(f"sdguard: cannot load rule set {rules}: {exc}", file=sys.stderr)
        return 2
    try:
        existing = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
    except json.JSONDecodeError as exc:
        print(f"sdguard: {settings} is not valid JSON: {exc}", file=sys.stderr)
        return 2

    plan = plan_claude_code(ruleset)
    merged = merge_claude_settings(existing, plan)
    text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"

    for entry in plan.deny:
        print(f"deny  {entry:<40} {', '.join(plan.sources[entry])}")
    for rule_id in plan.skipped:
        print(f"skip  {rule_id}: permission targets need enforcement 'block'")

    if dry_run:
        print(text, end="")
        return 0
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(text, encoding="utf-8")
    print(f"wrote {settings}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "permissions":
        return run_permissions(args.rules, args.settings, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
