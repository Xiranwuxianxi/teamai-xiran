---
name: stock-market-hotspot-discovery
description: 面向A股市场热点发现的综合能力。适用于用户提出“今日热点是什么”“当前热股有哪些”等泛化问题时，返回结构化的Markdown热点报告。覆盖热点资讯、热门股票等维度。触发核心条件：用户关注市场层面的热门方向或事件热度，而非单一标的的深度诊断或指标计算。
version: 1.2.0
category: investment-finance
author: 东方财富
license: proprietary
agent_created: true
---

# 股市热点发现

通过**自然语言问句**识别当前市场热点，返回 Markdown 热点报告，适用场景包括：
- **今日市场热点总览（资讯/事件/话题）**
- **热门股票与活跃方向识别**
- **交易日内快速捕捉情绪变化与关注焦点**


## 功能范围

### 基础热点能力
- 输入自然语言问句，调用热点发现接口生成结构化结论
- 覆盖热门资讯、热门股票等市场级热点信息
- 返回可读 Markdown 报告（优先提取 `data.displayData`）
- 支持将结果保存为本地 `.md` 文件，便于盘后复盘

### 触发规则（何时使用本技能）
- 用户问题是**市场层面的热点发现**：如“今日热点”“热股有哪些”
- 用户未指定单只股票/基金做深度诊断，也未要求具体指标计算
- 用户关注“热门、热搜、大事、活跃赛道、关注方向”等泛化主题

### 不触发规则（何时不要使用本技能）
- 用户明确询问单只股票深度分析（应走 stock-diagnosis）
- 用户明确询问单只基金深度分析（应走 fund-diagnosis）
- 用户要求具体指标计算或量化建模（MACD、回测、组合优化等）

### 触发示例

| 触发（热点发现） | 不触发（诊断/指标） |
|---|---|
| 今日热点是什么？ | 海康威视怎么样？ |
| 今天最热的股票有哪些？ | 丹化科技的MACD金叉了吗？ |
| 最近流行哪些投资赛道？ | 帮我建一个基金组合优化模型 |


## 授权与依赖

本 Skill 依赖 `EM_API_KEY`。优先复用已缓存凭据：先从平台私有的跨会话持久存储读取 `EM_API_KEY`，可用时仅将其注入当前业务脚本进程并直接执行，不要重复调用 `mx_get_user_api_key`。若平台私有存储不可读、未提供或没有凭据，再安全检查本机私有缓存 `~/.mx-skills/em_api_key`（只能检查是否存在、长度是否大于 0，不能 `cat` 或打印真实值）；若存在有效凭据，直接运行本 Skill 的业务脚本，脚本会自动读取该文件。

仅当平台私有存储与本机缓存都缺失或已确认失效时，才调用东方财富妙想 MCP 的 `mx_get_user_api_key` 工具获取当前 OAuth2 登录用户的东方财富 API Key。若成功取得 `apiKey`，优先保存为平台私有的跨会话 `EM_API_KEY`；同时必须把完整值写入 `~/.mx-skills/em_api_key`，作为本 Skill 业务脚本可直接读取的本机私有缓存（权限尽量设为仅当前用户可读写）。随后仅注入当前业务脚本进程并直接执行本 Skill 的业务脚本，不要再触发 skill 层面的二次授权、扫码授权或 `auth.py ensure`。

仅当 `mx_get_user_api_key` 不可用、调用失败、未返回有效 `apiKey`，或当前运行环境没有可用的东方财富妙想 MCP 时，才回退到 skill 内置授权流程。内置授权检查已内联到业务脚本，**直接执行业务脚本，不要先单独运行 `auth.py ensure`**，也不要把内置授权做成默认独立前置步骤；不要因为环境里没有 `EM_API_KEY` 就跳过本 Skill。回退时脚本按 `EM_API_KEY` 环境变量、`~/.mx-skills/em_api_key` 文件的顺序读取凭据，不再使用内置兜底 key。

处理 `apiKey` 时不要把真实值输出到 stdout/stderr、日志、命令回显或对话正文中；不要使用 `echo`、`cat`、`env | grep`、或把真实 key 直接拼进 shell 命令行的方式检查或传递凭据。需要确认凭据存在时，只检查文件是否存在、长度是否大于 0、或输出脱敏后的前后缀。执行查询或生成任务时优先使用平台私有存储注入当前业务脚本进程；没有平台凭据时，再让脚本从 `~/.mx-skills/em_api_key` 读取。确需进程级注入时，使用工具/运行时的环境变量能力，不要把真实 key 写进 shell 命令字符串。

### 退出码与授权输出

| 退出码 | 含义 | 处理方式 |
|---|---|---|
| `0` | 查询成功 | 读取 Markdown 正文及可选 `Saved:` 路径 |
| `10` | 需要用户授权 | 展示二维码并停止本轮调用 |
| `2` | 网络或业务错误 | 返回明确失败原因，不编造热点报告 |
| `1` | 缺少 query/stdin | 补充有效问句后再调用 |

需要授权时，stdout 输出带标签文本：

```text
need_auth: true
authUrl: https://...
apiKeyUrl: https://...
```


授权、凭据持久化及 401 失效处理必须遵循 [授权协议](references/auth_protocol.md)。安装依赖时运行 `pip3 install -r requirements.txt`。


## 快速开始

### 1. 命令行调用

```bash
python3 scripts/get_data.py --query "今日热点"
```

**输出示例**
```text
Saved: /path/to/workspace/stock_market_hotspot_discovery/stock_market_hotspot_discovery_90bf169c.md
（随后输出 Markdown 热点内容）
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
from scripts.get_data import discover_hotspot

async def main():
    result = await discover_hotspot(
        question="今日热点",
        output_dir=Path("workspace/stock_market_hotspot_discovery"),
        save_to_file=True,
    )
    if "error" in result:
        print(result["error"])
    else:
        print(result["content"])
        if result.get("output_path"):
            print("已保存至:", result["output_path"])

asyncio.run(main())
```

## 输出规范
通过脚本或工具拿到诊股结果后，**对用户的可见回复必须以接口返回的 Markdown 正文为主体**，避免模型二次转述。仅当接口/脚本明确返回 `error`、或正文为空时，才用简短文字说明失败原因；**禁止**在失败时杜撰报告内容。

## 常见问题

**为什么有时候不会保存 md 文件？**  
→ 当返回为不支持场景或失败结构（如 `code/status` 异常、`data` 为空）时，脚本会只输出内容而不落盘。

**如何只看输出，不落盘？**
```bash
python3 -m scripts.get_data --query "今日热点" --no-save
```

## 合规说明

- 热点信息具有时效性，结果反映接口调用时刻的市场状态。
- 热点信息仅供参考，不构成投资建议，输出时应附风险提示。
- 禁止在代码或提示词中硬编码账号 ID、会话 ID 或 token。
- 接口失败时不得编造结论，应返回明确错误或不确定性说明。
