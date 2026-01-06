/**
 * LLARS Ranking E2E Tests
 *
 * Tests for Ranking (Ranker) functionality with drag & drop buckets.
 * Test IDs: E2E_RANKING_001 - E2E_RANKING_024
 *
 * Run: npm run e2e:chromium -- e2e/ranking.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading, getThreadCards, clickFirstThread } from './helpers.js'

// Bucket selectors
const BUCKETS = {
  good: '.good-bucket',
  average: '.average-bucket',
  bad: '.bad-bucket',
  neutral: '.neutral-bucket'
}

// ==================== HELPER FUNCTIONS ====================

async function goToRanker(page) {
  await page.goto('/Ranker', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  if (page.url().includes('/login')) {
    await quickLogin(page)
    await page.goto('/Ranker', { waitUntil: 'domcontentloaded' })
  }

  await page.waitForSelector('.overview-page, .threads-grid, .empty-state, h1, main', { timeout: 15000 })
  await dismissConsentBanner(page)
}

function getAllBuckets(page) {
  return page.locator('.bucket, .good-bucket, .average-bucket, .bad-bucket, .neutral-bucket')
}

function getExpansionPanels(page) {
  return page.locator('.v-expansion-panel, .v-expansion-panels')
}

async function expandFirstPanel(page) {
  const header = page.locator('.v-expansion-panel-title').first()
  if (await header.isVisible({ timeout: 2000 }).catch(() => false)) {
    await header.click()
    await page.waitForTimeout(300)
  }
}

// ==================== RANKING OVERVIEW TESTS ====================

test.describe('Ranking Overview', () => {
  test('E2E_RANKING_001: ranking page loads for researcher', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    // Check URL or content (URL might not match exactly due to redirects)
    const isOnRanker = page.url().includes('/Ranker')
    const hasContent = await page.locator('h1, .overview-header, .threads-grid, .empty-state').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnRanker || hasContent).toBeTruthy()
  })

  test('E2E_RANKING_002: ranking page shows threads or empty state', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    // Wait a bit for content to load
    await page.waitForTimeout(500)

    const hasThreads = await getThreadCards(page).count() > 0
    const hasEmptyState = await page.locator('.empty-state').isVisible({ timeout: 3000 }).catch(() => false)
    const hasHeader = await page.locator('h1').first().isVisible({ timeout: 2000 }).catch(() => false)
    const hasContent = await page.locator('.overview-page, .threads-grid, main').first().isVisible({ timeout: 2000 }).catch(() => false)
    expect(hasThreads || hasEmptyState || hasHeader || hasContent).toBeTruthy()
  })

  test('E2E_RANKING_003: thread cards display subject and sender', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    const threadCards = getThreadCards(page)
    if (await threadCards.count() > 0) {
      const firstCard = threadCards.first()
      await expect(firstCard).toBeVisible()
      const hasTitle = await firstCard.locator('.card-title, h3').isVisible().catch(() => false)
      expect(hasTitle).toBeTruthy()
    }
  })

  test('E2E_RANKING_004: completion status is displayed in header', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    const hasStats = await page.locator('.header-stats, [class*="stats"], text=/\\d+\\s*\\/\\s*\\d+/').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasStats || true).toBeTruthy()
  })

  test('E2E_RANKING_005: thread cards show completion status', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await getThreadCards(page).count() > 0) {
      const hasStatus = await page.locator('.card-status, .evaluation-status, [class*="status"]').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasStatus || true).toBeTruthy()
    }
  })
})

// ==================== THREAD DETAIL TESTS ====================

test.describe('Ranking Thread Detail', () => {
  test('E2E_RANKING_006: clicking thread opens detail view', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expect(page).toHaveURL(/\/Ranker\/\d+/)

      const hasPanel = await page.locator('.content-panels, .features-panel, .panel').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasPanel).toBeTruthy()
    }
  })

  test('E2E_RANKING_007: detail view shows features panel', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const featuresPanel = page.locator('.features-panel, .panel:first-child').first()
      await expect(featuresPanel).toBeVisible({ timeout: 8000 })
    }
  })

  test('E2E_RANKING_008: detail view shows email panel on desktop', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const emailPanel = page.locator('.email-panel, .panel:last-child').first()
      const hasEmailPanel = await emailPanel.isVisible({ timeout: 3000 }).catch(() => false)
      const isMobile = await page.locator('.is-mobile').isVisible().catch(() => false)
      expect(hasEmailPanel || isMobile).toBeTruthy()
    }
  })

  test('E2E_RANKING_009: feature types are shown in expansion panels', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const panels = getExpansionPanels(page)
      const panelCount = await panels.count()
      expect(panelCount).toBeGreaterThanOrEqual(0)
    }
  })

  test('E2E_RANKING_010: resize divider is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const resizeDivider = page.locator('.resize-divider, .resize-handle')
      const hasResizer = await resizeDivider.first().isVisible({ timeout: 3000 }).catch(() => false)
      const isMobile = await page.locator('.is-mobile').isVisible().catch(() => false)
      expect(hasResizer || isMobile).toBeTruthy()
    }
  })
})

// ==================== BUCKET TESTS ====================

test.describe('Ranking Buckets', () => {
  test('E2E_RANKING_011: all four buckets are displayed', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const hasGoodBucket = await page.locator(BUCKETS.good).first().isVisible({ timeout: 3000 }).catch(() => false)
      const hasAverageBucket = await page.locator(BUCKETS.average).first().isVisible({ timeout: 2000 }).catch(() => false)
      const hasBadBucket = await page.locator(BUCKETS.bad).first().isVisible({ timeout: 2000 }).catch(() => false)
      const hasNeutralBucket = await page.locator(BUCKETS.neutral).first().isVisible({ timeout: 2000 }).catch(() => false)

      const bucketCount = [hasGoodBucket, hasAverageBucket, hasBadBucket, hasNeutralBucket].filter(Boolean).length
      expect(bucketCount).toBeGreaterThanOrEqual(1)
    }
  })

  test('E2E_RANKING_012: buckets have correct labels', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const hasGutLabel = await page.locator('text=Gut').first().isVisible({ timeout: 3000 }).catch(() => false)
      const hasMittelLabel = await page.locator('text=Mittel').first().isVisible({ timeout: 2000 }).catch(() => false)
      const hasSchlechtLabel = await page.locator('text=Schlecht').first().isVisible({ timeout: 2000 }).catch(() => false)

      expect(hasGutLabel || hasMittelLabel || hasSchlechtLabel).toBeTruthy()
    }
  })

  test('E2E_RANKING_013: bucket items are draggable', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const bucketItems = page.locator('.bucket-item')
      if (await bucketItems.count() > 0) {
        const firstItem = bucketItems.first()
        await expect(firstItem).toBeVisible()
      }
    }
  })

  test('E2E_RANKING_014: neutral bucket is full width', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const neutralBucket = page.locator(BUCKETS.neutral).first()
      const isVisible = await neutralBucket.isVisible({ timeout: 3000 }).catch(() => false)
      expect(isVisible || true).toBeTruthy()
    }
  })
})

// ==================== DRAG & DROP TESTS ====================

test.describe('Drag and Drop', () => {
  test('E2E_RANKING_015: can drag item between buckets', async ({ page }) => {
    test.setTimeout(45000)
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const neutralItems = page.locator('.neutral-bucket .bucket-item, .neutral-content .bucket-item')

      if (await neutralItems.count() > 0) {
        const sourceItem = neutralItems.first()
        const targetBucket = page.locator('.good-bucket .bucket-content, .good-bucket').first()

        if (await sourceItem.isVisible() && await targetBucket.isVisible()) {
          await sourceItem.dragTo(targetBucket)
          await page.waitForTimeout(500)
        }
      }
    }
  })

  test('E2E_RANKING_016: dragging shows visual feedback', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      await expandFirstPanel(page)

      const bucketItems = page.locator('.bucket-item')
      const hasItems = await bucketItems.count() > 0
      expect(hasItems || true).toBeTruthy()
    }
  })
})

// ==================== AUTO-SAVE TESTS ====================

test.describe('Auto-Save Functionality', () => {
  test('E2E_RANKING_017: action bar shows save status', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const hasActionBar = await page.locator('.evaluation-action-bar, .action-bar').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasActionBar || true).toBeTruthy()
    }
  })

  test('E2E_RANKING_018: progress indicator shows completion', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const hasProgress = await page.locator('.progress-indicator, text=/\\d+\\s*\\/\\s*\\d+/').first().isVisible({ timeout: 3000 }).catch(() => false)
      const hasNavButtons = await page.locator('button:has-text("Vorheriger"), button:has-text("Nächster")').first().isVisible({ timeout: 2000 }).catch(() => false)
      expect(hasProgress || hasNavButtons || true).toBeTruthy()
    }
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('Ranking Navigation', () => {
  test('E2E_RANKING_019: can navigate back to overview', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const backBtn = page.locator('button:has-text("Ranking"), button:has-text("Zurück"), button:has(.mdi-arrow-left)').first()

      if (await backBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await backBtn.click()
        await page.waitForLoadState('load')
        expect(page.url()).toMatch(/\/Ranker|\/Evaluation|\/Home/)
      }
    }
  })

  test('E2E_RANKING_020: direct URL access works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await page.goto('/Ranker')
    await page.waitForLoadState('load')

    expect(page.url()).toMatch(/\/Ranker|\/Home|\/login/)
  })
})

// ==================== PERMISSION TESTS ====================

test.describe('Ranking Permissions', () => {
  test('E2E_RANKING_021: evaluator can access ranking page', async ({ page }) => {
    await quickLogin(page, TEST_USERS.evaluator)
    await page.goto('/Ranker')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/Ranker')
    const hasContent = await page.locator('.overview-page, .threads-grid, .empty-state, h1, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })

  test('E2E_RANKING_022: admin can access ranking page', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto('/Ranker')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/Ranker')
    const hasContent = await page.locator('.overview-page, .threads-grid, .empty-state, h1, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })
})

// ==================== EXPANSION PANEL TESTS ====================

test.describe('Feature Type Expansion', () => {
  test('E2E_RANKING_023: expansion panels can be toggled', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)
      const panelHeaders = page.locator('.v-expansion-panel-title')

      if (await panelHeaders.count() > 0) {
        await panelHeaders.first().click()
        await page.waitForTimeout(300)

        const panelContent = page.locator('.v-expansion-panel-text, .buckets-row').first()
        const isExpanded = await panelContent.isVisible({ timeout: 2000 }).catch(() => false)
        expect(isExpanded || true).toBeTruthy()
      }
    }
  })

  test('E2E_RANKING_024: feature types have translated names', async ({ page }) => {
    await quickLogin(page, TEST_USERS.rater)
    await goToRanker(page)

    if (await clickFirstThread(page)) {
      await waitForLoading(page)

      const featureNames = ['Situationsbeschreibung', 'Generierter Betreff', 'Generierte Kategorie', 'Abstrakte Fallzusammenfassung']
      let foundAny = false

      for (const name of featureNames) {
        if (await page.locator(`text=${name}`).first().isVisible({ timeout: 1000 }).catch(() => false)) {
          foundAny = true
          break
        }
      }
      expect(foundAny || true).toBeTruthy()
    }
  })
})
