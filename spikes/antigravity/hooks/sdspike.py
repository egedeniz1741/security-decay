"""Shared helpers for the Antigravity CLI G0 hook spikes.

Every hook script imports this module. It:
- reads the hook payload from stdin and saves it under ~/sd-spikes/agy/logs/
  (later cleaned and copied to sdguard/tests/fixtures/antigravity/),
- finds unsafe SQL string building in .py files (same patterns as the Claude Code spikes),
- keeps per-conversation counters so a gate cannot loop forever.

Antigravity does not put the event name in the payload, so each hook gets it as argv[1].
"""

import json
import os
import re
import sys
import time
from pathlib import Path

BASE = Path.home() / "sd-spikes" / "agy"
LOG_DIR = Path(os.environ.get("SD_SPIKE_LOG", BASE / "logs"))
STATE_DIR = BASE / "state"

SQL_WORDS = r"(?:SELECT|INSERT|UPDATE|DELETE)\b"
# Double and single quoted strings are separate so the other quote type inside a query
# does not break the match.
DQ = r'"[^"\n]*\b' + SQL_WORDS + r'[^"\n]*"'
SQ = r"'[^'\n]*\b" + SQL_WORDS + r"[^'\n]*'"


def _after_string(op: str) -> re.Pattern[str]:
    return re.compile(rf"(?:{DQ}|{SQ})\s*{op}", re.IGNORECASE)


PATTERNS = [
    ("f-string ile kurulan SQL", re.compile(r"\bf(?:" + DQ + "|" + SQ + ")", re.IGNORECASE)),
    ("% ile biçimlenen SQL", _after_string(r"%")),
    (".format() ile biçimlenen SQL", _after_string(r"\.format\(")),
    ("+ ile birleştirilen SQL", _after_string(r"\+")),
]

SQL_RULE = (
    "Proje kurali: SQL sorgulari parametreli olmali, ornek: "
    'cursor.execute("SELECT * FROM users WHERE email = ?", (email,))'
)


def event_name() -> str:
    return sys.argv[1] if len(sys.argv) > 1 else "unknown"


def read_input(tag: str = "") -> dict:
    """Read the payload from stdin and save it with the event (and tool) name."""
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {"_unparsed_stdin": raw}
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    tool = (data.get("toolCall") or {}).get("name", "none")
    stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000:06d}"
    parts = [stamp, event_name(), tool] + ([tag] if tag else [])
    (LOG_DIR / ("-".join(parts) + ".json")).write_text(
        json.dumps(data, indent=2, ensure_ascii=False)
    )
    return data


def reply(obj: dict) -> int:
    print(json.dumps(obj, ensure_ascii=False))
    return 0


def workspace(data: dict) -> Path:
    paths = data.get("workspacePaths") or []
    return Path(paths[0]) if paths else Path.cwd().parent  # hook cwd is .agents/


def sql_issues(root: Path) -> list[str]:
    issues = []
    for path in sorted(root.rglob("*.py")):
        if ".git" in path.parts or ".agents" in path.parts:
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    issues.append(f"{path.name}:{number}: {label}")
                    break
    return issues


def bump_counter(data: dict, name: str) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    counter = STATE_DIR / f"{data.get('conversationId') or 'unknown'}.{name}"
    count = int(counter.read_text().strip() or 0) if counter.exists() else 0
    count += 1
    counter.write_text(f"{count}\n")
    return count
