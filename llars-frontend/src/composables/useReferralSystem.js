/**
 * Composable for the Referral/Invitation System.
 *
 * Provides:
 * - Registration status checking
 * - Referral code validation
 * - User registration via referral
 * - Admin campaign/link management
 * - Analytics data fetching
 *
 * @module useReferralSystem
 */

import { ref, computed } from 'vue'
import axios from 'axios'

// Shared state for registration status (singleton)
const registrationEnabled = ref(false)
const statusLoaded = ref(false)
const statusLoading = ref(false)

/**
 * Get the API base URL.
 * @returns {string} API base URL
 */
function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || ''
}

/**
 * Composable for referral system functionality.
 * @returns {Object} Referral system methods and state
 */
export function useReferralSystem() {
  // Local state for operations
  const loading = ref(false)
  const error = ref(null)

  // ============================================================
  // Public Endpoints (No Auth Required)
  // ============================================================

  /**
   * Check if self-registration is enabled.
   * Caches the result to avoid repeated API calls.
   * @returns {Promise<boolean>} Whether registration is enabled
   */
  async function checkRegistrationStatus() {
    if (statusLoaded.value) {
      return registrationEnabled.value
    }

    if (statusLoading.value) {
      // Wait for existing request to complete
      await new Promise(resolve => {
        const check = setInterval(() => {
          if (statusLoaded.value) {
            clearInterval(check)
            resolve()
          }
        }, 50)
      })
      return registrationEnabled.value
    }

    statusLoading.value = true
    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/system/status`)
      registrationEnabled.value = response.data.registration_enabled
      statusLoaded.value = true
      return registrationEnabled.value
    } catch (e) {
      console.warn('Failed to check registration status:', e)
      registrationEnabled.value = false
      statusLoaded.value = true
      return false
    } finally {
      statusLoading.value = false
    }
  }

  /**
   * Force refresh of registration status.
   * @returns {Promise<boolean>} Whether registration is enabled
   */
  async function refreshRegistrationStatus() {
    statusLoaded.value = false
    return checkRegistrationStatus()
  }

  /**
   * Validate a referral code or slug.
   * @param {string} code - Referral code or custom slug
   * @returns {Promise<Object>} Validation result with campaign info
   */
  async function validateReferralCode(code) {
    if (!code) {
      return { valid: false, error: 'Einladungscode ist erforderlich' }
    }

    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/validate/${encodeURIComponent(code)}`)
      return response.data
    } catch (e) {
      const errorMsg = e.response?.data?.error || 'Fehler bei der Code-Validierung'
      error.value = errorMsg
      return { valid: false, error: errorMsg }
    } finally {
      loading.value = false
    }
  }

  /**
   * Register a new user via referral code.
   * @param {Object} data - Registration data
   * @param {string} data.referral_code - Referral code or slug
   * @param {string} data.username - Username
   * @param {string} data.email - Email address
   * @param {string} data.password - Password
   * @param {string} [data.display_name] - Display name (optional)
   * @returns {Promise<Object>} Registration result
   */
  async function registerWithReferral(data) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post(`${getApiBaseUrl()}/api/referral/register`, data)
      return response.data
    } catch (e) {
      const errorMsg = e.response?.data?.error || 'Registrierung fehlgeschlagen'
      error.value = errorMsg
      throw new Error(errorMsg)
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Admin Endpoints - Campaigns
  // ============================================================

  /**
   * List all referral campaigns.
   * @param {boolean} [includeArchived=false] - Include archived campaigns
   * @returns {Promise<Array>} List of campaigns
   */
  async function listCampaigns(includeArchived = false) {
    loading.value = true
    error.value = null

    try {
      const params = includeArchived ? { include_archived: 'true' } : {}
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/campaigns`, { params })
      return response.data.campaigns
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden der Kampagnen'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Get a single campaign with its links.
   * @param {number} campaignId - Campaign ID
   * @returns {Promise<Object>} Campaign data with links
   */
  async function getCampaign(campaignId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}`)
      return response.data.campaign
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden der Kampagne'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new campaign.
   * @param {Object} data - Campaign data
   * @param {string} data.name - Campaign name
   * @param {string} [data.description] - Description
   * @param {string} [data.start_date] - Start date (ISO string)
   * @param {string} [data.end_date] - End date (ISO string)
   * @param {number} [data.max_registrations] - Max registrations
   * @returns {Promise<Object>} Created campaign
   */
  async function createCampaign(data) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post(`${getApiBaseUrl()}/api/referral/admin/campaigns`, data)
      return response.data.campaign
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Erstellen der Kampagne'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Update a campaign.
   * @param {number} campaignId - Campaign ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Updated campaign
   */
  async function updateCampaign(campaignId, data) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.put(`${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}`, data)
      return response.data.campaign
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Aktualisieren der Kampagne'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Update campaign status.
   * @param {number} campaignId - Campaign ID
   * @param {string} status - New status ('draft', 'active', 'paused', 'expired', 'archived')
   * @returns {Promise<Object>} Result
   */
  async function updateCampaignStatus(campaignId, status) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.patch(
        `${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}/status`,
        { status }
      )
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Aktualisieren des Status'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a campaign.
   * @param {number} campaignId - Campaign ID
   * @returns {Promise<Object>} Result
   */
  async function deleteCampaign(campaignId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.delete(`${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}`)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Löschen der Kampagne'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Admin Endpoints - Links
  // ============================================================

  /**
   * List all links for a campaign.
   * @param {number} campaignId - Campaign ID
   * @returns {Promise<Array>} List of links
   */
  async function listCampaignLinks(campaignId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}/links`)
      return response.data.links
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden der Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Create a new referral link.
   * @param {number} campaignId - Campaign ID
   * @param {Object} data - Link data
   * @param {string} [data.slug] - Custom slug
   * @param {string} [data.role_name] - Role to assign
   * @param {string} [data.label] - Label/description
   * @param {number} [data.max_uses] - Max uses
   * @param {string} [data.expires_at] - Expiry date (ISO string)
   * @returns {Promise<Object>} Created link
   */
  async function createLink(campaignId, data) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post(
        `${getApiBaseUrl()}/api/referral/admin/campaigns/${campaignId}/links`,
        data
      )
      return response.data.link
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Erstellen des Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Get link details with stats.
   * @param {number} linkId - Link ID
   * @returns {Promise<Object>} Link data with statistics
   */
  async function getLink(linkId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/links/${linkId}`)
      return response.data.link
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden des Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Update a link.
   * @param {number} linkId - Link ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>} Updated link
   */
  async function updateLink(linkId, data) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.put(`${getApiBaseUrl()}/api/referral/admin/links/${linkId}`, data)
      return response.data.link
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Aktualisieren des Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Deactivate a link.
   * @param {number} linkId - Link ID
   * @returns {Promise<Object>} Result
   */
  async function deactivateLink(linkId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post(`${getApiBaseUrl()}/api/referral/admin/links/${linkId}/deactivate`)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Deaktivieren des Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete a link.
   * @param {number} linkId - Link ID
   * @returns {Promise<Object>} Result
   */
  async function deleteLink(linkId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.delete(`${getApiBaseUrl()}/api/referral/admin/links/${linkId}`)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Löschen des Links'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Admin Endpoints - Analytics
  // ============================================================

  /**
   * Get system-wide analytics overview.
   * @returns {Promise<Object>} Analytics data
   */
  async function getAnalyticsOverview() {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/analytics/overview`)
      return response.data.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden der Analytics'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Get campaign-specific analytics.
   * @param {number} campaignId - Campaign ID
   * @returns {Promise<Object>} Campaign analytics
   */
  async function getCampaignAnalytics(campaignId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`${getApiBaseUrl()}/api/referral/admin/analytics/campaigns/${campaignId}`)
      return response.data.data
    } catch (e) {
      error.value = e.response?.data?.error || 'Fehler beim Laden der Kampagnen-Analytics'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Utility Functions
  // ============================================================

  /**
   * Generate a full URL for a referral link.
   * @param {Object} link - Link object with code and/or slug
   * @returns {string} Full URL
   */
  function getLinkUrl(link) {
    const base = window.location.origin
    const path = link.slug || link.code
    return `${base}/join/${path}`
  }

  /**
   * Copy link URL to clipboard.
   * @param {Object} link - Link object
   * @returns {Promise<boolean>} Success status
   */
  async function copyLinkToClipboard(link) {
    const url = getLinkUrl(link)
    try {
      await navigator.clipboard.writeText(url)
      return true
    } catch (e) {
      console.error('Failed to copy to clipboard:', e)
      return false
    }
  }

  /**
   * Get status badge color for campaign status.
   * @param {string} status - Campaign status
   * @returns {string} Vuetify color
   */
  function getStatusColor(status) {
    const colors = {
      draft: 'grey',
      active: 'success',
      paused: 'warning',
      expired: 'error',
      archived: 'grey-darken-2'
    }
    return colors[status] || 'grey'
  }

  /**
   * Get human-readable status label.
   * @param {string} status - Campaign status
   * @returns {string} Translated label
   */
  function getStatusLabel(status) {
    const labels = {
      draft: 'Entwurf',
      active: 'Aktiv',
      paused: 'Pausiert',
      expired: 'Abgelaufen',
      archived: 'Archiviert'
    }
    return labels[status] || status
  }

  return {
    // State
    loading,
    error,
    registrationEnabled: computed(() => registrationEnabled.value),
    statusLoaded: computed(() => statusLoaded.value),

    // Public methods
    checkRegistrationStatus,
    refreshRegistrationStatus,
    validateReferralCode,
    registerWithReferral,

    // Admin - Campaigns
    listCampaigns,
    getCampaign,
    createCampaign,
    updateCampaign,
    updateCampaignStatus,
    deleteCampaign,

    // Admin - Links
    listCampaignLinks,
    createLink,
    getLink,
    updateLink,
    deactivateLink,
    deleteLink,

    // Admin - Analytics
    getAnalyticsOverview,
    getCampaignAnalytics,

    // Utilities
    getLinkUrl,
    copyLinkToClipboard,
    getStatusColor,
    getStatusLabel
  }
}

export default useReferralSystem
