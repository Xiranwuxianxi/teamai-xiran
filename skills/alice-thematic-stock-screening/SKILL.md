---
name: alice-thematic-stock-screening
display_name: Wind Alice-按主题选股
display_name_en: Wind Alice-Thematic Stock Screening
description: 适用于赛道投资、产业链机会挖掘与概念股筛选，系统拆解市场交易核心逻辑，结合数据验证兑现程度，筛选真正受益标的并给出估值分位与交易建议。适用于主题选股、赛道投资、概念股挖掘等场景。
description_zh: Wind Alice 按主题选股 CLI：系统拆解主题投资逻辑、验证数据兑现、筛选核心受益标的，输出受益标的表、估值对比、交易建议与风险证伪点。
description_en: Wind Alice Thematic Stock Screening CLI - systematically deconstructs market narratives, validates logic maturity with key data, identifies genuine beneficiaries, and delivers valuation context with historical PE percentile and actionable trading perspective for sector investing and concept stock filtering.
version: 1.0.14
author: WindAlice
tags: [thematic, sector-investing, stock-screening, supply-chain, concept-stock, valuation, wind-alice]
---
# Thematic Stock Screening（Wind Alice-按主题选股）

通过 `alice-thematic-stock-screening` 调用 Wind Alice Agent 的「按主题选股」专业技能，按主题系统拆解投资逻辑、筛选真正受益标的，并给出估值与交易视角建议（核心受益标的表 / 估值对比 / 交易建议 / 风险证伪点）。

> **核心原则**：基础设施交给脚本；Agent 只负责把用户的主题/赛道拼成 `--prompt` 传入（可直接粘贴原话）。**默认就执行按主题选股，无需也不要再指定其它 Skill。** 任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**不要**读给用户看。
>
> **宿主 Agent**：本文件已包含调用命令与边界规范；如需了解深度底层契约可参考同目录 [`AGENT.md`](./AGENT.md)。本文重点规定**何时调用 + 边界消歧 + CLI 参数 + 环境配置**。

> 🔴🔴 **未见 DONE 不得结束回合**：
> - 主调用必须带 `--no-wait`，并**阻塞等到 CLI 进程退出**；**只要没看到 `ALICE_THEMATIC_STOCK_SCREENING_DONE` 行，就不得结束本回合**。
> - **禁止**只说一句「预计 X 分钟 / 还在跑 / 稍后再问我」就把等待推给用户下一轮——`[任务已受理]` 只代表已提交，不等于报告已生成。
> - 被环境中断（exit `4`/`6`、无 DONE）→ **同一回合内**立刻用**完全相同的命令**再发一条，循环到 DONE 或触顶（自首次提交起 60 分钟 / 已重发 20 轮）；重发会**接回**原任务；**换一个字会被视为新任务重新提交，无法接回原任务**。
> - **禁止** `Start-Sleep` / `check_command_status` 轮询代替阻塞等待；禁止并发多条、禁止 `--new`。
> - 完整执行契约（七步流程 / 八条红线 / 退出码分流 / 交付顺序）以 [`AGENT.md`](./AGENT.md) 为准。
>
> 🔴 **严禁防御性创建虚假占位文件**：
> - 严禁在 `./output/` 或工作空间创建任何《进度回应.md》、《提纲草稿.md》、《说明.md》等防御性占位文件。
> - 遇到任何凭据缺失或异常，**必须纯聊天文本提示用户**，禁止生成任何文件，禁止调用 `present_files`。

## 何时调用本技能

### 1. 明确应当调用的场景（必须调用）
用户问题只要涉及**特定主题/赛道投资机会拆解、产业链上下游受益标的筛选、概念股真伪辨别、赛道逻辑兑现验证与估值分位评估**，即应调用本技能。

| 场景 | 典型用户表达 | 输出重点 |
|------|-------------|---------|
| 主题投资深度拆解 | 如何参与AI算力主题？有哪些真受益标的？ | 核心逻辑拆解、产业链关键卡位、兑现程度评估 |
| 产业链受益标的筛选 | 低空经济产业链有哪些投资机会与核心上市公司？ | 上中下游环节划分、核心环节弹性、标的池梳理 |
| 概念股真伪辨别 | 固态电池概念股里哪些是真正有业务落地的标的？ | 业务纯度、订单/产能进度、证伪风险点 |
| 赛道估值与交易视角 | 半导体设备国产化有哪些标的值得关注，当前估值贵不贵？ | 历史PE分位、安全边际、交易视角与催化剂 |

### 2. 明确不应调用的场景（严禁误调）
以下场景有专门对应的专业技能，**严禁误调**本技能：
- **全市场多因子量化通用筛选**：如无特定产业链主题，仅要求按 ROE、PB、分红率等量化因子在全市场寻找投资机会，应调用 `alice-investment-idea-generation`。
- **单只个股全方位深度尽调**：如用户要求对某特定公司进行全面经营、财务与合规尽调，应调用 `alice-stock-dd-list`。
- **同业可比公司估值横向对标**：如明确要求对比几家同业公司的估值乘数，应调用 `alice-comps-analysis`。
- **单只标的一页纸备忘录**：如单一公司的快速投资备忘录，应调用 `alice-company-one-page-investment-memo`。
- **券商金股跟踪 / 机构持仓查询**：应调用 `alice-broker-top-picks-tracker` 或 `alice-institutional-holdings-insight`。
- **纯宏观经济、固收债券、商品衍生品**：调用对应宏观、固收或商品技能。

### 3. 边界消歧对比示例

| 用户输入 | 判定 | 依据与正确处理 |
|---------|------|---------------|
| 「低空经济产业链深度研究及核心受益标的梳理」 | **必须调用本技能** | 典型的特定赛道产业链拆解与受益标的筛选 |
| 「帮我用低PE+高分红因子从全市场筛选一批股票」 | **严禁误调本技能** | 属于全市场多因子量化筛选，转交 `alice-investment-idea-generation` |
| 「对比中际旭创、新易盛、天孚通信的估值乘数与盈利水平」 | **严禁误调本技能** | 属于明确同业可比公司估值对比，转交 `alice-comps-analysis` |
| 「给中际旭创做一份详细的尽调清单与供应链风险核查」 | **严禁误调本技能** | 属于单只个股深度尽调，转交 `alice-stock-dd-list` |
| 「光模块800G/1.6T升级周期下，哪些A股产业链标的真正受益」 | **必须调用本技能** | 典型的主题驱动赛道机会拆解与概念股真伪筛选 |

**构造 prompt**：把研究对象（投资主题或赛道，如"AI算力"或"低空经济"）与关注维度拼成一句自然语言。**不要加 `使用「按主题选股」技能：` 前缀，CLI 内部已自动注入。** 原文越完整、主题越明确，筛选越精准。
**多主体**：可一个或多个主题写进同一 prompt（建议 ≤ 5 个主题/标的）。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\atss.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
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
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径 |

## 环境与配置

**Node.js 18+**（自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

**登录授权**（获取访问万得 Alice Agent 的凭据）

⚠️ **已知限制（务必先读）**：OAuth 应用白名单里**只放行**
`workbuddy://workbuddy/mcp/connector:wind-finance/oauth/callback` 这一个回调地址，
且该地址由 **WorkBuddy 客户端**接管，**技能自身收不到授权码**（本机回环地址不在白名单）。

**首选 `login --from-connector`**：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，只要用户在本机 WorkBuddy「连接器」里绑定过 wind-finance，技能就能**只读地**解出该令牌并自动续期，**全程无需用户任何操作**（技能每次主调用前也会自动静默尝试）。
**支持的鉴权方式为复用 WorkBuddy 连接器凭据或标准 OAuth PKCE 授权**。若用户尚未绑定，请引导其在 WorkBuddy「连接器」中找到「Wind Alice 万得金融数据」(wind-finance) 并点击「连接」完成授权——绑定一次长期有效，之后无需任何登录命令。

**备选（手动 API Key）**：无法使用连接器时，可在 [Wind Alice 市场 → 个人中心](https://market.windalice.com/#/user/overview) 获取 API Key，再执行 `node scripts/cli.mjs apikey-set <KEY>` 写入本机（写入位置见下方「配置位置」）。

| 方式 | 命令 | 说明 |
|------|------|------|
| **连接器凭据复用（首选，免交互）** | `login --from-connector` | 读取本机 WorkBuddy「连接器」已授权的 wind-finance 令牌并自动续期。**用户绑定过 wind-finance 即可，零交互** |
| 查看 / 退出 | `login --status` / `login --url` / `logout` | 查看凭据状态与授权链接；清除令牌 |

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\atss.ps1" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\atss.ps1" login --status              # 查看凭据状态（脱敏）
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
node "<SKILL_DIR>/scripts/cli.mjs" login --status
```

CLI 把凭据写到 `~/.wind-aifinmarket/config.env`（Windows `%USERPROFILE%\.wind-aifinmarket\config.env`）——**唯一受支持位置**（**不读**环境变量、**不读** skill 目录内 `config.json`，避免凭据残留 shell 历史/CI 日志/提交记录）。登录成功后写入 `WIND_ALICE_TOKEN`（同时写入 `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`，到期自动续期）。历史目录 `~/.wind-alice/`（含无后缀 `config`）仍可兼容读取。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 首次登录后通过 `memory_write(file="agent_md", ...)` 持久化 Token；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并写回 `config.env`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)「鉴权配置流程」。

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-aifinmarket/config.env`（Win: `%USERPROFILE%\.wind-aifinmarket\config.env`） | dotenv：`WIND_ALICE_TOKEN=<access_token>`（+ `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`）。**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://mcp.wind.com.cn/skills/alice`，一般无需改 | 否 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道默认按 GBK 解码 -> live 输出变乱码，**不是 CLI 坏了**。三层防护（CLI 自动提供）：

1. **`scripts/atss.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
