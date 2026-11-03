#!/usr/bin/env python3
"""G0 deneme 1: ajanın .env dosyasına erişimini PreToolUse hook'u ile engelle.

Claude Code bu betiğe her araç çağrısından önce stdin üzerinden JSON gönderir.
Betik iki iş yapar:
1. Gelen JSON'u ~/sd-spikes/logs/ altına kaydeder (sonra fixture olarak kullanılacak).
2. Araç çağrısı .env dosyasına dokunuyorsa "deny" kararı döndürür.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

LOG_DIR = Path(os.environ.get("SD_SPIKE_LOG", Path.home() / "sd-spikes" / "logs"))
ENV_PATTERN = re.compile(r"""(?:^|[\s/'"=])\.env(?:$|[\s.'"/;|&)])""")


def save_input(data: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name = f"{stamp}-{data.get('hook_event_name', 'unknown')}-{data.get('tool_name', 'none')}.json"
    (LOG_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=False))


def touches_env(tool_input: dict) -> bool:
    text = " ".join(str(value) for value in tool_input.values())
    return bool(ENV_PATTERN.search(text))


def main() -> int:
    data = json.load(sys.stdin)
    save_input(data)
    if touches_env(data.get("tool_input") or {}):
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "sdguard deneme: .env dosyasina erisim proje kurali ile yasak."
                ),
            }
        }
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    sys.exit(main())
