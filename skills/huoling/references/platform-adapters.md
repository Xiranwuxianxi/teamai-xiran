# 火灵平台适配

火灵 Skill 遵循 [Agent Skills 开放标准](https://agentskills.io/home)。同一 `SKILL.md` 可在多平台复用；以下为各平台安装路径与续跑增强。

## 安装路径

| 平台 | 项目级 | 全局 |
|------|--------|------|
| Cursor | `.cursor/skills/huoling/` | `~/.cursor/skills/huoling/` |
| Claude Code | `.claude/skills/huoling/` | `~/.claude/skills/huoling/` |
| OpenClaw | `skills/huoling/` 或 `/.agents/skills/huoling/` | `~/.agents/skills/huoling/` |
| Hermes | `.agents/skills/huoling/` | `~/.agents/skills/huoling/` |
| GitHub Copilot | `.github/skills/huoling/` | — |
| Codex CLI | 项目 `.agents/skills/` | `$CODEX_HOME/skills/` |

使用仓库根目录的 `install.ps1` 或 `install.sh` 一键同步到当前项目各平台目录。

## Cursor

**续跑**：同会话内通过多轮 tool 调用持续推进；不要在一轮内提前结束。

**跨会话**：可配合 Cursor `loop` skill 作心跳唤醒，但进度仍按火灵里程碑计算，不得用 loop 次数代替进度。

**路径**：`{baseDir}` 在 Cursor 中指向 skill 目录，脚本引用用 `{baseDir}/scripts/progress_state.py`。

## Claude Code

**续跑**：会话内多 tool 轮次；长任务用 Todo 清单与火灵里程碑表对齐。

**安装**：复制到 `.claude/skills/huoling/` 或 `~/.claude/skills/huoling/`。

**注意**：Claude Code 的 `allowed-tools` 若存在，火灵不限制工具集；按任务需要调用。

## OpenClaw

**续跑**：OpenClaw agent 多轮 loop；火灵指令在每轮加载后生效。

**路径**：工作区 `skills/huoling/` 优先级最高。参见 [OpenClaw Skills 文档](https://docs.openclaw.ai/tools/skills)。

**可选 metadata**（单行的 `metadata` JSON）：

```yaml
metadata:
  {"openclaw":{"requires":{"bins":[]}},"huoling":{"version":"1.0.0"}}
```

无 `metadata.openclaw` 时 skill 默认 eligible。

## Hermes

**续跑**：使用 `/goal <目标>` 让 judge 在每轮后判定 done/continue。

**集成**：

1. 启动任务时：`/goal <用户目标>。成功标准：全部里程碑 done 且有验证证据，输出火灵完成报告。`
2. 每轮回复开头必须带火灵进度块。
3. 将 [stop-gate.md](stop-gate.md) 中的 Judge 标准作为 goal 的 success criteria。
4. `/goal resume` 在 turn budget 用尽后继续。
5. `/subgoal` 可追加验收条件，不破坏主循环。

**Judge 提示**：若响应中进度 < 100% 或存在 pending/doing 里程碑，判定 `continue`。

## Codex CLI / GitHub Copilot

**安装**：`.agents/skills/huoling/` 或 `.github/skills/huoling/`。

**行为**：与核心 SKILL 相同；progress_state.py 可在支持 exec 的环境中持久化跨轮状态。

## 跨平台一致性

| 行为 | 所有平台 |
|------|----------|
| 每轮进度块 | 必须 |
| 里程碑权重进度 | 必须 |
| 验证门控 | 必须 |
| 禁止空等 | 必须 |
| progress_state.py | 可选，有 Python 时推荐 |

## 显式启用

用户可说「用火灵」「huoling 模式」「永不停止」以强调本协议；因 description 广域匹配，多步骤任务也会自动加载。

**打断**：Hermes 上用户消息优先于 continuation loop；火灵须在回复中输出打断决策块。`/goal clear` + 新 `/goal` 对应 `ABORT`；`/subgoal` 对应 `MERGE` 或 `PARALLEL`。
