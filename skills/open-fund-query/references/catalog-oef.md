# 场外基金信息查询 — 接口字段权威参考

> 编写脚本前必读：数据路径、字段名、单位均以本文件为准。
>
> 说明：
> - 本文所有路径都是 JSON 路径。
> - `$` 表示返回 JSON 的根节点。
> - 所有接口响应外层结构统一为 `{success, code, message, data, requestId, timestamp}`：`success` 为调用成功标识，`code=0` 表示成功，`message` 为结果描述，`requestId` 为服务端生成的链路追踪 ID，`timestamp` 为响应时间戳（毫秒）。业务数据一律从 `data` 节点开始取值。
> - 默认按 catalog 中的路径取值；只有路径失败、字段缺失或结构可疑时，才先查看真实响应结构再继续。
> - 如果按 catalog 取值失败，不要跨接口猜路径。必须先请求该接口，检查根节点有哪些 key、`data` 是对象/数组/空值，以及列表真实位于哪一层。

---

## 公共请求头

所有接口请求均需携带以下请求头：

```
# 认证格式：Authorization: Bearer <API_KEY>
# 请求来源标识：X-Caller-Type: external
```

所有 POST 接口均支持可选公共参数 `requestId`（string，请求唯一标识，用于避免重复请求和请求追踪），下文各接口参数表不再重复列出。

---

## `POST /skill/v2/search/oef` — 关键词搜索场外基金

根据关键词模糊搜索场外指数基金（支持产品名称、代码等），返回匹配的场外基金列表，含净值、各周期涨跌幅、估值、跟踪指数、基金经理、费率、相关ETF、最大回撤等信息。适用于用户未提供具体代码、只知道名称或代码片段时的检索。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 否 | 搜索关键词，支持场外基金产品名称、代码等模糊搜索 |
| page | integer | 否 | 页码，从1开始，默认1 ⚠️ 注意是 `page` 不是 `pageNum` |
| pageSize | integer | 否 | 每页条数，建议10-100，默认10 |

> 本接口仅支持关键词与分页，无筛选（filters）、无排序参数；筛选、排序和比较基于搜索结果在本地完成。

**最终数据路径**：`$.data.data[]`（⚠️ 不是 `$.data.list[]`）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 场外基金代码，6位数字 |
| fundName | string | 产品名称（全称） |
| fundSht | string | 产品简称 |
| indexCode / indexName / indexType | string | 跟踪指数 |
| pubDt | string | 净值数据发布日期，yyyy-MM-dd |
| unitNav | number | 单位净值（元） |
| fundScale | number | 基金规模（**元**，÷1e8=亿） |
| navPctChg1D | number | 日涨跌幅（%） |
| eodPctChg1W/1M/3M/TY/1Y/3Y/5Y | number | 各周期涨跌幅（%） |
| annTrackError1Y | number | 近一年跟踪误差（%） |
| excessReturn1Y | number | 近1年超额收益（%） |
| maxDown1W/1M/3M/6M/1Y/3Y/5Y/10Y/TY/Bgn | number | 各周期最大回撤（%） |
| unitAccBonus / accBonusCount / currBonusDt | | 分红信息（单位累计分红 元 / 累计次数 / 最近权益登记日） |
| dividendYield | number | 指数股息率（%） |
| PETtm/PETtm5Y、PBLf/PBLf5Y、PSTtm/PSTtm5Y | number | 估值与近5年分位 ⚠️ 注意大小写 |
| fundManageComp | string | 基金管理人 |
| fundManagerCurrent | array | 基金经理信息（managerName/startDate） |
| establishDt | string | 成立日，yyyy-MM-dd |
| mgtFee / trstFee / salesServiceFee | number | 管理费、托管费、销售服务费（%） |
| relatedETF | array | 相关ETF产品信息（fundCode/relatedETFCode/relatedETFSht） |

**分页信息路径**：`$.data.totalNum`、`$.data.pageNum`、`$.data.pageSize`；另有 `$.data.serverTime`（服务器时间，yyyy-MM-dd HH:mm:ss）。

> **分页规则**：`pageSize` 取大值一次取回候选，以 `totalNum` 为界，仅当前几页确实无匹配时才翻页，最多翻页 5 页，仍覆盖不全时在回答中说明筛选条件、覆盖范围与排序口径，不得继续扫库；搜索响应已随附净值、规模、各周期收益、跟踪误差等比较字段，不为每只候选重复请求详情；多产品详情用批量接口一次传入全部代码，禁止逐个单查。

---

## `POST /skill/v2/oef/detail` — 批量场外基金详情

批量查询多只场外指数基金的详细信息：代码/名称/全称、成立日、费率、管理人/托管人、业绩比较基准、跟踪指数与分类、净值（元）、各周期涨跌幅（%）、近1年超额收益与跟踪误差（%）、报告日期与产品规模（元）、现任及历任基金经理、相关ETF/相关份额、全周期最大回撤（%）、风险等级等。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | 场外基金代码列表，最多10个 |

**最终数据路径**：`$.data[]`（数组，每项一只基金）

`$.data[]` 每项外层字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码 |
| availabilityStatus | string | 数据可用性状态：有数据 / 未找到该基金 / 代码类型不匹配 / 查询失败。单只基金无数据或失败时标记原因，不影响其他基金 |
| detail | object | 基金详情，availabilityStatus=有数据 时返回 |

`detail{}` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | 交易代码 |
| fundName | string | 基金名称（对外展示优先使用） |
| chiName | string | 基金全称（法律全称） |
| establishDt | string | 成立日，yyyy-MM-dd |
| mgtFee / trstFee / saleServiceFee | number | 管理费、托管费、销售服务费（%） |
| fundManageComp / fundManageSht | string | 基金管理人全称/简称 |
| fundCustComp / fundCustCompSht | string | 基金托管人全称/简称 |
| benchMark | string | 业绩比较基准 |
| indexCode / indexName / indexSht / indexType | string | 标的指数 |
| firstClass / secondClass / thirdClassMarketType / thirdClassMarketValue / className | string | 指数分类 |
| riskLevel | string | 风险等级 |
| pubDt | string | 数据更新日期 |
| unitNav / accuUnitNav | number | 单位净值、累计单位净值（元） |
| navPctChg1D/1W/1M/3M/6M/1Y/3Y/5Y/TY/Bgn | number | 各周期净值涨跌幅（%） |
| annTrackError1Y | number | 近1年年化跟踪误差（%） |
| excessReturn1Y | number | 近1年超额收益（%） |
| maxDown1W/1M/3M/6M/1Y/3Y/5Y/10Y/TY/Bgn | number | 最大回撤（%） |
| rptDt | string | 报告日期 |
| rptFundScale | number | 产品规模（报告日期）（**元**，÷1e8=亿） |
| unitAccBonus / accBonusCount / currBonusDt | | 分红信息 |
| fundManagerCurrent / fundManagerFormer | array | 现任/历任基金经理（psnCode/psnName/posiBgnDt/posiEndDt/managementTime/manageStatus 1在职/0离任/performance 等） |
| relatedETF | array | 相关ETF（trdCode/fundSht/fundType/fundScale 元） |
| relatedShareFunds | array | 相关份额基金（trdCode/relatedTrdCode/relatedFundSht） |
| sinfoWindcode / indexSInfoWindcode | string | 基金/跟踪指数万德代码 |
| authorizedIndex | boolean | 跟踪指数是否有权限 |

> - `fundNavJson`、`benchmarkReturnJson` 是资源文件路径，不当作内嵌 JSON 解析。
> - 跟踪误差读取规则：年化跟踪误差读取 `annTrackError1Y`。

---

## `POST /skill/v2/oef/holdings` — 批量场外基金前十大持仓

批量查询多只场外指数基金的最新（或指定日期）前十大重仓股，返回每只股票的代码、简称、占净值比例（%）及报告期截止日期。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | 场外基金代码列表，最多10个 |
| date | string | 否 | 持仓日期 yyyy-MM-dd，不传则默认最新 |

**最终数据路径**：`$.data[]`（按基金分组，每只基金一项）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码 |
| availabilityStatus | string | 数据可用性状态：有数据 / 未找到该基金 / 代码类型不匹配 / 无持仓数据 / 查询失败 |
| holdingItems | array | 持仓明细列表，availabilityStatus=有数据 时返回 |

`holdingItems[]` 每项字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | 基金交易代码 |
| endDt | string | 报告期截止日期，yyyy-MM-dd |
| stockCode | string | 股票代码（6位） |
| secuSht | string | 股票简称 |
| holdNavRat | number | 占净值比例（%） |
| stockWindcode / sinfoWindcode | string | 股票/基金万德代码 |

---

## `POST /skill/v2/oef/return` — 批量场外基金区间收益

批量查询多只场外指数基金在指定时间区间或预设周期内的区间收益率（%），逐只返回实际起止日期与收益率。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| codes | array | 是 | 场外基金代码数组，最多10只 |
| timeMode | string | 是 | PERIOD（预设周期，需传 period）或 RANGE（自定义区间，需传 startDate/endDate） |
| period | string | PERIOD时必填 | 1D/1W/1M/3M/6M/1Y |
| startDate | string | RANGE时必填 | yyyy-MM-dd |
| endDate | string | RANGE时必填 | yyyy-MM-dd |
| boundaryMatchMode | string | 否 | 仅 RANGE 生效：FLEXIBLE（默认，允许边界收缩到最近可交易日）/ STRICT（必须为交易日） |

**最终数据路径**：`$.data[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | 基金交易代码，6位数字 |
| indexCode | string | 返回基金自身代码（与 trdCode 相同），不是跟踪指数代码 |
| startDate / endDate | string | 实际区间起止日期，yyyy-MM-dd |
| availabilityStatus | string | 收益率数据可用性状态：有数据 / API接口无数据 / 历史查询无数据 / 不支持的期间 / API调用异常 / 系统异常 |
| returnRate | number | 区间收益率（%），保留2位小数，数据不可用时为 null |
| serverTime | string | 系统时间，yyyy-MM-dd hh:mm:ss |

> ⚠️ **returnRate 缺失值处理**：availabilityStatus≠有数据 时 returnRate 为 null，必须用 `.get('returnRate')` 取值并判空，不得把缺失当作 0。历史不足时状态为"历史查询无数据"，用自然语言说明，不补造收益率。
>
> ⚠️ **边界钳制**：起止日期可能被钳制到可得数据范围（如基金成立日晚于请求起点，则从成立日起算），不报错；展示时以返回的 `startDate`/`endDate` 为准。

---

## `POST /skill/v2/oef/dividends` — 批量场外基金分红明细

批量查询多只场外指数基金的历史分红明细，按分红时间倒序返回每次分红的权益登记日、分红基准日、每份分红金额（元）、红利发放日（场内/场外）。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodes | array | 是 | 场外基金代码数组，最多10只 |
| startDate | string | 否 | 查询开始日期 yyyy-MM-dd，不传则从最早历史数据开始 |
| endDate | string | 否 | 查询结束日期 yyyy-MM-dd，不传则到最新数据日期 |

**最终数据路径**：`$.data[]`（按基金分组，每只基金一项）

| 字段 | 类型 | 说明 |
|------|------|------|
| fundCode | string | 基金代码，6位数字 |
| availabilityStatus | string | 数据可用性状态：有数据 / 无历史分红 / 未找到该基金 / 代码类型不匹配 / 查询失败 |
| dividendItems | array | 分红明细列表，按分红时间倒序；无历史分红时该键不返回，用 `.get('dividendItems')` 判空 |

`dividendItems[]` 每项字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | 交易代码，6位数字 |
| eqyRecordDt | string | 权益登记日，yyyy-MM-dd |
| dvdBenDt | string | 分红计算基准日，yyyy-MM-dd |
| cashDvdPerShTax | number | 每份分红金额（元） |
| payDt | string | 红利发放日（场内），场外基金此字段通常为 null |
| divPayDt | string | 红利发放日（场外），yyyy-MM-dd |

---

## `POST /skill/v2/oef/financial-report` — 场外基金季报财务指标

查询场外基金的季报财务指标：本期利润、公允价值变动损益、份额净收益、期末资产净值、经营活动现金流量净额等。数据经 ETL 同步，存在 T+1 延迟。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trdCodes | array | 是 | 基金代码列表，最多20个 |
| beginDate | string | 否 | 查询开始日期 yyyy-MM-dd，与 endDate 配合使用查询日期范围内所有报告期 |
| endDate | string | 否 | 报告期结束日期 yyyy-MM-dd。单独传=指定报告期；配合 beginDate=日期范围；不传则返回最新一期 |

**最终数据路径**：`$.data[]`（按基金分组，每只基金一项）

| 字段 | 类型 | 说明 |
|------|------|------|
| trdCode | string | 基金代码 |
| chiName / fundName | string | 基金名称/简称 |
| availabilityStatus | string | 数据可用性状态：有数据 / 未找到该基金 / 查询失败 |
| financialReports | array | 季报财务指标列表，按报告期倒序排列 |

`financialReports[]` 每项字段（金额单位均为**元**）：

| 字段 | 类型 | 说明 |
|------|------|------|
| endDt | string | 报告期结束日期，yyyy-MM-dd |
| pubDt | string | 公告日期，yyyy-MM-dd |
| totalProfit | number | 基金本期利润（元） |
| netIncome | number | 本期利润扣除本期公允价值变动损益后的净额（元） |
| fairValueChangeIncome | number | 公允价值变动损益（元） |
| totalProfitPerShare | number | 加权平均基金份额本期利润 |
| netIncomePerShare | number | 份额净收益 |
| netAsset | number | 期末基金资产净值（元） |
| nvPerShare | number | 期末基金份额净值 |
| netOperateCashflow | number | 本期经营活动产生的现金流量净额（元） |
| totalRevenue | number | 本期收入（元） |

⚠️ 并非每份季报都披露全部字段：fairValueChangeIncome、netIncomePerShare、netOperateCashflow、totalRevenue 可能为 `null`，读取时用 `.get()` 判空，缺失字段不要按 0 展示。

---

## 关联ETF行情（场外基金无盘中行情，用关联ETF作参考）

场外基金按净值成交，没有盘中价格、成交额、换手率、IOPV或溢折率。用户询问这些指标时，先说明场外基金本身不存在这类数据；如用户实际想了解对应ETF的场内表现，先通过 `/skill/v2/oef/detail` 或关键词搜索获取 `relatedETF` 中的ETF代码，再调用以下接口，并在回答中明确标注数据来源是关联ETF而非场外基金本身。

### `GET /skill/v2/quote/etf` — 关联ETF批量盘口行情

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbols | string | 是 | ETF代码列表，英文逗号分隔，URL查询参数传递，单次最多50个 |

**最终数据路径**：`$.data.list[]`（另有 `$.data.serverTime` 服务器时间）

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 标的代码 |
| lastPrice | number | 最新价（元） |
| changeRate | number | 最新涨跌幅（%） |
| changeValue | number | 涨跌值（元） |
| dealBalance | number | 成交额（元） |
| dealVolume | number | 成交量（份） |
| turnoverRatio | number | 换手率（%） |
| iopv | number | IOPV实时估值（元） |
| deviationRate | number | 溢折率（%） |
| yesterdayClosePrice | number | 昨日收盘价（元） |
| date | integer | 行情日期 yyyyMMdd |
| timeStamp | integer | 行情时间戳 HHmmss |

> 无行情时返回仅含 symbol 的空对象（空值兜底）。

### `POST /skill/v2/quote/minite` — 关联ETF分时分钟行情

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| fundCodeList | array | 是 | 标的代码列表，最多50个 |
| date | string | 否 | 行情日期 yyyyMMdd，默认当天 |
| lastTimestamp | integer | 否 | 上次获取的最后时间戳：>0 走增量更新（仅返回新增分钟数据），=0 走全量 |

**最终数据路径**：`$.data.dataList[]`（另有 `$.data.serverTime` 服务器时间）

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | string | 标的代码 |
| quoteList[] | array | 分钟数据列表：minute（分钟时间戳，如930表示9:30）、lastPrice（元）、iopv（元）、changeRate（%） |
| latestQuote{} | object | 实时行情快照，字段同盘口行情（lastPrice/changeRate/dealBalance/dealVolume/turnoverRatio/iopv/deviationRate/yesterdayClosePrice/date/timeStamp/changeValue） |

> 不要把净值日涨跌（`navPctChg1D`）当作实时行情。`serverTime` 是接口响应时间，不是基金净值更新时间；单位净值必须同时展示净值日期（`pubDt`）。

---

## `GET /skill/v2/discovery/hot-search-recommend` — 按类型热搜推荐

根据产品类别返回对应的热搜推荐列表，可用于发现页热门推荐展示。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 是 | 产品类别：index（指数）/ etf（ETF）/ out-index（场外基金），URL查询参数传递 |

**最终数据路径**：`$.data[]`

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 产品编码 |
| name | string | 产品名称 |
| navPctChg1Y | number | 近一年涨跌幅（%），仅 out-index 类型返回，其他类型为空 |

---

## 单位速查

| 字段 | 接口 | 单位 | 换算 |
|------|------|------|------|
| fundScale | search/oef | 元 | ÷1e8=亿 |
| rptFundScale | oef/detail | 元 | ÷1e8=亿 |
| relatedETF[].fundScale | oef/detail | 元 | ÷1e8=亿 |
| holdNavRat | oef/holdings | % | 直接展示 |
| returnRate | oef/return | % | 直接展示 |
| cashDvdPerShTax | oef/dividends | 元/份 | 直接展示 |
| totalProfit/netIncome/fairValueChangeIncome/netAsset/netOperateCashflow/totalRevenue | oef/financial-report | 元 | ÷1e8=亿 |
| totalProfitPerShare/netIncomePerShare/nvPerShare | oef/financial-report | 元/份 | 直接展示 |
| annTrackError1Y | search/oef、oef/detail | % | 直接展示 |
| dealBalance | quote/etf、quote/minite | 元 | ÷1e8=亿 |

## 名称字段使用规则

| 接口 | 对外展示名 | 说明 |
|------|------------|------|
| oef/detail | `fundName` | detail 的 `fundName` 是展示名，`chiName` 是法律全称 |
| search/oef | `fundSht` 或 `fundName` | 简称优先 `fundSht` |

## 代码格式速查

| 场景 | 正确格式 | 常见错误 |
|------|----------|----------|
| 场外基金代码入参 | `006748`（6位数字） | `006748.OF`、`006748.SH`、`006748.SZ` |
| 批量代码（POST body） | `["006748", "110003"]` | 带 `.OF` 或交易所后缀 |
| 批量代码（GET query） | `510300,159919`（逗号分隔字符串） | JSON数组、带后缀 |

## 数据路径速查

| 接口 | 结果路径 | 常见错误 |
|------|---------|---------|
| search/oef | `$.data.data[]` | 误用 `$.data.list[]`；分页参数是 `page` |
| oef/detail | `$.data[].detail{}` | 忘记先判 `availabilityStatus` |
| oef/holdings | `$.data[].holdingItems[]` | 已按 fundCode 分组，无需本地再分组 |
| oef/return | `$.data[]` | status≠有数据时 returnRate 为 null，需判空 |
| oef/dividends | `$.data[].dividendItems[]` | 无分红时 dividendItems 键不返回，需判空 |
| oef/financial-report | `$.data[].financialReports[]` | 不传日期只返回最新一期 |
| quote/etf | `$.data.list[]` | data 是对象不是数组 |
| quote/minite | `$.data.dataList[]` | 分钟序列在 `quoteList[]`，快照在 `latestQuote{}` |
| discovery/hot-search-recommend | `$.data[]` | type 必填 |

## OEF vs ETF 关键差异

| 维度 | ETF | OEF |
|------|-----|-----|
| 搜索 | `/skill/v2/search/etf` | `/skill/v2/search/oef`（仅关键词+分页） |
| 详情规模字段 | fundScale（**元**） | rptFundScale（**元**） |
| 销售服务费 | 无 | saleServiceFee（detail）/ salesServiceFee（搜索） |
| 溢折率/实时行情 | 有（quote/etf、quote/minite） | 无（场外无盘中价、成交量、换手率、IOPV、溢折率） |
| 场内分红发放日 | payDt | payDt（通常null） |
| 场外分红发放日 | divPayDt | divPayDt |
| 上市日 | lstDt | 无 |
