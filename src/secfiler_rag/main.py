from fastapi import FastAPI, HTTPException
from secfiler_rag import __version__
from qdrant_client import AsyncQdrantClient
from secfiler_rag.config import settings


app=FastAPI(title="secfiler rag", version=__version__)
qclient=AsyncQdrantClient(settings.QDRANT_URL)


@app.get('/')
async def read_root():
    return {"service":"secfiler-rag","status":"ok" }

# to check if dependencies are reachable.
@app.get('/health')
async def health():
    try:
        await qclient.get_collections()
        return {"status": "healthy", "qdrant":"connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Qdrant unreachable")
