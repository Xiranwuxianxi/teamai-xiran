---
name: course-video-to-notes
description: B站等系列课程视频转结构化学习笔记。字幕/Whisper转录/笔记/网页交付全流程。
---

# 系列课程视频 → 学习笔记流水线

## 流程总览

合集信息 → 字幕（拿不到则 Whisper 转录）→ 分批写笔记（子代理并行）→ 合并 MD → 亮色网页交付。

## 1. 获取合集信息（无需浏览器）

```bash
curl -s --noproxy '*' 'https://api.bilibili.com/x/web-interface/view?bvid=BVxxx' -H 'User-Agent: Mozilla/5.0'
# data.pages[] = {page, part, duration, cid}；data.title / data.owner.name
```

## 2. 字幕：先试 API，空了走 Whisper

- `x/player/v2?bvid=&cid=` 与 `x/player/wbi/v2` 的 `subtitle.subtitles`：**未登录（仅 buvid3）时对 AI 字幕课程一律返回空数组**。要 AI 字幕必须用户提供 SESSDATA cookie，别反复试。
- 无字幕时的本机转录路线（2vCPU/2GB 实测可行）：
  1. **只下音频轨**：playurl API（`fnval=4048`）→ `dash.audio[0].backupUrl[0]`（Akamai CDN，服务器 IP 友好）→ `ffmpeg -i a.m4s -vn -ac 1 -ar 16000 pXX.wav`。28 集/7.4h ≈ 500MB，几分钟下完。
  2. **faster-whisper small**：`pip install faster-whisper`（腾讯镜像）；模型走 ModelScope：`snapshot_download('pengzhendong/faster-whisper-small')`（HF 国内不可达）。`WhisperModel(path, device="cpu", compute_type="int8", cpu_threads=2)`，`language="zh"`，`initial_prompt` 填课程领域词汇，`vad_filter=True, beam_size=1`。
  3. **速度**：约 2.7x 实时（7 分钟音频≈153s），峰值内存 <800MB，2GB 机器可跑。逐集落盘 .txt，天然支持断点续跑。

## 3. 转写质量与术语校正

small 模型同音错字多（ChatGPT→ChagBT、thread_id→Slide ID、checkpointer→切克帕尔特）。**笔记生成 prompt 里必须显式要求按领域知识校正术语**，子代理会做得很好；不给这句就会照抄错字。

## 4. 笔记生成：分批子代理并行

- 每批 7~8 集派一个子代理（delegate_task），要求通读转录稿全文后按固定模板写：本集要点 / 核心概念 / 关键操作或代码（可运行代码块）/ 金句记忆点。
- 合并为总 MD，再生成亮色单页 HTML（侧边目录 + highlight.js 代码高亮），部署 `/root/public/` 发公网链接。

## 5. 交付

MD 走 MEDIA 附件；网页发公网链接并提醒"裸 IP 可能被微信/QQ拦截，复制到浏览器"。

## 坑

- B站 API 需 `User-Agent` + `Referer: https://www.bilibili.com/`；backupUrl 含时效参数，取到尽快下。
- tee 管道输出是块缓冲的，后台任务日志迟迟不出不代表没跑——看进程和输出文件。
