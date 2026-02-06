# LaTeX Collaboration

**Version:** 1.0 | **Stand:** Januar 2026

LaTeX Collaboration ist ein Echtzeit-Kollaborationstool für wissenschaftliche Dokumente. Mehrere Nutzer können gleichzeitig an LaTeX-Projekten arbeiten, kommentieren, versionieren und PDFs kompilieren.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  LaTeX Collaboration                                              [⚙️]     │
├──────────────────┬──────────────────────────────────────────────────────────┤
│  Dateibaum       │  Editor                                     PDF-Viewer  │
│  ─────────────   │  ───────────────────────────────────────    ─────────── │
│                  │                                                         │
│  📁 Projekt      │  \documentclass{article}                    ┌─────────┐ │
│  ├── 📄 main.tex │  \begin{document}                           │         │ │
│  ├── 📄 intro.tex│  \section{Einleitung}                       │  PDF    │ │
│  ├── 📁 chapters │  Lorem ipsum dolor sit amet...              │         │ │
│  │   └── 📄 ch1  │                      ┌─────────────┐        │         │ │
│  └── 📁 images   │                      │ Kommentar   │        │         │ │
│                  │                      │ "Fix typo"  │        │         │ │
│  ─────────────   │                      │ [🤖 AI Fix] │        └─────────┘ │
│  Git Panel       │                      └─────────────┘                    │
│  +12 / -3        │                                                         │
│  [Commit]        │                                                         │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

---

## Schnellstart

!!! tip "In 4 Schritten zum Dokument"
    1. **Workspace erstellen** → Name eingeben, Template wählen
    2. **Dokumente hinzufügen** → Dateien und Ordner anlegen
    3. **Bearbeiten** → LaTeX schreiben, Kommentare hinzufügen
    4. **Kompilieren** → PDF generieren und herunterladen

---

## Workspace

### Neuen Workspace erstellen

1. **LaTeX Collab** in Navigation öffnen
2. **Neuer Workspace** klicken
3. Name eingeben (z.B. "IJCAI Paper 2026")
4. Template wählen (Artikel, Bericht, etc.)

### Workspace-Einstellungen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Workspace-Einstellungen                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Name:        [IJCAI Paper 2026_______________]                            │
│                                                                             │
│  Sichtbarkeit:                                                              │
│  ◉ Privat     (Nur ich und eingeladene Mitglieder)                         │
│  ○ Team       (Alle Team-Mitglieder)                                        │
│  ○ Organisation                                                             │
│                                                                             │
│  Haupt-Dokument:                                                            │
│  [main.tex                           ▼]                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Einstellung | Beschreibung |
|-------------|--------------|
| **Name** | Anzeigename des Workspaces |
| **Sichtbarkeit** | Zugriffsebene (privat, team, org) |
| **Haupt-Dokument** | Einstiegspunkt für PDF-Kompilierung |

---

## Dateibaum & Panels

Der linke Bereich kombiniert **Dateibaum**, **Git-Status** und **Gliederung**:

```
┌─────────────────────────────┐
│  Dateien                    │
├─────────────────────────────┤
│                             │
│  📁 IJCAI Paper 2026        │
│  ├── 📄 main.tex     [⭐]   │
│  ├── 📄 abstract.tex        │
│  ├── 📄 introduction.tex    │
│  ├── 📁 sections            │
│  │   ├── 📄 related.tex     │
│  │   ├── 📄 method.tex      │
│  │   └── 📄 results.tex     │
│  ├── 📁 figures             │
│  │   ├── 🖼️ diagram.png     │
│  │   └── 🖼️ results.pdf     │
│  └── 📄 references.bib      │
│                             │
│  [+ Datei]  [+ Ordner]      │
│                             │
└─────────────────────────────┘
```

### Dateien verwalten

| Aktion | Beschreibung |
|--------|--------------|
| **Neue Datei** | `.tex` Datei erstellen |
| **Neuer Ordner** | Unterordner anlegen |
| **Umbenennen** | Doppelklick oder Rechtsklick |
| **Verschieben** | Drag & Drop in Ordner |
| **Löschen** | Rechtsklick → Löschen |
| **Als Haupt-Dokument** | Stern-Icon für Kompilierung |

### Assets hochladen

Bilder und PDFs können hochgeladen werden:

- **Drag & Drop** in den Dateibaum
- **Rechtsklick** → Asset hochladen
- Unterstützte Formate: PNG, JPG, PDF, EPS

### Gliederung (Outline)

Die Gliederung zeigt die Struktur des aktuellen Dokuments (Parts/Chapter/Section).
Ein Klick springt direkt zur entsprechenden Stelle im Editor.

---

## Editor

Der Monaco-Editor bietet professionelle LaTeX-Bearbeitung:

### Funktionen

| Feature | Beschreibung |
|---------|--------------|
| **Syntax-Highlighting** | LaTeX-Befehle farbig hervorgehoben |
| **Autovervollständigung** | `\begin{` → Vorschläge für Umgebungen |
| **Klammer-Matching** | Passende Klammern markiert |
| **Zeilennummern** | Für Fehler-Navigation |
| **Mehrere Cursor** | Ctrl+Klick für paralleles Bearbeiten |
| **Review‑Modus** | Kommentare fokussiert anzeigen |
| **Ghost Text (optional)** | KI‑Vorschläge als dezente Einblendung |

### Echtzeit-Kollaboration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  main.tex                                             🟢 admin  🔵 researcher│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1  │ \documentclass{article}                                              │
│  2  │ \usepackage[utf8]{inputenc}                                          │
│  3  │                                                                      │
│  4  │ \begin{document}                                                     │
│  5  │                                                                      │
│  6  │ \section{Introduction}                    ← 🟢 admin bearbeitet hier │
│  7  │ Lorem ipsum dolor sit amet...                                        │
│  8  │                                                                      │
│  9  │ \section{Methods}                         ← 🔵 researcher hier       │
│ 10  │ We propose a novel approach...                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **Live-Cursor** anderer Nutzer sichtbar
- **Farbcodierung** pro Nutzer
- **Konfliktfreie** Bearbeitung durch YJS

---

## Kommentare

### Kommentar erstellen

1. **Text markieren** im Editor
2. **Kommentar-Icon** klicken oder `Ctrl+Shift+C`
3. **Kommentar schreiben** → Absenden

```
┌─────────────────────────────────────────┐
│  Neuer Kommentar                        │
├─────────────────────────────────────────┤
│                                         │
│  Markierter Text:                       │
│  "Lorem ipsum dolor sit amet"           │
│                                         │
│  Kommentar:                             │
│  [Hier sollte eine Quelle ergänzt___]   │
│  [werden für die Behauptung.________]   │
│                                         │
│                    [Abbrechen] [Senden] │
│                                         │
└─────────────────────────────────────────┘
```

### Kommentar-Thread

Kommentare können Antworten haben:

```
┌─────────────────────────────────────────┐
│  💬 admin · vor 2 Stunden               │
│  ───────────────────────────────────    │
│  "Lorem ipsum dolor sit amet"           │
│                                         │
│  Hier sollte eine Quelle ergänzt        │
│  werden für die Behauptung.             │
│                                         │
│  └─ 💬 researcher · vor 1 Stunde        │
│     Welche Quelle meinst du?            │
│                                         │
│  └─ 💬 admin · vor 30 Min               │
│     Smith et al. 2024                   │
│                                         │
│  [Antworten]  [🤖 KI-Lösung]  [✓ Lösen] │
└─────────────────────────────────────────┘
```

### KI-gestützte Kommentar-Auflösung

Die KI kann Kommentare automatisch umsetzen:

1. **Kommentar öffnen**
2. **KI-Lösung** klicken
3. KI analysiert Kontext und Kommentar
4. **Vorgeschlagene Änderung** wird angezeigt
5. **Änderung übernehmen** oder ablehnen

```
┌─────────────────────────────────────────┐
│  🤖 LLARS KI                            │
│  ───────────────────────────────────    │
│                                         │
│  Änderung vorgeschlagen:                │
│                                         │
│  - Lorem ipsum dolor sit amet           │
│  + Lorem ipsum dolor sit amet           │
│    (Smith et al., 2024).                │
│                                         │
│  Erklärung:                             │
│  Ich habe die Quellenangabe ergänzt     │
│  wie im Kommentar gewünscht.            │
│                                         │
│           [Ablehnen]  [Übernehmen]      │
└─────────────────────────────────────────┘
```

!!! tip "KI-Kontext"
    Die KI berücksichtigt 1000 Zeichen vor und nach dem markierten Text
    für besseres Verständnis.

**Streaming:** Während der KI‑Bearbeitung werden Tokens live gestreamt und am Ende
als Vorschlag zur Übernahme angezeigt.

---

## Git-Versionierung

### Git-Panel

Das Git-Panel zeigt ungespeicherte Änderungen:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Git                                                         [↗ Expandieren]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Änderungen: +12 / -3 Zeilen                                               │
│                                                                             │
│  Geänderte Dateien:                                                         │
│  ☑ main.tex           (+5, -2)                                              │
│  ☑ introduction.tex   (+7, -1)                                              │
│  ☐ references.bib     (+0, -0)                                              │
│                                                                             │
│  Commit-Nachricht:                                                          │
│  [Einleitung überarbeitet______________]                                   │
│                                                                             │
│  [Commit erstellen]                                                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Letzte Commits:                                                            │
│  ├── "Abstract finalisiert" (admin) · vor 2 Std                            │
│  ├── "Methodik ergänzt" (researcher) · vor 1 Tag                           │
│  └── "Initiale Version" (admin) · vor 3 Tagen                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Diff-Ansicht

Klick auf geänderte Datei zeigt Unterschiede:

```
┌────────────────────────────┬────────────────────────────┐
│  Vorher                    │  Nachher                   │
├────────────────────────────┼────────────────────────────┤
│  \section{Introduction}    │  \section{Introduction}    │
│                            │                            │
│  Lorem ipsum dolor sit     │  Lorem ipsum dolor sit     │
│  amet.                     │  amet, consectetur         │
│                            │  adipiscing elit.          │
│                            │                            │
│  We propose a method.      │  We propose a novel        │
│                            │  approach based on deep    │
│                            │  learning.                 │
└────────────────────────────┴────────────────────────────┘
```

### Commit wiederherstellen

1. **Commit-Historie** öffnen
2. **Commit auswählen**
3. **Wiederherstellen** klicken
4. Dokument wird auf Stand des Commits zurückgesetzt

!!! warning "Vorsicht"
    Wiederherstellen überschreibt den aktuellen Inhalt. Erstellen Sie vorher
    einen Commit um Änderungen zu sichern.

### Versions‑Kompilierung

Die PDF‑Vorschau kann für **aktuelle Dateien** oder **einen Commit** erstellt werden.
Auswahl im Compile‑Toolbar.

---

## PDF-Kompilierung

### Kompilieren

1. **Kompilieren-Button** klicken (oder `Ctrl+S`)
2. **latexmk** wird ausgeführt
3. **PDF** wird im Viewer angezeigt

### Kompilierungs-Log

Bei Fehlern wird der Log angezeigt:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Kompilierungs-Log                                               [Schließen]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ⚠️ Warnungen (2)                                                           │
│  ├── Zeile 45: Underfull \hbox                                              │
│  └── Zeile 78: Package hyperref Warning                                     │
│                                                                             │
│  ❌ Fehler (1)                                                              │
│  └── Zeile 23: Undefined control sequence \unknowncommand                   │
│                                                                             │
│  [Zu Zeile 23 springen]                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Auto‑Kompilieren

Im Toolbar‑Menü können Sie Auto‑Compile aktivieren:

- **Auto‑Kompilieren** an/aus
- **Delay** (ms)
- **Sync aktivieren** (für SyncTeX)

### SyncTeX-Navigation

Bidirektionale Synchronisation zwischen Editor und PDF:

| Aktion | Ergebnis |
|--------|----------|
| **Editor → PDF** | Klick auf Zeile → PDF scrollt zur Position |
| **PDF → Editor** | Ctrl+Klick in PDF → Editor springt zur Zeile |

---

## Teilen & Mitglieder

### Mitglieder einladen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Workspace teilen                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Nutzer einladen:                                                           │
│  [researcher@example.com_________] [+ Einladen]                            │
│                                                                             │
│  Aktuelle Mitglieder:                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  👤 admin          Owner         ──                                  │  │
│  │  👤 researcher     Mitglied      [Entfernen]                         │  │
│  │  👤 evaluator      Mitglied      [Entfernen]                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Rollen

| Rolle | Rechte |
|-------|--------|
| **Owner** | Volle Kontrolle, kann Mitglieder verwalten |
| **Mitglied** | Bearbeiten, Kommentieren, Kompilieren |

---

## Zotero (optional)

Zotero‑Bibliotheken können eingebunden werden:

- BibTeX‑Dateien werden automatisch synchronisiert
- Zotero‑Dateien sind **schreibgeschützt**
- Verbindung über OAuth oder API‑Key

---

## Import/Export

### ZIP-Export

1. **Menü** → **Als ZIP exportieren**
2. Vollständiges Projekt wird heruntergeladen
3. Enthält alle Dateien, Bilder, und Assets

### ZIP-Import

1. **Menü** → **ZIP importieren**
2. ZIP-Datei auswählen
3. Struktur wird im Workspace erstellt

---

## API-Endpunkte

### Workspace

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces` | GET | Workspaces auflisten |
| `/api/latex-collab/workspaces` | POST | Workspace erstellen |
| `/api/latex-collab/workspaces/:id` | GET | Workspace-Details |
| `/api/latex-collab/workspaces/:id` | PATCH | Workspace aktualisieren |
| `/api/latex-collab/workspaces/:id` | DELETE | Workspace löschen |
| `/api/latex-collab/workspaces/:id/leave` | POST | Workspace verlassen |
| `/api/latex-collab/workspaces/:id/members` | GET/POST | Mitglieder verwalten |
| `/api/latex-collab/workspaces/:id/members/:username` | DELETE | Mitglied entfernen |

### Dokumente

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/tree` | GET | Dateibaum abrufen |
| `/api/latex-collab/documents/content` | POST | Dokumentinhalt laden |
| `/api/latex-collab/documents` | POST | Datei/Ordner erstellen |
| `/api/latex-collab/workspaces/:id/main` | PATCH | Haupt‑Dokument setzen |
| `/api/latex-collab/documents/:id` | PATCH | Umbenennen, verschieben |
| `/api/latex-collab/documents/:id` | DELETE | Löschen |

### Kommentare

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/comments` | GET | Workspace‑Kommentare |
| `/api/latex-collab/documents/:id/comments` | GET/POST | Kommentare |
| `/api/latex-collab/comments/:id` | PATCH/DELETE | Kommentar ändern/löschen |
| `/api/latex-collab/comments/:id/replies` | POST | Antworten |
| `/api/latex-collab/comments/:id/ai-resolve/status` | GET | KI‑Status |
| `/api/latex-collab/comments/:id/ai-resolve` | POST | KI-Auflösung |

### Git / Commits

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/changes` | GET | Workspace‑Änderungen |
| `/api/latex-collab/workspaces/:id/commit` | POST | Workspace committen |
| `/api/latex-collab/documents/:id/commits` | GET | Commit‑Liste |
| `/api/latex-collab/documents/:id/commits/:commit_id` | GET | Commit‑Details |
| `/api/latex-collab/documents/:id/commit` | POST | Dokument committen |
| `/api/latex-collab/documents/:id/baseline` | GET | Baseline abrufen |
| `/api/latex-collab/documents/:id/diff` | GET | Diff abrufen |
| `/api/latex-collab/documents/:id/rollback` | POST | Rollback |
| `/api/latex-collab/documents/:id/restore` | POST | Restore |

### Kompilierung

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/compile` | POST | Kompilierung starten |
| `/api/latex-collab/compile/:id` | GET | Compile‑Status |
| `/api/latex-collab/workspaces/:id/pdf` | GET | PDF herunterladen |
| `/api/latex-collab/compile/:id/synctex/forward` | POST | SyncTeX vorwärts |
| `/api/latex-collab/compile/:id/synctex/inverse` | POST | SyncTeX rückwärts |

### Assets

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/assets` | POST | Asset hochladen |
| `/api/latex-collab/assets/:id` | GET | Asset herunterladen |

### ZIP

| Endpunkt | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/latex-collab/workspaces/:id/export` | GET | Workspace als ZIP |
| `/api/latex-collab/workspaces/import` | POST | ZIP → neuer Workspace |
| `/api/latex-collab/workspaces/:id/import` | POST | ZIP → bestehender Workspace |

---

## Socket.IO Events (Realtime)

| Event | Beschreibung |
|-------|--------------|
| `latex_collab:workspace_shared` | Workspace wurde geteilt |
| `latex_collab:commit_created` | Neuer Commit erstellt |
| `latex_collab:comment_changed` | Kommentar geändert |
| `latex_collab:workspace_comment_changed` | Workspace‑Kommentare geändert |
| `latex_collab:compile_status` | Compile‑Status Update |
| `latex_collab:ai_resolve:token` | KI‑Token stream |
| `latex_collab:ai_resolve:completed` | KI‑Vorschlag fertig |
| `latex_collab:ai_resolve:error` | KI‑Fehler |

---

## Berechtigungen

| Permission | Beschreibung |
|------------|--------------|
| `feature:latex_collab:view` | Workspaces ansehen |
| `feature:latex_collab:edit` | Bearbeiten, Kommentieren |
| `feature:latex_collab:share` | Mitglieder verwalten |

---

## Siehe auch

- [Prompt Engineering](prompt-engineering.md) - Prompts erstellen
- [Berechtigungssystem](permission-system.md) - Zugriffsrechte
