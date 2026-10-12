# 书籍信息

## API

| 接口 | 用途 |
|------|------|
| `/book/info` | 书籍详情 |
| `/book/chapterinfo` | 章节目录 |
| `/user/books/readprogress` | 阅读进度 |

## 参数

### /book/info

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |

### /book/chapterinfo

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |

### /user/books/readprogress

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |

## 字段

### /book/info 响应

| 字段 | 说明 |
|------|------|
| `title` | 书名 |
| `author` | 作者 |
| `cover` | 封面 URL |
| `intro` | 简介 |
| `category` | 分类 |
| `publishTime` | 出版时间（时间戳） |
| `isbn` | ISBN |
| `rating.count` | 评分人数 |
| `rating.localScore` | 评分（满分 5） |
| `totalWords` | 总字数 |
| `finishedCount` | 读完人数 |
| `readingCount` | 在读人数 |

### /book/chapterinfo 响应

| 字段 | 说明 |
|------|------|
| `chapters[].chapterUid` | 章节 UID |
| `chapters[].title` | 章节标题 |
| `chapters[].level` | 章节级别（1=章，2=节） |
| `chapters[].wordCount` | 字数 |

### /user/books/readprogress 响应

| 字段 | 说明 |
|------|------|
| `readProgress` | 阅读进度百分比（0-1） |
| `readUpdateTime` | 最后阅读时间（时间戳） |
| `finished` | 是否读完 |
| `readingTime` | 阅读时长（秒） |
