#!/usr/bin/env bash
# G0 deneme 4: dört klasörde aynı isteği insansız modda çalıştırır ve sonuçların özetini yazar.
# Tam JSON çıktıları ~/sd-spikes/logs/04-<klasör>.json dosyalarına kaydedilir.
set -uo pipefail
base="$HOME/sd-spikes"
prompt="app.py dosyasını oku ve içindeki fonksiyonun ne yaptığını tek cümleyle söyle."

for name in 04-cokme-varsayilan 04-cokme-block 04-yavas-varsayilan 04-yavas-block; do
  echo "=================== $name"
  out="$base/logs/$name.json"
  (cd "$base/$name" && claude -p "$prompt" --output-format json > "$out" 2> "$base/logs/$name.stderr")
  python3 - "$out" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print("JSON okunamadı:", e); sys.exit()
print("sure (sn)      :", round(d.get("duration_ms", 0) / 1000, 1))
print("adim sayisi    :", d.get("num_turns"))
print("reddedilenler  :", [x.get("tool_name") for x in d.get("permission_denials", [])])
print("ajanin cevabi  :", (d.get("result") or "").strip()[:600])
PY
done
