"""Command-line entry point for sdguard."""

import argparse

from sdguard import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdguard",
        description="Security rule compiler and protection ledger for coding agents.",
    )
    parser.add_argument("--version", action="version", version=f"sdguard {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
