---
name: private-multi-device-sync-center-dev
description: 快速开发完全自主可控的私有资料同步系统，支持多设备同步、多用户权限控制、文件版本管理、自动备份，所有代码集中在单个目录，部署维护简单
version: 1.0.0
author: Hermes Agent
tags: [私有云, 文件同步, 多用户, 自主可控, 全栈开发]
related_skills: [web开发, 自动化部署]
---

# 适用场景
当用户需要完全自主可控的跨设备资料同步服务，不想依赖第三方网盘服务，需要私有化部署、多用户权限控制、自动备份功能时使用。

## 核心功能清单
1. ✅ 多设备实时同步：电脑/手机/平板/脚本任意设备对接，修改自动同步所有设备
2. ✅ 三级权限控制：普通用户（仅管理自己文件）/管理员（管理所有文件+用户）/超级管理员（系统级权限）
3. ✅ 文件版本管理：自动保留最近10个历史版本，支持随时回退
4. ✅ 永久化自动备份：每天自动备份所有文件+数据库，保留最近30天备份，支持误删恢复
5. ✅ Web管理界面：响应式设计，手机电脑都适配，支持浏览器直接上传下载管理文件
6. ✅ 开放API接口：支持脚本对接，实现自动备份、定时同步等扩展功能
7. ✅ 全链路日志：所有操作有日志记录，方便排查问题

## 技术栈选择
- 后端：FastAPI（高性能轻量，低资源占用，自动生成API文档）
- 前端：原生HTML/CSS/JS（无依赖，加载快，无需编译）
- 数据库：MySQL（存储用户信息、文件元数据、操作日志）
- 缓存/消息队列：Redis（实现实时同步通知、热点数据缓存、token管理）
- 存储：本地磁盘（可扩展对接对象存储）

## 项目目录规范（所有文件集中在单个目录，方便迁移维护）
```
/opt/private-sync-center/
├── backend/          # 后端核心代码
├── frontend/         # 前端页面代码
├── config/           # 配置文件、系统服务配置
├── backup/           # 自动备份脚本、历史备份文件
├── logs/             # 运行日志
├── storage/          # 文件存储目录
├── start.sh          # 一键启动脚本
├── stop.sh           # 停止服务脚本
├── restart.sh        # 重启服务脚本
└── README.md         # 项目说明文档
```

## 核心代码实现要点
### 1. 后端接口设计
- 所有接口统一返回格式：`{"code": 0, "msg": "xxx", "data": {}}`
- 权限校验通过FastAPI依赖注入实现，自动验证token和用户权限
- 实时同步通过Redis发布订阅机制实现，文件变更后自动推送通知到所有在线设备
- 密码采用SHA256加密存储，不会明文保存
- token有效期7天，自动过期，保障安全

### 2. 前端页面设计
- 纯原生实现，无任何第三方依赖，加载速度快，兼容性好
- 响应式布局，适配手机、平板、电脑不同屏幕尺寸
- 支持拖拽上传，操作简单，符合普通用户使用习惯
- 管理员和普通用户自动显示对应功能菜单，权限隔离

### 3. 备份策略设计
- 自动备份脚本每天凌晨2点执行，备份内容包含全量数据库+所有文件
- 自动删除30天前的备份，避免磁盘空间占用过高
- 支持手动触发备份，备份文件按时间戳命名，方便恢复

## 部署步骤
1. 环境依赖安装：`dnf install python3-PyMySQL python3-redis python3-fastapi python3-uvicorn -y`
2. 配置数据库和Redis连接信息，修改`backend/main.py`中的配置
3. 开放服务器端口：默认服务端口9966，确保MySQL和Redis端口允许服务器访问
4. 启动服务：`cd /opt/private-sync-center && ./start.sh`
5. 初始化超级管理员：访问`http://服务器IP:9966/docs#/默认/init_admin_api_init_admin_post`设置管理员密码，默认用户名`admin`
6. 设置开机自启：
```bash
cp config/private-sync-center.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now private-sync-center
```
7. 设置定时自动备份：执行`crontab -e`添加：`0 2 * * * /opt/private-sync-center/backup/auto_backup.sh >> /opt/private-sync-center/logs/backup.log 2>&1`

## 常见问题排查
1. 服务启动失败：查看`logs/backend.log`日志，检查数据库/Redis连接是否正常
2. 上传文件失败：检查`storage`目录权限是否为可写，磁盘空间是否足够
3. 同步不及时：检查Redis服务是否正常运行，发布订阅功能是否可用
4. 备份失败：检查`mysqldump`命令是否可用，备份目录权限是否正常