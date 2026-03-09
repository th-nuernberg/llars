/**
 * useFullscreen Composable Tests
 *
 * Tests for fullscreen mode toggling (single and multi-worker).
 * Test IDs: FULL_001 - FULL_012
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useFullscreen } from '@/components/Judge/JudgeSession/composables/useFullscreen'

describe('useFullscreen', () => {
  let state
  let api
  let fullscreen

  beforeEach(() => {
    state = {
      session: ref({ status: 'running' }),
      fullscreenMode: ref(false),
      autoScrollEnabled: ref(false),
      multiWorkerFullscreenMode: ref(false),
      multiWorkerDisplayMode: ref('grid'),
      focusedWorkerId: ref(null),
      reconnecting: ref(false),
      isStreaming: ref(false)
    }

    api = {
      loadWorkerPoolStatus: vi.fn().mockResolvedValue(undefined)
    }

    fullscreen = useFullscreen(state, api)
  })

  // ==================== Single Worker Fullscreen ====================

  describe('openFullscreen', () => {
    it('FULL_001: sets fullscreenMode to true', () => {
      fullscreen.openFullscreen()
      expect(state.fullscreenMode.value).toBe(true)
    })

    it('FULL_002: enables auto scroll', () => {
      fullscreen.openFullscreen()
      expect(state.autoScrollEnabled.value).toBe(true)
    })

    it('FULL_003: calls reconnect when session is running and not streaming', () => {
      const reconnect = vi.fn()
      fullscreen.openFullscreen(reconnect)
      expect(reconnect).toHaveBeenCalled()
    })

    it('FULL_004: does not reconnect when already streaming', () => {
      state.isStreaming.value = true
      const reconnect = vi.fn()
      fullscreen.openFullscreen(reconnect)
      expect(reconnect).not.toHaveBeenCalled()
    })

    it('FULL_005: does not reconnect when session is not running', () => {
      state.session.value = { status: 'completed' }
      const reconnect = vi.fn()
      fullscreen.openFullscreen(reconnect)
      expect(reconnect).not.toHaveBeenCalled()
    })

    it('FULL_006: handles no reconnect function', () => {
      expect(() => fullscreen.openFullscreen()).not.toThrow()
    })
  })

  describe('closeFullscreen', () => {
    it('FULL_007: sets fullscreenMode to false', () => {
      state.fullscreenMode.value = true
      fullscreen.closeFullscreen()
      expect(state.fullscreenMode.value).toBe(false)
    })
  })

  // ==================== Multi-Worker Fullscreen ====================

  describe('openMultiWorkerFullscreen', () => {
    it('FULL_008: sets multiWorkerFullscreenMode to true', async () => {
      await fullscreen.openMultiWorkerFullscreen()
      expect(state.multiWorkerFullscreenMode.value).toBe(true)
    })

    it('FULL_009: loads worker pool status', async () => {
      await fullscreen.openMultiWorkerFullscreen()
      expect(api.loadWorkerPoolStatus).toHaveBeenCalled()
    })
  })

  describe('closeMultiWorkerFullscreen', () => {
    it('FULL_010: sets multiWorkerFullscreenMode to false', () => {
      state.multiWorkerFullscreenMode.value = true
      fullscreen.closeMultiWorkerFullscreen()
      expect(state.multiWorkerFullscreenMode.value).toBe(false)
    })
  })

  describe('openWorkerFullscreen', () => {
    it('FULL_011: sets focused worker and opens fullscreen', async () => {
      await fullscreen.openWorkerFullscreen(3)
      expect(state.focusedWorkerId.value).toBe(3)
      expect(state.multiWorkerDisplayMode.value).toBe('focus')
      expect(state.multiWorkerFullscreenMode.value).toBe(true)
    })

    it('FULL_012: loads worker pool status for focused worker', async () => {
      await fullscreen.openWorkerFullscreen(0)
      expect(api.loadWorkerPoolStatus).toHaveBeenCalled()
    })
  })
})
