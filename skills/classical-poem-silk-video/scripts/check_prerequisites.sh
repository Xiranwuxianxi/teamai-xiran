#!/usr/bin/env bash
set -euo pipefail

container="${POEM_DOCKER_CONTAINER:-gemini-flow-suite}"
failed=0

require_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'ok   command %s\n' "$1"
  else
    printf 'fail command %s\n' "$1" >&2
    failed=1
  fi
}

for command_name in docker ffmpeg ffprobe python3 rg; do
  require_command "$command_name"
done

if ! docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null | rg -q '^true$'; then
  printf 'fail container %s is not running\n' "$container" >&2
  failed=1
else
  printf 'ok   container %s\n' "$container"
  if docker exec "$container" test -x /opt/gemini-venv/bin/python; then
    printf 'ok   Gemini Python runtime\n'
  else
    printf 'fail /opt/gemini-venv/bin/python\n' >&2
    failed=1
  fi
  if docker exec "$container" test -s /data/auth/gemini/cookies.json; then
    printf 'ok   Gemini authorization file present\n'
  else
    printf 'fail Gemini authorization file missing\n' >&2
    failed=1
  fi
  if docker exec "$container" test -d /workspace; then
    printf 'ok   /workspace mount\n'
  else
    printf 'fail /workspace mount\n' >&2
    failed=1
  fi
  if docker exec "$container" test -w /data/outputs; then
    printf 'ok   /data/outputs writable\n'
  else
    printf 'fail /data/outputs is not writable\n' >&2
    failed=1
  fi
  if docker exec "$container" sh -lc 'command -v veo-watermark-remover >/dev/null 2>&1'; then
    printf 'ok   optional sparkle cleanup tool\n'
  else
    printf 'warn optional sparkle cleanup tool unavailable\n'
  fi
fi

exit "$failed"
