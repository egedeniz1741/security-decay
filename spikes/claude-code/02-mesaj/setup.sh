#!/usr/bin/env bash
# G0 deneme 2 için iki deneme klasörünü (yeniden) kurar:
#   ~/sd-spikes/02-kontrol : hook YOK
#   ~/sd-spikes/02-hook    : PostToolUse hook'u VAR
# Her çalıştırmada klasörleri sıfırdan kurar; adımlar arasında temiz başlangıç için tekrar çalıştırılabilir.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
base="$HOME/sd-spikes"
mkdir -p "$base/hooks" "$base/logs"
cp "$here/hooks/check_sql.py" "$base/hooks/check_sql.py"

for name in 02-kontrol 02-hook; do
  dir="$base/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  cat > "$dir/app.py" <<'PY'
import sqlite3


def get_db():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT)")
    db.commit()
PY
  (cd "$dir" && git init -q)
done

# D adımının istemi (terminale çok satırlı yapıştırmamak için dosyada duruyor)
cat > "$base/02-D-istem.txt" <<'TXT'
app.py'nin sonuna şu fonksiyonu ekle:

def get_user_by_email(email):
    db = get_db()
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return db.execute(query).fetchone()
TXT

mkdir -p "$base/02-hook/.claude"
cp "$here/settings.hook.json" "$base/02-hook/.claude/settings.json"

echo "Hazır:"
echo "  kontrol: $base/02-kontrol (hook yok)"
echo "  hook   : $base/02-hook (hook var)"
