# Frontend Testanforderungen: Visual & Responsive Tests

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Visual Regression Tests, Responsive Design Tests und Theme-Tests.

**Bereiche:** Breakpoints | Mobile | Dark Mode | Browser Compatibility | Screenshot Comparison

---

## 1. Responsive Breakpoints

### Vuetify Breakpoints

| Name | Bereich | Viewport |
|------|---------|----------|
| xs | < 600px | Mobile Portrait |
| sm | 600-959px | Mobile Landscape / Tablet |
| md | 960-1279px | Tablet / Small Desktop |
| lg | 1280-1919px | Desktop |
| xl | 1920-2559px | Large Desktop |
| xxl | ≥ 2560px | Ultra-Wide |

### Tests pro Breakpoint

| ID | Test | xs | sm | md | lg | xl |
|----|------|----|----|----|----|-----|
| RES-BP01 | Home Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| RES-BP02 | Chat Interface | ✓ | ✓ | ✓ | ✓ | ✓ |
| RES-BP03 | Admin Panel | - | ✓ | ✓ | ✓ | ✓ |
| RES-BP04 | Ranker/Rater | ✓ | ✓ | ✓ | ✓ | ✓ |
| RES-BP05 | LaTeX Editor | - | - | ✓ | ✓ | ✓ |
| RES-BP06 | Markdown Collab | - | ✓ | ✓ | ✓ | ✓ |

### Test-Code

```typescript
// e2e/visual/responsive.spec.ts
import { test, expect, devices } from '@playwright/test'

const viewports = {
  xs: { width: 375, height: 667 },   // iPhone SE
  sm: { width: 768, height: 1024 },  // iPad
  md: { width: 1024, height: 768 },  // iPad Landscape
  lg: { width: 1440, height: 900 },  // Laptop
  xl: { width: 1920, height: 1080 }, // Desktop
}

for (const [name, viewport] of Object.entries(viewports)) {
  test.describe(`Responsive: ${name} (${viewport.width}x${viewport.height})`, () => {
    test.use({ viewport })

    test(`RES-BP01: home dashboard renders correctly`, async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/Home')
      await expect(authenticatedPage.locator('.home-container')).toBeVisible()

      // Screenshot comparison
      await expect(authenticatedPage).toHaveScreenshot(`home-${name}.png`)
    })

    test(`RES-BP02: chat interface adapts`, async ({ authenticatedPage }) => {
      await authenticatedPage.goto('/chat')

      if (viewport.width < 600) {
        // Mobile: Sidebar should be hidden/collapsed
        await expect(authenticatedPage.locator('.sidebar')).not.toBeVisible()
      } else {
        await expect(authenticatedPage.locator('.sidebar')).toBeVisible()
      }
    })
  })
}
```

---

## 2. Mobile-Spezifische Tests

### Navigation

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MOB-NAV01 | Hamburger Menu | Sichtbar auf xs/sm | E2E |
| MOB-NAV02 | Menu öffnen | Drawer slides in | E2E |
| MOB-NAV03 | Menu schließen | Tap outside schließt | E2E |
| MOB-NAV04 | Navigation Items | Alle erreichbar | E2E |
| MOB-NAV05 | Back Button | Browser-Back funktioniert | E2E |

### Touch-Interaktionen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MOB-TCH01 | Tap auf Button | Click-Event | E2E |
| MOB-TCH02 | Long-Press | Kontextmenü (wenn vorhanden) | E2E |
| MOB-TCH03 | Swipe in List | Scroll funktioniert | E2E |
| MOB-TCH04 | Pinch-to-Zoom | PDF Viewer zoom | E2E |
| MOB-TCH05 | Pull-to-Refresh | Refresh (wenn implementiert) | E2E |

### Mobile Layout

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| MOB-LAY01 | Kein horizontaler Scroll | Kein overflow-x | Visual |
| MOB-LAY02 | Touch-Targets | Min. 44x44px | Audit |
| MOB-LAY03 | Font-Size | Min. 16px für Input | Audit |
| MOB-LAY04 | Viewport Meta | width=device-width | Audit |
| MOB-LAY05 | Safe Areas | Notch/Island berücksichtigt | Visual |

### Test-Code

```typescript
// e2e/visual/mobile.spec.ts
import { test, expect, devices } from '@playwright/test'

test.describe('Mobile Tests', () => {
  test.use({ ...devices['iPhone 13'] })

  test('MOB-NAV01: hamburger menu visible', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')
    await expect(authenticatedPage.locator('[data-test="hamburger-menu"]')).toBeVisible()
  })

  test('MOB-NAV02: menu opens on tap', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')
    await authenticatedPage.tap('[data-test="hamburger-menu"]')
    await expect(authenticatedPage.locator('.v-navigation-drawer')).toBeVisible()
  })

  test('MOB-LAY01: no horizontal scroll', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    const hasHorizontalScroll = await authenticatedPage.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth
    })

    expect(hasHorizontalScroll).toBe(false)
  })

  test('MOB-LAY02: touch targets minimum size', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    const buttons = await authenticatedPage.locator('button, a, [role="button"]').all()

    for (const button of buttons) {
      const box = await button.boundingBox()
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(44)
        expect(box.height).toBeGreaterThanOrEqual(44)
      }
    }
  })
})
```

---

## 3. Dark Mode Tests

### Theme Switching

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DRK-SW01 | Toggle Dark Mode | Theme wechselt | E2E |
| DRK-SW02 | Persist Preference | Nach Reload beibehalten | E2E |
| DRK-SW03 | System Preference | Übernimmt OS-Einstellung | E2E |
| DRK-SW04 | Manual Override | User-Wahl überschreibt System | E2E |

### Dark Mode Farben

| ID | Element | Light | Dark | Test |
|----|---------|-------|------|------|
| DRK-CL01 | Background | #ffffff | #1e1e1e | Visual |
| DRK-CL02 | Text | #333333 | #e0e0e0 | Visual |
| DRK-CL03 | Primary | #b0ca97 | #b0ca97 | Visual |
| DRK-CL04 | Cards | #ffffff | #2d2d2d | Visual |
| DRK-CL05 | Borders | #e0e0e0 | #404040 | Visual |
| DRK-CL06 | Inputs | #f5f5f5 | #333333 | Visual |

### Kontrast in Dark Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DRK-CT01 | Text auf Background | ≥4.5:1 | Audit |
| DRK-CT02 | Primary auf Dark | Ausreichend | Audit |
| DRK-CT03 | Error Messages | Gut lesbar | Visual |
| DRK-CT04 | Success Messages | Gut lesbar | Visual |
| DRK-CT05 | Charts/Graphs | Alle Farben sichtbar | Visual |

### Test-Code

```typescript
// e2e/visual/dark-mode.spec.ts
test.describe('Dark Mode', () => {
  test('DRK-SW01: toggle dark mode', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    // Open settings
    await authenticatedPage.click('[data-test="user-menu"]')
    await authenticatedPage.click('[data-test="settings-btn"]')

    // Toggle dark mode
    await authenticatedPage.click('[data-test="dark-mode-toggle"]')

    // Verify dark class
    await expect(authenticatedPage.locator('html')).toHaveClass(/dark/)
  })

  test('DRK-SW02: persists after reload', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    // Enable dark mode
    await authenticatedPage.evaluate(() => {
      localStorage.setItem('theme', 'dark')
    })

    await authenticatedPage.reload()

    await expect(authenticatedPage.locator('html')).toHaveClass(/dark/)
  })

  test('DRK-SW03: respects system preference', async ({ browser }) => {
    const context = await browser.newContext({
      colorScheme: 'dark'
    })
    const page = await context.newPage()
    await page.goto('/login')

    // Should auto-detect dark mode
    await expect(page.locator('html')).toHaveClass(/dark/)

    await context.close()
  })
})

// Screenshot comparison for both themes
for (const theme of ['light', 'dark']) {
  test(`Visual: home in ${theme} mode`, async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Home')

    if (theme === 'dark') {
      await authenticatedPage.evaluate(() => {
        document.documentElement.classList.add('dark')
      })
    }

    await expect(authenticatedPage).toHaveScreenshot(`home-${theme}.png`)
  })
}
```

---

## 4. Browser Compatibility

### Unterstützte Browser

| Browser | Version | Priorität |
|---------|---------|-----------|
| Chrome | 90+ | Hoch |
| Firefox | 88+ | Hoch |
| Safari | 14+ | Mittel |
| Edge | 90+ | Mittel |
| Mobile Safari | 14+ | Mittel |
| Chrome Android | 90+ | Mittel |

### Browser-spezifische Tests

| ID | Test | Chrome | Firefox | Safari | Edge |
|----|------|--------|---------|--------|------|
| BRW-01 | Login Flow | ✓ | ✓ | ✓ | ✓ |
| BRW-02 | WebSocket Connection | ✓ | ✓ | ✓ | ✓ |
| BRW-03 | File Upload | ✓ | ✓ | ✓ | ✓ |
| BRW-04 | PDF Viewer | ✓ | ✓ | ✓ | ✓ |
| BRW-05 | Monaco Editor | ✓ | ✓ | ✓ | ✓ |
| BRW-06 | Drag & Drop | ✓ | ✓ | ✓ | ✓ |
| BRW-07 | LocalStorage | ✓ | ✓ | ✓ | ✓ |
| BRW-08 | Clipboard API | ✓ | ✓ | ⚠️ | ✓ |
| BRW-09 | Fullscreen API | ✓ | ✓ | ⚠️ | ✓ |
| BRW-10 | CSS Grid/Flexbox | ✓ | ✓ | ✓ | ✓ |

### Test-Code (Cross-Browser)

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'edge', use: { channel: 'msedge' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
    { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },
  ],
})

// e2e/cross-browser/compatibility.spec.ts
test('BRW-02: websocket connection works', async ({ page, browserName }) => {
  await page.goto('/chat')

  // Wait for socket connection
  const connected = await page.evaluate(() => {
    return new Promise(resolve => {
      setTimeout(() => {
        const socketConnected = window.__socketConnected || false
        resolve(socketConnected)
      }, 3000)
    })
  })

  expect(connected).toBe(true)
})
```

---

## 5. Visual Regression Tests

### Screenshot-Vergleich Seiten

| ID | Seite | Breakpoints | Themes |
|----|-------|-------------|--------|
| VIS-01 | /login | xs, md, lg | light, dark |
| VIS-02 | /Home | xs, md, lg | light, dark |
| VIS-03 | /chat | sm, lg | light, dark |
| VIS-04 | /admin | md, lg | light, dark |
| VIS-05 | /Ranker | md, lg | light, dark |
| VIS-06 | /Rater | md, lg | light, dark |
| VIS-07 | /Judge | lg | light, dark |
| VIS-08 | /LatexCollab | lg | light, dark |
| VIS-09 | /MarkdownCollab | lg | light, dark |
| VIS-10 | /Anonymize | md, lg | light, dark |

### Komponenten-Screenshots

| ID | Komponente | Zustände |
|----|------------|----------|
| VIS-C01 | LBtn | all variants, hover, disabled |
| VIS-C02 | LTag | all variants, sizes |
| VIS-C03 | LSlider | inactive, active, gradient |
| VIS-C04 | LCard | default, hover, selected |
| VIS-C05 | LTabs | default, active, hover |
| VIS-C06 | Dialogs | open state |

### Test-Code

```typescript
// e2e/visual/screenshots.spec.ts
import { test, expect } from '@playwright/test'

// Page screenshots
const pages = [
  { path: '/login', name: 'login', auth: false },
  { path: '/Home', name: 'home', auth: true },
  { path: '/chat', name: 'chat', auth: true },
  { path: '/admin', name: 'admin', auth: true, role: 'admin' },
]

for (const pageConfig of pages) {
  test.describe(`Visual: ${pageConfig.name}`, () => {
    test(`screenshot matches`, async ({ authenticatedPage }) => {
      await authenticatedPage.goto(pageConfig.path)

      // Wait for content to load
      await authenticatedPage.waitForLoadState('networkidle')

      // Hide dynamic content
      await authenticatedPage.evaluate(() => {
        document.querySelectorAll('[data-dynamic]').forEach(el => {
          (el as HTMLElement).style.visibility = 'hidden'
        })
      })

      await expect(authenticatedPage).toHaveScreenshot(`${pageConfig.name}.png`, {
        maxDiffPixels: 100, // Allow small differences
        animations: 'disabled',
      })
    })
  })
}

// Component screenshots
test.describe('Component Screenshots', () => {
  test('VIS-C01: LBtn variants', async ({ page }) => {
    await page.goto('/component-test')

    const variants = ['primary', 'secondary', 'accent', 'danger', 'cancel']

    for (const variant of variants) {
      const btn = page.locator(`.l-btn.${variant}`).first()
      await expect(btn).toHaveScreenshot(`btn-${variant}.png`)
    }
  })

  test('VIS-C03: LSlider states', async ({ page }) => {
    await page.goto('/component-test')

    const slider = page.locator('.l-slider').first()

    // Inactive state
    await expect(slider).toHaveScreenshot('slider-inactive.png')

    // Active state (after interaction)
    await slider.click()
    await expect(slider).toHaveScreenshot('slider-active.png')
  })
})
```

---

## 6. Animation & Transition Tests

### Animationen

| ID | Animation | Element | Erwartung | Art |
|----|-----------|---------|-----------|-----|
| ANI-01 | Page Transition | Route Change | Smooth fade | Visual |
| ANI-02 | Dialog Open | v-dialog | Scale + fade | Visual |
| ANI-03 | Sidebar Toggle | Navigation | Slide | Visual |
| ANI-04 | Button Hover | LBtn | Background transition | Visual |
| ANI-05 | Card Hover | LCard | Subtle lift | Visual |
| ANI-06 | Loading Spinner | l-loading | Rotation | Visual |
| ANI-07 | Skeleton Pulse | v-skeleton | Pulse animation | Visual |
| ANI-08 | Toast Slide | Snackbar | Slide in/out | Visual |

### Reduced Motion Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANI-RM01 | prefers-reduced-motion | Animationen reduziert/aus | E2E |
| ANI-RM02 | Transitions | Instant oder minimal | E2E |
| ANI-RM03 | Loading States | Statisch oder minimal | E2E |

### Test-Code

```typescript
// e2e/visual/animations.spec.ts
test('ANI-02: dialog animation', async ({ page }) => {
  await page.goto('/Home')

  // Record video of dialog opening
  await page.click('[data-test="settings-btn"]')

  // Dialog should animate in
  const dialog = page.locator('.v-dialog')
  await expect(dialog).toBeVisible()

  // Check that transform was applied (animation start)
  const transform = await dialog.evaluate(el => {
    return getComputedStyle(el).transform
  })

  // After animation, should be at final position
  await page.waitForTimeout(300) // Animation duration
  const finalTransform = await dialog.evaluate(el => {
    return getComputedStyle(el).transform
  })

  expect(finalTransform).not.toBe(transform)
})

test('ANI-RM01: respects reduced motion', async ({ browser }) => {
  const context = await browser.newContext({
    reducedMotion: 'reduce'
  })
  const page = await context.newPage()
  await page.goto('/Home')

  // Check CSS variable or class
  const reducedMotion = await page.evaluate(() => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches
  })

  expect(reducedMotion).toBe(true)

  // Animations should be disabled
  const animationDuration = await page.evaluate(() => {
    const el = document.querySelector('.l-btn')
    return el ? getComputedStyle(el).transitionDuration : '0s'
  })

  expect(animationDuration).toMatch(/0s|0\.01s/)

  await context.close()
})
```

---

## 7. Layout-Stabilität (CLS)

### Cumulative Layout Shift Tests

| ID | Test | Seite | Max CLS | Art |
|----|------|-------|---------|-----|
| CLS-01 | Initial Load | /Home | < 0.1 | Perf |
| CLS-02 | Image Loading | Chat | < 0.1 | Perf |
| CLS-03 | Font Loading | Alle | < 0.1 | Perf |
| CLS-04 | Lazy Content | Admin | < 0.1 | Perf |
| CLS-05 | Ad/Banner | N/A | < 0.1 | Perf |

### Test-Code

```typescript
// e2e/visual/layout-stability.spec.ts
test('CLS-01: home page has low CLS', async ({ page }) => {
  await page.goto('/Home')

  // Measure CLS using Performance API
  const cls = await page.evaluate(() => {
    return new Promise(resolve => {
      let clsValue = 0
      const observer = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value
          }
        }
      })
      observer.observe({ type: 'layout-shift', buffered: true })

      setTimeout(() => {
        observer.disconnect()
        resolve(clsValue)
      }, 5000)
    })
  })

  expect(cls).toBeLessThan(0.1)
})
```

---

## 8. Print Styles

### Druckbare Seiten

| ID | Seite | Druckbar | Test |
|----|-------|----------|------|
| PRT-01 | Chat-Historie | Ja | E2E |
| PRT-02 | Evaluation Report | Ja | E2E |
| PRT-03 | Admin Dashboard | Nein | E2E |
| PRT-04 | PDF Preview | Nein (PDF export) | E2E |

### Print-spezifische Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| PRT-S01 | Navigation versteckt | display: none | Visual |
| PRT-S02 | Hintergrundfarben | Optimiert für Druck | Visual |
| PRT-S03 | Links sichtbar | URL nach Link | Visual |
| PRT-S04 | Page Breaks | Sinnvolle Umbrüche | Visual |

### Test-Code

```typescript
// e2e/visual/print.spec.ts
test('PRT-01: chat history printable', async ({ page }) => {
  await page.goto('/chat')

  // Emulate print media
  await page.emulateMedia({ media: 'print' })

  // Navigation should be hidden
  await expect(page.locator('.v-navigation-drawer')).not.toBeVisible()

  // Main content should be visible
  await expect(page.locator('.chat-messages')).toBeVisible()

  // Screenshot in print mode
  await expect(page).toHaveScreenshot('chat-print.png')
})
```

---

## 9. LLARS-spezifische Visual Tests

### Asymmetrischer Border-Radius

| ID | Komponente | Radius | Test |
|----|------------|--------|------|
| LLARS-V01 | LBtn | 16px 4px 16px 4px | Visual |
| LLARS-V02 | LTag | 6px 2px 6px 2px | Visual |
| LLARS-V03 | LCard | Standard + accent top | Visual |
| LLARS-V04 | Input Fields | Vuetify default | Visual |

### Pastel Farbpalette

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LLARS-C01 | Primary (#b0ca97) | Korrekt angewendet | Visual |
| LLARS-C02 | Secondary (#D1BC8A) | Korrekt angewendet | Visual |
| LLARS-C03 | Accent (#88c4c8) | Korrekt angewendet | Visual |
| LLARS-C04 | Danger (#e8a087) | Korrekt angewendet | Visual |

### Test-Code

```typescript
// e2e/visual/llars-design.spec.ts
test('LLARS-V01: LBtn has asymmetric border-radius', async ({ page }) => {
  await page.goto('/component-test')

  const btn = page.locator('.l-btn').first()
  const borderRadius = await btn.evaluate(el => {
    return getComputedStyle(el).borderRadius
  })

  // Should be asymmetric: 16px 4px 16px 4px
  expect(borderRadius).toMatch(/16px 4px 16px 4px|16px 4px/)
})

test('LLARS-C01: primary color is sage green', async ({ page }) => {
  await page.goto('/component-test')

  const btn = page.locator('.l-btn.primary').first()
  const bgColor = await btn.evaluate(el => {
    return getComputedStyle(el).backgroundColor
  })

  // #b0ca97 = rgb(176, 202, 151)
  expect(bgColor).toBe('rgb(176, 202, 151)')
})
```

---

## 10. Checkliste für manuelle Visual Tests

### Responsive

- [ ] xs (375px): Layout funktioniert
- [ ] sm (768px): Tablet-Layout korrekt
- [ ] md (1024px): Desktop-Layout
- [ ] lg (1440px): Großer Desktop
- [ ] xl (1920px): Full HD

### Dark Mode

- [ ] Toggle funktioniert
- [ ] Alle Texte lesbar
- [ ] Kontraste ausreichend
- [ ] Charts/Grafiken sichtbar
- [ ] Preference wird gespeichert

### Browser

- [ ] Chrome: Alle Features
- [ ] Firefox: Alle Features
- [ ] Safari: Basis-Features
- [ ] Edge: Alle Features
- [ ] Mobile Safari: Responsive

### Animationen

- [ ] Smooth transitions
- [ ] Keine Ruckler
- [ ] Reduced motion respektiert
- [ ] Loading states korrekt

### LLARS Design

- [ ] Asymmetrischer Border-Radius
- [ ] Pastel-Farbpalette
- [ ] Konsistente Abstände
- [ ] Einheitliche Schatten

---

## 11. Playwright Visual Test Setup

### Konfiguration

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',

  // Screenshot comparison settings
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
      caret: 'hide',
    },
  },

  // Update snapshots with: npx playwright test --update-snapshots
  updateSnapshots: 'missing',

  projects: [
    {
      name: 'visual-chrome',
      use: {
        browserName: 'chromium',
        viewport: { width: 1440, height: 900 },
      },
    },
    {
      name: 'visual-mobile',
      use: {
        browserName: 'chromium',
        viewport: { width: 375, height: 667 },
        isMobile: true,
      },
    },
  ],
})
```

### CI Integration

```yaml
# .github/workflows/visual-tests.yml
name: Visual Regression Tests

on:
  pull_request:
    branches: [main]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run visual tests
        run: npx playwright test --project=visual-chrome

      - name: Upload diff screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: visual-diff
          path: test-results/
```

---

**Letzte Aktualisierung:** 30. Dezember 2025
