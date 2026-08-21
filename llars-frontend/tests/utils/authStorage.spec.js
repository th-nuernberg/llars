/**
 * Auth Storage Utility Tests
 *
 * Tests for the auth storage layer with session/local/memory fallback chain.
 * Test IDs: UTIL_AUTH_001 - UTIL_AUTH_040
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// We need to reset modules to clear the internal memoryCache between tests
let AUTH_STORAGE_KEYS, getAuthStorageItem, setAuthStorageItem, removeAuthStorageItem, clearAuthStorage

// Create real storage mocks with internal state
const createStorageMock = () => {
  const store = {}
  return {
    getItem: vi.fn((key) => store[key] ?? null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { Object.keys(store).forEach(k => delete store[k]) }),
    _store: store
  }
}

let sessionStorageMock
let localStorageMock

describe('authStorage', () => {
  beforeEach(async () => {
    vi.resetModules()

    sessionStorageMock = createStorageMock()
    localStorageMock = createStorageMock()

    Object.defineProperty(global, 'window', {
      value: {
        sessionStorage: sessionStorageMock,
        localStorage: localStorageMock
      },
      writable: true,
      configurable: true
    })

    const mod = await import('@/utils/authStorage')
    AUTH_STORAGE_KEYS = mod.AUTH_STORAGE_KEYS
    getAuthStorageItem = mod.getAuthStorageItem
    setAuthStorageItem = mod.setAuthStorageItem
    removeAuthStorageItem = mod.removeAuthStorageItem
    clearAuthStorage = mod.clearAuthStorage
  })

  // ==================== AUTH_STORAGE_KEYS Tests ====================

  describe('AUTH_STORAGE_KEYS', () => {
    it('UTIL_AUTH_001: exports frozen AUTH_STORAGE_KEYS object', () => {
      expect(AUTH_STORAGE_KEYS).toBeDefined()
      expect(Object.isFrozen(AUTH_STORAGE_KEYS)).toBe(true)
    })

    it('UTIL_AUTH_002: contains all expected keys', () => {
      expect(AUTH_STORAGE_KEYS.token).toBe('auth_token')
      expect(AUTH_STORAGE_KEYS.refreshToken).toBe('auth_refreshToken')
      expect(AUTH_STORAGE_KEYS.idToken).toBe('auth_idToken')
      expect(AUTH_STORAGE_KEYS.roles).toBe('auth_llars_roles')
      expect(AUTH_STORAGE_KEYS.avatarSeed).toBe('auth_avatar_seed')
      expect(AUTH_STORAGE_KEYS.avatarUrl).toBe('auth_avatar_url')
      expect(AUTH_STORAGE_KEYS.collabColor).toBe('auth_collab_color')
    })
  })

  // ==================== getAuthStorageItem Tests ====================

  describe('getAuthStorageItem', () => {
    it('UTIL_AUTH_003: returns value from sessionStorage first', () => {
      sessionStorageMock._store['auth_token'] = 'session-token'
      localStorageMock._store['auth_token'] = 'local-token'

      const result = getAuthStorageItem('auth_token')
      expect(result).toBe('session-token')
    })

    it('UTIL_AUTH_004: falls back to localStorage when sessionStorage empty', () => {
      localStorageMock._store['auth_token'] = 'local-token'

      const result = getAuthStorageItem('auth_token')
      expect(result).toBe('local-token')
    })

    it('UTIL_AUTH_005: returns null when key not in any store', () => {
      const result = getAuthStorageItem('nonexistent')
      expect(result).toBeNull()
    })

    it('UTIL_AUTH_006: caches value in memory after reading from session', () => {
      sessionStorageMock._store['auth_token'] = 'session-token'
      getAuthStorageItem('auth_token')

      // Now remove from session storage and local storage
      delete sessionStorageMock._store['auth_token']

      // Should still get value from memory cache
      const result = getAuthStorageItem('auth_token')
      // Memory cache was populated, but getAuthStorageItem checks session first
      // Since session is now empty, it checks local, then memory
      expect(result).toBe('session-token')
    })

    it('UTIL_AUTH_007: caches value in memory after reading from localStorage', () => {
      localStorageMock._store['auth_token'] = 'local-token'
      getAuthStorageItem('auth_token')

      // Clear localStorage
      delete localStorageMock._store['auth_token']

      // Memory cache should return the value
      const result = getAuthStorageItem('auth_token')
      expect(result).toBe('local-token')
    })
  })

  // ==================== setAuthStorageItem Tests ====================

  describe('setAuthStorageItem', () => {
    it('UTIL_AUTH_008: stores value in sessionStorage by default', () => {
      setAuthStorageItem('auth_token', 'my-token')
      expect(sessionStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'my-token')
    })

    it('UTIL_AUTH_009: does not mirror to localStorage by default', () => {
      setAuthStorageItem('auth_token', 'my-token')
      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('UTIL_AUTH_010: mirrors to localStorage when option set', () => {
      setAuthStorageItem('auth_token', 'my-token', { mirrorToLocalStorage: true })
      expect(sessionStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'my-token')
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'my-token')
    })

    it('UTIL_AUTH_011: value is retrievable after setting', () => {
      setAuthStorageItem('auth_token', 'stored-value')
      const result = getAuthStorageItem('auth_token')
      expect(result).toBe('stored-value')
    })

    it('UTIL_AUTH_012: falls back to localStorage when sessionStorage fails', async () => {
      // Reset modules to get fresh state
      vi.resetModules()

      const failingSessionStorage = {
        getItem: vi.fn(() => null),
        setItem: vi.fn(() => { throw new Error('QuotaExceeded') }),
        removeItem: vi.fn()
      }
      const workingLocalStorage = createStorageMock()

      Object.defineProperty(global, 'window', {
        value: {
          sessionStorage: failingSessionStorage,
          localStorage: workingLocalStorage
        },
        writable: true,
        configurable: true
      })

      const mod = await import('@/utils/authStorage')
      mod.setAuthStorageItem('auth_token', 'fallback-value')
      expect(workingLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'fallback-value')
    })
  })

  // ==================== removeAuthStorageItem Tests ====================

  describe('removeAuthStorageItem', () => {
    it('UTIL_AUTH_013: removes from sessionStorage', () => {
      setAuthStorageItem('auth_token', 'value')
      removeAuthStorageItem('auth_token')
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
    })

    it('UTIL_AUTH_014: removes from localStorage', () => {
      setAuthStorageItem('auth_token', 'value', { mirrorToLocalStorage: true })
      removeAuthStorageItem('auth_token')
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
    })

    it('UTIL_AUTH_015: clears memory cache entry', () => {
      setAuthStorageItem('auth_token', 'cached-value')

      // Clear mock stores so only memory cache would have it
      delete sessionStorageMock._store['auth_token']
      delete localStorageMock._store['auth_token']

      // Remove should also clear memory cache
      removeAuthStorageItem('auth_token')

      const result = getAuthStorageItem('auth_token')
      expect(result).toBeNull()
    })

    it('UTIL_AUTH_016: handles removing non-existent key gracefully', () => {
      expect(() => removeAuthStorageItem('nonexistent')).not.toThrow()
    })
  })

  // ==================== clearAuthStorage Tests ====================

  describe('clearAuthStorage', () => {
    it('UTIL_AUTH_017: clears all known auth keys', () => {
      // Set all keys
      Object.values(AUTH_STORAGE_KEYS).forEach(key => {
        setAuthStorageItem(key, 'value')
      })

      clearAuthStorage()

      // All keys should be gone
      Object.values(AUTH_STORAGE_KEYS).forEach(key => {
        expect(getAuthStorageItem(key)).toBeNull()
      })
    })

    it('UTIL_AUTH_018: calls removeAuthStorageItem for each known key', () => {
      clearAuthStorage()

      const keyCount = Object.values(AUTH_STORAGE_KEYS).length
      // Each key should trigger sessionStorage.removeItem and localStorage.removeItem
      expect(sessionStorageMock.removeItem).toHaveBeenCalledTimes(keyCount)
      expect(localStorageMock.removeItem).toHaveBeenCalledTimes(keyCount)
    })

    it('UTIL_AUTH_019: does not affect non-auth keys in storage', () => {
      sessionStorageMock._store['other_key'] = 'other-value'
      clearAuthStorage()
      expect(sessionStorageMock._store['other_key']).toBe('other-value')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('UTIL_AUTH_020: handles storage throwing errors gracefully', async () => {
      vi.resetModules()

      const throwingStorage = {
        getItem: vi.fn(() => { throw new Error('SecurityError') }),
        setItem: vi.fn(() => { throw new Error('SecurityError') }),
        removeItem: vi.fn(() => { throw new Error('SecurityError') })
      }

      Object.defineProperty(global, 'window', {
        value: {
          sessionStorage: throwingStorage,
          localStorage: throwingStorage
        },
        writable: true,
        configurable: true
      })

      const mod = await import('@/utils/authStorage')
      // Should not throw
      expect(() => mod.getAuthStorageItem('auth_token')).not.toThrow()
      expect(() => mod.setAuthStorageItem('auth_token', 'val')).not.toThrow()
      expect(() => mod.removeAuthStorageItem('auth_token')).not.toThrow()
    })
  })
})
