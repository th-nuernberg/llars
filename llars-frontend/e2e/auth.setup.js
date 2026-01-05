/**
 * LLARS E2E Authentication Setup
 *
 * Creates authenticated browser states for different user roles.
 * On production, creates temporary test users via API that are deleted after tests.
 *
 * Run: npx playwright test --project=setup
 */

import { test as setup, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

// Password can be overridden via E2E_TEST_PASSWORD env variable for production servers
const testPassword = process.env.E2E_TEST_PASSWORD || 'admin123'
// Production servers need temporary test users created via API
const isProduction = !!process.env.E2E_TEST_PASSWORD
const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:55080'

const TEST_USERS = {
  researcher: { username: 'e2e-researcher', password: testPassword, role: 'researcher' },
  viewer: { username: 'e2e-viewer', password: testPassword, role: 'viewer' },
  admin: { username: 'admin', password: testPassword }
}

const AUTH_DIR = path.join(process.cwd(), '.auth')

// Ensure auth directory exists
if (!fs.existsSync(AUTH_DIR)) {
  fs.mkdirSync(AUTH_DIR, { recursive: true })
}

async function dismissConsentBanner(page) {
  const consentBtn = page.locator('.analytics-consent button').first()
  if (await consentBtn.isVisible({ timeout: 500 }).catch(() => false)) {
    await consentBtn.click({ force: true }).catch(() => {})
    await page.waitForTimeout(200)
  }
}

async function performLogin(page, user) {
  await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForLoadState('load')

  await dismissConsentBanner(page)
  await page.waitForTimeout(300)

  // Handle privacy page redirect - click "Anmelden" in header to go to actual login
  const isOnPrivacyPage = await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)
  if (isOnPrivacyPage) {
    const headerLoginBtn = page.locator('button:has-text("Anmelden")').first()
    if (await headerLoginBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await headerLoginBtn.click()
      await page.waitForLoadState('load')
      await page.waitForTimeout(500)
    }
  }

  // Check for dev-login buttons first (development environment)
  const devBtn = page.locator('.dev-login-buttons button:not([disabled])').filter({ hasText: user.username })
  if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await devBtn.click()
    await page.waitForURL(/\/Home/, { timeout: 25000 })
    await dismissConsentBanner(page)
    return
  }

  // Production: LLARS has its own login form that posts to backend
  await page.waitForSelector('[data-testid="login-form"], .login-form', { timeout: 15000 })

  const usernameInput = page.locator('[data-testid="username-input"] input, #username input, input[name="username"]').first()
  await usernameInput.waitFor({ state: 'visible', timeout: 10000 })
  await usernameInput.fill(user.username)

  const passwordInput = page.locator('[data-testid="password-input"] input, #password input, input[name="password"]').first()
  await passwordInput.waitFor({ state: 'visible', timeout: 5000 })
  await passwordInput.fill(user.password)

  const loginBtn = page.locator('[data-testid="login-btn"], .login-button, button:has-text("Anmelden")').first()
  await loginBtn.waitFor({ state: 'visible', timeout: 5000 })
  await loginBtn.click()

  // Wait for redirect to Home page after successful login
  await page.waitForURL(/\/Home/, { timeout: 30000 })
  await dismissConsentBanner(page)
}

/**
 * Creates a temporary test user via the admin API
 */
async function createTestUser(accessToken, username, password, roleName) {
  const response = await fetch(`${baseURL}/api/admin/users`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({
      username: username,
      email: `${username}@e2e-test.local`,
      password: password,
      display_name: `E2E Test ${roleName}`,
      role_names: [roleName],
      is_active: true,
      create_in_authentik: true
    })
  })

  if (!response.ok) {
    const text = await response.text()
    // User might already exist from a previous failed run - that's ok
    if (text.includes('already exists')) {
      console.log(`Test user ${username} already exists, will reuse`)
      return true
    }
    throw new Error(`Failed to create test user ${username}: ${response.status} ${text}`)
  }
  console.log(`Created temporary test user: ${username}`)
  return true
}

/**
 * Deletes a temporary test user via the admin API
 */
async function deleteTestUser(accessToken, username) {
  const response = await fetch(`${baseURL}/api/admin/users/${username}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  })

  if (!response.ok && response.status !== 404) {
    console.warn(`Failed to delete test user ${username}: ${response.status}`)
    return false
  }
  console.log(`Deleted temporary test user: ${username}`)
  return true
}

/**
 * Gets admin access token for API calls
 */
async function getAdminToken() {
  const response = await fetch(`${baseURL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: TEST_USERS.admin.username,
      password: TEST_USERS.admin.password
    })
  })

  if (!response.ok) {
    throw new Error(`Admin login failed: ${response.status}`)
  }

  const data = await response.json()
  return data.access_token
}

// Store admin token for cleanup
let adminToken = null

// Admin authentication - always runs first
setup('authenticate as admin', async ({ page }) => {
  await performLogin(page, TEST_USERS.admin)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'admin.json') })

  // On production, create temporary test users
  if (isProduction) {
    adminToken = await getAdminToken()
    await createTestUser(adminToken, TEST_USERS.researcher.username, testPassword, 'researcher')
    await createTestUser(adminToken, TEST_USERS.viewer.username, testPassword, 'viewer')
  }
})

setup('authenticate as researcher', async ({ page }) => {
  const user = isProduction ? TEST_USERS.researcher : { username: 'researcher', password: testPassword }
  await performLogin(page, user)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'researcher.json') })
})

setup('authenticate as viewer', async ({ page }) => {
  const user = isProduction ? TEST_USERS.viewer : { username: 'viewer', password: testPassword }
  await performLogin(page, user)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'viewer.json') })
})

// Cleanup: Delete temporary test users after all setup tests complete
setup.afterAll(async () => {
  if (isProduction && adminToken) {
    console.log('Cleaning up temporary test users...')
    await deleteTestUser(adminToken, TEST_USERS.researcher.username)
    await deleteTestUser(adminToken, TEST_USERS.viewer.username)
  }
})
