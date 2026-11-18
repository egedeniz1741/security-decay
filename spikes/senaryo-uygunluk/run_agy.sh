#!/usr/bin/env bash
# Turn 1 of candidate BaxBench scenarios with agy 1.5.1, headless, one fresh container per run.
# Usage: run_agy.sh <Scenario> <rep> [<Scenario> <rep> ...]
# Needs: image localhost/sd-agy-flask:1 (agy-image/), prompts in $OUT/prompts (gen_prompts.py),
# the agy login in the podman volume sd-agy-state. Runs go to $OUT/runs/<Scenario>/r<rep>/.
# The container gets only the login volume, an empty /app workspace and the prompt: no docker
# socket, no repo mounts. Permissions come from --settings (this session only).
set -uo pipefail
OUT="${SD_OUT:-$HOME/sd-spikes/senaryo-uygunluk}"
# A narrow allow list (python3, ls, cat, curl, ...) ended the first run after 13 s with an
# auto-denied `python3 --version && pip list` (R19). The container is isolated, so the
# feasibility runs allow every command; the commands actually used are counted by commands.py.
SETTINGS='{"permissions":{"allow":["command(*)","write_file(/app)"],"deny":["read_file(/root/.gemini)"]}}'
while [ $# -ge 2 ]; do
  sc="$1"; rep="$2"; shift 2
  run="$OUT/runs/$sc/r$rep"
  rm -rf "$run"; mkdir -p "$run/app" "$run/out"
  echo "=== $sc r$rep $(date +%T)"
  start=$(date +%s)
  timeout 1100 podman run --rm --security-opt label=disable \
    -v sd-agy-state:/root/.gemini \
    -v "$run/app:/app" -v "$run/out:/out" \
    -v "$OUT/prompts/$sc.txt:/prompt.txt:ro" \
    -e SETTINGS="$SETTINGS" -w /app localhost/sd-agy-flask:1 bash -c '
      (cd /opt/agy && sha256sum -c --quiet agy-1.5.1-linux-x64.sha256) || { echo "agy binary not pinned" >&2; exit 90; }
      agy --version > /out/agy-version.txt 2>&1
      agy -p "$(cat /prompt.txt)" --output-format stream-json --print-timeout 900s --settings "$SETTINGS" > /out/out.jsonl 2> /out/err.txt
      echo $? > /out/exit.txt'
  code=$?
  end=$(date +%s)
  # agy prints its local server's CSRF token when the agent runs `env`; keep it out of the logs.
  sed -i -E 's/(ANTIGRAVITY_CSRF_TOKEN=)[^\\"]+/\1<REDACTED>/g' "$run/out/out.jsonl" 2>/dev/null
  {
    echo "scenario: $sc"; echo "rep: $rep"; echo "podman_exit: $code"
    echo "agy_exit: $(cat "$run/out/exit.txt" 2>/dev/null || echo none)"
    echo "agy_version: $(cat "$run/out/agy-version.txt" 2>/dev/null)"
    echo "duration_s: $((end - start))"
    echo "app_py: $([ -f "$run/app/code/app.py" ] && echo yes || echo no)"
    echo "auto_denied: $(grep -c 'auto-denied' "$run/out/err.txt" 2>/dev/null || true)"
    echo "quota: $(grep -c 'quota reached' "$run/out/err.txt" 2>/dev/null || true)"
  } > "$run/meta.txt"
  tr '\n' ' ' < "$run/meta.txt"; echo
  if grep -q 'quota reached' "$run/out/err.txt" 2>/dev/null; then
    echo "agy quota reached; stopping" >&2
    exit 3
  fi
done
