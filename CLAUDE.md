# RAG Knowledge Base — instrukcja dla agenta

## Cel projektu

Zbudowanie lokalnego systemu RAG (Retrieval-Augmented Generation) działającego
w pełni offline, bez GPU. Projekt ma być **szablonem produktowym**: po ukończeniu
każdy klient może wdrożyć go na własnej infrastrukturze, podmienić swoje dokumenty
i mieć gotową bazę wiedzy wraz z API dla chatbota na stronie WWW.

Środowisko deweloperskie: Dell R810, 2x Xeon E7, 256 GB RAM, Ubuntu Server 24.04.
Brak GPU: cały inference odbywa się na CPU.

---

## Architektura systemu

```
documents/              <- dane klienta (podmieniane per wdrożenie)
      |
  Ingestion pipeline    <- parser PDF/DOCX/TXT, chunker, embedder
      |
  ChromaDB              <- baza wektorowa (persystowana na dysku)
      |
  Ollama (LLM + embed)  <- lokalny inference, brak zewnętrznych API
      |
  ┌───────────────────────────────┐
  │  RAG API (FastAPI)            │  <- główny punkt integracji
  │  GET  /health                 │
  │  POST /query                  │  <- chatbot WWW odpytuje ten endpoint
  │  POST /ingest                 │  <- trigger przeindeksowania dokumentów
  │  GET  /sources                │  <- lista załadowanych dokumentów
  └───────────────────────────────┘
      |
  Open WebUI             <- interfejs lokalny dla użytkownika wewnętrznego
```

Każdy komponent działa jako kontener Docker. Całość odpala się przez
`docker compose up`.

---

## Struktura repozytorium

```
/
├── CLAUDE.md                        # ten plik
├── README.md                        # dokumentacja dla nowego wdrożenia
├── .env.example                     # szablon zmiennych środowiskowych
├── .env                             # lokalne wartości (NIE idzie do repo)
├── .gitignore
├── docker-compose.yml               # główny plik kompozycji
├── docker-compose.override.yml.example  # przykład dla środowisk produkcyjnych
│
├── documents/                       # dane klienta (NIE idą do repo)
│   └── .gitkeep
│
├── chroma_db/                       # persystowana baza wektorowa (NIE idzie do repo)
│   └── .gitkeep
│
├── logs/                            # logi agenta i systemu (NIE idą do repo)
│   └── .gitkeep
│
├── memory/                          # pamięć operacyjna agenta (idzie do repo)
│   ├── progress.md
│   ├── decisions.md
│   ├── issues.md
│   └── model_perf.md
│
├── pipeline/                        # kod RAG (idzie do repo)
│   ├── ingest.py                    # parsowanie + chunking + embeddingi
│   ├── query.py                     # retrieval + prompt + inference
│   ├── config.py                    # konfiguracja z .env
│   └── requirements.txt
│
├── api/                             # FastAPI (idzie do repo)
│   ├── main.py
│   ├── routes/
│   │   ├── query.py
│   │   ├── ingest.py
│   │   └── sources.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── chatbot-widget/                  # gotowy embed dla stron WWW (idzie do repo)
│   ├── widget.js                    # vanilla JS, zero zależności
│   ├── widget.css
│   └── README.md                    # instrukcja osadzenia na stronie
│
└── scripts/
    ├── setup.sh                     # pierwsze uruchomienie na nowym serwerze
    ├── reload-documents.sh          # podmiana dokumentów bez restartu systemu
    └── healthcheck.sh               # weryfikacja czy wszystkie komponenty działają
```

---

## Zasady działania agenta

### Testuj każdy krok przed przejściem dalej

Po każdej zmianie uruchom test weryfikujący działanie komponentu.
Nie przechodź do następnego etapu jeśli poprzedni nie przeszedł testu.
Zapisz wynik testu do logs/ i zaktualizuj memory/progress.md.

### Cofaj się o krok jeśli coś nie gra

Jeśli test nie przechodzi: sprawdź logi, cofnij ostatnią zmianę,
spróbuj alternatywnego podejścia. Nie dodawaj kolejnych warstw
na zepsutym fundamencie. Zapisz problem i rozwiązanie do memory/issues.md.

### Loguj każdą decyzję techniczną

Jeśli wybierasz jedno rozwiązanie spośród kilku możliwych, zapisz to
w memory/decisions.md wraz z uzasadnieniem. Następna sesja powinna wiedzieć
dlaczego coś działa tak a nie inaczej.

---

## Etapy budowy (kolejność jest obowiązkowa)

### Etap 1: Infrastruktura Docker

Utwórz `docker-compose.yml` z serwisami: ollama, chromadb, rag-api, open-webui.
Upewnij się że wolumeny dla chroma_db/ i modeli Ollamy są persystowane na dysku.

Test: `docker compose ps` pokazuje wszystkie serwisy jako "running".
Test: `curl http://localhost:11434/api/tags` zwraca JSON.
Test: `curl http://localhost:8000/api/v1/heartbeat` zwraca odpowiedź ChromaDB.

### Etap 2: Pobranie modeli

Pobierz przez Ollama API: `llama3.1:8b` i `nomic-embed-text`.
Jeśli llama3.1:8b inference przekroczy 120 sekund dla krótkiego zapytania,
przełącz na `mistral:7b` i zapisz decyzję w memory/model_perf.md.

Test: `curl -X POST http://localhost:11434/api/generate` z krótkim promptem,
oczekiwany czas odpowiedzi poniżej 120 sekund.

### Etap 3: Pipeline ingestion

Napisz `pipeline/ingest.py` obsługujący pliki: PDF, DOCX, TXT, MD.
Chunking: 512 tokenów, overlap 64. Każdy chunk zachowuje metadane:
nazwa pliku źródłowego, numer strony jeśli dostępny, timestamp indeksowania.
Embeddingi przez Ollama (nomic-embed-text), zapis do ChromaDB.

Test: załaduj jeden dokument testowy, sprawdź liczbę chunków w kolekcji ChromaDB.
Test: sprawdź czy metadane (nazwa pliku) są zapisane przy każdym chunku.

### Etap 4: RAG query

Napisz `pipeline/query.py`: przyjmuje pytanie, pobiera top-5 chunków
z ChromaDB, buduje prompt z kontekstem i wysyła do Ollamy.
Odpowiedź zawiera: tekst odpowiedzi + lista źródeł (nazwa pliku, fragment).

Prompt systemowy ma działać po polsku i po angielsku.
Jeśli kontekst nie zawiera odpowiedzi, model ma to powiedzieć wprost,
a nie hallucynować.

Test: zadaj pytanie dotyczące treści załadowanego dokumentu.
Sprawdź czy odpowiedź zawiera informacje z dokumentu i podaje źródło.
Zadaj pytanie o temat którego nie ma w dokumentach. Sprawdź czy model
odpowiada "nie wiem" zamiast wymyślać.

### Etap 5: FastAPI

Napisz `api/main.py` z endpointami:

```
GET  /health          -> status wszystkich komponentów (Ollama, ChromaDB)
POST /query           -> { "question": "...", "language": "pl" }
                      <- { "answer": "...", "sources": [...] }
POST /ingest          -> trigger przeindeksowania katalogu documents/
                      <- { "status": "ok", "chunks_added": N }
GET  /sources         -> lista unikalnych dokumentów w kolekcji
```

API ma mieć autentykację przez API key (zmienna środowiskowa API_KEY w .env).
Nagłówek: `Authorization: Bearer <API_KEY>`.
Bez klucza: 401. Zły klucz: 403.

CORS: konfigurowalny przez zmienną ALLOWED_ORIGINS w .env,
domyślnie "*" dla środowiska deweloperskiego.

Test: odpytaj każdy endpoint przez curl z poprawnym i błędnym kluczem.

### Etap 6: Chatbot widget

Napisz `chatbot-widget/widget.js`: vanilla JavaScript, zero zależności,
możliwy do osadzenia na dowolnej stronie przez jeden tag `<script>`.
Widget konfigurowany przez atrybuty data- na tagu:

```html
<script
  src="widget.js"
  data-api-url="https://serwer-klienta.pl"
  data-api-key="klucz"
  data-title="Asystent firmy XYZ"
  data-primary-color="#185FA5"
></script>
```

Widget renderuje ikonę czatu w prawym dolnym rogu, po kliknięciu otwiera
okno z polem tekstowym. Wysyła zapytanie do `/query`, wyświetla odpowiedź
i listę źródeł. Obsługuje stan ładowania i błędy sieciowe.

Test: otwórz prostą stronę HTML z osadzonym widgetem, zadaj pytanie,
sprawdź czy odpowiedź się wyświetla poprawnie.

### Etap 7: Skrypty operacyjne

Napisz `scripts/reload-documents.sh`: usuwa istniejącą kolekcję ChromaDB,
uruchamia ingest.py na nowym katalogu documents/, raportuje liczbę
zaindeksowanych chunków. Klient podmienia pliki i odpala jeden skrypt.

Napisz `scripts/healthcheck.sh`: sprawdza czy Ollama, ChromaDB i API
odpowiadają na health check. Zwraca 0 jeśli wszystko działa, 1 jeśli coś nie.

Napisz `scripts/setup.sh`: instaluje Docker jeśli brak, klonuje repo,
kopiuje .env.example do .env, odpala docker compose, pobiera modele,
uruchamia pierwszy ingest z katalogu documents/. Nowe wdrożenie = jeden skrypt.

Test: uruchom healthcheck.sh, sprawdź exit code.

### Etap 8: Dokumentacja

Napisz `README.md` z sekcjami:
- Wymagania (RAM min. 16 GB, bez GPU, Docker)
- Szybki start (3 kroki: clone, .env, ./scripts/setup.sh)
- Podmiana dokumentów (opis reload-documents.sh)
- Osadzenie chatbota na stronie WWW (przykład HTML z widgetem)
- Zmienne środowiskowe (tabela: nazwa, domyślna wartość, opis)
- Endpointy API (tabela z przykładami curl)

### Etap 9: Test end-to-end

Uruchom pełny scenariusz: świeży katalog documents/ z 3 różnymi plikami,
przeindeksowanie przez reload-documents.sh, 5 pytań przez widget JS,
sprawdzenie czy każda odpowiedź cytuje właściwy dokument.
Zapisz wyniki do memory/model_perf.md.

---

## Bezpieczeństwo i GitHub

### Co idzie do repozytorium

Kod, konfiguracje Docker, skrypty, widget, dokumentacja, memory/.

### Co nigdy nie idzie do repozytorium

Sprawdź listę przed każdym commitem. Jeśli któryś z tych plików lub katalogów
jest w staging, usuń go i przerwij commit.

```
.env
documents/
chroma_db/
logs/
*.pdf
*.docx
*.xlsx
*.csv
__pycache__/
*.pyc
.venv/
```

### Zmienne środowiskowe

Wszystkie sekrety i konfiguracja środowiskowa idą przez .env.
Kod czyta wyłącznie z os.environ lub python-dotenv.
Żadnych hardkodowanych wartości w kodzie źródłowym.

Szablon `.env.example` zawiera wszystkie zmienne z pustymi wartościami
i komentarzem opisującym każdą z nich.

---

## Ograniczenia sprzętowe

Brak GPU: inference na CPU, spodziewany czas 20-90 sekund per zapytanie.
Jeśli inference przekracza 120 sekund, przełącz na mniejszy model.
Nie używaj modeli powyżej 13B bez testu prędkości.
Zapisuj wyniki benchmarku do memory/model_perf.md.

---

## Pamięć operacyjna agenta

Przed rozpoczęciem każdej sesji przeczytaj wszystkie pliki z katalogu memory/.
Po każdej zakończonej akcji zaktualizuj odpowiedni plik.

### memory/progress.md

Format każdego etapu:
```
- [ ] Etap N: nazwa
- [~] Etap N: nazwa (w toku)
- [x] Etap N: nazwa (ukończono YYYY-MM-DD)
```

### memory/decisions.md

Format każdego wpisu:
```
[YYYY-MM-DD] [ETAP N] Tytuł decyzji
Kontekst: co było do wyboru
Decyzja: co wybrano
Powód: dlaczego
```

### memory/issues.md

Format każdego wpisu:
```
[YYYY-MM-DD] [ETAP N] Opis problemu
Błąd: treść komunikatu błędu
Próba 1: co zrobiono -> wynik
Próba 2: co zrobiono -> wynik
Rozwiązanie: co finalnie zadziałało
Status: resolved / workaround / open
```

### memory/model_perf.md

Format każdego wpisu:
```
| Model | Typ zapytania | Czas (s) | Jakość RAG (1-5) | Data |
```

Agent aktualizuje memory/ przed zakończeniem każdej sesji.
Jeśli sesja kończy się błędem, zapisz aktualny stan w issues.md.

---

## Definicja sukcesu projektu

Użytkownik otwiera stronę WWW z osadzonym widgetem, wpisuje pytanie
po polsku lub angielsku dotyczące dokumentów firmy i otrzymuje odpowiedź
opartą na treści tych dokumentów, z podaniem nazwy pliku źródłowego.

Na nowej infrastrukturze wdrożenie zajmuje: clone repo, edycja .env,
uruchomienie setup.sh, wrzucenie dokumentów do documents/,
uruchomienie reload-documents.sh. Czas: poniżej 30 minut.
