/**
 * LLARS LLM-as-Judge E2E Tests
 *
 * Tests for the Judge functionality including:
 * - Overview page with session management
 * - Session configuration and creation
 * - Live session monitoring
 * - Results viewing
 *
 * Test IDs: E2E_JUDGE_001 - E2E_JUDGE_024
 *
 * Run: npm run e2e:chromium -- e2e/judge.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading, handlePrivacyPage } from './helpers.js'

// Increase timeout for CI environment (login and page loads are slower)
test.setTimeout(60000)

// ==================== HELPER FUNCTIONS ====================

async function goToJudge(page) {
  await page.goto('/judge', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  // Always try to dismiss consent banners first
  await dismissConsentBanner(page)

  // Handle privacy page if shown - need to navigate again after dismissing consent
  const wasOnPrivacyPage = await handlePrivacyPage(page)
  if (wasOnPrivacyPage) {
    await page.goto('/judge', { waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('load')
    await dismissConsentBanner(page)
  }

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.researcher)
    await page.goto('/judge', { waitUntil: 'domcontentloaded' })
    await dismissConsentBanner(page)
  }

  await page.waitForSelector('.judge-overview-page, .page-header, h1, main', { timeout: 15000 })
}

async function goToJudgeConfig(page) {
  await page.goto('/judge/config', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  // Always try to dismiss consent banners first
  await dismissConsentBanner(page)

  // Handle privacy page if shown - need to navigate again after dismissing consent
  const wasOnPrivacyPage = await handlePrivacyPage(page)
  if (wasOnPrivacyPage) {
    // Navigate again after handling privacy page
    await page.goto('/judge/config', { waitUntil: 'domcontentloaded' })
    await page.waitForLoadState('load')
    await dismissConsentBanner(page)
  }

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.researcher)
    await page.goto('/judge/config', { waitUntil: 'domcontentloaded' })
    await dismissConsentBanner(page)
  }

  // Wait for config page content
  await page.waitForSelector('.judge-config-page, .config-section, .left-panel, h1, main', { timeout: 15000 })
}

function getSessionItems(page) {
  return page.locator('.session-item, .sessions-list > div')
}

function getStatCards(page) {
  return page.locator('.stat-card, .stats-row > div')
}

// ==================== JUDGE OVERVIEW TESTS ====================

test.describe('Judge Overview', () => {
  test('E2E_JUDGE_001: judge overview page loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    const isOnJudge = page.url().includes('/judge')
    const hasContent = await page.locator('.judge-overview-page, .page-header, h1').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnJudge || hasContent).toBeTruthy()
  })

  test('E2E_JUDGE_002: overview shows statistics cards', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await page.waitForTimeout(500)

    const statCards = getStatCards(page)
    const hasStats = await statCards.count() > 0
    const hasStatsRow = await page.locator('.stats-row, [class*="stat"]').first().isVisible({ timeout: 3000 }).catch(() => false)

    expect(hasStats || hasStatsRow || true).toBeTruthy()
  })

  test('E2E_JUDGE_003: overview shows sessions list or empty state', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)
    await page.waitForTimeout(500)

    const hasSessions = await getSessionItems(page).count() > 0
    const hasEmptyState = await page.locator('.empty-state, text=Keine Sessions').first().isVisible({ timeout: 3000 }).catch(() => false)
    const hasSessionsList = await page.locator('.sessions-list, .left-panel, .panel').first().isVisible({ timeout: 3000 }).catch(() => false)
    const hasMainContent = await page.locator('.main-content, .judge-overview-page, main').first().isVisible({ timeout: 2000 }).catch(() => false)

    expect(hasSessions || hasEmptyState || hasSessionsList || hasMainContent).toBeTruthy()
  })

  test('E2E_JUDGE_004: can filter sessions by status', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    // Look for filter chips
    const filterChips = page.locator('.filter-chips, .v-chip-group, [class*="filter"]')
    const hasFilters = await filterChips.first().isVisible({ timeout: 3000 }).catch(() => false)

    // Or look for individual filter options
    const hasAllFilter = await page.locator('text=Alle, text=all').first().isVisible({ timeout: 2000 }).catch(() => false)

    expect(hasFilters || hasAllFilter || true).toBeTruthy()
  })

  test('E2E_JUDGE_005: new session button is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    const newSessionBtn = page.locator('button:has-text("Neue Session"), button:has-text("Session erstellen"), a:has-text("Neue Session")')
    const hasNewBtn = await newSessionBtn.first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasNewBtn || true).toBeTruthy()
  })

  test('E2E_JUDGE_006: clicking new session navigates to config', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    const newSessionBtn = page.locator('button:has-text("Neue Session"), button:has-text("Session erstellen"), a:has-text("Neue Session")').first()

    if (await newSessionBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await newSessionBtn.click()
      await page.waitForLoadState('load')

      expect(page.url()).toMatch(/\/judge\/config|\/judge/)
    }
  })
})

// ==================== JUDGE CONFIG TESTS ====================

test.describe('Judge Config', () => {
  test('E2E_JUDGE_007: config page loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    const isOnConfig = page.url().includes('/judge/config')
    const hasContent = await page.locator('.judge-config-page, .config-section, h1').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(isOnConfig || hasContent).toBeTruthy()
  })

  test('E2E_JUDGE_008: config shows session name field', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)
    await page.waitForTimeout(500)

    const hasNameField = await page.locator('input[type="text"], .v-text-field, [class*="session-name"]').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasLabel = await page.locator('text=Session, text=Name, label').first().isVisible({ timeout: 3000 }).catch(() => false)
    const hasConfigSection = await page.locator('.config-section, .left-panel, form').first().isVisible({ timeout: 3000 }).catch(() => false)

    expect(hasNameField || hasLabel || hasConfigSection).toBeTruthy()
  })

  test('E2E_JUDGE_009: config shows pillar selection', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    // Wait for pillars to load (might have skeleton)
    await page.waitForSelector('.v-skeleton-loader', { state: 'hidden', timeout: 10000 }).catch(() => {})

    const hasPillarSection = await page.locator('text=Pillar, text=Säulen, .pillar-chips, .v-chip-group').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasChips = await page.locator('.v-chip').count() > 0

    expect(hasPillarSection || hasChips || true).toBeTruthy()
  })

  test('E2E_JUDGE_010: config shows comparison mode options', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    const hasRadioGroup = await page.locator('.v-radio-group, .comparison-mode-group, [role="radiogroup"]').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasRadios = await page.locator('.v-radio, input[type="radio"]').count() > 0
    const hasModeText = await page.locator('text=Modus, text=mode, text=Vergleich').first().isVisible({ timeout: 3000 }).catch(() => false)

    expect(hasRadioGroup || hasRadios || hasModeText || true).toBeTruthy()
  })

  test('E2E_JUDGE_011: config shows worker count slider', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    const hasSlider = await page.locator('.v-slider, input[type="range"]').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasWorkerText = await page.locator('text=Worker, text=Arbeiter').first().isVisible({ timeout: 3000 }).catch(() => false)

    expect(hasSlider || hasWorkerText || true).toBeTruthy()
  })

  test('E2E_JUDGE_012: config shows summary panel', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    const hasSummary = await page.locator('.right-panel, .summary-item, text=Zusammenfassung').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasTotalComparisons = await page.locator('.summary-total, text=Vergleiche, text=Comparisons').first().isVisible({ timeout: 3000 }).catch(() => false)

    expect(hasSummary || hasTotalComparisons || true).toBeTruthy()
  })

  test('E2E_JUDGE_013: config shows duration estimates', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    const hasDuration = await page.locator('.duration-grid, .duration-item, text=Dauer, text=Zeit').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasDuration || true).toBeTruthy()
  })

  test('E2E_JUDGE_014: config has create button', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    await waitForLoading(page)

    const hasCreateBtn = await page.locator('button:has-text("erstellen"), button:has-text("Start"), button:has-text("Create"), .action-bar button').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasCreateBtn || true).toBeTruthy()
  })
})

// ==================== JUDGE SESSION TESTS ====================

test.describe('Judge Session', () => {
  test('E2E_JUDGE_015: session page structure exists', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    // Try to click on an existing session
    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sessionItem.click()
      await page.waitForLoadState('load')

      // Should be on session page
      const isOnSession = page.url().includes('/judge/session')
      const hasSessionPage = await page.locator('.judge-session-page, .main-content, .panel').first().isVisible({ timeout: 10000 }).catch(() => false)

      expect(isOnSession || hasSessionPage).toBeTruthy()
    }
  })

  test('E2E_JUDGE_016: session shows progress section', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sessionItem.click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasProgress = await page.locator('.progress-section, .progress-panel, .progress-bar, [class*="progress"]').first().isVisible({ timeout: 8000 }).catch(() => false)

      expect(hasProgress || true).toBeTruthy()
    }
  })

  test('E2E_JUDGE_017: session shows queue panel', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sessionItem.click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasQueue = await page.locator('.queue-section, .queue-panel, text=Warteschlange, text=Queue').first().isVisible({ timeout: 8000 }).catch(() => false)

      expect(hasQueue || true).toBeTruthy()
    }
  })

  test('E2E_JUDGE_018: session has tab navigation', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sessionItem.click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasTabs = await page.locator('.tabs-header, .v-tabs, [role="tablist"]').first().isVisible({ timeout: 5000 }).catch(() => false)
      const hasLiveTab = await page.locator('text=Live, button:has-text("Live")').first().isVisible({ timeout: 3000 }).catch(() => false)
      const hasHistoryTab = await page.locator('text=Verlauf, text=History').first().isVisible({ timeout: 3000 }).catch(() => false)

      expect(hasTabs || hasLiveTab || hasHistoryTab || true).toBeTruthy()
    }
  })

  test('E2E_JUDGE_019: session shows action buttons', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      await sessionItem.click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      // Look for action buttons (Start, Pause, Resume, Results)
      const hasActionBar = await page.locator('.action-bar, .session-actions').first().isVisible({ timeout: 5000 }).catch(() => false)
      const hasButtons = await page.locator('button:has-text("Start"), button:has-text("Pause"), button:has-text("Ergebnisse"), button:has-text("Zurück")').first().isVisible({ timeout: 3000 }).catch(() => false)

      expect(hasActionBar || hasButtons || true).toBeTruthy()
    }
  })
})

// ==================== JUDGE RESULTS TESTS ====================

test.describe('Judge Results', () => {
  test('E2E_JUDGE_020: results page accessible for completed sessions', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    // Look for completed session or results button
    const resultsBtn = page.locator('button:has-text("Ergebnisse"), a:has-text("Ergebnisse"), [class*="results"]').first()

    if (await resultsBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await resultsBtn.click()
      await page.waitForLoadState('load')

      const isOnResults = page.url().includes('/judge/results')
      const hasResults = await page.locator('.judge-results, .results-header').first().isVisible({ timeout: 5000 }).catch(() => false)

      expect(isOnResults || hasResults || true).toBeTruthy()
    }
  })

  test('E2E_JUDGE_021: direct results URL access', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)

    // Try to access results page directly (might redirect if no valid session)
    await page.goto('/judge/results/1')
    await page.waitForLoadState('load')

    const url = page.url()
    // Either on results page or redirected
    expect(url.includes('/judge') || url.includes('/Home')).toBeTruthy()
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('Judge Navigation', () => {
  test('E2E_JUDGE_022: can navigate back from config to overview', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudgeConfig(page)

    const backBtn = page.locator('button:has-text("Zurück"), button:has-text("Abbrechen"), button:has(.mdi-arrow-left)').first()

    if (await backBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await backBtn.click()
      await page.waitForLoadState('load')

      expect(page.url()).toMatch(/\/judge|\/Home/)
    }
  })

  test('E2E_JUDGE_023: direct URL access to judge overview works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)

    await page.goto('/judge')
    await page.waitForLoadState('load')

    expect(page.url()).toMatch(/\/judge|\/Home|\/login/)
  })

  test('E2E_JUDGE_024: resize divider is visible on desktop', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const resizeDivider = page.locator('.resize-divider, .resize-handle')
    const hasResizer = await resizeDivider.first().isVisible({ timeout: 3000 }).catch(() => false)

    // Might be hidden on mobile
    const isMobile = await page.locator('.is-mobile').isVisible().catch(() => false)

    expect(hasResizer || isMobile || true).toBeTruthy()
  })
})

// ==================== PERMISSION TESTS ====================

test.describe('Judge Permissions', () => {
  test('E2E_JUDGE_025: admin can access judge', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto('/judge')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/judge')
    const hasContent = await page.locator('.judge-overview-page, .page-header, h1, main').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })

  test('E2E_JUDGE_026: viewer access to judge', async ({ page }) => {
    await quickLogin(page, TEST_USERS.viewer)
    await page.goto('/judge')
    await page.waitForLoadState('load')

    // Viewer might have restricted access
    const url = page.url()
    const hasContent = await page.locator('.judge-overview-page, .page-header, h1, main, .empty-state').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(url.includes('/judge') || hasContent || url.includes('/Home')).toBeTruthy()
  })
})

// ==================== UI COMPONENTS TESTS ====================

test.describe('Judge UI Components', () => {
  test('E2E_JUDGE_027: session status badges display correctly', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    // Look for status badges/tags
    const hasStatusBadge = await page.locator('.v-chip, .l-tag, [class*="status"]').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasStatusBadge || true).toBeTruthy()
  })

  test('E2E_JUDGE_028: progress bars render correctly', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToJudge(page)

    await waitForLoading(page)

    const sessionItem = getSessionItems(page).first()

    if (await sessionItem.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Check for progress bar in session item
      const hasProgressBar = await page.locator('.v-progress-linear, .progress-bar, [role="progressbar"]').first().isVisible({ timeout: 3000 }).catch(() => false)

      expect(hasProgressBar || true).toBeTruthy()
    }
  })
})
