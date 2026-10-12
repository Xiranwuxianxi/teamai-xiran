---
name: alice-deep-research
display_name: Wind Alice-深度研究
display_name_en: Wind Alice-Deep Research
description: 对任何主题进行结构化、多阶段的深度研究。它会先澄清用户的问题，确定研究范围和分析维度，制定并确认研究计划，然后调度多个并行子代理开展调查研究，最后汇总所有研究成果，生成一份全面、详细的最终研究报告。适用于用户提出深度研究、深入分析、全面调查、综合研究等需求，或任何需要广泛覆盖和深入分析的研究任务。
description_zh: Wind Alice 深度研究 CLI：对任意主题进行结构化、多阶段深度研究，先澄清问题、界定研究范围与维度并确认研究计划，再调度多个并行子代理调研，最终汇总生成全面、详细的专业研究报告。
description_en: Conducts structured, multi-stage deep research on any topic by clarifying the question, scoping the research dimensions, generating a confirmed research plan, dispatching parallel subagents for investigation, and producing a comprehensive final report. Use when the user asks for deep research, in-depth analysis, thorough investigation, comprehensive study, or any research task that requires broad coverage and detailed findings.
version: 1.0.8
author: WindAlice
tags: [deep-research, multi-agent, research, analysis, investigation, wind-alice]
---
# Deep Research（Wind Alice-深度研究）

通过 `alice-deep-research` 调用 Wind Alice Agent 的「深度研究」专业技能，对任意主题进行结构化、多阶段的深度研究（澄清问题 -> 界定范围 -> 确认研究计划 -> 并行子代理调研 -> 汇总报告）。

> **核心原则**：基础设施交给脚本；Agent 把用户问题拼成一句自然语言作为 `--prompt` 传入（**不要**加 `使用「深度研究」技能：` 前缀，CLI 内部已自动注入）。任务完成后**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**仅告知路径，禁止加载内容展示**。**关键（避免结果被折叠）**：`agentResult.value` 必须由 Agent **作为自己的文本回复正文逐字打出来**（`type=text` 才不折叠）；**若 DONE 含 `reportFullFile=`，先在独立一条消息调 `present_files`，随后在另一条纯文本消息里逐字输出 `agentResult.value`（本条禁任何工具调用）**。
>
> **专家执行契约参考**：专家执行契约 [`AGENT.md`](./AGENT.md) 为参考规范，在执行过程中遵循其执行约束与交付规则。

> 🔴🔴 **未见 DONE 不得结束回合**（本条从 `AGENT.md` 提到这里：它最常被漏掉，而 `AGENT.md` 需要 Agent 主动读取、不保证已在上下文里）：
> - 主调用必须带 `--no-wait`，并**阻塞等到 CLI 进程退出**；**只要没看到 `ALICE_DEEP_RESEARCH_DONE` 行，就不得结束本回合**。
> - **禁止**只说一句「预计 X 分钟 / 还在跑 / 稍后再问我」就把等待推给用户下一轮——`[任务已受理]` 只代表已提交，不等于报告已生成。
> - 被环境中断（exit `4`/`6`、无 DONE）→ **同一回合内**立刻用**完全相同的命令**再发一条，循环到 DONE 或触顶（自首次提交起 90 分钟 / 已重发 20 轮）；重发会**接回**原任务、**不重复发起请求**（改一个字就是新任务、重新发起）。
> - **禁止** `Start-Sleep` / `check_command_status` 轮询代替阻塞等待；禁止并发多条、禁止 `--new`。
> - 完整执行契约（七步流程 / 九大红线 / 退出码分流 / 交付顺序）仍以 [`AGENT.md`](./AGENT.md) 为准。

## 适用场景与调用边界

### 1. 明确应当调用的场景（必须调用表格）

| 场景大类 | 典型输入/用户需求 | 必须调用的理由与能力要求 |
|---|---|---|
| **新兴产业/前沿赛道全景调研** | "深度研究固态电池产业化进展，从技术路线、量产成本、材料体系及主要玩家四维度全面展开"、"全面调研低空经济eVTOL适航认证进展与商业化落地节奏" | 跨多个细分学科与供应链环节，需多阶段拆解范围、制定计划、并行子代理多源搜索并汇总长篇深研报告 |
| **跨国出海与全球竞争格局** | "系统分析中国新能源汽车产业链出海东南亚及欧洲的准入壁垒、本土化供应链与竞争态势" | 覆盖全球政策准入、宏观关税、海外本土竞品对比等多维度复杂课题 |
| **重大战略投资与商业尽调前置** | "对合成生物学上游底盘细胞设计领域的代表性企业进行全景式竞争情报与技术壁垒调研" | 需由浅入深层层递进的长链路调查，交叉验证多源研报、学术与产业数据 |
| **复杂多阶段专题调查** | "全面调查全球半导体先进制程供应链自主可控现状、关键设备卡脖子环节及替代进展" | 需交互式界定范围、确认研究计划、调度多并行子代理协同深挖并交付数万字综合调研报告 |

### 2. 明确不应调用的场景（严禁误调列表）

- ❌ **单一上市公司深度基本面估值与财务分析**：严禁误调本技能，必须调用 `alice-equity-research-expert`（万得个股研报专家）。
- ❌ **特定成熟行业常规月度/季度研究点评**：严禁误调本技能，必须调用 `alice-industry-research-expert`（万得行业研报专家）。
- ❌ **单场业绩说明会/路演电话会纪要提炼**：严禁误调本技能，必须调用 `alice-meeting-expert`（万得会议纪要专家）。
- ❌ **公募基金对比或筛选投资建议**：严禁误调本技能，必须调用 `alice-fund-compare` 或 `alice-fund-screening-investment-advisory`。
- ❌ **商品期货特定品种交易策略、资金流向或情绪追踪**：严禁误调本技能，必须调用商品期货类专项技能。
- ❌ **综合金融全景问答、资产配置与宏观股债基综合咨询**：应调用 `alice-financial-copilot`，无需启动 15-30 分钟的多阶段深度研究流程。
- ❌ **简单问答与即时行情查询**：如"查询宁德时代今日收盘价"、"目前中国一年期LPR是多少"，让上层模型直接回答，严禁调用深度研究。

### 3. 边界消歧对比示例表格

| 用户输入 / 诉求 | 正确技能选择 | 错误技能选择（严禁误调） | 区分辨析与判定理由 |
|---|---|---|---|
| "对全球人形机器人核心减速器、力传感器与灵巧手供应链进行深度多源调查，分析技术成熟度与商业化拐点" | **alice-deep-research** | alice-industry-research-expert | 跨机器人、机械、传感器、算法多领域的复杂前沿课题，需制定研究计划并调度多子代理长链路深研 |
| "请对工业机器人行业出具一份深度研究报告，梳理产业链结构、市场规模与重点公司" | **alice-industry-research-expert** | alice-deep-research | 针对成熟工业机器人行业的常规卖方风格行业研报，必须由行业研报专家承接 |
| "深度分析汇川技术的基本面、工控业务护城河、财务报表与估值区间" | **alice-equity-research-expert** | alice-deep-research | 明确针对单一上市公司的全维度财务与估值个股研报，必须由个股研报专家承接 |
| "帮我提炼汇川技术昨晚三季度电话交流会的核心要点与管理层指引" | **alice-meeting-expert** | alice-deep-research | 针对具体会议纪要的高管观点与机构问答提炼，必须由会议纪要专家承接 |
| "当前降息背景下，大类资产配置应如何调整？股票与黄金如何平衡？" | **alice-financial-copilot** | alice-deep-research | 宏观大类资产与配置策略综合问答，属于金融专家入口标准功能，不宜调用 30 分钟长调查 |
| "查询最新的中美十年期国债利差走势" | **直接回答 / 宏观数据技能** | alice-deep-research | 单一数据即时查询，严禁调用长耗时深度研究技能 |

**使用须知（deep-research 专属）**：
- **耗时 15–30 分钟**：结构化多阶段流程（澄清 -> 界定 -> 确认计划 -> 并行调研 -> 汇总），子代理各自检索分析后汇总，远长于普通问答。执行中持续打印 `ALICE_POLL_HEARTBEAT status=working` 心跳，**只要在打印心跳就是正常跑**，耐心等 `ALICE_DEEP_RESEARCH_DONE`，**禁止**因"等太久"就 `--new` / 换 prompt / 连发多条。
- **交互式中间态**：服务端会先澄清问题、界定范围、制定研究计划（可能返回"确认研究计划 / 补充信息"等中间态而非最终报告）。Agent 只需把用户原话作为 `--prompt` 传入并阻塞等待；**中间态原样交给用户**由其回复确认即可，**不要**当成失败而 `--new` 重跑（会丢上下文并重新发起）。
- **中途别改方向**：研究一旦确认计划开始执行，中途换 prompt 会被当成新任务（原任务仍将继续执行），还可能命中 exit=76。等当前 DONE 交付后，**在同一会话里追问**（同话题什么都不加，自动续接 contextId）让服务端基于上文深入或补充。
- **终端超时短于 15 分钟**：把超时调到 ≥1800s（30min）只发一条 `--no-wait`；做不到则用 `--detach` + 相同 prompt `--no-wait` 续接（详见 `AGENT.md`「沙箱 / 短超时宿主」）。

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。

**Windows（唯一写法，PowerShell 5.x 不支持 `&&`）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--new]
```

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（自然语言原话）。**必填**；直接把用户原话传入，不要改写措辞 |
| `--no-wait` | **Agent 默认必带**--CLI 内部自旋 `tasks/get` 直到终态。默认 60s 探针、每轮 45min、全程 90min；到轮上限 CLI 自动续轮；Agent 禁止外层 `Start-Sleep` 或连发多条 |
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

**首选 `login --from-connector`**：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，只要用户在本机 WorkBuddy「连接器」里绑定过 wind-finance，技能就能**只读地**解出该令牌并自动续期，**全程无需用户任何操作**（技能每次主调用前也会自动静默尝试）。
若用户尚未绑定，请引导其在 WorkBuddy「连接器」中找到「Wind Alice 万得金融数据」(wind-finance) 并点击「连接」完成授权——绑定一次长期有效，之后无需任何登录命令。

| 方式 | 命令 | 说明 |
|------|------|------|
| **连接器凭据复用（首选，免交互）** | `login --from-connector` | 读取本机 WorkBuddy「连接器」已授权的 wind-finance 令牌并自动续期。**用户绑定过 wind-finance 即可，零交互** |
| 查看 / 退出 | `login --status` / `login --url` / `logout` | 查看凭据状态与授权链接；清除令牌 |

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" login --status              # 查看凭据状态（脱敏）
```
```bash
# macOS / Linux
node "<SKILL_DIR>/scripts/cli.mjs" login --from-connector   # 首选：复用本机 WorkBuddy 连接器凭据
node "<SKILL_DIR>/scripts/cli.mjs" login --status
```

CLI 把凭据写到 `~/.wind-alice/config.env`（Windows `%USERPROFILE%\.wind-alice\config.env`）——**唯一受支持位置**（**不读**环境变量、**不读** skill 目录内 `config.json`，避免凭据残留 shell 历史/CI 日志/提交记录）。登录成功后写入 `WIND_ALICE_TOKEN`（同时写入 `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`，到期自动续期）。历史无后缀的 `~/.wind-alice/config` 仍可读。

**跨会话持久化（Agent 必做）**：远程沙箱每次会话重置会清空 `config.env`。Agent 首次登录后通过 `memory_write(file="agent_md", ...)` 持久化 Token；后续每次会话开始时 `memory_recall(scope="agent_md")` 读取并写回 `config.env`，不再询问用户。详见 [`AGENT.md`](./AGENT.md)「鉴权配置流程」。

**手动写入**（无 Node 运维场景）：
```bash
# macOS / Linux
mkdir -p ~/.wind-alice && printf 'WIND_ALICE_TOKEN=...\n' > ~/.wind-alice/config.env && chmod 600 ~/.wind-alice/config.env
```
```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.wind-alice" | Out-Null
"WIND_ALICE_TOKEN=..." | Set-Content -Encoding ascii "$env:USERPROFILE\.wind-alice\config.env"
```

### 配置位置

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-alice/config.env`（Win: `%USERPROFILE%\.wind-alice\config.env`） | dotenv：`WIND_ALICE_TOKEN=<access_token>`（+ `WIND_ALICE_REFRESH_TOKEN` / `WIND_ALICE_TOKEN_EXPIRES_AT`）。**唯一受支持位置** | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务 `agentResult.value` 落盘副本（stdout 截断时可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://alice.wind.com.cn/Weaver/ChatAgent`，一般无需改 | 否 |

### 中文乱码（Windows 必读）

Node 输出 UTF-8，PowerShell 5.x 管道默认按 GBK 解码 -> live 输出变 `鏈繘绨嬪皢闃诲...`，**不是 CLI 坏了**。三层防护（CLI 自动提供）：

1. **`scripts/adr.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下 CLI 把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（完整 64 位 promptHash，UTF-8 BOM）。**只读 stdout 打印的那条路径**（`Get-Content -Encoding UTF8`），禁止 `view_folder logs/` 扫描。
3. 落盘 `.md`（`results/`、工作空间、`--detach` 日志）均带 UTF-8 BOM。

`--detach` 日志同理：`Get-Content -Path "<path>" -Encoding UTF8 -Tail 50 -Wait`（务必带 `-Encoding UTF8`，否则中文 Windows 几乎必乱码）。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

> 任务调度幂等性、停止行为、CLI 失败处理、退出码分流、沙箱被 kill 续接、replay 重放、`present_files` 交付顺序等执行细节，均见 [`AGENT.md`](./AGENT.md)。
