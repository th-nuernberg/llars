/**
 * Git Status Composable
 *
 * Shared state management for Git operations in LaTeX/Markdown Collab workspaces
 * and single-entity mode for Prompt Engineering.
 * Used by GitStatusWidget and GitDetailDialog for consistent state.
 *
 * Supports two modes:
 * - 'workspace': Multiple documents in a workspace (LaTeX/Markdown Collab)
 * - 'single': Single entity with version history (Prompt Engineering)
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'
import { logI18n } from '@/utils/logI18n'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

/**
 * @param {import('vue').Ref<number>} entityIdRef - Reactive entity ID (workspace or prompt)
 * @param {Object} options - Configuration options
 * @param {string} options.apiPrefix - API prefix (default: '/api/latex-collab')
 * @param {string} options.entityMode - 'workspace' (default) or 'single'
 * @param {boolean} options.autoSetup - Automatically setup socket and load data on mount
 * @param {Object} options.summary - For single mode: reactive summary object with hasChanges, insertions, deletions
 * @param {Function} options.getContent - For single mode: function to get current content
 */
export function useGitStatus(entityIdRef, options = {}) {
  const {
    apiPrefix = '/api/latex-collab',
    entityMode = 'workspace',
    autoSetup = true,
    summary = null,
    getContent = null
  } = options

  const { t, locale } = useI18n()

  // ============ STATE ============

  // Changed files
  const changedFiles = ref([])
  const deletedFiles = ref([])
  const selectedFiles = ref([])
  const checkingChanges = ref(false)
  const loadError = ref('')
  const restoringFile = ref(null)

  // Commit
  const commitMessage = ref('')
  const committing = ref(false)
  const commitError = ref('')

  // Recent commits
  const recentCommits = ref([])
  const loadingCommits = ref(false)

  // Rollback
  const rollingBack = ref(null)
  const showRollbackConfirm = ref(false)
  const rollbackTarget = ref(null)
  const forceRollback = ref(false)
  const forceRollbackDetails = ref(null)

  // ============ COMPUTED ============

  const changedCount = computed(() => changedFiles.value.length)
  const deletedCount = computed(() => deletedFiles.value.length)
  const totalChanges = computed(() => changedCount.value + deletedCount.value)

  const allSelected = computed(() =>
    changedFiles.value.length > 0 && selectedFiles.value.length === changedFiles.value.length
  )

  const someSelected = computed(() =>
    selectedFiles.value.length > 0 && selectedFiles.value.length < changedFiles.value.length
  )

  const totalInsertions = computed(() =>
    changedFiles.value
      .filter(f => selectedFiles.value.includes(f.id))
      .reduce((sum, f) => sum + (f.insertions || 0), 0)
  )

  const totalDeletions = computed(() =>
    changedFiles.value
      .filter(f => selectedFiles.value.includes(f.id))
      .reduce((sum, f) => sum + (f.deletions || 0), 0)
  )

  const canSubmitCommit = computed(() => {
    const msgOk = commitMessage.value.trim().length > 0
    if (entityMode === 'single') {
      // For single entity mode, check summary for changes
      const hasChanges = summary?.value?.hasChanges === true || (summary?.value?.totalChangedLines || 0) > 0
      return msgOk && hasChanges
    }
    return msgOk && selectedFiles.value.length > 0
  })

  // ============ HELPERS ============

  function authHeaders() {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  function formatDate(iso) {
    if (!iso) return '—'
    try {
      const date = new Date(iso)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return t('workspaceGit.relative.justNow')
      if (diffMins < 60) return t('workspaceGit.relative.minutesAgo', { count: diffMins })
      if (diffHours < 24) return t('workspaceGit.relative.hoursAgo', { count: diffHours })
      if (diffDays < 7) return t('workspaceGit.relative.daysAgo', { count: diffDays })
      return date.toLocaleDateString(locale.value || undefined, { day: '2-digit', month: '2-digit', year: '2-digit' })
    } catch {
      return iso
    }
  }

  function getFileIcon(path) {
    const ext = path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'tex': return 'mdi-file-document'
      case 'bib': return 'zotero'
      case 'sty': return 'mdi-file-cog'
      case 'cls': return 'mdi-file-settings'
      default: return 'mdi-file-document-outline'
    }
  }

  function getFileIconColor(path) {
    const ext = path.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'tex': return 'green'
      case 'bib': return undefined
      case 'sty': return 'orange'
      case 'cls': return 'purple'
      default: return 'grey'
    }
  }

  function getStatusBadge(file) {
    if (file.status === 'D') return { text: 'D', color: 'error', tooltip: t('workspaceGit.status.deleted') }
    if (file.status === 'A' || !file.has_baseline) return { text: 'A', color: 'info', tooltip: t('workspaceGit.status.added') }
    if (file.status === 'R') return { text: 'R', color: 'purple', tooltip: t('workspaceGit.status.renamed') }
    if (file.status === 'V') return { text: '→', color: 'cyan', tooltip: t('workspaceGit.status.moved') }
    if (file.status === 'RV') return { text: 'R→', color: 'purple', tooltip: t('workspaceGit.status.renamedMoved') }
    return { text: 'M', color: 'warning', tooltip: t('workspaceGit.status.modified') }
  }

  // ============ SELECTION ============

  function toggleFile(fileId) {
    const index = selectedFiles.value.indexOf(fileId)
    if (index === -1) {
      selectedFiles.value.push(fileId)
    } else {
      selectedFiles.value.splice(index, 1)
    }
  }

  function selectAll() {
    selectedFiles.value = changedFiles.value.map(f => f.id)
  }

  function deselectAll() {
    selectedFiles.value = []
  }

  function toggleSelectAll(value) {
    if (value) selectAll()
    else deselectAll()
  }

  // ============ API METHODS ============

  /**
   * Check for uncommitted changes in the workspace.
   * In single entity mode, this is a no-op (changes are tracked via summary prop).
   * @param {Object} opts - Options
   * @param {boolean} opts.silent - If true, don't show loading state
   */
  async function checkForChanges({ silent = false } = {}) {
    const entityId = entityIdRef.value
    if (!entityId) return

    // In single entity mode, changes are tracked externally via summary prop
    if (entityMode === 'single') return

    if (!silent) {
      checkingChanges.value = true
      loadError.value = ''
    }

    try {
      const res = await axios.get(
        `${API_BASE}${apiPrefix}/workspaces/${entityId}/changes`,
        { headers: authHeaders() }
      )

      const newChangedFiles = res.data.changed_files || []
      const newDeletedFiles = res.data.deleted_files || []

      // Smart merge: only update if different
      const changedFilesChanged = JSON.stringify(newChangedFiles.map(f => ({ id: f.id, insertions: f.insertions, deletions: f.deletions }))) !==
                                  JSON.stringify(changedFiles.value.map(f => ({ id: f.id, insertions: f.insertions, deletions: f.deletions })))
      const deletedFilesChanged = JSON.stringify(newDeletedFiles.map(f => f.id)) !==
                                  JSON.stringify(deletedFiles.value.map(f => f.id))

      if (changedFilesChanged) {
        const previouslySelected = new Set(selectedFiles.value)
        changedFiles.value = newChangedFiles

        const newFileIds = new Set(newChangedFiles.map(f => f.id))
        const stillSelected = selectedFiles.value.filter(id => newFileIds.has(id))
        const newFiles = newChangedFiles.filter(f => !previouslySelected.has(f.id)).map(f => f.id)
        selectedFiles.value = [...stillSelected, ...newFiles]
      }

      if (deletedFilesChanged) {
        deletedFiles.value = newDeletedFiles
      }
    } catch (e) {
      if (!silent) {
        loadError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.loadChangesFailed')
        changedFiles.value = []
        deletedFiles.value = []
        selectedFiles.value = []
      }
    } finally {
      if (!silent) {
        checkingChanges.value = false
      }
    }
  }

  /**
   * Load recent commits for the workspace or single entity
   */
  async function loadRecentCommits() {
    const entityId = entityIdRef.value
    if (!entityId) return

    loadingCommits.value = true
    try {
      if (entityMode === 'single') {
        // Single entity mode: Load commits directly for the entity
        const res = await axios.get(
          `${API_BASE}${apiPrefix}/${entityId}/commits`,
          { headers: authHeaders() }
        )
        recentCommits.value = (res.data.commits || []).map(c => ({
          ...c,
          file_count: 1,
          author_username: c.author || c.author_username
        }))
      } else {
        // Workspace mode: Aggregate commits from all documents
        const res = await axios.get(
          `${API_BASE}${apiPrefix}/workspaces/${entityId}/tree`,
          { headers: authHeaders() }
        )

        const nodes = res.data.nodes || []
        const textFiles = nodes.filter(n => n.type === 'file' && !n.asset_id)

        const commitPromises = textFiles.slice(0, 5).map(async (node) => {
          try {
            const commitRes = await axios.get(
              `${API_BASE}${apiPrefix}/documents/${node.id}/commits`,
              { headers: authHeaders() }
            )
            return commitRes.data.commits || []
          } catch {
            return []
          }
        })

        const allCommits = (await Promise.all(commitPromises)).flat()

        // Deduplicate
        const uniqueCommits = []
        const seen = new Set()
        for (const c of allCommits.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))) {
          const key = `${c.message}|${c.created_at}`
          if (!seen.has(key)) {
            seen.add(key)
            const sameCommits = allCommits.filter(cc =>
              cc.message === c.message && cc.created_at === c.created_at
            )
            uniqueCommits.push({ ...c, file_count: sameCommits.length })
          }
        }

        recentCommits.value = uniqueCommits.slice(0, 10)
      }
    } catch (e) {
      logI18n('error', 'logs.gitStatus.recentCommitsFailed', e)
      recentCommits.value = []
    } finally {
      loadingCommits.value = false
    }
  }

  /**
   * Submit a commit
   * @param {Object} opts - Options
   * @param {Function} opts.beforeCommit - Hook before commit
   */
  async function submitCommit({ beforeCommit } = {}) {
    if (!canSubmitCommit.value) return false

    committing.value = true
    commitError.value = ''

    try {
      if (typeof beforeCommit === 'function') {
        await beforeCommit(entityMode === 'single' ? null : [...selectedFiles.value])
      }

      if (entityMode === 'single') {
        // Single entity mode: Commit the single entity
        const contentSnapshot = getContent ? getContent() : null
        await axios.post(
          `${API_BASE}${apiPrefix}/${entityIdRef.value}/commit`,
          {
            message: commitMessage.value.trim(),
            diff_summary: summary?.value || null,
            content_snapshot: contentSnapshot
          },
          { headers: authHeaders() }
        )
      } else {
        // Workspace mode: Commit selected documents
        await axios.post(
          `${API_BASE}${apiPrefix}/workspaces/${entityIdRef.value}/commit`,
          {
            message: commitMessage.value.trim(),
            document_ids: selectedFiles.value
          },
          { headers: authHeaders() }
        )
        selectedFiles.value = []
        changedFiles.value = []
      }

      commitMessage.value = ''
      await Promise.all([checkForChanges(), loadRecentCommits()])
      return true
    } catch (e) {
      commitError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.commitFailed')
      return false
    } finally {
      committing.value = false
    }
  }

  /**
   * Quick commit - commits ALL changed files (workspace mode) or current content (single mode)
   * @param {string} message - Commit message
   * @param {Object} opts - Options
   */
  async function quickCommit(message, { beforeCommit } = {}) {
    if (!message?.trim()) return false

    if (entityMode === 'single') {
      // Single mode: Check summary for changes
      const hasChanges = summary?.value?.hasChanges === true || (summary?.value?.totalChangedLines || 0) > 0
      if (!hasChanges) return false
    } else {
      // Workspace mode: Need changed files
      if (changedFiles.value.length === 0) return false
      // Select all files for quick commit
      selectedFiles.value = changedFiles.value.map(f => f.id)
    }

    commitMessage.value = message.trim()
    return await submitCommit({ beforeCommit })
  }

  /**
   * Rollback a file to baseline
   */
  async function executeRollback({ beforeRollback } = {}) {
    if (!rollbackTarget.value) return false

    const file = rollbackTarget.value
    rollingBack.value = file.id
    showRollbackConfirm.value = false

    try {
      if (typeof beforeRollback === 'function') {
        await beforeRollback(file.id)
      }

      const res = await axios.post(
        `${API_BASE}${apiPrefix}/documents/${file.id}/rollback`,
        forceRollback.value ? { force: true } : {},
        { headers: authHeaders() }
      )

      await checkForChanges()

      return { documentId: file.id, baseline: res?.data?.baseline ?? null }
    } catch (e) {
      const details = e?.response?.data?.details
      if (details?.requires_force && !forceRollback.value) {
        forceRollback.value = true
        forceRollbackDetails.value = details
        showRollbackConfirm.value = true
        return false
      }
      commitError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.rollbackFailed')
      return false
    } finally {
      rollingBack.value = null
      if (!showRollbackConfirm.value) {
        rollbackTarget.value = null
        forceRollback.value = false
        forceRollbackDetails.value = null
      }
    }
  }

  function confirmRollback(file) {
    rollbackTarget.value = file
    forceRollback.value = false
    forceRollbackDetails.value = null
    showRollbackConfirm.value = true
  }

  function cancelRollback() {
    rollbackTarget.value = null
    forceRollback.value = false
    forceRollbackDetails.value = null
    showRollbackConfirm.value = false
  }

  /**
   * Restore a deleted file
   */
  async function restoreFile(file) {
    if (!file || restoringFile.value) return false

    restoringFile.value = file.id

    try {
      await axios.post(
        `${API_BASE}${apiPrefix}/documents/${file.id}/restore`,
        {},
        { headers: authHeaders() }
      )

      await checkForChanges()
      return file.id
    } catch (e) {
      loadError.value = e?.response?.data?.error || e?.message || t('workspaceGit.errors.restoreFailed')
      return false
    } finally {
      restoringFile.value = null
    }
  }

  // ============ REAL-TIME UPDATES ============

  /**
   * Update a single file's diff data (called from editor)
   */
  function updateFileDiff(data) {
    if (!data?.documentId) return

    const file = changedFiles.value.find(f => f.id === data.documentId)
    if (file) {
      if (data.insertions !== undefined) file.insertions = data.insertions
      if (data.deletions !== undefined) file.deletions = data.deletions
    }
  }

  // ============ SOCKET ============

  let socket = null
  let onSocketConnect = null

  function handleCommitCreated(payload) {
    // For single mode, check if the payload matches our entity
    if (entityMode === 'single' && payload?.prompt_id !== entityIdRef.value) return
    checkForChanges()
    loadRecentCommits()
  }

  function setupSocket() {
    socket = getSocket()
    if (!socket) return

    if (entityMode === 'single') {
      // Single entity mode (prompts)
      socket.on('prompt:commit_created', handleCommitCreated)

      onSocketConnect = () => {
        socket.emit('prompt:subscribe', { prompt_id: entityIdRef.value })
      }
    } else {
      // Workspace mode
      socket.on('latex_collab:commit_created', handleCommitCreated)

      onSocketConnect = () => {
        socket.emit('latex_collab:subscribe_workspace', { workspace_id: entityIdRef.value })
      }
    }

    if (socket.connected) {
      onSocketConnect()
    }
    socket.on('connect', onSocketConnect)
  }

  function cleanupSocket() {
    if (!socket) return

    if (entityMode === 'single') {
      socket.off('prompt:commit_created', handleCommitCreated)
      if (onSocketConnect) socket.off('connect', onSocketConnect)
      if (entityIdRef.value) {
        socket.emit('prompt:unsubscribe', { prompt_id: entityIdRef.value })
      }
    } else {
      socket.off('latex_collab:commit_created', handleCommitCreated)
      if (onSocketConnect) socket.off('connect', onSocketConnect)
      if (entityIdRef.value) {
        socket.emit('latex_collab:unsubscribe_workspace', { workspace_id: entityIdRef.value })
      }
    }
    onSocketConnect = null
  }

  // ============ LIFECYCLE ============

  function reset() {
    changedFiles.value = []
    deletedFiles.value = []
    selectedFiles.value = []
    commitMessage.value = ''
    recentCommits.value = []
    loadError.value = ''
    commitError.value = ''
  }

  async function refresh() {
    await Promise.all([checkForChanges(), loadRecentCommits()])
  }

  // Watch entity ID changes
  watch(entityIdRef, async (newId, oldId) => {
    if (oldId && oldId !== newId) {
      cleanupSocket()
    }
    reset()

    if (newId) {
      await refresh()
      setupSocket()
    }
  })

  if (autoSetup) {
    onMounted(async () => {
      if (entityIdRef.value) {
        await refresh()
        setupSocket()
      }
    })

    onUnmounted(() => {
      cleanupSocket()
    })
  }

  // ============ SINGLE MODE COMPUTED ============

  // Convenience computed for single entity mode
  const singleModeHasChanges = computed(() => {
    if (entityMode !== 'single') return false
    return summary?.value?.hasChanges === true || (summary?.value?.totalChangedLines || 0) > 0
  })

  const singleModeInsertions = computed(() => {
    if (entityMode !== 'single') return 0
    return summary?.value?.insertions || 0
  })

  const singleModeDeletions = computed(() => {
    if (entityMode !== 'single') return 0
    return summary?.value?.deletions || 0
  })

  // ============ RETURN ============

  return {
    // Config
    entityMode,

    // State
    changedFiles,
    deletedFiles,
    selectedFiles,
    checkingChanges,
    loadError,
    restoringFile,
    commitMessage,
    committing,
    commitError,
    recentCommits,
    loadingCommits,
    rollingBack,
    showRollbackConfirm,
    rollbackTarget,
    forceRollback,
    forceRollbackDetails,

    // Computed
    changedCount,
    deletedCount,
    totalChanges,
    allSelected,
    someSelected,
    totalInsertions,
    totalDeletions,
    canSubmitCommit,

    // Single mode computed
    singleModeHasChanges,
    singleModeInsertions,
    singleModeDeletions,

    // Helpers
    formatDate,
    getFileIcon,
    getFileIconColor,
    getStatusBadge,

    // Selection
    toggleFile,
    selectAll,
    deselectAll,
    toggleSelectAll,

    // API Methods
    checkForChanges,
    loadRecentCommits,
    submitCommit,
    quickCommit,
    executeRollback,
    confirmRollback,
    cancelRollback,
    restoreFile,

    // Real-time
    updateFileDiff,

    // Lifecycle
    reset,
    refresh,
    setupSocket,
    cleanupSocket
  }
}
