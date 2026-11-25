#!/usr/bin/env bash
# Prompt feasibility run for scenario 1 (not an experiment run): five headless Claude Code
# turns in one session, one git commit per turn, like the planned runner.
# Usage: bash spikes/senaryo-1-istemler/run_turns.sh <out_dir>
#   <out_dir>/venv  Python venv with BaxBench's Flask packages (README.md)
#   <out_dir>/work  the agent's working directory (created as a git repo)
#   <out_dir>/logs  stream-json and stderr per turn
# Resume after a failed turn: START=<n> SID=<session id> bash run_turns.sh <out_dir>
set -uo pipefail
OUT="$(cd "${1:?output folder}" && pwd)"
PROMPTS="$(cd "$(dirname "$0")/../.." && pwd)/harness/prompts/credit_card_service"
WORK="$OUT/work"
LOGS="$OUT/logs"
TOOLS=(Read Write Edit Glob Grep
  "Bash(python:*)" "Bash(python3:*)" "Bash(curl:*)" "Bash(ls:*)" "Bash(mkdir:*)" "Bash(cat:*)"
  "Bash(sqlite3:*)" "Bash(kill:*)" "Bash(pkill:*)" "Bash(sleep:*)" "Bash(cd:*)" "Bash(head:*)"
  "Bash(tail:*)" "Bash(echo:*)" "Bash(ps:*)" "Bash(lsof:*)" "Bash(timeout:*)" "Bash(grep:*)"
  "Bash(wc:*)" "Bash(env:*)" "Bash(export:*)" "Bash(pip list:*)" "Bash(pip show:*)")

mkdir -p "$LOGS"
if [ ! -d "$WORK/.git" ]; then
  mkdir -p "$WORK"
  git -C "$WORK" init -q
  git -C "$WORK" config user.name sd-run
  git -C "$WORK" config user.email sd-run@localhost
  git -C "$WORK" commit -q --allow-empty -m init
fi

free_port() {
  local pids
  pids=$(ss -ltnpH 'sport = :5000' 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u)
  [ -n "$pids" ] && { echo "killing leftover listeners on 5000: $pids"; kill $pids 2>/dev/null; sleep 1; }
  return 0
}

sid="${SID:-}"
app_secret="$(python3 -c "import secrets; print(secrets.token_hex(16))")"  # fixed for the session
for n in $(seq "${START:-1}" 5); do
  echo "=== turn $n start $(date -Is)"
  resume=()
  [ -n "$sid" ] && resume=(--resume "$sid")
  ( cd "$WORK" && env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
      PATH="$OUT/venv/bin:$PATH" APP_SECRET="$app_secret" \
      timeout 1500 claude -p "$(cat "$PROMPTS/turn-$n.txt")" "${resume[@]}" \
        --model sonnet --output-format stream-json --verbose \
        --permission-mode acceptEdits --allowedTools "${TOOLS[@]}" \
      > "$LOGS/turn-$n.jsonl" 2> "$LOGS/turn-$n.stderr" )
  rc=$?
  echo "turn $n exit $rc $(date -Is)"
  free_port
  [ -z "$sid" ] && sid=$(grep -m1 -o '"session_id":"[^"]*"' "$LOGS/turn-$n.jsonl" | cut -d'"' -f4)
  echo "session $sid"
  git -C "$WORK" add -A && git -C "$WORK" commit -q -m "turn-$n" && git -C "$WORK" log --oneline -1
  if [ "$rc" -ne 0 ] || ! grep '"type":"result"' "$LOGS/turn-$n.jsonl" | grep -q '"is_error":false'; then
    echo "turn $n failed; stopping"
    tail -c 2000 "$LOGS/turn-$n.stderr"
    exit 1
  fi
done
echo "=== all turns done"
