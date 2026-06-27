# PROGRESS.md — secfiler-rag

> **This document is the source of truth for project state across chat sessions with Claude.**
> Update at the end of every meaningful work session. Commit it.

---

## Project at a glance

- **Goal:** Production-grade, full-stack RAG system over SEC 10-K filings (Apple, Microsoft, Tesla). Deployable, with eval numbers, citation-backed answers, and a Next.js frontend.
- **Owner:** Rohit (`rohhitrz` on GitHub) — MERN dev (~6 months backend), learning AI engineering. North star: hireable as a remote AI engineer.
- **Mentor:** Claude, operating under the S2 RAG session contract (see "Working Rules" below).
- **Repo (local):** `/Users/rohit/Desktop/secfiler-rag`
- **Repo (remote):** **LIVE — public at github.com/rohhitrz/secfiler-rag**.

---

## Locked decisions (don't relitigate)

| Decision | Choice | Rationale |
|---|---|---|
| Corpus | Apple + Microsoft + Tesla 10-Ks (latest = **all FY2025**) | Real, messy, sellable use case |
| Vector DB | Qdrant in Docker (`qdrant/qdrant:v1.18.2`) | Production-grade, native hybrid, first-class metadata filtering |
| Embedding model (baseline) | OpenAI `text-embedding-3-small` (**1536-dim**) | Cheap, fast, strong baseline. Voyage `voyage-finance-2` is the measured-upgrade candidate |
| Reranker (Module 6) | Cohere Rerank | Free tier covers learning. `bge-reranker-large` is the self-hosted alternative |
| BM25 library | `rank-bm25` (`BM25Okapi`) | Pure Python, dependency-free, perfect for our vectorless baseline |
| HTML parsing | BeautifulSoup4 + `html.parser` | Standard, handles malformed markup; zero extra deps. lxml NOT needed |
| Web framework | FastAPI | Async-native, Pydantic-validated, OpenAPI docs built-in |
| Python | 3.13 | Already installed; ecosystem supports it |
| Package manager | `uv` (project-local `.venv/`) | Fast, lockfile-based, modern Python standard |
| Eval set | Hand-write 25 Q/A first (Module 9), then FinDER | Writing your own Q/A teaches what good eval looks like |
| Frontend (Module 11) | Next.js 14+ App Router | Differentiator over backend-only portfolios — Rohit's MERN edge |
| Failure-modes framework | 5 modes: bad chunking / embedding mismatch / retrieval noise / context overflow / hallucination | Senior interview framing for diagnosing RAG failures |
| Chunk strategy (baseline) | **Fixed-size + overlap (1000 chars / 200 overlap), raw Python** | Honest simple baseline. ~800 chars/chunk effective stride (1000−200). Structure-aware + semantic flagged as LATER experiments |
| Chunk shape | **`dict`: `{"text", "company", "chunk_id"}`** | Metadata-carrying records. company scopes eval + Qdrant filtering |
| Tokenizer (BM25) | **`lowercase + re.findall(r"[a-z0-9]+")`, raw Python, in `retrieve.py`** | Single shared tokenizer for BOTH index + query (symmetry mandatory) |
| Eval item shape | **`{"query", "expected_substring", "company"}`** | Substring answer key (Option B). Survives re-chunking. Substrings must be **distinctive + forgiving**, sourced from CLEANED text never browser |
| Eval set tiers | **Tier 1 (lexical sanity) + Tier 2 (natural-language)** | Tier 1 = near-tautological regression guards + harness smoke test. Tier 2 = realistic phrasing, the number that should move |
| Eval harness shape | **`evaluate(eval_set, search_fn, top_k)` — retriever-agnostic** | Harness takes retrieval fn as a param, never mentions BM25/vectors/company. Caller builds the index + passes a `search_fn` adapter. **FROZEN — never add domain knowledge to it.** |
| Eval code location | **`src/secfiler_rag/rag/evaluate.py` (harness) + `evals/eval_set.py` (data)** | Eval is version-controlled measurement infra. Harness/data split |
| Company casing convention | **lowercase everywhere (`"aapl"`, `"msft"`, `"tsla"`)** — ENFORCED | Matches eval items + filenames. Kills silent Qdrant filter-mismatch. **Hold it everywhere.** |
| **Qdrant point id** | **`str(uuid5(NAMESPACE_DNS, f"{company}-{chunk_id}"))`** — DECIDED & SHIPPED Chat 7 | Deterministic → collision-proof across companies + idempotent re-index (re-run overwrites in place, no duplication). Replaced the `id=i` scheme (which collided: every company restarted at 0). **Separator (`-`) is load-bearing — changing it changes every id → duplicates a parallel set.** |
| Indexing client vs search client | **sync `QdrantClient` for `index.py` (batch); `AsyncQdrantClient` for the FastAPI served path** | Indexing is a batch script outside any request path. Served search is in the event loop → async mandatory. NEVER sync-client-with-`await`. |
| **Company scoping (multi-company retrieval)** | **Option A — payload filter on single `filings` collection** (NOT per-company collections) — DECIDED & SHIPPED Chat 7 | Soft query-time boundary (flexible) beats hard storage boundary (rigid). A single query can widen/narrow/drop the company filter; per-company collections would force manual fan-out + merge for any cross-company query. Less re-architecting too — one collection already indexed. |

### Syllabus additions / reorders vs original spec
- **Module 5.5 (Contextual Retrieval) — MOVED TO THE VERY END** (Chat 7 decision). It's a measured-LIFT experiment; lift is only meaningful on a stable core. Will run as an extras/polish pass *after* the full RAG is built, not between vector and hybrid. Ref `pdichone/fcc-production-rag-part-6/02_contextual_retrieval.py`.
- **Module 12 (extended):** Response caching pattern from `lang-production-api/test_cache_demo.py`
- **Module 3 (reordered):** Production-shape repo from commit #1

---

## What's built so far

### ✅ Modules 0–2 (done)
Plan, big picture/market context, foundations (embeddings, vector space, cosine sim, chunking strategies, vectorless vs vector). All checkpoints passed.

### ✅ Module 3 — Stack & Repo Setup (COMPLETE)
`uv init` scaffold, full `src/secfiler_rag/{api,core,rag,models}` layout, `.gitignore`, branch `main`. Docker + Qdrant `v1.18.2` via docker-compose, persistent volume. Deps: fastapi, uvicorn[standard], pydantic-settings, qdrant-client. Typed `config.py` (pydantic-settings v2). `main.py` with `GET /` + async `GET /health` (real `AsyncQdrantClient` check, 200/503 verified).

### ✅ Module 4 — Vectorless Baseline (BM25) + Eval Harness — COMPLETE
- **Ingestion:** `load_filing_text()` strips HTML + inline-XBRL via BeautifulSoup (clean chars: AAPL 158,914 · MSFT 215,979 · TSLA 238,562). `chunk_text(text, company, chunk_size=1000, overlap=200) -> list[dict]`, fixed-size + overlap, returns `{"text","company","chunk_id"}`.
- **BM25 `retrieve.py`:** `tokenize()` (shared), `build_bm25_index() -> BM25Okapi`, `search(query, bm25, chunks, top_k=5) -> list[dict]`.
- **Eval harness:** `evals/eval_set.py` + retriever-agnostic `evaluate(eval_set, search_fn, top_k=3)` in `rag/evaluate.py`. Prints per-item PASS/FAIL+rank AND returns `{recall_at_k, hits, total, results}`.
- **BASELINE LOCKED: BM25 Recall@3 = 75% (3/4 AAPL).** Blind-spot ("total revenue"→"net sales") fails by design. Commit `bdb7885`.
- **Process lesson:** eval substrings must come from CLEANED text, never the rendered browser page.

### ✅ Module 5 — Vector Retrieval — **COMPLETE (multi-company, audited)**

**Concept (Chat 6):** embedding = text→1536-dim vector positioned by meaning. Cosine = dot/(norm·norm). OpenAI vectors pre-normalized → Qdrant metric = Cosine.

**`embed.py` (Chat 6):** `embed_texts(texts) -> list[list[float]]` — batched OpenAI call, `text-embedding-3-small`, **sorted by `.index`** (prevents silent vector↔chunk misalignment). `cosine(a,b)` raw `math`. Proof: `net sales ↔ total revenue = 0.539` vs `↔ banana = 0.176`. Commit `0e95dcb`.

**`index.py` (Chat 6 → multi-company Chat 7):**
- `get_or_create_collections()` — non-destructive, collection `"filings"`, size 1536, Cosine. **Outside the company loop** (one shared collection).
- `index_chunks(client, name, chunks)` — batched `embed_texts` (ONE API call per company), one `PointStruct` per chunk, `id = str(uuid5(NAMESPACE_DNS, f"{company}-{chunk_id}"))`, single `upsert`.
- `__main__` — loops `['aapl','msft','tsla']`, loads `data/raw/{c}-2025.htm`, chunks lowercase, indexes, then **per-company `client.count` with payload filter** (Rule #13). **VERIFIED: aapl=199, msft=270, tsla=299.**
- **Chat 7 collision caught live:** first multi-run showed `aapl: 398` — the old `id=i` (int) points from Chat 6 didn't overwrite under the new uuid5 (str) scheme → duplication (uuid4-style failure, self-inflicted by scheme change). Fix: one-time `client.delete_collection("filings")` + clean rebuild → aapl back to 199. **The `delete_collection` line was a manual one-off, removed from `__main__` (would nuke + re-embed every run).** Commit `60a7c8d`.

**`search.py` (Chat 6 → company-scoped Chat 7) — THE NUMBER:**
- `vector_search(query, company, top_k=3) -> list[dict]` — embeds query (`embed_texts([query])[0]`, same model = symmetry), builds `Filter(must=[FieldCondition(key="company", match=MatchValue(value=company))])`, passes as `query_filter` to `query_points` (note: `query_filter` for query_points vs `count_filter` for count). Reshapes points to `{**payload, "score": score}`.
- **Caller (`__main__`):** `company_by_query = {item["query"]: item["company"] for item in EVAL_SET}` + named `search_fn(query, top_k)` that resolves company internally and calls `vector_search(query, company, top_k)`. **`evaluate` signature UNCHANGED** — caller absorbs all company knowledge (retriever-agnostic contract held). Single named fn, no lambda → sidesteps late-binding closure bug.

  **🎯 RESULT: Vector Recall@3 = 100% (8/8) across aapl/msft/tsla.** Company routing verified non-cross-contaminating (each query filtered to its own company). Commit `af40542`.

  **Every pass AUDITED at chunk level (Rule #13 — read the chunk, don't trust the check):**
  - aapl `total revenue`→ chunk 153 (income statement), the blind-spot FLIPPED FAIL→PASS at rank 1
  - msft `research and development` → chunk 215 ✓ · msft business segments → chunk 18 "Productivity and Business Processes" ✓
  - tsla `Megapack` → chunk 15 ✓ · tsla energy business → "Powerwall" confirmed in chunk 21 via **full-text `in` audit** (printed snippet truncated before it; `"Powerwall" in r["text"]` returned True for chunk 21). NOTE: "Powerwall" is **1-of-1 in the whole TSLA corpus** — fragile if re-chunked (the single occurrence could land in a non-retrieved chunk). Flag.

**Honest findings (real data):**
- `derivative instruments` rank 2 (BM25) → rank 3 (vectors). Vectors win on meaning, lose on exact-lexical. **This is the measured motivation for HYBRID (Module 6).**
- `net sales` (bare lexical) passes rank 1 but rank-1 is chunk 24 (licensing chunk) — loose substring, slightly-lucky pass. Tighten when growing Tier 2.
- chunk 153 (income statement) has dollar figures BLANKED (`Products $ $ $`) — table cells stripped in HTML cleaning. Retrieval fine; WILL hurt answer-generation.

---

## Current state

- **Branch:** `main`. **Latest commit:** `af40542` (company-scoped retrieval + multi-company eval, 8/8). Chain: `0e95dcb` (embed) → `268c60d` (AAPL index) → `10d3009` (AAPL vector search) → `60a7c8d` (multi-company uuid5 index) → `af40542` (company filter + 8/8). All pushed.
- **Working tree:** clean after the commit (only `PROGRESS.md` will be dirty once this handoff is pasted — commit it).
- **Qdrant:** running `:6333`/`:6334`. Collection **`filings` holds 768 points: aapl=199, msft=270, tsla=299** (vectors + payloads, uuid5 ids). Dashboard `http://localhost:6333/dashboard`.
- **FastAPI app:** boots, serves `GET /` + async `GET /health`. Run: `uv run uvicorn secfiler_rag.main:app --reload`.
- **Deps installed:** fastapi, uvicorn[standard], pydantic-settings, qdrant-client, beautifulsoup4, rank-bm25, openai. lxml NOT installed. **Cohere NOT yet (Module 6).**
- **Corpus:** 3 raw 10-Ks in `data/raw/` (gitignored), all FY2025. All three embedded + indexed.
- **Eval harness:** `uv run python -m secfiler_rag.rag.evaluate` (BM25, AAPL-only, 75%) · `uv run python -m secfiler_rag.rag.search` (vectors, 3-company, **100% / 8/8**).
- **Local files NOT in git (intentional):** `.env`, `.venv/`, `qdrant_storage/`, `.vscode/`, `data/raw/*`, `scratch_bm25.py`, `aapl_clean.txt`, **`msft_clean.txt`, `tsla_clean.txt`** (added Chat 7).

---

## What's next (immediate)

**Resume at: Module 6 — Hybrid search (BM25 + vector) + Cohere reranker.**

The motivation is already measured and in hand: `derivative instruments` showed BM25 beats vectors on exact-lexical (rank 2 vs rank 3). Hybrid fuses both; reranker cleans the merged list.

Rough module beat (spec each sub-step, Rohit implements, review after):
1. **Foundation:** why hybrid — vectors win on synonymy/meaning, BM25 wins on exact-phrase/rare-token. Fusion strategies (RRF — Reciprocal Rank Fusion — vs weighted score combination). Why score normalization is needed (BM25 scores ~0–13, cosine ~0–1, not comparable raw).
2. **Implement fusion** — combine the BM25 `search` and `vector_search` result lists. Likely RRF (rank-based, sidesteps the normalization problem elegantly). Raw Python first (contract rule #4).
3. **Add Cohere reranker** — new dep (atomic commit with the code). Rerank the fused candidate list. Cohere `rerank` API, free tier.
4. **Re-run the SAME harness** (retriever-agnostic payoff again — new `search_fn` adapter, `evaluate` untouched). Get hybrid+rerank Recall@3. Audit which chunks pass. Compare vs 100% vector baseline — and specifically check whether `derivative instruments` climbs back to rank 2.

### Carried-forward flags (don't lose these):
- **Async search path** — when `vector_search` enters a FastAPI endpoint, switch to `AsyncQdrantClient` + `async def` + `await client.query_points(...)`. Sync `search.py` is correct for the standalone eval script only.
- **Cross-company "compare" retrieval** (correctly PARKED Chat 7) — "compare Apple vs Tesla R&D" needs chunks from multiple companies. Needs a different filter (`should`/`MatchAny`), a different success metric (one substring can't express "got both"), NOT a `company: list` hack on the current single-substring eval. Great frontend-demo query later. Don't build into the current eval.
- **`net sales` substring is loose** — tighten when growing Tier 2.
- **`Powerwall` is 1-of-1 in TSLA corpus** — re-chunking could move it into a non-retrieved chunk → silent FAIL. Consider a more robust tsla substring when expanding eval.
- **Tables / income statement = mangled text, $ figures blanked** (chunk 153: `Products $ $ $`). Retrieval fine, answer-generation will need real numbers. Flag, don't solve in retrieval phase.
- **Grow Tier 2** toward 25 hand-written pairs (Module 9). 8/8 is a clean sweep = eval is still easy (Tier-1 near-tautological). The 100% proves the pipeline is wired end-to-end multi-company, NOT that retrieval is excellent.
- **Collection name hardcoded `'filings'` in `search.py`** — sync with `settings` like `index.py`. Cosmetic.
- **`get_or_create_collections` non-destructive** — won't re-embed if chunks change. When re-chunking, drop the collection (hit this exact issue Chat 7).
- **Module-level clients** (`OpenAI()`, `QdrantClient()`) fire at import time. Fine now; lazy/injected when imported widely.
- **`verbose` flag on harness** — make printing optional when `evaluate` graduates into `tests/`.

---

## Open questions / known gotchas

- `requires-python = ">=3.13"` — aggressive; soften to `>=3.12` if deploy platform lacks 3.13.
- No `.dockerignore` — needed when FastAPI Dockerfile lands (Module 12).
- No tests yet — `tests/test_ingest.py`, `tests/test_retrieve.py`, `tests/test_evaluate.py` all naturals.
- No formatter run project-wide — a `ruff`/`black` pass cleans nits in one shot.
- `except Exception as e` in `/health` — `e` unused. Cosmetic.

---

## Working rules (the contract — must be respected in every session)

1. **Spec → Rohit implements the entire function/file → Claude reviews like senior code review → reference AFTER the attempt, never before.**
2. **No line-by-line dictation.** Function-level building.
3. **No pasted code before Rohit attempts.** In learning mode, Claude refuses to "just write it."
4. **Raw Python before framework.** Build from scratch ONCE, then show the framework version.
5. **Vectorless before vector.** (Done — BM25 75% before vectors.)
6. **Production-shape from commit #1.**
7. **Docker from the start.**
8. **Eval numbers before bragging.** (M5 honored: 100% / 8/8 measured + audited, not claimed.)
9. **Every module/sub-step ends with a checkpoint** — Rohit answers/implements BEFORE the reference appears.
10. **Rohit never keeps a line he can't explain.**
11. **No interview Q&A in public READMEs.**
12. **Failure-modes framework as recurring lens** — name which mode each feature kills (or flag operational). NOTE: the uuid5 id fix was correctly classified as an OPERATIONAL/data-integrity fix, not a RAG-quality mode (though it has a downstream recall consequence — overwritten chunks can't be retrieved).
13. **Audit Claude.** Trust EDGAR/live source/Rohit's machine over Claude's memory; don't fabricate terminal output, URLs, filenames. **Audit the green check — read which chunk passed, full text if the snippet truncates.** (Caught the `aapl: 398` collision AND verified the Powerwall pass this chat.)
14. **Hold-questions go at the END of a sub-step, in their own clearly-marked block, after the commit step.**
15. **Hold-questions must be VISUALLY DISTINCT** — `### ⛳ HOLD-QUESTIONS`, bold/blockquote. Restate if a reply skips them.

### Handoff protocol (Claude owns this)
1. Update PROGRESS.md (full state, latest commit) — real downloadable file artifact.
2. Fresh NEXT_CHAT_KICKOFF.md reflecting exact resume point — real file artifact.
3. SESSION_BRIEF.md only if rules/decisions fundamentally changed (Chat 7: NOT changed, reuse).
4. Proactively flag "context getting tight" at ~80% (Rohit's budget).
5. Hand off at a clean milestone (after a commit / end of sub-step), not mid-implementation. **Chat 7: handed off AFTER Module 5 fully complete (multi-company) + committed + pushed (`af40542`), 8/8 across three companies. Clean milestone.**

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

- **`pdichone/production-course-main-code`** — technique grab-bag; `rag_pipeline.py`.
- **`pdichone/fcc-production-rag-part-6`** — 2026 advanced; `02_contextual_retrieval.py` (M5.5, now END) + `04_agentic_rag.py` (M8).
- **`pdichone/lang-production-api`** — production-shape template; `app/` layout, `render.yml`, `test_cache_demo.py` caching. NOT copying Streamlit (we use Next.js).

**Flag:** these repos use ChromaDB + Streamlit. We use Qdrant + Next.js. Translate patterns, don't copy API calls.

---

## File map (current)

```
secfiler-rag/
├── .env                       ← gitignored, real OPENAI_API_KEY + QDRANT_URL
├── .env.example               ← committed
├── .gitignore                 ← + scratch_bm25.py + aapl_clean.txt + msft_clean.txt + tsla_clean.txt
├── .python-version            ← "3.13"
├── docker-compose.yml         ← Qdrant v1.18.2 pinned
├── pyproject.toml             ← 7 deps (cohere lands Module 6)
├── uv.lock                    ← committed
├── README.md                  ← one-line placeholder
├── PROGRESS.md                ← THIS FILE
├── evals/
│   └── eval_set.py            ← TIER_1 (5: 3 aapl + 1 msft + 1 tsla) + TIER_2 (3: 1 aapl + 1 msft + 1 tsla). EVAL_SET = 8 items
├── data/
│   ├── .gitkeep               ← tracked
│   └── raw/                   ← gitignored: aapl-2025.htm, msft-2025.htm, tsla-2025.htm
├── qdrant_storage/            ← gitignored (holds 768 points: aapl 199 / msft 270 / tsla 299)
├── src/
│   └── secfiler_rag/
│       ├── __init__.py
│       ├── main.py            ← FastAPI app, GET / + GET /health (async)
│       ├── config.py          ← typed Settings (pydantic-settings)
│       ├── api/__init__.py
│       ├── core/__init__.py
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── ingest.py      ← load_filing_text + chunk_text
│       │   ├── retrieve.py    ← tokenize + build_bm25_index + search (BM25)
│       │   ├── evaluate.py    ← retriever-agnostic evaluate() + BM25 caller (75%, AAPL)
│       │   ├── embed.py       ← embed_texts() + cosine()
│       │   ├── index.py       ← get_or_create_collections() + index_chunks() (uuid5) + multi-company indexer + per-company count verify
│       │   └── search.py      ← vector_search(query, company, top_k) + company-routed eval caller (100% / 8/8)
│       └── models/__init__.py
└── tests/
    └── __init__.py            ← no tests yet
```

---

*Last updated: end of Chat 7 (Module 5 FULLY COMPLETE — multi-company. Switched Qdrant ids to `uuid5` (collision-proof + idempotent); the per-company count check CAUGHT a live `aapl: 398` duplication from the int→uuid5 scheme transition, fixed via clean rebuild → aapl=199, msft=270, tsla=299. Added company payload-filter routing (Option A) to `vector_search` keeping `evaluate` frozen via a `company_by_query` + named `search_fn` adapter. Added 2 msft + 2 tsla eval items (substrings grepped from cleaned text). **Recall@3 = 100% (8/8) across all three companies, every pass audited at chunk level** including a full-text `in` check on the truncated Powerwall match. Commits `60a7c8d` → `af40542`, pushed. **Decision: Module 5.5 Contextual Retrieval moved to the VERY END as extras/polish.** Next: Module 6 Hybrid + Cohere rerank — motivation already measured (derivative instruments: BM25 rank 2 > vectors rank 3). Update at the end of every session.*