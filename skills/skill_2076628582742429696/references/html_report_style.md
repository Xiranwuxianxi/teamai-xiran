# HTML 复盘报告输出规范

分析/复盘型回答产出 HTML 文件时遵循本规范。

> **权威原则**：图表库、JS 自检、图/表切换、双轴与空值细则以官方 `wb-finance-skill/references/html-report-style.md` 为准。本文件只补充 A 股复盘的**章节结构**与**配色约定**；路径一～四按结构写 HTML，路径五用 `hotspot_report_template.html`。

## JS 语法自检（交付前必须执行）

见 wb-finance `html-report-style.md` §0。含 ECharts 的报告交付前必须 `node --check`。

## ECharts 图表库引用

引库与 option 骨架直接套用 wb-finance 文档；只替换 data / 标签。

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

若改为 head **内联**整库：业务初始化须与库分属两个平级 `<script>`（或库在 head、初始化在 body 末尾**单个** script）。**禁止** `<script>` 嵌套；内层 `</script>` 会截断外层，导致 `echarts.init` 不执行。

## 配色规范（硬约束 + 本 skill 视觉）

**硬约束（对齐 wb-finance）**：浅底深字；上涨 `--red` / `#dc2626`，下跌 `--green` / `#16a34a`；**首屏 `.tldr` 结论卡先行**。

**本 skill 视觉**：路径一～四可用石板蓝/行情蓝（`--accent` 建议 `#1e40af`～`#1e3a5f` 区间，勿强行与其它 skill 同色）；路径五热点速览严格跟 `hotspot_report_template.html`（橙红脉冲：`--accent #c2410c`）。禁止默认暗色仪表盘。

## 页面结构（路径一～四）

```
header（标题 + 日期）
.tldr 首屏结论卡（一句话定性 + 关键数据 + 条件→操作→止损框架）
## 技术面 / 情绪 / 短线 / 全景 …（按所选路径）
## 次日关注 / 风险提示
footer 免责声明
```

路径五热点速览：严格按 `hotspot_report_template.html`（已含 `.tldr` + ECharts）。

## 图表质量要求

趋势/对比/占比用 ECharts；查阅型用表格；优先图/表可切换。细则见 wb-finance §3–§4。
