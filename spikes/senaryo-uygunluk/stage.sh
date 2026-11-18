#!/usr/bin/env bash
# Copy agy's /app/code into BaxBench's results layout (model "agy-1.5.1"), dropping files the
# agent created while testing (SQLite db, caches). rep N -> sampleN-1. Finished runs only.
set -euo pipefail
OUT="${SD_OUT:-$HOME/sd-spikes/senaryo-uygunluk}"
R="${BAXBENCH:-$HOME/Projects/baxbench}/results/agy-1.5.1"
for d in "$OUT"/runs/*/r[0-9]*; do
  sc=$(basename "$(dirname "$d")"); rep=${d##*/r}
  [ -f "$d/meta.txt" ] || continue  # still running
  [ -f "$d/app/code/app.py" ] || { echo "skip $sc r$rep (no app.py)"; continue; }
  dst="$R/$sc/Python-Flask/temp0.2-openapi-none/sample$((rep - 1))"
  [ -d "$dst/code" ] && continue
  mkdir -p "$dst/code"
  rsync -a --exclude '*.sqlite3' --exclude '*.db' --exclude '__pycache__' --exclude '*.log' \
    "$d/app/code/" "$dst/code/"
  echo "staged $sc r$rep -> $(ls "$dst/code" | tr '\n' ' ')"
done
