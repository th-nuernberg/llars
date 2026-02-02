# LLARS Pipeline E2E-Test: Prompt Engineering → Batch Generation → Evaluation

**Stand:** 31. Januar 2026

## Konzept-Übersicht

Dieser Plan testet die vollständige Pipeline von der Prompt-Erstellung über die Batch-Generierung bis zur automatisierten LLM-Evaluation.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: PROMPT ENGINEERING                                                  │
│ ─────────────────────────────────────────────────────────────────────────── │
│  • Erstelle Summarization-Prompt über API                                    │
│  • Struktur: System-Block + User-Block mit {{content}} Variable              │
│  • Prompt wird versioniert und für Batch Generation verfügbar               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: BATCH GENERATION                                                    │
│ ─────────────────────────────────────────────────────────────────────────── │
│  • Input: 10 News-Artikel aus data/news_articles_sample.json                 │
│  • Prompt: Summarization-Template aus Phase 1                                │
│  • Modelle: 2 LLMs (z.B. GPT-4, Claude-3-Sonnet)                            │
│  • Matrix: 10 Artikel × 1 Prompt × 2 Modelle = 20 Outputs                   │
│  • Speichere Token-Counts + Kosten                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: SCENARIO WIZARD                                                     │
│ ─────────────────────────────────────────────────────────────────────────── │
│  • Konvertiere Batch-Outputs → Evaluation-Szenario                          │
│  • Typ: Multi-dimensionales Rating (LLM Evaluator Format)                   │
│  • Dimensionen: Coherence, Fluency, Relevance, Consistency                  │
│  • Reference: Original-Artikel als Kontext                                  │
│  • Items: LLM-generierte Zusammenfassungen                                  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: LLM-AS-ASSESSORS (Automatisierte Evaluation)                       │
│ ─────────────────────────────────────────────────────────────────────────── │
│  • LLM bewertet jeden Output auf Dimensionen                                │
│  • Score 1-5 pro Dimension mit Chain-of-Thought Reasoning                   │
│  • Ergebnisse werden in Szenario gespeichert                                │
│  • Agreement-Metriken berechenbar wenn mehrere LLMs bewerten               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Voraussetzungen

- LLARS läuft lokal (http://localhost:55080)
- LLM-Provider konfiguriert (OpenAI/Anthropic API Key in `.env`)
- Admin-Login: `admin` / `admin123`

---

## Phase 1: Prompt Engineering

### 1.1 API-Aufruf: Prompt erstellen

```bash
# Login und Token holen
TOKEN=$(curl -s -X POST http://localhost:55080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# Prompt erstellen
curl -X POST http://localhost:55080/api/prompts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "News Summarization v1",
    "content": {
      "blocks": {
        "block_system": {
          "title": "System",
          "content": "Du bist ein Experte für präzise Textzusammenfassungen. Erstelle kurze, informative Zusammenfassungen von Nachrichtenartikeln in 2-3 Sätzen. Fokussiere auf die wichtigsten Fakten.",
          "position": 0
        },
        "block_user": {
          "title": "User",
          "content": "Fasse folgenden Nachrichtenartikel zusammen:\n\nTitel: {{subject}}\n\nText: {{content}}",
          "position": 1
        }
      }
    }
  }'
```

**Erwartetes Ergebnis:**
```json
{
  "prompt_id": 1,
  "name": "News Summarization v1",
  "message": "Prompt created successfully"
}
```

### 1.2 Verifizierung im Frontend

1. Öffne http://localhost:55080/prompt-engineering
2. Sieh den neuen Prompt "News Summarization v1" in der Liste
3. Klicke zum Editieren und prüfe die Block-Struktur

---

## Phase 2: Batch Generation

### 2.1 Verfügbare Modelle prüfen

```bash
curl -s http://localhost:55080/api/llm/models/available \
  -H "Authorization: Bearer $TOKEN" | jq '.models[].name'
```

### 2.2 Batch-Job erstellen

```bash
# Testdaten laden
ITEMS=$(cat data/news_articles_sample.json)

# Job erstellen
curl -X POST http://localhost:55080/api/generation/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "News Summarization Test",
    "description": "E2E-Test: 10 Artikel × 2 Modelle",
    "config": {
      "mode": "matrix",
      "sources": {
        "type": "custom",
        "custom_texts": '"$ITEMS"'
      },
      "prompts": [
        {
          "template_id": 1,
          "variant_name": "Standard"
        }
      ],
      "llm_models": ["gpt-4o-mini", "claude-3-haiku-20240307"],
      "generation_params": {
        "temperature": 0.3,
        "max_tokens": 500
      }
    },
    "auto_start": true
  }'
```

**Erwartetes Ergebnis:**
```json
{
  "job_id": 1,
  "name": "News Summarization Test",
  "status": "QUEUED",
  "total_items": 20
}
```

### 2.3 Job-Status überwachen

```bash
# Poll Status
curl -s http://localhost:55080/api/generation/jobs/1 \
  -H "Authorization: Bearer $TOKEN" | jq '{status, completed_items, total_items}'
```

### 2.4 Verifizierung im Frontend

1. Öffne http://localhost:55080/batch-generation
2. Sieh den Job "News Summarization Test" in der Liste
3. Beobachte den Fortschrittsbalken (0/20 → 20/20)
4. Nach Abschluss: Klicke auf "Outputs anzeigen"

---

## Phase 3: Szenario erstellen (Scenario Wizard)

### 3.1 Batch-Outputs → Szenario konvertieren

```bash
curl -X POST http://localhost:55080/api/generation/jobs/1/to-scenario \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_name": "LLM Summarization Evaluation",
    "function_type": "rating",
    "config": {
      "type": "multi-dimensional",
      "min": 1,
      "max": 5,
      "step": 1,
      "dimensions": [
        {"id": "coherence", "name": {"de": "Kohärenz", "en": "Coherence"}, "weight": 0.25},
        {"id": "fluency", "name": {"de": "Flüssigkeit", "en": "Fluency"}, "weight": 0.25},
        {"id": "relevance", "name": {"de": "Relevanz", "en": "Relevance"}, "weight": 0.25},
        {"id": "consistency", "name": {"de": "Konsistenz", "en": "Consistency"}, "weight": 0.25}
      ],
      "labels": {
        "1": {"de": "Sehr schlecht", "en": "Very poor"},
        "2": {"de": "Schlecht", "en": "Poor"},
        "3": {"de": "Mittel", "en": "Average"},
        "4": {"de": "Gut", "en": "Good"},
        "5": {"de": "Sehr gut", "en": "Excellent"}
      }
    },
    "include_reference": true
  }'
```

**Erwartetes Ergebnis:**
```json
{
  "scenario_id": 1,
  "name": "LLM Summarization Evaluation",
  "items_count": 20,
  "function_type": "rating"
}
```

### 3.2 Verifizierung im Frontend

1. Öffne http://localhost:55080/evaluation
2. Sieh das neue Szenario "LLM Summarization Evaluation"
3. Klicke auf "Details" → Prüfe die 20 Items
4. Prüfe die Rating-Dimensionen in der Config

---

## Phase 4: LLM-as-Assessors (Automatisierte Bewertung)

### 4.1 Judge-Session starten

```bash
curl -X POST http://localhost:55080/api/judge/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": 1,
    "judge_model": "gpt-4o",
    "evaluation_type": "dimensional_rating",
    "config": {
      "dimensions": ["coherence", "fluency", "relevance", "consistency"],
      "include_reasoning": true
    }
  }'
```

### 4.2 Alternative: Manuelle Evaluation testen

1. Öffne http://localhost:55080/evaluation/1/session
2. Führe manuelle Bewertungen durch
3. Prüfe die Likert-Skalen pro Dimension

### 4.3 Agreement-Metriken abrufen (nach mehreren Bewertungen)

```bash
curl -s http://localhost:55080/api/evaluation/1/agreement-metrics \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Verifizierungs-Checkliste

### Phase 1: Prompt Engineering ✅
- [ ] Prompt in Datenbank erstellt
- [ ] Prompt im Frontend sichtbar
- [ ] Block-Struktur korrekt (System + User)
- [ ] Variable `{{content}}` und `{{subject}}` vorhanden

### Phase 2: Batch Generation ✅
- [ ] Job erstellt mit Status QUEUED
- [ ] Job wechselt zu RUNNING
- [ ] Fortschritt aktualisiert sich (X/20)
- [ ] Job endet mit Status COMPLETED
- [ ] 20 Outputs generiert
- [ ] Token-Counts und Kosten erfasst

### Phase 3: Scenario Wizard ✅
- [ ] Szenario erstellt mit korrektem Typ (rating)
- [ ] 20 Items im Szenario
- [ ] Reference (Original-Text) vorhanden
- [ ] 4 Dimensionen konfiguriert
- [ ] Source-Type = "llm" für alle Items

### Phase 4: Evaluation ✅
- [ ] Szenario in Evaluation-Hub sichtbar
- [ ] Rating-Interface zeigt Dimensionen
- [ ] Manuelle Bewertung funktioniert
- [ ] Automatische LLM-Bewertung startet
- [ ] Ergebnisse werden gespeichert
- [ ] Agreement-Metriken berechenbar

---

## Fehlerbehandlung

| Problem | Mögliche Ursache | Lösung |
|---------|------------------|--------|
| 401 Unauthorized | Token abgelaufen | Neu einloggen |
| Job bleibt QUEUED | Worker nicht aktiv | `docker logs llars_flask_service` prüfen |
| Keine Modelle verfügbar | API Key fehlt | `.env` prüfen: `OPENAI_API_KEY` |
| Scenario-Erstellung schlägt fehl | Ungültige Config | Schema validieren |
| Agreement-Metriken leer | Nicht genug Ratings | Mind. 2 Rater benötigt |

---

## Erwartete Ergebnisse nach Durchführung

Nach erfolgreichem Test sollten folgende Artefakte in LLARS existieren:

1. **Prompt Engineering** → "News Summarization v1"
2. **Batch Generation** → "News Summarization Test" (20 Outputs)
3. **Evaluation** → "LLM Summarization Evaluation" (Rating-Szenario)
4. **Ratings** → Bewertungen auf 4 Dimensionen

Alle können im Frontend unter den jeweiligen Bereichen eingesehen werden.
