---
name: summarize
description: Summarize URLs or files with the summarize CLI (web, PDFs, images, audio, YouTube).
homepage: https://summarize.sh
metadata: {"clawdbot":{"emoji":"🧾","requires":{"bins":["summarize"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/summarize","bins":["summarize"],"label":"Install summarize (brew)"}]}}
---

# Summarize

Fast CLI to summarize URLs, local files, and YouTube links.

## Quick start

```bash
summarize "https://example.com" --model google/gemini-3-flash-preview
summarize "/path/to/file.pdf" --model google/gemini-3-flash-preview
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto
```

## Model + keys

Set the API key for your chosen provider:
- OpenAI: `OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- xAI: `XAI_API_KEY`
- Google: `GEMINI_API_KEY` (aliases: `GOOGLE_GENERATIVE_AI_API_KEY`, `GOOGLE_API_KEY`)

Default model is `google/gemini-3-flash-preview` if none is set.

## Useful flags

- `--length short|medium|long|xl|xxl|<chars>`
- `--max-output-tokens <count>`
- `--extract-only` (URLs only)
- `--json` (machine readable)
- `--firecrawl auto|off|always` (fallback extraction)
- `--youtube auto` (Apify fallback if `APIFY_API_TOKEN` set)

## Prerequisites / Pitfalls

- **Node.js 20+ required.** Node 18 causes `SyntaxError: Invalid flags supplied to RegExp constructor 'v'` crash.
  Fix: `nvm use 20` before running summarize.
- CLI path: `/usr/local/bin/summarize` (global npm install)

## Config

Optional config file: `~/.summarize/config.json`

```json
{ "model": "openai/gpt-5.2" }
```

## DeepSeek Provider

- Set `DEEPSEEK_API_KEY` env var (e.g. in `~/.bashrc`)
- Use with: `summarize "https://example.com" --model deepseek/deepseek-v4-pro`
- DeepSeek v4-pro supports `thinking` mode and `reasoning_effort` via API directly

Optional services:
- `FIRECRAWL_API_KEY` for blocked sites
- `APIFY_API_TOKEN` for YouTube fallback
