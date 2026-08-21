/**
 * useMailCenter Composable Tests
 *
 * Tests the Admin Mail-Center API client: preview, invite, announce, log read
 * and per-link invitation stats. axios is mocked — no network.
 * Test IDs: MAIL_FE_001 - MAIL_FE_010
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import axios from 'axios'

let useMailCenter

describe('useMailCenter', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()
    const module = await import('@/composables/useMailCenter')
    useMailCenter = module.useMailCenter
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('MAIL_FE_001: exposes the expected API', () => {
    const mc = useMailCenter()
    expect(mc).toHaveProperty('loading')
    expect(mc).toHaveProperty('error')
    expect(typeof mc.preview).toBe('function')
    expect(typeof mc.sendInvite).toBe('function')
    expect(typeof mc.sendTemplate).toBe('function')
    expect(typeof mc.sendAnnouncement).toBe('function')
    expect(typeof mc.fetchTemplates).toBe('function')
    expect(typeof mc.fetchLog).toBe('function')
    expect(typeof mc.fetchLinkInvitations).toBe('function')
  })

  it('MAIL_FE_008: fetchTemplates returns the rendered templates array', async () => {
    axios.get.mockResolvedValue({
      data: { success: true, templates: [{ type: 'welcome', subject: 'Hi', html: '<b>x</b>' }] },
    })
    const mc = useMailCenter()
    const res = await mc.fetchTemplates()
    expect(axios.get).toHaveBeenCalledWith('/api/admin/mail/templates', { params: {} })
    expect(res).toHaveLength(1)
    expect(res[0].type).toBe('welcome')
  })

  it('MAIL_FE_009: fetchTemplates passes a single type param', async () => {
    axios.get.mockResolvedValue({ data: { templates: [{ type: 'invitation' }] } })
    const mc = useMailCenter()
    await mc.fetchTemplates('invitation')
    expect(axios.get).toHaveBeenCalledWith('/api/admin/mail/templates', {
      params: { type: 'invitation' },
    })
  })

  it('MAIL_FE_002: preview posts payload and returns rendered data', async () => {
    axios.post.mockResolvedValue({
      data: { subject: 'Hi', html: '<b>x</b>', text: 'x', recipients: { count: 3 } },
    })
    const mc = useMailCenter()
    const res = await mc.preview({ mode: 'announcement', subject: 'Hi', body: 'x' })
    expect(axios.post).toHaveBeenCalledWith('/api/admin/mail/preview', expect.any(Object))
    expect(res.recipients.count).toBe(3)
  })

  it('MAIL_FE_003: sendInvite maps camelCase to backend snake_case', async () => {
    axios.post.mockResolvedValue({ data: { success: true, result: { sent: 2 } } })
    const mc = useMailCenter()
    await mc.sendInvite({ referralLinkId: 7, listText: 'a@x.com', intro: 'Hi' })
    expect(axios.post).toHaveBeenCalledWith('/api/admin/mail/invite', {
      referral_link_id: 7,
      recipients: [],
      list_text: 'a@x.com',
      intro: 'Hi',
      // body_html/subject default to null (only set when sending a chosen +
      // edited per-org branded template).
      body_html: null,
      subject: null,
    })
  })

  it('MAIL_FE_004: sendAnnouncement posts subject/body/recipient_spec', async () => {
    axios.post.mockResolvedValue({ data: { success: true, result: { sent: 1 } } })
    const mc = useMailCenter()
    await mc.sendAnnouncement({ subject: 'S', body: 'B', recipientSpec: { role_name: 'evaluator' } })
    expect(axios.post).toHaveBeenCalledWith('/api/admin/mail/announce', {
      subject: 'S',
      body: 'B',
      recipient_spec: { role_name: 'evaluator' },
    })
  })

  it('MAIL_FE_005: fetchLog passes filter params through', async () => {
    axios.get.mockResolvedValue({ data: { entries: [], total: 0 } })
    const mc = useMailCenter()
    const res = await mc.fetchLog({ type: 'welcome', status: 'sent' })
    expect(axios.get).toHaveBeenCalledWith('/api/admin/mail/log', {
      params: { type: 'welcome', status: 'sent' },
    })
    expect(res.total).toBe(0)
  })

  it('MAIL_FE_006: fetchLinkInvitations returns the stats object', async () => {
    axios.get.mockResolvedValue({ data: { stats: { invited: 5, accepted: 2, pending: 3 } } })
    const mc = useMailCenter()
    const stats = await mc.fetchLinkInvitations(9)
    expect(axios.get).toHaveBeenCalledWith('/api/admin/referral/links/9/invitations')
    expect(stats).toEqual({ invited: 5, accepted: 2, pending: 3 })
  })

  it('MAIL_FE_010: sendTemplate posts type/subject/body_html + email (both variants)', async () => {
    axios.post.mockResolvedValue({ data: { success: true, result: { status: 'sent', email: 'a@x.com' } } })
    const mc = useMailCenter()
    // standard template by type
    await mc.sendTemplate({ type: 'welcome', email: 'a@x.com' })
    expect(axios.post).toHaveBeenCalledWith('/api/admin/mail/send-template', {
      type: 'welcome',
      subject: null,
      body_html: null,
      email: 'a@x.com',
    })
    // branded template by raw html
    await mc.sendTemplate({ subject: 'Einladung', bodyHtml: '<b>x</b>', email: 'b@y.com' })
    expect(axios.post).toHaveBeenLastCalledWith('/api/admin/mail/send-template', {
      type: null,
      subject: 'Einladung',
      body_html: '<b>x</b>',
      email: 'b@y.com',
    })
  })

  it('MAIL_FE_007: surfaces backend error message and resets loading', async () => {
    axios.post.mockRejectedValue({ response: { data: { message: 'nope' } } })
    const mc = useMailCenter()
    await expect(mc.sendAnnouncement({ subject: 'S', body: 'B' })).rejects.toThrow('nope')
    expect(mc.loading.value).toBe(false)
    expect(mc.error.value).toBe('nope')
  })
})
