#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <workspace-video> <workspace-output-video>" >&2
  exit 2
fi

workspace="$(pwd)"
input="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
output="$2"
case "$input" in
  "$workspace"/*) input_rel="${input#"$workspace"/}" ;;
  *) echo "Input must be inside the current workspace: $workspace" >&2; exit 2 ;;
esac

job="poem-watermark/$(date +%Y%m%d-%H%M%S)-$$"
name="$(basename "$output")"
docker exec gemini-flow-suite mkdir -p "/data/outputs/$job"
docker exec gemini-flow-suite veo-watermark-remover \
  --no-banner \
  --veo \
  --mark diamond \
  --region 'br:auto' \
  --snap \
  --denoise ai \
  --input "/workspace/$input_rel" \
  --output "/data/outputs/$job/$name"

mkdir -p "$(dirname "$output")"
cp "$workspace/outputs/gemini-flow-suite/$job/$name" "$output"
echo "$output"
