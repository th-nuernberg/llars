/**
 * useHistoryRatings Composable Tests
 *
 * Tests for ratings state, localStorage persistence, change detection, and API saving.
 * Test IDs: HIST_RAT_001 - HIST_RAT_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

vi.mock('@/components/HistoryGenerator/HistoryGenerationDetail/composables/useHistoryHelpers', () => ({
  useHistoryHelpers: vi.fn(() => ({
    checkIfDisabled: vi.fn(() => false),
    toggleClassForDiv: vi.fn()
  }))
}))

import axios from 'axios'
import { useHistoryRatings } from '@/components/HistoryGenerator/HistoryGenerationDetail/composables/useHistoryRatings'

describe('useHistoryRatings', () => {
  let ratings

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
    ratings = useHistoryRatings(ref(42))
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('HIST_RAT_001: starts with empty messages', () => {
      expect(ratings.messages.value).toEqual([])
    })

    it('HIST_RAT_002: starts with null ratings', () => {
      expect(ratings.ratings.value).toEqual({
        counsellor_coherence: null,
        client_coherence: null,
        quality: null,
        overall: null
      })
    })

    it('HIST_RAT_003: starts with null feedback', () => {
      expect(ratings.feedback.value).toBeNull()
    })

    it('HIST_RAT_004: starts with null selectedCategoryId', () => {
      expect(ratings.selectedCategoryId.value).toBeNull()
    })

    it('HIST_RAT_005: starts with null ratedStatus', () => {
      expect(ratings.ratedStatus.value).toBeNull()
    })

    it('HIST_RAT_006: starts with no unsaved changes', () => {
      expect(ratings.hasUnsavedChanges.value).toBe(false)
    })

    it('HIST_RAT_007: starts with all scales enabled', () => {
      expect(ratings.isDisabled.value).toEqual({
        counsellor_coherence: false,
        client_coherence: false,
        quality: false,
        overall: false
      })
    })
  })

  // ==================== rateMessage ====================

  describe('rateMessage', () => {
    it('HIST_RAT_008: sets message rating', () => {
      ratings.messages.value = [
        { message_id: 1, content: 'msg1', rating: null },
        { message_id: 2, content: 'msg2', rating: null }
      ]

      ratings.rateMessage(0, 3)

      expect(ratings.messages.value[0].rating).toBe(3)
    })

    it('HIST_RAT_009: toggles off same rating', () => {
      ratings.messages.value = [
        { message_id: 1, content: 'msg1', rating: 3 }
      ]

      ratings.rateMessage(0, 3)

      expect(ratings.messages.value[0].rating).toBeNull()
    })

    it('HIST_RAT_010: saves to localStorage after rating', () => {
      ratings.messages.value = [
        { message_id: 1, content: 'msg1', rating: null }
      ]

      ratings.rateMessage(0, 4)

      expect(localStorage.setItem).toHaveBeenCalled()
    })
  })

  // ==================== handleCategorySelection ====================

  describe('handleCategorySelection', () => {
    it('HIST_RAT_011: sets category ID and notes', () => {
      ratings.handleCategorySelection({
        categoryId: 5,
        categoryNotes: 'Test notes'
      })

      expect(ratings.selectedCategoryId.value).toBe(5)
      expect(ratings.categoryNotes.value).toBe('Test notes')
    })
  })

  // ==================== initializeData ====================

  describe('initializeData', () => {
    it('HIST_RAT_012: fetches and combines messages with ratings', async () => {
      axios.get
        .mockResolvedValueOnce({
          data: {
            messages: [
              { message_id: 1, content: 'msg1' },
              { message_id: 2, content: 'msg2' }
            ]
          }
        })
        .mockResolvedValueOnce({
          data: [
            { message_id: 1, rating: 4 }
          ]
        })
        .mockResolvedValueOnce({
          data: {
            rating: {
              counsellor_coherence_rating: 3,
              client_coherence_rating: 2,
              quality_rating: 4,
              overall_rating: 3,
              feedback: 'Good quality',
              rating_status: 'Rated'
            },
            consulting_category: {
              consulting_category_type_id: 5,
              consulting_category_note: 'Note'
            }
          }
        })

      await ratings.initializeData()

      expect(ratings.messages.value).toHaveLength(2)
      expect(ratings.messages.value[0].rating).toBe(4)
      expect(ratings.messages.value[1].rating).toBeNull()
      expect(ratings.ratings.value.counsellor_coherence).toBe(3)
      expect(ratings.feedback.value).toBe('Good quality')
      expect(ratings.ratedStatus.value).toBe('Rated')
    })

    it('HIST_RAT_013: sets Not Rated when no ratings exist', async () => {
      axios.get
        .mockResolvedValueOnce({ data: { messages: [] } })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: null })

      await ratings.initializeData()

      expect(ratings.ratedStatus.value).toBe('Not Rated')
    })

    it('HIST_RAT_014: converts 0 ratings to null', async () => {
      axios.get
        .mockResolvedValueOnce({ data: { messages: [] } })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({
          data: {
            rating: {
              counsellor_coherence_rating: 0,
              client_coherence_rating: 0,
              quality_rating: 0,
              overall_rating: 0,
              feedback: null,
              rating_status: 'Rated'
            },
            consulting_category: {
              consulting_category_type_id: null,
              consulting_category_note: null
            }
          }
        })

      await ratings.initializeData()

      expect(ratings.ratings.value.counsellor_coherence).toBeNull()
      expect(ratings.ratings.value.client_coherence).toBeNull()
    })
  })

  // ==================== saveRatingServerSide ====================

  describe('saveRatingServerSide', () => {
    it('HIST_RAT_015: saves ratings and messages to server', async () => {
      ratings.messages.value = [
        { message_id: 1, content: 'msg', rating: 3 }
      ]
      ratings.ratings.value = {
        counsellor_coherence: 3,
        client_coherence: 2,
        quality: 4,
        overall: 3
      }
      ratings.feedback.value = 'Good'
      ratings.selectedCategoryId.value = 5

      // Mock both save calls and the reinit calls
      axios.post.mockResolvedValue({})
      axios.get
        .mockResolvedValueOnce({ data: { messages: [] } })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: null })

      window.alert = vi.fn()

      await ratings.saveRatingServerSide()

      expect(axios.post).toHaveBeenCalledTimes(2)
      // First call: mailhistory ratings
      expect(axios.post.mock.calls[0][0]).toContain('save_mailhistory_rating/42')
      // Second call: message ratings
      expect(axios.post.mock.calls[1][0]).toContain('save_message_ratings/42')
    })

    it('HIST_RAT_016: clears localStorage after successful save', async () => {
      ratings.messages.value = []
      ratings.ratings.value = {
        counsellor_coherence: null,
        client_coherence: null,
        quality: null,
        overall: null
      }

      axios.post.mockResolvedValue({})
      axios.get
        .mockResolvedValueOnce({ data: { messages: [] } })
        .mockResolvedValueOnce({ data: [] })
        .mockResolvedValueOnce({ data: null })

      window.alert = vi.fn()

      await ratings.saveRatingServerSide()

      expect(localStorage.removeItem).toHaveBeenCalledWith('local_rating_changes_42')
      expect(localStorage.removeItem).toHaveBeenCalledWith('local_messageRating_changes_42')
    })
  })
})
