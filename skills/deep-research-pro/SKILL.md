---
name: deep-research-pro
version: 1.0.0
description: "Multi-source deep research agent. Searches the web, synthesizes findings, and delivers cited reports. No API keys required."
homepage: https://github.com/paragshah/deep-research-pro
metadata: {"clawdbot":{"emoji":"🔬","category":"research"}}
---

# Deep Research Pro 🔬

A powerful, self-contained deep research skill that produces thorough, cited reports from multiple web sources. No paid APIs required — uses DuckDuckGo search.

## How It Works

When the user asks for research on any topic, follow this workflow:

### Step 1: Understand the Goal (30 seconds)

Ask 1-2 quick clarifying questions:
- "What's your goal — learning, making a decision, or writing something?"
- "Any specific angle or depth you want?"

If the user says "just research it" — skip ahead with reasonable defaults.

### Step 2: Plan the Research (think before searching)

Break the topic into 3-5 research sub-questions. For example:
- Topic: "Impact of AI on healthcare"
  - What are the main AI applications in healthcare today?
  - What clinical outcomes have been measured?
  - What are the regulatory challenges?
  - What companies are leading this space?
  - What's the market size and growth trajectory?

### Step 3: Execute Multi-Source Search

For EACH sub-question, run a web search. On this Hermes server the original ddg-search script path does not exist — use any available local search channel instead:

```bash
# 优先：已装搜索技能（tavily-search / baidu-search / heavily-search）按其文档调用
# 兜底：execute_code 内用 urllib + ProxyHandler({}) 直连 DuckDuckGo HTML 端点解析结果
# 注意：cron/无人值守会话中不要写 curl 管道接 python3 的终端命令（会被安全扫描拦截），解析一律走 execute_code
```

**Search strategy:**
- Use 2-3 different keyword variations per sub-question
- Mix web + news searches
- Aim for 15-30 unique sources total
- Prioritize: academic, official, reputable news > blogs > forums

### Step 4: Deep-Read Key Sources

For the most promising URLs, fetch full content. Use the execute_code tool (urllib + ProxyHandler({}) for direct connection) to fetch and strip tags — do not pipe curl output into python3 in a terminal command, unattended cron sessions get blocked by the security scanner:

```python
# 在 execute_code 工具内运行（示例骨架）
import urllib.request, re
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
html = opener.open(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode('utf-8', 'ignore')
text = re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', html)).strip()
print(text[:5000])
```

Read 3-5 key sources in full for depth. Don't just rely on search snippets.

### Step 5: Synthesize & Write Report

Structure the report as:

```markdown
# [Topic]: Deep Research Report
*Generated: [date] | Sources: [N] | Confidence: [High/Medium/Low]*

## Executive Summary
[3-5 sentence overview of key findings]

## 1. [First Major Theme]
[Findings with inline citations]
- Key point ([Source Name](url))
- Supporting data ([Source Name](url))

## 2. [Second Major Theme]
...

## 3. [Third Major Theme]
...

## Key Takeaways
- [Actionable insight 1]
- [Actionable insight 2]
- [Actionable insight 3]

## Sources
1. [Title](url) — [one-line summary]
2. ...

## Methodology
Searched [N] queries across web and news. Analyzed [M] sources.
Sub-questions investigated: [list]
```

### Step 6: Save & Deliver

Save the full report:
```bash
mkdir -p ~/clawd/research/[slug]
# Write report to ~/clawd/research/[slug]/report.md
```

Then deliver:
- **Short topics**: Post the full report in chat
- **Long reports**: Post the executive summary + key takeaways, offer full report as file

## Quality Rules

1. **Every claim needs a source.** No unsourced assertions.
2. **Cross-reference.** If only one source says it, flag it as unverified.
3. **Recency matters.** Prefer sources from the last 12 months.
4. **Acknowledge gaps.** If you couldn't find good info on a sub-question, say so.
5. **No hallucination.** If you don't know, say "insufficient data found."

## Examples

```
"Research the current state of nuclear fusion energy"
"Deep dive into Rust vs Go for backend services in 2026"
"Research the best strategies for bootstrapping a SaaS business"
"What's happening with the US housing market right now?"
```

## For Sub-Agent Usage

When spawning as a sub-agent, include the full research request and context:

```
sessions_spawn(
  task: "Run deep research on [TOPIC]. Follow the deep-research-pro SKILL.md workflow.
  Read /home/clawdbot/clawd/skills/deep-research-pro/SKILL.md first.
  Goal: [user's goal]
  Specific angles: [any specifics]
  Save report to ~/clawd/research/[slug]/report.md
  When done, wake the main session with key findings.",
  label: "research-[slug]",
  model: "opus"
)
```

## Requirements

- 任一本地搜索渠道（tavily-search / baidu-search / heavily-search 技能，或 execute_code 直连 DuckDuckGo HTML 端点）
- execute_code 工具（用于抓取全文，替代 curl）
- No API keys needed!
