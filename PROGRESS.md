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
| BM25 library | `rank-bm25` (`BM25Okapi`) — **installed Chat 4** | Pure Python, dependency-free, perfect for our vectorless baseline |
| HTML parsing | BeautifulSoup4 + `html.parser` | Standard, handles malformed markup; `html.parser` = zero extra deps, fine for 1–8MB files. lxml NOT needed |
| Web framework | FastAPI | Async-native, Pydantic-validated, OpenAPI docs built-in |
| Python | 3.13 | Already installed; ecosystem supports it as of mid-2026 |
| Package manager | `uv` (project-local `.venv/`) | Fast, lockfile-based, modern Python standard |
| Eval set | Hand-write 25 Q/A first (Module 9), then FinDER | Writing your own Q/A teaches what good eval looks like |
| Frontend (Module 11) | Next.js 14+ App Router | Differentiator over backend-only portfolios — Rohit's MERN edge |
| Failure-modes framework | Adopted as recurring lens (5 modes: bad chunking / embedding mismatch / retrieval noise / context overflow / hallucination) | Senior interview framing for diagnosing RAG failures |
| Chunk strategy (baseline) | **Fixed-size + overlap (1000 chars / 200 overlap), raw Python** — decided Chat 4 | Honest simple baseline to beat. Structure-aware (Item N) + semantic both flagged as LATER measured experiments |
| Chunk shape | **`dict`: `{"text", "company", "chunk_id"}`** — decided Chat 4 | Metadata-carrying records, not bare strings. company scopes eval; Qdrant filtering uses it in M5 |
| Tokenizer (BM25) | **`lowercase + re.findall(r"[a-z0-9]+")`, raw Python, in `retrieve.py`** — decided Chat 4 | Single shared tokenizer for BOTH index + query (symmetry mandatory). No stemming/stopwords yet — tunable knobs added AFTER baseline number |
| **Eval item shape** | **`{"query", "expected_substring", "company"}`** — decided Chat 5 | Substring-based answer key (Option B). Survives re-chunking (chunk_ids don't). `expected_substring` must be **distinctive + forgiving** — plain word runs, no punctuation-dense/® strings (those break the exact `in` match) |
| **Eval set tiers** | **Tier 1 (lexical sanity) + Tier 2 (natural-language)** — decided Chat 5 | Tier 1 = near-tautological softballs, a regression guard that must always pass + proves the harness runs. Tier 2 = realistic human phrasing, the number that should move when vectors land. Both committed together as one suite |
| **Eval harness shape** | **`evaluate(eval_set, search_fn, top_k)` — retriever-agnostic** — decided Chat 5 | Harness takes the retrieval fn as a parameter, never mentions BM25. Caller builds the index + passes a `search_fn` adapter. Module 5 reuses the SAME harness with a vector `search_fn`. Returns `{recall_at_k, hits, total, results}` (prints AND returns) |
| **Eval code location** | **`src/secfiler_rag/rag/evaluate.py` (harness) + `evals/eval_set.py` (data)** — decided Chat 5 | Eval is measurement INFRASTRUCTURE, not debugging code — version-controlled, not gitignored scratch. Harness/data split: edit data (grow to 25, add tiers) without touching logic; swap retriever without touching data |
| **Company casing convention** | **lowercase everywhere (`"aapl"`, `"msft"`, `"tsla"`)** — DECIDED & ENFORCED Chat 6 | Matches eval items + filenames (`aapl-2025.htm`). Chunker now stamps lowercase. Kills the silent Qdrant filter-mismatch (index `"AAPL"` vs eval `"aapl"` → zero results, no error). **Hold it everywhere.** |
| **Qdrant point id (AAPL-only)** | **`id = i` (enumerate index 0..198), plain int** — decided Chat 6 | Qdrant ids must be int or UUID — a raw string like `"aapl-5"` is REJECTED. `id=i` is the minimal honest choice for single-company. **Multi-company will collide (every company restarts at 0) → switch to `uuid5(NAMESPACE, f"{company}-{chunk_id}")` when MSFT/TSLA land.** |
| **Indexing client = sync, search client = async** | **sync `QdrantClient` for `index.py` (one-shot batch); `AsyncQdrantClient` for the FastAPI search path** — decided Chat 6 | Indexing is a batch script outside any request path → nothing gains from async. The served search path is in the event loop → async mandatory (`/health` already uses AsyncQdrantClient). Two lanes, both honest. NEVER sync-client-with-`await`. |

### Syllabus additions vs original spec
- **Module 5.5 (NEW):** Contextual Retrieval (Anthropic's technique) — between vector RAG and hybrid
- **Module 12 (extended):** Response caching pattern from `lang-production-api/test_cache_demo.py`
- **Module 3 (reordered):** Production-shape repo from commit #1

---

## What's built so far

### ✅ Modules 0–2 (done)
Plan, big picture/market context, foundations (embeddings, vector space, cosine sim, chunking strategies, vectorless vs vector). All checkpoints passed.

### ✅ Module 3 — Stack & Repo Setup (COMPLETE)
- `uv init` scaffold, full `src/secfiler_rag/{api,core,rag,models}` layout, comprehensive `.gitignore`, branch `main`.
- Docker + Qdrant `v1.18.2` via docker-compose, persistent volume, verified.
- Deps: fastapi, uvicorn[standard], pydantic-settings, qdrant-client. `.env`/`.env.example`. Typed `config.py` (pydantic-settings v2). `main.py` with `GET /` + async `GET /health` (real `AsyncQdrantClient` check, 200/503 curl-verified).

### ✅ Module 4 — Vectorless Baseline (BM25) + Eval Harness — COMPLETE (Chat 5)

**Conceptual foundation (Chat 3):** BM25 = TF (k1 saturation) + IDF + length-norm (b), bag-of-words, no meaning. Baseline-first. Can't do synonymy/paraphrase/word-order. Failure-mode mapping. Checkpoint passed.

**Ingestion `load_filing_text()` (Chat 3):** Strips HTML + inline-XBRL (`ix:`) via BeautifulSoup. Clean chars: AAPL 158,914 · MSFT 215,979 · TSLA 238,562.

**Ingestion `chunk_text()` (Chat 4):** `chunk_text(text, company, chunk_size=1000, overlap=200) -> list[dict]`. Fixed-size + overlap, raw Python. `start += chunk_size - overlap`. Returns `{"text","company","chunk_id"}`. AAPL = 199 chunks. **Commit `97c76d6`.** (Chat 6: now called with `company="aapl"` lowercase.)

**BM25 retrieval `retrieve.py` (Chat 4):** `tokenize()` (shared tokenizer), `build_bm25_index() -> BM25Okapi`, `search(query, bm25, chunks, top_k=5) -> list[dict]` with `float` score, sorted desc. **Commit `22a02d9`.** rank-bm25 dep: **`7753441`.**

**🎯 EVAL HARNESS + FIRST BASELINE (Chat 5):**
- **`evals/eval_set.py`** — `TIER_1` (3 lexical-sanity softballs: derivative instruments, global minimum tax standards, net sales) + `TIER_2` (1 natural-language blind-spot: "what was Apple's total revenue this year?" → expects `net sales`). `EVAL_SET = TIER_1 + TIER_2`.
- **`src/secfiler_rag/rag/evaluate.py`** — retriever-agnostic `evaluate(eval_set, search_fn, top_k=3)`. Prints per-item PASS/FAIL+rank AND returns `{recall_at_k, hits, total, results}`. `__main__` = the BM25 caller.
- **BASELINE LOCKED: BM25 Recall@3 = 75% (3/4).** Blind-spot FAILS by design (returned chunks 125/124/4, missed income statement, couldn't bridge "revenue"→"net sales"). Failure modes #2 + #3, measured. **Commit `bdb7885`.**
- **Process lesson:** eval substrings must come from CLEANED text (`load_filing_text` output), never the rendered browser page. First run scored 0/4 from browser-copied substrings.

### ✅ Module 5 — Vector Retrieval — **COMPLETE (Chat 6) — THE PAYOFF**

The whole module's purpose: beat the 75% BM25 baseline with embeddings, and watch the blind-spot flip. **Done, measured, audited.**

**5.1–5.3 Conceptual foundation (Chat 6):** What an embedding is (text → fixed-length vector positioned by meaning, 1536-dim). Why "revenue" and "net sales" land near each other when BM25 can't connect them. Cosine = cosine of the angle between vectors (`dot / (norm·norm)`), ignores magnitude, range −1..1. OpenAI vectors come pre-normalized (norm ≈ 1) → cosine and dot rank identically → Qdrant metric = Cosine. Checkpoint passed.

**`embed.py` — `embed_texts()` + `cosine()` (Chat 6):**
- `embed_texts(texts: list[str]) -> list[list[float]]` — batched OpenAI call, `text-embedding-3-small`, returns ALL vectors **sorted by `.index`** (critical: prevents silent vector↔chunk misalignment if the API returns out of order). Key from typed `settings` (no side-channel config).
- `cosine(a, b)` — raw `math`, full `dot / (norm·norm)` (not the dot-only shortcut, so it survives a non-normalized model swap).
- **Proof measured:** `net sales ↔ total revenue = 0.539` vs `net sales ↔ banana = 0.176`. The synonymy bridge BM25 structurally cannot make, shown in numbers. **Commit `0e95dcb`** (atomic: `openai` dep + `embed.py`).

**`index.py` — Qdrant indexing (Chat 6):**
- `get_or_create_collections()` — non-destructive (`collection_exists` then create-if-missing, NOT `recreate`). Collection `"filings"`, `size=1536`, `distance=Cosine`.
- `index_chunks(client, name, chunks)` — batched `embed_texts` (ONE API call for all 199 — saves per-request round-trips + rate-limit slots), builds one `PointStruct` per chunk (`id=i`, `vector`, `payload={text,company,chunk_id}`), single `upsert`. Accumulate pattern (`points=[]` before loop, append inside).
- `__main__` — loads AAPL → `chunk_text(company="aapl")` → ensure collection → index → **`client.count` VERIFIED = 199** (Rule #13: confirm against live source). Sync `QdrantClient(url=...)`, no api_key locally (silenced insecure-connection warning). **Commit `268c60d`.**

**`search.py` — `vector_search()` + eval re-run (Chat 6) — THE NUMBER:**
- `vector_search(query, top_k=3) -> list[dict]` — embeds query via `embed_texts([query])[0]` (same model both sides — symmetry), `client.query_points(collection, query=vec, limit=top_k)`, reshapes each point to `{**point.payload, "score": point.score}` — the EXACT shape `evaluate` already consumes. Signature `(query, top_k)` matches `search_fn` directly → passed straight into `evaluate`, NO wrapper needed.
- **Re-ran the SAME harness, only `search_fn` swapped:** `evaluate(EVAL_SET, vector_search, top_k=3)`.

  **🎯 RESULT: Vector Recall@3 = 100% (4/4) — BEATS BM25's 75% (3/4).**
  - **Blind-spot FLIPPED FAIL→PASS.** "what was Apple's total revenue this year?" → **rank 1 = chunk 153, the CONSOLIDATED STATEMENTS OF OPERATIONS** (score 0.60), ranks 2–3 = segment-revenue table (chunk 132/131, `Total net sales $416,161`, `iPhone $209,586`). **AUDITED (Rule #13): the RIGHT chunk surfaced, not a lucky "net sales" footnote.** Mode #2 (synonymy) killed, measured, on the exact motivating item.
  - **Commit `10d3009`** (pushed to origin).

**Honest findings from the audit (real data, not flaws):**
- **`derivative instruments`** was rank 2 under BM25, dropped to **rank 3** under vectors. Still passes, but BM25 was *better* at this exact-lexical query. Vectors win on meaning, occasionally lose on exact-phrase match. **This is the measured motivation for HYBRID search (Module 6).**
- **`net sales`** (bare lexical query) passes at rank 1, but rank-1 is chunk 24 (a licensing chunk); the real revenue chunks rank 2–3. Loosest of the four — a Tier-1 softball with a weird bare-phrase input. Legit pass, worth noting.
- **Data-quality gotcha confirmed:** chunk 153 (income statement) has its dollar figures BLANKED (`Products $ $ $`) — table cell values stripped during HTML cleaning; structure survived, numbers didn't. Doesn't hurt retrieval; WILL hurt answer-generation later. (The "tables survive as mangled text" flag.)

---

## Current state

- **Branch:** `main`. **Latest commit:** `10d3009` (vector_search + 100% eval). Chain this chat: `0e95dcb` (embed+cosine) → `268c60d` (Qdrant index) → `10d3009` (vector search). All pushed to origin.
- **Working tree:** only `PROGRESS.md` modified (this handoff update) — commit it after pasting.
- **Qdrant:** running on `:6333`/`:6334`. Collection **`filings` now holds 199 AAPL points** (vectors + payloads). Dashboard `http://localhost:6333/dashboard`. **Qdrant is now LIVE and load-bearing** (no longer just running idle).
- **FastAPI app:** boots, serves `GET /` + async `GET /health`. Run: `uv run uvicorn secfiler_rag.main:app --reload`.
- **Deps installed:** fastapi, uvicorn[standard], pydantic-settings, qdrant-client, beautifulsoup4, rank-bm25, **openai** (Chat 6). lxml NOT installed.
- **Corpus:** 3 raw 10-Ks in `data/raw/` (gitignored), all FY2025, verified-clean. **Only AAPL is embedded/indexed so far.**
- **Eval harness:** `uv run python -m secfiler_rag.rag.evaluate` (BM25, 75%) · `uv run python -m secfiler_rag.rag.search` (vectors, 100%). Both AAPL-only.
- **Local files NOT in git (intentional):** `.env`, `.venv/`, `qdrant_storage/`, `.vscode/`, `data/raw/*`, `scratch_bm25.py`, `aapl_clean.txt`.

---

## What's next (immediate)

**Resume at: Module 5.5 — Contextual Retrieval (Anthropic's technique), OR finish Module 5 multi-company first. Decide at the top of Chat 7.**

Two honest paths — pick with a reason in front of you:

1. **Multi-company finish (close out M5 properly):** index MSFT + TSLA, switch Qdrant `id` to `uuid5(NAMESPACE, f"{company}-{chunk_id}")` (the `id=i` collision fix — every company currently restarts at 0), add MSFT/TSLA eval items, change the caller to route by `item["company"]` (the evaluate signature does NOT change — that's the retriever-agnostic design). Get a 3-company recall number.
2. **Module 5.5 Contextual Retrieval:** prepend LLM-generated context to each chunk before embedding (Anthropic's technique, ref `pdichone/fcc-production-rag-part-6/02_contextual_retrieval.py`). Measure recall lift vs the plain-vector 100%.
3. **Module 6 Hybrid + reranker:** the measured motivation is already in hand (derivative-instruments showed BM25 beats vectors on exact-lexical). Combine BM25 + vectors + Cohere rerank.

**Recommended order:** finish multi-company (path 1) first — it's a small, honest close-out that makes the eval real (4/4 on one company is thin), THEN 5.5, THEN 6. But Rohit's call.

### Carried-forward items (don't lose these):
- **Multi-company index loop + `uuid5` ids** — see path 1 above. The `id=i` → per-company collision is the concrete trigger.
- **Async search path** — when `vector_search` enters FastAPI, switch its client to `AsyncQdrantClient` + `async def` + `await client.query_points(...)`. The sync version in `search.py` is correct for the standalone eval script; the served endpoint must be async.
- **Grow Tier 2** toward 25 hand-written natural-language pairs (Module 9). Currently 1 item — the seed. 4/4 is a thin benchmark; more items = a real number.
- **`net sales` substring is loose** — passes for a slightly-lucky reason. When expanding Tier 2, tighten to point at the income-statement chunk specifically, or document. Flag.
- **Tables (Item 8 / income statement) survive as mangled text with blanked figures** — flag for answer-generation phase. Retrieval fine; generation will need real numbers. (Structure-aware chunking or table extraction is the eventual fix — deferred.)
- **`verbose` flag on harness** — make printing optional when `evaluate` graduates into `tests/`.
- **Collection name hardcoded `'filings'` in `search.py`** — sync with `settings.QDRANT_COLLECTION_NAME or "filings"` like `index.py`. Cosmetic.
- **`get_or_create_collections` is non-destructive** — won't re-embed if chunks change. Fine while data is fixed; when re-chunking, drop the collection or use overwrite-stable ids.
- **Module-level `OpenAI()` / `QdrantClient()` clients** — fire at import time. Fine now; consider lazy/injected when imported widely. Flag, don't solve.

---

## Open questions / known gotchas

- **`requires-python = ">=3.13"`** — aggressive; soften to `>=3.12` if deploy platform lacks 3.13.
- **No `.dockerignore`** — needed when FastAPI Dockerfile lands (Module 12).
- **No tests yet** — `tests/test_ingest.py`, `tests/test_retrieve.py`, `tests/test_evaluate.py` (assert recall on a fixed mini-corpus) all naturals now.
- **No formatter run project-wide** — a `ruff`/`black` pass cleans nits (incl. the `search_fn = lambda` E731) in one shot.
- **Numbers split on commas in BM25 tokenizer** — `"$1,000"` → `["1","000"]`. Accepted for baseline.
- **`except Exception as e` in `/health`** — `e` unused. Cosmetic.

---

## Working rules (the contract — must be respected in every session)

1. **Spec → Rohit implements the entire function/file → Claude reviews like senior code review → reference AFTER the attempt, never before.**
2. **No line-by-line dictation.** Function-level building.
3. **No pasted code before Rohit attempts.** In learning mode, Claude refuses to "just write it."
4. **Raw Python before framework.** Build from scratch ONCE, then show the framework version.
5. **Vectorless before vector.** Honest baseline first. (Done — BM25 75% before any vectors.)
6. **Production-shape from commit #1.** No "refactor later."
7. **Docker from the start.**
8. **Eval numbers before bragging.** Module 9 is the truth gate. (M5 honored this: 100% is measured + audited, not claimed.)
9. **Every module/sub-step ends with a checkpoint** — Rohit answers/implements BEFORE the reference appears.
10. **Rohit never keeps a line he can't explain.** (Enforced this chat: the `.index`-sort line was explained before kept.)
11. **No interview Q&A in public READMEs.**
12. **Failure-modes framework as recurring lens** — name which mode each feature kills (or flag when operational). Eval MEASURES whether a fix worked; it doesn't fix a mode.
13. **Audit Claude.** Trust EDGAR/live source/Rohit's machine over Claude's memory; don't fabricate terminal output, URLs, filenames. **Audit the green check — read which chunk passed, don't trust the substring match.**
14. **Hold-questions go at the END of a sub-step, in their own clearly-marked block, after the commit step.**
15. **Hold-questions must be VISUALLY DISTINCT** — under a marked header (`### ⛳ HOLD-QUESTIONS`), bold/blockquote, never plain trailing prose. Restate if a reply skips them.

### Handoff protocol (Claude owns this)
1. Update PROGRESS.md (full state, latest commit) — real downloadable file artifact.
2. Fresh NEXT_CHAT_KICKOFF.md reflecting exact resume point — real file artifact.
3. SESSION_BRIEF.md only if rules/decisions fundamentally changed.
4. Proactively flag "context getting tight" at ~60–70% (Rohit's budget ~80% — honor it).
5. Hand off at a clean milestone (after a commit / end of sub-step), not mid-implementation. **Chat 6: handed off AFTER Module 5 complete + committed + pushed (`10d3009`), vectors beat baseline 100% vs 75% — clean milestone.**

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

- **`pdichone/production-course-main-code`** — technique grab-bag; key file `rag_pipeline.py`.
- **`pdichone/fcc-production-rag-part-6`** — 2026 advanced; `02_contextual_retrieval.py` (M5.5) + `04_agentic_rag.py` (M8).
- **`pdichone/lang-production-api`** — production-shape template; `app/` layout, `render.yml`, `test_cache_demo.py` caching. NOT copying Streamlit UI (we use Next.js).

**Flag:** these repos use ChromaDB + Streamlit. We use Qdrant + Next.js. Translate patterns, don't copy API calls.

---

## File map (current)

```
secfiler-rag/
├── .env                       ← gitignored, real OPENAI_API_KEY + QDRANT_URL
├── .env.example               ← committed, template
├── .gitignore                 ← + scratch_bm25.py + aapl_clean.txt
├── .python-version            ← "3.13"
├── docker-compose.yml         ← Qdrant v1.18.2 pinned
├── pyproject.toml             ← 7 deps (openai added Chat 6)
├── uv.lock                    ← committed
├── README.md                  ← one-line placeholder
├── PROGRESS.md                ← THIS FILE
├── scratch_bm25.py            ← gitignored throwaway driver
├── aapl_clean.txt             ← gitignored cleaned-text dump
├── evals/
│   └── eval_set.py            ← TIER_1 + TIER_2, EVAL_SET (Chat 5)
├── data/
│   ├── .gitkeep               ← tracked
│   └── raw/                   ← gitignored: aapl-2025.htm, msft-2025.htm, tsla-2025.htm
├── qdrant_storage/            ← gitignored (now holds 199 AAPL points)
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
│       │   ├── evaluate.py    ← retriever-agnostic evaluate() + BM25 caller (75%)
│       │   ├── embed.py       ← NEW Chat 6: embed_texts() + cosine()
│       │   ├── index.py       ← NEW Chat 6: get_or_create_collections() + index_chunks() + AAPL indexer
│       │   └── search.py      ← NEW Chat 6: vector_search() + eval re-run (100%)
│       └── models/__init__.py
└── tests/
    └── __init__.py            ← no tests yet
```

---

*Last updated: end of Chat 6 (Module 5 COMPLETE — vector retrieval built end to end: embed_texts + cosine proof (0.54 vs 0.18), Qdrant index of 199 AAPL points verified, vector_search re-ran the SAME retriever-agnostic harness → **Recall@3 = 100% (4/4), beating BM25's 75%**. Blind-spot revenue→net sales flipped FAIL→PASS at rank 1, audited as the correct income-statement chunk. Honest finding: vectors lose to BM25 on exact-lexical (derivative instruments dropped rank 2→3) — the measured case for hybrid. Commits `0e95dcb` → `268c60d` → `10d3009`, all pushed). Next: finish multi-company (MSFT/TSLA, uuid5 ids) then Module 5.5 Contextual Retrieval, then Module 6 hybrid. Update at the end of every session.*