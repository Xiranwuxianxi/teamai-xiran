# 🔍 Research Gap Finder

**Category:** research, knowledge

## ✨ What This Skill Does

Turns a broad topic into a ranked, citation-backed list of **genuine research gaps** — ready to
become research questions. v2.0.0 adds a **reproducible, stdlib-only CLI**
(`scripts/research_gap_cli.py`) that performs the automated core against key-free scholarly APIs
(OpenAlex, Semantic Scholar, Crossref, Europe PMC, PubMed E-utilities, arXiv), builds an
**evidence matrix**, extracts gap cues, classifies each gap into the **six-type knowledge-gap
taxonomy**, scores the **five-dimension importance rubric** (max 15), verifies source
identifiers, and emits a **confidence-labeled Markdown gap report** with a candidate research
question per gap.

It distills 100 curated resources (gap-identification frameworks, AI/citation tools, academic
databases, bibliometric mining, advanced strategies) plus the operational pipeline into one
method that: gather evidence → map the citation landscape → run semantic "what is unstudied?"
queries → classify each gap → rank importance → verify novelty → output a report.

## 🔐 Permissions & Requirements

- **Runtime:** Python 3.8+ (standard library only) and `curl` — no third-party packages, no
  API keys required for the automated core.
- **Network (outbound, key-free):** `api.openalex.org`, `api.semanticscholar.org`,
  `api.crossref.org`, `www.ebi.ac.uk`, `eutils.ncbi.nlm.nih.gov`, `export.arxiv.org`.
- **Network (guided, requires accounts):** Litmaps, ResearchRabbit, Connected Papers, Elicit,
  SciSpace, Consensus, Scite, Inciteful, Dimensions, Google Scholar, Google Patents — users
  supply their own accounts/API keys; the skill drives them interactively and within their ToS.
- **Filesystem:** the CLI reads/writes only inside the project directory it is given
  (`config.json`, `evidence.json`, `evidence_matrix.csv`, `gaps.json`, `gaps.csv`,
  `report.md`, and `.cache/`). It does not scan unrelated files.

## 🔒 Security & Privacy

- **Data read/collected:** bibliographic metadata, abstracts, and citations you query; any
  papers you direct it to analyse.
- **Does data leave the machine?** Only your own queries are sent to the scholarly APIs/tools
  you choose. Nothing is uploaded beyond those queries; no telemetry.
- **Secrets:** no API key, credential, or secret is read, stored, or logged by the skill. It
  never asks for or persists passwords/API keys.
- **Offline / rate-limit behaviour:** a live API failure never aborts a run — the engine is
  skipped, the rest continue, raw responses are cached under `.cache/`, and a fully offline run
  degrades to a report whose gaps are labeled `Exploratory/Hypothetical`. Invented citations are
  structurally impossible because no source is reported without a resolvable identifier.
- **Known risks & mitigations:**
  - Browser-based citation tools lack public APIs; the skill scopes automated queries to key-free
    scholarly APIs and instructs human-in-the-loop use of browser tools within their terms of service.
  - AI-summarized "gaps" can be wrong; built-in honesty rules require zero-invented citations,
    DOI/Crossref verification, and confidence caps on AI-assisted findings.
  - Absence of a paper in any one tool may be a search artifact; the workflow mandates
    cross-checking with the AHRQ framework before treating it as a real gap.

## ✅ Verification Hash

Installers can verify this skill matches the published artifact by hashing the skill files:

- **Canonical artifact SHA-256:** `a766073bdb2353cec8685ccb60ee0428ac8544918a6e61a4f8b036189eccb4c2`

Verify locally:

```bash
python3 scripts/verify_integrity.py
sha256sum -c CHECKSUMS.sha256
```

The second command checks exact per-file SHA-256 values for all functional artifacts other than
`README.md`, `CHECKSUMS.sha256`, `_meta.json`, `skill-card.md`, and cache files. The first
command also covers the normalized README (`Canonical artifact SHA-256` line normalized to zeros).

## 🚀 Quick Start

```bash
# Init a project (topic + optional PICO), then run the automated pipeline:
python3 scripts/research_gap_cli.py init --dir proj --topic "My topic"
python3 scripts/research_gap_cli.py search --dir proj --query "my topic"
python3 scripts/research_gap_cli.py extract --dir proj
python3 scripts/research_gap_cli.py classify --dir proj
python3 scripts/research_gap_cli.py validate --dir proj --check-web
python3 scripts/research_gap_cli.py rank --dir proj --min-total 9
python3 scripts/research_gap_cli.py report --dir proj --top 8 --out report.md
```

## 📚 Included

- `SKILL.md` — operational methodology + the CLI workflow, six-type taxonomy, rubric, honesty rules.
- `resources.md` — the 100-resource gap-finding catalog.
- `scripts/research_gap_cli.py` — the stdlib-only operational CLI (`init/search/extract/classify/validate/rank/report/status/selftest`).
- `scripts/verify_integrity.py` — canonical hash computation/verification.
- `tests/` — offline self-test harness.

## Review before install

```bash
sed -n '1,260p' SKILL.md
sed -n '1,260p' scripts/research_gap_cli.py
python3 scripts/verify_integrity.py
```

## License

MIT-0. See `skill-card.md` for published metadata and `resources.md` for references.
