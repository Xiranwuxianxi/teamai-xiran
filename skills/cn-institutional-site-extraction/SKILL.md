---
name: cn-institutional-site-extraction
description: Use when 抓取国内高校/政务官网失败或正文是图片。JS质询绕过+图片正文OCR提取。
---

# 国内机构官网内容提取

国内高校教务处、政务公告站常见问题：WAF JS 质询、正文做成防复制图片、
站内搜索对子页面无效。本技能给出已验证的提取链路。

## 问题1：瑞数类 JS cookie challenge

**识别**：curl/web_extract 返回的不是 HTML 页面，而是一段混淆 JS
（`_0x17beeb` 式变量名、数组排序、最终写 document.cookie 后 reload）。

**解法（2026-09 在 jwc.sandau.edu.cn 验证）**：不依赖 browser daemon，直接 headless Chrome 渲染：

```bash
timeout 90 google-chrome --headless=new --no-sandbox --disable-gpu \
  --user-data-dir=/tmp/chrome-prof-$$ --virtual-time-budget=20000 \
  --dump-dom "https://目标URL" 2>/dev/null > /tmp/page.html
```

坑：
- `--virtual-time-budget` 必须给足（≥15000ms），challenge 要跑完并二次加载。
- **每次用独立 user-data-dir**：与已在运行的 Chrome 抢 profile 锁会输出 0 字节。
- 国内服务器直连时 curl 一律 `--noproxy '*'`。

## 问题2：正文是整张大图（校历/红头文件）

1. dump 出的 HTML 里 grep 图片路径，机构站多为 `_upload/article/images/...jpg`。
2. **带 Referer 下载**：`curl -e "https://站点域名/"`（不带可能 403）。
3. 读内容用 `mcp__filesystem__read_media_file` 直接看图。
4. 关键信息（日期、编号）用 tesseract 交叉验证：
   `tesseract img out -l chi_sim`。表格类图 OCR 错误率高，
   日期必须视觉+OCR 双确认再下结论。
5. 发给用户：cp 到 `/root/public/` 走公网 URL 嵌入发送，同时附官方原文链接。

## 参考
- `references/case-sandau-xiaoli.md` — 杉达教务处校历提取完整实录。
