# Frontend Testanforderungen: Kollaborative Editoren

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für den kollaborativen Markdown-Editor (Markdown Collab).

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

## 2. User Settings: Collab-Farbe ändern

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

### Collab-Farbe
- [ ] Farbe änderbar in Settings
- [ ] Farbe wird in Collab-Session angezeigt
- [ ] Avatar änderbar (max 3x/Tag)

---

**Letzte Aktualisierung:** 30. Dezember 2025
