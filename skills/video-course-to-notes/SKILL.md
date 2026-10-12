---
name: video-course-to-notes
description: Use when 用户发来视频课程合集要求整理学习笔记。音频下载→本地Whisper→子代理并行笔记→MD+网页。
---

# 视频课程转学习笔记全流程

## 流程总览

1. **合集枚举**：`api.bilibili.com/x/web-interface/view?bvid=xxx` 拿全部 pages（cid、标题、时长）存 pages.json
2. **字幕优先检查**：`x/player/v2?bvid=&cid=` 查 subtitle 轨——**无登录 cookie 时 B站 AI 字幕大概率拿不到**，不要反复试；直接问用户给 SESSDATA 或转 Whisper 本地方案
3. **只下音频轨**：`x/player/playurl?bvid=&cid=&qn=32&fnval=4048` → `dash.audio[0].backupUrl[0]`（Akamai CDN，国内服务器友好）→ ffmpeg 转 16kHz 单声道 wav。curl 必须 `--noproxy '*'`
4. **转写**：faster-whisper small int8（2核2G 服务器实测 ~2.7x 实时速），模型走 ModelScope `pengzhendong/faster-whisper-small`（HF 不通）。`initial_prompt` 塞课程领域术语，`beam_size=1`+`vad_filter=True`
5. **笔记生成**：按模块分批丢 delegate_task 子代理并行（每批 5-8 集），要求纠正 small 模型同音错字，每集固定结构：本集要点/核心概念/关键操作或代码/金句
6. **交付**：合并 MD 附件 + 亮色笔记网页（侧边目录+代码高亮）部署公网发链接

## 关键坑

- **tee 缓冲**：后台进程 `| tee log` 输出是块缓冲，开头几分钟日志为空不代表没在跑，用 `ps aux` 验证
- **Whisper small 中文同音错字必然存在**：笔记 prompt 必须要求按领域知识校正（如 ChagBT→ChatGPT、红沟→鸿沟），否则笔记全是错别字
- **2GB 内存**：small int8 峰值 ~700MB 可行；medium 不行。转写时别开其他重任务
- **MD→网页/Word**：`python-markdown`(fenced_code+tables+toc) 转 HTML；Word 用 scripts/md2docx.py（宋体+黑体标题+1.5倍行距+真表格）

## 支持文件

- `scripts/md2docx.py` — Markdown 转排版规整的中文 Word（标题/表格/代码/列表，宋体+Times）。用法：`python3 scripts/md2docx.py in.md out.docx`
