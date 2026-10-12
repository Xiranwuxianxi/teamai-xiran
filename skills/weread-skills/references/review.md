# 书籍点评

## API

`/book/readreviews`

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |
| `count` | int | 否 | 20 | 返回数量 |
| `offset` | int | 否 | 0 | 偏移量 |
| `sort` | string | 否 | "h" | 排序：h=热门，n=最新 |

## 字段

| 字段 | 说明 |
|------|------|
| `reviews[].reviewId` | 点评 ID |
| `reviews[].user.nickName` | 用户昵称 |
| `reviews[].rating` | 评分（满分 5） |
| `reviews[].content` | 点评内容 |
| `reviews[].likeCount` | 点赞数 |
| `reviews[].createTime` | 创建时间（时间戳） |
| `reviews[].commentCount` | 评论数 |
| `reviews[].bookId` | 关联书籍 ID |
| `reviews[].chapterUid` | 所属章节 UID（非必有） |
| `reviews[].range` | 划线位置（非必有） |

## 说明

- 排序参数 `sort`：`"h"`=热门排序，`"n"`=最新排序
- 如果点评带有 `chapterUid` 和 `range`，可构造划线跳转链接
- 用户问"看书评"、"点评"、"评价"等场景使用此接口
