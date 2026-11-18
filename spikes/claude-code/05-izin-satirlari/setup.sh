#!/usr/bin/env bash
# Deneme 5 (izin satırları) için klasörleri kurar. Hook yok; yalnızca Claude Code'un kendi
# izin sistemi sınanıyor. Bütün değerler sahte.
#   ~/sd-spikes/05-izin/proje          : .claude/settings.json içinde deny Read(/.env), Bash(cat|grep) izinli
#   ~/sd-spikes/05-izin/proje/alt      : alt klasör (ajan buradan başlatılınca kök ayarı geçerli mi?)
#   ~/sd-spikes/05-izin/yazim-hatasi   : deny satırında bilinmeyen araç adı (Reed)
#   ~/sd-spikes/05-izin/bozuk-desen    : deny satırında kapanmayan parantez
#   ~/sd-spikes/05-izin/ayarsiz        : proje ayarı yok; izinler --settings ile dışarıdan verilecek
#   ~/sd-spikes/05-izin/disari.json    : --settings dosyası (deny + iz bırakan bir hook)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
base="$HOME/sd-spikes/05-izin"
rm -rf "$base"
mkdir -p "$base" "$HOME/sd-spikes/logs"

fake_env() {  # $1 = klasör, $2 = sahte değer
  printf '%s=%s\n' "API_KEY" "$2" > "$1/.env"
}

make_project() {  # $1 = ad, $2 = settings dosyası (boşsa proje ayarı yok)
  local dir="$base/$1"
  mkdir -p "$dir/alt"
  printf 'def topla(a, b):\n    return a + b\n' > "$dir/app.py"
  fake_env "$dir" "KOK-DENEME-1111"
  fake_env "$dir/alt" "ALT-DENEME-2222"
  if [ -n "$2" ]; then
    mkdir -p "$dir/.claude"
    cp "$here/$2" "$dir/.claude/settings.json"
  fi
  (cd "$dir" && git init -q)
}

make_project proje settings.proje.json
make_project yazim-hatasi settings.yazim-hatasi.json
make_project bozuk-desen settings.bozuk-desen.json
make_project ayarsiz ""
sed "s#__LOG__#$HOME/sd-spikes/logs/05-F-hook.log#" "$here/disari.json" > "$base/disari.json"
rm -f "$HOME/sd-spikes/logs/05-F-hook.log"

echo "Hazır: $base"
