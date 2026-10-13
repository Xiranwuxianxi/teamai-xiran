# 图书带货视频 Skill

一个面向 Codex/Agents 的中文 Skill：从书名或飞书多维表格中的成稿文案出发，完成书籍核验、语义分镜、豆包配音、Pexels 开场、AI 配图、双语字幕和 OpenChatCut 可编辑视频初稿。

## 主要能力

- 支持“输入书名后原创文案”和“从飞书 Base 读取现成文案”两条路线。
- 首次使用自动检查软件、命令、API 配置和飞书只读权限，并给出缺失项安装指引。
- 飞书中存在同书多条记录时要求用户选择，不默认读取第一条。
- 配音只生成一条完整音频，以真实音频时长统一对齐画面和字幕。
- 字幕按标点与完整意群切分，避免把下一句话的词放进上一条字幕。
- 主书揭示后持续显示书名和作者，直至视频结束。
- 所有素材以独立可编辑项进入本机 OpenChatCut。

## 安装

```bash
git clone https://github.com/Kianzzz/book-sales-video.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R book-sales-video "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video"
```

安装后可这样触发：

```text
使用 $book-sales-video，根据《书名》制作一条图书带货短视频。
```

或：

```text
使用 $book-sales-video，读取我提供的飞书多维表格文案制作视频。
```

## 首次运行检查

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/check_environment.py" --json
```

使用飞书路线时：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/check_environment.py" \
  --json \
  --base-url "<飞书 Base URL>" \
  --lark-profile "<可选的 profile 名称>" \
  --script-field "<文案字段名>"
```

检查结果不会输出 API Key、App Secret 或访问令牌。缺失项会写入 `actions`，由 Agent 用中文解释安装、授权和复验方法。

## 依赖

- Python 3 与 `requests`
- FFmpeg / FFprobe
- 微信读书 Skill 与对应授权
- 豆包 TTS 配置
- Pexels API Key
- Codex 图像生成能力
- [OpenChatCut Desktop](https://github.com/0xsline/OpenChatCut)
- 飞书路线可选依赖：[lark-cli](https://github.com/larksuite/cli)

所有密钥只应保存在安全环境、系统钥匙串或工具自带的凭据存储中，不要提交到 Git，也不要发到对话中。

## 目录

- `SKILL.md`：中文主流程和决策规则
- `scripts/`：环境检查、配音、素材搜索和交付校验
- `references/`：文案、分镜、字幕、画面和剪辑规范
- `assets/`：视觉风格参考与轮播配置
- `agents/openai.yaml`：Codex 展示信息

## 许可证

MIT
