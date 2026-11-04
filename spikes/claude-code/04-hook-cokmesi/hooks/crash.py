#!/usr/bin/env python3
"""G0 deneme 4: bilerek çöken bir güvenlik hook'u.

Gerçek hayatta hook betiği bir hata yüzünden çökebilir (eksik paket, yazım hatası, bozuk dosya).
Soru: hook çöktüğünde Claude Code işlemi durdurur mu, yoksa kontrolsüz devam mı eder?
Betik gelen JSON'u kaydeder, sonra bilerek hata verip 1 koduyla çıkar.
"""

import json
import sys
import time
from pathlib import Path

log_dir = Path.home() / "sd-spikes" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
data = json.load(sys.stdin)
stamp = time.strftime("%Y%m%d-%H%M%S")
(log_dir / f"{stamp}-crash-{data.get('tool_name', 'none')}.json").write_text(
    json.dumps(data, indent=2, ensure_ascii=False)
)
raise RuntimeError("sdguard deneme: hook bilerek cokertildi")
