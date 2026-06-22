# PROGRESS.md — secfiler-rag

> **This document is the source of truth for project state across chat sessions with Claude.**
> Update at the end of every meaningful work session. Commit it.

---

## Project at a glance

- **Goal:** Production-grade, full-stack RAG system over SEC 10-K filings (Apple, Microsoft, Tesla). Deployable, with eval numbers, citation-backed answers, and a Next.js frontend.
- **Owner:** Rohit (`rohhitrz` on GitHub) — MERN dev (~6 months backend), learning AI engineering. North star: hireable as a remote AI engineer.
- **Mentor:** Claude, operating under the S2 RAG session contract (see "Working Rules" below).
- **Repo (local):** `/Users/rohit/Desktop/secfiler-rag`
- **Repo (remote):** Not pushed yet. Planned push after Module 4 (vectorless baseline).

---

## Locked decisions (don't relitigate)

| Decision | Choice | Rationale |
|---|---|---|
| Corpus | Apple + Microsoft + Tesla 10-Ks (latest FY) | Real, messy, sellable use case |
| Vector DB | Qdrant in Docker (`qdrant/qdrant:v1.18.2`) | Production-grade, native hybrid, first-class metadata filtering |
| Embedding model (baseline) | OpenAI `text-embedding-3-small` | Cheap, fast, strong baseline. Voyage `voyage-finance-2` is the measured-upgrade candidate |
| Reranker (Module 6) | Cohere Rerank | Free tier covers learning. `bge-reranker-large` is the self-hosted alternative |
| BM25 library | `rank-bm25` (Module 4) | Pure Python, dependency-free, perfect for our vectorless baseline |
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

### ✅ Module 0 — Plan & opening checkpoint (done)
- Roadmap reviewed, four sanity-check picks confirmed, opening checkpoint passed.

### ✅ Module 1 — Big Picture & Market Context (done)
- RAG architecture diagram (indexing + query phases) — Rohit can redraw from memory.
- Three problems RAG solves vs. fine-tuning vs. long-context vs. bigger LLM — internalized.
- Job market context (titles, bands, what interviewers test) — covered.
- Checkpoint: legal-assistant fine-tuning critique + architecture redraw — passed.

### ✅ Module 2 — Foundations & Mental Models (done)
- Embeddings (distributional ≠ referential meaning — Rohit caught an imprecision)
- Vector space, cosine similarity (with the "describes vs contains" distinction)
- Chunking strategies (fixed / recursive / semantic / structure-aware)
- Vectorless vs vector framing — covered properly
- Checkpoint (5 questions): verdicts all correct, depth thin in places — passed.

### ✅ Module 3 — Stack & Repo Setup (COMPLETE — all 4 phases done)
- **Phase 1 (Tool decisions):** Qdrant vs alternatives, embedding model choice, reranker, BM25, FastAPI, Python 3.13, `uv`, Next.js — opinions defended.
- **Phase 2 (Repo scaffold):**
  - `uv init --package --python 3.13` ran cleanly
  - `pyproject.toml` shaped (real description, no dead `[project.scripts]`)
  - `__init__.py` minimal (just `__version__`)
  - Full structure: `src/secfiler_rag/{api,core,rag,models}/__init__.py`, `tests/__init__.py`, `main.py`, `config.py`
  - Comprehensive `.gitignore` with sections for secrets, macOS, IDE, testing, type-checker, project data, logs
  - Renamed branch `master → main`
  - **Commit `1eb15fe`** — initial scaffold
- **Phase 3 (Docker & Qdrant):**
  - Docker Desktop installed, verified with `hello-world`
  - `docker-compose.yml` written with pinned `qdrant/qdrant:v1.18.2`, ports 6333+6334, persistent volume `./qdrant_storage/`
  - `qdrant_storage/` added to gitignore
  - `docker compose up -d` ran successfully; Qdrant verified three ways (docker ps, curl version JSON, dashboard loads)
  - **Commit `626b14e`** — Qdrant via docker-compose
- **Phase 4 (Env config + FastAPI service skeleton) — COMPLETE:**
  - **4.1 — Dependencies:** `uv add fastapi 'uvicorn[standard]' pydantic-settings qdrant-client`; `.venv/` + `uv.lock` (110KB); imports verified.
    - **Commit `41f5cd8`**
  - **4.2 — Env files:** `.env` (real `OPENAI_API_KEY`, local `QDRANT_URL`, blank `QDRANT_API_KEY`, gitignored); `.env.example` (commented template, tracked). Verified `.env` invisible to git.
    - **Commit `c9e5c0a`**
  - **4.3 — `config.py`:** Typed `Settings(BaseSettings)` via `pydantic-settings`. `model_config = SettingsConfigDict(env_file=".env")` (native v2 loading, NOT `load_dotenv`, NOT `class Config:`). Fields: `OPENAI_API_KEY: str` (required), `QDRANT_URL: str = "http://localhost:6333"` (defaulted — boots with zero config), `QDRANT_API_KEY: str | None = None` (genuinely optional — local Qdrant has no auth). Module-level `settings = Settings()` export. Verified loading via `uv run python -c`.
    - **Commit `[5th commit]`** — Add typed Settings via pydantic-settings
  - **4.4 — `main.py` root endpoint:** `app = FastAPI(title=..., version=__version__)`; `async def read_root()` on `GET /` returns truthful dict `{"service": "secfiler-rag", "status": "ok"}`. Boots under `uv run uvicorn secfiler_rag.main:app --reload`. `/docs` Swagger UI renders.
    - **Commit `[6th commit]`** — Add FastAPI app with root endpoint
  - **4.5 — `/health` endpoint (async-correct):** `async def health()` on `GET /health`. Uses **`AsyncQdrantClient`** (module-level, single instance) and `await qclient.get_collections()` to prove connectivity — honest non-blocking I/O (deliberately switched from sync client to make the `async def` truthful). Success → `{"status": "healthy", "qdrant": "connected"}` (200). Failure → `raise HTTPException(status_code=503, detail="Qdrant unreachable")`. **Both paths verified with `curl -i`:** 200 with Qdrant up, 503 after `docker compose stop`.
    - **Commit `f419ea4`** — Add /health endpoint with async Qdrant connectivity check

---

## Current state

- **Branch:** `main`
- **Latest commit:** `f419ea4 Add /health endpoint with async Qdrant connectivity check`
- **Total commits:** 7 (all on `main`, all clean atomic changes)
- **Working tree:** clean (`git status` shows no changes pending)
- **Qdrant:** running locally on `:6333` / `:6334`, dashboard at `http://localhost:6333/dashboard` (was stopped/started during 4.5 health-check testing — confirm it's UP with `docker compose start` before resuming)
- **FastAPI app:** boots, serves `GET /` and `GET /health`, `/docs` renders. Run: `uv run uvicorn secfiler_rag.main:app --reload`
- **Python venv:** created, 4 deps installed and importing cleanly
- **Local files NOT in git (intentional):** `.env`, `.venv/`, `qdrant_storage/`, `.vscode/`
- **Files staged but not committed:** none

---

## What's next (immediate)

**Resume at:** Phase 4 is DONE. Next is the GitHub push, then Module 4 (BM25 baseline).

### Immediate sequence:
1. **Commit this updated PROGRESS.md** — `git add PROGRESS.md && git commit -m "Update progress: Phase 4 complete"`.
2. **First push to GitHub** (repo becomes visible from this point):
   `gh repo create rohhitrz/secfiler-rag --public --source=. --remote=origin --push`
3. **Begin Module 4 — Vectorless Baseline (BM25).** Honest keyword-search baseline BEFORE any vectors (working rule #5). Library: `rank-bm25` (locked decision). This is where real RAG work starts — we need the 10-K corpus ingested and chunked first, so Module 4 likely opens with: source the filings (SEC EDGAR, Kaggle fallback), then chunk, then BM25 index, then a baseline retrieval query.

### Known prerequisite for Module 4:
- **Corpus acquisition not done yet.** No 10-K files downloaded. Module 4 starts with getting Apple/Microsoft/Tesla 10-Ks from SEC EDGAR (or Kaggle fallback) into the repo's (gitignored) data directory.

---

## Open questions / known gotchas

- **`/health` async client is now honest** — switched to `AsyncQdrantClient` in 4.5, no longer blocks the event loop. Resolved.
- **`except Exception as e` in `/health`** — `e` is currently unused (cosmetic; can drop `as e`). Non-blocking.
- **`qdrant/qdrant:v1.18.2` is pinned.** When deploying in Module 12, evaluate whether to switch to `-unprivileged` variant for production. For local dev, plain `v1.18.2` is fine.
- **`.python-version` says `3.13`, `pyproject.toml` says `requires-python = ">=3.13"`** — both aggressive. Soften to `>=3.12` if deployment platform doesn't support 3.13.
- **No tests written yet.** A `tests/test_health.py` hitting `/health` is a natural early test — was deferred during Phase 4, worth picking up.
- **No `.dockerignore` yet** — needed when we add a `Dockerfile` for the FastAPI app (Module 12).
- **No code formatter run yet** — several files have PEP 8 spacing nits (`app=FastAPI`, `{"key":val}`). A `ruff`/`black` pass would clean them in one shot; deferred as low-priority.

---

## Working rules (the contract — must be respected in every session)

These are non-negotiable. New chats must reload and respect them.

1. **Spec → Rohit implements the entire function/file → Claude reviews like senior code review → Claude shows reference version AFTER the attempt, never before.**
2. **No line-by-line dictation.** Function-level building.
3. **No pasted code before Rohit attempts.** In learning mode, Claude refuses to "just write it."
4. **Raw Python before framework.** Build chunking, embedding calls, similarity, prompt assembly from scratch ONCE — then show the LangChain version.
5. **Vectorless before vector.** Honest baseline first.
6. **Production-shape from commit #1.** No "I'll refactor later."
7. **Docker from the start.** Real containers, real networks, real volumes.
8. **Eval numbers before bragging.** Module 9 is the truth gate.
9. **Every module/sub-step ends with a checkpoint** — Rohit answers/implements BEFORE the reference appears.
10. **Rohit never keeps a line he can't explain.**
11. **No interview Q&A in public READMEs.** (Anti-pattern flagged by Rohit himself.)
12. **Failure-modes framework as recurring lens** — name which failure mode each feature kills. (NOTE: some features — typed config, `/health` — kill *operational* failures, NOT one of the five RAG-quality modes. Recognizing the layer is part of the lesson.)
13. **Audit Claude.** Rohit catches imprecision and pushes back; Claude tightens immediately.
14. **(NEW this chat) Hold-questions go at the END of a sub-step, in their own clearly-marked block, after the commit step — never scattered mid-review.** Rohit answers them as the closing beat before moving on. This was added because mid-cycle questions got buried during the code-build loop.

### Handoff protocol (Claude owns this)

At the end of every chat, BEFORE context runs out, Claude must:
1. Update this PROGRESS.md with the current state (what's built, what's next, latest commit hash) — create as a real file artifact for Rohit to download and commit.
2. Generate a fresh NEXT_CHAT_KICKOFF.md reflecting the exact resume point — also as a real file artifact.
3. Only update SESSION_BRIEF.md if rules or fundamental decisions have changed; otherwise it's reused. (NOTE: rule #14 was added this chat — SESSION_BRIEF should get the hold-question rule folded in next time it's regenerated, but it's captured here in the meantime.)
4. Proactively flag "context getting tight" at ~60-70% — don't wait until degradation starts.
5. Hand off at a clean milestone (after a commit, end of a sub-step), not mid-implementation.

### Steering commands Rohit may use
`next` · `deeper` · `expand this point` · `skip` · `code` (= switch to build mode, NOT learning mode) · `quiz me` · `real-world` · `hireable?` · `product` · `reset rules`

### Anti-patterns Claude must avoid
- Dumping multiple modules at once
- Jumping to mechanics before establishing conceptual "what is this" foundation
- Bloated examples that overwhelm (flagged during the LangGraph module in S0)
- Over-correcting after feedback (Rohit's 1-2 word → 80-word description swing is the canonical example)
- Vibes-words in technical explanations without backing them up ("sane," "clean," "magic")
- Re-litigating settled decisions
- Pushing a chat past safe context limits — proactively hand off

---

## Reference repos (use as guides, REBUILD never clone)

- **`pdichone/production-course-main-code`** — technique grab-bag. Most important file: `rag_pipeline.py` (the one Rohit must be able to rebuild from blank).
- **`pdichone/fcc-production-rag-part-6`** — 2026 advanced techniques. Building from: `02_contextual_retrieval.py` (Module 5.5) and `04_agentic_rag.py` (Module 8). Reading only: `01_long_context_vs_rag.py`, `03_late_chunking.py`, `05_graphrag_intro.py`, `06_multimodal_rag.py`.
- **`pdichone/lang-production-api`** — production shape template. Stealing: `app/` layout, `render.yml`, `test_cache_demo.py` caching pattern. NOT copying: the Streamlit UI (we use Next.js).

**Flag:** these repos use ChromaDB and Streamlit. We use Qdrant and Next.js. Translate patterns, don't copy API calls.

---

## File map (current)

```
secfiler-rag/
├── .env                       ← gitignored, has real OPENAI_API_KEY
├── .env.example               ← committed, template
├── .gitignore                 ← comprehensive
├── .python-version            ← "3.13"
├── .venv/                     ← gitignored, 4 deps installed
├── .vscode/                   ← gitignored
├── docker-compose.yml         ← Qdrant v1.18.2 pinned
├── pyproject.toml             ← 4 deps in [project]
├── uv.lock                    ← committed, ~110KB
├── README.md                  ← empty placeholder
├── PROGRESS.md                ← THIS FILE (commit the updated version)
├── qdrant_storage/            ← gitignored, Qdrant's data
├── src/
│   └── secfiler_rag/
│       ├── __init__.py        ← just __version__
│       ├── main.py            ← DONE: FastAPI app, GET / + GET /health (async)
│       ├── config.py          ← DONE: typed Settings via pydantic-settings
│       ├── api/__init__.py
│       ├── core/__init__.py
│       ├── rag/__init__.py
│       └── models/__init__.py
└── tests/
    └── __init__.py            ← no tests yet (test_health.py is a natural first)
```

---

*Last updated: end of Chat 2 (Phase 4 COMPLETE — sub-steps 4.3/4.4/4.5, commits 5/6/7, latest `f419ea4`). Next: commit this file, push to GitHub, begin Module 4 (BM25 baseline). Update at the end of every session.*
