/**
 * usePermissions Composable Tests
 *
 * Tests for the LLARS permission management composable.
 * Test IDs: PERM_001 - PERM_055
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

import axios from 'axios'

// We need to reset modules to get fresh state for each test
let usePermissions

describe('usePermissions Composable', () => {
  beforeEach(async () => {
    // Clear all mocks
    vi.clearAllMocks()

    // Reset module to get fresh shared state
    vi.resetModules()

    // Re-import to get fresh state
    const module = await import('@/composables/usePermissions')
    usePermissions = module.usePermissions
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('PERM_001: exports usePermissions function', () => {
      expect(typeof usePermissions).toBe('function')
    })

    it('PERM_002: returns all expected properties', () => {
      const perms = usePermissions()

      // State
      expect(perms).toHaveProperty('permissions')
      expect(perms).toHaveProperty('roles')
      expect(perms).toHaveProperty('username')
      expect(perms).toHaveProperty('isLoading')

      // Computed
      expect(perms).toHaveProperty('isAdmin')
      expect(perms).toHaveProperty('isResearcher')
      expect(perms).toHaveProperty('hasAdminPermissions')

      // Methods
      expect(perms).toHaveProperty('fetchPermissions')
      expect(perms).toHaveProperty('hasPermission')
      expect(perms).toHaveProperty('hasAnyPermission')
      expect(perms).toHaveProperty('hasAllPermissions')
      expect(perms).toHaveProperty('hasRole')
      expect(perms).toHaveProperty('hasAnyRole')
      expect(perms).toHaveProperty('clearPermissions')
      expect(perms).toHaveProperty('getPermissionsByCategory')
    })

    it('PERM_003: permissions is a ref with array value', () => {
      const perms = usePermissions()

      expect(Array.isArray(perms.permissions.value)).toBe(true)
    })

    it('PERM_004: roles is a ref with array value', () => {
      const perms = usePermissions()

      expect(Array.isArray(perms.roles.value)).toBe(true)
    })

    it('PERM_005: username is a ref', () => {
      const perms = usePermissions()

      expect(perms.username).toBeDefined()
      expect(perms.username.value).toBeNull()
    })

    it('PERM_006: isLoading is a ref with boolean value', () => {
      const perms = usePermissions()

      expect(typeof perms.isLoading.value).toBe('boolean')
    })
  })

  // ==================== Initial State Tests ====================

  describe('Initial State', () => {
    it('PERM_007: permissions is empty initially', () => {
      const perms = usePermissions()

      expect(perms.permissions.value).toEqual([])
    })

    it('PERM_008: roles is empty initially', () => {
      const perms = usePermissions()

      expect(perms.roles.value).toEqual([])
    })

    it('PERM_009: username is null initially', () => {
      const perms = usePermissions()

      expect(perms.username.value).toBeNull()
    })

    it('PERM_010: isLoading is false initially', () => {
      const perms = usePermissions()

      expect(perms.isLoading.value).toBe(false)
    })

    it('PERM_011: isAdmin is false initially', () => {
      const perms = usePermissions()

      expect(perms.isAdmin.value).toBe(false)
    })

    it('PERM_012: isResearcher is false initially', () => {
      const perms = usePermissions()

      expect(perms.isResearcher.value).toBe(false)
    })

    it('PERM_013: hasAdminPermissions is false initially', () => {
      const perms = usePermissions()

      expect(perms.hasAdminPermissions.value).toBe(false)
    })
  })

  // ==================== fetchPermissions Tests ====================

  describe('fetchPermissions', () => {
    it('PERM_014: fetchPermissions calls correct endpoint', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view'],
            roles: [],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/permissions/my-permissions')
      )
    })

    it('PERM_015: fetchPermissions sets isLoading during request', async () => {
      let loadingDuringRequest = false

      axios.get.mockImplementation(() => {
        const perms = usePermissions()
        loadingDuringRequest = perms.isLoading.value
        return Promise.resolve({
          data: {
            success: true,
            data: { permissions: [], roles: [], username: null }
          }
        })
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(loadingDuringRequest).toBe(true)
      expect(perms.isLoading.value).toBe(false)
    })

    it('PERM_016: fetchPermissions populates permissions', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:ranking:view', 'feature:rating:view'],
            roles: [],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.permissions.value).toEqual(['feature:ranking:view', 'feature:rating:view'])
    })

    it('PERM_017: fetchPermissions populates roles', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'researcher' }, { role_name: 'viewer' }],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.roles.value).toEqual([{ role_name: 'researcher' }, { role_name: 'viewer' }])
    })

    it('PERM_018: fetchPermissions populates username', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [],
            username: 'john_doe'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.username.value).toBe('john_doe')
    })

    it('PERM_019: fetchPermissions handles API error gracefully', async () => {
      axios.get.mockRejectedValueOnce(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.permissions.value).toEqual([])
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('PERM_020: fetchPermissions clears state on 401 error', async () => {
      // First populate some data
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view'],
            roles: [{ role_name: 'admin' }],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      // Now simulate 401
      axios.get.mockRejectedValueOnce({
        response: { status: 401 }
      })

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await perms.fetchPermissions(true) // Force refresh

      expect(perms.permissions.value).toEqual([])
      expect(perms.roles.value).toEqual([])
      expect(perms.username.value).toBeNull()

      consoleSpy.mockRestore()
    })

    it('PERM_021: fetchPermissions deduplicates concurrent requests', async () => {
      axios.get.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({
              data: {
                success: true,
                data: { permissions: ['test'], roles: [], username: 'user' }
              }
            })
          }, 50)
        })
      })

      const perms = usePermissions()

      // Call multiple times concurrently
      const promise1 = perms.fetchPermissions()
      const promise2 = perms.fetchPermissions()
      const promise3 = perms.fetchPermissions()

      await Promise.all([promise1, promise2, promise3])

      // Should only call API once
      expect(axios.get).toHaveBeenCalledTimes(1)
    })

    it('PERM_022: fetchPermissions with force=true makes new request', async () => {
      axios.get.mockResolvedValue({
        data: {
          success: true,
          data: { permissions: [], roles: [], username: 'user' }
        }
      })

      const perms = usePermissions()

      await perms.fetchPermissions()
      await perms.fetchPermissions(true)

      expect(axios.get).toHaveBeenCalledTimes(2)
    })

    it('PERM_023: fetchPermissions handles response without data wrapper', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          permissions: ['direct:permission'],
          roles: [{ role_name: 'direct' }],
          username: 'directuser'
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.permissions.value).toEqual(['direct:permission'])
      expect(perms.username.value).toBe('directuser')
    })
  })

  // ==================== hasPermission Tests ====================

  describe('hasPermission', () => {
    it('PERM_024: hasPermission returns false when permission not present', () => {
      const perms = usePermissions()

      expect(perms.hasPermission('feature:test:view')).toBe(false)
    })

    it('PERM_025: hasPermission returns true when permission present', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:ranking:view', 'feature:rating:edit'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasPermission('feature:ranking:view')).toBe(true)
    })

    it('PERM_026: hasPermission is case-sensitive', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasPermission('feature:test:view')).toBe(true)
      expect(perms.hasPermission('Feature:Test:View')).toBe(false)
    })

    it('PERM_027: hasPermission checks exact match', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:ranking:view'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasPermission('feature:ranking')).toBe(false)
      expect(perms.hasPermission('feature:ranking:view:extra')).toBe(false)
    })
  })

  // ==================== hasAnyPermission Tests ====================

  describe('hasAnyPermission', () => {
    it('PERM_028: hasAnyPermission returns false when no permissions match', () => {
      const perms = usePermissions()

      expect(perms.hasAnyPermission('a', 'b', 'c')).toBe(false)
    })

    it('PERM_029: hasAnyPermission returns true when one permission matches', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:rating:view'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAnyPermission('feature:ranking:view', 'feature:rating:view')).toBe(true)
    })

    it('PERM_030: hasAnyPermission returns true when all permissions match', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['perm:a', 'perm:b', 'perm:c'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAnyPermission('perm:a', 'perm:b')).toBe(true)
    })

    it('PERM_031: hasAnyPermission works with single permission', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['single:perm'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAnyPermission('single:perm')).toBe(true)
      expect(perms.hasAnyPermission('other:perm')).toBe(false)
    })
  })

  // ==================== hasAllPermissions Tests ====================

  describe('hasAllPermissions', () => {
    it('PERM_032: hasAllPermissions returns false when no permissions', () => {
      const perms = usePermissions()

      expect(perms.hasAllPermissions('a', 'b')).toBe(false)
    })

    it('PERM_033: hasAllPermissions returns false when only some match', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['perm:a'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAllPermissions('perm:a', 'perm:b')).toBe(false)
    })

    it('PERM_034: hasAllPermissions returns true when all match', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['perm:a', 'perm:b', 'perm:c'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAllPermissions('perm:a', 'perm:b')).toBe(true)
    })

    it('PERM_035: hasAllPermissions works with single permission', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['single:perm'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAllPermissions('single:perm')).toBe(true)
    })
  })

  // ==================== hasRole Tests ====================

  describe('hasRole', () => {
    it('PERM_036: hasRole returns false when role not present', () => {
      const perms = usePermissions()

      expect(perms.hasRole('admin')).toBe(false)
    })

    it('PERM_037: hasRole returns true when role present', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'admin' }, { role_name: 'researcher' }],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasRole('admin')).toBe(true)
    })

    it('PERM_038: hasRole checks role_name property', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'viewer', id: 1 }],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasRole('viewer')).toBe(true)
      expect(perms.hasRole('1')).toBe(false)
    })
  })

  // ==================== hasAnyRole Tests ====================

  describe('hasAnyRole', () => {
    it('PERM_039: hasAnyRole returns false when no roles match', () => {
      const perms = usePermissions()

      expect(perms.hasAnyRole('admin', 'researcher')).toBe(false)
    })

    it('PERM_040: hasAnyRole returns true when one role matches', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'viewer' }],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAnyRole('admin', 'viewer')).toBe(true)
    })

    it('PERM_041: hasAnyRole works with single role', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'chatbot_manager' }],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAnyRole('chatbot_manager')).toBe(true)
    })
  })

  // ==================== clearPermissions Tests ====================

  describe('clearPermissions', () => {
    it('PERM_042: clearPermissions clears permissions', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view'],
            roles: [{ role_name: 'admin' }],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.permissions.value.length).toBeGreaterThan(0)

      perms.clearPermissions()

      expect(perms.permissions.value).toEqual([])
    })

    it('PERM_043: clearPermissions clears roles', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'admin' }],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      perms.clearPermissions()

      expect(perms.roles.value).toEqual([])
    })

    it('PERM_044: clearPermissions clears username', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [],
            username: 'testuser'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      perms.clearPermissions()

      expect(perms.username.value).toBeNull()
    })
  })

  // ==================== Computed Properties Tests ====================

  describe('Computed Properties', () => {
    it('PERM_045: isAdmin returns true when user has admin role', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'admin' }],
            username: 'admin_user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.isAdmin.value).toBe(true)
    })

    it('PERM_046: isAdmin returns false when user lacks admin role', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'researcher' }],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.isAdmin.value).toBe(false)
    })

    it('PERM_047: isResearcher returns true when user has researcher role', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [],
            roles: [{ role_name: 'researcher' }],
            username: 'researcher_user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.isResearcher.value).toBe(true)
    })

    it('PERM_048: hasAdminPermissions returns true with admin: permissions', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['admin:users:view', 'feature:test:view'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAdminPermissions.value).toBe(true)
    })

    it('PERM_049: hasAdminPermissions returns false without admin: permissions', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view', 'data:read'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      expect(perms.hasAdminPermissions.value).toBe(false)
    })
  })

  // ==================== getPermissionsByCategory Tests ====================

  describe('getPermissionsByCategory', () => {
    it('PERM_050: getPermissionsByCategory returns empty array when no match', () => {
      const perms = usePermissions()

      expect(perms.getPermissionsByCategory('feature')).toEqual([])
    })

    it('PERM_051: getPermissionsByCategory filters by category prefix', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [
              'feature:ranking:view',
              'feature:rating:edit',
              'admin:users:view',
              'data:export'
            ],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      const featurePerms = perms.getPermissionsByCategory('feature')

      expect(featurePerms).toEqual(['feature:ranking:view', 'feature:rating:edit'])
    })

    it('PERM_052: getPermissionsByCategory returns all admin permissions', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: [
              'admin:users:view',
              'admin:users:edit',
              'admin:system:manage',
              'feature:test:view'
            ],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms = usePermissions()
      await perms.fetchPermissions()

      const adminPerms = perms.getPermissionsByCategory('admin')

      expect(adminPerms).toHaveLength(3)
      expect(adminPerms).toContain('admin:users:view')
      expect(adminPerms).toContain('admin:users:edit')
      expect(adminPerms).toContain('admin:system:manage')
    })
  })

  // ==================== Shared State Tests ====================

  describe('Shared State', () => {
    it('PERM_053: multiple usePermissions instances share state', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['shared:permission'],
            roles: [{ role_name: 'shared_role' }],
            username: 'shared_user'
          }
        }
      })

      const perms1 = usePermissions()
      const perms2 = usePermissions()

      await perms1.fetchPermissions()

      // perms2 should see the same state
      expect(perms2.permissions.value).toEqual(['shared:permission'])
      expect(perms2.roles.value).toEqual([{ role_name: 'shared_role' }])
      expect(perms2.username.value).toBe('shared_user')
    })

    it('PERM_054: clearPermissions affects all instances', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['test:perm'],
            roles: [{ role_name: 'test' }],
            username: 'test'
          }
        }
      })

      const perms1 = usePermissions()
      const perms2 = usePermissions()

      await perms1.fetchPermissions()
      perms1.clearPermissions()

      expect(perms2.permissions.value).toEqual([])
      expect(perms2.roles.value).toEqual([])
    })

    it('PERM_055: hasPermission reflects shared state changes', async () => {
      axios.get.mockResolvedValueOnce({
        data: {
          success: true,
          data: {
            permissions: ['feature:test:view'],
            roles: [],
            username: 'user'
          }
        }
      })

      const perms1 = usePermissions()
      const perms2 = usePermissions()

      expect(perms2.hasPermission('feature:test:view')).toBe(false)

      await perms1.fetchPermissions()

      expect(perms2.hasPermission('feature:test:view')).toBe(true)
    })
  })
})
