/**
 * Permission Management Composable
 *
 * Provides reactive permission checking and management for the LLars frontend.
 * Automatically fetches user permissions from the backend and provides helper functions.
 *
 * Usage:
 *   const { hasPermission, permissions, roles, isLoading, fetchPermissions } = usePermissions()
 *
 *   // Check if user has a permission
 *   if (hasPermission('feature:mail_rating:view')) {
 *     // Show mail rating feature
 *   }
 *
 *   // In template
 *   <v-btn v-if="hasPermission('feature:mail_rating:edit')">Edit</v-btn>
 */

import { ref, computed } from 'vue'
import axios from 'axios'
import { logI18n } from '@/utils/logI18n'

// Shared state across all instances
const permissions = ref([])
const roles = ref([])
const username = ref(null)
const isLoading = ref(false)
// True once a permission fetch has completed successfully at least once.
// The router guard awaits this on hard reload so permission-gated routes
// aren't bounced to /Home before the async fetch resolves (see router.js).
const hasLoaded = ref(false)
// True when the LAST fetch failed for a transient reason (429 rate limit, 5xx,
// network blip) rather than a genuine 401. The router guard reads this to tell
// "this user has no permissions" apart from "we could not find out yet".
//
// INCIDENT 2026-07-29: /api/permissions/my-permissions is polled every ~5s and
// was not exempt from the 500/h-per-IP production rate limit. Once a rater
// burned the budget the endpoint 429'd for the rest of the session; on a fresh
// login the very first fetch then failed, `permissions` stayed [] and the guard
// bounced every permission-gated route back to /login. Raters experienced it as
// "I keep getting logged out" and finally "I can't log in at all". No 401 was
// ever involved (230x 429, 0x 401 on the worst-hit IP).
const loadFailedTransiently = ref(false)
let inflightRequest = null

// A transient failure is anything that is not an authoritative "you are not
// allowed" answer from the backend. 403 is deliberately NOT in here: that is a
// real answer. Everything else (no response at all, 408/425/429, any 5xx) means
// we simply do not know the user's permissions right now.
function _isTransientFailure(error) {
  const status = Number(error?.response?.status || 0)
  if (!status) return true // network error / timeout — no response at all
  if (status === 401 || status === 403) return false
  return status === 408 || status === 425 || status === 429 || status >= 500
}

export function usePermissions() {
  /**
   * Fetch user permissions from the backend
   */
  async function fetchPermissions(force = false) {
    if (inflightRequest) {
      await inflightRequest
      if (!force) return
    }

    isLoading.value = true

    inflightRequest = (async () => {
      try {
        const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
        // Authorization header is injected globally via axios interceptor (main.js).
        const response = await axios.get(`${baseUrl}/api/permissions/my-permissions`)

        if (response.data.success) {
          // Backend returns payload under data: { username, permissions, roles }
          const payload = response.data.data || response.data
          permissions.value = payload.permissions || []
          roles.value = payload.roles || []
          username.value = payload.username || null
          hasLoaded.value = true
          loadFailedTransiently.value = false
        }
      } catch (error) {
        logI18n('error', 'logs.permissions.fetchFailed', error)
        if (_isTransientFailure(error)) {
          // We do not know the permissions — say so instead of silently
          // presenting an empty set as fact. Any previously loaded permissions
          // are kept so an established session degrades to "stale" rather than
          // "logged out"; the router guard uses this flag to stop bouncing
          // users out of gated routes while the backend is unreachable.
          // Server-side @require_permission still enforces access, so letting
          // navigation through here loosens nothing that actually matters.
          loadFailedTransiently.value = true
        } else {
          // 401/403 — an authoritative "no".
          permissions.value = []
          roles.value = []
          username.value = null
          hasLoaded.value = false
          loadFailedTransiently.value = false
        }
      } finally {
        inflightRequest = null
        isLoading.value = false
      }
    })()

    await inflightRequest
  }

  /**
   * Check if user has a specific permission
   *
   * @param {string} permissionKey - The permission to check (e.g., 'feature:mail_rating:view')
   * @returns {boolean} True if user has the permission
   */
  function hasPermission(permissionKey) {
    return permissions.value.includes(permissionKey)
  }

  /**
   * Check if user has ANY of the specified permissions (OR logic)
   *
   * @param {...string} permissionKeys - Permission keys to check
   * @returns {boolean} True if user has at least one permission
   */
  function hasAnyPermission(...permissionKeys) {
    return permissionKeys.some(key => permissions.value.includes(key))
  }

  /**
   * Check if user has ALL of the specified permissions (AND logic)
   *
   * @param {...string} permissionKeys - Permission keys to check
   * @returns {boolean} True if user has all permissions
   */
  function hasAllPermissions(...permissionKeys) {
    return permissionKeys.every(key => permissions.value.includes(key))
  }

  /**
   * Check if user has a specific role
   *
   * @param {string} roleName - The role to check (e.g., 'admin', 'researcher')
   * @returns {boolean} True if user has the role
   */
  function hasRole(roleName) {
    return roles.value.some(role => role.role_name === roleName)
  }

  /**
   * Check if user has ANY of the specified roles (OR logic)
   *
   * @param {...string} roleNames - Role names to check
   * @returns {boolean} True if user has at least one role
   */
  function hasAnyRole(...roleNames) {
    return roleNames.some(name => hasRole(name))
  }

  /**
   * Clear all permissions (used on logout)
   */
  function clearPermissions() {
    permissions.value = []
    roles.value = []
    username.value = null
    hasLoaded.value = false
    inflightRequest = null
  }

  /**
   * Computed property to check if user is admin
   */
  const isAdmin = computed(() => hasRole('admin'))

  /**
   * Computed property to check if user is researcher
   */
  const isResearcher = computed(() => hasRole('researcher'))

  /**
   * Computed property to check if user has any admin permissions
   */
  const hasAdminPermissions = computed(() => {
    return permissions.value.some(perm => perm.startsWith('admin:'))
  })

  /**
   * Get all permissions for a specific category
   *
   * @param {string} category - The category (e.g., 'feature', 'admin', 'data')
   * @returns {string[]} Permissions in that category
   */
  function getPermissionsByCategory(category) {
    return permissions.value.filter(perm => perm.startsWith(`${category}:`))
  }

  return {
    // State
    permissions,
    roles,
    username,
    isLoading,
    hasLoaded,
    loadFailedTransiently,

    // Computed
    isAdmin,
    isResearcher,
    hasAdminPermissions,

    // Methods
    fetchPermissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    clearPermissions,
    getPermissionsByCategory
  }
}
