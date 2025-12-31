/**
 * Tests for useKIAStatusCache composable
 *
 * Test IDs: KIA_001 - KIA_055
 *
 * Coverage:
 * - Exports and structure
 * - State initialization
 * - loadFromCache functionality
 * - saveToCache functionality
 * - clearCache functionality
 * - shouldFetch logic
 * - fetchStatus with cache
 * - fetchStatus with force refresh
 * - fetchStatus error handling
 * - updateAfterSync
 * - TTL expiration
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

// Mock sessionStorage
const mockSessionStorage = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()

Object.defineProperty(window, 'sessionStorage', {
  value: mockSessionStorage,
  writable: true
})

describe('useKIAStatusCache Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSessionStorage.clear()
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2025-01-01T12:00:00'))

    // Reset module to clear shared state
    vi.resetModules()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // Helper to get fresh composable instance
  const getComposable = async () => {
    const { useKIAStatusCache } = await import('@/composables/useKIAStatusCache')
    return useKIAStatusCache()
  }

  describe('Exports', () => {
    it('KIA_001: exports useKIAStatusCache function', async () => {
      const { useKIAStatusCache } = await import('@/composables/useKIAStatusCache')
      expect(typeof useKIAStatusCache).toBe('function')
    })

    it('KIA_002: returns all expected properties', async () => {
      const result = await getComposable()

      expect(result).toHaveProperty('pillars')
      expect(result).toHaveProperty('totalThreads')
      expect(result).toHaveProperty('gitlabConnected')
      expect(result).toHaveProperty('loading')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('state')
      expect(result).toHaveProperty('fetchStatus')
      expect(result).toHaveProperty('clearCache')
      expect(result).toHaveProperty('updateAfterSync')
      expect(result).toHaveProperty('shouldFetch')
    })

    it('KIA_003: fetchStatus is a function', async () => {
      const { fetchStatus } = await getComposable()
      expect(typeof fetchStatus).toBe('function')
    })

    it('KIA_004: clearCache is a function', async () => {
      const { clearCache } = await getComposable()
      expect(typeof clearCache).toBe('function')
    })

    it('KIA_005: updateAfterSync is a function', async () => {
      const { updateAfterSync } = await getComposable()
      expect(typeof updateAfterSync).toBe('function')
    })

    it('KIA_006: shouldFetch is a function', async () => {
      const { shouldFetch } = await getComposable()
      expect(typeof shouldFetch).toBe('function')
    })

    it('KIA_007: state is reactive object', async () => {
      const { state } = await getComposable()
      expect(typeof state).toBe('object')
      expect(state).toHaveProperty('pillars')
      expect(state).toHaveProperty('loading')
    })
  })

  describe('State Initialization', () => {
    it('KIA_008: initial pillars is empty object', async () => {
      const { state } = await getComposable()
      expect(state.pillars).toEqual({})
    })

    it('KIA_009: initial totalThreads is 0', async () => {
      const { state } = await getComposable()
      expect(state.totalThreads).toBe(0)
    })

    it('KIA_010: initial gitlabConnected is false', async () => {
      const { state } = await getComposable()
      expect(state.gitlabConnected).toBe(false)
    })

    it('KIA_011: initial loading is false', async () => {
      const { state } = await getComposable()
      expect(state.loading).toBe(false)
    })

    it('KIA_012: initial error is null', async () => {
      const { state } = await getComposable()
      expect(state.error).toBe(null)
    })

    it('KIA_013: initial lastFetched is null', async () => {
      const { state } = await getComposable()
      expect(state.lastFetched).toBe(null)
    })
  })

  describe('shouldFetch', () => {
    it('KIA_014: returns true when lastFetched is null', async () => {
      const { shouldFetch } = await getComposable()
      expect(shouldFetch()).toBe(true)
    })

    it('KIA_015: returns false when recently fetched', async () => {
      const { state, shouldFetch } = await getComposable()
      state.lastFetched = Date.now()
      expect(shouldFetch()).toBe(false)
    })

    it('KIA_016: returns true after TTL expires', async () => {
      const { state, shouldFetch } = await getComposable()
      state.lastFetched = Date.now()

      // Advance time past TTL (5 minutes)
      vi.advanceTimersByTime(5 * 60 * 1000 + 1)

      expect(shouldFetch()).toBe(true)
    })

    it('KIA_017: returns false just before TTL expires', async () => {
      const { state, shouldFetch } = await getComposable()
      state.lastFetched = Date.now()

      // Advance time to just before TTL
      vi.advanceTimersByTime(5 * 60 * 1000 - 1000)

      expect(shouldFetch()).toBe(false)
    })
  })

  describe('clearCache', () => {
    it('KIA_018: removes cache from sessionStorage', async () => {
      mockSessionStorage.setItem('kia-status-cache', '{}')
      const { clearCache } = await getComposable()

      clearCache()

      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('kia-status-cache')
    })

    it('KIA_019: sets lastFetched to null', async () => {
      const { state, clearCache } = await getComposable()
      state.lastFetched = Date.now()

      clearCache()

      expect(state.lastFetched).toBe(null)
    })
  })

  describe('fetchStatus - API Calls', () => {
    it('KIA_020: calls API with correct endpoint', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()
      await fetchStatus(true)

      // API_BASE may be set via env, so check endpoint ends correctly
      expect(axios.get).toHaveBeenCalledWith(expect.stringContaining('/api/judge/kia/status'))
    })

    it('KIA_021: sets loading to true during request', async () => {
      let loadingDuringRequest = false
      axios.get.mockImplementation(() => {
        return new Promise(resolve => {
          // Defer to allow state check
          setTimeout(() => resolve({
            data: { pillars: {}, total_threads: 0, gitlab_connected: false }
          }), 10)
        })
      })

      const { state, fetchStatus } = await getComposable()
      const promise = fetchStatus(true)

      // Loading should be true while request is in flight
      loadingDuringRequest = state.loading

      vi.advanceTimersByTime(20)
      await promise

      expect(loadingDuringRequest).toBe(true)
    })

    it('KIA_022: sets loading to false after successful request', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.loading).toBe(false)
    })

    it('KIA_023: updates state with API response', async () => {
      const mockPillars = { pillar1: { synced: 5 }, pillar2: { synced: 3 } }
      axios.get.mockResolvedValueOnce({
        data: { pillars: mockPillars, total_threads: 42, gitlab_connected: true }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.pillars).toEqual(mockPillars)
      expect(state.totalThreads).toBe(42)
      expect(state.gitlabConnected).toBe(true)
    })

    it('KIA_024: sets lastFetched after successful request', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.lastFetched).toBe(Date.now())
    })

    it('KIA_025: returns fromCache: false on API call', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 10, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()
      const result = await fetchStatus(true)

      expect(result.fromCache).toBe(false)
      expect(result.data).toBeDefined()
    })

    it('KIA_026: saves to cache after successful request', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: { p1: {} }, total_threads: 5, gitlab_connected: true }
      })

      const { fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'kia-status-cache',
        expect.stringContaining('pillars')
      )
    })
  })

  describe('fetchStatus - Cache Behavior', () => {
    it('KIA_027: returns fromCache: true when cache is valid', async () => {
      const cachedData = {
        pillars: { cached: true },
        totalThreads: 100,
        gitlabConnected: true,
        timestamp: Date.now()
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(cachedData))

      const { fetchStatus } = await getComposable()
      const result = await fetchStatus()

      expect(result.fromCache).toBe(true)
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('KIA_028: loads state from cache', async () => {
      const cachedData = {
        pillars: { pillar1: { synced: 10 } },
        totalThreads: 25,
        gitlabConnected: true,
        timestamp: Date.now()
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(cachedData))

      const { state, fetchStatus } = await getComposable()
      await fetchStatus()

      expect(state.pillars).toEqual(cachedData.pillars)
      expect(state.totalThreads).toBe(25)
      expect(state.gitlabConnected).toBe(true)
    })

    it('KIA_029: ignores expired cache', async () => {
      const expiredCache = {
        pillars: { old: true },
        totalThreads: 1,
        gitlabConnected: false,
        timestamp: Date.now() - (6 * 60 * 1000) // 6 minutes ago
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(expiredCache))
      axios.get.mockResolvedValueOnce({
        data: { pillars: { new: true }, total_threads: 50, gitlab_connected: true }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus()

      expect(axios.get).toHaveBeenCalled()
      expect(state.pillars).toEqual({ new: true })
    })

    it('KIA_030: force=true bypasses cache', async () => {
      const cachedData = {
        pillars: { cached: true },
        totalThreads: 100,
        timestamp: Date.now()
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(cachedData))
      axios.get.mockResolvedValueOnce({
        data: { pillars: { fresh: true }, total_threads: 200, gitlab_connected: false }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(axios.get).toHaveBeenCalled()
      expect(state.pillars).toEqual({ fresh: true })
    })

    it('KIA_031: returns cached data when shouldFetch is false', async () => {
      const { state, fetchStatus } = await getComposable()
      state.lastFetched = Date.now()
      state.pillars = { existing: true }

      const result = await fetchStatus()

      expect(result.fromCache).toBe(true)
      expect(axios.get).not.toHaveBeenCalled()
    })
  })

  describe('fetchStatus - Error Handling', () => {
    it('KIA_032: sets error on API failure', async () => {
      axios.get.mockRejectedValueOnce({
        response: { data: { error: 'Server error' }, status: 500 }
      })

      const { state, fetchStatus } = await getComposable()

      await expect(fetchStatus(true)).rejects.toBeDefined()
      expect(state.error).toBe('Server error')
    })

    it('KIA_033: sets loading to false after error', async () => {
      axios.get.mockRejectedValueOnce(new Error('Network error'))

      const { state, fetchStatus } = await getComposable()

      try {
        await fetchStatus(true)
      } catch (e) {
        // expected
      }

      expect(state.loading).toBe(false)
    })

    it('KIA_034: preserves existing data on error', async () => {
      const { state, fetchStatus } = await getComposable()
      state.pillars = { preserved: true }
      state.totalThreads = 999

      axios.get.mockRejectedValueOnce(new Error('Network error'))

      try {
        await fetchStatus(true)
      } catch (e) {
        // expected
      }

      expect(state.pillars).toEqual({ preserved: true })
      expect(state.totalThreads).toBe(999)
    })

    it('KIA_035: uses error.message as fallback', async () => {
      axios.get.mockRejectedValueOnce(new Error('Connection refused'))

      const { state, fetchStatus } = await getComposable()

      try {
        await fetchStatus(true)
      } catch (e) {
        // expected
      }

      expect(state.error).toBe('Connection refused')
    })

    it('KIA_036: throws error for caller to handle', async () => {
      const error = new Error('API error')
      axios.get.mockRejectedValueOnce(error)

      const { fetchStatus } = await getComposable()

      await expect(fetchStatus(true)).rejects.toThrow('API error')
    })
  })

  describe('updateAfterSync', () => {
    it('KIA_037: updates pillars', async () => {
      const { state, updateAfterSync } = await getComposable()
      const newPillars = { p1: { synced: 10 }, p2: { synced: 20 } }

      updateAfterSync(newPillars, 30)

      expect(state.pillars).toEqual(newPillars)
    })

    it('KIA_038: updates totalThreads', async () => {
      const { state, updateAfterSync } = await getComposable()

      updateAfterSync({}, 150)

      expect(state.totalThreads).toBe(150)
    })

    it('KIA_039: sets lastFetched to current time', async () => {
      const { state, updateAfterSync } = await getComposable()

      updateAfterSync({}, 0)

      expect(state.lastFetched).toBe(Date.now())
    })

    it('KIA_040: saves to cache', async () => {
      const { updateAfterSync } = await getComposable()

      updateAfterSync({ test: true }, 42)

      expect(mockSessionStorage.setItem).toHaveBeenCalledWith(
        'kia-status-cache',
        expect.stringContaining('test')
      )
    })
  })

  describe('Cache Serialization', () => {
    it('KIA_041: handles invalid JSON in cache gracefully', async () => {
      mockSessionStorage.getItem.mockReturnValueOnce('invalid json {{{')
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()
      const result = await fetchStatus()

      // Should fall back to API call
      expect(axios.get).toHaveBeenCalled()
    })

    it('KIA_042: handles missing timestamp in cache', async () => {
      const cacheWithoutTimestamp = {
        pillars: { test: true },
        totalThreads: 5
        // no timestamp
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(cacheWithoutTimestamp))
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()
      await fetchStatus()

      // Should treat as expired and fetch
      expect(axios.get).toHaveBeenCalled()
    })

    it('KIA_043: handles sessionStorage.setItem error', async () => {
      mockSessionStorage.setItem.mockImplementationOnce(() => {
        throw new Error('QuotaExceeded')
      })
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()

      // Should not throw, just warn
      await expect(fetchStatus(true)).resolves.toBeDefined()
    })

    it('KIA_044: handles sessionStorage.getItem error', async () => {
      mockSessionStorage.getItem.mockImplementationOnce(() => {
        throw new Error('Storage error')
      })
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      const { fetchStatus } = await getComposable()
      await fetchStatus()

      // Should fall back to API call
      expect(axios.get).toHaveBeenCalled()
    })
  })

  describe('Default Values', () => {
    it('KIA_045: handles missing pillars in response', async () => {
      axios.get.mockResolvedValueOnce({
        data: { total_threads: 10, gitlab_connected: true }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.pillars).toEqual({})
    })

    it('KIA_046: handles missing total_threads in response', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, gitlab_connected: true }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.totalThreads).toBe(0)
    })

    it('KIA_047: handles missing gitlab_connected in response', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 5 }
      })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.gitlabConnected).toBe(false)
    })

    it('KIA_048: handles missing pillars in cache', async () => {
      const cacheWithoutPillars = {
        totalThreads: 10,
        gitlabConnected: true,
        timestamp: Date.now()
      }
      mockSessionStorage.getItem.mockReturnValueOnce(JSON.stringify(cacheWithoutPillars))

      const { state, fetchStatus } = await getComposable()
      await fetchStatus()

      expect(state.pillars).toEqual({})
    })
  })

  describe('Edge Cases', () => {
    it('KIA_049: handles empty response data', async () => {
      axios.get.mockResolvedValueOnce({ data: {} })

      const { state, fetchStatus } = await getComposable()
      await fetchStatus(true)

      expect(state.pillars).toEqual({})
      expect(state.totalThreads).toBe(0)
      expect(state.gitlabConnected).toBe(false)
    })

    it('KIA_050: clears error on successful fetch', async () => {
      const { state, fetchStatus } = await getComposable()
      state.error = 'Previous error'

      axios.get.mockResolvedValueOnce({
        data: { pillars: {}, total_threads: 0, gitlab_connected: false }
      })

      await fetchStatus(true)

      expect(state.error).toBe(null)
    })

    it('KIA_051: multiple instances share state', async () => {
      axios.get.mockResolvedValueOnce({
        data: { pillars: { shared: true }, total_threads: 42, gitlab_connected: true }
      })

      const instance1 = await getComposable()
      await instance1.fetchStatus(true)

      // Get another instance without resetting modules
      const { useKIAStatusCache } = await import('@/composables/useKIAStatusCache')
      const instance2 = useKIAStatusCache()

      expect(instance2.state.pillars).toEqual({ shared: true })
      expect(instance2.state.totalThreads).toBe(42)
    })

    it('KIA_052: 401 error does not log to console', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      axios.get.mockRejectedValueOnce({
        response: { data: { error: 'Unauthorized' }, status: 401 }
      })

      const { fetchStatus } = await getComposable()

      try {
        await fetchStatus(true)
      } catch (e) {
        // expected
      }

      expect(consoleSpy).not.toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('KIA_053: non-401 errors log to console', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      axios.get.mockRejectedValueOnce({
        response: { data: { error: 'Server error' }, status: 500 }
      })

      const { fetchStatus } = await getComposable()

      try {
        await fetchStatus(true)
      } catch (e) {
        // expected
      }

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('KIA_054: cache key is correct', async () => {
      const { clearCache } = await getComposable()
      clearCache()

      expect(mockSessionStorage.removeItem).toHaveBeenCalledWith('kia-status-cache')
    })

    it('KIA_055: TTL is 5 minutes', async () => {
      const { state, shouldFetch } = await getComposable()
      state.lastFetched = Date.now()

      // Just under 5 minutes - should not fetch
      vi.advanceTimersByTime(4 * 60 * 1000 + 59 * 1000)
      expect(shouldFetch()).toBe(false)

      // Exactly 5 minutes - should fetch
      vi.advanceTimersByTime(1000)
      expect(shouldFetch()).toBe(true)
    })
  })
})
