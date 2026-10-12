---
name: a-share-market-data-collection
description: "A股（中国股市）市场数据采集完整方案。从东方财富网、腾讯证券等来源获取指数、个股、板块、龙虎榜、资金流向等数据的可靠方法。适用于盘后复盘、行情监控、数据分析等场景。触发条件：(1) 需要获取A股指数/个股行情 (2) 需要板块涨跌幅排行 (3) 需要龙虎榜数据 (4) 需要主力资金流向 (5) 需要北向/南向资金数据"
metadata:
  category: data-science
  version: "1.0.0"
  source: custom
---

# A股市场数据采集方案

从中国股市数据源（腾讯证券、东方财富）可靠获取行情数据的标准化方法。

## 零、输出前必须先 `date` 校准当前时段（主人纠正，2026-08-31）

报告里写"盘前/盘中/收盘"前，先跑 `date` 拿到真实时间再定口径，禁止凭感觉写：
- 09:15 前 → 盘前（只能用昨收数据，说"昨日收盘"）
- 09:30–15:00 → 盘中（实时数据，必须标注"截至 HH:MM 盘中"）
- 15:00 后 → 收盘后（可用收盘价/全天成交额）
节假日/周末同理——先确认今天是否交易日。时段写错会导致整份报告口径混乱（已实测被主人纠正过）。

## 一、数据源选择与优先级

```
优先级1: 新浪行情API (hq.sinajs.cn) — 最稳定可靠，需加Referer头
        格式简单易解析(逗号分隔)，成交量单位为手、成交额单位为元
        指数和个股都可用
        注意：不要加缓存破坏参数（如&_=timestamp），否则返回空
优先级2: 腾讯证券API (qt.gtimg.cn) — 稳定，含完整行情数据(波浪线分隔)
        字段多但索引偏移，需要对照字段表逐个匹配
        GBK编码需解码处理
优先级3: 东方财富浏览器页面 — JS动态加载页，用browser工具提取
        browser_navigate + browser_console提取
        适用于大盘资金流向、行业板块资金、龙虎榜等
优先级4: 东方财富API (push2.eastmoney.com) — 单证券查询可用，批量查询返回垃圾数据
        `/api/qt/stock/get?secid=...` 单证券查询正常
        `/api/qt/ulist.np/get?secids=...` 多证券查询返回异常数据，不可用
        有IP限流，经常exit code 52，不建议作为主要批量数据源
优先级5: 百度/同花顺/雪球等第三方API — 多数需要登录或访问受限
        可作为最后备选
```

### 数据源选择经验

实际盘后复盘时，推荐以下高效流程：
1. **腾讯证券API** → 三大指数行情+重点个股（最稳定，curl即可）
2. **新浪API** → 指数成交量和成交额（需加Referer头，格式简单）
3. 如果前两者数据够用，就不需要开浏览器（节约2G内存）
4. 需要板块/龙虎榜/资金流向时才用browser访问东方财富页面

### 完整盘面分析必须多源并行（2026-08-31 用户明确要求）

用户明确要求"结合所有能力分析，不要只盯一个"。完整A股盘面分析的标准三源（本技能只覆盖其中东财/腾讯一路）：
1. **小石量化**（api.shizixi.com）：key 在 /root/.hermes/xiaoshi/api_key（600权限，永不打印）；每任务开头 no-store 读 /api/v3/manifest 比版本哈希，端点以 SKILL.md 为准不写死
2. **问财6技能**：hithink-market-query / hithink-sector-selector / news-search 等，直接 `python3 scripts/cli.py` 调；问"今日涨停股票数量""今日主力资金净流入最大行业"等自然语言查询已验证可用
3. **东财/腾讯实时**（本技能下文）：qt.gtimg.cn 指数 + push2.eastmoney.com 板块资金流

执行模式：delegate_task 派3个子Agent并行采集（每源一个），主Agent汇总——比串行快约3倍，且避免单源失败导致整体阻塞。

### 东财 clist 接口反爬红线（2026-08-31 实测）

push2.eastmoney.com/api/qt/clist/get 对单页大 pz 值（500/2000/6000 实测全部 curl 52 Empty reply from server）直接断连；涨跌分布统计接口返回 rc:102 拒绝。板块榜小页（pz=20）带 UA+Referer 正常。要全市场涨跌家数：换问财直接问，或 pz≤100 分页循环累加，禁止 pz≥500 单页拉取。

## 二、腾讯证券API

### 基础行情数据

**股票/指数查询：** `https://qt.gtimg.cn/q=股票代码列表`

示例：上证指数+深证成指+创业板指用逗号分隔代码。
示例：单只股票用完整前缀+代码。

### GBK编码处理

腾讯接口返回GBK编码数据，必须解码。可使用terminal运行iconv转换，或在Python中raw.decode('gbk', errors='replace')处理。

### 字段位置对照（按~分割）

| 字段索引 | 含义 | 说明 |
|---------|------|------|
| [1] | 名称 | 如"上证指数"、"三花智控" |
| [2] | 代码 | 如"000001" |
| [3] | 当前价/收盘价 | 最新价 |
| [4] | 昨收 | 前一日收盘 |
| [5] | 开盘价 | 今日开盘 |
| [6] | 成交量（手） | 单位：手 |
| [30] | 时间戳 | 如20260515160021 |
| [31] | 涨跌额 | 数值 |
| [32] | 涨跌幅% | 百分比数值 |
| [33] | 最高价 | 当日最高 |
| [34] | 最低价 | 当日最低 |
| [37] | 成交额（万元） | 单位：万元 |
| [38] | 换手率% | 仅个股有此字段 |
| [39] | 市盈率 | 仅个股有此字段 |

### 股票代码前缀规则

| 市场 | 前缀 | 示例 |
|------|------|------|
| 上证指数/个股 | sh | sh000001, sh600519 |
| 深证指数/个股 | sz | sz399001, sz002050 |

### 北向资金数据获取（含API限制说明）

**API端点：** `https://push2.eastmoney.com/api/qt/kamt.rtmin/get?secid=1.000001&fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55`

**⚠️ 重要限制（已验证）：** 收盘后该API返回的所有分时数据中净买额均为`0.00`，无法获取有效北向资金数据。建议方案：
1. 盘中实时数据可用此API获取
2. **盘后复盘**时，北向资金数据需通过**浏览器访问东方财富沪深港通页面**提取
3. 浏览器页面 `https://data.eastmoney.com/hsgt/hsgtV2.html` 包含完整北向/南向资金数据

**沪深港通页面（browser方案）：**
- URL: `https://data.eastmoney.com/hsgt/hsgtV2.html`
- 可用数据：南向资金当日净买额、北向资金（收盘后有延迟）、沪深港通十大成交股、北向资金季度持股排行
- 提取方式：browser_navigate → browser_console执行 `document.body.innerText`

### 大盘资金流向历史数据

URL: `https://data.eastmoney.com/zjlx/dpzjlx.html`

**数据形式：** 页面直接渲染（非JS动态），可用浏览器直接提取。
**关键数据：** 完整的每日大盘资金流向历史表，包含：
- 上证/深证收盘价及涨跌幅
- 主力净流入（超大单+大单）、超大单净流入、大单净流入
- 中单、小单净流入
- 数据跨度大（半年以上历史）

**当日主力资金流向（browser从新浪财经提取）：**
从新浪财经页面vip.stock.finance.sina.com.cn可提取以下当日数据：
- 沪A上涨/下跌家数、深A涨跌家数
- 特大单/大单/中单/小单的净流入净流出（单位：亿）
- 注意：特大单净流出+大单净流出 ≈ 主力净流出，这个值对判断当天机构态度很有参考价值

**提取方式：** browser_navigate加载 → browser_console提取document.body.innerText，然后解析表格行。

### 行业板块资金流向

URL: `https://data.eastmoney.com/bkzj/hy.html`

**数据形式：** 页面动态渲染，需用browser_navigate + browser_console提取。
**提取方式：** 页面加载后，获取所有table元素。table[1]包含完整的行业板块主力资金流向排行（20+行），每个条目包括：
- 排名、名称、涨跌幅
- 主力净流入（金额+占比）
- 超大单/大单/中单/小单净流入
- 主力净流入最大股

## 四、东方财富 —— 龙虎榜数据

URL: `https://data.eastmoney.com/stock/lhb.html`

**数据形式：** 页面动态渲染，包含多张数据表。

**提取方式：** 页面加载后，用browser_console分析所有table元素：

| table索引 | 内容 | 说明 |
|-----------|------|------|
| 0-3 | 各市场今日上榜个股（沪/科创/深/京） | 快速浏览 |
| 6 | 龙虎榜净买额排行（完整数据） | 包含代码、名称、上榜次数、净买额、买入额、卖出额、总成交额 |
| 8 | 机构龙虎榜 | 买方机构数、卖方机构数、机构买入/卖出/净额 |

### 东方财富push2 API — 指数行情字段对照

| 字段 | 含义 | 单位 | 说明 |
|------|------|------|------|
| f43 | 现价/收盘价 | 点×100 | 如407728=4077.28点 |
| f44 | 最高价 | 点×100 | |
| f45 | 最低价 | 点×100 | |
| f46 | 开盘价 | 点×100 | |
| f47 | 成交量 | 手 | |
| f48 | 成交额 | 元 | |
| f170 | 涨跌额 | 点×100 | [-200, +200]范围 |
| **f171** | **涨跌点数(点)** | 点×100 | **⚠️ 注意：这是涨跌点数，不是百分比！** 如301=3.01点 |
| f169 | 昨收价 | 点×100 | |

**涨跌幅%计算：** `涨跌幅% = (f43 - f169) / f169 * 100`

**正确示例：**
```python
sh_data = {"f43": 407728, "f170": -204, "f171": 301, "f169": 417438}
# ❌ 错误：f171/100 = 3.01，误以为是+3.01%
# ✅ 正确：手动计算：
chg_pct = (407728 - 417438) / 417438 * 100  # = -2.33%
```

**经验教训：** f170（涨跌额）和f171（涨跌点数）两者含义是近似的(涨跌额≈涨跌点数)，但都**不是涨跌幅百分比**。百分比必须用(f43-f169)/f169*100计算。

### API可用性验证（2026-05更新）

以下API在VPS环境中存在限制，需针对性处理：

- **push2.eastmoney.com** — 行业板块/概念板块/个股列表API，**经常exit code 52（连接被远端重置）或空响应**。建议直接放弃curl方式，改用浏览器访问东方财富页面
- **datacenter-web.eastmoney.com** — 龙虎榜新版API，**可用但需注意排序字段**。详见下方"龙虎榜API正确用法"
- **datainterface.eastmoney.com** — 旧版数据接口，超时或无响应
- **nufm.dfcfw.com** — 概念板块接口，返回302重定向

### 龙虎榜API正确用法（datacenter-web）

**端点：** `https://datacenter-web.eastmoney.com/api/data/v1/get`
**参数：**
- `reportName=RPT_DAILYBILLBOARD_DETAILSNEW` — 必选
- `columns=ALL` — 获取全部字段
- `filter=(TRADE_DATE='2026-05-19')` — 日期过滤，用前一天日期（当日数据在16:00后仍未发布）
- `pageNumber=1&pageSize=50`
- `sortTypes=-1&sortColumns=SECURITY_CODE` — **注意：不能使用NET_BS_AMT或CHANGE_PCT作为排序字段，会报"排序列不存在"**

**注意：** 当日龙虎榜数据通常在**17:30-18:00之间**才发布。16:00查询当日日期会返回`"返回数据为空"`（code=9201）。**正确做法：查询前一个交易日数据作为参考。** 例如周四(5/21)查周三(5/20)的数据。

**可用排序字段（已验证）：** `SECURITY_CODE`, `TRADE_DATE`, `SECURITY_NAME_ABBR`
**❌ 不可用排序字段（会报错）：** `NET_BS_AMT`, `CHANGE_PCT`, `BUY_AMO`, `DEAL_AMOUNT_RATIO`

**返回字段名（实际API返回，与文档/页面显示不同）：**
| API字段名 | 含义 | 单位 |
|----------|------|------|
| `SECURITY_NAME_ABBR` | 股票名称 | 字符串 |
| `SECURITY_CODE` | 股票代码 | 字符串 |
| `CHANGE_RATE` | 涨跌幅 | %（如20.0表示+20%） |
| `NET_BS_AMT` | 净买入额 | 元（需÷10000转万元） |
| `SUM_BUY_AMT` | 买入总额 | 元（需÷10000转万元） |
| `SUM_SELL_AMT` | 卖出总额 | 元 |
| `CLOSE_PRICE` | 收盘价 | 元 |
| `EXPLANATION` | 上榜原因 | 字符串 |
| `TRADE_DATE` | 交易日期 | yyyy-MM-dd HH:mm:ss |
| `TURNOVERRATE` | 换手率 | % |
| `BUY_SEAT` | 买方机构数 | 数值 |
| `SELL_SEAT` | 卖方机构数 | 数值 |

**获取净买入TOP的方法（因为没有排序字段可用）：**
```python
# 获取全部数据后在Python中排序
result = terminal("curl -s 'https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=ALL&filter=(TRADE_DATE=...)'")
items = json.loads(result['output'])['result']['data']
sorted_items = sorted(items, key=lambda x: x.get('NET_BS_AMT', 0), reverse=True)  # 净买入TOP
# 或 reverse=False 获取净卖出TOP
```

**数据时效：** 当日龙虎榜数据通常在17:30-18:00才发布。16:00查询当日日期会返回"返回数据为空"。**正确做法：查询前一个交易日数据。** 例如周三(5/20)查周一(5/19)的数据。

### 板块排名数据获取（新浪财经浏览器方案）

当push2.eastmoney.com API被屏蔽时，**新浪财经的板块页面可通过浏览器提取**，这是最稳定的替代方案。

**行业板块排名：**
- 访问 `https://vip.stock.finance.sina.com.cn/mkt/#hangye_ZF`
- 在browser_console中执行 `document.body.innerText` 提取页面文本
- 数据包含：板块名称、涨跌幅、领涨股及涨幅
- 页面为SPA（JS渲染），需等页面完全加载后再提取

**概念板块排名：**
- 访问 `https://vip.stock.finance.sina.com.cn/mkt/#gn_ZF`
- 同样用browser_console提取

**资金流向（ETF资金监控）：**
- 访问 `https://data.eastmoney.com/zjlx/dpzjlx.html`
- 页面直接渲染（非JS动态），browser提取即可
- 包含：上证/深证收盘价、主力净流入（超大单+大单）、超大单/大单/中单/小单净流入
- 数据跨度可达半年以上

**解决方案：** 当curl方式失败时，立即切换到browser工具访问东方财富页面（如`data.eastmoney.com/bkzj/`或`quote.eastmoney.com/center/boardlist.html`），通过浏览器JS渲染获取数据。或者使用新浪、腾讯等替代数据源。

### 代理环境坑：mihomo未运行时curl全挂（2026-08验证）

服务器环境变量 `https_proxy=http://127.0.0.1:7890` 可能已设置但mihomo进程未启动，导致所有curl请求 `Connection refused` / `HTTP:000` / exit code 7。
**解决：所有国内数据源（新浪/腾讯/东方财富datacenter-web）的curl命令加 `--noproxy '*'` 参数直连**，国内站不需要代理。

### push2.eastmoney.com 彻底不可用时的板块数据替代方案（2026-08验证有效）

push2及其节点（82.push2/48.push2）全部 HTTP:000 不可达时，**板块涨跌幅排行改用新浪纯curl方案**（无需浏览器）：

```bash
# 行业板块（49个）
curl -s --noproxy '*' 'https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php' \
  -H 'Referer: https://finance.sina.com.cn' -o /tmp/hy.txt
# 概念板块（175个）
curl -s --noproxy '*' 'https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class' \
  -H 'Referer: https://finance.sina.com.cn' -o /tmp/gn.txt
```

**⚠️ GBK解码坑：必须先 `-o` 存文件再按字节读 `open(f,'rb').read().decode('gbk')`。** 不要：
- 在browser_console里fetch（中文全部乱码）
- 在Python里对terminal输出做 `encode('latin1', errors='ignore')`（中文字符>255被直接丢弃，名字全丢）

**字段格式**（逗号分割，key为板块代码）：
`"new_blhy":"new_blhy,玻璃行业,19,16.65,0.244,1.488,量,额,sz300093,领涨股涨幅,领涨股价,领涨股涨跌额,长海股份"`
- p[1]=板块名, p[2]=成分股数, p[5]=板块涨跌幅%, p[8]=领涨股代码, p[9]=领涨股涨跌幅, p[12]=领涨股名
- 用正则 `re.finditer(r'"(\w+)":"([^"]+)"', txt)` 提取后按p[5]排序

### 游资营业部席位统计API（RPT_OPERATEDEPT_ACTIVE）

**端点：** `https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_OPERATEDEPT_ACTIVE&columns=ALL&filter=(ONLIST_DATE='2026-08-19')&pageNumber=1&pageSize=30`

**已验证的坑：**
- ❌ filter用 `(TRADE_DATE='...')` → 报错"TRADE_DATE列不存在"，该表日期字段是 **ONLIST_DATE**
- ❌ filter用 `(STATISTICS_CYCLE='01')` → 不过滤，返回2004年至今的全量历史数据
- ❌ `sortColumns=NET_AMT` → 报错"NET_AMT排序列不存在"，**不要传sortColumns/sortTypes**，拿数据后在Python里自己排序

**返回字段：** OPERATEDEPT_NAME（营业部名）, ONLIST_DATE, BUYER_APPEAR_NUM, SELLER_APPEAR_NUM, TOTAL_BUYAMT, TOTAL_SELLAMT, TOTAL_NETAMT, BUY_STOCK, SECURITY_NAME_ABBR（涉及个股，空格分隔）

**用法：** 按ONLIST_DATE过滤当天后，按OPERATEDEPT_NAME聚合TOTAL_NETAMT求和，排序得游资席位净买/净卖TOP。知名席位参考：国泰海通上海分公司（章盟主）、东财拉萨系（散户大本营）、高盛世纪大道（北向马甲）。

### 安全扫描导致的管道命令失败

当使用`curl`管道到解释器时，Hermes的安全扫描可能会拦截。

**推荐替代方案：**
```bash
# 方式1：用execute_code工具，内部调用terminal()
# Python代码中：
from hermes_tools import terminal
r = terminal("curl -s 'https://hq.sinajs.cn/list=sh000001' -H 'Referer: https://finance.sina.com.cn'")
# 返回的output字符串可直接在Python中解析

# 方式2：保存到文件再读取
curl -s 'https://hq.sinajs.cn/list=sh000001' -H 'Referer: https://finance.sina.com.cn' -o /tmp/index.csv
# 然后用read_file读取
```

### 新浪行情API（最稳定数据源之一）

**🚨 关键：必须添加 `-H "Referer: https://finance.sina.com.cn"` 请求头**，否则返回 `Forbidden`。

```bash
# 获取指数行情（需要Referer头）
curl -s "https://hq.sinajs.cn/list=sh000001,sz399001,sz399006" \
  -H "Referer: https://finance.sina.com.cn"

# 获取个股行情
curl -s "https://hq.sinajs.cn/list=sz002050" \
  -H "Referer: https://finance.sina.com.cn"
```

返回格式：`var hq_str_sh000001="名称,今开,昨收,当前,最高,最低,?,?,成交量(手),成交额(元),..."`

**指数行情字段（逗号分割，0-indexed）：**

| 索引 | 含义 | 单位 | 示例值 |
|-----|------|------|--------|
| [0] | 名称 | 字符串 | "上证指数" |
| [1] | 今开 | 元/点 | 4162.1845 |
| [2] | **昨收**（关键） | 元/点 | 4174.3772 |
| [3] | **当前价/收盘价** | 元/点 | 4077.2765 |
| [4] | 最高价 | 元/点 | 4199.5269 |
| [5] | 最低价 | 元/点 | 4074.2167 |
| [8] | 成交量 | 手 | 727218701 |
| [9] | 成交额 | 元 | 1595726694715 |

**涨跌幅计算：** `涨跌幅% = (当前价[3] - 昨收[2]) / 昨收[2] * 100`

**⚠️ 注意与东方财富API的区别：** 东方财富push2 API的f171字段是**涨跌点数（点）**，不是涨跌幅百分比。如需百分比必须手动计算。

**个股行情字段（逗号分割）：**

| 索引 | 含义 | 单位 |
|-----|------|------|
| [0] | 名称 | 字符串 |
| [1] | 今开 | 元 |
| [2] | 昨收 | 元 |
| [3] | 当前价/收盘价 | 元 |
| [4] | 最高价 | 元 |
| [5] | 最低价 | 元 |
| [6] | 买一价 | 元 |
| [7] | 卖一价 | 元 |
| [8] | **成交量**（注意：单位是**股**，不是手） | 股 |
| [9] | 成交额 | 元 |

**💡 数据单位核验（关键差异）：**
- 新浪个股成交量单位 = **股**（÷100才得手数）
- 新浪指数成交量单位 = **手**（指数与个股不同）
- 腾讯个股成交量[6] = **手**
- 腾讯个股成交额[37] = **万元**

### 指数成交额 vs 个股成交额

指数的"成交额"是交易所所有股票成交额的总和。例如上证指数成交额13065亿 = 沪市所有股票成交额之和。这个值可以很大（1-2万亿），不代表指数本身"成交了这么多钱"。

### 新浪外盘期货/黄金符号（hq.sinajs.cn，2026-08-27验证）

同一个 `hq.sinajs.cn/list=` 接口（仍需 Referer 头 + `--noproxy '*'`，返回GBK）支持外盘和内盘贵金属：

| 符号 | 含义 | 备注 |
|------|------|------|
| `hf_GC` | COMEX黄金（纽约金） | 连续合约，近24h滚动 |
| `hf_SI` | COMEX白银（纽约银） | 同上 |
| `gds_AUTD` | 黄金T+D（上金所） | 夜盘约02:30收，之后时间戳停在收盘时刻，注意辨别"最新价"是否已停更 |

**hf_* 字段（逗号分割，0-indexed）：** [0]=最新价 [4]=当日最高 [5]=当日最低 [6]=时间 [7]=昨结（结算价，算涨跌幅的分母） [8]=开盘价 [12]=日期 [13]=名称。
**gds_* 字段：** [0]=最新价 [4]=最高 [5]=最低 [6]=时间 [7]=昨结 [12]=日期。
涨跌幅 = (最新[0] - 昨结[7]) / 昨结[7] × 100。

### 新浪7x24快讯API —— 财报/宏观突发事件首选（2026-08-27验证）

```bash
curl -s --noproxy '*' "https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=30&zhibo_id=152&tag_id=0&dire=f&dpc=1&pagesize=30" \
  -H "User-Agent: Mozilla/5.0" -H "Referer: https://finance.sina.com.cn/7x24/"
```

- 返回JSON：`result.data.feed.list[]`，每条含 `create_time`（精确到秒）+ `rich_text`（正文）
- **实测价值：** 英伟达凌晨4:20发财报，360搜索已被限流返回空、东方财富快讯API缺req_trace参数报错，只有这个接口直接给出了营收/EPS/数据中心/指引/盘后股价全链条快讯（4:31-5:12逐条滚动），是美股财报夜、联储议息夜等场景的**第一数据源**
- 直连可用，无需代理；page_size 最大约50；无鉴权

## 六、东方财富 —— 北向/南向资金

URL: `https://data.eastmoney.com/hsgt/hsgtV2.html`

**可用数据：**
- **南向资金（港股通）当日数据：** 页面直接渲染，包含港股通(沪)和港股通(深)的净买额、买入额、卖出额
- **北向资金当日数据：** 收盘后有时延迟，显示为"-"未更新
- **沪深港通十大成交股：** 前一日数据，含股票代码、名称、收盘价、涨跌幅、成交金额
- **沪深港通历史数据：** 近几日的南向净买额历史
- **北向资金季度持股排行：** 按持股市值排列，含变动%

**提取方式：** browser_navigate加载 → browser_console提取document.body.innerText，然后解析表格行。

页面结构索引（基于实际验证，索引可能微调）：
- header区域 → 南向资金当日数据（港股通沪/深净买额）
- 北向资金数据 → 陆股通：沪股通/深股通成交总额、领涨股
- 沪深港通十大成交股 → 前一日数据（个股明细）
- 北向资金季度持股排行 → 按持股市值排列

### 板块涨跌幅排行（板块API）

**可用API：** `https://push2.eastmoney.com/api/qt/clist/get`
- 概念板块：`fs=m:90+t:3`
- 行业板块：`fs=m:90+t:2`
- 板块涨幅排名：`fs=m:90+t:2&fid=f3&po=1`
  （f3=涨跌幅，po=1表示降序排列）
- 参数示例完整URL：`https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=10&po=1&np=1&fields=f2,f3,f4,f12,f14&fid=f3&fs=m:90+t:2`
- f3涨跌幅单位：实际值*100（如1080表示+10.80%）
- f2指数点位单位：实际值*100（如97557表示975.57）
- 建议pz=10获取前10名即可
- **注意：** 此API可能被限流返回空，备选方案是用浏览器访问板块资金流向页

### 今日板块涨幅排行 — 快速获取

对于快速盘后复盘，使用上述push2板块API最直接。若API返回空，后备方案：
- 浏览器访问 `https://data.eastmoney.com/bkzj/` 获取行业板块实时排行

## 六、备用数据源：新浪财经龙虎榜（当东方财富不可达时）

当东方财富 push2 API 返回 502 或浏览器无法加载时，**新浪财经龙虎榜页面**是最可靠的备用方案。

### 龙虎榜页面

URL: `http://vip.stock.finance.sina.com.cn/q/go.php/vInvestConsult/kind/lhb/index.phtml`

**特点：**
- 页面为静态HTML，数据直接在`<table>`标签中渲染（非JS动态加载）
- 可通过 `browser_navigate` + `browser_console` 直接提取
- 分类清晰：涨幅偏离值≥7%、跌幅偏离值≥7%、连续3日涨幅≥20%、换手率≥20%、振幅≥15%等
- 每只上榜股票包含：代码、名称、收盘价、对应值(%)、成交量(万股)、成交额(万元)
- ❌ 但 **不提供机构席位买卖明细**（需要点击"查看交易详情"才展开，且展开后也无法抓取明细数据）

**提取方式（数据提取技巧）：**

```javascript
// 在 browser_console 中执行：
let tables = document.querySelectorAll('table');
let result = '';
tables.forEach((t, i) => {
  let rows = t.querySelectorAll('tr');
  if (rows.length > 3) {
    result += `=== Table ${i} (${rows.length} rows) ===\n`;
    rows.forEach((r, j) => {
      if (j < 15) result += r.textContent.trim().substring(0, 300) + '\n';
    });
  }
});
result
```
这个技巧过滤掉日历表格、空表格，只保留数据表（rows.length > 3），并且每条只取前300字符避免输出过长。

页面上的表格索引和内容（基于验证）：
| 表索引 | 内容 | 说明 |
|-------|------|------|
| 4+ | 连续3日跌幅ST | *ST退市风险股 |
| 15+ | 连续3日涨幅≥20% | 趋势强势股 |
| 42+ | 换手率≥20% | 活跃短线标的 |
| 73+ | 涨幅偏离值≥7% | 当日强势股 |
| 94+ | 振幅≥15% | 多空分歧大的标的 |
| 111+ | 连续3日跌幅≥20% | 弱势股 |
| 114+ | 跌幅偏离值≥7% | 当日弱势股 |
| 137+ | 无涨跌幅限制 | 新股上市 |
| 142+ | 创业板涨幅20% | 20cm涨停标的 |

注意：表索引会因页面动态加载内容而变化，不要硬编码索引。

**数据局限性：**
- 只有深市主板和中小板的上榜数据
- 沪市主板和科创板数据不在同一页面
- 不含机构净买入/净卖出具体金额明细
- 适合快速复盘查看热门标的，不适合深度量化分析

### 新浪财经首页（快速查看三大指数）

URL: `https://finance.sina.com.cn/stock/`

**特点：**
- 直接显示上证综指、深证成指、北证50、创业板指四大指数的当前价、涨跌额、涨跌幅%
- 页面静态渲染，browser打开即可查看
- 可作为curl获取指数失败时的快速验证方案

### 已知不可用数据源（已验证）

| 数据源 | 结果 | 说明 |
|-------|------|------|
| Tencent GT 行业板块代码(sh881xxx) | ❌ 返回空 | 该接口不支持板块指数查询 |
| 东方财富 push2 API (上海服务器) | ❌ 502/超时 | 频繁被限流，curl和browser都不可靠 |
| 东方财富 push2 `ulist.np/get` 批量查询（多证券） | ❌ 返回垃圾数据 | 当secids包含多个证券时，指数返回全零（除f169/f170/f171外），个股返回异常数值（如f43=93367794.0）。**正确做法：用单证券endpoint `/api/qt/stock/get?secid=...` 逐个查询，或改用腾讯/新浪API批量查询** |
- **Bing 国际版中文搜索** | ❌ 无金融结果 | cn.bing.com 搜索结果不含金融新闻/数据（会被自动跳转到国内版，即使加cc=us参数也无效） |
| Google 搜索 | ❌ 被代理封锁 | 白嫖机场节点通常封锁Google |
| 新浪行业排名 (sshy/index.phtml) | ❌ 空页面 | 该页面已下线或改版 |
| 新浪API带缓存破坏参数 `&_=timestamp` | ❌ 返回空 | 加时间戳参数会导致API返回空字符串，**不要加此参数** |

### text_to_speech 工具行为说明

当调用 `text_to_speech` 工具时：
- 即使 `output_path` 指定 `.mp3` 扩展名，实际生成的文件格式为 **Ogg Opus**（`.ogg`）
- 返回的 `media_tag` 中 `MEDIA:` 路径也指向 `.ogg` 文件
- 在生成报告时，如果引用了语音链接，需注意URL扩展名与实际文件扩展名不一致的问题

## 七、最佳实践流程

### 完整盘后复盘数据采集流程

1. **判断数据源可用性** → 先curl测试新浪API和腾讯API，如果都正常走流程2-5
2. **新浪API (curl + Referer头)** → 获取三大指数 + 重点个股行情（最稳定）
3. **腾讯证券API** → 获取完整的个股行情数据（含换手率、市盈率等）
4. **东方财富浏览器** → 大盘资金流向 (dpzjlx.html) — 如果东方财富可达
5. **东方财富浏览器** → 行业板块资金流向 (bkzj/hy.html) — 如果东方财富可达
6. **东方财富浏览器** → 龙虎榜 (stock/lhb.html) — 如果东方财富可达
7. **⚠️ 降级方案（东方财富不可达时）** → 新浪财经龙虎榜 + 新浪首页查看指数
8. **东方财富浏览器** → 北向资金 (hsgt/hsgtV2.html)

### 快速5分钟盘后复盘方案（推荐低配服务器）

当服务器资源有限（2G内存）或网络受限时，用最少的请求获取核心数据：

```
Step 1: curl(新浪API) → 三大指数行情 + 三花智控/重点个股
Step 2: browser(新浪龙虎榜) → 热门上榜标的
Step 3: 综合撰写报告
```

不尝试东方财富API（大概率502浪费时间），不开不需要的浏览器窗口。

### 数据时效与发布时间

1. **收盘时间**：A股15:00收盘，盘后复盘建议安排在15:30之后
3. **龙虎榜发布时间**：交易所通常在收盘后1-2小时（约16:00-17:00）发布数据，但东方财富汇总整理约需17:30-18:00。**关键：API查询当日日期(如2026-05-20)在16:00返回"返回数据为空"，需查询前一个交易日(2026-05-19)**。
3. **大盘资金流向**：收盘后约15-30分钟更新完毕，可在16:00前获取当日完整数据
4. **北向资金**：收盘后盘中数据不完整，需等收盘后约30分钟完全更新

### 浏览器数据提取最佳实践

东方财富数据页面均为JS动态渲染，推荐用以下流程提取：

**步骤1：** `browser_navigate` 加载目标页面
**步骤2：** `browser_console` 执行 `document.body.innerText` 提取全文
**步骤3：** 用 `substring(start, end)` 截取含数据表格的关键段落
**步骤4：** 在最终报告中手动整理和格式化数据

**注意：** `browser_snapshot` 在数据量大的页面上会被截断（超过8000字符），JS console提取全文更可靠。

### 浏览器工具可用性降级

`browser_navigate` 可能因 daemon 启动失败而无法使用（返回 `Daemon failed to start`）。当浏览器不可用时：
1. 优先使用腾讯证券API或新浪API获取行情数据
2. 对于龙虎榜/板块资金等浏览器依赖的数据，改用新浪财经龙虎榜页面（静态HTML）
3. 不要在浏览器故障时反复重试，浪费时间
