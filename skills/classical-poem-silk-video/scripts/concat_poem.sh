#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ]; then
  echo "Usage: $0 <output.mp4> <bgm-or-none> <scene1.mp4> <scene2.mp4> [...]" >&2
  exit 2
fi

output="$1"
bgm="$2"
bgm_gain="${POEM_BGM_GAIN:-0.08}"
shift 2
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
list="$tmp_dir/scenes.txt"
joined="$tmp_dir/joined.mp4"

for scene in "$@"; do
  absolute="$(cd "$(dirname "$scene")" && pwd)/$(basename "$scene")"
  case "$absolute" in *"'"*) echo "Scene path may not contain a single quote" >&2; exit 2 ;; esac
  printf "file '%s'\n" "$absolute" >> "$list"
done

mkdir -p "$(dirname "$output")"
ffmpeg -y -f concat -safe 0 -i "$list" -c copy "$joined"

if [ "$bgm" = "none" ]; then
  cp "$joined" "$output"
else
  duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$joined")"
  fade_out="$(awk -v d="$duration" 'BEGIN { printf "%.3f", d - 1.2 }')"
  ffmpeg -y \
    -i "$joined" -stream_loop -1 -i "$bgm" \
    -filter_complex "[0:a]volume=1.0[amb];[1:a]atrim=start=0:end=$duration,asetpts=N/SR/TB,volume=$bgm_gain,afade=t=in:st=0:d=1.0,afade=t=out:st=$fade_out:d=1.2[music];[amb][music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[a]" \
    -map 0:v -map '[a]' \
    -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 \
    -movflags +faststart \
    "$output"
fi

echo "$output"
