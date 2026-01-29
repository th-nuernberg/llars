/**
 * useLatexComments.js
 *
 * Composable for managing workspace-wide comments in LaTeX workspace.
 * Shows all comments across all documents in the workspace.
 * Handles loading, creating, resolving, and deleting comments.
 * Supports real-time sync via Socket.IO events.
 */

import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Create LaTeX comments composable
 * @param {Object} options - Configuration options
 * @param {Ref<number>} options.workspaceId - Current workspace ID
 * @param {Ref<Object>} options.selectedNode - Currently selected document node
 * @param {Ref<Object>} options.editorRef - Editor component ref
 * @param {Function} options.hasPermission - Permission check function
 * @param {Function} options.onNavigateToDocument - Callback to navigate to a document
 * @param {Ref<Socket>} options.socket - Socket.IO instance for real-time updates
 * @returns {Object} Composable state and methods
 */
export function useLatexComments({
  workspaceId,
  selectedNode,
  editorRef,
  hasPermission,
  onNavigateToDocument = null,
  socket = null
}) {
  const { t } = useI18n()
  let currentWorkspaceId = null
  // State
  const comments = ref([])
  const activeCommentId = ref(null)
  const commentDialog = ref(false)
  const commentDraft = ref('')
  const commentError = ref('')
  const pendingCommentRange = ref(null)
  // Reply state
  const replyingToId = ref(null)
  const replyDraft = ref('')

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

  const canSubmitReply = computed(() => {
    return replyDraft.value.trim().length > 0 && !!replyingToId.value
  })

  // Methods

  /**
   * Load all comments for the workspace (across all documents)
   */
  async function loadComments() {
    const wsId = workspaceId?.value
    if (!wsId) {
      comments.value = []
      activeCommentId.value = null
      return
    }
    try {
      const res = await axios.get(
        `${API_BASE}/api/latex-collab/workspaces/${wsId}/comments`,
        { headers: authHeaders() }
      )
      comments.value = res.data?.comments || []
    } catch (e) {
      console.error('Konnte Kommentare nicht laden:', e)
      comments.value = []
    }
  }

  /**
   * Navigate to a comment's document and highlight the comment range
   * @param {Object} comment - The comment to navigate to
   */
  function navigateToComment(comment) {
    if (!comment || !comment.document_id) return

    // Compare as numbers to avoid string/number type mismatch
    const currentDocId = selectedNode.value?.id
    const targetDocId = comment.document_id
    const isSameDocument = currentDocId != null && Number(currentDocId) === Number(targetDocId)

    // Always set the comment as active
    selectComment(comment)

    if (!isSameDocument) {
      // Different document - navigate there first, then highlight
      if (onNavigateToDocument) {
        onNavigateToDocument(targetDocId, comment)
      }
    } else {
      // Same document - just highlight/scroll to the range
      highlightCommentRange(comment)
    }
  }

  /**
   * Highlight a comment's range in the editor
   * Only highlights if the comment belongs to the currently selected document.
   * @param {Object} comment - The comment with range_start and range_end
   */
  function highlightCommentRange(comment) {
    if (!comment || comment.range_start == null || comment.range_end == null) return
    if (!editorRef?.value?.highlightRange) return

    // Only highlight if comment belongs to current document (compare as numbers)
    const currentDocId = selectedNode.value?.id
    const commentDocId = comment.document_id
    if (currentDocId == null || Number(commentDocId) !== Number(currentDocId)) return

    editorRef.value.highlightRange(comment.range_start, comment.range_end)
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

  /**
   * Submit a new top-level comment
   * @param {string} authorColor - Optional author color (hex)
   */
  async function submitComment(authorColor = null) {
    if (!pendingCommentRange.value || !selectedNode.value) return
    commentError.value = ''
    try {
      await axios.post(
        `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/comments`,
        {
          range_start: pendingCommentRange.value.from,
          range_end: pendingCommentRange.value.to,
          body: commentDraft.value.trim(),
          author_color: authorColor
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
    replyingToId.value = null
    replyDraft.value = ''
  }

  /**
   * Start replying to a comment
   * @param {number} commentId - The parent comment ID to reply to
   */
  function startReply(commentId) {
    replyingToId.value = commentId
    replyDraft.value = ''
    commentError.value = ''
  }

  /**
   * Cancel the current reply
   */
  function cancelReply() {
    replyingToId.value = null
    replyDraft.value = ''
  }

  /**
   * Submit a reply to a comment
   * @param {string} authorColor - Optional author color (hex)
   */
  async function submitReply(authorColor = null) {
    if (!replyingToId.value) return
    commentError.value = ''
    try {
      await axios.post(
        `${API_BASE}/api/latex-collab/comments/${replyingToId.value}/replies`,
        {
          body: replyDraft.value.trim(),
          author_color: authorColor
        },
        { headers: authHeaders() }
      )
      replyingToId.value = null
      replyDraft.value = ''
      await loadComments()
    } catch (e) {
      commentError.value = e?.response?.data?.error || e?.message || t('latexCollab.comments.errors.saveFailed')
    }
  }

  // ============================================================
  // Socket.IO Real-time Sync (Workspace-level)
  // ============================================================

  /**
   * Handle incoming workspace comment change events from other users
   */
  function handleWorkspaceCommentChanged(data) {
    if (!data || data.workspace_id !== currentWorkspaceId) return

    const { action, comment } = data

    switch (action) {
      case 'created':
        // Add new comment at the beginning (newest first)
        if (comment && !comments.value.find(c => c.id === comment.id)) {
          comments.value = [comment, ...comments.value]
        }
        break

      case 'updated':
        // Update existing comment
        if (comment) {
          const idx = comments.value.findIndex(c => c.id === comment.id)
          if (idx !== -1) {
            comments.value = [
              ...comments.value.slice(0, idx),
              comment,
              ...comments.value.slice(idx + 1)
            ]
          }
        }
        break

      case 'deleted':
        // Remove deleted comment
        if (comment?.id) {
          comments.value = comments.value.filter(c => c.id !== comment.id)
          if (activeCommentId.value === comment.id) {
            activeCommentId.value = null
          }
        }
        break

      case 'reply_created':
        // Add reply to parent comment
        if (comment?.parent_id && comment?.reply) {
          const idx = comments.value.findIndex(c => c.id === comment.parent_id)
          if (idx !== -1) {
            const parent = comments.value[idx]
            const replies = parent.replies || []
            // Check if reply already exists
            if (!replies.find(r => r.id === comment.reply.id)) {
              const updatedParent = {
                ...parent,
                replies: [...replies, comment.reply]
              }
              comments.value = [
                ...comments.value.slice(0, idx),
                updatedParent,
                ...comments.value.slice(idx + 1)
              ]
            }
          }
        }
        break
    }
  }

  function updateCommentTreeColor(node, username, color) {
    if (!node) return { updated: node, changed: false }

    let changed = false
    let nextNode = node

    if (node.author_username === username && node.author_color !== color) {
      nextNode = { ...nextNode, author_color: color }
      changed = true
    }

    if (Array.isArray(node.replies) && node.replies.length > 0) {
      const updatedReplies = []
      let repliesChanged = false
      for (const reply of node.replies) {
        const { updated, changed: replyChanged } = updateCommentTreeColor(reply, username, color)
        updatedReplies.push(updated)
        if (replyChanged) repliesChanged = true
      }
      if (repliesChanged) {
        nextNode = nextNode === node ? { ...node, replies: updatedReplies } : { ...nextNode, replies: updatedReplies }
        changed = true
      }
    }

    return { updated: nextNode, changed }
  }

  function handleUserColorUpdated(payload) {
    const username = payload?.username
    const color = payload?.collab_color ?? null
    if (!username) return

    let anyChanged = false
    const next = comments.value.map((comment) => {
      const { updated, changed } = updateCommentTreeColor(comment, username, color)
      if (changed) anyChanged = true
      return updated
    })

    if (anyChanged) {
      comments.value = next
    }
  }

  /**
   * Subscribe to workspace comment updates
   */
  function subscribeToWorkspace(wsId) {
    if (!socket?.value || !wsId) return

    // Unsubscribe from previous workspace
    if (currentWorkspaceId && currentWorkspaceId !== wsId) {
      socket.value.emit('latex_collab:unsubscribe_workspace', { workspace_id: currentWorkspaceId })
    }

    currentWorkspaceId = wsId
    socket.value.emit('latex_collab:subscribe_workspace', { workspace_id: wsId })
  }

  /**
   * Unsubscribe from workspace comment updates
   */
  function unsubscribeFromWorkspace() {
    if (!socket?.value || !currentWorkspaceId) return
    socket.value.emit('latex_collab:unsubscribe_workspace', { workspace_id: currentWorkspaceId })
    currentWorkspaceId = null
  }

  /**
   * Setup socket event listeners
   */
  function setupSocketListeners() {
    if (!socket?.value) return

    socket.value.on('latex_collab:workspace_comment_changed', handleWorkspaceCommentChanged)
    socket.value.on('user:collab_color_updated', handleUserColorUpdated)
  }

  /**
   * Cleanup socket event listeners
   */
  function cleanupSocketListeners() {
    if (!socket?.value) return

    socket.value.off('latex_collab:workspace_comment_changed', handleWorkspaceCommentChanged)
    socket.value.off('user:collab_color_updated', handleUserColorUpdated)
    unsubscribeFromWorkspace()
  }

  // Watch for workspace changes and subscribe
  if (socket) {
    watch(
      () => workspaceId?.value,
      (newWsId) => {
        if (newWsId) {
          subscribeToWorkspace(newWsId)
          loadComments()
        } else {
          unsubscribeFromWorkspace()
        }
      },
      { immediate: true }
    )

    // Setup listeners when socket becomes available
    watch(
      () => socket.value,
      (newSocket) => {
        if (newSocket) {
          setupSocketListeners()
          // Subscribe to current workspace if any
          if (workspaceId?.value) {
            subscribeToWorkspace(workspaceId.value)
          }
        }
      },
      { immediate: true }
    )

    // Cleanup on unmount
    onUnmounted(() => {
      cleanupSocketListeners()
    })
  }

  return {
    // State
    comments,
    activeCommentId,
    commentDialog,
    commentDraft,
    commentError,
    pendingCommentRange,
    replyingToId,
    replyDraft,

    // Computed
    canComment,
    canSubmitComment,
    canSubmitReply,

    // Methods
    loadComments,
    openCommentDialog,
    submitComment,
    toggleCommentResolved,
    deleteComment,
    selectComment,
    resetComments,
    startReply,
    cancelReply,
    submitReply,
    navigateToComment,
    highlightCommentRange
  }
}
