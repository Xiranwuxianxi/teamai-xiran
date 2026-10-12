---
name: hf-space-gradio-api
description: Use when 程序化调用 HuggingFace Space 的 Gradio API 做推理。含国内访问与配额坑。
---

# 调用 HuggingFace Space 的 Gradio API

## 国内服务器访问策略（实测 2026-09，腾讯云）
- `huggingface.co` 直连超时（被墙）→ 用镜像 `hf-mirror.com` 替换域名拉取页面/元数据（含 `/agents.md`）。
- `*.hf.space`（Space 实际推理端点）**可以直连**，无需镜像。
- `upload.wikimedia.org`、GitHub raw 直连均不通；找测试图可用 `picsum.photos/id/<id>/800/600`（id 237=狗，id 1025=巴哥犬，内容固定可知）。
- curl 一律加 `--noproxy '*'`。

## agents.md 规范
任意 Space 追加 `/agents.md` 即为给 AI Agent 的 API 说明书，列出 schema/调用/轮询/上传端点。先取它再动手。

## 三段式调用流程（详见 references/gradio-api-call-recipe.md）
1. `GET  https://<org>-<space>.hf.space/gradio_api/info` 拿参数 schema（参数名、顺序、默认值）。
2. 文件类输入先 `POST /gradio_api/upload`（multipart, name="files"），返回路径后包成 `{"path": ..., "meta": {"_type": "gradio.FileData"}, "orig_name": ...}` 传入。
3. `POST /gradio_api/call/<endpoint>` body `{"data": [...]}`（参数按 schema 顺序）→ 拿 `event_id` → 轮询 `GET /gradio_api/call/<endpoint>/<event_id>` 直到 SSE 出现 `event: complete`，解析 `data: [...]`。

## 场景方案
- **零样本声音克隆（中文人声，低配服务器友好）**：见 `references/voice-cloning-f5-tts.md`（F5-TTS Space 端点、参数 schema、企微收录音的坑）。

## 坑
- **ZeroGPU 配额**：匿名调用报 `'The requested GPU duration (240s) is larger than the maximum allowed'` → 所有请求（含 upload/轮询）加 `Authorization: Bearer $HF_TOKEN`。token 存 `/root/.hf_token`。
- **枚举参数大小写敏感**：如 LocateAnything 的 `input_type` 必须 `"Image"`，小写 `"image"` 会被误判成视频模式报 "Please upload a video"。报错信息和真实原因可能不对应，先怀疑枚举值。
- **prompt 驱动检测器别用泛词**：category 写 "objects" 会框整张图；写具体目标（dog/car/描述短语）。
- 轮询间隔 3s、上限约 5 分钟足够。
