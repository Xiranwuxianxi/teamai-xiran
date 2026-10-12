---
name: huashu-art-motion-ops
description: 用 huashu-art-motion 在本服务器生产口播解说视频时用。安装修复、spec渲染、配音合成全流程。
---

# huashu-art-motion 解说视频生产管线

引擎本体在 `/root/.hermes/skills/huashu-art-motion`（用户指定的外部 skill，本体不要改；本 skill 是它的运维与使用手册）。

## 🎨 创意铁律：每条视频必须不一样（主人 2026-10-11 严正批评后定为第一铁律）
主人原话："不要老用同种款式来做视频，观众会看烦的，每个视频肯定要有不一样，不能只是抄袭前面的"、"不要局限在既定表格里，每次都要有新想法新思路"、"充分发挥独立思考能力，不要每一步都让我帮你做判断"。
1. **开工前先做创意决策**：根据内容+受众选叙事体、视觉语法、节奏、色彩、音乐情绪，禁止默认复制上一条的套路。同一种语法/版式不得连续出现在两条视频里。
2. **已验证的叙事体**（每次选不同的，也可以发明新的）：技术解说体（太空兔片）/ 男女双声音对话体（dual-voice-demo）/ 编辑墨纸体「墨纸×朱文」（muse-v5 定版：纸感米白底 #F5F1E8 + 墨黑 #1A1714 + 朱红印泥 #C8402F；非对称网格 + 幽灵大字底纹 + -8° 旋转朱印 + 侧边竖排字 + 结尾黑底反转贴朱印；模板 /root/sbr-work/muse-v5/build_scenes_v5.py 直接抄改，2026-10-12 主人验收通过"感觉这个还可以"）/ 情感故事体《声音情书》（voice-love-letter：痛点→转折→情感时刻→升华，温暖治愈系，y4_storytime 主导）/ 测评对比体 / 时间线体 / 清单体。
3. **语法、色彩、节奏、音乐都要轮换**：8 种 grammar 自由组合（一条片里混 3-5 种）；色彩不限于科技蓝；节奏按内容走（故事片慢、干货片快）；音乐情绪跟叙事（痛点段疑惑/紧张，高潮才高能）。
4. **自主判断**：选题、风格、结构自己定并说明理由，只在拿不准的口味问题上问主人；不要把方案甩回给主人选。但创意决策（选了什么风格、为什么）要在交付时汇报。
5. 听众画像（抖音 97% 男性、18-23 近半）是创意约束之一：想扩女性受众用双声音对话体+场景化选题（"给女朋友做 XX"），但每条的切入角度都要新。

## 安装/修复（2026-10-07 实测，腾讯云 2核2G OpenCloudOS）
1. GitHub 直连超时 → 用 `https://gh-proxy.com/https://codeload.github.com/<org>/<repo>/tar.gz/refs/heads/main` 拉 tarball（ghfast.top 等镜像返回 14 字节 "Invalid input"，不可用）。
2. Playwright chromium 国外源下载卡死 → 软链系统 Chrome，**两个目录都要建**（新版 playwright 默认走 headless shell）：
   ```sh
   # 先查期望路径：uv run --with playwright python -c "from playwright.sync_api import sync_playwright as s; p=s().start(); print(p.chromium.executable_path)"
   mkdir -p /root/.cache/ms-playwright/chromium-<rev>/chrome-linux64
   ln -sf /usr/bin/google-chrome /root/.cache/ms-playwright/chromium-<rev>/chrome-linux64/chrome
   mkdir -p /root/.cache/ms-playwright/chromium_headless_shell-<rev>/chrome-headless-shell-linux64
   ln -sf /usr/bin/google-chrome /root/.cache/ms-playwright/chromium_headless_shell-<rev>/chrome-headless-shell-linux64/chrome-headless-shell
   ```
3. **系统 ffmpeg 7.0.2 没有 libx264** → render.py 报 `Unknown encoder 'libx264'` + BrokenPipe。修复：
   ```sh
   pip install imageio-ffmpeg   # 自带静态 ffmpeg（johnvansickle 版，含 libx264 + libass）
   mkdir -p /tmp/ffbin && ln -sf $(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())") /tmp/ffbin/ffmpeg
   export PATH=/tmp/ffbin:$PATH   # 渲染和后续合成都要在这个 PATH 下跑
   ```

## 成片流程（口播解说片，已验证）
1. 分段写口播稿 → 逐段 TTS/克隆配音 → ffprobe 拿每段精确时长。
2. 按 `references/09-视频动画语法.md` 的片段契约写每段 spec（grammar 8 选 1，duration=音频时长，cue 的 at 按语速估算）。spec 加 `"safe":{"bottom":180}` 给字幕带留位。**grammar id 必须与 `scripts/engine/clips/*.js` 文件名逐一核对再写 spec**：真实 id 是 t1_3b1b / t2_keynote_ui / t3_finance_chart / y1_kurzgesagt / y2_vox / y3_whiteboard / y4_storytime / y5_kinetic_type。语法文档示例里的 `t3_chart` 不是真名——**写错 grammar 不报错、什么都不画**（2026-10-10 踩过，seg4 差点交白片）。核对命令：`ls scripts/engine/clips/`。
3. **先抽帧再全渲**：`render.py --spec x.json --stills 1,5 --out dir`，用 PIL 统计 RGB 均值/方差做廉价 sanity check（全黑 var≈0 或纯色才可疑；3b1b 黑底 var 300-600 是正常的）。确认后再渲整段。
4. 渲染日志里 `❌ 页面报错 1 条` 若只是 `Canvas2D: willReadFrequently` 性能提示 → 可忽略，照常出片。
5. 合成：视频 concat（-c copy）→ 音频各自后处理后 concat → subtitles 滤镜烧字幕（Noto Sans CJK SC）→ `-movflags +faststart` 出片。
6. 细节见引擎 references/ 下的语法卡；cue 时间对齐口播词（白板语法开写比说话晚约 0.5s）。**文字/图片与音频严格同步用词级时间戳**（主人 2026-10-11 报过"文字图片不同步"）：faster-whisper `transcribe(..., word_timestamps=True)` 拿词起止时间 → cue 的 at 直接取对应词的 start，禁止纯按字数比例估算（估算会在长句/停顿处漂移）；合成后抽 2-3 个点对比"文字出现时刻 vs 该词发音时刻"复核。

## 配音轨
TTS 用 edge-tts XiaoxiaoNeural；**真人克隆首选小米 MiMo voiceclone**（API 稳定无限额，见 references/mimo-tts-voiceclone.md）；F5-TTS/CosyVoice2 降为备胎（配额坑见 voice-clone-hf-space-f5tts 技能）。音画对齐：atempo 微调（±6% 内）优先，别重渲视频。
**克隆配音杂音治理（2026-10-11 主人报"有杂音/别的声音"，待修方案）**：① F5-TTS 底噪用 ffmpeg `afftdn`（或 `anlmdn`）降噪过一遍；② 逐段生成再拼接的段间咔哒/气息突变，在 concat 时给接缝加 50ms 交叉淡化；③ 若杂音是呼吸/语气音被克隆进来，换更干净的参考切片重新生成。修完回听+抽段频谱对比再交付。
**整片 6 段以上连跑配音用 `scripts/batch_clone.py`**（读工程目录 script.json 的 segs，F5 token→匿名→CosyVoice 三级故障切换 + 断点续跑；2026-10-10 太空兔片 6 段一次全过）。喂稿规范（数字中文、谐音锚定）见自检清单第 2 条。

## 交付
成品 cp 到 /root/public/ 发公网链接 + MEDIA: 附件（微信/企微惯例）。

## ⚠️ 出厂自检清单（2026-10-09 主人五轮返工后的铁律，交付前必须逐项过，禁止"做完就发"）

**融合 liyupi/ai-promo-video-maker 的加强项（2026-10-10 吸收，全量细则见 references/校验清单.md 与 references/踩坑记录.md，开工前先读一遍）：**
- 官网截图一律用 `scripts/web_shot.py`（networkidle+懒加载滚动+2x+碎图自检），禁止裸 `chrome --screenshot`（本次碎图事故根因）
- 渲染前闸门：spec 引用的图片逐个确认存在 + 源图宽 ≥ 显示宽×2（小图放大必糊）；缺文件/低清图此时就拦，不进渲染
- 配音校验升级为「关键词清单」：品牌名/型号/关键数字逐个在 whisper 回听文本里命中才算过（整句相似度会放过品牌名读错）
- 故事校验：外行复述测试——只读口播稿能讲清来龙去脉；第一句旁白+第一屏大字单独成立
- 节奏底线：开场 3 秒内出痛点/亮点；任何时刻往后 2 秒内必须有新信息；快切 ≥0.65s、重点展示 ≥1.3s
- （可选升级）BGM：Mixkit 免费可商用曲库选曲 + ducking（人声出现时音乐 -9dB），痛点段不配高能曲。**下载后必须 ffprobe 验真**：凭记忆猜的 Mixkit 直链会静默下到 111 字节错误页（2026-10-11 实测），文件 <10KB 或 ffprobe 读不出 duration 就是废文件，去 mixkit.co 页面拿真实直链，拿不到宁可裸声出片也别塞假 BGM
1. **声音对不对**：默认必须用主人克隆声（F5-TTS / CosyVoice2），用了别的声音要在交付前主动说明原因，不能等主人发现。
2. **配音文本规范**（TTS 吃稿前必改）：
   - 所有数字写中文：3800→三千八百、5%→百分之五、2024→二零二四、490亿→四百九十亿（阿拉伯数字必念飘）
   - 正确英文术语**保留**（MoE/token/GPT-4/H100/DeepSeek 等），不要自作主张全汉化；但易念错的词用谐音锚定：token→透肯、V3→V三（字幕仍显示标准写法）
   - 关键事实先联网核实再写稿（型号、数字、时间，例：DeepSeek-V3 是 2024-12-26 发布、671B MoE）
3. **音画同步**：字幕必须和配音同源生成（按段时长×字数比例出 SRT），禁止拿旧字幕配新音；抽 2-3 个点核对。
4. **画面不能只有字幕大小变化**：至少 2-3 段要嵌真实图片（y2_vox 的 image cue）。**小尺寸 logo 不算真实图片**（视觉上等于文字卡，主人原话"没有特色"）——优先用官网/产品页**整屏截图**（google-chrome --headless 截）。图片必须**复制进 specs 目录用纯文件名引用**（`../img/` 越级相对路径会 404 静默丢图，渲染器只 warn 不报错）。
4b. **官网截图必须防"碎图"**（2026-10-10 主人返工）：`--virtual-time-budget=20000` 等网页完整加载再截。截完程序化验尸：行方差<5 的空白行占比 >30%（浅色页）即为半加载碎图，重截；再用 tesseract OCR 确认标题/日期等关键文字在图里。nvidia 等深色主题页空白行天然高（~48%），别误判。
4c. **browser 工具/截图验图可能挂**（browser-harness daemon 起不来、chrome-devtools MCP Target closed）→ 验图降级链：PIL 多尺度 NCC > tesseract OCR > 空白行统计，不依赖浏览器。
5. **节奏**：口播片全片 atempo 1.1 左右提速，开场不能拖。
6. **复用旧 SRT 配新渲染**：若旧 SRT 是 atempo 提速版的时间轴而本轮按原始时长渲染，按总时长比例缩放回原始时间线（逐 cue 时间戳 ×比例，脚本见 scripts/resume-render-pipeline.sh 的 srt 缩放段）；音频用 atempo=视频总时长/音频原始总时长 微对齐。
6. **交付前最后一步**：ffprobe 验时长/流、抽帧验画面、快速回听转写（faster-whisper）核对关键数字和专有名词念对没有。**程序化验图**：browser 工具可能挂掉没法看截图，用 PIL+numpy 对"源图 vs 抽帧"做多尺度 NCC 模板匹配。三个坑（2026-10-10）：① 抽帧时间点必须在 image cue 的 `at` **之后**，在 cue 前抽会得到假阴性（NCC≈0.43 但图其实没问题）；② 图片以卡片/圆角样式渲染时 NCC≈0.75 也算通过，别死磕 >0.8；③ 顺手检查 spec 引用图片的尺寸，<512px 的 logo 直接换整屏截图再渲，别等主人发现。④ **最强验图法：整帧对照**——用 render.py --stills 在成片抽帧同一时刻出一张帧，与成片抽帧（resize 到同尺寸）做整帧 NCC：≈1.0（实测 0.996）即证明该段图片真实进了成片；比源图模板匹配稳得多，卡片/圆角/倾斜贴图样式会毁掉源图 NCC（曾低到 0.27-0.5 全是假阴性）但整帧对照不受影响。全过了才发链接。
7. **ffmpeg 拼接警示**：不同批次渲染的 clip 禁止 `-c copy` concat（会产生 NAL 损坏、接缝花屏）。正确：多输入 concat filter 重编码一步到位（`-i a -i b ... concat=n=N:v=1:a=0`）。
8. **后台流水线必须可续跑**：渲染循环跳过已存在且 ffprobe 完好的 clip；哨兵判断出片完成以 ffprobe 能读出 duration 为准，不能只 ls 文件存在（faststart 的 moov 最后才写入）；流水线被 OOM 静默杀掉过，哨兵同时要监控渲染进程是否还活着。
9. **每支视频交付必须附「五件套+概括」**（主人 2026-10-09 定为长期规则）：3 个备选标题 / 简介 / 封面文案 / 评论区引导语 / #标签，外加一句话概括全片内容。
10. **字幕必须中英双语**（主人 2026-10-10 定为长期规则）：**中文在上、英文在下**。烧字幕时用两个 subtitles 滤镜叠加或 ASS 双行样式；SRT 每条 cue 写两行（第一行中文、第二行英文翻译）。英文翻译由我自翻，保持简洁（不是逐字直译）。

## 克隆配音通道（2026-10-11 更新）
0. **小米 MiMo voiceclone（新首选）**：`mimo-v2.5-tts-voiceclone`，API 无限额、亚秒级稳定。关键坑：参考音频放 `audio.voice` 字段（`data:audio/mpeg;base64,<b64>`），不是 `reference_audio`（400）；合成文本放 assistant 消息、风格指令放 user 消息。完整配方与音色精进链见 `references/mimo-tts-voiceclone.md`。
1. `mrfakename/E2-F5-TTS`（备胎）：token 和匿名**各自独立配额**，一边烧完换另一边；免费 ZeroGPU 每天限量，连烧 3-4 次后 event:error 就是没额度了。
2. `taoyy/CosyVoice2-0.5B`（备胎，已验证可克隆）：endpoint `/gradio_api/call/synthesize`，参数 [tts_text, "零样本语音复刻", ref_file, ref_text, None, 1.0]；**返回的文件 URL 要把 `/grad/gradio_api/file=` 替换成 `/gradio_api/file=` 才能下载**；也会限流，失败 sleep 45-90s 重试。
3. 声纹资产（2026-10-11 定址，勿再散落）：**男声（启行）** `/root/sbr-work/qihang-ref-v2.wav`（新版 81s，比 /root/voice-assets/ref_clip.wav 好）；**女声（林佳颖）** `/root/sbr-work/linjiaying-ref.wav`。声纹预处理：`silenceremove` 去首尾静音 + `loudnorm=I=-20:TP=-2` -ar 24000 -ac 1。
4. /tmp/ffbin 软链会被系统清掉，渲染前先检查重建（imageio-ffmpeg）。

## 音色精进（2026-10-11 主人验收定型）
克隆原始输出偏闷，交付前必须过 ffmpeg 抛光链，**底线：好听但不能丢原声音色**（主人原话）。
- **女声标准链（清脆悦耳、细高）**：`asetrate=24000*1.04,aresample=24000`（提调 4%）+ EQ 2.5k+3dB/6k+2dB/10k+1.5dB + `acompressor=threshold=-22dB:ratio=3` + `loudnorm=I=-16:TP=-1.5`。成品：`/root/sbr-work/linjiaying-clone-higher.wav`。
- **男声标准链（磁性温暖、更细高一点）**：低频 150-300Hz +1~1.5dB、中频 1.8k+1.5dB、中高频 3.5k+2.5dB、高频 6.5k+2dB/10k+1.5dB + `deesser=i=0.1`（imageio-ffmpeg 版 deesser 参数是 i/m/f，均为 0-1 比例值；写 strength/freq 数字或 mode 都会报 Option not found，2026-10-12 muse-v5 实测）+ `acompressor=threshold=-18dB:ratio=2.5` + `alimiter` + `loudnorm=I=-16:TP=-1.5`。成品：`/root/sbr-work/qihang-v2-final.wav`。
- 调整幅度都 ≤3dB，调完必须和原声对比试听确认音色没跑；AMR 派生（企微语音气泡）：`-ar 8000 -ab 12.2k -ac 1`。
- 新声纹入库先用 `references/全要素测试稿.md` 验收（主人要求：连成自然文章体，不要分节标签式测试稿）；验收完才进生产。

## 受众与双声音内容策略（2026-10-11）
抖音受众 97% 男性（18-23 岁近半），主人要男女都能包裹的内容。验证过的打法：**男女双声音对话体**（男声提问/吐槽 + 女声讲解/卖萌）+ **场景化选题**（"给女朋友做 XX"而非纯技术讲解）。双声音克隆配音流程：按 voice 字段给每段选声纹分别走 MiMo voiceclone（风格指令男=磁性温暖、女=清脆温柔）→ 逐段 ffprobe 时长 → spec 分组渲染 → 音频 concat。参考成品：`/root/public/dual-voice-demo.mp4`（37.6s 测试片）。

## 🎨 视觉设计铁律（主人 2026-10-11 多轮返工后定型）
主人原话："照片你之后也别放了，好难看"、"不要高亮，很难看"、"不要纯色，这个谁会看呀，自己做图片可以吗"、"文字声音也确实都没有同步"。
1. **禁止使用照片/角色立绘**：主人明确说照片难看，不要放任何人物照片、角色图、立绘。画面靠**背景艺术图 + 文字排版**撑起来。
2. **禁止纯色背景**："谁会看呀"。必须用**自己生成的艺术背景**（PIL 渐变+光斑+粒子），9 种风格轮换：温暖夕阳/星空梦幻/粉色浪漫/科技蓝光/温暖烛光/黄昏思念/星空许愿/暖光依恋/品牌收尾。每段对话配不同背景，氛围跟内容匹配。
3. **禁止 karaoke 高亮效果**："很难看"。文字就是白色大字+阴影，干净利落，不要逐字高亮、不要花哨动画。
4. **文字声音同步是底线**：主人报过多次"文字图片不同步"。必须用 faster-whisper `word_timestamps=True` 拿词级时间戳，cue 的 at 直接取对应词的 start，**禁止纯按字数比例估算**（长句/停顿处必漂移）。合成后抽 2-3 个点对比"文字出现时刻 vs 该词发音时刻"复核。
5. **排版简洁**：居中大字，中文 64px+英文 32px 斜体，有分隔线，有 text-shadow。不要太多装饰元素。
6. **背景生成脚本**：PIL 渐变（create_gradient）+ 光斑（add_bokeh）+ 粒子（add_particles），9 种色彩方案见 `references/视觉设计.md`。
1. **截图必须加长等待**：`google-chrome --headless=new --window-size=1280,900 --hide-scrollbars --virtual-time-budget=20000 --screenshot=x.png <url>`。不加 virtual-time-budget 会在网页加载一半时截出"碎图"（mistral-news.png 旧图 47.6% 空白行就是这么来的）。
2. **碎图程序化判据**：PIL 转灰度 → 逐行方差，**行方差<5 的空白行占比 >40% 且整体 var 偏低 = 疑似加载不完整的碎图**，必须重截。正常整屏截图空白行约 10%。
3. **误报豁免**：深色主题页（如 NVIDIA 产品页，大片纯黑）和白底文档页（如 DeepSeek API docs 新闻列表）空白行天然 30-48%，别误杀——用 `tesseract x.png -` OCR 出关键文字（产品名/标题/日期）即证明加载完整，文字对上就放行。**密集 JS 应用（如 OpenRouter 榜单页）空白行天然 35%+，wait=8 也压不下去，判据对它不适用：连续两次判碎就直接 OCR 裁定，命中关键文字即放行，禁止无限重截**。深色页可给 web_shot.py 加 `--dark` 跳过空白行判定。
4. 同一 spec 引用的所有图片要逐一过检，别只查主人点名的那张；256×256 logo 一律换同目录整屏截图（自检清单③）。

## 工地选址与服务器重启防护（2026-10-10 踩坑）
1. **渲染工作目录必须放 /root 下**（如 /root/<project>-work），严禁放 /tmp：2026-10-10 凌晨渲染把 2G 内存吃光 → systemd-logind 连串 `Connection timed out` → 02:20 服务器重启，/tmp/ml4 里已渲好的 clips 和日志全灭，只有放 /root 的 specs/配音/图片活下来。源素材（specs/img/wav/srt）也一律存 /root 项目目录。
2. 用户报"出片卡住死掉重启"先查 `last -x | head`（重启历史）+ `journalctl --since today | grep -i 'timed out'`（logind 超时=内存耗尽前兆），别当渲染器 bug 排查。
3. 2核2G 防 OOM 的有效手段：**720p spec 渲染（width1280×height720 副本）+ 合成时 lanczos 升回 1080p**，内存占用大减；渲染前 `echo 3 > /proc/sys/vm/drop_caches` 清缓存。
4. **排障时别用 `pkill -f 'chrome...'` 杀浏览器**：-f 按完整命令行匹配，模式串会匹配到 agent 终端自身的命令行（整条命令里就含 'chrome' 字样），结果终端被 SIGTERM 自杀（2026-10-10 实测 exit -15）。先 `ps aux | grep chrome` 拿 PID，再按 PID kill。

## 轻量 HTML 场景管线（2026-10-11 Muse 新闻片验证，2核2G 上比 huashu 引擎快一个量级）
适合数据新闻/资讯快报类短片（<60s）：**Playwright 截 1080p HTML 场景图 → 每图 ffmpeg zoompan 推拉（奇数推近 1→1.07、偶数拉远 1.07→1，scale=2880:1620 过采样防抖）→ 渐进式两两 xfade 合并 → 加音轨**。参考实现 `/root/sbr-work/remake/{build_scenes,render_video,merge_video}.py`。
1. **合并必须渐进式两两 xfade**：10 路一次性 xfade filter_complex 在 2G 内存上必 OOM（渲完无 moov、进程被静默杀）；改成 merge-02→merge-03…→merge-10 逐轮合并。音画对齐公式：clip_i 时长=段时长+0.5（最后一段不加），xfade offset=累计时长-0.5，总时长=原音频时长。
2. **真实素材保鲜检查**：/root/sbr-work 里 2026-10 存的 techcrunch-muse/verge-muse/reuters-bright 等外媒截图全是 404/访问受限页，**复用旧截图前必须抽帧 vision 验内容**，废图直接现场重抓（App Store 链接在国内会 302 到国区 Today 页，抓不到美区榜单别硬用）。
3. **9to5Mac 是优质新闻截图源**：无弹窗无付费墙、domcontentloaded+9s 即完整，标题大字清晰，适合当"报道实拍"证据卡。
4. **数据可视化比截图更吸睛**：条形图/折线图/环形图用 HTML+SVG 手搓，比例必须真实（22:56:103 天那种）；超长数据可以做"冲出屏幕"的修辞梗。
5. **黄金 2 秒钩子帧（2026-10-11 主人提出留存问题后定型）**：主人数据——前 2 秒跳出率 40-50%，直接决定播放量。规矩：**第一条口播段拆成两个镜头**，前 2 秒放"冲击帧"（满屏高饱和撞色 + 占半屏的巨型数字 + 一句口语钩子，1 秒内零阅读成本看懂核心信息，参考 `/root/sbr-work/remake/scene-00-hook.html`），再淡入原信息版接住细节。冲击帧设计要点：数字与量纲必须绑定在同一视觉块（"500万下载"一体，不要让观众去第二行找量纲）；中心对称构图防左右失衡；钩子帧也用 zoompan（10% 快推，比普通场景的 7% 更急）。改钩子不动音频：把第一段时长切开（如 6.24s→2.0+4.24），只重渲这两段 clip 再全链重合并即可。
6. **HTML 场景验收用 vision 逐帧过**：批量截完场景图后逐张 vision_analyze 查"溢出/遮挡/孤字/图文不符"，本次连抓 4 个雷（截图张冠李戴、证据图是访问受限页、图表与证据卡重叠、"的"字孤行）——都是肉眼一眼问题，不做这步就直接交付给主人当验收员了（违反铁律）。

### 长视频新要求（2026-10-12 主人提出，适用于 2 分钟以上的解说片）
1. **时长基准**：主人明确要"稍微长的视频"（>2分钟档，非 40-45s 快讯），口播节奏仍保持 atempo 1.1 不拖。
2. **画面 = 动画 + 真实图片双轨**：每条长片必须既有动画段（图表/示意/白板），又嵌入 ≥3 张真实图片（官网整屏截图/报道实拍/产品 UI，走 web_shot.py 碎图自检），禁止全片只有动画。
3. **前两秒黄金钩子是硬指标**：主人原话"前两秒一定要吸引人，不能跳出率太高"。前 2 秒帧 = 高饱和撞色 + 巨型数字/悬念大字 + 口语钩子句（1 秒内看懂"这个视频值得留"），参考 scene-00-hook.html 冲击帧范式；钩子帧用 10% 快推。
4. **图片必须动态变换（2026-10-12 追加，主人原话"图片也能动"）**：真实图片禁止整段静态摆放。可选动效（按段自由搭配）：Ken Burns 推拉/平移、图片内局部放大锁定关键区域（如价格/按钮/报错处）、两张图交叉切换（如前后对比）、图片随口播词逐块"点亮"高亮（注意：是图片局部放大强调，不是文字逐字高亮，文字高亮仍被禁）、图块错位入场（上下/左右分层滑入）。参考 engine y2_vox 的 image cue 加 transform 动画，或 HTML 场景里对 <img> 加 CSS keyframes。动效节奏跟口播词：讲到哪块，画面就推到哪块。

## 节奏与配音新规矩（2026-10-12 muse-v5 轮次追加）
7. **节奏基准**：主人嫌 52.7s 慢、接受 42.6s。资讯短片目标 40-45s，整轨 atempo 1.12 提速自然不赶；钩子帧 1.5s、转场 0.4s 比 2.0s/0.5s 更利。
8. **双声分工**：提问/吐槽段用女声，讲解/数据段用男声（主人原话"提问的话，可以用女生声音"）。定脚本时按句型分派 voice，别全片单声。
9. **TTS"一个字一个字符"治理**：病根=文案逗号多+MiMo 默认语速偏慢。重写长句口语体+快节奏指令+关键段 2-3 个变体挑最短，细则见 voice-clone-hf-space-f5tts 技能「相似度与节奏铁律」。
10. **vision 逐帧验新案例（muse-v5 连抓 3 个雷）**：① 图表条长与数据方向自洽（Muse 22 天应是最短条，初版画成最长=逻辑矛盾，补"条越短=越快"标注修复）；② 清单最后一项 top:1010 超出 1080 底边被裁；③ 环形图与大标题重叠——文字和图表放对角/两侧。

## 长渲染任务守护（2026-10-09 渲染进程被 OOM 静默杀死、4 小时无人察觉后的规矩）
1. 分段渲染脚本必须**断点续跑**：每段渲染前先 `ffprobe` 验已有 clip 的 moov（能读出 duration 才算完好），完好的跳过，残的删掉重渲——禁止无脑从头重渲。
2. 哨兵进程判断"出片完成"必须用 `ffprobe 读 duration 成功` 当条件，**不能用文件存在**（ffmpeg 写到一半文件就存在了，会报假完成）。
3. 每次用户问进度，先看进程是否活着（`ps aux | grep render.py`）再看日志行数；日志 10 分钟没动 + 进程消失 = 已死，立刻续跑并告知，不要等用户追问。
4. 2核2G 上 y2_vox（带图拼贴）渲染约 2s/帧（18s 片段 ≈ 19 分钟），720p 约 1s/帧，报 ETA 按这个算，别拍脑袋说 10 分钟。内存不足时会触发 swap 拖慢 3-5 倍，提前提醒用户。
5. **整套断点续跑流水线模板**：`scripts/resume-render-pipeline.sh`（720p 渲染+完好跳过+音频对齐+SRT 缩放+concat filter 一步出片），新项目复制改路径即用。