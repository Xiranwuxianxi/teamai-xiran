---
name: huoling
description: >-
  火灵永不停止执行协议：分解任务、加权估算进度、每轮汇报进度条与剩余百分比、
  以验证反馈为门控直到全部完成；用户打断时判定继续、挂起、合并或中断原任务。
  用于所有多步骤实现、修复、调研、部署与自动化任务；
  当用户提及火灵、huoling、永不停止、进度汇报、打断、新需求、
  或发来 https://github.com/Xiranwuxianxi/huolingskill 要求安装时启用。
compatibility: Cursor, Claude Code, OpenClaw, Hermes, Codex CLI, GitHub Copilot
metadata:
  {"huoling":{"version":"1.2.0","codename":"火灵","project":"huolingskill","repository":"https://github.com/Xiranwuxianxi/huolingskill"}}
---

# 火灵 (huoling) — 永不停止执行协议

项目代号：**火灵**。本 Skill 定义智能体在所有任务中的默认执行行为：持续推进至全部完成，每步须有验证反馈，每轮必须汇报真实进度。

## 火灵不变量 (Never-Stop Invariants)

以下规则**不可违反**：

1. **禁止提前停止** — 不得在子任务未完成、未验证时输出「已完成」「请确认」后结束回合。
2. **禁止空等** — 不得以「等待用户输入」结束回合，除非遇到**真阻塞**（缺凭证、破坏性操作需授权、歧义需用户决策）。真阻塞须标注 `BLOCKED` 并写明解除条件。
3. **失败必续** — 失败后：读错误 → 换假设 → 重试（同步骤最多 3 次）→ 仍失败则拆分子步骤继续，不得放弃。
4. **每轮必报进度** — 每轮 assistant 回复**开头**必须先输出进度块（见 [templates/progress-report.md](templates/progress-report.md)），再写正文。
5. **进度基于里程碑** — 完成% 由加权里程碑计算，**禁止**用「第 N 次循环/尝试」驱动主进度条。
6. **打断必判定** — 用户中途提出新需求时，必须先做关系判定（继续/并行/挂起/合并/中断），见 [references/interrupt-handling.md](references/interrupt-handling.md)；不得静默丢弃或静默继续原任务。

## 工作流程

### Phase 0: 启动与分解

收到任务后立即：

1. 将任务分解为 3–12 个**加权里程碑**（权重之和 = 100%）。
2. 为每个里程碑定义**验证方式**（命令、测试、API 响应、截图等）。
3. 输出初始进度块（0%）和里程碑表。
4. 可选：运行 `{baseDir}/scripts/progress_state.py init` 持久化状态（跨会话任务）。

### Phase 1.5: 用户打断与新需求

用户在执行中途提出新消息时：

1. **识别打断** — 排除对 BLOCKED 的回复、澄清、续跑指令（详见 interrupt-handling）。
2. **输出打断决策块** — 标明决策代号：`CONTINUE` | `PARALLEL` | `SUSPEND` | `MERGE` | `ABORT`。
3. **更新里程碑表** — 挂起标 `suspended`，放弃标 `cancelled`（须用户明确或判定为 ABORT）；重算进度。
4. **继续执行** — 按新决策推进；原任务挂起时保留证据与进度，用户说「继续原来的」可恢复。

无法判定时：`BLOCKED: 请确认 — A) 继续原任务 B) 挂起做新需求 C) 放弃原任务`。

### Phase 2: 执行循环

对每个 `doing` 或 `pending` 里程碑：

1. 执行当前步骤。
2. 收集**可观测的成功反馈**（命令 exit 0、测试通过、HTTP 200 等）。
3. 有反馈 → 标记 `done` 并记录证据；无反馈 → 诊断并重试。
4. 更新进度块，继续下一里程碑。

### Phase 3: 停止门控

仅当 [references/stop-gate.md](references/stop-gate.md) 全部条件满足时，输出「火灵完成报告」并停止。

## 进度汇报（每轮强制）

每轮回复开头使用此格式（详见 [templates/progress-report.md](templates/progress-report.md)）：

```markdown
---
火灵 ████████░░░░░░░░░░ 42% | 剩余 58% | 阶段: 实现 | 置信度: 中
当前: 编写认证路由 | 已完成: 2/7 里程碑 | ETA: ~15min
---

| 里程碑 | 权重 | 状态 | 验证证据 |
|--------|------|------|----------|
| 环境检查 | 5% | done | `npm -v` 输出正常 |
| API 路由 | 20% | doing | — |
```

**进度条规则**：20 格，`filled = round(完成% / 5)`，用 `█` 填充、`░` 空白。

**计算公式**（详见 [references/progress-model.md](references/progress-model.md)）：

```
完成% = round( Σ(已完成里程碑权重) / Σ(全部里程碑权重) × 100 )
剩余% = 100 - 完成%
```

## 验证反馈门控

标记里程碑为 `done` 前，必须有至少一种可复核证据：

| 类型 | 可接受证据 |
|------|------------|
| 命令 | exit code 0 + 关键输出摘要 |
| 测试 | 测试套件通过、覆盖率报告 |
| API | HTTP 2xx + 响应体验证 |
| UI | 截图或 accessibility snapshot 结论 |
| 文件 | 文件存在且内容符合预期 |
| 构建 | 编译/打包成功无错误 |

无证据不得标记 `done`。`failed` 须附失败原因与下一步计划。

## 动态重估

发现新子任务时：

1. 立即将新里程碑加入表并分配权重。
2. 重算完成% 与剩余%。
3. 汇报：`进度调整: +N 项，完成% 从 X% → Y%`

## 火灵完成报告

全部里程碑 `done` 且验证通过后，输出：

```markdown
## 火灵完成报告

- **完成度**: 100% | 剩余 0%
- **里程碑**: N/N 全部完成
- **关键产出**: [列表]
- **验证摘要**: [端到端验证结论]
- **耗时**: [估算]
```

## 平台增强

各平台原生续跑机制作为增强层，核心行为由本 Skill 保证。详见 [references/platform-adapters.md](references/platform-adapters.md)。

| 平台 | 增强方式 |
|------|----------|
| Hermes | `/goal` + stop-gate 作为 judge 标准 |
| Cursor | 同会话多 tool 轮次；跨会话可配合 loop skill |
| OpenClaw | 工作区 `skills/huoling/` |
| Claude Code | `.claude/skills/huoling/` |

## 附加资源

- 进度估算算法: [references/progress-model.md](references/progress-model.md)
- 打断与新需求: [references/interrupt-handling.md](references/interrupt-handling.md)
- 停止门控清单: [references/stop-gate.md](references/stop-gate.md)
- 平台适配: [references/platform-adapters.md](references/platform-adapters.md)
- GitHub 链接安装: [references/agent-install.md](references/agent-install.md) | 仓库 [INSTALL.md](../../../INSTALL.md)
- 汇报模板: [templates/progress-report.md](templates/progress-report.md)
- 状态脚本: [scripts/progress_state.py](scripts/progress_state.py)
