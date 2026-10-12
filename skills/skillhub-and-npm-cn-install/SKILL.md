---
name: skillhub-and-npm-cn-install
description: SkillHub商店安装+npm国内镜像加速+mcporter+tencent-docs授权完整流程，补充ClawHub之外的技能安装渠道
version: 1.0.0
author: 药灵
tags: ["devops", "技能安装", "国内加速", "SkillHub", "腾讯文档"]
---

## SkillHub 商店安装（ClawHub替代方案）

SkillHub是国内技能商店，有加速+合规能力，部分技能在ClawHub找不到但在SkillHub有。

### 安装SkillHub CLI + 默认技能
```bash
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash
```
- CLI路径：`/root/.hermes/home/.local/bin/skillhub`
- 自动安装 `find-skills` 和 `skillhub-preference` 两个辅助技能

### 仅安装CLI（不装默认技能）
```bash
curl -fsSL https://skillhub-1388575217.cos.ap-guangzhou.myqcloud.com/install/install.sh | bash -s -- --cli-only
```

### 搜索和安装技能
```bash
export PATH="/root/.hermes/home/.local/bin:$PATH"
skillhub search <关键词>      # 搜索技能
skillhub install <技能名>      # 安装技能
```
- 安装路径同ClawHub：`/root/.hermes/hermes-agent/skills/<技能名>/`

---

## npm国内镜像加速（安装mcporter等npm全局包）

国内服务器npm默认源经常超时，**必须加国内镜像**：

```bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && nvm use 20
npm install -g mcporter --registry=https://registry.npmmirror.com
```

### 避坑
- 不加`--registry=https://registry.npmmirror.com`的话，国内服务器npm install大概率超时
- mcporter是MCP协议技能的依赖，tencent-docs等技能需要

---

## tencent-docs授权流程

tencent-docs技能安装后需要授权才能使用，依赖mcporter。

### 第一步：检查状态/发起授权
```bash
cd /root/.hermes/hermes-agent/skills/tencent-docs && bash ./setup.sh tdoc_check_and_start_auth
```
- 返回 `READY` → 已授权，直接用
- 返回 `AUTH_REQUIRED:<url>` → 需要用户在浏览器打开url完成授权（微信/QQ扫码）
- 返回 `ERROR:*` → 见下方错误表

### 第二步：用户确认完成授权后获取Token
```bash
cd /root/.hermes/hermes-agent/skills/tencent-docs && bash ./setup.sh tdoc_fetch_token
```
- 返回 `TOKEN_READY` → 授权成功
- 返回 `ERROR:not_authorized` → 用户还没完成授权，等用户确认后重试
- 返回 `ERROR:expired` → 授权码过期，重新执行第一步

### 人工兜底：手动设置Token
```bash
mcporter config add tencent-docs "https://docs.qq.com/openapi/mcp" \
    --header "Authorization=$Token" \
    --transport http \
    --scope home
```

### 关键提醒
- ⛔ 收到AUTH_REQUIRED后，**必须先向用户展示授权链接，等用户回复确认后再执行第二步**
- 授权链接有效期5分钟，超时需重新发起
