---
name: knowledge-capture
description: 用户说"记一下/存想法/小记/搜之前记的"时默认存取腾讯 IMA 笔记的路由与调用规范。
---

# knowledge-capture

## 铁律：默认记入 IMA

用户规则（2026-09-03 确立）：**知识类内容、想法、小记，默认存到腾讯 IMA，不要再问存哪里。**

路由：
| 用户说的 | 动作 |
|---|---|
| "记一下 XXX"（未指定位置） | IMA `import_doc` 新建笔记 |
| "记到 XX 笔记" | 先 `search_note` 拿 note_id，再 `append_doc` 追加 |
| "搜一下我之前记的 XX" | IMA `search_note`（search_type 0=标题, 1=正文） |
| 上传文件/收藏网页到知识库 | IMA knowledge-base 模块 |

IMA 技能本体在 `/root/.hermes/skills/ima-skill`（用户自装 v1.1.9，user-owned 不要改），
凭证在 `~/.config/ima/client_id` + `api_key`（权限 600）。

## ⚠️ 关键坑：接口路径必须带 v1

ima-skill 主 SKILL.md 里的示例 `openapi/list_docs` 是**旧路径，调用会 404 且空响应**（exit 0 但 stdout 为空，极易误判为成功）。
真实路径必须带子模块版本前缀：
- 笔记：`openapi/note/v1/{search_note,list_note,list_notebook,get_doc_content,import_doc,append_doc}`
- 知识库：`openapi/wiki/v1/...`

调用模板与完整 API 细节见 [references/ima-api.md](references/ima-api.md)。

## 凭证/敏感文件写入被安全层拦截时

在 QQ 等无确认弹窗的渠道，terminal 写密钥文件会因超时反复 BLOCKED。
**不要重试、不要换命令绕过**。降级方案：把命令贴给用户让其自行 SSH 执行，然后你再验证连通性。实测有效。

## 验证连通性的最小用例

`list_notebook`（见 references）。返回 `{"code":0,"msg":"success"}` 即凭证有效；
新账号 `note_folder_infos` 为空属正常，不是故障。