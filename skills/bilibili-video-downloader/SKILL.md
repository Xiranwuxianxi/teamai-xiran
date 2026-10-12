---
name: bilibili-video-downloader
description: B站视频批量下载并部署到公网的完整工作流。解决B站反爬（412错误、CDN限制、yt-dlp/you-get均不可用）、HTTPS跨域无法POST数据到服务器等问题，通过B站官方API + Akamai CDN backupUrl + ffmpeg合并，实现稳定下载。
trigger: 用户要求下载B站视频/剧集/合集
---

# B站视频下载完整工作流

## ⚠️ 核心避坑（必须先读）

### 1. 不要用这些工具（必失败）
- ❌ `yt-dlp` → HTTP 412 Precondition Failed（B站WAF拦截）
- ❌ `you-get` → JSON parse error（B站改版后失效）
- ❌ 服务器直连B站CDN → SSL_ERROR_SYSCALL / connection reset（IP被封）
- ❌ 浏览器内fetch→POST到服务器 → CORS被拦（HTTPS页面禁止HTTP请求）
- ❌ navigator.sendBeacon → 跨域失败
- ❌ WebSocket → HTTPS页面禁止ws://连接

### 2. 只有这个方案能稳定工作
**B站官方API获取播放地址 + Akamai CDN backupUrl下载 + ffmpeg合并**
Akamai的`upos-hz-mirrorakam.akamaized.net`CDN对服务器IP友好，不会被拦。

---

## 完整步骤

### Step 1: 获取视频的 avid 和 cid

有两种方式：

**方式A：从B站页面获取（推荐）**
```javascript
// 在浏览器控制台执行
window.__INITIAL_STATE__.videoData.aid  // 视频aid
window.__INITIAL_STATE__.videoData.cid  // 视频cid
```

**方式B：从已打开的页面取**
```javascript
// 先确认video元素存在且有视频源
document.querySelector('video') ? 'ok' : 'no'
// 点击播放器触发加载
// 然后取aid和cid
```

### Step 2: 调用B站API获取播放地址

```bash
curl -s 'https://api.bilibili.com/x/player/playurl?avid=AVID&cid=CID&qn=32&type=&otype=json&fnver=0&fnval=4048' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Referer: https://www.bilibili.com/' \
  --cookie 'buvid3=B508F96B-EBE5-E584-87B5-9CAE1B8FC41080613infoc'
```

参数说明：
- `qn=32` → 480p（免费最高画质）
- `qn=64` → 720p（需登录）
- `qn=80` → 1080p（需大会员）
- `fnval=4048` → DASH格式（m4s分段）

### Step 3: 解析返回的JSON

API返回格式：
```json
{
  "code": 0,
  "data": {
    "dash": {
      "video": [{
        "id": 32,
        "baseUrl": "...",
        "backupUrl": ["..."],  // ← 优先用这个
        "bandwidth": 166446,
        "width": 852,
        "height": 480
      }],
      "audio": [{
        "id": 30216,
        "baseUrl": "...",
        "backupUrl": ["..."],  // ← 优先用这个
        "bandwidth": 65694
      }]
    }
  }
}
```

**关键：始终用 `backupUrl[0]` 而非 `baseUrl`**
- `baseUrl` → B站CDN（upos-sz-*），对服务器IP不友好
- `backupUrl[0]` → 通常是Akamai CDN（upos-hz-mirrorakam.akamaized.net），对服务器友好

### Step 4: 下载视频轨和音频轨

```bash
# 下载视频m4s（从backupUrl取）
curl -L -o video.m4s \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  -H 'Referer: https://www.bilibili.com/' \
  "BACKUP_URL_VIDEO" \
  --connect-timeout 15 --max-time 60

# 下载音频m4s
curl -L -o audio.m4s \
  -H 'User-Agent: Mozilla/5.0' \
  -H 'Referer: https://www.bilibili.com/' \
  "BACKUP_URL_AUDIO" \
  --connect-timeout 15 --max-time 60
```

### Step 5: 合并为MP4

```bash
ffmpeg -i video.m4s -i audio.m4s -c copy -movflags +faststart /root/public/output.mp4 -y
```

### Step 6: 部署到公网

Nginx容器静态服务器已配置：
- 容器名：`static-nginx`
- 挂载目录：`/root/public/` → `/usr/share/nginx/html`
- 访问地址：`http://118.89.90.232/<文件名>.mp4`

直接发链接给用户即可，不用额外部署操作。

---

## 批量下载方案

对于合集多集下载，用`delegate_task`派子Agent并行下载。

**单集下载的Python脚本模板：**
```python
import requests, json, subprocess, os

avid = "116824570073597"
cid = "39465780159"
output = "/root/public/suivei-XX.mp4"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com/'
}
cookies = {'buvid3': 'B508F96B-EBE5-E584-87B5-9CAE1B8FC41080613infoc'}

# Step 1: 获取播放地址
api_url = f'https://api.bilibili.com/x/player/playurl?avid={avid}&cid={cid}&qn=32&type=&otype=json&fnver=0&fnval=4048'
resp = requests.get(api_url, headers=headers, cookies=cookies, timeout=15)
data = resp.json()

video_url = data['data']['dash']['video'][0]['backupUrl'][0]
audio_url = data['data']['dash']['audio'][0]['backupUrl'][0]

# Step 2: 下载
subprocess.run(['curl', '-L', '-o', '/tmp/v.m4s', '-H', headers['User-Agent'], video_url, '--max-time', '60'])
subprocess.run(['curl', '-L', '-o', '/tmp/a.m4s', '-H', headers['User-Agent'], audio_url, '--max-time', '60'])

# Step 3: 合并
subprocess.run(['ffmpeg', '-i', '/tmp/v.m4s', '-i', '/tmp/a.m4s', '-c', 'copy', '-movflags', '+faststart', output, '-y'])
```

---

## 注意事项

1. **Cookie有有效期**：`buvid3`可以在浏览器控制台通过`document.cookie`获取
2. **API有频率限制**：短时间内多次请求会被返回412
3. **Akamai URL含hdnts参数**：有时效性（大约30分钟），需在获取后尽快下载
4. **m4s文件不能直接播放**：必须用ffmpeg合并音视频轨
5. **480p是免费最高画质**：更高清晰度需要登录/大会员，API会返回对应错误码
6. **抢先看预览视频**：如果视频时长<10秒，说明是预览版，API只返回预览数据，无法获取完整内容
7. **合集获取**：用`browser_console`从页面提取videoData，或点进每集页面分别获取

## 验证清单

- [ ] 视频可播放（HTTP 200，浏览器直接打开）
- [ ] 时长与B站页面一致（对比duration）
- [ ] 音画同步
- [ ] 文件大小合理（480p约6-11MB/5分钟）
- [ ] 公网链接可访问
