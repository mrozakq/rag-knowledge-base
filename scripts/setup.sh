#!/usr/bin/env bash
# Pierwsze uruchomienie na nowym serwerze.
# Instaluje Docker (jeśli brak), uruchamia stack, pobiera modele, indeksuje dokumenty.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC}  $*"; }
die()  { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }

log "=== RAG Knowledge Base — setup $(date '+%Y-%m-%d %H:%M:%S') ==="

# ── 1. Docker ──────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  log "Instalacja Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  warn "Dodano użytkownika do grupy docker. Wyloguj się i zaloguj ponownie, potem uruchom setup.sh jeszcze raz."
  exit 0
fi

if ! docker compose version &>/dev/null; then
  die "docker compose nie jest dostępny. Zainstaluj Docker >= 24."
fi
log "Docker OK: $(docker --version)"

# ── 2. .env ────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  log "Tworzenie .env z .env.example..."
  cp .env.example .env
  # Generuj losowy klucz API
  API_KEY=$(openssl rand -hex 24 2>/dev/null || tr -dc 'a-f0-9' </dev/urandom | head -c 48)
  if grep -q '^API_KEY=$' .env; then
    sed -i "s|^API_KEY=$|API_KEY=$API_KEY|" .env
    log "Wygenerowano API_KEY: $API_KEY"
    log "Zachowaj ten klucz — będzie potrzebny do konfiguracji widgetu."
  fi
else
  warn ".env już istnieje — pomijam."
fi

# ── 3. Docker Compose up ───────────────────────────────────────────────────
log "Uruchamianie kontenerów..."
docker compose up -d

log "Czekam na Ollama (może potrwać do 60s)..."
until curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; do sleep 3; done
log "Ollama gotowa."

log "Czekam na ChromaDB..."
until curl -sf http://localhost:8000/api/v2/heartbeat >/dev/null 2>&1; do sleep 3; done
log "ChromaDB gotowa."

log "Czekam na RAG API..."
until curl -sf http://localhost:8080/health >/dev/null 2>&1; do sleep 3; done
log "RAG API gotowe."

# ── 4. Pobierz modele ──────────────────────────────────────────────────────
log "Pobieranie modelu nomic-embed-text..."
curl -s -X POST http://localhost:11434/api/pull \
  -d '{"name":"nomic-embed-text"}' | tail -1

log "Pobieranie modelu llama3.1:8b (4.7 GB, może potrwać kilka minut)..."
curl -s -X POST http://localhost:11434/api/pull \
  -d '{"name":"llama3.1:8b"}' | tail -1

# ── 5. Ingest dokumentów ───────────────────────────────────────────────────
DOC_COUNT=$(find documents/ -maxdepth 1 -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.txt" -o -name "*.md" \) 2>/dev/null | wc -l)

if [ "$DOC_COUNT" -gt 0 ]; then
  log "Indeksuję $DOC_COUNT dokumentów z katalogu documents/..."
  bash "$SCRIPT_DIR/reload-documents.sh"
else
  warn "Brak dokumentów w documents/. Wrzuć pliki i uruchom: ./scripts/reload-documents.sh"
fi

# ── Podsumowanie ───────────────────────────────────────────────────────────
log ""
log "=== Setup zakończony! ==="
log "  RAG API:    http://localhost:8080"
log "  Open WebUI: http://localhost:3000"
log "  API Key:    $(grep '^API_KEY=' .env | cut -d= -f2-)"
log ""
log "Embed widget na stronie:"
log '  <script src="http://TWÓJ_SERWER/widget/widget.js"'
log '    data-api-url="http://TWÓJ_SERWER"'
log '    data-api-key="TWÓJ_API_KEY"></script>'
