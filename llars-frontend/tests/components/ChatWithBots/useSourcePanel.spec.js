/**
 * useSourcePanel Composable Tests
 *
 * Tests for source panel state management, content loading, and citation handling.
 * Test IDs: SRC_PNL_001 - SRC_PNL_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: vi.fn()
  }
})

import axios from 'axios'
import { useSourcePanel } from '@/components/ChatWithBots/composables/useSourcePanel'

describe('useSourcePanel', () => {
  let panel

  beforeEach(() => {
    vi.clearAllMocks()
    panel = useSourcePanel()
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('SRC_PNL_001: panel starts closed', () => {
      expect(panel.sourcePanel.value.open).toBe(false)
    })

    it('SRC_PNL_002: panel starts unpinned', () => {
      expect(panel.sourcePanel.value.pinned).toBe(false)
    })

    it('SRC_PNL_003: default tab is excerpt', () => {
      expect(panel.sourcePanel.value.tab).toBe('excerpt')
    })

    it('SRC_PNL_004: source starts null', () => {
      expect(panel.sourcePanel.value.source).toBeNull()
    })

    it('SRC_PNL_005: dialog starts hidden', () => {
      expect(panel.sourceDialog.value.show).toBe(false)
    })

    it('SRC_PNL_006: fullscreen starts hidden', () => {
      expect(panel.fullscreenDialog.value.show).toBe(false)
    })
  })

  // ==================== Toggle / Open / Close ====================

  describe('toggleSourcePanel', () => {
    it('SRC_PNL_007: opens and pins panel when closed', () => {
      panel.toggleSourcePanel()

      expect(panel.sourcePanel.value.open).toBe(true)
      expect(panel.sourcePanel.value.pinned).toBe(true)
    })

    it('SRC_PNL_008: closes panel when open', () => {
      panel.sourcePanel.value.open = true
      panel.sourcePanel.value.pinned = true

      panel.toggleSourcePanel()

      expect(panel.sourcePanel.value.open).toBe(false)
      expect(panel.sourcePanel.value.pinned).toBe(false)
    })
  })

  describe('closeSourcePanel', () => {
    it('SRC_PNL_009: closes panel and resets state', () => {
      panel.sourcePanel.value.open = true
      panel.sourcePanel.value.pinned = true
      panel.sourcePanel.value.tab = 'document'

      panel.closeSourcePanel()

      expect(panel.sourcePanel.value.open).toBe(false)
      expect(panel.sourcePanel.value.pinned).toBe(false)
      expect(panel.sourcePanel.value.tab).toBe('excerpt')
    })
  })

  // ==================== Source Detail ====================

  describe('showSourceDetail', () => {
    it('SRC_PNL_010: opens dialog when panel not pinned', () => {
      const source = { id: 1, title: 'Test' }

      panel.showSourceDetail(source)

      expect(panel.sourceDialog.value.show).toBe(true)
      expect(panel.sourceDialog.value.source).toEqual(source)
    })

    it('SRC_PNL_011: opens in panel when pinned', () => {
      panel.sourcePanel.value.pinned = true
      const source = { id: 1, title: 'Test', document_id: 'doc-1' }

      panel.showSourceDetail(source)

      expect(panel.sourcePanel.value.source).toEqual(source)
      expect(panel.sourceDialog.value.show).toBe(false)
    })
  })

  describe('openSourceFromCitation', () => {
    it('SRC_PNL_012: opens panel with source from citation', () => {
      const source = { id: 1, document_id: 'doc-1' }

      panel.openSourceFromCitation(source)

      expect(panel.sourcePanel.value.open).toBe(true)
      expect(panel.sourcePanel.value.pinned).toBe(true)
      expect(panel.sourcePanel.value.source).toEqual(source)
    })

    it('SRC_PNL_013: does nothing for null source', () => {
      panel.openSourceFromCitation(null)

      expect(panel.sourcePanel.value.open).toBe(false)
    })
  })

  describe('pinSourceToPanel', () => {
    it('SRC_PNL_014: pins source and closes dialog', () => {
      panel.sourceDialog.value.show = true
      const source = { id: 1, document_id: 'doc-1' }

      panel.pinSourceToPanel(source)

      expect(panel.sourcePanel.value.open).toBe(true)
      expect(panel.sourcePanel.value.pinned).toBe(true)
      expect(panel.sourceDialog.value.show).toBe(false)
    })

    it('SRC_PNL_015: does nothing for null source', () => {
      panel.pinSourceToPanel(null)

      expect(panel.sourcePanel.value.open).toBe(false)
    })
  })

  // ==================== Content Loading ====================

  describe('loadPanelDocumentContent', () => {
    it('SRC_PNL_016: loads document content', async () => {
      panel.sourcePanel.value.source = { content_url: '/api/doc/1' }
      axios.get.mockResolvedValue({ data: { success: true, content: 'Document text' } })

      await panel.loadPanelDocumentContent()

      expect(panel.sourcePanel.value.documentContent).toBe('Document text')
      expect(panel.sourcePanel.value.loadingContent).toBe(false)
    })

    it('SRC_PNL_017: sets error on failed load', async () => {
      panel.sourcePanel.value.source = { content_url: '/api/doc/1' }
      axios.get.mockRejectedValue({ response: { data: { error: 'Not found' } } })

      await panel.loadPanelDocumentContent()

      expect(panel.sourcePanel.value.contentError).toBe('Not found')
      expect(panel.sourcePanel.value.loadingContent).toBe(false)
    })

    it('SRC_PNL_018: skips loading if no content_url', async () => {
      panel.sourcePanel.value.source = {}

      await panel.loadPanelDocumentContent()

      expect(axios.get).not.toHaveBeenCalled()
    })

    it('SRC_PNL_019: skips loading if content already loaded', async () => {
      panel.sourcePanel.value.source = { content_url: '/api/doc/1' }
      panel.sourcePanel.value.documentContent = 'Already loaded'

      await panel.loadPanelDocumentContent()

      expect(axios.get).not.toHaveBeenCalled()
    })
  })

  describe('loadPanelScreenshot', () => {
    it('SRC_PNL_020: loads screenshot', async () => {
      panel.sourcePanel.value.source = { screenshot_url: '/api/doc/1/screenshot' }
      const blob = new Blob(['image'])
      axios.get.mockResolvedValue({ data: blob })
      global.URL.createObjectURL = vi.fn(() => 'blob:test')

      await panel.loadPanelScreenshot()

      expect(panel.sourcePanel.value.screenshotBlobUrl).toBe('blob:test')
      expect(panel.sourcePanel.value.loadingScreenshot).toBe(false)
    })

    it('SRC_PNL_021: sets error on failed screenshot load', async () => {
      panel.sourcePanel.value.source = { document_id: 'doc-1' }
      axios.get.mockRejectedValue({ response: { data: { error: 'No screenshot' } } })

      await panel.loadPanelScreenshot()

      expect(panel.sourcePanel.value.screenshotError).toBe('No screenshot')
    })

    it('SRC_PNL_022: skips if already loaded', async () => {
      panel.sourcePanel.value.source = { screenshot_url: '/api/doc/1/screenshot' }
      panel.sourcePanel.value.screenshotBlobUrl = 'blob:existing'

      await panel.loadPanelScreenshot()

      expect(axios.get).not.toHaveBeenCalled()
    })
  })

  // ==================== Footnote Click ====================

  describe('handleFootnoteClick', () => {
    it('SRC_PNL_023: opens source for footnote click', () => {
      const sources = [{ footnote_id: 1, title: 'Source 1' }]
      const event = {
        target: {
          classList: { contains: vi.fn((cls) => cls === 'footnote-ref') },
          dataset: { footnoteId: '1' }
        }
      }

      panel.handleFootnoteClick(event, sources)

      expect(panel.sourcePanel.value.open).toBe(true)
      expect(panel.sourcePanel.value.source).toEqual(sources[0])
    })

    it('SRC_PNL_024: ignores non-footnote clicks', () => {
      const event = {
        target: {
          classList: { contains: vi.fn(() => false) },
          dataset: {}
        }
      }

      panel.handleFootnoteClick(event, [])

      expect(panel.sourcePanel.value.open).toBe(false)
    })
  })

  // ==================== Fullscreen ====================

  describe('fullscreen', () => {
    it('SRC_PNL_025: opens fullscreen dialog', () => {
      panel.openFullscreen('screenshot')

      expect(panel.fullscreenDialog.value.show).toBe(true)
      expect(panel.fullscreenDialog.value.type).toBe('screenshot')
    })

    it('SRC_PNL_026: closes fullscreen dialog', () => {
      panel.fullscreenDialog.value.show = true
      panel.closeFullscreen()

      expect(panel.fullscreenDialog.value.show).toBe(false)
    })
  })

  // ==================== Reset ====================

  describe('resetForConversationChange', () => {
    it('SRC_PNL_027: closes panel when not pinned', () => {
      panel.sourcePanel.value.open = true
      panel.sourcePanel.value.pinned = false

      panel.resetForConversationChange()

      expect(panel.sourcePanel.value.open).toBe(false)
    })

    it('SRC_PNL_028: keeps panel open when pinned', () => {
      panel.sourcePanel.value.open = true
      panel.sourcePanel.value.pinned = true

      panel.resetForConversationChange()

      expect(panel.sourcePanel.value.open).toBe(true)
    })

    it('SRC_PNL_029: resets source and tab', () => {
      panel.sourcePanel.value.source = { id: 1 }
      panel.sourcePanel.value.tab = 'document'

      panel.resetForConversationChange()

      expect(panel.sourcePanel.value.source).toBeNull()
      expect(panel.sourcePanel.value.tab).toBe('excerpt')
    })
  })
})
