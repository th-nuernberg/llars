# Frontend Testanforderungen: Kollaborative Editoren

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die kollaborativen Editoren: Markdown Collab, LaTeX Collab, LaTeX Collab AI.

---

## 1. Markdown Collab (`/MarkdownCollab`)

**Komponenten:** `MarkdownCollabHome.vue`, `MarkdownCollabWorkspace.vue`
**Priorität:** P1
**Permissions:** `feature:markdown_collab:view`, `feature:markdown_collab:edit`, `feature:markdown_collab:share`

### Home Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MD-001 | Home lädt | Workspace-Liste sichtbar | E2E |
| MD-002 | Eigene Workspaces | Owner-Workspaces angezeigt | E2E |
| MD-003 | Geteilte Workspaces | Shared-Workspaces angezeigt | E2E |
| MD-004 | Neuer Workspace | Dialog öffnet | E2E |
| MD-005 | Workspace erstellen | Workspace in DB | E2E |
| MD-006 | Workspace löschen | Workspace entfernt | E2E |
| MD-007 | Workspace-Card | Metadata korrekt | E2E |
| MD-008 | Workspace öffnen | Editor lädt | E2E |

### Workspace Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MD-W01 | Workspace lädt | Editor + Preview sichtbar | E2E |
| MD-W02 | Document Tree | Dateiliste links | E2E |
| MD-W03 | Document erstellen | Neues Dokument in Tree | E2E |
| MD-W04 | Document umbenennen | Name aktualisiert | E2E |
| MD-W05 | Document löschen | Dokument entfernt | E2E |
| MD-W06 | Document wechseln | Editor wechselt Inhalt | E2E |
| MD-W07 | Ordner erstellen | Ordner in Tree | E2E |
| MD-W08 | Member hinzufügen | User hat Zugriff | E2E |
| MD-W09 | Member entfernen | User verliert Zugriff | E2E |
| MD-W10 | Workspace verlassen | Redirect zu Home | E2E |

### Editor Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MD-E01 | Text eingeben | Text erscheint | E2E |
| MD-E02 | Markdown formatieren | **bold**, *italic* funktioniert | E2E |
| MD-E03 | Preview aktualisiert | Live-Preview rendert | E2E |
| MD-E04 | Code-Block | Syntax Highlighting | E2E |
| MD-E05 | Link einfügen | Link klickbar in Preview | E2E |
| MD-E06 | Bild einfügen | Bild in Preview | E2E |
| MD-E07 | Tabelle | Tabelle rendert korrekt | E2E |
| MD-E08 | Heading | Überschriften-Hierarchie | E2E |
| MD-E09 | Undo/Redo | Ctrl+Z/Ctrl+Y funktioniert | E2E |
| MD-E10 | Auto-Save | Änderungen gespeichert | E2E |

### Collaboration Tests (YJS)

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MD-Y01 | Zwei User verbinden | Beide sehen Editor | E2E |
| MD-Y02 | Text synct | User B sieht User A Eingabe | E2E |
| MD-Y03 | Cursor Awareness | Remote Cursor sichtbar | E2E |
| MD-Y04 | User-Farbe | Collab-Farbe korrekt | E2E |
| MD-Y05 | Gleichzeitige Eingabe | Kein Conflict, CRDT merge | E2E |
| MD-Y06 | Reconnection | Nach Disconnect sync | E2E |
| MD-Y07 | Offline Eingabe | Nach Reconnect synct | E2E |
| MD-Y08 | User verlässt | Cursor verschwindet | E2E |

### E2E Test-Code (Multi-User)

```typescript
// e2e/collaboration/markdown-collab.spec.ts
import { test, expect } from '@playwright/test'
import { testUsers, login } from '../fixtures/auth'

test.describe('Markdown Collaboration', () => {
  test('MD-Y02: real-time sync between users', async ({ browser }) => {
    // User A Context
    const contextA = await browser.newContext()
    const pageA = await contextA.newPage()
    await login(pageA, testUsers.researcher)

    // User B Context
    const contextB = await browser.newContext()
    const pageB = await contextB.newPage()
    await login(pageB, testUsers.admin)

    // Beide öffnen gleichen Workspace
    await pageA.goto('/MarkdownCollab/workspace/1')
    await pageB.goto('/MarkdownCollab/workspace/1')

    // User A tippt
    await pageA.locator('.editor').type('Hello from User A')

    // User B sieht es
    await expect(pageB.locator('.editor')).toContainText('Hello from User A', {
      timeout: 5000
    })

    await contextA.close()
    await contextB.close()
  })

  test('MD-Y03: cursor awareness', async ({ browser }) => {
    const contextA = await browser.newContext()
    const pageA = await contextA.newPage()
    await login(pageA, testUsers.researcher)

    const contextB = await browser.newContext()
    const pageB = await contextB.newPage()
    await login(pageB, testUsers.admin)

    await pageA.goto('/MarkdownCollab/workspace/1')
    await pageB.goto('/MarkdownCollab/workspace/1')

    // User A klickt in Editor
    await pageA.locator('.editor').click()

    // User B sieht Remote Cursor
    await expect(pageB.locator('.remote-cursor')).toBeVisible({
      timeout: 5000
    })

    await contextA.close()
    await contextB.close()
  })
})
```

---

## 2. LaTeX Collab (`/LatexCollab`)

**Komponenten:** `LatexCollabHome.vue`, `LatexCollabWorkspace.vue`
**Priorität:** P1
**Permissions:** `feature:latex_collab:view`, `feature:latex_collab:edit`, `feature:latex_collab:share`

### Home Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-001 | Home lädt | Workspace-Liste sichtbar | E2E |
| LTX-002 | Neuer Workspace | Dialog mit Template-Wahl | E2E |
| LTX-003 | Template wählen | Workspace mit Template | E2E |
| LTX-004 | Workspace-Card | PDF-Preview Thumbnail | E2E |
| LTX-005 | Workspace öffnen | Editor + PDF-Preview | E2E |

### Workspace Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-W01 | Workspace lädt | Editor + PDF sichtbar | E2E |
| LTX-W02 | File Tree | .tex Dateien links | E2E |
| LTX-W03 | Main Document | Haupt-.tex markiert | E2E |
| LTX-W04 | Main wechseln | Kompilierung nutzt neue Main | E2E |
| LTX-W05 | File erstellen | .tex/.bib/.sty erstellbar | E2E |
| LTX-W06 | File umbenennen | Name aktualisiert | E2E |
| LTX-W07 | File löschen | File entfernt | E2E |
| LTX-W08 | Asset hochladen | Bild hochladbar | E2E |
| LTX-W09 | Asset referenzieren | \includegraphics funktioniert | E2E |
| LTX-W10 | Member verwalten | Wie Markdown Collab | E2E |

### Editor Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-E01 | LaTeX eingeben | Syntax Highlighting | E2E |
| LTX-E02 | Commands | \section, \textbf, etc. | E2E |
| LTX-E03 | Math Mode | $...$ rendert | E2E |
| LTX-E04 | Environments | \begin{} \end{} | E2E |
| LTX-E05 | Auto-Complete | Command-Vorschläge | E2E |
| LTX-E06 | Error Markers | Fehler markiert | E2E |
| LTX-E07 | Line Numbers | Zeilennummern sichtbar | E2E |
| LTX-E08 | Undo/Redo | Funktioniert | E2E |

### Kompilierung Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-C01 | Kompilieren Button | Kompilierung startet | E2E |
| LTX-C02 | Progress Indicator | Loading angezeigt | E2E |
| LTX-C03 | PDF generiert | PDF in Preview | E2E |
| LTX-C04 | PDF Download | PDF downloadbar | E2E |
| LTX-C05 | Compile Errors | Fehlermeldungen angezeigt | E2E |
| LTX-C06 | Error Navigation | Klick → Zeile im Editor | E2E |
| LTX-C07 | Biber/BibTeX | Literaturverzeichnis generiert | E2E |
| LTX-C08 | Multiple Runs | Referenzen aufgelöst | E2E |
| LTX-C09 | SyncTeX Forward | Klick Editor → PDF springt | E2E |
| LTX-C10 | SyncTeX Inverse | Klick PDF → Editor springt | E2E |

### PDF Preview Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTX-P01 | PDF lädt | Seiten sichtbar | E2E |
| LTX-P02 | Zoom | Zoom +/- funktioniert | E2E |
| LTX-P03 | Seiten-Navigation | Seite wechseln | E2E |
| LTX-P04 | Fit to Width | Breitenanpassung | E2E |
| LTX-P05 | Scrolling | Smooth Scroll | E2E |
| LTX-P06 | Thumbnail Nav | Seiten-Thumbnails | E2E |

### E2E Test-Code (Kompilierung)

```typescript
// e2e/collaboration/latex-compile.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('LaTeX Compilation', () => {
  test('LTX-C03: compile generates PDF', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollab/workspace/1')

    // Compile Button klicken
    await authenticatedPage.click('button:has-text("Kompilieren")')

    // Warten auf PDF (max 60s für große Dokumente)
    await expect(authenticatedPage.locator('.pdf-viewer')).toBeVisible({
      timeout: 60000
    })

    // PDF hat Inhalt
    await expect(authenticatedPage.locator('.pdf-page')).toHaveCount(1, { min: true })
  })

  test('LTX-C05: compile errors displayed', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollab/workspace/1')

    // Ungültiges LaTeX eingeben
    await authenticatedPage.locator('.editor').fill('\\invalidcommand')
    await authenticatedPage.click('button:has-text("Kompilieren")')

    // Error Panel sichtbar
    await expect(authenticatedPage.locator('.compile-errors')).toBeVisible({
      timeout: 60000
    })
  })
})
```

---

## 3. LaTeX Collab AI (`/LatexCollabAI`)

**Komponenten:** `LatexCollabAIHome.vue`, `LatexCollabAIWorkspace.vue`, `AISidebar.vue`
**Priorität:** P1
**Permissions:** `feature:latex_collab:view`, `feature:latex_collab:edit`, `feature:latex_collab:ai`

### AI Features Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTXAI-001 | Beta Banner | Experimentell-Hinweis | E2E |
| LTXAI-002 | AI Sidebar | Chat-Panel rechts | E2E |
| LTXAI-003 | Ghost Text | Vorschläge erscheinen | E2E |
| LTXAI-004 | Ghost akzeptieren | Tab → Text eingefügt | E2E |
| LTXAI-005 | Ghost ablehnen | Esc → Text verschwindet | E2E |
| LTXAI-006 | @-Commands | @expand, @summarize, etc. | E2E |
| LTXAI-007 | Selection Menu | Rechtsklick → AI Actions | E2E |
| LTXAI-008 | Rewrite Selection | Text umgeschrieben | E2E |
| LTXAI-009 | Expand Selection | Text erweitert | E2E |
| LTXAI-010 | Summarize Selection | Text zusammengefasst | E2E |

### AI Chat Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTXAI-C01 | Chat öffnen | Sidebar sichtbar | E2E |
| LTXAI-C02 | Nachricht senden | AI antwortet | E2E |
| LTXAI-C03 | Streaming | Token-by-Token | E2E |
| LTXAI-C04 | Code-Insertion | "Einfügen" Button | E2E |
| LTXAI-C05 | Context aware | AI kennt Dokument | E2E |
| LTXAI-C06 | Chat History | Verlauf gespeichert | E2E |

### Citation Features Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LTXAI-Z01 | Zitation suchen | @cite → Suche | E2E |
| LTXAI-Z02 | Ergebnisse anzeigen | Paper-Liste | E2E |
| LTXAI-Z03 | Zitation einfügen | \cite{key} eingefügt | E2E |
| LTXAI-Z04 | BibTeX generiert | Eintrag in .bib | E2E |
| LTXAI-Z05 | DOI Lookup | DOI → Vollständiger Eintrag | E2E |

### E2E Test-Code (AI Features)

```typescript
// e2e/collaboration/latex-ai.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('LaTeX AI Features', () => {
  test('LTXAI-003: ghost text appears', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollabAI/workspace/1')

    // Am Ende einer Zeile stoppen
    await authenticatedPage.locator('.editor').click()
    await authenticatedPage.keyboard.type('\\section{Introduction}')
    await authenticatedPage.keyboard.press('Enter')

    // Warten auf Ghost Text (grauer Vorschlag)
    await expect(authenticatedPage.locator('.ghost-text')).toBeVisible({
      timeout: 10000
    })
  })

  test('LTXAI-C02: AI chat responds', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/LatexCollabAI/workspace/1')

    // Sidebar öffnen
    await authenticatedPage.click('[data-testid="ai-sidebar-toggle"]')

    // Nachricht senden
    await authenticatedPage.fill('.chat-input', 'Erkläre den Abstract')
    await authenticatedPage.click('button:has-text("Senden")')

    // Antwort erscheint
    await expect(authenticatedPage.locator('.chat-message.ai')).toBeVisible({
      timeout: 30000
    })
  })
})
```

---

## 4. User Settings: Collab-Farbe ändern

**Komponente:** User Settings Dialog
**API:** `PATCH /api/users/me/settings`

### Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| COLOR-001 | Settings öffnen | Color Picker sichtbar | E2E |
| COLOR-002 | Farbe wählen | Neue Farbe selektiert | E2E |
| COLOR-003 | Speichern | API-Call erfolgreich | E2E |
| COLOR-004 | Farbe persistent | Nach Reload gleiche Farbe | E2E |
| COLOR-005 | In Collab sichtbar | Remote Cursor hat neue Farbe | E2E |
| COLOR-006 | Avatar-Änderung | Neuer Avatar generierbar | E2E |
| COLOR-007 | Avatar-Limit | Max 3 Änderungen/Tag | E2E |

### E2E Test-Code

```typescript
// e2e/user/settings.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('User Settings', () => {
  test('COLOR-003: change collab color', async ({ authenticatedPage }) => {
    // User Menu öffnen
    await authenticatedPage.click('[data-testid="user-menu"]')
    await authenticatedPage.click('text=Einstellungen')

    // Color Picker
    const colorInput = authenticatedPage.locator('input[type="color"]')
    await colorInput.fill('#FF5733')

    // Speichern
    await authenticatedPage.click('button:has-text("Speichern")')

    // Success
    await expect(authenticatedPage.locator('.v-snackbar')).toContainText('gespeichert')
  })
})
```

---

## Checkliste für manuelle Tests

### Markdown Collab
- [ ] Workspace erstellen/löschen
- [ ] Dokumente erstellen/bearbeiten/löschen
- [ ] Ordner-Struktur
- [ ] Member hinzufügen/entfernen
- [ ] Multi-User Sync (2+ Browser)
- [ ] Cursor Awareness sichtbar
- [ ] Offline-Eingabe synct nach Reconnect
- [ ] Preview rendert korrekt

### LaTeX Collab
- [ ] Workspace mit Template erstellen
- [ ] .tex Dateien erstellen/bearbeiten
- [ ] Bilder hochladen & referenzieren
- [ ] Kompilierung startet & PDF generiert
- [ ] Fehler werden angezeigt
- [ ] SyncTeX Forward/Inverse
- [ ] BibTeX/Biber funktioniert
- [ ] Multi-User Sync

### LaTeX AI
- [ ] Ghost Text erscheint & akzeptierbar
- [ ] @-Commands funktionieren
- [ ] Selection Menu erscheint
- [ ] AI Chat antwortet
- [ ] Code-Insertion funktioniert
- [ ] Zitations-Suche funktioniert

### Collab-Farbe
- [ ] Farbe änderbar in Settings
- [ ] Farbe wird in Collab-Session angezeigt
- [ ] Avatar änderbar (max 3x/Tag)

---

**Letzte Aktualisierung:** 30. Dezember 2025
