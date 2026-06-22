from fastapi import FastAPI
from secfiler_rag import __version__


app=FastAPI(title="secfiler rag", version=__version__)

@app.get('/')
async def read_root():
    return {"service":"secfiler-rag","status":"ok" }
