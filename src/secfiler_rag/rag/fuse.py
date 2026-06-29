from collections import defaultdict

def reciprocal_rank_fusion(result_lists, k=60, top_k=3):
    totals = defaultdict(float)
    docs = {}
    for results in result_lists:
        for rank, doc in enumerate(results, start=1):
            score_contribution = 1 / (k + rank)
            key = (doc["company"], doc["chunk_id"])
            totals[key] += score_contribution
            docs[key] = doc
    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return [docs[key] for key, _ in ranked[:top_k]]