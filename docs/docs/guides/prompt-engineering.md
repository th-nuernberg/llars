# Prompt Engineering

**Version:** 1.0 | **Stand:** Januar 2026

Prompt Engineering ist ein kollaborativer Workspace zum Entwerfen, Organisieren, Testen und Versionieren von Prompts. Es kombiniert einen visuellen Block-Editor mit Git-ähnlicher Versionskontrolle, Variablen-Management und LLM-Testfunktionen.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Prompt Engineering                                     [+ Neuer Prompt]    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Meine Prompts                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ API Assistent   │  │ Support Bot     │  │ Code Review     │             │
│  │ Aktualisiert:   │  │ Aktualisiert:   │  │ Aktualisiert:   │             │
│  │ Heute           │  │ Gestern         │  │ vor 3 Tagen     │             │
│  │ 👤 👤 +2        │  │                 │  │ 👤              │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  Mit mir geteilt                                                            │
│  ┌─────────────────┐                                                        │
│  │ Team Prompt     │                                                        │
│  │ Von: researcher │                                                        │
│  └─────────────────┘                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Schnellstart

!!! tip "In 5 Schritten zum ersten Prompt"
    1. **Neuer Prompt** → Namen eingeben → Erstellen
    2. **Block hinzufügen** → z.B. "System Instruction"
    3. **Text eingeben** → Rich-Text-Editor mit Formatierung
    4. **Variablen nutzen** → `{{variable}}` per Drag & Drop einfügen
    5. **Testen** → Prompt mit LLM ausführen

---

## Editor-Workspace

Nach Klick auf einen Prompt öffnet sich der Editor:

```
┌────────────────────┬───────────────────────────────────────────────────────┐
│  Sidebar           │  Editor                                               │
│  ───────────────   │  ──────────────────────────────────────────────────   │
│                    │                                                       │
│  🟢 Online: 2      │  ┌─────────────────────────────────────────────────┐ │
│                    │  │ ≡ System Instruction                [✎] [🗑]   │ │
│  Aktionen:         │  ├─────────────────────────────────────────────────┤ │
│  [+ Block]         │  │ Du bist ein hilfreicher Assistent.              │ │
│  [📝 Variablen]    │  │ Antworte immer in {{language}}.                 │ │
│  [👁 Vorschau]     │  └─────────────────────────────────────────────────┘ │
│  [🧪 Testen]       │                                                       │
│                    │  ┌─────────────────────────────────────────────────┐ │
│  Variablen:        │  │ ≡ User Context                      [✎] [🗑]   │ │
│  ┌──────────────┐  │  ├─────────────────────────────────────────────────┤ │
│  │ {{language}} │  │  │ Der Benutzer fragt: {{user_query}}              │ │
│  │ {{user_query}}│  │  │                                                 │ │
│  └──────────────┘  │  └─────────────────────────────────────────────────┘ │
│                    │                                                       │
│  Import/Export:    │                                                       │
│  [⬇ Download]      │                                                       │
│  [📋 Kopieren]     │                                                       │
│                    │                                                       │
│  Git:              │                                                       │
│  [+12/-3 Synced]   │                                                       │
│                    │                                                       │
└────────────────────┴───────────────────────────────────────────────────────┘
```

---

## Funktionen

### Block-basiertes Editing

Prompts bestehen aus mehreren Blöcken, die einzeln bearbeitet werden können:

| Aktion | Beschreibung |
|--------|--------------|
| **Block hinzufügen** | Klick auf "+ Block" → Namen eingeben |
| **Block umbenennen** | Doppelklick auf Titel oder Stift-Icon |
| **Block löschen** | Papierkorb-Icon → Bestätigung |
| **Block verschieben** | Drag-Handle (≡) ziehen |
| **Text bearbeiten** | Rich-Text-Editor mit Formatierung |

!!! info "Block-Struktur"
    Typische Blöcke: `System Instruction`, `Context`, `Examples`, `User Query`, `Output Format`

---

### Variablen-System

Variablen ermöglichen dynamische Prompts:

```
Syntax: {{variable_name}}
Erlaubt: Buchstaben, Zahlen, Unterstriche
Beispiel: {{language}}, {{user_query}}, {{context_data}}
```

#### Variablen verwalten

```
┌─────────────────────────────────────────┐
│  Variablen Manager                      │
├─────────────────────────────────────────┤
│  Neue Variable:                         │
│  Name: [user_name________]              │
│  Wert: [John Doe__________]             │
│  [+ Hinzufügen]                         │
├─────────────────────────────────────────┤
│  Vorhandene Variablen:                  │
│  ┌────────────────────────────────────┐ │
│  │ {{language}}  → "Deutsch"    [🗑]  │ │
│  │ {{context}}   → "Support..."  [🗑] │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

| Funktion | Beschreibung |
|----------|--------------|
| **Palette** | Drag & Drop aus Sidebar in Editor |
| **Manager** | CRUD für Variablen-Namen und -Werte |
| **Extraktion** | Automatische Erkennung aus Prompt-Text |
| **Synchronisation** | Echtzeit-Sync zwischen Nutzern |

---

### Echtzeit-Kollaboration

Mehrere Nutzer können gleichzeitig am selben Prompt arbeiten:

```
┌─────────────────────────────────────────┐
│  🟢 Online (3)                          │
│  ├── admin (Owner)         🔴           │
│  ├── researcher            🟢           │
│  └── evaluator             🔵           │
└─────────────────────────────────────────┘
```

| Feature | Beschreibung |
|---------|--------------|
| **Live-Cursor** | Farbcodierte Cursor pro Nutzer |
| **Text-Highlighting** | Änderungen anderer Nutzer markiert |
| **Auto-Sync** | Änderungen sofort synchronisiert |
| **Konfliktfrei** | CRDT-Technologie (YJS) verhindert Konflikte |

!!! tip "Technologie"
    Die Kollaboration nutzt YJS + Socket.IO für Echtzeit-Synchronisation ohne Konflikte.

---

### Prompt testen

Der Test-Dialog ermöglicht das Ausführen von Prompts mit verschiedenen LLMs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Prompt Testen                                                              │
├────────────────────────────┬────────────────────────────────────────────────┤
│  Variablen                 │  Konfiguration                                 │
│  ─────────────────         │  ──────────────────────────────────────────    │
│                            │                                                │
│  {{language}}              │  Modell: [GPT-4o          ▼]                  │
│  [Deutsch_______]  ✓       │  Temperatur: [0.7_______]                      │
│                            │  Max Tokens: [2000______]                      │
│  {{user_query}}            │                                                │
│  [Wie funktio...]  ✓       │  [ ] JSON-Modus                                │
│                            │                                                │
│  {{context}}               │  [▶ Ausführen]                                 │
│  [_______________]  ⚠      │                                                │
│                            ├────────────────────────────────────────────────┤
│                            │  Antwort                                       │
│                            │  ──────────────────────────────────────────    │
│                            │  Die Funktion arbeitet wie folgt...            │
│                            │  █                                             │
│                            │                                                │
└────────────────────────────┴────────────────────────────────────────────────┘
```

| Option | Beschreibung |
|--------|--------------|
| **Modell** | GPT-4o, Claude 3.5, Mistral, etc. |
| **Temperatur** | 0.0 (deterministisch) bis 1.0 (kreativ) |
| **Max Tokens** | Maximale Antwortlänge |
| **JSON-Modus** | Strukturierte JSON-Antwort erzwingen |
| **Streaming** | Echtzeit-Anzeige der Generierung |

---

### Git-Versionskontrolle

Änderungen können wie in Git versioniert werden:

```
┌─────────────────────────────────────────┐
│  Git Panel                    [▼]       │
├─────────────────────────────────────────┤
│  Status: +12 / -3 Zeilen geändert       │
│                                         │
│  Beiträge:                              │
│  admin:      +8 / -2                    │
│  researcher: +4 / -1                    │
│                                         │
│  Commit-Nachricht:                      │
│  [Variable hinzugefügt______]           │
│  [Commit erstellen]                     │
├─────────────────────────────────────────┤
│  Historie:                              │
│  ├── "Variable hinzugefügt" (admin)     │
│  │   vor 2 Stunden                      │
│  ├── "System Prompt verbessert"         │
│  │   vor 1 Tag                          │
│  └── "Initial version"                  │
│      vor 3 Tagen                        │
└─────────────────────────────────────────┘
```

| Funktion | Beschreibung |
|----------|--------------|
| **Commit** | Snapshot des aktuellen Zustands |
| **Diff-Tracking** | Insertions/Deletions pro Block |
| **Beitrags-Tracking** | Änderungen pro Nutzer |
| **Historie** | Bis zu 200 Commits gespeichert |
| **Snapshot-Ansicht** | Vollständiger Inhalt jedes Commits |

---

### Teilen & Berechtigungen

Prompts können mit anderen Nutzern geteilt werden:

| Rolle | Rechte |
|-------|--------|
| **Owner** | Volle Rechte + Teilen verwalten |
| **Shared User** | Lesen + Bearbeiten, kein Teilen |

```
┌─────────────────────────────────────────┐
│  Geteilt mit:                           │
│  ┌────────────────────────────────────┐ │
│  │ 👤 researcher            [Entf.]  │ │
│  │ 👤 evaluator             [Entf.]  │ │
│  └────────────────────────────────────┘ │
│                                         │
│  Nutzer hinzufügen:                     │
│  [Suchen...___________] [+ Teilen]      │
└─────────────────────────────────────────┘
```

---

### Import/Export

| Format | Beschreibung |
|--------|--------------|
| **JSON Download** | Block-Namen als Keys, Inhalt als Values |
| **Clipboard** | Gleiches Format in Zwischenablage |
| **JSON Upload** | Import mit Wahl: Anhängen oder Ersetzen |

**Export-Format:**
```json
{
  "System Instruction": "Du bist ein hilfreicher Assistent...",
  "User Context": "Der Benutzer fragt: {{user_query}}"
}
```

---

## Workflow-Beispiel

### Prompt erstellen und testen

1. **Erstellen**: `/promptengineering` → "Neuer Prompt" → "API Assistent"
2. **Struktur**: Blöcke hinzufügen:
   - `System Instruction` → Rolle und Verhalten
   - `Context` → Kontextinformationen
   - `Output Format` → Gewünschtes Ausgabeformat
3. **Variablen**: `{{api_endpoint}}`, `{{user_request}}` einfügen
4. **Testen**: Test-Dialog → Variablen füllen → Ausführen
5. **Versionieren**: Git Panel → "Initial version" committen
6. **Teilen**: Team-Mitglieder hinzufügen

---

## Vorschau-Modus

Der Vorschau-Dialog zeigt den zusammengesetzten Prompt:

| Modus | Beschreibung |
|-------|--------------|
| **Placeholder** | `{{variablen}}` als Tags hervorgehoben |
| **Resolved** | Variablen durch Werte ersetzt |

!!! warning "Unaufgelöste Variablen"
    Variablen ohne Wert werden im Resolved-Modus orange hervorgehoben.

---

## API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/prompts` | GET | Eigene Prompts abrufen |
| `/api/prompts` | POST | Neuen Prompt erstellen |
| `/api/prompts/:id` | GET | Prompt-Details |
| `/api/prompts/:id` | PUT | Prompt aktualisieren |
| `/api/prompts/:id` | DELETE | Prompt löschen |
| `/api/prompts/:id/rename` | PUT | Prompt umbenennen |
| `/api/prompts/:id/share` | POST | Mit Nutzer teilen |
| `/api/prompts/:id/unshare` | POST | Teilen aufheben |
| `/api/prompts/:id/commit` | POST | Commit erstellen |
| `/api/prompts/:id/commits` | GET | Commit-Historie |
| `/api/prompts/shared` | GET | Geteilte Prompts |
| `/api/prompts/templates` | GET | Prompts für Batch Generation |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `feature:prompts:view` | Prompts ansehen |
| `feature:prompts:manage` | Prompts erstellen/bearbeiten |

---

## Siehe auch

- [Batch Generation](batch-generation.md) - Massenhafte Prompt-Ausführung
- [Berechtigungssystem](permission-system.md) - Zugriffsrechte
- [Chatbot Wizard](chatbot-wizard.md) - Chatbots mit Prompts erstellen
