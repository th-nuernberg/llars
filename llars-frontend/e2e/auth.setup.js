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

  // Check for dev-login buttons first (development environment)
  const devBtn = page.locator('.dev-login-buttons button:not([disabled])').filter({ hasText: user.username })
  if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await devBtn.click()
    await page.waitForURL(/\/Home/, { timeout: 25000 })
    await dismissConsentBanner(page)
    return
  }

  // Production: Authentik OAuth flow
  // Click "Mit Authentik anmelden" or similar OAuth button to initiate Authentik login
  const authentikBtn = page.locator('button:has-text("Authentik"), button:has-text("OAuth"), a:has-text("Authentik"), .oauth-button, .authentik-login').first()
  if (await authentikBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    await authentikBtn.click()
    await page.waitForLoadState('load')
  }

  // Wait for Authentik login form (different selectors for Authentik UI)
  // Authentik uses input[name="uidField"] for username and input[name="password"] for password
  const usernameSelectors = [
    'input[name="uidField"]',
    'input[name="uid_field"]',
    'input[autocomplete="username"]',
    '#id_uid_field',
    '#username',
    'input[placeholder*="username" i]',
    'input[placeholder*="Username" i]',
    'input[placeholder*="E-Mail" i]'
  ]

  // Wait for any username input to appear
  await page.waitForSelector(usernameSelectors.join(', '), { timeout: 15000 })

  // Fill username - try multiple selectors
  for (const selector of usernameSelectors) {
    const input = page.locator(selector).first()
    if (await input.isVisible({ timeout: 500 }).catch(() => false)) {
      await input.fill(user.username)
      break
    }
  }

  // Fill password
  const passwordSelectors = [
    'input[name="password"]',
    'input[type="password"]',
    '#id_password',
    '#password'
  ]
  for (const selector of passwordSelectors) {
    const input = page.locator(selector).first()
    if (await input.isVisible({ timeout: 500 }).catch(() => false)) {
      await input.fill(user.password)
      break
    }
  }

  // Click login button - try multiple selectors for Authentik
  const loginBtnSelectors = [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Log in")',
    'button:has-text("Login")',
    'button:has-text("Anmelden")',
    'button:has-text("Sign in")',
    '.pf-c-button--primary',
    '.ak-flow-submit'
  ]

  for (const selector of loginBtnSelectors) {
    const btn = page.locator(selector).first()
    if (await btn.isVisible({ timeout: 500 }).catch(() => false)) {
      await btn.click()
      break
    }
  }

  // Wait for redirect back to app (Home page)
  await page.waitForURL(/\/Home/, { timeout: 30000 })
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
