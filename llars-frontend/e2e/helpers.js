/**
 * LLARS E2E Test Helpers
 *
 * Shared utility functions for all E2E tests.
 * Following Playwright best practices:
 * - NO waitForTimeout() - use condition-based waits instead
 * - Use web-first assertions (toBeVisible, toHaveText, etc.)
 * - Use stable selectors (data-testid preferred)
 * - Use waitFor() for explicit synchronization
 *
 * @see https://playwright.dev/docs/best-practices
 */

const testPassword = process.env.E2E_TEST_PASSWORD || 'admin123'
export const isProduction = !!process.env.E2E_TEST_PASSWORD
const playwrightBaseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:55080'
const apiBaseURL = process.env.PLAYWRIGHT_API_BASE_URL || playwrightBaseURL
const adminUsername = isProduction ? (process.env.E2E_ADMIN_USER || 'test_admin') : 'admin'
const researcherUsername = isProduction ? (process.env.E2E_RESEARCHER_USER || 'test_researcher') : 'researcher'
const evaluatorUsername = isProduction ? (process.env.E2E_EVALUATOR_USER || 'test_evaluator') : 'evaluator'
const chatbotManagerUsername = isProduction
  ? (process.env.E2E_CHATBOT_MANAGER_USER || adminUsername)
  : 'chatbot_manager'

export const TEST_USERS = {
  rater: { username: researcherUsername, password: testPassword },
  researcher: { username: researcherUsername, password: testPassword },
  evaluator: { username: evaluatorUsername, password: testPassword },
  admin: { username: adminUsername, password: testPassword },
  chatbot_manager: { username: chatbotManagerUsername, password: testPassword }
}

async function apiLogin(user) {
  const response = await fetch(`${apiBaseURL}/auth/authentik/login`, {
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
  await page.evaluate((payload) => {
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

/**
 * Dismiss consent banner if visible (handles both old and new consent dialogs)
 * Uses condition-based waits instead of timeouts
 */
export async function dismissConsentBanner(page) {
  try {
    // Try old analytics-consent banner - use short timeout for optional elements
    const consentBtn = page.locator('.analytics-consent button').first()
    if (await consentBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await consentBtn.click({ force: true })
      // Wait for the banner to be hidden instead of fixed timeout
      await consentBtn.waitFor({ state: 'hidden', timeout: 2000 }).catch(() => {})
    }

    // Try new Analytics & Datenschutz dialog - look for ZUSTIMMEN or ABLEHNEN buttons
    // These appear as uppercase in the UI
    const zustimmenBtn = page.locator('button:has-text("ZUSTIMMEN"), button:has-text("Zustimmen")').first()
    const ablehnenBtn = page.locator('button:has-text("ABLEHNEN"), button:has-text("Ablehnen")').first()

    if (await zustimmenBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
      await zustimmenBtn.click({ force: true })
      // Wait for dialog to close
      await zustimmenBtn.waitFor({ state: 'hidden', timeout: 3000 }).catch(() => {})
    } else if (await ablehnenBtn.isVisible({ timeout: 500 }).catch(() => false)) {
      await ablehnenBtn.click({ force: true })
      await ablehnenBtn.waitFor({ state: 'hidden', timeout: 3000 }).catch(() => {})
    }
  } catch (e) {
    // Page might be closed, ignore
  }
}

/**
 * Handle privacy page redirect (Datenschutzerklärung)
 * Uses URL-based detection instead of timeouts
 */
export async function handlePrivacyPage(page) {
  try {
    const isOnPrivacyPage = page.url().includes('Datenschutz') ||
      await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)

    if (isOnPrivacyPage) {
      await dismissConsentBanner(page)
      // Wait for navigation if it happens, but don't block
      await page.waitForLoadState('domcontentloaded', { timeout: 3000 }).catch(() => {})
    }
    return isOnPrivacyPage
  } catch (e) {
    return false
  }
}

/**
 * Quick login using dev buttons (fast) with retry
 *
 * Best practices applied:
 * - Uses waitFor() for explicit synchronization
 * - Uses waitForURL() instead of fixed delays
 * - Uses domcontentloaded for reliable page load detection (avoids analytics timeouts)
 * - Handles Datenschutz page redirect properly
 */
export async function quickLogin(page, user = TEST_USERS.researcher, retries = 2) {
  // In production mode, storageState provides auth tokens - check if already authenticated
  if (isProduction) {
    await page.goto('/Home', { waitUntil: 'domcontentloaded', timeout: 30000 })
    await page.waitForLoadState('load', { timeout: 5000 }).catch(() => {})
    if (page.url().includes('/Home')) {
      await dismissConsentBanner(page)
      return // Already authenticated via storageState
    }

    // Session expired or missing: refresh tokens via API to avoid brittle form login.
    try {
      const tokenData = await apiLogin(user)
      await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {})
      await applyAuthStorage(page, user, tokenData)
      await page.goto('/Home', { waitUntil: 'domcontentloaded', timeout: 30000 })
      await page.waitForLoadState('load', { timeout: 5000 }).catch(() => {})
      await dismissConsentBanner(page)
      if (page.url().includes('/Home')) {
        return
      }
    } catch (error) {
      // Fall back to form-based login below when API login is unavailable.
    }
  }

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      // Navigate to login page - use domcontentloaded to avoid analytics timeout
      await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 })

      // Clear storage for clean state (dev mode only - production uses storageState)
      if (!isProduction) {
        await page.evaluate(() => {
          localStorage.clear()
          sessionStorage.clear()
        })
      }

      // Handle privacy/Datenschutz page redirect - this is a common first-visit redirect
      // Check URL or page content for privacy page
      const currentUrl = page.url()
      const isOnPrivacyPage = currentUrl.includes('Datenschutz') || currentUrl.includes('datenschutz') ||
        await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)

      if (isOnPrivacyPage) {
        // Dismiss consent dialog first
        await dismissConsentBanner(page)

        // After consent, click "Anmelden" button in header or navigate to /login
        const anmeldenBtn = page.locator('button:has-text("Anmelden"), a:has-text("Anmelden")').first()
        if (await anmeldenBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
          await anmeldenBtn.click()
          await page.waitForLoadState('domcontentloaded', { timeout: 10000 })
        } else {
          // Fallback: navigate directly to login
          await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 })
        }
        await dismissConsentBanner(page)
      }

      // Dismiss any remaining consent dialogs
      await dismissConsentBanner(page)

      // Wait for login form to be ready
      const loginForm = page.locator('.dev-login-buttons, #username, .login-form, [data-testid="login-form"]')
      await loginForm.first().waitFor({ state: 'visible', timeout: 30000 })

      // Try dev login buttons first (faster)
      const devBtn = page.locator('.dev-login-buttons button:not([disabled]), [data-testid="dev-login-btn"]')
        .filter({ hasText: user.username })

      if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await devBtn.click()
      } else {
        // Fallback to manual login
        const usernameInput = page.locator('#username, input[placeholder*="username" i], [data-testid="username-input"]').first()
        const passwordInput = page.locator('#password, input[type="password"], [data-testid="password-input"]').first()
        const loginButton = page.locator('.login-button, button:has-text("Anmelden"), [data-testid="login-btn"]').first()

        await usernameInput.fill(user.username)
        await passwordInput.fill(user.password)
        await loginButton.click()
      }

      // Wait for successful navigation to Home
      await page.waitForURL(/\/Home/, { timeout: 30000 })
      await dismissConsentBanner(page)

      return // Success
    } catch (error) {
      if (attempt === retries) throw error
      // Use page reload for retry
      await page.reload({ waitUntil: 'domcontentloaded', timeout: 10000 }).catch(() => {})
    }
  }
}

/**
 * Wait for loading indicators to disappear using condition-based waits
 */
export async function waitForLoading(page, timeout = 10000) {
  // Wait for any loading indicators to disappear
  const loadingIndicators = [
    '[role="alert"]:has-text("Loading")',
    '.v-progress-circular',
    '.loading-spinner',
    '[data-testid="loading"]'
  ]

  for (const selector of loadingIndicators) {
    await page.locator(selector).first().waitFor({ state: 'hidden', timeout: timeout / 2 }).catch(() => {})
  }
}

/**
 * Wait for page to be ready (no skeletons, no loading)
 * Uses condition-based waits for each indicator
 */
export async function waitForPageReady(page, timeout = 10000) {
  // Wait for skeleton loaders to disappear
  await page.locator('.v-skeleton-loader').first().waitFor({ state: 'hidden', timeout }).catch(() => {})

  // Wait for any loading states
  await waitForLoading(page, timeout)

  // Wait for DOM to be ready (avoid networkidle due to analytics)
  await page.waitForLoadState('domcontentloaded', { timeout: 5000 }).catch(() => {})
}

/**
 * Wait for API response - useful for verifying backend operations
 * @param {Page} page - Playwright page
 * @param {string} urlPattern - URL pattern to match (e.g., '/api/chatbots')
 * @param {number} timeout - Timeout in ms
 */
export async function waitForApiResponse(page, urlPattern, timeout = 10000) {
  return page.waitForResponse(
    response => response.url().includes(urlPattern) && response.status() < 400,
    { timeout }
  ).catch(() => null)
}

/**
 * Get thread cards on overview pages
 */
export function getThreadCards(page) {
  return page.locator('.thread-card, [data-testid="thread-card"]')
}

/**
 * Click first available thread card with proper waiting
 */
export async function clickFirstThread(page) {
  const threadCard = getThreadCards(page).first()

  // Use waitFor instead of isVisible with timeout
  try {
    await threadCard.waitFor({ state: 'visible', timeout: 5000 })
    await threadCard.click()
    await page.waitForLoadState('domcontentloaded', { timeout: 10000 })
    return true
  } catch {
    return false
  }
}

/**
 * Navigate to a page and ensure it's loaded
 * @param {Page} page - Playwright page
 * @param {string} path - URL path (e.g., '/LatexCollab')
 * @param {Object} options - Navigation options
 */
export async function navigateTo(page, path, options = {}) {
  const { requireAuth = true, user = TEST_USERS.researcher } = options

  await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 30000 })
  await dismissConsentBanner(page)

  // Check if redirected to login
  if (page.url().includes('/login') && requireAuth) {
    await quickLogin(page, user)
    await page.goto(path, { waitUntil: 'domcontentloaded', timeout: 30000 })
    await dismissConsentBanner(page)
  }
}

/**
 * Assert element is visible with auto-retry (web-first assertion)
 * Preferred over manual visibility checks
 */
export async function assertVisible(page, selector, timeout = 10000) {
  const { expect } = await import('@playwright/test')
  await expect(page.locator(selector).first()).toBeVisible({ timeout })
}

/**
 * Assert element contains text with auto-retry
 */
export async function assertHasText(page, selector, text, timeout = 10000) {
  const { expect } = await import('@playwright/test')
  await expect(page.locator(selector).first()).toContainText(text, { timeout })
}

/**
 * Click element with proper waiting and optional API response verification
 */
export async function clickAndWait(page, selector, apiPattern = null) {
  const element = page.locator(selector).first()
  await element.waitFor({ state: 'visible', timeout: 10000 })

  if (apiPattern) {
    // Click and wait for API response
    await Promise.all([
      waitForApiResponse(page, apiPattern),
      element.click()
    ])
  } else {
    await element.click()
    await page.waitForLoadState('domcontentloaded', { timeout: 10000 }).catch(() => {})
  }
}
