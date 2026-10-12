---
name: nl-echarts
description: >-
  fintrust-deep-research 内嵌出图运行时。父技能按 chart_contracts 填模后调用
  nl-echarts/render-echarts.mjs；禁止独立安装为本 skill，禁止 Agent 手写 option 数据面。
---

# nl-echarts（内嵌）

文件名必须是 `subSKILL.md`（禁止再放 `SKILL.md`，否则会被扫成第二个 skill）。

## 被父技能调用（强制）

1. 出图只认契约：`categories` / `series` / `ohlc` / `unit` / `decimals` / `title` / `caption`。
2. 父技能 `--render-all`：`build_option_from_contract` 填模 → 本目录 `render-echarts.mjs`。
3. 未进 `suggested_chart_slugs` 的 slug 禁止出图；option 内禁止 JS `function`；禁止 SVG/`show_widget`/CDN。
4. HTML 强制本地化：`charts_dir/echarts.min.js` + `script src="./echarts.min.js"`。

```bash
python3 scripts/prepare_workbuddy_report.py --render-all --charts-dir <charts_dir>
```
