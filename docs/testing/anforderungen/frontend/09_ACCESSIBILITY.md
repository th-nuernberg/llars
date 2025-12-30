# Frontend Testanforderungen: Accessibility (A11y)

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Accessibility-Tests nach WCAG 2.1 AA Standards.

**Bereiche:** Keyboard Navigation | Screen Reader | Focus Management | Color Contrast

---

## 1. Keyboard Navigation

### Tab-Reihenfolge

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-KB01 | Tab durch Formular | Logische Reihenfolge | Manual |
| A11Y-KB02 | Tab durch Navigation | Top→Left→Main→Footer | Manual |
| A11Y-KB03 | Tab in Dialog | Fokus bleibt in Dialog | E2E |
| A11Y-KB04 | Tab-Trap vermeiden | Kein Fokus-Gefängnis | Manual |
| A11Y-KB05 | Skip-Link | "Zum Hauptinhalt" | E2E |

### Fokus-Indikatoren

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-FI01 | Button fokussiert | Sichtbarer Outline | Visual |
| A11Y-FI02 | Link fokussiert | Sichtbarer Outline | Visual |
| A11Y-FI03 | Input fokussiert | Border-Änderung | Visual |
| A11Y-FI04 | Custom Focus Style | LLARS-konform (2px solid) | Visual |
| A11Y-FI05 | Focus nicht versteckt | Immer sichtbar | Manual |

### Keyboard-Aktivierung

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-KA01 | Enter auf Button | Click-Event | E2E |
| A11Y-KA02 | Space auf Button | Click-Event | E2E |
| A11Y-KA03 | Enter auf Link | Navigation | E2E |
| A11Y-KA04 | Escape schließt Dialog | Dialog geschlossen | E2E |
| A11Y-KA05 | Arrow Keys in Select | Navigation funktioniert | E2E |
| A11Y-KA06 | Arrow Keys in Slider | Wert ändert sich | E2E |
| A11Y-KA07 | Arrow Keys in Tabs | Tab wechselt | E2E |

### Test-Code

```typescript
// e2e/a11y/keyboard.spec.ts
test('A11Y-KB01: tab order is logical in forms', async ({ page }) => {
  await page.goto('/login')

  // Start at username
  await page.keyboard.press('Tab')
  await expect(page.locator('input[name="username"]')).toBeFocused()

  // Tab to password
  await page.keyboard.press('Tab')
  await expect(page.locator('input[name="password"]')).toBeFocused()

  // Tab to submit
  await page.keyboard.press('Tab')
  await expect(page.locator('button[type="submit"]')).toBeFocused()
})

test('A11Y-KB03: focus stays in dialog', async ({ page }) => {
  await page.goto('/Home')
  await page.click('[data-test="settings-btn"]')

  // Tab through dialog
  for (let i = 0; i < 20; i++) {
    await page.keyboard.press('Tab')
    const focusedInDialog = await page.evaluate(() => {
      const focused = document.activeElement
      return document.querySelector('.v-dialog')?.contains(focused)
    })
    expect(focusedInDialog).toBe(true)
  }
})

test('A11Y-KA04: escape closes dialog', async ({ page }) => {
  await page.goto('/Home')
  await page.click('[data-test="settings-btn"]')
  await expect(page.locator('.v-dialog')).toBeVisible()

  await page.keyboard.press('Escape')
  await expect(page.locator('.v-dialog')).not.toBeVisible()
})
```

---

## 2. Screen Reader Support

### ARIA Labels

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-AR01 | Icon-Buttons | aria-label vorhanden | Audit |
| A11Y-AR02 | Bilder | alt-Text vorhanden | Audit |
| A11Y-AR03 | Formulare | aria-describedby bei Errors | Audit |
| A11Y-AR04 | Live Regions | aria-live für Updates | Audit |
| A11Y-AR05 | Dialoge | role="dialog" + aria-modal | Audit |

### Semantic HTML

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-SM01 | Überschriften | h1-h6 hierarchisch | Audit |
| A11Y-SM02 | Listen | ul/ol mit li | Audit |
| A11Y-SM03 | Navigation | nav Element | Audit |
| A11Y-SM04 | Main Content | main Element | Audit |
| A11Y-SM05 | Footer | footer Element | Audit |

### Screen Reader Announcements

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-SR01 | Toast/Snackbar | aria-live="polite" | Manual |
| A11Y-SR02 | Loading States | aria-busy="true" | Manual |
| A11Y-SR03 | Fehler-Meldungen | Vorgelesen | Manual |
| A11Y-SR04 | Erfolg-Meldungen | Vorgelesen | Manual |
| A11Y-SR05 | Progress Updates | aria-valuenow | Manual |

### Test-Code (axe-core)

```typescript
// e2e/a11y/axe-audit.spec.ts
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility Audit', () => {
  test('A11Y-AR01: home page has no violations', async ({ page }) => {
    await page.goto('/Home')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    expect(results.violations).toEqual([])
  })

  test('A11Y-AR01: login page has no violations', async ({ page }) => {
    await page.goto('/login')

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    expect(results.violations).toEqual([])
  })

  test('A11Y-AR01: admin page has no violations', async ({ adminPage }) => {
    await adminPage.goto('/admin')

    const results = await new AxeBuilder({ page: adminPage })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    expect(results.violations).toEqual([])
  })
})
```

---

## 3. Color Contrast

### Text Contrast (WCAG AA: 4.5:1)

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| A11Y-CC01 | Body Text | Normaler Text | ≥4.5:1 | Audit |
| A11Y-CC02 | Button Text | LBtn | ≥4.5:1 | Audit |
| A11Y-CC03 | Link Text | Links | ≥4.5:1 | Audit |
| A11Y-CC04 | Error Text | Fehlermeldungen | ≥4.5:1 | Audit |
| A11Y-CC05 | Placeholder | Input Placeholder | ≥4.5:1 | Audit |

### Large Text Contrast (WCAG AA: 3:1)

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| A11Y-LC01 | Headings | h1-h3 | ≥3:1 | Audit |
| A11Y-LC02 | Large Buttons | size="large" | ≥3:1 | Audit |

### Non-Text Contrast (WCAG AA: 3:1)

| ID | Test | Element | Erwartung | Art |
|----|------|---------|-----------|-----|
| A11Y-NC01 | Focus Indicator | Outline | ≥3:1 | Audit |
| A11Y-NC02 | Form Borders | Input Borders | ≥3:1 | Audit |
| A11Y-NC03 | Icons | Actionable Icons | ≥3:1 | Audit |
| A11Y-NC04 | Charts | Chart Lines/Bars | ≥3:1 | Audit |

### LLARS Farben Kontrast-Check

| Farbe | Hex | Auf Weiß | Auf Schwarz |
|-------|-----|----------|-------------|
| Primary | #b0ca97 | 1.8:1 ⚠️ | 8.5:1 ✅ |
| Secondary | #D1BC8A | 1.7:1 ⚠️ | 7.6:1 ✅ |
| Accent | #88c4c8 | 2.1:1 ⚠️ | 7.0:1 ✅ |
| Success | #98d4bb | 1.9:1 ⚠️ | 7.9:1 ✅ |
| Danger | #e8a087 | 2.0:1 ⚠️ | 6.1:1 ✅ |
| Text Dark | #333333 | 12.6:1 ✅ | 1.7:1 ⚠️ |

**Hinweis:** LLARS Pastel-Farben benötigen dunklen Text auf hellem Hintergrund.

---

## 4. Focus Management

### Dialog Focus

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-DF01 | Dialog öffnet | Fokus auf erstes Element | E2E |
| A11Y-DF02 | Dialog schließt | Fokus zurück zum Trigger | E2E |
| A11Y-DF03 | Nested Dialog | Fokus korrekt verwaltet | E2E |

### Page Navigation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-PN01 | Route-Wechsel | Fokus auf h1 oder main | E2E |
| A11Y-PN02 | Nach Formular-Submit | Fokus auf Ergebnis/Fehler | E2E |

### Dynamic Content

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-DC01 | Liste erweitert | Fokus nicht verloren | E2E |
| A11Y-DC02 | Accordion öffnet | Fokus auf Content | E2E |
| A11Y-DC03 | Tab wechselt | Fokus auf neuen Content | E2E |

---

## 5. Motion & Animation

### Reduced Motion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-RM01 | prefers-reduced-motion | Animationen reduziert | E2E |
| A11Y-RM02 | Loading Animation | Statisch oder minimal | E2E |
| A11Y-RM03 | Hover Effects | Keine Bewegung | E2E |
| A11Y-RM04 | Transitions | Instant oder minimal | E2E |

### Test-Code

```typescript
// e2e/a11y/reduced-motion.spec.ts
test('A11Y-RM01: respects prefers-reduced-motion', async ({ browser }) => {
  const context = await browser.newContext({
    reducedMotion: 'reduce'
  })
  const page = await context.newPage()
  await page.goto('/Home')

  // Check that animations are disabled
  const animation = await page.evaluate(() => {
    const element = document.querySelector('.l-loading')
    if (!element) return 'no-element'
    const styles = getComputedStyle(element)
    return styles.animation
  })

  expect(animation).toMatch(/none|0s/)
  await context.close()
})
```

---

## 6. Form Accessibility

### Labels

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-FL01 | Input hat Label | Verknüpft via for/id | Audit |
| A11Y-FL02 | Required markiert | aria-required="true" | Audit |
| A11Y-FL03 | Error verknüpft | aria-describedby | Audit |

### Validation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-FV01 | Error bei Submit | aria-invalid="true" | E2E |
| A11Y-FV02 | Error-Text | Screen Reader liest vor | Manual |
| A11Y-FV03 | Fokus auf erstem Fehler | Automatisch fokussiert | E2E |

### Autocomplete

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-FA01 | Username | autocomplete="username" | Audit |
| A11Y-FA02 | Password | autocomplete="current-password" | Audit |
| A11Y-FA03 | Email | autocomplete="email" | Audit |

---

## 7. Image & Media

### Images

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-IM01 | Informative Images | Descriptiver alt-Text | Audit |
| A11Y-IM02 | Decorative Images | alt="" oder role="presentation" | Audit |
| A11Y-IM03 | Complex Images | Lange Beschreibung | Audit |

### Icons

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-IC01 | Standalone Icons | aria-label | Audit |
| A11Y-IC02 | Icons in Buttons | aria-hidden + Button Label | Audit |
| A11Y-IC03 | Status Icons | Zusätzlicher Text | Audit |

---

## 8. Tables

### Data Tables

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| A11Y-TB01 | Table Headers | th mit scope | Audit |
| A11Y-TB02 | Caption | caption oder aria-label | Audit |
| A11Y-TB03 | Sortierbare Columns | aria-sort | Audit |
| A11Y-TB04 | Pagination | Status announced | Manual |

---

## 9. Komplette Seiten-Audits

### Kritische Seiten

| ID | Seite | Erwartung | Art |
|----|-------|-----------|-----|
| A11Y-PG01 | /login | Keine Violations | Audit |
| A11Y-PG02 | /Home | Keine Violations | Audit |
| A11Y-PG03 | /chat | Keine Violations | Audit |
| A11Y-PG04 | /admin | Keine Violations | Audit |
| A11Y-PG05 | /Ranker | Keine Violations | Audit |
| A11Y-PG06 | /MarkdownCollab | Keine Violations | Audit |
| A11Y-PG07 | /LatexCollab | Keine Violations | Audit |
| A11Y-PG08 | /Anonymize | Keine Violations | Audit |

### Test-Code (Automated Audit)

```typescript
// e2e/a11y/full-audit.spec.ts
import AxeBuilder from '@axe-core/playwright'

const criticalPages = [
  '/login',
  '/Home',
  '/chat',
  '/admin',
  '/Ranker',
  '/Rater',
  '/MarkdownCollab',
  '/LatexCollab',
  '/Anonymize'
]

for (const pagePath of criticalPages) {
  test(`A11Y audit: ${pagePath}`, async ({ authenticatedPage }) => {
    await authenticatedPage.goto(pagePath)

    const results = await new AxeBuilder({ page: authenticatedPage })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .exclude('.monaco-editor') // Exclude third-party
      .analyze()

    // Log violations for debugging
    if (results.violations.length > 0) {
      console.log(`Violations on ${pagePath}:`, JSON.stringify(results.violations, null, 2))
    }

    expect(results.violations).toEqual([])
  })
}
```

---

## 10. Checkliste für manuelle Tests

### Keyboard
- [ ] Tab-Reihenfolge logisch
- [ ] Fokus immer sichtbar
- [ ] Enter/Space aktiviert Buttons
- [ ] Escape schließt Dialoge
- [ ] Kein Fokus-Trap

### Screen Reader
- [ ] Alle Buttons haben Labels
- [ ] Alle Bilder haben alt-Text
- [ ] Überschriften hierarchisch
- [ ] Live-Regions für Updates
- [ ] Fehler werden vorgelesen

### Farben
- [ ] Text-Kontrast ausreichend
- [ ] Nicht nur Farbe zur Info
- [ ] Dark Mode funktioniert
- [ ] High Contrast Mode

### Motion
- [ ] prefers-reduced-motion beachtet
- [ ] Keine automatisch startenden Videos
- [ ] Animationen pausierbar

---

## 11. Tools

| Tool | Verwendung |
|------|------------|
| **axe-core** | Automatisierte Audits |
| **WAVE** | Browser Extension |
| **Lighthouse** | Chrome DevTools |
| **VoiceOver** | macOS Screen Reader |
| **NVDA** | Windows Screen Reader |
| **Color Contrast Analyzer** | Kontrast-Check |

---

**Letzte Aktualisierung:** 30. Dezember 2025
