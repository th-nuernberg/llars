/**
 * Communication Admin Composable
 *
 * Singleton state for communication feature toggle (cached).
 * Listens for real-time Socket.IO events when admin changes settings.
 * Provides API methods for the admin communication management panel.
 */
import { ref } from 'vue'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'

// Singleton state - shared across all component instances
const communicationEnabled = ref(false)
const loaded = ref(false)
const loading = ref(false)
const _socketListenerAttached = ref(false)

// Permission re-fetch helper (shared singleton)
const _perms = usePermissions()

export function useCommunicationAdmin() {
  /**
   * Fetch global communication status (public endpoint, no auth required).
   * Cached in singleton - call once on app mount.
   */
  async function fetchCommunicationStatus() {
    if (loaded.value) return
    loading.value = true
    try {
      const { data } = await axios.get('/api/system/communication-status')
      communicationEnabled.value = data.communication_enabled || false
      loaded.value = true
    } catch {
      communicationEnabled.value = false
    } finally {
      loading.value = false
    }
  }

  /**
   * Force refresh (e.g. after admin toggles the setting).
   * Does NOT reset loaded flag to avoid UI flicker.
   */
  async function refreshCommunicationStatus() {
    try {
      const { data } = await axios.get('/api/system/communication-status')
      communicationEnabled.value = data.communication_enabled || false
      loaded.value = true
    } catch {
      // Keep current value on error
    }
  }

  /**
   * Attach Socket.IO listeners for real-time updates.
   * Call once from App.vue after socket is ready.
   */
  function attachSocketListeners(socket) {
    if (_socketListenerAttached.value || !socket) return

    // Global toggle changed by admin
    socket.on('communication:status_changed', (data) => {
      communicationEnabled.value = !!data.communication_enabled
      loaded.value = true
    })

    // Per-user permissions changed by admin → re-fetch own permissions
    socket.on('communication:permissions_changed', () => {
      _perms.fetchPermissions(true)
    })

    _socketListenerAttached.value = true
  }

  // ── Admin API methods ──

  async function fetchUsers() {
    const { data } = await axios.get('/api/admin/communication/users')
    return data.users || []
  }

  async function setUserPermissions(username, permissions) {
    const { data } = await axios.put(`/api/admin/communication/users/${username}`, { permissions })
    return data
  }

  async function bulkSetPermissions(usernames, permissions) {
    const { data } = await axios.post('/api/admin/communication/users/bulk', { usernames, permissions })
    return data
  }

  async function fetchStats() {
    const { data } = await axios.get('/api/admin/communication/stats')
    return data
  }

  return {
    communicationEnabled,
    loaded,
    loading,
    fetchCommunicationStatus,
    refreshCommunicationStatus,
    attachSocketListeners,
    // Admin
    fetchUsers,
    setUserPermissions,
    bulkSetPermissions,
    fetchStats,
  }
}
