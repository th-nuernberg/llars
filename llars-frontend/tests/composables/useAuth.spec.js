/**
 * useAuth Composable Tests
 *
 * Tests for the LLARS authentication composable.
 * Test IDs: AUTH_001 - AUTH_060
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock matomo plugin
vi.mock('@/plugins/llars-metrics', () => ({
  matomoSetUserId: vi.fn(),
  matomoResetUserId: vi.fn()
}))

// Mock usePermissions composable
vi.mock('@/composables/usePermissions', () => ({
  usePermissions: vi.fn(() => ({
    clearPermissions: vi.fn(),
    fetchPermissions: vi.fn().mockResolvedValue({})
  }))
}))

// Mock authStorage
const mockStorage = {}
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: {
    token: 'llars_token',
    refreshToken: 'llars_refresh_token',
    idToken: 'llars_id_token',
    roles: 'llars_roles',
    avatarSeed: 'llars_avatar_seed',
    avatarUrl: 'llars_avatar_url',
    collabColor: 'llars_collab_color'
  },
  getAuthStorageItem: vi.fn((key) => mockStorage[key] || null),
  setAuthStorageItem: vi.fn((key, value) => { mockStorage[key] = value }),
  removeAuthStorageItem: vi.fn((key) => { delete mockStorage[key] }),
  clearAuthStorage: vi.fn(() => { Object.keys(mockStorage).forEach(k => delete mockStorage[k]) })
}))

// Mock jwt utility
vi.mock('@/utils/jwt', () => ({
  decodeJwtPayload: vi.fn((token) => {
    if (!token) return null
    // Return mock payload based on token
    if (token === 'valid_token') {
      return {
        sub: 'user123',
        preferred_username: 'testuser',
        groups: ['researcher'],
        exp: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
      }
    }
    if (token === 'admin_token') {
      return {
        sub: 'admin123',
        preferred_username: 'admin',
        groups: ['admin', 'researcher'],
        exp: Math.floor(Date.now() / 1000) + 3600
      }
    }
    if (token === 'expired_token') {
      return {
        sub: 'user123',
        preferred_username: 'testuser',
        groups: [],
        exp: Math.floor(Date.now() / 1000) - 3600 // 1 hour ago
      }
    }
    if (token === 'no_exp_token') {
      return {
        sub: 'user123',
        preferred_username: 'testuser',
        groups: []
        // No exp field
      }
    }
    return null
  })
}))

// Import after mocks are set up
import axios from 'axios'
import { matomoSetUserId, matomoResetUserId } from '@/plugins/llars-metrics'
import { usePermissions } from '@/composables/usePermissions'
import { getAuthStorageItem, setAuthStorageItem, clearAuthStorage } from '@/utils/authStorage'
import { decodeJwtPayload } from '@/utils/jwt'

// We need to reset modules to get fresh state for each test
let useAuth

describe('useAuth Composable', () => {
  beforeEach(async () => {
    // Clear all mocks
    vi.clearAllMocks()

    // Clear mock storage
    Object.keys(mockStorage).forEach(k => delete mockStorage[k])

    // Reset module to get fresh state
    vi.resetModules()

    // Re-import to get fresh state
    const module = await import('@/composables/useAuth')
    useAuth = module.useAuth
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Basic State Tests ====================

  describe('Initial State', () => {
    it('AUTH_001: exports useAuth function', () => {
      expect(typeof useAuth).toBe('function')
    })

    it('AUTH_002: returns all expected properties', () => {
      const auth = useAuth()

      expect(auth).toHaveProperty('isAuthenticated')
      expect(auth).toHaveProperty('userRoles')
      expect(auth).toHaveProperty('isAdmin')
      expect(auth).toHaveProperty('tokenParsed')
      expect(auth).toHaveProperty('avatarSeed')
      expect(auth).toHaveProperty('avatarUrl')
      expect(auth).toHaveProperty('avatarChangesLeft')
      expect(auth).toHaveProperty('collabColor')
      expect(auth).toHaveProperty('login')
      expect(auth).toHaveProperty('logout')
      expect(auth).toHaveProperty('getToken')
      expect(auth).toHaveProperty('isTokenExpired')
      expect(auth).toHaveProperty('fetchUserProfile')
      expect(auth).toHaveProperty('fetchUserSettings')
      expect(auth).toHaveProperty('updateCollabColor')
      expect(auth).toHaveProperty('uploadAvatar')
      expect(auth).toHaveProperty('regenerateAvatar')
      expect(auth).toHaveProperty('resetAvatar')
    })

    it('AUTH_003: isAuthenticated is computed property', () => {
      const auth = useAuth()

      expect(auth.isAuthenticated).toBeDefined()
      expect(typeof auth.isAuthenticated.value).toBe('boolean')
    })

    it('AUTH_004: isAuthenticated is false initially', () => {
      const auth = useAuth()

      expect(auth.isAuthenticated.value).toBe(false)
    })

    it('AUTH_005: userRoles is empty initially', () => {
      const auth = useAuth()

      expect(auth.userRoles.value).toEqual([])
    })

    it('AUTH_006: isAdmin is false initially', () => {
      const auth = useAuth()

      expect(auth.isAdmin.value).toBe(false)
    })

    it('AUTH_007: getToken returns null initially', () => {
      const auth = useAuth()

      expect(auth.getToken()).toBeNull()
    })
  })

  // ==================== Login Tests ====================

  describe('Login', () => {
    it('AUTH_008: login function returns object with success property', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['researcher']
        }
      })

      const auth = useAuth()
      const result = await auth.login('testuser', 'password')

      expect(result).toHaveProperty('success')
    })

    it('AUTH_009: successful login sets isAuthenticated to true', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['researcher']
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.isAuthenticated.value).toBe(true)
    })

    it('AUTH_010: successful login stores token', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['researcher']
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.getToken()).toBe('valid_token')
    })

    it('AUTH_011: successful login stores roles', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['researcher', 'evaluator']
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.userRoles.value).toEqual(['researcher', 'evaluator'])
    })

    it('AUTH_012: login with admin role sets isAdmin to true', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'admin_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['admin', 'researcher']
        }
      })

      const auth = useAuth()
      await auth.login('admin', 'password')

      expect(auth.isAdmin.value).toBe(true)
    })

    it('AUTH_013: login calls axios with correct endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/authentik/login'),
        { username: 'testuser', password: 'password' },
        expect.objectContaining({
          headers: { 'Content-Type': 'application/json' }
        })
      )
    })

    it('AUTH_014: login stores tokens in storage', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          id_token: 'id_123',
          llars_roles: ['researcher']
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(setAuthStorageItem).toHaveBeenCalledWith('llars_token', 'valid_token')
      expect(setAuthStorageItem).toHaveBeenCalledWith('llars_refresh_token', 'refresh_123')
      expect(setAuthStorageItem).toHaveBeenCalledWith('llars_id_token', 'id_123')
    })

    it('AUTH_015: login calls matomoSetUserId', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(matomoSetUserId).toHaveBeenCalledWith('testuser')
    })

    it('AUTH_016: login fetches user profile', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          avatar_seed: 'seed123',
          avatar_url: null,
          avatar_changes_left: 3
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/auth/authentik/me'),
        expect.any(Object)
      )
    })

    it('AUTH_017: failed login returns error message', async () => {
      axios.post.mockRejectedValueOnce({
        response: {
          status: 401,
          statusText: 'Unauthorized'
        }
      })

      const auth = useAuth()
      const result = await auth.login('testuser', 'wrong_password')

      expect(result.success).toBe(false)
      expect(result.error).toBeDefined()
    })

    it('AUTH_018: 401 error returns invalid credentials message', async () => {
      axios.post.mockRejectedValueOnce({
        response: {
          status: 401,
          statusText: 'Unauthorized'
        }
      })

      const auth = useAuth()
      const result = await auth.login('testuser', 'wrong')

      expect(result.success).toBe(false)
      expect(result.error).toContain('Benutzername oder Passwort')
    })

    it('AUTH_019: 400 error returns bad request message', async () => {
      axios.post.mockRejectedValueOnce({
        response: {
          status: 400,
          statusText: 'Bad Request'
        }
      })

      const auth = useAuth()
      const result = await auth.login('', '')

      expect(result.success).toBe(false)
      expect(result.error).toContain('Fehlerhafte Anfrage')
    })

    it('AUTH_020: network error returns connection message', async () => {
      axios.post.mockRejectedValueOnce({
        request: {}
      })

      const auth = useAuth()
      const result = await auth.login('testuser', 'password')

      expect(result.success).toBe(false)
      expect(result.error).toContain('Keine Verbindung')
    })

    it('AUTH_021: login clears and refreshes permissions', async () => {
      const mockClearPermissions = vi.fn()
      const mockFetchPermissions = vi.fn().mockResolvedValue({})
      vi.mocked(usePermissions).mockReturnValue({
        clearPermissions: mockClearPermissions,
        fetchPermissions: mockFetchPermissions
      })

      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(mockClearPermissions).toHaveBeenCalled()
      expect(mockFetchPermissions).toHaveBeenCalledWith(true)
    })
  })

  // ==================== Logout Tests ====================

  describe('Logout', () => {
    it('AUTH_022: logout clears authentication state', async () => {
      // First login
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: ['researcher']
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      expect(auth.isAuthenticated.value).toBe(true)

      // Then logout
      auth.logout()

      expect(auth.isAuthenticated.value).toBe(false)
    })

    it('AUTH_023: logout clears token', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      auth.logout()

      expect(auth.getToken()).toBeNull()
    })

    it('AUTH_024: logout clears roles', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: ['researcher']
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      auth.logout()

      expect(auth.userRoles.value).toEqual([])
    })

    it('AUTH_025: logout clears storage', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      auth.logout()

      expect(clearAuthStorage).toHaveBeenCalled()
    })

    it('AUTH_026: logout calls matomoResetUserId', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      auth.logout()

      expect(matomoResetUserId).toHaveBeenCalled()
    })

    it('AUTH_027: logout clears avatar data', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          avatar_seed: 'seed123',
          avatar_url: '/api/avatar/123',
          collab_color: '#ff0000'
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      auth.logout()

      expect(auth.avatarSeed.value).toBeNull()
      expect(auth.avatarUrl.value).toBeNull()
      expect(auth.collabColor.value).toBeNull()
    })
  })

  // ==================== Token Expiration Tests ====================

  describe('Token Expiration', () => {
    it('AUTH_028: isTokenExpired returns true for expired token', () => {
      const auth = useAuth()

      expect(auth.isTokenExpired('expired_token')).toBe(true)
    })

    it('AUTH_029: isTokenExpired returns false for valid token', () => {
      const auth = useAuth()

      expect(auth.isTokenExpired('valid_token')).toBe(false)
    })

    it('AUTH_030: isTokenExpired returns false for token without exp', () => {
      const auth = useAuth()

      expect(auth.isTokenExpired('no_exp_token')).toBe(false)
    })

    it('AUTH_031: isAuthenticated returns false for expired token', async () => {
      // Manually set an expired token scenario
      mockStorage['llars_token'] = 'expired_token'

      // Re-import to trigger loadTokensFromStorage
      vi.resetModules()
      const module = await import('@/composables/useAuth')
      const auth = module.useAuth()

      expect(auth.isAuthenticated.value).toBe(false)
    })
  })

  // ==================== User Profile Tests ====================

  describe('User Profile', () => {
    it('AUTH_032: fetchUserProfile returns null without token', async () => {
      const auth = useAuth()
      const result = await auth.fetchUserProfile()

      expect(result).toBeNull()
    })

    it('AUTH_033: fetchUserProfile calls correct endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          avatar_seed: 'seed123',
          avatar_url: null,
          avatar_changes_left: 3
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      // Clear the calls from login
      vi.clearAllMocks()

      await auth.fetchUserProfile()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/auth/authentik/me'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer valid_token' }
        })
      )
    })

    it('AUTH_034: fetchUserProfile updates avatarSeed', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          avatar_seed: 'new_seed_456',
          avatar_url: null,
          avatar_changes_left: 3
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.avatarSeed.value).toBe('new_seed_456')
    })

    it('AUTH_035: fetchUserProfile updates avatarUrl', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          avatar_seed: 'seed',
          avatar_url: '/api/users/avatar/abc123',
          avatar_changes_left: 2
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.avatarUrl.value).toBe('/api/users/avatar/abc123')
    })

    it('AUTH_036: fetchUserProfile handles API error gracefully', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockRejectedValue(new Error('Network error'))

      const auth = useAuth()

      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await auth.login('testuser', 'password')

      // Should not throw, just log error
      expect(auth.avatarSeed.value).toBeNull()

      consoleSpy.mockRestore()
    })
  })

  // ==================== User Settings Tests ====================

  describe('User Settings', () => {
    it('AUTH_037: fetchUserSettings returns null without token', async () => {
      const auth = useAuth()
      const result = await auth.fetchUserSettings()

      expect(result).toBeNull()
    })

    it('AUTH_038: fetchUserSettings calls correct endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          collab_color: '#ff0000',
          avatar_seed: 'seed123'
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      vi.clearAllMocks()
      await auth.fetchUserSettings()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/users/me/settings'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer valid_token' }
        })
      )
    })

    it('AUTH_039: fetchUserSettings updates collabColor', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: {
          collab_color: '#00ff00',
          avatar_seed: 'seed'
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      await auth.fetchUserSettings()

      expect(auth.collabColor.value).toBe('#00ff00')
    })

    it('AUTH_040: updateCollabColor returns false without token', async () => {
      const auth = useAuth()
      const result = await auth.updateCollabColor('#ff0000')

      expect(result).toBe(false)
    })

    it('AUTH_041: updateCollabColor calls correct endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.patch.mockResolvedValueOnce({
        data: { success: true, collab_color: '#0000ff' }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      vi.clearAllMocks()
      await auth.updateCollabColor('#0000ff')

      expect(axios.patch).toHaveBeenCalledWith(
        expect.stringContaining('/api/users/me/settings'),
        { collab_color: '#0000ff' },
        expect.objectContaining({
          headers: { Authorization: 'Bearer valid_token' }
        })
      )
    })

    it('AUTH_042: updateCollabColor returns true on success', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.patch.mockResolvedValueOnce({
        data: { success: true, collab_color: '#0000ff' }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      const result = await auth.updateCollabColor('#0000ff')

      expect(result).toBe(true)
    })

    it('AUTH_043: updateCollabColor updates collabColor ref', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.patch.mockResolvedValueOnce({
        data: { success: true, collab_color: '#ff00ff' }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      await auth.updateCollabColor('#ff00ff')

      expect(auth.collabColor.value).toBe('#ff00ff')
    })
  })

  // ==================== Avatar Management Tests ====================

  describe('Avatar Management', () => {
    it('AUTH_044: uploadAvatar returns failure without token', async () => {
      const auth = useAuth()
      const result = await auth.uploadAvatar(new File([''], 'test.png'))

      expect(result.success).toBe(false)
    })

    it('AUTH_045: uploadAvatar returns failure without file', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      const result = await auth.uploadAvatar(null)

      expect(result.success).toBe(false)
    })

    it('AUTH_046: uploadAvatar sends FormData', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.post.mockResolvedValueOnce({
        data: {
          success: true,
          avatar_url: '/api/users/avatar/new123',
          avatar_changes_left: 2
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      vi.clearAllMocks()
      const file = new File(['test'], 'avatar.png', { type: 'image/png' })
      await auth.uploadAvatar(file)

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/users/me/avatar'),
        expect.any(FormData),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'multipart/form-data'
          })
        })
      )
    })

    it('AUTH_047: regenerateAvatar returns failure without token', async () => {
      const auth = useAuth()
      const result = await auth.regenerateAvatar()

      expect(result.success).toBe(false)
    })

    it('AUTH_048: regenerateAvatar calls PATCH endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.patch.mockResolvedValueOnce({
        data: {
          success: true,
          avatar_seed: 'new_random_seed',
          avatar_changes_left: 1
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      vi.clearAllMocks()
      await auth.regenerateAvatar()

      expect(axios.patch).toHaveBeenCalledWith(
        expect.stringContaining('/api/users/me/avatar'),
        {},
        expect.any(Object)
      )
    })

    it('AUTH_049: regenerateAvatar updates avatarSeed', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: { avatar_seed: 'old_seed' } })
      axios.patch.mockResolvedValueOnce({
        data: {
          success: true,
          avatar_seed: 'regenerated_seed',
          avatar_changes_left: 0
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      await auth.regenerateAvatar()

      expect(auth.avatarSeed.value).toBe('regenerated_seed')
    })

    it('AUTH_050: resetAvatar returns failure without token', async () => {
      const auth = useAuth()
      const result = await auth.resetAvatar()

      expect(result.success).toBe(false)
    })

    it('AUTH_051: resetAvatar calls DELETE endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })
      axios.delete.mockResolvedValueOnce({
        data: {
          success: true,
          avatar_seed: 'default_seed',
          avatar_url: null
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      vi.clearAllMocks()
      await auth.resetAvatar()

      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringContaining('/api/users/me/avatar'),
        expect.any(Object)
      )
    })

    it('AUTH_052: resetAvatar clears avatarUrl', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({
        data: { avatar_url: '/api/users/avatar/old' }
      })
      axios.delete.mockResolvedValueOnce({
        data: {
          success: true,
          avatar_seed: 'default',
          avatar_url: null
        }
      })

      const auth = useAuth()
      await auth.login('testuser', 'password')
      await auth.resetAvatar()

      expect(auth.avatarUrl.value).toBeNull()
    })
  })

  // ==================== Computed Properties Tests ====================

  describe('Computed Properties', () => {
    it('AUTH_053: userRoles falls back to token groups when llarsRoles empty', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: [] // Empty LLARS roles
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      // Should fall back to token's groups
      expect(auth.userRoles.value).toEqual(['researcher'])
    })

    it('AUTH_054: userRoles prefers llarsRoles over token groups', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token', // Token has groups: ['researcher']
          refresh_token: 'refresh_123',
          llars_roles: ['admin', 'chatbot_manager'] // Different roles
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.userRoles.value).toEqual(['admin', 'chatbot_manager'])
    })

    it('AUTH_055: isAdmin checks userRoles for admin', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: ['researcher', 'evaluator'] // No admin
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.isAdmin.value).toBe(false)
    })

    it('AUTH_056: tokenParsed contains decoded JWT payload', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          access_token: 'valid_token',
          refresh_token: 'refresh_123',
          llars_roles: []
        }
      })
      axios.get.mockResolvedValue({ data: {} })

      const auth = useAuth()
      await auth.login('testuser', 'password')

      expect(auth.tokenParsed.value).toMatchObject({
        sub: 'user123',
        preferred_username: 'testuser'
      })
    })
  })

  // ==================== Storage Loading Tests ====================

  describe('Storage Loading', () => {
    it('AUTH_057: loads token from storage on init', async () => {
      mockStorage['llars_token'] = 'valid_token'
      mockStorage['llars_roles'] = JSON.stringify(['researcher'])

      vi.resetModules()
      const module = await import('@/composables/useAuth')
      const auth = module.useAuth()

      expect(auth.getToken()).toBe('valid_token')
    })

    it('AUTH_058: loads roles from storage on init', async () => {
      mockStorage['llars_token'] = 'valid_token'
      mockStorage['llars_roles'] = JSON.stringify(['admin', 'researcher'])

      vi.resetModules()
      const module = await import('@/composables/useAuth')
      const auth = module.useAuth()

      expect(auth.userRoles.value).toEqual(['admin', 'researcher'])
    })

    it('AUTH_059: clears state when stored token is expired', async () => {
      mockStorage['llars_token'] = 'expired_token'
      mockStorage['llars_roles'] = JSON.stringify(['researcher'])

      vi.resetModules()
      const module = await import('@/composables/useAuth')
      const auth = module.useAuth()

      expect(auth.isAuthenticated.value).toBe(false)
      expect(auth.getToken()).toBeNull()
    })

    it('AUTH_060: handles invalid JSON in stored roles gracefully', async () => {
      mockStorage['llars_token'] = 'no_exp_token' // Token with empty groups
      mockStorage['llars_roles'] = 'invalid json {'

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      vi.resetModules()
      const module = await import('@/composables/useAuth')
      const auth = module.useAuth()

      // When JSON parsing fails, llarsRoles becomes [], which falls back to token groups
      // no_exp_token has empty groups, so userRoles should be []
      expect(auth.userRoles.value).toEqual([])
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })
  })
})
