# nvidia/LocateAnything 调用实录（2026-09-03 验证）

Space: https://huggingface.co/spaces/nvidia/LocateAnything
模型: nvidia/LocateAnything-3B（Qwen2.5-3B 语言模型 + MoonViT-SO-400M 视觉编码器，Eagle VLM 家族）
代码: github.com/NVlabs/Eagle/tree/main/Embodied（论文 arXiv:2605.27365）
License: NVIDIA 非商业许可，仅学术/研究用途，商用禁止。

## 端点

唯一端点 `/run_inference`，参数按序：

| # | 参数 | 默认 | 说明 |
|---|------|------|------|
| 1 | input_type | 必填 | `"Image"` 或 `"Video"`（大写！小写会走错分支报误导错误） |
| 2 | image_file | None | FileData 包装 |
| 3 | video_file | None | FileData 包装 |
| 4 | task_type | "Detection" | |
| 5 | category | "objects" | ⚠️ 检测目标 prompt，必须具体（如 "dog"、"the red cup"）。泛词 "objects" 会把整张图框成一个框 |
| 6 | model_mode | "hybrid" | |
| 7 | temp | 0.7 | |
| 8 | top_p | 0.9 | |
| 9 | top_k | 20 | |
| 10 | short_size | None | |
| 11 | question_override | None | 自定义问题 |
| 12 | max_video_frames | 4 | 视频用 |

返回 3 个值：[标注图 FileData, 视频或 None, info dict]。
info dict 含 `success`、`detections`（label+coords，0–1000 归一化坐标）、`raw_text`、`stats`（耗时/tokens）。

实测：800×600 图检测 dog → 0.89s，10 tokens，框 [132,55,795,983] 准确。

## 自部署评估

- bf16 约需 7GB 显存；4-bit 量化约 3GB 内存。
- 2C2G CPU 服务器跑不动（内存不够 + CPU 推理慢）。有 GPU（≥8GB 显存）则轻松。
- ZeroGPU Space 每次请求申请 240s GPU，匿名用户直接被拒，必须带 token。
