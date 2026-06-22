# RAG Knowledge Base

Lokalny system Q&A oparty na dokumentach firmowych. Działa w pełni offline, bez GPU.
Szablon produktowy — podmień dokumenty i masz gotową bazę wiedzy z API dla chatbota WWW.

## Wymagania

| | Minimum | Zalecane |
|---|---|---|
| RAM | 16 GB | 32 GB+ |
| Dysk | 20 GB | 50 GB+ |
| CPU | 4 rdzenie | 8+ rdzeni |
| GPU | nie wymagane | nie wymagane |
| OS | Ubuntu 22.04+ | Ubuntu 24.04 |
| Docker | 24.0+ | najnowszy |

> Środowisko deweloperskie: Dell R810, 2× Xeon E7, 256 GB RAM. Czas odpowiedzi: 20–130 s.

---

## Szybki start

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/mrozakq/rag-knowledge-base.git
cd rag-knowledge-base

# 2. Uruchom setup (instaluje Docker jeśli brak, pobiera modele, startuje stack)
bash scripts/setup.sh

# 3. Wrzuć dokumenty i zaindeksuj
cp /twoje/pliki/*.pdf documents/
bash scripts/reload-documents.sh
```

Po zakończeniu:
- **RAG API:** http://localhost:8080
- **Open WebUI:** http://localhost:3000
- **API docs:** http://localhost:8080/docs

---

## Podmiana dokumentów

```bash
# Usuń stare pliki, wrzuć nowe
rm documents/*.pdf documents/*.docx 2>/dev/null || true
cp /nowe/dokumenty/* documents/

# Przeindeksuj (usuwa starą kolekcję i buduje od nowa)
bash scripts/reload-documents.sh
```

Obsługiwane formaty: **PDF, DOCX, TXT, MD**

---

## Osadzenie chatbota na stronie WWW

Dodaj jeden tag `<script>` przed `</body>`:

```html
<script
  src="https://TWÓJ-SERWER/widget/widget.js"
  data-api-url="https://TWÓJ-SERWER"
  data-api-key="TWÓJ_API_KEY"
  data-title="Asystent firmy XYZ"
  data-primary-color="#185FA5"
></script>
```

Widget renderuje ikonę czatu w prawym dolnym rogu. Po kliknięciu otwiera okno z polem tekstowym, wyświetla odpowiedź i listę dokumentów źródłowych.

Pliki widgetu: `chatbot-widget/widget.js`, `chatbot-widget/widget.css`

---

## Zmienne środowiskowe

Plik `.env` (tworzony z `.env.example` przez `setup.sh`):

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `API_KEY` | *(wymagane)* | Klucz Bearer do autoryzacji API |
| `ALLOWED_ORIGINS` | `*` | Dozwolone originy CORS (przecinek = separator) |
| `OLLAMA_HOST` | `http://ollama:11434` | Adres Ollamy (w Docker: nazwa serwisu) |
| `OLLAMA_LLM_MODEL` | `llama3.1:8b` | Model LLM do generowania odpowiedzi |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model do embeddingów |
| `CHROMA_HOST` | `http://chromadb:8000` | Adres ChromaDB |
| `CHROMA_COLLECTION` | `rag_documents` | Nazwa kolekcji wektorowej |
| `RAG_TOP_K` | `5` | Liczba chunków pobieranych przy retrieval |
| `CHUNK_SIZE` | `512` | Rozmiar chunka (tokeny) |
| `CHUNK_OVERLAP` | `64` | Overlap między chunkami (tokeny) |
| `OPEN_WEBUI_PORT` | `3000` | Port Open WebUI |

---

## Endpointy API

Wszystkie endpointy poza `/health` wymagają nagłówka:
```
Authorization: Bearer <API_KEY>
```

### GET /health
Sprawdza status komponentów. Nie wymaga autoryzacji.

```bash
curl http://localhost:8080/health
```

```json
{
  "status": "ok",
  "ollama": "ok",
  "chromadb": "ok",
  "ollama_models": ["llama3.1:8b", "nomic-embed-text:latest"]
}
```

---

### POST /query
Zadaj pytanie i otrzymaj odpowiedź z listą źródeł.

```bash
curl -X POST http://localhost:8080/query \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Ile kosztuje diagnostyka?", "language": "pl"}'
```

```json
{
  "answer": "Diagnostyka sprzętu kosztuje 50 zł brutto...",
  "sources": [
    {
      "source": "cennik_uslug.pdf",
      "page": "2",
      "excerpt": "Diagnostyka sprzętu: 50 zł brutto..."
    }
  ]
}
```

---

### POST /ingest
Przeindeksuj dokumenty z katalogu `documents/`.

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Authorization: Bearer $API_KEY"
```

```json
{ "status": "ok", "chunks_added": 42 }
```

---

### GET /sources
Lista zaindeksowanych dokumentów.

```bash
curl http://localhost:8080/sources \
  -H "Authorization: Bearer $API_KEY"
```

```json
{
  "sources": [
    { "source": "regulamin.pdf", "chunks": 12, "indexed_at": "2026-06-22T15:35:47" }
  ],
  "total_chunks": 42
}
```

---

## Diagnostyka

```bash
# Status kontenerów
docker compose ps

# Logi konkretnego serwisu
docker compose logs rag-api --tail=50
docker compose logs ollama --tail=20

# Pełny healthcheck
bash scripts/healthcheck.sh

# Restart po problemie
docker compose restart rag-api
```

## Architektura

```
documents/  →  ingest.py  →  ChromaDB
                               ↓
              Ollama (nomic-embed-text + llama3.1:8b)
                               ↓
                         FastAPI /query
                               ↓
                      chatbot-widget (JS)
```
