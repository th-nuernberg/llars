/**
 * useLatexComments.js
 *
 * Composable for managing document comments in LaTeX workspace.
 * Handles loading, creating, resolving, and deleting comments.
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
 * Create LaTeX comments composable
 * @param {Object} options - Configuration options
 * @param {Ref<Object>} options.selectedNode - Currently selected document node
 * @param {Ref<Object>} options.editorRef - Editor component ref
 * @param {Function} options.hasPermission - Permission check function
 * @returns {Object} Composable state and methods
 */
export function useLatexComments({
  selectedNode,
  editorRef,
  hasPermission
}) {
  const { t } = useI18n()
  // State
  const comments = ref([])
  const activeCommentId = ref(null)
  const commentDialog = ref(false)
  const commentDraft = ref('')
  const commentError = ref('')
  const pendingCommentRange = ref(null)

  // Computed
  const canComment = computed(() => {
    return !!(
      selectedNode.value &&
      selectedNode.value.type === 'file' &&
      !selectedNode.value.asset_id &&
      hasPermission('feature:latex_collab:edit')
    )
  })

  const canSubmitComment = computed(() => {
    return commentDraft.value.trim().length > 0 && !!pendingCommentRange.value
  })

  // Methods
  async function loadComments() {
    if (!selectedNode.value || selectedNode.value.asset_id) {
      comments.value = []
      activeCommentId.value = null
      return
    }
    try {
      const res = await axios.get(
        `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/comments`,
        { headers: authHeaders() }
      )
      comments.value = res.data?.comments || []
    } catch (e) {
      console.error('Konnte Kommentare nicht laden:', e)
      comments.value = []
    }
  }

  function openCommentDialog(presetRange = null) {
    commentError.value = ''
    const range = presetRange || editorRef.value?.getSelectionRange?.()
    if (!range || range.from === range.to) {
      commentError.value = t('latexCollab.comments.errors.selectText')
      return
    }
    pendingCommentRange.value = range
    commentDraft.value = ''
    commentDialog.value = true
  }

  async function submitComment() {
    if (!pendingCommentRange.value || !selectedNode.value) return
    commentError.value = ''
    try {
      await axios.post(
        `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/comments`,
        {
          range_start: pendingCommentRange.value.from,
          range_end: pendingCommentRange.value.to,
          body: commentDraft.value.trim()
        },
        { headers: authHeaders() }
      )
      commentDialog.value = false
      commentDraft.value = ''
      pendingCommentRange.value = null
      await loadComments()
  } catch (e) {
      commentError.value = e?.response?.data?.error || e?.message || t('latexCollab.comments.errors.saveFailed')
    }
  }

  async function toggleCommentResolved(comment) {
    if (!comment) return
    try {
      await axios.patch(
        `${API_BASE}/api/latex-collab/comments/${comment.id}`,
        { resolved: !comment.resolved_at },
        { headers: authHeaders() }
      )
      await loadComments()
    } catch (e) {
      console.error('Konnte Kommentar nicht aktualisieren:', e)
    }
  }

  async function deleteComment(comment) {
    if (!comment) return
    try {
      await axios.delete(`${API_BASE}/api/latex-collab/comments/${comment.id}`, {
        headers: authHeaders()
      })
      await loadComments()
    } catch (e) {
      console.error('Konnte Kommentar nicht loeschen:', e)
    }
  }

  function selectComment(comment) {
    activeCommentId.value = comment?.id || null
  }

  function resetComments() {
    comments.value = []
    activeCommentId.value = null
    pendingCommentRange.value = null
    commentError.value = ''
    commentDraft.value = ''
  }

  return {
    // State
    comments,
    activeCommentId,
    commentDialog,
    commentDraft,
    commentError,
    pendingCommentRange,

    // Computed
    canComment,
    canSubmitComment,

    // Methods
    loadComments,
    openCommentDialog,
    submitComment,
    toggleCommentResolved,
    deleteComment,
    selectComment,
    resetComments
  }
}
