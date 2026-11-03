#!/usr/bin/env python3
"""G0 deneme 2: ajan bir Python dosyası yazdıktan sonra SQL sorgusunu kontrol et, açık varsa ajana söyle.

Claude Code bu betiği her Write / Edit / Bash işleminden SONRA (PostToolUse) çalıştırır.
Betik:
1. Gelen JSON'u ~/sd-spikes/logs/ altına kaydeder.
2. Değişen .py dosyalarında güvensiz SQL kalıbı arar
   (f-string, % veya .format() ile kurulan ya da + ile birleştirilen sorgular).
3. Bulursa mesajı stderr'e yazar ve 2 koduyla çıkar. Claude Code bu durumda mesajı ajana gösterir.
   Bulamazsa sessizce 0 ile çıkar.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

LOG_DIR = Path(os.environ.get("SD_SPIKE_LOG", Path.home() / "sd-spikes" / "logs"))

SQL_WORDS = r"(?:SELECT|INSERT|UPDATE|DELETE)\b"
# Çift ve tek tırnaklı stringler ayrı yazılıyor ki sorgunun içindeki diğer tırnak türü eşleşmeyi bozmasın.
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
    name = f"{stamp}-{data.get('hook_event_name', 'unknown')}-{data.get('tool_name', 'none')}.json"
    (LOG_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def find_issues(path: Path) -> list[str]:
    issues = []
    for number, line in enumerate(path.read_text(errors="replace").splitlines(), start=1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                issues.append(f"{path.name}:{number}: {label}: {line.strip()}")
                break
    return issues


RECENT_SECONDS = 60


def changed_files(data: dict) -> list[Path]:
    """Bu araç çağrısında değişmiş olabilecek .py dosyaları.

    Write / Edit: girdideki file_path.
    Bash: komutun hangi dosyaya yazdığını güvenilir şekilde çıkaramıyoruz (ör. `cat >> app.py <<EOF`),
    bu yüzden çalışma klasöründe son 60 saniyede değişen .py dosyalarına bakıyoruz.
    """
    tool_input = data.get("tool_input") or {}
    if data.get("tool_name") == "Bash":
        root = Path(data.get("cwd") or ".")
        now = time.time()
        return [
            p
            for p in root.rglob("*.py")
            if ".git" not in p.parts and now - p.stat().st_mtime <= RECENT_SECONDS
        ]
    path = Path(tool_input.get("file_path", ""))
    return [path] if path.suffix == ".py" and path.is_file() else []


def main() -> int:
    data = json.load(sys.stdin)
    save_input(data)
    issues = []
    for path in changed_files(data):
        issues.extend(find_issues(path))
    if not issues:
        return 0
    message = (
        "sdguard deneme: SQL sorgusu kullanici girdisiyle string olarak kuruluyor "
        "(SQL injection riski).\n"
        + "\n".join(issues)
        + "\nProje kurali: SQL sorgulari parametreli olmali, ornek: "
        'cursor.execute("SELECT * FROM users WHERE username = ?", (username,))'
    )
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
