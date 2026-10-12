# 零样本声音克隆：F5-TTS Space（实测 2026-10-07）

低配服务器（2核2G）跑不动本地克隆模型，直接用 HF Space 远程推理，30秒干净参考音频即可克隆中文人声。

## 可用端点
- Space：`mrfakename/E2-F5-TTS` → 端点 `https://mrfakename-e2-f5-tts.hf.space`（国内直连可达，2026-10 实测）
- `funaudiollm-cosyvoice2-0-5b` 的 /gradio_api/info 当时返回 HTML 而非 JSON（不可用或未开 API），用 F5 那个。

## /predict 参数（顺序固定）
1. `ref_audio` — FileData（先 POST /gradio_api/upload，multipart name="files"；参考音频转 16k/24k 单声道 wav 再传）
2. `ref_text` — 参考音频的逐字文稿（必须和录音内容一致，错字会影响音色对齐）
3. `gen_text` — 要生成的文本
4. `remove_silence` — bool，建议 true

## 调用要点
- 所有请求（upload/call/轮询）带 `Authorization: Bearer $(cat /root/.hf_token)`。
- 轮询 SSE 直到 `event: complete`，结果 data[0].url 可直接 curl 下载 wav。
- 短句生成很快（秒级）；异常短的输出（如28字只出2.3s）说明可能被截断，换长句重试或检查 gen_text。
- 生成后 ffmpeg 转 mp3 交付；视频配音直接替换音轨再 mux。

## ⚠️ 最关键的坑：参考音频必须 ≤15 秒（2026-10-07 实测）
F5-TTS 训练时总长（ref+gen）上限约 30s。**参考音频给 30s 以上，输出必然又快又糊**（语速模型崩掉），不是素材质量问题。
正确做法：
1. 长录音先切出 9–15s 干净连续语音：`ffmpeg -i ref.wav -af silencedetect=noise=-30dB:d=0.25 -f null - 2>&1 | grep silence_` 找句读边界，挑内容覆盖好的一段（含数字/平翘舌更好），按边界 `-ss/-to` 切。
2. `ref_text` 只写**这一小段**的逐字文稿（含标点），不是整段录音的文稿；对不上 = 音色崩。
3. 健康信号：生成约 4–5 字/秒；异常信号：>10 字/秒（如 22 字只出 1.4s）→ ref 过长或 ref_text 不匹配。

## 配音后处理链（更舒服，保住本人音色）
```sh
ffmpeg -i seg.wav -af "highpass=f=80,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,equalizer=f=200:t=q:w=1.2:g=1.5,deesser=i=0.25,loudnorm=I=-16:TP=-1.5,atempo=<比例>" -ar 44100 out.wav
```
- 节奏/停顿靠 gen_text 里的标点和断句控制，比硬调参数自然。
- 对齐已有视频段时长：atempo = 音频时长/视频时长，±6% 内听不出变形；差太多用 apad 补静音，别狂拉。

## 收集用户参考录音的坑（企微场景）
- **企微语音消息会被平台自动转成文字，音频文件到不了 Agent 手里**。必须让用户走「+ → 文件」把录音当附件发（m4a/mp3 都行）。
- 录音要求写清楚：安静环境、正常距离防喷麦、无背景音、自然说话状态。手机录音机App 30–60s 即可。
- 收到 m4a 后：`ffmpeg -i in.m4a -ar 16000 -ac 1 ref.wav`，再按上面「≤15秒」规则切片后上传。
- 让用户录的素材稿最好自带数字、平翘舌、语气起伏（声纹覆盖面），并让用户把念的原文发回来备用——但最终 ref_text 以切片实际内容为准。
