# Frontend Testanforderungen: Evaluation Features

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für die Evaluations-Features: Ranking, Rating, Judge, OnCoCo, KAIMO.

---

## 1. Ranker (`/Ranker`)

**Komponente:** `Ranker.vue`, `RankerDetail.vue`
**Priorität:** P1
**Permission:** `feature:ranking:view`

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RANK-001 | Übersicht lädt | Thread-Liste sichtbar | E2E |
| RANK-002 | Threads nach Szenario | Nur zugewiesene Threads | E2E |
| RANK-003 | Status-Badge | Fertig/Offen-Status korrekt | E2E |
| RANK-004 | Thread anklicken | Detail-Ansicht öffnet | E2E |
| RANK-005 | Features laden | Alle Features des Threads | E2E |
| RANK-006 | Drag & Drop | Features umsortierbar | E2E |
| RANK-007 | Ranking speichern | API-Call erfolgreich | E2E |
| RANK-008 | Ranking laden | Gespeichertes Ranking angezeigt | E2E |
| RANK-009 | Fortschritt aktualisiert | Nach Speichern Status "Fertig" | E2E |
| RANK-010 | Navigation zurück | Zurück zur Übersicht | E2E |

### Drag & Drop Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RANK-DD1 | Feature nach oben ziehen | Reihenfolge ändert sich | E2E |
| RANK-DD2 | Feature nach unten ziehen | Reihenfolge ändert sich | E2E |
| RANK-DD3 | Feature an gleiche Stelle | Keine Änderung | E2E |
| RANK-DD4 | Keyboard Drag | Mit Tastatur sortierbar | E2E |
| RANK-DD5 | Touch Drag | Auf Mobile sortierbar | E2E |

### E2E Test-Code

```typescript
// e2e/evaluation/ranker.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Ranker', () => {
  test('RANK-001: overview loads threads', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Ranker')
    await expect(authenticatedPage.locator('.thread-card')).toHaveCount(1, { min: true })
  })

  test('RANK-006: drag and drop works', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Ranker/1')

    // Erste und zweite Feature-Position merken
    const features = authenticatedPage.locator('.feature-item')
    const firstFeature = await features.nth(0).textContent()
    const secondFeature = await features.nth(1).textContent()

    // Drag first to second position
    await features.nth(0).dragTo(features.nth(1))

    // Prüfe neue Reihenfolge
    const newFirst = await features.nth(0).textContent()
    expect(newFirst).toBe(secondFeature)
  })

  test('RANK-007: save ranking', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/Ranker/1')

    // Speichern klicken
    await authenticatedPage.click('button:has-text("Speichern")')

    // Success-Snackbar
    await expect(authenticatedPage.locator('.v-snackbar')).toContainText('gespeichert')
  })
})
```

---

## 2. Rater (`/Rater`)

**Komponente:** `Rater.vue`, `RaterDetail.vue`, `RaterDetailFeature.vue`
**Priorität:** P1
**Permission:** `feature:rating:view`

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RATE-001 | Übersicht lädt | Thread-Liste sichtbar | E2E |
| RATE-002 | Thread anklicken | Feature-Liste öffnet | E2E |
| RATE-003 | Feature anklicken | Rating-Interface öffnet | E2E |
| RATE-004 | Rating-Skala | 1-5 Sterne/Slider sichtbar | E2E |
| RATE-005 | Rating speichern | API-Call erfolgreich | E2E |
| RATE-006 | Rating laden | Gespeichertes Rating angezeigt | E2E |
| RATE-007 | Nächstes Feature | Navigation zu nächstem | E2E |
| RATE-008 | Vorheriges Feature | Navigation zu vorherigem | E2E |
| RATE-009 | Alle Features bewertet | Thread als "Fertig" markiert | E2E |
| RATE-010 | Kommentar speichern | Freitext-Kommentar gespeichert | E2E |

### Rating-Interface Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| RATE-UI1 | Slider bewegen | Wert ändert sich | E2E |
| RATE-UI2 | Sterne klicken | Rating gesetzt | E2E |
| RATE-UI3 | Kategorie wählen | Selection markiert | E2E |
| RATE-UI4 | Kommentarfeld | Text eingebbar | E2E |
| RATE-UI5 | Formular validiert | Pflichtfelder geprüft | E2E |

---

## 3. LLM-as-Judge (`/judge`)

**Komponente:** `JudgeOverview.vue`, `JudgeConfig.vue`, `JudgeSession.vue`, `JudgeResults.vue`
**Priorität:** P1
**Permission:** `feature:judge:view`, `feature:judge:edit`

### Übersicht Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-001 | Übersicht lädt | Session-Liste sichtbar | E2E |
| JUDGE-002 | Neue Session | Config-Dialog öffnet | E2E |
| JUDGE-003 | Status-Filter | Sessions nach Status filtern | E2E |
| JUDGE-004 | Session anklicken | Detail-Ansicht öffnet | E2E |
| JUDGE-005 | Session löschen | Session entfernt | E2E |

### Konfiguration Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-C01 | Name eingeben | Name gespeichert | E2E |
| JUDGE-C02 | Pillars auswählen | Pillars selektierbar | E2E |
| JUDGE-C03 | LLM auswählen | Model selektierbar | E2E |
| JUDGE-C04 | Worker-Anzahl | 1-10 Worker einstellbar | E2E |
| JUDGE-C05 | Comparison Mode | Mode auswählbar | E2E |
| JUDGE-C06 | Estimation | Geschätzte Vergleiche angezeigt | E2E |
| JUDGE-C07 | Session erstellen | Session in DB angelegt | E2E |

### Session Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-S01 | Session starten | Status wechselt zu "running" | E2E |
| JUDGE-S02 | Session pausieren | Status wechselt zu "paused" | E2E |
| JUDGE-S03 | Session fortsetzen | Status wechselt zu "running" | E2E |
| JUDGE-S04 | Progress Bar | Fortschritt aktualisiert | E2E |
| JUDGE-S05 | Worker Lanes | Alle Worker sichtbar | E2E |
| JUDGE-S06 | Streaming | LLM-Output streamt | E2E |
| JUDGE-S07 | Queue Panel | Warteschlange sichtbar | E2E |
| JUDGE-S08 | History Table | Abgeschlossene Vergleiche | E2E |
| JUDGE-S09 | Fullscreen Mode | Fullscreen Dialog öffnet | E2E |
| JUDGE-S10 | Multi-Worker View | Grid-Ansicht funktioniert | E2E |

### Ergebnis Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| JUDGE-R01 | Ergebnisse laden | Statistics sichtbar | E2E |
| JUDGE-R02 | Ranking-Tabelle | LLMs gerankt | E2E |
| JUDGE-R03 | Thread Performance | Pro-Thread Analyse | E2E |
| JUDGE-R04 | Transition Matrix | Matrix-Heatmap | E2E |
| JUDGE-R05 | Position Swap | Bias-Analyse | E2E |
| JUDGE-R06 | Verbosity Analysis | Längen-Analyse | E2E |
| JUDGE-R07 | Export CSV | Download funktioniert | E2E |
| JUDGE-R08 | Export JSON | Download funktioniert | E2E |

### E2E Test-Code

```typescript
// e2e/evaluation/judge.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('LLM-as-Judge', () => {
  test('JUDGE-001: overview loads', async ({ adminPage }) => {
    await adminPage.goto('/judge')
    await expect(adminPage.locator('.session-list')).toBeVisible()
  })

  test('JUDGE-S01: start session', async ({ adminPage }) => {
    await adminPage.goto('/judge/session/1')

    await adminPage.click('button:has-text("Starten")')

    await expect(adminPage.locator('.status-badge')).toContainText('running', {
      timeout: 10000
    })
  })

  test('JUDGE-S06: LLM streaming works', async ({ adminPage }) => {
    await adminPage.goto('/judge/session/1')

    // Session starten
    await adminPage.click('button:has-text("Starten")')

    // Warten auf ersten Stream
    await expect(adminPage.locator('.worker-output')).toContainText(/\w+/, {
      timeout: 30000
    })
  })
})
```

---

## 4. OnCoCo (`/oncoco`)

**Komponente:** `OnCoCoOverview.vue`, `OnCoCoConfig.vue`, `OnCoCoResults.vue`
**Priorität:** P1
**Permission:** `feature:oncoco:view`, `feature:oncoco:edit`

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ONCO-001 | Übersicht lädt | Analyse-Liste sichtbar | E2E |
| ONCO-002 | Neue Analyse | Config-Dialog öffnet | E2E |
| ONCO-003 | Analyse konfigurieren | Parameter einstellbar | E2E |
| ONCO-004 | Analyse starten | Processing beginnt | E2E |
| ONCO-005 | Progress tracking | Fortschritt sichtbar | E2E |
| ONCO-006 | Ergebnisse laden | Results-View öffnet | E2E |
| ONCO-007 | Transition Matrix | Heatmap angezeigt | E2E |
| ONCO-008 | Statistics | Chi-Square, Effektstärke | E2E |
| ONCO-009 | Pillar Comparison | Vergleichs-Panel | E2E |
| ONCO-010 | Export | Daten exportierbar | E2E |

---

## 5. KAIMO (`/kaimo`)

**Komponente:** `KaimoHub.vue`, `KaimoPanel.vue`, `KaimoCase.vue`, `KaimoCaseEditor.vue`
**Priorität:** P2
**Permission:** `feature:kaimo:view`, `feature:kaimo:edit`, `admin:kaimo:manage`

### Hub Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KAIMO-001 | Hub lädt | Case-Grid sichtbar | E2E |
| KAIMO-002 | Kategorien angezeigt | Category-Filter funktioniert | E2E |
| KAIMO-003 | Case anklicken | Case-Detail öffnet | E2E |
| KAIMO-004 | Neuer Case (Admin) | Editor öffnet | E2E |
| KAIMO-005 | Published Badge | Status korrekt angezeigt | E2E |

### Case Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KAIMO-C01 | Case laden | Alle Tabs sichtbar | E2E |
| KAIMO-C02 | Documents Tab | Dokumente angezeigt | E2E |
| KAIMO-C03 | Assessment Tab | Bewertungsformular | E2E |
| KAIMO-C04 | Diagram Tab | Visualisierung | E2E |
| KAIMO-C05 | Hint anzeigen | Hinweis einblenden | E2E |
| KAIMO-C06 | Assessment speichern | Bewertung gespeichert | E2E |
| KAIMO-C07 | Case abschließen | Completion markiert | E2E |

### Admin Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| KAIMO-A01 | Case erstellen | Neuer Case in DB | E2E |
| KAIMO-A02 | Case editieren | Änderungen gespeichert | E2E |
| KAIMO-A03 | Case publizieren | Status = published | E2E |
| KAIMO-A04 | Hint hinzufügen | Hint gespeichert | E2E |
| KAIMO-A05 | Document hinzufügen | Dokument verknüpft | E2E |
| KAIMO-A06 | Ergebnisse einsehen | Results-View | E2E |

---

## 6. Authenticity (Fake/Echt) (`/authenticity`)

**Komponente:** `AuthenticityOverview.vue`, `AuthenticityDetail.vue`
**Priorität:** P2
**Permission:** `feature:authenticity:view`, `feature:authenticity:edit`

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| AUTH-001 | Übersicht lädt | Thread-Cards sichtbar | E2E |
| AUTH-002 | Thread anklicken | Detail-Ansicht | E2E |
| AUTH-003 | Konversation lesen | Messages angezeigt | E2E |
| AUTH-004 | Vote "Echt" | Vote gespeichert | E2E |
| AUTH-005 | Vote "Fake" | Vote gespeichert | E2E |
| AUTH-006 | Vote ändern | Änderung möglich | E2E |
| AUTH-007 | Completion Badge | Nach Vote markiert | E2E |

---

## 7. Evaluation Hub (`/evaluation`)

**Komponente:** `EvaluationHub.vue`
**Priorität:** P1

### Funktionale Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| EVAL-001 | Hub lädt | Tool-Grid sichtbar | E2E |
| EVAL-002 | Tools gefiltert | Nur erlaubte Tools | E2E |
| EVAL-003 | Scenario Count | Anzahl pro Tool korrekt | E2E |
| EVAL-004 | Disabled State | Tools ohne Szenarien grau | E2E |
| EVAL-005 | Tool anklicken | Navigation korrekt | E2E |

---

## Checkliste für manuelle Tests

### Ranking/Rating
- [ ] Alle Threads des Szenarios sichtbar
- [ ] Zeitraum wird beachtet (begin/end)
- [ ] RATER vs EVALUATOR Unterschied
- [ ] Distribution Mode funktioniert
- [ ] Order Mode (shuffle) funktioniert

### Judge
- [ ] Mehrere Worker parallel
- [ ] Session Pause/Resume
- [ ] Ergebnisse nach Completion
- [ ] KIA Sync (wenn aktiviert)

### OnCoCo
- [ ] Dialogue Classification Labels
- [ ] Statistical Tests korrekt
- [ ] Outlier Detection

### KAIMO
- [ ] Researcher kann bewerten
- [ ] Admin kann Cases verwalten
- [ ] Hints werden gezählt

---

**Letzte Aktualisierung:** 30. Dezember 2025
