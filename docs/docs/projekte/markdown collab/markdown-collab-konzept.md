# Markdown Collab Workspace – Konzept

!!! warning "Status: Konzept" Dieses Dokument beschreibt das Zielbild und die geplante Umsetzung. Details können sich in der Implementierung noch ändern.

**Stand:** 2025-12-12  
**Autor:** Philipp Steigerwald / Codex  
**Version:** 1.1

---

## 1. Zielbild und Nutzen

Der **Markdown Collab Workspace** ist eine kollaborative Arbeitsfläche für Markdown-Dateien innerhalb von LLARS.  
Er nutzt die vorhandene Plattform‑Infrastruktur (YJS‑Service, RBAC, Authentik, Theme‑System, Skeleton‑Loading, Home‑Kachel‑Startseite), um:

-   Markdown‑Dateien in Echtzeit gemeinsam zu bearbeiten
-   eine Live‑Preview parallel zum Editor zu rendern
-   Änderungen pro Nutzer git‑ähnlich nachvollziehbar zu machen (Highlights, Commits, History)
-   Dateien/Ordner kontrolliert zu teilen (view/edit/share)

**Abgrenzung (Out of Scope, v1):**

-   Vollwertige Git‑Integration mit Branching/Merging außerhalb der App
-   Offline‑Modus
-   Externe Datei‑Synchronisation (z. B. direktes Repo‑Mount)

---

## 2. Nutzer‑Flow (Kurz)

1.  **Home → Markdown Collab**  
    Einstieg über Kachel in eine Workspace‑Übersicht.
2.  **Workspace wählen/erstellen**  
    Ordnerbaum und „Zuletzt bearbeitet“ sichtbar.
3.  **Datei öffnen**  
    Editor/Split/Preview wählen, Live‑Preview läuft automatisch.
4.  **Gemeinsam arbeiten**  
    Presence (Cursors/Selections), Auto‑Save, Highlights.
5.  **Committen & Teilen**  
    Changes reviewen, Commit‑Message setzen, History anschauen, Links/Einladungen verwalten.

---

## 3. Anforderungen

### 3.1 Funktionale Anforderungen

**Workspace & Navigation**

-   **F01 (hoch)**: Home‑Kachel „Markdown Collab“ führt in eine Workspace‑Startseite mit Ordnerstruktur und zuletzt bearbeiteten Dateien.
-   **F02 (hoch)**: Ordnerbaum mit CRUD für Dateien/Ordner (anlegen, umbenennen, löschen, duplizieren) sowie Drag‑and‑Drop zum Sortieren/Verschieben.

**Ansichten & Rendering**

-   **F03 (hoch)**: Drei View‑Modi: **Editor**, **Split** (Editor links, Preview rechts), **Preview**. Umschaltbar ohne Reload, pro User persistent.
-   **F04 (hoch)**: Live‑Preview mit **gleichem Markdown‑Renderer wie im LLARS‑Frontend** (aktuell `marked` + DOMPurify, siehe Chat‑Rendering). Preview rendert automatisch ohne Save‑Aktion.

**Kollaboration & Presence**

-   **F05 (hoch)**: YJS‑Realtime‑Kollaboration inkl. Presence (Avatare/Initialen, Cursor‑ und Selection‑Farben) sowie Anzeige aktiver Nutzer im Dokument.
-   **F06 (hoch)**: Auto‑Save über WebSockets: jede Änderung wird sofort synchronisiert, kein Save‑Button.

**Teilen & Rechte**

-   **F07 (hoch)**: Teilen von Dateien/Ordnern über Einladungen (User/Rolle) und optionalen Freigabe‑Link. Rechte: **view / edit / share**; Ordner‑Freigaben vererben sich rekursiv auf alle enthaltenen Dokumente, sofern nicht überschrieben.
-   **F08 (mittel)**: Quick‑Share‑Button im Header der aktuellen Datei (kopiert Link, zeigt aktuelle Freigaben).

**Git‑Flow & Nachvollziehbarkeit**

-   **F09 (hoch)**: Git‑artige Änderungsverfolgung: farbliche Highlights pro User für uncommitted Änderungen; Farbkollisionen werden automatisch auf freie Töne verschoben.
-   **F10 (hoch)**: Commit‑Flow im UI: Änderungsliste, Commit‑Message Pflicht, Highlights resetten; History mit Diff‑Preview pro Commit.

**Produktivität**

-   **F11 (mittel)**: Benutzerdefinierte Shortcuts (z. B. View‑Modus‑Wechsel) im lokalen Profil speichern.
-   **F12 (mittel)**: Schnellsuche über Dateien im Workspace (Titel, Inhalt, Ersteller).
-   **F13 (niedrig)**: Onboarding‑Tour (Tooltip‑Walkthrough) für Modi, Git‑Panel, Sharing.

### 3.2 Nicht‑funktionale Anforderungen

**Performance & Stabilität**

-   **NF01 (hoch)**: Realtime‑Latenz für Kollaboration und Preview < 250 ms im lokalen Netz.
-   **NF02 (hoch)**: Rejoin/Reload stellt YJS‑Dokument, Presence und Git‑Status nahtlos wieder her.

**Feedback & UX**

-   **NF03 (hoch)**: Skeleton‑Loader für Ordnerbaum, Editor, Preview und Git‑Panel (bestehendes `useSkeletonLoading`).
-   **NF04 (hoch)**: Farbkontrast im Light‑Mode sicherstellen; bei farbigen Hintergründen immer explizite Textfarbe setzen.
-   **NF05 (mittel)**: Barrierefreiheit: Tastatursteuerung für Moduswechsel, Tabs und Git‑Panel.

**Sicherheit, Skalierung & Audit**

-   **NF06 (hoch)**: RBAC‑Check via Authentik vor jedem API‑ und WebSocket‑Zugriff; Deny‑by‑Default.
-   **NF07 (mittel)**: ≥50 gleichzeitige Sessions pro Dokument ohne sichtbare Degradation.
-   **NF08 (mittel)**: Auditierbarkeit: Commit‑Historie speichert Autor, Timestamp und Delta‑Hash.

---

## 4. Technische Einordnung in LLARS

-   **Realtime‑Sync:** Nutzung des bestehenden `yjs-service` (`/collab/socket.io/`).  
    Das Event‑API ist identisch zum Prompt‑Engineering‑Modul (`join_room`, `sync_update`, `cursor_update` usw.).  
    Für Markdown‑Collab wird ein eigener Room‑Prefix verwendet (z. B. `markdown_{documentId}`), damit keine Kollisionen mit Prompt‑Rooms entstehen.
-   **Persistenz:** Der YJS‑Service speichert aktuell Prompts in `user_prompts`. Für Markdown‑Collab wird die Persistenz auf `markdown_documents` erweitert (Adapter nach Room‑Prefix).
-   **Backend:** Flask‑REST‑API unter `/api/markdown-collab/*`, abgesichert via `@require_permission`.
-   **Frontend:** Vue/Vuetify‑Views analog Prompt‑Engineering‑Struktur; Skeleton‑Loading verpflichtend.

---

## 5. Datenbank‑Design

### 5.1 Neue Tabellen

#### `markdown_workspaces`
| Spalte | Typ | Null | Beschreibung |
|---|---|---|---|
| id | INT (PK) | nein | Eindeutige Workspace‑ID |
| name | VARCHAR(255) | nein | Anzeigename der Arbeitsfläche |
| owner_user_id | INT (FK) | nein | Besitzer (Default: Anlegender) |
| visibility | ENUM | nein | `private`, `team`, `org` |
| created_at | DATETIME | nein | Erstellt |
| updated_at | DATETIME | ja | Geändert |

#### `markdown_documents`
| Spalte | Typ | Null | Beschreibung |
|---|---|---|---|
| id | INT (PK) | nein | Dokument‑ID |
| workspace_id | INT (FK) | nein | Zuordnung zum Workspace |
| parent_id | INT (FK) | ja | Ordner‑Hierarchie (Self‑Reference) |
| title | VARCHAR(255) | nein | Dateiname (ohne Endung) |
| slug | VARCHAR(255) | nein | URL‑Slug |
| yjs_doc_id | VARCHAR(255) | nein | Referenz auf YJS‑Room |
| last_editor_user_id | INT (FK) | ja | Letzter Bearbeiter |
| last_commit_id | INT (FK) | ja | Letzter Commit |
| created_at | DATETIME | nein | Erstellt |
| updated_at | DATETIME | ja | Geändert |

#### `markdown_shares`
| Spalte | Typ | Null | Beschreibung |
|---|---|---|---|
| id | INT (PK) | nein | Freigabe‑ID |
| document_id | INT (FK) | nein | Geteiltes Dokument/Ordner |
| grantee_type | ENUM | nein | `user` oder `role` |
| grantee_id | INT | ja | User‑ oder Rollen‑ID |
| permission | ENUM | nein | `view`, `edit`, `share` |
| created_by | INT (FK) | nein | Wer teilte |
| expires_at | DATETIME | ja | Optionale Ablaufzeit |
| created_at | DATETIME | nein | Erstellt |

Freigaben können auf **Dokument‑ oder Ordner‑Nodes** gesetzt werden. Ordner‑Freigaben gelten standardmäßig für alle Unterordner und Dokumente, bis eine spezifischere Regel (z. B. explizites Deny oder engeres Grant) greift.

#### `markdown_commits`
| Spalte | Typ | Null | Beschreibung |
|---|---|---|---|
| id | INT (PK) | nein | Commit‑ID |
| document_id | INT (FK) | nein | Bezogenes Dokument |
| author_user_id | INT (FK) | nein | Autor |
| message | TEXT | nein | Commit‑Message |
| diff_summary | TEXT | ja | Aggregierte Änderungsliste |
| created_at | DATETIME | nein | Zeitstempel |

#### `markdown_commit_deltas`
| Spalte | Typ | Null | Beschreibung |
|---|---|---|---|
| id | INT (PK) | nein | Delta‑ID |
| commit_id | INT (FK) | nein | Zugehöriger Commit |
| user_color | VARCHAR(16) | ja | Farbe zum Zeitpunkt des Commits |
| line_range | VARCHAR(64) | nein | Bereich, der geändert wurde |
| hash | VARCHAR(64) | nein | Hash des Blocks |

### 5.2 Relationen (vereinfacht)

```
workspace ──< documents (Self‑Reference für Ordnerbaum)
documents ──< shares
documents ──< commits ──< commit_deltas
documents ── yjs_doc_id → yjs‑server Room
```

### 5.3 Änderungen an bestehenden Tabellen
| Tabelle | Änderung | Beschreibung |
|---|---|---|
| permission_service (RBAC) | Neue Permissions `feature:markdown_collab:{view,edit,share}` | Konsistente Deny‑by‑Default‑Integration |
| user_settings (falls vorhanden) | Neues Feld `markdown_collab_view_mode` | Persistiert Modus je User |

---

## 6. API‑Design (REST)
| Methode | Pfad | Beschreibung | Permission |
|---|---|---|---|
| GET | `/api/markdown-collab/workspaces` | Liste der Workspaces | `feature:markdown_collab:view` |
| POST | `/api/markdown-collab/workspaces` | Workspace anlegen | `feature:markdown_collab:edit` |
| GET | `/api/markdown-collab/workspaces/:id/tree` | Ordner‑/Dateistruktur laden | `feature:markdown_collab:view` |
| POST | `/api/markdown-collab/documents` | Datei/Ordner anlegen | `feature:markdown_collab:edit` |
| PATCH | `/api/markdown-collab/documents/:id` | Umbenennen, verschieben | `feature:markdown_collab:edit` |
| DELETE | `/api/markdown-collab/documents/:id` | Löschen | `feature:markdown_collab:edit` |
| GET | `/api/markdown-collab/documents/:id/commits` | Commit‑Historie | `feature:markdown_collab:view` |
| POST | `/api/markdown-collab/documents/:id/commit` | Commit anlegen (inkl. `diff_summary`) | `feature:markdown_collab:edit` |
| POST | `/api/markdown-collab/documents/:id/share` | Sharing‑Regel setzen | `feature:markdown_collab:share` |
| GET | `/api/markdown-collab/search` | Suche über Dateien/Content | `feature:markdown_collab:view` |

**Response‑Formate (nur strukturell):**  
Workspaces‑Liste, Tree‑Nodes (`id`, `type`, `title`, `hasChildren`), Commits inkl. Autor/Hash, Share‑Infos (`grantee`, `permission`, `expiry`).

---

## 7. Realtime‑Design (YJS‑Service)

Der bestehende YJS‑Service wird wiederverwendet. Für Markdown‑Collab gelten dieselben Basisevents wie im Prompt‑Engineering‑Modul:

-   **Socket.IO Path:** `/collab/socket.io/`
-   **Room‑Namen:** `markdown_{documentId}` (eigener Prefix; Persistenzadapter im YJS‑Service erforderlich)

**Client → Server**

-   `join_room` `{ room }`  
    Liefert `snapshot_document` und `room_state`, broadcastet `user_joined`.
-   `sync_update` `{ room, update }`  
    Überträgt YJS‑Updates für Inhalt und kollaborative Metadaten (z. B. Highlights).
-   `cursor_update` `{ room, blockId, range|null }`  
    Presence für Cursor/Selection.

**Server → Client**

-   `snapshot_document` (voller YJS‑State)
-   `room_state` (User‑Liste + Cursors)
-   `user_joined` / `user_left`
-   `sync_update`
-   `cursor_updated`

**Git‑Highlights & Commit‑Reset**

-   Uncommitted‑Highlights werden als kollaborative Metadaten im selben YJS‑Dokument gehalten (z. B. `Y.Map` pro Block/Line‑Range).  
    Dadurch reicht `sync_update` für Broadcast/Replay.
-   Nach einem Commit wird der Highlight‑State serverseitig (REST) geleert und über YJS‑Update synchronisiert.

---

## 8. Frontend‑Design

### 8.1 Neue Views/Komponenten
| Komponente | Pfad | Zweck |
|---|---|---|
| `MarkdownCollabHome.vue` | `llars-frontend/src/views/MarkdownCollab/MarkdownCollabHome.vue` | Workspace‑Einstieg, zuletzt bearbeitet |
| `MarkdownCollabWorkspace.vue` | `llars-frontend/src/views/MarkdownCollab/MarkdownCollabWorkspace.vue` | Hauptansicht mit Baum, Toolbar, Editor/Preview |
| `MarkdownTreePanel.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownTreePanel.vue` | Ordnerbaum + Actions + Skeleton |
| `MarkdownEditorPane.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownEditorPane.vue` | Editor mit YJS‑Binding und Presence |
| `MarkdownPreviewPane.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownPreviewPane.vue` | Live‑Preview (marked + Sanitize) |
| `MarkdownModeToggle.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownModeToggle.vue` | Umschalter Editor/Split/Preview |
| `MarkdownGitPanel.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownGitPanel.vue` | Highlights, Commit‑Form, History |
| `MarkdownShareDialog.vue` | `llars-frontend/src/components/MarkdownCollab/MarkdownShareDialog.vue` | Teilen nach User/Rolle, Link‑Sharing |

### 8.1.1 Standard View (Workspace‑Übersicht)

Die Standardansicht ist der Datei‑ und Ordner‑Explorer eines Workspaces. Hier sieht man **alle Dateien**, kann die Struktur bearbeiten und Freigaben direkt am Baum setzen (Datei **oder** Ordner).  
Wird ein User auf Ordner‑Ebene hinzugefügt, kann er alle enthaltenen Dokumente gemeinsam mit dem Besitzer bearbeiten (rekursive Vererbung).  
Ein Klick auf eine Markdown‑Datei öffnet anschließend die Editor‑Ansicht gemäß Abschnitt **8.2**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Header: [Workspace] [Suche] [Neue Datei] [Neuer Ordner] [Upload]         │
├───────────────────────────────┬──────────────────────────────────────────┤
│ Ordnerbaum / Dateien          │ Details & Freigaben                        │
│ (kompletter Workspace)        │                                           │
│ ├─ Research/            [S]   │ Auswahl: Research/                         │
│ │   ├─ intro.md   [S]         │ Besitzer: philipp                          │
│ │   ├─ notes.md   [S]         │ Mitbearbeiter: alice, bob                  │
│ │   └─ drafts/    [S]         │ Rechte: view/edit/share                    │
│ │       ├─ v1.md [S]          │ Aktionen: [User/Rolle hinzufügen] [Link]   │
│ │       └─ v2.md [S]          │ (Ordner‑Freigaben vererben sich)           │
│ └─ Archive/                   │                                           │
└───────────────────────────────┴──────────────────────────────────────────┘
[S] = Freigabe/Mitbearbeiter‑Icon pro Node (Datei oder Ordner)
```

### 8.2 Layout (Default Split View)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Header: [Breadcrumb] [Search] [Mode Toggle] [Share] [Git Status]         │
├───────────────┬─────────────────────────────────────┬────────────────────┤
│ Ordnerbaum    │ Editor (YJS, Presence, Highlights)  │ Live Preview        │
│ (3/12 Breite) │ ▒▒▒▒▒▒ Skeleton beim Laden          │ ▒▒▒▒▒▒ Skeleton     │
│ - Workspace   │                                     │ (gleicher Renderer) │
│ - Files ...   │                                     │                    │
├───────────────┴─────────────────────────────────────┴────────────────────┤
│ Git Panel (History, Commit Message, Diff Preview, Highlights Reset)      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 8.3 View‑Modus Toggle (PyCharm‑inspiriert)

```
[Editor] [Split] [Preview]
   |        |        |
   |        |        +-- Preview Pane übernimmt die Fläche
   |        +----------- Editor links, Preview rechts
   +-------------------- Editor Vollbild
```


### 8.4 Presence, Git‑UX, Sharing, Styling

-   **Presence/Farben:** Avatare/Initialen im Header und Cursor/Selections im Editor; Farbkollisionen werden auf freie Töne verschoben.
-   **Git‑UX:** Live‑Highlighting pro User‑Farbe, Uncommitted‑Liste mit Sprung ins Dokument, Commit‑Pflichtmessage, History‑Diffs.
-   **Sharing:** Freigaben direkt im Baum (Datei/Ordner) oder via Quick‑Share im Header; Dialog für User/Rollen‑Freigaben inkl. Ablaufzeit; Ordner‑Freigaben vererben sich und werden entsprechend markiert.
-   **Skeleton‑Loading:** TreePanel/Editor/Preview/GitPanel verwenden `useSkeletonLoading` je Abschnitt.
-   **Theme:** Keine neue Palette außer Highlights; bei Highlights immer `color: rgb(var(--v-theme-on-surface))` setzen.

### 8.4.1 Git‑Panel & Highlighting (Detailansicht)

Die Editor‑Ansicht kombiniert zwei unabhängige Hervorhebungs‑Ebenen:

- **Syntax‑Highlighting (Textfarbe):** Markdown‑Tokens (Überschriften, Listen, Links, Inline‑/Block‑Code, Zitate usw.) werden farblich gemäß Light/Dark‑Theme eingefärbt. Implementierung über einen Markdown‑fähigen Code‑Editor (z. B. CodeMirror 6 oder Monaco) mit LLARS‑Theme‑Tokens.
- **Git‑Highlighting (Hintergrundfarbe):** Uncommitted Änderungen werden halbtransparent im Hintergrund markiert – **in der Farbe des Users**, der den Block zuletzt geändert hat. Syntax‑Farben bleiben sichtbar, da nur der Hintergrund eingefärbt wird.

**Farblegende (live‑Beispiel im Doc):**

- Syntax‑Beispiele (Textfarbe):
    - <span style="color:#1976D2; font-weight:700"># *Überschrift*</span>
    - <span style="color:#2E7D32">- *Liste / Bullet*</span>
    - <span style="color:#9C27B0">`inline code` / ```fenced code```</span>
    - <span style="color:#1565C0">[*Link*](...)</span>
- Git‑Change‑Beispiele (Hintergrundfarbe pro User):
    - <span style="background-color:rgba(255,105,180,0.25)">Alice‑Änderung</span>
    - <span style="background-color:rgba(0,188,212,0.25)">Bob‑Änderung</span>

**Beispiel – Editor‑Ausschnitt mit Syntax‑ und Change‑Highlights (mit echten Farben):**

<pre style="font-family: monospace; white-space: pre; line-height: 1.3;">
┌──────────────────────────────────────────────────────────────────────────┐
│ Editor (Syntax‑Farben + Git‑Hintergründe)                                │
├──────────────────────────────────────────────────────────────────────────┤
│  12 │ <span style="color:#1976D2; font-weight:700"># Projekt‑Ziel</span>                                                     │
│  13 │ Dieser Workspace erlaubt …                                         │
│  14 │                                                                    │
│  15 │ <span style="background-color:rgba(255,105,180,0.25); color:#1976D2; font-weight:600">## Vorgehen</span>                                                        │
│  16 │ <span style="background-color:rgba(255,105,180,0.25); color:#2E7D32">- Schritt 1</span>                                                        │
│  17 │ <span style="background-color:rgba(0,188,212,0.25); color:#2E7D32">- Schritt 2</span>                                                        │
│  18 │                                                                    │
│  19 │ <span style="color:#9C27B0">```python</span>                                                          │
│  20 │ <span style="background-color:rgba(0,188,212,0.25); color:#9C27B0">def hello():</span>                                                       │
│  21 │ <span style="background-color:rgba(0,188,212,0.25); color:#9C27B0">    return "hi"</span>                                                    │
│  22 │ <span style="color:#9C27B0">```</span>                                                                │
└──────────────────────────────────────────────────────────────────────────┘
</pre>

Legende:
Syntax‑Textfarben = farbige Markdown‑Tokens (Theme‑abhängig)  
Git‑Hintergrund   = halbtransparente User‑Farbe pro uncommitted Change

**Beispiel – Git‑Panel mit Changes, Diff und History (mit Farben):**

<pre style="font-family: monospace; white-space: pre; line-height: 1.3;">
┌──────────────────────────────────────────────────────────────────────────┐
│ Git Panel                                                                 │
├────────────── Uncommitted Changes ────────────────┬────────── History ───┤
│ <span style="color:#E91E63; font-weight:600">Alice (pink)</span>                                      │  a1b2c3  "Intro"       │
│  • <span style="background-color:rgba(255,105,180,0.25)">lines 15‑16  ## Vorgehen</span>                       │  d4e5f6  "Fix typos"   │
│ <span style="color:#00BCD4; font-weight:600">Bob (cyan)</span>                                        │  g7h8i9  "Add code"    │
│  • <span style="background-color:rgba(0,188,212,0.25)">lines 17,20‑21  Liste + Code‑Block</span>             │                        │
├────────────────────────── Commit ─────────────────┴──────────────────────┤
│ Message: [_____________________________________]  [Commit] [Discard]     │
│ Diff Preview (selected change)                                            │
│  - old: …                                                                 │
│  + new: …   (Raw Diff / Rendered Diff toggle)                             │
└──────────────────────────────────────────────────────────────────────────┘
</pre>

Nach erfolgreichem Commit werden die Uncommitted‑Highlights geleert und die History um den neuen Commit ergänzt.

---

## 9. Sicherheit und Berechtigungen
| Permission | Zweck |
|---|---|
| `feature:markdown_collab:view` | Kachel sehen, Workspaces/Dateien lesen |
| `feature:markdown_collab:edit` | Dateien bearbeiten, Commits erstellen, Modi wechseln |
| `feature:markdown_collab:share` | Sharing‑Regeln setzen, Links erzeugen |

Weitere Checks:

-   Jede WebSocket‑Verbindung validiert Authentik‑JWT (RS256). User‑Infos kommen **nur** aus dem Token.
-   Deny‑by‑Default; explizite Deny‑Regeln übersteuern Grants.
-   Tokens bleiben in `sessionStorage` (analog Frontend‑Auth).
-   Rate‑Limits für Share‑Links und Commits pro User auf API‑Ebene.

---

## 10. Offene Fragen

-   Sollen Commits **pro Dokument** (aktueller Vorschlag) oder als Workspace‑Repository geführt werden?
-   Wie viele automatische Farbschritte sind ok, bevor ein Konflikt sichtbar angezeigt wird?
-   Diff‑Preview: rein textuell oder mit gerenderten Markdown‑Sections?
-   Reicht Rollen‑basiertes Link‑Sharing oder wird anonymes Lesen benötigt?

---

## 11. Abnahme
| Reviewer | Datum | Status |
|---|---|---|
| Philipp Steigerwald | offen | ausstehend |
