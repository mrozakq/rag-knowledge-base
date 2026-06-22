import os
import sys

# pipeline/ scripts use bare `from config import ...` — expose the directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pipeline"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.health import router as health_router
from routes.query import router as query_router
from routes.ingest import router as ingest_router
from routes.sources import router as sources_router

app = FastAPI(title="RAG Knowledge Base API", version="1.0.0")

_origins_raw = os.environ.get("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in _origins_raw.split(",")] if _origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(query_router)
app.include_router(ingest_router)
app.include_router(sources_router)
