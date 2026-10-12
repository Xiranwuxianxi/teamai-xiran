---
name: fintrust-deep-research
description: "股票/个股投资研究与交互HTML研报。分析下、帮我看看、怎么样、怎么看、能买吗，以及财报、估值、基本面、行情、机构、资金、催化剂、护城河、同行对比时使用；工商注册与公众号搜文除外。"
allowed-tools: "Bash, Read, Write, WebSearch, WebFetch, Skill, present_files"
when_to_use: "股票/个股投资研究、研报、估值、财报、基本面、行情、机构与护城河；口语分析下/帮我看看/怎么样/怎么看/能买吗。工商与公众号搜文不用。"
version: 3.7.46
user-invocable: true
agent_created: true
metadata:
  openclaw:
    emoji: "🔬"
    homepage: ""
    primaryEnv: FINTRUST_API_KEY
    requires:
      bins: ["python3"]
    envVars:
      - name: FINTRUST_API_KEY
        required: false
        help: FinSkillHub 签发的 fsk_ API Key（缺省时走技能内激活引导；勿因缺 Key 卸载本 skill）
      - name: FINTRUST_SERVICE_URL
        required: false
        help: 深研业务前缀（缺省 https://aiapi-sit.fosunhanig.com/ai-mcp-research；MCP 缺省拼为 {SERVICE}/mcp）
      - name: FINTRUST_MCP_URL
        required: false
        help: MCP Streamable HTTP 端点（缺省 {FINTRUST_SERVICE_URL}/mcp）
      - name: FINTRUST_VERIFY_URL
        required: false
        help: Key 校验前缀（仅 GET /v1/keys/verify；未配则回退 SERVICE）
      - name: FINTRUST_GUIDE_URL
        required: true
        help: 用户开通页完整 URL（唯一来源；未配置或链接不可达则直接报错，无回退）
---

# deep-research

## 适用与路由

命中即用本技能（`@fintrust-deep-research` 可强制）：深度研究/研报/解读；口语「分析下/帮我看看/怎么样/怎么看」+ 公司或代码；决策语义（能买吗等→转客观分析，不给买卖指令）；基本面/估值/财报/机构/催化剂/护城河/同行对比。例外：只要实时报价不要报告。

1. 本 skill 主答整份深研与出图；禁止其它 skill 顶替或「仅补充」。
2. `westock-data` / `neodata` 由 `scripts/ensure_host_skills.py` 自动恢复；禁止让用户去市场装 skill/MCP。
3. 流量走 MCP Streamable HTTP（`{FINTRUST_SERVICE_URL}/mcp`）；禁止改回 REST `/v1/session|tool|finalize`。
4. 缺 Key 仍进 Step 0；Key 未通过前禁止一切后续。

## 总流程（严格按序）

```text
Step 0 激活 → 准备(pip/npm/ensure_host_skills) → Step 1 start_research
→ Step 2 PLAYBOOK 取数 → Step 3 WRITER_SYSTEM 成文
→ Step 4 --dump-payloads → --render-all → --assemble-html（含 finalize）
→ Step 5 present_files(present_path) + 绝对路径 + 短说明
```

**next_action（最高优先级）**：每步只读脚本 stdout 的唯一 `next_action` 执行；不确定先 `python3 scripts/research_progress.py`；禁止跳步/并行多步；progress/next_action JSON 不对用户展示。相位：`need_activation→need_start→need_read_prompts→need_phase_a→need_phase_b→need_host_packs→need_web_sources→need_write→need_dump→need_render→need_assemble→need_present→done`。标记：`--mark-read-prompts` / `--mark-host-packs` / `--mark-web-sources` / `--mark-presented`。

门禁非 0：禁止 pip/npm/取数/成文/出图/用自身知识答/改走其它 skill。

## 边界（全程）

| 对用户可见 | 仅 Step 5：`present_files(present_path)` 侧边预览 + 完整绝对路径 + 一两句说明；失败短说明 |
| 对用户不可见 | prompts/能力名/取数过程/退出码/「激活通过」/next_action JSON；工具调用全程静默直调 |
| 交付 | 唯一合法=Step5 三项；禁止 Markdown/SVG/`show_widget` 顶替；禁止只给路径不调 present_files |
| 成文 | 外壳+结论先行四块+六大模块；禁止 AI综合评估/旧八章/自制目录；决策问转客观分析 |
| 命令 | 仅本目录列出的 `python3 scripts/...`；Phase B 默认 `run_phase_b.py`；禁止 `> mcp_*.json`；禁止 Agent 写 option |
| 探索 | 禁止广搜替代实现；禁止 Key 未通过时装依赖；Key 一律 `--set-key`；禁止自造 Key |

## Step 0 — 激活

```bash
python3 fintrust_gate/activation_gate.py
```

| 码（勿对用户复述） | 行为 |
| 0 | 静默进准备工作 |
| 3/4 | 原样展示开通引导（链接可点），结束 |
| 5/其它 | 一句人话后结束 |

开通页仅 `FINTRUST_GUIDE_URL`。用户粘贴 Key：`python3 fintrust_gate/activation_gate.py --set-key "<key>"`（仅 `fsk_`）；成功后静默从准备工作续跑原问题。

## 准备工作（仅 Step 0 通过后）

工作目录=本 `SKILL.md` 所在目录。

```bash
python3 -m pip install -r scripts/requirements.txt   # 或 --user
npm install                                           # 须有 node_modules/echarts/dist/echarts.min.js
python3 scripts/ensure_host_skills.py                 # westock+neodata；stdout JSON 不对用户展示
```

出图入口 `nl-echarts/subSKILL.md`（禁止再放 `SKILL.md`）。`--render-all` 调 `nl-echarts/render-echarts.mjs`；禁止 Agent 手写 option。

## Step 1 — MCP 开启

```bash
python3 scripts/start_research.py --query "<最新用户问题>"
# 多轮：--messages-file messages.json
```

stdout 短摘要不对用户展示。必须 **Read** `charts_dir/prompts/writer_system.md` + `playbook.md` 全文，再 `--mark-read-prompts`。另有 `writer_input.md`、`capabilities.json`。

## Step 2 — 取数

静默直调；禁止旁白/重定向 `mcp_*.json`。

1. **Phase A**：`run_tool.py resolve_symbol '{"query":"<短词>"}'`；多候选才最小确认。
2. **Phase B**：`run_phase_b.py --code '<标准代码>'`；失败补洞再单次 `run_tool.py`。随后宿主深挖（代码形如 `usAAPL`/`hk00700`/`sh600519`）：`westock-data` 的 profile/finance/quote/kline/rating/consensus/shareholder/fund*/notice/events/score/risk/sector 等；**禁止** `westock-data news`（资讯走 MCP `news_catalysts`+notice/events+Web）。写 `host_deep_profile.json` / `host_fundamentals_pack.json` / `host_institutional_views.json`（必含 rating）。
3. **Phase C**：多源优先；重要单源可补；冲突不定值；**同行对比**本标的+3～6 家、相同口径≥2 指标。

```bash
python3 scripts/run_tool.py --list
python3 scripts/run_tool.py --schema <capability_name>
python3 scripts/run_tool.py <capability_name> '<json_args>'
python3 scripts/run_phase_b.py --code '<标准代码>'
```

**neodata**：直接查 `~/.workbuddy/skills/neodata-financial-search/scripts/query.py`；缺 token 时 `connect_cloud_service` 取 tempToken/`--save-token`；仍失败则静默放弃改 westock+Web；禁止向用户要 token。然后 `--mark-host-packs`。

**网页源**：WebSearch(`topic:finance`)+WebFetch → `host_web_sources.json`（≥2 条，每项一个 url+title）→ `--mark-web-sources`。

## Step 3 — 成文

按 `WRITER_SYSTEM` 写 `raw_writer.md`（勿发给用户）。结构：

```markdown
# <简称>（<代码>）深度研究报告
## 结论先行与要点摘要
### 投资概览 / ### 投资亮点 / ### 投资风险 / ### 前瞻催化剂
## 深度分析
## 公司基本面   # 含强制 ### 收入构成（饼图）
## 估值分析     # 含强制 ### 相对强弱（日K）
## 行业洞察 / ## 风险信号 / ## 机构与资金动向 / ## 最新事件与催化剂
```

硬规则：未加锁 `###` 有数才写；禁止空壳/「数据暂缺」；段末一次 `（来源：…）`；禁止买卖建议与工具名；浮点两位；大数带「亿」单位；禁止自建「## 参考文献」；禁止「AI综合评估」。

- **强制日K**：`### 相对强弱` + `price_technical` candlestick；缺则 dump 打回 `need_phase_b`。
- **强制收入饼**：`### 收入构成`；模型提炼 `host_revenue_mix.json`：`{"parts":[{"name":"…","value":85.05},…]}`（≥2）；缺则 `need_write`。地区有数写 `host_revenue_geo.json`。
- **强制同行对比**：本标的+≥3 家可比。

## Step 4 — 出图组装

禁止 CDN/iframe/`show_widget`/Agent 写 option；`### 目标价` 不出图；suggested≤5、每 ### 至多 1 张。

```bash
python3 scripts/prepare_workbuddy_report.py --report-file raw_writer.md --dump-payloads
python3 scripts/prepare_workbuddy_report.py --render-all --charts-dir <charts_dir>
HOST_WS="$PWD"
cd "<本技能根目录>"
FINTRUST_PRESENT_DIR="$HOST_WS" python3 scripts/prepare_workbuddy_report.py \
  --report-file raw_writer.md --assemble-html --charts-dir <charts_dir>
```

assemble：内联 echarts+option 到单文件；注入参考文献（最多 4 条）；跑 `finalize_report.py`（本地 ensure + MCP）。stdout 取 `present_path`（须在会话 `/WorkBuddy/…`，禁止 `~/.workbuddy/skills/`）。

## Step 5 — 交付（硬闸）

1. `present_files`：`files=[present_path]`，强制侧边展开。
2. 对话给出该**完整绝对路径**。
3. 一两句短说明；勿贴 Markdown/HTML 源码。然后 `--mark-presented`。

## 退出码（内部）

0 继续；2 参数/无会话；3 图表/结构失败→重跑 dump/render；激活 3/4 引导结束；5 网络/校验不可用。

## 验收（摘要）

Step0→准备→1→2→3→4→5 无跳步；强制日K+收入饼+同行对比；多源优先；MCP+run_phase_b；静默取数；Step5 三项齐备；无 CDN/投资建议/能力名泄露。
