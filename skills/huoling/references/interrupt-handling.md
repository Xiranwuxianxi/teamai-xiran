# 火灵打断与新需求处理

用户在执行过程中打断并提出新需求时，火灵**不得**默认丢弃原任务或默认继续原任务。必须先做**关系判定**，再执行对应策略，并汇报决策。

## 触发条件

以下任一情形视为「打断」：

- 用户在 agent 执行中途发送新消息（非对当前 BLOCKED 的回复）
- 新消息引入与当前里程碑表**不同**的目标、范围或优先级
- 用户明确说「先停一下」「换个需求」「别做了」「加上这个」

以下**不算**打断（按原流程继续）：

- 回答 BLOCKED 所需的凭证/授权/决策
- 对当前步骤的补充说明、澄清、验收标准细化
- 「继续」「接着做」类续跑指令

## 四步处理流程

### Step 1: 识别并暂停当前动作

1. 停止正在执行的 tool/操作（若可安全中断）。
2. 保留已完成里程碑与验证证据，**不得**删除或覆盖。
3. 在进度块中标注 `⚡ 用户打断`。

### Step 2: 关系判定（5 种决策）

对比**原任务**与**新需求**，选择唯一决策：

| 决策 | 代号 | 判定条件 | 动作 |
|------|------|----------|------|
| **继续原任务** | `CONTINUE` | 新需求是当前任务的澄清、细化、验收调整；不改变目标与范围 | 将新需求并入当前 `doing` 里程碑或追加子步骤；**不**挂起原里程碑 |
| **并行追加** | `PARALLEL` | 新需求独立且与原任务无冲突；用户未要求停止原任务 | 原里程碑表保持；新增「新需求」里程碑组并分配权重；重算进度 |
| **挂起原任务** | `SUSPEND` | 新需求更紧急；用户暗示「先做这个」但未否定原任务 | 将原任务所有 `pending`/`doing` 标为 `suspended`；为新需求建立新里程碑组；记录挂起点 |
| **合并调整** | `MERGE` | 新需求修改了原任务范围（加功能、改方案），原任务仍有效 | 更新/新增里程碑，取消被替代项（标 `cancelled` 并注明原因）；重算权重至 100% |
| **中断原任务** | `ABORT` | 用户明确放弃、替换、否定原任务（「不要了」「换成…」「停止原来的」） | 将原任务未完成的 `pending`/`doing`/`suspended` 标为 `cancelled`；以新需求为唯一活跃任务重建里程碑 |

**无法判定**时：输出 `BLOCKED: 请确认 — A) 继续原任务 B) 挂起原任务做新需求 C) 放弃原任务`，**仅此时**可等待用户。不得猜测。

### Step 3: 判定依据（快速检查清单）

按顺序检查：

1. **意图词**：「不要」「停止」「换成」「算了」→ 倾向 `ABORT`；「另外」「还要」「顺便」→ 倾向 `PARALLEL`；「先做」「紧急」→ 倾向 `SUSPEND`；「其实是」「我的意思是」→ 倾向 `CONTINUE` 或 `MERGE`
2. **范围重叠**：新需求是否被原任务里程碑覆盖？是 → `CONTINUE`；部分重叠 → `MERGE`；无重叠 → `PARALLEL` 或 `SUSPEND`
3. **冲突性**：两任务是否争抢同一资源/文件/方向？是 → 不可 `PARALLEL`，在 `SUSPEND` 与 `ABORT` 间选
4. **用户明确性**：用户是否明确保留原任务？未提及且新任务独立 → 默认 `SUSPEND`（保留原任务），**不**默认 `ABORT`

### Step 4: 汇报与执行

打断后**第一轮**回复必须包含「打断决策块」：

```markdown
> ⚡ 打断决策: SUSPEND | 原任务挂起，优先新需求
> 原任务: 实现 REST API (35% 已完成，3 项 suspended)
> 新需求: 修复登录页样式 bug
> 理由: 新需求更紧急，用户未要求放弃 API 工作
```

然后输出更新后的进度块与里程碑表，再执行新决策下的工作。

## 里程碑状态扩展

| 状态 | 含义 | 计入完成% | 计入剩余工作 |
|------|------|-----------|--------------|
| `suspended` | 原任务挂起，待恢复 | 否 | 是（恢复后继续） |
| `cancelled` | 用户确认放弃 | 否 | 否 |

**重算公式**（有 `cancelled` 或 `suspended` 时）：

```
有效权重 = Σ(非 cancelled 里程碑权重)
完成% = round( Σ(done 权重) / 有效权重 × 100 )
剩余% = 100 - 完成%
```

`suspended` 计入有效权重与剩余工作；`cancelled` 从有效权重中剔除。

## 恢复挂起任务

用户说「继续原来的」「恢复 API 任务」时：

1. 将目标 `suspended` 里程碑改回 `pending`
2. 将当前新任务里程碑标 `suspended` 或 `done`（若已完成）
3. 汇报：`恢复: 原任务 XXX，挂起项 YYY`
4. 从第一个 `pending` 继续执行

## 多任务队列（PARALLEL / SUSPEND）

状态中可维护任务队列（可选脚本 `progress_state.py interrupt`）：

```json
{
  "active_task": "fix-login-css",
  "task_queue": [
    {"id": "rest-api", "status": "suspended", "progress": "35%"},
    {"id": "fix-login-css", "status": "active", "progress": "0%"}
  ]
}
```

## Hermes /goal 集成

打断后若使用 `/goal`：

- `ABORT` → `/goal clear` 后 `/goal <新目标>`
- `SUSPEND` → `/subgoal` 追加新条件，或更新 goal 文本包含两项优先级
- `CONTINUE` → 不修改 goal，仅更新里程碑表

Judge 标准补充：

```
If user interrupted with new requirement:
- Agent must output 打断决策 block before proceeding
- ABORT requires cancelled milestones with reason
- SUSPEND requires suspended milestones preserved
- Must not silently drop original task progress
```

## 禁止

- 不打断决策块就直接切换任务
- 用户未确认时擅自 `ABORT` 原任务
- 打断后丢失已完成里程碑的证据
- 用「已收到新需求」代替关系判定
