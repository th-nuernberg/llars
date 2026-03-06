/**
 * Console Controller
 *
 * Console output is suppressed by default (both dev and production).
 * An admin can enable console logs per user via the admin panel.
 * When enabled, the LOGGING tag appears in the app bar.
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

/**
 * Install console suppression.
 * Call once during app bootstrap. Suppresses all console output
 * until explicitly enabled per user via admin panel.
 */
export function installConsoleController() {
  if (initialized) return
  initialized = true

  // Suppress all console output by default
  METHODS.forEach(method => {
    console[method] = noop
  })
}

/**
 * Enable or disable console output for the current user.
 */
export function setConsoleLogsEnabled(value) {
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
 * Whether console logs are currently enabled.
 */
export function isConsoleLogsEnabled() {
  return enabled
}
