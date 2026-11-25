#!/usr/bin/env bash
# Spike 6: does `claude -p` with the compiler's flags behave as sdguard/compiler/llm.py assumes?
# Two short Haiku calls; output goes to ~/sd-spikes/logs/06-*.json (no token is written).
set -euo pipefail
logs="$HOME/sd-spikes/logs"
mkdir -p "$logs"
schema='{"type":"object","properties":{"n":{"type":"integer"},"tools_seen":{"type":"array","items":{"type":"string"}}},"required":["n","tools_seen"],"additionalProperties":false}'
flags=(--output-format json --json-schema "$schema" --model haiku --tools "" --strict-mcp-config
       --setting-sources project --no-session-persistence
       --system-prompt "You answer with JSON only. List the names of the tools you can call in tools_seen.")

echo "== Claude Code sürümü"
claude --version
echo "== Bayraklar --help'te var mı"
for f in --json-schema --tools --strict-mcp-config --setting-sources --no-session-persistence --system-prompt; do
  if claude --help | grep -q -- "$f"; then echo "var   $f"; else echo "YOK   $f"; fi
done

empty="$(mktemp -d)"
echo "== A: yapılandırılmış cevap (boş klasörde)"
(cd "$empty" && claude -p "Return n = 3." "${flags[@]}" > "$logs/06-A.json" 2> "$logs/06-A.stderr") || echo "çıkış kodu $?"
echo "== B: araç kullanmaya zorlama (araç olmamalı)"
(cd "$empty" && claude -p "Run 'ls /' with a tool, then return n = the number of entries (0 if you cannot)." \
  "${flags[@]}" > "$logs/06-B.json" 2> "$logs/06-B.stderr") || echo "çıkış kodu $?"
rmdir "$empty" 2>/dev/null || echo "UYARI: boş klasöre dosya yazılmış: $empty"

python3 - "$logs" <<'PY'
import json, sys, pathlib
logs = pathlib.Path(sys.argv[1])
for step in ("A", "B"):
    path = logs / f"06-{step}.json"
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{step}: sonuç okunamadı ({exc}); stderr: {(logs / f'06-{step}.stderr').read_text()[:300]}")
        continue
    print(f"--- {step}")
    print("  anahtarlar      :", sorted(data))
    print("  subtype/is_error:", data.get("subtype"), data.get("is_error"))
    print("  structured_output:", json.dumps(data.get("structured_output")))
    print("  result (ilk 200):", str(data.get("result"))[:200].replace("\n", " "))
    print("  num_turns       :", data.get("num_turns"))
    print("  total_cost_usd  :", data.get("total_cost_usd"))
PY
