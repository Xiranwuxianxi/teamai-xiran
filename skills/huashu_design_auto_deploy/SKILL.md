---
name: huashu_design_auto_deploy
description: Huashu Design生成的所有HTML作品自动部署到公网可访问的标准化流程，无需用户手动操作本地文件
version: 1.0.0
author: 药灵
tags: [部署, Huashu Design, 自动化, 静态页面]
---

# 触发条件
所有Huashu Design类产出（设计稿、原型、动画、展示页等HTML格式文件）生成完成后，自动触发本部署流程，无需用户提醒。

# 部署步骤（按优先级执行）
## 1. 优先用Nginx部署
```bash
# 检查Nginx配置的root目录
grep -r 'root /' /www/server/nginx/conf/nginx.conf /etc/nginx/nginx.conf 2>/dev/null | grep html | head -1 | awk '{print $2}' | sed 's/;//g'
# 复制HTML文件到Nginx root目录
cp <生成的HTML文件路径> <Nginx root目录>/<文件名>.html
# 验证访问
curl -s -o /dev/null -w "%{http_code}" http://localhost/<文件名>.html
```
访问地址格式：`http://118.89.90.232/<文件名>.html`

## 2. 降级方案：Python http.server临时部署
如果Nginx不可用/配置异常：
```bash
# 杀掉8000端口占用
pkill -f "python3 -m http.server 8000" || true
# 后台启动静态服务
cd /root && nohup python3 -m http.server 8000 > /tmp/http.log 2>&1 &
# 复制文件到/root目录
cp <生成的HTML文件路径> /root/
```
访问地址格式：`http://118.89.90.232:8000/<文件名>.html`

# 交付规范
部署完成后第一时间向用户返回：
✅ 作品已部署完成，访问地址：<完整访问链接>
无需用户询问路径、手动打开本地文件。

# 前置规则
每次会话启动时自动执行`skills_list`刷新技能列表，确保Huashu Design相关技能为最新版本，无需用户主动提醒刷新。