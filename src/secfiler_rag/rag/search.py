from secfiler_rag.rag.embed import embed_texts
from secfiler_rag.config import settings
from qdrant_client import QdrantClient
from evals.eval_set import EVAL_SET
from secfiler_rag.rag.evaluate import evaluate

client=QdrantClient(url=settings.QDRANT_URL)
def vector_search(query:str, top_k=3):
    embedded_query=embed_texts([query])
    query_vector=embedded_query[0]

    # search quadrant
    response=client.query_points(
        collection_name='filings',
        limit=top_k,
        query=query_vector
    )
    results=[]
    for point in response.points:
        results.append({
            **point.payload,
            "score":point.score,
        })
    return results

if __name__ == "__main__":
    # results = vector_search(
    #     "What was Apple's total revenue this year?",
    #     top_k=3,
    # )

    # for result in results:
    #     print(result)
    evaluate(EVAL_SET, vector_search, top_k=3)


