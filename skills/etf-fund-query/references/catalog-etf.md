# ETF信息查询 — 接口字段权威参考

> 编写脚本前必读：数据路径、字段名、单位均以本文件为准。
>
> 说明：
> - 本文所有路径都是 JSON 路径。
> - `$` 表示返回 JSON 的根节点。
> - 默认按 catalog 中的路径取值；只有路径失败、字段缺失或结构可疑时，才先查看真实响应结构再继续。
> - 如果按 catalog 取值失败，不要跨接口猜路径。必须先请求该接口，检查根节点有哪些 key、`data` 是对象/数组/空值，以及列表真实位于哪一层。

---

## 公共请求头

所有接口请求均需携带以下请求头：

```
# 认证格式：Authorization: Bearer <API_KEY>
# 请求来源标识：X-Caller-Type: external
```

**统一约定**：

- 所有 POST 接口均带可选公共参数 `requestId`（string，请求唯一标识，用于避免重复请求和链路追踪），下文参数表不再逐接口重复列出。
- 所有接口响应外层信封一致：`$.success`（boolean）、`$.code`（integer，0 表示成功）、`$.message`、`$.data`、`$.requestId`、`$.timestamp`（毫秒）。下文只描述 `$.data` 及以内结构。

---

## `POST /skill/v2/search/etf` — ETF关键词搜索

按关键词模糊搜索 ETF（支持产品名称、代码片段），返回匹配 ETF 列表及随附行情、规模、各周期涨跌幅、估值等比较字段。适用于用户未提供具体代码时的检索。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 搜索关键词，支持 ETF 产品名称、代码等模糊搜索 |
| page | integer | 否 | 页码，从 1 开始，默认 1 |
| pageSize | integer | 否 | 每页条数，建议 10-100，默认 10 |

**最终数据路径**：`$.data.data[]`（平铺 ETF 列表，⚠️ 不是 `$.data.list[]`）

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | ETF交易代码，6位数字 |
| fundName / extdSecuSht | string | ETF产品全称 / 产品简称 |
| indexCode / indexName / indexType | string | 跟踪指数代码（不带后缀）、名称、类型 |
| fundScale | number | ETF规模（**元**，÷1e8=亿） |
| lastPrice / changeRate | number | 最新价（元）、实时涨跌幅（%）【随附行情，可直接使用】 |
| premiumRate | number | 实时折溢价率（%）【随附行情】 |
| dealBalance / turnoverRate | number | 实时成交额（元）、实时换手率（%）【随附行情】 |
| eodPctChg1D/1W/1M/3M/TY/1Y/3Y/5Y | number | 各周期涨跌幅（%） |
| avgAmount1W/1M/3M/TY/1Y | number | 各周期日均成交额（元） |
| netInflow1D/1W/1M/3M/TY/1Y | number | 各周期净流入（元） |
| excessReturn1Y | number | 近1年超额收益（%） |
| annTrackError1Y | number | 近1年跟踪误差（年化，%） |
| unitAccBonus / accBonusCount / currBonusDt | | 单位累计分红（元）、累计分红次数、最近一次分红权益登记日 |
| dividendYield | number | 跟踪指数股息率（%） |
| PETtm/PETtm5Y、PBLf/PBLf5Y、PSTtm/PSTtm5Y | number | 估值（倍）与近5年分位（%）⚠️ 注意大小写 |
| fundManageComp | string | 基金管理人 |
| fundManagerCurrent | array | 基金经理信息（managerName、startDate） |
| establishDt / lstDt | string | 成立日、上市日，yyyy-MM-dd |
| mgtFee / trstFee | number | 管理费、托管费（%） |
| relatedFunds | array | 联接基金列表（trdCode、relatedTrdCode、relatedFundSht） |

**分页信息路径**：`$.data.totalNum`、`$.data.pageNum`、`$.data.pageSize`；`$.data.serverTime` 为服务器时间。

> **分页规则**：`pageSize` 取大值一次取回候选，以 `totalNum` 为界，仅当前几页确实无匹配时才翻页，最多翻页 5 页，仍覆盖不全时在回答中说明筛选条件、覆盖范围与排序口径，不得继续扫库；多产品详情用批量接口一次传入全部代码，禁止逐个单查。

---

## `POST /skill/v2/search/etf-by-stock` — 按股票反查ETF

根据股票代码列表搜索持有这些股票的 ETF，返回 ETF 列表及持仓占比、规模、跟踪指数等信息。适用于「哪些 ETF 重仓了某只股票」类问题。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| stockCodes | array | 是 | 股票代码列表（6位数字，不带交易所后缀），如 ["600519","000858"] |
| onlyIncludeFullMatch | string | 否 | Y=仅返回同时持有全部输入股票的ETF，N=任意包含（默认） |
| sortField | string | 否 | 排序字段 |
| sortOrder | string | 否 | desc（降序）/ asc（升序） |
| pageNum / pageSize | integer | 否 | 页码/每页条数，默认 1/10 |

**最终数据路径**：`$.data.list[]`；分页信息在 `$.data.currentPage`、`totalPage`、`totalCount`。

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode / fundName / extdSecuSht | string | ETF代码、名称、简称 |
| indexCode / indexName / indexSht / firstClass / secondClass | string | 跟踪指数与分类 |
| totalRatio | number | 查询股票的持仓合计比例（%） |
| holdings | array | 该ETF实际持有的输入股票代码列表 |
| holdingsDetail | array | 查询股票在该ETF中的持仓明细（`stockCode`、`secuSht`、`holdNavRat`、`endDt` 报告期）；用户要"具体持仓明细"时读取本字段 |
| fundScale | number | 资产规模（**元**，÷1e8=亿） |
| unitNav / navPctChg1D / eodPctChg1M / eodPctChgTM | number | 净值与涨跌幅（%） |
| pubDt / exchName | string | 数据更新日期、上市场所 |
| maxScaleFlag | boolean | 是否相同跟踪指数中规模最大 |

辅助回显：`$.data.matchedStocks[]`（匹配到的股票 key/label）、`$.data.requestList[]`（请求股票回显）。

**降级策略**：`onlyIncludeFullMatch:"Y"` 返回空时改 `"N"` 重试，并告知用户条件已放宽。

---

## `POST /skill/v2/etf/detail` — 批量ETF详情

批量查询多只 ETF 的详细信息：基本信息、费率、跟踪指数、净值、各周期涨跌幅、成交额/净流入、跟踪误差与超额、夏普比率、最大回撤、基金经理、联接基金及随附实时行情。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | ETF基金代码列表，最多 20 个 |

**最终数据路径**：`$.data[]`（数组，每个元素对应一只 ETF）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码 |
| availabilityStatus | string | 数据可用性状态：有数据 / 未找到该基金 / 代码类型不匹配 / 查询失败。单只失败不影响其他只；为有数据时才返回 `detail` |
| detail | object | ETF详情（字段见下表） |

`$.data[].detail` 内字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode / capitalType | string | 交易代码、基金类型 |
| fundName / chiName / extdSecuSht | string | 基金名称（产品名）/ 全称 / 扩位简称（ETF对外展示名优先使用 extdSecuSht） |
| indexCode / indexName / indexSht / indexType | string | 跟踪指数 |
| firstClass / secondClass / thirdClassMarketType / thirdClassMarketValue / className | string | 指数分类 |
| establishDt / lstDt / exchName | string | 成立日、上市日、上市场所 |
| mgtFee / trstFee | number | 管理费、托管费（%） |
| fundManageComp / fundManageSht / fundCustComp | string | 基金管理人全称/简称、托管人 |
| fundStatus / pubDt | string | 基金状态、数据更新日期 |
| fundScale | number | 产品规模（**元**，÷1e8=亿） |
| unitNav / accuUnitNav / navPctChg1D | number | 单位净值、累计单位净值（元）、当日净值涨跌幅（%） |
| lastPrice / changeRate / turnoverRate / iopvDiscount | number | 最新价（元）、实时涨跌幅（%）、换手率（%）、IOPV折价率（%）【随附行情】 |
| eodPctChg1D/1W/1M/3M/6M/1Y/3Y/5Y/TY/Bgn | number | 各周期收盘涨跌幅（%） |
| navPctChg1W/1M/3M/6M/1Y/3Y/5Y/10Y/TY/Bgn | number | 各周期复权净值收益率（%） |
| amount1W~5Y、avgAmount1W~5Y | number | 各周期成交额、日均成交额（元） |
| netInflow1D/1W/1M/3M/6M/TY/1Y/3Y/5Y | number | 各周期净流入（**元**） |
| annTrackError1Y / trackErrorLst | number | 近1年年化跟踪误差、上市至今跟踪误差（%） |
| excessReturn1Y / excessReturnLst | number | 近1年、上市至今超额收益（%） |
| sharpRatio1M~Bgn | number | 夏普比率（1M/3M/6M/1Y/3Y/5Y/10Y/TY/Bgn） |
| maxDown1M~Bgn | number | 最大回撤（%，1M/3M/6M/1Y/3Y/5Y/10Y/TY/Bgn） |
| avgTurnoverRate1M | number | 近1月日均换手率（%） |
| unitAccBonus / accBonusCount / currBonusDt | | 分红信息 |
| netInflows | array | 申赎净流入（近5日）：trdDt、netInflow1D（元） |
| fundManagerCurrent / fundManagerFormer | array | 现任/历任基金经理（psnCode、psnName、posiBgnDt、posiEndDt、managementTime、manageStatus 1在职/0离任、performance 任期业绩%） |
| relatedFunds | array | 联接基金（trdCode、relatedTrdCode、relatedFundSht） |

> - `fundNavJson`、`benchmarkReturnJson` 是数据文件路径，不当作内嵌 JSON 解析。
> - 跟踪误差统一使用 `annTrackError1Y`。

---

## `POST /skill/v2/etf/holdings` — 批量ETF前十大持仓

批量查询多只 ETF 的最新（或指定日期）前十大重仓股。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | ETF代码列表，最多 10 个 |
| date | string | 否 | 持仓日期 yyyy-MM-dd，不传返回最新报告期 |

**最终数据路径**：`$.data[]`（按基金分组）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码 |
| availabilityStatus | string | 有数据 / 未找到该基金 / 代码类型不匹配 / 无持仓数据 / 查询失败。单只失败不影响其他只；为有数据时才返回 `holdingItems` |
| holdingItems | array | 持仓明细列表 |

`holdingItems[]` 内字段：`trdCode`、`endDt`（报告期截止日期 yyyy-MM-dd）、`stockCode`、`secuSht`（股票简称）、`holdNavRat`（占净值比例 %）、`sinfoWindcode`、`stockWindcode`。

---

## `POST /skill/v2/etf/return` — 批量ETF区间收益

批量查询多只 ETF 在预设周期或自定义区间内的收益率（%）。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | array | 是 | ETF代码数组，最多 10 只 |
| timeMode | string | 是 | PERIOD（预设周期）或 RANGE（自定义区间） |
| period | string | PERIOD时必填 | 1D/1W/1M/3M/6M/1Y |
| startDate | string | RANGE时必填 | yyyy-MM-dd |
| endDate | string | RANGE时必填 | yyyy-MM-dd |
| boundaryMatchMode | string | 否 | 仅 RANGE 生效：FLEXIBLE（默认，允许边界收缩到最近可交易日）/ STRICT（严格，起止必须为交易日，数据不足不收缩） |

**最终数据路径**：`$.data[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | ETF代码 |
| indexCode | string | 与 trdCode 相同的代码本身；RANGE 模式下可能为 null |
| startDate / endDate | string | 实际区间起止日期，yyyy-MM-dd |
| returnRate | number | 区间收益率（%，保留2位小数）⚠️ 见下方说明 |
| availabilityStatus | string | 有数据 / API接口无数据 / 历史查询无数据 / 不支持的期间 / API调用异常 / 系统异常 |
| serverTime | string | 服务器时间，yyyy-MM-dd HH:mm:ss |

> ⚠️ **returnRate 空值处理**：availabilityStatus≠有数据 时，`returnRate` 为 null，必须用 `.get('returnRate')` 取值，不得把空值当作 0。历史不足时状态为"历史查询无数据"，用自然语言说明，不补造收益率。
>
> ⚠️ 展示时以返回的 `startDate`/`endDate` 为准（FLEXIBLE 模式下边界可能收缩到最近可交易日）。

---

## `POST /skill/v2/etf/dividends` — 批量ETF分红明细

批量查询多只 ETF 的历史分红明细，按分红时间倒序。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | ETF代码数组，最多 10 只 |
| startDate | string | 否 | 查询开始日期 yyyy-MM-dd，不传从最早记录 |
| endDate | string | 否 | 查询结束日期 yyyy-MM-dd，不传到最新记录 |

**最终数据路径**：`$.data[]`（按基金分组）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码 |
| availabilityStatus | string | 有数据 / 无历史分红 / 未找到该基金 / 代码类型不匹配 / 查询失败。单只失败不影响其他只 |
| dividendItems | array | 分红明细列表（按时间倒序，无数据时为 null） |

`dividendItems[]` 内字段：`trdCode`、`eqyRecordDt`（权益登记日）、`dvdBenDt`（分红计算基准日）、`cashDvdPerShTax`（每份分红金额，元）、`payDt`（红利发放日-场内）、`divPayDt`（红利发放日-场外），日期均为 yyyy-MM-dd。

---

## `POST /skill/v2/etf/etf-scale` — 批量ETF规模变动

批量查询多只 ETF 的规模与净流入变动（数据 T+1 延迟）。适用于「某 ETF 最新规模」「近一个月净流入情况」类问题。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trdCodes | array | 是 | 基金代码列表，最多 20 个 |
| beginDate | string | 否 | 查询开始日期 yyyy-MM-dd，不传则返回每只基金最新一天数据 |
| endDate | string | 否 | 查询结束日期 yyyy-MM-dd，与 beginDate 配合使用 |

**最终数据路径**：`$.data[]`（按基金分组）

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode / fundName | string | 基金代码、简称 |
| availabilityStatus | string | 有数据 / 未找到该基金 / 查询失败。单只失败不影响其他只 |
| scaleChanges | array | 规模变动列表（按日期倒序） |

`scaleChanges[]` 内字段：`trdCode`、`trdDt`（日期 yyyy-MM-dd）、`nscale`（规模，**万元**，÷1e4=亿）、`nnetInflow`（净流入，**万元**）、`sreferDate`（参考日期）。⚠️ 字段名为小写形式，不要按驼峰拼写取值。

> ⚠️ 本接口规模/净流入单位为**万元**，与其他接口的元口径不同；数据存在 T+1 延迟，"今日规模"类问题应答最新可得日期。

---

## `GET /skill/v2/quote/etf` — 批量ETF盘口行情

批量获取多个 ETF 的实时盘口行情。

> **调用前检查**：`search/etf`、`etf/detail`、`discovery/top-etf` 的响应已随附 `lastPrice`、`changeRate` 等行情字段。已通过它们获得问题所需的最新价或涨跌幅时，**禁止**再调本接口获取相同信息。只有需要批量刷新行情，或需要成交额、IOPV、溢折率、精确行情时间等随附字段未覆盖的口径时才调用。

**请求参数**（URL query）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbols | string | 是 | ETF代码，英文逗号分隔，单次最多 50 个 |

**最终数据路径**：`$.data.list[]`（`$.data.serverTime` 为服务器时间）

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | ETF代码 |
| lastPrice | number | 最新价（元） |
| changeRate / changeValue | number | 涨跌幅（%）、涨跌值（元） |
| yesterdayClosePrice | number | 昨收（元） |
| dealBalance / dealVolume | number | 成交额（元）、成交量（份） |
| turnoverRatio | number | 换手率（%） |
| iopv / deviationRate | number | IOPV 实时估值（元）、溢折率（%） |
| date | integer | 行情日期，yyyyMMdd |
| timeStamp | integer | 行情时间，HHmmss |

> 无行情时返回仅含 `symbol` 的空对象（空值兜底），不得当作 0 展示。

---

## `POST /skill/v2/quote/etf/kline` — ETF历史K线

查询 ETF 历史 K 线（日K/周K/月K/分钟K），支持原始/前复权/后复权。适用于「近一年日K线」「周K走势」类问题。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | 是 | ETF代码（单只） |
| candlePeriod | string | 是 | DAY（日K）/ WEEK（周K）/ MONTH（月K）/ MINUTE_1 / MINUTE_5 / MINUTE_15 |
| dateRange | string | 是 | 查询日期范围，格式 yyyyMMdd~yyyyMMdd，如 20260101~20260501 |
| candleModel | string | 否 | 复权模式：ORIGINAL（原始，默认）/ FORWARD（前复权）/ BACKWARD（后复权） |
| needFillKLine | integer | 否 | 是否补全K线：0=不补（默认）、1=补全 |

**查询范围限制**：日K 最多 500 天，周K/月K 最多 10 年，分钟K 最多 7 天，超出返回错误提示。

**最终数据路径**：`$.data.candle`（列名数组）+ `$.data.<代码>`（如 `$.data.510300`，与列名逐列对齐的二维数组）

> 列名以返回的 `data.candle` 为准，固定为 `["date", "min_time", "open_px", "high_px", "low_px", "close_px", "deal_volume", "deal_amount"]`：`date` 为交易日（yyyyMMdd 整数）；`min_time` 为分钟时间（HHmm 整数，日K/周K/月K 为 0，分钟K 如 935 表示 9:35）；`open_px`/`high_px`/`low_px`/`close_px` 为开高低收（元）；`deal_volume` 成交量（份）、`deal_amount` 成交额（元）。解析时按下标与列名逐列对齐。

---

## `POST /skill/v2/quote/minite` — 批量分时分钟行情

批量获取 ETF/指数当日分时分钟行情及最新盘口快照，支持增量更新。适用于「今日盘中走势」类问题。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodeList | array | 是 | 标的代码列表，最多 50 个 |
| date | string | 否 | 行情日期 yyyyMMdd，默认当天 |
| lastTimestamp | integer | 否 | 0 获取全量；>0 仅获取该时间戳之后的新增分钟 |

**最终数据路径**：`$.data.dataList[]`（`$.data.serverTime` 为服务器时间）

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 标的代码 |
| latestQuote | object | 最新盘口快照：lastPrice、changeRate、changeValue、dealBalance（元）、dealVolume（份）、turnoverRatio（%）、iopv（元）、deviationRate（%）、yesterdayClosePrice（元）、date（yyyyMMdd）、timeStamp（HHmmss） |
| quoteList | array | 分钟序列 |

`quoteList[]` 内字段：`minute`（integer，分钟时间戳，如 930 表示 9:30）、`lastPrice`、`iopv`、`changeRate`。

---

## `GET /skill/v2/discovery/top-etf` — 涨幅前10 ETF

查询当前涨幅排名前 10 的 ETF 榜单（按跟踪指数去重）。适用于「今日涨幅居前的 ETF 有哪些」类问题。

**无请求参数**

**最终数据路径**：`$.data.list[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode / fundName | string | ETF代码、名称 |
| indexCode / indexName | string | 跟踪指数 |
| lastPrice | number | 最新价（元） |
| changeRate | number | 涨跌幅（%） |

> 该接口为服务端涨幅榜来源，不要用少量行情样本自行重建榜单。

---

## `GET /skill/v2/discovery/hot-search` — 热搜关键词

查询近期热搜关键词排行（按搜索次数降序），用于了解用户近期关注热点。

**无请求参数**

**最终数据路径**：`$.data[]`（前 20 条）

| 字段 | 类型 | 说明 |
|------|------|------|
| keyword | string | 热搜关键词 |

> 返回结果为纯关键词列表，不含指数/基金详细信息；命中热点需进一步查询时用对应搜索接口。

---

## `GET /skill/v2/discovery/hot-search-recommend` — 按类型热搜推荐

按产品类别返回热搜推荐列表，可用于热门推荐展示。

**请求参数**（URL query）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 产品类别：index（指数）/ etf（ETF）/ out-index（场外基金） |

**最终数据路径**：`$.data[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 产品编码 |
| name | string | 产品名称 |
| navPctChg1Y | number | 近一年涨跌幅（%，仅 out-index 类型返回，其他类型为空） |

---

## 单位速查

| 字段 | 接口 | 单位 | 换算 |
|------|------|------|------|
| fundScale | search/etf、etf/detail、quote 相关 | 元 | ÷1e8=亿 |
| fundScale | search/etf-by-stock | 元 | ÷1e8=亿 |
| nscale / nnetInflow | etf/etf-scale | **万元** | ÷1e4=亿 ⚠️ |
| netInflow* / avgAmount* / amount* / dealBalance | 其余全部接口 | 元 | ÷1e8=亿 |
| holdNavRat | etf/holdings、etf-by-stock | % | 直接展示 |
| cashDvdPerShTax | etf/dividends | 元/份 | 直接展示 |
| annTrackError1Y / 各涨跌幅 / returnRate | 全部接口 | % | 直接展示 |

## 名称字段使用规则

| 接口 | 对外展示名 | 说明 |
|------|------------|------|
| etf/detail | `detail.extdSecuSht` | detail 的 `fundName` 是产品名，`extdSecuSht` 是扩位简称 |
| search/etf | `extdSecuSht` 或 `fundName` | 列表简称优先 `extdSecuSht` |
| search/etf-by-stock | `extdSecuSht` | 基金简称 |
| discovery/top-etf | `fundName` | 榜单直接返回展示名 |

## 代码格式速查

| 场景 | 正确格式 | 常见错误 |
|------|----------|----------|
| ETF代码入参 | `510300`（6位数字） | `510300.SH`、`510300.SZ` |
| 批量代码（GET query） | `symbols=510300,510500`（逗号分隔字符串） | JSON数组 `["510300"]` |
| 批量代码（POST body） | `["510300", "510500"]` | 带交易所后缀 |
| K线日期范围 | `dateRange=20260101~20260501`（yyyyMMdd~yyyyMMdd） | `2026-01-01` 带连字符 |
| 分时/业务日期 | 接口参数为 yyyy-MM-dd 或 yyyyMMdd，逐接口核对本文件 | 两种格式混用 |

## 数据路径速查

| 接口 | 结果路径 | 常见错误 |
|------|---------|---------|
| search/etf | `$.data.data[]` | 误用 `$.data.list[]`；分页在 `$.data.totalNum` |
| search/etf-by-stock | `$.data.list[]` | fundScale 单位是元，÷1e8=亿 |
| etf/detail | `$.data[].detail`，如 `$.data[0].detail.unitNav` | 忘记先检查 `availabilityStatus` |
| etf/holdings | `$.data[].holdingItems[]` | 已按 fundCode 分组，无需再本地分组 |
| etf/return | `$.data[]` | status≠有数据时 returnRate 为 null，需用 `.get('returnRate')` |
| etf/dividends | `$.data[].dividendItems[]` | 无数据时 dividendItems 为 null |
| etf/etf-scale | `$.data[].scaleChanges[]` | 单位是万元；数据 T+1 延迟 |
| quote/etf | `$.data.list[]` | 无行情时元素仅含 symbol，勿当 0 |
| quote/etf/kline | `$.data.candle` + `$.data.<代码>` | 二维数组需按 candle 列名对齐解析 |
| quote/minite | `$.data.dataList[].quoteList[]`、`.latestQuote` | minute 是 HHmm 整数（930=9:30） |
| discovery/top-etf | `$.data.list[]` | 误用 `$.data[]` |
| discovery/hot-search(-recommend) | `$.data[]` | 无分页参数 |

## 行情字段归一

- 随附行情（search/etf、etf/detail、discovery/top-etf）：`lastPrice`、`changeRate`（detail 另有 `turnoverRate`、`iopvDiscount`；search/etf 另有 `premiumRate`、`dealBalance`、`turnoverRate`）——不含精确行情时间。
- 批量盘口（quote/etf）：完整盘口（含 `iopv`、`deviationRate`、`yesterdayClosePrice`、`changeValue`）+ `date + timeStamp` 精确行情时间。
- 分时分钟（quote/minite 的 latestQuote）：字段同批量盘口，另含分钟序列 `quoteList[]`。
- 回答"现在/实时/盘中"口径问题必须注明行情时间（`date + timeStamp`）；非交易时段表述为"接口返回的最新一笔行情"。
