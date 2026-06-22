# Decisions

[2026-06-22] [ETAP 1] Inicjalizacja repozytorium
Kontekst: Repo na GitHub już istniało (mrozakq/rag-knowledge-base), katalog /opt/rag-kb był bez git
Decyzja: git init + git remote add origin, branch main
Powód: Dopasowanie do istniejącego repo bez nadpisywania historii

[2026-06-22] [ETAP 1] Health-check ChromaDB v2 API
Kontekst: ChromaDB zaktualizowało API - endpoint /api/v1/heartbeat zwraca błąd deprecacji
Decyzja: Zmieniono health-check na bash /dev/tcp/localhost/8000 (TCP check)
Powód: Kontener nie ma curl; /api/v2/heartbeat działa, ale sprawdzenie TCP jest prostsze i niezależne od wersji API

[2026-06-22] [ETAP 1] Health-check Ollama — ollama list
Kontekst: Kontener ollama/ollama nie ma curl ani wget
Decyzja: Użyto `ollama list` jako health-check (natywne polecenie dostępne w kontenerze)
Powód: Sprawdza czy daemon Ollamy jest gotowy do obsługi zapytań

[2026-06-22] [ETAP 1] Build context rag-api — root projektu
Kontekst: Dockerfile w ./api/ chciał skopiować ../pipeline/ - poza kontekstem
Decyzja: build context ustawiony na root projektu (.), Dockerfile w api/Dockerfile
Powód: Pozwala COPY pipeline/ wewnątrz kontenera razem z api/

[2026-06-22] [ETAP 2] llama3.1:8b — model pozostaje bez zmiany
Kontekst: Limit to 120s; mierzony czas dla krótkiego prompta to 17.72s
Decyzja: Zostaje llama3.1:8b (nie przełączamy na mistral:7b)
Powód: 17.72s << 120s; jest tu duży zapas nawet dla dłuższych promptów RAG

[2026-06-22] [ETAP 3] chromadb client >= 1.0.0 zamiast ==0.5.3
Kontekst: Serwer chromadb:latest to wersja 1.0.0 używająca API v2; klient 0.5.3 używał API v1 (410 Gone)
Decyzja: chromadb>=1.0.0 w requirements.txt (zainstalowano 1.5.9)
Powód: Klient musi pasować do API serwera; wersja latest serwera zawsze będzie >= 1.0.0

[2026-06-22] [ETAP 4] Streaming zamiast stream=False + read timeout 300s
Kontekst: Ollama przy cold start (model evicted po 5 min TTL) potrzebuje ~60s na załadowanie
          Pełny prompt RAG (2753 tokenów) + eval ~100 tokenów = 60+1.4+69.5 ≈ 131s total
Decyzja: stream=True z httpx.stream(), read timeout 300s (na każdy indywidualny chunk)
Powód: Z stream=False trzeba czekać na cały response w jednym bloku; z stream=True
       timeout dotyczy czasu między kolejnymi tokenami (nie całości) więc 300s starcza

[2026-06-22] [ETAP 4] llama3.1:8b context_length 4096 - wystarczy dla RAG
Kontekst: Model załadowany z context_length=4096; prompt RAG to ~2753 tokenów
Decyzja: Brak zmiany - 4096 wystarczy (2753 input + ~100 output = 2853 < 4096)
Powód: Prefill dla 2753 tok tylko 1.4s; zmiana na większy context niepotrzebna

[2026-06-22] [ETAP 5] run_in_executor dla blocking pipeline functions
Kontekst: answer() i ingest_directory() to synchroniczne funkcje blokujące event loop FastAPI
Decyzja: asyncio.get_event_loop().run_in_executor(None, fn) w endpointach /query i /ingest
Powód: FastAPI jest async; blokujące operacje w async endpoint blokują cały serwer

[2026-06-22] [ETAP 5] sys.path.insert dla pipeline imports w main.py
Kontekst: pipeline/query.py robi "from config import" (nie "from pipeline.config import")
Decyzja: sys.path.insert(0, "/app/pipeline") na początku main.py
Powód: Skrypty pipeline działają standalone z CWD=/app/pipeline; w kontenerze CWD=/app
