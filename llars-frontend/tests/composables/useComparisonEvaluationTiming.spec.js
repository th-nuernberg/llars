/**
 * Tests that useComparisonEvaluation captures per-case timing and sends it with
 * the A/B choice, so exports carry time-on-case (the "Kann KI Beratung" type).
 *
 * Test IDs: CMP_TIME_001 - CMP_TIME_002
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn()
  }
}))

function mockLoad() {
  axios.get.mockImplementation((url) => {
    if (url.endsWith('/threads/10/features')) {
      return Promise.resolve({
        data: {
          subject: 'Fall 10',
          features: [{ content: 'Antwort A' }, { content: 'Antwort B' }],
          messages: []
        }
      })
    }
    // session items list
    return Promise.resolve({ data: { items: [{ item_id: 10 }], config: {} } })
  })
  axios.post.mockResolvedValue({ data: { success: true } })
}

describe('useComparisonEvaluation timing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('CMP_TIME_001: sends numeric time_on_item_ms with the choice', async () => {
    mockLoad()
    const { useComparisonEvaluation } = await import('@/composables/useComparisonEvaluation')
    const c = useComparisonEvaluation(ref(1))

    await c.loadItems()          // auto-loads item 10 → starts the per-case timer
    await c.selectOption('A')

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url, body] = axios.post.mock.calls[0]
    expect(url).toContain('/api/evaluation/session/1/items/10/evaluate')
    expect(body.function_type).toBe('comparison')
    expect(body.choice).toBe('A')
    expect(typeof body.time_on_item_ms).toBe('number')
    expect(body.time_on_item_ms).toBeGreaterThanOrEqual(0)
  })

  it('CMP_TIME_002: time_on_item_ms is null when no item was shown', async () => {
    // No load → itemShownAt stays null → getItemId returns null → no POST.
    mockLoad()
    const { useComparisonEvaluation } = await import('@/composables/useComparisonEvaluation')
    const c = useComparisonEvaluation(ref(1))

    const res = await c.selectOption('A')
    expect(res.success).toBe(false)      // guarded: no item selected
    expect(axios.post).not.toHaveBeenCalled()
  })
})
