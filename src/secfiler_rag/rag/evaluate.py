from typing import Callable


def evaluate(
    eval_set: list[dict],
    search_fn: Callable[[str, int], list[dict]],
    top_k: int = 3,
):
    total_queries = len(eval_set)
    hits = 0
    results_summary = []

    for eval_case in eval_set:
        results = search_fn(
            eval_case["query"],
            top_k,
        )

        expected = eval_case["expected_substring"]
        hit_rank = None

        print(f"\n=== Query: {eval_case['query']} ===")

        for rank, r in enumerate(results, start=1):
            print(
                f"  [{r['score']:.2f}] "
                f"rank={rank} "
                f"id={r['chunk_id']} "
                f"{r['text'][:120]!r}"
            )

            if (
                hit_rank is None
                and expected.lower() in r["text"].lower()
            ):
                hit_rank = rank

        if hit_rank is not None:
            hits += 1
            print(f"✅ PASS (found at rank {hit_rank})")
        else:
            print("❌ FAIL (not found in top-k)")

        results_summary.append(
            {
                "query": eval_case["query"],
                "hit": hit_rank is not None,
                "rank": hit_rank,
            }
        )

    recall_at_k = hits / total_queries

    print("\n" + "=" * 50)
    print("Evaluation Summary")
    print("=" * 50)
    print(f"Hits: {hits}/{total_queries}")
    print(f"Recall@{top_k}: {recall_at_k:.2%}")

    return {
        "recall_at_k": recall_at_k,
        "hits": hits,
        "total": total_queries,
        "results": results_summary,
    }

from evals.eval_set import EVAL_SET

from secfiler_rag.rag.ingest import (
    load_filing_text,
    chunk_text,
)

from secfiler_rag.rag.retrieve import (
    build_bm25_index,
    search,
)


if __name__ == "__main__":
    company = EVAL_SET[0]["company"]

    text = load_filing_text(
        f"data/raw/{company}-2025.htm"
    )

    chunks = chunk_text(
        text,
        company=company.upper(),
    )

    bm25 = build_bm25_index(chunks)

    search_fn = lambda query, top_k: search(
        query,
        bm25,
        chunks,
        top_k,
    )

    evaluate(
        EVAL_SET,
        search_fn,
        top_k=3,
    )