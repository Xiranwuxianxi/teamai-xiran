---
name: animation-quality-standards
description: |
  动画制作质量标准和评估指南，帮助识别常见质量问题并提供优化方向。
  适用于各类动画视频制作（包括AI生成、Remotion、纯代码动画等）。
tags: [animation, quality, standards, video, remotion, improvement]
---

# 动画制作质量标准

## 视觉质量问题

### 1. 分辨率与清晰度
- **基准**: 1920×1080 (Full HD) 或更高
- **码率**: 视频码率 ≥ 8 Mbps（高质量）
- **检查**: `ffprobe -v quiet -show_streams output.mp4`

### 2. 帧率与流畅度
- **基准**: 30fps（标准）或 60fps（高动态）
- **注意**: Remotion 默认 30fps，复杂动画建议 60fps

### 3. 色彩与对比度
- **基准**: 色彩鲜艳、对比度清晰
- **避免**: 灰暗、模糊、色彩单一
- **检查**: 播放时直观感受，或截图对比

### 4. 动画流畅性
- **基准**: 动作自然、无卡顿
- **关键**: 使用 `spring` 或 `interpolate` 实现平滑过渡
- **避免**: 线性生硬移动、跳帧

## 内容质量问题

### 1. 叙事结构
- **清晰**: 有开头→发展→结尾
- **节奏**: 每场景时长合理（3-10秒）
- **逻辑**: 场景切换有因果关系

### 2. 视觉元素
- **层次**: 前景/中景/背景分明
- **对齐**: 元素居中或遵循设计网格
- **留白**: 不拥挤，呼吸感

### 3. 字体与排版
- **可读**: 字体大小 ≥ 24px（移动端 ≥ 16px）
- **对比**: 文字与背景对比度 ≥ 4.5:1
- **统一**: 字体家族一致，最多2种

### 4. 音画同步
- **关键**: 音频总时长 ≈ 视频总时长
- **实现**: `staticFile('audio/xxx.mp3')` + `durationInFrames` 精确匹配
- **检查**: 播放时逐场景验证

## 常见质量问题清单

- [ ] **分辨率不足**: 低于 1920×1080 或码率 < 5 Mbps
- [ ] **码率过低**: 画面有块效应、模糊
- [ ] **帧率不足**: 快速移动时卡顿
- [ ] **色彩灰暗**: 饱和度 < 50%，对比度 < 30%
- [ ] **动画生硬**: 使用线性插值而非 spring
- [ ] **文字难读**: 字体 < 24px 或颜色对比不足
- [ ] **音画不同步**: 音频时长与视频时长差距 > 2秒
- [ ] **布局混乱**: 元素无对齐、拥挤或重叠

## 优化方向

1. **提升码率**: `ffmpeg -i input.mp4 -b:v 8M -maxrate 12M output.mp4`
2. **换 H.265**: 同画质体积减半
3. **增强色彩**: 调整 CSS `filter: contrast(1.2) saturate(1.3)`
4. **平滑动画**: 用 `spring({fps, frame, config: {damping: 10, stiffness: 100}})`
5. **音画对齐**: 精确计算每段 `durationInFrames` = `音频时长 × fps`

## 快速评估脚本

```bash
#!/bin/bash
# 动画质量快速检查

VIDEO="$1"

echo "=== 动画质量报告 ==="

# 1. 分辨率
RES=$(ffprobe -v quiet -show_entries stream=width,height -of json "$VIDEO" | jq '.streams[0]')
echo "分辨率: $(echo $RES | jq -r '.width')x$(echo $RES | jq -r '.height')"

# 2. 码率
BITRATE=$(ffprobe -v quiet -show_entries format=bit_rate -of json "$VIDEO" | jq -r '.format.bit_rate')
echo "码率: $((BITRATE/1000)) kbps"

# 3. 帧率
FPS=$(ffprobe -v quiet -show_entries stream=r_frame_rate -of json "$VIDEO" | jq -r '.streams[0].r_frame_rate')
echo "帧率: $FPS"

# 4. 音频音量
VOL=$(ffmpeg -i "$VIDEO" -af volumedetect -f null - 2>&1 | grep mean_volume | awk '{print $5}')
echo "平均音量: $VOL"

# 5. 文件大小
SIZE=$(du -h "$VIDEO" | cut -f1)
echo "文件大小: $SIZE"

echo "=== 评估完成 ==="
```
