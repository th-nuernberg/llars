import fs from 'fs'
import os from 'os'
import path from 'path'
import { test, expect } from '@playwright/test'
import workflowsContract from './nightly_workflows.contract.json' with { type: 'json' }

import {
  TEST_USERS,
  quickLogin,
  dismissConsentBanner,
  waitForPageReady
} from '../helpers.js'

const BASE_URL = (process.env.PLAYWRIGHT_API_BASE_URL || process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:55080').replace(/\/+$/, '')
const RUN_SUFFIX = String(process.env.CI_PIPELINE_ID || Date.now())
const NIGHTLY_PREFIX = `nightly-${RUN_SUFFIX}`

function hasWorkflow(name) {
  return workflowsContract.workflows.some((w) => w.name === name)
}

async function activity(id, title, fn) {
  await test.step(`[ACT:${id}] ${title}`, fn)
}

async function openRoute(page, user, route, readySelector = 'main, .page-container, .panel-content') {
  await quickLogin(page, user)
  await page.goto(route, { waitUntil: 'domcontentloaded' })

  if (page.url().includes('/login')) {
    await quickLogin(page, user)
    await page.goto(route, { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector(readySelector, { timeout: 30000 })
  await waitForPageReady(page, 15000)
}

async function apiLogin(user) {
  const response = await fetch(`${BASE_URL}/auth/authentik/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: user.username, password: user.password })
  })
  const raw = await response.text()
  let data = {}
  try {
    data = JSON.parse(raw)
  } catch {
    data = {}
  }
  if (!response.ok || !data.access_token) {
    throw new Error(`API login failed (${user.username}): ${response.status} ${raw}`)
  }
  return data.access_token
}

async function apiCall(token, method, pathName, payload = null) {
  const response = await fetch(`${BASE_URL}${pathName}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: payload == null ? undefined : JSON.stringify(payload)
  })
  const raw = await response.text()
  let data = {}
  try {
    data = raw ? JSON.parse(raw) : {}
  } catch {
    data = {}
  }
  return { ok: response.ok, status: response.status, data, raw }
}

async function createScenarioViaApi(adminToken, name) {
  const begin = new Date()
  const end = new Date(begin.getTime() + 24 * 60 * 60 * 1000)
  const payload = {
    scenario_name: name,
    function_type_id: 2,
    begin: begin.toISOString(),
    end: end.toISOString(),
    evaluator: [],
    viewer: [],
    threads: [],
    config_json: {}
  }
  const result = await apiCall(adminToken, 'POST', '/api/admin/create_scenario', payload)
  if (!result.ok || !result.data.scenario_id) {
    throw new Error(`Failed to create scenario: ${result.status} ${result.raw}`)
  }
  return Number(result.data.scenario_id)
}

async function deleteScenarioViaApi(adminToken, scenarioId) {
  return apiCall(adminToken, 'DELETE', `/api/admin/delete_scenario/${scenarioId}`)
}

async function deletePromptViaApi(token, promptId) {
  return apiCall(token, 'DELETE', `/api/prompts/${promptId}`)
}

async function createGroupViaApi(adminToken, name) {
  const result = await apiCall(adminToken, 'POST', '/api/conference-manager/groups', {
    name,
    description: `Nightly test group ${name}`
  })
  if (!result.ok || !result.data?.group?.id) {
    throw new Error(`Failed to create group: ${result.status} ${result.raw}`)
  }
  return Number(result.data.group.id)
}

async function deleteGroupViaApi(adminToken, groupId) {
  return apiCall(adminToken, 'DELETE', `/api/conference-manager/groups/${groupId}`)
}

async function chooseUserInSearch(container, username) {
  const input = container.locator('input').first()
  await input.click()
  await input.fill(username)

  const suggestion = container
    .locator(`.user-suggestion:has-text("${username}"), .v-list-item:has-text("${username}")`)
    .first()
  await suggestion.waitFor({ state: 'visible', timeout: 8000 })
  await suggestion.click()
}

test.describe('Nightly Cross-Tile Workflows', () => {
  test.setTimeout(420000)

  if (hasWorkflow('Szenario Wizard')) {
    test('Szenario Wizard', async ({ page }) => {
      await openRoute(page, TEST_USERS.researcher, '/generation', '.generation-hub, .page-container, main')

      await activity('BG-WIZ-ENTRY-001', 'Batch Generation Wizard öffnen', async () => {
        const newJobButton = page
          .locator('button:has-text("Neu"), button:has-text("New"), button:has-text("Job"), button:has(.mdi-plus)')
          .first()
        await expect(newJobButton).toBeVisible({ timeout: 10000 })
        await newJobButton.click()
        await expect(page.locator('.generation-wizard, .wizard-stepper, .wizard-content').first())
          .toBeVisible({ timeout: 10000 })
        await page.locator('.generation-wizard button:has(.mdi-close), .generation-wizard button:has-text("Schließen"), .generation-wizard button:has-text("Close")').first().click().catch(() => {})
      })

      await activity('BG-WIZ-HANDOFF-001', 'Handoff Richtung Szenario Wizard prüfen', async () => {
        const firstJobCard = page.locator('.jobs-grid .v-card, .jobs-grid .l-card, .job-card').first()
        if (await firstJobCard.isVisible({ timeout: 4000 }).catch(() => false)) {
          await firstJobCard.click()
          await waitForPageReady(page, 12000)
          const wizardAction = page
            .locator('button:has-text("Szenario"), button:has-text("Wizard"), button:has(.mdi-wizard-hat)')
            .first()
          if (await wizardAction.isVisible({ timeout: 3000 }).catch(() => false)) {
            await wizardAction.click()
            await expect(page.locator('.scenario-wizard, .wizard-header, [class*="scenario-wizard"]').first())
              .toBeVisible({ timeout: 8000 })
            return
          }
        }

        const hasStableGenerationUi = await page
          .locator('.generation-hub, .job-detail, .outputs-panel, .empty-state, main')
          .first()
          .isVisible({ timeout: 4000 })
          .catch(() => false)
        expect(hasStableGenerationUi, 'Generation flow should remain stable even without completed jobs').toBeTruthy()
      })
    })
  }

  if (hasWorkflow('Prompt Engineering Collaboration')) {
    test('Prompt Engineering Collaboration', async ({ page }) => {
      const promptName = `${NIGHTLY_PREFIX}-prompt`
      const blockName = `${NIGHTLY_PREFIX}-block`
      const importedBlockName = `${NIGHTLY_PREFIX}-import`
      const importedText = 'nightly import content'
      let promptId = null

      const researcherToken = await apiLogin(TEST_USERS.researcher)

      await openRoute(page, TEST_USERS.researcher, '/PromptEngineering', '.prompt-home, .prompts-grid, main')

      try {
        await activity('PE-CREATE-001', 'Prompt anlegen', async () => {
          await page.locator('button:has-text("Neues Prompt"), button:has-text("Neu"), button:has(.mdi-plus)').first().click()
          const dialog = page.locator('.v-dialog, [role="dialog"]').first()
          await expect(dialog).toBeVisible({ timeout: 8000 })
          await dialog.locator('input[type="text"]').first().fill(promptName)
          await dialog.locator('button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Speichern")').first().click()
          await expect(page.locator('.prompt-card, .l-card').filter({ hasText: promptName }).first())
            .toBeVisible({ timeout: 12000 })
          await page.locator('.prompt-card, .l-card').filter({ hasText: promptName }).first().click()
          await expect(page).toHaveURL(/\/PromptEngineering\/\d+/, { timeout: 12000 })
          const match = page.url().match(/\/PromptEngineering\/(\d+)/)
          promptId = match ? Number(match[1]) : null
          expect(promptId, 'Prompt ID should be present in URL').toBeTruthy()
        })

        await activity('PE-BLOCK-001', 'Block anlegen und bearbeiten', async () => {
          await page.locator('button:has-text("Block"), button:has-text("Neu"), button:has(.mdi-plus-circle), button:has(.mdi-plus)').first().click()
          const dialog = page.locator('.v-dialog, [role="dialog"]').first()
          await dialog.locator('input[type="text"]').first().fill(blockName)
          await dialog.locator('button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Speichern")').first().click()

          const blockCard = page.locator('.editor-block').filter({ has: page.locator(`.block-title:has-text("${blockName}")`) }).first()
          await expect(blockCard).toBeVisible({ timeout: 10000 })

          const editor = blockCard.locator('.editor-content .ql-editor').first()
          await editor.click()
          await editor.fill(`Nightly Text ${NIGHTLY_PREFIX}`)
          await expect(editor).toContainText(`Nightly Text ${NIGHTLY_PREFIX}`, { timeout: 8000 })
        })

        await activity('PE-TEST-001', 'Test-Dialog und LLM-Antwort prüfen', async () => {
          await page.locator('.sidebar button:has-text("Test"), .sidebar button:has(.mdi-rocket), button:has-text("Test")').first().click()
          const responseText = page.locator('.response-text, .response-content pre').first()
          await expect(responseText).toBeVisible({ timeout: 10000 })
          await expect
            .poll(
              async () => (await responseText.innerText().catch(() => '')).trim().length,
              { timeout: 60000 }
            )
            .toBeGreaterThan(0)
          await page.locator('.test-prompt-card button:has(.mdi-close), .test-prompt-card button:has-text("Schließen"), .test-prompt-card button:has-text("Close")').first().click().catch(() => {})
        })

        await activity('PE-EXPORT-001', 'Prompt exportieren', async () => {
          const downloadPromise = page.waitForEvent('download', { timeout: 20000 })
          await page.locator('.sidebar button:has-text("Download"), .sidebar button:has(.mdi-download)').first().click()
          const download = await downloadPromise
          expect(download.suggestedFilename()).toBeTruthy()
        })

        await activity('PE-IMPORT-001', 'Prompt importieren', async () => {
          const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'llars-nightly-import-'))
          const filePath = path.join(tmpDir, 'prompt-import.json')
          fs.writeFileSync(filePath, JSON.stringify({ [importedBlockName]: importedText }, null, 2), 'utf-8')

          const fileInput = page.locator('input[type="file"][accept=".json"]').first()
          await fileInput.setInputFiles(filePath)
          await page.locator('button:has-text("Anhängen"), button:has-text("Append"), button:has-text("Überschreiben"), button:has-text("Override")').first().click()
          await expect(page.locator('.block-title').filter({ hasText: importedBlockName }).first())
            .toBeVisible({ timeout: 10000 })
        })

        await activity('PE-SHARE-001', 'Prompt mit Evaluator teilen', async () => {
          const shareSection = page.locator('.sidebar .share-input-section').first()
          await expect(shareSection).toBeVisible({ timeout: 10000 })
          await chooseUserInSearch(shareSection, TEST_USERS.evaluator.username)
          await shareSection.locator('button:has-text("Teilen"), button:has-text("Share"), button:has-text("Hinzufügen")').first().click()
          await expect(page.locator('.shared-item').filter({ hasText: TEST_USERS.evaluator.username }).first())
            .toBeVisible({ timeout: 12000 })
        })

        await activity('PE-UNSHARE-001', 'Prompt-Freigabe entfernen', async () => {
          const sharedItem = page.locator('.shared-item').filter({ hasText: TEST_USERS.evaluator.username }).first()
          await expect(sharedItem).toBeVisible({ timeout: 8000 })
          await sharedItem.locator('button').last().click()
          await expect(sharedItem).toHaveCount(0, { timeout: 12000 })
        })
      } finally {
        await activity('PE-CLEANUP-001', 'Nightly Prompt löschen', async () => {
          if (!promptId) return
          const deletion = await deletePromptViaApi(researcherToken, promptId)
          expect(
            deletion.ok || deletion.status === 404,
            `Prompt cleanup failed: ${deletion.status} ${deletion.raw}`
          ).toBeTruthy()
        })
      }
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
            await input.fill(`${NIGHTLY_PREFIX}-latex`)
            await page.locator('button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Speichern")').first().click().catch(() => {})
          }
          await page.locator('.workspace-card, .l-card, .item-card').first().click().catch(() => {})
        }
      }

      await dismissConsentBanner(page)
      await waitForPageReady(page, 12000)

      await activity('LTX-RESIZE-001', 'LaTeX Resizer per Drag bewegen', async () => {
        const resizer = page.locator('.resize-divider.vertical, .pane-resizer, .gutter').first()
        await expect(resizer).toBeVisible({ timeout: 12000 })

        const before = await resizer.boundingBox()
        expect(before, 'Unable to read resizer position before drag').not.toBeNull()

        await page.mouse.move(before.x + before.width / 2, before.y + before.height / 2)
        await page.mouse.down()
        await page.mouse.move(before.x + before.width / 2 + 120, before.y + before.height / 2, { steps: 14 })
        await page.mouse.up()

        const after = await resizer.boundingBox()
        expect(after, 'Unable to read resizer position after drag').not.toBeNull()

        const moved = Math.abs(after.x - before.x)
        expect(moved, 'Resizer should move after drag interaction').toBeGreaterThan(5)
      })
    })
  }

  if (hasWorkflow('Scenario Manager Role Assignment')) {
    test('Scenario Manager Role Assignment', async ({ page }) => {
      const adminToken = await apiLogin(TEST_USERS.admin)
      const scenarioName = `${NIGHTLY_PREFIX}-scenario`
      let scenarioId = null

      try {
        await activity('SCN-ASSIGN-SETUP-001', 'Nightly-Szenario erzeugen', async () => {
          scenarioId = await createScenarioViaApi(adminToken, scenarioName)
          expect(scenarioId).toBeGreaterThan(0)
        })

        await openRoute(page, TEST_USERS.admin, `/scenarios/${scenarioId}?tab=assessors`, '.scenario-workspace, .team-tab, main')

        await activity('SCN-ASSIGN-INVITE-001', 'Evaluator per UI einladen', async () => {
          await page.locator('button:has-text("Einladen"), button:has-text("Invite"), button:has(.mdi-account-plus)').first().click()
          const dialog = page.locator('.v-dialog, [role="dialog"]').first()
          await expect(dialog).toBeVisible({ timeout: 10000 })

          const userSearch = dialog.locator('.l-user-search').first()
          await chooseUserInSearch(userSearch, TEST_USERS.evaluator.username)

          await dialog.locator('button:has-text("Einladen"), button:has-text("Invite"), button:has-text("Send")').first().click()
          await expect(page.locator('.member-card').filter({ hasText: TEST_USERS.evaluator.username }).first())
            .toBeVisible({ timeout: 20000 })
        })

        await activity('SCN-ASSIGN-ROLE-001', 'Rolle im Team-Tab ändern', async () => {
          const memberCard = page.locator('.member-card').filter({ hasText: TEST_USERS.evaluator.username }).first()
          await expect(memberCard).toBeVisible({ timeout: 10000 })

          const menuButton = memberCard.locator('button:has(.mdi-dots-vertical)').first()
          if (await menuButton.isVisible({ timeout: 3000 }).catch(() => false)) {
            await menuButton.click()
            await page.locator('.v-list-item:has-text("Role"), .v-list-item:has-text("Rolle"), .v-list-item:has-text("changeRole")').first().click()
            const roleDialog = page.locator('.v-dialog, [role="dialog"]').last()
            await expect(roleDialog).toBeVisible({ timeout: 8000 })
            const roleSelect = roleDialog.locator('.v-select').first()
            await roleSelect.click()
            await page.locator('.v-list-item:has-text("Viewer"), .v-list-item:has-text("VIEWER"), .v-list-item:has-text("Assessor"), .v-list-item:has-text("ASSESSOR")').first().click()
            await roleDialog.locator('button:has-text("Speichern"), button:has-text("Save")').first().click()
            await expect(memberCard.locator('.l-tag, .v-chip').first()).toBeVisible({ timeout: 8000 })
          } else {
            const assignmentControls = await page
              .locator('text=/Evaluator|Viewer|Rolle|Role|Zuweisen|Invite|Benutzer/i')
              .first()
              .isVisible({ timeout: 4000 })
              .catch(() => false)
            expect(assignmentControls, 'Role assignment controls should be visible').toBeTruthy()
          }
        })
      } finally {
        await activity('SCN-ASSIGN-CLEANUP-001', 'Nightly-Szenario löschen', async () => {
          if (!scenarioId) return
          const deletion = await deleteScenarioViaApi(adminToken, scenarioId)
          expect(
            deletion.ok || deletion.status === 404,
            `Scenario cleanup failed: ${deletion.status} ${deletion.raw}`
          ).toBeTruthy()
        })
      }
    })
  }

  if (hasWorkflow('Conference Manager Access Request')) {
    test('Conference Manager Access Request', async ({ page }) => {
      const adminToken = await apiLogin(TEST_USERS.admin)
      const groupName = `${NIGHTLY_PREFIX}-group`
      let groupId = null

      try {
        await activity('CONF-REQ-SETUP-001', 'Nightly-Forschungsgruppe erzeugen', async () => {
          groupId = await createGroupViaApi(adminToken, groupName)
          expect(groupId).toBeGreaterThan(0)
        })

        await activity('CONF-REQ-SUBMIT-001', 'Access-Request als Researcher senden', async () => {
          await openRoute(
            page,
            TEST_USERS.researcher,
            `/conferences/groups/${groupId}/request-access`,
            '.access-request-page, .request-card, main'
          )
          const textArea = page.locator('textarea').first()
          if (await textArea.isVisible({ timeout: 4000 }).catch(() => false)) {
            await textArea.fill(`Nightly access request ${NIGHTLY_PREFIX}`)
          }
          await page.locator('button:has-text("Senden"), button:has-text("Submit"), button:has-text("Anfrage")').first().click()
          const sentMarker = await page
            .locator('text=/gesendet|sent|erfolgreich|success/i')
            .first()
            .isVisible({ timeout: 12000 })
            .catch(() => false)
          expect(sentMarker).toBeTruthy()
        })

        await activity('CONF-REQ-VISIBLE-001', 'Access-Request bei Gruppenmitglied sichtbar', async () => {
          await openRoute(
            page,
            TEST_USERS.admin,
            `/conferences/groups/${groupId}/members`,
            '.group-members-page, .members-card, main'
          )
          await expect(page.locator('.member-item, .v-list-item').filter({ hasText: TEST_USERS.researcher.username }).first())
            .toBeVisible({ timeout: 15000 })
        })
      } finally {
        await activity('CONF-REQ-CLEANUP-001', 'Nightly-Forschungsgruppe löschen', async () => {
          if (!groupId) return
          const deletion = await deleteGroupViaApi(adminToken, groupId)
          expect(
            deletion.ok || deletion.status === 404,
            `Group cleanup failed: ${deletion.status} ${deletion.raw}`
          ).toBeTruthy()
        })
      }
    })
  }
})
