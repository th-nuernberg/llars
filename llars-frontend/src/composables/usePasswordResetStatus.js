/**
 * Password Reset Status Composable
 *
 * Singleton state for the self-service "forgot password" feature toggle.
 * The login page fetches this (public endpoint, no auth) on mount to decide
 * whether to show the "Passwort vergessen?" link.
 */
import { ref } from 'vue'
import axios from 'axios'

// Singleton state - shared across all component instances
const passwordResetEnabled = ref(false)
const loaded = ref(false)
const loading = ref(false)

export function usePasswordResetStatus() {
  /**
   * Fetch the global self-service password-reset status (public endpoint).
   * Cached in the singleton - call once (e.g. on the login page mount).
   */
  async function fetchPasswordResetStatus() {
    if (loaded.value) return passwordResetEnabled.value
    loading.value = true
    try {
      const { data } = await axios.get('/api/system/password-reset-status')
      passwordResetEnabled.value = data.self_service_password_reset_enabled || false
      loaded.value = true
    } catch {
      passwordResetEnabled.value = false
    } finally {
      loading.value = false
    }
    return passwordResetEnabled.value
  }

  return {
    passwordResetEnabled,
    loaded,
    loading,
    fetchPasswordResetStatus,
  }
}
