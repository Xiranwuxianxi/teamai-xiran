---
name: alice-broker-top-picks-tracker
display_name: Wind Alice-券商金股追踪
display_name_en: Wind Alice-Broker Top Picks Tracker
description: 每月汇总主流券商金股推荐，统计被推荐次数与热度，梳理推荐逻辑与行业分布，输出含金股热度排行、行业主线、个股推荐理由与近月趋势的结构化报告。适用于查询某月券商金股、热门金股排行、金股行业分布等场景。
description_zh: Wind Alice 券商金股追踪 CLI：汇总各大券商月度金股推荐，统计推荐热度与行业分布，输出含金股排行、推荐理由摘要与近月变化趋势的结构化报告。
description_en: Wind Alice Broker Top Picks Tracker CLI - aggregates monthly broker top-pick recommendations, ranks stocks by recommendation frequency and heat score, summarizes investment rationale, and delivers sector distribution breakdown and trend charts. Ideal for monthly strategy meetings, sector rotation analysis, and pre-research stock screening.
version: 1.0.12
author: WindAlice
tags: [broker, top-picks, gold-stock, heat-ranking, sector-distribution, monthly-strategy, wind-alice]
---
# Broker Top Picks Tracker（Wind Alice-券商金股追踪）

通过 `alice-broker-top-picks-tracker` 调用 Wind Alice Agent 的「券商金股追踪」专业技能，汇总各大券商每月金股推荐，统计推荐热度与行业分布，输出金股热度排行与推荐理由。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「券商金股追踪」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> 本文件已包含调用命令与边界规范；如需了解深度底层契约可参考同目录 [`AGENT.md`](./AGENT.md)。本文重点规定**何时调用 + 边界消歧 + CLI 参数 + 环境配置**。

> 🔴🔴 **未见 DONE 不得结束回合**：
> - 主调用必须带 `--no-wait`，并**阻塞等到 CLI 进程退出**；**只要没看到 `ALICE_BROKER_TOP_PICKS_TRACKER_DONE` 行，就不得结束本回合**。
> - **禁止**只说一句「预计 X 分钟 / 还在跑 / 稍后再问我」就把等待推给用户下一轮——`[任务已受理]` 只代表已提交，不等于报告已生成。
> - 被环境中断（exit `4`/`6`、无 DONE）→ **同一回合内**立刻用**完全相同的命令**再发一条，循环到 DONE 或触顶（自首次提交起 60 分钟 / 已重发 20 轮）；重发会**接回**原任务（改一个字会被视为新任务重新提交）。
> - **禁止** `Start-Sleep` / `check_command_status` 轮询代替阻塞等待；禁止并发多条、禁止 `--new`。
> - 完整执行契约（执行流程 / 核心红线 / 退出码分流 / 交付顺序）仍以 [`AGENT.md`](./AGENT.md) 为准。

## 何时调用本技能

### 1. 明确应当调用的场景（必须调用）
用户明确需要查询**券商月度金股推荐、热门金股排行、金股行业热度分布与推荐逻辑**时调用：

| 触发意图 | 典型用户表达 | 判定规则 |
|---------|-------------|---------|
| **月度金股总览** | 「2026年5月有哪些券商金股？」「中信证券本月推荐了哪些金股？」 | 查询指定月份或指定券商的金股组合 |
| **热门金股挖掘** | 「本月被推荐次数最多的热门金股是哪些？」「哪些金股被超过5家券商同时推荐？」 | 统计金股推荐频次与共识重仓标的 |
| **行业主线分布** | 「近三个月券商金股主要集中在哪些行业？」「本月金股行业超配方向」 | 分析券商共识主线与行业配置倾斜 |
| **个股金股推荐理由** | 「贵州茅台最近被哪些券商选为金股？核心推荐逻辑是什么？」 | 梳理个股在券商金股中的覆盖度与研报观点 |

### 2. 明确不应调用的场景（严禁误调）
- **单只个股全套交易策略**：若用户需要针对某只股票的仓位、盈亏、买卖点与技术指标分析，应调用 `alice-stock-trading-strategy`。
- **公募/社保等机构真实持仓追踪**：若用户关注公募基金、QFII、社保基金等机构季报真实持股与调仓轨迹，应调用 `alice-institutional-holdings-insight`。
- **主题与产业链概念选股**：若用户按特定产业链或概念逻辑筛选股票，应调用 `alice-thematic-stock-screening`。
- **单家公司深度一页纸备忘录**：若用户需要某上市公司的全面财务估值与催化剂分析，应调用 `alice-company-one-page-investment-memo`。

### 3. 边界消歧对比示例
| 用户提问 | 判定结果 | 分流/处理理由 |
|---------|:-------:|-------------|
| 「查看本月各大券商推荐频率最高的前十只金股与推荐逻辑」 | ✅ 调用本技能 | 典型的券商金股排行榜与共识分析 |
| 「查看公募基金在今年一季度主要重仓了哪些半导体股票」 | ❌ 严禁调用 | 属于公募基金真实季报持仓，应调用 `alice-institutional-holdings-insight` |
| 「帮我做一份贵州茅台的持仓买卖点与短线交易执行策略」 | ❌ 严禁调用 | 属于个股交易策略与量价技术面，应调用 `alice-stock-trading-strategy` |
| 「按照低空经济主题筛选一下符合条件的 A 股标的」 | ❌ 严禁调用 | 属于主题概念选股，应调用 `alice-thematic-stock-screening` |

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（自然语言原话）。**必填**；直接把用户原话传入，不要改写措辞 |
| `--no-wait` | **Agent 默认必带**--CLI 内部自旋 `tasks/get` 直到终态。默认 60s 探针、每轮 30min、全程 60min；到轮上限 CLI 自动续轮；Agent 禁止外层 `Start-Sleep` 或连发多条 |
| `-d`, `--download-dir` | 保留兼容；**不影响下载目录**--所有附件统一落当前工作空间（`process.cwd()`）。同名冲突自动加 ` (1)`，**绝不覆盖** |
| `--new` | 用户明确要求**并行新建**时清除本地记录后新建（**须先经用户确认**） |
| `--context-id <id>` | **可选**（显式精确续接）：从上一轮 DONE 行 `contextId=` 原样传回，优先级最高，用于跨工作区/精确指定。同工作区内同话题续接已由默认自动续接覆盖，通常不需要 |
| `--new-session` | 显式强制新建会话上下文。**完全无关新话题/用户明说「换个话题」时加**；同话题追问**不要加**（靠自动续接） |
| `--continue-session` / `--session-scope` | 已废弃（no-op），可不传 |
| `--once` | 配合 `--no-wait` 单次探针；**仅脚本调试**，Agent 禁止外层循环 |
| `--no-strict` | 关闭 strict 模式（默认开启：未输出 DONE 行时 exit=0 改成 6）；Agent 禁止传 |
| `--watch-interval` / `--watch-timeout` / `--watch-absolute-max` | 自旋节奏与上限调优（秒），通常默认即可 |
| `--help`, `-h` | 查看帮助 |

> 会话续接判断（同话题追问什么都不加 / 完全无关新话题加 `--new-session`）、`--new` 与 `--new-session` 的区别、命令拼装铁律见 [`AGENT.md`](./AGENT.md)。

### 子命令（只读/配置类）

| 子命令 | 用途 |
|--------|------|
| `login --from-connector` | **复用本机 WorkBuddy「连接器」已授权的 wind-finance 令牌（首选，免交互，自动续期）** |
| `login --url` / `login --callback <URL/CODE>` | 输出网页授权链接 / 用回调串换取令牌（备选路径） |
| `login --status` | 查看当前凭据状态与是否有效 |
| `logout` | 退出登录，清除授权令牌 |
| `login --status` | 查看当前登录状态（凭据由 WorkBuddy 连接器自动提供） |
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径 |

## 环境与配置

**Node.js 18+**（自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

**登录授权**（获取访问万得 Alice Agent 的凭据）

⚠️ **已知限制（务必先读）**：OAuth 应用白名单里**只放行**
`workbuddy://workbuddy/mcp/connector:wind-finance/oauth/callback` 这一个回调地址，
且该地址由 **WorkBuddy 客户端**接管，**技能自身收不到授权码**（本机回环地址不在白名单）。
因此在 WorkBuddy 环境下**网页授权通常走不通**。

**首选 `login --from-connector`**：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，只要用户在本机 WorkBuddy「连接器」里绑定过 wind-finance，技能就能**只读地**解出该令牌并自动续期，**全程无需用户任何操作**（技能每次主调用前也会自动静默尝试）。
**唯一支持的鉴权方式就是复用 WorkBuddy 连接器凭据**。若用户尚未绑定，请引导其在 WorkBuddy「连接器」中找到「Wind Alice 万得金融数据」(wind-finance) 并点击「连接」完成授权——绑定一次长期有效，之后无需任何登录命令。

**备选（手动 API Key）**：无法使用连接器时，可在 [Wind Alice 市场 → 个人中心](https://market.windalice.com/#/user/overview) 获取 API Key，再执行 `node scripts/cli.mjs apikey-set <KEY>` 写入本机（写入位置见下方「配置位置」）。

| 方式 | 命令 | 说明 |
|------|------|------|
| **连接器凭据复用（首选，免交互）** | `login --from-connector` | 读取本机 WorkBuddy「连接器」已授权的 wind-finance 令牌并自动续期。**用户绑定过 wind-finance 即可，零交互** |
| 查看 / 退出 | `login --status` / `login --url` / `logout` | 查看凭据状态与授权链接；清除令牌 |

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\abtpt.ps1" login --status              # 查看凭据状态（脱敏）
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
node "<SKILL_DIR>/scripts/cli.mjs" login --status
```

CLI 把凭据写到 `~/.wind-aifinmarket/config.env`（Windows `%USERPROFILE%\.wind-aifinmarket\config.env`）——**唯一受支持位置**（**不读**环境变量、**不读** skill 目录内 `config.json`，避免凭据残留 shell 历史/CI 日志/提交记录）。登录成功后写入 `WIND_ALICE_TOKEN`（同时写入 `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`，到期自动续期）。历史目录 `~/.wind-alice/`（含无后缀 `config`）仍可兼容读取。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 首次登录后通过 `memory_write(file="agent_md", ...)` 持久化 Token；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并写回 `config.env`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)「鉴权配置流程」。

**手动写入**（无 Node 运维场景）：
```bash
# macOS / Linux
mkdir -p ~/.wind-aifinmarket && printf 'WIND_ALICE_TOKEN=...\n' > ~/.wind-aifinmarket/config.env && chmod 600 ~/.wind-aifinmarket/config.env
```
```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.wind-aifinmarket" | Out-Null
"WIND_ALICE_TOKEN=..." | Set-Content -Encoding ascii "$env:USERPROFILE\.wind-aifinmarket\config.env"
```

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-aifinmarket/config.env`（Win: `%USERPROFILE%\.wind-aifinmarket\config.env`） | dotenv：`WIND_ALICE_TOKEN=<access_token>`（+ `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`）。**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://mcp.wind.com.cn/skills/alice`，一般无需改 | 否 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道默认按 GBK 解码 -> live 输出变 `鏈繘绨嬪皢闃诲...`，**不是 CLI 坏了**。三层防护（CLI 自动提供）：

1. **`scripts/abtpt.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
