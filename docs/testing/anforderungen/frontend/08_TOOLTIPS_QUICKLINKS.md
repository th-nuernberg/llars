# Frontend Testanforderungen: Tooltips & Quicklinks

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Tests für ALLE Tooltips und Quicklinks in LLARS.

**Tooltips:** 100+ | **Quicklinks:** 20+ | **Keyboard Shortcuts:** 15+

---

## 1. Chat & Chatbot Tooltips

**Datei:** `src/components/ChatWithBots.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-CB01 | Neuer Chat Button | "Neuer Chat" | right | E2E |
| TT-CB02 | Collapse Button | "Erweitern"/"Zuklappen" | dynamic | E2E |
| TT-CB03 | Chatbot Item (collapsed) | Bot-Name | right | E2E |
| TT-CB04 | Umbenennen Button | "Umbenennen" | top | E2E |
| TT-CB05 | Löschen Button | "Löschen" | top | E2E |
| TT-CB06 | Home Link (collapsed) | "Zur Startseite" | right | E2E |
| TT-CB07 | Sources Toggle | "Quellen anzeigen/ausblenden" | bottom | E2E |
| TT-CB08 | Pin Button | "Anheften"/"Lösen" | bottom | E2E |
| TT-CB09 | Close Button | "Schließen" | bottom | E2E |
| TT-CB10 | File Upload | Dynamic (disabled reason) | bottom | E2E |

### Test-Code

```typescript
// e2e/tooltips/chat-tooltips.spec.ts
test('TT-CB01: new chat button tooltip', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/chat')
  await authenticatedPage.locator('[data-test="new-chat-btn"]').hover()
  await expect(authenticatedPage.locator('.v-tooltip')).toContainText('Neuer Chat')
})

test('TT-CB02: collapse button tooltip changes', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/chat')

  // Expanded state
  await authenticatedPage.locator('.collapse-btn').hover()
  await expect(authenticatedPage.locator('.v-tooltip')).toContainText('Zuklappen')

  // Click to collapse
  await authenticatedPage.locator('.collapse-btn').click()

  // Collapsed state
  await authenticatedPage.locator('.collapse-btn').hover()
  await expect(authenticatedPage.locator('.v-tooltip')).toContainText('Erweitern')
})
```

---

## 2. KAIMO Tooltips

**Datei:** `src/components/Kaimo/KaimoPanel.vue`, `KaimoCase.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-KM01 | View Button | "Fall öffnen (User-Ansicht)" | top | E2E |
| TT-KM02 | Edit Button | "Fall bearbeiten" | top | E2E |
| TT-KM03 | Publish Button | "Veröffentlichen" | top | E2E |
| TT-KM04 | Delete Button | "Löschen" | top | E2E |
| TT-KM05 | Nav: Fallakte | "Fallakte" | end | E2E |
| TT-KM06 | Nav: Diagramm | "Diagramm" | end | E2E |
| TT-KM07 | Nav: Bewertung | "Bewertung" | end | E2E |

---

## 3. LaTeX AI Tooltips (mit Shortcuts)

**Datei:** `src/components/LatexCollabAI/ai/AISelectionMenu.vue`

| ID | Element | Tooltip-Text | Shortcut | Test |
|----|---------|--------------|----------|------|
| TT-AI01 | Umformulieren | "Umformulieren (Ctrl+Shift+R)" | Ctrl+Shift+R | E2E |
| TT-AI02 | Erweitern | "Erweitern (Ctrl+Shift+E)" | Ctrl+Shift+E | E2E |
| TT-AI03 | Kürzen | "Kürzen (Ctrl+Shift+K)" | Ctrl+Shift+K | E2E |
| TT-AI04 | Zitat finden | "Zitat finden (Ctrl+Shift+C)" | Ctrl+Shift+C | E2E |
| TT-AI05 | In Chat fragen | "In Chat fragen (Ctrl+Shift+?)" | Ctrl+Shift+? | E2E |
| TT-AI06 | LaTeX prüfen | "LaTeX prüfen (Ctrl+Shift+L)" | Ctrl+Shift+L | E2E |

### Shortcut-Tests

```typescript
// e2e/shortcuts/latex-ai-shortcuts.spec.ts
test('TT-AI01: Ctrl+Shift+R triggers reformulate', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/LatexCollabAI/workspace/1')

  // Select text
  await authenticatedPage.locator('.monaco-editor').click()
  await authenticatedPage.keyboard.press('Control+a')

  // Trigger shortcut
  await authenticatedPage.keyboard.press('Control+Shift+R')

  // AI action should trigger
  await expect(authenticatedPage.locator('.ai-action-indicator')).toBeVisible()
})
```

---

## 4. Admin Tooltips

**Datei:** `src/components/Admin/ChatbotAdmin/*.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-AD01 | Fullscreen Button | "Vollbild öffnen" | bottom | E2E |
| TT-AD02 | Source Chip | Filename | top | E2E |
| TT-AD03 | Icon Suggest | "Icon vorschlagen (LLM)" | top | E2E |
| TT-AD04 | Random Icon | "Zufälliges Icon" | top | E2E |
| TT-AD05 | Upload Error | Error Message | top | E2E |

---

## 5. Markdown/LaTeX Collab Tooltips

**Dateien:** `src/components/MarkdownCollab/*.vue`, `src/components/LatexCollab/*.vue`

### Workspace-Toolbar

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-WS01 | Neues Dokument | "Neues Dokument" | bottom | E2E |
| TT-WS02 | Ordner erstellen | "Ordner erstellen" | bottom | E2E |
| TT-WS03 | Speichern | "Speichern" | bottom | E2E |
| TT-WS04 | Undo | "Rückgängig" | bottom | E2E |
| TT-WS05 | Redo | "Wiederholen" | bottom | E2E |
| TT-WS06 | Kompilieren (LaTeX) | "Kompilieren" | bottom | E2E |
| TT-WS07 | Download PDF | "PDF herunterladen" | bottom | E2E |

### PDF Viewer

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-PDF01 | Zoom Out | "Zoom out" | bottom | E2E |
| TT-PDF02 | Zoom In | "Zoom in" | bottom | E2E |
| TT-PDF03 | Fit Width | "Fit width" | bottom | E2E |

### Git Panel

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-GIT01 | Commit | "Commit" | bottom | E2E |
| TT-GIT02 | Push | "Push" | bottom | E2E |
| TT-GIT03 | Pull | "Pull" | bottom | E2E |
| TT-GIT04 | History | "Historie" | bottom | E2E |
| TT-GIT05 | Diff View | "Änderungen anzeigen" | bottom | E2E |

---

## 6. Evaluation Tooltips

**Datei:** `src/components/Rater/RaterDetail.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-EV01 | Progress Chip | "Bewertete Features / Gesamtfeatures" | bottom | E2E |

**Datei:** `src/components/Evaluation/EvaluationHub.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-EV02 | Feature Card (disabled) | "Keine Szenarien zugewiesen" | top | E2E |

---

## 7. Anonymize Tooltips

**Datei:** `src/components/Anonymize/AnonymizeTool.vue`

| ID | Element | Tooltip-Text | Position | Test |
|----|---------|--------------|----------|------|
| TT-AN01 | Info Button | (LInfoTooltip Content) | bottom | E2E |
| TT-AN02 | Health Chip | Health Status | bottom | E2E |
| TT-AN03 | Settings Button | "Einstellungen" | bottom | E2E |

---

## 8. Quicklinks

### Home Dashboard

| ID | Element | Ziel | Test |
|----|---------|------|------|
| QL-01 | Ranking-Kachel | /Ranker | E2E |
| QL-02 | Rating-Kachel | /Rater | E2E |
| QL-03 | Chat-Kachel | /chat | E2E |
| QL-04 | Markdown-Kachel | /MarkdownCollab | E2E |
| QL-05 | LaTeX-Kachel | /LatexCollab | E2E |
| QL-06 | Judge-Kachel | /Judge | E2E |
| QL-07 | OnCoCo-Kachel | /OnCoCo | E2E |
| QL-08 | KAIMO-Kachel | /Kaimo | E2E |
| QL-09 | Anonymize-Kachel | /Anonymize | E2E |
| QL-10 | Admin-Kachel | /admin | E2E |

### AppBar

| ID | Element | Ziel/Aktion | Test |
|----|---------|-------------|------|
| QL-11 | Logo | /Home | E2E |
| QL-12 | Home Icon | /Home | E2E |
| QL-13 | User Menu | Öffnet Dropdown | E2E |
| QL-14 | Settings | Öffnet Dialog | E2E |
| QL-15 | Logout | /login | E2E |

### Sidebar

| ID | Element | Ziel/Aktion | Test |
|----|---------|-------------|------|
| QL-16 | Home Link | /Home | E2E |
| QL-17 | Sidebar Items | Jeweilige Seite | E2E |
| QL-18 | Collapse Toggle | Klappt Sidebar | E2E |

### Test-Code

```typescript
// e2e/quicklinks/home-quicklinks.spec.ts
test('QL-01: ranking tile navigates to /Ranker', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/Home')
  await authenticatedPage.click('[data-test="tile-ranking"]')
  await expect(authenticatedPage).toHaveURL(/.*Ranker/)
})

test('QL-10: admin tile navigates to /admin', async ({ adminPage }) => {
  await adminPage.goto('/Home')
  await adminPage.click('[data-test="tile-admin"]')
  await expect(adminPage).toHaveURL(/.*admin/)
})

test('QL-15: logout navigates to /login', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/Home')
  await authenticatedPage.click('[data-test="user-menu"]')
  await authenticatedPage.click('[data-test="logout-btn"]')
  await expect(authenticatedPage).toHaveURL(/.*login/)
})
```

---

## 9. Keyboard Shortcuts (Global)

### Editor Shortcuts

| ID | Shortcut | Aktion | Kontext | Test |
|----|----------|--------|---------|------|
| KS-01 | Ctrl+S | Speichern | Markdown/LaTeX Editor | E2E |
| KS-02 | Ctrl+Z | Undo | Alle Editoren | E2E |
| KS-03 | Ctrl+Y | Redo | Alle Editoren | E2E |
| KS-04 | Ctrl+Shift+S | Speichern als... | LaTeX | E2E |
| KS-05 | Ctrl+B | Kompilieren | LaTeX | E2E |

### AI Shortcuts (LaTeX AI)

| ID | Shortcut | Aktion | Test |
|----|----------|--------|------|
| KS-06 | Ctrl+Shift+R | Umformulieren | E2E |
| KS-07 | Ctrl+Shift+E | Erweitern | E2E |
| KS-08 | Ctrl+Shift+K | Kürzen | E2E |
| KS-09 | Ctrl+Shift+C | Zitat finden | E2E |
| KS-10 | Ctrl+Shift+? | In Chat fragen | E2E |
| KS-11 | Ctrl+Shift+L | LaTeX prüfen | E2E |

### Chat Shortcuts

| ID | Shortcut | Aktion | Test |
|----|----------|--------|------|
| KS-12 | Enter | Nachricht senden | E2E |
| KS-13 | Shift+Enter | Neue Zeile | E2E |
| KS-14 | Escape | Input leeren/Dialog schließen | E2E |

### Navigation Shortcuts

| ID | Shortcut | Aktion | Test |
|----|----------|--------|------|
| KS-15 | Tab | Nächstes Element fokussieren | A11y |

---

## 10. Tooltip Timing Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TT-TM01 | openDelay 300ms | Tooltip nach 300ms | E2E |
| TT-TM02 | openDelay 0ms | Tooltip sofort | E2E |
| TT-TM03 | closeDelay 0ms | Tooltip verschwindet sofort | E2E |
| TT-TM04 | Hover-then-leave | Tooltip verschwindet | E2E |
| TT-TM05 | Quick hover | Kein Tooltip (zu schnell) | E2E |

### Test-Code

```typescript
// e2e/tooltips/timing.spec.ts
test('TT-TM01: tooltip shows after 300ms delay', async ({ page }) => {
  await page.goto('/component-test')
  const element = page.locator('[data-tooltip="Test"]')

  await element.hover()

  // Immediately after hover, no tooltip
  await expect(page.locator('.v-tooltip')).not.toBeVisible()

  // After 300ms, tooltip appears
  await page.waitForTimeout(350)
  await expect(page.locator('.v-tooltip')).toBeVisible()
})

test('TT-TM05: quick hover shows no tooltip', async ({ page }) => {
  await page.goto('/component-test')
  const element = page.locator('[data-tooltip="Test"]')

  await element.hover()
  await page.waitForTimeout(100) // Less than delay
  await element.blur()

  await expect(page.locator('.v-tooltip')).not.toBeVisible()
})
```

---

## 11. Tooltip Content Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TT-CT01 | Kurzer Text | Einzeilig | Visual |
| TT-CT02 | Langer Text | Multiline/Wrap | Visual |
| TT-CT03 | HTML Content | Gerendert | Visual |
| TT-CT04 | Icons im Tooltip | Angezeigt | Visual |
| TT-CT05 | Leerer Text | Kein Tooltip | E2E |

---

## 12. Checkliste für manuelle Tests

### Tooltips prüfen
- [ ] Alle Chat-Tooltips erscheinen
- [ ] Alle Admin-Tooltips erscheinen
- [ ] Alle Editor-Tooltips erscheinen
- [ ] Tooltip-Position korrekt
- [ ] Tooltip-Timing korrekt
- [ ] Dynamische Tooltips aktualisieren

### Quicklinks prüfen
- [ ] Alle Home-Kacheln verlinken korrekt
- [ ] AppBar-Links funktionieren
- [ ] Sidebar-Links funktionieren
- [ ] Breadcrumbs funktionieren

### Shortcuts prüfen
- [ ] Ctrl+S speichert
- [ ] Ctrl+Z macht rückgängig
- [ ] Enter sendet Chat
- [ ] Shift+Enter neue Zeile
- [ ] AI-Shortcuts funktionieren

---

**Letzte Aktualisierung:** 30. Dezember 2025
