---
name: llars-api-guide
description: Guide for using LLARS APIs including Prompt Engineering, Batch Generation, Scenario Wizard, and LLM Evaluation. Use when creating prompts, generating content with LLMs, creating evaluation scenarios, or working with the LLARS API.
---

# LLARS API Guide

Vollständige Anleitung zur Nutzung der LLARS APIs für Prompt Engineering, Batch Generation, Szenario Wizard und LLM Evaluation.

## Quick Start

### Authentifizierung

Alle API-Aufrufe benötigen einen Bearer Token:

```bash
# Login und Token speichern
TOKEN=$(curl -s -X POST http://localhost:55080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

# Token in allen Requests verwenden
curl -H "Authorization: Bearer $TOKEN" http://localhost:55080/api/...
```

**Verfügbare User:**
| User | Passwort | Rolle |
|------|----------|-------|
| admin | admin123 | admin |
| researcher | admin123 | researcher |
| evaluator | admin123 | evaluator |

---

## 1. Prompt Engineering API

**Base URL:** `/api/prompts`

### Prompt-Struktur

Prompts bestehen aus Blöcken (YJS-basiert):

```json
{
  "name": "Mein Prompt",
  "content": {
    "blocks": {
      "system": {
        "title": "System",
        "content": "Du bist ein hilfreicher Assistent...",
        "position": 0
      },
      "user": {
        "title": "User",
        "content": "Bearbeite: {{content}}",
        "position": 1
      }
    }
  }
}
```

### Variablen

Variablen werden in doppelten geschweiften Klammern definiert:

| Variable | Alias | Beschreibung |
|----------|-------|--------------|
| `{{content}}` | `{{input}}`, `{{text}}` | Haupttext |
| `{{subject}}` | `{{betreff}}` | Betreff/Titel |
| `{{messages}}` | `{{email_content}}` | Konversation |

### API Endpoints

#### Prompt erstellen

```bash
curl -X POST http://localhost:55080/api/prompts \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Summarization Prompt",
    "content": {
      "blocks": {
        "system": {
          "title": "System",
          "content": "Du bist ein Experte für Zusammenfassungen. Erstelle präzise Zusammenfassungen in 2-3 Sätzen.",
          "position": 0
        },
        "user": {
          "title": "User",
          "content": "Fasse zusammen:\n\nTitel: {{subject}}\n\nText: {{content}}",
          "position": 1
        }
      }
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Summarization Prompt"
  }
}
```

#### Prompts auflisten

```bash
curl http://localhost:55080/api/prompts \
  -H "Authorization: Bearer $TOKEN"
```

#### Prompt abrufen

```bash
curl http://localhost:55080/api/prompts/1 \
  -H "Authorization: Bearer $TOKEN"
```

#### Prompt aktualisieren

```bash
curl -X PUT http://localhost:55080/api/prompts/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "content": {
      "blocks": { ... }
    }
  }'
```

#### Prompt umbenennen

```bash
curl -X PUT http://localhost:55080/api/prompts/1/rename \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name": "Neuer Name"}'
```

#### Prompt teilen

```bash
curl -X POST http://localhost:55080/api/prompts/1/share \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 2}'
```

#### Prompt-Versionen (Git-artig)

```bash
# Commit erstellen
curl -X POST http://localhost:55080/api/prompts/1/commit \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"message": "Verbesserte Anweisungen"}'

# Commits auflisten
curl http://localhost:55080/api/prompts/1/commits \
  -H "Authorization: Bearer $TOKEN"

# Rollback
curl -X POST http://localhost:55080/api/prompts/1/rollback \
  -H "Authorization: Bearer $TOKEN"
```

---

## 2. Batch Generation API

**Base URL:** `/api/generation`

### Job-Konfiguration

```json
{
  "name": "Job Name",
  "description": "Beschreibung",
  "config": {
    "mode": "matrix",

    "sources": {
      "type": "custom",
      "custom_texts": [
        {"subject": "Titel 1", "content": "Text 1..."},
        {"subject": "Titel 2", "content": "Text 2..."}
      ]
    },

    "prompts": [
      {
        "template_id": 1,
        "variant_name": "Standard"
      }
    ],

    "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],

    "generation_params": {
      "temperature": 0.7,
      "max_tokens": 500
    }
  },
  "auto_start": true
}
```

### Source Types

| Type | Beschreibung | Beispiel |
|------|--------------|----------|
| `scenario` | Items aus bestehendem Szenario | `{"type": "scenario", "scenario_id": 123}` |
| `items` | Direkte Item-IDs | `{"type": "items", "item_ids": [1, 2, 3]}` |
| `custom` | Eigene Texte | `{"type": "custom", "custom_texts": [...]}` |
| `manual` | Upload-Daten | `{"type": "manual", "items": [...]}` |

### API Endpoints

#### Verfügbare Modelle prüfen

```bash
curl http://localhost:55080/api/llm/models/available \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json; [print(f'{m[\"display_name\"]} ({m[\"model_id\"]})') for m in json.load(sys.stdin).get('models',[]) if m.get('model_type')=='llm']"
```

#### Job erstellen

```bash
curl -X POST http://localhost:55080/api/generation/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "News Summarization",
    "config": {
      "mode": "matrix",
      "sources": {
        "type": "custom",
        "custom_texts": [
          {"subject": "Klimagipfel", "content": "Die Teilnehmer des Weltklimagipfels..."},
          {"subject": "Technologie", "content": "Ein Tech-Konzern präsentierte..."}
        ]
      },
      "prompts": [{"template_id": 1, "variant_name": "Standard"}],
      "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"],
      "generation_params": {"temperature": 0.3, "max_tokens": 300}
    },
    "auto_start": true
  }'
```

**Response:**
```json
{
  "success": true,
  "job": {
    "id": 1,
    "status": "queued",
    "progress": {"total": 2, "completed": 0}
  },
  "auto_started": true
}
```

#### Job-Status prüfen

```bash
curl http://localhost:55080/api/generation/jobs/1 \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys,json; j=json.load(sys.stdin).get('job',{}); print(f'Status: {j.get(\"status\")}, Progress: {j.get(\"progress\",{}).get(\"completed\")}/{j.get(\"progress\",{}).get(\"total\")}')"
```

#### Outputs abrufen

```bash
curl "http://localhost:55080/api/generation/jobs/1/outputs" \
  -H "Authorization: Bearer $TOKEN"
```

#### Job pausieren/fortsetzen

```bash
# Pausieren
curl -X POST http://localhost:55080/api/generation/jobs/1/pause \
  -H "Authorization: Bearer $TOKEN"

# Fortsetzen
curl -X POST http://localhost:55080/api/generation/jobs/1/start \
  -H "Authorization: Bearer $TOKEN"
```

#### Outputs exportieren

```bash
# Als CSV
curl -X POST http://localhost:55080/api/generation/jobs/1/export/csv \
  -H "Authorization: Bearer $TOKEN" \
  -o outputs.csv

# Als JSON
curl -X POST http://localhost:55080/api/generation/jobs/1/export/json \
  -H "Authorization: Bearer $TOKEN"
```

#### Szenario aus Outputs erstellen

```bash
curl -X POST http://localhost:55080/api/generation/jobs/1/to-scenario \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_name": "LLM Output Evaluation",
    "evaluation_type": "rating",
    "config_json": {
      "type": "multi-dimensional",
      "min": 1,
      "max": 5,
      "dimensions": [
        {"id": "coherence", "name": {"de": "Kohärenz", "en": "Coherence"}, "weight": 0.25},
        {"id": "fluency", "name": {"de": "Flüssigkeit", "en": "Fluency"}, "weight": 0.25},
        {"id": "relevance", "name": {"de": "Relevanz", "en": "Relevance"}, "weight": 0.25},
        {"id": "consistency", "name": {"de": "Konsistenz", "en": "Consistency"}, "weight": 0.25}
      ]
    }
  }'
```

---

## 3. Szenario Wizard API

**Base URL:** `/api/wizard`

### Wizard Session Flow

```
1. Session erstellen → 2. Datei hochladen → 3. AI analysieren → 4. Config anpassen → 5. Szenario erstellen
```

### API Endpoints

#### Session erstellen

```bash
curl -X POST http://localhost:55080/api/wizard/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Response:**
```json
{
  "session_id": "abc123",
  "status": "created"
}
```

#### Datei hochladen

```bash
curl -X POST "http://localhost:55080/api/wizard/sessions/abc123/files" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@data/news_articles_sample.json"
```

#### AI-Analyse starten

```bash
curl -X POST "http://localhost:55080/api/wizard/sessions/abc123/analyze" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "suggested_type": "rating",
  "suggested_preset": "llm-judge-standard",
  "detected_fields": ["subject", "content", "reference_summary"],
  "item_count": 10
}
```

#### Konfiguration anpassen

```bash
curl -X PUT "http://localhost:55080/api/wizard/sessions/abc123/config" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "evaluation_type": "rating",
    "preset_id": "llm-judge-standard",
    "field_mapping": {
      "content": "content",
      "reference": "reference_summary"
    }
  }'
```

#### Preview

```bash
curl -X POST "http://localhost:55080/api/wizard/sessions/abc123/preview" \
  -H "Authorization: Bearer $TOKEN"
```

#### Szenario erstellen

```bash
curl -X POST "http://localhost:55080/api/wizard/sessions/abc123/create" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_name": "News Rating",
    "description": "Bewertung von Nachrichtenartikeln"
  }'
```

### Unterstützte Dateiformate

| Format | Beispiel |
|--------|----------|
| **CSV** | `id,text,summary` |
| **JSON** | `[{"id": 1, "content": "..."}]` |
| **JSONL** | `{"id": 1}\n{"id": 2}` |
| **OpenAI/LMSYS** | `{"conversation_a": [...], "conversation_b": [...], "winner": "A"}` |

---

## 4. Scenarios API

**Base URL:** `/api/scenarios`

### Evaluationstypen

| Typ | ID | Beschreibung |
|-----|----|--------------|
| `ranking` | 1 | Items sortieren |
| `rating` | 2 | Multi-dimensionale Bewertung |
| `mail_rating` | 3 | E-Mail-Bewertung |
| `comparison` | 4 | Paarweiser Vergleich |
| `authenticity` | 5 | Fake/Echt Erkennung |
| `labeling` | 7 | Kategorisierung |

### API Endpoints

#### Szenario erstellen

```bash
curl -X POST http://localhost:55080/api/scenarios \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_name": "Mein Rating Szenario",
    "function_type_id": 2,
    "config_json": {
      "type": "multi-dimensional",
      "min": 1,
      "max": 5,
      "dimensions": [
        {"id": "quality", "name": {"de": "Qualität"}, "weight": 1.0}
      ]
    }
  }'
```

#### Szenarien auflisten

```bash
curl http://localhost:55080/api/scenarios \
  -H "Authorization: Bearer $TOKEN"
```

#### Szenario abrufen

```bash
curl http://localhost:55080/api/scenarios/1 \
  -H "Authorization: Bearer $TOKEN"
```

#### Szenario aktualisieren

```bash
curl -X PUT http://localhost:55080/api/scenarios/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "config_json": {
      "enable_llm_evaluation": true,
      "llm_evaluators": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]
    }
  }'
```

---

## 5. LLM Evaluation API

**Base URL:** `/api/evaluation/llm`

### LLM-Evaluator zu Szenario hinzufügen

```bash
curl -X PUT http://localhost:55080/api/scenarios/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "config_json": {
      "enable_llm_evaluation": true,
      "llm_evaluators": [
        "mistralai/Mistral-Small-3.2-24B-Instruct-2506",
        "mistralai/Magistral-Small-2509"
      ],
      "dimensions": [
        {"id": "coherence", "name": {"de": "Kohärenz"}, "weight": 0.25},
        {"id": "fluency", "name": {"de": "Flüssigkeit"}, "weight": 0.25},
        {"id": "relevance", "name": {"de": "Relevanz"}, "weight": 0.25},
        {"id": "consistency", "name": {"de": "Konsistenz"}, "weight": 0.25}
      ]
    }
  }'
```

### Evaluation Progress prüfen

```bash
curl http://localhost:55080/api/evaluation/llm/1/progress \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "scenario_id": 1,
  "status": "completed",
  "progress": {
    "total": 24,
    "completed": 24,
    "percent": 100.0
  },
  "model_progress": {
    "mistralai/Mistral-Small-3.2-24B-Instruct-2506": {
      "completed": 12,
      "total": 12
    }
  }
}
```

---

## 6. Komplettes Beispiel: E2E Pipeline

### Schritt 1: Prompt erstellen

```bash
TOKEN=$(curl -s -X POST http://localhost:55080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

PROMPT_ID=$(curl -s -X POST http://localhost:55080/api/prompts \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "News Summary",
    "content": {
      "blocks": {
        "system": {"title": "System", "content": "Fasse Nachrichtenartikel in 2 Sätzen zusammen.", "position": 0},
        "user": {"title": "User", "content": "Titel: {{subject}}\n\n{{content}}", "position": 1}
      }
    }
  }' | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('id',''))")

echo "Prompt erstellt: ID $PROMPT_ID"
```

### Schritt 2: Batch Generation starten

```bash
JOB_ID=$(curl -s -X POST http://localhost:55080/api/generation/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "News Test",
    "config": {
      "sources": {
        "type": "custom",
        "custom_texts": [
          {"subject": "Klimagipfel", "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue Ziele geeinigt."},
          {"subject": "Technologie", "content": "Ein Tech-Konzern stellte eine neue KI vor."}
        ]
      },
      "prompts": [{"template_id": '"$PROMPT_ID"'}],
      "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]
    },
    "auto_start": true
  }' | python3 -c "import sys,json; print(json.load(sys.stdin).get('job',{}).get('id',''))")

echo "Job gestartet: ID $JOB_ID"
```

### Schritt 3: Auf Abschluss warten

```bash
while true; do
  STATUS=$(curl -s http://localhost:55080/api/generation/jobs/$JOB_ID \
    -H "Authorization: Bearer $TOKEN" | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('job',{}).get('status',''))")
  echo "Status: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 2
done
```

### Schritt 4: Szenario erstellen

```bash
SCENARIO_ID=$(curl -s -X POST http://localhost:55080/api/generation/jobs/$JOB_ID/to-scenario \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "scenario_name": "News Evaluation",
    "evaluation_type": "rating",
    "config_json": {
      "dimensions": [
        {"id": "quality", "name": {"de": "Qualität"}, "weight": 1.0}
      ]
    }
  }' | python3 -c "import sys,json; print(json.load(sys.stdin).get('scenario_id',''))")

echo "Szenario erstellt: ID $SCENARIO_ID"
```

### Schritt 5: LLM-Evaluation aktivieren

```bash
curl -X PUT http://localhost:55080/api/scenarios/$SCENARIO_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "config_json": {
      "enable_llm_evaluation": true,
      "llm_evaluators": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]
    }
  }'

echo "LLM-Evaluator aktiviert"
```

---

## 7. Testdaten

Verfügbare Testdaten in `data/`:

| Datei | Beschreibung |
|-------|--------------|
| `news_articles_sample.json` | 10 Nachrichtenartikel mit Referenz-Zusammenfassungen |
| `szenario_wizard/rating-llm-responses.json` | Q&A-Paare mit Qualitäts-Labels |
| `szenario_wizard/ranking-summaries-short.csv` | Ranking-Daten mit 3 Zusammenfassungs-Varianten |
| `szenario_wizard/mail-rating-conversations.json` | E-Mail-Beratungsgespräche |

### Testdaten laden

```bash
# JSON-Daten als custom_texts verwenden
ITEMS=$(cat data/news_articles_sample.json)

curl -X POST http://localhost:55080/api/generation/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Full News Test",
    "config": {
      "sources": {"type": "custom", "custom_texts": '"$ITEMS"'},
      "prompts": [{"template_id": 1}],
      "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]
    }
  }'
```

---

## 8. Frontend URLs

| Bereich | URL |
|---------|-----|
| Prompt Engineering | http://localhost:55080/prompt-engineering |
| Batch Generation | http://localhost:55080/batch-generation |
| Szenario Wizard | http://localhost:55080/scenario-wizard |
| Evaluation Hub | http://localhost:55080/evaluation |
| Szenarien | http://localhost:55080/scenarios |
| Admin Dashboard | http://localhost:55080/admin |

---

## 9. Troubleshooting

| Problem | Lösung |
|---------|--------|
| 401 Unauthorized | Token abgelaufen → Neu einloggen |
| Job bleibt "queued" | Flask-Logs prüfen: `docker logs llars_flask_service` |
| Keine Modelle verfügbar | `.env` prüfen: `OPENAI_API_KEY` oder `LITELLM_API_KEY` |
| to-scenario schlägt fehl | Prüfe ob Job "completed" ist |
| LLM-Evaluation startet nicht | `enable_llm_evaluation: true` in config_json setzen |
