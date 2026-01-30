# Batch Generation

**Version:** 1.0 | **Stand:** Januar 2026

Batch Generation ermöglicht die massenhafte Ausführung von Prompts mit verschiedenen LLM-Modellen. Es verbindet Prompt Engineering mit Evaluation, indem aus Kombinationen von Eingabedaten, Prompts und Modellen automatisch Outputs generiert werden.

---

## Übersicht

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                              BATCH GENERATION                                  │
│                                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                       │
│  │ Eingabedaten│    │   Prompts   │    │   Modelle   │                       │
│  │  (Items)    │  × │ (Templates) │  × │   (LLMs)    │                       │
│  │    10       │    │      2      │    │      3      │  =  60 Outputs        │
│  └─────────────┘    └─────────────┘    └─────────────┘                       │
│         ↓                  ↓                  ↓                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        Generation Job                                   │ │
│  │  ████████████████████████░░░░░░░░  75%  ·  45/60 fertig  ·  $2.35      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│         ↓                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Export: CSV, JSON  |  Zu Evaluation-Szenario konvertieren              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Schnellstart

!!! tip "In 5 Schritten zur Batch Generation"
    1. **Hub öffnen** → `/generation` oder Navigation
    2. **Neuer Job** → Wizard starten
    3. **Konfigurieren** → Quellen, Prompts, Modelle wählen
    4. **Starten** → Echtzeit-Fortschritt beobachten
    5. **Exportieren** → CSV/JSON oder Evaluation-Szenario erstellen

---

## Generation Hub

Der Hub zeigt alle Jobs des aktuellen Nutzers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Batch Generation                                          [+ Neuer Job]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Aktive Jobs                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  🔄 LLM Vergleich Studie                              [⏸] [✕]       │   │
│  │  ████████████████░░░░░░░░  68%  ·  34/50  ·  $1.23                  │   │
│  │  GPT-4, Claude 3.5  ·  Gestartet: vor 5 Min                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Abgeschlossene Jobs                                                        │
│  ┌──────────────────────┐  ┌──────────────────────┐                        │
│  │ ✓ Summary Test       │  │ ✓ Prompt Iteration   │                        │
│  │   100/100 · $4.50    │  │   25/25 · $0.85      │                        │
│  │   vor 2 Stunden      │  │   Gestern            │                        │
│  └──────────────────────┘  └──────────────────────┘                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Job-Status

| Status | Icon | Beschreibung |
|--------|------|--------------|
| **Erstellt** | ○ | Job konfiguriert, noch nicht gestartet |
| **In Warteschlange** | ◷ | Wartet auf Verarbeitung |
| **Läuft** | 🔄 | Aktive Generierung |
| **Pausiert** | ⏸ | Pausiert, fortsetzen möglich |
| **Abgeschlossen** | ✓ | Alle Outputs generiert |
| **Fehlgeschlagen** | ✕ | Job mit Fehler abgebrochen |
| **Abgebrochen** | ○ | Vom Nutzer abgebrochen |

---

## Job-Wizard

Der 5-Schritte-Wizard führt durch die Konfiguration:

### Schritt 1: Quellen auswählen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schritt 1: Eingabedaten                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Quelle wählen:                                                             │
│                                                                             │
│  ◉ Aus Szenario                                                             │
│    [LLM-as-Judge Studie          ▼]  ·  150 Items                          │
│                                                                             │
│  ○ Manuelle Eingabe                                                         │
│    JSON/CSV hochladen oder Text einfügen                                    │
│                                                                             │
│  ○ Nur Prompt (ohne Eingabedaten)                                           │
│    Prompt ist selbstständig, keine externen Daten nötig                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Quellentyp | Beschreibung | Anwendung |
|------------|--------------|-----------|
| **Szenario** | Items aus bestehendem Evaluation-Szenario | Bestehende Daten verarbeiten |
| **Manuell** | JSON, CSV oder Plaintext hochladen | Neue Daten testen |
| **Nur Prompt** | Keine Eingabedaten benötigt | Prompt-Templates testen |

---

### Schritt 2: Prompts auswählen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schritt 2: Prompt-Templates                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Verfügbare Prompts:                                                        │
│                                                                             │
│  ☑ Zusammenfassung Standard                                                 │
│    Variablen: {{content}}, {{language}}                                     │
│                                                                             │
│  ☑ Zusammenfassung Kurz                                                     │
│    Variablen: {{content}}                                                   │
│                                                                             │
│  ☐ Analyse Detailliert                                                      │
│    Variablen: {{content}}, {{criteria}}                                     │
│                                                                             │
│  Ausgewählt: 2 Prompts                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

!!! info "Prompt-Integration"
    Prompts werden aus dem [Prompt Engineering](prompt-engineering.md) Modul geladen.
    Variablen werden automatisch durch Eingabedaten ersetzt.

**Variable-Aliase:**
Der Generator erkennt verschiedene Feld-Namen automatisch:

| Alias | Beschreibung |
|-------|--------------|
| `{{content}}`, `{{input}}`, `{{text}}` | Hauptinhalt |
| `{{messages}}`, `{{email_content}}` | E-Mail-Verlauf |
| `{{subject}}`, `{{betreff}}` | Betreff |

---

### Schritt 3: Modelle auswählen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schritt 3: LLM-Modelle                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ☑ GPT-4o                    $5.00 / 1M input   $15.00 / 1M output         │
│  ☑ Claude 3.5 Sonnet         $3.00 / 1M input   $15.00 / 1M output         │
│  ☐ GPT-4 Turbo               $10.00 / 1M input  $30.00 / 1M output         │
│  ☐ Llama 3 70B               $0.70 / 1M input   $0.90 / 1M output          │
│                                                                             │
│  Ausgewählt: 2 Modelle                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Schritt 4: Konfiguration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schritt 4: Parameter                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Generierungsparameter:                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Temperatur:     [0.7_______]  (0.0 - 1.0)                           │  │
│  │  Max Tokens:     [1000______]                                        │  │
│  │  Top P:          [1.0_______]                                        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Limits:                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Max parallele Anfragen:  [5_________]                               │  │
│  │  Budget-Limit (USD):      [10.00_____]                               │  │
│  │  Max Wiederholungen:      [3_________]                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Parameter | Beschreibung | Standard |
|-----------|--------------|----------|
| **Temperatur** | Kreativität (0 = deterministisch, 1 = kreativ) | 0.7 |
| **Max Tokens** | Maximale Ausgabelänge | 1000 |
| **Top P** | Nucleus Sampling | 1.0 |
| **Budget-Limit** | Pausiert Job bei Überschreitung | - |
| **Max Wiederholungen** | Retries bei Fehlern | 3 |

---

### Schritt 5: Übersicht & Starten

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Schritt 5: Zusammenfassung                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Job-Name: [LLM Vergleich Studie_______________]                           │
│                                                                             │
│  Konfiguration:                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Eingabedaten:   150 Items aus "LLM-as-Judge Studie"                 │  │
│  │  Prompts:        2 Templates                                          │  │
│  │  Modelle:        GPT-4o, Claude 3.5 Sonnet                           │  │
│  │  ───────────────────────────────────────────────────────────         │  │
│  │  Gesamt:         600 Outputs (150 × 2 × 2)                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Kostenvoranschlag:                                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GPT-4o:              300 × ~1000 Tokens  ≈  $4.50                   │  │
│  │  Claude 3.5 Sonnet:   300 × ~1000 Tokens  ≈  $2.70                   │  │
│  │  ───────────────────────────────────────────────────────────         │  │
│  │  Geschätzt gesamt:    ~$7.20                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                              [Job erstellen und starten]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Job-Detailansicht

Nach dem Start zeigt die Detailansicht Echtzeit-Fortschritt:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LLM Vergleich Studie                                    [⏸] [✕] [↓ Export]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Fortschritt                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  ████████████████████████████░░░░░░░░░░░░░░  68%                     │  │
│  │  408 / 600 abgeschlossen  ·  2 fehlgeschlagen  ·  $4.89              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Aktuell in Verarbeitung:                                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  🔄 Item #127  ·  Zusammenfassung Standard  ·  GPT-4o                │  │
│  │     Tokens: 234... █                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Outputs                                                     [Filter ▼]    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  #408  ✓  Item #85  ·  Kurz  ·  Claude   ·  $0.012  ·  1.2s         │  │
│  │  #407  ✓  Item #85  ·  Kurz  ·  GPT-4o   ·  $0.018  ·  0.9s         │  │
│  │  #406  ✓  Item #84  ·  Standard  ·  Claude   ·  $0.015  ·  1.5s     │  │
│  │  ...                                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                        [< Zurück]  Seite 1/20  [Weiter >]  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Echtzeit-Updates (Socket.IO)

| Event | Beschreibung |
|-------|--------------|
| `job:started` | Job wurde gestartet |
| `job:progress` | Fortschritts-Update |
| `item:started` | Einzelnes Item wird verarbeitet |
| `item:token` | Streaming-Token empfangen |
| `item:completed` | Item erfolgreich generiert |
| `item:failed` | Item fehlgeschlagen |
| `job:completed` | Job abgeschlossen |
| `job:budget_exceeded` | Budget-Limit erreicht |

---

## Export & Weiterverarbeitung

### Export-Formate

| Format | Beschreibung | Verwendung |
|--------|--------------|------------|
| **CSV** | Tabellarisch mit Metadaten | Excel, Analyse-Tools |
| **JSON** | Strukturiert mit vollständiger Config | Programmatische Verarbeitung |

**CSV-Spalten:**
- `output_id`, `source_item_id`, `prompt_variant`, `model_name`
- `generated_content`, `input_tokens`, `output_tokens`, `cost_usd`
- `processing_time_ms`, `status`, `error_message`
- `created_at`, `completed_at`

---

### Zu Evaluation-Szenario konvertieren

Generierte Outputs können direkt als Evaluation-Szenario verwendet werden:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Evaluation-Szenario erstellen                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Szenario-Name:  [LLM Vergleich Evaluation________]                        │
│                                                                             │
│  Evaluationstyp:                                                            │
│  ○ Rating (Multi-dimensional)                                               │
│  ◉ Ranking (Items sortieren)                                                │
│  ○ Comparison (A vs B)                                                      │
│  ○ Labeling (Kategorien zuweisen)                                           │
│                                                                             │
│  Konfiguration:                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Items: 150 (gruppiert nach Quelle)                                  │  │
│  │  Varianten pro Item: 4 (2 Prompts × 2 Modelle)                       │  │
│  │  Evaluatoren: [Einladen nach Erstellung]                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                                              [Szenario erstellen]          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

!!! tip "Workflow-Integration"
    Nach der Szenario-Erstellung können Evaluatoren die generierten Outputs
    im [Szenario Manager](scenario-manager.md) bewerten.

---

## API-Endpunkte

### Job-Management

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/generation/jobs` | GET | Jobs des Nutzers abrufen |
| `/api/generation/jobs` | POST | Neuen Job erstellen |
| `/api/generation/jobs/:id` | GET | Job-Details |
| `/api/generation/jobs/:id` | DELETE | Job löschen |

### Job-Lifecycle

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/generation/jobs/:id/start` | POST | Job starten |
| `/api/generation/jobs/:id/pause` | POST | Job pausieren |
| `/api/generation/jobs/:id/cancel` | POST | Job abbrechen |

### Outputs & Export

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/generation/jobs/:id/outputs` | GET | Outputs (paginiert) |
| `/api/generation/outputs/:id` | GET | Einzelner Output |
| `/api/generation/jobs/:id/export/csv` | POST | CSV-Export |
| `/api/generation/jobs/:id/export/json` | POST | JSON-Export |
| `/api/generation/jobs/:id/to-scenario` | POST | Zu Szenario konvertieren |

### Statistiken

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/generation/jobs/:id/statistics` | GET | Job-Statistiken |
| `/api/generation/estimate` | POST | Kostenvoranschlag |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `feature:generation:view` | Jobs und Outputs ansehen |
| `feature:generation:create` | Jobs erstellen |
| `feature:generation:manage` | Jobs starten/pausieren/abbrechen |
| `feature:generation:export` | Outputs exportieren |
| `feature:generation:to_scenario` | Evaluation-Szenarien erstellen |

---

## Fehlerbehandlung

### Automatische Wiederholung

Bei Fehlern werden Outputs automatisch wiederholt:

| Versuch | Wartezeit |
|---------|-----------|
| 1 | 1 Sekunde |
| 2 | 5 Sekunden |
| 3 | 15 Sekunden |

Nach 3 fehlgeschlagenen Versuchen wird der Output als `FAILED` markiert.

### Budget-Überschreitung

Bei Erreichen des Budget-Limits:
1. Job wird automatisch pausiert
2. Nutzer erhält Benachrichtigung
3. Budget kann erhöht und Job fortgesetzt werden

---

## Häufige Fragen

??? question "Wie werden Kosten berechnet?"
    Kosten basieren auf den Token-Preisen der gewählten Modelle.
    Ein Kostenvoranschlag wird vor dem Start angezeigt.
    Tatsächliche Kosten können abweichen (meist niedriger).

??? question "Kann ich einen laufenden Job ändern?"
    Nein. Pausieren Sie den Job und erstellen Sie einen neuen mit geänderter Konfiguration.

??? question "Was passiert bei Verbindungsabbruch?"
    Der Job läuft im Backend weiter. Bei Wiederverbindung wird der aktuelle Status
    synchronisiert inkl. teilweise generierter Inhalte.

??? question "Wie viele Jobs kann ich parallel ausführen?"
    Ein Job pro Nutzer. Weitere Jobs werden in die Warteschlange gestellt.

---

## Siehe auch

- [Prompt Engineering](prompt-engineering.md) - Prompts erstellen und verwalten
- [Szenario Manager](scenario-manager.md) - Evaluations-Szenarien verwalten
- [Evaluation](evaluation.md) - Bewertungen durchführen
