/**
 * Console Controller
 *
 * In production, all console output is suppressed by default.
 * An admin can enable console logs per user via the admin panel.
 * When enabled, the user sees a notification banner.
 */

const METHODS = ['log', 'warn', 'error', 'info', 'debug']
const originalConsole = {}

let enabled = false
let initialized = false

// Store originals before anything can overwrite them
METHODS.forEach(method => {
  originalConsole[method] = console[method]?.bind(console)
})

function noop() {}

function isProduction() {
  return import.meta.env.PROD && import.meta.env.MODE !== 'development'
}

/**
 * Install console suppression (production only).
 * Call once during app bootstrap.
 */
export function installConsoleController() {
  if (!isProduction() || initialized) return
  initialized = true

  // Suppress all console output by default in production
  METHODS.forEach(method => {
    console[method] = noop
  })
}

/**
 * Enable or disable console output for the current user.
 */
export function setConsoleLogsEnabled(value) {
  if (!isProduction()) return // in dev, console is always available

  enabled = Boolean(value)
  METHODS.forEach(method => {
    console[method] = enabled ? originalConsole[method] : noop
  })

  if (enabled) {
    originalConsole.log(
      '%c[LLARS] Console logging enabled by admin',
      'color: #b0ca97; font-weight: bold'
    )
  }
}

/**
 * Whether console logs are currently enabled (always true in dev).
 */
export function isConsoleLogsEnabled() {
  if (!isProduction()) return true
  return enabled
}
