/**
 * LLARS E2E Test Helpers
 *
 * Shared utility functions for all E2E tests.
 * Import these helpers to reduce code duplication.
 */

export const TEST_USERS = {
  rater: { username: 'researcher', password: 'admin123' },
  researcher: { username: 'researcher', password: 'admin123' },
  viewer: { username: 'viewer', password: 'admin123' },
  admin: { username: 'admin', password: 'admin123' },
  chatbot_manager: { username: 'chatbot_manager', password: 'admin123' }
}

/**
 * Dismiss consent banner if visible (handles both old and new consent dialogs)
 */
export async function dismissConsentBanner(page) {
  try {
    // Try old analytics-consent banner
    const consentBtn = page.locator('.analytics-consent button').first()
    if (await consentBtn.isVisible({ timeout: 300 }).catch(() => false)) {
      await consentBtn.click({ force: true }).catch(() => {})
      await page.waitForTimeout(100).catch(() => {})
    }

    // Try new Analytics & Datenschutz dialog with Zustimmen/Ablehnen buttons
    const analyticsDialog = page.locator('button:has-text("Zustimmen"), button:has-text("Ablehnen")').first()
    if (await analyticsDialog.isVisible({ timeout: 500 }).catch(() => false)) {
      await analyticsDialog.click({ force: true }).catch(() => {})
      await page.waitForTimeout(300).catch(() => {})
    }
  } catch (e) {
    // Page might be closed, ignore
  }
}

/**
 * Handle privacy page redirect (Datenschutzerklärung)
 */
export async function handlePrivacyPage(page) {
  try {
    const isOnPrivacyPage = await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 1000 }).catch(() => false)
    if (isOnPrivacyPage) {
      // Dismiss analytics consent first
      await dismissConsentBanner(page)
      // Wait a bit for any redirects
      await page.waitForTimeout(500).catch(() => {})
    }
    return isOnPrivacyPage
  } catch (e) {
    return false
  }
}

/**
 * Quick login using dev buttons (fast) with retry
 */
export async function quickLogin(page, user = TEST_USERS.researcher, retries = 3) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      await page.goto('/login', { waitUntil: 'domcontentloaded', timeout: 30000 })
      await page.waitForLoadState('load')
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })

      await dismissConsentBanner(page)
      await page.waitForTimeout(200)

      // Handle privacy page
      const isOnPrivacyPage = await page.locator('h1:has-text("Datenschutzerklärung")').isVisible({ timeout: 500 }).catch(() => false)
      if (isOnPrivacyPage) {
        const acceptBtn = page.locator('button:has-text("Zustimmen"), button:has-text("Ablehnen")').first()
        if (await acceptBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
          await acceptBtn.click()
          await page.waitForTimeout(300)
        }
      }

      await page.waitForSelector('.dev-login-buttons, #username, .login-form', { timeout: 15000 })

      const devBtn = page.locator('.dev-login-buttons button:not([disabled])').filter({ hasText: user.username })
      if (await devBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await devBtn.click()
        await page.waitForURL(/\/Home/, { timeout: 25000 })
      } else {
        await page.locator('#username, input[placeholder*="username" i]').first().fill(user.username)
        await page.locator('#password, input[type="password"]').first().fill(user.password)
        await page.locator('.login-button, button:has-text("Anmelden")').first().click()
        await page.waitForURL(/\/Home/, { timeout: 25000 })
      }

      await dismissConsentBanner(page)
      return // Success
    } catch (error) {
      if (attempt === retries) throw error
      await page.waitForTimeout(1000 * attempt)
    }
  }
}

/**
 * Wait for loading indicators to disappear
 */
export async function waitForLoading(page, timeout = 10000) {
  await page.waitForSelector('[role="alert"]:has-text("Loading")', { state: 'hidden', timeout }).catch(() => {})
  await page.waitForTimeout(200)
}

/**
 * Wait for page to be ready (no skeletons, no loading)
 */
export async function waitForPageReady(page, timeout = 10000) {
  await page.waitForSelector('.v-skeleton-loader', { state: 'hidden', timeout }).catch(() => {})
  await waitForLoading(page, timeout)
}

/**
 * Get thread cards on overview pages
 */
export function getThreadCards(page) {
  return page.locator('.thread-card')
}

/**
 * Click first available thread card
 */
export async function clickFirstThread(page) {
  const threadCard = getThreadCards(page).first()
  if (await threadCard.isVisible({ timeout: 3000 }).catch(() => false)) {
    await threadCard.click()
    await page.waitForLoadState('load')
    return true
  }
  return false
}
