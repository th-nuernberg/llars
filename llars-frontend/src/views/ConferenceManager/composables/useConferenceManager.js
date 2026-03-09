/**
 * Composable for Conference Manager state and API interactions
 */
import { ref } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

// Shared state across components
const conferences = ref([])
const papers = ref([])
const series = ref([])
const stats = ref(null)
const loading = ref(false)
const error = ref(null)
const latexAccessMap = ref({})
const activeGroupId = ref(null)

export function useConferenceManager() {
  const { getToken } = useAuth()

  function getHeaders() {
    return { Authorization: `Bearer ${getToken()}` }
  }

  function setGroupId(groupId) {
    activeGroupId.value = groupId ? Number(groupId) : null
  }

  function _addGroupParam(params) {
    if (activeGroupId.value) {
      params.group_id = activeGroupId.value
    }
    return params
  }

  // ── Conferences ────────────────────────────────────────────

  async function fetchConferences(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const params = {}
      if (filters.year) params.year = filters.year
      if (filters.core_ranking) params.core_ranking = filters.core_ranking
      if (filters.search) params.search = filters.search
      _addGroupParam(params)

      const response = await axios.get('/api/conference-manager/conferences', {
        headers: getHeaders(),
        params,
      })
      conferences.value = response.data.conferences || []
      return conferences.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch conferences'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getConference(id) {
    const response = await axios.get(`/api/conference-manager/conferences/${id}`, {
      headers: getHeaders(),
    })
    return response.data.conference
  }

  async function createConference(data) {
    const payload = { ...data }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    const response = await axios.post('/api/conference-manager/conferences', payload, {
      headers: getHeaders(),
    })
    await fetchConferences()
    return response.data.conference
  }

  async function updateConference(id, data) {
    const response = await axios.put(`/api/conference-manager/conferences/${id}`, data, {
      headers: getHeaders(),
    })
    await fetchConferences()
    return response.data.conference
  }

  async function deleteConference(id) {
    await axios.delete(`/api/conference-manager/conferences/${id}`, {
      headers: getHeaders(),
    })
    await fetchConferences()
  }

  // ── Papers ─────────────────────────────────────────────────

  async function fetchPapers(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const params = {}
      if (filters.status) params.status = filters.status
      if (filters.conference_id) params.conference_id = filters.conference_id
      if (filters.search) params.search = filters.search
      _addGroupParam(params)

      const response = await axios.get('/api/conference-manager/papers', {
        headers: getHeaders(),
        params,
      })
      papers.value = response.data.papers || []
      checkLatexAccess()
      return papers.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch papers'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getPaper(id) {
    const response = await axios.get(`/api/conference-manager/papers/${id}`, {
      headers: getHeaders(),
    })
    return response.data.paper
  }

  async function createPaper(data) {
    const payload = { ...data }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    const response = await axios.post('/api/conference-manager/papers', payload, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  async function updatePaper(id, data) {
    const response = await axios.put(`/api/conference-manager/papers/${id}`, data, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  async function updatePaperStatus(id, status) {
    const response = await axios.patch(`/api/conference-manager/papers/${id}/status`, { status }, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  async function deletePaper(id) {
    await axios.delete(`/api/conference-manager/papers/${id}`, {
      headers: getHeaders(),
    })
    await fetchPapers()
  }

  async function setPaperAuthors(paperId, authors) {
    const response = await axios.put(`/api/conference-manager/papers/${paperId}/authors`, { authors }, {
      headers: getHeaders(),
    })
    return response.data.authors
  }

  // ── Submissions ──────────────────────────────────────────────

  async function addSubmission(paperId, data) {
    const response = await axios.post(`/api/conference-manager/papers/${paperId}/submissions`, data, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  async function updateSubmission(paperId, submissionId, data) {
    const response = await axios.put(`/api/conference-manager/papers/${paperId}/submissions/${submissionId}`, data, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  async function deleteSubmission(paperId, submissionId) {
    const response = await axios.delete(`/api/conference-manager/papers/${paperId}/submissions/${submissionId}`, {
      headers: getHeaders(),
    })
    await fetchPapers()
    return response.data.paper
  }

  // ── Series ─────────────────────────────────────────────────

  async function fetchSeries(search = '') {
    try {
      const params = {}
      if (search) params.search = search
      _addGroupParam(params)
      const response = await axios.get('/api/conference-manager/series', {
        headers: getHeaders(),
        params,
      })
      series.value = response.data.series || []
      return series.value
    } catch (err) {
      console.error('Failed to fetch series:', err)
    }
  }

  async function createSeries(data) {
    const payload = { ...data }
    if (activeGroupId.value) payload.group_id = activeGroupId.value
    const response = await axios.post('/api/conference-manager/series', payload, {
      headers: getHeaders(),
    })
    await fetchSeries()
    return response.data.series
  }

  async function findSeriesByAcronym(acronym) {
    const response = await axios.get('/api/conference-manager/series/find-by-acronym', {
      headers: getHeaders(),
      params: { acronym },
    })
    return response.data.series
  }

  async function getNewEditionDefaults(seriesId) {
    const response = await axios.get(`/api/conference-manager/series/${seriesId}/new-edition-defaults`, {
      headers: getHeaders(),
    })
    return response.data.defaults
  }

  // ── LaTeX Access ─────────────────────────────────────────────

  async function checkLatexAccess() {
    try {
      const response = await axios.get('/api/conference-manager/papers/latex-access', {
        headers: getHeaders(),
      })
      latexAccessMap.value = response.data.access || {}
    } catch (err) {
      console.error('Failed to check latex access:', err)
    }
  }

  async function requestLatexAccess(workspaceId, message = '') {
    const response = await axios.post(
      `/api/latex-collab/workspaces/${workspaceId}/access-requests`,
      message ? { message } : {},
      { headers: getHeaders() }
    )
    await checkLatexAccess()
    return response.data
  }

  // ── Stats ──────────────────────────────────────────────────

  async function fetchStats() {
    try {
      const params = {}
      _addGroupParam(params)
      const response = await axios.get('/api/conference-manager/stats', {
        headers: getHeaders(),
        params,
      })
      stats.value = response.data.stats
      return stats.value
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }

  return {
    // State
    conferences,
    papers,
    series,
    stats,
    loading,
    error,
    latexAccessMap,
    activeGroupId,

    // Group scope
    setGroupId,

    // Conference methods
    fetchConferences,
    getConference,
    createConference,
    updateConference,
    deleteConference,

    // Series methods
    fetchSeries,
    createSeries,
    findSeriesByAcronym,
    getNewEditionDefaults,

    // Paper methods
    fetchPapers,
    getPaper,
    createPaper,
    updatePaper,
    updatePaperStatus,
    deletePaper,
    setPaperAuthors,

    // Submission methods
    addSubmission,
    updateSubmission,
    deleteSubmission,

    // LaTeX access
    checkLatexAccess,
    requestLatexAccess,

    // Stats
    fetchStats,
  }
}
