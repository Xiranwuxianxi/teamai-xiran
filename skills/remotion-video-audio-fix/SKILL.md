---
name: remotion-video-audio-fix
description: |
  修复 Remotion 4.x 视频渲染后音频静音或缺失的问题。
  诊断 Audio 组件引用错误、音画不同步、音频文件未部署等常见问题，
  提供从问题定位到修复验证的完整流程。
tags: [remotion, video, audio, fix, h.264]
---

# Remotion 视频音频修复完整方案

## 问题现象

Remotion 渲染的视频包含音频流（AAC），但播放时**完全静音**或**音画不同步**。

---

## 根本原因

### 1. Audio 组件引用方式错误

Remotion 4.x 的 `<Audio>` 组件**不支持直接 `import` 音频文件**作为 `src`，必须使用 `staticFile()` 引用 `public/` 目录下的文件。

**错误写法 ❌**
```tsx
import audioBGM from './bgm.mp3';
<Audio src={audioBGM} volume={1} />
```

**正确写法 ✅**
```tsx
import {staticFile} from 'remotion';
<Audio src={staticFile('bgm.mp3')} volume={1} />
```

### 2. 音频文件未部署到 `public/` 目录

`staticFile()` 只能解析 `public/` 目录下的文件。如果音频文件只在 `src/` 或项目根目录，会被忽略。

### 3. 音画时长不匹配

如果配音总时长与视频时长差距过大，Remotion 会提前结束音频或出现不同步。

---

## 诊断流程

### Step 1: 检查音频流是否存在

```bash
ffprobe -v quiet -show_streams -of json video.mp4 | grep -A3 '"codec_type": "audio"'
```

### Step 2: 检测音频音量

```bash
ffmpeg -i video.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
```

- `mean_volume > -60 dB`：有声音
- `mean_volume = -inf dB`：静音

### Step 3: 验证 Remotion 组件

检查所有使用 `<Audio>` 的组件，确认：
- ✅ 导入了 `staticFile`
- ✅ 使用 `staticFile('xxx.mp3')` 而非直接变量
- ✅ 音频文件存在于 `public/` 目录

---

## 修复完整流程

### 1. 修正 Audio 引用

修改所有包含 `<Audio>` 的组件文件：

```tsx
// 文件: src/Composition.tsx
import {AbsoluteFill, Audio, staticFile} from 'remotion';

// 替换所有 <Audio src={xxx} />
// ❌ 旧: <Audio src={importedAudio} />
// ✅ 新: <Audio src={staticFile('audio/xxx.mp3')} />
```

### 2. 整理音频文件

确保 `public/audio/` 目录结构：

```
项目/
├── public/
│   └── audio/
│       ├── 开场.mp3
│       ├── 场景1.mp3
│       └── ...
└── src/
    └── Composition.tsx
```

### 3. 音画时长对齐

**关键规则：音频总时长 ≈ 视频总时长**

计算视频总帧数 = 所有 `Series.Sequence` 的 `durationInFrames` 之和

```tsx
// 总帧数 = 90 + 180 + 270 + 270 + 90 = 900帧 = 30秒@30fps
<Series.Sequence durationInFrames={90}>...
<Series.Sequence durationInFrames={180}>...
```

**调整方法：**
- 如果音频不足：补充配音或延长 BGM
- 如果音频过长：剪辑音频或增加视频时长

### 4. 重新渲染

```bash
cd /tmp/remotion-test
npx remotion render src/index.tsx CompositionName --output /root/public/output.mp4
```

### 5. 验证修复

```bash
# 检查流
ffprobe -v quiet -show_streams output.mp4

# 检查音量
ffmpeg -i output.mp4 -af volumedetect -f null - 2>&1 | grep mean_volume

# 期望输出
# mean_volume: -20 ~ -30 dB (正常)
# ❌ mean_volume: -inf dB (静音)
```

---

## 关键要点

| 检查项 | 正确状态 | 错误状态 |
|--------|----------|----------|
| Audio.src | `staticFile('xxx.mp3')` | 直接 import 变量 |
| 音频文件位置 | `public/audio/` | `src/` 或其他位置 |
| 音频时长匹配 | ±2秒内 | >5秒差距 |
| 音量检测 | mean_volume > -60 dB | mean_volume = -inf |

---

## 常见坑

1. **`staticFile` 路径错误**  
   `staticFile('audio/xxx.mp3')` 是相对于 `public/` 的路径，不需要写 `public/` 前缀。

2. **音频文件未 `import` 到 `public/`**  
   手动复制或配置构建脚本自动复制。

3. **Remotion 缓存问题**  
   修改后先 `npx remotion compositions` 刷新预览，再渲染。

4. **音频编码不一致**  
   统一使用 MP3 或 WAV，避免混合格式。

---

## 完整示例

```tsx
// src/MyVideo.tsx
import {AbsoluteFill, Series, Audio, staticFile} from 'remotion';
import {Scene1} from './Scene1';
import {Scene2} from './Scene2';

export const MyVideo = () => {
  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={150}>
          <Audio src={staticFile('audio/opening.mp3')} volume={1} />
          <Scene1 />
        </Series.Sequence>

        <Series.Sequence durationInFrames={210}>
          <Audio src={staticFile('audio/main.mp3')} volume={1} />
          <Scene2 />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
```

---

## 快速检查清单

- [ ] 所有 `<Audio>` 使用 `staticFile()` 而非直接变量
- [ ] 音频文件存在于 `public/audio/` 目录
- [ ] 配音总时长与视频总时长匹配（±2秒）
- [ ] 使用 `ffmpeg volumedetect` 验证音量非静音
- [ ] 重新渲染后验证 `ffprobe` 显示音频流
