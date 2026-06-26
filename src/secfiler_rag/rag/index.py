from secfiler_rag.config import settings
from qdrant_client.models import VectorParams, Distance,PointStruct
from qdrant_client import QdrantClient
from secfiler_rag.rag.embed import embed_texts
from secfiler_rag.rag.ingest import load_filing_text,chunk_text

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
    for i,(chunk, vector) in enumerate(zip(chunks,vectors)):
        points.append(PointStruct(
            id=i,
            vector=vector,
            payload=chunk

        ))
    
    client.upsert(
        collection_name=collection_name,
        points=points,
    )

if __name__=="__main__":
    text=load_filing_text("data/raw/aapl-2025.htm")
    chunks = chunk_text(text, company="aapl")

    name=get_or_create_collections()
    index_chunks(client,name,chunks)
    result=client.count(collection_name=name)
    print(result.count)