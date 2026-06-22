import asyncio
from fastapi import APIRouter, Depends
from pipeline.ingest import ingest_directory
from .auth import require_api_key

router = APIRouter()


@router.post("/ingest")
async def ingest(_=Depends(require_api_key)):
    loop = asyncio.get_event_loop()
    chunks_added = await loop.run_in_executor(None, ingest_directory)
    return {"status": "ok", "chunks_added": chunks_added}
