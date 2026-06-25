from openai import OpenAI
from secfiler_rag.config import settings
import math

client=OpenAI(api_key=settings.OPENAI_API_KEY)
# texts=["what", "is", "2*2", " ?"]

def embed_texts(texts:list[str])->list[list[float]]:
    response=client.embeddings.create(
        model='text-embedding-3-small',
        input=texts
    )
    return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]

def cosine(a: list[float], b:list[float])->float:
    dot=sum(x*y for x,y in zip(a,b))
    norm_a=math.sqrt(sum(x * x for x in a))
    norm_b=math.sqrt(sum(y * y for y in b))
    return dot/(norm_a * norm_b)

if __name__=="__main__":
    texts = [
        "net sales",
        "total revenue",
        "banana",
    ]

    vectors = embed_texts(texts)
    print(len(vectors))
    print(len(vectors[0]))

    print("sales vs revenue:", cosine(vectors[0], vectors[1]))
    print("sales vs banana:", cosine(vectors[0], vectors[2]))




    

    

