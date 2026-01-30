# Szenario Wizard - Testergebnisse

**Stand:** 16. Januar 2026
**Status:** Alle Tests bestanden

---

## Übersicht

Dieses Dokument dokumentiert die Testergebnisse der AI-gestützten Datenanalyse im Szenario Wizard. Die Tests wurden mit populären öffentlichen Datensätzen durchgeführt.

### Testergebnisse

| Kategorie | Tests | Bestanden | Genauigkeit |
|-----------|-------|-----------|-------------|
| Haupttests | 8 | 8 | 100% |
| Edge Cases | 8 | 8 | 100% |
| **Gesamt** | **16** | **16** | **100%** |

---

## Getestete Datensätze

### Rating (Bewertung auf Skala)

| Datensatz | Quelle | Beschreibung | Ergebnis |
|-----------|--------|--------------|----------|
| IMDb Movie Reviews | HuggingFace | 50k Filmrezensionen | `rating` / `likert-5` |
| Amazon Product Reviews | HuggingFace | 142M Produktbewertungen | `rating` / `stars-5` |
| Yelp Reviews | HuggingFace | 500k+ Restaurantbewertungen | `rating` / `stars-5` |
| Stanford Sentiment | HuggingFace | 215k Sentiment-Phrasen | `rating` / `likert-5` |

### Labeling (Kategorisierung)

| Datensatz | Quelle | Beschreibung | Ergebnis |
|-----------|--------|--------------|----------|
| AG News | HuggingFace | 120k Nachrichtenartikel in 4 Kategorien | `labeling` / `multi-class` |
| TruthfulQA | HuggingFace | 800 Fragen zur Wahrheitsprüfung | `labeling` / `binary-authentic` |
| Multi-Label Topics | Custom | Dokumente mit mehreren Themen | `labeling` / `multi-label` |

### Comparison (Paarweiser Vergleich)

| Datensatz | Quelle | Beschreibung | Ergebnis |
|-----------|--------|--------------|----------|
| Anthropic HH-RLHF | HuggingFace | 170k Präferenz-Vergleiche | `comparison` / `pairwise` |

### Ranking (Sortierung)

| Datensatz | Quelle | Beschreibung | Ergebnis |
|-----------|--------|--------------|----------|
| Quality Ranking | Custom | Antwortqualität in Kategorien | `ranking` / `buckets-3` |

---

## Edge Case Tests

| Testfall | Beschreibung | Erwartung | Ergebnis |
|----------|--------------|-----------|----------|
| Ambiguous Sentiment | Labels ohne Skala | labeling | labeling |
| Binary Spam Detection | Boolean is_spam | labeling | labeling |
| Unlabeled Text | Rohe Texte | labeling | labeling |
| Numeric Scores | Numerische Werte | rating | rating |
| Multi-Criteria Compare | Mehrere Kriterien | comparison | comparison |
| German Reviews | Deutsche Sprache | rating | rating |
| Minimal Data | Nur 1 Datenpunkt | comparison | comparison |
| Medical Diagnosis | Wissenschaftliche Daten | labeling | labeling |

---

## Erkennungslogik

Das LLM erkennt Evaluationstypen anhand folgender Merkmale:

| Datenmerkmal | Erkannter Typ |
|--------------|---------------|
| Numerische Scores (1-5, 1-10) | rating |
| Felder: `stars`, `rating`, `score` | rating |
| Kategorien: `category`, `label`, `class` | labeling |
| Boolean: `is_spam`, `is_truthful` | labeling |
| Paare: `response_a`/`response_b` + `preferred` | comparison |
| Qualitäts-Buckets: `Good`/`Poor`/`Excellent` | ranking |

---

## Konfiguration

- **Modell:** `mistralai/Mistral-Small-3.2-24B-Instruct-2506`
- **Prompt-Template:** `scenario.analysis` (in Admin konfigurierbar)
- **Konfidenz:** Durchschnittlich 0.9 bei allen Tests

---

## Testskripte

Die Testskripte befinden sich in:

```
scripts/
├── test_scenario_wizard.py       # Externer HTTP-Test
└── test_wizard_internal.py       # Interner Flask-Test
```

### Ausführung

```bash
# Im Flask-Container
docker exec llars_flask_service python -c "
from main import app
with app.app_context():
    exec(open('/app/scripts/test_wizard_internal.py').read())
    main()
"
```

---

## Fazit

Der Szenario Wizard erkennt alle 4 Evaluationstypen zuverlässig:

- **rating**: Bewertungen auf Skalen (Likert, Sterne, Prozent)
- **labeling**: Kategorisierung (binär, multi-class, multi-label)
- **comparison**: Paarweiser Vergleich (A vs B)
- **ranking**: Sortierung und Bucket-Kategorisierung

Die AI-Analyse ist produktionsbereit und generalisiert gut über verschiedene Domänen und Sprachen.

---

## Referenzen

- [IMDb Dataset](https://huggingface.co/datasets/imdb)
- [AG News](https://huggingface.co/datasets/fancyzhx/ag_news)
- [Anthropic HH-RLHF](https://huggingface.co/datasets/Anthropic/hh-rlhf)
- [TruthfulQA](https://huggingface.co/datasets/truthfulqa/truthful_qa)
- [Awesome LLM Human Preference Datasets](https://github.com/glgh/awesome-llm-human-preference-datasets)
