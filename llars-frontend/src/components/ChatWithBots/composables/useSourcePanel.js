/**
 * useSourcePanel.js
 * Composable for managing source panel state and operations
 */
import { ref, watch, onUnmounted } from 'vue'
import axios from 'axios'

export function useSourcePanel() {
  // Panel state
  const sourcePanel = ref({
    open: false,
    pinned: false,
    tab: 'excerpt',
    source: null,
    documentContent: '',
    loadedDocumentId: null,
    screenshotBlobUrl: null,
    loadedScreenshotDocumentId: null,
    loadingScreenshot: false,
    screenshotError: null,
    loadingContent: false,
    contentError: null
  })

  // Source detail dialog state
  const sourceDialog = ref({
    show: false,
    source: null
  })

  // Fullscreen dialog state
  const fullscreenDialog = ref({
    show: false,
    type: null // 'screenshot' or 'document'
  })

  /**
   * Show source detail dialog
   */
  function showSourceDetail(source) {
    console.log('[useSourcePanel] showSourceDetail called with:', source)
    console.log('[useSourcePanel] sourcePanel.pinned:', sourcePanel.value.pinned)
    console.log('[useSourcePanel] sourcePanel.open:', sourcePanel.value.open)
    if (sourcePanel.value.pinned) {
      console.log('[useSourcePanel] Panel is pinned, opening in panel')
      openSourceInPanel(source)
      return
    }
    console.log('[useSourcePanel] Opening dialog')
    // Set properties individually to maintain reactivity
    sourceDialog.value.source = source
    sourceDialog.value.show = true
    console.log('[useSourcePanel] sourceDialog.show:', sourceDialog.value.show)
  }

  /**
   * Open source from citation click
   */
  function openSourceFromCitation(source) {
    if (!source) return
    sourcePanel.value.open = true
    sourcePanel.value.pinned = true
    openSourceInPanel(source)
  }

  /**
   * Toggle source panel visibility
   */
  function toggleSourcePanel() {
    if (sourcePanel.value.open) {
      closeSourcePanel()
      return
    }
    sourcePanel.value.open = true
    sourcePanel.value.pinned = true
  }

  /**
   * Close source panel
   */
  function closeSourcePanel() {
    sourcePanel.value.open = false
    sourcePanel.value.pinned = false
    sourcePanel.value.tab = 'excerpt'
  }

  /**
   * Pin source to panel from dialog
   */
  function pinSourceToPanel(source) {
    if (!source) return
    sourcePanel.value.open = true
    sourcePanel.value.pinned = true
    sourceDialog.value.show = false
    openSourceInPanel(source)
  }

  /**
   * Open a source in the panel
   */
  function openSourceInPanel(source) {
    sourcePanel.value.source = source
    sourcePanel.value.tab = 'excerpt'
    sourcePanel.value.contentError = null
    sourcePanel.value.screenshotError = null

    if (sourcePanel.value.loadedDocumentId !== source?.document_id) {
      sourcePanel.value.documentContent = ''
      sourcePanel.value.loadedDocumentId = source?.document_id || null
    }

    if (sourcePanel.value.loadedScreenshotDocumentId !== source?.document_id) {
      if (sourcePanel.value.screenshotBlobUrl && String(sourcePanel.value.screenshotBlobUrl).startsWith('blob:')) {
        URL.revokeObjectURL(sourcePanel.value.screenshotBlobUrl)
      }
      sourcePanel.value.screenshotBlobUrl = null
      sourcePanel.value.loadedScreenshotDocumentId = source?.document_id || null
    }
  }

  /**
   * Load document content for the panel
   */
  async function loadPanelDocumentContent() {
    const source = sourcePanel.value.source
    if (!source?.content_url) return
    if (sourcePanel.value.documentContent) return

    sourcePanel.value.loadingContent = true
    sourcePanel.value.contentError = null
    try {
      const response = await axios.get(source.content_url)
      if (response.data?.success) {
        sourcePanel.value.documentContent = response.data.content || ''
      } else {
        sourcePanel.value.contentError = response.data?.error || 'Konnte Dokumenttext nicht laden'
      }
    } catch (error) {
      sourcePanel.value.contentError = error.response?.data?.error || 'Konnte Dokumenttext nicht laden'
    } finally {
      sourcePanel.value.loadingContent = false
    }
  }

  /**
   * Load screenshot for the panel
   */
  async function loadPanelScreenshot() {
    const source = sourcePanel.value.source
    if (!source?.screenshot_url && !source?.document_id) return
    if (sourcePanel.value.screenshotBlobUrl) return

    const url = source.screenshot_url || `/api/rag/documents/${source.document_id}/screenshot`

    sourcePanel.value.loadingScreenshot = true
    sourcePanel.value.screenshotError = null
    try {
      const response = await axios.get(url, { responseType: 'blob' })
      sourcePanel.value.screenshotBlobUrl = URL.createObjectURL(response.data)
    } catch (error) {
      sourcePanel.value.screenshotError = error.response?.data?.error || 'Konnte Screenshot nicht laden'
      sourcePanel.value.screenshotBlobUrl = null
    } finally {
      sourcePanel.value.loadingScreenshot = false
    }
  }

  /**
   * Handle click on footnote references in message content
   */
  function handleFootnoteClick(event, sources) {
    const target = event.target
    if (target.classList.contains('footnote-ref')) {
      const footnoteId = parseInt(target.dataset.footnoteId)
      if (sources && sources.length > 0) {
        const source = sources.find(s => s.footnote_id === footnoteId)
        if (source) {
          openSourceFromCitation(source)
        }
      }
    }
  }

  /**
   * Open fullscreen dialog for screenshot or document
   */
  function openFullscreen(type) {
    fullscreenDialog.value = { show: true, type }
  }

  /**
   * Close fullscreen dialog
   */
  function closeFullscreen() {
    fullscreenDialog.value.show = false
  }

  /**
   * Reset source panel when switching conversations
   */
  function resetForConversationChange() {
    if (!sourcePanel.value.pinned) {
      sourcePanel.value.open = false
    }
    sourcePanel.value.source = null
    sourcePanel.value.tab = 'excerpt'
    fullscreenDialog.value.show = false
  }

  // Watch tab changes to load content
  watch(
    () => sourcePanel.value.tab,
    async (tab) => {
      if (tab === 'document') {
        await loadPanelDocumentContent()
      }
      if (tab === 'screenshot') {
        await loadPanelScreenshot()
      }
    }
  )

  // Cleanup blob URLs on unmount
  onUnmounted(() => {
    if (sourcePanel.value.screenshotBlobUrl && String(sourcePanel.value.screenshotBlobUrl).startsWith('blob:')) {
      URL.revokeObjectURL(sourcePanel.value.screenshotBlobUrl)
    }
  })

  return {
    // State
    sourcePanel,
    sourceDialog,
    fullscreenDialog,

    // Panel actions
    showSourceDetail,
    openSourceFromCitation,
    toggleSourcePanel,
    closeSourcePanel,
    pinSourceToPanel,
    openSourceInPanel,

    // Content loading
    loadPanelDocumentContent,
    loadPanelScreenshot,

    // Event handlers
    handleFootnoteClick,

    // Fullscreen
    openFullscreen,
    closeFullscreen,

    // Utilities
    resetForConversationChange
  }
}
