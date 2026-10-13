#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 <final-video.mp4> <qa-output-dir> [timestamps.tsv]" >&2
  exit 2
fi

video="$1"
qa_dir="$2"
timestamps_file="${3:-}"

test -f "$video" || { echo "Video not found: $video" >&2; exit 2; }
mkdir -p "$qa_dir/frames"

ffprobe -v error -show_streams -show_format -of json "$video" > "$qa_dir/ffprobe.json"
ffmpeg -hide_banner -nostats -i "$video" -vf 'blackdetect=d=0.15:pix_th=0.10' -an -f null - 2> "$qa_dir/blackdetect.log" || true
ffmpeg -hide_banner -nostats -i "$video" -map 0:a:0 -af 'silencedetect=n=-45dB:d=1.0' -f null - 2> "$qa_dir/silencedetect.log" || true
ffmpeg -hide_banner -nostats -i "$video" -map 0:a:0 -af volumedetect -f null - 2> "$qa_dir/volumedetect.log" || true

duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$video")"
for item in '0.10:p10' '0.25:p25' '0.50:p50' '0.75:p75' '0.90:p90'; do
  ratio="${item%%:*}"
  label="${item##*:}"
  timestamp="$(awk -v d="$duration" -v r="$ratio" 'BEGIN { printf "%.3f", d * r }')"
  ffmpeg -hide_banner -loglevel error -y -ss "$timestamp" -i "$video" -frames:v 1 "$qa_dir/frames/$label.png"
done

last_timestamp="$(awk -v d="$duration" 'BEGIN { printf "%.3f", (d > 0.08 ? d - 0.08 : 0) }')"
ffmpeg -hide_banner -loglevel error -y -ss "$last_timestamp" -i "$video" -frames:v 1 "$qa_dir/frames/last.png"

if [ -n "$timestamps_file" ]; then
  test -f "$timestamps_file" || { echo "Timestamp file not found: $timestamps_file" >&2; exit 2; }
  while IFS=$'\t' read -r timestamp label; do
    [ -n "${timestamp:-}" ] || continue
    case "$timestamp" in \#*) continue ;; esac
    safe_label="$(printf '%s' "${label:-frame}" | tr -cs 'A-Za-z0-9._-' '-')"
    ffmpeg -hide_banner -loglevel error -y -ss "$timestamp" -i "$video" -frames:v 1 "$qa_dir/frames/$safe_label.png"
  done < "$timestamps_file"
fi

ffmpeg -hide_banner -loglevel error -y \
  -i "$qa_dir/frames/p10.png" -i "$qa_dir/frames/p25.png" \
  -i "$qa_dir/frames/p50.png" -i "$qa_dir/frames/p75.png" \
  -i "$qa_dir/frames/p90.png" -i "$qa_dir/frames/last.png" \
  -filter_complex '[0:v]scale=270:480[a];[1:v]scale=270:480[b];[2:v]scale=270:480[c];[3:v]scale=270:480[d];[4:v]scale=270:480[e];[5:v]scale=270:480[f];[a][b][c]hstack=3[top];[d][e][f]hstack=3[bottom];[top][bottom]vstack=2[out]' \
  -map '[out]' -frames:v 1 "$qa_dir/contact-sheet.png"

python3 - "$qa_dir/ffprobe.json" <<'PY'
import json
import math
import sys

payload = json.load(open(sys.argv[1], encoding="utf-8"))
streams = payload.get("streams", [])
video = next((s for s in streams if s.get("codec_type") == "video"), None)
audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
errors = []
if not video:
    errors.append("missing video stream")
else:
    if video.get("codec_name") != "h264":
        errors.append(f"video codec is {video.get('codec_name')}, expected h264")
    if (video.get("width"), video.get("height")) != (1080, 1920):
        errors.append(f"video size is {video.get('width')}x{video.get('height')}, expected 1080x1920")
    rate = video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"
    numerator, denominator = (float(part) for part in rate.split("/", 1))
    fps = numerator / denominator if denominator else 0.0
    if not math.isclose(fps, 30.0, abs_tol=0.05):
        errors.append(f"frame rate is {fps:.3f}, expected 30")
if not audio:
    errors.append("missing audio stream")
elif audio.get("codec_name") != "aac":
    errors.append(f"audio codec is {audio.get('codec_name')}, expected aac")
if errors:
    raise SystemExit("; ".join(errors))
print("media contract passed: H.264/AAC, 1080x1920, 30 fps")
PY

printf 'QA artifacts: %s\n' "$qa_dir"
