# 笔记划线

## API

| 接口 | 用途 |
|------|------|
| `/book/bookmarklist` | 获取个人笔记（划线+想法+书签） |
| `/review/list/mine` | 个人想法/点评列表 |
| `/book/bestbookmarks` | 书籍热门划线 |
| `/book/underlines` | 划线热度统计 |
| `/book/readreviews` | 书籍点评（联合 review.md 使用） |

## 参数

### /book/bookmarklist

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |

### /review/list/mine

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |
| `count` | int | 否 | 20 | 返回数量 |
| `offset` | int | 否 | 0 | 偏移量 |

### /book/bestbookmarks

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |
| `chapterUid` | int | 否 | - | 指定章节 UID（不传则返回全书热门划线） |
| `count` | int | 否 | 20 | 返回数量 |

### /book/underlines

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `bookId` | string | 是 | - | 书籍 ID |

## 字段

### /book/bookmarklist 响应

| 字段 | 说明 |
|------|------|
| `bookmarkList[].chapterUid` | 所属章节 UID |
| `bookmarkList].range` | 划线位置，"起始-结束" |
| `bookmarkList[].markText` | 划线文本 |
| `bookmarkList[].createTime` | 创建时间（时间戳） |
| `bookmarkList[].type` | 类型：1=划线，2=想法，4=书签 |
| `bookmarkList[].abstract` | 想法内容（type=2 时） |

### /book/bestbookmarks 响应

| 字段 | 说明 |
|------|------|
| `items[].chapterUid` | 章节 UID |
| `items[].range` | 划线位置 |
| `items[].markText` | 划线文本 |
| `items[].likeCount` | 点赞数 |
| `items[].totalCount` | 划线人数 |
| `items[].comments[].content` | 热门想法内容 |
| `items[].comments[].user.nickName` | 想法用户昵称 |

### /book/underlines 响应

| 字段 | 说明 |
|------|------|
| `underlines[].chapterUid` | 章节 UID |
| `underlines[].totalCount` | 划线人数，按章节聚合 |

注意：`/book/underlines` 仅返回划线人数统计，不含划线文本。想看划线内容用 `/book/bestbookmarks`。
