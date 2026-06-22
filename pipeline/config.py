import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL", "llama3.1:8b")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

CHROMA_HOST = os.environ.get("CHROMA_HOST", "http://localhost:8000")
CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "rag_documents")

RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "64"))

DOCUMENTS_DIR = os.environ.get("DOCUMENTS_DIR", "/app/documents")
