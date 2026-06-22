# Issues

[2026-06-22] [ETAP 1] Health-check failował — curl niedostępny w kontenerach
Błąd: "curl: executable file not found in $PATH" w rag-ollama i rag-chromadb
Próba 1: CMD curl -f http://localhost:11434/api/tags -> curl not found
Próba 2: CMD-SHELL bash -c 'echo > /dev/tcp/localhost/8000' dla chromadb -> działa
Rozwiązanie: ollama list dla ollama; bash /dev/tcp dla chromadb
Status: resolved

[2026-06-22] [ETAP 3] chromadb client v0.5.3 nie działa z serwerem v1.0.0
Błąd: ValueError: Could not connect to tenant default_tenant (HTTP 410 Gone na /api/v1/tenants)
Próba 1: chromadb==0.5.3 HttpClient -> 410 Gone
Próba 2: pip install chromadb>=1.0.0 (zainstalowano 1.5.9) -> połączenie OK
Rozwiązanie: Zaktualizowano requirements.txt do chromadb>=1.0.0
Status: resolved

[2026-06-22] [ETAP 1] ChromaDB API v1 deprecated
Błąd: {"error":"Unimplemented","message":"The v1 API is deprecated. Please use /v2 apis"}
Próba 1: curl /api/v1/heartbeat -> error
Próba 2: curl /api/v2/heartbeat -> {"nanosecond heartbeat": ...}
Rozwiązanie: Zmieniono health-check URL na /api/v2/heartbeat, ostatecznie użyto TCP check
Status: resolved
