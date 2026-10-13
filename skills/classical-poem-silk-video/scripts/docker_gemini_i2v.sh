#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <workspace-image> <prompt-file> <output-relative-to-outputs/gemini-flow-suite>" >&2
  exit 2
fi

skill_dir="$(cd "$(dirname "$0")" && pwd)"
workspace="$(pwd)"
image="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
prompt_file="$2"
output_rel="$3"

case "$image" in
  "$workspace"/*) image_rel="${image#"$workspace"/}" ;;
  *) echo "Image must be inside the current workspace: $workspace" >&2; exit 2 ;;
esac
case "$output_rel" in
  /*|*..*) echo "Output must be a safe relative path" >&2; exit 2 ;;
esac

prompt="$(<"$prompt_file")"
mkdir -p "$workspace/outputs/gemini-flow-suite/$output_rel"

docker exec -i \
  -e "POEM_I2V_IMAGE=/workspace/$image_rel" \
  -e "POEM_I2V_OUTPUT=/data/outputs/$output_rel" \
  -e "POEM_I2V_PROMPT=$prompt" \
  gemini-flow-suite \
  /opt/gemini-venv/bin/python - < "$skill_dir/docker_gemini_i2v.py"

echo "$workspace/outputs/gemini-flow-suite/$output_rel"
