#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 5 ]; then
  echo "Usage: $0 <output.mp4> <bgm-or-none> <transition-seconds> <scene1.mp4> <scene2.mp4> [...]" >&2
  exit 2
fi

output="$1"
bgm="$2"
transition="$3"
bgm_gain="${POEM_BGM_GAIN:-0.08}"
shift 3
scenes=("$@")
count="${#scenes[@]}"

inputs=()
durations=()
filter=""
for ((i=0; i<count; i++)); do
  scene="${scenes[$i]}"
  inputs+=( -i "$scene" )
  duration="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$scene")"
  durations+=( "$duration" )
  filter+="[$i:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30,format=yuv420p[vsrc$i];"
  filter+="[$i:a]asetpts=PTS-STARTPTS[asrc$i];"
done

video_label="[vsrc0]"
audio_label="[asrc0]"
elapsed="${durations[0]}"
for ((i=1; i<count; i++)); do
  offset="$(awk -v e="$elapsed" -v t="$transition" 'BEGIN { printf "%.3f", e - t }')"
  filter+="$video_label[vsrc$i]xfade=transition=fade:duration=$transition:offset=$offset[vx$i];"
  filter+="$audio_label[asrc$i]acrossfade=d=$transition:c1=tri:c2=tri[ax$i];"
  video_label="[vx$i]"
  audio_label="[ax$i]"
  elapsed="$(awk -v e="$elapsed" -v d="${durations[$i]}" -v t="$transition" 'BEGIN { printf "%.3f", e + d - t }')"
done

if [ "$bgm" = "none" ]; then
  filter+="$video_label format=yuv420p[vout];$audio_label alimiter=limit=0.95[aout]"
else
  bgm_index="$count"
  inputs+=( -stream_loop -1 -i "$bgm" )
  fade_out="$(awk -v d="$elapsed" 'BEGIN { printf "%.3f", d - 1.2 }')"
  filter+="[$bgm_index:a]atrim=start=0:end=$elapsed,asetpts=N/SR/TB,volume=$bgm_gain,afade=t=in:st=0:d=1.0,afade=t=out:st=$fade_out:d=1.2[music];"
  filter+="$video_label format=yuv420p[vout];$audio_label[music]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,alimiter=limit=0.95[aout]"
fi

mkdir -p "$(dirname "$output")"
ffmpeg -y \
  "${inputs[@]}" \
  -filter_complex "$filter" \
  -map '[vout]' -map '[aout]' \
  -r 30 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.1 \
  -c:a aac -b:a 192k -ar 44100 -ac 2 \
  -movflags +faststart \
  "$output"

echo "$output"
