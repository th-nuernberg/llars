# LLARS Pipeline E2E-Test: Anleitung

**Datum:** 31. Januar 2026
**Getestet von:** Claude Code

---

## Zusammenfassung

Die vollständige Pipeline von **Prompt Engineering → Batch Generation → Evaluation (LLM-as-Assessors)** wurde erfolgreich getestet.

### Ergebnisse im System

Nach dem Test findest du folgende Artefakte in LLARS:

| Bereich | Name | ID | Zugriff |
|---------|------|----|----|
| **Prompt Engineering** | "News Summarization Test" | 2 | http://localhost:55080/prompt-engineering |
| **Batch Generation** | "News Summarization E2E Test" | 1 | http://localhost:55080/batch-generation |
| **Szenario** | "News Summarization Rating Test" | 27 | http://localhost:55080/scenarios/27 |
| **LLM-as-Judge Demo** | "LLM-as-Judge Demo" | 5 | http://localhost:55080/scenarios/5 |

---

## Schritt-für-Schritt Anleitung

### Voraussetzungen

1. LLARS läuft lokal (`./start_llars.sh`)
2. Zugriff auf http://localhost:55080
3. Login-Daten: `admin` / `admin123`

---

### Phase 1: Prompt Engineering

**Ziel:** Ein Prompt für Textzusammenfassungen erstellen.

#### Im Frontend

1. Öffne http://localhost:55080/prompt-engineering
2. Klicke "Neuer Prompt"
3. Name: `News Summarization Test`
4. Füge 2 Blöcke hinzu:

**Block 1 - System:**
```
Du bist ein Experte für präzise Textzusammenfassungen.
Erstelle kurze, informative Zusammenfassungen in 2-3 Sätzen.
Fokussiere auf die wichtigsten Fakten.
```

**Block 2 - User:**
```
Fasse folgenden Nachrichtenartikel zusammen:

Titel: {{subject}}

Text: {{content}}
```

5. Klicke "Speichern"

#### Verifizierung
- Prompt erscheint in der Liste
- Block-Struktur mit Variablen `{{subject}}` und `{{content}}` sichtbar

---

### Phase 2: Batch Generation

**Ziel:** Mehrere LLM-Outputs mit dem Prompt generieren.

#### Im Frontend

1. Öffne http://localhost:55080/batch-generation
2. Klicke "Neuer Job"
3. Konfiguration:

| Feld | Wert |
|------|------|
| Name | News Summarization E2E Test |
| Prompt | "News Summarization Test" (aus Phase 1) |
| Modell | Mistral Small 3.2 |
| Temperatur | 0.3 |

4. **Daten hochladen** - Nutze eine der folgenden Optionen:

**Option A: Custom Texts eingeben**
```json
[
  {"subject": "Klimagipfel", "content": "Die Teilnehmer des Weltklimagipfels haben sich auf neue ambitionierte Ziele geeinigt..."},
  {"subject": "KI-Technologie", "content": "Ein führendes Technologieunternehmen hat heute einen bedeutenden Fortschritt vorgestellt..."},
  {"subject": "Inflation", "content": "Die Inflationsrate in Deutschland ist auf 2,4 Prozent gesunken..."}
]
```

**Option B: Testdaten-Datei verwenden**
- Datei: `data/news_articles_sample.json` (10 Artikel)

5. Klicke "Job starten"

#### Verifizierung
- Job erscheint mit Status "Queued" → "Running" → "Completed"
- Fortschrittsbalken zeigt X/Y Outputs
- Nach Abschluss: Outputs mit generierten Zusammenfassungen sichtbar

---

### Phase 3: Szenario erstellen

**Ziel:** Evaluation-Szenario aus den Batch-Outputs erstellen.

#### Im Frontend (Scenario Wizard)

1. Öffne http://localhost:55080/scenario-wizard
2. Wähle "Aus Batch Generation importieren"
3. Wähle den Job "News Summarization E2E Test"
4. Konfiguration:

| Feld | Wert |
|------|------|
| Szenario-Name | LLM Summarization Evaluation |
| Evaluationstyp | Rating (Multi-dimensional) |
| Preset | LLM Judge Standard |

5. Dimensionen konfigurieren:
   - Kohärenz (25%)
   - Flüssigkeit (25%)
   - Relevanz (25%)
   - Konsistenz (25%)

6. Klicke "Szenario erstellen"

#### Verifizierung
- Szenario erscheint in http://localhost:55080/evaluation
- Items enthalten die LLM-generierten Zusammenfassungen
- Dimensionen sind konfiguriert

---

### Phase 4: LLM-as-Assessors (Automatisierte Bewertung)

**Ziel:** LLM bewertet die generierten Outputs automatisch.

#### Im Frontend

1. Öffne das Szenario (z.B. http://localhost:55080/scenarios/5)
2. Gehe zu "Einstellungen" → "LLM Evaluatoren"
3. Aktiviere "LLM Evaluation"
4. Wähle Modelle:
   - Mistral Small 3.2
   - Magistral Small (optional für Vergleich)
5. Klicke "Evaluation starten"

#### Verifizierung
- Fortschrittsanzeige: "Evaluiere Item X von Y"
- Nach Abschluss: 100% Progress
- LLM-Bewertungen sichtbar neben menschlichen Bewertungen

---

### Phase 5: Ergebnisse analysieren

**Ziel:** Agreement-Metriken und Statistiken prüfen.

#### Im Frontend

1. Öffne das Szenario → "Statistiken"
2. Prüfe:
   - **Progress:** Alle Items bewertet
   - **LLM vs. Mensch:** Vergleich der Bewertungen
   - **Agreement-Metriken:** Krippendorff's Alpha, Cohen's Kappa

---

## API-Befehle (Referenz)

Falls du die Tests per API wiederholen möchtest:

### Login
```bash
TOKEN=$(curl -s -X POST http://localhost:55080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')
```

### Prompt erstellen
```bash
curl -X POST http://localhost:55080/api/prompts \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Prompt",
    "content": {"blocks": {"system": {"title": "System", "content": "...", "position": 0}}}
  }'
```

### Batch Job erstellen
```bash
curl -X POST http://localhost:55080/api/generation/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Job",
    "config": {
      "sources": {"type": "custom", "custom_texts": [...]},
      "prompts": [{"template_id": 2}],
      "llm_models": ["mistralai/Mistral-Small-3.2-24B-Instruct-2506"]
    },
    "auto_start": true
  }'
```

### Job-Status prüfen
```bash
curl http://localhost:55080/api/generation/jobs/1 \
  -H "Authorization: Bearer $TOKEN"
```

### LLM-Evaluation Progress
```bash
curl http://localhost:55080/api/evaluation/llm/5/progress \
  -H "Authorization: Bearer $TOKEN"
```

---

## Bekannte Issues

1. **to-scenario Bug:** Die Route `/api/generation/jobs/{id}/to-scenario` hat einen SQL-Fehler bei custom_texts mit Dict-Struktur. Workaround: Szenario manuell über Wizard erstellen.

2. **Szenario ohne Items:** Wenn ein Szenario leer ist, muss man Items über den Wizard oder die `/api/scenarios/{id}/threads` Endpoint hinzufügen.

---

## Nächste Schritte

1. **Mehr Modelle testen:** Verschiedene LLMs in Batch Generation verwenden
2. **Größere Datenmengen:** `data/news_articles_sample.json` mit allen 10 Artikeln
3. **Agreement-Analyse:** Mehrere LLM-Evaluatoren vergleichen
4. **Comparison-Modus:** Pairwise-Vergleiche über Judge-Sessions testen

---

## Prozess-Nachverfolgung

Um die Prozesskette nachzuvollziehen:

1. **Prompt:** http://localhost:55080/prompt-engineering → "News Summarization Test"
2. **Batch Job:** http://localhost:55080/batch-generation → "News Summarization E2E Test"
3. **Szenario:** http://localhost:55080/scenarios/27 → "News Summarization Rating Test"
4. **LLM-Demo:** http://localhost:55080/scenarios/5 → "LLM-as-Judge Demo" (zeigt vollständige Evaluation)

Alle Komponenten sind miteinander verknüpft und im Frontend sichtbar.
