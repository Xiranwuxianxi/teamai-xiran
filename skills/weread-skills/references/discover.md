# 发现推荐

## API

| 接口 | 用途 |
|------|------|
| `/store/recommend` | 个性化推荐 |
| `/store/similar` | 相似推荐 |

## 参数

### /store/recommend

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `count` | int | 否 | 20 | 返回数量 |

### /store/similar

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 基于哪本书推荐 |
| `count` | int | 否 | 20 | 返回数量 |

## 字段

| 字段 | 说明 |
|------|------|
| `books[].bookId` | 书籍 ID |
| `books[].title` | 书名 |
| `books[].author` | 作者 |
| `books[].cover` | 封面 URL |
| `books[].intro` | 简介 |
| `books[].rating.count` | 评分人数 |
| `books[].rating.localScore` | 评分（满分 5） |
| `books[].recommendReason` | 推荐理由 |
