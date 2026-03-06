/**
 * LLARS Home Tile Sweep E2E Tests
 *
 * Goal:
 * - Click every visible tile on /Home for each main role
 * - Verify navigation leaves /Home
 * - Verify no redirect to /login
 * - Verify no NotFound page
 * - Verify no backend API 5xx during navigation
 *
 * This spec is intended for nightly staging validation.
 */

import { test, expect } from '@playwright/test'
import {
  TEST_USERS,
  quickLogin,
  handlePrivacyPage,
  dismissConsentBanner,
  waitForPageReady
} from './helpers.js'

const HOME_PATH = '/Home'
const HOME_CARD_SELECTOR = '.feature-card'
const HOME_READY_SELECTOR = '.home-page, .features-grid, .feature-card, main'
const NAV_TIMEOUT_MS = 20000
const runTag = process.env.E2E_RUN_TAG || 'manual'

function createApi5xxTracker(page) {
  const failures = []
  const listener = (response) => {
    const url = response.url()
    const status = response.status()
    if (!url.includes('/api/')) return
    if (status >= 500) {
      failures.push({ status, url })
    }
  }

  page.on('response', listener)
  return {
    failures,
    stop: () => page.off('response', listener)
  }
}

async function openHome(page, user) {
  await page.goto(HOME_PATH, { waitUntil: 'domcontentloaded' })

  if (page.url().includes('/login')) {
    await quickLogin(page, user)
    await page.goto(HOME_PATH, { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await handlePrivacyPage(page, HOME_PATH)
  await page.waitForSelector(HOME_READY_SELECTOR, { timeout: 15000 })
  await waitForPageReady(page, 15000)
}

async function readCardTitle(card, fallback) {
  const raw = await card
    .locator('.feature-title')
    .first()
    .textContent()
    .catch(() => '')

  const normalized = (raw || '').replace(/\s+/g, ' ').trim()
  return normalized || fallback
}

async function assertValidTargetPage(page, tileTitle, failuresSinceClick) {
  const currentUrl = page.url()
  expect(currentUrl, `${tileTitle}: redirected to login`).not.toContain('/login')
  expect(currentUrl, `${tileTitle}: did not leave /Home`).not.toContain('/Home')

  const isNotFound = await page
    .locator('.not-found-container')
    .first()
    .isVisible({ timeout: 2000 })
    .catch(() => false)
  expect(isNotFound, `${tileTitle}: opened NotFound page`).toBeFalsy()

  const hasMainContent = await page
    .locator('main, .v-main, .page-container, .overview-page, .panel-content')
    .first()
    .isVisible({ timeout: 8000 })
    .catch(() => false)
  expect(hasMainContent, `${tileTitle}: no visible page content`).toBeTruthy()

  const summary = failuresSinceClick.map((f) => `${f.status} ${f.url}`).join('\n')
  expect(
    failuresSinceClick,
    `${tileTitle}: backend API 5xx detected\n${summary || '(no details)'}`
  ).toEqual([])
}

async function runTileSweep(page, user, roleLabel) {
  console.log(`[E2E][${runTag}] Starting home tile sweep for role=${roleLabel}`)
  const tracker = createApi5xxTracker(page)

  try {
    await quickLogin(page, user)
    await openHome(page, user)

    const initialCardCount = await page.locator(HOME_CARD_SELECTOR).count()
    expect(initialCardCount, `${roleLabel}: no tiles visible on /Home`).toBeGreaterThan(0)

    for (let index = 0; index < initialCardCount; index += 1) {
      await openHome(page, user)

      const cards = page.locator(HOME_CARD_SELECTOR)
      const cardCount = await cards.count()
      expect(
        cardCount,
        `${roleLabel}: tile count changed unexpectedly while iterating`
      ).toBeGreaterThan(index)

      const card = cards.nth(index)
      const tileTitle = await readCardTitle(card, `tile-${index + 1}`)
      const failureStartIndex = tracker.failures.length

      await test.step(`${roleLabel} -> ${tileTitle}`, async () => {
        await card.scrollIntoViewIfNeeded()
        await card.click()

        await expect
          .poll(() => page.url(), {
            timeout: NAV_TIMEOUT_MS,
            message: `${tileTitle}: route did not change from /Home`
          })
          .not.toContain('/Home')

        await dismissConsentBanner(page)
        await waitForPageReady(page, 12000)

        const failuresSinceClick = tracker.failures.slice(failureStartIndex)
        await assertValidTargetPage(page, tileTitle, failuresSinceClick)
      })
    }
  } finally {
    tracker.stop()
  }
}

test.describe('Home Tile Sweep Nightly', () => {
  test.setTimeout(360000)

  test('E2E_HOME_SWEEP_001: researcher can open every visible home tile', async ({ page }) => {
    await runTileSweep(page, TEST_USERS.researcher, 'researcher')
  })

  test('E2E_HOME_SWEEP_002: evaluator can open every visible home tile', async ({ page }) => {
    await runTileSweep(page, TEST_USERS.evaluator, 'evaluator')
  })

  test('E2E_HOME_SWEEP_003: admin can open every visible home tile', async ({ page }) => {
    await runTileSweep(page, TEST_USERS.admin, 'admin')
  })
})
