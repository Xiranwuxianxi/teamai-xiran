---
name: openclaw-gateway-operation
description: OpenClaw Gateway的启动、配置、故障排查与插件管理完整指南。包含常见启动失败原因分析和修复方法。
version: 1.1
author: 药灵
---

# OpenClaw Gateway 运维指南

## 触发条件
- 用户要求安装/配置/启动 OpenClaw
- OpenClaw Gateway 启动失败，报配置校验错误
- 需要安装 OpenClaw 插件或管理 skills
- 需要将阶跃星辰/Kimi等模型配置到 OpenClaw

## 基础配置

| 用途 | 路径 |
|------|------|
| 主配置 | `~/.openclaw/openclaw.json` |
| 日志 | `/tmp/openclaw/` |
| workspace | `~/.openclaw/workspace/` |
| skills 目录 | `~/.openclaw/workspace/skills/` |
| 插件目录 | `~/.openclaw/extensions/` |

## Agent 人格設定

OpenClaw Agent 的 workspace 目录是 `~/.openclaw/workspace/`。默認只有模板文件，需要手動補全才能讓 Agent 有完整人格：

- `IDENTITY.md` — Agent 自我認知（名字、氣質）
- `USER.md` — 用戶信息（背景、喜好、雷區）
- `SOUL.md` — 核心價值觀、行爲準則

## 注意事项

- **`openclaw config set` 会截断长 API key**：长key会被截断为 `xxx...xxx` 格式，必须直接编辑 json 文件写入完整key
- **openclaw workspace 路径**：真正目录是 `~/.openclaw/workspace/`，不是其他同步目录

## 阶跃星辰 API 配置

```json
{
  "models": {
    "providers": {
      "stepfun": {
        "baseUrl": "https://api.stepfun.com/step_plan/v1",
        "apiKey": "<your-api-key>",
        "api": "openai-completions",
        "models": [{
          "id": "step-3.5-flash-2603",
          "name": "Step 3.5 Flash",
          "input": ["text"],
          "contextWindow": 32000,
          "maxTokens": 4096
        }]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": "stepfun/step-3.5-flash-2603"
    }
  }
}
```

通过 CLI 配置：
```
openclaw config set models.providers.stepfun.baseUrl "https://api.stepfun.com/step_plan/v1"
openclaw config set models.providers.stepfun.apiKey "<your-key>"
openclaw config set agents.defaults.model "stepfun/step-3.5-flash-2603"
```

## Gateway 启动

**前台启动（兜底方案）**：
```bash
export NODE_COMPILE_CACHE=/var/tmp/openclaw-compile-cache
mkdir -p /var/tmp/openclaw-compile-cache
export OPENCLAW_NO_RESPAWN=1
nohup openclaw gateway --port 18789 > /tmp/openclaw-gateway.log 2>&1 &
```

**重要**：`OPENCLAW_NO_RESPAWN=1` 防止进程自动守护重生，否则 pkill 后进程会立即被重新拉起。

**systemd 开机自启**：创建 service 文件并 enable

## 常见故障：OpenClaw 全局安装依赖缺失

### 现象

执行 `openclaw` 命令或启动 gateway 时报 `Cannot find package 'xxx'`。原因是 `npm install -g openclaw` 时依赖树不完整，部分 scoped packages 未正确安装到全局。

### 修复方法

查看 openclaw 的 package.json 获取完整依赖列表：
```bash
cat /usr/local/lib/node_modules/openclaw/package.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(*d.get('dependencies',{}), sep='\\n')"
```

批量安装已知常缺失的包：
```bash
# Scoped packages
npm install -g @openclaw/proxyline @openclaw/fs-safe
npm install -g @modelcontextprotocol/sdk
npm install -g @earendil-works/pi-agent-core @earendil-works/pi-ai @earendil-works/pi-coding-agent @earendil-works/pi-tui
npm install -g @agentclientprotocol/sdk @clack/core @clack/prompts
npm install -g @google/genai @grammyjs/runner @grammyjs/transformer-throttler
npm install -g @homebridge/ciao @lydell/node-pty @mozilla/readability
npm install -g markdown-it --force  # --force 绕过 bin 冲突
npm install -g openai dotenv json5 tslog chalk
npm install -g ipaddr.js commander croner express file-type grammy jiti jszip
npm install -g kysely linkedom pdfjs-dist playwright-core qrcode quickjs-wasi
npm install -g tar tokenjuice tree-sitter-bash typebox typescript undici
npm install -g web-push web-tree-sitter ws yaml zod chokidar ajv
```

## 常见故障：openclaw-stepfun 插件协议版本不匹配（protocol mismatch）

**现象**：Gateway 日志显示 `protocol mismatch`，如：
```
ws] protocol mismatch conn=... remote=stepfun-plugin-loopback backend v0.2.21 min=3 max=3 expected=4
```
后面跟着 `ws closed code=1002 reason=protocol mismatch`。Gateway 虽然 `ready`，但 agent 无法响应，QQ Bot 收到消息后返回 "Something went wrong"。

**原因**：`openclaw-stepfun` 插件的 WebSocket 协议版本（v0.2.x，协议版本号=3）与 openclaw 主程序（2026.5.20+，要求协议版本号=4）不匹配。即使 `npm install -g openclaw-stepfun@latest` 装到最新版（如 0.2.27），协议版本可能仍未更新。

**修复方法**：

**方案A：升级 stepfun 插件（若新版本已修复）**
```bash
npm install -g openclaw-stepfun@latest
pkill -9 -f openclaw
sleep 2
rm -f /root/.hermes/home/.openclaw/agents/main/sessions/*.jsonl*
export OPENCLAW_NO_RESPAWN=1
nohup openclaw gateway --port 18789 > /tmp/openclaw-gateway.log 2>&1 &
```

**方案B（推荐，当升级无效时）：禁用 stepfun channel**
在 `~/.openclaw/openclaw.json` 中将 stepfun channel 的 `enabled` 设为 `false`：
```json
"stepfun": {
  "enabled": false,
  "appId": "...",
  "appToken": "..."
}
```
注意：禁用 stepfun channel 后，agent 的默认模型仍指向 stepfun，但 gateway 不再尝试建立 stepfun WebSocket 连接。此时 QQ Bot 可以正常连接和接收消息。

如果 agent 仍因模型指向 stepfun 而无法响应，需要将 agent 的默认模型改为其他可用的 provider（如 openai/deepseek 等），或在 `agents.list` 中为 QQ Bot 单独指定模型。

**方案C：直接调 API 验证模型连通性**
```bash
curl -s -X POST "https://api.stepfun.com/step_plan/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-key>" \
  -d '{"model": "step-3.5-flash", "messages": [{"role": "user", "content": "你好"}]}'
```

## 直接与七七（Agent）对话方式

OpenClaw 提供两种直接对话方式，不需要走 gateway 的 REST API：

### 方式1：交互式聊天终端（推荐）
```bash
openclaw chat --local
```
进入一个 TUI（终端UI）界面，可以直接跟 agent 对话，类似命令行版的微信聊天。

### 方式2：单条消息模式（非交互）
```bash
# 清理旧的 session 文件防止冲突
rm -f /root/.hermes/home/.openclaw/agents/main/sessions/<session-id>.jsonl*

# 发送一条消息
openclaw agent --local --message "你的问题" --session-id main --timeout 30

# 查看回复（在 session 日志中）
tail -5 /root/.hermes/home/.openclaw/agents/main/sessions/main.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        if d.get('type')=='message' and d.get('message',{}).get('role')=='assistant':
            content = d['message']['content']
            if isinstance(content, list):
                text = ''.join([c.get('text','') for c in content if c.get('type')=='text'])
            else:
                text = content
            print('回复:', text[:500])
    except: pass
"
```

**常见错误**：`EmbeddedAttemptSessionTakeoverError: session file changed while embedded prompt lock was released`
- **原因**：上一次 agent 调用还没完全结束就发起了新调用，或者 session 文件被手动修改过
- **修复**：先删掉冲突的 session 文件 `rm -f ~/.openclaw/agents/main/sessions/<session-id>.jsonl*`

## 常见故障：wizard.lastRunMode 校验错误

**现象**：日志显示 `wizard.lastRunMode: Invalid input (allowed: "local", "remote")`

**原因**：`openclaw doctor --fix` 写入的 `wizard.lastRunCommand: "doctor"` 导致额外的运行时校验不通过。

**修复方法**：
```bash
# 正确设置值（注意引号嵌套）
openclaw config set wizard.lastRunMode '"local"'

# 或删除整个 wizard 字段
openclaw config unset wizard

# 重置 systemd 重新尝试
systemctl reset-failed openclaw-gateway.service
systemctl restart openclaw-gateway.service
```

**重要**：`openclaw config validate` 说配置有效 ≠ Gateway 能启动，Gateway 有额外运行时校验。

## Kimi Claw 安装

```bash
bash <(curl -fsSL https://cdn.kimi.com/kimi-claw/claw-install.sh) --bot-token <token>
```

安装内容：kimiim-cli（群聊CLI工具）、kimi-claw 插件（bridge插件）、3个skills

**注意**：插件注册步骤可能报 `Plugin not found`，但文件已解压到 `~/.openclaw/extensions/kimi-claw/`，Gateway 重启时会 auto-discover 并加载。

## QQ Bot 插件安装（@tencent-connect/openclaw-qqbot）

### 前置依赖

确保 openclaw 的所有全局依赖已安装（见上方"依赖缺失"章节），否则 gateway 无法启动。

### 安装命令

```bash
# 使用淘宝镜像加速
npm config get registry  # 确认是 https://registry.npmmirror.com
npm install -g @tencent-connect/openclaw-qqbot@latest
```

### 注册插件（auto-discover）

创建符号链接让 OpenClaw auto-discover 插件：

```bash
mkdir -p ~/.openclaw/extensions
ln -sf /usr/local/lib/node_modules/@tencent-connect/openclaw-qqbot ~/.openclaw/extensions/openclaw-qqbot
```

### 配置文件

**不要用 `openclaw channels add` CLI 命令**（可能因依赖缺失而报错）。直接在 `~/.openclaw/openclaw.json` 手动编辑：

```json
{
  "channels": {
    "qqbot": {
      "enabled": true,
      "appId": "你的BotAppID",
      "clientSecret": "你的ClientSecret"
    }
  },
  "plugins": {
    "entries": {
      "openclaw-qqbot": {
        "enabled": true
      }
    }
  }
}
```

**配置字段说明**：
- `appId` + `clientSecret`：QQ 开放平台的 Bot 凭据（**不是** `token` 字段）
- 如果你收到冒号分隔的凭据 `appId:clientSecret`，拆开分别填入这两个字段
- 支持多账号：用 `accounts` 对象，如 `"accounts": { "main": { "appId": "...", "clientSecret": "..." } }`
- 可选配置：`imageServerBaseUrl`（图片服务器）、`allowFrom`（白名单列表）、`systemPrompt`（自定义系统提示）

### 启动与验证

```bash
export OPENCLAW_NO_RESPAWN=1
pkill -9 -f openclaw
sleep 2
rm -f ~/.openclaw/agents/main/sessions/*.jsonl*  # 清理 session 避免冲突

nohup openclaw gateway --port 18789 > /tmp/openclaw-gateway.log 2>&1 &
sleep 15

# 检查启动状态
grep -E "listening|ready" /tmp/openclaw-gateway.log
curl -s http://127.0.0.1:18789/health  # 应返回 {"ok":true,"status":"live"}

# 检查 QQ Bot 连接
grep "Access token\|WebSocket\|Gateway ready" /tmp/openclaw-gateway.log
```

**正常启动日志链**：
```
Access token obtained successfully
WebSocket connected
Hello received
Ready with 群聊+私信+频道+交互
Gateway ready
```

### 验证 Bot 在线

在 QQ 中给 Bot 发一条私聊消息，或者在群里 @Bot。如果返回 "Something went wrong"，检查：
1. 日志中是否有 `protocol mismatch` → 禁用 stepfun channel
2. 日志中是否有 `session file changed` → 清理 session 文件后重启
3. 日志中是否有 `Cannot find package` → 补装缺失的 npm 包

## 常见故障：插件安装后 QQ Bot 不回复 / 返回 "Something went wrong"

### 检查顺序

1. **确认插件已注册**：`grep "openclaw-qqbot" /tmp/openclaw-gateway.log`
   - 应看到 `discovered non-bundled plugins: ... openclaw-qqbot`
   - 应看到 `http server listening (X plugins: ..., openclaw-qqbot, ...)`

2. **确认 QQ Bot 已连接**：`grep "Gateway ready" /tmp/openclaw-gateway.log`
   - 应看到 `[qqbot] [qqbot:default] Gateway ready`

3. **确认 token 获取成功**：`grep "Access token" /tmp/openclaw-gateway.log`
   - 应看到 `[qqbot] ✅ Access token obtained successfully`

4. **确认 agent 模型可访问**：发一条消息后检查日志
   - 如果看到 `protocol mismatch` → 禁用 stepfun channel
   - 如果看到 `EmbeddedAttemptSessionTakeoverError` → 清理 session 文件

### 根因判断

| 现象 | 原因 | 修复 |
|------|------|------|
| QQ Bot 在线但回复 "Something went wrong" | stepfun 协议不匹配导致 agent 崩溃 | 禁用 stepfun channel |
| QQ Bot 完全无响应 | 插件未注册 / token 无效 | 检查插件注册和凭据 |
| 第一次消息成功，后续失败 | session 文件冲突 | `rm -f *.jsonl*` 后重启 |
| Gateway 启动报依赖缺失 | npm 全局安装不完整 | 批量安装缺失包 |

## 数据目录

QQ Bot 数据存储位置：`~/.openclaw/qqbot/`

## 验证运行状态

```bash
grep -E "listening|ready|fail" /tmp/openclaw-gateway.log
```

正常标志：`http server listening (X plugins)`、`ready`

## 避坑清单

1. **`openclaw config set` 会截断长 API key**：`config set` 命令处理长 API key 时会被截断为 `xxx...xxx` 格式（只保留前6后4），必须直接编辑 `~/.openclaw/openclaw.json` 文件才能写入完整key
2. **openclaw workspace 路径**：真正目录是 `~/.openclaw/workspace/`，不是 `/root/.hermes/home/.openclaw/workspace/`。IDENTITY.md、USER.md、SOUL.md 等必须写到这里才能被Agent读取
3. **QQ Bot 配置字段**：是 `appId` + `clientSecret`，不是 `token`
4. **stepfun 协议不匹配**：openclaw 2026.5.20 要求协议版本=4，但 stepfun 插件 0.2.27 仍为协议版本=3
5. **session 文件冲突**：每次重启前 `rm -f ~/.openclaw/agents/main/sessions/*.jsonl*`
6. **`OPENCLAW_NO_RESPAWN=1`**：必须设置，否则 pkill 后进程自动重生
