# Frontend Testanforderungen: Chat & Chatbots

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für das Chat-Interface und den Chatbot-Wizard.

---

## 1. Chat mit Bots (`/chat`)

**Komponente:** `ChatWithBots.vue`
**Priorität:** P1
**Permission:** `feature:chatbots:view`

### Sidebar Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHAT-001 | Seite lädt | Sidebar + Chat-Area | E2E |
| CHAT-002 | Chatbot-Liste | Verfügbare Bots angezeigt | E2E |
| CHAT-003 | Chatbot-Gruppen | Nach Kategorie gruppiert | E2E |
| CHAT-004 | Chatbot-Suche | Filter funktioniert | E2E |
| CHAT-005 | Conversations | Pro Bot mehrere Gespräche | E2E |
| CHAT-006 | Conversation erstellen | Neues Gespräch | E2E |
| CHAT-007 | Conversation löschen | Gespräch entfernt | E2E |
| CHAT-008 | Conversation wechseln | Chat-History wechselt | E2E |
| CHAT-009 | Vision Indicator | Kamera-Icon bei Vision-Bots | E2E |
| CHAT-010 | Bot Capabilities | Fähigkeiten angezeigt | E2E |

### Chat-Interface Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHAT-M01 | Message senden | Nachricht in Chat | E2E |
| CHAT-M02 | Bot antwortet | Antwort erscheint | E2E |
| CHAT-M03 | Streaming | Token-by-Token | E2E |
| CHAT-M04 | Markdown in Antwort | Formatierung rendert | E2E |
| CHAT-M05 | Code Blocks | Syntax Highlighting | E2E |
| CHAT-M06 | Copy Button | Code kopierbar | E2E |
| CHAT-M07 | Scroll to Bottom | Auto-Scroll bei neuer Message | E2E |
| CHAT-M08 | Input Textarea | Mehrzeilig möglich | E2E |
| CHAT-M09 | Enter = Send | Enter sendet Message | E2E |
| CHAT-M10 | Shift+Enter | Neue Zeile im Input | E2E |

### RAG/Source Panel Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHAT-R01 | Sources anzeigen | Quellen-Panel sichtbar | E2E |
| CHAT-R02 | Document Chunks | Relevante Chunks angezeigt | E2E |
| CHAT-R03 | Chunk klickbar | Modal mit Volltext | E2E |
| CHAT-R04 | Screenshot Viewer | Screenshot-Vorschau | E2E |
| CHAT-R05 | Source Ranking | Score/Relevanz angezeigt | E2E |
| CHAT-R06 | No Sources | "Keine Quellen" Hinweis | E2E |

### File Attachment Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHAT-F01 | Attach Button | Upload-Dialog öffnet | E2E |
| CHAT-F02 | Image Upload | Bild wird angezeigt | E2E |
| CHAT-F03 | Image an Bot | Vision-Bot analysiert | E2E |
| CHAT-F04 | PDF Upload | PDF-Icon angezeigt | E2E |
| CHAT-F05 | File Size Limit | Große Files abgelehnt | E2E |
| CHAT-F06 | File Remove | Attachment entfernbar | E2E |

### E2E Test-Code

```typescript
// e2e/chat/chat-with-bots.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Chat with Bots', () => {
  test('CHAT-001: page loads correctly', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat')
    await expect(authenticatedPage.locator('.chatbot-sidebar')).toBeVisible()
    await expect(authenticatedPage.locator('.chat-area')).toBeVisible()
  })

  test('CHAT-M02: bot responds to message', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat')

    // Ersten Chatbot wählen
    await authenticatedPage.click('.chatbot-item >> nth=0')

    // Nachricht senden
    await authenticatedPage.fill('.message-input', 'Hallo, wer bist du?')
    await authenticatedPage.click('button:has-text("Senden")')

    // Bot-Antwort erscheint
    await expect(authenticatedPage.locator('.message.bot')).toBeVisible({
      timeout: 30000
    })
  })

  test('CHAT-M03: streaming works', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat')
    await authenticatedPage.click('.chatbot-item >> nth=0')

    await authenticatedPage.fill('.message-input', 'Erkläre mir Machine Learning in 3 Sätzen.')
    await authenticatedPage.click('button:has-text("Senden")')

    // Prüfe dass Streaming-Indicator erscheint
    await expect(authenticatedPage.locator('.streaming-indicator')).toBeVisible({
      timeout: 5000
    })

    // Warte auf Completion
    await expect(authenticatedPage.locator('.streaming-indicator')).not.toBeVisible({
      timeout: 60000
    })
  })

  test('CHAT-R01: sources panel shows chunks', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/chat')
    await authenticatedPage.click('.chatbot-item >> nth=0')

    // RAG-basierte Frage
    await authenticatedPage.fill('.message-input', 'Was steht in den Dokumenten?')
    await authenticatedPage.click('button:has-text("Senden")')

    // Warte auf Antwort
    await authenticatedPage.waitForSelector('.message.bot', { timeout: 30000 })

    // Sources Panel prüfen
    const sourcesPanel = authenticatedPage.locator('.sources-panel')
    if (await sourcesPanel.isVisible()) {
      await expect(sourcesPanel.locator('.source-chunk')).toHaveCount(1, { min: true })
    }
  })
})
```

---

## 2. Chatbot-Wizard (Admin)

**Komponenten:** `ChatbotManager.vue`, `ChatbotEditor.vue`, Wizard-Komponenten
**Priorität:** P1
**Permissions:** `feature:chatbots:edit`, `feature:chatbots:advanced`

### Wizard-Flow Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-001 | Wizard starten | Step 1 sichtbar | E2E |
| WIZ-002 | Step 1: Name | Name eingeben + validieren | E2E |
| WIZ-003 | Step 2: Beschreibung | Beschreibung eingeben | E2E |
| WIZ-004 | Step 3: Dokumente | Upload oder Crawler | E2E |
| WIZ-005 | Step 3a: Upload | Files hochladen | E2E |
| WIZ-006 | Step 3b: Crawler | URL eingeben + starten | E2E |
| WIZ-007 | Step 4: Embedding | Embedding-Fortschritt | E2E |
| WIZ-008 | Step 5: LLM Config | Model + Params wählen | E2E |
| WIZ-009 | Step 6: Test | Test-Chat funktioniert | E2E |
| WIZ-010 | Finalize | Chatbot fertigstellen | E2E |
| WIZ-011 | Cancel | Wizard abbrechen | E2E |
| WIZ-012 | Resume | Wizard fortsetzen | E2E |

### Document Upload Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-U01 | Drag & Drop | File-Drop funktioniert | E2E |
| WIZ-U02 | Click Upload | File-Dialog öffnet | E2E |
| WIZ-U03 | Multiple Files | Mehrere Files auf einmal | E2E |
| WIZ-U04 | Progress | Upload-Fortschritt | E2E |
| WIZ-U05 | Supported Types | PDF, DOCX, TXT, MD | E2E |
| WIZ-U06 | Unsupported Type | Fehlermeldung | E2E |
| WIZ-U07 | Size Limit | Große Files abgelehnt | E2E |
| WIZ-U08 | File Remove | Vor Embedding entfernbar | E2E |

### Crawler Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-C01 | URL eingeben | URL validiert | E2E |
| WIZ-C02 | Preview | Site-Preview angezeigt | E2E |
| WIZ-C03 | Depth einstellen | Tiefe 1-5 wählbar | E2E |
| WIZ-C04 | Max Pages | Limit einstellbar | E2E |
| WIZ-C05 | Crawl starten | Job startet | E2E |
| WIZ-C06 | Progress | Fortschritt sichtbar | E2E |
| WIZ-C07 | Pages collected | Gefundene Seiten | E2E |
| WIZ-C08 | Crawl abbrechen | Job abbrechbar | E2E |

### Embedding Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-E01 | Embedding startet | Progress Bar | E2E |
| WIZ-E02 | Chunk-Anzeige | Chunks werden gezählt | E2E |
| WIZ-E03 | Embedding fertig | Status "completed" | E2E |
| WIZ-E04 | Embedding Fehler | Fehlermeldung | E2E |
| WIZ-E05 | Model auswählen | Embedding-Model wählbar | E2E |

### LLM Config Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| WIZ-L01 | Model wählen | Dropdown mit Models | E2E |
| WIZ-L02 | Temperature | Slider 0-2 | E2E |
| WIZ-L03 | Max Tokens | Input validiert | E2E |
| WIZ-L04 | System Prompt | Textarea | E2E |
| WIZ-L05 | RAG Config | Top-K, Threshold | E2E |
| WIZ-L06 | Agent Mode | Basic/ReAct/Reflection | E2E |
| WIZ-L07 | Advanced nur mit Permission | Button disabled ohne | E2E |

### E2E Test-Code

```typescript
// e2e/admin/chatbot-wizard.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Chatbot Wizard', () => {
  test('WIZ-001 to WIZ-010: complete wizard flow', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=chatbots')

    // Neuer Chatbot
    await adminPage.click('button:has-text("Neuer Chatbot")')

    // Step 1: Name
    await adminPage.fill('input[name="name"]', 'E2E Test Bot')
    await adminPage.click('button:has-text("Weiter")')

    // Step 2: Beschreibung
    await adminPage.fill('textarea[name="description"]', 'Testbeschreibung')
    await adminPage.click('button:has-text("Weiter")')

    // Step 3: Dokumente (Upload)
    const testFile = 'e2e/fixtures/files/test-document.txt'
    await adminPage.setInputFiles('input[type="file"]', testFile)
    await expect(adminPage.locator('.upload-success')).toBeVisible({ timeout: 30000 })
    await adminPage.click('button:has-text("Weiter")')

    // Step 4: Embedding
    await expect(adminPage.locator('.embedding-progress')).toBeVisible()
    await expect(adminPage.locator('.embedding-complete')).toBeVisible({ timeout: 120000 })
    await adminPage.click('button:has-text("Weiter")')

    // Step 5: LLM Config
    await adminPage.selectOption('select[name="model"]', 'gpt-4o-mini')
    await adminPage.click('button:has-text("Weiter")')

    // Step 6: Test
    await adminPage.fill('.test-input', 'Test-Nachricht')
    await adminPage.click('button:has-text("Testen")')
    await expect(adminPage.locator('.test-response')).toBeVisible({ timeout: 30000 })
    await adminPage.click('button:has-text("Weiter")')

    // Finalize
    await adminPage.click('button:has-text("Fertigstellen")')
    await expect(adminPage.locator('.v-snackbar')).toContainText('erstellt')
  })
})
```

---

## 3. Chatbot-Verwaltung (Admin)

**Komponente:** `ChatbotManager.vue`, `ChatbotEditor.vue`
**Permission:** `feature:chatbots:edit`, `feature:chatbots:delete`, `feature:chatbots:share`

### List & Card Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-001 | Liste lädt | Chatbot-Cards sichtbar | E2E |
| BOT-002 | Eigene Bots | Owner-Filter funktioniert | E2E |
| BOT-003 | Geteilte Bots | Shared-Bots sichtbar | E2E |
| BOT-004 | Status-Badge | draft/published/shared | E2E |
| BOT-005 | Card-Actions | Edit/Delete/Share Buttons | E2E |
| BOT-006 | Search | Suche funktioniert | E2E |

### Editor Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-E01 | Editor öffnen | Config-Form sichtbar | E2E |
| BOT-E02 | Name ändern | Name aktualisiert | E2E |
| BOT-E03 | Beschreibung ändern | Beschreibung aktualisiert | E2E |
| BOT-E04 | LLM ändern | Model wechseln | E2E |
| BOT-E05 | System Prompt | Prompt editierbar | E2E |
| BOT-E06 | Collections | Collections hinzufügen/entfernen | E2E |
| BOT-E07 | Speichern | Änderungen persistiert | E2E |
| BOT-E08 | Löschen | Chatbot entfernt | E2E |

### Sharing Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-S01 | Share Dialog | Dialog öffnet | E2E |
| BOT-S02 | User hinzufügen | User in Liste | E2E |
| BOT-S03 | Rolle hinzufügen | Rolle in Liste | E2E |
| BOT-S04 | Access entfernen | User/Rolle entfernt | E2E |
| BOT-S05 | Sharing speichern | Änderungen persistiert | E2E |
| BOT-S06 | Shared User sieht Bot | Zugriff funktioniert | E2E |

### Test-Chat Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BOT-T01 | Test Dialog | Dialog öffnet | E2E |
| BOT-T02 | Nachricht senden | Bot antwortet | E2E |
| BOT-T03 | Streaming | Token-by-Token | E2E |
| BOT-T04 | Sources | Quellen angezeigt | E2E |
| BOT-T05 | Reset | Konversation zurücksetzen | E2E |

---

## 4. LLM Models (Admin)

**API:** `/api/llm/models`
**Permission:** Admin

### Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLM-001 | Models laden | Liste aller Models | Integration |
| LLM-002 | Default Model | Default markiert | Integration |
| LLM-003 | Model-Typ Filter | llm/embedding/reranker | Integration |
| LLM-004 | Vision Support | Vision-Flag korrekt | Integration |
| LLM-005 | Sync Models | LiteLLM-Sync funktioniert | Integration |

---

## Checkliste für manuelle Tests

### Chat Interface
- [ ] Chatbot-Sidebar zeigt alle zugänglichen Bots
- [ ] Conversation erstellen/löschen/wechseln
- [ ] Nachrichten senden und empfangen
- [ ] Streaming funktioniert flüssig
- [ ] Sources werden angezeigt (wenn RAG)
- [ ] Markdown in Antworten rendert korrekt
- [ ] File-Attachments funktionieren

### Chatbot Wizard
- [ ] Alle Steps durchlaufen
- [ ] Dokument-Upload funktioniert
- [ ] Crawler funktioniert
- [ ] Embedding läuft durch
- [ ] Test-Chat funktioniert
- [ ] Chatbot wird erstellt

### Chatbot Admin
- [ ] Liste zeigt alle Bots
- [ ] Editor speichert Änderungen
- [ ] Sharing funktioniert
- [ ] Löschen funktioniert
- [ ] Collections zuweisbar

---

**Letzte Aktualisierung:** 30. Dezember 2025
