#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <input-video> <scene.ass> <output.mp4> <duration-seconds> [fade|none]" >&2
  exit 2
fi

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
input="$1"
ass="$2"
output="$3"
duration="$4"
fade_mode="${5:-fade}"
fade_out="$(awk -v d="$duration" 'BEGIN { printf "%.3f", d - 0.45 }')"
mkdir -p "$(dirname "$output")"

case "$fade_mode" in
  fade)
    video_fade=",fade=t=in:st=0:d=0.35,fade=t=out:st=$fade_out:d=0.45"
    audio_fade=",afade=t=in:st=0:d=0.35,afade=t=out:st=$fade_out:d=0.45"
    ;;
  none)
    video_fade=""
    audio_fade=""
    ;;
  *)
    echo "Fade mode must be 'fade' or 'none'" >&2
    exit 2
    ;;
esac

if ffprobe -v error -select_streams a:0 -show_entries stream=index -of csv=p=0 "$input" | rg -q '[0-9]'; then
  ffmpeg -y \
    -i "$input" \
    -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,subtitles='$ass':fontsdir='$skill_dir/assets'$video_fade,format=yuv420p[v];[0:a]atrim=start=0:end=$duration,asetpts=N/SR/TB,volume=0.92$audio_fade[a]" \
    -map '[v]' -map '[a]' \
    -t "$duration" -r 30 \
    -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.1 \
    -c:a aac -b:a 192k -ar 44100 -ac 2 \
    -movflags +faststart \
    "$output"
else
  ffmpeg -y \
    -i "$input" -f lavfi -i anullsrc=r=44100:cl=stereo \
    -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,subtitles='$ass':fontsdir='$skill_dir/assets'$video_fade,format=yuv420p[v];[1:a]atrim=start=0:end=$duration$audio_fade[a]" \
    -map '[v]' -map '[a]' \
    -t "$duration" -r 30 \
    -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.1 \
    -c:a aac -b:a 192k -ar 44100 -ac 2 \
    -movflags +faststart \
    "$output"
fi

echo "$output"
