# 技能贡献规范（团队仓库 skills/ 读写准则）

## 命名铁律（违反即"delivered but unreadable"，doctor 标红）

1. 目录名必须等于该目录下 `SKILL.md` frontmatter 的 `name`。哈希目录（`skill_20xx...`）、前缀目录（`chatcut-*`）一律改目录名跟随语义 name。
2. `description` 不允许为空字符串——Agent 会拒收。缺描述时用 `description_zh` 或技能正文首段补。
3. 禁止提交空壳目录（tracked 但无文件、import 漏导残留）。合并前跑一遍：
   ```bash
   for d in skills/*/; do [ -f "$d/SKILL.md" ] || echo "BAD: $d"; done
   ```
4. 重名去留原则：正文一致的保留语义目录、删哈希目录；正文不同的按版本号/接口新旧留新（如 aihot v2.0.0 官方接口 > v1.2.1 旧域名）。

## 密钥红线

- 团队仓库**永不提交明文 API key**。密钥一律走 `teamai env add <KEY> --secret` 声明（值不入库），成员各自 `teamai env set <KEY>` 填自己的值。
- 需要密钥的技能，在技能文档里写"密钥来自 env 变量 XXX_KEY（团队 secrets.yaml 已声明）"，不写具体值。

## 流程

分支 → 本地 `teamai doctor` 全绿 → 合入 main → 其他节点 `teamai pull --force`（普通 pull 对无变化的 scope 会跳过，修脏技能后必须 force）。
