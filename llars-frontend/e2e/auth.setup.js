/**
 * LLARS E2E Authentication Setup
 *
 * Creates authenticated browser states for different user roles.
 * These states are reused across tests to avoid repeated logins.
 *
 * Run: npx playwright test --project=setup
 */

import { test as setup, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

// Password can be overridden via E2E_TEST_PASSWORD env variable for production servers
const testPassword = process.env.E2E_TEST_PASSWORD || 'admin123'
// Production servers typically only have admin user, not test users
const isProduction = !!process.env.E2E_TEST_PASSWORD

const TEST_USERS = {
  researcher: { username: 'researcher', password: testPassword },
  viewer: { username: 'viewer', password: testPassword },
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
    // Privacy page has "Anmelden" button in header to navigate to login
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
  // Wait for the login form to be visible (data-testid is most reliable for Vuetify)
  await page.waitForSelector('[data-testid="login-form"], .login-form', { timeout: 15000 })

  // Fill username using data-testid (works with Vuetify v-text-field)
  const usernameInput = page.locator('[data-testid="username-input"] input, #username input, input[name="username"]').first()
  await usernameInput.waitFor({ state: 'visible', timeout: 10000 })
  await usernameInput.fill(user.username)

  // Fill password
  const passwordInput = page.locator('[data-testid="password-input"] input, #password input, input[name="password"]').first()
  await passwordInput.waitFor({ state: 'visible', timeout: 5000 })
  await passwordInput.fill(user.password)

  // Click login button
  const loginBtn = page.locator('[data-testid="login-btn"], .login-button, button:has-text("Anmelden")').first()
  await loginBtn.waitFor({ state: 'visible', timeout: 5000 })
  await loginBtn.click()

  // Wait for redirect to Home page after successful login
  await page.waitForURL(/\/Home/, { timeout: 30000 })
  await dismissConsentBanner(page)
}

// Admin authentication - always runs first
setup('authenticate as admin', async ({ page }) => {
  await performLogin(page, TEST_USERS.admin)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'admin.json') })

  // On production, create fallback auth files for researcher/viewer using admin's auth
  // This allows tests to run (with admin permissions) even if these users don't exist
  if (isProduction) {
    const adminAuth = fs.readFileSync(path.join(AUTH_DIR, 'admin.json'), 'utf-8')
    fs.writeFileSync(path.join(AUTH_DIR, 'researcher.json'), adminAuth)
    fs.writeFileSync(path.join(AUTH_DIR, 'viewer.json'), adminAuth)
  }
})

setup('authenticate as researcher', async ({ page }) => {
  // Skip on production - admin's auth is used as fallback
  setup.skip(isProduction, 'researcher user not available on production, using admin fallback')
  await performLogin(page, TEST_USERS.researcher)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'researcher.json') })
})

setup('authenticate as viewer', async ({ page }) => {
  // Skip on production - admin's auth is used as fallback
  setup.skip(isProduction, 'viewer user not available on production, using admin fallback')
  await performLogin(page, TEST_USERS.viewer)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'viewer.json') })
})
