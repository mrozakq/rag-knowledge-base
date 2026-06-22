import chromadb
from urllib.parse import urlparse
from fastapi import APIRouter, Depends
from pipeline.config import CHROMA_HOST, CHROMA_COLLECTION
from .auth import require_api_key

router = APIRouter()


@router.get("/sources")
async def sources(_=Depends(require_api_key)):
    parsed = urlparse(CHROMA_HOST)
    client = chromadb.HttpClient(host=parsed.hostname, port=parsed.port or 8000)
    try:
        collection = client.get_collection(CHROMA_COLLECTION)
    except Exception:
        return {"sources": [], "total_chunks": 0}

    result = collection.get(include=["metadatas"])
    seen = {}
    for meta in result["metadatas"]:
        src = meta.get("source", "unknown")
        if src not in seen:
            seen[src] = {"source": src, "indexed_at": meta.get("indexed_at", ""), "chunks": 0}
        seen[src]["chunks"] += 1

    return {
        "sources": sorted(seen.values(), key=lambda x: x["source"]),
        "total_chunks": collection.count(),
    }
