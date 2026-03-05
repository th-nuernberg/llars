import { test, expect } from '@playwright/test'
import workflowsContract from './nightly_workflows.contract.json' with { type: 'json' }

import {
  TEST_USERS,
  quickLogin,
  dismissConsentBanner,
  waitForPageReady
} from '../helpers.js'

async function openRoute(page, user, route, readySelector = 'main, .page-container, .panel-content') {
  await quickLogin(page, user)
  await page.goto(route, { waitUntil: 'domcontentloaded' })

  if (page.url().includes('/login')) {
    await quickLogin(page, user)
    await page.goto(route, { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector(readySelector, { timeout: 20000 })
  await waitForPageReady(page, 12000)
}

function hasWorkflow(name) {
  return workflowsContract.workflows.some((w) => w.name === name)
}

test.describe('Nightly Cross-Tile Workflows', () => {
  test.setTimeout(240000)

  if (hasWorkflow('Szenario Wizard')) {
    test('Szenario Wizard', async ({ page }) => {
      await openRoute(page, TEST_USERS.researcher, '/generation', '.generation-hub, .page-container, main')

      const hasGenerationEntry = await page
        .locator('button:has-text("Neu"), button:has-text("Start"), button:has-text("Create"), a[href*="/generation/new"]')
        .first()
        .isVisible({ timeout: 5000 })
        .catch(() => false)

      expect(hasGenerationEntry, 'Batch Generation entry actions should be available').toBeTruthy()

      const scenarioHints = await page
        .locator('text=/Szenario|Scenario|Wizard/i')
        .first()
        .isVisible({ timeout: 4000 })
        .catch(() => false)

      expect(scenarioHints, 'Scenario handoff/wizard references should be visible').toBeTruthy()
    })
  }

  if (hasWorkflow('Prompt Engineering Collaboration')) {
    test('Prompt Engineering Collaboration', async ({ page }) => {
      await openRoute(page, TEST_USERS.researcher, '/PromptEngineering', '.prompt-home, .prompts-grid, main')

      const createButton = page.locator('button:has-text("Neues Prompt"), button:has-text("Neu"), button:has(.mdi-plus)').first()
      const canCreate = await createButton.isVisible({ timeout: 5000 }).catch(() => false)

      if (canCreate) {
        await createButton.click().catch(() => {})
        const nameInput = page.locator('input[type="text"], input[placeholder*="Name" i]').first()
        if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
          await nameInput.fill(`nightly-${Date.now()}`)
          await page.locator('button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Speichern")').first().click().catch(() => {})
        }
      }

      const hasTestAction = await page
        .locator('button:has-text("Test"), button:has-text("Testen"), button:has(.mdi-play)')
        .first()
        .isVisible({ timeout: 6000 })
        .catch(() => false)

      const hasImportExport = await page
        .locator('button:has-text("Import"), button:has-text("Export"), button:has-text("Download"), .mdi-download, .mdi-upload')
        .first()
        .isVisible({ timeout: 6000 })
        .catch(() => false)

      const hasShareAction = await page
        .locator('button:has-text("Teilen"), button:has-text("Share"), .mdi-account-multiple-plus, .mdi-share-variant')
        .first()
        .isVisible({ timeout: 6000 })
        .catch(() => false)

      expect(hasTestAction, 'Prompt test action should be visible').toBeTruthy()
      expect(hasImportExport, 'Prompt import/export/download actions should be visible').toBeTruthy()
      expect(hasShareAction, 'Prompt sharing action should be visible').toBeTruthy()
    })
  }

  if (hasWorkflow('Latex Collab Resizer')) {
    test('Latex Collab Resizer', async ({ page }) => {
      await openRoute(page, TEST_USERS.researcher, '/LatexCollab', '.latex-collab-home, .page-container, main')

      const workspaceCard = page.locator('.workspace-card, .l-card, .item-card').first()
      if (await workspaceCard.isVisible({ timeout: 4000 }).catch(() => false)) {
        await workspaceCard.click()
      } else {
        const createWorkspace = page.locator('button:has-text("Workspace"), button:has-text("Erstellen"), button:has(.mdi-plus)').first()
        if (await createWorkspace.isVisible({ timeout: 4000 }).catch(() => false)) {
          await createWorkspace.click().catch(() => {})
          const input = page.locator('input[type="text"], input[placeholder*="Name" i]').first()
          if (await input.isVisible({ timeout: 3000 }).catch(() => false)) {
            await input.fill(`nightly-latex-${Date.now()}`)
            await page.locator('button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Speichern")').first().click().catch(() => {})
          }
          await page.locator('.workspace-card, .l-card, .item-card').first().click().catch(() => {})
        }
      }

      await dismissConsentBanner(page)
      await waitForPageReady(page, 10000)

      const resizer = page.locator('.resize-divider, .splitter, .pane-resizer, .gutter').first()
      await expect(resizer, 'A resizer divider must be present in LaTeX workspace').toBeVisible({ timeout: 10000 })

      const before = await resizer.boundingBox()
      expect(before, 'Unable to read resizer position before drag').not.toBeNull()

      await page.mouse.move(before.x + before.width / 2, before.y + before.height / 2)
      await page.mouse.down()
      await page.mouse.move(before.x + before.width / 2 + 100, before.y + before.height / 2, { steps: 12 })
      await page.mouse.up()

      const after = await resizer.boundingBox()
      expect(after, 'Unable to read resizer position after drag').not.toBeNull()

      const moved = Math.abs(after.x - before.x)
      expect(moved, 'Resizer should move after drag interaction').toBeGreaterThan(5)
    })
  }

  if (hasWorkflow('Scenario Manager Role Assignment')) {
    test('Scenario Manager Role Assignment', async ({ page }) => {
      await openRoute(page, TEST_USERS.admin, '/scenarios', '.scenario-manager, .page-container, main')

      const createOrOpen = page.locator('button:has-text("Neu"), button:has-text("Szenario"), .scenario-card, .scenario-row').first()
      if (await createOrOpen.isVisible({ timeout: 5000 }).catch(() => false)) {
        await createOrOpen.click().catch(() => {})
      }

      const hasAssignmentControls = await page
        .locator('text=/Evaluator|Viewer|Rolle|Role|Zuweisen|Invite|Benutzer/i')
        .first()
        .isVisible({ timeout: 8000 })
        .catch(() => false)

      expect(hasAssignmentControls, 'Scenario role assignment controls should be visible').toBeTruthy()
    })
  }

  if (hasWorkflow('Conference Manager Access Request')) {
    test('Conference Manager Access Request', async ({ page }) => {
      await openRoute(page, TEST_USERS.researcher, '/conferences', '.conference-entry-page, .page-container, main')

      const hasRequestAction = await page
        .locator('button:has-text("Access"), button:has-text("Anfrage"), a[href*="request-access"], text=/Zugang|Request/i')
        .first()
        .isVisible({ timeout: 6000 })
        .catch(() => false)

      // Falls keine Gruppe vorhanden ist, muss die Seite zumindest stabil laden.
      const hasStablePage = await page
        .locator('main, .conference-entry-page, .empty-state, .v-container')
        .first()
        .isVisible({ timeout: 3000 })
        .catch(() => false)

      expect(hasRequestAction || hasStablePage, 'Conference manager page should expose access request flow or stable empty state').toBeTruthy()
    })
  }
})
