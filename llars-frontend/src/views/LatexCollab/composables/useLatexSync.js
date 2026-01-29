/**
 * useLatexSync.js
 *
 * Composable for SyncTeX synchronization between editor and PDF viewer.
 * Handles forward sync (source → PDF) and inverse sync (PDF → source).
 */

import { ref, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const SYNC_KEY = 'latex-collab-sync-enabled'

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Create LaTeX sync composable
 * @param {Object} options - Configuration options
 * @param {Ref<Object>} options.selectedNode - Currently selected document node
 * @param {Ref<Object>} options.pdfViewerRef - PDF viewer component ref
 * @param {Ref<number>} options.compileJobId - Current compile job ID
 * @param {Ref<boolean>} options.canSync - Whether sync is available
 * @param {Function} options.jumpToDocument - Function to navigate to a document and line
 * @returns {Object} Composable state and methods
 */
export function useLatexSync({
  selectedNode,
  pdfViewerRef,
  compileJobId,
  canSync,
  jumpToDocument
}) {
  // State
  const syncEnabled = ref(localStorage.getItem(SYNC_KEY) !== 'false')

  // Timer for debounced sync
  let syncTimer = null

  // Watchers
  watch(syncEnabled, (val) => {
    localStorage.setItem(SYNC_KEY, val ? 'true' : 'false')
    if (!val && syncTimer) {
      clearTimeout(syncTimer)
      syncTimer = null
    }
  })

  // Methods

  /**
   * Handle sync request from editor (forward sync)
   * @param {Object} payload - Sync request payload with line/column
   */
  function handleEditorSyncRequest(payload) {
    if (!syncEnabled.value || !canSync.value) return
    if (!payload || !payload.line) return
    if (!selectedNode.value || selectedNode.value.asset_id) return
    scheduleSyncToPdf(payload.line, payload.column)
  }

  /**
   * Schedule debounced forward sync to PDF
   * @param {number} line - Source line number
   * @param {number} column - Source column number
   */
  function scheduleSyncToPdf(line, column = 1) {
    if (!syncEnabled.value || !canSync.value) return
    if (syncTimer) clearTimeout(syncTimer)
    syncTimer = setTimeout(() => {
      syncSourceToPdf(line, column)
    }, 350)
  }

  /**
   * Perform forward sync (source → PDF)
   * @param {number} line - Source line number
   * @param {number} column - Source column number
   */
  async function syncSourceToPdf(line, column = 1) {
    if (!compileJobId.value || !selectedNode.value) return
    try {
      const res = await axios.post(
        `${API_BASE}/api/latex-collab/compile/${compileJobId.value}/synctex/forward`,
        {
          document_id: selectedNode.value.id,
          line,
          column
        },
        { headers: authHeaders() }
      )
      if (res.data?.success === false) return
      const location = res.data?.location
      if (location) {
        pdfViewerRef.value?.scrollToLocation?.(location)
      }
    } catch (e) {
      // Ignore sync errors to avoid blocking editor usage
    }
  }

  /**
   * Handle PDF click for inverse sync (PDF → source)
   * @param {Object} payload - Click payload with page, x, y coordinates
   */
  async function handlePdfClick(payload) {
    if (!syncEnabled.value || !canSync.value) return
    if (!payload || !payload.page) return
    if (!compileJobId.value) return

    try {
      const res = await axios.post(
        `${API_BASE}/api/latex-collab/compile/${compileJobId.value}/synctex/inverse`,
        {
          page: payload.page,
          x: payload.x,
          y: payload.y
        },
        { headers: authHeaders() }
      )
      if (res.data?.success === false) return
      const location = res.data?.location
      if (!location) return
      if (!location.document_id) return
      jumpToDocument(location.document_id, location.line || 1, location.column || 1)
    } catch (e) {
      // Ignore sync errors to avoid interrupting normal PDF usage
    }
  }

  // Cleanup
  onUnmounted(() => {
    if (syncTimer) clearTimeout(syncTimer)
  })

  return {
    // State
    syncEnabled,

    // Methods
    handleEditorSyncRequest,
    scheduleSyncToPdf,
    syncSourceToPdf,
    handlePdfClick
  }
}
