#!/usr/bin/env bash
# Sprawdza czy Ollama, ChromaDB i RAG API odpowiadają.
# Exit 0 = wszystko OK, exit 1 = coś nie działa.
set -euo pipefail

OLLAMA_URL="${OLLAMA_HOST:-http://localhost:11434}"
CHROMA_URL="${CHROMA_HOST:-http://localhost:8000}"
API_URL="${RAG_API_URL:-http://localhost:8080}"

FAILED=0

check() {
  local name="$1" url="$2"
  if curl -sf --max-time 5 "$url" >/dev/null 2>&1; then
    echo "[OK]  $name — $url"
  else
    echo "[ERR] $name — $url"
    FAILED=1
  fi
}

echo "=== RAG healthcheck $(date '+%Y-%m-%d %H:%M:%S') ==="
check "Ollama"   "$OLLAMA_URL/api/tags"
check "ChromaDB" "$CHROMA_URL/api/v2/heartbeat"
check "RAG API"  "$API_URL/health"
echo ""

if [ "$FAILED" -eq 0 ]; then
  echo "Status: OK — wszystkie serwisy odpowiadają"
  exit 0
else
  echo "Status: BŁĄD — sprawdź logi: docker compose logs"
  exit 1
fi
