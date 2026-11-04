#!/usr/bin/env bash
# G0 deneme 4 için dört deneme klasörü kurar:
#   ~/sd-spikes/04-cokme-varsayilan : hook çöküyor, onFailure ayarı YOK
#   ~/sd-spikes/04-cokme-block      : hook çöküyor, "onFailure": "block"
#   ~/sd-spikes/04-yavas-varsayilan : hook zaman aşımına uğruyor, onFailure ayarı YOK
#   ~/sd-spikes/04-yavas-block      : hook zaman aşımına uğruyor, "onFailure": "block"
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
base="$HOME/sd-spikes"
mkdir -p "$base/hooks" "$base/logs"
cp "$here/hooks/crash.py" "$base/hooks/crash.py"
cp "$here/hooks/slow.py" "$base/hooks/slow.py"

make_dir() {
  local name="$1" settings="$2"
  local dir="$base/$name"
  rm -rf "$dir"
  mkdir -p "$dir/.claude"
  printf 'def topla(a, b):\n    return a + b\n' > "$dir/app.py"
  cp "$here/$settings" "$dir/.claude/settings.json"
  (cd "$dir" && git init -q)
}

make_dir 04-cokme-varsayilan settings.crash.varsayilan.json
make_dir 04-cokme-block settings.crash.block.json
make_dir 04-yavas-varsayilan settings.slow.varsayilan.json
make_dir 04-yavas-block settings.slow.block.json

echo "Hazır: $base/04-cokme-varsayilan, 04-cokme-block, 04-yavas-varsayilan, 04-yavas-block"
