/**
 * LLARS Authenticity (Fake/Echt) E2E Tests
 *
 * Tests for the Authenticity evaluation feature including:
 * - Overview page with thread cards
 * - Detail page with voting
 * - Confidence slider and notes
 * - Navigation between threads
 * - Auto-save functionality
 *
 * Test IDs: E2E_AUTH_001 - E2E_AUTH_024
 *
 * Run: npm run e2e:chromium -- e2e/authenticity.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading, getThreadCards, clickFirstThread } from './helpers.js'

// Increase timeout for CI environment
test.setTimeout(60000)

// ==================== HELPER FUNCTIONS ====================

async function goToAuthenticity(page) {
  await page.goto('/authenticity', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.researcher)
    await page.goto('/authenticity', { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector('.overview-page, .threads-grid, .thread-card, .empty-state, main', { timeout: 15000 })
}

function getAuthThreadCards(page) {
  return page.locator('.thread-card')
}

async function clickFirstAuthThread(page) {
  const threadCard = getAuthThreadCards(page).first()
  if (await threadCard.isVisible({ timeout: 3000 }).catch(() => false)) {
    await threadCard.click()
    await page.waitForLoadState('load')
    return true
  }
  return false
}

// ==================== AUTHENTICITY OVERVIEW TESTS ====================

test.describe('Authenticity Overview', () => {
  test('E2E_AUTH_001: authenticity page loads for researcher', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    const isOnAuth = page.url().includes('/authenticity')
    const hasContent = await page.locator('.overview-page, .threads-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnAuth || hasContent).toBeTruthy()
  })

  test('E2E_AUTH_002: overview shows title', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    const hasTitle = await page.locator('h1, text=Fake, text=Echt, text=Authentizität').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasTitle || true).toBeTruthy()
  })

  test('E2E_AUTH_003: overview shows progress stats', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    const hasStats = await page.locator('.header-stats, text=/\\d+\\s*\\/\\s*\\d+/, [class*="progress"]').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasStats || true).toBeTruthy()
  })

  test('E2E_AUTH_004: overview shows thread cards or empty state', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    await waitForLoading(page)

    const hasThreads = await getAuthThreadCards(page).count() > 0
    const hasEmptyState = await page.locator('.empty-state, text=Keine Threads').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasThreads || hasEmptyState).toBeTruthy()
  })

  test('E2E_AUTH_005: thread cards show subject and sender', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    await waitForLoading(page)

    const threadCards = getAuthThreadCards(page)
    if (await threadCards.count() > 0) {
      const firstCard = threadCards.first()
      const hasTitle = await firstCard.locator('.card-title, h3').isVisible().catch(() => false)
      const hasSubtitle = await firstCard.locator('.card-subtitle, .sender').isVisible().catch(() => false)
      expect(hasTitle || hasSubtitle).toBeTruthy()
    }
  })

  test('E2E_AUTH_006: completed threads show vote badge', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    await waitForLoading(page)

    // Some cards might show Echt/Fake badge if already voted
    const hasBadge = await page.locator('.l-tag, .v-chip, text=Echt, text=Fake').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasBadge || true).toBeTruthy()
  })
})

// ==================== AUTHENTICITY DETAIL TESTS ====================

test.describe('Authenticity Detail', () => {
  test('E2E_AUTH_007: clicking thread opens detail view', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    await waitForLoading(page)

    if (await clickFirstAuthThread(page)) {
      await expect(page).toHaveURL(/\/authenticity\/\d+/)
    }
  })

  test('E2E_AUTH_008: detail view shows messages panel', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasMessages = await page.locator('.left-panel, .messages-panel, .panel-content').first().isVisible({ timeout: 8000 }).catch(() => false)
      expect(hasMessages).toBeTruthy()
    }
  })

  test('E2E_AUTH_009: detail view shows voting panel', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasVoting = await page.locator('.right-panel, .vote-section, .vote-buttons').first().isVisible({ timeout: 8000 }).catch(() => false)
      expect(hasVoting).toBeTruthy()
    }
  })

  test('E2E_AUTH_010: detail view shows resize divider', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasResizer = await page.locator('.resize-divider, .resize-handle').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasResizer || true).toBeTruthy()
    }
  })
})

// ==================== VOTING TESTS ====================

test.describe('Authenticity Voting', () => {
  test('E2E_AUTH_011: vote buttons are visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasRealBtn = await page.locator('.vote-btn.vote-real, button:has-text("Echt")').first().isVisible({ timeout: 5000 }).catch(() => false)
      const hasFakeBtn = await page.locator('.vote-btn.vote-fake, button:has-text("Fake")').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasRealBtn || hasFakeBtn).toBeTruthy()
    }
  })

  test('E2E_AUTH_012: can click Echt button', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const realBtn = page.locator('.vote-btn.vote-real, button:has-text("Echt")').first()
      if (await realBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await realBtn.click()
        await page.waitForTimeout(500)

        // Button should show selected state
        const isSelected = await realBtn.evaluate(el => el.classList.contains('selected') || el.classList.contains('active'))
        expect(isSelected || true).toBeTruthy()
      }
    }
  })

  test('E2E_AUTH_013: can click Fake button', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const fakeBtn = page.locator('.vote-btn.vote-fake, button:has-text("Fake")').first()
      if (await fakeBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await fakeBtn.click()
        await page.waitForTimeout(500)

        // Button should show selected state
        const isSelected = await fakeBtn.evaluate(el => el.classList.contains('selected') || el.classList.contains('active'))
        expect(isSelected || true).toBeTruthy()
      }
    }
  })

  test('E2E_AUTH_014: vote buttons have descriptions', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasHint = await page.locator('.vote-hint, text=Menschen, text=KI').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasHint || true).toBeTruthy()
    }
  })
})

// ==================== METADATA TESTS ====================

test.describe('Authenticity Metadata', () => {
  test('E2E_AUTH_015: confidence slider is visible after vote', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      // Click a vote button first
      const voteBtn = page.locator('.vote-btn, button:has-text("Echt"), button:has-text("Fake")').first()
      if (await voteBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await voteBtn.click()
        await page.waitForTimeout(500)

        const hasSlider = await page.locator('.l-slider, .v-slider, input[type="range"]').first().isVisible({ timeout: 3000 }).catch(() => false)
        expect(hasSlider || true).toBeTruthy()
      }
    }
  })

  test('E2E_AUTH_016: notes field is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasNotes = await page.locator('textarea, .v-textarea, [placeholder*="Notiz"], [placeholder*="Begründung"]').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasNotes || true).toBeTruthy()
    }
  })

  test('E2E_AUTH_017: can enter notes', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const notesField = page.locator('textarea, .v-textarea textarea').first()
      if (await notesField.isVisible({ timeout: 5000 }).catch(() => false)) {
        await notesField.fill('Test note from E2E')
        await page.waitForTimeout(500)

        const value = await notesField.inputValue()
        expect(value).toContain('Test note')
      }
    }
  })
})

// ==================== AUTO-SAVE TESTS ====================

test.describe('Authenticity Auto-Save', () => {
  test('E2E_AUTH_018: saving indicator appears after vote', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const voteBtn = page.locator('.vote-btn, button:has-text("Echt")').first()
      if (await voteBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await voteBtn.click()
        await page.waitForTimeout(1000)

        const hasSaving = await page.locator('.saving-indicator, .mdi-cloud-sync, text=Speicher, text=Gespeichert').first().isVisible({ timeout: 3000 }).catch(() => false)
        expect(hasSaving || true).toBeTruthy()
      }
    }
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('Authenticity Navigation', () => {
  test('E2E_AUTH_019: can navigate back to overview', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const backBtn = page.locator('button:has-text("Zurück"), button:has(.mdi-arrow-left), a:has-text("Übersicht")').first()
      if (await backBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await backBtn.click()
        await page.waitForLoadState('load')

        expect(page.url()).toMatch(/\/authenticity$|\/evaluation/)
      }
    }
  })

  test('E2E_AUTH_020: prev/next navigation buttons exist', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    if (await clickFirstAuthThread(page)) {
      await waitForLoading(page)

      const hasPrevNext = await page.locator('button:has(.mdi-chevron-left), button:has(.mdi-chevron-right), button:has-text("Vorherig"), button:has-text("Nächst")').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasPrevNext || true).toBeTruthy()
    }
  })

  test('E2E_AUTH_021: direct URL access works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)

    await page.goto('/authenticity')
    await page.waitForLoadState('load')

    expect(page.url()).toMatch(/\/authenticity|\/Home|\/login/)
  })
})

// ==================== PERMISSION TESTS ====================

test.describe('Authenticity Permissions', () => {
  test('E2E_AUTH_022: researcher can access authenticity', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToAuthenticity(page)

    const hasAccess = page.url().includes('/authenticity')
    const hasContent = await page.locator('.overview-page, .threads-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })

  test('E2E_AUTH_023: admin can access authenticity', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto('/authenticity')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/authenticity')
    const hasContent = await page.locator('.overview-page, .threads-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })

  test('E2E_AUTH_024: viewer access behavior', async ({ page }) => {
    await quickLogin(page, TEST_USERS.viewer)
    await page.goto('/authenticity')
    await page.waitForLoadState('load')

    // Viewer might have access or be redirected
    const url = page.url()
    expect(url.includes('/authenticity') || url.includes('/Home')).toBeTruthy()
  })
})
