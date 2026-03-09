import { test, expect } from '@playwright/test'
import tileContract from '../../src/config/home_tiles.contract.json' with { type: 'json' }

import {
  TEST_USERS,
  quickLogin,
  handlePrivacyPage,
  dismissConsentBanner,
  waitForPageReady
} from '../helpers.js'

const HOME_PATH = '/Home'
const HOME_READY_SELECTOR = '.home-page, .features-grid, .feature-card, main'
const ROLE_ORDER = Array.isArray(tileContract.roles_order) && tileContract.roles_order.length > 0
  ? tileContract.roles_order
  : ['evaluator', 'researcher', 'chatbot_manager', 'admin']

// Each regression test iterates across multiple roles and a capped UI smoke sweep.
// Some pages (for example Batch Generation) need more than 3 minutes in CI when
// the suite walks all roles sequentially.
test.describe.configure({ timeout: 420_000 })

const ROLE_TO_USER_KEY = {
  evaluator: 'evaluator',
  researcher: 'researcher',
  chatbot_manager: 'chatbot_manager',
  admin: 'admin'
}

const TILE_SMOKE_PROFILES = {
  // The nightly workflow suite already opens the Batch Generation wizard.
  // Keep tile regression bounded here and only verify navigation/readiness.
  'Batch Generation': {
    maxButtons: 0
  }
}

function routeToTileTestId(route) {
  return `home-tile-${String(route || '')
    .trim()
    .replace(/^\/+/, '')
    .replace(/[/?=&]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase()}`
}

function isDestructiveButtonLabel(text) {
  return /(löschen|delete|remove|entfernen|abbrechen|cancel|discard|trash|zurücksetzen|reset|stoppen|beenden)/i.test(text)
}

async function openHome(page, user) {
  await page.goto(HOME_PATH, { waitUntil: 'domcontentloaded' })

  if (page.url().includes('/login')) {
    await quickLogin(page, user)
    await page.goto(HOME_PATH, { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await handlePrivacyPage(page, HOME_PATH)
  await page.waitForSelector(HOME_READY_SELECTOR, { timeout: 20000 })
  await waitForPageReady(page, 15000)
}

async function safeButtonSweep(page, maxButtons = 5) {
  const buttons = page.locator('button:visible, [role="button"]:visible')
  const count = await buttons.count()
  let clicked = 0

  for (let i = 0; i < Math.min(count, maxButtons); i += 1) {
    const button = buttons.nth(i)
    const label = (await button.innerText().catch(() => '')).trim()

    if (isDestructiveButtonLabel(label)) continue

    await button.scrollIntoViewIfNeeded().catch(() => {})
    const isEnabled = await button.isEnabled().catch(() => false)
    if (!isEnabled) continue

    await button.click({ timeout: 3000 }).catch(() => {})
    await dismissConsentBanner(page)
    await page.waitForLoadState('domcontentloaded', { timeout: 4000 }).catch(() => {})
    clicked += 1
  }

  return clicked
}

async function assertDirectRouteBlockedOrRestricted(page, tile) {
  await page.goto(tile.route, { waitUntil: 'domcontentloaded' })
  await dismissConsentBanner(page)
  await waitForPageReady(page, 10000)

  const currentUrl = page.url()
  if (currentUrl.includes('/login') || currentUrl.includes('/Home')) {
    expect(true).toBeTruthy()
    return
  }

  const forbiddenMarker = await page
    .locator('text=/Zugriff verweigert|Keine Berechtigung|Access denied|Forbidden/i')
    .first()
    .isVisible({ timeout: 1500 })
    .catch(() => false)

  const hasCreateActions = await page
    .locator('button:has-text("Neu"), button:has-text("Erstellen"), button:has-text("Create"), button:has-text("Start")')
    .count()
    .catch(() => 0)

  expect(
    forbiddenMarker || hasCreateActions === 0,
    `${tile.name}: hidden tile route should be blocked or read-restricted`
  ).toBeTruthy()
}

async function runTileRegression(page, tileName) {
  const tile = tileContract.tiles.find((entry) => entry.name === tileName)
  expect(tile, `Tile '${tileName}' must exist in home_tiles.contract.json`).toBeTruthy()
  const smokeProfile = TILE_SMOKE_PROFILES[tile.name] || {}
  const maxButtons = smokeProfile.maxButtons ?? 5

  for (const role of ROLE_ORDER) {
    const userKey = ROLE_TO_USER_KEY[role]
    const user = TEST_USERS[userKey]
    if (!user) continue

    const shouldBeVisible = Array.isArray(tile.allowed_roles) && tile.allowed_roles.includes(role)
    const testId = routeToTileTestId(tile.route)

    await test.step(`${tile.name} :: ${role}`, async () => {
      await quickLogin(page, user)
      await openHome(page, user)

      const tileCard = page.locator(`[data-testid="${testId}"]`).first()

      if (shouldBeVisible) {
        await expect(tileCard, `${tile.name} should be visible for ${role}`).toBeVisible({ timeout: 10000 })

        await tileCard.scrollIntoViewIfNeeded()
        await tileCard.click()

        await expect
          .poll(() => page.url(), {
            timeout: 15000,
            message: `${tile.name} did not navigate for role ${role}`
          })
          .not.toContain('/Home')

        await expect(page.url(), `${tile.name} redirected to login for ${role}`).not.toContain('/login')
        await expect(page.url(), `${tile.name} did not reach expected route base for ${role}`)
          .toContain(tile.route.split('?')[0])

        await dismissConsentBanner(page)
        await waitForPageReady(page, 12000)
        if (maxButtons > 0) {
          await safeButtonSweep(page, maxButtons)
        }
      } else {
        await expect(tileCard, `${tile.name} should be hidden for ${role}`).toHaveCount(0)
        await assertDirectRouteBlockedOrRestricted(page, tile)
      }
    })
  }
}

test('Prompt Engineering', async ({ page }) => runTileRegression(page, 'Prompt Engineering'))
test('Batch Generation', async ({ page }) => runTileRegression(page, 'Batch Generation'))
test('Evaluation', async ({ page }) => runTileRegression(page, 'Evaluation'))
test('Scenario Manager', async ({ page }) => runTileRegression(page, 'Scenario Manager'))
test('Chatbot', async ({ page }) => runTileRegression(page, 'Chatbot'))
test('Video', async ({ page }) => runTileRegression(page, 'Video'))
test('Markdown Collab', async ({ page }) => runTileRegression(page, 'Markdown Collab'))
test('Latex Collab', async ({ page }) => runTileRegression(page, 'Latex Collab'))
test('Chatbot Arena', async ({ page }) => runTileRegression(page, 'Chatbot Arena'))
test('Anonymization', async ({ page }) => runTileRegression(page, 'Anonymization'))
test('Anonymisierungs-Pipeline', async ({ page }) => runTileRegression(page, 'Anonymisierungs-Pipeline'))
test('KAIMO', async ({ page }) => runTileRegression(page, 'KAIMO'))
test('OnCoCo', async ({ page }) => runTileRegression(page, 'OnCoCo'))
test('Admin Dashboard', async ({ page }) => runTileRegression(page, 'Admin Dashboard'))
test('Chatbot Admin', async ({ page }) => runTileRegression(page, 'Chatbot Admin'))
test('RAG Admin', async ({ page }) => runTileRegression(page, 'RAG Admin'))
test('Conference Manager', async ({ page }) => runTileRegression(page, 'Conference Manager'))
test('Pipeline', async ({ page }) => runTileRegression(page, 'Pipeline'))
test('User Settings', async ({ page }) => runTileRegression(page, 'User Settings'))
