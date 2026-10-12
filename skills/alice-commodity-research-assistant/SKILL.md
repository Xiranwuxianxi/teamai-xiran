---
name: alice-commodity-research-assistant
display_name: Wind Alice-商品智研助手
display_name_en: Wind Alice-Commodity Research Assistant
description: 输入期货品种或 Wind Code，生成涵盖价格、基差、基本面、远期曲线、资金、仓单、宏观多维度的商品智能日报或专项分析，提炼核心驱动逻辑并给出结论。适用于商品日报、基本面分析、基差、远期曲线、仓单等场景。
description_zh: Wind Alice 商品智研助手 CLI：输入期货品种名称或 Wind Code，自动生成涵盖价格、基差、基本面、远期曲线、资金、仓单、宏观等多维度的商品智能日报或专项分析，输出含核心驱动逻辑与明确结论的结构化报告。
description_en: Wind Alice Commodity Research Assistant CLI - enter a commodity name or Wind Code to auto-generate smart research reports distilling core drivers across price, structure, capital flow, and fundamentals, with clear conclusions for institutional investors and professional traders.
version: 1.0.12
author: WindAlice
tags: [commodity, futures, basis, forward-curve, warehouse-receipt, capital-flow, macro, wind-alice]
---
# Commodity Research Assistant（Wind Alice-商品智研助手）

通过 `alice-commodity-research-assistant` 调用 Wind Alice Agent 的「商品智研助手」专业技能，输入期货品种名或 Wind Code，自动生成涵盖价格、基差、基本面、远期曲线、资金流向、仓单、宏观等多维度的商品智能日报或专项分析。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「商品智研助手」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> 本文件已包含调用命令与边界规范。如需深入理解宿主 Agent 执行契约（七步流程 / 交付规范 / 退出码分流），可参阅同目录 [`AGENT.md`](./AGENT.md)。

> 🔴🔴 **未见 DONE 不得结束回合**：
> - 主调用必须带 `--no-wait`，并**阻塞等到 CLI 进程退出**；**只要没看到 `ALICE_COMMODITY_RESEARCH_ASSISTANT_DONE` 行，就不得结束本回合**。
> - **禁止**只说一句「预计 X 分钟 / 还在跑 / 稍后再问我」就把等待推给用户下一轮——`[任务已受理]` 只代表已提交，不等于报告已生成。
> - 被环境中断（exit `4`/`6`、无 DONE）→ **同一回合内**立刻用**完全相同的命令**再发一条，循环到 DONE 或触顶（自首次提交起 60 分钟 / 已重发 20 轮）；重发会**接回**原任务；改一个字会被视为新任务重新提交，无法接回原任务。
> - **禁止** `Start-Sleep` / `check_command_status` 轮询代替阻塞等待；禁止并发多条、禁止 `--new`。
> - 完整执行契约（七步流程 / 九条红线 / 退出码分流 / 交付顺序）仍以 [`AGENT.md`](./AGENT.md) 为准。
>
> 🔴 **严禁防御性占位文件**：任何鉴权失败、任务异常或服务错误，必须直接在对话中以纯文本向用户说明，**严禁在 `./output/` 或工作区内写入诸如《商品研报进度回应.md》、《提纲草稿.md》、《说明.md》等防御性占位文件**，严禁在此类错误分支调用 `present_files`。

## 技能边界与路由规范

### 1. 明确应当调用的场景（必须调用）

用户问题涉及**商品期货单一品种全维度研究日报、产业链基本面深度分析、期现基差与期限结构、远期曲线形态、仓单库存压力与沉淀资金分析**等场景，必须调用本技能。

| 场景分类 | 适用范围与分析目标 | 典型用户问法示例 |
|---|---|---|
| **单品种全维度智能日报** | 输入特定境内外商品期货品种，自动生成覆盖价格、基差、基本面、远期曲线、资金、仓单、宏观 7 大板块的结构化日报 | 「帮我生成一份今天的沪铜日报」「棕榈油期货日报」「CU.SHF daily research report」「COMEX 黄金 outlook」 |
| **产业链供需与基本面分析** | 深度剖析特定商品的产能产量、开工率、下游需求、进出口及全产业链库存数据 | 「分析一下螺纹钢的基本面情况，供需矛盾大吗？」「详细拆解一下豆粕目前的库存和压榨利润」 |
| **期现基差与远期曲线研究** | 追踪特定品种历史基差走势、现货升贴水、月间跨期价差结构（Back/Contango）与远期曲线演进 | 「帮我分析一下原油目前的基差走势」「黄金期货的远期曲线结构目前是怎样的？」「纯碱跨期价差与升贴水情况」 |
| **仓单库存与资金沉淀追踪** | 统计交易所注册仓单增减、交割库容占用情况，以及品种沉淀资金与持仓集中度分析 | 「螺纹钢当前注册仓单和沉淀资金情况如何？」「碳酸锂期货仓单去化速度怎样？」 |

### 2. 明确不应调用的场景（严禁误调）

- **交易时段盘前/盘中操作策略与多空机会监控**：需要获取开盘前策略推演、盘中支撑阻力位、买卖方向指引及 A/B/C 三级机会池，**严禁调用本技能**，应调用 `alice-ai-commodity-strategist`（AI商品策略师）。
- **期货主力席位净多空持仓与增减仓异动**：专门查询期货公司前 20 席位多空主力动向与机构持仓态度，应调用 `alice-futures-leading-institution-analysis`。
- **期货资金流向排行榜与全市场异动监控**：需要统计全市场资金净流入/流出排名榜单与板块资金沉淀走势，应调用 `alice-futures-fund-flow-monitor`。
- **日内单个品种突发异动归因**：盘中某品种急速拉升或跳水，需要紧急排查消息面与驱动因素，应调用 `alice-intraday-futures-move-attribution`。
- **商品期权定价与隐含波动率分析**：涉及期权希腊字母、波动率曲面或期权策略组合，应调用期权类技能。
- **股票或信用债分析**：涉及上市公司股票行情、财务报告或信用违约，应调用对应股票/信用技能。

### 3. 边界消歧对比示例

| 用户真实提问 | 正确路由技能 | 错误路由原因分析 |
|---|---|---|
| 「详细分析一下螺纹钢当前的供需平衡表、铁水产量和库存情况」 | **`alice-commodity-research-assistant`（本技能）** | 核心场景：单一商品产业链基本面与供需深度研报 |
| 「开盘前帮我看一下今天螺纹钢的交易策略，关键支撑位和阻力位是多少？」 | `alice-ai-commodity-strategist` | 属于盘前交易策略与点位研判，非基本面研究 |
| 「中信期货在沪铜合约上今天增持了多少手多单？持仓态度如何？」 | `alice-futures-leading-institution-analysis` | 属于主力期货机构席位持仓行为剖析 |
| 「今天橡胶盘中突然拉升 4%，是什么消息刺激的？」 | `alice-intraday-futures-move-attribution` | 属于特定品种日内突发异动归因分析 |
| 「今天整个商品市场哪个板块资金流入最多？帮我排个榜」 | `alice-futures-fund-flow-monitor` | 属于全市场资金流向排行榜与板块资金监测 |

---

## 构造 prompt 规范

- 输入期货品种名称（如「沪铜」「铁矿石」「PTA」）、标准品种代码（如 `CU.SHF`、`I.DCE`）或月合约代码。
- 只说品种名自动生成全维度日报；在品种后加「基差」「库存」「远期曲线」「沉淀资金」「仓单」「宏观」等则输出专项分析。
- **不要加 `使用「商品智研助手」技能：` 前缀，CLI 内部已自动注入。**

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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

### 子命令（只读/配置类，本地命令）

| 子命令 | 用途 |
|--------|------|
| `login --from-connector` | **复用本机 WorkBuddy「连接器」已授权的 wind-finance 令牌（首选，免交互，自动续期）** |
| `login --url` / `login --callback <URL/CODE>` | 输出网页授权链接 / 用回调串换取令牌（备选路径） |
| `login --status` | 查看当前凭据状态与是否有效 |
| `logout` | 退出登录，清除授权令牌 |
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径 |

## 环境与配置

**Node.js 18+**（自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

**登录授权**（获取访问万得 Alice Agent 的凭据）

网页授权的回调地址 `workbuddy://workbuddy/mcp/connector:wind-finance/oauth/callback` 由 **WorkBuddy 客户端**接管。

**首选 `login --from-connector`**：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，只要用户在本机 WorkBuddy「连接器」里绑定过 wind-finance，技能就能**只读地**解出该令牌并自动续期，**全程无需用户任何操作**（技能每次主调用前也会自动静默尝试）。
若用户尚未绑定，请引导其在 WorkBuddy「连接器」中找到「Wind Alice 万得金融数据」(wind-finance) 并点击「连接」完成授权——绑定一次长期有效，之后无需任何登录命令。

**备选（手动 API Key）**：无法使用连接器时，可在 [Wind Alice 市场 → 个人中心](https://market.windalice.com/#/user/overview) 获取 API Key，再执行 `node scripts/cli.mjs apikey-set <KEY>` 写入本机（写入位置见下方「配置位置」）。

| 方式 | 命令 | 说明 |
|------|------|------|
| **连接器凭据复用（首选，免交互）** | `login --from-connector` | 读取本机 WorkBuddy「连接器」已授权的 wind-finance 令牌并自动续期。**用户绑定过 wind-finance 即可，零交互** |
| **OAuth PKCE 授权（备选）** | `login --url` / `login --callback "<URL/CODE>"` | 输出授权链接并在获取回调后换取 Token |
| 查看 / 退出 | `login --status` / `logout` | 查看凭据状态；清除令牌 |

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\acra.ps1" login --status              # 查看凭据状态（脱敏）
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
node "<SKILL_DIR>/scripts/cli.mjs" login --status
```

CLI 把凭据写到 `~/.wind-aifinmarket/config.env`（Windows `%USERPROFILE%\.wind-aifinmarket\config.env`）——**唯一受支持位置**。登录成功后写入 `WIND_ALICE_TOKEN`（同时写入 `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`，到期自动续期）。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 首次登录后通过 `memory_write(file="agent_md", ...)` 持久化 Token；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并写回 `config.env`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)「鉴权配置流程」。

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-aifinmarket/config.env`（Win: `%USERPROFILE%\.wind-aifinmarket\config.env`） | dotenv：`WIND_ALICE_TOKEN=<access_token>`（+ `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`）。**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://mcp.wind.com.cn/skills/alice`，一般无需改 | 否 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道默认按 GBK 解码 -> live 输出乱码，**不是 CLI 坏了**。三层防护（CLI 自动提供）：

1. **`scripts/acra.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
