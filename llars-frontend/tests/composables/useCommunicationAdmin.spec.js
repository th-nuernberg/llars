/**
 * useCommunicationAdmin Composable Tests
 *
 * Tests for communication feature toggle and admin management.
 * Test IDs: COMM_ADM_001 - COMM_ADM_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn()
  }
}))

// Mock usePermissions
const mockFetchPermissions = vi.fn()
vi.mock('@/composables/usePermissions', () => ({
  usePermissions: vi.fn(() => ({
    fetchPermissions: mockFetchPermissions
  }))
}))

import axios from 'axios'

let useCommunicationAdmin

describe('useCommunicationAdmin', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    const module = await import('@/composables/useCommunicationAdmin')
    useCommunicationAdmin = module.useCommunicationAdmin
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('COMM_ADM_001: returns all expected properties', () => {
      const result = useCommunicationAdmin()
      expect(result).toHaveProperty('communicationEnabled')
      expect(result).toHaveProperty('loaded')
      expect(result).toHaveProperty('loading')
      expect(typeof result.fetchCommunicationStatus).toBe('function')
      expect(typeof result.refreshCommunicationStatus).toBe('function')
      expect(typeof result.attachSocketListeners).toBe('function')
      expect(typeof result.fetchUsers).toBe('function')
      expect(typeof result.setUserPermissions).toBe('function')
      expect(typeof result.bulkSetPermissions).toBe('function')
      expect(typeof result.fetchStats).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('COMM_ADM_002: communicationEnabled starts false', () => {
      const { communicationEnabled } = useCommunicationAdmin()
      expect(communicationEnabled.value).toBe(false)
    })

    it('COMM_ADM_003: loaded starts false', () => {
      const { loaded } = useCommunicationAdmin()
      expect(loaded.value).toBe(false)
    })

    it('COMM_ADM_004: loading starts false', () => {
      const { loading } = useCommunicationAdmin()
      expect(loading.value).toBe(false)
    })
  })

  // ==================== fetchCommunicationStatus ====================

  describe('fetchCommunicationStatus', () => {
    it('COMM_ADM_005: fetches status from API', async () => {
      axios.get.mockResolvedValue({
        data: { communication_enabled: true }
      })

      const { fetchCommunicationStatus, communicationEnabled, loaded } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      expect(communicationEnabled.value).toBe(true)
      expect(loaded.value).toBe(true)
      expect(axios.get).toHaveBeenCalledWith('/api/system/communication-status')
    })

    it('COMM_ADM_006: caches result after first call', async () => {
      axios.get.mockResolvedValue({
        data: { communication_enabled: true }
      })

      const { fetchCommunicationStatus } = useCommunicationAdmin()
      await fetchCommunicationStatus()
      await fetchCommunicationStatus()

      expect(axios.get).toHaveBeenCalledTimes(1)
    })

    it('COMM_ADM_007: handles API error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const { fetchCommunicationStatus, communicationEnabled } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      expect(communicationEnabled.value).toBe(false)
    })

    it('COMM_ADM_008: sets loading during fetch', async () => {
      let resolvePromise
      axios.get.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { fetchCommunicationStatus, loading } = useCommunicationAdmin()
      const promise = fetchCommunicationStatus()
      expect(loading.value).toBe(true)

      resolvePromise({ data: { communication_enabled: false } })
      await promise
      expect(loading.value).toBe(false)
    })

    it('COMM_ADM_009: defaults to false when communication_enabled missing', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const { fetchCommunicationStatus, communicationEnabled } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      expect(communicationEnabled.value).toBe(false)
    })
  })

  // ==================== refreshCommunicationStatus ====================

  describe('refreshCommunicationStatus', () => {
    it('COMM_ADM_010: refreshes status without cache', async () => {
      axios.get.mockResolvedValue({
        data: { communication_enabled: true }
      })

      const { fetchCommunicationStatus, refreshCommunicationStatus } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      axios.get.mockResolvedValue({
        data: { communication_enabled: false }
      })
      await refreshCommunicationStatus()

      expect(axios.get).toHaveBeenCalledTimes(2)
    })

    it('COMM_ADM_011: updates communicationEnabled on refresh', async () => {
      axios.get.mockResolvedValueOnce({
        data: { communication_enabled: true }
      })

      const { fetchCommunicationStatus, refreshCommunicationStatus, communicationEnabled } = useCommunicationAdmin()
      await fetchCommunicationStatus()
      expect(communicationEnabled.value).toBe(true)

      axios.get.mockResolvedValueOnce({
        data: { communication_enabled: false }
      })
      await refreshCommunicationStatus()
      expect(communicationEnabled.value).toBe(false)
    })

    it('COMM_ADM_012: keeps current value on refresh error', async () => {
      axios.get.mockResolvedValueOnce({
        data: { communication_enabled: true }
      })

      const { fetchCommunicationStatus, refreshCommunicationStatus, communicationEnabled } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      axios.get.mockRejectedValueOnce(new Error('Error'))
      await refreshCommunicationStatus()

      expect(communicationEnabled.value).toBe(true)
    })
  })

  // ==================== Socket Listeners ====================

  describe('attachSocketListeners', () => {
    it('COMM_ADM_013: attaches socket listeners', () => {
      const mockSocket = {
        on: vi.fn()
      }

      const { attachSocketListeners } = useCommunicationAdmin()
      attachSocketListeners(mockSocket)

      expect(mockSocket.on).toHaveBeenCalledWith(
        'communication:status_changed',
        expect.any(Function)
      )
      expect(mockSocket.on).toHaveBeenCalledWith(
        'communication:permissions_changed',
        expect.any(Function)
      )
    })

    it('COMM_ADM_014: does nothing with null socket', () => {
      const { attachSocketListeners } = useCommunicationAdmin()
      // Should not throw
      attachSocketListeners(null)
    })

    it('COMM_ADM_015: only attaches once', () => {
      const mockSocket = { on: vi.fn() }

      const { attachSocketListeners } = useCommunicationAdmin()
      attachSocketListeners(mockSocket)
      attachSocketListeners(mockSocket)

      // Should be called exactly twice (2 events x 1 attachment)
      expect(mockSocket.on).toHaveBeenCalledTimes(2)
    })

    it('COMM_ADM_016: status_changed event updates state', () => {
      const handlers = {}
      const mockSocket = {
        on: vi.fn((event, handler) => { handlers[event] = handler })
      }

      const { attachSocketListeners, communicationEnabled } = useCommunicationAdmin()
      attachSocketListeners(mockSocket)

      handlers['communication:status_changed']({ communication_enabled: true })
      expect(communicationEnabled.value).toBe(true)

      handlers['communication:status_changed']({ communication_enabled: false })
      expect(communicationEnabled.value).toBe(false)
    })

    it('COMM_ADM_017: permissions_changed event triggers permission refresh', () => {
      const handlers = {}
      const mockSocket = {
        on: vi.fn((event, handler) => { handlers[event] = handler })
      }

      const { attachSocketListeners } = useCommunicationAdmin()
      attachSocketListeners(mockSocket)

      handlers['communication:permissions_changed']()
      expect(mockFetchPermissions).toHaveBeenCalledWith(true)
    })
  })

  // ==================== Admin API Methods ====================

  describe('fetchUsers', () => {
    it('COMM_ADM_018: fetches users list', async () => {
      axios.get.mockResolvedValue({
        data: { users: [{ username: 'user1' }, { username: 'user2' }] }
      })

      const { fetchUsers } = useCommunicationAdmin()
      const result = await fetchUsers()

      expect(result).toHaveLength(2)
      expect(axios.get).toHaveBeenCalledWith('/api/admin/communication/users')
    })

    it('COMM_ADM_019: returns empty array when no users', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const { fetchUsers } = useCommunicationAdmin()
      const result = await fetchUsers()

      expect(result).toEqual([])
    })
  })

  describe('setUserPermissions', () => {
    it('COMM_ADM_020: sets permissions for user', async () => {
      axios.put.mockResolvedValue({
        data: { success: true }
      })

      const { setUserPermissions } = useCommunicationAdmin()
      const result = await setUserPermissions('user1', { can_chat: true, can_call: false })

      expect(result.success).toBe(true)
      expect(axios.put).toHaveBeenCalledWith(
        '/api/admin/communication/users/user1',
        { permissions: { can_chat: true, can_call: false } }
      )
    })
  })

  describe('bulkSetPermissions', () => {
    it('COMM_ADM_021: sets permissions for multiple users', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, updated: 3 }
      })

      const { bulkSetPermissions } = useCommunicationAdmin()
      const result = await bulkSetPermissions(
        ['user1', 'user2', 'user3'],
        { can_chat: true }
      )

      expect(result.updated).toBe(3)
      expect(axios.post).toHaveBeenCalledWith(
        '/api/admin/communication/users/bulk',
        {
          usernames: ['user1', 'user2', 'user3'],
          permissions: { can_chat: true }
        }
      )
    })
  })

  describe('fetchStats', () => {
    it('COMM_ADM_022: fetches communication stats', async () => {
      axios.get.mockResolvedValue({
        data: { total_users: 50, active_chats: 10 }
      })

      const { fetchStats } = useCommunicationAdmin()
      const result = await fetchStats()

      expect(result.total_users).toBe(50)
      expect(axios.get).toHaveBeenCalledWith('/api/admin/communication/stats')
    })
  })

  // ==================== Singleton Behavior ====================

  describe('Singleton State', () => {
    it('COMM_ADM_023: shares state between instances', async () => {
      axios.get.mockResolvedValue({
        data: { communication_enabled: true }
      })

      const instance1 = useCommunicationAdmin()
      await instance1.fetchCommunicationStatus()

      const instance2 = useCommunicationAdmin()
      expect(instance2.communicationEnabled.value).toBe(true)
      expect(instance2.loaded.value).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMM_ADM_024: status_changed with falsy data', () => {
      const handlers = {}
      const mockSocket = {
        on: vi.fn((event, handler) => { handlers[event] = handler })
      }

      const { attachSocketListeners, communicationEnabled } = useCommunicationAdmin()
      attachSocketListeners(mockSocket)

      handlers['communication:status_changed']({})
      expect(communicationEnabled.value).toBe(false)
    })

    it('COMM_ADM_025: loading resets after error', async () => {
      axios.get.mockRejectedValue(new Error('Error'))

      const { fetchCommunicationStatus, loading } = useCommunicationAdmin()
      await fetchCommunicationStatus()

      expect(loading.value).toBe(false)
    })
  })
})
