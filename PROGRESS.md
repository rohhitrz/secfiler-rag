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

### ✅ Module 3 — Stack & Repo Setup (Phases 1-3 done, Phase 4 in progress)
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
  - `docker compose up -d` ran successfully; Qdrant verified three ways:
    - `docker ps` shows container Up, ports mapped
    - `curl http://localhost:6333/` returns version JSON
    - `http://localhost:6333/dashboard` loads in browser
  - **Commit `626b14e`** — Qdrant via docker-compose
- **Phase 4 sub-step 4.1:** Dependencies installed via `uv add fastapi 'uvicorn[standard]' pydantic-settings qdrant-client`
  - `.venv/` created, `uv.lock` written (110KB), all four imports verified working
  - **Commit `41f5cd8`** — FastAPI, uvicorn, pydantic-settings, qdrant-client
- **Phase 4 sub-step 4.2:** Environment config files created
  - `.env` with real `OPENAI_API_KEY`, local `QDRANT_URL`, blank `QDRANT_API_KEY` (gitignored, never committed)
  - `.env.example` with comments above each variable, sensible default for `QDRANT_URL`, blank keys
  - Verified: `.env` invisible to git, `.env.example` tracked
  - **Commit `c9e5c0a`** — .env.example template

---

## Current state

- **Branch:** `main`
- **Latest commit:** `c9e5c0a Add .env.example template with OpenAI and Qdrant config`
- **Total commits:** 4 (all on `main`, all clean atomic changes)
- **Working tree:** clean (`git status` shows no changes pending)
- **Qdrant:** running locally on `:6333` / `:6334`, dashboard at `http://localhost:6333/dashboard`
- **Python venv:** created, 4 deps installed and importing cleanly
- **Local files NOT in git (intentional):** `.env`, `.venv/`, `qdrant_storage/`, `.vscode/`
- **Files staged but not committed:** none

---

## What's next (immediate)

**Resume at:** Phase 4 sub-step 4.3 — write `app/config.py`

### Sub-steps remaining in Phase 4:
- **4.3 — `src/secfiler_rag/config.py`:** Pydantic Settings class that loads `.env` into a typed `Settings` object. Variables: `OPENAI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`. Uses `pydantic-settings` (already installed).
- **4.4 — `src/secfiler_rag/main.py`:** FastAPI app with a hello-world `GET /` endpoint. Must boot with `uv run uvicorn secfiler_rag.main:app --reload`.
- **4.5 — `/health` endpoint:** returns app status + verifies Qdrant connectivity by hitting the Qdrant client. Real connectivity check, not a fake "ok".

### After Phase 4:
- Commit Phase 4 as a coherent set of commits
- Push to GitHub (`gh repo create rohhitrz/secfiler-rag --public --source=. --remote=origin --push`) — this is the FIRST push, so the repo becomes visible from this point.
- Begin **Module 4 — Vectorless Baseline (BM25)**

---

## Open questions / known gotchas

- **`qdrant/qdrant:v1.18.2` is pinned.** When deploying in Module 12, evaluate whether to switch to `-unprivileged` variant for production. For local dev, plain `v1.18.2` is fine.
- **`.python-version` says `3.13`, `pyproject.toml` says `requires-python = ">=3.13"`** — both aggressive. Soften to `>=3.12` if deployment platform doesn't support 3.13.
- **No tests written yet.** First test arrives with sub-step 4.5 (hitting `/health` from a `tests/test_health.py`).
- **No `.dockerignore` yet** — needed when we add a `Dockerfile` for the FastAPI app (Module 12).

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
9. **Every module ends with a checkpoint** — Rohit answers/implements BEFORE the reference appears.
10. **Rohit never keeps a line he can't explain.**
11. **No interview Q&A in public READMEs.** (Anti-pattern flagged by Rohit himself.)
12. **Failure-modes framework as recurring lens** — name which failure mode each feature kills.
13. **Audit Claude.** Rohit catches imprecision and pushes back; Claude tightens immediately.

### Handoff protocol (Claude owns this)

At the end of every chat, BEFORE context runs out, Claude must:
1. Update this PROGRESS.md with the current state (what's built, what's next, latest commit hash) — create as a real file artifact for Rohit to download and commit.
2. Generate a fresh NEXT_CHAT_KICKOFF.md reflecting the exact resume point — also as a real file artifact.
3. Only update SESSION_BRIEF.md if rules or fundamental decisions have changed; otherwise it's reused.
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
├── qdrant_storage/            ← gitignored, Qdrant's data
├── src/
│   └── secfiler_rag/
│       ├── __init__.py        ← just __version__
│       ├── main.py            ← EMPTY (next: sub-step 4.4)
│       ├── config.py          ← EMPTY (next: sub-step 4.3)
│       ├── api/__init__.py
│       ├── core/__init__.py
│       ├── rag/__init__.py
│       └── models/__init__.py
└── tests/
    └── __init__.py
```

---

*Last updated: end of Chat 1 (Phase 4 sub-step 4.2 complete). Update at the end of every session.*
