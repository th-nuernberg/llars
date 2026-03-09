/**
 * Composable for Research Group API interactions
 */
import { ref } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

const myGroups = ref([])
const allGroups = ref([])
const currentGroup = ref(null)
const groupMembers = ref([])
const pendingRequests = ref([])
const groupLoading = ref(false)

export function useResearchGroups() {
  const { getToken } = useAuth()

  function getHeaders() {
    return { Authorization: `Bearer ${getToken()}` }
  }

  // ── Groups ──────────────────────────────────────────────

  async function fetchMyGroups() {
    groupLoading.value = true
    try {
      const response = await axios.get('/api/conference-manager/groups/my', {
        headers: getHeaders(),
      })
      myGroups.value = response.data.groups || []
      return myGroups.value
    } catch (err) {
      console.error('Failed to fetch my groups:', err)
      return []
    } finally {
      groupLoading.value = false
    }
  }

  async function fetchAllGroups(search = '') {
    try {
      const params = {}
      if (search) params.search = search
      const response = await axios.get('/api/conference-manager/groups', {
        headers: getHeaders(),
        params,
      })
      allGroups.value = response.data.groups || []
      return allGroups.value
    } catch (err) {
      console.error('Failed to fetch all groups:', err)
      return []
    }
  }

  async function fetchGroup(groupId) {
    try {
      const response = await axios.get(`/api/conference-manager/groups/${groupId}`, {
        headers: getHeaders(),
      })
      currentGroup.value = response.data.group
      return currentGroup.value
    } catch (err) {
      console.error('Failed to fetch group:', err)
      throw err
    }
  }

  async function createGroup(data) {
    const response = await axios.post('/api/conference-manager/groups', data, {
      headers: getHeaders(),
    })
    return response.data.group
  }

  async function updateGroup(groupId, data) {
    const response = await axios.put(`/api/conference-manager/groups/${groupId}`, data, {
      headers: getHeaders(),
    })
    return response.data.group
  }

  async function deleteGroup(groupId) {
    await axios.delete(`/api/conference-manager/groups/${groupId}`, {
      headers: getHeaders(),
    })
  }

  // ── Members ─────────────────────────────────────────────

  async function fetchMembers(groupId) {
    try {
      const response = await axios.get(`/api/conference-manager/groups/${groupId}/members`, {
        headers: getHeaders(),
      })
      groupMembers.value = response.data.members || []
      return groupMembers.value
    } catch (err) {
      console.error('Failed to fetch members:', err)
      return []
    }
  }

  async function addMember(groupId, userId, role = 'member') {
    const response = await axios.post(`/api/conference-manager/groups/${groupId}/members`, {
      user_id: userId,
      role,
    }, {
      headers: getHeaders(),
    })
    await fetchMembers(groupId)
    return response.data.member
  }

  async function updateMemberRole(groupId, memberId, role) {
    const response = await axios.put(`/api/conference-manager/groups/${groupId}/members/${memberId}`, {
      role,
    }, {
      headers: getHeaders(),
    })
    await fetchMembers(groupId)
    return response.data.member
  }

  async function removeMember(groupId, memberId) {
    await axios.delete(`/api/conference-manager/groups/${groupId}/members/${memberId}`, {
      headers: getHeaders(),
    })
    await fetchMembers(groupId)
  }

  // ── Access Requests ─────────────────────────────────────

  async function createAccessRequest(groupId, message = '') {
    const response = await axios.post(`/api/conference-manager/groups/${groupId}/access-requests`,
      message ? { message } : {},
      { headers: getHeaders() }
    )
    return response.data.request
  }

  async function fetchPendingRequests() {
    try {
      const response = await axios.get('/api/conference-manager/groups/access-requests', {
        headers: getHeaders(),
      })
      pendingRequests.value = response.data.requests || []
      return pendingRequests.value
    } catch (err) {
      console.error('Failed to fetch pending requests:', err)
      return []
    }
  }

  async function fetchGroupRequests(groupId) {
    try {
      const response = await axios.get(`/api/conference-manager/groups/${groupId}/access-requests`, {
        headers: getHeaders(),
      })
      return response.data.requests || []
    } catch (err) {
      console.error('Failed to fetch group requests:', err)
      return []
    }
  }

  async function resolveAccessRequest(requestId, action) {
    const response = await axios.put(`/api/conference-manager/access-requests/${requestId}`, {
      action,
    }, {
      headers: getHeaders(),
    })
    return response.data.result
  }

  async function fetchGroupConferences(groupId) {
    try {
      const response = await axios.get('/api/conference-manager/conferences', {
        headers: getHeaders(),
        params: { group_id: groupId },
      })
      return response.data.conferences || []
    } catch (err) {
      console.error('Failed to fetch group conferences:', err)
      return []
    }
  }

  async function fetchGroupPapers(groupId) {
    try {
      const response = await axios.get('/api/conference-manager/papers', {
        headers: getHeaders(),
        params: { group_id: groupId },
      })
      return response.data.papers || []
    } catch (err) {
      console.error('Failed to fetch group papers:', err)
      return []
    }
  }

  return {
    // State
    myGroups,
    allGroups,
    currentGroup,
    groupMembers,
    pendingRequests,
    groupLoading,

    // Group methods
    fetchMyGroups,
    fetchAllGroups,
    fetchGroup,
    createGroup,
    updateGroup,
    deleteGroup,

    // Member methods
    fetchMembers,
    addMember,
    updateMemberRole,
    removeMember,

    // Access request methods
    createAccessRequest,
    fetchPendingRequests,
    fetchGroupRequests,
    resolveAccessRequest,

    // Content methods
    fetchGroupConferences,
    fetchGroupPapers,
  }
}
