---
name: cn-ecommerce-link-research
description: 用户要具体商品购买链接时用。服务器抓电商被登录墙拦，用搜索渠道交付三层链接。
---

# 国内电商购买链接调研（淘宝/京东/速卖通）

用户要"具体产品链接，不要只给搜索链接"时用这个流程。

## 现实约束（2026-10 实测）

- **京东搜索页**：无头浏览器（browser_exec、chrome-devtools MCP、agent-browser）一律被重定向到 passport.jd.com 登录墙；curl 移动版 so.m.jd.com 返回空 53 字节。服务器端无法直接扒商品列表。
- **淘宝搜索页**：s.taobao.com 对无头浏览器返回空页面，抓不到 item 链接。
- **速卖通 aliexpress**：国内服务器访问超时抓不动，但**它的单品链接可以被 web_search 搜到**，可作备用链接来源。

## 可行交付流程

1. 用 `web_search` 搜 `<品类> 官方旗舰店 京东/天猫`、`site:aliexpress.com <product>`，能稳定拿到三类耐用链接：
   - 京东官方旗舰店店铺页（`mall.jd.com/index-<id>.html`，非常稳定，如香橙派官旗 index-12862142）
   - 淘宝官方聚合页/单品页（`taobao.com/list/item/...`、`taobao.com/list/product/...`）
   - 速卖通单品页（`aliexpress.com/item/<id>.html`）
   - 厂商官方 Wiki/资料页（如 waveshare.net/wiki/...，附带接线/驱动文档，价值高）
2. 每件商品按**三层链接**交付，并明说单品链接可能失效：
   - 🏪 具体店铺/单品链接（直接点）
   - 📖 官方产品页/Wiki（核对规格）
   - 🔍 平台搜索直达（`s.taobao.com/search?q=...` / `search.jd.com/Search?keyword=...`，永久有效兜底）
3. 不要浪费时间反复尝试抓取电商搜索页——弹登录墙是确定性的，直接转 web_search 渠道。

## 沟通要点

- 主动坦白"电商反爬拦了服务器抓取，单品链接是从公开渠道核实的"，用户接受这个前提。
- 标准化配件（声卡/喇叭/线材）给搜索链接+选型关键词即可；大件（主板/屏幕）尽量给 2-3 个具体链接。
