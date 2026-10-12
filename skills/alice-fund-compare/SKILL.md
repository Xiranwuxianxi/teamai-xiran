---
name: alice-fund-compare
description: 对多只公募基金做全方位对比分析，覆盖业绩、风险、持仓、管理四大维度，支持客观中立与主观倾向性两种模式。适用于对比多只基金、分析基金差异、基金替换评估、哪个更好等场景。
description_zh: Wind Alice 基金对比分析 CLI：对多只基金做业绩、风险、持仓、管理四维度对比分析，支持客观中立与主观倾向性分析，输出含核心结论、优势、风险、投资建议的结构化报告。
description_en: Wind Alice Fund Compare CLI - comprehensive comparative analysis of multiple funds across performance, risk, portfolio structure, and management assessment, supporting both objective neutral and subjective preference modes, for fund selection, replacement evaluation, portfolio optimization, due diligence, and investment education.
version: 1.0.0
author: WindAlice
tags: [fund, compare, mutual-fund, performance, risk, holdings, manager, wind-alice]
---

# Fund Compare（Wind Alice-基金对比分析）

通过 `alice-fund-compare` 调用 Wind Alice Agent，针对多只公募基金（2–5 只）一键生成结构化对比分析报告。

> **核心原则**：基础设施交给脚本处理；Agent 只负责把用户的对比对象拼成一句自然语言 prompt 传入。**默认就执行 Fund Compare 技能，无需也不要再指定其它 Skill。** 任务完成后，**只将 CLI stdout 中的 `agentResult.value` 原文原样交给用户**；CLI 静默下载的附件（`reportFullFile=`）**不要**读给用户看。
>
> **宿主 Agent：执行任何 shell 命令前必须先读同目录 [`AGENT.md`](./AGENT.md)**（一页执行契约，与 IDE 无关，随 skill 包发布）。

---

## 何时调用本技能

专业的基金对比分析能力，基于 Wind 金融终端数据，对**多只基金**（股票型、债券型、混合型、指数型、货币型等公募基金）覆盖**业绩表现、风险指标、持仓结构、管理评估**四大维度，进行全方位、多维度的深度对比，为基金研究、投资决策与组合管理提供定量依据。**支持客观中立分析和主观倾向性分析两种模式。**

### 适用场景

| 场景               | 解决的问题                                           |
| ------------------ | ---------------------------------------------------- |
| 基金选择决策       | 在多只候选基金中选择最适合的，辅助买卖 / 申赎判断    |
| 基金替换评估       | 评估是否应该用基金 A 替换基金 B，对比性价比          |
| 投资组合优化       | 对比同类基金，挑选性价比更高的标的优化组合           |
| 基金尽职调查       | 全面评估候选基金的优劣势，做投前尽调                 |
| 基金投资教育       | 理解不同基金的差异和特点，做投资者教育               |

### 核心能力

1. **业绩表现对比**
   - 近期 / 中长期净值增长率（近 1 月 / 3 月 / 6 月 / 1 年 / 3 年 / 成立以来）
   - 同类排名与分位数对比
   - 超额收益与基准跟踪误差（指数型）
   - 业绩一致性 / 稳定性评估

2. **风险指标对比**
   - 年化波动率、最大回撤、回撤修复时间
   - 夏普比率、卡玛比率、索提诺比率
   - 下行风险、在险价值（VaR）
   - 风险调整后收益对比

3. **持仓结构对比**
   - 资产配置（股票 / 债券 / 现金 / 其它占比）
   - 重仓股 / 重仓债集中度与重合度
   - 行业分布、市值风格、久期 / 信用等级（债券基金）
   - 换手率与持仓稳定性

4. **管理评估对比**
   - 基金经理任职年限、管理规模、历史业绩
   - 基金公司实力与同类型产品线
   - 管理费率、托管费率、综合费率（含销售服务费）
   - 份额规模与流动性

### 试试这样问

- "帮我对比一下华夏成长和易方达中小盘"
- "易方达蓝筹精选和兴全合润哪个更好？"
- "对比这几只基金：000001.OF, 110011.OF, 163406.OF"
- "华夏成长相比易方达中小盘有什么优势？"
- "分析一下这两只债券基金的差异"
- "我该不该用基金 A 替换基金 B？"

### 输出形式

- **Agent 向用户展示的内容**：CLI stdout 中的 `agentResult.value` 正文（服务端流式返回）
- 自动生成的结构化内容包含：**核心结论、各基金优势、主要风险、投资 / 配置建议**
- 多维度对比：业绩表现、风险指标、持仓结构、管理评估的对比表和专业分析
- 部分场景下 CLI 会**静默**把完整报告附件下载到用户 `Downloads/` 文件夹或 `-d` 指定目录（供用户本地查阅）；**Agent 向用户展示时只用 `agentResult.value`，不要粘贴附件正文**
- 数据受限时在对应模块明确标注

### 💡 使用提示

- 支持 **2–5 只基金同时对比**，建议不超过 3 只以便深入分析。
- 可以使用**基金名称或代码**（如 `000001.OF`）。
- 明确说明"详细分析"可获得更深入的报告。
- 系统会自动识别您的倾向性（如"A 比 B 好在哪"会重点分析 A 的优势）。

### 触发场景与 prompt 构造

用户提问命中以下任一场景即可调用：对比多只基金 / 基金优劣比较 / 基金替换评估 / 同类基金筛选 / 基金尽职调查。

把对比对象（基金名称 / 代码，如 `000001.OF`）和关注维度拼成一句自然语言。**不要加 `使用「...」技能：` 前缀，CLI 内部已自动注入。**

---

## CLI 参数

`<SKILL_DIR>` = 本文件所在目录绝对路径。**Windows 一律用方案 A**（PowerShell 5.x 不支持 `&&`，见 [`AGENT.md`](./AGENT.md)「命令模板」与「禁止写法（Windows）」）；macOS / Linux 用 `node scripts/cli.mjs`。

### 命令行调用

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" --prompt "<USER_QUESTION>" --no-wait [-d "<DIR>"] [--new]
```

```bash
# macOS / Linux
node scripts/cli.mjs --prompt "<USER_QUESTION>" --no-wait [-d "<DIR>"] [--new]
```

### 参数

| 参数 | 说明 |
|------|------|
| `--prompt`, `-p` | 用户提问（对比对象 + 关注角度，自然语言）。**必填**；CLI 自动加 `使用「基金对比分析」技能：` 前缀，Agent 不要再加 |
| `--no-wait` | **Agent 默认必带**——CLI 内部自旋 `tasks/get` 直到终态。默认 60s 一次探针、每轮 30min、全程 60min；到轮上限 **CLI 自动续轮**；Agent 禁止外层 `Start-Sleep` 或连发多条 |
| `-d`, `--download-dir` | 报告附件落地目录；不传则用户 `Downloads/` 文件夹（Windows `%USERPROFILE%\Downloads`）。不存在自动创建；同名冲突自动加 ` (1)` 后缀，**绝不覆盖** |
| `--new` | 用户明确要求**并行新建**时清除本地记录后新建；**须先 check-conflict 询问用户** |
| `--continue-session` | **显式请求**延续上一次多轮会话上下文（opt-in）。**默认每次 CLI 调用视为全新会话**，`contextId` 每次新生成，避免跨 Agent / 跨话题的 context 污染。**宿主 Agent 判定为同一会话追问时（省略式追问 / 明确承接前文 / 代词指代等）应自动加此参数**，不再要求用户显式说「接着刚才那个话题继续」。若上次调用在 30min idle window 内，CLI 会复用上次落盘的 `contextId`；否则退化为新会话。与 `--new` 正交：`--new` 决定是否新建 taskId、`--continue-session` 决定是否复用 contextId |
| `--new-session` | 显式强制新建会话上下文（**与默认行为一致**，保留兼容旧脚本）。与 `--continue-session` 同时给时以 `--new-session` 为准 |
| `--session-scope <ID>` | **宿主 Agent 会话隔离标识**（推荐始终传入）。同一 OS 用户下 Cursor / Trae 等宿主 Agent 默认共享 `~/.wind-alice/current-session.json`；不隔离会出现"A Agent 的续接读到 B Agent 的 `contextId`"这类跨宿主污染。传入 `<ID>` 后按 `current-session.<ID>.json` 隔离到宿主自己的文件。也可用环境变量 `WIND_ALICE_SESSION_SCOPE` 统一设置（命令行 `--session-scope` 优先）。非法字符（空格 / 冒号 / 路径分隔符 / 中文等）自动替换成 `_`，长度上限 64 |
| `--once` | 配合 `--no-wait`，单次探针；**仅脚本调试**，Agent 禁止外层循环 |
| `--no-strict` | 关闭 strict 模式（默认开启：未输出 DONE 行时 exit=0 改成 6）；Agent 禁止传 |
| `--watch-interval` / `--watch-timeout` / `--watch-absolute-max` | 自旋节奏与上限调优（秒），通常默认即可 |
| `--help`, `-h` | 查看帮助 |

> 已废弃：`--watch` / `-w`（`--no-wait` 默认即内部自旋）。

### 调用示例

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" -p "帮我对比一下华夏成长和易方达中小盘" --no-wait
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" -p "易方达蓝筹精选和兴全合润哪个更好？重点看风险和持仓" --no-wait
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" -p "对比 000001.OF 和 110011.OF" --no-wait -d "D:\reports\fund"
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" -p "重新对比华夏成长和易方达中小盘" --no-wait --new   # 仅用户说"重新跑"才加
```

```bash
# macOS / Linux
node scripts/cli.mjs -p "帮我对比一下华夏成长和易方达中小盘" --no-wait
node scripts/cli.mjs -p "易方达蓝筹精选和兴全合润哪个更好？重点看风险和持仓" --no-wait
node scripts/cli.mjs -p "对比 000001.OF 和 110011.OF" --no-wait -d "/reports/fund"
node scripts/cli.mjs -p "重新对比华夏成长和易方达中小盘" --no-wait --new
```

附件用 `WIND_API_KEY` 自动鉴权下载到 `Downloads/` 或 `-d` 目录（CLI 在 DONE 行给出 `reportFullFile=` 路径仅供落盘核对）；**Agent 交付用户时只用 `agentResult.value`，不要展示下载附件内容**。

### 子命令

只读 / 配置类，不消耗服务端额度：

| 子命令 | 用途 |
|--------|------|
| `apikey-set <KEY>` / `apikey-get` / `apikey-clear` | 写入 / 查看（脱敏）/ 清除 `~/.wind-alice/config.env` 中的 API Key |
| `status --prompt <Q>` | 查询本地 tasks.json 中该 prompt 最近一条任务的落盘路径（**禁止常规轮询**；仅 CLI 被反复杀死时允许 1 次，见 `AGENT.md`） |
| `wait --prompt <Q>` | Trae `-IdeSafe` 内部探针用；**禁止 Agent 手动调用** |
| `check-conflict --prompt <Q>` | **主调用前的并发预检**：检测是否有同/相似 prompt 的 running 任务。无冲突 → exit=0；命中 → exit=11，stdout 列出 `EXISTING_TASK ...`，Agent 必须把详情列给用户、由用户三选一（attach / `--new` / 取消）。详见 `AGENT.md`「check-conflict 后用户三选一」 |

### 解析下载目录意图

扫描用户对话中是否说过"下载到 X / 保存到 X / 放到 X 目录"。

- 命中 → 用 `-d "<DIR>"` 传入（多次指定取**最近一次**，含空格的路径必须加双引号）。
- 未命中 → **不要传**该参数；CLI 落到用户 `Downloads/` 文件夹。

---

## 环境与配置

### 1. Node.js 18+

CLI 基于 Node.js（18+ 自带 `fetch`）。`node -v` 检查，未达标到 [nodejs.org](https://nodejs.org/) 下载。

### 2. 获取并配置 `WIND_API_KEY`

**获取**：浏览器打开 [Wind Alice → 设置 → 账户](https://alice.wind.com.cn/settings?tab=account)，在「API Key」一栏点「生成」/「复制」（失效或泄漏点「重置」会让旧 Key 立即作废）。

**写入（推荐用 CLI 子命令）**：

```powershell
# Windows（方案 A）
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" apikey-set <KEY>
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" apikey-get
powershell -NoProfile -ExecutionPolicy Bypass -File "<SKILL_DIR>\scripts\afcmp.ps1" apikey-clear
```

```bash
# macOS / Linux
node scripts/cli.mjs apikey-set <KEY>    # 写入（KEY 裸值，不加引号）
node scripts/cli.mjs apikey-get          # 查看是否已配置 + 脱敏末四位
node scripts/cli.mjs apikey-clear        # 清除
```

CLI 把 Key 写到 `~/.wind-alice/config.env`（Windows `%USERPROFILE%\.wind-alice\config.env`），dotenv 格式单行 `WIND_API_KEY=...`——**这是唯一受支持的位置**。历史无后缀的 `~/.wind-alice/config` 仍可读取，`apikey-set` 会自动迁移。

**手动写入**（无 Node 运维场景）：

```bash
# macOS / Linux
mkdir -p ~/.wind-alice && printf 'WIND_API_KEY=...\n' > ~/.wind-alice/config.env && chmod 600 ~/.wind-alice/config.env
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.wind-alice" | Out-Null
"WIND_API_KEY=..." | Set-Content -Encoding ascii "$env:USERPROFILE\.wind-alice\config.env"
```

> 安全：CLI **不读**环境变量，也**不读** skill 目录内的 `config.json`——避免 Key 残留在 shell 历史 / CI 日志 / 提交记录。`apikey-set` / `apikey-get` stdout 仅回显脱敏 Key；macOS/Linux 会自动把文件权限收到 `600`。

### 配置位置与环境变量

| 路径 / 变量 | 内容 | 必备 |
|-------------|------|------|
| `~/.wind-alice/config.env`（Win: `%USERPROFILE%\.wind-alice\config.env`） | dotenv：`WIND_API_KEY=<KEY>`，**唯一受支持位置**（不读环境变量、不读 skill 目录 `config.json`） | ✅ |
| `~/.wind-alice/tasks.json` | 本地任务注册表（CLI 自动维护） | 自动 |
| `~/.wind-alice/results/<taskId>.md` | 每条任务的 `agentResult.value` 落盘副本（stdout 截断时 Agent 可读） | 自动 |
| `WIND_ALICE_API_URL`（环境变量） | Alice Agent 接口地址，默认 `https://alice.wind.com.cn/Weaver/ChatAgent`，一般无需修改 | 否 |

> 兼容：历史无后缀的 `~/.wind-alice/config` 仍可读取，`apikey-set` 会自动迁移到 `config.env`。

### 中文乱码（Windows 必读）

**根因**：Node 输出 UTF-8 字节，Trae / PowerShell 5.x 管道捕获时默认按 **GBK** 解码 → live 输出变成 `鏈繘绋嬪皢闃诲...`，**不是 CLI 坏了**。

**三层防护（由 CLI 自动提供）**：

1. **`scripts/afcmp.ps1`**：调用前切 UTF-8 代码页（Windows Agent **优先用它**代替裸 `node`）。
2. **`ALICE_SESSION_LOG=`**：非 TTY 管道场景下，CLI 会把全部输出 tee 到 `~/.wind-alice/logs/<promptHash>.session.log`（**完整 64 位** promptHash，UTF-8 BOM）。**只能读 stdout 打印的那条路径**，禁止 `view_folder logs/` 扫描：

   ```powershell
   # ✅ 从本次 CLI stdout 复制 ALICE_SESSION_LOG= 的完整路径
   Get-Content -Path "$env:USERPROFILE\.wind-alice\logs\<promptHash>.session.log" -Encoding UTF8 -Tail 200 -Wait

   # ❌ 禁止：按 mtime 挑「最新」或只认 12 位前缀——不同 prompt（同公司）会落在不同文件
   ```
3. **落盘 `.md`**（`results/`、`Downloads/`、`--detach` 日志）均带 **UTF-8 BOM**，`Get-Content` 即使不写 `-Encoding UTF8` 通常也能正确显示。

**禁止**：因 live 乱码就改 prompt 重试、连发多条 CLI、或手工 `Start-Sleep` 轮询 `tasks.json`。

### 查看 `--detach` 日志（避免中文乱码）

`~/.wind-alice/logs/<hash>.log` 由 CLI 以 **UTF-8** 写入。PowerShell 5.x 的 `Get-Content` **默认按 GBK 解码**，会把 UTF-8 中文显示成 `鏈繘绋嬪皢闃诲...` 这类乱码——**不是日志坏了，是读法错了**。

```powershell
# ✅ 正确：显式指定 UTF-8
Get-Content -Path "$env:USERPROFILE\.wind-alice\logs\969e4c647aae.log" -Encoding UTF8 -Tail 50 -Wait

# ❌ 错误：省略 -Encoding UTF8，中文 Windows 上几乎必乱码
Get-Content -Path "...\969e4c647aae.log" -Tail 50 -Wait
```

自新版 CLI 起，`--detach` 创建的日志文件会写入 **UTF-8 BOM**，部分环境下即使不写 `-Encoding UTF8` 也能正常显示；**仍建议 Agent 始终带 `-Encoding UTF8`**。

---

> **执行契约**（七步流程 / 红线 / 完成判定 / replay / 退出码 / 交付顺序 / 会话续接 / 命令模板 / 自检清单）见 [`AGENT.md`](./AGENT.md)——**唯一权威来源**，本文不重复。
> **排障与常见问题**（任务幂等性与停止行为、CLI 执行失败处理、Q&A）见 [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)。
