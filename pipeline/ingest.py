"""
Ingestion pipeline: parse PDF/DOCX/TXT/MD -> chunk -> embed -> store in ChromaDB.
"""
import os
import sys
import hashlib
import datetime
from pathlib import Path

import httpx
import tiktoken
import chromadb
from pypdf import PdfReader
from docx import Document as DocxDocument

from config import (
    OLLAMA_HOST, OLLAMA_EMBED_MODEL,
    CHROMA_HOST, CHROMA_COLLECTION,
    CHUNK_SIZE, CHUNK_OVERLAP, DOCUMENTS_DIR,
)

_enc = tiktoken.get_encoding("cl100k_base")


def _token_len(text: str) -> int:
    return len(_enc.encode(text))


def _chunk_text(text: str, source: str, page: int | None = None) -> list[dict]:
    tokens = _enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _enc.decode(chunk_tokens)
        chunks.append({
            "text": chunk_text,
            "source": source,
            "page": page,
        })
        if end == len(tokens):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def _parse_pdf(path: Path) -> list[dict]:
    reader = PdfReader(str(path))
    chunks = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            chunks.extend(_chunk_text(text, path.name, page=i))
    return chunks


def _parse_docx(path: Path) -> list[dict]:
    doc = DocxDocument(str(path))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return _chunk_text(text, path.name)


def _parse_text(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return _chunk_text(text, path.name)


PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".txt": _parse_text,
    ".md": _parse_text,
}


def _embed(texts: list[str]) -> list[list[float]]:
    embeddings = []
    with httpx.Client(timeout=60) as client:
        for text in texts:
            resp = client.post(
                f"{OLLAMA_HOST}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
    return embeddings


def _chunk_id(source: str, index: int, text: str) -> str:
    h = hashlib.md5(f"{source}:{index}:{text[:64]}".encode()).hexdigest()[:8]
    return f"{source}:{index}:{h}"


def ingest_directory(documents_dir: str = DOCUMENTS_DIR, clear: bool = True) -> int:
    docs_path = Path(documents_dir)
    if not docs_path.exists():
        print(f"Documents directory not found: {docs_path}", file=sys.stderr)
        return 0

    from urllib.parse import urlparse
    parsed = urlparse(CHROMA_HOST)
    chroma = chromadb.HttpClient(host=parsed.hostname, port=parsed.port or 8000)

    if clear:
        try:
            chroma.delete_collection(CHROMA_COLLECTION)
            print(f"Cleared existing collection: {CHROMA_COLLECTION}")
        except Exception:
            pass

    collection = chroma.get_or_create_collection(CHROMA_COLLECTION)

    timestamp = datetime.datetime.utcnow().isoformat()
    total_added = 0

    for file_path in sorted(docs_path.iterdir()):
        ext = file_path.suffix.lower()
        if ext not in PARSERS or not file_path.is_file():
            continue

        print(f"Parsing: {file_path.name}")
        try:
            chunks = PARSERS[ext](file_path)
        except Exception as e:
            print(f"  ERROR parsing {file_path.name}: {e}", file=sys.stderr)
            continue

        if not chunks:
            print(f"  No text extracted from {file_path.name}")
            continue

        print(f"  {len(chunks)} chunks, embedding...")
        texts = [c["text"] for c in chunks]
        try:
            embeddings = _embed(texts)
        except Exception as e:
            print(f"  ERROR embedding {file_path.name}: {e}", file=sys.stderr)
            continue

        ids = [_chunk_id(c["source"], i, c["text"]) for i, c in enumerate(chunks)]
        metadatas = [
            {
                "source": c["source"],
                "page": str(c["page"]) if c["page"] is not None else "",
                "indexed_at": timestamp,
            }
            for c in chunks
        ]

        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        total_added += len(chunks)
        print(f"  Added {len(chunks)} chunks from {file_path.name}")

    print(f"\nTotal chunks added: {total_added}")
    return total_added


if __name__ == "__main__":
    count = ingest_directory()
    sys.exit(0 if count >= 0 else 1)
