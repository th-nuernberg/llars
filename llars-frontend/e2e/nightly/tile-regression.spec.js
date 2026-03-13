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

const ROLE_TO_USER_KEY = {
  evaluator: 'evaluator',
  researcher: 'researcher',
  chatbot_manager: 'chatbot_manager',
  admin: 'admin'
}

// Tiles with heavy API calls or complex editors — skip button sweep to stay within timeout
// and avoid 429 rate-limit cascades in CI.
const TILE_SMOKE_PROFILES = {
  'Batch Generation': { maxButtons: 0 },
  'Latex Collab': { maxButtons: 0 },
  'Chatbot Arena': { maxButtons: 0 },
  'Pipeline': { maxButtons: 0 },
  'Admin Dashboard': { maxButtons: 0 },
  'Conference Manager': { maxButtons: 0 }
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
  // Redirected away from the tile route = access was blocked
  const tileRouteBase = tile.route.split('?')[0]
  if (currentUrl.includes('/login') || currentUrl.includes('/Home') || !currentUrl.includes(tileRouteBase)) {
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

// ---------------------------------------------------------------------------
// Section 1: Role Visibility (4 tests = 4 logins)
//
// One login per role, then DOM-check ALL 20 tiles (visible/hidden).
// No clicks, no navigation — pure visibility assertion to stay within rate limits.
// ---------------------------------------------------------------------------
test.describe('Tile Visibility by Role', () => {
  test.describe.configure({ timeout: 120_000 })

  for (const role of ROLE_ORDER) {
    test(`Visibility :: ${role}`, async ({ page }) => {
      const userKey = ROLE_TO_USER_KEY[role]
      const user = TEST_USERS[userKey]
      await quickLogin(page, user)
      await openHome(page, user)

      for (const tile of tileContract.tiles) {
        const shouldBeVisible = Array.isArray(tile.allowed_roles) && tile.allowed_roles.includes(role)
        const testId = routeToTileTestId(tile.route)

        await test.step(`${tile.name} ${shouldBeVisible ? 'visible' : 'hidden'}`, async () => {
          const tileCard = page.locator(`[data-testid="${testId}"]`).first()

          if (shouldBeVisible) {
            await expect(tileCard, `${tile.name} should be visible for ${role}`).toBeVisible({ timeout: 10000 })
          } else {
            await expect(tileCard, `${tile.name} should be hidden for ${role}`).toHaveCount(0)
          }
        })
      }
    })
  }
})

// ---------------------------------------------------------------------------
// Section 2: Admin Navigation Smoke (16 active + 4 skipped = 20 tiles)
//
// Each tile gets its own test() to satisfy contract-validator tile-name matching.
// Only admin: login → Home → tile click → navigation check → optional button sweep.
// ---------------------------------------------------------------------------
test.describe('Tile Navigation (admin)', () => {
  test.describe.configure({ timeout: 420_000 })

  async function runAdminNavigation(page, tileName) {
    const tile = tileContract.tiles.find((entry) => entry.name === tileName)
    expect(tile, `Tile '${tileName}' must exist in home_tiles.contract.json`).toBeTruthy()
    const smokeProfile = TILE_SMOKE_PROFILES[tile.name] || {}
    const maxButtons = smokeProfile.maxButtons ?? 5

    const user = TEST_USERS.admin
    await quickLogin(page, user)
    await openHome(page, user)

    const testId = routeToTileTestId(tile.route)
    const tileCard = page.locator(`[data-testid="${testId}"]`).first()

    await expect(tileCard, `${tile.name} should be visible for admin`).toBeVisible({ timeout: 10000 })

    await tileCard.scrollIntoViewIfNeeded()
    await tileCard.click()

    await expect
      .poll(() => page.url(), {
        timeout: 15000,
        message: `${tile.name} did not navigate`
      })
      .not.toContain('/Home')

    await expect(page.url(), `${tile.name} redirected to login`).not.toContain('/login')
    await expect(page.url(), `${tile.name} did not reach expected route`)
      .toContain(tile.route.split('?')[0])

    await dismissConsentBanner(page)
    await waitForPageReady(page, 12000)
    if (maxButtons > 0) {
      await safeButtonSweep(page, maxButtons)
    }
  }

  test('Prompt Engineering', async ({ page }) => runAdminNavigation(page, 'Prompt Engineering'))
  test('Batch Generation', async ({ page }) => runAdminNavigation(page, 'Batch Generation'))
  test('Evaluation', async ({ page }) => runAdminNavigation(page, 'Evaluation'))
  test('Scenario Manager', async ({ page }) => runAdminNavigation(page, 'Scenario Manager'))
  test('Chatbot', async ({ page }) => runAdminNavigation(page, 'Chatbot'))
  test('Video', async ({ page }) => runAdminNavigation(page, 'Video'))
  test('Markdown Collab', async ({ page }) => runAdminNavigation(page, 'Markdown Collab'))
  test('Latex Collab', async ({ page }) => runAdminNavigation(page, 'Latex Collab'))
  test('Chatbot Arena', async ({ page }) => runAdminNavigation(page, 'Chatbot Arena'))
  test('Anonymization', async ({ page }) => runAdminNavigation(page, 'Anonymization'))
  test('Anonymisierungs-Pipeline', async ({ page }) => runAdminNavigation(page, 'Anonymisierungs-Pipeline'))
  test('KAIMO', async ({ page }) => runAdminNavigation(page, 'KAIMO'))
  test.skip('OnCoCo', async ({ page }) => runAdminNavigation(page, 'OnCoCo'))
  test.skip('DB Preisagent', async ({ page }) => runAdminNavigation(page, 'DB Preisagent'))
  test('Admin Dashboard', async ({ page }) => runAdminNavigation(page, 'Admin Dashboard'))
  test.skip('Chatbot Admin', async ({ page }) => runAdminNavigation(page, 'Chatbot Admin'))
  test.skip('RAG Admin', async ({ page }) => runAdminNavigation(page, 'RAG Admin'))
  test('Conference Manager', async ({ page }) => runAdminNavigation(page, 'Conference Manager'))
  test('Pipeline', async ({ page }) => runAdminNavigation(page, 'Pipeline'))
  test('User Settings', async ({ page }) => runAdminNavigation(page, 'User Settings'))
})

// ---------------------------------------------------------------------------
// Section 3: Negative Route Checks (3 tests = 3 logins)
//
// Representative samples per non-admin role. Each test logs in once, then
// verifies that 3 hidden tile routes are blocked or read-restricted.
// ---------------------------------------------------------------------------
test.describe('Negative Route Access', () => {
  test.describe.configure({ timeout: 120_000 })

  const NEGATIVE_CHECKS = {
    evaluator: ['Chatbot Arena', 'Anonymisierungs-Pipeline', 'Admin Dashboard'],
    researcher: ['Chatbot Arena', 'Admin Dashboard', 'Pipeline'],
    chatbot_manager: ['Evaluation', 'Anonymization', 'Conference Manager']
  }

  for (const [role, tileNames] of Object.entries(NEGATIVE_CHECKS)) {
    test(`Negative Routes :: ${role}`, async ({ page }) => {
      const userKey = ROLE_TO_USER_KEY[role]
      const user = TEST_USERS[userKey]
      await quickLogin(page, user)

      for (const tileName of tileNames) {
        const tile = tileContract.tiles.find((t) => t.name === tileName)
        expect(tile, `Tile '${tileName}' must exist in contract`).toBeTruthy()

        await test.step(`${tileName} blocked for ${role}`, async () => {
          await assertDirectRouteBlockedOrRestricted(page, tile)
        })
      }
    })
  }
})
