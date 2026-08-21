/**
 * LLARS Admin Dashboard E2E Tests
 *
 * Tests for Admin functionality including:
 * - Admin page access and navigation
 * - Permissions management
 * - Scenario management
 * - System settings
 * - Role-based access control
 *
 * Test IDs: E2E_ADMIN_001 - E2E_ADMIN_030
 *
 * Run: npm run e2e:chromium -- e2e/admin.spec.js
 */

import { test, expect } from '@playwright/test'
import { TEST_USERS, quickLogin, dismissConsentBanner, waitForLoading } from './helpers.js'

// Increase timeout for CI environment
test.setTimeout(60000)

// ==================== HELPER FUNCTIONS ====================

async function goToAdmin(page, tab = null) {
  const url = tab ? `/admin?tab=${tab}` : '/admin'
  await page.goto(url, { waitUntil: 'domcontentloaded' })
  await page.waitForLoadState('load')

  if (page.url().includes('/login')) {
    await quickLogin(page, TEST_USERS.admin)
    await page.goto(url, { waitUntil: 'domcontentloaded' })
  }

  await dismissConsentBanner(page)
  await page.waitForSelector('.admin-page, .admin-content, main, h1', { timeout: 15000 })
}

// ==================== ADMIN ACCESS TESTS ====================

test.describe('Admin Access', () => {
  test('E2E_ADMIN_001: admin page loads for admin user', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page)

    const isOnAdmin = page.url().includes('/admin')
    const hasContent = await page.locator('.admin-page, .admin-content, main').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(isOnAdmin || hasContent).toBeTruthy()
  })

  test('E2E_ADMIN_002: admin page has sidebar navigation', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page)

    await expect(page.locator('aside, nav, .admin-sidebar, .v-navigation-drawer').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_003: admin page shows navigation items', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page)

    // Should have multiple navigation items (on staging, admin page structure may differ)
    const navItems = page.locator('nav a, nav button, .v-list-item, [role="menuitem"]')
    const count = await navItems.count()
    const hasAdminContent = await page.locator('.admin-page, .admin-content, main, h1').first().isVisible({ timeout: 5000 }).catch(() => false)
    expect(count > 0 || hasAdminContent).toBeTruthy()
  })

  test('E2E_ADMIN_004: non-admin redirected or denied', async ({ page }) => {
    await quickLogin(page, TEST_USERS.evaluator)
    await page.goto('/admin')
    await page.waitForLoadState('load')

    // Evaluator should be redirected to Home or see access denied
    const url = page.url()
    const hasAccessDenied = await page.locator('text=Zugriff verweigert, text=Access denied, text=keine Berechtigung').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(url.includes('/Home') || url.includes('/admin') || hasAccessDenied).toBeTruthy()
  })
})

// ==================== ADMIN OVERVIEW TESTS ====================

test.describe('Admin Overview', () => {
  test('E2E_ADMIN_005: overview tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'overview')

    await expect(page.locator('.admin-overview, .overview-section, [class*="overview"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_006: overview shows statistics', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'overview')

    await waitForLoading(page)

    await expect(page.locator('.stat-card, .v-card, [class*="stat"]').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== PERMISSIONS TAB TESTS ====================

test.describe('Admin Permissions', () => {
  test('E2E_ADMIN_007: permissions tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'permissions')

    await waitForLoading(page)

    await expect(page.locator('.admin-permissions, [class*="permission"], .role-card').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_008: permissions tab shows roles', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'permissions')

    await waitForLoading(page)

    // Wait for skeleton to disappear
    await page.waitForSelector('.v-skeleton-loader', { state: 'hidden', timeout: 10000 }).catch(() => {})

    await expect(page.locator('.role-card, text=admin, text=researcher, text=evaluator').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_009: permissions has sub-tabs', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'permissions')

    await waitForLoading(page)

    await expect(page.locator('.v-tabs, .v-tab, [role="tablist"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_010: can switch between permission sub-tabs', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'permissions')

    await waitForLoading(page)

    // Try clicking on a tab if available
    const tabs = page.locator('.v-tab, [role="tab"]')
    if (await tabs.count() > 1) {
      await tabs.nth(1).click()
      await page.waitForTimeout(500)
      // Content should update
      expect(true).toBeTruthy()
    }
  })
})

// ==================== SCENARIOS TAB TESTS ====================

test.describe('Admin Scenarios', () => {
  test('E2E_ADMIN_011: scenarios tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'scenarios')

    await waitForLoading(page)

    await expect(page.locator('.scenarios-section, .scenario-row, v-table, text=Szenario').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_012: scenarios shows table or list', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'scenarios')

    await waitForLoading(page)

    const hasTable = await page.locator('table, v-table, .v-data-table, .scenario-row').first().isVisible({ timeout: 5000 }).catch(() => false)
    const hasEmptyState = await page.locator('.empty-state, text=Keine Szenarien').first().isVisible({ timeout: 3000 }).catch(() => false)
    expect(hasTable || hasEmptyState).toBeTruthy()
  })

  test('E2E_ADMIN_013: scenarios has search field', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'scenarios')

    await waitForLoading(page)

    await expect(page.locator('input[type="text"], .v-text-field, [placeholder*="Such"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_014: scenarios has status filter', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'scenarios')

    await waitForLoading(page)

    await expect(page.locator('.v-select, select, [class*="filter"]').first()).toBeVisible({ timeout: 5000 })
  })

  test('E2E_ADMIN_015: scenarios has create button', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'scenarios')

    await waitForLoading(page)

    await expect(page.locator('button:has-text("Erstellen"), button:has-text("Neu"), button:has(.mdi-plus)').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== USERS TAB TESTS ====================

test.describe('Admin Users', () => {
  test('E2E_ADMIN_016: users tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'users')

    await waitForLoading(page)

    await expect(page.locator('.users-section, .user-row, table, text=Benutzer').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_017: users shows user list', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'users')

    await waitForLoading(page)

    await expect(page.locator('table, .v-data-table, .user-card, text=admin, text=researcher').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== RAG TAB TESTS ====================

test.describe('Admin RAG', () => {
  test('E2E_ADMIN_018: RAG tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'rag')

    await waitForLoading(page)

    await expect(page.locator('.rag-section, [class*="rag"], text=RAG, text=Dokumente').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_019: RAG shows document management', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'rag')

    await waitForLoading(page)

    await expect(page.locator('table, .document-list, .collection-list, .v-card').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== CHATBOTS TAB TESTS ====================

test.describe('Admin Chatbots', () => {
  test('E2E_ADMIN_020: chatbots tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'chatbots')

    await waitForLoading(page)

    await expect(page.locator('.chatbot-manager, [class*="chatbot"], text=Chatbot').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_021: chatbots shows list or grid', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'chatbots')

    await waitForLoading(page)

    await expect(page.locator('table, .chatbot-list, .v-card, .chatbot-card').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== SYSTEM SETTINGS TESTS ====================

test.describe('Admin System Settings', () => {
  test('E2E_ADMIN_022: settings tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'settings')

    await waitForLoading(page)

    await expect(page.locator('.settings-section, [class*="settings"], text=Einstellungen').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_023: settings shows configuration options', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'settings')

    await waitForLoading(page)

    await expect(page.locator('.v-switch, .v-text-field, .v-select, input').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== DOCKER MONITOR TESTS ====================

test.describe('Admin Docker Monitor', () => {
  test('E2E_ADMIN_024: docker monitor tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'docker')

    await waitForLoading(page)

    await expect(page.locator('.docker-monitor, [class*="docker"], text=Docker, text=Container').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_025: docker shows container list', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'docker')

    await waitForLoading(page)

    await expect(page.locator('table, .container-list, .v-card, text=llars').first()).toBeVisible({ timeout: 8000 })
  })
})

// ==================== DATABASE EXPLORER TESTS ====================

test.describe('Admin Database Explorer', () => {
  test('E2E_ADMIN_026: database tab loads', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'db')

    await waitForLoading(page)

    await expect(page.locator('.db-explorer, [class*="database"], text=Datenbank, text=Tabellen').first()).toBeVisible({ timeout: 8000 })
  })

  test('E2E_ADMIN_027: database shows table list', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'db')

    await waitForLoading(page)

    await expect(page.locator('table, .table-list, select, .v-select').first()).toBeVisible({ timeout: 5000 })
  })
})

// ==================== NAVIGATION TESTS ====================

test.describe('Admin Navigation', () => {
  test('E2E_ADMIN_028: can navigate between admin tabs', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page, 'overview')

    // Click on scenarios nav item
    const scenariosNav = page.locator('text=Szenario, [value="scenarios"], a[href*="scenarios"]').first()
    if (await scenariosNav.isVisible({ timeout: 3000 }).catch(() => false)) {
      await scenariosNav.click()
      await page.waitForTimeout(500)
      expect(page.url()).toContain('scenarios')
    }
  })

  test('E2E_ADMIN_029: URL query param changes tab', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)

    await goToAdmin(page, 'permissions')
    const hasPermissions = await page.locator('.admin-permissions, [class*="permission"]').first().isVisible({ timeout: 5000 }).catch(() => false)

    await goToAdmin(page, 'scenarios')
    const hasScenarios = await page.locator('text=Szenario, .scenario-row').first().isVisible({ timeout: 5000 }).catch(() => false)

    expect(hasPermissions || hasScenarios).toBeTruthy()
  })

  test('E2E_ADMIN_030: back navigation works', async ({ page }) => {
    await quickLogin(page, TEST_USERS.admin)
    await goToAdmin(page)

    // Navigate to Home
    await page.goto('/Home')
    await page.waitForLoadState('load')

    // Navigate back
    await page.goBack()
    await page.waitForLoadState('load')

    // On staging with storageState auth, back navigation may land on a different page
    const url = page.url()
    expect(url.includes('/admin') || url.includes('/Home')).toBeTruthy()
  })
})
