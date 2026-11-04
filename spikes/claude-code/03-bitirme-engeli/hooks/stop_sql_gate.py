#!/usr/bin/env python3
"""G0 deneme 3: ajan "işim bitti" dediğinde, kodda SQL açığı kaldıysa bitirmesine izin verme.

Claude Code bu betiği ajan cevabını bitirip durmak üzereyken (Stop olayı) çalıştırır.
Betik:
1. Gelen JSON'u ~/sd-spikes/logs/ altına kaydeder.
2. Çalışma klasöründeki tüm .py dosyalarında güvensiz SQL kalıbı arar.
3. Bulursa {"decision": "block", "reason": ...} döndürür: Claude Code ajanı durdurmaz,
   gerekçeyi ajana verip çalışmaya devam ettirir.
4. Sonsuz döngüyü önlemek için aynı oturumda en fazla MAX_BLOCKS kez engeller,
   sonra ajanın durmasına izin verir ve bunu kayda geçirir.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

BASE = Path.home() / "sd-spikes"
LOG_DIR = Path(os.environ.get("SD_SPIKE_LOG", BASE / "logs"))
STATE_DIR = BASE / "state"
MAX_BLOCKS = 3

SQL_WORDS = r"(?:SELECT|INSERT|UPDATE|DELETE)\b"
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


def save_input(data: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = f"{stamp}-{data.get('hook_event_name', 'unknown')}.json"
    (LOG_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def find_issues(root: Path) -> list[str]:
    issues = []
    for path in sorted(root.rglob("*.py")):
        if ".git" in path.parts or ".claude" in path.parts:
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
            for label, pattern in PATTERNS:
                if pattern.search(line):
                    issues.append(f"{path.name}:{number}: {label}: {line.strip()}")
                    break
    return issues


def bump_counter(session_id: str) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    counter = STATE_DIR / f"{session_id or 'unknown'}.stop-blocks"
    count = int(counter.read_text()) if counter.exists() else 0
    count += 1
    counter.write_text(str(count))
    return count


def main() -> int:
    data = json.load(sys.stdin)
    save_input(data)
    issues = find_issues(Path(data.get("cwd") or "."))
    if not issues:
        return 0
    count = bump_counter(data.get("session_id", ""))
    if count > MAX_BLOCKS:
        print(
            f"sdguard deneme: {MAX_BLOCKS} engellemeden sonra durmaya izin verildi, acik hala duruyor.",
            file=sys.stderr,
        )
        return 0
    reason = (
        f"sdguard deneme (engelleme {count}/{MAX_BLOCKS}): Kodda SQL injection acigi var, "
        "bu haliyle isi bitiremezsin.\n"
        + "\n".join(issues)
        + "\nProje kurali: SQL sorgulari parametreli olmali, ornek: "
        'cursor.execute("SELECT * FROM users WHERE email = ?", (email,)). '
        "Aciklari kapat, sonra bitir."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
