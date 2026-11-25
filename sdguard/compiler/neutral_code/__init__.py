"""Code that no compiled Semgrep rule may report.

A Semgrep finding blocks the agent until the code changes, so a rule that reports safe
code changes how the agent works even when it follows every rule. ``service.py`` collects
common safe idioms of small Flask services (parameterized queries with a variable number
of placeholders, secrets from the environment, hashed passwords, verified JWTs, list-form
subprocess calls, sanitized upload paths). Each compiled rule runs against it during
validation; a finding there fails the validation like a missed bad example.

The file is written from general Flask and Python practice, not from any experiment
scenario. It is parsed by Semgrep only, never imported or run.
"""

from pathlib import Path

NEUTRAL_CODE: Path = Path(__file__).parent / "service.py"
