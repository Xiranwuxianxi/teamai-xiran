---
name: stock-diagnosis
description: 面向沪深京A股的单票综合诊断能力。适用于用户提出“这只股票整体怎么样”“是否值得继续持有/加仓/减仓”“当前风险和机会如何”等泛化问题时，返回结构化的Markdown诊断报告。每次仅分析一只股票，不处理港股/美股及多标的对比。触发核心条件：用户问法为概括性诊断，未指定某个单一技术指标或财务指标（如MACD、RSI、ROE等）做精确计算。
version: 1.2.0
category: investment-finance
author: 东方财富
license: proprietary
agent_created: true
---

# 股票综合诊断

通过**自然语言问句**对单只A股进行综合分析，返回 Markdown 诊断报告，适用场景包括：
- **个股整体判断（基本面 + 资金面 + 风险面）**
- **持仓决策参考（持有/减仓/止盈/观望）**
- **热点行情下的个股风险排查**
- **用户泛化问法的一站式诊断回答**


## 功能范围

### 基础诊断能力
- 输入自然语言问句，调用诊股接口生成结构化结论
- 每次仅处理**一只**沪深京A股股票
- 返回可读 Markdown 报告（优先提取 `data.displayData`）
- 将与 `refIndexList` 同级的 `data.dataMarkdown` 原样保存为同名 `.data.md` 数据底稿
- 支持将正文和数据底稿保存为本地 Markdown 文件，便于复盘追踪

### 触发规则（何时使用本技能）
- 用户问题是**笼统/概括性**诊断：如“这只股票怎么样”“值得买吗”“该不该卖”
- 问句中未明确要求计算单个技术指标或财务指标
- 若上下文已明确股票实体，用户后续使用“它/这只股票”等代词继续提问，也应触发

### 不触发规则（何时不要使用本技能）
- 用户明确点名具体指标计算：MACD、KDJ、RSI、布林带、ROE、PE 等
- 用户要求多只股票横向对比（应走多标的分析类能力）
- 用户咨询港股、美股或其他非A股市场

### 触发示例

| 触发（泛化诊断） | 不触发（指标定向） |
|---|---|
| 丹化科技怎么样？ | 丹化科技的MACD出现金叉了吗？ |
| 海康威视亏了怎么操作？ | 海康威视当前市盈率是多少？ |
| 华尔泰值得投资吗？ | 华尔泰的RSI是否超买？ |
| 全面分析一下中国平安 | 中国平安的ROE趋势如何？ |


## 前提条件

### 授权（已内联，无需单独跑）

本 Skill 依赖 `EM_API_KEY`。优先复用已缓存凭据：先从平台私有的跨会话持久存储读取 `EM_API_KEY`，可用时仅将其注入当前业务脚本进程并直接执行，不要重复调用 `mx_get_user_api_key`。若平台私有存储不可读、未提供或没有凭据，再安全检查本机私有缓存 `~/.mx-skills/em_api_key`（只能检查是否存在、长度是否大于 0，不能 `cat` 或打印真实值）；若存在有效凭据，直接运行本 Skill 的业务脚本，脚本会自动读取该文件。

仅当平台私有存储与本机缓存都缺失或已确认失效时，才调用东方财富妙想 MCP 的 `mx_get_user_api_key` 工具获取当前 OAuth2 登录用户的东方财富 API Key。若成功取得 `apiKey`，优先保存为平台私有的跨会话 `EM_API_KEY`；同时必须把完整值写入 `~/.mx-skills/em_api_key`，作为本 Skill 业务脚本可直接读取的本机私有缓存（权限尽量设为仅当前用户可读写）。随后仅注入当前业务脚本进程并直接执行本 Skill 的业务脚本，不要再触发 skill 层面的二次授权、扫码授权或 `auth.py ensure`。

仅当 `mx_get_user_api_key` 不可用、调用失败、未返回有效 `apiKey`，或当前运行环境没有可用的东方财富妙想 MCP 时，才回退到 skill 内置授权流程。内置授权检查已内联到业务脚本，**直接执行业务脚本，不要先单独运行 `auth.py ensure`**，也不要把内置授权做成默认独立前置步骤；不要因为环境里没有 `EM_API_KEY` 就跳过本 Skill。回退时脚本按 `EM_API_KEY` 环境变量、`~/.mx-skills/em_api_key` 文件的顺序读取凭据，不再使用内置兜底 key。

处理 `apiKey` 时不要把真实值输出到 stdout/stderr、日志、命令回显或对话正文中；不要使用 `echo`、`cat`、`env | grep`、或把真实 key 直接拼进 shell 命令行的方式检查或传递凭据。需要确认凭据存在时，只检查文件是否存在、长度是否大于 0、或输出脱敏后的前后缀。执行查询或生成任务时优先使用平台私有存储注入当前业务脚本进程；没有平台凭据时，再让脚本从 `~/.mx-skills/em_api_key` 读取。确需进程级注入时，使用工具/运行时的环境变量能力，不要把真实 key 写进 shell 命令字符串。

| 退出码 | 含义 | agent 动作 |
|---|---|---|
| `0` | 成功 | 读取 `Saved:`（若有）及随后输出的 Markdown 正文 |
| `10` | 需用户授权 | 按下方 `need_auth` 流程处理 |
| `2` | 授权网络错误、接口错误或业务错误 | 检查网络后最多重试 1 次，持续失败则向用户说明 |
| `1` | 参数错误 | 不重试，向用户说明缺少或无效参数 |

退出码 `10` 时 stdout 会打印：

```text
need_auth: true
authUrl: <以实际返回为准>
apiKeyUrl: <以实际返回为准>
```


授权、凭据持久化及 401 失效处理必须遵循 [授权协议](references/auth_protocol.md)。安装依赖时运行 `pip3 install -r requirements.txt`。


## 快速开始

### 1. 命令行调用

```bash
python3 scripts/get_data.py --query "东方财富股票咋样"
```

**输出示例**
```text
Saved: /path/to/workspace/stock_diagnosis/stock_diagnosis_90bf169c.md
Data saved: /path/to/workspace/stock_diagnosis/stock_diagnosis_90bf169c.data.md
（随后输出 Markdown 诊断内容）
```

**参数说明：**

| 参数 | 说明 | 必填 |
|---|---|---|
| `--query` | 用户原始自然语言问句 | ✅（`--query` 或 stdin 二选一） |
| `--no-save` | 仅输出结果，不写入本地文件 | 否 |

### 2. 代码调用

```python
import asyncio
from pathlib import Path
from scripts.get_data import diagnose_stock

async def main():
    result = await diagnose_stock(
        question="分析一下东方财富这只股票",
        output_dir=Path("workspace/stock_diagnosis"),
        save_to_file=True,
    )
    if "error" in result:
        print(result["error"])
    else:
        print(result["content"])
        if result.get("output_path"):
            print("已保存至:", result["output_path"])
        if result.get("data_md_path"):
            print("数据底稿已保存至:", result["data_md_path"])

asyncio.run(main())
```

## 输出规范
通过脚本或工具拿到诊股结果后，**对用户的可见回复必须以接口返回的 Markdown 正文为主体**，避免模型二次转述。`data_markdown` 与 `data_md_path` 是数据底稿内容及路径，底稿供后续处理使用，不直接拼入用户可见正文。仅当接口/脚本明确返回 `error`、或正文为空时，才用简短文字说明失败原因；**禁止**在失败时杜撰报告内容。

## 常见问题
**为什么需要保持原始问句？**  
→ 诊股接口依赖用户自然语言上下文，建议避免改写导致语义偏移。

**如何只看输出，不落盘？**
```bash
python3 -m scripts.get_data --query "东方财富股票咋样" --no-save
```

## 合规说明

- 诊股结果仅供参考，不构成投资建议，输出时应附风险提示。
- 禁止在代码或提示词中硬编码账号 ID、会话 ID 或 token。
- 环境变量按敏感信息处理，不在日志或回复中泄露。
- 接口失败时不得编造结论，应返回明确错误或不确定性说明。
