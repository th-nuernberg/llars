/**
 * Console Controller
 *
 * Verbose developer logging (log/info/debug) is suppressed by default (both
 * dev and production); an admin can enable full logging per user via the admin
 * panel (the LOGGING tag then appears in the app bar).
 *
 * CRITICAL: real problems must NEVER be silently swallowed. `console.error` and
 * `console.warn` always pass through — this is how Vue surfaces component
 * setup/render errors (Vue catches them internally and logs via console rather
 * than throwing to window.onerror, so noop-ing console.error made real bugs
 * render as a blank page with zero output). Only explicitly KNOWN, expected
 * noise (see KNOWN_NOISE) is filtered out of those channels.
 */

// Verbose channels — off by default, toggled by the admin per-user.
const VERBOSE = ['log', 'info', 'debug']
// Real-problem channels — always on, only KNOWN_NOISE is filtered.
const ALWAYS_ON = ['warn', 'error']
const METHODS = [...VERBOSE, ...ALWAYS_ON]

// Explicit allowlist of KNOWN, harmless noise we still want to hide on the
// always-on channels (e.g. third-party deprecation spam). Keep this tight —
// anything not matched here is a real signal and must reach the console.
const KNOWN_NOISE = [
  // Example (add only proven-harmless patterns):
  // /\[Vuetify\] Translation key/,
]

const originalConsole = {}
let enabled = false
let initialized = false

// Store originals before anything can overwrite them
METHODS.forEach(method => {
  originalConsole[method] = console[method]?.bind(console) || (() => {})
})

function noop() {}

function isKnownNoise(args) {
  if (!KNOWN_NOISE.length) return false
  const msg = args
    .map(a => (typeof a === 'string' ? a : a && a.message ? a.message : ''))
    .join(' ')
  return KNOWN_NOISE.some(re => re.test(msg))
}

// A wrapper for the always-on channels: passes everything through to the real
// console EXCEPT explicitly-known noise.
function makeAlwaysOn(method) {
  return (...args) => {
    if (isKnownNoise(args)) return
    originalConsole[method](...args)
  }
}

/**
 * Install console handling. Call once during app bootstrap.
 * - warn/error: always on (minus KNOWN_NOISE) — real problems are never hidden.
 * - log/info/debug: suppressed until an admin enables logging for the user.
 */
export function installConsoleController() {
  if (initialized) return
  initialized = true

  VERBOSE.forEach(method => { console[method] = noop })
  ALWAYS_ON.forEach(method => { console[method] = makeAlwaysOn(method) })
}

/**
 * Enable or disable verbose console output for the current user. warn/error are
 * unaffected (always on); this only toggles the verbose log/info/debug channels.
 */
export function setConsoleLogsEnabled(value) {
  enabled = Boolean(value)
  VERBOSE.forEach(method => {
    console[method] = enabled ? originalConsole[method] : noop
  })
  // Keep warn/error on the filtered always-on wrapper regardless.
  ALWAYS_ON.forEach(method => {
    console[method] = makeAlwaysOn(method)
  })

  if (enabled) {
    originalConsole.log(
      '%c[LLARS] Verbose console logging enabled by admin',
      'color: #b0ca97; font-weight: bold'
    )
  }
}

/**
 * Whether verbose console logs are currently enabled.
 */
export function isConsoleLogsEnabled() {
  return enabled
}
