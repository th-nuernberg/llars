# Frontend Testanforderungen: Edge Cases & Error States

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Tests für Edge Cases, Error States und ungewöhnliche Szenarien.

**Kategorien:** Empty States | Error Handling | Limits | Network | Browser

---

## 1. Empty States

### Listen & Tabellen

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| ES-01 | Keine Chatbots | Chatbot-Liste | "Keine Chatbots" + Icon | E2E |
| ES-02 | Keine Dokumente | RAG Dokumente | "Keine Dokumente" + Upload-Button | E2E |
| ES-03 | Keine Collections | Collection-Liste | "Keine Collections" + Create-Button | E2E |
| ES-04 | Keine Szenarien | Szenario-Liste | "Keine Szenarien zugewiesen" | E2E |
| ES-05 | Keine Messages | Chat-Verlauf | Welcome Message | E2E |
| ES-06 | Keine Sources | Source-Panel | "Keine Quellen gefunden" | E2E |
| ES-07 | Keine Threads | Ranker/Rater | "Keine Threads" | E2E |
| ES-08 | Keine User | User-Suche | "Keine User gefunden" | E2E |
| ES-09 | Leeres Workspace | Markdown/LaTeX | "Kein Dokument ausgewählt" | E2E |
| ES-10 | Keine Hints | KAIMO Hints | "Keine Hints in dieser Kategorie" | E2E |

### Daten-Visualisierung

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| ES-11 | Leeres Chart | LChart | "Keine Daten" | Visual |
| ES-12 | Null-Werte | LGauge | "0" oder "-" | Visual |
| ES-13 | Keine Stats | Admin Stats | Placeholder-Werte | E2E |

### Test-Code

```typescript
// e2e/edge-cases/empty-states.spec.ts
test('ES-01: empty chatbot list shows message', async ({ page }) => {
  // Mock empty response
  await page.route('/api/chatbots', route => {
    route.fulfill({ json: { chatbots: [] } })
  })

  await page.goto('/chat')
  await expect(page.locator('.empty-state')).toContainText('Keine Chatbots')
})

test('ES-05: new chat shows welcome message', async ({ page }) => {
  await page.goto('/chat')
  await page.click('.chatbot-item >> nth=0')
  await page.click('[data-test="new-chat"]')

  await expect(page.locator('.welcome-message')).toBeVisible()
})
```

---

## 2. Error States

### API Errors

| ID | Test | Status | Erwartung | Art |
|----|------|--------|-----------|-----|
| ERR-01 | 400 Bad Request | Validation | Fehlermeldung anzeigen | E2E |
| ERR-02 | 401 Unauthorized | Auth | Redirect zu /login | E2E |
| ERR-03 | 403 Forbidden | Permission | "Keine Berechtigung" | E2E |
| ERR-04 | 404 Not Found | Resource | "Nicht gefunden" | E2E |
| ERR-05 | 409 Conflict | Duplicate | "Bereits vorhanden" | E2E |
| ERR-06 | 413 Payload Too Large | Upload | "Datei zu groß" | E2E |
| ERR-07 | 429 Too Many Requests | Rate Limit | "Zu viele Anfragen" | E2E |
| ERR-08 | 500 Server Error | Server | "Serverfehler" | E2E |
| ERR-09 | 503 Unavailable | Maintenance | "Nicht verfügbar" | E2E |
| ERR-10 | Network Error | Offline | "Netzwerkfehler" | E2E |

### Form Validation

| ID | Test | Field | Erwartung | Art |
|----|------|-------|-----------|-----|
| ERR-V01 | Leeres Required-Feld | Alle | "Pflichtfeld" | E2E |
| ERR-V02 | Ungültige Email | Email | "Ungültige E-Mail" | E2E |
| ERR-V03 | Passwort zu kurz | Passwort | "Min. 8 Zeichen" | E2E |
| ERR-V04 | Ungültige URL | URL-Input | "Ungültige URL" | E2E |
| ERR-V05 | Zahl außerhalb Range | Number | "Zwischen X und Y" | E2E |
| ERR-V06 | Ungültiges JSON | JSON-Feld | "Ungültiges JSON" | E2E |

### Upload Errors

| ID | Test | Ursache | Erwartung | Art |
|----|------|---------|-----------|-----|
| ERR-U01 | Falscher Dateityp | .exe | "Nicht unterstützt" | E2E |
| ERR-U02 | Zu große Datei | >50MB | "Max 50MB" | E2E |
| ERR-U03 | Korrupte Datei | Beschädigt | "Datei fehlerhaft" | E2E |
| ERR-U04 | Upload abgebrochen | Netzwerk | "Upload fehlgeschlagen" | E2E |
| ERR-U05 | Quota erreicht | Server voll | "Speicher voll" | E2E |

### Test-Code

```typescript
// e2e/edge-cases/error-states.spec.ts
test('ERR-01: 400 error shows validation message', async ({ page }) => {
  await page.route('/api/chatbots', route => {
    route.fulfill({
      status: 400,
      json: { error: 'Name ist erforderlich' }
    })
  })

  await page.goto('/admin?tab=chatbots')
  await page.click('[data-test="create-chatbot"]')
  await page.click('[data-test="save"]')

  await expect(page.locator('.v-snackbar')).toContainText('Name ist erforderlich')
})

test('ERR-02: 401 redirects to login', async ({ page }) => {
  await page.route('/api/users/me', route => {
    route.fulfill({ status: 401 })
  })

  await page.goto('/Home')
  await expect(page).toHaveURL(/.*login/)
})

test('ERR-10: network error shows message', async ({ page }) => {
  await page.goto('/Home')

  // Simulate offline
  await page.route('/api/**', route => route.abort('failed'))

  await page.click('.chatbot-item >> nth=0')
  await page.fill('.message-input', 'Test')
  await page.click('[data-test="send"]')

  await expect(page.locator('.error-message')).toContainText('Netzwerk')
})
```

---

## 3. Limits & Boundaries

### Text Limits

| ID | Test | Field | Limit | Erwartung | Art |
|----|------|-------|-------|-----------|-----|
| LIM-01 | Sehr langer Username | Login | 255 chars | Akzeptiert oder Error | E2E |
| LIM-02 | Sehr langer Chat-Text | Chat | 10000 chars | Akzeptiert | E2E |
| LIM-03 | Sehr lange Prompt | Prompt | 50000 chars | Akzeptiert | E2E |
| LIM-04 | Leerer Text | Diverse | 0 chars | Validation Error | E2E |
| LIM-05 | Nur Whitespace | Diverse | " " | Validation Error | E2E |

### Numerische Limits

| ID | Test | Field | Wert | Erwartung | Art |
|----|------|-------|------|-----------|-----|
| LIM-N01 | Slider Min | Temperature | 0 | Akzeptiert | E2E |
| LIM-N02 | Slider Max | Temperature | 2 | Akzeptiert | E2E |
| LIM-N03 | Unter Min | Max Tokens | -1 | Auf Min setzen | E2E |
| LIM-N04 | Über Max | Max Tokens | 999999 | Auf Max setzen | E2E |
| LIM-N05 | Dezimal | Top-K | 3.5 | Auf Integer runden | E2E |
| LIM-N06 | NaN | Diverse | "abc" | Validation Error | E2E |

### Collection Limits

| ID | Test | Element | Limit | Erwartung | Art |
|----|------|---------|-------|-----------|-----|
| LIM-C01 | Max Dokumente | Collection | 1000 | Warnung oder Limit | E2E |
| LIM-C02 | Max Collections pro Chatbot | Chatbot | 10 | Warnung | E2E |
| LIM-C03 | Max Chunks pro Dokument | Dokument | 10000 | Verarbeitet | E2E |

### Test-Code

```typescript
// e2e/edge-cases/limits.spec.ts
test('LIM-01: very long username', async ({ page }) => {
  await page.goto('/login')
  const longUsername = 'a'.repeat(256)
  await page.fill('input[name="username"]', longUsername)
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')

  // Should either accept (if <= 255) or show error
  const hasError = await page.locator('.v-input--error').isVisible()
  const isRedirected = await page.url().includes('/Home')
  expect(hasError || isRedirected).toBe(true)
})

test('LIM-N03: slider below min resets to min', async ({ page }) => {
  await page.goto('/admin?tab=chatbots')
  await page.click('.chatbot-item >> nth=0')

  // Try to set temperature to -1
  await page.fill('input[name="temperature"]', '-1')
  await page.keyboard.press('Tab')

  const value = await page.inputValue('input[name="temperature"]')
  expect(parseFloat(value)).toBeGreaterThanOrEqual(0)
})
```

---

## 4. Spezialzeichen & Encoding

### Text mit Spezialzeichen

| ID | Test | Input | Erwartung | Art |
|----|------|-------|-----------|-----|
| CHAR-01 | HTML Tags | `<script>alert(1)</script>` | Escaped anzeigen | E2E |
| CHAR-02 | Umlaute | "Größe: äöüß" | Korrekt anzeigen | E2E |
| CHAR-03 | Emoji | "Test 🚀 Emoji" | Korrekt anzeigen | E2E |
| CHAR-04 | Unicode | "中文 العربية" | Korrekt anzeigen | E2E |
| CHAR-05 | Newlines | "Zeile1\nZeile2" | Multiline | E2E |
| CHAR-06 | Tabs | "Text\tTab" | Mit Tab | E2E |
| CHAR-07 | SQL Injection | `'; DROP TABLE users; --` | Kein Effekt | Security |
| CHAR-08 | XSS | `<img onerror=alert(1)>` | Escaped | Security |

### Dateinamen

| ID | Test | Filename | Erwartung | Art |
|----|------|----------|-----------|-----|
| FILE-01 | Leerzeichen | "my file.pdf" | Upload funktioniert | E2E |
| FILE-02 | Umlaute | "größe.pdf" | Upload funktioniert | E2E |
| FILE-03 | Spezialzeichen | "file#1(2).pdf" | Upload funktioniert | E2E |
| FILE-04 | Sehr lang | "a".repeat(200) + ".pdf" | Fehler oder Truncate | E2E |
| FILE-05 | Hidden files | ".hidden.pdf" | Upload funktioniert | E2E |

---

## 5. Network Edge Cases

### Slow Network

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| NET-01 | Slow API (5s) | Login | Loading-Indicator | E2E |
| NET-02 | Slow Upload | Dokument | Progress angezeigt | E2E |
| NET-03 | Slow LLM (30s) | Chat | Streaming zeigt Fortschritt | E2E |
| NET-04 | Timeout (60s) | API Call | Timeout-Error | E2E |

### Disconnection

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| NET-05 | WebSocket disconnect | Chat | Reconnect-Versuch | E2E |
| NET-06 | Offline während Upload | Upload | Error + Retry Option | E2E |
| NET-07 | Offline während Save | Formular | Error + Lokale Speicherung | E2E |
| NET-08 | Reconnect | Nach Offline | Automatischer Sync | E2E |

### Test-Code

```typescript
// e2e/edge-cases/network.spec.ts
test('NET-01: slow API shows loading', async ({ page }) => {
  await page.route('/auth/authentik/login', async route => {
    await page.waitForTimeout(3000) // 3s delay
    await route.fulfill({ json: { access_token: 'token' } })
  })

  await page.goto('/login')
  await page.fill('input[name="username"]', 'admin')
  await page.fill('input[name="password"]', 'admin123')
  await page.click('button[type="submit"]')

  // Loading indicator should appear
  await expect(page.locator('.v-progress-circular')).toBeVisible()
})

test('NET-05: websocket reconnects', async ({ page }) => {
  await page.goto('/chat')
  await page.click('.chatbot-item >> nth=0')

  // Simulate disconnect
  await page.evaluate(() => {
    window.dispatchEvent(new Event('offline'))
  })

  // Wait for reconnect attempt
  await page.waitForTimeout(2000)

  // Simulate reconnect
  await page.evaluate(() => {
    window.dispatchEvent(new Event('online'))
  })

  // Should show reconnected
  await expect(page.locator('.connection-status')).not.toContainText('Offline')
})
```

---

## 6. Browser Edge Cases

### Verschiedene Zustände

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| BRW-01 | Refresh während Upload | Upload | Warnung vor Verlassen | E2E |
| BRW-02 | Back-Button | Dialog offen | Dialog schließt | E2E |
| BRW-03 | Forward-Button | Nach Back | Navigation funktioniert | E2E |
| BRW-04 | Mehrere Tabs | Gleicher User | Session-Sync | E2E |
| BRW-05 | Tab schließen | Unsaved Changes | Warnung | E2E |
| BRW-06 | Browser-Zoom | 50%-200% | Layout intakt | Visual |

### LocalStorage/Cookies

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| BRW-07 | LocalStorage voll | Speichern | Error + Graceful Fallback | E2E |
| BRW-08 | Cookies deaktiviert | Login | Warnung | E2E |
| BRW-09 | Private/Incognito | Login | Funktioniert | E2E |
| BRW-10 | Cache geleert | Nach Reload | Funktioniert | E2E |

---

## 7. Concurrent Users

### Gleichzeitige Bearbeitung

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| CONC-01 | Collab Edit | 2 User gleichzeitig | YJS Sync | E2E |
| CONC-02 | Gleiche Ressource | Delete während Edit | Konflikt-Handling | E2E |
| CONC-03 | Gleiches Dokument | Upload während Embed | Queue-Handling | E2E |
| CONC-04 | Race Condition | Schnelle Doppel-Klicks | Nur eine Aktion | E2E |

---

## 8. Langzeit-Sessions

### Session-Verwaltung

| ID | Test | Szenario | Erwartung | Art |
|----|------|----------|-----------|-----|
| LONG-01 | Token Expiration | Nach 1h | Refresh oder Re-Login | E2E |
| LONG-02 | Lange Inaktivität | 30min idle | Session noch aktiv | E2E |
| LONG-03 | Memory Leak | 1h Chat | Kein Memory-Anstieg | Perf |
| LONG-04 | WebSocket Ping | 2h Verbindung | Verbindung stabil | E2E |

---

## 9. Loading States

### Skeleton Loader

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| LOAD-01 | Chatbot-Liste | Sidebar | Skeleton während Load | E2E |
| LOAD-02 | Admin Dashboard | Sections | Staggered Loading | E2E |
| LOAD-03 | User-Details | Dialog | Skeleton | E2E |
| LOAD-04 | Chart Data | Charts | Skeleton | E2E |

### Progress Indicators

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| LOAD-05 | Embedding | RAG | Progress-Bar 0-100% | E2E |
| LOAD-06 | PDF Compile | LaTeX | Spinner + Text | E2E |
| LOAD-07 | LLM Response | Chat | Typing Indicator | E2E |
| LOAD-08 | File Upload | Upload | Per-File Progress | E2E |

---

## 10. Checkliste für manuelle Tests

### Empty States
- [ ] Alle Listen zeigen Empty-State korrekt
- [ ] Empty-State Icons passend
- [ ] Action-Buttons in Empty-States

### Error Handling
- [ ] API-Fehler werden angezeigt
- [ ] Form-Validierung funktioniert
- [ ] Upload-Fehler klar kommuniziert
- [ ] Netzwerk-Fehler behandelt

### Limits
- [ ] Lange Texte werden akzeptiert
- [ ] Slider-Limits respektiert
- [ ] File-Size-Limits durchgesetzt

### Spezialzeichen
- [ ] Umlaute korrekt
- [ ] Emoji funktioniert
- [ ] HTML escaped
- [ ] Unicode unterstützt

### Network
- [ ] Loading-States sichtbar
- [ ] Reconnect funktioniert
- [ ] Offline-Handling

### Browser
- [ ] Refresh-Warnung bei unsaved
- [ ] Back/Forward funktioniert
- [ ] Multi-Tab stabil

---

**Letzte Aktualisierung:** 30. Dezember 2025
