# Security Testanforderungen: Rollen-Zugriffs-Matrix

**Version:** 1.0 | **Stand:** 30. Dezember 2025

---

## Übersicht

Dieses Dokument definiert die vollständige Zugriffs-Matrix für alle 4 Rollen und muss bei jedem Test verifiziert werden.

---

## 1. Rollen-Übersicht

| Rolle | Beschreibung | User-Beispiel |
|-------|--------------|---------------|
| **admin** | Vollzugriff auf alles | `admin` |
| **researcher** | Evaluation + Collab + KAIMO | `researcher` |
| **chatbot_manager** | Chatbots + RAG + Collab | `chatbot_manager` |
| **evaluator** | Nur lesen + KAIMO/Authenticity votes | `evaluator` |

---

## 2. Feature-Zugriffs-Matrix

### Navigation & Grundfunktionen

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Login | ✅ | ✅ | ✅ | ✅ |
| Home Dashboard | ✅ | ✅ | ✅ | ✅ |
| User Settings | ✅ | ✅ | ✅ | ✅ |
| Collab-Farbe ändern | ✅ | ✅ | ✅ | ✅ |
| Avatar ändern | ✅ | ✅ | ✅ | ✅ |
| Logout | ✅ | ✅ | ✅ | ✅ |

### Evaluation Features

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| **Ranking** |
| - Kachel sichtbar | ✅ | ✅ | ❌ | ✅ |
| - Threads ansehen | ✅ | ✅ | ❌ | ✅ |
| - Rankings erstellen | ✅ | ✅ | ❌ | ❌ |
| **Rating** |
| - Kachel sichtbar | ✅ | ✅ | ❌ | ✅ |
| - Threads ansehen | ✅ | ✅ | ❌ | ✅ |
| - Ratings erstellen | ✅ | ✅ | ❌ | ❌ |
| **Judge** |
| - Kachel sichtbar | ✅ | ❌ | ❌ | ❌ |
| - Sessions ansehen | ✅ | ❌ | ❌ | ❌ |
| - Sessions erstellen | ✅ | ❌ | ❌ | ❌ |
| - Sessions starten | ✅ | ❌ | ❌ | ❌ |
| **OnCoCo** |
| - Kachel sichtbar | ✅ | ❌ | ❌ | ❌ |
| - Analysen ansehen | ✅ | ❌ | ❌ | ❌ |
| - Analysen erstellen | ✅ | ❌ | ❌ | ❌ |
| **Authenticity** |
| - Kachel sichtbar | ✅ | ✅ | ❌ | ✅ |
| - Threads ansehen | ✅ | ✅ | ❌ | ✅ |
| - Votes abgeben | ✅ | ✅ | ❌ | ✅ |

### KAIMO

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Kachel sichtbar | ✅ | ✅ | ❌ | ✅ |
| Cases ansehen | ✅ | ✅ | ❌ | ✅ |
| Assessments abgeben | ✅ | ✅ | ❌ | ✅ |
| Cases erstellen | ✅ | ✅ | ❌ | ❌ |
| Cases editieren | ✅ | ✅ | ❌ | ❌ |
| Cases publizieren | ✅ | ❌ | ❌ | ❌ |
| Ergebnisse sehen | ✅ | ❌ | ❌ | ❌ |

### Chatbot Features

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Chat nutzen | ✅ | ✅ | ✅ | ✅ |
| Chatbot erstellen | ✅ | ❌ | ✅ | ❌ |
| Chatbot editieren | ✅ | ❌ | ✅ | ❌ |
| Chatbot löschen | ✅ | ❌ | ✅ | ❌ |
| Chatbot teilen | ✅ | ❌ | ✅ | ❌ |
| Advanced Modes (ReAct) | ✅ | ❌ | ✅ | ❌ |
| Wizard nutzen | ✅ | ❌ | ✅ | ❌ |

### RAG Features

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Dokumente ansehen | ✅ | ❌ | ✅ | ✅ |
| Dokumente hochladen | ✅ | ❌ | ✅ | ❌ |
| Dokumente editieren | ✅ | ❌ | ✅ | ❌ |
| Dokumente löschen | ✅ | ❌ | ✅ | ❌ |
| Dokumente teilen | ✅ | ❌ | ✅ | ❌ |
| Collections erstellen | ✅ | ❌ | ✅ | ❌ |
| Crawler nutzen | ✅ | ❌ | ✅ | ❌ |

### Collaboration Features

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| **Markdown Collab** |
| - Kachel sichtbar | ✅ | ✅ | ✅ | ✅ |
| - Workspaces ansehen | ✅ | ✅ | ✅ | ✅ |
| - Dokumente editieren | ✅ | ✅ | ✅ | ❌ |
| - Workspaces teilen | ✅ | ✅ | ✅ | ❌ |
| **LaTeX Collab** |
| - Kachel sichtbar | ✅ | ✅ | ✅ | ✅ |
| - Workspaces ansehen | ✅ | ✅ | ✅ | ✅ |
| - Dokumente editieren | ✅ | ✅ | ✅ | ❌ |
| - PDF kompilieren | ✅ | ✅ | ✅ | ❌ |
| - Workspaces teilen | ✅ | ✅ | ✅ | ❌ |
| **LaTeX AI** |
| - Kachel sichtbar | ✅ | ✅ | ✅ | ❌ |
| - AI-Features nutzen | ✅ | ✅ | ✅ | ❌ |
| - Ghost Text | ✅ | ✅ | ✅ | ❌ |
| - @-Commands | ✅ | ✅ | ✅ | ❌ |
| - Zitations-Suche | ✅ | ✅ | ✅ | ❌ |

### Prompt Engineering

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Kachel sichtbar | ✅ | ✅ | ✅ | ✅ |
| Prompts ansehen | ✅ | ✅ | ✅ | ✅ |
| Prompts erstellen | ✅ | ✅ | ✅ | ❌ |
| Prompts editieren | ✅ | ✅ | ✅ | ❌ |
| Prompts teilen | ✅ | ✅ | ✅ | ❌ |
| Prompts testen | ✅ | ✅ | ✅ | ❌ |

### Anonymize

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Kachel sichtbar | ✅ | ✅ | ❌ | ✅ |
| Tool nutzen | ✅ | ✅ | ❌ | ✅ |

### Admin Dashboard

| Feature | Admin | Researcher | Chatbot_Manager | Evaluator |
|---------|:-----:|:----------:|:---------------:|:------:|
| Dashboard sichtbar | ✅ | ❌ | ⚠️ | ❌ |
| Overview Tab | ✅ | ❌ | ❌ | ❌ |
| Docker Monitor | ✅ | ❌ | ❌ | ❌ |
| DB Explorer | ✅ | ❌ | ❌ | ❌ |
| System Health | ✅ | ❌ | ❌ | ❌ |
| System Events | ✅ | ❌ | ❌ | ❌ |
| System Settings | ✅ | ❌ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ | ❌ |
| Permissions | ✅ | ❌ | ❌ | ❌ |
| Szenarien | ✅ | ❌ | ❌ | ❌ |
| Chatbots Tab | ✅ | ❌ | ✅ | ❌ |
| RAG Tab | ✅ | ❌ | ✅ | ❌ |
| Crawler Tab | ✅ | ❌ | ✅ | ❌ |
| Analytics | ✅ | ❌ | ❌ | ❌ |

**Legende:** ✅ = Zugriff | ❌ = Kein Zugriff | ⚠️ = Eingeschränkt

---

## 3. E2E Tests für Rollen-Matrix

### Test-Struktur

```typescript
// e2e/security/role-matrix.spec.ts
import { test, expect, testUsers, login } from '../fixtures/auth'

// Test für jede Rolle
const roles = ['admin', 'researcher', 'chatbot_manager', 'evaluator']

for (const role of roles) {
  test.describe(`${role} role access`, () => {
    test.beforeEach(async ({ page }) => {
      await login(page, testUsers[role])
    })

    // Home sichtbar für alle
    test('can access home', async ({ page }) => {
      await page.goto('/Home')
      await expect(page).toHaveURL(/.*Home/)
    })

    // Admin-Dashboard nur für admin/chatbot_manager
    test('admin dashboard access', async ({ page }) => {
      await page.goto('/admin')

      if (role === 'admin') {
        await expect(page).toHaveURL(/.*admin/)
        await expect(page.locator('[data-tab="docker"]')).toBeVisible()
      } else if (role === 'chatbot_manager') {
        await expect(page).toHaveURL(/.*admin/)
        await expect(page.locator('[data-tab="docker"]')).not.toBeVisible()
        await expect(page.locator('[data-tab="chatbots"]')).toBeVisible()
      } else {
        await expect(page).not.toHaveURL(/.*admin/)
      }
    })

    // Judge nur für admin
    test('judge access', async ({ page }) => {
      await page.goto('/judge')

      if (role === 'admin') {
        await expect(page).toHaveURL(/.*judge/)
      } else {
        await expect(page).not.toHaveURL(/.*judge/)
      }
    })
  })
}
```

### Spezifische Rollen-Tests

| ID | Rolle | Test | Erwartung | Art |
|----|-------|------|-----------|-----|
| ROLE-A01 | admin | Alle Kacheln sichtbar | Alle Features | E2E |
| ROLE-A02 | admin | Admin-Dashboard vollständig | Alle Tabs | E2E |
| ROLE-A03 | admin | User anlegen | User erstellt | E2E |
| ROLE-A04 | admin | User sperren | User gesperrt | E2E |
| ROLE-A05 | admin | Szenario anlegen | Szenario erstellt | E2E |
| ROLE-R01 | researcher | Ranking/Rating sichtbar | Features sichtbar | E2E |
| ROLE-R02 | researcher | Kein Admin-Zugang | Redirect | E2E |
| ROLE-R03 | researcher | Kein Judge-Zugang | Redirect | E2E |
| ROLE-R04 | researcher | Collab editieren | Funktioniert | E2E |
| ROLE-R05 | researcher | KAIMO bewerten | Vote speichern | E2E |
| ROLE-C01 | chatbot_mgr | Chatbot erstellen | Chatbot erstellt | E2E |
| ROLE-C02 | chatbot_mgr | RAG hochladen | Dokument hochgeladen | E2E |
| ROLE-C03 | chatbot_mgr | Kein Ranking/Rating | Features nicht sichtbar | E2E |
| ROLE-C04 | chatbot_mgr | Admin nur Chatbot Tab | Nur bestimmte Tabs | E2E |
| ROLE-E01 | evaluator | Nur lesen | Keine Edit-Buttons | E2E |
| ROLE-E02 | evaluator | Authenticity voten | Vote funktioniert | E2E |
| ROLE-E03 | evaluator | KAIMO bewerten | Vote funktioniert | E2E |
| ROLE-E04 | evaluator | Kein Admin-Zugang | Redirect | E2E |
| ROLE-E05 | evaluator | Kein Collab-Edit | Nur lesen | E2E |

---

## 4. Kachel-Sichtbarkeits-Tests

### Home Dashboard Kacheln

| Kachel | admin | researcher | chatbot_manager | evaluator |
|--------|:-----:|:----------:|:---------------:|:------:|
| Ranking | ✅ | ✅ | ❌ | ✅ |
| Rating | ✅ | ✅ | ❌ | ✅ |
| Judge | ✅ | ❌ | ❌ | ❌ |
| OnCoCo | ✅ | ❌ | ❌ | ❌ |
| Prompt Engineering | ✅ | ✅ | ✅ | ✅ |
| Chat | ✅ | ✅ | ✅ | ✅ |
| Markdown Collab | ✅ | ✅ | ✅ | ✅ |
| LaTeX Collab | ✅ | ✅ | ✅ | ✅ |
| LaTeX AI | ✅ | ✅ | ✅ | ❌ |
| Anonymize | ✅ | ✅ | ❌ | ✅ |
| KAIMO | ✅ | ✅ | ❌ | ✅ |
| Admin | ✅ | ❌ | ⚠️ | ❌ |

### E2E Test-Code

```typescript
// e2e/security/tile-visibility.spec.ts
import { test, expect, testUsers, login } from '../fixtures/auth'

test.describe('Tile Visibility by Role', () => {
  test('admin sees all tiles', async ({ page }) => {
    await login(page, testUsers.admin)
    await page.goto('/Home')

    await expect(page.locator('text=Ranking')).toBeVisible()
    await expect(page.locator('text=Judge')).toBeVisible()
    await expect(page.locator('text=OnCoCo')).toBeVisible()
    await expect(page.locator('text=Admin')).toBeVisible()
  })

  test('researcher sees evaluation tiles, not admin', async ({ page }) => {
    await login(page, testUsers.researcher)
    await page.goto('/Home')

    await expect(page.locator('text=Ranking')).toBeVisible()
    await expect(page.locator('text=Rating')).toBeVisible()
    await expect(page.locator('text=Judge')).not.toBeVisible()
    await expect(page.locator('text=OnCoCo')).not.toBeVisible()
    await expect(page.locator('text=Admin')).not.toBeVisible()
  })

  test('chatbot_manager sees chatbot tiles, not evaluation', async ({ page }) => {
    await login(page, testUsers.chatbot_manager)
    await page.goto('/Home')

    await expect(page.locator('text=Chat')).toBeVisible()
    await expect(page.locator('text=Ranking')).not.toBeVisible()
    await expect(page.locator('text=Rating')).not.toBeVisible()
    // Admin sichtbar aber eingeschränkt
    await expect(page.locator('text=Admin')).toBeVisible()
  })

  test('evaluator sees only view tiles', async ({ page }) => {
    await login(page, testUsers.evaluator)
    await page.goto('/Home')

    await expect(page.locator('text=Ranking')).toBeVisible()
    await expect(page.locator('text=Chat')).toBeVisible()
    await expect(page.locator('text=Judge')).not.toBeVisible()
    await expect(page.locator('text=Admin')).not.toBeVisible()
    await expect(page.locator('text=LaTeX AI')).not.toBeVisible()
  })
})
```

---

## 5. Navigation-Schutz Tests

| ID | Test | Erwartung | Art |
|----|------|-----------|-----|
| NAV-R01 | Researcher → /admin | Redirect zu /Home | E2E |
| NAV-R02 | Researcher → /judge | Redirect zu /Home | E2E |
| NAV-R03 | Researcher → /oncoco | Redirect zu /Home | E2E |
| NAV-V01 | Evaluator → /admin | Redirect zu /Home | E2E |
| NAV-V02 | Evaluator → /LatexCollabAI | Redirect zu /Home | E2E |
| NAV-C01 | Chatbot_Mgr → /Ranker | Redirect zu /Home | E2E |
| NAV-C02 | Chatbot_Mgr → /judge | Redirect zu /Home | E2E |

---

## Checkliste für manuelle Tests

### Admin-Rolle
- [ ] Alle Kacheln sichtbar
- [ ] Admin-Dashboard vollständig
- [ ] Docker Monitor funktioniert
- [ ] DB Explorer funktioniert
- [ ] System Settings editierbar
- [ ] User anlegen/sperren
- [ ] Szenarien anlegen
- [ ] Alle Features nutzbar

### Researcher-Rolle
- [ ] Ranking/Rating/Authenticity sichtbar
- [ ] KAIMO sichtbar + bewertbar
- [ ] Collab-Editoren nutzbar
- [ ] LaTeX AI nutzbar
- [ ] Anonymize nutzbar
- [ ] Kein Judge/OnCoCo
- [ ] Kein Admin-Zugang

### Chatbot_Manager-Rolle
- [ ] Chatbot-Features vollständig
- [ ] RAG-Features vollständig
- [ ] Collab-Editoren nutzbar
- [ ] Admin nur Chatbot/RAG Tabs
- [ ] Kein Ranking/Rating
- [ ] Kein Judge/OnCoCo

### Evaluator-Rolle
- [ ] Nur lesen überall
- [ ] Keine Edit-Buttons
- [ ] KAIMO + Authenticity Votes funktionieren
- [ ] Anonymize funktioniert
- [ ] Kein LaTeX AI
- [ ] Kein Admin

---

**Letzte Aktualisierung:** 30. Dezember 2025
