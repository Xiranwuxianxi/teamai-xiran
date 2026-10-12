---
name: supervisor-skills
description: >-
  Index and router for the Supervisor-Skills pack (HKUSTDial), 12 academic
  research and paper-writing skills. Use when the user mentions
  Supervisor-Skills, asks which research/paper skill to use, or needs to
  locate the accompanying handbook (科研与写作系统指南). Routes a research
  task to the right skill and points to handbook chapters for background reading.
---

# Supervisor-Skills 索引

来源：https://github.com/HKUSTDial/Supervisor-Skills （CC BY-NC-SA 4.0，非商业用途）
安装位置：`~/.workbuddy/skills/`（12 个技能，各自独立）

## 论文生命周期 → 技能路由

| 阶段 | 任务 | 技能 |
| --- | --- | --- |
| 构思 | 评估 idea 是否值得做、可行性/创新性打分 | `idea-evaluator` |
| 构思 | 技术类论文搭逻辑骨架（思考模板表） | `tech-paper-template` |
| 构思 | Benchmark / Evaluation 类论文搭骨架 | `benchmark-paper-template` |
| 调研 | 综述级文献调研、引用逐条核验 | `deep-research` |
| 写作 | 写 Introduction 六段式正文 | `intro-drafter` |
| 写作 | 写论文正文（证据门控、可溯源） | `paper-writer` |
| 自查 | 投稿前五维审查（逻辑/细节/语法/LaTeX/图） | `pre-submission-reviewer` |
| 润色 | 忠于原意润色、去 AI 腔、中译英 | `paper-polish` |
| 作图 | 动机图/总览图/实验图设计规范建议 | `figure-designer` |
| 作图 | 参考图重建为可编辑 .drawio | `drawio-reconstruction` |
| 返修 | Rebuttal 策略与回应指导 | `rebuttal-guidance` |
| 通识 | AI 辅助科研（Vibe Coding/Figure/Writing） | `vibe-research-workflow` |

## Handbook（理论指南）

多个技能会引用 handbook 章节做延伸阅读，本地路径：

`C:\Users\76809\.workbuddy\Supervisor-Skills\handbook\`（中文）
`C:\Users\76809\.workbuddy\Supervisor-Skills\handbook-en\`（英文）

章节：01 评价论文质量 / 02 Idea 的诞生 / 03 论文写作方法论 / 04 科研作图 / 05 Vibe Research / 06 顶会案例剖析

## 注意事项

- `drawio-reconstruction` 需要 Python `Pillow`；导出 PNG 还需本机安装 Draw.io Desktop CLI。
- 这些技能是第三方上游文件，升级时直接覆盖同名目录即可，不建议手工改动。
