#!/bin/bash
# 断点续跑口播片流水线模板（huashu-art-motion，2核2G 防 OOM 版）
# 用法：复制到项目工地（必须在 /root 下，禁 /tmp），改顶部变量，后台跑 + notify ["DONE","FAIL"]
# 工地约定：seg{1..N}.json（1080p 原 spec）、seg{1..N}.wav（配音）、subs_src.srt、图片与 spec 同目录纯文件名引用
export PATH=/tmp/ffbin:$PATH   # /tmp/ffbin 不在先重建（imageio-ffmpeg，见 SKILL.md 安装节）
FF=/tmp/ffbin/ffmpeg; FP=/tmp/ffbin/ffprobe
W=/root/PROJECT-work                       # ← 改：工地（/root 下持久目录）
ENG=/root/.hermes/skills/huashu-art-motion/scripts
NSEGS=6                                    # ← 改：段数
OUT=/root/public/OUTPUT.mp4                # ← 改：成片路径
SRT_SRC=$W/subs_src.srt                    # ← 改：源字幕
SRT_SCALE=1.1                              # ← 改：SRT 时间轴缩放比（原始时长/旧SRT末时间）；已对齐填 1.0
LOG=$W/pipeline.log
echo "=== pipeline start $(date) ===" >> $LOG
ok() { $FP -v error -show_entries format=duration -of csv=p=0 "$1" >/dev/null 2>&1; }

# 0. 生成 720p 渲染 spec（防 OOM；只建一次）
python3 - "$W" "$NSEGS" <<'PY'
import json,sys,os
w,n=sys.argv[1],int(sys.argv[2])
for i in range(1,n+1):
    p=f'{w}/seg{i}.json'; q=f'{w}/seg{i}_720.json'
    if os.path.exists(q): continue
    s=json.load(open(p)); s['width'],s['height']=1280,720
    json.dump(s,open(q,'w'),ensure_ascii=False)
print('720p specs ok')
PY

# 1. 逐段渲染（完好的跳过，残的删了重渲）
cd $ENG
for i in $(seq 1 $NSEGS); do
  if ok $W/clip$i.mp4; then echo "seg$i skip (done)" >> $LOG; continue; fi
  rm -f $W/clip$i.mp4
  echo "seg$i render start $(date +%T)" >> $LOG
  uv run --with playwright python engine/render.py --spec $W/seg${i}_720.json --out $W/clip$i.mp4 >> $LOG 2>&1
  if ok $W/clip$i.mp4; then echo "seg$i OK" >> $LOG; else echo "seg$i FAIL" >> $LOG; echo "FAIL seg$i"; exit 1; fi
  sleep 5
done

# 2. 音频 concat + atempo 对齐视频总时长
rm -f $W/alist.txt
for i in $(seq 1 $NSEGS); do echo "file '$W/seg$i.wav'" >> $W/alist.txt; done
VDUR=$(python3 -c "import json;print(sum(json.load(open('$W/seg%d.json'%i))['duration'] for i in range(1,$NSEGS+1)))")
$FF -y -f concat -safe 0 -i $W/alist.txt -af "loudnorm=I=-16:TP=-1.5" -ar 44100 $W/audio_raw.wav >> $LOG 2>&1
ADUR=$($FP -v error -show_entries format=duration -of csv=p=0 $W/audio_raw.wav)
ATE=$(python3 -c "print(round($VDUR/$ADUR,4))")
$FF -y -i $W/audio_raw.wav -af "atempo=$ATE" -ar 44100 $W/audio_all.wav >> $LOG 2>&1 || { echo FAIL_AUDIO; exit 1; }

# 3. SRT 时间轴缩放（SCALE=1.0 时直接复制）
python3 - "$SRT_SRC" "$W/subs.srt" "$SRT_SCALE" <<'PY' >> $LOG 2>&1
import re,sys,shutil
src,dst,k=sys.argv[1],sys.argv[2],float(sys.argv[3])
if k==1.0: shutil.copy(src,dst); print('srt copied'); raise SystemExit
def t2s(t):
    h,m,rest=t.split(':'); s,ms=rest.split(','); return (int(h)*3600+int(m)*60+int(s)+int(ms)/1000)*k
def s2t(x):
    ms=int(round(x*1000)); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
txt=open(src).read()
out=re.sub(r'(\d\d:\d\d:\d\d,\d\d\d) --> (\d\d:\d\d:\d\d,\d\d\d)',lambda mo: s2t(t2s(mo.group(1)))+' --> '+s2t(t2s(mo.group(2))),txt)
open(dst,'w').write(out); print('srt scaled x',k)
PY

# 4. concat filter 一步重编码：升 1080p + 烧字幕 + 配音（禁止 -c copy 拼接）
INPUTS=""; MAPV=""
for i in $(seq 1 $NSEGS); do INPUTS="$INPUTS -i $W/clip$i.mp4"; MAPV="$MAPV[$((i-1)):v]"; done
STYLE="FontName=Noto Sans CJK SC Medium,FontSize=21,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=0,Outline=0,Shadow=0,MarginV=60,Alignment=2"
$FF -y $INPUTS -i $W/audio_all.wav \
 -filter_complex "${MAPV}concat=n=$NSEGS:v=1:a=0[cv];[cv]scale=1920:1080:flags=lanczos,subtitles=$W/subs.srt:force_style='$STYLE'[v]" \
 -map "[v]" -map $NSEGS:a -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart \
 $OUT >> $LOG 2>&1 || { echo FAIL_MUX; exit 1; }

ok $OUT && echo "DONE $($FP -v error -show_entries format=duration -of csv=p=0 $OUT)s" || { echo FAIL_FINAL; exit 1; }
