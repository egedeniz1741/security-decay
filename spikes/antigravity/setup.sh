#!/usr/bin/env bash
# Antigravity CLI G0 spikes: (re)creates every workspace under ~/sd-spikes/agy/ (outside the repo).
# Run inside the sd-ubuntu container. Re-run before each step for a clean start.
#   bash spikes/antigravity/setup.sh            -> all workspaces
#   bash spikes/antigravity/setup.sh 02-post    -> only the named workspace(s)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
base="$HOME/sd-spikes/agy"
mkdir -p "$base/hooks" "$base/logs" "$base/state"
cp "$here"/hooks/*.py "$base/hooks/"

# Headless (-p) auto-denies every tool that needs a permission prompt and exits 0 with an empty
# answer, so the spikes need allow rules. Narrow on purpose; the agent may not touch the hooks.
python3 - "$base" <<'PY'
import json, pathlib, sys
base = sys.argv[1]
path = pathlib.Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(path.read_text()) if path.exists() else {}
# The agent read .agents/hooks.json and the hook scripts in the first 02 runs, so reading them is
# denied too (cat/find dropped for the same reason; grep stays for step 01D).
settings["permissions"] = {
    "allow": [f"command({c})" for c in ("ls", "grep", "python3", "git", "head", "tail")]
    + [f"write_file({base})"],
    "deny": [
        f"write_file({base}/hooks)", "write_file(.agents)",
        f"read_file({base}/hooks)", "read_file(.agents)", f"read_file({base}/logs)",
        f"read_file({pathlib.Path.home() / '.gemini'})",
    ],
}
path.write_text(json.dumps(settings, indent=2) + "\n")
PY

write_env() {
  # Fake values. Key and value written separately so secret scanners do not flag them.
  printf '%s=%s\n' "API_KEY" "BU-BIR-DENEME-DEGERIDIR" "DB_SIFRE" "BU-DA-DENEME" > "$1/.env"
  printf 'print("merhaba")\n' > "$1/app.py"
}

write_sql_app() {
  cat > "$1/app.py" <<'PY'
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
}

write_sum_app() {
  printf 'def topla(a, b):\n    return a + b\n' > "$1/app.py"
}

# name | content | hooks.json (relative to this folder, "-" = no hooks)
workspaces=(
  "01-kontrol|env|-"
  "01-hook|env|01-engelleme/hooks.hook.json"
  "01-ls-kontrol|sum|-"
  "01-empty|sum|01-engelleme/hooks.decision-empty.json"
  "01-silent|sum|01-engelleme/hooks.decision-silent.json"
  "01-ask|sum|01-engelleme/hooks.decision-ask.json"
  "01-allow|sum|01-engelleme/hooks.decision-allow.json"
  "02-kontrol|sql|-"
  "02-post|sql|02-mesaj/hooks.post.json"
  "02-inject|sql|02-mesaj/hooks.inject.json"
  "03-kontrol|sql|-"
  "03-hook|sql|03-bitirme-engeli/hooks.hook.json"
  "04-cokme|sum|04-hook-cokmesi/hooks.cokme.json"
  "04-bozukjson|sum|04-hook-cokmesi/hooks.bozukjson.json"
  "04-yavas|sum|04-hook-cokmesi/hooks.yavas.json"
  "05-hook|env|05-skip-permissions/hooks.hook.json"
)

for entry in "${workspaces[@]}"; do
  IFS='|' read -r name content hooks <<<"$entry"
  if [ $# -gt 0 ] && [[ " $* " != *" $name "* ]]; then continue; fi
  dir="$base/$name"
  rm -rf "$dir"
  mkdir -p "$dir"
  case "$content" in
    env) write_env "$dir" ;;
    sql) write_sql_app "$dir" ;;
    sum) write_sum_app "$dir" ;;
  esac
  if [ "$hooks" != "-" ]; then
    mkdir -p "$dir/.agents"
    cp "$here/$hooks" "$dir/.agents/hooks.json"
  fi
  (cd "$dir" && git init -q)
  echo "ready: $dir ($([ "$hooks" = "-" ] && echo 'no hooks' || echo "$hooks"))"
done
