# Konzept: KI-gestützte Kommentare im LaTeX Collab

## Übersicht

Dieses Konzept beschreibt die Erweiterung des LaTeX Collab Kommentar-Systems um KI-gestützte Funktionen, eine dedizierte LLARS-KI-Identität sowie verbesserte UI-Elemente.

---

## 1. LLARS KI als dedizierter User

### 1.1 KI-User-Identität

Die LLARS KI wird als eigenständiger "virtueller User" im System behandelt:

```
Username:      LLARS KI
Typ:           System-AI (is_ai = true)
Farbe:         Admin-konfigurierbar (Standard: #9B59B6 - Violett)
Avatar:        Spezielles KI-Icon (Roboter/Sparkles)
```

### 1.2 Admin-Einstellungen (SystemSettings)

Neue Felder in `system_settings`:

```python
# Neue Spalten
ai_assistant_color: str = "#9B59B6"     # Reservierte KI-Farbe (Hex)
ai_assistant_username: str = "LLARS KI"  # Anzeigename der KI
ai_assistant_enabled: bool = True        # KI-Features aktiviert
```

### 1.3 Farb-Reservierung

- Die KI-Farbe ist **reserviert** und kann von regulären Usern nicht gewählt werden
- Bei User-Farbauswahl wird die KI-Farbe aus der Palette ausgeschlossen
- Visuell sofort erkennbar: "Das hat die KI gemacht"

---

## 2. KI-Kommentar-Assistent

### 2.1 Feature: "KI umsetzen"

Button auf jedem Kommentar, der:
1. Den markierten Textbereich (`range_start` bis `range_end`) identifiziert
2. Zusätzlichen Kontext sammelt (±500 Zeichen um den Bereich)
3. Die Anmerkung analysiert und als Änderungsvorschlag interpretiert
4. Die Änderung im Dokument umsetzt
5. Automatisch als KI auf den Kommentar antwortet
6. Optional: Kommentar als "erledigt" markiert

### 2.2 Workflow

```
┌─────────────────────────────────────────────────────────┐
│  Kommentar: "Hier fehlt ein Absatz über die Methodik"   │
│  [Antworten] [Erledigen] [🤖 KI umsetzen]              │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  KI-Verarbeitung:                                       │
│  1. Text bei range_start:range_end extrahieren          │
│  2. Kontext drumherum sammeln                           │
│  3. Prompt erstellen mit Anweisung                      │
│  4. LLM generiert Änderung                              │
│  5. Änderung in Editor einfügen (via Yjs)               │
│  6. Auto-Reply erstellen                                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Kommentar: "Hier fehlt ein Absatz über die Methodik"   │
│  └─ 🤖 LLARS KI: "Ich habe einen Absatz zur Methodik   │
│     eingefügt, der die experimentelle Vorgehensweise    │
│     beschreibt."                                        │
│  Status: ✅ Erledigt                                    │
└─────────────────────────────────────────────────────────┘
```

### 2.3 Backend-API

Neuer Endpoint:

```
POST /api/latex-collab/comments/{comment_id}/ai-resolve
```

Request:
```json
{
  "model_id": "optional - falls User spezifisches Model wählt",
  "auto_resolve": true
}
```

Response:
```json
{
  "success": true,
  "changes": {
    "document_id": 3,
    "range_start": 150,
    "range_end": 200,
    "old_text": "...",
    "new_text": "..."
  },
  "reply": {
    "id": 42,
    "author_username": "LLARS KI",
    "author_color": "#9B59B6",
    "body": "Ich habe die Änderung umgesetzt: ..."
  }
}
```

### 2.4 Prompt-Struktur

```
Du bist ein hilfreicher Assistent für LaTeX-Dokumente.

Ein Benutzer hat folgenden Kommentar zu einem Textabschnitt hinterlassen:
---
Kommentar: "{comment_body}"
---

Der betroffene Textabschnitt ist:
---
{selected_text}
---

Kontext davor:
---
{context_before}
---

Kontext danach:
---
{context_after}
---

Bitte setze die Anmerkung des Benutzers um und gib nur den
verbesserten/geänderten Text zurück, der den markierten Abschnitt
ersetzen soll. Behalte die LaTeX-Formatierung bei.
```

---

## 3. KI-Textänderungen im Editor

### 3.1 Visuelle Kennzeichnung

Wenn die KI Text ändert, wird dieser temporär markiert:

```css
.ai-changed-text {
  background-color: rgba(155, 89, 182, 0.15);  /* KI-Farbe transparent */
  border-left: 3px solid #9B59B6;
  transition: background-color 2s ease-out;
}
```

- Highlight verschwindet nach ~5 Sekunden
- Bleibt bei Hover über "KI-Änderungen anzeigen" Button

### 3.2 KI-Änderungen im Git-Panel

Im Git-Panel werden KI-Änderungen gesondert angezeigt:

```
🤖 KI-Änderungen (2)
├── main.tex: +15 Zeilen (Methodik-Absatz)
└── intro.tex: ~3 Zeilen (Formulierung)
```

---

## 4. Resizable Panels (Kommentare ↔ PDF)

### 4.1 Aktuelle Struktur

```
┌──────────────────────────────────────────────────┐
│                   Preview Pane                    │
│  ┌────────────────────────────────────────────┐  │
│  │              PDF Viewer                     │  │
│  │                                            │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │           Comments Panel (fixed)           │  │
│  │  max-height: 260px                         │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 4.2 Neue Struktur mit Resize

```
┌──────────────────────────────────────────────────┐
│                   Preview Pane                    │
│  ┌────────────────────────────────────────────┐  │
│  │              PDF Viewer                     │  │
│  │         (flex: 1, resizable)               │  │
│  └────────────────────────────────────────────┘  │
│  ═══════════════ RESIZE HANDLE ═══════════════   │
│  ┌────────────────────────────────────────────┐  │
│  │           Comments Panel                   │  │
│  │      (height stored in localStorage)       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```

### 4.3 Implementation

Verwende `useSplitPaneResize` Composable (bereits vorhanden):

```javascript
const {
  topPanelStyle,
  bottomPanelStyle,
  startVerticalResize
} = useSplitPaneResize({
  direction: 'vertical',
  initialTopPercent: 70,
  minTopPercent: 30,
  maxTopPercent: 90,
  storageKey: 'latex-preview-comments-split'
})
```

### 4.4 Resize Handle CSS

```css
.preview-resize-divider {
  height: 8px;
  cursor: row-resize;
  background: rgba(var(--v-theme-on-surface), 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-resize-divider:hover {
  background: rgba(var(--v-theme-primary), 0.15);
}

.preview-resize-handle {
  width: 40px;
  height: 4px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}
```

---

## 5. Datenmodell-Erweiterungen

### 5.1 SystemSettings (neu)

```python
# app/db/models/system_settings.py
class SystemSettings(db.Model):
    # ... existing fields ...

    # AI Assistant Settings
    ai_assistant_color: Mapped[str] = mapped_column(
        db.String(7), nullable=False, default="#9B59B6"
    )
    ai_assistant_username: Mapped[str] = mapped_column(
        db.String(50), nullable=False, default="LLARS KI"
    )
    ai_assistant_enabled: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, default=True
    )
```

### 5.2 User-Erweiterung

```python
# Bestehend - zur Referenz
class User(db.Model):
    is_ai: Mapped[bool] = mapped_column(db.Boolean, default=False)
    llm_model_id: Mapped[Optional[str]] = mapped_column(db.String(255))
```

### 5.3 LatexComment-Erweiterung

```python
class LatexComment(db.Model):
    # ... existing fields ...

    # Neues Feld für KI-generierte Antworten
    is_ai_generated: Mapped[bool] = mapped_column(
        db.Boolean, nullable=False, default=False
    )
    # Referenz auf den Kommentar, der diese KI-Antwort ausgelöst hat
    ai_source_comment_id: Mapped[Optional[int]] = mapped_column(
        db.Integer, db.ForeignKey("latex_comments.id", ondelete="SET NULL"),
        nullable=True
    )
```

---

## 6. Frontend-Komponenten

### 6.1 Neue Komponenten

```
src/views/LatexCollab/
├── components/
│   └── CommentAiButton.vue      # KI-umsetzen Button mit Loading-State
├── composables/
│   └── useLatexCommentAi.js     # KI-Interaktion Logic
```

### 6.2 CommentAiButton.vue

```vue
<template>
  <v-btn
    icon
    variant="text"
    size="x-small"
    :loading="isProcessing"
    :disabled="!canUseAi"
    :title="$t('latexCollab.comments.aiResolve')"
    @click.stop="handleAiResolve"
  >
    <LIcon size="16">mdi-robot</LIcon>
  </v-btn>
</template>
```

### 6.3 Neue i18n Keys

```json
{
  "latexCollab": {
    "comments": {
      "aiResolve": "Mit KI umsetzen",
      "aiProcessing": "KI verarbeitet...",
      "aiSuccess": "KI hat die Änderung umgesetzt",
      "aiError": "KI konnte die Änderung nicht umsetzen"
    }
  }
}
```

---

## 7. Implementierungs-Roadmap

### Phase 1: Grundlagen (Bug-Fixes & UI)
- [x] Bug-Fix: `range_start`/`range_end` nullable machen
- [x] Kommentare nach Autor-Farbe einfärben
- [ ] Resizable Panels für Kommentare/PDF

### Phase 2: KI-Identität
- [ ] SystemSettings um KI-Felder erweitern
- [ ] Admin-UI für KI-Farbe/Name
- [ ] Farb-Reservierung bei User-Auswahl

### Phase 3: KI-Kommentar-Assistent
- [ ] Backend: `/comments/{id}/ai-resolve` Endpoint
- [ ] Service: `LatexCommentAiService`
- [ ] Frontend: CommentAiButton Komponente
- [ ] Frontend: useLatexCommentAi Composable

### Phase 4: KI-Änderungen Tracking
- [ ] Editor-Highlighting für KI-Änderungen
- [ ] Git-Panel KI-Änderungen Anzeige
- [ ] `is_ai_generated` Flag für Kommentare

---

## 8. Sicherheitsüberlegungen

### 8.1 Rate Limiting
- Max. 10 KI-Anfragen pro Minute pro User
- Admin kann Limit konfigurieren

### 8.2 Modell-Zugriff
- KI-Feature nutzt Modell-Berechtigungen des Users
- Fallback auf Standard-Modell wenn kein Zugriff

### 8.3 Audit-Log
- Alle KI-Änderungen werden geloggt
- Includes: User, Timestamp, Original-Text, Neuer Text, Kommentar-ID

---

## 9. UX-Überlegungen

### 9.1 Undo-Funktionalität
- KI-Änderungen sind über Yjs-History rückgängig machbar
- "Rückgängig" Button direkt nach KI-Änderung anzeigen

### 9.2 Bestätigungs-Dialog (optional)
- Admin kann einstellen ob vor KI-Änderung bestätigt werden muss
- Zeigt Preview der geplanten Änderung

### 9.3 KI-Qualitätsfeedback
- Thumbs up/down auf KI-Antworten
- Feedback wird für zukünftige Prompt-Optimierung genutzt

---

## Anhang: Mockups

### A1: Kommentar mit KI-Button

```
┌─────────────────────────────────────────────────────────┐
│ 🔵 Max Mustermann                           14:32      │
│ ─────────────────────────────────────────────────────  │
│ Hier sollte noch eine Erklärung zur Methodik stehen.   │
│                                                         │
│ [💬] [✓] [🗑] [🤖]                                      │
└─────────────────────────────────────────────────────────┘

[💬] = Antworten
[✓]  = Erledigen
[🗑] = Löschen
[🤖] = Mit KI umsetzen
```

### A2: Nach KI-Bearbeitung

```
┌─────────────────────────────────────────────────────────┐
│ 🔵 Max Mustermann                           14:32      │
│ ─────────────────────────────────────────────────────  │
│ Hier sollte noch eine Erklärung zur Methodik stehen.   │
│                                                         │
│   └─ 🟣 LLARS KI                            14:33      │
│      Ich habe einen Absatz zur Methodik eingefügt,     │
│      der die experimentelle Vorgehensweise und die     │
│      verwendeten Materialien beschreibt.               │
│                                                         │
│ ✅ Erledigt                                             │
└─────────────────────────────────────────────────────────┘
```

### A3: Resizable Preview Panel

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    PDF VIEWER                           │
│                  (70% - resizable)                      │
│                                                         │
├═══════════════════════ ━━━ ════════════════════════════┤
│                                                         │
│                  COMMENTS PANEL                         │
│                  (30% - resizable)                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
