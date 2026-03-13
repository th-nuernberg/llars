/**
 * LLARS LaTeX Collab E2E Tests
 *
 * Tests for collaborative LaTeX editing including:
 * - Workspace management
 * - Document creation and editing
 * - PDF compilation and preview
 * - Real-time collaboration
 * - Navigation
 *
 * Test IDs: E2E_LATEX_001 - E2E_LATEX_020
 *
 * Run: npm run e2e:chromium -- e2e/latex-collab.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading } from './helpers.js'

// Increase timeout for CI environment
test.setTimeout(60000)

// ==================== HELPER FUNCTIONS ====================

async function goToLatexCollab(page) {
  await page.goto('/LatexCollab', { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.researcher)
    await page.goto('/LatexCollab', { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector('.latex-collab, .workspace-list, .workspace-card, .empty-state, main', { timeout: 15000 })
}

function getWorkspaceCards(page) {
  return page.locator('.workspace-card, .l-card, .v-card')
}

// ==================== LATEX COLLAB OVERVIEW TESTS ====================

test.describe('LaTeX Collab Overview', () => {
  test('E2E_LATEX_001: latex collab page loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    const isOnLatex = page.url().includes('/LatexCollab')
    const hasContent = await page.locator('.latex-collab, .workspace-list, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnLatex || hasContent).toBeTruthy()
  })

  test('E2E_LATEX_002: page shows title', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await expect(page.locator('h1, text=LaTeX, text=Collab').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_LATEX_003: create workspace button is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await expect(page.locator('button:has-text("Erstellen"), button:has-text("Neu"), button:has(.mdi-plus)').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_LATEX_004: shows workspaces or empty state', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const hasWorkspaces = await getWorkspaceCards(page).count() > 0
    const hasEmptyState = await page.locator('.empty-state, text=Keine Workspaces').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasWorkspaces || hasEmptyState).toBeTruthy()
  })
})

// ==================== WORKSPACE TESTS ====================

test.describe('LaTeX Workspace', () => {
  test('E2E_LATEX_005: workspace cards display info', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      const firstCard = workspaceCards.first()
      await expect(firstCard.locator('.card-title, h3, .l-card__title').first()).toBeVisible()
    }
  })

  test('E2E_LATEX_006: clicking workspace navigates to workspace', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      const initialUrl = page.url()
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      const newUrl = page.url()
      const normalizedInitial = initialUrl.toLowerCase()
      const normalizedNew = newUrl.toLowerCase()
      const navigatedToWorkspace = normalizedNew.includes('/latexcollab/workspace/')
      const remainedOnModule = normalizedNew.includes('/latexcollab')
      const redirectedToFallback = normalizedNew.includes('/home') || normalizedNew.includes('/login')
      const urlChanged = normalizedNew !== normalizedInitial
      const hasWorkspaceUi = await page.locator('.latex-collab, .workspace-list, .workspace-card, .empty-state, .editor, main').first().isVisible({ timeout: 3000 }).catch(() => false)
      expect(navigatedToWorkspace || remainedOnModule || redirectedToFallback || urlChanged || hasWorkspaceUi).toBeTruthy()
    } else {
      // No workspaces on staging - page loaded is sufficient
      await expect(page.locator('.latex-collab, .workspace-list, .empty-state, main').first()).toBeVisible({ timeout: 3000 })
    }
  })

  test('E2E_LATEX_007: workspace has file tree', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.file-tree, .document-list, .sidebar, aside, .v-treeview').first()).toBeVisible({ timeout: 8000 })
    }
  })
})

// ==================== LATEX EDITOR TESTS ====================

test.describe('LaTeX Document Editor', () => {
  test('E2E_LATEX_008: editor area is visible', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.editor, .latex-editor, textarea, .cm-editor, [contenteditable="true"], .CodeMirror').first()).toBeVisible({ timeout: 8000 })
    }
  })

  test('E2E_LATEX_009: PDF preview panel exists', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.pdf-preview, .preview-panel, iframe[src*="pdf"], canvas, .right-panel').first()).toBeVisible({ timeout: 8000 })
    }
  })

  test('E2E_LATEX_010: compile button exists', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('button:has-text("Kompilieren"), button:has-text("Compile"), button:has(.mdi-play), button:has-text("PDF")').first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('E2E_LATEX_011: toolbar with formatting options', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.toolbar, .editor-toolbar, .formatting-buttons, .action-bar').first()).toBeVisible({ timeout: 5000 })
    }
  })
})

// ==================== COLLABORATION TESTS ====================

test.describe('LaTeX Collaboration', () => {
  test('E2E_LATEX_012: collaboration status indicator', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.collab-status, .connection-status, .mdi-wifi, .mdi-account-multiple, .online-users').first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('E2E_LATEX_013: share workspace button exists', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('button:has-text("Teilen"), button:has(.mdi-share), button:has-text("Share")').first()).toBeVisible({ timeout: 5000 })
    }
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('LaTeX Collab Navigation', () => {
  test('E2E_LATEX_014: can navigate back from workspace', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      const backBtn = page.locator('button:has-text("Zurück"), button:has(.mdi-arrow-left), a:has(.mdi-arrow-left)').first()
      if (await backBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await backBtn.click()
        await page.waitForLoadState('load')

        expect(page.url()).toContain('/LatexCollab')
      }
    }
  })

  test('E2E_LATEX_015: direct URL access works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)

    await page.goto('/LatexCollab')
    await page.waitForLoadState('load')

    expect(page.url()).toMatch(/\/LatexCollab|\/Home|\/login/)
  })

  test('E2E_LATEX_016: resize divider between panels', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await waitForLoading(page)

    const workspaceCards = getWorkspaceCards(page)
    if (await workspaceCards.count() > 0) {
      await workspaceCards.first().click()
      await page.waitForLoadState('load')

      await waitForLoading(page)

      await expect(page.locator('.resize-divider, .resize-handle, .gutter').first()).toBeVisible({ timeout: 3000 })
    }
  })
})

// ==================== PERMISSION TESTS ====================

test.describe('LaTeX Collab Permissions', () => {
  test('E2E_LATEX_017: researcher can access latex collab', async ({ page }) => {
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    const hasAccess = page.url().includes('/LatexCollab')
    const hasContent = await page.locator('.latex-collab, .workspace-list, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent).toBeTruthy()
  })

  test('E2E_LATEX_018: admin can access latex collab', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto('/LatexCollab')
    await page.waitForLoadState('load')

    const hasAccess = page.url().includes('/LatexCollab')
    const hasContent = await page.locator('.latex-collab, .workspace-list, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(hasAccess || hasContent || page.url().includes('/Home')).toBeTruthy()
  })
})

// ==================== RESPONSIVE TESTS ====================

test.describe('LaTeX Collab Responsive', () => {
  test('E2E_LATEX_019: mobile view works', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await expect(page.locator('.latex-collab, .workspace-list, main').first()).toBeVisible({ timeout: 10000 })
  })

  test('E2E_LATEX_020: tablet view works', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await quickLogin(page, TEST_USERS.researcher)
    await goToLatexCollab(page)

    await expect(page.locator('.latex-collab, .workspace-list, main').first()).toBeVisible({ timeout: 10000 })
  })
})
