# 小米 MiMo TTS / voiceclone API 配方（2026-10-11 实测可用）

凭证：`XIAOMI_API_KEY` / `XIAOMI_BASE_URL` 在 `/root/.hermes/.env`（base_url=`https://token-plan-cn.xiaomimimo.com/v1`）。三个模型：

| model | 用途 |
|---|---|
| `mimo-v2.5-tts` | 预置音色（冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean），支持情绪/方言/角色扮演 |
| `mimo-v2.5-tts-voicedesign` | 文本描述捏音色（user 消息=音色描述，必填） |
| `mimo-v2.5-tts-voiceclone` | **声纹克隆**（视频配音主力） |

## voiceclone 调用格式（坑：参考音频放 `audio.voice`，不是 `reference_audio`，后者 400）

```python
import json, base64, urllib.request
ref = base64.b64encode(open(ref_wav, 'rb').read()).decode()
payload = {
    "model": "mimo-v2.5-tts-voiceclone",
    "messages": [
        {"role": "user", "content": "用清脆悦耳的语调，明亮清晰"},   # 风格指令，可空串
        {"role": "assistant", "content": "要合成的文本"}              # 合成文本只能放 assistant
    ],
    "audio": {
        "format": "wav",
        "voice": f"data:audio/mpeg;base64,{ref}"   # ← 参考音频在这里
    }
}
req = urllib.request.Request(f"{base_url}/chat/completions",
    json.dumps(payload).encode(),
    {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
data = json.loads(urllib.request.urlopen(req, timeout=300).read())
audio = base64.b64decode(data['choices'][0]['message']['audio']['data'])
```

要点：
- 输出 base64 WAV 24kHz mono；长文本单段生成要 timeout=300s（150s 会超）。
- 风格指令实测有效：女声"清脆悦耳，明亮清晰，声音干净通透，保持自然温柔"；男声"磁性温暖，沉稳有力"。
- 预置音色版：`audio.voice` 换成音色名（如 `"冰糖"`），model 换 `mimo-v2.5-tts`。
- 参考音频 ≤10MB base64，mp3/wav；先跑声纹预处理（去静音+loudnorm，见 SKILL.md 音色精进节）。
- 无 ASR 端点；回听校验仍用 faster-whisper。

## 配套：audio/speech 端点（OpenAI 兼容）
`POST /audio/speech` `{"model":"mimo-tts-2.5","input":"...","voice":"mimo_preset_female_1"}` 也可用，但 chat/completions 形式才能带风格指令和声纹克隆。

## 声音资产（2026-10-11）
- 男声（启行）声纹：`/root/sbr-work/qihang-ref-v2.wav`；精进成品 `/root/sbr-work/qihang-v2-final.wav`(+.amr)
- 女声（林佳颖）声纹：`/root/sbr-work/linjiaying-ref.wav`；精进成品 `/root/sbr-work/linjiaying-clone-higher.wav`(+.amr)
- 全要素测试稿见本目录 `全要素测试稿.md`
