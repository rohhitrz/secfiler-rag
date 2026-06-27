from secfiler_rag.rag.embed import embed_texts
from secfiler_rag.config import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from evals.eval_set import EVAL_SET
from secfiler_rag.rag.evaluate import evaluate

client=QdrantClient(url=settings.QDRANT_URL)
def vector_search(query:str,company:str, top_k=3):
    embedded_query=embed_texts([query])
    query_vector=embedded_query[0]

    query_filter=Filter(
        must=[
            FieldCondition(
                key="company",
                match=MatchValue(value=company)
            )
        ]
    )

    # search quadrant
    response=client.query_points(
        collection_name='filings',
        limit=top_k,
        query=query_vector,
        query_filter=query_filter,
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

    company_by_query={
        item['query']: item['company']
        for item in EVAL_SET
    }

    def search_fn(query, top_k):
        company=company_by_query[query]
        return vector_search(
            query,
            company,
            top_k
        )
    
    evaluate(
    EVAL_SET,
    search_fn,
    top_k=3,
)


