# Konzept: News Summarization Ranking Pipeline

**Ziel:** News-Artikel mit zwei LLMs (Mistral & Magistral) zusammenfassen lassen und die Qualität in einem Ranking-Szenario bewerten (Gut / Moderat / Schlecht).

---

## 1. Datensatz: Deutsche Nachrichtenartikel

### Empfohlene Datensätze

| Datensatz | Sprache | Beschreibung | Download |
|-----------|---------|--------------|----------|
| **MLSUM** (German) | DE | 220k deutsche News-Artikel mit Zusammenfassungen | HuggingFace `mlsum` |
| **SwissText** | DE | Schweizer News mit Referenz-Summaries | swisstext.org |
| **10kGNAD** | DE | 10k österreichische News-Artikel | GitHub |
| **XSum** | EN | BBC News mit extreme Summaries | HuggingFace |
| **CNN/DailyMail** | EN | 300k News mit Highlights | HuggingFace |

### Empfehlung: MLSUM German (Subset)

```python
# Download via HuggingFace
from datasets import load_dataset

dataset = load_dataset("mlsum", "de", split="test[:50]")  # 50 Artikel für Test

# Format für LLARS Import:
items = [
    {
        "id": f"news_{i}",
        "subject": article["title"],
        "content": article["text"],
        "reference_summary": article["summary"]  # Ground Truth
    }
    for i, article in enumerate(dataset)
]

# Als JSON exportieren
import json
with open("news_articles.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
```

### Dateiformat für LLARS Upload

```json
[
  {
    "id": "news_001",
    "subject": "Klimagipfel: Neue Ziele für CO2-Reduktion",
    "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele zur Reduktion von Treibhausgasen geeinigt. Die Industrieländer verpflichten sich zu einer Senkung der Emissionen um 55% bis 2030...",
    "reference_summary": "Beim Klimagipfel wurden neue CO2-Reduktionsziele von 55% bis 2030 beschlossen."
  },
  {
    "id": "news_002",
    "subject": "Tech-Konzern kündigt KI-Durchbruch an",
    "content": "Ein führendes Technologieunternehmen hat heute einen bedeutenden Fortschritt im Bereich der künstlichen Intelligenz vorgestellt..."
  }
]
```

---

## 2. Batch Generation: Zusammenfassungen mit Mistral & Magistral

### 2.1 Prompt Template erstellen

**Route:** `POST /api/prompt-engineering/prompts`

```json
{
  "name": "News Summarization DE",
  "description": "Generiert prägnante Zusammenfassungen von Nachrichtenartikeln",
  "content": {
    "blocks": {
      "system": {
        "content": "Du bist ein professioneller Journalist und Redakteur. Deine Aufgabe ist es, Nachrichtenartikel präzise und neutral zusammenzufassen. Halte dich an die Fakten und verwende einen sachlichen Schreibstil.",
        "position": 0
      },
      "default": {
        "content": "Fasse den folgenden Nachrichtenartikel in 2-3 Sätzen zusammen. Die Zusammenfassung soll die wichtigsten Informationen enthalten und für Leser verständlich sein, die den Originalartikel nicht gelesen haben.\n\n**Titel:** {{subject}}\n\n**Artikel:**\n{{content}}\n\n**Zusammenfassung:**",
        "position": 1
      }
    }
  },
  "variables": ["subject", "content"],
  "is_active": true
}
```

### 2.2 Batch Job erstellen

**Route:** `POST /api/generation/jobs`

```json
{
  "name": "News Summarization - Mistral vs Magistral",
  "description": "Vergleich von Mistral und Magistral für News-Zusammenfassungen",
  "config": {
    "sources": {
      "type": "scenario",
      "scenario_id": null
    },
    "prompts": [
      {
        "template_id": 1,
        "variant_name": "Standard",
        "variables": {}
      }
    ],
    "llm_models": [
      "mistral-large-latest",
      "magistral-medium-latest"
    ],
    "generation_params": {
      "temperature": 0.3,
      "top_p": 0.9,
      "max_tokens": 200
    },
    "limits": {
      "max_parallel": 3,
      "max_cost_usd": 5.0,
      "max_retries": 2
    }
  },
  "auto_start": false
}
```

**Alternative: Custom Text Input (ohne Szenario)**

```json
{
  "name": "News Summarization Test",
  "config": {
    "sources": {
      "type": "custom",
      "custom_texts": [
        {
          "subject": "Klimagipfel: Neue Ziele für CO2-Reduktion",
          "content": "Die Teilnehmer des Weltklimagipfels haben sich..."
        },
        {
          "subject": "Tech-Konzern kündigt KI-Durchbruch an",
          "content": "Ein führendes Technologieunternehmen..."
        }
      ]
    },
    "prompts": [{"template_id": 1, "variant_name": "Standard"}],
    "llm_models": ["mistral-large-latest", "magistral-medium-latest"],
    "generation_params": {
      "temperature": 0.3,
      "max_tokens": 200
    }
  },
  "auto_start": true
}
```

### 2.3 Job starten und überwachen

```bash
# Job starten
POST /api/generation/jobs/{job_id}/start

# Status abrufen (Polling)
GET /api/generation/jobs/{job_id}

# Outputs abrufen
GET /api/generation/jobs/{job_id}/outputs?include_prompts=true
```

### 2.4 Erwartete Output-Matrix

| Item | Modell | Output |
|------|--------|--------|
| news_001 | mistral-large | "Beim Klimagipfel einigten sich..." |
| news_001 | magistral-medium | "Die Teilnehmer beschlossen neue..." |
| news_002 | mistral-large | "Ein Tech-Unternehmen präsentierte..." |
| news_002 | magistral-medium | "Heute wurde ein KI-Fortschritt..." |

---

## 3. Ranking-Szenario erstellen

### 3.1 Direkt aus Batch Job (empfohlen)

**Route:** `POST /api/generation/jobs/{job_id}/to-scenario`

```json
{
  "scenario_name": "News Summary Quality Ranking",
  "evaluation_type": "ranking",
  "config_json": {
    "eval_type": "ranking",
    "eval_config": {
      "presetId": "buckets-3",
      "config": {
        "type": "buckets",
        "buckets": [
          { "id": 1, "name": { "de": "Gut", "en": "Good" }, "color": "#98d4bb" },
          { "id": 2, "name": { "de": "Moderat", "en": "Moderate" }, "color": "#D1BC8A" },
          { "id": 3, "name": { "de": "Schlecht", "en": "Poor" }, "color": "#e8a087" }
        ],
        "allowTies": true,
        "dragDrop": true
      }
    },
    "distribution_mode": "all",
    "order_mode": "random"
  }
}
```

### 3.2 Manuell via Scenario Wizard API

**Schritt 1: Szenario erstellen**

```bash
POST /api/scenarios
```

```json
{
  "scenario_name": "News Summary Quality Ranking",
  "function_type_id": 1,
  "description": "Bewertung der Zusammenfassungsqualität: Mistral vs Magistral",
  "config_json": {
    "eval_type": "ranking",
    "eval_config": {
      "presetId": "custom",
      "config": {
        "type": "buckets",
        "buckets": [
          { "id": 1, "name": { "de": "Gut", "en": "Good" }, "color": "#98d4bb", "description": "Präzise, vollständig, gut lesbar" },
          { "id": 2, "name": { "de": "Moderat", "en": "Moderate" }, "color": "#D1BC8A", "description": "Akzeptabel, aber verbesserungswürdig" },
          { "id": 3, "name": { "de": "Schlecht", "en": "Poor" }, "color": "#e8a087", "description": "Ungenau, unvollständig oder schlecht formuliert" }
        ],
        "allowTies": true,
        "dragDrop": true,
        "instructions": {
          "de": "Ordnen Sie jede Zusammenfassung einer Qualitätskategorie zu. Berücksichtigen Sie: Faktentreue, Vollständigkeit, Lesbarkeit.",
          "en": "Assign each summary to a quality category. Consider: Accuracy, completeness, readability."
        }
      }
    },
    "distribution_mode": "all",
    "order_mode": "random",
    "show_source": true
  }
}
```

**Schritt 2: Items importieren (aus Generation Outputs)**

```bash
POST /api/import/from-data
```

```json
{
  "scenario_id": 123,
  "task_type": "ranking",
  "source_name": "Batch Generation Import",
  "data": [
    {
      "id": "gen_output_1",
      "subject": "Mistral: Klimagipfel",
      "content": "Beim Klimagipfel einigten sich die Teilnehmer auf neue CO2-Ziele...",
      "metadata": {
        "source_article": "news_001",
        "model": "mistral-large-latest",
        "generation_job_id": 42
      }
    },
    {
      "id": "gen_output_2",
      "subject": "Magistral: Klimagipfel",
      "content": "Die Teilnehmer beschlossen beim Weltklimagipfel ambitionierte Reduktionsziele...",
      "metadata": {
        "source_article": "news_001",
        "model": "magistral-medium-latest",
        "generation_job_id": 42
      }
    }
  ]
}
```

**Schritt 3: Evaluatoren einladen**

```bash
POST /api/scenarios/123/invite
```

```json
{
  "user_ids": [2, 3, 4],
  "role": "EVALUATOR",
  "message": "Bitte bewerten Sie die Qualität der generierten Zusammenfassungen."
}
```

---

## 4. Kompletter API-Workflow (Sequenz)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: DATEN VORBEREITEN                       │
├─────────────────────────────────────────────────────────────────────┤
│ 1. News-Datensatz als JSON vorbereiten (lokal)                     │
│ 2. Optional: Basis-Szenario für Quelldaten erstellen               │
│    POST /api/scenarios (function_type_id=2, nur als Container)     │
│ 3. Daten importieren                                                │
│    POST /api/import/from-data                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: PROMPT ERSTELLEN                        │
├─────────────────────────────────────────────────────────────────────┤
│ 4. Summarization Prompt erstellen                                   │
│    POST /api/prompt-engineering/prompts                             │
│    → Speichere template_id                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: BATCH GENERATION                        │
├─────────────────────────────────────────────────────────────────────┤
│ 5. Kosten schätzen (optional)                                       │
│    POST /api/generation/estimate                                    │
│                                                                     │
│ 6. Batch Job erstellen                                              │
│    POST /api/generation/jobs                                        │
│    → config.sources.scenario_id = Quell-Szenario                   │
│    → config.llm_models = ["mistral-large", "magistral-medium"]     │
│    → config.prompts[0].template_id = Prompt ID                     │
│                                                                     │
│ 7. Job starten (falls auto_start=false)                            │
│    POST /api/generation/jobs/{job_id}/start                        │
│                                                                     │
│ 8. Status überwachen                                                │
│    GET /api/generation/jobs/{job_id}                               │
│    → Warten bis status = "completed"                               │
│                                                                     │
│ 9. Outputs abrufen                                                  │
│    GET /api/generation/jobs/{job_id}/outputs                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: RANKING SZENARIO                        │
├─────────────────────────────────────────────────────────────────────┤
│ 10. Ranking-Szenario aus Outputs erstellen                         │
│     POST /api/generation/jobs/{job_id}/to-scenario                 │
│     → evaluation_type = "ranking"                                  │
│     → Buckets: Gut / Moderat / Schlecht                           │
│                                                                     │
│ 11. Evaluatoren einladen                                           │
│     POST /api/scenarios/{scenario_id}/invite                       │
│                                                                     │
│ 12. Evaluation durchführen (UI)                                    │
│     → Evaluatoren ordnen Summaries den Buckets zu                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 5: ANALYSE                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 13. Ergebnisse abrufen                                             │
│     GET /api/scenarios/{scenario_id}/stats                         │
│                                                                     │
│ 14. Inter-Rater Agreement prüfen                                   │
│     GET /api/evaluation/agreement/{scenario_id}                    │
│                                                                     │
│ 15. Export                                                         │
│     POST /api/scenarios/{scenario_id}/export                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Beispiel-Skript (Python)

```python
import requests
import time

BASE_URL = "http://localhost:55080/api"
TOKEN = "your-auth-token"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# ============ PHASE 2: Prompt erstellen ============
prompt_data = {
    "name": "News Summarization DE",
    "content": {
        "blocks": {
            "system": {
                "content": "Du bist ein professioneller Journalist...",
                "position": 0
            },
            "default": {
                "content": "Fasse den folgenden Artikel zusammen:\n\n**Titel:** {{subject}}\n\n**Artikel:**\n{{content}}\n\n**Zusammenfassung:**",
                "position": 1
            }
        }
    },
    "variables": ["subject", "content"]
}

resp = requests.post(f"{BASE_URL}/prompt-engineering/prompts", json=prompt_data, headers=HEADERS)
prompt_id = resp.json()["id"]
print(f"Prompt erstellt: ID {prompt_id}")

# ============ PHASE 3: Batch Job ============
job_data = {
    "name": "News Summary Comparison",
    "config": {
        "sources": {
            "type": "custom",
            "custom_texts": [
                {"subject": "Klimagipfel", "content": "Die Teilnehmer des Klimagipfels..."},
                {"subject": "Tech-News", "content": "Ein Technologieunternehmen hat..."}
            ]
        },
        "prompts": [{"template_id": prompt_id, "variant_name": "Standard"}],
        "llm_models": ["mistral-large-latest", "magistral-medium-latest"],
        "generation_params": {"temperature": 0.3, "max_tokens": 200}
    },
    "auto_start": True
}

resp = requests.post(f"{BASE_URL}/generation/jobs", json=job_data, headers=HEADERS)
job_id = resp.json()["job"]["id"]
print(f"Job erstellt: ID {job_id}")

# Warten auf Completion
while True:
    resp = requests.get(f"{BASE_URL}/generation/jobs/{job_id}", headers=HEADERS)
    status = resp.json()["job"]["status"]
    progress = resp.json()["job"].get("progress_percent", 0)
    print(f"Status: {status}, Progress: {progress}%")
    if status in ["completed", "failed"]:
        break
    time.sleep(5)

# ============ PHASE 4: Ranking Szenario ============
scenario_data = {
    "scenario_name": "News Summary Quality Ranking",
    "evaluation_type": "ranking",
    "config_json": {
        "eval_type": "ranking",
        "eval_config": {
            "config": {
                "type": "buckets",
                "buckets": [
                    {"id": 1, "name": {"de": "Gut"}, "color": "#98d4bb"},
                    {"id": 2, "name": {"de": "Moderat"}, "color": "#D1BC8A"},
                    {"id": 3, "name": {"de": "Schlecht"}, "color": "#e8a087"}
                ],
                "allowTies": True
            }
        }
    }
}

resp = requests.post(f"{BASE_URL}/generation/jobs/{job_id}/to-scenario", json=scenario_data, headers=HEADERS)
scenario_id = resp.json()["scenario_id"]
print(f"Ranking-Szenario erstellt: ID {scenario_id}")

print(f"\n✅ Fertig! Öffne: http://localhost:55080/scenarios/{scenario_id}/evaluate")
```

---

## 6. Erwartete Ergebnisse

### Ranking-Verteilung (Beispiel)

| Modell | Gut | Moderat | Schlecht | Ø Qualität |
|--------|-----|---------|----------|------------|
| Mistral Large | 65% | 25% | 10% | 2.55 |
| Magistral Medium | 45% | 40% | 15% | 2.30 |

### Metriken

- **Inter-Rater Agreement (Fleiss' Kappa):** Misst Übereinstimmung zwischen Evaluatoren
- **Win-Rate pro Modell:** Wie oft wurde ein Modell als "Gut" eingestuft
- **Confusion Matrix:** Zeigt Verteilung über Buckets

---

## 7. Nächste Schritte

1. [ ] MLSUM-Datensatz herunterladen und als JSON formatieren
2. [ ] Prompt in Prompt Engineering erstellen
3. [ ] Batch Job mit beiden Modellen starten
4. [ ] Ranking-Szenario erstellen
5. [ ] 2-3 Evaluatoren einladen
6. [ ] Ergebnisse analysieren und dokumentieren

---

**Erstellt:** 27. Januar 2026
**Status:** Konzept
