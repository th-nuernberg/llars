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

  // Handle privacy page redirect
  const isOnPrivacyPage = await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)
  if (isOnPrivacyPage) {
    const acceptBtn = page.locator('button:has-text("Zustimmen"), button:has-text("Ablehnen")').first()
    if (await acceptBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await acceptBtn.click()
      await page.waitForTimeout(500)
    }
  }

  // Wait for login form
  await page.waitForSelector('.dev-login-buttons, #username, .login-form', { timeout: 15000 })

  // Use dev quick-login
  const devBtn = page.locator('.dev-login-buttons button:not([disabled])').filter({ hasText: user.username })
  if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await devBtn.click()
    await page.waitForURL(/\/Home/, { timeout: 25000 })
  } else {
    // Fallback to form login
    await page.locator('#username, input[placeholder*="username" i]').first().fill(user.username)
    await page.locator('#password, input[type="password"]').first().fill(user.password)
    await page.locator('.login-button, button:has-text("Anmelden")').first().click()
    await page.waitForURL(/\/Home/, { timeout: 25000 })
  }

  await dismissConsentBanner(page)
}

setup('authenticate as researcher', async ({ page }) => {
  await performLogin(page, TEST_USERS.researcher)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'researcher.json') })
})

setup('authenticate as viewer', async ({ page }) => {
  await performLogin(page, TEST_USERS.viewer)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'viewer.json') })
})

setup('authenticate as admin', async ({ page }) => {
  await performLogin(page, TEST_USERS.admin)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'admin.json') })
})
