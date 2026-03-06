/**
 * useReferralSystem Composable Tests
 *
 * Tests for the referral/invitation system composable.
 * Test IDs: REFERRAL_001 - REFERRAL_055
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key) => key)
  }))
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

import axios from 'axios'

let useReferralSystem

describe('useReferralSystem', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    const module = await import('@/composables/useReferralSystem')
    useReferralSystem = module.useReferralSystem
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('REFERRAL_001: returns all expected state properties', () => {
      const result = useReferralSystem()
      expect(result).toHaveProperty('loading')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('registrationEnabled')
      expect(result).toHaveProperty('statusLoaded')
    })

    it('REFERRAL_002: returns all public methods', () => {
      const result = useReferralSystem()
      expect(typeof result.checkRegistrationStatus).toBe('function')
      expect(typeof result.refreshRegistrationStatus).toBe('function')
      expect(typeof result.validateReferralCode).toBe('function')
      expect(typeof result.registerWithReferral).toBe('function')
    })

    it('REFERRAL_003: returns all admin campaign methods', () => {
      const result = useReferralSystem()
      expect(typeof result.listCampaigns).toBe('function')
      expect(typeof result.getCampaign).toBe('function')
      expect(typeof result.createCampaign).toBe('function')
      expect(typeof result.updateCampaign).toBe('function')
      expect(typeof result.updateCampaignStatus).toBe('function')
      expect(typeof result.deleteCampaign).toBe('function')
    })

    it('REFERRAL_004: returns all admin link methods', () => {
      const result = useReferralSystem()
      expect(typeof result.listCampaignLinks).toBe('function')
      expect(typeof result.createLink).toBe('function')
      expect(typeof result.getLink).toBe('function')
      expect(typeof result.updateLink).toBe('function')
      expect(typeof result.deactivateLink).toBe('function')
      expect(typeof result.deleteLink).toBe('function')
    })

    it('REFERRAL_005: returns all analytics methods', () => {
      const result = useReferralSystem()
      expect(typeof result.getAnalyticsOverview).toBe('function')
      expect(typeof result.getCampaignAnalytics).toBe('function')
      expect(typeof result.listRegistrations).toBe('function')
    })

    it('REFERRAL_006: returns utility methods', () => {
      const result = useReferralSystem()
      expect(typeof result.getLinkUrl).toBe('function')
      expect(typeof result.copyLinkToClipboard).toBe('function')
      expect(typeof result.getStatusColor).toBe('function')
      expect(typeof result.getStatusLabel).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('REFERRAL_007: loading starts false', () => {
      const { loading } = useReferralSystem()
      expect(loading.value).toBe(false)
    })

    it('REFERRAL_008: error starts null', () => {
      const { error } = useReferralSystem()
      expect(error.value).toBeNull()
    })
  })

  // ==================== Registration Status ====================

  describe('checkRegistrationStatus', () => {
    it('REFERRAL_009: fetches registration status from API', async () => {
      axios.get.mockResolvedValue({
        data: { registration_enabled: true }
      })

      const { checkRegistrationStatus, registrationEnabled } = useReferralSystem()
      const result = await checkRegistrationStatus()

      expect(result).toBe(true)
      expect(registrationEnabled.value).toBe(true)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/system/status')
    })

    it('REFERRAL_010: caches registration status', async () => {
      axios.get.mockResolvedValue({
        data: { registration_enabled: true }
      })

      const { checkRegistrationStatus } = useReferralSystem()
      await checkRegistrationStatus()
      await checkRegistrationStatus()

      expect(axios.get).toHaveBeenCalledTimes(1)
    })

    it('REFERRAL_011: handles API error gracefully', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const { checkRegistrationStatus, registrationEnabled } = useReferralSystem()
      const result = await checkRegistrationStatus()

      expect(result).toBe(false)
      expect(registrationEnabled.value).toBe(false)
    })
  })

  describe('refreshRegistrationStatus', () => {
    it('REFERRAL_012: forces refresh of status', async () => {
      axios.get.mockResolvedValue({
        data: { registration_enabled: true }
      })

      const { checkRegistrationStatus, refreshRegistrationStatus } = useReferralSystem()
      await checkRegistrationStatus()

      axios.get.mockResolvedValue({
        data: { registration_enabled: false }
      })
      const result = await refreshRegistrationStatus()

      expect(result).toBe(false)
      expect(axios.get).toHaveBeenCalledTimes(2)
    })
  })

  // ==================== Referral Code Validation ====================

  describe('validateReferralCode', () => {
    it('REFERRAL_013: validates a valid referral code', async () => {
      axios.get.mockResolvedValue({
        data: { valid: true, campaign: { name: 'Test Campaign' } }
      })

      const { validateReferralCode } = useReferralSystem()
      const result = await validateReferralCode('ABC123')

      expect(result.valid).toBe(true)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/validate/ABC123')
    })

    it('REFERRAL_014: returns invalid for empty code', async () => {
      const { validateReferralCode } = useReferralSystem()
      const result = await validateReferralCode('')

      expect(result.valid).toBe(false)
      expect(result.error).toBe('referral.errors.codeRequired')
    })

    it('REFERRAL_015: returns invalid for null code', async () => {
      const { validateReferralCode } = useReferralSystem()
      const result = await validateReferralCode(null)

      expect(result.valid).toBe(false)
    })

    it('REFERRAL_016: handles validation API error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Code expired' } }
      })

      const { validateReferralCode, error } = useReferralSystem()
      const result = await validateReferralCode('EXPIRED')

      expect(result.valid).toBe(false)
      expect(result.error).toBe('Code expired')
      expect(error.value).toBe('Code expired')
    })

    it('REFERRAL_017: encodes code in URL', async () => {
      axios.get.mockResolvedValue({ data: { valid: true } })

      const { validateReferralCode } = useReferralSystem()
      await validateReferralCode('code with spaces')

      expect(axios.get).toHaveBeenCalledWith('/api/referral/validate/code%20with%20spaces')
    })
  })

  // ==================== Registration ====================

  describe('registerWithReferral', () => {
    it('REFERRAL_018: registers user successfully', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, username: 'newuser' }
      })

      const { registerWithReferral } = useReferralSystem()
      const result = await registerWithReferral({
        referral_code: 'ABC123',
        username: 'newuser',
        email: 'new@test.com',
        password: 'pass123'
      })

      expect(result.success).toBe(true)
      expect(axios.post).toHaveBeenCalledWith('/api/referral/register', expect.any(Object))
    })

    it('REFERRAL_019: throws on registration error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Username taken' } }
      })

      const { registerWithReferral, error } = useReferralSystem()

      await expect(registerWithReferral({
        referral_code: 'ABC123',
        username: 'taken',
        email: 'test@test.com',
        password: 'pass'
      })).rejects.toThrow('Username taken')

      expect(error.value).toBe('Username taken')
    })

    it('REFERRAL_020: sets loading during registration', async () => {
      let resolvePromise
      axios.post.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { registerWithReferral, loading } = useReferralSystem()
      const promise = registerWithReferral({ referral_code: 'X' })
      expect(loading.value).toBe(true)

      resolvePromise({ data: { success: true } })
      await promise
      expect(loading.value).toBe(false)
    })
  })

  // ==================== Admin - Campaigns ====================

  describe('Campaign Management', () => {
    it('REFERRAL_021: listCampaigns fetches campaigns', async () => {
      axios.get.mockResolvedValue({
        data: { campaigns: [{ id: 1, name: 'Campaign 1' }] }
      })

      const { listCampaigns } = useReferralSystem()
      const result = await listCampaigns()

      expect(result).toHaveLength(1)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/campaigns', { params: {} })
    })

    it('REFERRAL_022: listCampaigns with archived flag', async () => {
      axios.get.mockResolvedValue({ data: { campaigns: [] } })

      const { listCampaigns } = useReferralSystem()
      await listCampaigns(true)

      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/campaigns', {
        params: { include_archived: 'true' }
      })
    })

    it('REFERRAL_023: getCampaign fetches single campaign', async () => {
      axios.get.mockResolvedValue({
        data: { campaign: { id: 1, name: 'Test', links: [] } }
      })

      const { getCampaign } = useReferralSystem()
      const result = await getCampaign(1)

      expect(result.name).toBe('Test')
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/campaigns/1')
    })

    it('REFERRAL_024: createCampaign posts campaign data', async () => {
      axios.post.mockResolvedValue({
        data: { campaign: { id: 2, name: 'New Campaign' } }
      })

      const { createCampaign } = useReferralSystem()
      const result = await createCampaign({ name: 'New Campaign' })

      expect(result.name).toBe('New Campaign')
      expect(axios.post).toHaveBeenCalledWith('/api/referral/admin/campaigns', { name: 'New Campaign' })
    })

    it('REFERRAL_025: updateCampaign sends PUT request', async () => {
      axios.put.mockResolvedValue({
        data: { campaign: { id: 1, name: 'Updated' } }
      })

      const { updateCampaign } = useReferralSystem()
      const result = await updateCampaign(1, { name: 'Updated' })

      expect(result.name).toBe('Updated')
      expect(axios.put).toHaveBeenCalledWith('/api/referral/admin/campaigns/1', { name: 'Updated' })
    })

    it('REFERRAL_026: updateCampaignStatus patches status', async () => {
      axios.patch.mockResolvedValue({ data: { success: true } })

      const { updateCampaignStatus } = useReferralSystem()
      await updateCampaignStatus(1, 'active')

      expect(axios.patch).toHaveBeenCalledWith(
        '/api/referral/admin/campaigns/1/status',
        { status: 'active' }
      )
    })

    it('REFERRAL_027: deleteCampaign sends DELETE request', async () => {
      axios.delete.mockResolvedValue({ data: { success: true } })

      const { deleteCampaign } = useReferralSystem()
      await deleteCampaign(1)

      expect(axios.delete).toHaveBeenCalledWith('/api/referral/admin/campaigns/1')
    })

    it('REFERRAL_028: campaign operations throw on error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Permission denied' } }
      })

      const { listCampaigns, error } = useReferralSystem()

      await expect(listCampaigns()).rejects.toThrow('Permission denied')
      expect(error.value).toBe('Permission denied')
    })

    it('REFERRAL_029: getCampaign throws on error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const { getCampaign } = useReferralSystem()
      await expect(getCampaign(999)).rejects.toThrow('Not found')
    })

    it('REFERRAL_030: createCampaign throws on error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Validation error' } }
      })

      const { createCampaign } = useReferralSystem()
      await expect(createCampaign({})).rejects.toThrow('Validation error')
    })
  })

  // ==================== Admin - Links ====================

  describe('Link Management', () => {
    it('REFERRAL_031: listCampaignLinks fetches links', async () => {
      axios.get.mockResolvedValue({
        data: { links: [{ id: 1, code: 'ABC' }] }
      })

      const { listCampaignLinks } = useReferralSystem()
      const result = await listCampaignLinks(1)

      expect(result).toHaveLength(1)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/campaigns/1/links')
    })

    it('REFERRAL_032: createLink creates a new link', async () => {
      axios.post.mockResolvedValue({
        data: { link: { id: 2, code: 'XYZ', slug: 'custom' } }
      })

      const { createLink } = useReferralSystem()
      const result = await createLink(1, { slug: 'custom', role_name: 'evaluator' })

      expect(result.slug).toBe('custom')
      expect(axios.post).toHaveBeenCalledWith(
        '/api/referral/admin/campaigns/1/links',
        { slug: 'custom', role_name: 'evaluator' }
      )
    })

    it('REFERRAL_033: getLink fetches link details', async () => {
      axios.get.mockResolvedValue({
        data: { link: { id: 1, uses: 5 } }
      })

      const { getLink } = useReferralSystem()
      const result = await getLink(1)

      expect(result.uses).toBe(5)
    })

    it('REFERRAL_034: updateLink updates link data', async () => {
      axios.put.mockResolvedValue({
        data: { link: { id: 1, label: 'Updated' } }
      })

      const { updateLink } = useReferralSystem()
      const result = await updateLink(1, { label: 'Updated' })

      expect(result.label).toBe('Updated')
    })

    it('REFERRAL_035: deactivateLink deactivates a link', async () => {
      axios.post.mockResolvedValue({ data: { success: true } })

      const { deactivateLink } = useReferralSystem()
      await deactivateLink(1)

      expect(axios.post).toHaveBeenCalledWith('/api/referral/admin/links/1/deactivate')
    })

    it('REFERRAL_036: deleteLink deletes a link', async () => {
      axios.delete.mockResolvedValue({ data: { success: true } })

      const { deleteLink } = useReferralSystem()
      await deleteLink(1)

      expect(axios.delete).toHaveBeenCalledWith('/api/referral/admin/links/1')
    })

    it('REFERRAL_037: link operations throw on error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Link not found' } }
      })

      const { listCampaignLinks } = useReferralSystem()
      await expect(listCampaignLinks(999)).rejects.toThrow()
    })

    it('REFERRAL_038: createLink throws on error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Slug taken' } }
      })

      const { createLink } = useReferralSystem()
      await expect(createLink(1, { slug: 'taken' })).rejects.toThrow('Slug taken')
    })

    it('REFERRAL_039: deactivateLink throws on error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Already inactive' } }
      })

      const { deactivateLink } = useReferralSystem()
      await expect(deactivateLink(1)).rejects.toThrow()
    })
  })

  // ==================== Admin - Analytics ====================

  describe('Analytics', () => {
    it('REFERRAL_040: getAnalyticsOverview fetches analytics', async () => {
      axios.get.mockResolvedValue({
        data: { data: { total_registrations: 100, active_campaigns: 3 } }
      })

      const { getAnalyticsOverview } = useReferralSystem()
      const result = await getAnalyticsOverview()

      expect(result.total_registrations).toBe(100)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/analytics/overview')
    })

    it('REFERRAL_041: getCampaignAnalytics fetches campaign analytics', async () => {
      axios.get.mockResolvedValue({
        data: { data: { registrations: 50 } }
      })

      const { getCampaignAnalytics } = useReferralSystem()
      const result = await getCampaignAnalytics(1)

      expect(result.registrations).toBe(50)
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/analytics/campaigns/1')
    })

    it('REFERRAL_042: listRegistrations fetches registrations', async () => {
      axios.get.mockResolvedValue({
        data: { registrations: [], total: 0, limit: 50, offset: 0 }
      })

      const { listRegistrations } = useReferralSystem()
      const result = await listRegistrations({ campaign_id: 1, limit: 25 })

      expect(result).toHaveProperty('registrations')
      expect(axios.get).toHaveBeenCalledWith('/api/referral/admin/registrations', {
        params: { campaign_id: 1, limit: 25 }
      })
    })

    it('REFERRAL_043: analytics operations throw on error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Permission denied' } }
      })

      const { getAnalyticsOverview } = useReferralSystem()
      await expect(getAnalyticsOverview()).rejects.toThrow()
    })
  })

  // ==================== Utility Functions ====================

  describe('Utility Functions', () => {
    it('REFERRAL_044: getLinkUrl generates URL with slug', () => {
      const { getLinkUrl } = useReferralSystem()
      const url = getLinkUrl({ slug: 'my-invite', code: 'ABC123' })

      expect(url).toContain('/join/my-invite')
    })

    it('REFERRAL_045: getLinkUrl falls back to code', () => {
      const { getLinkUrl } = useReferralSystem()
      const url = getLinkUrl({ code: 'ABC123' })

      expect(url).toContain('/join/ABC123')
    })

    it('REFERRAL_046: copyLinkToClipboard copies URL', async () => {
      const mockWriteText = vi.fn().mockResolvedValue(undefined)
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: mockWriteText },
        writable: true,
        configurable: true
      })

      const { copyLinkToClipboard } = useReferralSystem()
      const result = await copyLinkToClipboard({ code: 'ABC123' })

      expect(result).toBe(true)
      expect(mockWriteText).toHaveBeenCalled()
    })

    it('REFERRAL_047: copyLinkToClipboard returns false on error', async () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: vi.fn().mockRejectedValue(new Error('Denied')) },
        writable: true,
        configurable: true
      })

      const { copyLinkToClipboard } = useReferralSystem()
      const result = await copyLinkToClipboard({ code: 'ABC123' })

      expect(result).toBe(false)
    })

    it('REFERRAL_048: getStatusColor returns correct colors', () => {
      const { getStatusColor } = useReferralSystem()

      expect(getStatusColor('draft')).toBe('grey')
      expect(getStatusColor('active')).toBe('success')
      expect(getStatusColor('paused')).toBe('warning')
      expect(getStatusColor('expired')).toBe('error')
      expect(getStatusColor('archived')).toBe('grey-darken-2')
    })

    it('REFERRAL_049: getStatusColor returns grey for unknown status', () => {
      const { getStatusColor } = useReferralSystem()
      expect(getStatusColor('unknown')).toBe('grey')
    })

    it('REFERRAL_050: getStatusLabel returns status fallback when not translated', () => {
      const { getStatusLabel } = useReferralSystem()
      const label = getStatusLabel('active')
      // When t() returns the key unchanged, getStatusLabel falls back to raw status
      expect(label).toBe('active')
    })
  })

  // ==================== Loading State ====================

  describe('Loading State', () => {
    it('REFERRAL_051: sets loading during campaign operations', async () => {
      let resolvePromise
      axios.get.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { listCampaigns, loading } = useReferralSystem()
      const promise = listCampaigns().catch(() => {})
      expect(loading.value).toBe(true)

      resolvePromise({ data: { campaigns: [] } })
      await promise
      expect(loading.value).toBe(false)
    })

    it('REFERRAL_052: clears error before new operation', async () => {
      axios.get.mockRejectedValueOnce({
        response: { data: { error: 'First error' } }
      })

      const { validateReferralCode, error } = useReferralSystem()
      await validateReferralCode('bad')
      expect(error.value).toBe('First error')

      axios.get.mockResolvedValueOnce({ data: { valid: true } })
      await validateReferralCode('good')
      expect(error.value).toBeNull()
    })

    it('REFERRAL_053: loading resets after error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Error' } }
      })

      const { getCampaign, loading } = useReferralSystem()
      await expect(getCampaign(1)).rejects.toThrow()

      expect(loading.value).toBe(false)
    })

    it('REFERRAL_054: updateCampaign sets loading correctly', async () => {
      axios.put.mockResolvedValue({
        data: { campaign: { id: 1 } }
      })

      const { updateCampaign, loading } = useReferralSystem()
      await updateCampaign(1, { name: 'Test' })

      expect(loading.value).toBe(false)
    })

    it('REFERRAL_055: deleteCampaign sets loading correctly', async () => {
      axios.delete.mockResolvedValue({ data: {} })

      const { deleteCampaign, loading } = useReferralSystem()
      await deleteCampaign(1)

      expect(loading.value).toBe(false)
    })
  })
})
