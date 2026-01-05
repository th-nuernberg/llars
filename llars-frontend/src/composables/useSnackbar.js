/**
 * Global Snackbar Composable
 *
 * Provides a simple snackbar/toast notification system.
 * Uses a shared state so notifications can be triggered from anywhere.
 */
import { ref, readonly } from 'vue'

// Shared state across all instances
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
  timeout: 4000,
  icon: null
})

export function useSnackbar() {
  /**
   * Show a success notification
   */
  const showSuccess = (message, timeout = 4000) => {
    snackbar.value = {
      show: true,
      message,
      color: 'success',
      timeout,
      icon: 'mdi-check-circle'
    }
  }

  /**
   * Show an error notification
   */
  const showError = (message, timeout = 6000) => {
    snackbar.value = {
      show: true,
      message,
      color: 'error',
      timeout,
      icon: 'mdi-alert-circle'
    }
  }

  /**
   * Show an info notification
   */
  const showInfo = (message, timeout = 4000) => {
    snackbar.value = {
      show: true,
      message,
      color: 'info',
      timeout,
      icon: 'mdi-information'
    }
  }

  /**
   * Show a warning notification
   */
  const showWarning = (message, timeout = 5000) => {
    snackbar.value = {
      show: true,
      message,
      color: 'warning',
      timeout,
      icon: 'mdi-alert'
    }
  }

  /**
   * Show a custom notification
   */
  const showMessage = (message, options = {}) => {
    snackbar.value = {
      show: true,
      message,
      color: options.color || 'primary',
      timeout: options.timeout || 4000,
      icon: options.icon || null
    }
  }

  /**
   * Hide the snackbar
   */
  const hideSnackbar = () => {
    snackbar.value.show = false
  }

  return {
    // State (readonly to prevent direct mutations)
    snackbar: readonly(snackbar),
    // For v-model binding in the snackbar component
    snackbarModel: snackbar,
    // Methods
    showSuccess,
    showError,
    showInfo,
    showWarning,
    showMessage,
    hideSnackbar
  }
}
