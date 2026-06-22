# RAG Chatbot Widget

Gotowy do osadzenia widget czatu — vanilla JS, zero zależności.

## Szybkie osadzenie

Dodaj jeden tag `<script>` przed `</body>`:

```html
<script
  src="https://serwer-klienta.pl/widget/widget.js"
  data-api-url="https://serwer-klienta.pl"
  data-api-key="TWÓJ_KLUCZ_API"
  data-title="Asystent firmy XYZ"
  data-primary-color="#185FA5"
></script>
```

## Atrybuty konfiguracyjne

| Atrybut | Wymagany | Domyślnie | Opis |
|---|---|---|---|
| `data-api-url` | ✓ | — | URL serwera API (bez trailing slash) |
| `data-api-key` | ✓ | — | Klucz API (Bearer token) |
| `data-title` | — | `Asystent` | Nagłówek okna czatu |
| `data-primary-color` | — | `#185FA5` | Kolor główny (hex) |

## Pliki

- `widget.js` — logika widgetu (vanilla JS, IIFE)
- `widget.css` — style (ładowane automatycznie przez widget.js)
- `test.html` — strona testowa do uruchomienia lokalnie
