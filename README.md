# TeamAI 团队仓库

用 Git 管理 AI Agent 的技能（Skill）、规范（Rules）和环境配置（Env）——像管理代码一样管理团队的 AI 能力。改动走分支 + 评审，合入后所有接入的 Agent 自动拉取最新版，出问题可回滚。

> 基于腾讯云 [teamai-cli](https://github.com/Tencent/teamai-cli) 的仓库模板。

## 它是什么

```
你的技能改动（新增/修改/修复）
        │  commit + push（或 PR）
        ▼
   本仓库（唯一可信源）
        │  会话启动钩子自动 pull（teamai pull --force 可手动强制）
        ▼
各 Agent 本地落地（~/.hermes/skills 等）→ 全员同版本
```

本质是 **GitOps 思路搬到 AI 协作**：技能是 manifest，仓库是源，Agent 是执行器。

## 快速开始

```bash
# 1. 安装 CLI（需 Node 22+）
npm install -g teamai-cli

# 2. 初始化（交互式选 agent/scope；非交互加 --scope user 和 TEAMAI_NONINTERACTIVE=1）
export GITHUB_TOKEN=***   # 仓库访问 token
teamai init https://github.com/Xiranwuxianxi/teamai-xiran --scope user

# 3. 后续同步
teamai pull            # 日常拉取（团队仓无变化时会跳过 scope）
teamai pull --force    # 强制重铺（修复"delivered but unreadable"时用）

# 4. 健康检查
teamai doctor          # 校验技能落地、钩子注入、指令同步全链路
```

接入后，支持会话钩子的 Agent（Hermes / OpenClaw / Copilot）在每次会话启动时自动拉取最新技能，无需手动操作。

## 目录结构

| 目录 | 内容 | 状态 |
|---|---|---|
| `skills/` | 团队技能库（163 个） | 主体 |
| `rules/` | 团队工作规范（Rules） | 预留，待填充 |
| `env/` | 注入 shell profile 的环境变量 | 预留，待填充 |
| `members/` | 成员清单 | 预留，待填充 |
| `docs/` | 团队文档 | 预留，待填充 |
| `teamai.yaml` | 仓库配置 | 已配 |

### skills/ 分类速览

| 分类 | 代表技能 | 数量 |
|---|---|---|
| 内容创作 | baoyu-*（22 个）、khazix-writer、wechat-write、xiaohongshu-write、juejin-viral-article-writer | ~32 |
| 金融数据 | ifind-finance-data、westockdata、mx-finance-data/search、gf-lhb-list、gf-fund-invest、index-query | 7 |
| A 股复盘/选股 | a-share-daily-review、alice-a-share-short-term-strategy-report、alice-broker-top-picks-tracker、fintrust-deep-research、research-report | 11 |
| 基金/筛选 | alice-fund-compare、alice-fund-screening-investment-advisory、pa-public-fund-filter、open/etf-fund-query | 5 |
| 资讯聚合 | aihot、daily-financial-news、news-search、wechat-viral-topic | 8 |
| 视频/音频管线 | huashu-art-motion、koubo-video-pipeline、voice-clone-*、digital-human、promo-video-maker | 11 |
| 开发工具 | frontend-dev、fullstack-dev、android-native-dev、officecli、github 系列、drawio-reconstruction | 8 |
| 方法论/框架 | dbs-*（dontbesilent 商业工具箱 27 个）、supervisor-skills、ponytail 系列、write/humanizer 系列 | 大量 |

> 完整列表：`ls skills/`。带 `_skillhub_meta.json` 的是 SkillHub 商店来源，可忽略该元数据文件。

## 技能规范（新增/修改必读）

Hermes / OpenClaw 等 Agent **靠约定发现技能**，不满足就"送达但读不到"（delivered but unreadable），`teamai doctor` 会标红。三条铁律：

1. **目录名必须等于 `SKILL.md` frontmatter 的 `name`**。`skill_208842...`、`chatcut-*` 这类哈希/前缀目录名一律不行——改目录名跟随 name（name 是作者本意）。
2. **`description` 不允许为空**（`description: ""` 会被拒收）。拿 `description_zh` 填上。
3. **不要提交空壳目录**（目录在 git 里 tracked 但无文件，或 import 漏导的残留）。定期 `git ls-files -r skills/ | 检查`。

### 贡献流程

```
git checkout -b feat/xxx   # 从 main 开分支
# 改技能 / 新增技能（遵守上面三条）
git commit -m "..." && git push origin feat/xxx
# 开 PR（或直接合 main，仓库为私有且当前单维护者）
teamai pull --force         # 其他节点同步
```

## 兼容 Agent

| Agent | 技能落地 | 知识库 | Analytics | 会话钩子自动 pull |
|---|---|---|---|---|
| Hermes | ✅ | ✅ | ✅ | ✅ |
| OpenClaw | ✅ | ✅ | ✅ | ✅ |
| Copilot | ✅ | ✅ | ✅ | ✅ |
| Claude Code / Codex / Cursor 等 | ✅ | ✅ | ✅ | 视版本 |

（矩阵以 `teamai` CLI 官方 [README](https://github.com/Tencent/teamai-cli) 为准，CLI 持续更新中。）

## 当前接入节点

| 节点 | 位置 | 备注 |
|---|---|---|
| 药灵（Hermes Agent） | 腾讯云轻量 2C2G，118.89.90.232 | 主节点，会话钩子自动 pull |

## 维护记录

- **2026-10-12** 仓库初始化 + 导入 169 个本地技能
- **2026-10-12** 修复 47 个 name≠目录 的脏技能（48 目录改名、删 2 个哈希重复体 aihot v1.2.1/khazix、删 3 个空壳、ifind 去引号、ima-skills 补空 description）→ 163 个全部合规，`teamai doctor` 14 项全绿

## 参考

- 官方文档：[teamai-cli 使用指南](https://github.com/Tencent/teamai-cli)
- 介绍文章：[TeamAI：让 AI Agent 协作像管理代码一样管理技能（微信）](https://mp.weixin.qq.com/s/4DQdafdoQvCVHqyRWnzqjw)
