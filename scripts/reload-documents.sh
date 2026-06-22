#!/usr/bin/env bash
# Przeindeksowuje katalog documents/ od zera.
# Użycie: ./scripts/reload-documents.sh [ścieżka_do_dokumentów]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DOCS_DIR="${1:-$PROJECT_ROOT/documents}"
API_URL="${RAG_API_URL:-http://localhost:8080}"
API_KEY="${API_KEY:-}"

echo "=== Przeindeksowanie dokumentów $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "Katalog: $DOCS_DIR"
echo ""

if [ ! -d "$DOCS_DIR" ]; then
  echo "BŁĄD: katalog $DOCS_DIR nie istnieje."
  exit 1
fi

FILE_COUNT=$(find "$DOCS_DIR" -maxdepth 1 -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.txt" -o -name "*.md" \) | wc -l)
echo "Znaleziono $FILE_COUNT plików do zaindeksowania."

if [ "$FILE_COUNT" -eq 0 ]; then
  echo "Brak plików do zaindeksowania. Wrzuć dokumenty do $DOCS_DIR i spróbuj ponownie."
  exit 0
fi

echo "Wysyłanie żądania /ingest do API..."

if [ -z "$API_KEY" ]; then
  # Spróbuj załadować z .env
  ENV_FILE="$PROJECT_ROOT/.env"
  if [ -f "$ENV_FILE" ]; then
    API_KEY=$(grep -E '^API_KEY=' "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
  fi
fi

if [ -z "$API_KEY" ]; then
  echo "BŁĄD: Zmienna API_KEY nie jest ustawiona. Ustaw ją w .env lub jako zmienną środowiskową."
  exit 1
fi

RESPONSE=$(curl -sf --max-time 600 \
  -X POST "$API_URL/ingest" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" 2>&1) || {
  echo "BŁĄD: Nie można połączyć się z API ($API_URL)."
  echo "Czy serwis działa? Uruchom: docker compose ps"
  exit 1
}

CHUNKS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('chunks_added', 0))" 2>/dev/null || echo "?")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")

echo ""
echo "Status: $STATUS"
echo "Zaindeksowanych chunków: $CHUNKS"
echo ""
echo "Gotowe! Dokumenty są teraz dostępne w bazie wiedzy."
