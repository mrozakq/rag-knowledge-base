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
