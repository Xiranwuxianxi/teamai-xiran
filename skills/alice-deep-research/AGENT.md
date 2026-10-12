# Alice 深度研究 - 宿主 Agent 执行契约

> **专家执行契约参考**：本文档为宿主 Agent 执行规范参考，在执行过程中遵循其执行约束与交付规则。
> 产品与参数细节见同目录 `SKILL.md`；本文只规定**怎么跑、怎么判定完成、怎么交付**。

`<SKILL_DIR>` = 本文件所在目录的绝对路径。

---

## 🔴 最重要规则:结果必须由你复述成正文,否则用户看不到

宿主 UI（WorkBuddy 等）的折叠规则：**你亲自打字输出的文本正文（`type=text`）永远正常显示；任何工具调用的输出（含 Bash stdout、read_file 内容、present_files 卡片）回合结束后会被折叠进「已完成」块，用户必须点开才看得到。** CLI 通过 `adr.ps1` 跑完后，`agentResult.value` 完整结果**会停留在 Bash stdout 里被折叠**，你不能指望用户去点开。

**你必须做的动作**：从 stdout 提取 `agentResult.value:` 后面的正文，**亲自把它作为自己的回复文本逐字打出来**（可去掉行首前缀）。只有你亲自打字输出的内容才会作为正文正常显示。自检：交付前问自己「我有没有亲自把 agentResult.value 全文打字说出来？」没有就不算交付完。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框，见到即执行。

- **正确**：跑完 CLI -> 你在回复里写下「报告如下:」+ agentResult.value 全文（逐字，不概括）。
- **错误（会被折叠）**：跑完 CLI 就结束让 stdout 自己显示；或只说「报告完成，详见已完成块」；或用 `Out-File` 重定向到文件让用户自己看。
- **`present_files` 与分析正文必须分两条消息**：`present_files` 单独一条（折叠成卡片可接受）；分析正文必须在**另一条不含任何工具调用**的纯文本消息里--含工具调用的整条消息会被 WorkBuddy 折叠、藏住正文。

## 🔴 第二重要规则:同会话追问默认自动续接,切话题才用 `--new-session`

CLI **默认在工作区内自动复用**上次 `contextId`（30 分钟空闲窗口内），**无需手动传 `--context-id`**。会话状态落在 `<工作区>/temp/current-session.json`（工作区 = `process.cwd()`），空闲窗口内下一轮自动复用。**同一工作区 = 同一会话文件**，不同工作区 / 不同宿主各自独立文件，**物理上不串号**。

只有**切到完全无关的新话题**时加 `--new-session` 强制新会话；同话题追问（哪怕换角度、加维度）**什么都不用加**。`--context-id` 仍可用但通常不需要（优先级最高，用于跨工作区 / 精确指定续接）；`--continue-session` / `--session-scope` 已废弃（no-op），可不传。距上次超 30 分钟 CLI 自动按新会话处理。

拿不准时**倾向不加 `--new-session`**（续接错代价小，误切新会话代价大）。详见下方「会话续接判断」专节。

---

## 七步流程（按顺序，不可跳步）

> 注：CLI **不做任何重复判断**——每次提问都直接新建服务端任务。无需预检，也不存在本地重放。

| 步 | 动作 | 对用户怎么说 |
|----|------|-------------|
| 0 | **鉴权配置**：执行 `login --status` 检查状态（或从 `agent_md` 恢复）；未配置时**执行 `login --from-connector`**（复用本机 WorkBuddy 连接器凭据，零交互）；若失败，引导用户先在 WorkBuddy「连接器」中绑定「Wind Alice 万得金融数据」(wind-finance) 后重试 | （已配置时静默执行）；未配置时引导用户完成登录授权 |
| 1 | 把用户问题拼成一句自然语言 `--prompt`（**不要**加 `使用「深度研究」技能：` 前缀）；同步判断是否切到完全无关的新话题：同话题追问**什么都不加**（CLI 工作区内自动续接）；完全无关新话题才加 `--new-session` | （无需说话） |
| 2 | 告知用户：通常需 **15–30 分钟** | 「好的，我来帮你分析。深度研究通常需要 15–30 分钟，请稍等。」 |
| 3 | **主调用**：**一条** `--no-wait -d "<WORKSPACE_DIR>"`，**阻塞等待**该 shell 进程结束；**被中断（exit `4`/`6`、无 DONE）→ 同一回合内立刻用完全相同命令再发一条，循环到 DONE 或触顶，见「中断续跑循环」** | 「已提交分析，正在等待结果，请稍候……」 |
| 4 | 核对 **完成信号**（见下节） | （无需说话） |
| 5 | **若 DONE 含 `reportFullFile=`**：CLI 已把附件**统一下载到当前工作空间**（`process.cwd()`），路径必在工作空间内，**无需 `cp`**。在一条**独立消息**里调 `present_files`（直接传该路径）。**这条消息不要写分析正文，也禁止任何其它工具调用**（尤其 Edit/Write 写 `.workbuddy/memory`）--否则整条被折叠、卡片被隐藏。记忆日志写入必须在主调用同回合完成。无 `reportFullFile=` 时跳过本步 | （静默调用） |
| 6 | 🔴 **现在立即**：在**另一条只含文本、不含任何工具调用**的消息里，把 stdout 里的 `agentResult.value` **全文逐字复制**（去掉 `agentResult.value:` 行首前缀）。**本条消息禁止调用任何工具**。**禁止**只说「报告完成」、**禁止**概括/改写。附件路径已内联在正文中；禁止加载 `reportFullFile=` 内容展示。CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒框 | 交付报告（含内联路径） |

> ⚠️ **交付方式铁律（结果被折叠的根因）**：
> 1. **`agentResult.value` 必须由 Agent 作为「自己的文本回复正文」逐字打出来**，不能留在工具输出里。
> 2. **`present_files` 与分析正文必须分两条消息**：`present_files`（若需）在独立一条消息（折叠成卡片可接受）；分析正文在另一条不含任何工具调用的纯文本消息里。🔴 `present_files` 那条消息也必须**零其它工具调用**--尤其禁止同回合 Edit/Write（写 `.workbuddy/memory` 记忆日志）、Bash、Read；否则整条被折叠、文件卡片被一起藏起来。记忆日志写入必须在主调用同回合完成、先于 present_files。
> 3. **顺序**：① 静默跑完主调用 + 同回合完成所有内存/日志写入 -> ②（若 `reportFullFile=`）在独立消息调 `present_files`（本回合只能有 present_files 一个工具调用）-> ③ 在纯文本消息里输出 `agentResult.value`（本条禁任何工具调用）。
> 4. 🔴 **每轮都要独立调 `present_files`**：只要**本轮** DONE 含 `reportFullFile=` / `attachmentFile=`，本轮就必须在独立消息里用**本轮** DONE 的路径调 `present_files`。**禁止**因为「上一轮已经调过」就跳过本轮。

### 鉴权配置流程（步骤 0 详细说明）

**背景**：鉴权方式首选复用 WorkBuddy「连接器」中的 wind-finance 凭据（零交互）。

**首选 `login --from-connector`**：WorkBuddy 的 wind-finance 连接器用的是**同一个 OAuth 应用**，
用户在 WorkBuddy「连接器」绑定过一次后，令牌就落在本机
`~/.workbuddy/connectors/<userId>/.credentials.v3.json`（AES-256-GCM 加密，密钥由同目录 `.master.key` 经 HKDF-SHA256 派生）；
技能**只读地**解出该令牌并用 refresh_token 自动续期，**全程零交互**，且每次主调用前都会静默自动尝试。
沙箱重置时可把 Token 保存到 `agent_md` 跨会话恢复。

**流程**：
1. 执行 `login --status` 检查当前状态（或调用 `memory_recall(action="load", scope="agent_md")`）；
2. **若已配置（status: "configured"）或 memory 中有有效 Token 记录**：若 memory 中有 Token 则写入 `config.env`，**静默完成，不对用户提及**，直接进入步骤 1；
3. **若未配置（status: "missing"）**：直接执行 `login --from-connector`。它只读地解析本机 WorkBuddy 连接器仓库中 wind-finance 的 OAuth 令牌（`~/.workbuddy/connectors/<userId>/.credentials.v3.json`），并用 refresh_token 自动换取新令牌。未绑定时向用户说明需先在 WorkBuddy「连接器」中绑定「Wind Alice 万得金融数据」(wind-finance) 后重试；
4. **备选（网页授权 — 仅在宿主能回传 code 时可用）**：通过 `login --url` 获取授权链接，用户授权后执行 `login --callback "<回调地址或CODE>"` 完成授权。

**红线**：
- **禁止**在已有有效凭据时向用户重复索要授权；
- **禁止**向用户索要万得账号密码；
- 登录换取 Token 成功后写入 `~/.wind-alice/config.env`，后续无需重复登录；Token 到期可用 `refresh_token` 自动续期，仅在刷新失败时才重新引导登录。

### 话术红线

**禁止**向用户暴露内部实现细节（CLI、自旋、task_id、进程、shell、exit code 等）。用户只需知道「在做什么」和「大概等多久」。示例：「已提交分析，正在等待结果，请稍候……」（✅）；「分析任务已在后台启动（task_id: 88MT9l），CLI 内部自旋直到终态」（❌）。已有有效凭据时静默执行，不对用户说。不要问用户「想接着刚才那个话题继续吗」--Agent 自己按承接信号判断。

### 工具调用 `description` 字段用中文

宿主执行 Bash 工具调用时，会把 `description` 字段文字作为**权限确认框标题**展示给用户。填**简短中文**：步骤 3 主调用填「调用万得 Alice 进行深度研究」；`status` 填「查询本地任务落盘路径」。不要把 CLI / task_id / exit code 等技术细节写进 `description`。

---

## 命令模板

> ⚠️ **命令拼装铁律（照抄下方模板，禁止自由发挥）**：必须逐字照抄，只替换占位符，**不准自行增删参数、不准重定向输出、不准 cd 到 skill 目录**。
> 1. **Windows 必须用 `adr.ps1`，禁止裸 `node scripts/cli.mjs`**（裸 node 在 PowerShell 5.x 下中文乱码 + 沙箱兼容性问题）。
> 2. **禁止 `Set-Location`/`cd` 到 `<SKILL_DIR>`**。`adr.ps1` 用绝对路径调用，不 cd，让 `process.cwd()` 保持当前工作区。状态目录(tasks.json / results / logs)**在 `<工作目录>/temp/`**，随 `process.cwd()` 走。
> 3. **`-d` 必传，且必须指向当前工作区根目录**（`process.cwd()`/`workspace`），**禁止**指向 `C:\Users\<用户>\WorkBuddy\...` 工作区外临时目录或 skill 目录。`-d` 决定**报告附件落盘位置**，`present_files` 只能呈现工作区内的文件。`-d` **只管报告附件**，不管状态文件。
> 4. **禁止用 `Out-File`/`>`/`2>&1 | Out-File` 把 stdout 重定向到文件**。完成信号(`ALICE_DEEP_RESEARCH_DONE`、`agentResult.value`)在 stdout，Agent 必须直接捕获 stdout。
> 5. **`-d` 路径含空格必须加双引号**。

**Windows（PowerShell 5.x 不支持 `&&`，一律用方案 A）**：
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\adr.ps1" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```
**macOS / Linux**：
```bash
node "<SKILL_DIR>/scripts/cli.mjs" --prompt "<USER_QUESTION>" --no-wait -d "<WORKSPACE_DIR>" [--context-id <上一轮contextId>] [--new-session]
```

`-d "<WORKSPACE_DIR>"` **必传**；用户明确要求重新分析时加 `--new`（须先经用户确认）；**同话题追问无需任何会话参数**，**完全无关的新话题才加 `--new-session`**；`--context-id` 可选（优先级最高）；`--continue-session` / `--session-scope` 已废弃，可不传。

---

## 会话续接判断（Agent 自动执行，无需用户显式说）

**核心原则**：CLI 在工作区内**默认自动续接**上次 `contextId`（30 分钟空闲窗口内）。Agent 唯一要做的判断--**本次是否切到了完全无关的新话题**：是 -> 加 `--new-session`；否 -> **什么都不加**。无需从 DONE 行抓 contextId 手动接力。

会话状态写在 `<工作区>/temp/current-session.json`（工作区 = `process.cwd()`）。下一轮默认读它、在 30 分钟窗口内复用其 `contextId`。CLI 打印 `[CLI] 会话续接：复用 contextId = ...（工作区自动续接）` 确认。第一轮无历史文件，自然开新会话。不同工作区 / 不同宿主各自独立文件，不会串号。

### 判断规则（只判"是否切换"，宁滥勿缺）

默认续接；只有完全无关的新主题才加 `--new-session`。判断不准时**倾向不加**--续接错代价小（多带点上文），误切新会话代价大（丢上下文）。

| 情形 | Agent 动作 |
|------|-----------|
| 本工作区首次调用 | 自动开新会话（无需参数） |
| 与上一轮有任何话题关联（见下） | **什么都不加**（自动续接） |
| 完全无关新主题 / 用户明说「换个话题」 | 加 `--new-session` |
| 距上次超 30 分钟 | CLI 自动按新会话处理（窗口过期） |

**判定为续接（任一命中即什么都不加）**：追问上文结论/原因（「是XX引起的吗」「为什么上面说XX」）；省略式追问（「XX 呢」）；显式承接（「接着刚才/再看下XX方面」）；代词指代（「它/上面那份」）；相同主体追加维度；同一研究主题延伸（如「深度研究固态电池产业化进展」->「那量产难点呢 / 产业链上游呢 / 成本怎么看」）。

**判定为切换（加 `--new-session`）**：用户明说「换个话题/忘掉刚才」；主体明显无关（如固态电池研究 -> 东南亚电商 / 公司信用）；用户明说要「重新分析」（同时加 `--new`，语义正交）。案例：上文「深度研究固态电池产业化进展」->「东南亚电商竞争格局怎么样」= 完全无关新主题，加 `--new-session`。

`--context-id` 仍兼容（优先级最高，跨工作区/精确指定续接）；`--continue-session` / `--session-scope` 已废弃（no-op）。续接生效无需向用户提及 `contextId` / `--new-session` 等技术细节，直接交付结果；禁止把续接判断包装成"我帮你续接了会话"这样的话术。

---

## 八条红线

## 九大红线

违反任一条可能导致**任务中断、交付错误数据、编造指标**。

1. **阻塞等到 CLI 进程退出** - 禁止 `check_command_status`、禁止 `Start-Sleep` 轮询、禁止在进程未结束前读 `results/`/`logs/`/`Downloads/`「猜结果」。 **🔴 未见 DONE 不得结束回合**——被环境中断（exit `4`/`6`）就在同一回合内继续重发续跑，直到 DONE 或触顶（60 分钟 / 20 轮），禁止只说一句「还在跑 / 稍后再问我」就把等待推给用户下一轮。
2. **重发必须用完全相同的 prompt** - CLI 只在 promptHash 完全一致、且上次任务仍在执行时接回（不重复发起）；**换一个字就是新任务、重新发起**。CLI 不做任何相似度判断。
3. **没有 DONE 行 = 未完成** - `[任务已受理]`、`state=submitted`、`STATUS=COMPLETED`、本地 `tasks.json` 的 running，**均不算完成**。
4. **禁止手动翻目录猜报告** - 禁止扫 `Downloads/`、`results/`、`logs/` 按主题名或修改时间挑文件；`ALICE_ARTIFACT_GUARD`、`ORPHAN_DOWNLOAD_CANDIDATE`、`ALICE_FORBIDDEN_READ_UNTIL_DONE` 是**警告**，不是可交付路径。
5. **交付 `agentResult.value` 原文（附件路径已内联）** - 禁止自行总结、改表格、重写评级；附件路径已由 CLI 内联在正文中，不需末尾再追加；**必须保留 CLI 生成的 markdown 链接格式**（`[文件名](file:///绝对路径) (绝对路径)`）--禁止改成行内代码 `` `路径` ``，行内代码不可点击；**禁止加载 `reportFullFile=` / `attachmentFile=` 文件内容展示给用户**（`agentResult.value` 已是面向用户的核心分析摘要）。**中间态原样交付**：若 `agentResult.value` 是「确认研究计划 / 补充信息」等服务端交互式中间态而非最终报告，**原样交给用户**由其回复确认即可，**不要**当成失败而 `--new` 重跑（会丢上下文并重新发起）。
6. **禁止在无完成信号时交付** - 无 `ALICE_DEEP_RESEARCH_DONE` 与 `agentResult.value` 时**不得交付**任何分析结论。
7. **禁止手动改动 CLI 状态文件** - 任务状态写在 **`<工作目录>/temp/`**（`tasks.json` / `results/` / `logs/`），由 CLI 维护；**禁止手动删改**，也不要据此判断任务是否完成——判定标准只有 DONE 行。
8. **禁止凭猜测声称凭据缺失** - 凭据缺失有**唯一确定信号**：退出码 `2` **且** stderr 含 JSON `"code":"KEY_MISSING"`。退出码 `4`/`6`（strict 兜底 / 被沙箱杀）、stdout "输出不完整"、`login --status` 返回 `status: configured`--这些都**不是**凭据问题。核实凭据只能跑 `login --status` 并读其 JSON `status` 字段（`configured`=正常 / `missing`=缺失）。**禁止**在无 `KEY_MISSING` 退出码时引导用户去配置凭据。
9. **严禁生成占位/防御性文件** — 严禁在 `./output/` 或工作区写入任何占位 markdown、草稿提纲、进度回应或错误说明文件；严禁在异常/中断分支调用 `present_files`。任何错误、排队或未完成状态必须仅作为普通聊天文本返回。

---

## 完成判定（唯一标准）

同时满足才算完成：

- stdout 含 **`ALICE_DEEP_RESEARCH_DONE`**，且其中 **`promptHash=`** 与本次 CLI 打印的 **`PROMPT_HASH=`** 一致；
- 退出码 **`0`**；
- **Agent 已把 `agentResult.value` 全文逐字写进正文回复**（CLI 会在 DONE 前打印 `ALICE_DELIVER_AS_TEXT=1` 提醒）。自检：用户**不点开「已完成 / Tool calls」折叠块**就能在你的回复正文里看到完整分析（含表格、评级、链接）--否则**视为未完成**，不得结束回合。

`serverCallsThisProcess=0`（正常情况下不应出现）**仍须**满足上述 DONE 行；**不等于**可以改读 `Downloads/` 里的同名主体文件。

---
## 交付来源

| 优先级 | 来源 | Agent 用法 |
|--------|------|------------|
| ✅ 首选 | stdout 中 `agentResult.value:` 正文 | **原样**交给用户（仅去掉行首前缀）；CLI 已自动把 `/project/` 附件引用**就地替换**为本地下载路径，并去掉 `### …完整报告` 标题；其余正文禁止改写 |
| ✅ 兜底 | DONE 行 `reportFile=` -> `<工作目录>/temp/results/<taskId>.md` | 仅当 stdout 被截断；读文件**正文**（跳过 `<!-- ... -->` 头）原样输出 |
| ✅ **必须** | DONE 行 `reportFullFile=` -> `工作空间/*.md` | **必须告知完整路径**（**保留 markdown 链接格式** `[文件名](file:///绝对路径) (绝对路径)`；**禁止**改成行内代码）；**禁止加载文件内容展示给用户**（`agentResult.value` 已是核心分析摘要）；`.xlsx` 等仅告知路径；禁止只说「已下载」而不写路径 |
| ❌ 禁止 | 自行概括、摘录、重制表格 | 定量指标会被改错 |

附件路径已由 CLI **内联到正文中**（markdown 链接格式，可点击，原样输出即可）。**禁止**改成行内代码；**禁止**加载附件内容展示；**禁止**在末尾再追加「已保存到：…」；**禁止**只说「已下载」。`reportFile=` -> `results/` 只是 `agentResult.value` 摘要副本，**不要**称为「完整报告」。若 DONE 行**没有** `reportFullFile=`，**不要**编造下载路径，只交付 `agentResult.value`。

---

## 退出码速查

| 码 | 场景 | Agent 怎么做 |
|----|------|--------------|
| `2` | 参数错误 **或** `KEY_MISSING`（stderr 含 `"code":"KEY_MISSING"`） | 参数错误 -> 看 stderr 提示；凭据缺失 -> 按「鉴权配置流程」引导用户先在 WorkBuddy「连接器」中绑定「Wind Alice 万得金融数据」(wind-finance)，再 `login --from-connector` 复验。**禁止**在退出码不是 2 时声称凭据缺失 |
| `0` | 正常（须另有 DONE 行才算完成） | 按完成判定交付 |
| `4` / `6` | 沙箱杀进程 / 未输出 DONE | **同一回合内立刻**用**完全相同的 prompt** 再发**一条** `--no-wait`，可接回被中断的任务、**不重复发起**；仍被中断就**继续循环重发**，直到 DONE 或触顶（自首次提交起 **60 分钟** / 已重发 **20 轮**）——**未见 DONE 一律不得结束回合**，禁止说一句「还在跑」就把等待推给用户（详见「沙箱 / 短超时宿主（中断续跑循环）」）；**换一个字就是新任务、重新发起**；禁止并发多条、禁止 `--new` |
| `75` | 服务端临时拒绝（并发上限 / 服务繁忙 / 账户授权受限） | **停止**；按 stderr 内容分流话术（见下方）；禁止换 prompt / `--new` 绕过 |
| `78` | 环境受限，无法保存任务状态 | **未向服务端发请求**；告知用户「当前环境无法运行 深度研究，请在工具中开启完全访问权限后重试」；禁止换 prompt / `--new` / 反复重试 |

### exit 75 话术分流（按 stderr 内容选对用户说什么）

退出码 75 涵盖三种原因，**话术不能混**--尤其账户授权受限不能说「等任务执行完」或「稍后重试」。话术用「您」称呼，措辞已润色，可接近原样转述。

**① 账户授权受限**（stderr 含 `权限` / `受限` / `账户` / `points` 等）：「很抱歉，这次的分析没能跑起来——您的万得 Alice 账户服务权限需要确认。烦请您前往万得 Alice 设置中心核对您的账户与授权状态。确认完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。」要点：给唯一动作（前往设置中心核对权限）；明确请用户确认后重新发送问题；不提内部代码或技术词；不说「等任务执行完」「稍后重试」。权限确认前禁止重试或换 prompt。

**② 并发上限**（stderr 含 `最大同步执行任务` / `并发` / `请等待其他任务执行完成`）：「您这边还有别的分析任务正在跑，已经达到同时进行的数量上限，这次没发起。等那些任务完成后，请您把刚才的问题再发一遍，我立刻为您重新分析。」要点：强调「等已有任务执行完」，**不是**「稍后重试 / 过几分钟」；需用户在已有任务完成后重新发送问题；禁止换 prompt / `--new` / 改 `-d`。

**③ 服务繁忙**（stderr 含 `服务繁忙` / `系统繁忙` / `请稍后重试`）：「服务端现在比较忙，暂时没接上这次请求。请您稍等一会儿，把刚才的问题再发一遍，我立刻为您重新分析。」要点：强调「稍后重试」，**不是**「等已有任务执行完」（那是并发上限话术）；需用户稍后重新发送问题；禁止连续重试或换 prompt。

---

## 沙箱 / 短超时宿主（中断续跑循环）

深度研究通常 **15–30 分钟**。若宿主 `run_command` 只有数十秒～几分钟超时，**第一条 `--no-wait` 会被强杀**（exit `4`/`6`），看起来像「卡住」——其实是终端杀了 CLI，**服务端仍在跑**；用同一 prompt 重发会**接回**那个任务、**不重复发起请求**。对用户不要说「被杀」「超时」等技术细节。

### 🔴 未见 DONE 不得结束回合

被中断后你必须**在同一回合内立刻重发，循环到拿结果为止**。**禁止**只对用户说一句「分析仍在进行中，我会持续跟进 / 你稍后再问我」就结束回合——那是把等待甩回给用户，是本技能最常见的交付失败。

**循环规则**：

1. 记住首次提交时刻 `T0`，以及那条命令的**逐字原文**（prompt、`-d`、会话参数一字不改）。
2. 跑**一条** `--no-wait`，阻塞等它退出。
3. 按退出结果分流：
   - **有 DONE 且 `promptHash=` 与本次 `PROMPT_HASH=` 一致** → 跳出循环，按「完成判定」交付。
   - **exit `4`/`6`、无 DONE** → **不结束回合**，把**同一条命令逐字**再发一遍，回到第 2 步。允许在重发前对用户说一句「分析仍在进行中，我继续等待……」，但这句话之后**必须紧跟下一条命令**，不能停在那里等用户开口。
   - **exit `2` / `75` / `78`** → 确定性失败，重发无用；**终止循环**，按「退出码速查」处置。
4. **停止条件（先到者为准）**：① 见到 DONE；② 自 `T0` 起累计已等 **60 分钟**（CLI 全程自旋上限）；③ 已重发 **20 轮**。
5. **只有触顶（②/③）才结束回合**，对用户说：「这次分析等了比较久仍没有返回结果，可能是服务端排队较多。麻烦您稍后把刚才的问题原样再发一遍，我接着帮您查。」——不提 CLI / 进程 / 退出码等内部细节。

**空转保护**：若某一轮在 **10 秒内**就以 `4`/`6` 退出，那不是「被终端超时杀掉」而是启动即失败；**连续 2 次**即终止循环，读 stderr 排查，不要空转刷屏。

**优先做**：把 shell / `run_command` 超时调到 **≥1200 秒（20 分钟）**，一条 `--no-wait` 直接等到进程结束，循环自然只跑一轮。**无法拉长超时**时（Trae / Cursor 等）用 `--detach` + 续接：① `adr.ps1 --prompt "<Q>" --detach`（后台提交，父进程立刻退出）→ ② 相同 prompt `--no-wait` 续接轮询——续接轮询**同样**按上面的循环规则重发。

**循环期间禁止**：`check_command_status` 轮询、并发多条 CLI、读 `session.log` / `results/` 猜进度、换 prompt、加 `--new`（换一个字就是新任务、重新发起任务）。

---

## CLI stdout 机器信号（辅助识别）

| 信号 | 含义 |
|------|------|
| `ALICE_DEEP_RESEARCH_DONE` | **唯一**完成标记 |
| `ALICE_DELIVER_AS_TEXT=1` | **交付动作提醒**（DONE 前打印）：必须把上面 stdout 里的 `agentResult.value` **逐字复制成正文回复**，否则被宿主折叠、用户看不到 |
| `ALICE_POLL_HEARTBEAT` | 仍在执行，未完成 |
| `ALICE_ARTIFACT_GUARD` / `ALICE_FORBIDDEN_READ_UNTIL_DONE` | 禁止读列出的旧报告路径 |
| `ALICE_USER_DOWNLOAD_HINT=` | 完整报告附件可点击的 markdown 链接（已内联在 `agentResult.value` 正文中） |
| `ALICE_SESSION_LOG=` | Windows 乱码时只读 stdout 给出的**完整**日志路径 |
| `ALICE_SANDBOX_NO_PERSIST=1` | 当前环境无法保存任务状态，已阻止提交（退出码 78）；**未向服务端发请求**；告知用户开启完全访问权限后重试 |

---

## 禁止写法（Windows）

```powershell
# ❌ PowerShell 5.x：&& 解析失败
cd "<SKILL_DIR>" && node scripts/cli.mjs --prompt "..." --no-wait
# ❌ 命令末尾拼 undefined 等垃圾参数
... adr.ps1 --prompt "..." --no-wait undefined
# ❌ 用 check_command_status 轮询代替阻塞等待（终端超时杀 CLI，任务仍在服务端跑）
... adr.ps1 --prompt "..." --no-wait   # 然后反复 check_command_status / Get-Content session.log / Test-Path results/
# ❌ 后台 / fire-and-forget（分析主路径禁止；仅 --detach 场景由 CLI 内部 detached 子进程）
Start-Process ... | Out-Null
# ❌ 用裸 node cli.mjs 代替 adr.ps1（Windows 上会导致中文乱码、沙箱兼容性问题）
node "...\scripts\cli.mjs" --prompt "..." --no-wait
```

---

## 自检清单（交付前必做）

```
□ 步骤 0 已完成：已确认鉴权有效（`login --status` 返回 `status: "configured"`，或已从 memory 恢复有效 Token）？
□ 步骤 1 会话续接判断已执行：同话题追问什么都不加；完全无关新话题才加 --new-session？
□ stdout 有 ALICE_DEEP_RESEARCH_DONE？DONE 的 promptHash= 等于本次 PROMPT_HASH=？
□ 🔴 已把 agentResult.value 全文逐字写进回复正文（见到 ALICE_DELIVER_AS_TEXT=1 即执行）？用户不点开折叠块就能看到完整分析？
□ 正文来自 agentResult.value 或 reportFile=，而非 Downloads/ 附件正文？未自行概括、未改数字、未摘录（整段逐字，含所有表格行）？
□ 若 agentResult.value 是「确认研究计划」等中间态，已原样交给用户确认，未当成失败 --new 重跑？
□ 若 DONE 含 reportFullFile=：路径已在工作空间（CLI 统一下载到 process.cwd()），直接用该路径调 present_files（无需 cp）？
□ 🔴 本轮（不是上一轮）已调 present_files？续问每轮都要独立调，不能因上一轮调过就跳过本轮？
□ 🔴 present_files 那条消息有没有混入 Edit/Write（写 .workbuddy/memory 记忆日志）或其它工具调用？若有，整条会被折叠、卡片被隐藏--把记忆写入移到主调用回合，让 present_files 单独一条、零其它工具调用？
□ 🔴 present_files 和分析正文分在两条独立消息（present_files 单独一条；正文在另一条不含任何工具调用的纯文本消息）？
□ 附件路径保留了 markdown 链接格式（[文件名](file:///...) (绝对路径)），没有改成行内代码？未加载 reportFullFile= / attachmentFile= 文件内容展示给用户？
□ 🔴 被环境中断（exit 4/6、无 DONE）时，已在同一回合内继续重发续跑直到 DONE 或触顶（60 分钟 / 20 轮）？没有只说一句「还在跑 / 稍后再问我」就结束回合、把等待推给用户？
□ 对用户说的话里没有暴露 CLI、自旋、task_id、进程、shell、exit code 等内部技术细节？没有用 view_folder / view_files 扫描 Downloads/、results/、logs/ 猜报告？
□ 若向用户说过"凭据缺失"--退出码确实是 2 且 stderr 含 KEY_MISSING？若否，已停止并改按真实退出码处理（红线 8）？没有在 agent_md 已保存有效凭据的情况下再次询问用户提供凭据？
□ 🔴 **严禁生成占位/防御性文件**：未在 ./output/ 或工作区生成任何中间进度、提纲草稿或错误说明 markdown 文件，未在异常分支调用 present_files？
```

任一为 **否** → **不得交付**；向用户说明未完成，并说明重新发起将重新提交分析。

---

更多 FAQ、环境配置见 `SKILL.md`。
