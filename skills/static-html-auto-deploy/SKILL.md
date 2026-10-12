---
name: static-html-auto-deploy
description: 任意HTML页面一键公网部署，自动返回可直接点击的访问链接，无需手动配置服务器
version: 1.0.0
author: Hermes Agent
tags: ["前端部署", "静态页面", "公网访问", "自动化"]
---
## 前置条件
已完成服务器部署配置（一次配置永久生效）：
1. 服务器公网IP：118.89.90.232
2. 已通过Docker部署Nginx静态服务，容器映射本地目录`/root/public/`到Nginx静态资源目录
3. 80端口已开放防火墙/安全组，外网可正常访问
## 自动化部署流程
生成HTML文件后自动执行以下步骤：
1. 拷贝HTML文件到静态服务目录：`cp ${HTML_FILE_PATH} /root/public/`
2. 设置文件权限，确保可访问：`chmod 755 /root/public/$(basename ${HTML_FILE_PATH})`
3. 单独返回访问链接给用户：
```
http://118.89.90.232/$(basename ${HTML_FILE_PATH})
```
⚠️ 注意事项：链接必须单独发送，不要和其他文本内容合并，确保用户可直接点击访问
补充（2026-08实测）：SKILL.md 等技能文档文件也允许放静态目录供下载分享；QQ/微信内可能拦截裸IP http 链接，发链接时提醒用户复制到系统浏览器打开。
## 部署前检查清单

部署前确认：
1. HTML 文件有实际功能（交互/计算/可视化），不只是静态展示
2. 亮色主题（用户明确拒绝暗色）
3. 单文件，所有 CSS/JS 内嵌，无外部依赖（除 CDN）
4. 有示例数据，打开就能体验
5. 纯前端运行，数据不上传服务器

## 部署后验证

1. 用 browser_navigate 访问 URL，确认页面加载正常
2. 用 browser_vision 截图，确认视觉效果
3. 如有交互功能，点击测试确认可用
4. 将访问链接单独发送给用户

## 从"静态页面"到"简历资产"

用户已明确表示：**不要只做信息推送类任务，要创造可复用、可展示、能写进简历的硬资产。**

因此部署的 HTML 应定位为 **portfolio tool** 而非 static page：
- 有明确的使用场景（如 K8s 安全巡检、数据分析、代码生成）
- 有输入→处理→输出的完整流程
- 有可视化结果（图表、评分、报告）
- 代码结构清晰，面试时能讲清楚
- 后续可迭代（加功能、写文章、开源）

## 故障排查：文件存在但公网 404（bind mount 失效，2026-07 实测）

**症状**：文件已在 `/root/public/` 且权限 755，`docker inspect` 挂载配置正常，但公网 URL 全部 404（包括以前能访问的旧文件）。

**根因**：系统定期清理 `/tmp`（systemd-tmpfiles），`/root/public` 被删除后重建。Docker bind mount 仍指向**已删除的旧目录 inode**，容器内看到的 `/usr/share/nginx/html` 是悬空的旧 inode → nginx 全站 404。

**诊断链路**（按序执行，逐步确认）：
```bash
# 1. 挂载配置看着正常（不能说明问题）
docker inspect static-nginx --format '{{json .Mounts}}' | grep -E 'Source|Destination'
# 2. 关键证据：容器内目录是空的（宿主有文件 ≠ 容器看得到）
docker exec static-nginx ls /usr/share/nginx/html/
# 3. docker cp 会"假成功"：exit 0 但文件不出现（写进了旧 inode 黑洞）
docker cp /root/public/x.png static-nginx:/usr/share/nginx/html/  # 无效
# 4. 实锤：容器内直接写文件报 "nonexistent directory"
docker exec static-nginx sh -c 'echo t > /usr/share/nginx/html/t.html'
```

**修复**：`docker restart static-nginx` 重新绑定到新 inode，1~2 秒完成、无数据风险。
⚠️ 用户铁律：**操作 Docker 前必须先问用户许可**，即使是无害重启。

**临时降级**（未获授权时）：图片/文件直接 `MEDIA:` 原生发送；勿尝试 `docker cp`（无效）、勿开端口替代品（公网 8080 有别的服务占用会 502）。

**长期预防（✅ 已完成 2026-08-20，用户授权）**：static-nginx 已重建，挂载从 `/tmp/static` 改为 `/root/public`（持久化目录，不受 /tmp 清理影响），并加 `--restart unless-stopped`。重建命令备查：
```bash
docker stop static-nginx && docker rm static-nginx
docker run -d --name static-nginx --restart unless-stopped -p 80:80 \
  -v /root/public:/usr/share/nginx/html nginx:alpine
```
**注意**：`/tmp/static` 已弃用，新文件一律放 `/root/public/`。若发现老文件 404（如 sysmonitor.html 曾是清理受害者），先查项目源码目录（如 `/root/sysmonitor/frontend/dist/`）有没有母本，直接 cp 恢复。

## 语音文件（text_to_speech）公网部署链路（2026-08-20 实测）

cron任务若指示语音存到 `/tmp/static/xxx.mp3` 并推送 `http://118.89.90.232/xxx.mp3`，实际需三步才能通：
1. `text_to_speech` 即使用 output_path 指定 `.mp3`，**实际生成的是 `.ogg`**（Ogg Opus）→ 需转码：
   `ffmpeg -y -i /tmp/static/xxx.ogg -codec:a libmp3lame -q:a 4 /tmp/static/xxx.mp3`
2. `/tmp/static` 已弃用，**必须 `cp /tmp/static/xxx.mp3 /root/public/xxx.mp3`** 才能被 nginx 服务
3. 部署后验证再发链接：`curl -s -o /dev/null -w "%{http_code}" --noproxy '*' http://118.89.90.232/xxx.mp3` 返回 200 才算成功（直连加 --noproxy '*'，代理可能未运行）

## 成功案例

**K8s Security Auditor** (`k8s-security-auditor.html`)
- 功能：粘贴 K8s YAML → 自动安全巡检 → 评分+可视化报告
- 技术：原生 JS + js-yaml + Chart.js
- 访问：http://118.89.90.232/k8s-security-auditor.html
- 简历写法："独立开发 K8s 安全巡检工具，支持 12 项安全规则自动检查，实现浏览器本地 YAML 解析与可视化报告生成"
