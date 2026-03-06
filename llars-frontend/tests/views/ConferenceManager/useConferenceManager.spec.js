/**
 * useConferenceManager Composable Tests
 *
 * Tests for conference, paper, series, submission CRUD operations,
 * group scoping, LaTeX access, and stats fetching.
 * Test IDs: CONF_MGR_001 - CONF_MGR_040
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

vi.mock('@/composables/useAuth', () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => 'test-token')
  }))
}))

import axios from 'axios'

describe('useConferenceManager', () => {
  let cm

  beforeEach(async () => {
    vi.clearAllMocks()
    // Reset module-level shared state
    vi.resetModules()
    const mod = await import('@/views/ConferenceManager/composables/useConferenceManager')
    cm = mod.useConferenceManager()
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('CONF_MGR_001: starts with empty conferences', () => {
      expect(cm.conferences.value).toEqual([])
    })

    it('CONF_MGR_002: starts with empty papers', () => {
      expect(cm.papers.value).toEqual([])
    })

    it('CONF_MGR_003: starts with empty series', () => {
      expect(cm.series.value).toEqual([])
    })

    it('CONF_MGR_004: starts with null stats', () => {
      expect(cm.stats.value).toBeNull()
    })

    it('CONF_MGR_005: starts not loading', () => {
      expect(cm.loading.value).toBe(false)
    })

    it('CONF_MGR_006: starts with no error', () => {
      expect(cm.error.value).toBeNull()
    })

    it('CONF_MGR_007: starts with null activeGroupId', () => {
      expect(cm.activeGroupId.value).toBeNull()
    })
  })

  // ==================== Group Scoping ====================

  describe('setGroupId', () => {
    it('CONF_MGR_008: sets group ID as number', () => {
      cm.setGroupId('42')
      expect(cm.activeGroupId.value).toBe(42)
    })

    it('CONF_MGR_009: sets null when given falsy value', () => {
      cm.setGroupId('42')
      cm.setGroupId(null)
      expect(cm.activeGroupId.value).toBeNull()
    })

    it('CONF_MGR_010: sets null when given empty string', () => {
      cm.setGroupId('')
      expect(cm.activeGroupId.value).toBeNull()
    })
  })

  // ==================== Conferences ====================

  describe('fetchConferences', () => {
    it('CONF_MGR_011: fetches conferences and updates state', async () => {
      const mockConfs = [{ id: 1, name: 'IJCAI' }]
      axios.get.mockResolvedValue({ data: { conferences: mockConfs } })

      const result = await cm.fetchConferences()

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/conferences', {
        headers: { Authorization: 'Bearer test-token' },
        params: {}
      })
      expect(result).toEqual(mockConfs)
      expect(cm.conferences.value).toEqual(mockConfs)
      expect(cm.loading.value).toBe(false)
    })

    it('CONF_MGR_012: passes filters to request', async () => {
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      await cm.fetchConferences({ year: 2025, core_ranking: 'A*', search: 'AI' })

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/conferences', {
        headers: { Authorization: 'Bearer test-token' },
        params: { year: 2025, core_ranking: 'A*', search: 'AI' }
      })
    })

    it('CONF_MGR_013: includes group_id when activeGroupId is set', async () => {
      cm.setGroupId(5)
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      await cm.fetchConferences()

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/conferences', {
        headers: { Authorization: 'Bearer test-token' },
        params: { group_id: 5 }
      })
    })

    it('CONF_MGR_014: sets error on failure', async () => {
      axios.get.mockRejectedValue({ response: { data: { error: 'Unauthorized' } } })

      await expect(cm.fetchConferences()).rejects.toBeDefined()
      expect(cm.error.value).toBe('Unauthorized')
      expect(cm.loading.value).toBe(false)
    })

    it('CONF_MGR_015: defaults to empty array when response has no conferences', async () => {
      axios.get.mockResolvedValue({ data: {} })

      await cm.fetchConferences()
      expect(cm.conferences.value).toEqual([])
    })
  })

  describe('getConference', () => {
    it('CONF_MGR_016: fetches single conference by id', async () => {
      const mockConf = { id: 1, name: 'IJCAI' }
      axios.get.mockResolvedValue({ data: { conference: mockConf } })

      const result = await cm.getConference(1)

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/conferences/1', {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual(mockConf)
    })
  })

  describe('createConference', () => {
    it('CONF_MGR_017: creates conference and refreshes list', async () => {
      const newConf = { name: 'NeurIPS' }
      axios.post.mockResolvedValue({ data: { conference: { id: 2, ...newConf } } })
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      const result = await cm.createConference(newConf)

      expect(axios.post).toHaveBeenCalledWith('/api/conference-manager/conferences', newConf, {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual({ id: 2, ...newConf })
    })

    it('CONF_MGR_018: includes group_id in payload when set', async () => {
      cm.setGroupId(3)
      axios.post.mockResolvedValue({ data: { conference: { id: 2, name: 'Test' } } })
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      await cm.createConference({ name: 'Test' })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/conferences',
        { name: 'Test', group_id: 3 },
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })
  })

  describe('updateConference', () => {
    it('CONF_MGR_019: updates conference and refreshes list', async () => {
      axios.put.mockResolvedValue({ data: { conference: { id: 1, name: 'Updated' } } })
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      const result = await cm.updateConference(1, { name: 'Updated' })

      expect(axios.put).toHaveBeenCalledWith('/api/conference-manager/conferences/1', { name: 'Updated' }, {
        headers: { Authorization: 'Bearer test-token' }
      })
      expect(result).toEqual({ id: 1, name: 'Updated' })
    })
  })

  describe('deleteConference', () => {
    it('CONF_MGR_020: deletes conference and refreshes list', async () => {
      axios.delete.mockResolvedValue({})
      axios.get.mockResolvedValue({ data: { conferences: [] } })

      await cm.deleteConference(1)

      expect(axios.delete).toHaveBeenCalledWith('/api/conference-manager/conferences/1', {
        headers: { Authorization: 'Bearer test-token' }
      })
    })
  })

  // ==================== Papers ====================

  describe('fetchPapers', () => {
    it('CONF_MGR_021: fetches papers with filters', async () => {
      const mockPapers = [{ id: 1, title: 'AI Paper' }]
      axios.get.mockResolvedValue({ data: { papers: mockPapers, access: {} } })

      const result = await cm.fetchPapers({ status: 'accepted', conference_id: 1 })

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/papers', {
        headers: { Authorization: 'Bearer test-token' },
        params: { status: 'accepted', conference_id: 1 }
      })
      expect(result).toEqual(mockPapers)
      expect(cm.papers.value).toEqual(mockPapers)
    })

    it('CONF_MGR_022: sets error on paper fetch failure', async () => {
      axios.get.mockRejectedValue({ response: { data: { error: 'Not found' } } })

      await expect(cm.fetchPapers()).rejects.toBeDefined()
      expect(cm.error.value).toBe('Not found')
    })
  })

  describe('createPaper', () => {
    it('CONF_MGR_023: creates paper and refreshes list', async () => {
      axios.post.mockResolvedValue({ data: { paper: { id: 1, title: 'New Paper' } } })
      axios.get.mockResolvedValue({ data: { papers: [], access: {} } })

      const result = await cm.createPaper({ title: 'New Paper' })

      expect(result).toEqual({ id: 1, title: 'New Paper' })
    })
  })

  describe('updatePaperStatus', () => {
    it('CONF_MGR_024: patches paper status', async () => {
      axios.patch.mockResolvedValue({ data: { paper: { id: 1, status: 'accepted' } } })
      axios.get.mockResolvedValue({ data: { papers: [], access: {} } })

      const result = await cm.updatePaperStatus(1, 'accepted')

      expect(axios.patch).toHaveBeenCalledWith(
        '/api/conference-manager/papers/1/status',
        { status: 'accepted' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ id: 1, status: 'accepted' })
    })
  })

  describe('setPaperAuthors', () => {
    it('CONF_MGR_025: sets paper authors', async () => {
      const authors = ['Alice', 'Bob']
      axios.put.mockResolvedValue({ data: { authors } })

      const result = await cm.setPaperAuthors(1, authors)

      expect(axios.put).toHaveBeenCalledWith(
        '/api/conference-manager/papers/1/authors',
        { authors },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual(authors)
    })
  })

  // ==================== Submissions ====================

  describe('submissions', () => {
    it('CONF_MGR_026: adds submission to paper', async () => {
      axios.post.mockResolvedValue({ data: { paper: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { papers: [], access: {} } })

      const result = await cm.addSubmission(1, { venue: 'IJCAI' })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/conference-manager/papers/1/submissions',
        { venue: 'IJCAI' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ id: 1 })
    })

    it('CONF_MGR_027: updates submission', async () => {
      axios.put.mockResolvedValue({ data: { paper: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { papers: [], access: {} } })

      await cm.updateSubmission(1, 2, { status: 'accepted' })

      expect(axios.put).toHaveBeenCalledWith(
        '/api/conference-manager/papers/1/submissions/2',
        { status: 'accepted' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })

    it('CONF_MGR_028: deletes submission', async () => {
      axios.delete.mockResolvedValue({ data: { paper: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { papers: [], access: {} } })

      await cm.deleteSubmission(1, 2)

      expect(axios.delete).toHaveBeenCalledWith(
        '/api/conference-manager/papers/1/submissions/2',
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })
  })

  // ==================== Series ====================

  describe('series', () => {
    it('CONF_MGR_029: fetches series list', async () => {
      const mockSeries = [{ id: 1, acronym: 'IJCAI' }]
      axios.get.mockResolvedValue({ data: { series: mockSeries } })

      const result = await cm.fetchSeries('IJCAI')

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/series', {
        headers: { Authorization: 'Bearer test-token' },
        params: { search: 'IJCAI' }
      })
      expect(result).toEqual(mockSeries)
    })

    it('CONF_MGR_030: creates series', async () => {
      axios.post.mockResolvedValue({ data: { series: { id: 1, acronym: 'NEW' } } })
      axios.get.mockResolvedValue({ data: { series: [] } })

      const result = await cm.createSeries({ acronym: 'NEW' })

      expect(result).toEqual({ id: 1, acronym: 'NEW' })
    })

    it('CONF_MGR_031: finds series by acronym', async () => {
      axios.get.mockResolvedValue({ data: { series: { id: 1 } } })

      const result = await cm.findSeriesByAcronym('IJCAI')

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/series/find-by-acronym', {
        headers: { Authorization: 'Bearer test-token' },
        params: { acronym: 'IJCAI' }
      })
      expect(result).toEqual({ id: 1 })
    })

    it('CONF_MGR_032: gets new edition defaults', async () => {
      axios.get.mockResolvedValue({ data: { defaults: { year: 2026 } } })

      const result = await cm.getNewEditionDefaults(1)

      expect(result).toEqual({ year: 2026 })
    })
  })

  // ==================== LaTeX Access ====================

  describe('LaTeX access', () => {
    it('CONF_MGR_033: checks LaTeX access and updates map', async () => {
      const accessData = { ws_1: 'member', ws_2: 'pending' }
      axios.get.mockResolvedValue({ data: { access: accessData } })

      await cm.checkLatexAccess()

      expect(cm.latexAccessMap.value).toEqual(accessData)
    })

    it('CONF_MGR_034: requests LaTeX access', async () => {
      axios.post.mockResolvedValue({ data: { request: { id: 1 } } })
      axios.get.mockResolvedValue({ data: { access: {} } })

      const result = await cm.requestLatexAccess('ws_1', 'Please grant access')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/latex-collab/workspaces/ws_1/access-requests',
        { message: 'Please grant access' },
        { headers: { Authorization: 'Bearer test-token' } }
      )
      expect(result).toEqual({ request: { id: 1 } })
    })

    it('CONF_MGR_035: requests LaTeX access without message', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { access: {} } })

      await cm.requestLatexAccess('ws_1')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/latex-collab/workspaces/ws_1/access-requests',
        {},
        { headers: { Authorization: 'Bearer test-token' } }
      )
    })
  })

  // ==================== Stats ====================

  describe('fetchStats', () => {
    it('CONF_MGR_036: fetches stats', async () => {
      const mockStats = { total_papers: 10, total_conferences: 5 }
      axios.get.mockResolvedValue({ data: { stats: mockStats } })

      const result = await cm.fetchStats()

      expect(result).toEqual(mockStats)
      expect(cm.stats.value).toEqual(mockStats)
    })

    it('CONF_MGR_037: includes group_id in stats request', async () => {
      cm.setGroupId(3)
      axios.get.mockResolvedValue({ data: { stats: {} } })

      await cm.fetchStats()

      expect(axios.get).toHaveBeenCalledWith('/api/conference-manager/stats', {
        headers: { Authorization: 'Bearer test-token' },
        params: { group_id: 3 }
      })
    })
  })
})
