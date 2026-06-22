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
