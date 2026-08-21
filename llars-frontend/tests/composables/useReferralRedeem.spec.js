/**
 * useReferralRedeem Composable Tests
 *
 * Tests the authenticated "redeem invitation code" flow used in
 * UserSettings > Personal. Test IDs: REDEEM_001 - REDEEM_006
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: { post: vi.fn() }
}))

import axios from 'axios'
import { useReferralRedeem } from '@/composables/useReferralRedeem'

describe('useReferralRedeem', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('REDEEM_001: posts the trimmed code and returns success data', async () => {
    axios.post.mockResolvedValue({
      data: { success: true, target_scenario_id: 7, role: 'evaluator', already_enrolled: false }
    })
    const { redeem, result } = useReferralRedeem()

    const res = await redeem('  kann-ki-beratung-test  ')

    expect(axios.post).toHaveBeenCalledWith('/api/referral/redeem', { code: 'kann-ki-beratung-test' })
    expect(res.success).toBe(true)
    expect(res.data.target_scenario_id).toBe(7)
    expect(result.value.target_scenario_id).toBe(7)
  })

  it('REDEEM_002: empty code short-circuits without calling the API', async () => {
    const { redeem, error } = useReferralRedeem()
    const res = await redeem('   ')
    expect(axios.post).not.toHaveBeenCalled()
    expect(res.success).toBe(false)
    expect(res.error).toBe('empty')
    expect(error.value).toBe('empty')
  })

  it('REDEEM_003: surfaces backend message on error', async () => {
    axios.post.mockRejectedValue({ response: { data: { message: 'Ungültiger Einladungscode' } } })
    const { redeem, error } = useReferralRedeem()
    const res = await redeem('bad')
    expect(res.success).toBe(false)
    expect(res.error).toBe('Ungültiger Einladungscode')
    expect(error.value).toBe('Ungültiger Einladungscode')
  })

  it('REDEEM_004: falls back to request_failed when no message present', async () => {
    axios.post.mockRejectedValue({})
    const { redeem } = useReferralRedeem()
    const res = await redeem('x')
    expect(res.error).toBe('request_failed')
  })

  it('REDEEM_005: reports already_enrolled from backend', async () => {
    axios.post.mockResolvedValue({
      data: { success: true, target_scenario_id: 3, role: 'evaluator', already_enrolled: true }
    })
    const { redeem } = useReferralRedeem()
    const res = await redeem('code')
    expect(res.data.already_enrolled).toBe(true)
  })

  it('REDEEM_006: toggles loading around the request', async () => {
    let resolveFn
    axios.post.mockReturnValue(new Promise((r) => { resolveFn = r }))
    const { redeem, loading } = useReferralRedeem()
    const p = redeem('code')
    expect(loading.value).toBe(true)
    resolveFn({ data: { success: true, target_scenario_id: 1 } })
    await p
    expect(loading.value).toBe(false)
  })
})
