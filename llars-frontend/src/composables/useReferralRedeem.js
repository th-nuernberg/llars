/**
 * Referral Redeem Composable
 *
 * Lets an ALREADY logged-in user join a study by entering a referral
 * code/slug. Mirrors the public registration referral flow but for an
 * existing account: the backend enrolls the user into the link's target
 * scenario and attributes the campaign WITHOUT changing the user's role.
 *
 * Backend: POST /api/referral/redeem  { code }
 *   -> { success, target_scenario_id, role, already_enrolled }
 *
 * Kept as a composable (not inline) so the redeem logic is unit-testable in
 * isolation and reusable from any place a participant can reach (settings,
 * evaluation overview, ...).
 */
import { ref } from 'vue'
import axios from 'axios'

export function useReferralRedeem() {
  const loading = ref(false)
  const error = ref('')
  const result = ref(null)

  /**
   * Redeem a referral code/slug for the current user.
   *
   * @param {string} code - Referral code or friendly slug.
   * @returns {Promise<{success: boolean, data?: object, error?: string}>}
   */
  const redeem = async (code) => {
    error.value = ''
    result.value = null

    const trimmed = (code || '').trim()
    if (!trimmed) {
      // Surfaced inline by the caller; matches the backend's required check.
      error.value = 'empty'
      return { success: false, error: 'empty' }
    }

    loading.value = true
    try {
      const response = await axios.post('/api/referral/redeem', { code: trimmed })
      result.value = response.data
      return { success: true, data: response.data }
    } catch (e) {
      // Backend returns a human-readable message via @handle_api_errors.
      const msg = e?.response?.data?.message
        || e?.response?.data?.error
        || 'request_failed'
      error.value = msg
      return { success: false, error: msg }
    } finally {
      loading.value = false
    }
  }

  return { loading, error, result, redeem }
}
