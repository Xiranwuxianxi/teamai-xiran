---
name: daily-financial-news
description: >-
  多源财经资讯聚合与智能摘要。接入财经新闻数据库，完成获取、清洗、主题聚类、 逐条深度概括后生成可视化 HTML 日报，支持新闻汇总与快讯两种模式。 适用：每日财经要闻整理、市场电报实时追踪、舆情简报生成。 触发：财经新闻、新闻汇总、电报快讯、市场资讯、每日简报。
agent_created: true
version: 1.0.1
display_name: "每日财经新闻"
display_name_en: "Daily Financial News"
description_zh: "财经新闻多源接入与深度解读，经去重分类后逐条深度概括，附市场影响解读。"
description_en: "Multi-source financial news aggregation with deduplication and deep summaries."
visibility: "public"
---

# 多源财经资讯聚合与智能摘要

## 能力概览

本 skill 提供财经资讯的端到端处理管线，覆盖两种典型需求：

1. **日报生成**：按日期拉取多维度财经新闻，经过时间筛选、跨源去重、主题分类、逐条深度
   摘要后产出自包含 HTML 报告。
2. **快讯接入**：拉取财经电报/快讯类短资讯，归一化后输出 HTML 列表（也可按需输出 JSON）。

两种模式共用同一数据通道（通过 `neodata-financial-search` 自然语言查询），只是处理深度与产出形态不同。

> **输出默认**：正式交付为自包含 `.html`；对话中只给一句话摘要 + 文件路径。HTML 风格为资讯阅读风
> （浅底纸感排版），结构参考 `references/news_report_template.html`。
> 仅用户明确要求 Markdown / 纯文本 / JSON 时才切换格式。
>
> **加载顺序**：先加载 `wb-finance-skill` 获取合规红线（如涉及投资解读），再调 neodata 取数据。

## 适用场景

- 生成某日的财经新闻汇总报告
- 对财经新闻做分类整理与深度摘要
- 输出每日财经简报（晨报/午报/晚报均可）
- 接入实时财经电报与市场快讯
- 构建舆情热度仪表板或投顾沟通素材库

## 模式一：日报（新闻抓取与深度摘要）

### 参数约定

执行前由用户指定以下参数，不指定则用默认值：

| 参数 | 含义 | 默认值 | 示例 |
|------|------|--------|------|
| `{DATE}` | 目标日期 | 当天 | `2026-06-27` |
| `{TIME_START}` | 起始时间（HKT） | `00:00` | `00:00` |
| `{TIME_END}` | 截止时间（HKT） | `20:00` | `20:00` |
| `{OUTPUT_DIR}` | 产物目录 | 当前工作目录 | `.` |

### 阶段一：拉取原始新闻

通过 `neodata-financial-search` 的自然语言查询，覆盖以下五个维度，每个维度单独查询：

1. 港股市场 — 当日要闻、个股异动、板块动态
2. 国际财经 — 全球宏观、央行政策、地缘事件
3. 内地财经 — 经济政策、行业动态、资本市场
4. 地产市场 — 香港及内地地产信息
5. 金融市场 — 大宗商品、外汇、债券

调用示例：

```bash
python3 scripts/query.py --query "港股今日要闻 {DATE}"
python3 scripts/query.py --query "国际财经新闻 {DATE}"
python3 scripts/query.py --query "中国财经新闻 {DATE}"
python3 scripts/query.py --query "香港地产市场新闻 {DATE}"
python3 scripts/query.py --query "金融市场大宗商品外汇新闻 {DATE}"
```

> `scripts/query.py` 位于 `neodata-financial-search` 的 skill 目录下。调用前确认该 skill 已安装
> 且凭证有效。若返回 `TOKEN_EXPIRED` 或 `TOKEN_MISSING`，按 neodata-financial-search SKILL.md
> 的凭证获取流程处理。

**字段提取**：从返回的 `data.docData.docRecall` 中取每条新闻的 `title`、`publishTime`、`source`、
`url`、`content`。

### 阶段二：逐条提取关键信息

对每条新闻记录以下四项：

1. 完整标题
2. 发布时间（精确到分钟，如 `02:34`）
3. 原文链接 URL
4. 内容摘要（来自返回的 `content` 字段）

### 阶段三：时间过滤与去重

1. **时间窗口**：只保留 `{DATE} {TIME_START}` 至 `{DATE} {TIME_END}` HKT 的新闻
2. **时区**：`publishTime` 为 Unix 时间戳（秒），统一转 HKT（GMT+8）后过滤
3. **去重规则**：标题相似度 > 80% 且发布时间差 < 30 分钟视为同一条，只保留其中一条
   - 优先保留来源更权威的（官方媒体优先于自媒体）
4. 向用户报告：`共获取 X 条，去重后 Y 条`

### 阶段四：访问原文获取完整内容

对去重后的每条新闻，访问其 URL 抓取完整正文。

> 若 `content` 已是完整正文，可跳过此步。

抓取时关注五个要素，用于后续深度摘要：

- 核心事件：发生了什么
- 关键数据：股价、指数、百分比、金额等具体数字
- 人物表态：关键人物原话或直接表态
- 事件背景：前因后果
- 市场影响：对金融/行业/政策的潜在影响

### 阶段五：主题聚类

将同类新闻归入同一主题。常用分类如下（可根据当日新闻灵活调整）：

1. 地缘政治 / 国际局势
2. 全球宏观 / 货币政策 / 经济数据
3. 大宗商品 / 金融市场
4. 企业动态
5. 中美科技与贸易博弈
6. 香港本地政策与社会
7. 极端天气 / 自然灾害
8. 港股 / 亚太市场

规则：
- 同主题新闻按发布时间从早到晚排列
- 同一事件的连续报道合并为一条（保留最新进展）

### 阶段六：逐条深度摘要

每条新闻写 200–400 字深度摘要，包含以下要素：

1. 核心事件概述（首段）
2. 具体数字数据（第二段，如可用）
3. 关键人物表态或原话
4. 事件背景与前因后果（第二或第三段）
5. 对金融市场/行业的影响分析（末段）

格式：
- 多段落（2–3 段），段间空一行
- 非一句话摘要，有分析深度
- 内容多的可接近 400 字，内容少的约 200 字
- 每条末尾补「所以呢」：数据背后的含义或可观察信号（不做买卖建议）

### 阶段七：生成 HTML 报告

按 `references/news_report_template.html` 写出自包含 HTML，并遵循 `wb-finance-skill` 的
`references/html-report-style.md`：

- 资讯阅读风：浅底、墨色标题区、时间线/标签；避免暗色仪表盘
- 首屏结论先行：顶部「今日要点」3–6 条 + 抓取/去重统计卡片
- 按主题分节；每条含标题、时间、来源标签、原文链接、深度摘要、「所以呢」解读
- Agent 用文件写入工具直接生成 HTML，不依赖本 skill 本地脚本

保存建议：`{OUTPUT_DIR}/{YYYY-MM-DD}-财经新闻汇总.html`。

可选产物（仅用户明确要求时）：
- `{YYYY-MM-DD}-财经新闻汇总.txt` — 纯文本版
- `final_articles_v3.json` — 结构化 JSON（标题、链接、时间、摘要、主题、正文、概括）

对话交付：一句摘要（条数 + 1–2 个最重要主题）+ HTML 路径。含内联 JS/图表时交付前 `node --check`。

### 日报注意事项

- 五个维度的查询必须全部执行，不可遗漏
- Unix 时间戳转时区注意使用 HKT（GMT+8）
- 深度摘要不是简单复述，需含数据、表态、背景分析和市场影响
- 若某次查询返回空，可改写 query 表述（如补充具体日期、市场名）重试
- 报告中不暴露具体数据源名称、抓取路径；统一用「综合消息面」「市场反馈」等中性表述

---

## 模式二：快讯接入（电报/短资讯流）

### 能力说明

通过 `neodata-financial-search` 的文档召回能力获取财经快讯/电报类短内容。面向阅读时默认输出
HTML；面向脚本/仪表盘嵌入时输出归一化 JSON。

### 执行流程

1. 主查询：用 `neodata-financial-search` 查财经快讯/电报
2. 补查：按市场细分查询（A 股、港股、全球宏观等），确保覆盖全面
3. 解析归一化：从 `docData.docRecall` 提取 `content`、`title`、`publishTime`、`source`、`url`
4. 输出：默认按模板写 HTML（快讯列表）；用户要数据接口时再给 JSON

调用示例：

```bash
python3 scripts/query.py --query "今日财经快讯 财联社电报"
python3 scripts/query.py --query "A股市场最新快讯"
python3 scripts/query.py --query "港股市场最新快讯"
python3 scripts/query.py --query "全球宏观最新快讯"
```

### 返回字段

从 `docData.docRecall[].docList[]` 提取：

| 字段 | 类型 | 含义 |
|------|------|------|
| `title` | str | 新闻标题 |
| `content` | str | 新闻正文/摘要 |
| `publishTime` | number | Unix 时间戳（秒） |
| `source` | str | 文章来源 |
| `url` | str | 文章链接 |

### 归一化规则

- 若 `title` 存在且不包含在 `content` 中，前缀：`title｜content`
- `publishTime`（Unix 时间戳）转本地时间字符串 `%H:%M`
- 按来源和时间排序，最新优先

### HTML 输出（默认）

按 `references/news_report_template.html` 的快讯列表结构生成，保存建议：
`{OUTPUT_DIR}/{YYYY-MM-DD}-财经快讯.html`。首屏放「最新要点」3–5 条，下方按时间倒序列出归一化快讯。

### 快讯注意事项

- 查询返回空时尝试换 query 关键词重试（如「财经电报」→「市场快讯」→「财经要闻」）
- 快讯类查询建议不传 `--data-type`（默认 `all`），同时覆盖 API 和文档召回
- 需要深度内容时，对感兴趣的新闻可追加 neodata 查询获取完整正文

## 前置条件

### 运行环境

- **Python >= 3.7** — 运行 neodata 查询脚本
- **Node.js**（可选）— 若 HTML 含内联 JS/图表，交付前 `node --check`

### 依赖 Skill

| Skill | 用途 |
|------|------|
| `neodata-financial-search` | 自然语言查询获取港股/财经新闻、快讯、电报等资讯 |
| `wb-finance-skill` | HTML 研报输出规范（`references/html-report-style.md`） |

### 数据源

所有财经新闻数据统一通过 `neodata-financial-search` 获取，其内部聚合多源金融资讯（财经媒体、
券商研报、公司公告等），无需单独配置外部数据源。

## 产物交付

1. 默认 HTML：两种模式正式交付均为自包含 `.html`
2. Agent 直写：读取模板 + `wb-finance-skill/references/html-report-style.md` 后写入文件
3. 对话回复：一句摘要 + 文件路径
4. 可选：用户明确要求时再输出 txt / JSON

## 参考文件

| 用途 | 路径 |
|------|------|
| 新闻/快讯 HTML 模板 | `references/news_report_template.html` |
| HTML 研报风格规范 | `wb-finance-skill/references/html-report-style.md` |

## 免责声明

所有获取数据仅供市场热度追踪和投顾沟通参考，不作为投资建议。转发内容给客户时须附带风险免责声明。
