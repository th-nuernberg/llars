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
const loginTimeout = process.env.CI ? 60000 : 45000
const setupTimeout = process.env.CI ? 120000 : 90000

setup.setTimeout(setupTimeout)

const TEST_USERS = {
  researcher: { username: 'e2e-researcher', password: testPassword, role: 'researcher' },
  evaluator: { username: 'e2e-evaluator', password: testPassword, role: 'evaluator' },
  chatbot_manager: { username: 'e2e-chatbot-manager', password: testPassword, role: 'chatbot_manager' },
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

async function apiLogin(user) {
  const response = await fetch(`${baseURL}/auth/authentik/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: user.username, password: user.password })
  })

  const responseText = await response.text()
  if (!response.ok) {
    throw new Error(`API login failed for ${user.username}: ${response.status} ${responseText}`)
  }

  let data = {}
  try {
    data = JSON.parse(responseText)
  } catch (error) {
    throw new Error(`API login invalid JSON for ${user.username}: ${error.message}`)
  }

  if (!data.access_token) {
    throw new Error(`API login missing access_token for ${user.username}`)
  }

  return data
}

async function applyAuthStorage(page, user, tokenData) {
  await page.addInitScript((payload) => {
    const rolesValue = JSON.stringify(payload.roles || [])
    const usernameValue = payload.username || ''
    const store = (storage, key, value) => {
      try {
        storage.setItem(key, value)
      } catch (e) {
        // ignore storage failures
      }
    }

    store(window.sessionStorage, 'auth_token', payload.accessToken || '')
    store(window.sessionStorage, 'auth_refreshToken', payload.refreshToken || '')
    store(window.sessionStorage, 'auth_idToken', payload.idToken || '')
    store(window.sessionStorage, 'auth_llars_roles', rolesValue)
    store(window.localStorage, 'auth_token', payload.accessToken || '')
    store(window.localStorage, 'auth_refreshToken', payload.refreshToken || '')
    store(window.localStorage, 'auth_idToken', payload.idToken || '')
    store(window.localStorage, 'auth_llars_roles', rolesValue)
    store(window.localStorage, 'username', usernameValue)
  }, {
    accessToken: tokenData.access_token,
    refreshToken: tokenData.refresh_token,
    idToken: tokenData.id_token,
    roles: tokenData.llars_roles || [],
    username: user.username
  })
}

async function performLogin(page, user) {
  console.log(`[E2E] Starting login for user: ${user.username}`)
  console.log(`[E2E] Base URL: ${baseURL}, isProduction: ${isProduction}`)

  if (isProduction) {
    console.log('[E2E] Production mode: using API login for reliability')
    const tokenData = await apiLogin(user)
    await applyAuthStorage(page, user, tokenData)
    await page.goto('/Home', { waitUntil: 'domcontentloaded', timeout: loginTimeout })
    await page.waitForURL(/\/(Home|home|dashboard)/i, { timeout: loginTimeout })
    await dismissConsentBanner(page)
    console.log(`[E2E] Login complete for ${user.username} (API)`)
    return
  }

  const loginResponse = await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: loginTimeout })
  if (loginResponse && loginResponse.status() >= 400) {
    throw new Error(`Login page returned ${loginResponse.status()} ${loginResponse.statusText()}`)
  }
  console.log(`[E2E] Current URL after goto /login: ${page.url()}`)

  await dismissConsentBanner(page)
  await page.waitForTimeout(300)

  // Handle privacy page redirect - click "Anmelden" in header to go to actual login
  const isOnPrivacyPage = await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)
  if (isOnPrivacyPage) {
    console.log('[E2E] On privacy page, clicking Anmelden button')
    const headerLoginBtn = page.locator('button:has-text("Anmelden")').first()
    if (await headerLoginBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await headerLoginBtn.click()
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(500)
      console.log(`[E2E] After clicking Anmelden, URL: ${page.url()}`)
    }
  }

  // Check for dev-login buttons first (development environment)
  const devBtn = page.locator('.dev-login-buttons button:not([disabled])').filter({ hasText: user.username })
  if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    console.log('[E2E] Found dev-login button, clicking it')
    await devBtn.click()
    await page.waitForURL(/\/Home/, { timeout: loginTimeout })
    await dismissConsentBanner(page)
    return
  }

  console.log('[E2E] No dev-login buttons found, using production login form')

  // Production: LLARS has its own login form that posts to backend
  // Wait for either login form OR already logged in (Home page)
  const loginFormVisible = await page.waitForSelector('[data-testid="login-form"], .login-form, .login-container', { timeout: loginTimeout }).catch(() => null)

  if (!loginFormVisible) {
    // Maybe we're already on home?
    if (page.url().includes('/Home')) {
      console.log('[E2E] Already on Home page, login not needed')
      return
    }
    console.log(`[E2E] Login form not found, current URL: ${page.url()}`)
    console.log(`[E2E] Page content: ${await page.content().then(c => c.substring(0, 500))}`)
    throw new Error('Login form not found')
  }

  // Try multiple selectors for username input
  const usernameSelectors = [
    '[data-testid="username-input"] input',
    '#username input',
    'input[name="username"]',
    'input[type="text"]'
  ]

  let usernameInput = null
  for (const selector of usernameSelectors) {
    const input = page.locator(selector).first()
    if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
      usernameInput = input
      console.log(`[E2E] Found username input with selector: ${selector}`)
      break
    }
  }

  if (!usernameInput) {
    console.log(`[E2E] Username input not found, page URL: ${page.url()}`)
    throw new Error('Username input not found')
  }

  await usernameInput.fill(user.username)
  console.log(`[E2E] Filled username: ${user.username}`)

  // Try multiple selectors for password input
  const passwordSelectors = [
    '[data-testid="password-input"] input',
    '#password input',
    'input[name="password"]',
    'input[type="password"]'
  ]

  let passwordInput = null
  for (const selector of passwordSelectors) {
    const input = page.locator(selector).first()
    if (await input.isVisible({ timeout: 1000 }).catch(() => false)) {
      passwordInput = input
      console.log(`[E2E] Found password input with selector: ${selector}`)
      break
    }
  }

  if (!passwordInput) {
    throw new Error('Password input not found')
  }

  await passwordInput.fill(user.password)
  console.log('[E2E] Filled password')

  // Find and click login button
  const loginBtn = page.locator('[data-testid="login-btn"], .login-button, button:has-text("Anmelden"), button[type="submit"]').first()
  await loginBtn.waitFor({ state: 'visible', timeout: 5000 })
  console.log('[E2E] Clicking login button')
  const loginResponsePromise = page.waitForResponse(
    (response) => response.url().includes('/auth/authentik/login') && response.request().method() === 'POST',
    { timeout: 30000 }
  ).catch(() => null)
  await loginBtn.click()
  const loginResponseResult = await loginResponsePromise
  if (loginResponseResult && !loginResponseResult.ok()) {
    throw new Error(`Login failed: ${loginResponseResult.status()} ${loginResponseResult.statusText()}`)
  }

  // Wait for navigation - could be to /Home or could show error
  console.log('[E2E] Waiting for navigation after login...')

  // First, wait for any navigation or for the page to settle
  await page.waitForTimeout(1500)
  console.log(`[E2E] URL after clicking login: ${page.url()}`)

  // Check for error messages
  const errorMsg = page.locator('.login-error, .error-message, .v-alert--error, [role="alert"]').first()
  if (await errorMsg.isVisible({ timeout: 1000 }).catch(() => false)) {
    const errorText = await errorMsg.textContent()
    console.log(`[E2E] Login error message: ${errorText}`)
    throw new Error(`Login failed with error: ${errorText}`)
  }

  // Wait for redirect to Home page after successful login
  // Use a more flexible approach - wait for URL change first
  try {
    await page.waitForURL(/\/(Home|home|dashboard)/i, { timeout: loginTimeout })
    console.log(`[E2E] Successfully navigated to: ${page.url()}`)
  } catch (e) {
    const hasToken = await page.evaluate(() => !!window.sessionStorage.getItem('auth_token')).catch(() => false)
    if (hasToken) {
      console.log('[E2E] Token present in storage, forcing navigation to Home')
      await page.goto('/Home', { waitUntil: 'domcontentloaded', timeout: loginTimeout })
      await page.waitForURL(/\/(Home|home|dashboard)/i, { timeout: loginTimeout })
      await dismissConsentBanner(page)
      return
    }
    console.log(`[E2E] Failed to navigate to Home. Current URL: ${page.url()}`)
    if (page.isClosed()) {
      console.log('[E2E] Page closed before title could be read')
    } else {
      try {
        console.log(`[E2E] Page title: ${await page.title()}`)
      } catch (error) {
        console.log(`[E2E] Page title unavailable: ${error.message}`)
      }
    }

    // Check if we're on an Authentik page
    if (page.url().includes('authentik') || page.url().includes('auth')) {
      console.log('[E2E] Appears to be on Authentik auth page')
    }

    throw e
  }

  await dismissConsentBanner(page)
  console.log(`[E2E] Login complete for ${user.username}`)
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
    if (response.status === 409 || text.includes('already exists')) {
      console.log(`Test user ${username} already exists, will reuse`)
      return { existed: true }
    }
    throw new Error(`Failed to create test user ${username}: ${response.status} ${text}`)
  }

  const data = await response.json().catch(() => ({}))
  if (data.warning && data.authentik_created === false) {
    throw new Error(`Authentik user not created for ${username}: ${data.warning}`)
  }

  console.log(`Created temporary test user: ${username} (${roleName})`)
  return data
}

async function waitForUserLogin(username, password, attempts = 6, delayMs = 3000) {
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const response = await fetch(`${baseURL}/auth/authentik/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      if (response.ok) {
        console.log(`User ${username} login verified`)
        return true
      }
      console.log(`User ${username} login not ready (attempt ${attempt}/${attempts})`)
    } catch (error) {
      console.log(`User ${username} login check failed (attempt ${attempt}/${attempts})`)
    }
    await new Promise(resolve => setTimeout(resolve, delayMs))
  }
  throw new Error(`User ${username} could not log in after ${attempts} attempts`)
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
    console.log('Production mode detected, creating temporary test users...')
    try {
      adminToken = await getAdminToken()
      console.log('Got admin token, creating users...')

      await createTestUser(adminToken, TEST_USERS.researcher.username, testPassword, 'researcher')
      await createTestUser(adminToken, TEST_USERS.evaluator.username, testPassword, 'evaluator')
      await createTestUser(adminToken, TEST_USERS.chatbot_manager.username, testPassword, 'chatbot_manager')

      console.log('Verifying test users can log in...')
      await waitForUserLogin(TEST_USERS.researcher.username, testPassword)
      await waitForUserLogin(TEST_USERS.evaluator.username, testPassword)
      await waitForUserLogin(TEST_USERS.chatbot_manager.username, testPassword)
      console.log('Test users ready')
    } catch (error) {
      console.error('Failed to create test users:', error.message)
      throw error
    }
  }
})

setup('authenticate as researcher', async ({ page }) => {
  const user = isProduction ? TEST_USERS.researcher : { username: 'researcher', password: testPassword }
  await performLogin(page, user)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'researcher.json') })
})

setup('authenticate as evaluator', async ({ page }) => {
  const user = isProduction ? TEST_USERS.evaluator : { username: 'evaluator', password: testPassword }
  await performLogin(page, user)
  await page.context().storageState({ path: path.join(AUTH_DIR, 'evaluator.json') })
})

// Cleanup: Delete temporary test users after all setup tests complete
setup.afterAll(async () => {
  if (isProduction && adminToken) {
    console.log('Cleaning up temporary test users...')
    await deleteTestUser(adminToken, TEST_USERS.researcher.username)
    await deleteTestUser(adminToken, TEST_USERS.evaluator.username)
    await deleteTestUser(adminToken, TEST_USERS.chatbot_manager.username)
  }
})
