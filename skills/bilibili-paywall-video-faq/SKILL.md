---
name: bilibili-paywall-video-faq
title: B站付费/充电专属视频FAQ
description: B站充电专属(付费)视频无法通过技术手段免费获取的说明及实测方案对比
---

# B站付费/充电专属视频处理指南

## 触发条件
用户发来B站视频链接，要求下载/观看免费。检查视频元数据中 `is_upower_exclusive` 或 `is_upower_preview` 为 true 的情况。

## 特征
- B站API返回 `"is_upower_exclusive":true`
- 普通API调用仅返回低画质(360P)预览片段
- API返回 `"permission":"0"` 和 `"preview_toast"`
- 合集号里标记为「抢先看」「充电专属」

## 已知失效方案(已实测)

| 方案 | 结果 |
|------|------|
| yt-dlp 直接下载 | 412反爬风控 |
| B站官方API(qn=80/116/120) | 仅返回预览片段(几秒)，高清流被权限拦截 |
| you-get | 同412风控 |
| 第三方在线解析(biliob.com等) | 下载文件不完整/损坏 |
| Playwright+浏览器模拟 | playwright在受限环境装不上 |
| google-chrome headless | 412反爬，海外IP限制 |
| HD区player API | 付费墙拦截 |

## 真实原因
这是B站UP主充电专属内容，需要：
1. 用户B站账号已登录
2. 账号已给该UP主充值/充电
3. 持有效登录Cookie才能获取真实视频流

服务器没有任何合法技术手段能绕过B站付费墙。

## 可提供方案
1. **用户已有充电账号** → 提供B站Cookie，可下载
2. **用户未充电** → 建议去B站App充电后获取
3. **用户不想花钱** → 查找该视频是否在其他平台有分享(搜索引擎)
4. **合集内其他免费集** → 该系列公开集可免费下载
