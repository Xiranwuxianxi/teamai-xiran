---
name: restricted-server-skill-installer
description: 网络受限、命令超时环境下第三方Hermes技能一键安装流程，解决GitHub访问慢、克隆失败、npx安装超时等问题
version: 1.0.0
author: Hermes Agent
tags: ["服务器运维", "技能安装", "网络优化", "超时处理"]
---
## 适用场景
- 服务器访问GitHub速度慢、延迟高
- 命令执行有60秒超时限制，直接clone/安装容易中断
- 网络不稳定，容易断开
## 标准化安装流程
### 前置配置（仅需执行一次）
```bash
# 优化Git网络参数
git config --global http.postBuffer 524288000
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999
# 创建技能目录
mkdir -p /root/.hermes/skills/
```
### 安装步骤
1. 进入技能目录：`cd /root/.hermes/skills/`
2. 后台执行浅克隆，避免前台超时：
```bash
# 标准GitHub地址
nohup git clone --depth=1 https://github.com/${AUTHOR}/${SKILL_NAME}.git > /tmp/skill_${SKILL_NAME}_install.log 2>&1 &
# 国内加速（可选）
nohup git clone --depth=1 https://mirror.ghproxy.com/https://github.com/${AUTHOR}/${SKILL_NAME}.git > /tmp/skill_${SKILL_NAME}_install.log 2>&1 &
```
3. 等待验证：
```bash
# 等待30秒
sleep 30
# 验证安装结果
ls -la ${SKILL_NAME}/ && echo "✅ 技能文件克隆成功"
skills_list | grep -i ${SKILL_NAME} && echo "✅ 技能已加载到系统"
```
### 失败降级方案
1. 手动下载zip包：`wget https://mirror.ghproxy.com/https://github.com/${AUTHOR}/${SKILL_NAME}/archive/refs/heads/main.zip -O ${SKILL_NAME}.zip`
2. 解压：`unzip -q ${SKILL_NAME}.zip && mv ${SKILL_NAME}-main ${SKILL_NAME} && rm ${SKILL_NAME}.zip`

## ClawHub CLI 安装方式

### 前置要求
- **Node.js ≥ 20**（clawhub@0.12+ 要求 Node≥20，v18会报 `SyntaxError: Invalid regular expression flags`）
- 如果当前Node<20，用nvm安装（GitHub超时则用gitee镜像）：
```bash
# gitee镜像安装nvm
git clone https://gitee.com/mirrors/nvm.git ~/.nvm
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install 20
# 每次使用前需source nvm：export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
```

### Slug格式避坑
- ClawHub网页URL格式：`https://clawhub.ai/用户名/技能名`
- CLI安装slug格式：**只用技能名**，不带用户名前缀
- ✅ 正确：`npx clawhub@latest install skill-vetter`
- ❌ 错误：`npx clawhub@latest install spclaudehome/skill-vetter`（报Invalid slug）
- ❌ 错误：`npx clawhub@latest install spclaudehome-skill-vetter`（报Skill not found）

### 安装命令
```bash
export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
npx clawhub@latest install <技能名> --no-input
```

### 安装路径注意
- npx clawhub默认安装到：`/root/.hermes/hermes-agent/skills/<技能名>/`
- Hermes原生技能目录：`/root/.hermes/skills/`
- 两处均会被 skills_list 扫描到，无需手动迁移

### 常见问题
1. **"Skill not found"**：该技能可能已从ClawHub下架。用 `npx clawhub@latest search <关键词>` 搜索替代品
2. **Rate limit (3000/hr)**：频繁请求会触发限流，遇到后等60秒再试
3. **Node v18报错**：升级到Node 20+（见上方nvm安装步骤）
4. **搜索无结果**：ClawHub搜索是向量搜索，换同义词/英文词试试
5. **npx skills add OOM**：低内存VPS（2核2G）执行 `npx skills add` 可能出现 JavaScript heap out-of-memory 或进入交互模式无法退出。改用手动git clone方式（见上方"失败降级方案"）
6. **npx skills add 报 "Failed to connect to 127.0.0.1 port 7890"**（2026-08实测）：即使已 unset http_proxy 等环境变量仍失败——因为 **git 全局配置里残留了 http.proxy**（`git config --global --get http.proxy` 可查）。npx skills 内部调用 git clone，走的是 git config 而非 shell 环境变量。解决方案（临时覆盖、不改全局配置）：
```bash
GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_0=http.proxy GIT_CONFIG_VALUE_0= GIT_CONFIG_KEY_1=https.proxy GIT_CONFIG_VALUE_1= \
npx -y skills add <author>/<repo> --yes
```
安装成功后技能落在 `./.agents/skills/<repo名>/`，并自动 symlink 到 Hermes Agent，可直接使用。

## 2026-08-30 新增实测坑

7. **terminal 会话 $HOME 被重映射**：本机 terminal 里 `$HOME=/root/.hermes/home`（不是 /root），`cp ... ~/.hermes/skills/` 会报 "No such file or directory"。**凡涉及技能/cron/配置路径，一律用 `/root/.hermes/` 绝对路径**，不要用 `~` 或 `$HOME`。

8. **codeload tarball 直连兜底（git clone 挂时首选）**：代理已失效环境下 git clone 常报 "Failure when receiving data from the peer"。直接用 GitHub codeload 拉压缩包，比 git 稳定：
```bash
curl -sL --noproxy '*' https://codeload.github.com/<owner>/<repo>/tar.gz/refs/heads/main -o repo.tar.gz
tar xzf repo.tar.gz
# 只需部分目录时可在解压时过滤，避免全量解压：
tar xzf repo.tar.gz <repo>-main/<目标子目录>
cp -r <repo>-main/<目标子目录>/<skill名> /root/.hermes/skills/[分类/]
```

9. **安装器 slug 与真实仓库不一致 + EXIT=143**：`hermes skills install "skills-sh:xxx/yyy"` 类命令被超时杀掉时输出 `EXIT=143`（SIGTERM，非代码错误）。且安装器里的仓库路径可能根本不存在（GitHub API 404）。排查法：
```bash
# 1. 验证仓库是否存在
curl -s --noproxy '*' "https://api.github.com/repos/<owner>/<repo>" | grep -E '"full_name"|"message"'
# 2. 404 时用递归 tree API 在整个候选仓库里定位 skill 真实位置（可能藏在编号子目录，如 20-ml-paper-writing/ml-paper-writing）
curl -s --noproxy '*' "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep -o '"path": "[^"]*<skill名>[^"]*"'
# 3. 找到后走 codeload tarball 手动安装，装完用 skill_view 验证 readiness_status=available
```
