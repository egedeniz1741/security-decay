#!/usr/bin/env bash
# Build the experiment images and print their image ids (the runner records the ids).
# Usage: harness/docker/build.sh [agent|eval]...   (default: both)
# Uses $SD_CONTAINER_CLI, else docker, else podman.
set -euo pipefail
cd "$(dirname "$0")"

cli="${SD_CONTAINER_CLI:-$(command -v docker || command -v podman || true)}"
[ -n "$cli" ] || { echo "neither docker nor podman found" >&2; exit 1; }

claude_version="$(sed -n 's/^ARG CLAUDE_CODE_VERSION=//p' agent-claude.Containerfile)"

build() {  # build <tag> <containerfile>
  echo "== $1"
  "$cli" build -t "$1" -f "$2" .
  echo "$1 $("$cli" image inspect --format '{{.Id}}' "$1")"
}

for target in "${@:-agent eval}"; do
  for t in $target; do
    case "$t" in
      agent) build "sd-agent-claude:$claude_version" agent-claude.Containerfile ;;
      eval) build "sd-eval:latest" eval.Containerfile ;;
      *) echo "unknown target: $t" >&2; exit 2 ;;
    esac
  done
done
