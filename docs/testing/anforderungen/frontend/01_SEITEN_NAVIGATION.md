# Frontend Testanforderungen: Seiten & Navigation

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die Hauptseiten und Navigation in LLARS.

---

## 1. Login-Seite (`/login`)

**Komponente:** `Login.vue`
**Priorität:** P0

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LOGIN-001 | Seite lädt | Login-Formular sichtbar | E2E |
| LOGIN-002 | Gültige Credentials | Redirect zu `/Home` | E2E |
| LOGIN-003 | Ungültige Credentials | Fehlermeldung angezeigt | E2E |
| LOGIN-004 | Leeres Formular | Submit-Button deaktiviert | Unit |
| LOGIN-005 | Redirect-Parameter | Nach Login zu ursprünglicher URL | E2E |
| LOGIN-006 | Token im localStorage | Token nach Login gespeichert | E2E |
| LOGIN-007 | Automatischer Redirect | Bei gültigem Token → Home | E2E |

### E2E Test-Code

```typescript
// e2e/auth/login.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('LOGIN-001: page loads correctly', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[name="username"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('LOGIN-002: valid credentials redirect to home', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'admin')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/.*Home/)
  })

  test('LOGIN-003: invalid credentials show error', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'wrong')
    await page.fill('input[name="password"]', 'wrong')
    await page.click('button[type="submit"]')
    await expect(page.locator('.v-alert')).toBeVisible()
  })
})
```

---

## 2. Home Dashboard (`/Home`)

**Komponente:** `Home.vue`
**Priorität:** P0

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| HOME-001 | Seite lädt | Dashboard mit Kacheln sichtbar | E2E |
| HOME-002 | Kategorien angezeigt | Linke Sidebar mit Kategorien | E2E |
| HOME-003 | Kacheln pro Kategorie | Feature-Kacheln in Grid | E2E |
| HOME-004 | Alle Kacheln klickbar | Jede Kachel navigiert korrekt | E2E |
| HOME-005 | Berechtigungs-Filter | Nur erlaubte Kacheln sichtbar | E2E |
| HOME-006 | Kategorie wechseln | Grid aktualisiert sich | E2E |
| HOME-007 | Panel resizable | Linkes Panel verstellbar | E2E |
| HOME-008 | Mobile Ansicht | Kategorie-Drawer statt Sidebar | E2E |

### Kachel-Navigations-Tests

| Kachel | Route | Permission | Test-ID |
|--------|-------|------------|---------|
| Ranking | `/Ranker` | `feature:ranking:view` | HOME-K01 |
| Rating | `/Rater` | `feature:rating:view` | HOME-K02 |
| Judge | `/judge` | `feature:judge:view` | HOME-K03 |
| OnCoCo | `/oncoco` | `feature:oncoco:view` | HOME-K04 |
| Prompt Engineering | `/PromptEngineering` | `feature:prompt_engineering:view` | HOME-K05 |
| Chat | `/chat` | `feature:chatbots:view` | HOME-K06 |
| Markdown Collab | `/MarkdownCollab` | `feature:markdown_collab:view` | HOME-K07 |
| LaTeX Collab | `/LatexCollab` | `feature:latex_collab:view` | HOME-K08 |
| LaTeX AI | `/LatexCollabAI` | `feature:latex_collab:view` | HOME-K09 |
| Anonymize | `/Anonymize` | `feature:anonymize:view` | HOME-K10 |
| KAIMO | `/kaimo` | `feature:kaimo:view` | HOME-K11 |
| Admin | `/admin` | Admin-Rolle | HOME-K12 |

### E2E Test-Code

```typescript
// e2e/navigation/home.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Home Dashboard', () => {
  test('HOME-001: dashboard loads with tiles', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')
    await expect(authenticatedPage.locator('.feature-card')).toHaveCount(1, { min: true })
  })

  test('HOME-004: all tiles navigate correctly', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    const tiles = [
      { name: 'Ranking', route: '/Ranker' },
      { name: 'Rating', route: '/Rater' },
      { name: 'Chat', route: '/chat' },
    ]

    for (const tile of tiles) {
      await authenticatedPage.goto('/Home')
      await authenticatedPage.click(`text=${tile.name}`)
      await expect(authenticatedPage).toHaveURL(new RegExp(tile.route))
    }
  })

  test('HOME-005: evaluator only sees allowed tiles', async ({ page }) => {
    // Login als Evaluator
    await page.goto('/login')
    await page.fill('input[name="username"]', 'evaluator')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/Home')

    // Admin-Kachel sollte nicht sichtbar sein
    await expect(page.locator('text=Admin')).not.toBeVisible()
    // Aber Ranking sollte sichtbar sein
    await expect(page.locator('text=Ranking')).toBeVisible()
  })
})
```

---

## 3. 404 Not Found (`/:pathMatch(.*)`)

**Komponente:** `NotFound.vue`
**Priorität:** P2

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| 404-001 | Ungültige Route | 404-Seite angezeigt | E2E |
| 404-002 | Feature-Vorschläge | Passende Features vorgeschlagen | E2E |
| 404-003 | Navigation zurück | Link zu Home funktioniert | E2E |

---

## 4. Anonymize-Seite (`/Anonymize`)

**Komponente:** `AnonymizeTool.vue`
**Priorität:** P2

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANON-001 | Seite lädt | Editor und Ausgabe sichtbar | E2E |
| ANON-002 | Text eingeben | Input wird angezeigt | E2E |
| ANON-003 | Pseudonymisierung | Personendaten ersetzt | E2E |
| ANON-004 | File Upload | DOCX/PDF hochladen | E2E |
| ANON-005 | Beispieltext laden | Beispiel wird geladen | E2E |
| ANON-006 | Output kopieren | Text in Zwischenablage | E2E |
| ANON-007 | Health Check | Service-Status angezeigt | Integration |
| ANON-008 | Mapping anzeigen | Entity-Mapping sichtbar | E2E |

### E2E Test-Code

```typescript
// e2e/features/anonymize.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Anonymize Tool', () => {
  test('ANON-001: page loads correctly', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Anonymize')
    await expect(authenticatedPage.locator('.editor-input')).toBeVisible()
    await expect(authenticatedPage.locator('.editor-output')).toBeVisible()
  })

  test('ANON-003: pseudonymization works', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Anonymize')

    // Text mit Namen eingeben
    await authenticatedPage.fill('.editor-input', 'Max Mustermann wohnt in Berlin.')
    await authenticatedPage.click('button:has-text("Pseudonymisieren")')

    // Warten auf Ergebnis
    await expect(authenticatedPage.locator('.editor-output')).not.toContainText('Max Mustermann')
  })
})
```

---

## 5. Organisatorische Seiten (Öffentlich)

### Impressum (`/Impressum`)

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| IMP-001 | Ohne Login zugänglich | Seite lädt ohne Auth | E2E |
| IMP-002 | Inhalt sichtbar | Rechtliche Infos angezeigt | E2E |

### Datenschutz (`/Datenschutz`)

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DSE-001 | Ohne Login zugänglich | Seite lädt ohne Auth | E2E |
| DSE-002 | Inhalt sichtbar | Datenschutz-Text angezeigt | E2E |

### Kontakt (`/Kontakt`)

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KON-001 | Ohne Login zugänglich | Seite lädt ohne Auth | E2E |
| KON-002 | Kontaktdaten sichtbar | Infos angezeigt | E2E |

---

## 6. Navigation-Guard Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| NAV-001 | Geschützte Route ohne Token | Redirect zu `/login` | E2E |
| NAV-002 | Token expired | Redirect zu `/login` | E2E |
| NAV-003 | Nach Login ursprüngliche Route | Redirect zu gespeicherter URL | E2E |
| NAV-004 | Logout löscht Token | localStorage leer | E2E |
| NAV-005 | Admin-Route als Evaluator | Redirect oder 403 | E2E |

### E2E Test-Code

```typescript
// e2e/navigation/guards.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Navigation Guards', () => {
  test('NAV-001: protected route redirects to login', async ({ page }) => {
    await page.goto('/Home')
    await expect(page).toHaveURL(/.*login/)
  })

  test('NAV-005: evaluator cannot access admin', async ({ page }) => {
    // Login als Evaluator
    await page.goto('/login')
    await page.fill('input[name="username"]', 'evaluator')
    await page.fill('input[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/Home')

    // Versuche Admin zu öffnen
    await page.goto('/admin')

    // Sollte redirect oder Fehlermeldung
    await expect(page).not.toHaveURL(/.*admin/)
  })
})
```

---

## 7. AppBar & Footer Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| APP-001 | AppBar sichtbar | Navigation sichtbar | E2E |
| APP-002 | User-Menu | Avatar + Dropdown | E2E |
| APP-003 | Logout Button | Logout funktioniert | E2E |
| APP-004 | Footer sichtbar | Copyright + Links | E2E |
| APP-005 | Theme Toggle | Dark/Light Mode wechselt | E2E |

---

## Checkliste für manuelle Tests

### Seiten-Ladeverhalten

- [ ] Alle Seiten laden ohne Console-Errors
- [ ] Skeleton-Loading während Datenladung
- [ ] Keine unbehandelten Promise-Rejections
- [ ] Responsive auf verschiedenen Bildschirmgrößen

### Navigation

- [ ] Breadcrumb korrekt (wo vorhanden)
- [ ] Browser Back-Button funktioniert
- [ ] Direct URL Access funktioniert
- [ ] Deep Links funktionieren

### Berechtigungen

- [ ] Admin sieht alle Kacheln
- [ ] Researcher sieht nur erlaubte Kacheln
- [ ] Evaluator sieht eingeschränkte Kacheln
- [ ] Chatbot_Manager sieht Chatbot + RAG

---

**Letzte Aktualisierung:** 30. Dezember 2025
