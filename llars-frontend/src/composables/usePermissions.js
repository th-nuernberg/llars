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

// Shared state across all instances
const permissions = ref([])
const roles = ref([])
const username = ref(null)
const isLoading = ref(false)
let inflightRequest = null

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
        const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
        // Authorization header is injected globally via axios interceptor (main.js).
        const response = await axios.get(`${baseUrl}/api/permissions/my-permissions`)

        if (response.data.success) {
          // Backend returns payload under data: { username, permissions, roles }
          const payload = response.data.data || response.data
          permissions.value = payload.permissions || []
          roles.value = payload.roles || []
          username.value = payload.username || null
        }
      } catch (error) {
        console.error('Failed to fetch permissions:', error)
        if (error.response?.status === 401) {
          permissions.value = []
          roles.value = []
          username.value = null
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
