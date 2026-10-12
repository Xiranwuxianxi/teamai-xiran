# IMA OpenAPI 调用细节（实测于 2026-09-03，ima-skill v1.1.9）

## 调用模板

```bash
cd /root/.hermes/skills/ima-skill
OPTS=$(printf '{"clientId":"%s","apiKey":"%s"}' "$(cat ~/.config/ima/client_id)" "$(cat ~/.config/ima/api_key)")
node ima_api.cjs "<apiPath>" '<jsonBody>' "$OPTS"
```

- stdout = 业务响应 `{"code":0,...}`（code=0 成功；≠0 直接把 msg 给用户看）
- stderr = 程序错误 JSON（-100 程序错误 / -200 有新版 skill），进程非 0 退出
- 注意：**必须显式传 OPTS**；不传时即使凭证文件存在也可能空响应

## 已验证可用的路径

- `openapi/note/v1/list_notebook` body `{"cursor":"0","limit":5}` — 列笔记本，连通性测试首选
- `openapi/wiki/v1/create_knowledge_base` body `{"name":"...","description":"...","type":"KBT_MINE_KB"}` — 新建知识库（2026-09-27 实测可用；type 必填，枚举 KBT_MINE_KB/KBT_SHARED_KB/KBT_SUBSCRIBED_CREATE_KB）

## 主人专属约定：每日生活总结

主人每日口述当天经历 → 整理成 Markdown（文件名 `diary-YYYY-MM-DD.md`，含学习/采购/运动/饮食/小评板块）→ 上传到 IMA 知识库「药灵生活日记总结」（kb_id: `Fl1hfEn8a7MtbyzJbqS4mrD1nqqwgBx8osjZqWETdWk=`）。更正内容时重新上传同名文件（无删除 API，旧版会并存，提醒主人看最新版）。

## 笔记模块路径（来自 notes/SKILL.md，未逐一实测）

- `openapi/note/v1/search_note` — `{"search_type":0,"query_info":{"title":"词"},"start":0,"end":20}`；search_type 1=正文检索，query_info 用 `{"content":"词"}`
- `openapi/note/v1/list_note` — `{"folder_id":"","sort_type":0,"cursor":"","limit":20}`
- `openapi/note/v1/get_doc_content` — `{"note_id":"...","target_content_format":0}`
- `openapi/note/v1/import_doc` — `{"content_format":1,"content":"# 标题\n\n正文"}`，可选 folder_id
- `openapi/note/v1/append_doc` — `{"note_id":"...","content_format":1,"content":"追加文本"}`

## 写入前强制 UTF-8 校验

notes 写入类 API（import_doc/append_doc）的 content/title 必须确保合法 UTF-8，乱码不可逆。
文件内容先检测编码转 UTF-8；网络抓取内容（可能 GBK）必须转码。

## 更新检查

每天首次调用自动检查新版；新版可用时原请求不发送，exit 非 0、stderr code=-200。强制检查：环境变量 `IMA_FORCE_UPDATE_CHECK=1`。

## 已知的坑

- `openapi/list_docs`（主 SKILL.md 示例）404 空响应——是旧路径，所有业务路径必须带 `/v1/`
- 404 时进程 exit 0 且无任何输出，判断成功要看 stdout 里 `code==0`，不能只看退出码