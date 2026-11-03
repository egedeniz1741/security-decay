#!/usr/bin/env bash
# G0 deneme 1 için iki ayrı deneme klasörü kurar:
#   ~/sd-spikes/01-kontrol : hook YOK (karşılaştırma için)
#   ~/sd-spikes/01-hook    : PreToolUse hook'u VAR
# Repo klasörünün dışında kuruyoruz ki projenin kendi Claude ayarlarına karışmasın.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
base="$HOME/sd-spikes"
mkdir -p "$base/hooks" "$base/logs"
cp "$here/hooks/block_env.py" "$base/hooks/block_env.py"

for name in 01-kontrol 01-hook; do
  dir="$base/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  # Sahte değerler. Anahtar adı ve değer ayrı yazılıyor ki gizli bilgi tarayıcıları
  # (Gitleaks, GitGuardian) bunu gerçek şifre sanmasın.
  printf '%s=%s\n' "API_KEY" "BU-BIR-DENEME-DEGERIDIR" "DB_SIFRE" "BU-DA-DENEME" > "$dir/.env"
  printf 'print("merhaba")\n' > "$dir/app.py"
  (cd "$dir" && git init -q)
done

mkdir -p "$base/01-hook/.claude"
cp "$here/settings.hook.json" "$base/01-hook/.claude/settings.json"

echo "Hazır:"
echo "  kontrol: $base/01-kontrol (hook yok)"
echo "  hook   : $base/01-hook (hook var)"
echo "  kayıtlar: $base/logs"
