# 团队成员

成员注册由 `teamai init` 自动登记（CLI 侧 `teamai members list` 可查当前团队）。本文件是给人看的节点清单，新节点加入后在此登记一行。

| 成员 | GitHub 账号 | 节点 | 角色 | 加入日期 |
|---|---|---|---|---|
| 胡启行 | Xiranwuxianxi | 腾讯云轻量 2C2G（118.89.90.232） | 维护者 | 2026-10-12 |
| 药灵（Hermes Agent） | 同机运行 | 同上 | 执行节点 | 2026-10-12 |

## 新节点接入三步

```bash
npm install -g teamai-cli
export GITHUB_TOKEN=***
teamai init https://github.com/Xiranwuxianxi/teamai-xiran --scope user
# 有 secrets 的节点再执行：
teamai env set IFIND_KEY          # 按提示逐个填
```

接入后在本表加一行。
