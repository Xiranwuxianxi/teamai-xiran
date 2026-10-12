---
name: reviewer-revision-workflow
description: Use when revising a paper from reviewer comments or a 修改清单.
---

# Reviewer Revision Workflow

Responding to a numbered reviewer/revision list for an experiment-based paper.

## Step 1 — Triage before touching anything

Classify every item into one of two buckets and say the split explicitly to the user:

- **Text-only**: claim softening, scope narrowing, internal contradiction fixes, citation/version/command completeness, presentation. Can be done immediately.
- **Requires new evidence**: fairness controls, timing/latency re-measurement, resource usage, multi-seed statistics, data-integrity checks. MUST NOT be "fixed" by editing prose — the numbers have to be re-measured first.

Never rewrite paper text that depends on numbers you are about to re-measure — that is double work. Launch the experiments first, revise text while they run only for sections whose numbers will not change, and finalize after results land.

## Step 2 — Common reviewer demand → experiment mapping

| Reviewer demand | Concrete response |
|---|---|
| "comparison unfair, inputs differ (e.g. truncation)" | Measure truncation/loss rate; add a control arm where the cheap method sees the SAME truncated input |
| "batch-average ≠ single-request latency" | Separate timing: feature-build / classifier-fit / encoding / end-to-end single-request latency (median + p95 over ~50 repeats, warmup first) |
| "unsupported speed multiplier (N orders of magnitude)" | Delete the claim until unified-protocol raw timings exist; then report the measured ratio with the protocol stated |
| "one OOM proves nothing / no resource evidence" | Log peak RSS (`resource.getrusage`), swap usage (sample `/proc/meminfo` on a thread), load average, at each phase boundary |
| "no statistical reliability" | Multi-seed (≥3 data-split/subsample seeds), save per-sample predictions (npz), paired bootstrap 95% CI on accuracy differences, McNemar exact test for method pairs |
| "data leakage / version unclear" | Exact-duplicate count, train/test exact-text overlap, class ratios, dataset source + snapshot date |
| "only one configuration compared" | Add cheap ablations from the same forward pass (e.g. [CLS] vs mean pooling — zero extra encoding cost) |

## Step 3 — Make re-runs cheap

- **Cache embeddings**: encode the full corpus ONCE, save npz, reuse across data-split seeds. Turns multi-seed from hours into minutes. (Subsample seeds where the text SET changes still need re-encoding — budget accordingly.)
- Ablations sharing a forward pass (pooling variants) are free — collect them in the same loop.
- Run long jobs with `terminal(background=true, notify=true)` — never nohup (rejected by Hermes terminal); tee output to a log file; piped stdout is block-buffered so the log may stay empty for minutes while the process is fine (check `ps` instead of panicking).
- Warn the user about load/duration if the box also runs production services.

## Step 4 — Text revision rules

- Narrow conclusions to what was measured: dataset-specific ≠ language-general; one cloud VM ≠ all edge devices; distinguish "trained on this machine" from "deployed on this machine".
- Delete unprovable superlatives ("strongest feasible", "only realistic route") — replace with "one feasible configuration, others untested".
- Fix internal contradictions by trusting the raw results file over prose (e.g. "under one second" vs a measured 1.06 s).
- A fixed hardware condition is a controlled condition, not an "independent variable".
- Weaken deployment advice to hypotheses unless directly measured.

## Step 5 — Deliver

Revised md → regenerate figures → regenerate docx → send files. Keep a change-note mapping each reviewer item number to what was done (text edit / new measurement / rejected with reason).

## Support files

- `scripts/md_to_docx_cjk.py` — dependency-light Markdown→docx converter (python-docx) with proper CJK fonts (宋体/黑体 + Times New Roman), headings, real Word tables, 1.5 line spacing. Use when pandoc is absent.
- `references/rigor-experiment-patterns.md` — reusable code patterns for the Step-2 measurements (swap sampler thread, single-request latency harness, bootstrap CI, McNemar, embedding cache layout).
