/**
 * Snackbar notification composable
 * Simple notification system for user feedback
 */

export function useSnackbar() {
  const showSuccess = (message) => {
    console.log('[SUCCESS]', message)
    // TODO: Integrate with Vuetify v-snackbar or global notification system
    alert(`✓ ${message}`)
  }

  const showError = (message) => {
    console.error('[ERROR]', message)
    // TODO: Integrate with Vuetify v-snackbar or global notification system
    alert(`✗ ${message}`)
  }

  const showInfo = (message) => {
    console.info('[INFO]', message)
    alert(`ℹ ${message}`)
  }

  const showWarning = (message) => {
    console.warn('[WARNING]', message)
    alert(`⚠ ${message}`)
  }

  return {
    showSuccess,
    showError,
    showInfo,
    showWarning
  }
}
