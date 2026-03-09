/**
 * useRankerApi Composable Tests
 *
 * Tests for email thread, ranking, and navigation API calls.
 * Test IDs: RANK_API_001 - RANK_API_015
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

import axios from 'axios'
import { useRankerApi } from '@/components/Ranker/RankerDetail/composables/useRankerApi'

describe('useRankerApi', () => {
  let api

  beforeEach(() => {
    vi.clearAllMocks()
    api = useRankerApi()
  })

  describe('fetchEmailThreads', () => {
    it('RANK_API_001: fetches email threads for thread ID', async () => {
      const mockData = { messages: [], features: [] }
      axios.get.mockResolvedValue({ data: mockData })

      const result = await api.fetchEmailThreads(42)

      expect(axios.get).toHaveBeenCalledWith('http://localhost:55080/api/email_threads/rankings/42')
      expect(result).toEqual(mockData)
    })

    it('RANK_API_002: returns null on error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const result = await api.fetchEmailThreads(42)

      expect(result).toBeNull()
    })
  })

  describe('fetchServerRanking', () => {
    it('RANK_API_003: fetches current ranking', async () => {
      const mockRanking = { ranking: [1, 2, 3] }
      axios.get.mockResolvedValue({ data: mockRanking })

      const result = await api.fetchServerRanking(42)

      expect(axios.get).toHaveBeenCalledWith('http://localhost:55080/api/email_threads/42/current_ranking')
      expect(result).toEqual(mockRanking)
    })

    it('RANK_API_004: returns null on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await api.fetchServerRanking(42)

      expect(result).toBeNull()
    })
  })

  describe('fetchRankingThreads', () => {
    it('RANK_API_005: fetches thread list for navigation', async () => {
      const threads = [{ thread_id: 1 }, { thread_id: 2 }]
      axios.get.mockResolvedValue({ data: threads })

      const result = await api.fetchRankingThreads()

      expect(axios.get).toHaveBeenCalledWith('http://localhost:55080/api/email_threads/feature_ranking_list')
      expect(result).toEqual(threads)
    })

    it('RANK_API_006: returns empty array on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await api.fetchRankingThreads()

      expect(result).toEqual([])
    })
  })

  describe('fetchTotalCases', () => {
    it('RANK_API_007: returns count of total cases', async () => {
      axios.get.mockResolvedValue({ data: [{}, {}, {}] })

      const result = await api.fetchTotalCases()

      expect(result).toBe(3)
    })

    it('RANK_API_008: returns 0 on error', async () => {
      axios.get.mockRejectedValue(new Error('fail'))

      const result = await api.fetchTotalCases()

      expect(result).toBe(0)
    })
  })

  describe('saveRankingToServer', () => {
    it('RANK_API_009: saves ranking successfully', async () => {
      const features = [{ id: 1, rank: 1 }]
      axios.post.mockResolvedValue({ data: { success: true } })

      const result = await api.saveRankingToServer(42, features)

      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:55080/api/save_ranking/42',
        features,
        { headers: { 'Content-Type': 'application/json' } }
      )
      expect(result.success).toBe(true)
    })

    it('RANK_API_010: returns error result on failure', async () => {
      axios.post.mockRejectedValue(new Error('fail'))

      const result = await api.saveRankingToServer(42, [])

      expect(result.success).toBe(false)
      expect(result.error).toBeDefined()
    })
  })
})
