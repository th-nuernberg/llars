/**
 * useCollabMembers Composable Tests
 *
 * Tests for workspace member/sharing management.
 * Test IDs: COLLAB_001 - COLLAB_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, computed } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key) => key)
  }))
}))

// Mock authStorage
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: { token: 'llars_token' },
  getAuthStorageItem: vi.fn(() => 'test-token')
}))

import axios from 'axios'

let useCollabMembers

describe('useCollabMembers', () => {
  const defaultOptions = () => ({
    workspaceId: ref(1),
    workspace: ref({ owner_username: 'owner' }),
    hasPermission: vi.fn(() => true),
    currentUsername: ref('owner'),
    isAdmin: ref(false),
    apiPrefix: '/api/latex-collab',
    permissionKey: 'feature:latex_collab:share',
    i18nPrefix: 'latexCollab'
  })

  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    const module = await import('@/composables/useCollabMembers')
    useCollabMembers = module.useCollabMembers
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('COLLAB_001: returns all expected state properties', () => {
      const result = useCollabMembers(defaultOptions())
      expect(result).toHaveProperty('shareDialog')
      expect(result).toHaveProperty('members')
      expect(result).toHaveProperty('membersLoading')
      expect(result).toHaveProperty('shareError')
      expect(result).toHaveProperty('removingUsername')
      expect(result).toHaveProperty('selectedUser')
      expect(result).toHaveProperty('userSearchRef')
      expect(result).toHaveProperty('ownerInfo')
    })

    it('COLLAB_002: returns computed properties', () => {
      const result = useCollabMembers(defaultOptions())
      expect(result).toHaveProperty('canShareWorkspace')
      expect(result).toHaveProperty('excludedUsernames')
    })

    it('COLLAB_003: returns all methods', () => {
      const result = useCollabMembers(defaultOptions())
      expect(typeof result.loadMembers).toBe('function')
      expect(typeof result.openShareDialog).toBe('function')
      expect(typeof result.inviteMember).toBe('function')
      expect(typeof result.removeMember).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('COLLAB_004: shareDialog starts closed', () => {
      const { shareDialog } = useCollabMembers(defaultOptions())
      expect(shareDialog.value).toBe(false)
    })

    it('COLLAB_005: members starts empty', () => {
      const { members } = useCollabMembers(defaultOptions())
      expect(members.value).toEqual([])
    })

    it('COLLAB_006: shareError starts empty', () => {
      const { shareError } = useCollabMembers(defaultOptions())
      expect(shareError.value).toBe('')
    })

    it('COLLAB_007: removingUsername starts empty', () => {
      const { removingUsername } = useCollabMembers(defaultOptions())
      expect(removingUsername.value).toBe('')
    })

    it('COLLAB_008: selectedUser starts null', () => {
      const { selectedUser } = useCollabMembers(defaultOptions())
      expect(selectedUser.value).toBeNull()
    })

    it('COLLAB_009: ownerInfo starts with empty values', () => {
      const { ownerInfo } = useCollabMembers(defaultOptions())
      expect(ownerInfo.value.username).toBe('')
      expect(ownerInfo.value.avatar_url).toBeNull()
    })
  })

  // ==================== Computed ====================

  describe('Computed Properties', () => {
    it('COLLAB_010: canShareWorkspace true for owner with permission', () => {
      const { canShareWorkspace } = useCollabMembers(defaultOptions())
      expect(canShareWorkspace.value).toBe(true)
    })

    it('COLLAB_011: canShareWorkspace true for admin', () => {
      const opts = defaultOptions()
      opts.isAdmin = ref(true)
      opts.currentUsername = ref('admin')
      const { canShareWorkspace } = useCollabMembers(opts)
      expect(canShareWorkspace.value).toBe(true)
    })

    it('COLLAB_012: canShareWorkspace false without permission', () => {
      const opts = defaultOptions()
      opts.hasPermission = vi.fn(() => false)
      const { canShareWorkspace } = useCollabMembers(opts)
      expect(canShareWorkspace.value).toBe(false)
    })

    it('COLLAB_013: canShareWorkspace false for non-owner, non-admin', () => {
      const opts = defaultOptions()
      opts.currentUsername = ref('other')
      opts.isAdmin = ref(false)
      const { canShareWorkspace } = useCollabMembers(opts)
      expect(canShareWorkspace.value).toBe(false)
    })

    it('COLLAB_014: canShareWorkspace false when no workspace', () => {
      const opts = defaultOptions()
      opts.workspace = ref(null)
      const { canShareWorkspace } = useCollabMembers(opts)
      expect(canShareWorkspace.value).toBe(false)
    })

    it('COLLAB_015: excludedUsernames includes owner', () => {
      const { excludedUsernames } = useCollabMembers(defaultOptions())
      expect(excludedUsernames.value).toContain('owner')
    })

    it('COLLAB_016: excludedUsernames includes existing members', () => {
      const { excludedUsernames, members } = useCollabMembers(defaultOptions())
      members.value = [{ username: 'member1' }, { username: 'member2' }]
      expect(excludedUsernames.value).toContain('member1')
      expect(excludedUsernames.value).toContain('member2')
    })
  })

  // ==================== loadMembers ====================

  describe('loadMembers', () => {
    it('COLLAB_017: loads members from API', async () => {
      axios.get.mockResolvedValue({
        data: {
          members: [{ username: 'member1' }],
          owner: { username: 'owner', avatar_url: null, avatar_seed: 'seed', collab_color: '#ff0000' }
        }
      })

      const { loadMembers, members, ownerInfo } = useCollabMembers(defaultOptions())
      await loadMembers()

      expect(members.value).toHaveLength(1)
      expect(ownerInfo.value.username).toBe('owner')
      expect(ownerInfo.value.collab_color).toBe('#ff0000')
    })

    it('COLLAB_018: skips when no workspaceId', async () => {
      const opts = defaultOptions()
      opts.workspaceId = ref(null)
      const { loadMembers } = useCollabMembers(opts)
      await loadMembers()
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('COLLAB_019: handles load error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const { loadMembers, members, shareError } = useCollabMembers(defaultOptions())
      await loadMembers()

      expect(members.value).toEqual([])
      expect(shareError.value).toBe('Not found')
    })

    it('COLLAB_020: sets loading state', async () => {
      let resolvePromise
      axios.get.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { loadMembers, membersLoading } = useCollabMembers(defaultOptions())
      const promise = loadMembers()
      expect(membersLoading.value).toBe(true)

      resolvePromise({ data: { members: [] } })
      await promise
      expect(membersLoading.value).toBe(false)
    })

    it('COLLAB_021: uses correct API prefix', async () => {
      axios.get.mockResolvedValue({ data: { members: [] } })

      const opts = defaultOptions()
      opts.apiPrefix = '/api/markdown-collab'
      const { loadMembers } = useCollabMembers(opts)
      await loadMembers()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/markdown-collab/workspaces/1/members'),
        expect.any(Object)
      )
    })
  })

  // ==================== openShareDialog ====================

  describe('openShareDialog', () => {
    it('COLLAB_022: opens dialog and triggers load', () => {
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { openShareDialog, shareDialog, selectedUser } = useCollabMembers(defaultOptions())
      openShareDialog()

      expect(shareDialog.value).toBe(true)
      expect(selectedUser.value).toBeNull()
      expect(axios.get).toHaveBeenCalled()
    })
  })

  // ==================== inviteMember ====================

  describe('inviteMember', () => {
    it('COLLAB_023: invites user via API', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [{ username: 'newuser' }] } })

      const { inviteMember, selectedUser } = useCollabMembers(defaultOptions())
      selectedUser.value = { username: 'newuser' }
      await inviteMember()

      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/workspaces/1/members'),
        { username: 'newuser' },
        expect.any(Object)
      )
    })

    it('COLLAB_024: invites via user argument', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { inviteMember } = useCollabMembers(defaultOptions())
      await inviteMember({ username: 'directuser' })

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        { username: 'directuser' },
        expect.any(Object)
      )
    })

    it('COLLAB_025: does nothing without username', async () => {
      const { inviteMember } = useCollabMembers(defaultOptions())
      await inviteMember()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('COLLAB_026: clears selectedUser after invite', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { inviteMember, selectedUser } = useCollabMembers(defaultOptions())
      selectedUser.value = { username: 'user1' }
      await inviteMember()

      expect(selectedUser.value).toBeNull()
    })

    it('COLLAB_027: handles invite error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'User not found' } }
      })

      const { inviteMember, shareError } = useCollabMembers(defaultOptions())
      await inviteMember({ username: 'unknown' })

      expect(shareError.value).toBe('User not found')
    })

    it('COLLAB_028: reloads members after successful invite', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [{ username: 'member1' }] } })

      const { inviteMember, members } = useCollabMembers(defaultOptions())
      await inviteMember({ username: 'member1' })

      expect(axios.get).toHaveBeenCalled()
    })
  })

  // ==================== removeMember ====================

  describe('removeMember', () => {
    it('COLLAB_029: removes member via API', async () => {
      axios.delete.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { removeMember } = useCollabMembers(defaultOptions())
      await removeMember('member1')

      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringContaining('/workspaces/1/members/member1'),
        expect.any(Object)
      )
    })

    it('COLLAB_030: does nothing without username', async () => {
      const { removeMember } = useCollabMembers(defaultOptions())
      await removeMember(null)
      expect(axios.delete).not.toHaveBeenCalled()
    })

    it('COLLAB_031: sets removingUsername during operation', async () => {
      let resolvePromise
      axios.delete.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { removeMember, removingUsername } = useCollabMembers(defaultOptions())
      const promise = removeMember('user1')
      expect(removingUsername.value).toBe('user1')

      resolvePromise({ data: {} })
      // Mock loadMembers
      axios.get.mockResolvedValue({ data: { members: [] } })
      await promise
      expect(removingUsername.value).toBe('')
    })

    it('COLLAB_032: handles remove error', async () => {
      axios.delete.mockRejectedValue({
        response: { data: { error: 'Cannot remove owner' } }
      })

      const { removeMember, shareError } = useCollabMembers(defaultOptions())
      await removeMember('owner')

      expect(shareError.value).toBe('Cannot remove owner')
    })

    it('COLLAB_033: reloads members after removal', async () => {
      axios.delete.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { removeMember } = useCollabMembers(defaultOptions())
      await removeMember('member1')

      expect(axios.get).toHaveBeenCalled()
    })

    it('COLLAB_034: encodes username in URL', async () => {
      axios.delete.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { members: [] } })

      const { removeMember } = useCollabMembers(defaultOptions())
      await removeMember('user name')

      expect(axios.delete).toHaveBeenCalledWith(
        expect.stringContaining('user%20name'),
        expect.any(Object)
      )
    })
  })

  // ==================== Configuration ====================

  describe('Configuration', () => {
    it('COLLAB_035: uses custom apiPrefix', async () => {
      axios.get.mockResolvedValue({ data: { members: [] } })

      const opts = defaultOptions()
      opts.apiPrefix = '/api/markdown-collab'
      const { loadMembers } = useCollabMembers(opts)
      await loadMembers()

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/markdown-collab'),
        expect.any(Object)
      )
    })
  })
})
