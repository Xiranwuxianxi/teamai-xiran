---
name: voice-clone-hf-space-f5tts
description: 声音克隆与TTS配音。首选小米MiMo voiceclone，备胎F5-TTS/CosyVoice2。含喂稿规范、批量配音、多音色对话。
---

# 声音克隆与 TTS 配音

## 首选通道：小米 MiMo voiceclone（2026-10-10 实测）

API key 在 `/root/.hermes/.env`（`XIAOMI_API_KEY`），base_url `https://token-plan-cn.xiaomimimo.com/v1`。**无配额限制、企业级稳定、亚秒级延迟**。

**端点坑（2026-10-11 实测）**：实际可用端点是 `POST {base}/chat/completions`；猜的 `/audio/speech` 返回 openresty 404。响应是 chat JSON，音频在 `choices[0].message.audio.data`（base64 编码的 wav），需 `base64.b64decode` 后写盘。

### 声音克隆（mimo-v2.5-tts-voiceclone）

```python
import base64, json, urllib.request

ref_b64 = base64.b64encode(open('/root/voice-assets/ref_clip.wav','rb').read()).decode()
payload = {
    "model": "mimo-v2.5-tts-voiceclone",
    "messages": [
        {"role": "user", "content": ""},
        {"role": "assistant", "content": "要合成的文字"}
    ],
    "audio": {
        "format": "wav",
        "voice": f"data:audio/mpeg;base64,{ref_b64}"  # ← 关键坑：data URI 格式，不是 reference_audio 字段
    }
}
```

**头号坑**：参考音频放在 `audio.voice` 字段，格式必须是 `data:audio/mpeg;base64,<纯base64>`。用 `reference_audio` 字段或纯 base64 会 400。支持 mp3/wav，≤10MB。

### 预置音色合成（mimo-v2.5-tts）

9 个音色：冰糖(中女)/茉莉(中女)/苏打(中男)/白桦(中男)/Mia(英女)/Chloe(英女)/Milo(英男)/Dean(英男)。支持 user message 传风格指令（温柔/活泼/东北话/四川话/粤语/角色扮演/唱歌）。

```python
payload = {
    "model": "mimo-v2.5-tts",
    "messages": [
        {"role": "user", "content": "用温柔的语气"},  # 可选风格指令
        {"role": "assistant", "content": "要合成的文字"}
    ],
    "audio": {"format": "wav", "voice": "冰糖"}
}
```

### 文本捏音（mimo-v2.5-tts-voicedesign）

无需音频样本，写描述生成定制音色。user message = 音色描述。

### 多音色对话脚本（男女双声）

一个对话多个角色时，每个角色单独调 API，用不同 voice/参考音频：
- 男声（主人克隆）→ voiceclone + ref_clip.wav
- 女声（AI助手）→ 预置音色"冰糖"或"茉莉"
- 逐段生成后按时间轴 concat

### 相似度与节奏铁律（2026-10-12 主人"不像""一个字一个字符"三轮返工后定型，别再重踩）
1. **参考音长度是相似度第一因**：80 秒长参考会稀释音色特征，克隆出来"不像"。裁 18-20s 干净段做参考（电平平稳段，先 silenceremove 去首尾 + loudnorm=I=-20:TP=-2 标准化）。
2. **风格指令优先"忠实"不优先"人设"**：写"忠实还原参考音色，不要改变音色特征"比人设词（磁性温暖/甜美）更像本人；人设词会把结果带偏，只在主人明确要某种气质时用。
3. **"一个字一个字符"病 = 文案逗号多 + MiMo 默认语速偏慢（约 0.6 字/秒）**：TTS 每个逗号都停顿。三管齐下：① 文案重写成长句口语体（每句最多 1-2 个逗号）；② 加快节奏风格指令，且关键段生成 2-3 个变体挑最短的（指令不可靠，有时会反而更慢，别省这一步）；③ 最后 atempo ≤1.05 微调对齐画面。
4. **相似度优先就去升调**：女声 asetrate×1.04 的"细高"链会把声音推细，主人评"不像她"。升调链只在主人明确说"再细一点高一点"时用，默认不开。
5. **atempo 对齐补偿**：女声链若含 asetrate×1.04 会把时长缩到 1/1.04，按目标时长算 atempo 时要 ×1.04 补偿（2026-10-12 实测 52.7s 画面 52.56s 音频，补偿后对上）。
6. **双声分工（muse 片定型）**：讲解/数据段用男声（主人克隆），提问/吐槽段用女声（林佳颖克隆）。

## 备胎通道：F5-TTS（免费 Space）

本地 2核2G 跑不动克隆模型 → 调 Space：`https://mrfakename-e2-f5-tts.hf.space`（upload→call→poll 三段式与 HF token 坑见 skill `hf-space-gradio-api`，token 在 /root/.hf_token）。

## 头号坑（先记住再动手）

**参考音频总长必须 ≤30 秒**（F5-TTS 训练上限，ref+gen 合计约 30s）。用户随手录 40s+ 很常见，直接用会导致生成语音又快又糊、完全听不清——症状就是"念得飞快"，别怀疑参数，先砍参考长度。

## 标准流程

1. **收素材**：企微语音消息会被自动转文字、音频到不了手，必须让用户走「+ → 文件」发 m4a/mp3 附件。缓存路径形如 `/root/.hermes/cache/documents/doc_*`。
2. **预处理**：
   ```sh
   ffmpeg -i in.m4a -af "silenceremove=start_periods=1:start_threshold=-40dB,areverse,silenceremove=start_periods=1:start_threshold=-40dB,areverse,loudnorm=I=-20:TP=-2" -ar 24000 -ac 1 ref.wav
   ```
3. **截取 10–15s 干净段**当参考（电平平稳、无咳嗽/停顿/环境声）。`astats` 看 Peak/RMS：Peak -2dB、RMS -23dB 左右是好素材。
4. **ref_text 必须与参考段逐字一致**（音素对齐，错字会崩语速）。用户没给逐字稿就自己转写：faster-whisper tiny CPU 可跑（`pip install faster-whisper`，`HF_ENDPOINT=https://hf-mirror.com` 拉模型）。
5. **调用**（upload → /gradio_api/call/predict → 轮询 event: complete，参数序：ref_audio, ref_text, gen_text, remove_silence）：完整可跑脚本见 `references/f5-clone-client.py`。
6. **后期抛光**（承诺过的"调声"清单）：响度 `loudnorm=I=-16:TP=-1.5`；语速用 `atempo`（0.9–1.1 内自然）；去齿音/轻压缩按听感加。音色是模型定的，别动；能调的是节奏（靠喂稿的标点断句）、语速、响度、贴画面。

## 录音素材指导（发给用户）

- 30–60s、安静环境、麦离嘴一拳、正常偏慢语速（克隆继承语速）
- 文本要覆盖：平翘舌对（知识/这些）、前后鼻音（神经/增长）、数字多形态（年份/大数/小数/百分比）、语气起伏、长短句停顿
- 让用户念完把原话一字不差发来，或自己转写对齐

## 配额与备胎通道（2026-10-09 实测）

- F5 Space 免费 ZeroGPU 每天限量；**带 token 与匿名是两套独立配额**，一边 event:error 连烧就换另一边重试。
- 备胎：`taoyy/CosyVoice2-0.5B`（已验证可克隆）：endpoint `/gradio_api/call/synthesize`，参数 `[tts_text, "零样本语音复刻", ref_file(FileData), ref_text, None, 1.0]`；**返回的文件 URL 要把 `/grad/gradio_api/file=` 改成 `/gradio_api/file=` 才能下载**（否则下到 HTML 错误页）。也限流，失败 sleep 45–90s 重试。
- **声纹参考必须备份到 /root**：`/root/voice-assets/ref_clip.wav`（主人 9.55s 切片）+ `clone2.py`（含逐字 ref_text）。/tmp 会被系统清，2026-10-09 已踩过一次。

## 喂稿规范（念错词全是不规范喂稿的锅）

- **数字一律写中文**：3800→三千八百、5%→百分之五、2024→二零二四（阿拉伯数字必念飘）。
- 正确英文术语保留（MoE/GPT-4/DeepSeek），但易念错的用谐音锚定：token→透肯、V3→V三；字幕另存标准写法，音字分离。
- 生成后可用 faster-whisper 回听转写，核对关键数字/专名没念错再交付。

## 克隆声音抛光（2026-10-10 实测，主人要求"清脆悦耳但不失本色"）

克隆出的声音可能不够通透/不够亮。**两步走：先用 MiMo 风格指令，再用 ffmpeg 后处理。**

### 第一步：MiMo 风格指令（user message）

```python
{"role": "user", "content": "用清脆悦耳的语调，明亮清晰，声音干净通透，保持自然温柔"}
```

有效风格词：清脆悦耳/明亮清晰/干净通透/温柔/活泼/高冷/磁性/甜美/稚嫩/苍老。

### 第二步：ffmpeg 音频抛光链

**清脆明亮版**（推荐日常配音）：
```sh
ffmpeg -i in.wav -af "highpass=f=80,lowpass=f=12000,equalizer=f=3000:t=q:w=1.2:g=2.5,equalizer=f=8000:t=q:w=1.5:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=5:release=50,loudnorm=I=-16:TP=-1.5" -ar 24000 -ac 1 out.wav
```

**细高版**（更接近年轻女声/需要更高音调时）：
```sh
ffmpeg -i in.wav -af "asetrate=24000*1.04,aresample=24000,highpass=f=100,lowpass=f=14000,equalizer=f=2500:t=q:w=1.2:g=3,equalizer=f=6000:t=q:w=1.5:g=2,equalizer=f=10000:t=q:w=2:g=1.5,acompressor=threshold=-22dB:ratio=3:attack=5:release=50,loudnorm=I=-16:TP=-1.5" -ar 24000 -ac 1 out.wav
```

参数说明：`asetrate=24000*1.04` 提升音调 4%（1.03-1.05 内自然，超 1.08 会失真）；高频 EQ 2.5k/6k/10k 各 +1.5~3dB 提亮；compressor 稳定音量；loudnorm 标准化到 -16 LUFS。

**微调指南**：主人说"再细一点高一点" → asetrate 倍率 +0.01~0.02；说"太尖了" → 倍率 -0.01 或降 6kHz EQ 增益。

## 克隆质量测试文稿（全要素覆盖，自然文章体）

验证克隆质量时别用测试清单体（"平翘舌：xxx"），写成**自然流畅的小文章**，把测试要素织进内容里。模板见 `references/voice-test-script.md`。

## 主人已否决的方向（2026-10-11，别再推荐）

- **TTS 克隆唱歌**（MiMo voiceclone + "唱歌"风格指令）：试过三版（温柔慢版/童声儿歌版/升调加速版），主人嫌太慢、不像唱歌，否决。
- **rubberband 升调变童声**（p5/p6/p7 + 共振峰上移 + EQ）：主人评价"都刺耳"，否决。成人声带升调变童声物理上限如此，别再试。

## 声纹参考备份

- 主人（启行）：`/root/voice-assets/ref_clip.wav`（9.55s 切片，ref_text 见 /root/voice-assets/clone2.py）
- 女声（林佳颖）：`/root/sbr-work/linjiaying-ref.wav`（84.6s，2026-10-10 收）
- **换参考音必须同时换 REF_TEXT**，否则音素错位、语速崩。

## 批量配音（整片连跑，2026-10-10 实测 6 段一次全过）

整片配音别一段段手动调。工程目录放 `script.json`：

```json
{"segs": [{"id": 1, "tts": "喂稿（数字写中文、易飘英文谐音锚定，见喂稿规范）"}, ...]}
```

跑 `python3 scripts/batch_clone.py --work <工程目录> --script script.json`（脚本在 huashu-art-motion-ops 技能，从那拷改，别重写）。行为：

- 每段依次试 F5 带 token → F5 匿名（两套独立 ZeroGPU 配额）→ CosyVoice2-0.5B，段间失败 sleep 50s
- 已存在且 >20KB 的 `segN.wav` 自动跳过（断点续跑）；`--only 1 3` 补跑指定段
- 任何一段三通道全灭才 exit 1；全部成功打印 ALL_VOICE_DONE
- 参考上传结果按 space 缓存，整片只上传一次声纹

REF_TEXT 默认值是 `/root/voice-assets/ref_clip.wav` 的逐字稿（源自 /root/voice-assets/clone2.py），**换参考音必须同时换 --ref-text**，否则音素错位、语速崩。

## 克隆唱歌（2026-10-11 实测可行）

MiMo voiceclone 支持唱歌：user message 写风格指令如「用充满梦想和童真的感觉，温柔地唱这首歌」，assistant content 放歌词。风格指令对 voiceclone 同样生效（不限于预置音色）。

- **节奏**：唱歌比说话慢很多，约 2~3 字/秒（30 字 ≈ 14s），整首歌按歌词行/句分段生成再 concat。
- **验收**：自己不能听 → 用 faster-whisper tiny 回听转写核对歌词（唱歌转写会有同音错字，"尼罗河底→尼羅核底"级属正常，只抓大段缺失/乱码）；再看 ffprobe 时长是否符合唱歌节奏（说话节奏=没唱起来）。
- 交付 mp3：`ffmpeg -i in.wav -codec:a libmp3lame -q:a 4 out.mp3`。

### 主人反馈与调优（2026-10-11）

首版"温柔地唱"被主人否了：「不够孩童，太慢了，要像唱歌一样」。教训：

- **唱歌风格指令要下猛料**，单写"温柔地唱"输出偏念白。有效加强版：「用稚嫩天真的童声唱歌，像小朋友唱歌一样有明确的旋律和节奏，轻快活泼，不要拖慢」「童声演唱，稚嫩可爱，节奏明快，音调高一点，像儿歌一样唱出来」。
- **还不够就叠加后处理**：`asetrate=<输入采样率>*1.12,aresample=<输入采样率>,atempo=1.15`（升调 12% 更嫩 + 提速 15% 更像歌）。⚠️ **asetrate 必须用输入文件的真实采样率当基数**（MiMo 输出是 24000Hz）——当时误写 44100 导致 2 倍速花栗鼠音。
- **一次出 2~3 个风格变体让主人挑**，别一次一版来回拉锯。
- **知道 TTS 唱歌的上限**：克隆只模仿音色+大概旋律感，没有准确音高节拍。主人要"真正像唱歌"时，终极方案 = 主人自己清唱一遍（跑调无所谓）→ speech-to-speech 转音色（ElevenLabs `/v1/speech-to-speech` 可经 monid 调用，$0.12/分钟，见 monid 技能）。主动提出这条路，别在 TTS 上死磕。

## 替换既有视频音轨

画面已按旧配音时长渲染时：新配音逐段生成→量时长→`atempo` 微调进原段时长（±10% 听不出）→ concat 换轨。差距大就重渲该段动画。
