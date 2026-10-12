# 火灵停止门控 (Stop Gate)

智能体**仅当以下全部为真**时方可停止并输出完成报告。

## 必要条件（全部满足）

### 1. 里程碑完整性

- [ ] 所有项均为 `done`、`cancelled`（已确认放弃）或 `suspended`（已挂起且用户已知）
- [ ] 无未处理的 `pending` / `doing` / `failed`（除非整个原任务已 `suspended` 且新任务在进行中）

### 2. 验证证据

- [ ] 每个 `done` 里程碑均有**可复核的验证证据**
- [ ] 证据类型符合 [progress-model.md](progress-model.md) 中的可接受证据表
- [ ] 无「推测完成」「应该可以」类表述

### 3. 端到端验证（交互类任务）

若任务涉及以下任一类型，必须有一次**端到端成功反馈**：

- API 调用（实际请求 + 2xx 响应）
- UI 交互（点击/输入 + 预期结果）
- 部署（服务可访问）
- 用户可见变更（构建产物、文件输出可验证）

### 4. 完成报告

- [ ] 输出「火灵完成报告」模板（见 SKILL.md）
- [ ] 完成度 = 100%，剩余 = 0%
- [ ] 列出关键产出与验证摘要

## 禁止停止的情形

| 情形 | 正确做法 |
|------|----------|
| 部分里程碑未完成 | 继续执行下一项 |
| 无验证证据就标 done | 执行验证命令/测试后再标 |
| 测试失败 | 修复后重跑，不得跳过 |
| 仅「实现完成」未跑测试 | 运行测试并确认通过 |
| 等待用户说「继续」 | 自动继续，除非真阻塞 |

## 真阻塞 (BLOCKED)

仅以下情况可暂停并请求用户：

| 阻塞类型 | 示例 | 必须标注 |
|----------|------|----------|
| 缺凭证 | API key、密码、token | `BLOCKED: 需要 XXX 凭证` |
| 需授权 | 删除生产数据、force push | `BLOCKED: 需确认破坏性操作` |
| 歧义需决策 | 两种架构方案无法推断 | `BLOCKED: 请确认方案 A/B` |
| 外部不可用 | 第三方服务宕机且无替代 | `BLOCKED: 服务 X 不可达，已重试 3 次` |

阻塞时仍须输出当前进度块，并写明解除条件。

## 打断场景下的停止

| 场景 | 能否对原任务输出完成报告 |
|------|--------------------------|
| `ABORT` 后只做新任务 | 原任务输出「火灵中断报告」（非 100%），新任务独立里程碑 |
| `SUSPEND` 后做新任务 | 原任务**不可**标完成；新任务完成后可恢复挂起项 |
| `PARALLEL` | 两任务分别有里程碑表，各自完成报告或合并总报告 |
| 用户恢复挂起任务 | 继续原里程碑表直至原任务 stop-gate 满足 |

**中断报告**（ABORT 时）：

```markdown
## 火灵中断报告

- **原任务**: [名称]
- **完成度**: X% | 剩余 Y%（已放弃部分不计入）
- **已保留产出**: [列表]
- **取消原因**: 用户切换至新需求
- **新任务**: [名称] — 已接管
```

## Judge 标准（Hermes /goal 等）

将以下作为 goal 完成判定标准，供 judge 模型使用：

```
Goal is DONE only when:
1. All milestones in the progress table are status "done"
2. Every "done" milestone has verifiable evidence in the evidence column
3. For interactive tasks, at least one end-to-end success feedback exists
4. The agent has output the 火灵完成报告 with 100% completion

Goal is NOT done when:
- Any milestone is pending, doing, or failed (in the active task)
- Agent says "please confirm" or "waiting for input" without BLOCKED
- Progress is based on retry/loop count without milestone completion
- Tests were not run when the task requires testing
- User interrupted with new requirement but agent did not output 打断决策 block
- Agent silently dropped suspended task without user ABORT confirmation
```

## 完成报告模板

```markdown
## 火灵完成报告

- **完成度**: 100% | 剩余 0%
- **里程碑**: 7/7 全部完成
- **关键产出**:
  - [产出 1]
  - [产出 2]
- **验证摘要**: [端到端验证结论，含命令/测试/请求结果]
- **耗时**: [估算]
```
