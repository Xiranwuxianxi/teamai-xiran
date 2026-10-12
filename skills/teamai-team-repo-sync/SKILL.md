---
name: teamai-team-repo-sync
description: "Use when 接入 TeamAI 团队技能仓或修 Hermes 读不到的脏技能：init、去重、doctor 验收。"
---

# TeamAI 团队技能仓 ↔ Hermes 同步与修复 (TeamAI Team Skill Repo ↔ Hermes Sync & Repair)

团队仓 = Git 管理 Skill/规范/MCP 配置的协作仓库（腾讯云 TeamAI）。本机已接入 `Xiranwuxianxi/teamai-xiran`（私有仓，user scope，技能交付到 /root/.hermes/skills）。环境细节见 `references/env-notes.md`，通用用法看官方 `teamai` 技能（团队仓同步，勿改）。

## 接入新机器/新 Agent (Onboarding a New Machine/Agent)
1. `npm install -g teamai-cli`（Node 22 直接装，v0.27.0）
2. `export GITHUB_TOKEN=***`（token 来源见下）+ `teamai init <repo-url> --scope user`
   - 交互确认一律加 `TEAMAI_NONINTERACTIVE=1`，否则 pull/init 停在 confirm 会被安全扫描 block 整条命令
3. 本地克隆在 `/root/.teamai/team-repo`；git 提交前需**仓库级**身份 `git config user.name/user.email`（服务器无全局身份，不配就 commit 失败）
4. PAT 存 `/root/.teamai/ghp-token`（chmod 600），命令里用 `$(cat ...)` 引用。**PAT 明文不得出现在命令文本里**（Tirith 安全扫描直接 block）；`/root/.git-credentials` 是受保护文件，write_file 会拒

## Hermes 技能发现铁律（"delivered but unreadable" 两大根因）(Hermes Skill Discovery Iron Rules)
1. **frontmatter `name` 必须等于目录名**。典型脏数据：`skill_<哈希ID>` 目录（SkillHub 导入产物）、`chatcut-` 等前缀目录、name 值带引号。修法：**git mv 目录跟随 name**（语义名是作者本意，git mv 保留历史）
2. **`description` 不能为空**（`description: ""` 会被 Hermes 拒收）。用同文件现成的 `description_zh` 文案补

动手前先跑 `scripts/verify_hermes_skill_names.py` 出三类问题清单（mismatch / 缺 SKILL.md / 空 description），再按清单修。

## 重复技能去重判据 (Deduplication Criteria for Duplicate Skills)
两个目录同 name 并存：
- 正文一致（`diff -rq` 只差 `_skillhub_meta.json` 等 meta）→ 删哈希版，留语义版
- 正文不同 → 比版本新旧留新的（实例：aihot 留 v2.0.0 官方 aihot.news 接口版，删 v1.2.1 旧域名版）
- 批量 import 漏导会留**空壳目录**且 git 不跟踪：先 `git ls-files skills/<dir>` 确认为空才 rmdir

## 同步与验收 (Sync & Acceptance)
- 普通 `teamai pull` 对"团队仓没变"的 scope 直接跳过 → 修完脏技能必须 `teamai pull --force` 重新分发
- 验收：`teamai doctor` 全绿（重点看 "Skills delivered to hermes"）+ verify 脚本 0 问题
- init 已注入 hermes/copilot/openclaw 会话钩子：每次新会话启动自动 pull 团队仓最新技能，无需手动

## 脚本与参考 (Scripts & References)
- `scripts/verify_hermes_skill_names.py`：扫描团队仓 skills/，输出 mismatch / 缺 SKILL.md / 空 description 三类问题 JSON，退出码 0=全干净
- `references/env-notes.md`：本机接入记录（CLI 版本、仓库路径、token 位置、2026-10-12 首发接入的修复清单与 commit）
