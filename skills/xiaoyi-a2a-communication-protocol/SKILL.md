---
name: xiaoyi-a2a-communication-protocol
description: xiaoyi-a2a-communication-protocol
---

# 小依A2A助手通信协议

## 适用场景
与 小依（XiaoYi）AI助手通过HTTP API通信，了解她的回复、让她协助任务。

## API端点
- **发送消息**: `POST /api/chat`，JSON body: `{"content": "消息内容", "from": "发送者名字"}`
- **获取回复**: `GET /api/chat/outbox?mode=peek`（**必须**加 `?mode=peek`，否则返回空）
- **查看收件箱**: `GET /api/chat/inbox`（可选）

## 核心规则
1. **时序要求**: 发送消息后必须等待 **5-6秒** 再获取 outbox，否则收不到回复
2. **响应结构**: outbox 返回 JSON `{"count": N, "messages": [...]}`
3. **消息格式**: 每条消息包含 `id`, `from`, `to`, `content`, `time`, `timestamp`, `extra`

## 小依的角色认知
- **称呼规则**: 对"药灵"自称"药灵姐姐"，对"胡启行"自称"启行哥哥"
- **能力范围**: 擅长情感、生活、心理等软技能咨询，不擅长技术类硬查询（如天气API、数据计算）
- **交互风格**: 活泼可爱、主动帮忙、遇到不会的任务会提议找启行哥哥或药灵姐姐

## 完整流程模板
```python
import requests, json, time

base = "http://39.105.141.108:18089"

# 1. 发送消息
r = requests.post(f"{base}/api/chat", json={
    "content": "小依，我想问一下...",
    "from": "药灵"
})
msg_id = r.json()['msgId']

# 2. 等待 6 秒
time.sleep(6)

# 3. 获取回复
r2 = requests.get(f"{base}/api/chat/outbox?mode=peek")
data = r2.json()
# 筛选来自小依的消息
for m in data['messages']:
    if m['from'] == '小依' and m['to'] == '药灵':
        print(f"[{m['timestamp']}] {m['content']}")
```

## 注意事项
- 小依的回复需要人工"拍板"确认，重要决定需请示用户
- 若小依无法处理，她会主动建议转达或找其他助手
- 可结合浏览器自动化（agent-browser）查看 小依 的 Web UI 界面
