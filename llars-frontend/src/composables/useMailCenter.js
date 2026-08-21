/**
 * useMailCenter — Admin Mail-Center API client.
 *
 * Thin axios wrapper around the backend Mail-Center endpoints
 * (/api/admin/mail/*, /api/admin/referral/links/<id>/invitations). All routes
 * are admin-gated server-side (feature:admin:mail) — this composable just
 * shapes requests/responses for the Mail-Center UI.
 *
 * Two compose modes mirror the backend:
 *   - invitation: pick a referral link, optional intro → branded invite
 *   - announcement: free subject + Markdown body → branded announcement
 *
 * Recipient resolution is delegated to the backend resolver via `recipient_spec`.
 */
import { ref } from 'vue'
import axios from 'axios'

export function useMailCenter() {
  const loading = ref(false)
  const error = ref(null)

  async function _call(fn) {
    loading.value = true
    error.value = null
    try {
      return await fn()
    } catch (e) {
      error.value = e?.response?.data?.message || e?.message || 'Request failed'
      throw new Error(error.value)
    } finally {
      loading.value = false
    }
  }

  /** Render a live preview (no send). Returns { subject, html, text, recipients }. */
  async function preview(payload) {
    return _call(async () => {
      const { data } = await axios.post('/api/admin/mail/preview', payload)
      return data
    })
  }

  /** Send branded invitations for a referral link to an ad-hoc recipient list.
   *  `bodyHtml`/`subject` (optional): send a chosen + edited per-org branded
   *  template verbatim instead of the generic invitation. */
  async function sendInvite({ referralLinkId, recipients, listText, intro, bodyHtml, subject }) {
    return _call(async () => {
      const { data } = await axios.post('/api/admin/mail/invite', {
        referral_link_id: referralLinkId,
        recipients: recipients || [],
        list_text: listText || '',
        intro: intro || null,
        body_html: bodyHtml || null,
        subject: subject || null,
      })
      return data
    })
  }

  /** Quick-send a chosen template (from the "Vorlagen" tab) to a single address.
   *  Pass `type` (welcome/password_reset/invitation) for a standard template, or
   *  `subject` + `bodyHtml` to send a bundled branded template verbatim.
   *  Returns { result: { status, log_id, email } }. */
  async function sendTemplate({ type, subject, bodyHtml, email }) {
    return _call(async () => {
      const { data } = await axios.post('/api/admin/mail/send-template', {
        type: type || null,
        subject: subject || null,
        body_html: bodyHtml || null,
        email,
      })
      return data
    })
  }

  /** Send a branded announcement to a resolved recipient spec. */
  async function sendAnnouncement({ subject, body, recipientSpec }) {
    return _call(async () => {
      const { data } = await axios.post('/api/admin/mail/announce', {
        subject,
        body,
        recipient_spec: recipientSpec || {},
      })
      return data
    })
  }

  /**
   * Render the standard transactional templates (welcome / password_reset /
   * invitation) with clearly-marked sample data. No send. Returns an array of
   * { type, subject, html, text, description, variables }. Pass a `type` to
   * fetch a single template.
   */
  async function fetchTemplates(type = null) {
    return _call(async () => {
      const params = type ? { type } : {}
      const { data } = await axios.get('/api/admin/mail/templates', { params })
      return data.templates || []
    })
  }

  /** Paginated, filterable read of the central mail log. */
  async function fetchLog(params = {}) {
    return _call(async () => {
      const { data } = await axios.get('/api/admin/mail/log', { params })
      return data
    })
  }

  /** Invited / accepted / pending funnel for a referral link. */
  async function fetchLinkInvitations(linkId) {
    return _call(async () => {
      const { data } = await axios.get(`/api/admin/referral/links/${linkId}/invitations`)
      return data.stats
    })
  }

  return {
    loading,
    error,
    preview,
    sendInvite,
    sendTemplate,
    sendAnnouncement,
    fetchTemplates,
    fetchLog,
    fetchLinkInvitations,
  }
}
