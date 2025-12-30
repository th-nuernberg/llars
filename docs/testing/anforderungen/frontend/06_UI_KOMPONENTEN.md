# Frontend Testanforderungen: UI-Komponenten

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt Tests für ALLE interaktiven UI-Komponenten in LLARS.

**Komponenten:** 20+ Custom LLARS | 45+ Vuetify | 100+ Tooltips | 10 Dialoge

---

## 1. LBtn (Button-Komponente)

**Datei:** `llars-frontend/src/components/common/LBtn.vue`

### Varianten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-V01 | variant="primary" | Grüner Hintergrund (#b0ca97) | Visual |
| BTN-V02 | variant="secondary" | Beige Hintergrund (#D1BC8A) | Visual |
| BTN-V03 | variant="accent" | Teal Hintergrund (#88c4c8) | Visual |
| BTN-V04 | variant="success" | Mint Hintergrund (#98d4bb) | Visual |
| BTN-V05 | variant="warning" | Gold Hintergrund (#e8c87a) | Visual |
| BTN-V06 | variant="danger" | Coral Hintergrund (#e8a087) | Visual |
| BTN-V07 | variant="cancel" | Grauer Hintergrund (#9e9e9e) | Visual |
| BTN-V08 | variant="text" | Transparenter Hintergrund | Visual |
| BTN-V09 | variant="tonal" | Leichter Hintergrund | Visual |
| BTN-V10 | variant="outlined" | Border ohne Fill | Visual |

### Größen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-S01 | size="small" | Kleinere Höhe/Padding | Visual |
| BTN-S02 | size="default" | Standard Größe | Visual |
| BTN-S03 | size="large" | Größere Höhe/Padding | Visual |

### Icons

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-I01 | prepend-icon="mdi-plus" | Icon links vor Text | Visual |
| BTN-I02 | append-icon="mdi-arrow-right" | Icon rechts nach Text | Visual |
| BTN-I03 | Nur Icon (kein Text) | Icon zentriert | Visual |

### States

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-ST01 | loading=true | Spinner anstatt Content | E2E |
| BTN-ST02 | disabled=true | Ausgegraut, nicht klickbar | E2E |
| BTN-ST03 | block=true | Volle Breite | Visual |
| BTN-ST04 | Hover | Brightness +10%, translateY(-1px) | Visual |
| BTN-ST05 | Focus | 2px Outline primary | A11y |
| BTN-ST06 | Active (gedrückt) | Scale(0.98) | Visual |

### Tooltip

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-T01 | tooltip="Hilfe" | Tooltip bei Hover | E2E |
| BTN-T02 | tooltipLocation="top" | Tooltip oben | E2E |
| BTN-T03 | tooltipLocation="bottom" | Tooltip unten | E2E |
| BTN-T04 | tooltipLocation="left" | Tooltip links | E2E |
| BTN-T05 | tooltipLocation="right" | Tooltip rechts | E2E |

### Events

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| BTN-E01 | @click | Event fired | Unit |
| BTN-E02 | @click disabled | Kein Event | Unit |
| BTN-E03 | @click loading | Kein Event | Unit |

---

## 2. LIconBtn (Icon-Button)

**Datei:** `llars-frontend/src/components/common/LIconBtn.vue`

### Varianten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| IBTN-V01 | variant="default" | Grauer Hintergrund | Visual |
| IBTN-V02 | variant="primary" | Primary Hintergrund | Visual |
| IBTN-V03 | variant="danger" | Danger Hintergrund | Visual |
| IBTN-V04 | variant="success" | Success Hintergrund | Visual |
| IBTN-V05 | variant="warning" | Warning Hintergrund | Visual |

### Größen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| IBTN-S01 | size="x-small" | 20px | Visual |
| IBTN-S02 | size="small" | 28px | Visual |
| IBTN-S03 | size="default" | 36px | Visual |
| IBTN-S04 | size="large" | 44px | Visual |
| IBTN-S05 | size="x-large" | 52px | Visual |

### Accessibility

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| IBTN-A01 | aria-label von tooltip | Korrekt gesetzt | A11y |
| IBTN-A02 | Keyboard fokussierbar | Tab erreicht Button | A11y |
| IBTN-A03 | Enter/Space aktiviert | Click-Event | A11y |

---

## 3. LTag (Tag/Chip-Komponente)

**Datei:** `llars-frontend/src/components/common/LTag.vue`

### Varianten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TAG-V01 | variant="primary" | Primary Farbe | Visual |
| TAG-V02 | variant="secondary" | Secondary Farbe | Visual |
| TAG-V03 | variant="accent" | Accent Farbe | Visual |
| TAG-V04 | variant="success" | Success Farbe | Visual |
| TAG-V05 | variant="info" | Info Farbe | Visual |
| TAG-V06 | variant="warning" | Warning Farbe | Visual |
| TAG-V07 | variant="danger" | Danger Farbe | Visual |
| TAG-V08 | variant="gray" | Gray Farbe | Visual |

### Größen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TAG-S01 | size="sm" | Klein (20px) | Visual |
| TAG-S02 | size="md" | Medium (24px) | Visual |
| TAG-S03 | size="lg" | Groß (32px) | Visual |

### Features

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TAG-F01 | closable=true | X-Button sichtbar | E2E |
| TAG-F02 | closable @close | Event fired | E2E |
| TAG-F03 | clickable=true | Pointer Cursor | E2E |
| TAG-F04 | clickable @click | Event fired | E2E |
| TAG-F05 | prepend-icon | Icon links | Visual |
| TAG-F06 | append-icon | Icon rechts | Visual |

---

## 4. LSlider (Gradient-Slider)

**Datei:** `llars-frontend/src/components/common/LSlider.vue`

### Initialzustand

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SLD-I01 | Initial grau | Slider grau bis Touch | E2E |
| SLD-I02 | startActive=true | Sofort farbig | E2E |
| SLD-I03 | Nach Touch | Slider wird farbig | E2E |

### Gradient Farben

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SLD-G01 | Wert 0-30% | Rot (#e8a087) | Visual |
| SLD-G02 | Wert 31-70% | Gelb (#e8c87a) | Visual |
| SLD-G03 | Wert 71-100% | Grün (#98d4bb) | Visual |

### Fixed Color Mode

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SLD-F01 | colorMode="fixed" | Feste Farbe | Visual |
| SLD-F02 | color="primary" | Primary Farbe | Visual |

### Interaktion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SLD-INT01 | Drag Thumb | Wert ändert sich | E2E |
| SLD-INT02 | Click auf Track | Wert springt | E2E |
| SLD-INT03 | Keyboard Arrow | +/- step | A11y |
| SLD-INT04 | min/max respektiert | Wert nicht außerhalb | E2E |
| SLD-INT05 | step respektiert | Korrekte Schritte | E2E |

### Events

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SLD-E01 | @update:modelValue | Bei jeder Änderung | Unit |
| SLD-E02 | @change | Bei Release | Unit |
| SLD-E03 | @touched | Bei erster Interaktion | Unit |

---

## 5. LTooltip (Tooltip-Wrapper)

**Datei:** `llars-frontend/src/components/common/LTooltip.vue`

### Positionen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TTP-P01 | location="top" | Tooltip oben | E2E |
| TTP-P02 | location="bottom" | Tooltip unten | E2E |
| TTP-P03 | location="left" | Tooltip links | E2E |
| TTP-P04 | location="right" | Tooltip rechts | E2E |
| TTP-P05 | location="start" | Tooltip am Start | E2E |
| TTP-P06 | location="end" | Tooltip am Ende | E2E |

### Timing

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TTP-T01 | openDelay=300 (default) | 300ms Verzögerung | E2E |
| TTP-T02 | openDelay=0 | Sofort sichtbar | E2E |
| TTP-T03 | closeDelay=0 (default) | Sofort ausblenden | E2E |
| TTP-T04 | closeDelay=500 | 500ms verzögert | E2E |

### Content

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TTP-C01 | text="Hilfe" | Text angezeigt | E2E |
| TTP-C02 | #content Slot | Custom HTML | E2E |
| TTP-C03 | Langer Text | Richtig umbrechen | Visual |

---

## 6. LActionGroup (Action-Buttons)

**Datei:** `llars-frontend/src/components/common/LActionGroup.vue`

### Presets

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ACT-P01 | "view" | Auge-Icon, Tooltip "Anzeigen" | E2E |
| ACT-P02 | "edit" | Stift-Icon, Tooltip "Bearbeiten" | E2E |
| ACT-P03 | "delete" | Mülleimer-Icon, Danger-Farbe | E2E |
| ACT-P04 | "stats" | Chart-Icon | E2E |
| ACT-P05 | "download" | Download-Icon | E2E |
| ACT-P06 | "copy" | Copy-Icon | E2E |
| ACT-P07 | "lock" | Schloss-Icon | E2E |
| ACT-P08 | "unlock" | Schloss-offen-Icon | E2E |
| ACT-P09 | "refresh" | Refresh-Icon | E2E |
| ACT-P10 | "close" | X-Icon | E2E |
| ACT-P11 | "add" | Plus-Icon, Success-Farbe | E2E |
| ACT-P12 | "settings" | Zahnrad-Icon | E2E |
| ACT-P13 | "play" | Play-Icon | E2E |
| ACT-P14 | "pause" | Pause-Icon | E2E |
| ACT-P15 | "stop" | Stop-Icon | E2E |

### Custom Actions

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ACT-C01 | Custom icon | Icon angezeigt | E2E |
| ACT-C02 | Custom tooltip | Tooltip angezeigt | E2E |
| ACT-C03 | Custom variant | Farbe korrekt | E2E |
| ACT-C04 | loading=true | Spinner | E2E |
| ACT-C05 | disabled=true | Ausgegraut | E2E |

### Events

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ACT-E01 | @action | (key, action) emitted | Unit |
| ACT-E02 | Action disabled | Kein Event | Unit |

---

## 7. LCard (Card-Komponente)

**Datei:** `llars-frontend/src/components/common/LCard.vue`

### Header

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CARD-H01 | title | Titel angezeigt | Visual |
| CARD-H02 | subtitle | Untertitel angezeigt | Visual |
| CARD-H03 | icon | Avatar mit Icon | Visual |
| CARD-H04 | color | Akzentfarbe (Border-Top) | Visual |

### Status

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CARD-S01 | status="Aktiv" | Badge angezeigt | Visual |
| CARD-S02 | statusVariant="success" | Grünes Badge | Visual |
| CARD-S03 | statusVariant="danger" | Rotes Badge | Visual |

### Stats

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CARD-ST01 | stats Array | Stats-Row angezeigt | Visual |
| CARD-ST02 | stats.icon | Icon pro Stat | Visual |
| CARD-ST03 | stats.value | Wert angezeigt | Visual |
| CARD-ST04 | stats.label | Label angezeigt | Visual |

### Interaktion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CARD-I01 | clickable=true | Hover-Effekt | E2E |
| CARD-I02 | clickable @click | Event fired | E2E |
| CARD-I03 | flat=true | Kein Schatten | Visual |
| CARD-I04 | outlined=true | Border statt Elevation | Visual |

---

## 8. LTabs (Tab-Navigation)

**Datei:** `llars-frontend/src/components/common/LTabs.vue`

### Tabs

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TABS-T01 | tabs Array | Alle Tabs angezeigt | Visual |
| TABS-T02 | tab.label | Label sichtbar | Visual |
| TABS-T03 | tab.icon | Icon sichtbar | Visual |
| TABS-T04 | tab.badge | Badge-Zahl angezeigt | Visual |

### Varianten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TABS-V01 | variant="filled" (default) | Gefüllter Hintergrund | Visual |
| TABS-V02 | variant="outlined" | Border ohne Fill | Visual |
| TABS-V03 | variant="underlined" | Unterstreichung | Visual |

### Interaktion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| TABS-I01 | Tab klicken | v-model aktualisiert | E2E |
| TABS-I02 | Aktiver Tab | Visuell hervorgehoben | Visual |
| TABS-I03 | grow=true | Gleiche Breite | Visual |

---

## 9. LAvatar (Avatar-Komponente)

**Datei:** `llars-frontend/src/components/common/LAvatar.vue`

### Größen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AVA-S01 | size="xs" | 24px | Visual |
| AVA-S02 | size="sm" | 32px | Visual |
| AVA-S03 | size="md" (default) | 40px | Visual |
| AVA-S04 | size="lg" | 56px | Visual |
| AVA-S05 | size="xl" | 80px | Visual |

### Quellen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AVA-Q01 | seed="abc" | DiceBear generiert | Visual |
| AVA-Q02 | src="url" | Custom Image | Visual |
| AVA-Q03 | username (fallback) | Initiale | Visual |

### Varianten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AVA-V01 | variant="bottts-neutral" | Robot-Style | Visual |
| AVA-V02 | variant="shapes" | Geometrisch | Visual |
| AVA-V03 | variant="fun-emoji" | Emoji-Style | Visual |
| AVA-V04 | variant="identicon" | Identicon | Visual |

---

## 10. LChart (Chart-Komponente)

**Datei:** `llars-frontend/src/components/common/LChart.vue`

### Daten

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHART-D01 | data Array | Linie gezeichnet | Visual |
| CHART-D02 | series Array | Mehrere Linien | Visual |
| CHART-D03 | Leere Daten | Empty State | Visual |

### Optionen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| CHART-O01 | fill=true | Gradient-Fill | Visual |
| CHART-O02 | grid=true | Grid-Linien | Visual |
| CHART-O03 | smooth=true | Bezier-Kurven | Visual |
| CHART-O04 | title | Titel angezeigt | Visual |
| CHART-O05 | loading=true | Loading-State | Visual |

---

## 11. LGauge (Metrik-Anzeige)

**Datei:** `llars-frontend/src/components/common/LGauge.vue`

### Anzeige

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| GAUGE-A01 | icon | Icon angezeigt | Visual |
| GAUGE-A02 | label | Label angezeigt | Visual |
| GAUGE-A03 | value | Wert angezeigt | Visual |
| GAUGE-A04 | suffix | Suffix nach Wert | Visual |
| GAUGE-A05 | percent | Prozent-Bar | Visual |

### Farben

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| GAUGE-C01 | colorMode="threshold" | Auto-Farbe | Visual |
| GAUGE-C02 | percent < 60% | Grün | Visual |
| GAUGE-C03 | percent 60-80% | Gelb | Visual |
| GAUGE-C04 | percent > 80% | Rot | Visual |
| GAUGE-C05 | colorMode="fixed" | Feste Farbe | Visual |

---

## 12. LLoading (Loading-Animation)

**Datei:** `llars-frontend/src/components/common/LLoading.vue`

### Größen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LOAD-S01 | size="sm" | Klein | Visual |
| LOAD-S02 | size="md" (default) | Medium | Visual |
| LOAD-S03 | size="lg" | Groß | Visual |

### Features

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| LOAD-F01 | label="Loading..." | Label angezeigt | Visual |
| LOAD-F02 | Animation läuft | Floating-Effekt | Visual |
| LOAD-F03 | prefers-reduced-motion | Animation reduziert | A11y |

---

## 13. LUserSearch (User-Suche)

**Datei:** `llars-frontend/src/components/common/LUserSearch.vue`

### Suche

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USRCH-S01 | Tippen | Debounced API-Call | E2E |
| USRCH-S02 | Ergebnisse | Dropdown angezeigt | E2E |
| USRCH-S03 | User auswählen | v-model aktualisiert | E2E |
| USRCH-S04 | Avatar in Liste | Avatare angezeigt | Visual |

### Buttons

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USRCH-B01 | showAddButton=true | Add-Button sichtbar | E2E |
| USRCH-B02 | Add klicken | @add Event | E2E |

---

## 14. LThemeToggle (Theme-Umschalter)

**Datei:** `llars-frontend/src/components/common/LThemeToggle.vue`

### Optionen

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| THEME-O01 | System | System-Theme aktiv | E2E |
| THEME-O02 | Light | Helles Theme | E2E |
| THEME-O03 | Dark | Dunkles Theme | E2E |

### Interaktion

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| THEME-I01 | Menu öffnet | Optionen sichtbar | E2E |
| THEME-I02 | Option wählen | Theme wechselt | E2E |
| THEME-I03 | Checkmark | Aktive Option markiert | Visual |

---

## 15. Test-Code für Komponenten

```typescript
// e2e/components/lbtn.spec.ts
import { test, expect } from '@playwright/test'

test.describe('LBtn Component', () => {
  test('BTN-V01: primary variant has correct color', async ({ page }) => {
    await page.goto('/component-test')
    const btn = page.locator('button.l-btn.primary')
    await expect(btn).toHaveCSS('background-color', 'rgb(176, 202, 151)')
  })

  test('BTN-ST01: loading state shows spinner', async ({ page }) => {
    await page.goto('/component-test')
    const btn = page.locator('button.l-btn[loading]')
    await expect(btn.locator('.v-progress-circular')).toBeVisible()
  })

  test('BTN-ST02: disabled button not clickable', async ({ page }) => {
    await page.goto('/component-test')
    const btn = page.locator('button.l-btn[disabled]')
    await expect(btn).toBeDisabled()
  })

  test('BTN-T01: tooltip appears on hover', async ({ page }) => {
    await page.goto('/component-test')
    const btn = page.locator('button.l-btn[data-tooltip="Hilfe"]')
    await btn.hover()
    await expect(page.locator('.v-tooltip')).toBeVisible()
  })

  test('BTN-E01: click event fires', async ({ page }) => {
    await page.goto('/component-test')
    const btn = page.locator('button.l-btn.clickable')
    await btn.click()
    await expect(page.locator('.click-result')).toHaveText('clicked')
  })
})
```

```javascript
// vitest/components/LSlider.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LSlider from '@/components/common/LSlider.vue'

describe('LSlider', () => {
  it('SLD-I01: starts gray when not touched', () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 50 }
    })
    expect(wrapper.classes()).toContain('inactive')
  })

  it('SLD-G01: low value has red color', async () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 20, startActive: true }
    })
    const color = wrapper.vm.gradientColor
    expect(color).toContain('#e8a087')
  })

  it('SLD-E03: touched event fires on first interaction', async () => {
    const wrapper = mount(LSlider, {
      props: { modelValue: 50 }
    })
    await wrapper.find('input').trigger('input')
    expect(wrapper.emitted('touched')).toBeTruthy()
  })
})
```

---

## 16. Checkliste für manuelle Tests

### Buttons (LBtn)
- [ ] Alle Varianten visuell korrekt
- [ ] Alle Größen korrekt
- [ ] Loading-State zeigt Spinner
- [ ] Disabled-State nicht klickbar
- [ ] Hover-Effekt funktioniert
- [ ] Focus-Outline sichtbar
- [ ] Tooltip erscheint

### Slider (LSlider)
- [ ] Initial grau
- [ ] Wird farbig nach Touch
- [ ] Gradient korrekt (rot→gelb→grün)
- [ ] Keyboard-Navigation funktioniert
- [ ] Min/Max respektiert

### Tags (LTag)
- [ ] Alle Varianten korrekt
- [ ] Closable zeigt X
- [ ] Close-Event funktioniert
- [ ] Clickable-Cursor

### Cards (LCard)
- [ ] Titel/Subtitle korrekt
- [ ] Avatar mit Icon
- [ ] Status-Badge korrekt
- [ ] Stats angezeigt
- [ ] Clickable Hover-Effekt

### Tooltips (LTooltip)
- [ ] Alle Positionen funktionieren
- [ ] Timing korrekt
- [ ] Custom Content funktioniert

---

**Letzte Aktualisierung:** 30. Dezember 2025
