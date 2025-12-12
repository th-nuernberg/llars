# Markdown Collab Workspace - Konzept

!!! warning "Status: Konzept" Dieses Projekt befindet sich in der Konzeptphase. Das Design wird erarbeitet und kann sich noch aendern.

**Erstellt:** 2025-12-12  
**Autor:** Codex (AI Assistant)  
**Version:** 1.0

---

## Ziel

Ein kollaborativer Markdown-Arbeitsplatz, der die bestehende LLARS-Infrastruktur (YJS, RBAC, Authentik, Theme-System, Skeleton-Loading, Home-Kachel-Startseite) nutzt. Benutzer koennen Markdown-Dateien gemeinsam in Echtzeit bearbeiten, live rendern und git-artig nachvollziehen, wer was geaendert hat. Drei Ansichten (Editor Only, Split View, Preview Only) orientieren sich an PyCharm und koennen jederzeit umgeschaltet werden.

---

## Anforderungen

### Funktionale Anforderungen

ID

Anforderung

Prioritaet

F01

Home-Kachel "Markdown Collab" fuehrt in eigene Workspace-Startseite mit kompakter Ordnerstruktur und zuletzt bearbeiteten Dateien.

Hoch

F02

Ordnerbaum in der Standardansicht; neue Markdown-Dateien und Unterordner anlegen, umbenennen, loeschen, duplizieren; Drag-and-Drop fuer Reihung.

Hoch

F03

Drei View-Modi: Editor, Split (Editor links, Preview rechts), Preview. Umschaltbar ohne Reload, Auswahl je User persistent.

Hoch

F04

Live-Preview mit identischem Markdown-Renderer wie Doku; automatisches Rendern ohne manuellen Save.

Hoch

F05

YJS-basierte Echtzeit-Kollaboration mit Presence (Avatare/Initialen, Cursor- und Selection-Farben), inklusive Anzeige, wer im Dokument ist und wo tippt.

Hoch

F06

Teilen von Dateien und Ordnern: Einladungen per Nutzer- und Rollen-Auswahl; Link-Sharing optional mit RBAC-Check; Rechte: view, edit, share.

Hoch

F07

Git-artige Aenderungsverfolgung: Farbliche Highlights pro User fuer uncommitted Aenderungen; Farben frei waehlbar, Konflikt-Autoresolution bei Doppelbelegung.

Hoch

F08

Commit-Flow im UI: Aenderungsliste, Commit-Message, Reset der Highlights nach Commit; History mit Diff-Preview pro Commit.

Hoch

F09

Auto-Save: Alle Aenderungen werden sofort ueber WebSockets zum Server gespiegelt; kein manueller Save-Button.

Hoch

F10

Benutzerdefinierte Shortcuts (z. B. Umschalten der View-Modi) im lokalen Profil speichern.

Mittel

F11

Quick-Share Button fuer aktuelle Datei (kopiert Freigabe-Link, zeigt aktuelle Berechtigungen).

Mittel

F12

Schnellsuche ueber Dateien im Workspace (Titel, Inhalt, Ersteller).

Mittel

F13

Onboarding-Tooltip-Tour fuer Modi-Umschaltung, Git-Panel, Sharing.

Niedrig

### Nicht-funktionale Anforderungen

ID

Anforderung

Prioritaet

NF01

Realtime-Latenz fuer Kollaboration und Preview < 250 ms im lokalen Netz.

Hoch

NF02

Sichtbare Skeleton-Loader fuer Ordnerbaum, Editor, Preview und Git-Panel (Verwendung des bestehenden `useSkeletonLoading`).

Hoch

NF03

Rollen- und Berechtigungspruefung ueber Authentik/RBAC vor jedem API- und WebSocket-Zugriff; Deny-by-Default.

Hoch

NF04

Stabil bei Browser-Refresh: Reconnect stellt YJS-Dokument, Presence und Git-Status wieder her.

Hoch

NF05

Farbkontrast: Bei individuellen Highlights immer Textfarbe explizit setzen, auch bei Custom-Backgrounds (Theme-Vorgabe).

Hoch

NF06

Skalierung: Mindestens 50 gleichzeitige Sessions pro Dokument ohne sichtbare Degradation.

Mittel

NF07

Auditierbarkeit: Commit-Historie speichert Author, Timestamp, Delta-Hash.

Mittel

NF08

Barrierefreiheit: Tastatursteuerung fuer Moduswechsel, Tabs und Git-Panel.

Mittel

---

## Datenbank-Design

### Neue Tabellen

#### `markdown_workspaces`

Spalte

Typ

Nullable

Beschreibung

id

INT (PK)

Nein

Eindeutige Workspace-ID

name

VARCHAR(255)

Nein

Anzeigename der Arbeitsflaeche

owner_user_id

INT (FK)

Nein

Besitzer, Default ist Anlegender

visibility

ENUM

Nein

private, team, org

created_at

DATETIME

Nein

Erstellt

updated_at

DATETIME

Ja

Geaendert

#### `markdown_documents`

Spalte

Typ

Nullable

Beschreibung

id

INT (PK)

Nein

Dokument-ID

workspace_id

INT (FK)

Nein

Zuordnung zu Workspace

parent_id

INT (FK)

Ja

Ordner-Hierarchie (self-reference)

title

VARCHAR(255)

Nein

Dateiname (ohne Endung)

slug

VARCHAR(255)

Nein

URL-Slug

yjs_doc_id

VARCHAR(255)

Nein

Referenz auf YJS-Dokument

last_editor_user_id

INT (FK)

Ja

Letzter Bearbeiter

last_commit_id

INT (FK)

Ja

Letzter Commit

created_at

DATETIME

Nein

Erstellt

updated_at

DATETIME

Ja

Geaendert

#### `markdown_shares`

Spalte

Typ

Nullable

Beschreibung

id

INT (PK)

Nein

Freigabe-ID

document_id

INT (FK)

Nein

Geteiltes Dokument/Ordner

grantee_type

ENUM

Nein

user, role

grantee_id

INT

Ja

User- oder Rollen-ID

permission

ENUM

Nein

view, edit, share

created_by

INT (FK)

Nein

Wer teilte

expires_at

DATETIME

Ja

Optionale Ablaufzeit

created_at

DATETIME

Nein

Erstellt

#### `markdown_commits`

Spalte

Typ

Nullable

Beschreibung

id

INT (PK)

Nein

Commit-ID

document_id

INT (FK)

Nein

Bezogenes Dokument

author_user_id

INT (FK)

Nein

Autor

message

TEXT

Nein

Commit-Message

diff_summary

TEXT

Ja

Aggregierte Aenderungsliste

created_at

DATETIME

Nein

Zeitstempel

#### `markdown_commit_deltas`

Spalte

Typ

Nullable

Beschreibung

id

INT (PK)

Nein

Delta-ID

commit_id

INT (FK)

Nein

Zugehoeriger Commit

user_color

VARCHAR(16)

Ja

Farbe zum Zeitpunkt des Commits

line_range

VARCHAR(64)

Nein

Bereich, der geaendert wurde

hash

VARCHAR(64)

Nein

Hash des Blocks

### Relationen (vereinfacht)

```
workspace ──< documents (self-referencing fuer Ordnerbaum)
documents ──< shares
documents ──< commits ──< commit_deltas
documents ── yjs_doc_id mapped auf yjs-server Room
```

### Aenderungen an bestehenden Tabellen

Tabelle

Aenderung

Beschreibung

permission_service (RBAC)

Neue Permissions `feature:markdown_collab:{view,edit,share}`

Konsistente Deny-by-Default Integration

user_settings (falls vorhanden)

Neues Feld `markdown_collab_view_mode`

Persistiert Modus je User

---

## API-Design

Methode

Pfad

Beschreibung

Permission

GET

/api/markdown-collab/workspaces

Liste der Workspaces

feature:markdown_collab:view

POST

/api/markdown-collab/workspaces

Workspace anlegen

feature:markdown_collab:edit

GET

/api/markdown-collab/workspaces/:id/tree

Ordner- und Dateistruktur laden

feature:markdown_collab:view

POST

/api/markdown-collab/documents

Datei/Ordner anlegen

feature:markdown_collab:edit

PATCH

/api/markdown-collab/documents/:id

Umbenennen, verschieben

feature:markdown_collab:edit

DELETE

/api/markdown-collab/documents/:id

Loeschen

feature:markdown_collab:edit

GET

/api/markdown-collab/documents/:id/commits

Commit-Historie

feature:markdown_collab:view

POST

/api/markdown-collab/documents/:id/commit

Commit anlegen (inkl. diff_summary)

feature:markdown_collab:edit

POST

/api/markdown-collab/documents/:id/share

Sharing-Regel setzen

feature:markdown_collab:share

GET

/api/markdown-collab/search

Suche ueber Dateien/Content

feature:markdown_collab:view

**Responses werden als strukturierte Felder beschrieben (kein Code im Konzept):** listen von Workspaces, Baumknoten (id, type, title, hasChildren), Commits mit Author und Delta-Hash, Share-Infos (grantee, permission, expiry).

---

## WebSocket-Design

-   Namespace: `/collab/markdown` auf bestehendem YJS-Server, analog Prompt-Engineering.
-   Rooms:
    -   `markdown-doc-{id}` fuer Inhalt
    -   `markdown-doc-{id}-presence` fuer Cursor, Selections, Farben
    -   `markdown-doc-{id}-git` fuer Uncommitted-Highlights und Commit-Broadcast
-   Client -> Server Events:
    -   `presence:update` (user_id, cursor, selection, color)
    -   `mode:update` (view_mode)
    -   `git:stage` (block_hash, user_color)
    -   `git:commit` (commit_id, cleared_highlights=true)
    -   `share:request_link` (document_id)
-   Server -> Client Events:
    -   `presence:joined/left` (user, color)
    -   `render:update` (latest markdown AST hash fuer Preview)
    -   `git:highlight` (block_hash, user_id, color, timestamp)
    -   `git:reset` (clears highlights after commit)
    -   `share:link_ready` (url, permission)
-   Reconnect-Mechanik: bei Wiederbeitritt werden Cursor, farbliche Highlights und letzter View-Modus aus dem Room-State geladen.

---

## Frontend-Design

### Neue Komponenten

Komponente

Pfad-Vorschlag

Beschreibung

MarkdownCollabHome.vue

llars-frontend/src/views/MarkdownCollab/MarkdownCollabHome.vue

Einstieg mit Kachel-Liste und letzter Aktivitaet

MarkdownCollabWorkspace.vue

llars-frontend/src/views/MarkdownCollab/MarkdownCollabWorkspace.vue

Hauptansicht mit Baum, Toolbar, Editor/Preview

MarkdownTreePanel.vue

llars-frontend/src/components/MarkdownCollab/MarkdownTreePanel.vue

Ordnerbaum mit Actions und Skeleton

MarkdownEditorPane.vue

llars-frontend/src/components/MarkdownCollab/MarkdownEditorPane.vue

Editor mit YJS-Binding, Presence-Avatare

MarkdownPreviewPane.vue

llars-frontend/src/components/MarkdownCollab/MarkdownPreviewPane.vue

Live-Preview, nutzt bestehende Markdown-Render-Pipeline

MarkdownModeToggle.vue

llars-frontend/src/components/MarkdownCollab/MarkdownModeToggle.vue

Schalter Editor/Split/Preview

MarkdownGitPanel.vue

llars-frontend/src/components/MarkdownCollab/MarkdownGitPanel.vue

Uncommitted-Highlights, Commit-Form, History

MarkdownShareDialog.vue

llars-frontend/src/components/MarkdownCollab/MarkdownShareDialog.vue

Teilen nach User/Rolle, Link-Sharing

### Layout (Default Split View)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Header: [Breadcrumb] [Search] [Mode Toggle] [Share] [Git Status]         │
├───────────────┬─────────────────────────────────────┬────────────────────┤
│ Ordnerbaum    │ Editor (YJS, Presence, Highlights)  │ Live Preview        │
│ (3/12 Breite) │                                     │ (identischer MD)    │
│ - Workspace   │ ▒▒▒▒▒▒ Skeleton beim Laden          │ ▒▒▒▒▒▒ Skeleton     │
│ - Files ...   │                                     │                    │
├───────────────┴─────────────────────────────────────┴────────────────────┤
│ Git Panel (History, Commit Message, Diff Preview, Highlights Reset)      │
└──────────────────────────────────────────────────────────────────────────┘
```

### View-Modus Toggle (PyCharm-inspiriert)

```
[Editor] [Split] [Preview]
   |        |        |
   |        |        +-- rendert gesamte Flaeche (Preview Pane nimmt Editor ein)
   |        +----------- Editor links, Preview rechts
   +-------------------- Editor Vollbild
```

### Presence und Farben

-   Avatare/Initialen in Toolbar und im Editor (Cursor + Selection).
-   User waehlt Farbe in Profileinstellungen; falls Farbe bereits von anderem Nutzer im gleichen Dokument aktiv genutzt wird, automatische Verschiebung zum naechstliegenden freien Farbton und UI-Hinweis.
-   Highlights auf Textbausteinen bleiben bis zum naechsten Commit sichtbar; danach Reset per `git:reset`.

### Git-UX und Highlights

-   Live-Highlighting wie Textmarker pro User-Farbe; Hover zeigt User + Timestamp.
-   Uncommitted-Panel listet geaenderte Textbloecke mit Sprung ins Dokument.
-   Commit-Dialog zwingt zu Message; nach Commit verschwinden Highlights, History-Tab zeigt diff-summaries.
-   Konfliktanzeige: parallele Aenderungen werden nebeneinander dargestellt; YJS-CRDT loest Content, Farbhinterlegung bleibt pro Nutzer sichtbar bis Commit.

### Sharing UX

-   Quick-Share im Header: kopiert Link, zeigt aktuelle Rechte.
-   Share-Dialog: User/Rolle Auswahl, Rechte (view/edit/share), optionale Ablaufzeit; Audit-Log-Eintrag in Historie.
-   In Baum sichtbar, welche Ordner oder Dateien geteilt sind.

### Skeleton Loading

-   TreePanel: Skeleton-Zeilen fuer Ordner/File-Items.
-   EditorPane: Placeholder-Lines; GitPanel: Skeleton Cards; PreviewPane: Placeholder-Blocks.
-   Nutzung des bestehenden `useSkeletonLoading` Composable, inkl. isLoading pro Abschnitt.

### Styling und Theme

-   Dark/Light wird ueber bestehendes Theme-System gesteuert.
-   Bei farbigen Highlights und Panels immer `color: rgb(var(--v-theme-on-surface))` oder on-surface-variant erzwingen, um Kontrast im Light Mode sicherzustellen.
-   Keine neue Farbpalette ausser User-Highlight-Farben; restliche UI nutzt Vuetify Tokens.

---

## Sicherheit und Berechtigungen

Permission

Zweck

feature:markdown_collab:view

Kachel sehen, Workspaces und Dateien lesen

feature:markdown_collab:edit

Dateien bearbeiten, Commits erstellen, Modi wechseln

feature:markdown_collab:share

Sharing-Regeln setzen, Links erzeugen

Weitere Checks:

-   Jede WebSocket-Verbindung validiert Authentik-JWT (RS256) und mapped Rollen auf Permissions.
-   Deny-by-Default, explizite Deny-Regeln uebersteuern Grants.
-   Keine Speicherung von Tokens im LocalStorage; SessionStorage analog Frontend-Auth.
-   Rate Limits fuer Share-Links und Commits (pro User) auf API-Ebene.

---

## Offene Fragen

-   Soll ein Workspace git-multiples Dokumente als ein Repository behandeln oder Commit-Historie je Datei fuehren? (aktueller Vorschlag: pro Dokument).
-   Wie viele Farbschritte fuer Autoresolution sind erlaubt, bevor ein Konflikt als Fehler angezeigt wird?
-   Sollen Diff-Previews rein textbasiert bleiben oder gerenderte Markdown-Sections zeigen?
-   Ist Link-Sharing auf Rollen-Basis ausreichend oder wird anonymes Lesen fuer bestimmte Faelle erwuenscht?

---

## Abnahme

Reviewer

Datum

Status

Philipp Steigerwald

offen

Ausstehend