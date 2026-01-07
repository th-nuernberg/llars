# LLARS Data Importer - Konzept

!!! warning "Status: Konzept"
    Dieses Projekt befindet sich in der **Konzeptphase**.
    Das Design wird noch erarbeitet.

**Erstellt:** 2026-01-05
**Autor:** Philipp Steigerwald
**Version:** 1.0

---

## Ziel

> Ein universeller, KI-gestützter Daten-Import-Wizard, der Benutzer durch den gesamten Prozess führt:
> **Daten hochladen → KI-gestützte Konvertierung → Szenario erstellen → Benutzer zuweisen → Evaluation starten**

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
| **Lernend** | System merkt sich erfolgreiche Mappings für ähnliche Datensätze |

### Wizard-Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                     LLARS DATA IMPORTER WIZARD                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [1. Upload]  →  [2. Analyse]  →  [3. Transform]  →  [4. Szenario]   │
│      ↓              ↓                 ↓                  ↓            │
│   Dateien       KI erkennt         KI hilft bei       Szenario-      │
│   hochladen     Format &           Konvertierung      Einstellungen   │
│                 Struktur           (optional)                         │
│                                                                       │
│                          →  [5. Benutzer]  →  [6. Deploy]            │
│                                  ↓                ↓                   │
│                           RATER/EVALUATOR    Evaluation               │
│                             zuweisen         aktivieren               │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Anwendungsszenarien

### Unterstützte Evaluationstypen

| Typ | function_type_id | Beschreibung | Datenstruktur |
|-----|------------------|--------------|---------------|
| **Rating** | 2 | Bewertung von Features (1-5 Sterne) | Konversation + Features |
| **Ranking** | 1 | Sortierung von Features (Drag & Drop) | Konversation + Features |
| **Mail Rating** | 3 | Bewertung ganzer Konversationen | Konversation |
| **Comparison** | 4 | Paarweiser Vergleich (Model A vs B) | 2 Responses zum gleichen Prompt |
| **Authenticity** | 5 | Fake/Real Unterscheidung | Konversation + is_fake Flag |
| **LLM-as-Judge** | 7 | Automatische + Human Evaluation | Konversation + Judge Config |

### Konkrete Use Cases

#### Use Case 1: Mensch vs. Maschine Ranking
> "Ich habe 500 Konversationen. Ich möchte dass Menschen und ein LLM diese ranken."

**Workflow:**
1. Upload: JSON/CSV mit Konversationen
2. KI: Erkennt Konversationsstruktur, schlägt Mapping vor
3. Transform: Optional - KI generiert Features aus Konversationen
4. Szenario: "Ranking" auswählen, LLM-Judge aktivieren
5. Benutzer: 5 RATER zuweisen
6. Deploy: Parallel Human + Machine Evaluation starten

#### Use Case 2: Fake/Real Detection
> "Ich habe synthetische und echte E-Mails. Menschen sollen erkennen was fake ist."

**Workflow:**
1. Upload: Zwei Ordner (fake/, real/) oder JSON mit `is_fake` Flag
2. KI: Erkennt Authenticity-Format
3. Transform: Keine Transformation nötig
4. Szenario: "Authenticity" auswählen
5. Benutzer: RATER zuweisen
6. Deploy: Evaluation starten

#### Use Case 3: LLM Output Qualität
> "Ich habe Outputs von GPT-4 und Claude. Menschen sollen bewerten welcher besser ist."

**Workflow:**
1. Upload: JSONL mit `{prompt, response_a, response_b, model_a, model_b}`
2. KI: Erkennt Pairwise-Comparison Format (LMSYS-Style)
3. Transform: Mapping zu LLARS Comparison Schema
4. Szenario: "Comparison" mit Modell-Labels
5. Benutzer: RATER zuweisen
6. Deploy: Side-by-Side Evaluation

#### Use Case 4: Beratungsqualität bewerten
> "Ich habe Beratungsgespräche. Experten sollen die Qualität bewerten."

**Workflow:**
1. Upload: JSON mit Konversationen (Client ↔ Berater)
2. KI: Erkennt Rollen, schlägt Feature-Generierung vor
3. Transform: LLM generiert Analyse-Features (Zusammenfassung, Qualität, etc.)
4. Szenario: "Rating" oder "Mail Rating"
5. Benutzer: Domain-Experten als RATER
6. Deploy: Experten-Evaluation

#### Use Case 5: Custom Dataset
> "Ich habe ein eigenes Format das LLARS nicht kennt."

**Workflow:**
1. Upload: Beliebiges JSON/CSV
2. KI: Analysiert Struktur, zeigt Felder
3. Transform: **KI schreibt Python-Transformationsskript**
4. User: Prüft Skript, passt ggf. an
5. Execute: Skript transformiert Daten
6. Weiter mit Szenario-Erstellung

---

## Wizard-Schritte im Detail

### Step 1: Upload

**UI-Elemente:**
- Drag & Drop Zone (wie in `DocumentUploadDialog.vue`)
- Unterstützte Formate: `.json`, `.jsonl`, `.csv`, `.xlsx`
- Multi-File Upload
- URL-Import (HuggingFace, GitLab, etc.)

**Features:**
- Format-Autodetection
- Dateigrößen-Limit (konfigurierbar)
- Fortschrittsanzeige bei großen Dateien

### Step 2: Analyse (AI-Powered)

**UI-Elemente:**
- Daten-Preview (erste 5-10 Einträge)
- Erkannte Felder mit Typ-Annotation
- Vorgeschlagenes Ziel-Schema
- "LLM analysieren" Button (optional)

**KI-Funktionen:**
```
┌─────────────────────────────────────────────────────┐
│  KI-Analyse Vorschlag                               │
├─────────────────────────────────────────────────────┤
│  Erkanntes Format: OpenAI Chat Completion           │
│                                                     │
│  Feld-Mapping:                                      │
│  ├── messages[] → Konversation                      │
│  │   ├── role: "user" → Klient                      │
│  │   └── role: "assistant" → Berater                │
│  └── id → Thread-ID                                 │
│                                                     │
│  Empfohlener Szenario-Typ: Mail Rating              │
│                                                     │
│  [Vorschlag übernehmen]  [Anpassen]  [Ablehnen]    │
└─────────────────────────────────────────────────────┘
```

### Step 3: Transform (AI-Assisted)

**Zwei Modi:**

#### Modus A: Automatisches Mapping
- KI mapped erkannte Felder auf LLARS-Schema
- User bestätigt oder passt an
- Keine Code-Generierung nötig

#### Modus B: Skript-Generierung
Wenn automatisches Mapping nicht möglich:

```
┌─────────────────────────────────────────────────────┐
│  KI-generiertes Transformationsskript               │
├─────────────────────────────────────────────────────┤
│  Das LLM hat folgendes Python-Skript erstellt:      │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ def transform(data):                          │  │
│  │     result = []                               │  │
│  │     for item in data['conversations']:        │  │
│  │         thread = {                            │  │
│  │             'id': item['conv_id'],            │  │
│  │             'messages': []                    │  │
│  │         }                                     │  │
│  │         for msg in item['turns']:             │  │
│  │             thread['messages'].append({       │  │
│  │                 'role': 'user' if msg['is_hu  │  │
│  │                 'content': msg['text']        │  │
│  │             })                                │  │
│  │         result.append(thread)                 │  │
│  │     return result                             │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [Skript ausführen]  [Bearbeiten]  [Neu generieren] │
└─────────────────────────────────────────────────────┘
```

**Sicherheit:**
- Skript läuft in Sandbox
- Nur lesender Zugriff auf Daten
- Timeout nach X Sekunden
- Code-Review vor Ausführung

### Step 4: Szenario konfigurieren

**UI-Elemente:**
- Szenario-Name
- Szenario-Typ Auswahl (Rating/Ranking/etc.)
- Zeitraum (Start/Ende)
- Distribution Mode (Alle sehen alles / Round-Robin)
- Order Mode (Original / Shuffle)

**AI-Suggestion:**
- KI schlägt passenden Typ basierend auf Datenstruktur vor
- Begründung wird angezeigt

### Step 5: Benutzer zuweisen

**UI-Elemente:**
- User-Liste mit Checkboxen
- Rollen-Auswahl pro User (RATER / EVALUATOR)
- Quick-Actions: "Alle Researcher als RATER"

**Features:**
- Vorschau: Wie viele Threads pro RATER
- Warnung bei ungleicher Verteilung

### Step 6: Review & Deploy

**UI-Elemente:**
- Zusammenfassung aller Einstellungen
- Test-Preview (ein Thread anschauen)
- "Evaluation starten" Button

**Nach Deploy:**
- Redirect zur Szenario-Übersicht
- Notification an zugewiesene User

---

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
| **OpenAI/ChatML** | `messages: [{role, content}]` | Ja |
| **LMSYS Pairwise** | `{prompt, response_a, response_b}` | Ja |
| **JSONL** | Eine Konversation pro Zeile | Ja |
| **CSV** | Spalten: id, user_msg, assistant_msg | Ja |
| **KIA Legacy** | Säulen-basiertes Format | Ja |
| **HuggingFace** | datasets Library Format | Via URL |
| **Custom** | Beliebige Struktur | KI-Analyse |

---

## Existierende Komponenten (Wiederverwendung)

### Frontend

| Komponente | Pfad | Nutzung |
|------------|------|---------|
| **ChatbotBuilderWizard** | `llars-frontend/src/components/Admin/ChatbotAdmin/ChatbotBuilderWizard.vue` | Wizard-Pattern, Step-Navigation |
| **CreateScenarioDialog** | `llars-frontend/src/components/parts/CreateScenarioDialog.vue` | Szenario-Formulare |
| **DocumentUploadDialog** | `llars-frontend/src/components/RAG/DocumentUploadDialog.vue` | Drag & Drop Upload |
| **AdminScenariosSection** | `llars-frontend/src/components/Admin/sections/AdminScenariosSection.vue` | Szenario-Verwaltung |

### Backend

| Service/Route | Pfad | Nutzung |
|---------------|------|---------|
| **LiteLLMClient** | `app/llm/litellm_client.py` | LLM-Calls für Analyse/Transform |
| **KIASyncService** | `app/services/judge/kia_sync_service.py` | Adapter-Pattern für Import |
| **scenario_crud** | `app/routes/scenarios/scenario_crud.py` | Szenario-Erstellung |
| **scenario_management** | `app/routes/scenarios/scenario_management.py` | User/Thread-Zuweisung |
| **authenticity_admin** | `app/routes/authenticity/authenticity_admin.py` | Import-Logik |

### Datenbank

| Model | Pfad | Nutzung |
|-------|------|---------|
| **EmailThread** | `app/db/models/scenario.py` | Thread-Speicherung |
| **Message** | `app/db/models/scenario.py` | Nachrichten |
| **RatingScenarios** | `app/db/models/scenario.py` | Szenario-Definition |
| **ScenarioUsers** | `app/db/models/scenario.py` | User-Zuweisung |

---

## Neue Komponenten

### Backend

```
app/
├── services/
│   └── import/
│       ├── __init__.py
│       ├── import_service.py          # Haupt-Orchestrierung
│       ├── format_detector.py         # Auto-Detection Logik
│       ├── schema_validator.py        # LLARS Schema Validierung
│       ├── ai_analyzer.py             # LLM-basierte Analyse
│       ├── ai_transformer.py          # LLM-generierte Skripte
│       └── adapters/
│           ├── __init__.py
│           ├── base_adapter.py        # Abstract Base Class
│           ├── llars_adapter.py       # Native Format
│           ├── openai_adapter.py      # ChatML/OpenAI
│           ├── lmsys_adapter.py       # Pairwise Comparison
│           ├── jsonl_adapter.py       # JSONL
│           ├── csv_adapter.py         # CSV/Excel
│           └── kia_adapter.py         # Legacy KIA
├── routes/
│   └── import/
│       ├── __init__.py
│       └── import_routes.py           # REST API Endpoints
```

### Frontend

```
llars-frontend/src/
├── components/
│   └── DataImporter/
│       ├── DataImporterWizard.vue     # Haupt-Wizard
│       ├── steps/
│       │   ├── StepUpload.vue         # Datei-Upload
│       │   ├── StepAnalyze.vue        # KI-Analyse
│       │   ├── StepTransform.vue      # Transformation
│       │   ├── StepScenario.vue       # Szenario-Config
│       │   ├── StepUsers.vue          # User-Zuweisung
│       │   └── StepReview.vue         # Review & Deploy
│       ├── components/
│       │   ├── FormatPreview.vue      # Daten-Vorschau
│       │   ├── FieldMapper.vue        # Feld-Mapping UI
│       │   ├── AIAnalysisCard.vue     # KI-Vorschlag Card
│       │   ├── ScriptEditor.vue       # Code-Editor für Skripte
│       │   └── TransformPreview.vue   # Vorher/Nachher Ansicht
│       └── composables/
│           ├── useImportWizard.js     # Wizard State Management
│           └── useAIAssistant.js      # KI-Interaktion
├── views/
│   └── DataImporter/
│       └── DataImporterView.vue       # Route Entry Point
```

---

## API-Endpoints

### Import API

| Method | Endpoint | Beschreibung |
|--------|----------|--------------|
| POST | `/api/import/upload` | Datei hochladen (multipart) |
| GET | `/api/import/session/{id}` | Session-Status abrufen |
| POST | `/api/import/analyze` | KI-Analyse starten |
| POST | `/api/import/transform` | Transformation ausführen |
| POST | `/api/import/validate` | Schema validieren |
| POST | `/api/import/execute` | Finalen Import durchführen |
| GET | `/api/import/templates` | Beispiel-Formate abrufen |

### Wizard Session

```json
// POST /api/import/upload Response
{
  "session_id": "abc123",
  "file_info": {
    "name": "data.json",
    "size": 1024000,
    "type": "application/json"
  },
  "detected_format": "openai_chat",
  "confidence": 0.95,
  "preview": {
    "total_items": 500,
    "sample": [...]
  }
}
```

---

## KI-Prompts

### Analyse-Prompt

```
Du bist ein Datenformat-Experte. Analysiere diese JSON-Struktur:

{SAMPLE_DATA}

Aufgaben:
1. Erkenne das Format (OpenAI, LMSYS, Custom, etc.)
2. Identifiziere Felder für: Konversation, Rollen, Timestamps, Metadata
3. Schlage ein Mapping auf das LLARS-Schema vor
4. Empfehle einen passenden Szenario-Typ

Antworte im JSON-Format:
{
  "detected_format": "...",
  "confidence": 0.0-1.0,
  "field_mapping": {...},
  "recommended_task_type": "...",
  "reasoning": "..."
}
```

### Transform-Prompt

```
Du bist ein Python-Experte. Schreibe ein Transformationsskript.

Eingabe-Format:
{INPUT_SCHEMA}

Ziel-Format (LLARS):
{LLARS_SCHEMA}

Anforderungen:
- Funktion: def transform(data: list) -> list
- Keine externen Dependencies
- Fehlerbehandlung für fehlende Felder
- Kommentare im Code

Skript:
```

---

## Arbeitscheckliste

### Phase 1: Foundation
- [ ] Backend Import-Service Grundstruktur
- [ ] Base Adapter Pattern implementieren
- [ ] OpenAI/ChatML Adapter (häufigstes Format)
- [ ] Format Auto-Detection Logik
- [ ] REST API Grundendpoints

### Phase 2: Frontend Wizard
- [ ] DataImporterWizard.vue Grundstruktur
- [ ] Step 1: Upload Component
- [ ] Step 2: Analyse Preview
- [ ] Step 3: Transform UI
- [ ] Step 4-6: Szenario/User/Review Integration

### Phase 3: KI-Integration
- [ ] AI Analyzer Service (Format-Erkennung)
- [ ] AI Transformer Service (Skript-Generierung)
- [ ] Frontend AI-Suggestion Components
- [ ] Skript-Sandbox für sichere Ausführung

### Phase 4: Weitere Adapter
- [ ] JSONL Adapter
- [ ] CSV Adapter
- [ ] LMSYS Pairwise Adapter
- [ ] HuggingFace URL Import
- [ ] KIA Legacy Adapter (Migration)

### Phase 5: Polish & Testing
- [ ] E2E Tests für Wizard Flow
- [ ] Error Handling & Edge Cases
- [ ] Performance bei großen Dateien
- [ ] Dokumentation

---

## Offene Fragen

- [ ] Maximale Dateigröße für Upload?
- [ ] Sandbox-Technologie für Skript-Ausführung (subprocess? Docker?)
- [ ] Sollen transformierte Daten zwischengespeichert werden?
- [ ] HuggingFace Authentication für private Datasets?
- [ ] Rate-Limiting für LLM-Calls im Wizard?

---

## Referenzen (Externe Plattformen)

| Plattform | Relevante Features | Link |
|-----------|-------------------|------|
| **Argilla** | ChatField, RatingQuestion, RankingQuestion | [Docs](https://docs.argilla.io/latest/how_to_guides/dataset/) |
| **Label Studio** | Template-basierte LLM Evaluation | [Blog](https://labelstud.io/blog/new-llm-evaluation-templates-for-label-studio/) |
| **LMSYS Arena** | Pairwise Comparison Format | [Dataset](https://huggingface.co/datasets/lmsys/chatbot_arena_conversations) |

---

## Abnahme

| Reviewer | Datum | Status |
|----------|-------|--------|
| Philipp Steigerwald | - | Ausstehend |
