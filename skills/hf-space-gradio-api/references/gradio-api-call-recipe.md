# Gradio API 调用配方（以 nvidia/LocateAnything 实测为例）

## 端点（把 nvidia-locateanything 换成目标 Space 的 <org>-<space>）
- Schema: `GET https://nvidia-locateanything.hf.space/gradio_api/info`
- 上传: `POST .../gradio_api/upload` multipart, 字段名 `files` → 返回 `["/tmp/gradio/<hash>/<name>"]`
- 调用: `POST .../gradio_api/call/run_inference` body `{"data": [...]}` → `{"event_id": "..."}`
- 轮询: `GET .../gradio_api/call/run_inference/<event_id>` → SSE 文本，等 `event: complete`，同一响应里 `data: [...]` 是结果 JSON
- 结果文件: `GET .../gradio_api/file=<path>`

所有请求带头：`Authorization: Bearer $(cat /root/.hf_token)`

## LocateAnything /run_inference 参数顺序（2026-09-03 实测）
`[input_type, image_file, video_file, task_type, category, model_mode, temp, top_p, top_k, short_size, question_override, max_video_frames]`
示例：`["Image", {"path": up, "meta": {"_type": "gradio.FileData"}, "orig_name": "dog.jpg"}, None, "Detection", "dog", "hybrid", 0.7, 0.9, 20, None, None, 4]`

返回：`[标注图FileData, None, {"success": true, "detections": [{"label","type":"box","coords":[x1,y1,x2,y2]}], "raw_text", "stats", ...}]`，coords 归一化到 0–1000。

## Python 实现要点
urllib 标准库够用（无需 requests）；upload 用手写 multipart boundary；轮询每 3s 一次，匹配 `"event: complete"` 后用 `re.search(r"data: (\[.*\])", txt, re.S)` 提取结果。

## 测试图源（国内可达）
`https://picsum.photos/id/<id>/800/600` — id 237=黑狗正面照，id 1025=巴哥犬裹毯子。内容固定，适合做确定性演示。
