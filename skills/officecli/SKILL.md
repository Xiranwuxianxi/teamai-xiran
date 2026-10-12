---
name: officecli
description: Create, analyze, proofread, and modify Office documents (.docx, .xlsx, .pptx) using the officecli CLI tool. Use when the user wants to create, inspect, check formatting, find issues, add charts, or modify Office documents.
---

# officecli

AI-friendly CLI for .docx, .xlsx, .pptx. Single binary, no dependencies, no Office installation needed.

## Install

If `officecli` is not installed:

```bash
# macOS / Linux
curl -fsSL https://d.officecli.ai/install.sh | bash

# Windows (PowerShell)
irm https://d.officecli.ai/install.ps1 | iex
```

Verify with `officecli --version`. If still not found after install, open a new terminal.

---

## Strategy

**L1 (read) → L2 (DOM edit) → L3 (raw XML)**. Always prefer higher layers. Add `--json` for structured output.

**Before doc work, check Specialized Skills** (bottom of this file). Fundraising decks, academic papers, financial models, dashboards, and Morph animations need their own skill loaded first — `load_skill` once, then proceed.

---

## Help System (IMPORTANT)

**When unsure about property names, value formats, or command syntax, ALWAYS run help instead of guessing.** One help query beats guess-fail-retry loops.

```bash
officecli help                                  # All commands + global options + schema entry points
officecli help docx                             # List all docx elements
officecli help docx paragraph                   # Full schema: properties, aliases, examples, readbacks
officecli help docx set paragraph               # Verb-filtered: only props usable with `set`
officecli help docx paragraph --json            # Structured schema (machine-readable)
```

Format aliases: `word`→`docx`, `excel`→`xlsx`, `ppt`/`powerpoint`→`pptx`. Verbs: `add`, `set`, `get`, `query`, `remove`. MCP exposes the same schema via the single `command` string param: `{"command":"help docx paragraph"}`.

---

## Performance: Resident Mode

**Every command auto-starts a resident on first access** (60s idle timeout) — file-lock conflicts are automatically avoided. Explicit `open`/`close` is still recommended for longer sessions (12min idle):
```bash
officecli open report.docx       # explicitly keep in memory
officecli set report.docx ...    # no file I/O overhead
officecli close report.docx      # save and release
```

Opt out of auto-start: `OFFICECLI_NO_AUTO_RESIDENT=1`.

---

## Quick Start

**PPT:**
```bash
officecli create slides.pptx
officecli add slides.pptx / --type slide --prop title="Q4 Report" --prop background=1A1A2E
officecli add slides.pptx '/slide[1]' --type shape --prop text="Revenue grew 25%" --prop x=2cm --prop y=5cm --prop font=Arial --prop size=24 --prop color=FFFFFF
```

**Word:**
```bash
officecli create report.docx
officecli add report.docx /body --type paragraph --prop text="Executive Summary" --prop style=Heading1
officecli add report.docx /body --type paragraph --prop text="Revenue increased by 25% year-over-year."
```

**Excel:**
```bash
officecli create data.xlsx
officecli set data.xlsx /Sheet1/A1 --prop value="Name" --prop bold=true
officecli set data.xlsx /Sheet1/A2 --prop value="Alice"
```

---

## L1: Create, Read & Inspect

```bash
officecli create <file>               # Create blank .docx/.xlsx/.pptx
officecli view <file> <mode>          # outline | stats | issues | text | annotated | html
officecli get <file> <path> --depth N # Get a node and its children [--json]
officecli query <file> <selector>     # CSS-like query
officecli validate <file>             # Validate against OpenXML schema
```

### view modes

| Mode | Description |
|------|-------------|
| `outline` | Document structure |
| `stats` | Statistics (pages, words, shapes) |
| `issues` | Formatting/content/structure problems |
| `text` | Plain text extraction |
| `annotated` | Text with formatting annotations |
| `html` | Static HTML snapshot |
| `screenshot` / `svg` / `pdf` / `forms` | PNG via headless browser / SVG / PDF export / form-fields JSON |

### get

Any XML path via element localName. Use `--depth N` to expand children. Add `--json` for structured output.

```bash
officecli get report.docx '/body/p[3]' --depth 2 --json
officecli get slides.pptx '/slide[1]' --depth 1
officecli get data.xlsx '/Sheet1/B2' --json
```

### Stable ID Addressing

```
/slide[1]/shape[@id=550950021]
/body/p[@paraId=1A2B3C4D]
/comments/comment[@commentId=1]
```

### query

CSS-like selectors: `[attr=value]`, `[attr!=value]`, `:contains("text")`, `:empty`, `:has(formula)`. Boolean `and`/`or` supported.

```bash
officecli query report.docx 'paragraph[style=Normal] > run[font!=Arial]'
officecli query slides.pptx 'shape[fill=FF0000]'
```

---

## Watch & Interactive Selection

Live HTML preview that auto-refreshes on every file change.

```bash
officecli watch <file> [--port N]      # Start preview server
officecli unwatch <file>               # Stop
officecli goto <file> <path>           # Scroll to element
```

Click to select in browser. Then:
```bash
officecli get <file> selected [--json]
```

---

## L2: DOM Operations

### set — modify properties

```bash
officecli set <file> <path> --prop key=value [--prop ...]
```

**Value formats:**
- Colors: `FF0000`, `#FF0000`, `red`, `rgb(255,0,0)`
- Spacing: `12pt`, `0.5cm`, `1.5x`, `150%`
- Dimensions: `914400`, `2.54cm`, `1in`, `96px`

**Dotted-attr aliases:** `font.color=red`, `font.bold=true`, `font.size=14pt`

### find — format or replace matched text

```bash
# Format matched text
officecli set doc.docx '/body/p[1]' --find weather --prop bold=true --prop color=red

# Replace text
officecli set doc.docx / --find draft --replace final

# Regex matching
officecli set doc.docx '/body/p[1]' --find '\d+%' --prop regex=true --prop color=red
```

### add — add elements or clone

```bash
officecli add <file> <parent> --type <type> [--prop ...]
officecli add <file> <parent> --type <type> --after <path> [--prop ...]
officecli add <file> <parent> --type <type> --before <path> [--prop ...]
officecli add <file> <parent> --type <type> --from <path>   # clone
```

**Element types by format:**

| Format | Types |
|--------|-------|
| **pptx** | slide, shape, picture, chart, table, row, connector, group, align/distribute, video/audio, equation, notes, animation, transition, paragraph |
| **docx** | paragraph, run, table, row, cell, image, header/footer, section, bookmark, comment, footnote, endnote, chart, equation, field, hyperlink, style, toc, watermark, break, diagram, textbox |
| **xlsx** | sheet, row, col, cell, chart, image, comment, table, namedrange, pivottable, sparkline, validation, autofilter, shape, textbox, CF |

### Pivot tables (xlsx)

```bash
officecli add data.xlsx /Sheet1 --type pivottable \
  --prop source="Sheet1!A1:E100" --prop rows=Region,Category \
  --prop cols=Year --prop values="Sales:sum,Qty:count" \
  --prop grandTotals=rows
```

### Document-level properties

```bash
officecli set doc.docx / --prop docDefaults.font=Arial --prop docDefaults.fontSize=11pt
officecli set data.xlsx / --prop calc.mode=manual
officecli set slides.pptx / --prop defaultFont=Arial
```

### Sort (xlsx)

```bash
officecli set data.xlsx /Sheet1 --prop sort="C desc" --prop sortHeader=true
```

### Text-anchored insert

```bash
officecli add doc.docx '/body/p[1]' --type run --after find:weather --prop text=" (sunny)"
```

### batch — multiple operations in one save cycle

```bash
echo '[
  {"command":"set","path":"/Sheet1/A1","props":{"value":"Name","bold":"true"}},
  {"command":"set","path":"/Sheet1/B1","props":{"value":"Score","bold":"true"}}
]' | officecli batch data.xlsx --json
```

Supports: `add`, `set`, `get`, `query`, `remove`, `move`, `swap`, `view`, `raw`, `raw-set`, `validate`.

---

## L3: Raw XML

Use when L2 cannot express what you need.

```bash
officecli raw <file> <part>
officecli raw-set <file> <part> --xpath "..." --action replace --xml '<w:p>...</w:p>'
officecli add-part <file> <parent>
```

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---------|-----------------|
| `--name "foo"` | Use `--prop name="foo"` |
| Unquoted `[N]` in zsh/bash | Always quote: `'/slide[1]'` |
| PPT `shape[1]` for content | Use `shape[2]+` for content shapes |
| Guessing property names | Run `officecli help <format> <element>` |

---

## Specialized Skills

`officecli load_skill <name>`

### Word (.docx)
- `word` — Reports, letters, memos, proposals
- `academic-paper` — Journal/conference/thesis: APA/Chicago/IEEE citations, equations, cross-refs

### PowerPoint (.pptx)
- `pptx` — Generic decks: board reviews, sales decks, all-hands
- `pitch-deck` — Fundraising only (seed/Series A-C)
- `morph-ppt` — Cinematic Morph-animated presentations
- `morph-ppt-3d` — 3D Morph with GLB models

### Excel (.xlsx)
- `excel` — Generic workbooks, formulas, pivots
- `financial-model` — Financial models, scenarios, projections
- `data-dashboard` — KPI/analytics dashboards
