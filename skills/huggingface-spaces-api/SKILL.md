---
name: huggingface-spaces-api
description: "编程调用 HuggingFace Space API 时用，含 ZeroGPU 认证与 gradio 流程。"
---

# HuggingFace Space API 调用

## 快速判断：这个 Space 能不能调

1. 先取 `https://huggingface.co/spaces/<org>/<name>/agents.md`（新版 HF 给 AI Agent 的说明书）。
   存在则直接给出 API schema / 调用 / 轮询 / 上传端点，省去逆向。
2. 国内服务器：`huggingface.co` 直连超时，用镜像 `https://hf-mirror.com/...` 拿 agents.md / README / app.py；
   但实际推理端点 `<org>-<name>.hf.space` 通常**可以直连**，务必实测，别假设也被墙。

## Gradio API 三段式（标准流程）

```
1. GET  https://<host>.hf.space/gradio_api/info        # 参数 schema + 返回值结构
2. POST https://<host>.hf.space/gradio_api/upload      # 仅文件输入需要；multipart -F files=@f
   → 返回 ["/tmp/gradio/xxx/file.jpg"]
   传参时包装为 {"path": "<返回路径>", "meta": {"_type": "gradio.FileData"}, "orig_name": "file.jpg"}
3. POST https://<host>.hf.space/gradio_api/call/<endpoint>   # body {"data": [按info顺序的参数]}
   → {"event_id": "..."}
4. GET  https://<host>.hf.space/gradio_api/call/<endpoint>/<event_id>  # SSE 轮询
   直到出现 "event: complete" 或 "event: error"，解析 data: 后的 JSON
```

认证：所有请求加 header `Authorization: Bearer $HF_TOKEN`。
用户的 HF token 存于 `/root/.hf_token`（chmod 600），直接 `open('/root/.hf_token').read().strip()`。

## 坑（已踩过）

- **ZeroGPU 配额**：Space 页显示 "Running on Zero" 即 ZeroGPU。匿名调用常因单次 GPU 时长超限被拒
  （报 `The requested GPU duration (240s) is larger than the maximum allowed`）。
  解法只有一个：带 HF token（免费账号每日也有 GPU 秒数上限，PRO 更多）。这是稳定限制，重试无用。
- **枚举参数大小写敏感**：如 LocateAnything 的 `input_type` 必须是 `"Image"`/`"Video"`，
  传小写 `"image"` 不报参数错误，而是走错分支返回误导性错误（如 "Please upload a video"）。
  遇到莫名其妙的业务错误，先核对枚举值大小写。
- **取 Space 示例图**：`/config` 的 components 里 `example_inputs` 多为占位符，别指望；
  测试图可用 picsum 固定 id（`https://picsum.photos/id/237/800/600` 是狗）。
- Wikimedia、GitHub raw 在国内服务器均不可达；hf-mirror 是主力镜像。

## 返回值处理

`event: complete` 后的 `data:` 是一个数组，按 `/gradio_api/info` 的 returns 顺序对应。
Gradio FileData 结果带 `url` 字段（`gradio_api/file=...`），下载时同样要带 Bearer token。

## references/

- `references/locateanything.md` — nvidia/LocateAnything-3B 的完整调用参数、结果示例、自部署评估
