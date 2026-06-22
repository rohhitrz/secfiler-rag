# PROGRESS.md — secfiler-rag

> **This document is the source of truth for project state across chat sessions with Claude.**
> Update at the end of every meaningful work session. Commit it.

---

## Project at a glance

- **Goal:** Production-grade, full-stack RAG system over SEC 10-K filings (Apple, Microsoft, Tesla). Deployable, with eval numbers, citation-backed answers, and a Next.js frontend.
- **Owner:** Rohit (`rohhitrz` on GitHub) — MERN dev (~6 months backend), learning AI engineering. North star: hireable as a remote AI engineer.
- **Mentor:** Claude, operating under the S2 RAG session contract (see "Working Rules" below).
- **Repo (local):** `/Users/rohit/Desktop/secfiler-rag`
- **Repo (remote):** **LIVE — public at github.com/rohhitrz/secfiler-rag** (pushed Chat 3).

---

## Locked decisions (don't relitigate)

| Decision | Choice | Rationale |
|---|---|---|
| Corpus | Apple + Microsoft + Tesla 10-Ks (latest = **all FY2025**) | Real, messy, sellable use case |
| Vector DB | Qdrant in Docker (`qdrant/qdrant:v1.18.2`) | Production-grade, native hybrid, first-class metadata filtering |
| Embedding model (baseline) | OpenAI `text-embedding-3-small` | Cheap, fast, strong baseline. Voyage `voyage-finance-2` is the measured-upgrade candidate |
| Reranker (Module 6) | Cohere Rerank | Free tier covers learning. `bge-reranker-large` is the self-hosted alternative |
| BM25 library | `rank-bm25` (Module 4) | Pure Python, dependency-free, perfect for our vectorless baseline |
| HTML parsing | BeautifulSoup4 + `html.parser` | Standard, handles malformed markup; `html.parser` = zero extra deps, fine for 1–8MB files. lxml NOT needed (verified `^ix:` regex works under html.parser) |
| Web framework | FastAPI | Async-native, Pydantic-validated, OpenAPI docs built-in |
| Python | 3.13 | Already installed; ecosystem supports it as of mid-2026 |
| Package manager | `uv` (project-local `.venv/`) | Fast, lockfile-based, modern Python standard |
| Eval set | Hand-write 25 Q/A first (Module 9), then FinDER | Writing your own Q/A teaches what good eval looks like |
| Frontend (Module 11) | Next.js 14+ App Router | Differentiator over backend-only portfolios — Rohit's MERN edge |
| Failure-modes framework | Adopted as recurring lens (5 modes: bad chunking / embedding mismatch / retrieval noise / context overflow / hallucination) | Senior interview framing for diagnosing RAG failures |

### Syllabus additions vs. original spec (from reviewing pdichone repos)
- **Module 5.5 (NEW):** Contextual Retrieval (Anthropic's technique) — added between vector RAG and hybrid
- **Module 12 (extended):** Response caching pattern from `lang-production-api/test_cache_demo.py`
- **Module 3 (reordered):** Production-shape repo from commit #1, inspired by `lang-production-api/` layout

---

## What's built so far

### ✅ Modules 0–2 (done)
- M0 Plan & opening checkpoint; M1 Big Picture & Market Context; M2 Foundations & Mental Models (embeddings, vector space, cosine sim, chunking strategies, vectorless vs vector). All checkpoints passed. (Full detail in prior PROGRESS versions / repo history.)

### ✅ Module 3 — Stack & Repo Setup (COMPLETE — all 4 phases)
- Phase 1: tool decisions defended. Phase 2: `uv init` scaffold, `pyproject.toml`, full `src/secfiler_rag/{api,core,rag,models}` layout, comprehensive `.gitignore`, branch `main`. Phase 3: Docker + Qdrant `v1.18.2` via docker-compose, persistent volume, verified. Phase 4: deps (`fastapi`, `uvicorn[standard]`, `pydantic-settings`, `qdrant-client`), `.env`/`.env.example`, typed `config.py` (pydantic-settings v2), `main.py` with `GET /` + async `GET /health` (real `AsyncQdrantClient` connectivity check, 200/503 both curl-verified).
- Commits through `f419ea4`.

### 🔄 Module 4 — Vectorless Baseline (BM25) — IN PROGRESS

**Conceptual foundation (DONE):**
- What BM25 is: lexical ranking — TF (with k1 saturation) + IDF (down-weight common, up-weight rare) + length normalization (b). No meaning, bag-of-words.
- Why baseline-first (rule #5): vectors aren't free/always better; can't claim vectors helped without a measured baseline (rule #8); BM25 wins exact-terminology/defined-term queries; scaffolding (load/chunk/eval) is reused by the vector retriever anyway.
- What BM25 *cannot* do: synonymy ("earnings" ≠ "net income"), paraphrase, word-order (bag-of-words), cross-lingual. **Canonical eval query to watch vectors beat BM25: "How did Apple's earnings change YoY?" — filing says "net income," BM25 scores ~0.**
- Failure-modes mapping: BM25 attacks **retrieval noise**; defenseless vs **embedding mismatch**/synonymy (that's Module 5's job); downstream of **bad chunking**.
- Checkpoint passed (BM25-wins-vs-loses-badly query construction; "exact number" tightened → "exact terminology/defined terms" — numbers ride along, words rank).

**GitHub push (DONE — repo now public):**
- `gh`/manual push completed; `main` tracks `origin/main`. NOTE: a throwaway commit `4b6de52 "first commit"` (one-line README) sits in history from the push step — cosmetic blemish, left as-is (already public, not worth history rewrite). Going forward: atomic messages only.
- `.env` confirmed untracked; `git ls-files | grep -i env` shows only `.env.example`. No secret leak.

**Corpus sourcing (DONE):**
- Learned EDGAR by hand: CIK, filing-list vs single-filing-index distinction, the rigid `Item N` 10-K structure (Part I–IV; Item 1A Risk Factors, Item 7 MD&A = where eval answers live; Item 8 = tables, handled poorly by BM25/naive chunking — note for later).
- The `ix?doc=` URL is the inline-XBRL **viewer**; strip `ix?doc=` → raw `/Archives/...` `.htm` is what we save.
- **EDGAR requires a User-Agent header** on automated requests (name + email) or it blocks/empties the response.
- Three raw filings downloaded via `curl -A "Rohit <email>"` into `data/raw/`, renamed company-keyed:
  - `aapl-2025.htm` (1.4M) — CIK 320193, accession 000032019325000079, FY ended 2025-09-27
  - `msft-2025.htm` (7.8M) — CIK 789019, accession 000095017025100235, FY ended 2025-06-30
  - `tsla-2025.htm` (2.3M) — CIK 1318605, accession 000162828026003952, FY ended 2025-12-31
  - (All three are FY2025. Fiscal-year-ends differ — Sep/Jun/Dec — so eval questions must be **company-scoped**, not "compare FY2025 across all three.")

**`data/` dir + gitignore (DONE):**
- `data/raw/` for source HTML (gitignored), `data/.gitkeep` tracked to preserve skeleton.
- gitignore gotcha learned: `data/` (directory ignore) makes git refuse to descend → `!data/.gitkeep` can't rescue. Fix = **contents-pattern**: `data/*` + `!data/.gitkeep`.
- **Commit `009f60d`** — "Add gitignored data/ directory for raw filings".

**`load_filing_text()` — HTML/XBRL → clean text (DONE & VERIFIED on all 3):**
- File: `src/secfiler_rag/rag/ingest.py`. First of TWO single-responsibility ingestion functions (strip is separate from chunk — they change for different reasons; chunker will be rewritten many times, cleaner stays frozen).
- Reads via `Path(path).read_text(encoding="utf-8")`; `BeautifulSoup(content, "html.parser")`; decomposes `script`/`style`/`head` AND the entire inline-XBRL namespace (`soup.find_all(re.compile(r"^ix:"))`); `get_text(separator=" ", strip=True)` then `" ".join(text.split())`.
- **The lesson:** raw `.get_text()` leaked XBRL junk (`fasb.org/us-gaap/...` taxonomy URLs, `P1Y` period markers, CIK, flags). Diagnosed by reading `print(repr(text[:500]))` — the junk's *vocabulary* (URLs/type-codes/IDs) fingerprints its source (the `ix:` machine-data layer). Method to keep: extract → `repr` the output → read the junk → trace to its tag → decompose → re-verify.
- Verified clean on all three: each opens with "UNITED STATES SECURITIES AND EXCHANGE COMMISSION Washington, D.C. 20549". Clean char counts: AAPL 158,914 · MSFT 215,979 · TSLA 238,562. (MSFT's 7.8MB raw → 216K clean confirms bloat was markup, not content.)
- Known cosmetic artifacts (NOT bugs, left as-is): cover-page XBRL-tagged *values* (fiscal-year-end date, file number) are blank because their `ix:` tags were correctly decomposed — fine, we're not extracting financials from XBRL here. MSFT surfaces one markdown-style `<a>` link. Harmless for BM25.
- **Commit `f084485`** — "Add load_filing_text: strip HTML/XBRL from raw 10-Ks".

---

## Current state

- **Branch:** `main`. **Latest commit:** `f084485`. Local `main` is **~3 commits ahead of `origin/main`** (origin last saw `4b6de52`) — push at next natural break.
- **Working tree:** clean.
- **Qdrant:** running on `:6333`/`:6334` (`docker compose ps` → Up). Dashboard `http://localhost:6333/dashboard`.
- **FastAPI app:** boots, serves `GET /` + async `GET /health`. Run: `uv run uvicorn secfiler_rag.main:app --reload`.
- **Deps installed:** fastapi, uvicorn[standard], pydantic-settings, qdrant-client, **beautifulsoup4** (added Chat 3). lxml NOT installed (not needed).
- **Corpus:** 3 raw 10-Ks in `data/raw/` (gitignored), all FY2025, all verified-clean through `load_filing_text`.
- **Local files NOT in git (intentional):** `.env`, `.venv/`, `qdrant_storage/`, `.vscode/`, `data/raw/*`.

---

## What's next (immediate)

**Resume at: Module 4 — the CHUNKER (step 2 of 2 of ingestion). This is a big implement-it-yourself beat.**

### Immediate sequence:
1. **(optional housekeeping)** `git push` to sync origin (local is ~3 ahead).
2. **Spec + implement the chunker** — second ingestion function, takes the clean text from `load_filing_text` and splits into chunks. Raw Python first (rule #4 — NO LangChain text splitter yet). Open question to decide at spec time: chunk strategy. The 10-K's rigid `Item N` structure is a natural **structure-aware** boundary candidate vs. fixed-size/recursive. Decide and justify. Consider: chunk size, overlap, whether to attach metadata (company ticker, which Item) to each chunk — metadata matters because eval is company-scoped and Qdrant filtering will use it later.
3. **Build the BM25 index** over the chunks (`rank-bm25`, locked). Raw mechanics first.
4. **Run a baseline retrieval query** — first honest retrieval numbers. Likely use the "earnings vs net income" query to *demonstrate* BM25's synonymy blind spot live (sets up Module 5).

### Known prerequisites/notes for the chunker:
- `load_filing_text` returns one flat string per filing — no structure preserved yet. If we want structure-aware chunking by `Item`, the chunker (or a helper) needs to *detect* Item boundaries in the flat text (regex on "Item 1A." etc.) — or we accept fixed/recursive for the baseline and revisit. Decide at spec.
- Tables (Item 8) survive as mangled inline text after stripping — flag for later, don't solve in baseline.

---

## Open questions / known gotchas

- **Throwaway `4b6de52 "first commit"` in public history** — cosmetic, left as-is.
- **`except Exception as e` in `/health`** — `e` unused (cosmetic; can drop `as e`). Non-blocking.
- **`qdrant/qdrant:v1.18.2` pinned** — evaluate `-unprivileged` variant at deploy (Module 12).
- **`requires-python = ">=3.13"`** — aggressive; soften to `>=3.12` if deploy platform lacks 3.13.
- **No tests yet** — `tests/test_health.py` is the natural first; `tests/test_ingest.py` (assert clean text, no `fasb.org`/`<` in output) is a natural second now that ingest exists.
- **No `.dockerignore`** — needed when FastAPI Dockerfile lands (Module 12).
- **No formatter run** — minor PEP 8 nits across files (`app=FastAPI`, tight dict colons). A `ruff`/`black` pass cleans in one shot; deferred low-priority. (Reference `ingest.py` already hoists constants + orders imports if you want to match it.)

---

## Working rules (the contract — must be respected in every session)

1. **Spec → Rohit implements the entire function/file → Claude reviews like senior code review → reference AFTER the attempt, never before.**
2. **No line-by-line dictation.** Function-level building.
3. **No pasted code before Rohit attempts.** In learning mode, Claude refuses to "just write it."
4. **Raw Python before framework.** Build chunking/embedding/similarity/prompt-assembly from scratch ONCE, then show the LangChain version.
5. **Vectorless before vector.** Honest baseline first.
6. **Production-shape from commit #1.** No "refactor later."
7. **Docker from the start.**
8. **Eval numbers before bragging.** Module 9 is the truth gate.
9. **Every module/sub-step ends with a checkpoint** — Rohit answers/implements BEFORE the reference appears.
10. **Rohit never keeps a line he can't explain.**
11. **No interview Q&A in public READMEs.**
12. **Failure-modes framework as recurring lens** — name which mode each feature kills (and flag when a feature is *operational*, e.g. config/`/health`, not one of the 5 RAG-quality modes).
13. **Audit Claude.** Rohit catches imprecision; Claude tightens immediately. (Chat 3 examples: Claude was stale on fiscal years — trust EDGAR over Claude's memory on "latest filing"; Claude can't fabricate accession-number URLs.)
14. **Hold-questions go at the END of a sub-step, in their own clearly-marked block, after the commit step** — Rohit answers them as the closing beat before moving on.
15. **(NEW Chat 3) Hold-questions must be VISUALLY DISTINCT and impossible to miss** — render them under a clear marked header (e.g. a `### ⛳ HOLD-QUESTIONS — answer before we move on` block, or bold/blockquote), not as plain trailing prose. Rohit reported they get lost when he's heads-down implementing and pasting back; this is a process fix, not a focus problem. Claude restates them if a reply skips them.

### Handoff protocol (Claude owns this)
1. Update PROGRESS.md (full state, latest commit) — real downloadable file artifact.
2. Fresh NEXT_CHAT_KICKOFF.md reflecting exact resume point — real file artifact.
3. SESSION_BRIEF.md only if rules/decisions fundamentally changed (rule #15 added Chat 3 — fold into BRIEF next regeneration; captured here meanwhile).
4. Proactively flag "context getting tight" at ~60–70% (Rohit opted to push to ~80% in Chat 3 — honor his stated budget but never past safe limits).
5. Hand off at a clean milestone (after a commit / end of sub-step), not mid-implementation.

### Steering commands
`next` · `deeper` · `expand this point` · `skip` · `code` (build mode) · `quiz me` · `real-world` · `hireable?` · `product` · `reset rules`

### Anti-patterns Claude must avoid
- Dumping multiple modules at once
- Jumping to mechanics before "what is this" foundation
- Bloated overwhelming examples
- Over-correcting after feedback (the 1–2 word → 80-word swing)
- Vibes-words without backing ("sane," "clean," "magic")
- Re-litigating settled decisions
- Pushing past safe context — proactively hand off

---

## Reference repos (use as guides, REBUILD never clone)

- **`pdichone/production-course-main-code`** — technique grab-bag; key file `rag_pipeline.py` (rebuild from blank).
- **`pdichone/fcc-production-rag-part-6`** — 2026 advanced; building from `02_contextual_retrieval.py` (M5.5) + `04_agentic_rag.py` (M8); reading-only the rest.
- **`pdichone/lang-production-api`** — production-shape template; stealing `app/` layout, `render.yml`, `test_cache_demo.py` caching. NOT copying Streamlit UI (we use Next.js).

**Flag:** these repos use ChromaDB + Streamlit. We use Qdrant + Next.js. Translate patterns, don't copy API calls.

---

## File map (current)

```
secfiler-rag/
├── .env                       ← gitignored, real OPENAI_API_KEY
├── .env.example               ← committed, template
├── .gitignore                 ← comprehensive; data/* + !data/.gitkeep added Chat 3
├── .python-version            ← "3.13"
├── docker-compose.yml         ← Qdrant v1.18.2 pinned
├── pyproject.toml             ← 5 deps (added beautifulsoup4)
├── uv.lock                    ← committed
├── README.md                  ← one-line placeholder (from throwaway commit)
├── PROGRESS.md                ← THIS FILE (commit the updated version)
├── data/
│   ├── .gitkeep               ← tracked
│   └── raw/                   ← gitignored: aapl-2025.htm, msft-2025.htm, tsla-2025.htm
├── qdrant_storage/            ← gitignored
├── src/
│   └── secfiler_rag/
│       ├── __init__.py        ← __version__
│       ├── main.py            ← FastAPI app, GET / + GET /health (async)
│       ├── config.py          ← typed Settings (pydantic-settings)
│       ├── api/__init__.py
│       ├── core/__init__.py
│       ├── rag/
│       │   ├── __init__.py
│       │   └── ingest.py      ← DONE: load_filing_text (HTML/XBRL strip). NEXT: chunker here.
│       └── models/__init__.py
└── tests/
    └── __init__.py            ← no tests yet
```

---

*Last updated: end of Chat 3 (Module 4 in progress — repo pushed public, corpus sourced + cleaned, `load_filing_text` done & verified on all 3 filings, latest commit `f084485`). Next: the chunker (step 2 of ingestion), then BM25 index, then baseline retrieval query. Update at the end of every session.*