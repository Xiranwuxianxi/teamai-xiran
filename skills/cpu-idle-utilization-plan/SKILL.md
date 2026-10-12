---
name: cpu-idle-utilization-plan
description: 低配VPS（如2核2G）CPU闲置时的榨干方案——将空闲CPU转化为有持续产出价值的后台任务集群，含永动机数据采集器+纯Python压测器+多cron定时任务组合
triggers:
  - 服务器CPU一直闲着
  - CPU空闲怎么利用
  - 服务器白买了
  - VPS闲置CPU利用
  - 持续CPU消耗任务
---

# 药灵·低配VPS CPU闲置利用方案

## 适用场景
- 低配VPS（2核2G/1核1G），CPU长期空闲70%+
- 需要CPU消耗有产出价值（不空转）
- 有公网IP可以部署服务展示成果

## 架构总览

三层结构从轻到重：

```
Layer 1: 定时cron任务 (爆发式CPU，每2-6小时触发)
→ AI云原生资讯/A股复盘/雅思/K8s编译/视频渲染

Layer 2: 7×24永动机 (低强度持续)
→ 白天爬虫采集(30min/轮)，凌晨视频转码

Layer 3: 纯Python压测器 (高强度定时，每天3轮)
→ 40秒压测CPU冲到90%+，产出性能基线报告
```

## Layer 1: 定时cron任务

用 `cronjob` 工具创建，自动推送到用户：

| 任务 | 频率 | CPU消耗 |
|------|------|---------|
| AI云原生资讯(早晚) | 08/20点 | 中低 |
| A股盘后复盘 | 交易日16点 | 中 |
| 雅思每日一练 | 09点 | 低 |
| K8s源码编译 | 周二/五凌晨2点 | 🔥🔥🔥 |
| 短视频渲染 | 周一/四凌晨3点 | 🔥🔥🔥🔥🔥 |

## Layer 2: 永动机·数据采集器

### 核心模式
Python脚本挂systemd后台，30分钟一轮，异常自动重启。

```python
# 工作模式轮换
while True:
    if 6 <= datetime.now().hour < 23:
        data = collect_from_github_and_devto()
        update_html_report(data)
    else:
        video_transcode_and_compress()
    time.sleep(30 * 60)
```

### 数据源选择（稳定可达的）
- **GitHub Search API**：`created:>{DATE}` 新项目查询
- **DevTo API**：`https://dev.to/api/articles?tag=kubernetes`
- **HN Algolia**：`https://hn.algolia.com/api/v1/search?query=kubernetes`
- ❌ HuggingFace从国内服务器通常不通，跳过

### systemd配置要点
- `Restart=always` + `RestartSec=30` 确保挂了自动拉起重试
- **不要用** `StandardOutput=append:` —— 在OpenCloudOS上会导致exit status 209
- 让脚本自己管理日志文件

### 避坑
1. 爬虫间sleep 1.2秒避免GitHub API次级限流
2. GitHub API未认证每小时60次，优先用Search API（一次搜索返回15条，极划算）
3. HuggingFace/api.github.com都可用，但github.com主站curl超时
4. 磁盘超85%自动清理tmp和journal日志

## Layer 3: 纯Python压测器

### 为什么不用wrk
wrk在某些发行版（OpenCloudOS）yum/dnf找不到，源码编译可能因网络超时。**纯Python优势**：Python的GIL+解释器开销本身就是天然CPU消耗器。

### 核心模式
```python
def worker_thread(url, duration):
    while time.time() < end_time:
        send_http_request(url)
        # CPU密集计算：让GIL保持竞争，CPU占用率飙升
        for _ in range(10):
            _ = sum(i*i + math.sqrt(i+1) for i in range(1, 500))
```

### 精确CPU监控（基于/proc/stat差分）
不要用psutil（可能没装），不要解析top输出。

```python
with open("/proc/stat") as f:
    parts = f.readline().split()
    vals = [int(x) for x in parts[1:]]
    # vals[0]=user, vals[1]=nice, vals[2]=system, vals[3]=idle, vals[4]=iowait
# 采样间隔后再次读取，差分计算CPU使用率
usage = (1 - delta_idle / delta_total) * 100
```

### 实测数据（2核2G OpenCloudOS · 8线程 · 40秒）
- RPS: **356 req/s**
- CPU峰值: **97.5%**
- CPU平均: **42.4%**
- 延迟: **21.4ms**
- 成功率: **100%**

### 产出价值
1. 公网性能看板（实时趋势+RPS曲线）
2. 自动性能评级（S/A/B/C）
3. 瓶颈分析
4. 面试作品："持续性能测试平台"

## f-string三元表达式避坑
不要在f-string里嵌套多层三元表达式：
```python
# ❌ 报错
f"{'a' if x >= y if len>1 else 'b' else 'c'}"
# ✅ 先算再插
flag = "a" if x >= y else "c"
f"{flag}"
```
