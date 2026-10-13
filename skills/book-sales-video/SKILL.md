---
name: book-sales-video
description: 从书名或飞书多维表格中的成稿文案出发，结合微信读书资料与公开点评创作图书带货/书评短视频，并用豆包 TTS、Pexels、Codex 生图和本机 OpenChatCut 完成配音、配图、双语字幕、音效、动效、BGM、可编辑初稿与按需导出。用户提出“根据一本书做带货视频”“读取飞书文案制作图书视频”“写书评口播并自动剪成抖音视频”“仿参考样式做图书推荐短视频”时使用；仅查书、仅写普通书评或无关剪辑不触发。
---

# 图书带货视频创作

从书籍研究到本地可编辑初稿的一体化流程。只设置一次正常审核：先自动选择最佳角度并完成口播和语义分镜，用户确认后自动完成配音、画面、字幕、音效、动效、BGM、时间线和质检，不再逐项确认。

## 不可退让的完成线

- 书籍事实来自微信读书；公开点评只用于理解读者视角，不冒充原书内容。
- 用户指定从飞书多维表格读取文案时，目标记录中由用户确认的文案字段是权威口播源；除清理首尾空白和统一换行外保持原文，不擅自改写、拼接其他记录或用研究稿覆盖。
- 用户提供个人风格档案和禁用表达清单时，创作口播前必须读取；未提供时使用本 Skill 自带的口播参考，不猜测用户的私有路径或风格规则。
- 默认自动形成 2–3 个候选角度并评分，直接采用综合最优角度写成完整文案；不在前期让用户选角度。
- 唯一正常审核点位于完整口播与语义分镜之后。若用户打回，才展示候选角度供选择；选定后重写并直接进入制作，不新增第二次确认。
- 对已确认全文只运行一次 `scripts/doubao_tts.py`，最终只产生一个 `audio/narration.wav`。长稿允许脚本内部按句界请求并合并，但不能按镜头人工生成多份配音。
- 必须检查开头、结尾和所有句间静音：普通句间不超过 0.45 秒，段落/视觉转折不超过 0.70 秒；唯一允许的 0.80–1.20 秒无旁白区是有连续轮播音效覆盖的模板轮播。
- 最终配音的真实可听毫秒是全部画面、字幕、音效和转场的唯一时间依据；帧位用 OpenChatCut 当前项目的 timeline fps 换算。
- 开场动态视频固定通过 Pexels API 搜索 `book`，不根据书名或文案改关键词。
- 轮播使用 OpenChatCut 本地库 `library:sound:mechanical-clicking-loop`，每个有效峰值硬切一张不同封面；最后经短光溶进入主书揭示。
- 主书封弹出使用 OpenChatCut 本地库 `library:sound:cash-register-success`，视觉重音与音效锚点对齐。
- 正文每张图片必须有轻微呼吸/推近动效，相邻图片必须有转场；不能只把静态图片首尾拼接。
- 中文字幕与英文字幕均为白字、清晰黑描边；中文在上、英文在下，只保留一套可见字幕。
- 正文锁定“粗纸油画画外留白 v3”：油画叙事场景占画幅至少 70%（默认 70%–80%），横向一直铺到左右边缘；未上色粗纸只允许在上方、下方或上下两端，总占比 20%–30%。每次以 `assets/visual-style/approved-rough-paper-oil-v3.png` 为主锚点。
- 所有素材以独立可编辑项进入本机 OpenChatCut；不以本地预合成扁平视频冒充可编辑初稿。
- 本 Skill 禁用旧 ChatCut 云端 MCP、账号登录、云端项目链接和积分生成路线。本地 OpenChatCut 可用时不得回退云端。

## 首次使用与预检

每个新环境第一次触发本 Skill 时，先读取当前项目的 `AGENTS.md`，再运行只读预检；使用飞书路线时把用户提供的 Base URL 一并传入，实测机器人身份、Base 权限和文案字段，不以“已经配置过”代替验证：

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/check_environment.py" --json
python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/check_environment.py" \
  --json --base-url "<用户提供的飞书 Base URL>" \
  --lark-profile "<profile>" --script-field "<文案字段名>"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/openchatcut_mcp.py" status
```

读取预检输出中的 `checks`、`gates` 和 `actions`。缺少依赖、环境变量、应用、Skill、飞书 scope 或资源协作者权限时，先用中文说明“缺什么、影响哪个阶段、如何安装或授权、安装后怎样复验”，提供预检给出的准确命令或官方地址；涉及账号登录、App Secret、API Key 时引导用户在本机安全输入，禁止要求粘贴到对话。只允许安装用户当前路线真正需要的项目，安装或授权完成后重跑同一预检。对应 gate 未通过前不得进入该阶段，也不得伪装已经完成。

若任务使用飞书文案输入，还要确认 `larkBase.status` 为 `ready`。App Secret 只允许通过 `lark-cli config init --app-secret-stdin` 写入本机安全配置；禁止出现在对话、命令参数、工作目录或日志中。

### 缺失项安装与授权指引

预检发现缺失项时，只引导安装当前路线需要的能力，并在完成后复验：

- Python 依赖：`python3 -m pip install requests`
- FFmpeg：macOS 使用 `brew install ffmpeg`；其他系统使用对应包管理器，并确认 `ffmpeg`、`ffprobe` 可执行。
- 飞书官方 CLI：`npx @larksuite/cli@latest install`；随后运行 `lark-cli config init --new`，通过本机交互配置企业自建应用。
- 飞书 Base 权限：企业应用至少开通 `base:field:read`、`base:record:read`、`base:table:read`、`base:view:read`，并把机器人加入目标多维表格协作者。
- 微信读书能力：`npx skills add Tencent/WeChatReading -g`，再按该 Skill 的说明安全配置 `WEREAD_API_KEY`。
- Pexels：从 `https://www.pexels.com/api/` 申请只供本机使用的 API Key。
- 豆包 TTS：在火山引擎控制台取得 API Key、resource ID 和 speaker，保存到安全环境或系统钥匙串。
- OpenChatCut：从 `https://github.com/0xsline/OpenChatCut/releases` 安装桌面版；macOS 放入 `/Applications`。首次启动后打开目标工程，再复验本地 MCP 工具。

涉及网页审批、账号登录或密钥录入时，给出最小权限和操作入口后等待用户完成；不要代替用户公开凭据，也不要要求把 Secret 或 API Key 发到对话中。

OpenChatCut 状态命令会在需要时启动 `/Applications/OpenChatCut.app`，自动发现随机 localhost 端口，并验证 `/api/external-mcp/mcp`。不得把某次端口写死到 Skill 或任务状态。

**重启后的工程连接检查：** OpenChatCut 重启时默认停在“我的工程”列表。此状态只会暴露项目管理工具，`read_timeline`、`edit_item`、`edit_track` 等完整编辑工具不会注册，并可能误报“工程未连接”。对已有项目，必须先核对任务状态中保存的 `projectId` 与工程名，再让用户或 Computer Use 明确打开该工程；随后重新运行 `list-tools` 和只读 `read_project`，确认返回的 `projectId`、`timelineId` 与任务状态完全一致，才允许写入。连接失败、点击位置不确定或当前工程 ID 不一致时立即停止，不点击“新建工程”，不调用 `create_project`，不创建替代项目。

按阶段处理缺失项：

| 阶段 | 必需 | 缺失时处理 |
|---|---|---|
| 飞书文案 | `lark-cli`、可用的默认或命名 profile、机器人为表格协作者、Base 只读权限 | 停止读取并报告缺失的 scope 或资源权限；不改用浏览器复制、不猜测文案 |
| 研究 | `weread-skills`、`WEREAD_API_KEY` | 停止事实研究，不用未知网页代替 |
| 配音 | `requests`、豆包密钥、资源 ID、音色 | 停止配音，不回退编辑器音色 |
| 开场 | `PEXELS_API_KEY` | 文案可继续，但不得伪装已取得视频 |
| 配图 | Codex `image_gen` | 保存分镜与提示词，明确缺口 |
| 本地初稿 | OpenChatCut Desktop、本地 MCP 必需工具、可导入素材 | 修复本地应用或导入后再装配，不回退云端 |

密钥只从安全环境或钥匙串读取，不写入工作目录或日志。豆包变量为 `DOUBAO_API_KEY`、`DOUBAO_TTS_RESOURCE_ID`、`DOUBAO_TTS_SPEAKER`；Pexels 为 `PEXELS_API_KEY`；微信读书为 `WEREAD_API_KEY`。

## 工作目录

使用项目 `AGENTS.md` 的 `work/` 约定，单次任务目录至少包含：

```text
research.md              script.md
storyboard.json          shot-plan.json
visual-style.json        voice-timeline.json
timeline-plan.json       subtitle-pairs.json
asset-manifest.json      quality_check.json
review_report.md         visuals/
audio/
```

状态文件只保存当前有效状态，并共享同一 `stateRevision`、`projectId`、`timelineId` 和 timeline fps。

## 飞书多维表格文案输入

当用户提供飞书 Base 链接、记录链接，或明确要求“读取飞书文案制作”时，先读取文案，再进入书籍事实核对和分镜。公开版不内置任何用户表格地址、应用 ID、字段 ID 或记录 ID；首次使用时由用户提供 Base URL、profile 名称和文案字段名：

```text
Base URL: <用户提供>
profile: <用户本机的默认配置或命名 profile>
文案字段: <用户提供，示例：文案仿写.输出结果>
```

读取规则：

1. 先用 `base +url-resolve` 解析链接，不从 URL 字符串猜测资源类型；确认 `base_token`、`table_id` 和 `view_id`。
2. 用 bot 身份执行 `base +field-list`，动态核对字段。界面显示名、口语别名和真实字段名可能不同，必须以实时字段列表返回的名称或字段 ID 为准，不能把某个用户的字段 ID 写死到 Skill。
3. 默认只投影 `视频标题`、`书名`、`作者` 和用户指定的文案字段，并限定到链接指定的 view；字段不存在时先让用户确认映射，不读取无关字段或附件。
4. 记录选择优先级固定为：用户提供的 record ID/记录链接 → `视频标题` 精确匹配 → `书名` 精确匹配。匹配前只允许去除书名号和首尾空白，不做模糊包含匹配。
5. 如果精确匹配仍有多条记录，列出每条的 `视频标题`、`书名`、`作者` 和 record ID，让用户选择；禁止默认取第一条、最长文案或最新文案。
6. 目标字段为空时停止；不得擅自回退到其他字段或其他记录。读取成功后把原文写入 `script.md`，并在 `research.md` 记录脱敏后的数据源说明、table/view/record ID、字段名和读取时间，不记录完整私有 URL、应用密钥或访问令牌。

推荐只读调用：

```bash
lark-cli --profile "<profile>" base +url-resolve --url "<Base URL>" --as bot
lark-cli --profile "<profile>" base +field-list \
  --base-token "<base_token>" --table-id "<table_id>" --as bot
lark-cli --profile "<profile>" base +record-list \
  --base-token "<base_token>" --table-id "<table_id>" --view-id "<view_id>" \
  --field-id "视频标题" --field-id "书名" --field-id "作者" \
  --field-id "<文案字段名>" --format json --as bot
```

若报 `missing_scope`，只申请 `base:field:read`、`base:record:read`、`base:table:read`、`base:view:read`；若报资源无权访问，确认机器人已作为协作者加入当前 Base。bot 身份禁止执行用户 OAuth 登录。

## 阶段一：确认书籍与研究

1. 加载 `weread-skills`，搜索并定位书籍；飞书输入路线优先使用已选记录的 `书名`，只有重名或版本歧义会影响内容时才请用户选择。
2. 获取书名、作者、简介、分类、评分、封面、目录和 `bookId`，事实与解释分开写入 `research.md`。
3. 分别收集推荐、最新和全部点评，目标 20–40 条有效样本；去重并过滤纯表情、无关或极短点评，数量不足就使用现有全部。
4. 提炼痛点、具体处境、反直觉认识、情绪张力、争议和读后变化。
5. 形成 2–3 个候选角度，按受众代入、与书相关性、证据覆盖、视觉化潜力、自然购买过渡五项评分。选择综合最佳角度并记录理由，不先询问用户。

飞书输入路线中，步骤 3–5 只用于事实核验和视觉理解，不重写或替换已读取文案，也不再生成候选文案角度。

此阶段读取 [references/copywriting-and-storyboard.md](references/copywriting-and-storyboard.md)。

## 阶段二：文案、分镜与唯一审核

严格读取 [references/reference-copy-style.md](references/reference-copy-style.md) 和 [references/copywriting-and-storyboard.md](references/copywriting-and-storyboard.md)。用户另外提供个人风格档案或禁用表达清单时也要读取；已明确提供但不可读时停止创作并报告准确路径，用户未提供时不构成阻塞。

默认结构：

1. 固定开场“今天分享的是”。
2. 无正文口播的快速封面轮播。
3. 最后卡点揭示并报出《书名》。
4. 从观众正在经历的具体处境进入正文，给出书中可核验的认识、情境或方法。
5. 回到观众处境，说明适合谁和能帮助看见什么，避免硬促销和抽象升华。

上述默认结构只约束新创作文案。飞书输入路线直接使用已选记录的全文：保留段落、语序和措辞，只基于该全文生成语义分镜、双语字幕草稿和预计画面数量。若文案中的书名或作者与微信读书核验结果冲突，停止并明确指出差异，不静默修正原文。

完成 `script.md`、`storyboard.json` 和 `draft` 状态的 `subtitle-pairs.json`。分镜按语义、动作、场景或情绪变化切，不按句号平均切图。把主角度、评分摘要、完整口播、分镜摘要、预计图片数量和后续自动生成范围一次性交给用户审核。

用户确认后即授权该视频的完整本地制作。若用户不满意，展示候选角度并按其选择重写；重写完成后直接制作，不再增加确认关卡。

## 阶段三：一次生成完整配音

1. 新任务且状态中没有项目时，才用本地桥接调用一次 `create_project`，明确指定 1080×1920、30fps，并保存真实项目与时间线 ID；继续已有任务时必须重连保存的同一工程，禁止调用 `create_project`。禁止沿用已确认失败的项目，也禁止在后续阶段再次创建替代项目。
2. 将确认稿保存为 `audio/narration.txt`，只运行一次：

   ```bash
   python3 "${CODEX_HOME:-$HOME/.codex}/skills/book-sales-video/scripts/doubao_tts.py" \
     --text-file audio/narration.txt --output audio/narration.wav \
     --report audio/narration.wav.json
   ```

3. 用 ffmpeg/ffprobe 与试听证据检查首尾、第一二句边界、最长句间停顿、段落边界和结尾。异常时先修剪或重跑这一条完整配音，未通过不得生图或装配。
4. 通过 OpenChatCut 本地上传会话导入唯一 WAV 到 A1。不得调用编辑器 TTS，也不得重新拆成多条旁白资产。
5. 优先读取同一次 `doubao_tts.py` 生成的句段时间账本，从同一 `audioAssetId` 派生语义 `voiceUnitId`，生成 `voice-timeline.json`。该账本记录每段修剪后的真实 PCM 时长及拼接静音，作为可复核对齐证据；不依赖 OpenChatCut 转录。仅在账本缺失时才尝试已获授权的 ASR；不能伪造词时间。

具体 MCP 调用、导入和轨道结构读取 [references/openchatcut-build.md](references/openchatcut-build.md)。

## 阶段四：按配音生成全部视觉

### 开场与封面

- 运行 `scripts/search_pexels_videos.py --page 1 --per-page 20`，固定 `book`、竖屏、中等尺寸；实际查看候选后选择，记录 Pexels 页面、创作者、文件和归属。
- 开场中央显示“今天分享的是 / Today, I'd like to share”，底部不重复显示该句字幕。
- 轮播封面排除当前主讲书，按内容指纹去重。先读取机械音效真实峰值，再决定封面数量和切点，不预设 6 张。
- 当前书封使用微信读书真实封面，作为 **普通 image 项** 放在 V2（V1 揭示背景的正上方）；AI 图只做 V1 揭示背景，不让模型重画书名。禁止为单张主书封创建全画布 Motion Graphic：它会引入局部画布与时间线的二次缩放，造成封面偏小、偏移或在时间线上不可直观选中。
- 主书封弹出时，V3 同步出现 `《书名》` 与 `作者 / 著`；从揭示开始持续到视频结束，正文换图时文字内容、位置和样式保持不变。揭示段若口播仅重复书名作者，顶部常驻标题可替代底部重复字幕，避免同屏出现两套相同信息。

### 正文图

1. 读取 [references/body-visual-style.md](references/body-visual-style.md) 与 [references/shot-planning.md](references/shot-planning.md)，先完整生成 `shot-plan.json`。
2. 每张定义叙事功能、主体动作、景别、视角、构图、上下粗纸比例、统一字幕框和与前一张的视觉反差。相邻图片不得同景别、同视角；六张以上至少四种景别和四种视角。
3. 运行 `scripts/validate_shot_plan.py shot-plan.json`，通过后才调用 `image_gen`。
4. 每次生图都使用已批准主锚点，明确场景至少 70%、左右满幅、只在上下留粗纸、图中无字幕/书名/logo/水印。
5. 把全部缩略图并排检查；只重生成偏离镜头规划或风格的图片。

## 阶段五：本地 OpenChatCut 自动装配

执行前读取 [references/openchatcut-build.md](references/openchatcut-build.md)、[references/editing-effects-and-rhythm.md](references/editing-effects-and-rhythm.md) 和 [references/bilingual-subtitles.md](references/bilingual-subtitles.md)。

- 所有 MCP 调用通过 `scripts/openchatcut_mcp.py`，每次动态发现本机端口；工具参数以当前 `list-tools` schema 为准。
- 轨道角色：V1 开场/轮播/揭示背景/正文；V2 仅为主书真实封面这一条普通图片项；V3 为书名、作者与字幕等可编辑文字覆盖层；A1 完整配音；A2 BGM；A3 机械轮播音效；A4 揭示音效。
- 主书封先以 `type:"image"` 放到 V2，再用实例关键帧定位；不得以扁平预合成或全画布 MG 替代。最终画面以封面占画幅约 52%–60% 宽为起点、水平居中、书名下方留一段正常空白、左右均留白为验收，而不是只相信 CSS 或资产的自然尺寸。以当前已验证的竖屏封面为基线：`x=0`、`y≈8`、`scale≈0.56`，但每本书都必须以实际渲染画面微调。
- 主书封只使用一次简洁出场：约 0.23 秒内 `opacity 0→1`、`scale 0.42→0.60→最终值`、`y 16→最终值`，之后保持静止；禁止持续呼吸、横移、旋转或额外复杂动效。收银成功音的重音落在该入场开始处。
- 轮播内部硬切；最后一张到揭示使用约 0.10 秒光溶；揭示到正文及正文相邻画面使用约 0.20 秒交叉叠化。
- 每张正文图添加且只添加一个轻微呼吸/推近动效。默认使用无位移的、比常规慢约 10% 的单次呼吸：`x=0`、`y=0` 固定，`scale` 从 `1.02`（起点）缓慢到 `1.085`（片段 55% 处），再柔和回落到 `1.035`（片段末尾）。不得在同一张图中重复第二次呼吸，也不得为赶在片段末尾归零而突然缩小。优先使用本地已验证的 `builtin:zoom` 慢推近或等价关键帧；必须检查放大后主体和字幕安全区没有被裁坏。
- 机械轮播音效使用 `library:sound:mechanical-clicking-loop` 一段连续资产；揭示音效使用 `library:sound:cash-register-success` 一次。不得重新生成替代音效。
- BGM 从第 0 帧开始，优先使用 OpenChatCut 本地/可追溯音乐；人声为主，BGM 降音量或 duck。没有合适音乐时，只有唯一审核已披露并授权才生成一条，不批量变体。
- 中文与英文逐卡语义对应、时间一致。字幕必须先按句号、问号、叹号、分号和逗号等标点确定句子与分句边界，再按完整意群细分；禁止先按固定字数切块，也禁止把下一分句的开头词塞进上一卡。中文每卡最多 11 个有效字符只是切分后的长度上限，不能推翻语义边界。默认中文 76px/800，英文 42px/600，均白色填充、黑色描边。原生字幕无法精确实现时，整段使用可编辑双语 Motion Graphic，不能留下两套可见字幕。
- 复杂批量编辑先 `validateOnly`，再原子提交；请求超时先读回项目判断是否已写入，禁止盲目重复。

## 阶段六：质检与交付

先结构、后画面、再声音。`quality_check.json` 至少包含并通过：

`bookFacts`、`voiceContinuity`、`timelineStructure`、`carouselRhythm`、`bookReveal`、`bodyMotion`、`transitions`、`subtitles`、`bgmMix`、`visualStyle`、`frameReview`。

必须逐项验证：

- 开场、轮播、揭示和正文连续，无黑帧、空轨、错误重叠或截断。
- 机械音效一峰一图；最后卡点准确进入主书，收银成功音与书封弹出同步且只出现一次。
- 每张正文图恰好一个呼吸/推近动效；全部规定边界有正确转场。
- 配音停顿满足阈值，画面、字幕、转场、BGM 和音效已按修剪后的同一时间表重排。
- 中英文白字黑描边、语义一致、单套可见、不溢出、不遮挡、不跨越所属 `voiceUnitId`。
- 逐句回读字幕卡，确认每个句号、问号、叹号、分号和逗号后的新意群都从新卡开始；抽查不得出现固定字数硬切、上一卡携带下一分句开头或揭示段重复显示书名作者。
- 从主书封稳定帧到最后一帧，V3 的书名作者必须持续可见且内容、位置、样式不变；分别检查揭示稳定帧、正文首帧、中段和末帧。
- BGM 从第 0 帧开始且不盖人声。
- 正文图达到 70% 以上画面、左右满幅、仅上下留粗纸；实际镜头符合 `shot-plan.json`。
- 使用 OpenChatCut `read_project`/`read_timeline` 读回结构，并检查开场、轮播中点、主书揭示的入场/中段/稳定三帧、每个正文边界和最后一帧。主书封验收同时要求：V2 存在一条 `kind:"image"` 的可见片段、片段可直接在时间线上选中，且渲染画面中封面居中、不裁边、不压住书名作者。

任何结构性修改都会让旧检查变为 `stale`。修复后必须重新读项目、抽查画面和试听。运行：

```bash
python3 scripts/validate_subtitle_cards.py subtitle-pairs.json --voice-timeline voice-timeline.json --strict
python3 scripts/validate_delivery_state.py .
```

全部通过后交付：本机 OpenChatCut 中可编辑项目、文案、字幕对照、分镜、状态文件和 `review_report.md`。默认停在可编辑初稿供用户检查；用户明确要求或确认最终版后才调用本地导出，并验证导出历史与实际文件。

## 失败处理

- OpenChatCut 未安装：报告 `/Applications/OpenChatCut.app` 缺失并停止本地装配。
- 应用未运行：桥接脚本自动启动并有限等待；仍不可达时报告本地进程和端口发现结果。
- MCP 工具缺失或 schema 变化：先 `list-tools`，按当前 schema 调整调用；不回退旧云端接口。
- 本地素材上传失败：读取上传会话和资产列表判断是否已经导入；未确认前不重复上传。
- 豆包、Pexels、微信读书或图像生成失败：保留已完成状态和准确缺口，不用虚构资产顶替。
- 音效、动效、转场、双语字幕样式、BGM 或关键帧检查缺一项，状态必须为 `blocked-not-deliverable`，不得称为“可审核初稿”。

## 资源路由

- 参考节奏：[references/reference-style.md](references/reference-style.md)
- 口播语言：[references/reference-copy-style.md](references/reference-copy-style.md)
- 研究、角度、文案和分镜：[references/copywriting-and-storyboard.md](references/copywriting-and-storyboard.md)
- 正文视觉：[references/body-visual-style.md](references/body-visual-style.md)
- 镜头规划：[references/shot-planning.md](references/shot-planning.md)
- 双语字幕：[references/bilingual-subtitles.md](references/bilingual-subtitles.md)
- 动效与节奏：[references/editing-effects-and-rhythm.md](references/editing-effects-and-rhythm.md)
- 本地项目、导入、时间线和导出：[references/openchatcut-build.md](references/openchatcut-build.md)
- 本地 MCP：`scripts/openchatcut_mcp.py`
- 环境检查：`scripts/check_environment.py`
- 完整配音：`scripts/doubao_tts.py`
- Pexels 搜索：`scripts/search_pexels_videos.py`
- 校验：`scripts/validate_shot_plan.py`、`scripts/validate_subtitle_cards.py`、`scripts/validate_delivery_state.py`
