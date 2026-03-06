/**
 * useResearchGroups Composable Tests
 *
 * Tests for research group CRUD, member management, and access requests.
 * Test IDs: RES_GRP_001 - RES_GRP_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

vi.mock('@/composables/useAuth', () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => 'test-token')
  }))
}))

import axios from 'axios'

describe('useResearchGroups', () => {
  let rg

  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()
    const mod = await import('@/views/ConferenceManager/composables/useResearchGroups')
    rg = mod.useResearchGroups()
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('RES_GRP_001: starts with empty myGroups', () => {
      expect(rg.myGroups.value).toEqual([])
    })

    it('RES_GRP_002: starts with empty allGroups', () => {
      expect(rg.allGroups.value).toEqual([])
    })

    it('RES_GRP_003: starts with null currentGroup', () => {
      expect(rg.currentGroup.value).toBeNull()
    })

    it('RES_GRP_004: starts with empty groupMembers', () => {
      expect(rg.groupMembers.value).toEqual([])
    })

    it('RES_GRP_005: starts not loading', () => {
      expect(rg.groupLoading.value).toBe(false)
    })
  })

  // ==================== Groups ====================

  describe('fetchMyGroups', () => {
    it('RES_GRP_006: fetches user groups', async () => {
      const groups = [{ id: 1, name: 'NLP Lab' }]
      axios.get.mockResolvedValue({ data: { groups } })

      const result = await rg.fetchMyGroups()

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/groups/my', {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual(groups)
      expect(rg.myGroups.value).toEqual(groups)
      expect(rg.groupLoading.value).toBe(false)
    })

    it('RES_GRP_007: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const result = await rg.fetchMyGroups()

      expect(result).toEqual([])
      expect(rg.groupLoading.value).toBe(false)
    })

    it('RES_GRP_008: defaults to empty array when no groups in response', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const result = await rg.fetchMyGroups()

      expect(result).toEqual([])
    })
  })

  describe('fetchAllGroups', () => {
    it('RES_GRP_009: fetches all groups with search', async () => {
      const groups = [{ id: 1, name: 'NLP' }]
      axios.get.mockResolvedValue({ data: { groups } })

      const result = await rg.fetchAllGroups('NLP')

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/groups', {
        headers: { Authorization: 'Bearer test-token' },
        params: { search: 'NLP' }
      })
      expect(result).toEqual(groups)
    })

    it('RES_GRP_010: fetches all groups without search', async () => {
      axios.get.mockResolvedValue({ data: { groups: [] } })

      await rg.fetchAllGroups()

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/groups', {
        headers: { Authorization: 'Bearer test-token' },
        params: {}
      })
    })

    it('RES_GRP_011: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await rg.fetchAllGroups()

      expect(result).toEqual([])
    })
  })

  describe('fetchGroup', () => {
    it('RES_GRP_012: fetches single group by ID', async () => {
      const group = { id: 1, name: 'NLP Lab' }
      axios.get.mockResolvedValue({ data: { group } })

      const result = await rg.fetchGroup(1)

      expect(result).toEqual(group)
      expect(rg.currentGroup.value).toEqual(group)
    })

    it('RES_GRP_013: throws on fetch failure', async () => {
      axios.get.mockRejectedValue(new Error('Not found'))

      await expect(rg.fetchGroup(999)).rejects.toThrow('Not found')
    })
  })

  describe('createGroup', () => {
    it('RES_GRP_014: creates new group', async () => {
      const newGroup = { name: 'New Lab', description: 'Research group' }
      axios.post.mockResolvedValue({ data: { group: { id: 2, ...newGroup } } })

      const result = await rg.createGroup(newGroup)

      expect(axios.post).toHaveBeenCalledWith('/api/conference-manager/groups', newGroup, {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual({ id: 2, ...newGroup })
    })
  })

  describe('updateGroup', () => {
    it('RES_GRP_015: updates existing group', async () => {
      axios.put.mockResolvedValue({ data: { group: { id: 1, name: 'Updated' } } })

      const result = await rg.updateGroup(1, { name: 'Updated' })

      expect(axios.put).toHaveBeenCalledWith('/api/conference-manager/groups/1', { name: 'Updated' }, {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual({ id: 1, name: 'Updated' })
    })
  })

  describe('deleteGroup', () => {
    it('RES_GRP_016: deletes group', async () => {
      axios.delete.mockResolvedValue({})

      await rg.deleteGroup(1)

      expect(axios.delete).toHaveBeenCalledWith('/api/conference-manager/groups/1', {
        headers: { Authorization: 'Bearer test-token' }
      })
    })
  })

  // ==================== Members ====================

  describe('fetchMembers', () => {
    it('RES_GRP_017: fetches group members', async () => {
      const members = [{ id: 1, username: 'alice' }]
      axios.get.mockResolvedValue({ data: { members } })

      const result = await rg.fetchMembers(1)

      expect(result).toEqual(members)
      expect(rg.groupMembers.value).toEqual(members)
    })

    it('RES_GRP_018: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await rg.fetchMembers(1)

      expect(result).toEqual([])
    })
  })

  describe('addMember', () => {
    it('RES_GRP_019: adds member with default role', async () => {
      axios.post.mockResolvedValue({ data: { member: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const result = await rg.addMember(1, 'user-123')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/groups/1/members',
        { user_id: 'user-123', role: 'member' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ id: 1 })
    })

    it('RES_GRP_020: adds member with custom role', async () => {
      axios.post.mockResolvedValue({ data: { member: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { members: [] } })

      await rg.addMember(1, 'user-123', 'admin')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/groups/1/members',
        { user_id: 'user-123', role: 'admin' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })
  })

  describe('updateMemberRole', () => {
    it('RES_GRP_021: updates member role', async () => {
      axios.put.mockResolvedValue({ data: { member: { id: 1, role: 'admin' } } })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const result = await rg.updateMemberRole(1, 2, 'admin')

      expect(axios.put).toHaveBeenCalledWith(
        '/api/conference-manager/groups/1/members/2',
        { role: 'admin' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ id: 1, role: 'admin' })
    })
  })

  describe('removeMember', () => {
    it('RES_GRP_022: removes member and refreshes list', async () => {
      axios.delete.mockResolvedValue({})
      axios.get.mockResolvedValue({ data: { members: [] } })

      await rg.removeMember(1, 2)

      expect(axios.delete).toHaveBeenCalledWith('/api/conference-manager/groups/1/members/2', {
        headers: { Authorization: 'Bearer test-token' }
      })
      // Should trigger fetchMembers
      expect(axios.get).toHaveBeenCalled()
    })
  })

  // ==================== Access Requests ====================

  describe('createAccessRequest', () => {
    it('RES_GRP_023: creates access request with message', async () => {
      axios.post.mockResolvedValue({ data: { request: { id: 1, status: 'pending' } } })

      const result = await rg.createAccessRequest(1, 'Please add me')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/groups/1/access-requests',
        { message: 'Please add me' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ id: 1, status: 'pending' })
    })

    it('RES_GRP_024: creates access request without message', async () => {
      axios.post.mockResolvedValue({ data: { request: { id: 1 } } })

      await rg.createAccessRequest(1)

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/groups/1/access-requests',
        {},
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })
  })

  describe('fetchPendingRequests', () => {
    it('RES_GRP_025: fetches pending requests', async () => {
      const requests = [{ id: 1, status: 'pending' }]
      axios.get.mockResolvedValue({ data: { requests } })

      const result = await rg.fetchPendingRequests()

      expect(result).toEqual(requests)
      expect(rg.pendingRequests.value).toEqual(requests)
    })

    it('RES_GRP_026: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await rg.fetchPendingRequests()

      expect(result).toEqual([])
    })
  })

  describe('fetchGroupRequests', () => {
    it('RES_GRP_027: fetches group-specific requests', async () => {
      const requests = [{ id: 1 }]
      axios.get.mockResolvedValue({ data: { requests } })

      const result = await rg.fetchGroupRequests(1)

      expect(result).toEqual(requests)
    })

    it('RES_GRP_028: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await rg.fetchGroupRequests(1)

      expect(result).toEqual([])
    })
  })

  describe('resolveAccessRequest', () => {
    it('RES_GRP_029: resolves access request', async () => {
      axios.put.mockResolvedValue({ data: { result: { status: 'approved' } } })

      const result = await rg.resolveAccessRequest(1, 'approve')

      expect(axios.put).toHaveBeenCalledWith(
        '/api/conference-manager/access-requests/1',
        { action: 'approve' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ status: 'approved' })
    })
  })
})
