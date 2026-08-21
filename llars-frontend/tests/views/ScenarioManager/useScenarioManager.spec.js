/**
 * useScenarioManager Composable Tests
 *
 * Tests for scenario CRUD operations, team management, and data loading.
 * Test IDs: SCEN_MGR_001 - SCEN_MGR_050
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

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
    getToken: vi.fn(() => 'test-token'),
    tokenParsed: { value: { sub: 'user-123' } }
  }))
}))

import axios from 'axios'
import { useScenarioManager } from '@/views/ScenarioManager/composables/useScenarioManager'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function expectAuthHeader(call) {
  const config = call[call.length - 1]
  expect(config.headers || config).toEqual(
    expect.objectContaining({ Authorization: 'Bearer test-token' })
  )
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useScenarioManager', () => {
  let manager

  beforeEach(() => {
    vi.clearAllMocks()
    // Reset shared state by getting a fresh instance and clearing scenarios
    manager = useScenarioManager()
    manager.scenarios.value = []
    manager.currentScenario.value = null
    manager.loading.value = false
    manager.error.value = null
  })

  // =========================================================================
  // Initial State
  // =========================================================================

  describe('initial state', () => {
    it('SCEN_MGR_001: has empty scenarios and null current', () => {
      expect(manager.scenarios.value).toEqual([])
      expect(manager.currentScenario.value).toBeNull()
    })

    it('SCEN_MGR_002: loading and error are false/null', () => {
      expect(manager.loading.value).toBe(false)
      expect(manager.error.value).toBeNull()
    })

    it('SCEN_MGR_003: currentUserId is derived from token', () => {
      expect(manager.currentUserId.value).toBe('user-123')
    })
  })

  // =========================================================================
  // fetchScenarios
  // =========================================================================

  describe('fetchScenarios', () => {
    it('SCEN_MGR_004: fetches scenarios and populates state', async () => {
      const mockScenarios = [
        { id: 1, name: 'Scenario A' },
        { id: 2, name: 'Scenario B' }
      ]
      axios.get.mockResolvedValueOnce({ data: { scenarios: mockScenarios } })

      const result = await manager.fetchScenarios()

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios', expect.objectContaining({
        headers: { Authorization: 'Bearer test-token' },
        params: { include_stats: 'true' }
      }))
      expect(manager.scenarios.value).toEqual(mockScenarios)
      expect(result).toEqual(mockScenarios)
    })

    it('SCEN_MGR_005: passes filter parameter when provided', async () => {
      axios.get.mockResolvedValueOnce({ data: { scenarios: [] } })

      await manager.fetchScenarios('owned')

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios', expect.objectContaining({
        params: { filter: 'owned', include_stats: 'true' }
      }))
    })

    it('SCEN_MGR_006: passes include_stats=false when disabled', async () => {
      axios.get.mockResolvedValueOnce({ data: { scenarios: [] } })

      await manager.fetchScenarios(null, false)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios', expect.objectContaining({
        params: { include_stats: 'false' }
      }))
    })

    it('SCEN_MGR_007: sets error on failure', async () => {
      axios.get.mockRejectedValueOnce({ response: { data: { error: 'Forbidden' } } })

      await expect(manager.fetchScenarios()).rejects.toBeDefined()
      expect(manager.error.value).toBe('Forbidden')
      expect(manager.loading.value).toBe(false)
    })

    it('SCEN_MGR_008: handles missing scenarios key in response', async () => {
      axios.get.mockResolvedValueOnce({ data: {} })

      await manager.fetchScenarios()

      expect(manager.scenarios.value).toEqual([])
    })

    it('SCEN_MGR_009: sets loading during request', async () => {
      let resolvePromise
      axios.get.mockReturnValueOnce(new Promise(resolve => {
        resolvePromise = resolve
      }))

      const promise = manager.fetchScenarios()
      expect(manager.loading.value).toBe(true)

      resolvePromise({ data: { scenarios: [] } })
      await promise

      expect(manager.loading.value).toBe(false)
    })
  })

  // =========================================================================
  // fetchScenario (single)
  // =========================================================================

  describe('fetchScenario', () => {
    it('SCEN_MGR_010: fetches and sets currentScenario', async () => {
      const mockScenario = { id: 42, name: 'Test Scenario', config: {} }
      axios.get.mockResolvedValueOnce({ data: mockScenario })

      const result = await manager.fetchScenario(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42', expect.objectContaining({
        headers: { Authorization: 'Bearer test-token' }
      }))
      expect(manager.currentScenario.value).toEqual(mockScenario)
      expect(result).toEqual(mockScenario)
    })

    it('SCEN_MGR_011: sets error on failure', async () => {
      axios.get.mockRejectedValueOnce({ response: { data: { error: 'Not found' } } })

      await expect(manager.fetchScenario(999)).rejects.toBeDefined()
      expect(manager.error.value).toBe('Not found')
    })
  })

  // =========================================================================
  // createNewScenario
  // =========================================================================

  describe('createNewScenario', () => {
    it('SCEN_MGR_012: creates scenario and adds to list', async () => {
      const newScenario = { id: 10, name: 'New Scenario' }
      axios.post.mockResolvedValueOnce({ data: { scenario: newScenario } })

      const result = await manager.createNewScenario({ name: 'New Scenario' })

      expect(axios.post).toHaveBeenCalledWith('/api/scenarios', { name: 'New Scenario' }, expect.any(Object))
      expect(result).toEqual(newScenario)
      expect(manager.scenarios.value[0]).toEqual(newScenario)
    })

    it('SCEN_MGR_013: adds new scenario at the beginning of list', async () => {
      manager.scenarios.value = [{ id: 1 }, { id: 2 }]
      axios.post.mockResolvedValueOnce({ data: { scenario: { id: 10, name: 'New' } } })

      await manager.createNewScenario({ name: 'New' })

      expect(manager.scenarios.value[0].id).toBe(10)
      expect(manager.scenarios.value).toHaveLength(3)
    })

    it('SCEN_MGR_014: sets error on failure', async () => {
      axios.post.mockRejectedValueOnce({ response: { data: { error: 'Validation error' } } })

      await expect(manager.createNewScenario({})).rejects.toBeDefined()
      expect(manager.error.value).toBe('Validation error')
    })
  })

  // =========================================================================
  // updateScenario
  // =========================================================================

  describe('updateScenario', () => {
    it('SCEN_MGR_015: updates scenario in list', async () => {
      manager.scenarios.value = [{ id: 1, name: 'Old' }, { id: 2, name: 'Other' }]
      axios.put.mockResolvedValueOnce({ data: { scenario: { id: 1, name: 'Updated' } } })

      const result = await manager.updateScenario(1, { name: 'Updated' })

      expect(axios.put).toHaveBeenCalledWith('/api/scenarios/1', { name: 'Updated' }, expect.any(Object))
      expect(result).toEqual({ id: 1, name: 'Updated' })
      expect(manager.scenarios.value[0].name).toBe('Updated')
    })

    it('SCEN_MGR_016: updates currentScenario if same id', async () => {
      manager.currentScenario.value = { id: 1, name: 'Old' }
      manager.scenarios.value = [{ id: 1, name: 'Old' }]
      axios.put.mockResolvedValueOnce({ data: { scenario: { id: 1, name: 'New Name' } } })

      await manager.updateScenario(1, { name: 'New Name' })

      expect(manager.currentScenario.value.name).toBe('New Name')
    })

    it('SCEN_MGR_017: does not update currentScenario if different id', async () => {
      manager.currentScenario.value = { id: 2, name: 'Untouched' }
      manager.scenarios.value = [{ id: 1, name: 'Old' }]
      axios.put.mockResolvedValueOnce({ data: { scenario: { id: 1, name: 'Updated' } } })

      await manager.updateScenario(1, { name: 'Updated' })

      expect(manager.currentScenario.value.name).toBe('Untouched')
    })

    it('SCEN_MGR_018: handles scenario not in list gracefully', async () => {
      manager.scenarios.value = [{ id: 2, name: 'Other' }]
      axios.put.mockResolvedValueOnce({ data: { scenario: { id: 99, name: 'Ghost' } } })

      const result = await manager.updateScenario(99, { name: 'Ghost' })

      expect(result.name).toBe('Ghost')
      // scenarios list unchanged because id 99 not found
      expect(manager.scenarios.value).toHaveLength(1)
    })
  })

  // =========================================================================
  // deleteScenarioById
  // =========================================================================

  describe('deleteScenarioById', () => {
    it('SCEN_MGR_019: removes scenario from list', async () => {
      manager.scenarios.value = [{ id: 1 }, { id: 2 }, { id: 3 }]
      axios.delete.mockResolvedValueOnce({})

      await manager.deleteScenarioById(2)

      expect(axios.delete).toHaveBeenCalledWith('/api/scenarios/2', expect.any(Object))
      expect(manager.scenarios.value.map(s => s.id)).toEqual([1, 3])
    })

    it('SCEN_MGR_020: clears currentScenario if it was deleted', async () => {
      manager.scenarios.value = [{ id: 1 }]
      manager.currentScenario.value = { id: 1 }
      axios.delete.mockResolvedValueOnce({})

      await manager.deleteScenarioById(1)

      expect(manager.currentScenario.value).toBeNull()
    })

    it('SCEN_MGR_021: does not clear currentScenario if different id', async () => {
      manager.scenarios.value = [{ id: 1 }, { id: 2 }]
      manager.currentScenario.value = { id: 2, name: 'Keep' }
      axios.delete.mockResolvedValueOnce({})

      await manager.deleteScenarioById(1)

      expect(manager.currentScenario.value.name).toBe('Keep')
    })
  })

  // =========================================================================
  // fetchScenarioStats
  // =========================================================================

  describe('fetchScenarioStats', () => {
    it('SCEN_MGR_022: fetches stats for a scenario', async () => {
      const mockStats = { total: 10, completed: 5 }
      axios.get.mockResolvedValueOnce({ data: mockStats })

      const result = await manager.fetchScenarioStats(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/stats', expect.any(Object))
      expect(result).toEqual(mockStats)
    })
  })

  // =========================================================================
  // Team Management
  // =========================================================================

  describe('inviteUsers', () => {
    it('SCEN_MGR_023: sends invite request', async () => {
      axios.post.mockResolvedValueOnce({ data: { message: 'Invited' } })

      await manager.inviteUsers(42, ['user1', 'user2'], 'EVALUATOR')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/invite',
        { user_ids: ['user1', 'user2'], role: 'EVALUATOR' },
        expect.any(Object)
      )
    })

    it('SCEN_MGR_024: uses default role ASSESSOR', async () => {
      axios.post.mockResolvedValueOnce({ data: {} })

      await manager.inviteUsers(42, ['user1'])

      const payload = axios.post.mock.calls[0][1]
      expect(payload.role).toBe('ASSESSOR')
    })
  })

  describe('removeUser', () => {
    it('SCEN_MGR_025: sends delete request for user', async () => {
      axios.delete.mockResolvedValueOnce({})

      await manager.removeUser(42, 'user-5')

      expect(axios.delete).toHaveBeenCalledWith('/api/scenarios/42/users/user-5', expect.any(Object))
    })
  })

  describe('updateUserRole', () => {
    it('SCEN_MGR_026: sends role update request', async () => {
      axios.put.mockResolvedValueOnce({ data: { message: 'Updated' } })

      await manager.updateUserRole(42, 'user-5', 'VIEWER')

      expect(axios.put).toHaveBeenCalledWith(
        '/api/scenarios/42/users/user-5/role',
        { role: 'VIEWER' },
        expect.any(Object)
      )
    })
  })

  // =========================================================================
  // LLM Evaluation
  // =========================================================================

  describe('startLLMEvaluation', () => {
    it('SCEN_MGR_027: sends start request with options', async () => {
      const options = { model_id: 'gpt-4', prompt_template_id: 1 }
      axios.post.mockResolvedValueOnce({ data: { status: 'started' } })

      await manager.startLLMEvaluation(42, options)

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/llm-evaluation/start',
        options,
        expect.any(Object)
      )
    })
  })

  describe('stopLLMEvaluation', () => {
    it('SCEN_MGR_028: sends stop request', async () => {
      axios.post.mockResolvedValueOnce({ data: { status: 'stopped' } })

      await manager.stopLLMEvaluation(42)

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/llm-evaluation/stop',
        {},
        expect.any(Object)
      )
    })
  })

  // =========================================================================
  // Export
  // =========================================================================

  describe('exportResults', () => {
    it('SCEN_MGR_029: exports as JSON by default', async () => {
      axios.get.mockResolvedValueOnce({ data: { results: [] } })

      await manager.exportResults(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/export', expect.objectContaining({
        params: { format: 'json' },
        responseType: 'json'
      }))
    })

    it('SCEN_MGR_030: exports as blob for non-JSON formats', async () => {
      axios.get.mockResolvedValueOnce({ data: new Blob() })

      await manager.exportResults(42, 'csv')

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/export', expect.objectContaining({
        params: { format: 'csv' },
        responseType: 'blob'
      }))
    })
  })

  // =========================================================================
  // Thread Management
  // =========================================================================

  describe('getAvailableUsers', () => {
    it('SCEN_MGR_031: fetches available users', async () => {
      const users = [{ id: 1, name: 'User1' }]
      axios.get.mockResolvedValueOnce({ data: { users } })

      const result = await manager.getAvailableUsers(42)

      expect(result).toEqual(users)
    })

    it('SCEN_MGR_032: returns empty array when users key missing', async () => {
      axios.get.mockResolvedValueOnce({ data: {} })

      const result = await manager.getAvailableUsers(42)

      expect(result).toEqual([])
    })
  })

  describe('getAvailableThreads', () => {
    it('SCEN_MGR_033: fetches available threads', async () => {
      axios.get.mockResolvedValueOnce({ data: { threads: [], total: 0 } })

      await manager.getAvailableThreads(42, { page: 1, per_page: 20 })

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/available-threads', expect.objectContaining({
        params: { page: 1, per_page: 20 }
      }))
    })
  })

  describe('addThreadsToScenario', () => {
    it('SCEN_MGR_034: posts thread IDs', async () => {
      axios.post.mockResolvedValueOnce({ data: { added: 3 } })

      await manager.addThreadsToScenario(42, [10, 11, 12])

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/threads',
        { thread_ids: [10, 11, 12] },
        expect.any(Object)
      )
    })
  })

  describe('removeThreadFromScenario', () => {
    it('SCEN_MGR_035: deletes a thread from scenario', async () => {
      axios.delete.mockResolvedValueOnce({ data: {} })

      await manager.removeThreadFromScenario(42, 10)

      expect(axios.delete).toHaveBeenCalledWith('/api/scenarios/42/threads/10', expect.any(Object))
    })
  })

  describe('getThreadDetail', () => {
    it('SCEN_MGR_036: fetches thread detail', async () => {
      const thread = { id: 10, content: 'text' }
      axios.get.mockResolvedValueOnce({ data: { thread } })

      const result = await manager.getThreadDetail(42, 10)

      expect(result).toEqual(thread)
    })
  })

  // =========================================================================
  // Invitation Management
  // =========================================================================

  describe('respondToInvitation', () => {
    it('SCEN_MGR_037: accepts invitation and updates state', async () => {
      manager.scenarios.value = [{ id: 42, invitation: { status: 'pending' } }]
      axios.post.mockResolvedValueOnce({ data: { status: 'accepted' } })

      await manager.respondToInvitation(42, 'accept')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/respond',
        { action: 'accept' },
        expect.any(Object)
      )
      expect(manager.scenarios.value[0].invitation.status).toBe('accepted')
    })

    it('SCEN_MGR_038: rejects invitation and removes from list', async () => {
      manager.scenarios.value = [{ id: 42, invitation: { status: 'pending' } }]
      axios.post.mockResolvedValueOnce({ data: { status: 'rejected' } })

      await manager.respondToInvitation(42, 'reject')

      expect(manager.scenarios.value).toHaveLength(0)
    })

    it('SCEN_MGR_039: handles scenario not in list gracefully', async () => {
      manager.scenarios.value = []
      axios.post.mockResolvedValueOnce({ data: {} })

      // Should not throw
      await manager.respondToInvitation(999, 'accept')
    })
  })

  describe('reinviteUser', () => {
    it('SCEN_MGR_040: sends reinvite request', async () => {
      axios.post.mockResolvedValueOnce({ data: { message: 'Reinvited' } })

      await manager.reinviteUser(42, 'user-7')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/42/reinvite/user-7',
        {},
        expect.any(Object)
      )
    })
  })

  describe('getScenarioTeam', () => {
    it('SCEN_MGR_041: fetches team details', async () => {
      const teamData = { members: [{ user_id: 1, role: 'EVALUATOR' }] }
      axios.get.mockResolvedValueOnce({ data: teamData })

      const result = await manager.getScenarioTeam(42)

      expect(axios.get).toHaveBeenCalledWith('/api/scenarios/42/team', expect.any(Object))
      expect(result).toEqual(teamData)
    })
  })

  // =========================================================================
  // Duplicate / Archive
  // =========================================================================

  describe('duplicateScenario', () => {
    it('SCEN_MGR_042: duplicates and adds new scenario to list', async () => {
      manager.scenarios.value = [{ id: 1 }]
      const duplicate = { id: 10, name: 'Copy of Scenario' }
      axios.post.mockResolvedValueOnce({ data: { scenario: duplicate } })

      const result = await manager.duplicateScenario(1, 'Copy of Scenario')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/1/duplicate',
        { scenario_name: 'Copy of Scenario' },
        expect.any(Object)
      )
      expect(result).toEqual(duplicate)
      expect(manager.scenarios.value[0].id).toBe(10) // Added at beginning
    })

    it('SCEN_MGR_043: sends empty payload when no new name', async () => {
      axios.post.mockResolvedValueOnce({ data: { scenario: { id: 10 } } })

      await manager.duplicateScenario(1)

      expect(axios.post).toHaveBeenCalledWith(
        '/api/scenarios/1/duplicate',
        {},
        expect.any(Object)
      )
    })
  })

  describe('archiveScenario', () => {
    it('SCEN_MGR_044: archives and updates local state', async () => {
      manager.scenarios.value = [{ id: 1, status: 'active' }]
      manager.currentScenario.value = { id: 1, status: 'active' }
      const archived = { id: 1, status: 'archived' }
      axios.post.mockResolvedValueOnce({ data: { scenario: archived } })

      const result = await manager.archiveScenario(1)

      expect(result.status).toBe('archived')
      expect(manager.scenarios.value[0].status).toBe('archived')
      expect(manager.currentScenario.value.status).toBe('archived')
    })
  })

  describe('unarchiveScenario', () => {
    it('SCEN_MGR_045: unarchives and updates local state', async () => {
      manager.scenarios.value = [{ id: 1, status: 'archived' }]
      manager.currentScenario.value = { id: 1, status: 'archived' }
      const restored = { id: 1, status: 'active' }
      axios.post.mockResolvedValueOnce({ data: { scenario: restored } })

      const result = await manager.unarchiveScenario(1)

      expect(result.status).toBe('active')
      expect(manager.scenarios.value[0].status).toBe('active')
      expect(manager.currentScenario.value.status).toBe('active')
    })

    it('SCEN_MGR_046: does not update currentScenario if different id', async () => {
      manager.scenarios.value = [{ id: 1, status: 'archived' }]
      manager.currentScenario.value = { id: 2, status: 'active' }
      axios.post.mockResolvedValueOnce({ data: { scenario: { id: 1, status: 'active' } } })

      await manager.unarchiveScenario(1)

      expect(manager.currentScenario.value.id).toBe(2)
    })
  })

  // =========================================================================
  // Error handling patterns
  // =========================================================================

  describe('generic error handling', () => {
    it('SCEN_MGR_047: uses fallback error message when response has no error field', async () => {
      axios.get.mockRejectedValueOnce({ response: { data: {} } })

      await expect(manager.fetchScenarios()).rejects.toBeDefined()
      expect(manager.error.value).toBe('Failed to fetch scenarios')
    })

    it('SCEN_MGR_048: loading is always reset after error', async () => {
      axios.post.mockRejectedValueOnce(new Error('Network error'))

      await expect(manager.createNewScenario({})).rejects.toBeDefined()
      expect(manager.loading.value).toBe(false)
    })
  })

  // =========================================================================
  // Return interface
  // =========================================================================

  describe('return interface', () => {
    it('SCEN_MGR_049: exposes all expected methods', () => {
      const methods = [
        'fetchScenarios', 'fetchScenario', 'createNewScenario', 'updateScenario',
        'deleteScenarioById', 'fetchScenarioStats', 'inviteUsers', 'removeUser',
        'updateUserRole', 'startLLMEvaluation', 'stopLLMEvaluation', 'exportResults',
        'getAvailableUsers', 'getAvailableThreads', 'addThreadsToScenario',
        'removeThreadFromScenario', 'getThreadDetail', 'respondToInvitation',
        'reinviteUser', 'getScenarioTeam', 'duplicateScenario', 'archiveScenario',
        'unarchiveScenario'
      ]
      for (const method of methods) {
        expect(typeof manager[method], `${method} should be a function`).toBe('function')
      }
    })

    it('SCEN_MGR_050: exposes all expected state refs', () => {
      expect(manager.scenarios).toBeDefined()
      expect(manager.currentScenario).toBeDefined()
      expect(manager.loading).toBeDefined()
      expect(manager.error).toBeDefined()
      expect(manager.currentUserId).toBeDefined()
    })
  })
})
