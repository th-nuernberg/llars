# Frontend Testanforderungen: Admin Dashboard

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument beschreibt alle Tests für das Admin Dashboard und seine Sektionen.

---

## 1. Admin Dashboard (`/admin`)

**Komponente:** `AdminDashboard.vue`
**Priorität:** P0
**Permission:** Admin-Rolle oder `chatbot_manager`

### Zugriffs-Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ADM-001 | Admin sieht alle Tabs | Alle Sektionen sichtbar | E2E |
| ADM-002 | Chatbot_Manager Tabs | Nur Chatbot + RAG Tabs | E2E |
| ADM-003 | Researcher keinen Zugang | Redirect oder 403 | E2E |
| ADM-004 | Viewer keinen Zugang | Redirect oder 403 | E2E |
| ADM-005 | Tab-Navigation | Tabs wechseln korrekt | E2E |
| ADM-006 | URL Query-Param | `?tab=` lädt korrekten Tab | E2E |
| ADM-007 | Staggered Loading | Sections laden nacheinander | E2E |

### E2E Test-Code

```typescript
// e2e/admin/dashboard.spec.ts
import { test, expect, testUsers, login } from '../fixtures/auth'

test.describe('Admin Dashboard Access', () => {
  test('ADM-001: admin sees all tabs', async ({ page }) => {
    await login(page, testUsers.admin)
    await page.goto('/admin')

    await expect(page.locator('[data-tab="overview"]')).toBeVisible()
    await expect(page.locator('[data-tab="docker"]')).toBeVisible()
    await expect(page.locator('[data-tab="db"]')).toBeVisible()
    await expect(page.locator('[data-tab="users"]')).toBeVisible()
    await expect(page.locator('[data-tab="permissions"]')).toBeVisible()
  })

  test('ADM-003: researcher cannot access', async ({ page }) => {
    await login(page, testUsers.researcher)
    await page.goto('/admin')

    // Sollte nicht auf /admin bleiben
    await expect(page).not.toHaveURL(/.*admin/)
  })

  test('ADM-004: evaluator cannot access', async ({ page }) => {
    await login(page, testUsers.evaluator)
    await page.goto('/admin')

    await expect(page).not.toHaveURL(/.*admin/)
  })
})
```

---

## 2. Docker Monitor

**Komponente:** `AdminDockerMonitorSection.vue`
**Socket.IO Namespace:** `/admin`
**Permission:** `admin:system:configure`

### Container Status Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DOCKER-001 | Sektion lädt | Container-Liste sichtbar | E2E |
| DOCKER-002 | Container Count | Anzahl korrekt | E2E |
| DOCKER-003 | Status Badges | running/exited/unhealthy | E2E |
| DOCKER-004 | CPU Usage | Prozent angezeigt | E2E |
| DOCKER-005 | Memory Usage | MB/GB angezeigt | E2E |
| DOCKER-006 | Network I/O | RX/TX Bytes | E2E |
| DOCKER-007 | Refresh | Stats aktualisieren | E2E |
| DOCKER-008 | Scope Filter | Project/All Filter | E2E |

### Charts Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DOCKER-C01 | CPU Chart | Live-Chart aktualisiert | E2E |
| DOCKER-C02 | Memory Chart | Live-Chart aktualisiert | E2E |
| DOCKER-C03 | Chart History | 60 Datenpunkte | E2E |
| DOCKER-C04 | Chart Hover | Tooltip mit Wert | E2E |

### Logs Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DOCKER-L01 | Logs Tab | Log-Viewer sichtbar | E2E |
| DOCKER-L02 | Container auswählen | Logs für Container | E2E |
| DOCKER-L03 | Log Streaming | Neue Logs erscheinen | E2E |
| DOCKER-L04 | Tail Selector | 100/500/1000 Lines | E2E |
| DOCKER-L05 | Log Pause | Streaming pausierbar | E2E |
| DOCKER-L06 | ANSI Colors | Farben korrekt | E2E |
| DOCKER-L07 | Log Search | Filter funktioniert | E2E |

### E2E Test-Code

```typescript
// e2e/admin/docker-monitor.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Docker Monitor', () => {
  test('DOCKER-001: shows container list', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=docker')

    await expect(adminPage.locator('.container-table')).toBeVisible({ timeout: 10000 })
    await expect(adminPage.locator('.container-row')).toHaveCount(1, { min: true })
  })

  test('DOCKER-003: status badges shown', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=docker')

    const statusBadge = adminPage.locator('.status-badge >> nth=0')
    await expect(statusBadge).toBeVisible()
    await expect(statusBadge).toHaveText(/running|exited|restarting/)
  })

  test('DOCKER-L03: log streaming works', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=docker')

    // Logs Tab öffnen
    await adminPage.click('[data-tab="logs"]')

    // Container wählen
    await adminPage.selectOption('.container-select', { index: 0 })

    // Warten auf erste Logs
    await expect(adminPage.locator('.log-line')).toHaveCount(1, { min: true, timeout: 10000 })
  })
})
```

---

## 3. Database Explorer

**Komponente:** `AdminDatabaseSection.vue`
**Socket.IO Namespace:** `/admin`
**Permission:** `admin:system:configure`

### Table List Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DB-001 | Sektion lädt | Table-Liste sichtbar | E2E |
| DB-002 | Table Count | Anzahl Tabellen korrekt | E2E |
| DB-003 | Row Count | Zeilen pro Tabelle | E2E |
| DB-004 | Table Search | Filter funktioniert | E2E |
| DB-005 | Table wählen | Daten werden geladen | E2E |

### Table Viewer Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| DB-V01 | Columns angezeigt | Spalten-Header | E2E |
| DB-V02 | Rows angezeigt | Datenzeilen | E2E |
| DB-V03 | Row Limit | 1-200 Zeilen einstellbar | E2E |
| DB-V04 | Search in Table | Filter über Zeilen | E2E |
| DB-V05 | Null Values | "null" formatiert | E2E |
| DB-V06 | Boolean Values | true/false formatiert | E2E |
| DB-V07 | JSON Objects | Formatiert angezeigt | E2E |
| DB-V08 | Long Text | Truncated (100 chars) | E2E |
| DB-V09 | Refresh | Daten neu laden | E2E |
| DB-V10 | Polling | Auto-Update alle 1.5s | E2E |

### E2E Test-Code

```typescript
// e2e/admin/db-explorer.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Database Explorer', () => {
  test('DB-001: shows table list', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=db')

    await expect(adminPage.locator('.table-list')).toBeVisible({ timeout: 10000 })
    await expect(adminPage.locator('.table-item')).toHaveCount(1, { min: true })
  })

  test('DB-005: selecting table loads data', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=db')

    // Erste Tabelle wählen
    await adminPage.click('.table-item >> nth=0')

    // Daten erscheinen
    await expect(adminPage.locator('.data-table')).toBeVisible({ timeout: 10000 })
    await expect(adminPage.locator('.data-row')).toHaveCount(1, { min: true })
  })
})
```

---

## 4. System Health

**Komponente:** `AdminSystemHealthSection.vue`
**Permission:** `admin:system:configure`

### Host Metrics Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| HEALTH-001 | Tab lädt | Metriken sichtbar | E2E |
| HEALTH-002 | CPU % | CPU-Auslastung | E2E |
| HEALTH-003 | Memory % | RAM-Auslastung | E2E |
| HEALTH-004 | Disk I/O | Lese/Schreib-Raten | E2E |
| HEALTH-005 | Network | Interface-Stats | E2E |
| HEALTH-006 | Process List | Top-Prozesse | E2E |
| HEALTH-007 | Refresh | Auto-Update 2s | E2E |

### API Performance Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| HEALTH-A01 | API Tab | Metriken sichtbar | E2E |
| HEALTH-A02 | Request Count | Anzahl Requests | E2E |
| HEALTH-A03 | Response Times | min/max/avg | E2E |
| HEALTH-A04 | Error Rates | Status-Code Breakdown | E2E |
| HEALTH-A05 | Time Window | 1min/5min/15min/1h | E2E |

### WebSocket Stats Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| HEALTH-W01 | WS Tab | Stats sichtbar | E2E |
| HEALTH-W02 | Connections | Pro Namespace | E2E |
| HEALTH-W03 | Messages | Throughput | E2E |
| HEALTH-W04 | Connect/Disconnect | Rates angezeigt | E2E |

---

## 5. System Events

**Komponente:** `AdminSystemMonitorSection.vue`
**Permission:** `admin:system:configure`

### Event Log Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| EVENT-001 | Log lädt | Event-Liste sichtbar | E2E |
| EVENT-002 | Event Details | Type, User, Time | E2E |
| EVENT-003 | Severity | Info/Warning/Error | E2E |
| EVENT-004 | Filter by Type | Type-Filter funktioniert | E2E |
| EVENT-005 | Search | Text-Suche | E2E |
| EVENT-006 | Pagination | Mehr Events laden | E2E |

---

## 6. System Settings

**Komponente:** `AdminSystemSettingsSection.vue`
**Permission:** `admin:system:configure`

### Settings Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SETTINGS-001 | Form lädt | Alle Felder sichtbar | E2E |
| SETTINGS-002 | Crawler Timeout | 60-86400s Range | E2E |
| SETTINGS-003 | Embedding Timeout | 60-86400s Range | E2E |
| SETTINGS-004 | Max Pages | 1-10000 Range | E2E |
| SETTINGS-005 | Max Depth | 1-10 Range | E2E |
| SETTINGS-006 | Chunk Size | 100-10000 Range | E2E |
| SETTINGS-007 | Chunk Overlap | 0-5000 Range | E2E |
| SETTINGS-008 | Speichern | API-Call erfolgreich | E2E |
| SETTINGS-009 | Validation | Out-of-Range Fehler | E2E |
| SETTINGS-010 | Event logged | Änderung in Events | E2E |

---

## 7. User Management

**Komponente:** `AdminUsersSection.vue`
**Permission:** `admin:users:manage`

### User List Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USER-001 | Liste lädt | User-Tabelle sichtbar | E2E |
| USER-002 | User Search | Filter funktioniert | E2E |
| USER-003 | Role Filter | Nach Rolle filtern | E2E |
| USER-004 | Status angezeigt | Active/Locked/Deleted | E2E |
| USER-005 | Rollen angezeigt | User-Rollen sichtbar | E2E |

### User CRUD Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| USER-C01 | User erstellen | Dialog öffnet | E2E |
| USER-C02 | Username eingeben | Validierung | E2E |
| USER-C03 | Rollen zuweisen | Multi-Select | E2E |
| USER-C04 | User speichern | In DB angelegt | E2E |
| USER-C05 | User editieren | Dialog mit Daten | E2E |
| USER-C06 | User sperren | Status = locked | E2E |
| USER-C07 | User entsperren | Status = active | E2E |
| USER-C08 | User löschen | Soft-Delete | E2E |
| USER-C09 | Collab-Farbe | Color Picker | E2E |
| USER-C10 | Avatar Seed | Avatar ändert sich | E2E |

### E2E Test-Code

```typescript
// e2e/admin/user-management.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('User Management', () => {
  test('USER-001: shows user list', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=users')

    await expect(adminPage.locator('.user-table')).toBeVisible()
    await expect(adminPage.locator('.user-row')).toHaveCount(1, { min: true })
  })

  test('USER-C06: lock user', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=users')

    // User-Zeile finden
    await adminPage.click('.user-row:has-text("evaluator") .action-lock')

    // Bestätigen
    await adminPage.click('button:has-text("Sperren")')

    // Status prüfen
    await expect(adminPage.locator('.user-row:has-text("evaluator") .status-badge')).toContainText('gesperrt')
  })

  test('USER-C04: create user', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=users')

    await adminPage.click('button:has-text("Neuer User")')

    await adminPage.fill('input[name="username"]', 'testuser_e2e')
    await adminPage.selectOption('select[name="roles"]', 'evaluator')
    await adminPage.click('button:has-text("Erstellen")')

    await expect(adminPage.locator('.v-snackbar')).toContainText('erstellt')
  })
})
```

---

## 8. Scenario Management

**Komponente:** `AdminScenariosSection.vue`
**Permission:** Admin-Rolle

### Scenario List Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SCEN-001 | Liste lädt | Scenario-Tabelle | E2E |
| SCEN-002 | Status-Filter | aktiv/ausstehend/beendet | E2E |
| SCEN-003 | Typ angezeigt | Rating/Ranking/Mail | E2E |
| SCEN-004 | Zeitraum | Begin/End Datum | E2E |
| SCEN-005 | User Count | Assigned Users | E2E |

### Scenario CRUD Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| SCEN-C01 | Neues Szenario | Dialog öffnet | E2E |
| SCEN-C02 | Name eingeben | Validierung | E2E |
| SCEN-C03 | Typ wählen | Dropdown | E2E |
| SCEN-C04 | Zeitraum wählen | Date Picker | E2E |
| SCEN-C05 | Threads hinzufügen | Multi-Select | E2E |
| SCEN-C06 | Users hinzufügen | RATER/VIEWER | E2E |
| SCEN-C07 | Distribution Mode | all/round_robin | E2E |
| SCEN-C08 | Order Mode | none/shuffle | E2E |
| SCEN-C09 | Speichern | In DB angelegt | E2E |
| SCEN-C10 | Editieren | Änderungen speichern | E2E |
| SCEN-C11 | Löschen | Szenario entfernt | E2E |

### E2E Test-Code

```typescript
// e2e/admin/scenario-management.spec.ts
import { test, expect } from '../fixtures/auth'

test.describe('Scenario Management', () => {
  test('SCEN-C09: create scenario', async ({ adminPage }) => {
    await adminPage.goto('/admin?tab=scenarios')

    await adminPage.click('button:has-text("Neues Szenario")')

    await adminPage.fill('input[name="name"]', 'E2E Test Szenario')
    await adminPage.selectOption('select[name="function_type"]', '1') // Ranking
    await adminPage.fill('input[name="begin"]', '2025-01-01')
    await adminPage.fill('input[name="end"]', '2025-12-31')

    await adminPage.click('button:has-text("Erstellen")')

    await expect(adminPage.locator('.v-snackbar')).toContainText('erstellt')
  })
})
```

---

## 9. Chatbot Activity

**Komponente:** `AdminChatbotActivitySection.vue`
**Permission:** `admin:system:configure`

### Activity Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ACTIVITY-001 | Panel lädt | Activity-Liste | E2E |
| ACTIVITY-002 | User angezeigt | Aktive User | E2E |
| ACTIVITY-003 | Chatbot angezeigt | Genutzte Bots | E2E |
| ACTIVITY-004 | Message Count | Nachrichten-Anzahl | E2E |
| ACTIVITY-005 | Real-time | Live-Updates | E2E |

---

## 10. Analytics Settings

**Komponente:** `AdminAnalyticsSection.vue`
**Permission:** `admin:system:configure`

### Matomo Config Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| ANALYTICS-001 | Form lädt | Alle Felder | E2E |
| ANALYTICS-002 | Matomo URL | URL-Input | E2E |
| ANALYTICS-003 | Site ID | Nummer | E2E |
| ANALYTICS-004 | Enable/Disable | Toggle | E2E |
| ANALYTICS-005 | Tracking Options | Checkboxen | E2E |
| ANALYTICS-006 | Speichern | API-Call | E2E |

---

## Checkliste für manuelle Tests

### Admin Zugang
- [ ] Admin sieht alle Tabs
- [ ] Chatbot_Manager nur Chatbot + RAG
- [ ] Researcher kein Zugang
- [ ] Viewer kein Zugang

### Docker Monitor
- [ ] Alle LLARS-Container sichtbar
- [ ] Status-Badges korrekt (running/exited)
- [ ] CPU/Memory Charts aktualisieren
- [ ] Logs für Container streamen
- [ ] Logs pausierbar

### DB Explorer
- [ ] Alle Tabellen aufgelistet
- [ ] Tabellen-Daten ladbar
- [ ] Such-Filter funktioniert
- [ ] Pagination/Limit funktioniert

### System Health
- [ ] Host-Metriken angezeigt
- [ ] API-Performance sichtbar
- [ ] WebSocket-Stats sichtbar

### System Events
- [ ] Event-Log zeigt Einträge
- [ ] Filter funktioniert

### System Settings
- [ ] Alle Settings editierbar
- [ ] Speichern funktioniert
- [ ] Änderungen in Events geloggt

### User Management
- [ ] User-Liste komplett
- [ ] User anlegen/editieren
- [ ] User sperren/entsperren
- [ ] Rollen zuweisen

### Szenarien
- [ ] Szenarien anlegen
- [ ] Threads zuweisen
- [ ] User als RATER/VIEWER zuweisen
- [ ] Zeitraum korrekt

---

**Letzte Aktualisierung:** 30. Dezember 2025
