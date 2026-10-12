# 书架管理

## API

`/shelf/sync`

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `books` | string | 否 | - | 同步标记，首次传 `""` |

## 字段

| 字段 | 说明 |
|------|------|
| `books[].bookId` | 书籍 ID |
| `books[].title` | 书名 |
| `books[].author` | 作者 |
| `books[].cover` | 封面 URL |
| `books[].finished` | 是否读完 |
| `books[].readUpdateTime` | 最后阅读时间（时间戳） |
| `books[].readingTime` | 阅读时长（秒） |
| `books[].type` | 类型：1=书籍，2=公众号文章，3=有声书 |
| `books[].format` | 格式：1=epub，2=pdf，3=txt，4=mobi，5=azw3 |
| `books[].remark` | 备注 |
| `albums[].bookId` | 专辑/有声书 ID |
| `albums[].title` | 专辑名称 |
| `albums[].author` | 作者/主播 |
| `mp` | 公众号书架信息（一般非空即可认为有公众号内容） |
| `synckey` | 同步 key，下次请求需传入 |

## 书架数量计算

回答"书架有多少本书/多少条目"时使用：`books.length + albums.length + (mp 非空 ? 1 : 0)`
- `books[]` = 书籍列表
- `albums[]` = 专辑/有声书（也属于书架里的内容）
- `mp` 非空 = 公众号书架（算 1 条）

## 书架排序

书架默认按「最后阅读时间」倒序，先展示最近阅读的书籍。如果用户问"阅读进度"，调用 `/user/books/readprogress` 看具体进度。
