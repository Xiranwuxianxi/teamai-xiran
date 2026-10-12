# TeamAI 接入环境记录（2026-10-12 首发接入）(TeamAI Onboarding Environment Record)

- teamai-cli v0.27.0，`/root/.hermes/node/bin/teamai`（npm -g，Node 22）
- 团队仓：`Xiranwuxianxi/teamai-xiran`（私有，main），本地克隆 `/root/.teamai/team-repo`
- scope=user → 技能交付 `/root/.hermes/skills`；钩子注入 hermes/copilot/openclaw 三端
- token：`/root/.teamai/ghp-token`（chmod 600）；命令引用 `$(cat ...)`，PAT 明文不入命令文本；`/root/.git-credentials` 受保护写不了
- 团队仓 git 身份（仓库级）：user.name=Qixing-Hermes / user.email=agent@hermes.local
- 首发 165 技能，修复后 163 全合规：
  - 48 个目录 git mv 改名跟随 name（skill_哈希ID / chatcut-前缀 / __skillhub 后缀 / 引号）
  - 删 2 个重名哈希版（aihot v1.2.1 旧域名、khazix 正文重复体），留语义/新版
  - 删 3 个 import 漏导空壳目录（guizang-ppt-skill / gzh-design-skill / humanizer-zh，git 不跟踪）
  - ifind-finance-data name 去引号；ima-skills 空 description 用 description_zh 补齐
- commits（已推 main）：`4a108dc` 对齐改名 + `d547d5a` ima-skills description
- 验收：`teamai doctor` 14 项全绿；修后必须 `teamai pull --force`（普通 pull 跳过未变 scope）
