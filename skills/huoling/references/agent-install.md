# 当用户给出 GitHub 链接时的安装协议

**本仓库**: https://github.com/Xiranwuxianxi/huolingskill

用户发来上述链接（或要求「安装火灵」「install huoling from github」）时，Agent **必须**尝试自动安装，不要只告诉用户手动步骤。

## 执行顺序

1. **读取** [INSTALL.md](https://raw.githubusercontent.com/Xiranwuxianxi/huolingskill/main/INSTALL.md) 或本地 `INSTALL.md`

2. **优先执行**：
   ```bash
   npx skills add Xiranwuxianxi/huolingskill --skill huoling -y --all
   ```

3. **回退 A**：
   ```bash
   git clone --depth 1 https://github.com/Xiranwuxianxi/huolingskill.git /tmp/huolingskill && cd /tmp/huolingskill && ./install.sh
   ```

4. **回退 B**：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/Xiranwuxianxi/huolingskill/main/install-from-url.sh | bash
   ```

5. **验证** — 确认至少一项存在：
   - `.cursor/skills/huoling/SKILL.md`
   - `.claude/skills/huoling/SKILL.md`
   - `.agents/skills/huoling/SKILL.md`

6. **汇报** — 告知安装方式、路径、是否成功

## URL 解析

| 输入 | 安装命令 |
|------|----------|
| `https://github.com/Xiranwuxianxi/huolingskill` | `npx skills add Xiranwuxianxi/huolingskill --skill huoling -y --all` |
| `Xiranwuxianxi/huolingskill` | 同上 |

## 禁止

- 仅回复「请手动复制 skills 文件夹」而不执行安装命令
- 未验证就声称已安装
- 安装失败时不尝试回退方案
