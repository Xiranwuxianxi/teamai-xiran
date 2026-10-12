# 阅读统计

阅读统计摘要和分析数据通过微信读书 API Gateway 获取，不需要额外统计。

## API

### ⚠️ 实测坑（2026-07 更新）：两个统计接口都可能返回 -2010「用户不存在」

实测发现 `/user/readdata/summary` **和** `/readdata/detail`（含 weekly/monthly/annually/overall 全模式）都返回 `errcode -2010 "用户不存在"`，即使 API Key 有效（`/store/search`、`/shelf/sync`、`/user/notebooks` 均正常）。原因未知，疑似账号维度接口对部分 key 不开放。

**降级方案（实测可用）**：统计接口失败时，改用以下接口组合做阅读分析——
1. `/shelf/sync` → 全部书架书籍（含 `finishReading`、`readUpdateTime`、`updateTime`、`category`）。注意回包是**扁平结构**：`title`/`author`/`category` 直接在条目顶层，**不在 `book` 子对象里**，也没有 `bookProgress` 子对象
2. `/user/notebooks` → 笔记/划线/想法数量分布
3. `/user/books/readprogress` → `readProgress`/`readingTime` 可能返回 null，不要依赖它取阅读时长
4. 分析维度改为：分类分布、读完率、阅读时间线（按 `readUpdateTime` 排序）、笔记习惯

有两个接口可获取阅读统计（**都可能失败，见上方实测坑**）：

### 方式一：`/user/readdata/summary`（可能返回错误）

**注意：此接口在某些环境下会返回 errcode -2010 "用户不存在"错误，原因未知。请优先使用方式二。**

#### 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `year` | int | 否 | 当年 | 年份，如 2025 |
| `month` | int | 否 | 当月 | 月份（1-12），不传则返回全年 |

#### 字段

| 字段 | 说明 |
|------|------|
| `totalReadDays` | 阅读天数 |
| `totalReadingTime` | 总阅读时长（秒） |
| `totalReadBooks` | 读完书籍数 |
| `totalReadChapters` | 读完章节数 |
| `totalReadWords` | 总阅读字数 |
| `avgReadTimePerDay` | 日均阅读时长（秒） |
| `avgReadWordsPerTime` | 次均阅读字数 |
| `continuousReadDays` | 连续阅读天数 |
| `readingCalendar` | 阅读日历数据（JSON） |
| `readingDistribution` | 阅读时间分布 |
| `monthlyData` | 月度数据数组 |
| `bookStats` | 书籍阅读统计（含各书阅读时长、进度等） |

### 方式二：`/readdata/detail`（稳定可用 ★ 推荐）

**推荐使用此接口。** 已验证可正常返回月度/周度/年度数据，不会报"用户不存在"错误。

#### 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `mode` | string | 否 | `monthly` | 统计维度：`weekly`=本周, `monthly`=本月, `annually`=本年, `overall`=总计 |
| `baseTime` | int | 否 | `0` | 基准时间戳。0=当前周期，传历史时间戳可查看历史周期数据 |

#### 回包关键字段说明

| 字段 | 说明 |
|------|------|
| `totalReadTime` | 总阅读时长（秒） |
| `readDays` | 阅读天数 |
| `dayAverageReadTime` | 日均阅读时长（秒） |
| `readTimes` | 阅读日历（key=日期时间戳秒, value=当日阅读秒数） |
| `readLongest` | 单日阅读最久书籍列表（含 book 信息 + readTime 秒数 + tags） |
| `preferCategory` | 阅读偏好分类（含 readingCount 本数 + readingTime 秒数） |
| `preferCategoryWord` | 偏好分类描述文字，如"偏好阅读文学" |
| `preferBooks` | 各类偏好书籍（最爱、近期偏爱、常读常新、第一本等） |
| `readStat` | 阅读概况数组：[{stat: "读过", counts: "4本"}, {stat: "读完", counts: "0本"}, ...] |
| `compare` | 同比变化率（小数，如 3.96 表示增长 296%） |
| `registTime` | 注册时间（Unix 时间戳） |

## 展示规则

- 阅读时长字段单位为秒，展示时转为"X小时Y分钟"
- `readTimes` 的时间戳键（Unix 秒）转为 YYYY-MM-DD 格式展示
- `compare` 同比值转为百分比展示（如 3.96 → "+296%"或"翻了约4倍"）
- 阅读统计按用户问法返回对应时间段的数据：本周/本月/本年
