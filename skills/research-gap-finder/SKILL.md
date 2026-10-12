---
name: research-gap-finder
description: "Turn a broad topic into a ranked, citation-backed list of genuine research gaps — ready to become research questions. Combines a reproducible, key-free scholarly-API pipeline (OpenAlex, Semantic Scholar, Crossref, Europe PMC, PubMed, arXiv) with 100 curated gap-identification resources: gap frameworks (PICO/PICOS, six-type gap taxonomy, five-dimension importance rubric, AHRQ, Robinson, Arksey-O'Malley), AI/citation tools (Litmaps, ResearchRabbit, Connected Papers, Elicit, SciSpace, Consensus, Scite, Inciteful), bibliometric mining, and a confidence-labeled honesty protocol. Outputs a classified, importance-ranked, citation-backed gap report with a candidate research question per gap."
version: 2.0.0
categories: [research, knowledge]
topics: [research-gaps, literature-review, systematic-review, citation-analysis, academic-research]
metadata:
  openclaw:
    emoji: "🔍"
    requires:
      bins: ["python3", "curl"]
      python: [stdlib]
      apis: ["open scholarly APIs (OpenAlex, Crossref, Europe PMC, PubMed E-utilities, arXiv, Semantic Scholar) are key-free; Elicit, SciSpace, Scite, Dimensions and most citation-mapping tools require user accounts / API keys"]
    network:
      outbound: ["api.semanticscholar.org", "api.crossref.org", "api.openalex.org", "www.ebi.ac.uk", "eutils.ncbi.nlm.nih.gov", "export.arxiv.org", "api.biorxiv.org", "api.medrxiv.org", "api.ssrn.com", "api.elsevier.com", "api.incites.clarivate.com", "litmaps.com", "researchrabbit.ai", "connectedpapers.com", "elicit.com", "scispace.com", "consensus.app", "scite.ai", "inciteful.xyz", "dimensions.ai", "scholar.google.com", "patents.google.com"]
---

# 🔍 research-gap-finder

**Turn a broad topic into a ranked, citation-backed list of genuine research gaps — ready to become research questions.**

v2.0.0 makes the skill **fully operational**: a reproducible, stdlib-only CLI
(`scripts/research_gap_cli.py`) now performs the automated core against key-free scholarly
APIs, while the richer methodology and the browser-based citation tools remain as a
guided human-in-the-loop layer. Every gap the tool emits is labeled with a confidence and
traceable to a resolvable source identifier, so it never invents a citation or a trend.

## The two layers

| Layer | What it does | Who runs it |
|---|---|---|
| **Automated (CLI)** | Search key-free APIs, build the evidence matrix, extract gap cues, classify gaps into the six-type taxonomy, score importance, verify source identifiers, and emit a report. | The agent, fully scriptable |
| **Guided (browser/paid)** | Litmaps, ResearchRabbit, Connected Papers, Elicit, SciSpace, Consensus, Scite, Dimensions, grants/patents/trials databases. | Human-in-the-loop, within ToS |

The CLI is honest by construction: **a gap is never credited to a source without a resolvable
identifier** (DOI / accession). Unverifiable items are marked `Exploratory/Hypothetical`.

## When to use

- A researcher asks: *"what are the research gaps in X?"*
- A PhD student needs a defensible gap for a proposal or literature-review chapter.
- A lab wants to scan a field for understudied angles before committing resources.
- An agent must produce an evidence-backed "state of the field + open problems" brief.

## 1 · Automated pipeline (`research_gap_cli.py`)

Stdlib-only (no pip installs) — Python 3.8+ plus `curl`/network. Full help:
`python3 scripts/research_gap_cli.py <subcommand> --help`.

```bash
# 1) Create a project (topic + optional PICO) and an evidence matrix.
python3 scripts/research_gap_cli.py init --dir proj \
  --topic "Alzheimer's disease biomarkers" \
  --pico '{"population":"older adults","outcome":"accurate early diagnosis"}'

# 2) Search key-free scholarly APIs and append to the evidence matrix.
python3 scripts/research_gap_cli.py search --dir proj \
  --query "plasma biomarkers early diagnosis Alzheimer's" \
  --engines openalex,semantic,crossref,europepmc,arxiv --limit 100 --years 2018 2026

# 3) Extract clear gap cues (limitations / future-work / absence statements).
python3 scripts/research_gap_cli.py extract --dir proj

# 4) Classify each gap into the six-type taxonomy + score the 5-dimension rubric.
python3 scripts/research_gap_cli.py classify --dir proj --scores scores.json

# 5) Verify source identifiers (Crossref DOI resolution) and set confidence labels.
python3 scripts/research_gap_cli.py validate --dir proj --check-web

# 6) Rank gaps by importance x confidence.
python3 scripts/research_gap_cli.py rank --dir proj --min-total 9 --min-confidence medium

# 7) Emit the citation-backed, confidence-labeled Markdown report.
python3 scripts/research_gap_cli.py report --dir proj --top 8 --out report.md

# Inspect project state / run an offline self-test.
python3 scripts/research_gap_cli.py status --dir proj
python3 scripts/research_gap_cli.py selftest
```

**Per-command behavior**

- `init` — writes `config.json` (topic, PICO, engines, years, limit, cache flags).
- `search` — queries the selected engines, de-duplicates by DOI / normalized title, and
  appends to `evidence.json` + `evidence_matrix.csv`. Raw API responses are cached under
  `proj/.cache/`; **a live API failure never aborts the run** — the engine is skipped, the
  rest continue, and the report clearly notes any unreachable engines. When fully offline the
  tool degrades to a report whose gaps are labeled `Exploratory/Hypothetical`.
- `extract` — pulls "gap cue" sentences (limitations, future work, absence statements) from
  abstracts into candidate gap statements. It never fabricates a gap; if a search returns no
  cue sentence there simply is no candidate.
- `classify` — assigns the **six-type taxonomy** (evidence / methodological / population /
  contextual / theoretical / translational) via a transparent cue lexicon, and scores the
  **five-dimension rubric** (theoretical, practical, feasibility, novelty, coherence, each 0–3,
  total /15). Baseline scores are clearly marked `estimated`; supply per-gap scores via
  `scores.json` (or `--scores`) for your proposal.
- `validate` — resolves every source via Crossref (or marks identifiers) and sets
  `confidence` by the skill's honesty rules: **High** = ≥2 independent sources & resolved;
  **Medium** = 1 source; **Low** = no resolvable source → flagged `Exploratory/Hypothetical`.
- `rank` / `report` — sort by importance × confidence and emit the gap report.
- `status` / `selftest` — project state and an offline self-test.

## 2 · Methodology (guided layer — keep doing this to add depth)

### Define the search horizon
Draft a PICO/PICOS statement (Population, Intervention, Comparison, Outcome, Setting). Record
it as the query template for the whole investigation. Record it in the PICO section of the
project config.

### Collect recent systematic reviews
Search PubMed, Cochrane, and Scopus for the 3–5 most recent systematic reviews/meta-analyses
on the topic; export citation lists. Combine with the automated search results.

### Extract explicit gap cues
Read each review's **"Limitations"** and **"Future Directions"** sections. Summarize each gap
in a matrix: *Source, Gap type, Evidence*. The CLI's `extract` automates the cue-detection pass
on abstracts; your reading adds the depth.

### Map citation networks (guided tools)
Import reference lists into **Litmaps** (reference-gap method: spot seminal works the reviews
failed to cite) and **ResearchRabbit / Connected Papers** (find "citation islands" that never
link). These tools are browser-based; drive them interactively and **within their terms of
service** — do not attempt unauthorized programmatic access, and avoid uploading proprietary
or sensitive data to services you do not trust.

### Run semantic *"what is unstudied?"* queries (guided)
Use **Elicit** or **Consensus** to ask questions such as *"What aspects of X have not been
studied in population Y?"* Capture answers plus their supporting citations.

## 3 · Classify & rank gaps

### Six-type knowledge-gap taxonomy
| Gap type | Look for | How the CLI tags it |
|---|---|---|
| **Evidence** | No/only weak studies for a PICO element | "insufficient evidence", "little is known" … |
| **Methodological** | Weak designs, outdated instruments, no controls | "small sample", "no control" … |
| **Population** | Demographic/geographic/severity groups absent | "rural", "elderly", "underrepresented" … |
| **Contextual** | Settings/cultures/real-world omitted | "low-resource", "community", "setting" … |
| **Theoretical** | No explicit theory / conflicting explanations | "mechanism", "framework", "no consensus" … |
| **Translational** | Findings not moved to practice/policy | "implementation", "uptake", "policy" … |

### Five-dimension importance rubric (0–3 each, max 15)
| Dimension | Question |
|---|---|
| **Theoretical** | Does filling it advance core concepts or resolve contradictions? |
| **Practical** | Does it solve a real problem / inform policy-practice? |
| **Feasibility** | Are data, methods, resources realistically obtainable? |
| **Novelty** | Is it genuinely unstudied (check preprints, trials, grants)? |
| **Coherence** | Is it the logical next step of the field's trajectory? |

**13–15** high → proposal-ready; **9–12** medium → needs feasibility work; **≤8** low →
re-evaluate. Require ≥2 feasibility to avoid "interesting but impossible".

The CLI's `classify` emits **baseline (estimated)** scores. Override them per gap with a
`scores.json` of the form `{"<gap-id>": {"theoretical":2,"practical":3,...}}` (or
`--scores scores.json`) before you finalise a proposal — the rubric's judgment is yours, not
the tool's.

> ⚠️ **Gap identification ≠ importance assessment.** Identification ends when the "Gap(s)"
> cell is non-empty; importance is judged *afterwards* with the rubric. Many gaps are genuine
> but unimportant — never conflate absence of evidence with value of evidence.

## 4 · Advanced mining strategies (guided layer)

- **Patents** (Google Patents, USPTO, Espacenet) — what's patented but not academically researched.
- **Preprints** (arXiv, bioRxiv, medRxiv, SSRN) — emerging gaps before publication.
- **Conference proceedings** (NeurIPS, CHI, AAAI) — mine "future work" sections.
- **Theses** (ProQuest, OATD, EThOS) — PhD authors state gaps explicitly.
- **Grants** (NIH RePORTER, NSF, EU CORDIS) — what's funded, and what's not.
- **Trials** (ClinicalTrials.gov, WHO ICTRP) — conditions with few/no trials.
- **Policy & industry** (WHO, World Bank, OECD; McKinsey, Gartner) — where practice outpaces evidence.
- **Replication studies** (PLOS ONE, JASNH) — findings that fail to replicate.
- **Bibliometrics** — VOSviewer (co-citation/keyword maps), CiteSpace (burst keywords),
  Bibliometrix (R), Gephi (network viz), Publish or Perish (metrics).

## 5 · Output: the gap report

The `report` subcommand emits a Markdown report with this schema per gap:

- **Gap statement** — concise, declarative statement of what's missing.
- **Gap type** — six-type taxonomy label (+ secondary type).
- **Source evidence** — the specific papers/queries establishing the absence (DOI/resolvable ID).
- **Importance assessment** — five-dimension scores + total (max 15), marked whether estimated.
- **Confidence** — High / Medium / Low (based on source count + verification).
- **Candidate research question** — one falsifiable question that would fill the gap.

### Honesty & anti-hallucination rules (non-negotiable)
1. **Zero-invented citations** — every gap traces to an identifiable source; otherwise mark it
   `Exploratory/Hypothetical`. **Definition:** `Exploratory/Hypothetical` means the gap's
   statement could not be tied to an independently verified, resolvable source — it is a
   hypothesis for the agent/human to investigate, never a citation-backed claim. The CLI
   enforces this because it only emits sources with a DOI/accession; anything without one is
   labelled accordingly.
2. **Separate identification from importance** — always run the rubric; never present a trivial
   absence as valuable.
3. **Label confidence** — AI-assisted semantic findings unverified by a review are capped at Medium.
4. **No invented trends** — if the literature is sparse, say "insufficient literature to
   determine trends", don't speculate.
5. **Absence ≠ algorithm failure** — a missing paper may be a search artifact; cross-check with
   the AHRQ framework before calling it a gap.
6. **Verify every citation you output** — resolve DOIs/titles via Crossref (the `validate`
   subcommand) before writing them; never emit a citation you cannot resolve.

## 6 · The 100-resource catalog

The complete, categorized reference list this skill is built on — frameworks, AI tools,
databases, strategies, courses, channels, books, library guides, reference managers,
bibliometric tools, communities, key papers, and advanced mining strategies — lives in
[`resources.md`](resources.md).

## ✅ Quick-start checklist

1. `init` a project with a topic (+ PICO).
2. `search` the key-free APIs for evidence.
3. `extract` gap cues (then add depth from reading reviews).
4. `classify` into the six-type taxonomy and score importance (override defaults as needed).
5. `validate` source identifiers / set confidence.
6. `rank` and `report` the citation-backed, confidence-labeled gap report.
7. Cross-check novelty with grants/preprints/trials before committing.

---
*Authored and hardened with the repo's AI multi-model team (parallel drafting + review), and
published under the Skill Publishing Standard.*
