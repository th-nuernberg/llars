/**
 * Composable for Scenario Manager state and API interactions
 */
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

// Shared state across components
const scenarios = ref([])
const currentScenario = ref(null)
const loading = ref(false)
const error = ref(null)

export function useScenarioManager() {
  const { getToken, tokenParsed } = useAuth()

  const currentUserId = computed(() => tokenParsed.value?.sub)

  /**
   * Get authorization headers
   */
  function getHeaders() {
    return {
      Authorization: `Bearer ${getToken()}`
    }
  }

  /**
   * Fetch all scenarios for the current user
   * Includes both owned and shared scenarios
   *
   * @param {string} filter - Optional filter: 'owned', 'accepted', 'rejected', 'pending', 'all'
   */
  async function fetchScenarios(filter = null) {
    loading.value = true
    error.value = null
    try {
      const params = filter ? { filter } : {}
      const response = await axios.get('/api/scenarios', {
        headers: getHeaders(),
        params
      })
      scenarios.value = response.data.scenarios || []
      return scenarios.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch scenarios'
      console.error('Error fetching scenarios:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single scenario by ID with full details
   */
  async function fetchScenario(scenarioId) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}`, {
        headers: getHeaders()
      })
      currentScenario.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch scenario'
      console.error('Error fetching scenario:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new scenario
   */
  async function createNewScenario(scenarioData) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.post('/api/scenarios', scenarioData, {
        headers: getHeaders()
      })
      const newScenario = response.data.scenario
      scenarios.value.unshift(newScenario)
      return newScenario
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to create scenario'
      console.error('Error creating scenario:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update an existing scenario
   */
  async function updateScenario(scenarioId, updates) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.put(`/api/scenarios/${scenarioId}`, updates, {
        headers: getHeaders()
      })
      const updated = response.data.scenario

      // Update in list
      const index = scenarios.value.findIndex(s => s.id === scenarioId)
      if (index !== -1) {
        scenarios.value[index] = { ...scenarios.value[index], ...updated }
      }

      // Update current if same
      if (currentScenario.value?.id === scenarioId) {
        currentScenario.value = { ...currentScenario.value, ...updated }
      }

      return updated
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to update scenario'
      console.error('Error updating scenario:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a scenario by ID
   */
  async function deleteScenarioById(scenarioId) {
    loading.value = true
    error.value = null
    try {
      await axios.delete(`/api/scenarios/${scenarioId}`, {
        headers: getHeaders()
      })
      scenarios.value = scenarios.value.filter(s => s.id !== scenarioId)
      if (currentScenario.value?.id === scenarioId) {
        currentScenario.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to delete scenario'
      console.error('Error deleting scenario:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get scenario statistics
   */
  async function fetchScenarioStats(scenarioId) {
    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/stats`, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error fetching scenario stats:', err)
      throw err
    }
  }

  /**
   * Invite users to a scenario
   */
  async function inviteUsers(scenarioId, userIds, role = 'EVALUATOR') {
    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/invite`, {
        user_ids: userIds,
        role
      }, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error inviting users:', err)
      throw err
    }
  }

  /**
   * Remove a user from a scenario
   */
  async function removeUser(scenarioId, userId) {
    try {
      await axios.delete(`/api/scenarios/${scenarioId}/users/${userId}`, {
        headers: getHeaders()
      })
    } catch (err) {
      console.error('Error removing user:', err)
      throw err
    }
  }

  /**
   * Start LLM evaluation for a scenario
   */
  async function startLLMEvaluation(scenarioId, options = {}) {
    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/llm-evaluation/start`, options, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error starting LLM evaluation:', err)
      throw err
    }
  }

  /**
   * Stop LLM evaluation for a scenario
   */
  async function stopLLMEvaluation(scenarioId) {
    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/llm-evaluation/stop`, {}, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error stopping LLM evaluation:', err)
      throw err
    }
  }

  /**
   * Export scenario results
   */
  async function exportResults(scenarioId, format = 'json') {
    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/export`, {
        params: { format },
        headers: getHeaders(),
        responseType: format === 'json' ? 'json' : 'blob'
      })
      return response.data
    } catch (err) {
      console.error('Error exporting results:', err)
      throw err
    }
  }

  /**
   * Get available users that can be invited to a scenario
   */
  async function getAvailableUsers(scenarioId) {
    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/available-users`, {
        headers: getHeaders()
      })
      return response.data.users || []
    } catch (err) {
      console.error('Error fetching available users:', err)
      throw err
    }
  }

  /**
   * Respond to a scenario invitation (accept or reject)
   * @param {number} scenarioId - The scenario ID
   * @param {string} action - 'accept' or 'reject'
   */
  async function respondToInvitation(scenarioId, action) {
    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/respond`, {
        action
      }, {
        headers: getHeaders()
      })

      // Update local state
      const index = scenarios.value.findIndex(s => s.id === scenarioId)
      if (index !== -1) {
        if (action === 'reject') {
          // Remove from list when rejected
          scenarios.value.splice(index, 1)
        } else {
          // Update invitation status when accepted
          scenarios.value[index].invitation = {
            ...scenarios.value[index].invitation,
            status: 'accepted'
          }
        }
      }

      return response.data
    } catch (err) {
      console.error('Error responding to invitation:', err)
      throw err
    }
  }

  /**
   * Re-invite a user who previously rejected an invitation
   * @param {number} scenarioId - The scenario ID
   * @param {number} userId - The user ID to reinvite
   */
  async function reinviteUser(scenarioId, userId) {
    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/reinvite/${userId}`, {}, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error reinviting user:', err)
      throw err
    }
  }

  /**
   * Get detailed team information with invitation status
   * @param {number} scenarioId - The scenario ID
   */
  async function getScenarioTeam(scenarioId) {
    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/team`, {
        headers: getHeaders()
      })
      return response.data
    } catch (err) {
      console.error('Error fetching scenario team:', err)
      throw err
    }
  }

  return {
    // State
    scenarios,
    currentScenario,
    loading,
    error,
    currentUserId,

    // Methods
    fetchScenarios,
    fetchScenario,
    createNewScenario,
    updateScenario,
    deleteScenarioById,
    fetchScenarioStats,
    inviteUsers,
    removeUser,
    startLLMEvaluation,
    stopLLMEvaluation,
    exportResults,
    getAvailableUsers,

    // Invitation Management
    respondToInvitation,
    reinviteUser,
    getScenarioTeam
  }
}
