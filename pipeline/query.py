"""
RAG query pipeline: embed question -> retrieve top-K chunks -> build prompt -> LLM.
"""
import httpx
import chromadb
from urllib.parse import urlparse

from config import (
    OLLAMA_HOST, OLLAMA_LLM_MODEL, OLLAMA_EMBED_MODEL,
    CHROMA_HOST, CHROMA_COLLECTION, RAG_TOP_K,
)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context documents.

Rules:
- Answer in the same language the user uses (Polish or English).
- Base your answer exclusively on the context below.
- If the context does not contain enough information to answer the question, say clearly:
  - In Polish: "Nie znalazłem odpowiedzi na to pytanie w dostępnych dokumentach."
  - In English: "I could not find an answer to this question in the available documents."
- Do NOT make up information not present in the context.
- When referencing information, mention the source document name.
- Be concise and factual.
"""


def _get_chroma_collection():
    parsed = urlparse(CHROMA_HOST)
    client = chromadb.HttpClient(host=parsed.hostname, port=parsed.port or 8000)
    return client.get_or_create_collection(CHROMA_COLLECTION)


def _embed_question(question: str) -> list[float]:
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": question},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


def _retrieve(question_embedding: list[float], n_results: int = RAG_TOP_K) -> list[dict]:
    collection = _get_chroma_collection()
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page": meta.get("page", ""),
            "distance": dist,
        })
    return chunks


def _build_prompt(question: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        page_info = f", strona {chunk['page']}" if chunk["page"] else ""
        context_parts.append(
            f"[{i}] Źródło: {chunk['source']}{page_info}\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)
    return f"{SYSTEM_PROMPT}\n\nKONTEKST:\n{context}\n\nPYTANIE: {question}\n\nODPOWIEDŹ:"


def _llm_generate(prompt: str) -> str:
    """Stream the response to avoid read-timeout on long CPU inference."""
    import json as _json
    parts = []
    # read=300: cold model load (~60s) + prefill + first token generation
    with httpx.Client(timeout=httpx.Timeout(connect=10, read=300, write=10, pool=5)) as client:
        with client.stream(
            "POST",
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_LLM_MODEL, "prompt": prompt, "stream": True},
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                data = _json.loads(line)
                parts.append(data.get("response", ""))
                if data.get("done"):
                    break
    return "".join(parts).strip()


def answer(question: str) -> dict:
    """
    Returns {"answer": str, "sources": [{"source": str, "page": str, "excerpt": str}]}
    """
    question_embedding = _embed_question(question)
    chunks = _retrieve(question_embedding)

    if not chunks:
        return {
            "answer": "Brak dokumentów w bazie wiedzy. Najpierw załaduj dokumenty przez endpoint /ingest.",
            "sources": [],
        }

    prompt = _build_prompt(question, chunks)
    response_text = _llm_generate(prompt)

    sources = []
    seen = set()
    for chunk in chunks:
        key = (chunk["source"], chunk["page"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": chunk["source"],
                "page": chunk["page"],
                "excerpt": chunk["text"][:200].replace("\n", " "),
            })

    return {"answer": response_text, "sources": sources}


if __name__ == "__main__":
    import sys
    import json

    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Ile kosztuje diagnostyka?"
    print(f"Pytanie: {q}\n")
    result = answer(q)
    print(f"Odpowiedź:\n{result['answer']}\n")
    print("Źródła:")
    for s in result["sources"]:
        page = f" (s.{s['page']})" if s["page"] else ""
        print(f"  - {s['source']}{page}: {s['excerpt'][:100]}...")
