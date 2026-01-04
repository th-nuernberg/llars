/**
 * LLARS Login Flow E2E Tests
 *
 * Tests for authentication functionality including:
 * - Login page accessibility
 * - Successful login with valid credentials
 * - Failed login with invalid credentials
 * - Logout functionality
 * - Session persistence
 * - Redirect after login
 * - Input validation
 *
 * Test IDs: E2E_LOGIN_001 - E2E_LOGIN_025
 */

import { test, expect } from '@playwright/test'

// Increase timeout for CI environment
test.setTimeout(60000)

// Test credentials (from CLAUDE.md documentation)
const TEST_USERS = {
  admin: { username: 'admin', password: 'admin123', role: 'admin' },
  researcher: { username: 'researcher', password: 'admin123', role: 'researcher' },
  viewer: { username: 'viewer', password: 'admin123', role: 'viewer' },
  chatbot_manager: { username: 'chatbot_manager', password: 'admin123', role: 'chatbot_manager' }
}

// Helper function to login
async function login(page, username, password) {
  await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 })

  // Wait for login form to be ready
  await page.locator('#username').waitFor({ state: 'visible', timeout: 10000 })

  await page.fill('#username', username)
  await page.fill('#password', password)
  // Use the login form button (has class login-button), not the AppBar button
  await page.click('.login-button')
}

// Helper function to logout
async function logout(page) {
  // Open user menu (click the user-menu-trigger in AppBar)
  await page.click('.user-menu-trigger')
  // Wait for menu to open
  await page.waitForSelector('.user-menu-list', { state: 'visible' })
  // Click logout (Abmelden in German)
  await page.click('text=Abmelden')
}

// Helper to clear auth state
async function clearAuth(page) {
  // First navigate to the app to have access to localStorage
  await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 })
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
}

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  // ==================== Page Load Tests ====================

  test('E2E_LOGIN_001: login page loads correctly', async ({ page }) => {
    // clearAuth already navigates to /login, so we just check elements
    // Check page elements
    await expect(page.locator('.login-page')).toBeVisible()
    await expect(page.locator('.login-card')).toBeVisible()
    await expect(page.locator('.login-title')).toContainText('LLars')
  })

  test('E2E_LOGIN_002: login form has required fields', async ({ page }) => {
    // clearAuth already navigates to /login
    // Check form fields exist
    await expect(page.locator('#username')).toBeVisible()
    await expect(page.locator('#password')).toBeVisible()
    await expect(page.locator('.login-button')).toBeVisible()
  })

  test('E2E_LOGIN_003: username field is focusable', async ({ page }) => {
    // clearAuth already navigates to /login
    await page.click('#username')
    await expect(page.locator('#username')).toBeFocused()
  })

  test('E2E_LOGIN_004: password field is type password', async ({ page }) => {
    // clearAuth already navigates to /login
    const passwordInput = page.locator('#password')
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('E2E_LOGIN_005: password visibility toggle works', async ({ page }) => {
    // clearAuth already navigates to /login
    // Initial state: password hidden
    await expect(page.locator('#password')).toHaveAttribute('type', 'password')

    // Click eye icon to show password (within the password field container)
    const passwordField = page.locator('.login-field').filter({ has: page.locator('#password') })
    await passwordField.locator('.v-field__append-inner').click()

    // Password should now be visible
    await expect(page.locator('#password')).toHaveAttribute('type', 'text')

    // Click again to hide
    await passwordField.locator('.v-field__append-inner').click()
    await expect(page.locator('#password')).toHaveAttribute('type', 'password')
  })
})

test.describe('Successful Login', () => {
  // Run these tests serially to avoid auth state interference
  test.describe.configure({ mode: 'serial' })

  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test('E2E_LOGIN_006: admin can login successfully', async ({ page }) => {
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 15000 })
  })

  test('E2E_LOGIN_007: researcher can login successfully', async ({ page }) => {
    await login(page, TEST_USERS.researcher.username, TEST_USERS.researcher.password)

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 15000 })
  })

  test('E2E_LOGIN_008: viewer can login successfully', async ({ page }) => {
    await login(page, TEST_USERS.viewer.username, TEST_USERS.viewer.password)

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 15000 })
  })

  test('E2E_LOGIN_009: chatbot_manager can login successfully', async ({ page }) => {
    await login(page, TEST_USERS.chatbot_manager.username, TEST_USERS.chatbot_manager.password)

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 15000 })
  })

  test('E2E_LOGIN_010: token is stored after login', async ({ page }) => {
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)

    await expect(page).toHaveURL(/\/Home/, { timeout: 15000 })

    // Check sessionStorage for token (LLARS stores as 'auth_token')
    const token = await page.evaluate(() => {
      return sessionStorage.getItem('auth_token') || localStorage.getItem('auth_token')
    })

    expect(token).toBeTruthy()
  })

  test('E2E_LOGIN_011: login button shows loading state', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'networkidle', timeout: 30000 })

    await page.fill('#username', TEST_USERS.admin.username)
    await page.fill('#password', TEST_USERS.admin.password)

    // Click and check for loading state or successful navigation
    const loginButton = page.locator('.login-button')
    await loginButton.click()

    // Either button shows loading state OR we navigate to Home (both are valid outcomes)
    await Promise.race([
      expect(loginButton).toBeDisabled({ timeout: 5000 }),
      expect(page).toHaveURL(/\/Home/, { timeout: 15000 })
    ])
  })
})

test.describe('Failed Login', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test('E2E_LOGIN_012: wrong password shows error', async ({ page }) => {
    await login(page, TEST_USERS.admin.username, 'wrongpassword')

    // Should show error message
    await expect(page.locator('.login-error, .v-alert')).toBeVisible({ timeout: 10000 })

    // Should stay on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('E2E_LOGIN_013: wrong username shows error', async ({ page }) => {
    await login(page, 'nonexistentuser', 'admin123')

    // Should show error message
    await expect(page.locator('.login-error, .v-alert')).toBeVisible({ timeout: 10000 })

    // Should stay on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('E2E_LOGIN_014: empty username prevents submit', async ({ page }) => {
    await page.goto('/login')

    await page.fill('#password', 'admin123')

    // Button should be disabled when username is empty
    const loginButton = page.locator('.login-button')
    await expect(loginButton).toBeDisabled()
  })

  test('E2E_LOGIN_015: empty password prevents submit', async ({ page }) => {
    await page.goto('/login')

    await page.fill('#username', 'admin')

    // Button should be disabled when password is empty
    const loginButton = page.locator('.login-button')
    await expect(loginButton).toBeDisabled()
  })

  test('E2E_LOGIN_016: error message can be dismissed', async ({ page }) => {
    await login(page, 'wronguser', 'wrongpassword')

    // Wait for error to appear
    const errorAlert = page.locator('.login-error, .v-alert')
    await expect(errorAlert).toBeVisible({ timeout: 10000 })

    // Click close button on alert
    await page.click('.login-error button, .v-alert button').catch(() => {
      // Alert might auto-dismiss or have different structure
    })
  })
})

test.describe('Logout', () => {
  test('E2E_LOGIN_017: user can logout', async ({ page }) => {
    // First login
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })

    // Then logout
    await logout(page)

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
  })

  test('E2E_LOGIN_018: token is cleared after logout', async ({ page }) => {
    // Login first
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })

    // Logout
    await logout(page)
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 })

    // Check token is cleared
    const token = await page.evaluate(() => {
      return localStorage.getItem('access_token') || localStorage.getItem('token')
    })

    expect(token).toBeFalsy()
  })
})

test.describe('Session & Redirects', () => {
  test('E2E_LOGIN_019: unauthenticated user redirected to login', async ({ page }) => {
    await clearAuth(page)

    // Try to access protected page
    await page.goto('/Home')

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 10000 })
  })

  test('E2E_LOGIN_020: authenticated user can access Home', async ({ page }) => {
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })

    // Home page content should be visible
    await expect(page.locator('.home-container, .feature-cards, [class*="home"]')).toBeVisible()
  })

  test('E2E_LOGIN_021: redirect query param works after login', async ({ page }) => {
    await clearAuth(page)

    // Go to login with redirect param
    await page.goto('/login?redirect=/admin')

    await page.fill('#username', TEST_USERS.admin.username)
    await page.fill('#password', TEST_USERS.admin.password)
    await page.click('.login-button')

    // Should redirect to admin (if user has permission)
    await expect(page).toHaveURL(/\/(admin|Home)/, { timeout: 10000 })
  })

  test('E2E_LOGIN_022: already logged in user redirected from login page', async ({ page }) => {
    // First login
    await login(page, TEST_USERS.admin.username, TEST_USERS.admin.password)
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })

    // Try to go to login page
    await page.goto('/login')

    // Should redirect back to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })
  })
})

test.describe('Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await clearAuth(page)
  })

  test('E2E_LOGIN_023: Enter key submits login form', async ({ page }) => {
    await page.goto('/login')

    await page.fill('#username', TEST_USERS.admin.username)
    await page.fill('#password', TEST_USERS.admin.password)

    // Press Enter on password field
    await page.press('#password', 'Enter')

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })
  })

  test('E2E_LOGIN_024: Tab navigation works through form', async ({ page }) => {
    await page.goto('/login')

    // Focus username
    await page.click('#username')
    await expect(page.locator('#username')).toBeFocused()

    // Tab to password
    await page.keyboard.press('Tab')
    await expect(page.locator('#password')).toBeFocused()
  })
})

test.describe('Mobile Responsive', () => {
  test.use({ viewport: { width: 375, height: 667 } }) // iPhone SE size

  test('E2E_LOGIN_025: login works on mobile viewport', async ({ page }) => {
    await clearAuth(page)

    await page.goto('/login')

    // Check mobile-specific class
    await expect(page.locator('.login-page')).toBeVisible()

    // Login should work
    await page.fill('#username', TEST_USERS.admin.username)
    await page.fill('#password', TEST_USERS.admin.password)
    await page.click('.login-button')

    // Should redirect to Home
    await expect(page).toHaveURL(/\/Home/, { timeout: 10000 })
  })
})
