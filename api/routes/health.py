import httpx
from fastapi import APIRouter
from pipeline.config import OLLAMA_HOST, CHROMA_HOST

router = APIRouter()


@router.get("/health")
async def health():
    status = {"ollama": "error", "chromadb": "error", "status": "degraded"}

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                status["ollama"] = "ok"
                status["ollama_models"] = models
        except Exception as e:
            status["ollama_error"] = str(e)

        try:
            r = await client.get(f"{CHROMA_HOST}/api/v2/heartbeat")
            if r.status_code == 200:
                status["chromadb"] = "ok"
        except Exception as e:
            status["chromadb_error"] = str(e)

    if status["ollama"] == "ok" and status["chromadb"] == "ok":
        status["status"] = "ok"

    return status
