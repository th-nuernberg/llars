/**
 * useHistoryNavigation Composable Tests
 *
 * Tests for case navigation (previous, next, overview).
 * Test IDs: HIST_NAV_001 - HIST_NAV_015
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockPush = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: vi.fn(() => ({
    push: mockPush
  }))
}))

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

import axios from 'axios'
import { useHistoryNavigation } from '@/components/HistoryGenerator/HistoryGenerationDetail/composables/useHistoryNavigation'

describe('useHistoryNavigation', () => {
  let nav

  beforeEach(() => {
    vi.clearAllMocks()
    nav = useHistoryNavigation()
  })

  // ==================== fetchCaseList ====================

  describe('fetchCaseList', () => {
    it('HIST_NAV_001: fetches case list from API', async () => {
      const threads = [{ thread_id: 1 }, { thread_id: 2 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.fetchCaseList()

      expect(axios.get).toHaveBeenCalledWith('http://localhost:55080/api/email_threads/mailhistory_ratings')
      expect(result).toEqual(threads)
    })

    it('HIST_NAV_002: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await nav.fetchCaseList()

      expect(result).toEqual([])
    })
  })

  // ==================== navigateToPreviousCase ====================

  describe('navigateToPreviousCase', () => {
    it('HIST_NAV_003: navigates to previous case', async () => {
      const threads = [{ thread_id: 10 }, { thread_id: 20 }, { thread_id: 30 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToPreviousCase(20)

      expect(result).toBe(true)
      expect(mockPush).toHaveBeenCalledWith({
        name: 'HistoryGenerationDetail',
        params: { id: 10 }
      })
    })

    it('HIST_NAV_004: returns false when at first case', async () => {
      const threads = [{ thread_id: 10 }, { thread_id: 20 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToPreviousCase(10)

      expect(result).toBe(false)
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('HIST_NAV_005: returns false when case not found', async () => {
      const threads = [{ thread_id: 10 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToPreviousCase(999)

      expect(result).toBe(false)
    })

    it('HIST_NAV_006: returns false when no cases available', async () => {
      axios.get.mockResolvedValue({ data: { threads: [] } })

      const result = await nav.navigateToPreviousCase(10)

      expect(result).toBe(false)
    })

    it('HIST_NAV_007: returns false when fetch fails', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await nav.navigateToPreviousCase(10)

      expect(result).toBe(false)
    })
  })

  // ==================== navigateToNextCase ====================

  describe('navigateToNextCase', () => {
    it('HIST_NAV_008: navigates to next case', async () => {
      const threads = [{ thread_id: 10 }, { thread_id: 20 }, { thread_id: 30 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToNextCase(20)

      expect(result).toBe(true)
      expect(mockPush).toHaveBeenCalledWith({
        name: 'HistoryGenerationDetail',
        params: { id: 30 }
      })
    })

    it('HIST_NAV_009: returns false when at last case', async () => {
      const threads = [{ thread_id: 10 }, { thread_id: 20 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToNextCase(20)

      expect(result).toBe(false)
      expect(mockPush).not.toHaveBeenCalled()
    })

    it('HIST_NAV_010: returns false when case not found', async () => {
      const threads = [{ thread_id: 10 }]
      axios.get.mockResolvedValue({ data: { threads } })

      const result = await nav.navigateToNextCase(999)

      expect(result).toBe(false)
    })

    it('HIST_NAV_011: returns false when no cases', async () => {
      axios.get.mockResolvedValue({ data: { threads: [] } })

      const result = await nav.navigateToNextCase(10)

      expect(result).toBe(false)
    })
  })

  // ==================== navigateToOverview ====================

  describe('navigateToOverview', () => {
    it('HIST_NAV_012: pushes HistoryGenerator route', () => {
      nav.navigateToOverview()

      expect(mockPush).toHaveBeenCalledWith({ name: 'HistoryGenerator' })
    })
  })
})
