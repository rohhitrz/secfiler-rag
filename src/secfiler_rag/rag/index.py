from secfiler_rag.config import settings
from qdrant_client.models import VectorParams, Distance,PointStruct,Filter,FieldCondition,MatchValue
from qdrant_client import QdrantClient
from secfiler_rag.rag.embed import embed_texts
from secfiler_rag.rag.ingest import load_filing_text,chunk_text
from uuid import uuid5, NAMESPACE_DNS

client = QdrantClient(url=settings.QDRANT_URL)

def get_or_create_collections():
    collection_name = "filings"
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE,
            ),
        )

    return collection_name

def index_chunks(client,collection_name, chunks):
    # the structure of each chunk is {"text","company","chunk_id"}
    texts=[c['text'] for c in chunks]
    vectors=embed_texts(texts)

    points=[]
    for chunk, vector in zip(chunks,vectors):
        point_id=str(
            uuid5(
                NAMESPACE_DNS,
                f"{chunk['company']}-{chunk['chunk_id']}"
            )
        )
        points.append(PointStruct(
            id=point_id,
            vector=vector,
            payload=chunk

        ))
    
    client.upsert(
        collection_name=collection_name,
        points=points,
    )

if __name__=="__main__":
    companies=['aapl','msft','tsla']
    name=get_or_create_collections()

    for c in companies:
        text=load_filing_text(f"data/raw/{c}-2025.htm")
        chunks = chunk_text(text, company=c)
        index_chunks(client,name,chunks)
        result=client.count(
        collection_name=name,
        count_filter=Filter(
        must=[FieldCondition(key="company", match=MatchValue(value=c))]
    ),
)       
        print(f"{c}: {result.count} points")

