/**
 * AdminMailCenterSection Component Tests
 *
 * Covers the redesigned three-area Mail-Center: the standard-template preview
 * cards (Vorlagen), and the sent-log rendering + empty-state hint. The
 * composables are mocked so no network is hit; Vuetify + a key-returning $t
 * keep the mount lightweight.
 * Test IDs: MAIL_SEC_001 - MAIL_SEC_010
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({ components, directives })

// ---- Mock the Mail-Center API composable ----
const mockFetchTemplates = vi.fn()
const mockFetchLog = vi.fn()
const mockPreview = vi.fn()
const mockSendInvite = vi.fn()
const mockSendAnnouncement = vi.fn()

vi.mock('@/composables/useMailCenter', () => ({
  useMailCenter: () => ({
    loading: ref(false),
    error: ref(null),
    preview: mockPreview,
    sendInvite: mockSendInvite,
    sendAnnouncement: mockSendAnnouncement,
    fetchTemplates: mockFetchTemplates,
    fetchLog: mockFetchLog,
    fetchLinkInvitations: vi.fn(),
  }),
}))

vi.mock('@/composables/useReferralSystem', () => ({
  useReferralSystem: () => ({
    listCampaigns: vi.fn().mockResolvedValue([]),
    listCampaignLinks: vi.fn().mockResolvedValue([]),
  }),
}))

vi.mock('@/composables/useSnackbar', () => ({
  useSnackbar: () => ({ showSuccess: vi.fn(), showError: vi.fn() }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (k) => k, locale: ref('de') }),
}))

import AdminMailCenterSection from '@/components/Admin/sections/AdminMailCenterSection.vue'

// Lightweight stubs for the LLARS design-system components so the section
// mounts cleanly (they are globally registered in the app, not in tests).
// Each renders its default slot + any named slots used here so v-html /
// titles still surface for assertions.
const passthrough = (extra = '') => ({
  template: `<div ${extra}><slot name="actions" /><slot /></div>`,
  props: ['title', 'icon', 'variant', 'tabs', 'modelValue', 'size', 'text', 'prependIcon', 'disabled', 'loading'],
})

const lStubs = {
  LCard: passthrough(),
  LTabs: passthrough(),
  LBtn: passthrough(),
  LTag: passthrough(),
  LLoading: { template: '<div class="l-loading" />' },
}

function mountSection() {
  return mount(AdminMailCenterSection, {
    global: {
      plugins: [vuetify],
      mocks: { $t: (k) => k },
      stubs: lStubs,
    },
  })
}

const SAMPLE_TEMPLATES = [
  { type: 'welcome', subject: 'Willkommen', html: '<b>welcome-body</b>', text: 'w',
    description: 'Beim Registrieren.', variables: ['username'] },
  { type: 'password_reset', subject: 'Reset', html: '<b>reset-body</b>', text: 'r',
    description: 'Bei Passwort vergessen.', variables: ['reset_link'] },
  { type: 'invitation', subject: 'Einladung', html: '<b>invite-body</b>', text: 'i',
    description: 'Beim Einladen.', variables: ['join_link'] },
]

describe('AdminMailCenterSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockFetchTemplates.mockResolvedValue(SAMPLE_TEMPLATES)
    mockFetchLog.mockResolvedValue({ entries: [], total: 0 })
  })

  it('MAIL_SEC_001: loads standard templates on mount', async () => {
    mountSection()
    await flushPromises()
    expect(mockFetchTemplates).toHaveBeenCalled()
  })

  it('MAIL_SEC_002: renders a preview card per standard template', async () => {
    const wrapper = mountSection()
    await flushPromises()
    const html = wrapper.html()
    // All three sample HTML bodies are rendered via v-html.
    expect(html).toContain('welcome-body')
    expect(html).toContain('reset-body')
    expect(html).toContain('invite-body')
    // Description + variable from sample data surfaces.
    expect(html).toContain('Beim Registrieren.')
    expect(html).toContain('username')
  })

  it('MAIL_SEC_003: shows the empty-state hint when no log entries', async () => {
    const wrapper = mountSection()
    await flushPromises()
    // Switch to the log tab.
    wrapper.vm.tab = 'log'
    await flushPromises()
    expect(wrapper.html()).toContain('admin.mailCenter.log.emptyHint')
  })

  it('MAIL_SEC_004: renders log rows when entries are present', async () => {
    mockFetchLog.mockResolvedValue({
      entries: [
        { id: 1, created_at: '2026-06-01T10:00:00', mail_type: 'welcome',
          recipient_email: 'a@x.com', subject: 'Hi', status: 'sent', scenario_id: null },
      ],
      total: 1,
    })
    const wrapper = mountSection()
    await flushPromises()
    wrapper.vm.tab = 'log'
    await flushPromises()
    const html = wrapper.html()
    expect(html).toContain('a@x.com')
    // Empty-state hint must NOT show when there are rows.
    expect(html).not.toContain('admin.mailCenter.log.emptyHint')
  })

  it('MAIL_SEC_005: defaults to the templates tab', async () => {
    const wrapper = mountSection()
    await flushPromises()
    expect(wrapper.vm.tab).toBe('templates')
  })
})
