import re
from rank_bm25 import BM25Okapi


def tokenize(text:str)->list[str]:
    """
    Lowercase + split into word tokens. The SINGLE tokenizer used for
    BOTH chunk indexing and query — symmetry is mandatory.
    """
    text=text.lower()
    tokens=re.findall(r"[a-z0-9]+", text)  
    return tokens

def build_bm25_index(chunks: list[dict])->BM25Okapi:
    """
    Tokenize every chunk's text and build a BM25 index over the corpus.

    Args:
        chunks: output of chunk_text() — list of {"text", "company", "chunk_id"}
    Returns:
        a fitted BM25Okapi index
    """
    # tokenize each chunk["text"] -> list of token-lists -> BM25Okapi(...)
    tokenized_corpus=[]
    for chunk in chunks:
        tokenized_chunk=tokenize(chunk["text"])
        tokenized_corpus.append(tokenized_chunk)

    bm25=BM25Okapi(tokenized_corpus)
    return bm25

def search(
    query: str,
    bm25: BM25Okapi,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Tokenize the query, score all chunks, return the top_k chunks
    (with their metadata) ranked by BM25 score.

    Returns: list of chunks, each with its score attached.
    """
    # tokenize query (SAME tokenizer) -> bm25.get_scores(query_tokens)
    # -> rank chunk indices by score -> return top_k chunks + scores
    tokenized_query=tokenize(query)
    scores=bm25.get_scores(tokenized_query)
    chunk_scores=[]

    for i in range(len(chunks)):
        chunk_scores.append({**chunks[i], "score": float(scores[i])})
    
    chunk_scores.sort(key=lambda x: x["score"], reverse=True)
    return chunk_scores[:top_k]
