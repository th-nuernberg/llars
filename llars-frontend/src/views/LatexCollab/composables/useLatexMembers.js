/**
 * useLatexMembers.js
 *
 * Composable for workspace member/sharing management.
 * Handles loading members, inviting, and removing members.
 */

import { ref, computed } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Create LaTeX members composable
 * @param {Object} options - Configuration options
 * @param {Ref<number>} options.workspaceId - Workspace ID ref
 * @param {Ref<Object>} options.workspace - Workspace object ref
 * @param {Function} options.hasPermission - Permission check function
 * @param {Ref<string>} options.currentUsername - Current user's username
 * @param {Ref<boolean>} options.isAdmin - Whether current user is admin
 * @returns {Object} Composable state and methods
 */
export function useLatexMembers({
  workspaceId,
  workspace,
  hasPermission,
  currentUsername,
  isAdmin
}) {
  const { t } = useI18n()
  // State
  const shareDialog = ref(false)
  const members = ref([])
  const membersLoading = ref(false)
  const shareError = ref('')
  const removingUsername = ref('')
  const selectedUser = ref(null)
  const userSearchRef = ref(null)
  const ownerInfo = ref({
    username: '',
    avatar_url: null,
    avatar_seed: null,
    collab_color: null
  })

  // Computed
  const canShareWorkspace = computed(() => {
    if (!workspace.value) return false
    if (!hasPermission('feature:latex_collab:share')) return false
    return isAdmin.value || (currentUsername.value && currentUsername.value === workspace.value.owner_username)
  })

  const excludedUsernames = computed(() => {
    const excluded = []
    if (workspace.value?.owner_username) excluded.push(workspace.value.owner_username)
    members.value.forEach(m => excluded.push(m.username))
    return excluded
  })

  // Methods
  async function loadMembers() {
    if (!workspaceId.value) return
    membersLoading.value = true
    shareError.value = ''
    try {
      const res = await axios.get(
        `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members`,
        { headers: authHeaders() }
      )
      members.value = res.data.members || []
      // Store owner info
      ownerInfo.value = {
        username: res.data.owner?.username || '',
        avatar_url: res.data.owner?.avatar_url || null,
        avatar_seed: res.data.owner?.avatar_seed || null,
        collab_color: res.data.owner?.collab_color || null
      }
  } catch (e) {
    members.value = []
      shareError.value = e?.response?.data?.error || e?.message || t('latexCollab.errors.membersLoadFailed')
    } finally {
      membersLoading.value = false
    }
  }

  function openShareDialog() {
    shareDialog.value = true
    selectedUser.value = null
    loadMembers()
  }

  async function inviteMember(user) {
    const username = user?.username || selectedUser.value?.username
    if (!username) return
    shareError.value = ''
    try {
      await axios.post(
        `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members`,
        { username: username.trim() },
        { headers: authHeaders() }
      )
      selectedUser.value = null
      userSearchRef.value?.reset?.()
      await loadMembers()
  } catch (e) {
      shareError.value = e?.response?.data?.error || e?.message || t('latexCollab.errors.inviteFailed')
    userSearchRef.value?.setAdding?.(false)
  }
  }

  async function removeMember(username) {
    if (!username) return
    removingUsername.value = username
    shareError.value = ''
    try {
      await axios.delete(
        `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members/${encodeURIComponent(username)}`,
        { headers: authHeaders() }
      )
      await loadMembers()
  } catch (e) {
      shareError.value = e?.response?.data?.error || e?.message || t('latexCollab.errors.removeFailed')
  } finally {
      removingUsername.value = ''
    }
  }

  return {
    // State
    shareDialog,
    members,
    membersLoading,
    shareError,
    removingUsername,
    selectedUser,
    userSearchRef,
    ownerInfo,

    // Computed
    canShareWorkspace,
    excludedUsernames,

    // Methods
    loadMembers,
    openShareDialog,
    inviteMember,
    removeMember
  }
}
