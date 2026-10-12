# 指数信息查询 — 接口字段权威参考

本文中的路径均为 JSON 路径，`$` 表示响应根节点。字段缺失、空值或结构异常时先检查真实响应，不把 ETF 或场外基金字段套到指数对象。

## 公共请求头与约定

- 请求头：`Authorization: Bearer <token>`、`X-Caller-Type: external`，由 `scripts/api_client.py` 与 `config.py` 处理。
- POST 接口均带可选公共参数 `requestId`（请求唯一标识，用于链路追踪与防重复）。
- 指数代码通常使用 6 位交易代码；带后缀代码读取 `sinfoWindcode` / `sInfoWindcode`。
- 批量接口逐项检查 `availabilityStatus`：`有数据` 表示该项正常；其他取值（如 `未找到该指数`、`代码类型不匹配`、`无持仓数据`、`查询失败` 等）表示该项无数据或失败，不影响其他代码的结果，展示时按状态用自然语言说明，不补造数据。
- 指数点位不是基金净值，指数成分股不是某只基金的实际持仓，指数收益也不是跟踪基金的实际收益。

## 能力与数据路径速查

| 接口 | 结果路径 | 主要用途 |
|---|---|---|
| `POST /skill/v2/search/chinaIndex` | `$.data.data[]` | 境内指数关键词搜索与条件筛选 |
| `POST /skill/v2/search/index-by-stock` | `$.data.list[]` | 按成分股反查指数 |
| `POST /skill/v2/index/detail` | `$.data[]{indexCode, detail{}}` | 指数完整画像（批量） |
| `POST /skill/v2/index/holdings` | `$.data[]{fundCode, holdingItems[]}` | 前十大成分股（批量） |
| `POST /skill/v2/index/return` | `$.data[]` | 历史区间收益（批量） |
| `POST /skill/v2/index/valuation` | `$.data[]` | 当前估值与历史分位（批量） |
| `POST /skill/v2/index/financial-indicators` | `$.data[]` | 基本面汇总指标（批量） |
| `GET /skill/v2/quote/index` | `$.data.list[]` | 批量盘口行情（含精确行情时间） |
| `POST /skill/v2/quote/index/kline` | `$.data.candle` + `$.data.<代码>` | 指数历史K线 |
| `POST /skill/v2/quote/minite` | `$.data.dataList[]` | 分时分钟行情（批量） |
| `GET /skill/v2/discovery/hot-search` | `$.data[]` | 热搜关键词 |
| `GET /skill/v2/discovery/hot-search-recommend` | `$.data[]` | 按类型热搜推荐 |

## `POST /skill/v2/search/chinaIndex` — 搜索中国指数

按关键词与复杂条件检索境内指数（regionType 固定 CHINA，只覆盖境内指数），返回含随附行情、表现、估值基本面和跟踪产品的指数列表。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 指数代码、名称或简称 |
| `pageNum` | integer | 否 | 默认1 |
| `pageSize` | integer | 否 | 默认10 |
| `filters` | object | 否 | 复杂筛选条件 |
| `requestId` | string | 否 | 请求唯一标识 |

⚠️ 本接口无 `sortField/sortOrder` 排序参数，排序和比较基于搜索结果在本地完成。

`filters` 支持（数值筛选均为 `{ "min": number, "max": number }`，边界包含，只传需限制的一侧）：

- `productType[]`：产品类型多选（一级-二级-三级，用 `-` 拼接）；
- 表现区间：`pctChg1D/1W/1M/3M/TY/1Y/3Y/5Y`（⚠️ 筛选项无 6M，响应字段里有 `pctChg6M`）；
- 估值：`PETtm/PETtm5Y`、`PBLf/PBLf5Y`、`PSTtm/PSTtm5Y`（倍数及近5年分位）；
- 基本面：`dividendYield`、`ROE`、`operatingRevenueYoy`、`parentComOwnerYoy`；
- 跟踪产品：`trackETFNetInFlow`（元）、`trackETFAmount`（元）、`trackETFCount`（只）、`trackETFScale`（**万元**）、`trackETFLinkedCount`（只）、`trackETFLinkedScale`（**万元**）；
- 年度表现：`lastYearYield`、`prevYearYield`。

分页字段：`$.data.pageNum`、`pageSize`、`totalNum`、`serverTime`。

> **筛选与分页规则**：筛选类条件（表现、估值、基本面、跟踪产品区间）必须优先用 `filters` 参数在服务端完成，禁止靠翻页逐条人工过滤。搜索响应已随附行情（`lastPrice`、`changeRate`）、表现（`pctChg*`）、估值基本面和跟踪产品等字段；筛选、排序和比较必须基于搜索结果在本地完成，不为每只候选重复请求详情。`pageSize` 建议直接取大值一次取回候选；翻页仅为浏览候选，根据 `totalNum` 判断是否还有未覆盖结果，仅当已取页面确实无匹配候选时才翻页，最多翻页 5 页，仍覆盖不全时在回答中说明筛选条件、覆盖范围与排序口径，不得继续扫库。确需详情时，多指数必须用批量接口一次传入全部代码，禁止逐个单查。

`$.data.data[]` 关键字段：

- 标识分类：`trdCode`、`sinfoWindcode`、`indexName`、`indexSht`、`firstClass`、`indexType`、`indexTopType`/`indexBottomType`、`creatIndexOrg`、`regionType`、`realtimeQuoteType`。
- ⚠️ `sinfoWindcodeHighLight`、`indexShtHighLight` 含 HTML 高亮标签，对外展示必须用不带 HighLight 的字段。
- 随附行情：`lastPrice`（点）、`changeRate`（%）。
- 表现：`pctChg1D~Bgn`（含 6M）、`lastYearYield`、`prevYearYield`。
- 估值基本面：`PETtm/PBLf/PSTtm` 及 5Y/Bgn 分位、`ROE`、`dividendYield`、营收与利润增速（`trdDt` 为基本面披露日期）。
- 跟踪产品：`trackETFCount`、`trackETFScale`（元）、`trackETFAmount`（元）、`trackETFNetInFlow`（元）、`trackETFLinkedCount`、`trackETFLinkedScale`（元）。⚠️ 筛选口径与响应单位不一致：`filters.trackETFScale/trackETFLinkedScale` 按**万元**传区间，响应同名字段为**元**。
- 代表产品：`maxScaleFund`、`maxExcessReturnFund`、`minTrackErrorFund`（各自 fundScale 万元）。
- 产品列表：`relatedETF[]`（fundScale 万元）、`relatedOutIndex[]`（fundScale **元**，与详情接口口径一致）。

## `POST /skill/v2/search/index-by-stock` — 按成分股反查指数

根据股票代码列表搜索包含这些股票的指数，返回指数列表及成分股持仓占比。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `stockCodes` | array | 是 | 股票代码列表 |
| `onlyIncludeFullMatch` | string | 否 | `Y` 仅返回同时包含全部输入股票的指数，`N` 包含任意一只 |
| `showOnlyMaxIndexScaleMatch` | string | 否 | 仅显示规模最大的匹配（预留参数，本接口不生效） |
| `sortField` / `sortOrder` | string | 否 | 排序字段 + `desc`/`asc` |
| `type` | string | 否 | 类型 |
| `pageNum` / `pageSize` | integer | 否 | 默认 1 / 10 |

`$.data.list[]`：`sInfoWindcode`、`trdCode`、`indexName`、`indexSht`、`indexType`、`totalRatio`（合计持仓占比 %）、`holdingsDetail[]`。

`holdingsDetail[]`：`stockCode`、`secuSht`、`holdNavRat`（持仓占比 %）。分页信息位于 `$.data.currentPage`、`pageSize`、`totalPage`、`totalCount`；`requestList[]` 用于回显输入股票。

⚠️ 本接口只返回指数列表与成分占比，**不含跟踪产品**。用户还需要跟踪这些指数的 ETF 或场外基金时，必须用返回的指数代码再调 `search/chinaIndex` 或 `index/detail`，从 `relatedETF` / `relatedOutIndex` 读取跟踪产品，保持"股票 → 指数 → 跟踪产品"的层级完整。

## `POST /skill/v2/index/detail` — 批量指数详情

批量查询多个指数的完整画像：分类、编制属性、跟踪产品、代表产品、年化/累计收益、风险指标、市值与行业分布、随附行情。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fundCodes` | array | 是 | ⚠️ 参数名是 `fundCodes`，传的是**指数代码**，最多20个 |
| `requestId` | string | 否 | 请求唯一标识 |

结果：`$.data[]`，每项 `{indexCode, availabilityStatus, detail{}}`；`availabilityStatus` 非"有数据"时 `detail` 为 `null`（键仍存在），用 `.get('detail')` 判空。

`detail{}` 按问题选择字段：

| 类别 | 关键字段 |
|---|---|
| 标识分类 | `trdCode`、`sinfoWindcode`、`indexName`、`indexSht`、`indexType`、`firstClass`/`secondClass`/`thirdClassMarketType`/`thirdClassMarketValue`、`className` |
| 编制属性 | `pubDt`（发布日期）、`baseDt`（基日）、`creatIndexOrg`（编制机构）、`regionType`、`quoteRegionType`、`realtimeQuoteType`（REALTIME 实时 / DAILY 日度 / DELAYED15 延迟15分钟）、`authorizedIndex` |
| 随附行情 | `lastPrice`（点）、`changeRate`（%） |
| 跟踪产品 | `relatedETF[]`（fundScale 万元）、`relatedOutIndex[]`（fundScale 元）、`trackETFCount`、`trackETFScale`（万元）、`trackETFLinkedCount`、`trackETFLinkedScale`（元） |
| 代表产品 | `maxScaleFund`、`maxExcessReturnFund`、`minTrackErrorFund`（fundScale 万元，含 `navPctChg1Y/1D`） |
| 收益 | `annualizedReturn1Y/3Y/5Y/10Y/Bgn`（年化，%）、`pctChg1Y/3Y/5Y/10Y/Bgn`（累计，%）、`lastYearYield`、`prevYearYield` |
| 风险 | `annualizedVol1Y~Bgn`（年化波动率 %）、`volatility1Y~Bgn`（累计波动率 %）、`maxDown1Y~Bgn`（%）、`sharpRatio1Y~Bgn` |
| 市值风格 | `marketCapDistTrdDt`、`largeCapStocks(+Proportion)`、`midCapStocks(+Proportion)`、`smallCapStocks(+Proportion)` |
| 行业分布 | `industryOptions[]`、`industryDistribution[]`：`trdDt`、`industryClassType`、`industryClassTypeName`、`industryLevel`、`industryName`、`industryWeight`（%）、`industryWeightOrder` |

相关基金规模单位：`relatedETF[].fundScale`、`trackETFScale`、代表产品 `fundScale` 为**万元**；`trackETFLinkedScale`、`relatedOutIndex[].fundScale` 为**元**。展示前按字段换算。

以下字段虽然以 `Json` 结尾，实际返回的是数据文件路径字符串，不是内嵌 JSON：

- `eodPriceJson`
- `financialIndicatorJson`
- `valuationPercentileJson`
- `dividendRatioJson`

除非用户明确要求访问链接内容，否则不要继续抓取，也不要直接 `json.loads`。

## `POST /skill/v2/index/holdings` — 批量指数前十大成分股

批量查询多个指数最新（或指定日期）的前十大成分股。

请求体：`fundCodes` 必填（array，传指数代码），最多10个；`date` 可选，格式 `yyyy-MM-dd`，不传返回最新；`requestId` 可选。

`$.data[]`（按指数分组，每只指数一项）：

| 字段 | 说明 |
|---|---|
| `fundCode` | 指数代码 |
| `availabilityStatus` | 数据可用性状态（`有数据` / `未找到该指数` / `代码类型不匹配` / `无持仓数据` / `查询失败`） |
| `holdingItems[]` | 成分股明细列表 |

`holdingItems[]`：`stockCode`（股票代码）、`secuSht`（股票简称）、`holdNavRat`（权重，占净值比例 %）。

## `POST /skill/v2/index/return` — 批量指数区间收益

批量查询多个指数在预设周期或自定义区间内的区间收益率，逐只返回实际起止日期。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `codes` | array | 是 | 指数代码列表，最多10个 |
| `timeMode` | string | 是 | `PERIOD`（预设周期）或 `RANGE`（自定义区间） |
| `period` | string | PERIOD时 | `1D/1W/1M/3M/6M/1Y` |
| `startDate`/`endDate` | string | RANGE时 | `yyyy-MM-dd` |
| `boundaryMatchMode` | string | 否 | 仅 RANGE 生效：`FLEXIBLE`（默认，允许边界收缩到最近可交易日）或 `STRICT`（必须为交易日） |

`$.data[]`：`trdCode`、`startDate`、`endDate`（实际起止日期）、`availabilityStatus`、`returnRate`（区间收益率 %）。

> ⚠️ **returnRate 缺失值处理**：`availabilityStatus≠有数据`（如 `API接口无数据`、`历史查询无数据`、`不支持的期间` 等）时不得把收益率当作 0，用 `.get('returnRate')` 取值；展示实际起止日期，状态异常时用自然语言说明，不补造收益率。
>
> ⚠️ **STRICT 模式钳制**：`boundaryMatchMode=STRICT` 时，起止日期会被钳制到可得数据范围，不报错；展示时以返回的 `startDate`/`endDate` 为准。

## `POST /skill/v2/index/valuation` — 批量指数估值

批量查询多个指数的最新估值倍数及历史分位。

请求体：`indexCodes` 必填（array），最多10个；`requestId` 可选。

`$.data[]`：

- `trdCode`、`trdDt`（指标更新日期）；
- 当前倍数（倍）：`pETtm`、`pBLf`、`pSTtm`、`pCFTtm`；
- 历史分位（%）：对应字段后缀 `3M/6M/1Y/2Y/3Y/5Y/10Y/TY/Bgn`；⚠️ `pCFTtm` 的分位无 `6M` 与 `TY`。

API 响应使用小写前缀 `pETtm/pBLf/pSTtm/pCFTtm`，与搜索接口 `PETtm/PBLf/PSTtm` 大小写不同。当前倍数与百分位不可混淆。

## `POST /skill/v2/index/financial-indicators` — 批量指数基本面指标

批量查询多个指数的基本面汇总指标（成分股汇总口径，不是单家公司的财务数据）。

请求体：`indexCodes` 必填（array），最多10个；`requestId` 可选。

`$.data[]`：

| 字段 | 单位/含义 |
|---|---|
| `trdCode`、`trdDt` | 指数代码、数据更新日期 |
| `rOE` | 净资产收益率（%） |
| `dividendYield` | 股息率（%） |
| `operatingRevenueYoy` | 营收同比增速（%） |
| `parentComOwnerYoy` | 归母净利润同比增速（%） |
| `operatingIncome` | 营业收入（元） |
| `parentComOwners` | 归母净利润（元） |

## `GET /skill/v2/quote/index` — 批量指数盘口行情

批量获取多个指数的实时盘口快照，含精确行情时间。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbols` | string | 是 | 指数代码，英文逗号分隔（query 参数），单次最多50个 |

`$.data.list[]`（每个指数一项）：

- `symbol`、`lastPrice`（点）、`changeValue`（点）、`changeRate`（%）、`yesterdayClosePrice`（点）、`dealVolume`（份）、`dealBalance`（元）、`turnoverRatio`（%）。
- 精确行情时间：`date`（yyyyMMdd）+ `timeStamp`（HHmmss）。

`$.data.serverTime` 为服务器时间。盘前时段（9:10-9:30）指数涨跌幅显示为 0.00%。响应中的 `iopv`、`deviationRate` 对指数无实际意义，不要展示为有效指数指标；指数没有溢折率，不得补造。

> **调用前检查**：`search/chinaIndex` 与 `index/detail` 的响应已随附 `lastPrice`（点）和 `changeRate`（%）。已通过它们获得问题所需的最新点位或涨跌幅时，**禁止**再调本接口获取相同信息。只有需要本接口独有字段时才调用：`changeValue`、`yesterdayClosePrice`、`dealVolume`/`dealBalance`、精确行情时间（`date + timeStamp`）。
>
> **应当使用本接口的情形**：用户以"现在/实时/盘中"口径询问点位、要求精确到秒的行情时间，或明确提出批量刷新行情时，直接使用本接口——随附行情字段不含 `date + timeStamp`，用随附字段回答实时口径问题属于口径不达标。

## `POST /skill/v2/quote/index/kline` — 指数历史K线

查询单只指数的历史K线（日K/周K/月K/分钟K）。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `symbol` | string | 是 | 指数代码 |
| `candlePeriod` | string | 是 | `DAY` / `WEEK` / `MONTH` / `MINUTE_1` / `MINUTE_5` / `MINUTE_15` |
| `dateRange` | string | 是 | 日期范围，格式 `yyyyMMdd~yyyyMMdd` |
| `needFillKLine` | integer | 否 | 是否补全K线：0 不补（默认）、1 补全 |

查询范围限制：日K最多500天，周K/月K最多10年，分钟K最多7天，超出返回错误提示。境外指数（含MSCI指数）不支持K线查询，用户询问境外指数K线时如实说明。

响应：`$.data.candle` 为列名数组，固定为 `date`（yyyyMMdd）、`min_time`（分钟时间，日K中为 0）、`open_px`、`high_px`、`low_px`、`close_px`、`deal_volume`（成交量，份）、`deal_amount`（成交额，**万元**）；`$.data.<指数代码>` 为K线二维数组，每行按 `candle` 列名顺序对齐。

## `POST /skill/v2/quote/minite` — 分时分钟行情

批量获取指数（或ETF）当日分时分钟数据与最新行情快照。

请求体：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `fundCodeList` | array | 是 | 标的代码列表，最多50个 |
| `date` | string | 否 | 行情日期 `yyyyMMdd`，默认当天 |
| `lastTimestamp` | integer | 否 | 上次获取的最后时间戳：>0 走增量更新（仅返回增量分钟数据），=0 或不传走全量 |

`$.data.dataList[]`：`symbol`、`quoteList[]`（分钟序列：`minute` 分钟时间戳，如 930 表示 9:30；`lastPrice` 点；`changeRate` %；`iopv` 对指数无意义）、`latestQuote{}`（最新行情快照，字段同盘口接口的 `$.data.list[]` 项，含 `date + timeStamp`）。`$.data.serverTime` 为服务器时间。

## `GET /skill/v2/discovery/hot-search` — 热搜关键词

查询近期热搜关键词排行，按搜索次数降序，默认返回前20条。无参数。

`$.data[]`：`keyword`（热搜关键词）。返回结果仅为关键词列表，不含指数/基金详细信息。

## `GET /skill/v2/discovery/hot-search-recommend` — 按类型热搜推荐

按产品类别返回热搜推荐列表。

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | string | 是 | 产品类别：`index`（指数）/ `etf`（ETF）/ `out-index`（场外基金），本技能用 `index` |

`$.data[]`：`code`（产品代码）、`name`（产品名称）、`navPctChg1Y`（近一年涨跌幅 %，仅场外基金类型返回，其他类型为空）。

## 时间、单位与解释

- 行情数据时间：每条行情的 `date + timeStamp`；`serverTime` 只是服务器时间。实时口径回答以 `quote/index` 或 `quote/minite` 的精确行情时间为准。
- 非交易时段表述为"接口返回的最新一笔行情"；盘前（9:10-9:30）涨跌幅显示 0.00%。
- 点位、涨跌额使用"点"；收益率、涨跌幅、权重、估值分位和基本面比例使用"%"。
- 估值倍数使用"倍"；金额按接口字段的元、万元口径换算（见各接口标注）。
- 低历史分位只说明当前指标在自身历史中的位置，不等价于投资建议或未来回报判断。
