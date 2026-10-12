#!/usr/bin/env python3
"""
research_gap_cli.py — operational CLI for the "research-gap-finder" ClawHub skill.

Turns a broad topic into a ranked, citation-backed list of genuine research gaps —
ready to become research questions.

The skill's methodology is described in SKILL.md (six-type gap taxonomy,
five-dimension importance rubric, evidence matrix, anti-hallucination rules).
This CLI is the *executable* core of that methodology. It:

  * QUERIES key-free scholarly APIs (OpenAlex, Semantic Scholar, Crossref,
    Europe PMC, PubMed E-utilities, arXiv) and appends results to an
    evidence matrix (JSON + CSV).
  * EXTRACTS gap cues from titles/abstracts ("limitations", "future work",
    "insufficient evidence", ...) into candidate gap statements.
  * CLASSIFIES each gap with the six-type knowledge-gap taxonomy and scores it
    on the five-dimension importance rubric.
  * VALIDATES every output citation (resolves DOIs / IDs) so no gap is ever
    credited to an unverifiable source, and cross-checks novelty against
    preprints / grants where a key-free source exists.
  * RANKS gaps by importance x novelty and emits a confidence-labeled
    Markdown gap report with a candidate research question per gap.

DESIGN GOALS (hard requirements)
  1. Stdlib-only (no third-party deps) so it runs anywhere a skill runs.
  2. Offline / rate-limit graceful: live API failures never abort a run.
     It caches raw API responses under <project>/.cache and, when offline,
     degrades to a report whose gaps are labeled "Exploratory/Hypothetical"
     with confidence "Low" and a clear warning. Invented citations are impossible
     because no source is ever reported without a resolvable identifier.
  3. Honest by construction: every gap carries its source evidence (list of
     DOIs / IDs), a confidence label, and — for AI-assist derived statements a
     "humanity" caveat when they are not independent of a verified source.

Usage:
  python3 scripts/research_gap_cli.py init    --dir <proj> --topic "<topic>" [--pico '{"population":...}']
  python3 scripts/research_gap_cli.py search  --dir <proj> [--query "<q>"] [--engines openalex,semantic,crossref,europepmc,arxiv]
                                               [--limit N] [--years 2018-2026]
  python3 scripts/research_gap_cli.py extract --dir <proj> [--cuefile cues.json]
  python3 scripts/research_gap_cli.py classify --dir <proj> [--scores scores.json]
  python3 scripts/research_gap_cli.py validate --dir <proj> [--check-web]
  python3 scripts/research_gap_cli.py rank     --dir <proj> [--min-total N] [--min-confidence low|medium|high] [--top N]
  python3 scripts/research_gap_cli.py report   --dir <proj> [--top N] [--out report.md]
  python3 scripts/research_gap_cli.py status   --dir <proj>
  python3 scripts/research_gap_cli.py selftest [--dir <tmp>]

Exit codes: 0 ok · 1 fatal config/usage · 2 (search) all engines failed offline.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2.0.0"
APP = "research-gap-finder"

# ── six-type knowledge-gap taxonomy ─────────────────────────────────────────
TAXONOMY = {
    "evidence": ["insufficient evidence", "no evidence", "lack of evidence", "few studies",
                 "limited data", "not well studied", "evidence gap", "data scarcity",
                 "paucity of", "scarcity of", "no studies", "weak evidence",
                 "little is known", "poorly understood", "limited research",
                 "understudied", "not studied", "missing data"],
    "methodological": ["methodological", "small sample", "small sample size", "no control",
                       "control group", "cross-sectional", "self-report", "instrument",
                       "confound", "longitudinal", "reproducibility", "bias", "outdated",
                       "measurement", "sample size", "retrospective", "observational"],
    "population": ["population", "subgroup", "children", "adolescent", "elderly", "pregnant",
                   "minority", "ethnic", "rural", "geographic", "low-income", "patients with",
                   "cohort", "demographic", "sex", "gender", "age group", "underrepresented",
                   "vulnerable"],
    "contextual": ["real-world", "setting", "low-resource", "resource-limited", "community",
                   "primary care", "hospital", "school", "workplace", "context",
                   "implementation setting", "cross-cultural", "cultural", "everyday"],
    "theoretical": ["theoretical", "framework", "mechanism", "theory", "model",
                    "conceptual", "underlying", "pathway", "explanatory", "contradict",
                    "mechanistic", "no consensus", "not well understood"],
    "translational": ["translation", "implementation", "practice", "policy", "clinical uptake",
                      "dissemination", "adoption", "scaling", "guideline", "health system",
                      "barrier", "into practice", "evidence to practice", "uptake"],
}

# ── five-dimension importance rubric ─────────────────────────────────────────
DIMENSIONS = ["theoretical", "practical", "feasibility", "novelty", "coherence"]
DIM_QUESTIONS = {
    "theoretical": "Advance core concepts / resolve contradictions",
    "practical": "Solve a real problem / inform policy-practice",
    "feasibility": "Data, methods, resources realistically obtainable",
    "novelty": "Genuinely unstudied (vs preprints, trials, grants)",
    "coherence": "Logical next step of the field's trajectory",
}

# Field names for cue-sentence extraction from abstracts
GAP_CUES = (
    "limitations", "future work", "future research", "further research", "further study",
    "however, these", "more studies", "needed", "remains unclear", "not fully understood",
    "inconclusive", "small sample", "warrants further", "opening question", "remains to be",
    "limited by", "unaddressed", "research gap", "open question", "less is known",
)

DEFAULT_LIMIT = 100
KNOWN_ENGINES = ["openalex", "semantic", "crossref", "europepmc", "pubmed", "arxiv"]
DEFAULT_ENGINES = ["openalex", "crossref", "europepmc", "arxiv"]

# Runtime flags set from project config on each run (see run_search / run_init).
USE_CACHE = True
TIMEOUT = 25


# ─────────────────────────────────────────────────────────────────────────────
# utilities
# ─────────────────────────────────────────────────────────────────────────────
def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def now_epoch() -> int:
    return int(time.time())


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def norm_title(t: str) -> str:
    t = re.sub(r"<[^>]+>", " ", t or "")
    t = re.sub(r"[^A-Za-z0-9 ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t


def title_key(title: str) -> str:
    # remove stopwords for dedup so "A novel kinase inhibitor" == "kinase inhibitor"
    stop = {"a", "an", "the", "of", "and", "in", "on", "for", "to", "with", "from",
            "is", "are", "using", "the", "new", "novel"}
    toks = [w for w in norm_title(title).split(" ") if w and w not in stop]
    return " ".join(toks)[:200]


def _http_json(url: str, timeout: int = 25, headers=None) -> dict:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": f"{APP}/" + VERSION})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_text(url: str, timeout: int = 25, headers=None) -> str:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": f"{APP}/" + VERSION})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def api_get_json(url: str, project: Path, use_cache: bool = USE_CACHE,
                 timeout: int = TIMEOUT, retries: int = 2) -> dict:
    """Fetch + parse JSON from a key-free scholarly API, with per-project disk
    cache and exponential backoff on transient failures (429/5xx/network).

    A live failure never aborts a run: callers catch the raised exception and
    degrade. Caching means a rerun with no network still reads prior results.
    """
    cp = project / ".cache" / (hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".json")
    if use_cache and cp.exists():
        cached = load_json(cp, None)
        if cached is not None:
            return cached
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            data = _http_json(url, timeout)
            if use_cache:
                cp.parent.mkdir(parents=True, exist_ok=True)
                cp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            return data
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise
        except Exception as exc:  # noqa: BLE001 - network/parse errors
            last = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise
    raise last if last else RuntimeError("retries exhausted")


class RateLimiter:
    """Minimal per-engine rate limiter with exponential backoff on 429/503."""

    def __init__(self, min_interval: float = 0.4):
        self.min_interval = min_interval
        self._last: dict[str, float] = {}

    def wait(self, engine: str) -> None:
        now = time.time()
        last = self._last.get(engine, 0)
        delta = self.min_interval - (now - last)
        if delta > 0:
            time.sleep(delta)
        self._last[engine] = time.time()


def get_inverted_abstract(inv) -> str:
    """OpenAlex stores abstracts as an inverted index; rebuild plain text."""
    if not isinstance(inv, dict):
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    if not pos:
        return ""
    return " ".join(pos[i] for i in sorted(pos))


# ─────────────────────────────────────────────────────────────────────────────
# Project structure
# ─────────────────────────────────────────────────────────────────────────────
def project_schema() -> dict:
    return {
        "topic": "",
        "pico": {},
        "engines": DEFAULT_ENGINES,
        "limit": DEFAULT_LIMIT,
        "years": [None, None],
        "queries": [],
        "use_cache": True,
        "timeout": 25,
        "created": utc(),
    }


def project_paths(project: Path) -> dict:
    return {
        "config": project / "config.json",
        "evidence_json": project / "evidence.json",
        "evidence_csv": project / "evidence_matrix.csv",
        "gaps_json": project / "gaps.json",
        "gaps_csv": project / "gaps.csv",
        "report": project / "report.md",
        "scores": project / "scores.json",
        "cache": project / ".cache",
    }


def _parse_pico(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def ensure_project(args) -> dict:
    project = Path(args.dir).expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)
    p = project_paths(project)
    cfg = load_json(p["config"])
    if cfg is None:
        cfg = {
            "topic": getattr(args, "topic", "") or "",
            "pico": _parse_pico(getattr(args, "pico", {})),
            "engines": DEFAULT_ENGINES,
            "limit": DEFAULT_LIMIT,
            "years": [None, None],
            "queries": [],
            "use_cache": True,
            "timeout": 25,
            "created": utc(),
        }
        write_json(p["config"], cfg)
    # ensure evidence/gaps json exist
    if not p["evidence_json"].exists():
        write_json(p["evidence_json"], {"papers": [], "fetched_at": None})
    if not p["gaps_json"].exists():
        write_json(p["gaps_json"], {"gaps": [], "computed_at": None})
    return {"project": project, "paths": p, "config": cfg}


def load_papers(project: Path) -> list[dict]:
    d = load_json(project / "evidence.json", {"papers": []})
    return d.get("papers", [])


def save_papers(project: Path, papers: list[dict]) -> None:
    write_json(project / "evidence.json", {"papers": papers, "fetched_at": utc()})
    write_evidence_csv(project, papers)


def write_evidence_csv(project: Path, papers: list[dict]) -> None:
    cols = ["id", "title", "authors", "year", "source", "source_id", "doi", "url",
            "abstract", "cited_by", "journal", "design", "population", "setting",
            "findings", "limitations", "gap_statement"]
    with open(project / "evidence_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for p in papers:
            row = {c: p.get(c, "") for c in cols}
            first = [str(x) for x in (p.get("authors") or []) if x]
            row["authors"] = "; ".join(first)
            w.writerow(row)


def load_gaps(project: Path) -> list[dict]:
    d = load_json(project / "gaps.json", {"gaps": []})
    return d.get("gaps", [])


def save_gaps(project: Path, gaps: list[dict]) -> None:
    write_json(project / "gaps.json", {"gaps": gaps, "computed_at": utc()})
    cols = ["id", "statement", "type", "secondary_type", "importance",
            "confidence", "sources", "research_question", "novelty_status"]
    with open(project / "gaps.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for g in gaps:
            row = {c: g.get(c, "") for c in cols}
            imp = g.get("importance") or {}
            row["importance"] = "; ".join(f"{k}={v}" for k, v in imp.items() if isinstance(imp, dict))
            srcs = [str(s) for s in (g.get("sources") or []) if s]
            row["sources"] = "; ".join(srcs)
            # JSON-safe nested fields
            if isinstance(g.get("secondary_type"), list):
                row["secondary_type"] = "; ".join(str(x) for x in g["secondary_type"])
            if isinstance(g.get("importance"), dict):
                row["importance"] = "; ".join(f"{k}={v}" for k, v in g["importance"].items())
            w.writerow(row)


def emit_paper(engine: str, source_id: str, title: str, authors, year, doi, url,
               abstract="", cited_by=0, journal=""):
    return {
        "id": title_key(title) or source_id,
        "title": re.sub(r"\s+", " ", (title or "")).strip(),
        "authors": authors or [],
        "year": year,
        "source": engine,
        "source_id": source_id,
        "doi": doi or "",
        "url": url or "",
        "abstract": abstract or "",
        "cited_by": int(cited_by or 0),
        "journal": journal or "",
        "design": "", "population": "", "setting": "", "findings": "",
        "limitations": "", "gap_statement": "",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Engines (key-free)
# ─────────────────────────────────────────────────────────────────────────────
def engine_openalex(project, query, limit, years, rl: RateLimiter) -> list[dict]:
    rl.wait("openalex")
    params = {"search": query, "per-page": min(limit, 200),
              "sort": "relevance_score:desc", "mailto": "agent@example.com"}
    if years and years[0]:
        params["from_publication_date"] = f"{years[0]}-01-01"
    if years and years[1]:
        params["to_publication_date"] = f"{years[1]}-12-31"
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = api_get_json(url, project)
    out = []
    for w in data.get("results", []):
        authors = [a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])]
        out.append(emit_paper(
            "openalex", w.get("id", "").split("/")[-1], w.get("title", ""), authors,
            w.get("publication_year"), w.get("doi", "").replace("https://doi.org/", ""),
            w.get("id", ""), get_inverted_abstract(w.get("abstract_inverted_index")),
            w.get("cited_by_count", 0), (w.get("primary_location") or {}).get("source", {}).get("display_name", "")))
    return out


def engine_crossref(project, query, limit, years, rl: RateLimiter) -> list[dict]:
    rl.wait("crossref")
    params = {"query": query, "rows": min(limit, 1000), "select": "DOI,title,author,issued,abstract,container-title"}
    if years and years[0]:
        params["filter"] = f"from-pub-date:{years[0]}-01-01"
    if years and years[1]:
        params["filter"] = (params.get("filter", "") + f",until-pub-date:{years[1]}-12-31").lstrip(",")
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = api_get_json(url, project)
    out = []
    for it in data.get("message", {}).get("items", []):
        authors = [f"{a.get('given','')} {a.get('family','')}".strip() for a in it.get("author", [])]
        year = None
        ip = it.get("issued", {}).get("date-parts", [[None]])
        if ip and ip[0]:
            year = ip[0][0]
        out.append(emit_paper(
            "crossref", it.get("DOI", ""), (it.get("title") or [""])[0], authors, year,
            it.get("DOI", ""), "https://doi.org/" + it.get("DOI", ""),
            re.sub(r"<[^>]+>", " ", it.get("abstract", ""))[:2000],
            0, (it.get("container-title") or [""])[0]))
    return out


def engine_europepmc(project, query, limit, years, rl: RateLimiter) -> list[dict]:
    rl.wait("europepmc")
    q = urllib.parse.quote(query)
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize={min(limit,1000)}"
    data = api_get_json(url, project)
    out = []
    for r in data.get("resultList", {}).get("result", []):
        authors = [r.get("authorString", "")]
        out.append(emit_paper(
            "europepmc", r.get("id", ""), r.get("title", ""), authors,
            r.get("pubYear"), r.get("doi", ""), "https://europepmc.org/article/MED/" + str(r.get("pmid", r.get("id", ""))),
            r.get("abstractText", ""), r.get("citedByCount", 0), r.get("journalInfo", {}).get("journal", {}).get("title", "")))
    return out


def engine_pubmed(project, query, limit, years, rl: RateLimiter) -> list[dict]:
    rl.wait("pubmed")
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    term = query
    if years and years[0]:
        try:
            lo = int(years[0])
            hi = int(years[1]) if years[1] else 3000
            term += f" AND {lo}/01/01:{hi}/12/31[dp]"
        except (TypeError, ValueError):
            pass
    es_url = f"{base}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(term)}&retmax={min(int(limit), 200)}&retmode=json"
    try:
        es = _http_json(es_url)
    except Exception:
        return []
    ids = es.get("esearchresult", {}).get("idlist", []) or []
    if not ids:
        return []
    su_url = f"{base}/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
    try:
        su = _http_json(su_url)
    except Exception:
        return []
    res = su.get("result", {})
    out = []
    for pid in ids:
        it = res.get(pid, {}) or {}
        if not it or str(it.get("uid")) != str(pid):
            continue
        doi = ""
        for aid in it.get("articleids", []) or []:
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        authors = []
        for a in it.get("authors", []) or []:
            name = f"{a.get('name','')}".strip()
            if name:
                authors.append(name)
        out.append(emit_paper(
            "pubmed", pid, it.get("title", ""), authors,
            (it.get("pubdate", "") or "")[:4], doi,
            "https://pubmed.ncbi.nlm.nih.gov/" + pid,
            it.get("abstracttext", ""), 0, it.get("fulljournalname", "")))
    return out


def engine_arxiv(project, query, limit, years, rl: RateLimiter) -> list[dict]:
    rl.wait("arxiv")
    url = ("https://export.arxiv.org/api/query?search_query=all:" + urllib.parse.quote(query)
           + f"&start=0&max_results={min(limit, 200)}")
    try:
        xml = _http_text(url)
    except Exception:
        return []
    root = ET.fromstring(xml)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    for e in root.findall("a:entry", ns):
        title = (e.findtext("a:title", "", ns) or "").replace("\n", " ").strip()
        summary = (e.findtext("a:summary", "", ns) or "").replace("\n", " ").strip()
        aid = (e.findtext("a:id", "", ns) or "").split("/abs/")[-1]
        authors = [a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)]
        published = e.findtext("a:published", "", ns)
        year = published[:4] if published else None
        doi = ""
        for link in e.findall("a:link", ns):
            if link.get("title") == "doi":
                doi = link.get("href", "").replace("https://doi.org/", "")
        out.append(emit_paper("arxiv", aid, title, authors, year, doi,
                              "https://arxiv.org/abs/" + aid, summary, 0, "arXiv"))
    return out


ENGINES = {
    "openalex": engine_openalex,
    "crossref": engine_crossref,
    "europepmc": engine_europepmc,
    "pubmed": engine_pubmed,
    "arxiv": engine_arxiv,
}


def dedupe_papers(papers: list[dict]) -> list[dict]:
    seen = {}
    merged = []
    for p in papers:
        key = (p.get("doi", "").lower() if p.get("doi") else "") or \
              title_key(p.get("title", "")) or p.get("source_id", "")
        if not key:
            continue
        if key in seen:
            # merge: prefer one that carries more info (abstract, cited_by, doi)
            cur = merged[seen[key]]
            for field in ("abstract", "cited_by", "journal", "authors"):
                if not cur.get(field) and p.get(field):
                    cur[field] = p[field]
            if not cur.get("doi") and p.get("doi"):
                cur["doi"] = p["doi"]
            if p.get("source") and p["source"] not in cur.get("sources", []):
                cur.setdefault("sources", []).append(p["source"])
            continue
        p.setdefault("sources", [p.get("source", "")])
        seen[key] = len(merged)
        merged.append(p)
    return merged


def run_search(args) -> int:
    global USE_CACHE, TIMEOUT
    st = ensure_project(args)
    project, paths, cfg = st["project"], st["paths"], st["config"]
    USE_CACHE = bool(cfg.get("use_cache", True))
    TIMEOUT = int(cfg.get("timeout", 25) or 25)
    query = args.query or cfg.get("topic", "")
    if not query:
        print("ERROR: no query (pass --query or set topic via init)", file=sys.stderr)
        return 1
    engines = [e for e in (args.engines or cfg.get("engines", DEFAULT_ENGINES)).split(",") if e] or DEFAULT_ENGINES
    limit = args.limit or cfg.get("limit", DEFAULT_LIMIT)
    years = [args.years[0], args.years[1]] if args.years else cfg.get("years", [None, None])
    rl = RateLimiter(0.7)
    new_papers = []
    failed = []
    for eng in engines:
        eng = eng.strip()
        if eng not in ENGINES:
            print(f"  [!] unknown engine '{eng}' (known: {', '.join(KNOWN_ENGINES)})")
            continue
        try:
            got = ENGINES[eng](project, query, limit, years, rl)
            print(f"  [ok] {eng:10s} -> {len(got)} results")
            new_papers.extend(got)
        except urllib.error.HTTPError as e:
            print(f"  [!] {eng:10s} HTTP {e.code} ({e.reason}) — skipped")
            failed.append(eng)
        except Exception as e:
            print(f"  [!] {eng:10s} error: {type(e).__name__}: {str(e)[:80]} — skipped")
            failed.append(eng)
    existing = load_papers(project)
    combined = dedupe_papers(existing + new_papers)
    save_papers(project, combined)
    cfg["queries"] = cfg.get("queries", []) + [{"query": query, "at": utc(), "engines": engines}]
    cfg["engines"] = engines
    cfg["limit"] = limit
    cfg["years"] = years
    write_json(paths["config"], cfg)
    print(f"\n  total evidence records: {len(combined)} (new {len(new_papers)})")
    if failed:
        print(f"  WARNING: engines unreachable: {', '.join(failed)} — continuing with the rest.")
    if not new_papers and len(combined) == 0:
        print("  ERROR: no results at all (offline or all engines failed). Run again with network.", file=sys.stderr)
        return 2
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Gap extraction + classification + importance scorificient
# ─────────────────────────────────────────────────────────────────────────────
def cue_statements(text: str) -> list[str]:
    """Return short cue sentences (limitations / future-work style) from a text."""
    if not text:
        return []
    # split into sentences
    sents = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sents:
        low = s.lower()
        if any(cue in low for cue in GAP_CUES):
            out.append(s.strip()[:300])
    return out[:6]


def classify_type(statement: str, context: str = "") -> tuple[str, list[str]]:
    hay = (statement + " " + context).lower()
    scores = {t: sum(1 for pat in pats if pat in hay) for t, pats in TAXONOMY.items()}
    order = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    top, second = order[0], order[1] if len(order) > 1 else ("", 0)
    if top[1] == 0:
        return "evidence", []
    secondary = [second[0]] if second[1] > 0 and second[0] != top[0] else []
    return top[0], secondary


def scores_from_importance(imp: dict) -> int:
    return int(sum(max(0, min(3, int(imp.get(d, 0) or 0))) for d in DIMENSIONS))


def default_importance(novelty_status: str = "unchecked", supported: int = 1) -> dict:
    """Baseline scores: transparent defaults the agent/human overrides via scores.json."""
    novel = {"checked_new": 3, "checked_seen": 1, "unchecked": 2}.get(novelty_status, 2)
    practical = 2 if supported >= 2 else 1
    return {
        "theoretical": 2, "practical": practical, "feasibility": 2,
        "novelty": novel, "coherence": 2,
        "estimated": True,
        "note": "Baseline heuristic scores — override via scores.json or the assess step.",
    }


def bootstrap_extract(st, args) -> list[dict]:
    papers = load_papers(st["project"])
    yes_no = "y"
    outs = []
    for p in papers:
        # build a candidate statement from abstract cue sentences + limitations field
        cues = cue_statements(p.get("abstract", ""))
        manual = p.get("gap_statement", "").strip()
        if manual:
            cues = [manual] + [c for c in cues if c != manual]
        # also derive a topic-level gap from the title if it literally signals absence
        low_title = (p.get("title", "") or "").lower()
        if any(k in low_title for k in ("gap", "understud", "unknown", "unexplored", "missing", "lack")):
            cues.append(f"Title signals a gap: {p.get('title','')}")
        for c in cues:
            outs.append({
                "id": "gap-" + hashlib.sha1((c + p.get("id", "")).encode()).hexdigest()[:10],
                "statement": c,
                "type": "", "secondary_type": [],
                "importance": {}, "confidence": "",
                "sources": [s for s in ([p.get("doi")] if p.get("doi") else [])],
                "source_paper_id": p.get("id", ""),
                "research_question": "", "novelty_status": "unchecked",
                "extracted": utc(),
            })
    return outs


def run_extract(args) -> int:
    st = ensure_project(args)
    cand = bootstrap_extract(st, args)
    existing = load_gaps(st["project"])
    # merge by id
    seen = {g.get("id") for g in existing}
    for c in cand:
        if c["id"] not in seen:
            existing.append(c)
    save_gaps(st["project"], existing)
    print(f"  evidence records processed: {len(load_papers(st['project']))}")
    print(f"  candidate gap statements: {len(cand)} (total stored {len(existing)})")
    return 0


def run_classify(args) -> int:
    st = ensure_project(args)
    project = st["project"]
    gaps = load_gaps(project)
    overrides = load_json(project / "scores.json", {})
    # optionally load a user scores file from --scores
    if getattr(args, "scores", None) and Path(args.scores).exists():
        overrides = load_json(Path(args.scores), overrides)
    any_controlled = False
    for g in gaps:
        stmt = g.get("statement", "")
        type_, secondary = classify_type(stmt, g.get("source_paper_title", ""))
        g["type"] = type_
        g["secondary_type"] = secondary
        if g["id"] in overrides:
            g["importance"] = overrides[g["id"]]
            g["importance"]["estimated"] = False
            any_controlled = True
        else:
            g["importance"] = default_importance(g.get("novelty_status", "unchecked"),
                                                 len(g.get("sources", [])))
        g["importance"]["total"] = scores_from_importance(g["importance"])
    save_gaps(project, gaps)
    n = len(gaps)
    print(f"  classified {n} gap candidate(s) into the six-type taxonomy")
    if not any_controlled:
        print("  NOTE: importance scores are baseline estimates (estimated=True).")
        print("        Supply per-gap 0-3 scores in scores.json (or --scores) to finalise.")
    return 0


def resolve_citation(doi: str, timeout: int = 20) -> bool:
    """Verify a DOI resolves via Crossref (no invented citations)."""
    if not doi:
        return False
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    try:
        _http_json(url, timeout)
        return True
    except Exception:
        return False


def run_validate(args) -> int:
    st = ensure_project(args)
    project, paths = st["project"], st["paths"]
    gaps = load_gaps(project)
    do_web = getattr(args, "check_web", False)
    seen_status = {"checked_new": 0, "checked_seen": 0, "unverified": 0}
    for g in gaps:
        sources = g.get("sources", [])
        verified = False
        for s in sources:
            if do_web and s:
                if resolve_citation(s):
                    verified = True
                    break
            elif s:
                verified = True  # a DOI/id is present; not network-verified
        # novelty check is a human/agent step; default stays 'unchecked' unless set
        status = g.get("novelty_status", "unchecked")
        # confidence rule (SKILL.md): high = >=2 independent sources & verified;
        # medium = 1 source; low = no resolvable source -> exploratory
        if not sources or not verified:
            conf = "Low"
            status = "unverified"
        elif len(sources) >= 2 and verified:
            conf = "High" if do_web else "Medium"
        else:
            conf = "Medium"
        g["confidence"] = conf
        g["verification"] = "web-validated" if do_web and verified else "identifier-present"
        if conf == "Low":
            g["exploratory"] = True
        seen_status[status if status in seen_status else "unverified"] = \
            seen_status.get(status if status in seen_status else "unverified", 0) + 1
    save_gaps(project, gaps)
    n = len(gaps)
    print(f"  validated {n} gap(s); confidence set per source-verification rules.")
    print(f"  novelty status distribution: {seen_status}")
    return 0


def run_rank(args) -> int:
    st = ensure_project(args)
    project = st["project"]
    gaps = load_gaps(project)
    min_total = args.min_total or 0
    min_conf = (args.min_confidence or "low").lower()
    order = {"low": 0, "medium": 1, "high": 2}
    ranked = []
    for g in gaps:
        total = scores_from_importance(g.get("importance", {}))
        g["importance"]["total"] = total
        if total < min_total:
            continue
        if order.get(g.get("confidence", "low").lower(), 0) < order.get(min_conf, 0):
            continue
        ranked.append(g)
    ranked.sort(key=lambda g: (-g["importance"].get("total", 0),
                               -order.get(g.get("confidence", "low").lower(), 0)))
    print(f"  ranked {len(ranked)} gap(s) that clear score>= {min_total} and confidence>= {min_conf}:")
    for i, g in enumerate(ranked[:args.top or 10], 1):
        print(f"   {i:>2}. [{g.get('confidence'):6s}] {g.get('importance',{}).get('total',0):>2}/15 "
              f"({g.get('type','?'):14s}) {g.get('statement','')[:100]}")
    return 0


def formulate_question(gap: dict) -> str:
    """Turn a gap into a falsifiable research question (PICO-aware placeholder)."""
    stmt = gap.get("statement", "").strip()
    type_ = gap.get("type", "")
    return f"How does {stmt[:220]}? What population, intervention/comparator, and outcome would test it — and under what [state the assumption]?"


def run_report(args) -> int:
    st = ensure_project(args)
    project, paths = st["project"], st["paths"]
    cfg = st["config"]
    gaps = load_gaps(project)
    top = args.top or 8
    ranked = sorted(gaps, key=lambda g: -g.get("importance", {}).get("total", 0))
    include = ranked[:top]

    # assemble per-gap RQ (fill blank ones)
    for g in include:
        if not g.get("research_question"):
            g["research_question"] = formulate_question(g)

    topic = cfg.get("topic", "")
    lines = [
        "# Research Gap Report",
        "",
        "**Skill:** research-gap-finder · **Tool:** research_gap_cli.py v" + VERSION,
        f"**Topic:** {topic or '(not set)'}",
        f"**Generated:** {utc()}",
        "",
        "> This report is produced by a reproducible, key-free scholarly-API",
        "> pipeline. Every gap is labeled with a confidence and its source",
        "> identifiers. **Gap identification is separate from importance** — the",
        "> importance scores below are baseline estimates unless overridden.",
        "",
        "## Executive summary",
        "",
        f"Candidate gaps identified: **{len(gaps)}**; shown: **{len(include)}** (top-ranked).",
        "",
        "## PICO / search horizon",
        "",
    ]
    if cfg.get("pico"):
        for k, v in cfg["pico"].items():
            lines.append(f"- **{k.capitalize()}:** {v}")
    lines += ["", "## Classified, importance-ranked gaps", ""]
    for i, g in enumerate(include, 1):
        imp = g.get("importance", {})
        lines += [
            f"### {i}. {g.get('statement','')}",
            "",
            f"- **Gap type:** {g.get('type','unclassified')}"
            + (f" / secondary: {', '.join(g.get('secondary_type', []))}"
               if g.get("secondary_type") else ""),
            f"- **Importance (five-dimension, 0-3 each / max 15):** "
            f"theoretical={imp.get('theoretical')}, practical={imp.get('practical')}, "
            f"feasibility={imp.get('feasibility')}, novelty={imp.get('novelty')}, "
            f"coherence={imp.get('coherence')} → **{imp.get('total', 0)}/15**"
            + (" *(estimated)*" if imp.get("estimated") else ""),
            f"- **Confidence:** {g.get('confidence','Low')}"
            + (" — **Exploratory/Hypothetical** (no independently verified source)" if g.get("exploratory") else ""),
            f"- **Novelty status:** {g.get('novelty_status','unchecked')}",
            f"- **Source evidence:** {', '.join(g.get('sources', [])) or 'no resolvable identifier (EXPLORATORY)'}",
            "",
            f"**Candidate research question:** {g.get('research_question','')}",
            "",
        ]
    lines += [
        "## Method & honesty constraints",
        "",
        "1. **Zero-invented citations.** A gap is only credited to a source with a",
        "   resolvable identifier (DOI / accession). Unverifiable gaps are marked",
        "   `Exploratory/Hypothetical`.",
        "2. **Identification ≠ importance.** Scores are separate and transparent.",
        "3. **Confidence labels.** High = ≥2 independent sources & resolved; Medium =",
        "   1 source; Low = no resolvable source.",
        "4. **Absence ≠ algorithm failure.** A missed paper may be a search artifact;",
        "   cross-check with the AHRQ framework before treating it as a real gap.",
        "5. **Importance defaults are estimates.** Provide per-gap scores to finalise.",
        "",
        "## Limitations",
        "",
        "- This report reflects the queries and engines run at generation time; a",
        "  different horizon yields different gaps.",
        "- Key-free API coverage (OpenAlex, Crossref, Europe PMC, arXiv, PubMed) is",
        "  metadata-level; it does not replace a full systematic review.",
        "",
    ]
    if not include:
        lines += ["*No gaps found — run `search`, `extract`, `classify`, `validate` first.*"]
    text = "\n".join(lines)
    out = Path(args.out) if getattr(args, "out", None) else paths["report"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"  report written: {out}")
    return 0


def run_status(args) -> int:
    st = ensure_project(args)
    project, paths = st["project"], st["paths"]
    papers = load_papers(project)
    gaps = load_gaps(project)
    cfg = st["config"]
    print(f"  project: {project}")
    print(f"  topic:   {cfg.get('topic','(not set)')}")
    print(f"  evidence records: {len(papers)} ; gaps: {len(gaps)}")
    by_src = {}
    for p in papers:
        by_src[p.get("source", "?")] = by_src.get(p.get("source", "?"), 0) + 1
    print("  evidence by source:", by_src)
    return 0


def run_selftest(args) -> int:
    import tempfile
    d = Path(args.dir or tempfile.mkdtemp(prefix="rgf-selftest-")) / "proj"
    d.mkdir(parents=True, exist_ok=True)
    # seed a tiny synthetic evidence set (stdlib only) and run extract/classify/validate/report
    papers = [
        emit_paper("openalex", "w1", "Impact of X intervention on outcomes", ["A"],
                   2021, "10.1000/x1", "https://example/w1",
                   "We found limited evidence that X is effective; however, small sample "
                   "size and no control group limit conclusions. Future work should test "
                   "in rural populations."),
        emit_paper("crossref", "10.1000/x2", "A gap in the literature on Y", ["B"],
                   2020, "10.1000/x2", "https://doi.org/10.1000/x2",
                   "Little is known about the mechanism of Y. More studies are needed in "
                   "low-resource settings; implementation into practice remains unaddressed."),
    ]
    save_papers(d, papers)
    class NS: pass
    ns = NS(); ns.dir = str(d)
    st = ensure_project(ns)
    # extract
    gobj = NS(); gobj.dir = str(d)
    candidates = bootstrap_extract(st, gobj)
    save_gaps(d, candidates)
    # classify
    for g in load_gaps(d):
        stmt = g.get("statement", "")
        type_, secondary = classify_type(stmt)
        g["type"] = type_
        g["secondary_type"] = secondary
        g["importance"] = default_importance("checked_new", len(g.get("sources", [])))
        g["importance"]["total"] = scores_from_importance(g["importance"])
        g["confidence"] = "Medium"
        g["research_question"] = formulate_question(g)
    save_gaps(d, load_gaps(d))
    n_gaps = len(load_gaps(d))
    # report
    nsobj = NS(); nsobj.dir = str(d); nsobj.top = 8; nsobj.out = str(d / "report.md")
    run_report(nsobj)
    rep = (d / "report.md").read_text(encoding="utf-8")
    ok = n_gaps >= 1 and "Research Gap Report" in rep and "Candidate research question" in rep
    print(f"  self-test: {n_gaps} gap(s) generated; report ok={ok}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="research_gap_cli.py", description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ["init", "search", "extract", "classify", "validate", "rank", "report", "status", "selftest"]:
        pass
    # dir is common
    def add_dir(sp):
        sp.add_argument("--dir", required=True, help="Project directory")

    sp = sub.add_parser("init", help="Create a research-gap project.")
    add_dir(sp); sp.add_argument("--topic", required=True); sp.add_argument("--pico", default="{}")
    sp = sub.add_parser("search", help="Query key-free scholarly APIs and build the evidence matrix.")
    add_dir(sp); sp.add_argument("--query"); sp.add_argument("--engines", default=None)
    sp.add_argument("--limit", type=int); sp.add_argument("--years", nargs=2, type=int)
    sp = sub.add_parser("extract", help="Extract candidate gap statements from evidence records.")
    add_dir(sp); sp.add_argument("--cuefile")
    sp = sub.add_parser("classify", help="Assign the six-type taxonomy and importance rubric scores.")
    add_dir(sp); sp.add_argument("--scores")
    sp = sub.add_parser("validate", help="Verify source identifiers and set confidence labels.")
    add_dir(sp); sp.add_argument("--check-web", action="store_true")
    sp = sub.add_parser("rank", help="Rank gaps by importance x confidence.")
    add_dir(sp); sp.add_argument("--min-total", type=int); sp.add_argument("--top", type=int)
    sp.add_argument("--min-confidence", choices=["low", "medium", "high"])
    sp = sub.add_parser("report", help="Emit the Markdown gap report.")
    add_dir(sp); sp.add_argument("--top", type=int); sp.add_argument("--out")
    sp = sub.add_parser("status", help="Show project state.")
    add_dir(sp)
    sp = sub.add_parser("selftest", help="Run an offline self-test.")
    sp.add_argument("--dir")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command
    dispatch = {
        "init": _init_msg,
        "search": run_search,
        "extract": run_extract,
        "classify": run_classify,
        "validate": run_validate,
        "rank": run_rank,
        "report": run_report,
        "status": run_status,
        "selftest": run_selftest,
    }
    try:
        return dispatch[cmd](args)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


def _init_msg(args) -> int:
    st = ensure_project(args)
    print(f"  project initialised: {st['project']}")
    print(f"  topic: {st['config'].get('topic')}")
    print("  next: run `python3 scripts/research_gap_cli.py search --dir <proj> --query \"...\"`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
