# 搜索书籍

## API

`/store/search`

## 参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `keyword` | string | 是 | - | 搜索关键词 |
| `count` | int | 否 | 20 | 返回数量，最大 100 |
| `offset` | int | 否 | 0 | 偏移量，用于分页 |

## 字段

| 字段 | 说明 |
|------|------|
| `books[].bookId` | 书籍 ID，后续操作用 |
| `books[].title` | 书名 |
| `books[].author` | 作者 |
| `books[].cover` | 封面 URL |
| `books[].intro` | 简介 |
| `books[].rating.count` | 评分人数 |
| `books[].rating.localScore` | 评分，满分 5 |
| `books[].category` | 分类 |
| `books[].finished` | 是否读完 |
| `books[].reading` | 是否在读 |
| `books[].type` | 类型：1=书籍 2=公众号文章 3=有声书 |
| `books[].isHide` | 是否隐藏 |
| `books[].remark` | 备注 |
| `books[].hasNewNote` | 是否有新笔记 |
