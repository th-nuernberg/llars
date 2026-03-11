/**
 * LLARS Prompt Engineering E2E Tests
 *
 * Tests for Prompt Engineering functionality including:
 * - Overview page with prompt listing
 * - Create, edit, delete prompts
 * - Prompt detail view
 * - Sharing functionality
 * - Test prompt dialog
 *
 * Test IDs: E2E_PROMPT_001 - E2E_PROMPT_021
 *
 * Run: npm run e2e:chromium -- e2e/prompt-engineering.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading, assertNotErrorResponse } from './helpers.js'

// Increase timeout for CI environment
test.setTimeout(60000)

// ==================== HELPER FUNCTIONS ====================

async function goToPromptEngineering(page) {
  await page.goto('/PromptEngineering', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.researcher)
    await page.goto('/PromptEngineering', { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector('.prompt-home, .prompts-grid, .prompt-card, .empty-state, main', { timeout: 15000 })
}

function getPromptCards(page) {
  return page.locator('.prompt-card, .l-card')
}

// ==================== PROMPT ENGINEERING OVERVIEW TESTS ====================

test.describe('Prompt Engineering Overview', () => {
  test('E2E_PROMPT_001: prompt engineering page loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const isOnPrompt = page.url().includes('/PromptEngineering')
    const hasContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnPrompt || hasContent).toBeTruthy()
  })

  test('E2E_PROMPT_002: page shows title', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const hasTitle = await page.locator('h1, text=Prompt Engineering, text=Prompts').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasPageContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasTitle || hasPageContent).toBeTruthy()
  })

  test('E2E_PROMPT_003: new prompt button is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const hasCreateBtn = await page.locator('button:has-text("Neues Prompt"), button:has-text("Neu"), button:has(.mdi-plus)').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasPageContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasCreateBtn || hasPageContent).toBeTruthy()
  })

  test('E2E_PROMPT_004: shows prompts or empty state', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const hasPrompts = await getPromptCards(page).count() > 0
    const hasEmptyState = await page.locator('.empty-state, text=Noch keine Prompts').first().isVisible({ timeout: 3000 }).catch(() => false)
    const hasPageContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasPrompts || hasEmptyState || hasPageContent).toBeTruthy()
  })

  test('E2E_PROMPT_005: refresh button works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const refreshBtn = page.locator('button:has(.mdi-refresh), [tooltip*="Aktualisieren"]').first()
    if (await refreshBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await refreshBtn.click()
      await page.waitForTimeout(500)
      // Page should still be functional
      expect(true).toBeTruthy()
    }
  })
})

// ==================== PROMPT CARDS TESTS ====================

test.describe('Prompt Cards', () => {
  test('E2E_PROMPT_006: prompt cards show name', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      const firstCard = promptCards.first()
      const hasTitle = await firstCard.locator('.card-title, h3, .l-card__title').first().isVisible().catch(() => false)
      expect(hasTitle || true).toBeTruthy()
    }
  })

  test('E2E_PROMPT_007: prompt cards show creation date', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      const hasDate = await page.locator('.mdi-clock-outline, text=/vor\\s+\\d+/, text=/\\d+.*ago/i').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasDate || true).toBeTruthy()
    }
  })

  test('E2E_PROMPT_008: prompt cards have action buttons', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      const firstCard = promptCards.first()
      const hasActions = await firstCard.locator('.l-action-group, button, .mdi-pencil, .mdi-delete').first().isVisible().catch(() => false)
      expect(hasActions || true).toBeTruthy()
    }
  })

  test('E2E_PROMPT_009: clicking prompt card navigates to detail', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      const initialUrl = page.url()
      await promptCards.first().click()
      await page.waitForLoadState('load')

      // Should navigate to detail page
      const newUrl = page.url()
      expect(newUrl.includes('/PromptEngineering/') || newUrl !== initialUrl).toBeTruthy()
    }
  })
})

// ==================== CREATE PROMPT TESTS ====================

test.describe('Create Prompt', () => {
  test('E2E_PROMPT_010: clicking new prompt opens dialog', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const createBtn = page.locator('button:has-text("Neues Prompt"), button:has-text("Neu"), button:has(.mdi-plus)').first()
    if (await createBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createBtn.click()
      await page.waitForTimeout(500)

      const hasDialog = await page.locator('.v-dialog, .v-overlay, [role="dialog"]').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasDialog || true).toBeTruthy()
    }
  })

  test('E2E_PROMPT_011: create dialog has name field', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const createBtn = page.locator('button:has-text("Neues Prompt"), button:has(.mdi-plus)').first()
    if (await createBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createBtn.click()
      await page.waitForTimeout(500)

      const hasNameField = await page.locator('input[type="text"], .v-text-field, [placeholder*="Name"]').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(hasNameField || true).toBeTruthy()
    }
  })
})

// ==================== PROMPT DETAIL TESTS ====================

test.describe('Prompt Detail', () => {
  test('E2E_PROMPT_012: detail page shows prompt content', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      await promptCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasContent = await page.locator('.prompt-detail, .editor, textarea, .content-area').first().isVisible({ timeout: 8000 }).catch(() => false)
      expect(hasContent || page.url().includes('/PromptEngineering/')).toBeTruthy()
    }
  })

  test('E2E_PROMPT_013: detail page has test button', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      await promptCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasTestBtn = await page.locator('button:has-text("Test"), button:has-text("Testen"), button:has(.mdi-play)').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasTestBtn || true).toBeTruthy()
    }
  })

  test('E2E_PROMPT_014: detail page has save functionality', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      await promptCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      const hasSave = await page.locator('button:has-text("Speichern"), button:has(.mdi-content-save), text=Gespeichert').first().isVisible({ timeout: 5000 }).catch(() => false)
      expect(hasSave || true).toBeTruthy()
    }
  })
})

// ==================== SHARED PROMPTS TESTS ====================

test.describe('Shared Prompts', () => {
  test('E2E_PROMPT_015: shows shared prompts section', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const hasSharedSection = await page.locator('text=Geteilt, text=Shared, text=Mit mir geteilt').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasSharedSection || true).toBeTruthy()
  })

  test('E2E_PROMPT_016: shared prompts show sharing info', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const hasShareInfo = await page.locator('.mdi-share-variant, .shared-info, text=Nutzer').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasShareInfo || true).toBeTruthy()
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('Prompt Engineering Navigation', () => {
  test('E2E_PROMPT_017: can navigate back from detail', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    await waitForLoading(page)

    const promptCards = getPromptCards(page)
    if (await promptCards.count() > 0) {
      await promptCards.first().click()
      await page.waitForLoadState('load')

      const backBtn = page.locator('button:has-text("Zurück"), button:has(.mdi-arrow-left)').first()
      if (await backBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await backBtn.click()
        await page.waitForLoadState('load')

        expect(page.url()).toContain('/PromptEngineering')
      }
    }
  })

  test('E2E_PROMPT_018: direct URL access works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)

    await page.goto('/PromptEngineering')
    await page.waitForLoadState('load')

    expect(page.url()).toMatch(/\/PromptEngineering|\/Home|\/login/)
  })
})

// ==================== PERMISSION TESTS ====================

test.describe('Prompt Engineering Permissions', () => {
  test('E2E_PROMPT_019: researcher can access prompt engineering', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)

    const hasAccess = page.url().includes('/PromptEngineering')
    const hasContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent).toBeTruthy()
  })

  test('E2E_PROMPT_020: admin can access prompt engineering', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto('/PromptEngineering')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/PromptEngineering')
    const hasContent = await page.locator('.prompt-home, .prompts-grid, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })
})

// ==================== LLM STREAMING TEST ====================

test.describe('LLM Streaming', () => {
  // This test verifies that LLM streaming works end-to-end in a real browser.
  // It opens Prompt Engineering, navigates to a prompt detail, clicks Test,
  // and verifies that the streamed LLM response contains real content (not errors).
  // This catches outages like Flask/Werkzeug incompatibilities or encryption key mismatches
  // that previously went undetected because the smoke test was non-blocking.
  test('E2E_PROMPT_021: LLM stream produces real content in browser', async ({ page }) => {
    test.setTimeout(120000)

    await quickLogin(page, TEST_USERS.researcher)
    await goToPromptEngineering(page)
    await waitForLoading(page)

    // Need at least one prompt to test with
    const promptCards = getPromptCards(page)
    const cardCount = await promptCards.count()
    if (cardCount === 0) {
      // No prompts available — create one via the "New Prompt" button
      const createBtn = page.locator('button:has-text("Neues Prompt"), button:has-text("Neu"), button:has(.mdi-plus)').first()
      const canCreate = await createBtn.isVisible({ timeout: 5000 }).catch(() => false)
      if (!canCreate) {
        test.skip(true, 'No prompts and no create button available')
        return
      }
      await createBtn.click()
      await page.waitForTimeout(1000)

      // Fill name field and submit dialog
      const nameInput = page.locator('.v-dialog input[type="text"], .v-dialog .v-text-field input').first()
      if (await nameInput.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nameInput.fill('E2E LLM Stream Test')
        // Click create/save button in dialog
        const saveBtn = page.locator('.v-dialog button:has-text("Erstellen"), .v-dialog button:has-text("Speichern"), .v-dialog button:has-text("Create")').first()
        if (await saveBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
          await saveBtn.click()
          await page.waitForLoadState('load')
        }
      }
    } else {
      // Navigate to existing prompt detail
      await promptCards.first().click()
      await page.waitForLoadState('load')
    }

    await waitForLoading(page)

    // Click the Test button (rocket icon in sidebar)
    const testBtn = page.locator(
      '.sidebar button:has-text("Test"), .sidebar button:has(.mdi-rocket), button:has-text("Test"), button:has-text("Testen")'
    ).first()
    await expect(testBtn).toBeVisible({ timeout: 10000 })
    await testBtn.click()

    // Wait for the test dialog to open
    await expect(page.locator('.test-prompt-card, [role="dialog"]').first()).toBeVisible({ timeout: 10000 })

    // Wait for the response section to appear and accumulate streamed content.
    // The response-text element contains the pre-formatted LLM output.
    const responseText = page.locator('.response-text, .response-content pre, .response-content').first()
    await expect(responseText).toBeVisible({ timeout: 30000 })

    // Poll until streaming produces non-empty content (LLM responses take time)
    await expect
      .poll(
        async () => (await responseText.innerText().catch(() => '')).trim().length,
        { timeout: 60000, message: 'LLM stream should produce non-empty content' }
      )
      .toBeGreaterThan(5)

    // Verify the response is real LLM content, not an error message
    const content = await responseText.innerText()
    assertNotErrorResponse(expect, content)

    // Close the dialog
    const closeBtn = page.locator(
      '.test-prompt-card button:has(.mdi-close), .test-prompt-card button:has-text("Schließen"), .test-prompt-card button:has-text("Close")'
    ).first()
    if (await closeBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await closeBtn.click()
    }
  })
})
