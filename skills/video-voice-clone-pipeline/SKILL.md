---
name: video-voice-clone-pipeline
description: Use when 本机渲视频或克隆声音。ffmpeg无x264、F5克隆、企微收音频的实测坑。
---

# 视频渲染 + 声音克隆本机实测（2026-10-07 腾讯云 2核2G）

## huashu-art-motion 环境坑
- 安装走 `https://gh-proxy.com/https://codeload.github.com/alchaincyf/huashu-art-motion/tar.gz/refs/heads/main`（直连/ghfast.top 不通），已装在 /root/.hermes/skills/huashu-art-motion
- Playwright chromium 下载卡死 → 软链系统 Chrome：`~/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome` 和 `chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell` 都指 `/usr/bin/google-chrome`（新版默认用 headless shell，两个都要链），launch 加 `--no-sandbox`
- **系统 ffmpeg 无 libx264**，render.py 出 mp4 必挂（BrokenPipe 是表象）：`pip install imageio-ffmpeg` 得静态 ffmpeg 自带 x264，软链 `/tmp/ffbin/ffmpeg` 并 `export PATH=/tmp/ffbin:$PATH`。stills 模式不需要。⚠️/tmp 重启会丢，丢了重建
- spec 渲染日志 "❌ 页面报错 1 条" 通常只是 Canvas2D willReadFrequently 提示，出帧正常即可忽略

## 口播成片流程（已跑通，77秒成片）
分段 edge-tts(XiaoxiaoNeural) → ffprobe 拿每段时长 → 按文稿节奏写 clips spec（cue 的 at 对语速）→ `render.py --spec` 逐段出无声 mp4 → ffmpeg concat → 烧 SRT 字幕（subtitles filter + Noto Sans CJK SC）→ faststart → 部署 /root/public

## F5-TTS 声音克隆（零样本，本地跑不动就走 HF Space）
- Space `mrfakename-e2-f5-tts`：hf.space 域名可直连，所有请求带 `Authorization: Bearer $(cat /root/.hf_token)`；参数 ref_audio(先upload) / ref_text / gen_text / remove_silence
- **ref_text 必须和参考音频一字不差**（口误也不能纠正），错配 → 输出又快又糊（已踩过）
- 手机外放录音质量不够（噪音+语速快），要麦克风+安静环境+30-60s；录音稿需覆盖平翘舌、前后鼻音、数字多形态（年份/大数/小数/百分比）
- 企微语音消息会被转成文字、音频到不了服务器，必须让用户走「文件」通道发 m4a/mp3
