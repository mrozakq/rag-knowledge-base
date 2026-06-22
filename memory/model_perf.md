# Model Performance

| Model | Typ zapytania | Czas (s) | Jakość RAG (1-5) | Data |
|-------|--------------|---------|-----------------|------|
| llama3.1:8b | krótki prompt (1 słowo) | 17.72 | - | 2026-06-22 |
| llama3.1:8b | pełny RAG (2753 tok. input, ~100 tok. output) | 72 | 4 | 2026-06-22 |
| llama3.1:8b | cold start (model evicted) first token | 60.5 | - | 2026-06-22 |
| nomic-embed-text | embedding 3 słów | <1 | - | 2026-06-22 |
