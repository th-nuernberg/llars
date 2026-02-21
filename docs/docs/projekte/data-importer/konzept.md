# LLARS Data Importer - Konzept

!!! info "Status: Implementiert (Wizard)"
    Der Data Importer ist im LLARS-Frontend umgesetzt.
    Einige Abschnitte in diesem Dokument beschreiben geplante Erweiterungen und sind als **geplant** markiert.

**Erstellt:** 2026-01-05
**Autor:** Philipp Steigerwald
**Version:** 1.0

---

## Ziel

> Ein universeller, KI-gestützter Daten-Import-Wizard, der Benutzer durch den gesamten Prozess führt:
> **Daten hochladen → KI-Analyse (Intent) → Review & Konfiguration → Benutzer zuweisen → Import ausführen**

Der LLARS Data Importer macht das System für jeden nutzbar - unabhängig vom Datenformat.
"AI by Design" bedeutet: Ein LLM hilft aktiv beim Verstehen, Transformieren und Aufbereiten der Daten.

---

## Kernprinzipien

### AI by Design

| Prinzip | Umsetzung |
|---------|-----------|
| **LLM als Helfer** | LLM analysiert hochgeladene Daten und schlägt Transformationen vor |
| **Optionale KI** | Jeder LLM-Vorschlag kann abgelehnt werden - volle Kontrolle beim User |
| **Transparenz** | User sieht immer was das LLM vorschlägt bevor es angewendet wird |
| **Lernend** | **Geplant:** System merkt sich erfolgreiche Mappings für ähnliche Datensätze |

### Wizard-Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     LLARS DATA IMPORTER WIZARD                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [1. Upload] → [2. Describe] → [3. Review & Configure] → [4. Users]  │
│      ↓               ↓                   ↓                 ↓          │
│   Dateien       Intent +            Szenario-          Evaluators/     │
│   hochladen     KI-Analyse          Konfiguration      Viewer wählen   │
│                                                                       │
│                          →  [5. Execute Import]                       │
│                                  ↓                                   │
│                           Import starten & abschließen                │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Anwendungsszenarien

### Unterstützte Evaluationstypen

| task_type | Beschreibung | Datenstruktur (Kurz) |
|----------|--------------|----------------------|
| **rating** | Bewertung einzelner Antworten/Features | Konversation oder Einzeltext |
| **ranking** | Sortierung von Varianten (Drag & Drop) | Referenz + mehrere Outputs |
| **mail_rating** | Bewertung ganzer Konversationen | Konversation |
| **comparison** | Paarweiser Vergleich (A vs B) | text_a/text_b |
| **authenticity** | Fake/Real Unterscheidung | Konversation oder Text + Label |
| **labeling** | Klassifikation | Einzeltext + Label |

Hinweis: **LLM Evaluators** sind eine Konfiguration im Scenario Manager (kein eigener `task_type`).

### Konkrete Use Cases

#### Use Case 1: Mensch vs. Maschine Ranking
> "Ich habe 500 Konversationen. Ich möchte dass Menschen und ein LLM diese ranken."

**Workflow:**
1. Upload: JSON/CSV mit Konversationen
2. KI: Erkennt Konversationsstruktur, schlägt Mapping vor
3. Review: "Ranking" auswählen und Konfiguration prüfen
4. Benutzer: Evaluators/Viewer zuweisen
5. Import: Ausführen und anschließend im Scenario Manager weiterarbeiten
6. Optional: LLM Evaluators im Scenario Manager aktivieren

#### Use Case 2: Fake/Real Detection
> "Ich habe synthetische und echte E-Mails. Menschen sollen erkennen was fake ist."

**Workflow:**
1. Upload: Zwei Ordner (fake/, real/) oder JSON mit `is_fake` Flag
2. KI: Erkennt Authenticity-Format
3. Transform: Keine Transformation nötig
4. Szenario: "Authenticity" auswählen
5. Benutzer: Evaluators zuweisen
6. Import ausführen und Evaluation im Scenario Manager starten

#### Use Case 3: LLM Output Qualität
> "Ich habe Outputs von GPT-4 und Claude. Menschen sollen bewerten welcher besser ist."

**Workflow:**
1. Upload: JSONL mit `{prompt, response_a, response_b, model_a, model_b}`
2. KI: Erkennt Pairwise-Comparison Format (LMSYS-Style)
3. Transform: Mapping zu LLARS Comparison Schema
4. Szenario: "Comparison" mit Modell-Labels
5. Benutzer: Evaluators zuweisen
6. Import ausführen und Side-by-Side Evaluation starten

#### Use Case 4: Beratungsqualität bewerten
> "Ich habe Beratungsgespräche. Experten sollen die Qualität bewerten."

**Workflow:**
1. Upload: JSON mit Konversationen (Client ↔ Berater)
2. KI: Erkennt Rollen, schlägt Mapping vor
3. Review: "Rating" oder "Mail Rating" auswählen
4. Benutzer: Domain-Experten als Evaluators zuweisen
5. Import ausführen und Experten-Evaluation starten

#### Use Case 5: Custom Dataset
> "Ich habe ein eigenes Format das LLARS nicht kennt."

**Workflow:**
1. Upload: Beliebiges JSON/CSV
2. KI: Analysiert Struktur, zeigt Felder
3. Transform: Universal Transformer nutzt KI-Mapping
4. **Geplant:** Optionales Transformationsskript zur Feinsteuerung
5. Import ausführen und mit Szenario-Konfiguration fortfahren

---

## Wizard-Schritte im Detail

### Step 1: Upload

**UI-Elemente:**
- Drag & Drop Zone
- Multi-File Upload inkl. Ordnerstruktur
- Unterstützte Formate: `.json`, `.jsonl`/`.ndjson`, `.csv`, `.tsv`
- **XLSX:** UI akzeptiert Upload, Backend-Unterstuetzung ist **geplant**

**Features:**
- Format-Autodetection
- Fortschrittsanzeige bei mehreren Dateien
- Fehlermeldungen pro Datei

### Step 2: Describe (Intent + Vorschau)

**UI-Elemente:**
- Daten-Preview (mehrere Samples)
- Struktur-Zusammenfassung (Felder, Eintraege, Format)
- Intent-Eingabe mit Beispiel-Prompts
- Chat-Interface fuer Nachfragen

**KI-Funktionen:**
- Analyse von Struktur + Nutzer-Intent (`/ai/analyze-intent`)
- Streaming-Chat fuer Feinjustierung (`/ai/chat-stream`)
- Live-Konfiguration (Task Type, Field Mapping, Labels/Buckets)

### Step 3: Review & Configure

**UI-Elemente:**
- Szenario-Name
- Evaluationstyp (mail_rating, rating, ranking, comparison, authenticity, labeling)
- Zeitraum (Start/Ende)
- KI-Analyse-Zusammenfassung (Mapping, Rollen, Kriterien, Konfidenz)
- Daten-Uebersicht (Dateien, Eintraege, Format)

**Hinweis:**
- Erweiterte Szenario-Optionen (z. B. Verteilung/Order) erfolgen im Scenario Manager.

### Step 4: Users

**UI-Elemente:**
- Auswahl von Evaluators und Viewers
- Quick-Actions (z. B. alle Researcher als Evaluator)
- Verteilungs-Vorschau bei Round-Robin

### Step 5: Execute Import

**UI-Elemente:**
- Zusammenfassung (Dateien, Eintraege, Task Type, User)
- Start-Button mit Fortschrittsanzeige
- Erfolgsmeldung nach Abschluss

**Nach dem Import:**
- Weiterarbeit im Scenario Manager (z. B. Fein-Konfiguration, LLM Evaluators)

## Datenformate

### LLARS Native Format (Ziel-Schema)

```json
{
  "$schema": "llars-import-v1",
  "metadata": {
    "name": "Mein Datensatz",
    "description": "Beschreibung",
    "task_type": "rating",
    "source": "custom"
  },
  "items": [
    {
      "id": "unique-123",
      "subject": "Beratung zu Thema X",
      "conversation": [
        {
          "role": "user",
          "content": "Hallo, ich brauche Hilfe...",
          "timestamp": "2026-01-05T10:00:00Z"
        },
        {
          "role": "assistant",
          "content": "Gerne helfe ich Ihnen...",
          "timestamp": "2026-01-05T10:05:00Z"
        }
      ],
      "features": [
        {
          "type": "summary",
          "content": "Der Klient fragt nach...",
          "generated_by": "gpt-4"
        }
      ],
      "metadata": {
        "source_file": "data.json",
        "is_fake": false
      }
    }
  ]
}
```

### Unterstützte Eingabeformate

| Format | Beschreibung | Auto-Detection |
|--------|--------------|----------------|
| **LLARS Native** | `llars-import-v1` Schema | Ja |
| **OpenAI/ChatML** | `messages: [{role, content}]` | Ja |
| **LMSYS Pairwise** | `{prompt, response_a, response_b}` | Ja |
| **JSONL/NDJSON** | Eine Konversation pro Zeile | Ja |
| **CSV/TSV** | Spaltenbasierte Tabellen | Ja |
| **Generic JSON** | Beliebige JSON-Listen | Ja (Fallback) |
| **Custom** | Beliebige Struktur | KI-Analyse + Mapping |

Hinweis: **XLSX** ist geplant (UI akzeptiert Upload, Backend-Unterstuetzung ausstehend).

---

## Implementierte Komponenten

### Backend
- `app/services/data_import/import_service.py` - Orchestrierung (Session, Transform, Execute)
- `app/services/data_import/format_detector.py` - Format-Erkennung + Adapter-Auswahl
- `app/services/data_import/universal_transformer.py` - KI-gestuetzte Transformation
- `app/services/data_import/ai_analyzer.py` - Intent-/Struktur-Analyse
- `app/services/data_import/schema_validator.py` / `schema_detector.py` - Validierung
- `app/services/data_import/adapters/` - Adapter (llars, openai, lmsys, jsonl, csv, generic)
- `app/routes/data_import/import_routes.py` - REST API (`/api/import/...`)

### Frontend
- `llars-frontend/src/views/DataImporter/DataImporterView.vue` - Route `/data-import`
- `llars-frontend/src/components/DataImporter/DataImporterWizard.vue` - Wizard
- `llars-frontend/src/components/DataImporter/steps/` - StepUpload, StepDescribe, StepReviewNew, StepUsers
- `llars-frontend/src/services/importService.js` - API-Client

### Integration
- `llars-frontend/src/views/ScenarioManager/components/tabs/ScenarioDataTab.vue` nutzt `/api/import/from-data`

---

## API-Endpoints (aktuell)

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| GET | `/api/import/formats` | Verfuegbare Formate + Task Types |
| POST | `/api/import/upload` | Datei hochladen (multipart) |
| GET | `/api/import/session/{id}` | Session-Status abrufen |
| GET | `/api/import/session/{id}/sample` | Sample fuer Preview |
| POST | `/api/import/transform` | Transformation ausfuehren |
| POST | `/api/import/validate` | Validierung ausfuehren |
| POST | `/api/import/execute` | Import in DB ausfuehren |
| DELETE | `/api/import/session/{id}` | Session loeschen |
| POST | `/api/import/from-data` | Direktimport (Wizard/Scenario Manager) |
| POST | `/api/import/ai/analyze` | KI-Strukturanalyse |
| POST | `/api/import/ai/analyze-intent` | KI-Intent + Mapping |
| POST | `/api/import/ai/transform` | KI-Transformation anwenden |
| POST | `/api/import/ai/transform-script` | Transformationsskript generieren |
| POST | `/api/import/ai/suggest` | Mapping-Verbesserungen vorschlagen |
| POST | `/api/import/ai/chat-stream` | SSE-Chat fuer Konfig-Feinschliff |

---

## Geplante Erweiterungen

- XLSX-Parsing im Backend
- URL-/HuggingFace-Import
- UI fuer Transformationsskripte (Backend-Endpoint vorhanden)
- Wiederverwendbare Mapping-Profile
