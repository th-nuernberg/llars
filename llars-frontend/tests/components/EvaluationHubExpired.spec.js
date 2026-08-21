/**
 * EvaluationHub — scenario visibility by status
 *
 * Test IDs: EVHUB_001 - EVHUB_020
 *
 * Regression coverage for a production bug: the hub filtered scenarios down to
 * `['evaluating', 'data_collection', 'active']`, which dropped anything the
 * backend reported as 'completed'.
 *
 * 'completed' is a *schedule* state, not an archival one — the backend derives
 * it purely from `now > scenario.end` (format_scenario_for_api), and the
 * Scenario Wizard defaults `end` to begin + 30 days. So a study silently
 * vanished from the evaluation page 30 days in, while the Scenario Manager's
 * invitations tab (no status filter) kept listing it. Raters mid-study lost
 * their entry point with no explanation — this hit scenario 660 ("Survey
 * Screening") at 270/300 items and all 15 IJCAI demo scenarios.
 *
 * Expired scenarios must stay REACHABLE (evaluation endpoints have no date
 * guard, so submitting still works) and be labelled — but the hub answers
 * "what still needs doing", so they are behind the "Beendet" / "Alle" filter
 * rather than in the default view.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as vuetifyComponents from 'vuetify/components'
import * as vuetifyDirectives from 'vuetify/directives'
import EvaluationHub from '@/components/Evaluation/EvaluationHub.vue'

const vuetify = createVuetify({ components: vuetifyComponents, directives: vuetifyDirectives })

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
import axios from 'axios'

const pushSpy = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push: pushSpy }) }))

vi.mock('@/composables/useAuth', () => ({
  useAuth: () => ({ tokenParsed: ref({ sub: 'u-10', preferred_username: 'ieb-steigerwald' }) }),
}))

// Socket.IO stub: lets a test push a scenario:access_granted event into the
// component the same way the backend would.
const socketHandlers = {}
const socketStub = {
  connected: true,
  emit: vi.fn(),
  on: vi.fn((event, cb) => { socketHandlers[event] = cb }),
  off: vi.fn((event) => { delete socketHandlers[event] }),
}
vi.mock('@/services/socketService', () => ({ getSocket: () => socketStub }))

vi.mock('@/composables/useSkeletonLoading', () => ({
  useSkeletonLoading: () => ({
    isLoading: () => false,
    withLoading: async (_key, fn) => fn(),
  }),
}))

const scenario = (over = {}) => ({
  id: 1,
  scenario_name: 'S',
  function_type_id: 7,
  is_owner: false,
  owner_name: 'ieb-rudolph',
  thread_count: 300,
  invitation: { status: 'accepted' },
  ...over,
})

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.getItem.mockReturnValue(undefined)
  Object.keys(socketHandlers).forEach((k) => delete socketHandlers[k])
  socketStub.connected = true
  // IntersectionObserver drives lazy stats loading; not under test here.
  vi.stubGlobal('IntersectionObserver', class {
    observe() {}
    unobserve() {}
    disconnect() {}
  })
})

async function mountHub(scenarios) {
  axios.get.mockImplementation((url) => {
    if (url === '/api/scenarios') return Promise.resolve({ data: { scenarios } })
    return Promise.resolve({ data: {} })
  })

  const wrapper = mount(EvaluationHub, {
    global: {
      plugins: [vuetify],
      stubs: {
        LBtn: true,
        LTag: true,
        LIcon: true,
        LEvaluationStatus: true,
      },
      mocks: { $t: (key) => key },
    },
  })
  await flushPromises()
  await nextTickTwice(wrapper)
  return wrapper
}

async function nextTickTwice(wrapper) {
  await wrapper.vm.$nextTick()
  await wrapper.vm.$nextTick()
}

const titles = (wrapper) => wrapper.findAll('.card-title').map((n) => n.text())
const chip = (wrapper, key) => wrapper.find(`.filter-chip[data-filter="${key}"]`)
const chipText = (wrapper, key) => chip(wrapper, key).text()

async function selectFilter(wrapper, key) {
  await chip(wrapper, key).trigger('click')
  await wrapper.vm.$nextTick()
}

describe('EvaluationHub scenario visibility', () => {
  it('EVHUB_001: expired scenarios remain reachable via the filter', async () => {
    // The original bug was that they vanished with no way back. They are no
    // longer in the default view, but one click must still surface them.
    const wrapper = await mountHub([
      scenario({ id: 660, scenario_name: 'Survey Screening', status: 'completed' }),
    ])
    expect(titles(wrapper)).toEqual([])

    await selectFilter(wrapper, 'expired')
    expect(titles(wrapper)).toContain('Survey Screening')
  })

  it('EVHUB_002: marks expired scenarios with an expired chip', async () => {
    const wrapper = await mountHub([
      scenario({ id: 660, scenario_name: 'Survey Screening', status: 'completed' }),
    ])
    await selectFilter(wrapper, 'expired')

    expect(wrapper.find('.expired-chip').exists()).toBe(true)
    expect(wrapper.find('.scenario-card').classes()).toContain('is-expired')
  })

  it('EVHUB_003: does not mark running scenarios as expired', async () => {
    const wrapper = await mountHub([
      scenario({ id: 869, scenario_name: 'Konsens', status: 'evaluating' }),
    ])
    expect(wrapper.find('.expired-chip').exists()).toBe(false)
    expect(wrapper.find('.scenario-card').classes()).not.toContain('is-expired')
  })

  it('EVHUB_004: still hides archived and draft scenarios', async () => {
    const wrapper = await mountHub([
      scenario({ id: 1, scenario_name: 'Archived', status: 'archived' }),
      scenario({ id: 2, scenario_name: 'Draft', status: 'draft' }),
      scenario({ id: 3, scenario_name: 'Running', status: 'evaluating' }),
    ])
    expect(titles(wrapper)).toEqual(['Running'])
  })

  it('EVHUB_005: still hides scenarios without an accepted invitation', async () => {
    const wrapper = await mountHub([
      scenario({ id: 1, scenario_name: 'Pending', invitation: { status: 'pending' } }),
      scenario({ id: 2, scenario_name: 'Rejected', invitation: { status: 'rejected' } }),
      scenario({ id: 3, scenario_name: 'Accepted' }),
    ])
    expect(titles(wrapper)).toEqual(['Accepted'])
  })

  it('EVHUB_006: sorts strictly newest-created first, ignoring schedule state', async () => {
    const wrapper = await mountHub([
      scenario({ id: 660, scenario_name: 'Alt', status: 'evaluating', begin: '2026-01-01' }),
      scenario({ id: 869, scenario_name: 'Neu', status: 'evaluating', begin: '2026-07-01' }),
    ])
    expect(titles(wrapper)).toEqual(['Neu', 'Alt'])
  })
})

describe('EvaluationHub filter bar', () => {
  const mixed = () => [
    scenario({ id: 1, scenario_name: 'Laeuft-offen', status: 'evaluating',
               user_progress: { completed: 0, total: 10 }, begin: '2026-07-20' }),
    scenario({ id: 2, scenario_name: 'Laeuft-teilweise', status: 'evaluating',
               user_progress: { completed: 4, total: 10 }, begin: '2026-07-22' }),
    scenario({ id: 3, scenario_name: 'Laeuft-fertig', status: 'evaluating',
               user_progress: { completed: 10, total: 10 }, begin: '2026-07-24' }),
    scenario({ id: 4, scenario_name: 'Beendet', status: 'completed',
               user_progress: { completed: 2, total: 10 }, begin: '2026-07-26' }),
  ]

  it('EVHUB_007: defaults to active only — no expired scenarios', async () => {
    const wrapper = await mountHub(mixed())
    expect(titles(wrapper)).not.toContain('Beendet')
    expect(titles(wrapper)).toHaveLength(3)
  })

  it('EVHUB_008: sorts newest created first', async () => {
    const wrapper = await mountHub(mixed())
    // begin doubles as the creation timestamp in the API payload.
    expect(titles(wrapper)).toEqual(['Laeuft-fertig', 'Laeuft-teilweise', 'Laeuft-offen'])
  })

  it('EVHUB_009: "Alle" reveals the expired ones too', async () => {
    const wrapper = await mountHub(mixed())
    await selectFilter(wrapper, 'all')
    expect(titles(wrapper)).toHaveLength(4)
    expect(titles(wrapper)).toContain('Beendet')
  })

  it('EVHUB_010: each progress filter selects its own bucket', async () => {
    const wrapper = await mountHub(mixed())

    await selectFilter(wrapper, 'pending')
    expect(titles(wrapper)).toEqual(['Laeuft-offen'])

    await selectFilter(wrapper, 'in_progress')
    expect(titles(wrapper)).toEqual(['Laeuft-teilweise'])

    await selectFilter(wrapper, 'done')
    expect(titles(wrapper)).toEqual(['Laeuft-fertig'])

    await selectFilter(wrapper, 'expired')
    expect(titles(wrapper)).toEqual(['Beendet'])
  })

  it('EVHUB_011: progress buckets never include expired scenarios', async () => {
    // An elapsed study is not something a rater can still be "pending" on;
    // it belongs under "Beendet" only.
    const wrapper = await mountHub([
      scenario({ id: 4, scenario_name: 'Beendet', status: 'completed',
                 user_progress: { completed: 0, total: 10 } }),
    ])

    for (const key of ['pending', 'in_progress', 'done']) {
      await selectFilter(wrapper, key)
      expect(titles(wrapper)).toEqual([])
    }
    await selectFilter(wrapper, 'expired')
    expect(titles(wrapper)).toEqual(['Beendet'])
  })

  it('EVHUB_012: chip counts reflect the full set, not the current view', async () => {
    const wrapper = await mountHub(mixed())

    expect(chipText(wrapper, 'active')).toContain('(3)')
    expect(chipText(wrapper, 'pending')).toContain('(1)')
    expect(chipText(wrapper, 'in_progress')).toContain('(1)')
    expect(chipText(wrapper, 'done')).toContain('(1)')
    expect(chipText(wrapper, 'expired')).toContain('(1)')
    expect(chipText(wrapper, 'all')).toContain('(4)')

    // Counts must not shrink to "what is currently rendered".
    await selectFilter(wrapper, 'pending')
    expect(chipText(wrapper, 'all')).toContain('(4)')
  })

  it('EVHUB_013: marks the selected chip as active', async () => {
    const wrapper = await mountHub(mixed())
    expect(chip(wrapper, 'active').classes()).toContain('active')

    await selectFilter(wrapper, 'expired')
    expect(chip(wrapper, 'expired').classes()).toContain('active')
    expect(chip(wrapper, 'active').classes()).not.toContain('active')
  })

  it('EVHUB_014: expired cards stay greyed out but clickable', async () => {
    const wrapper = await mountHub([
      scenario({ id: 660, scenario_name: 'Beendet', status: 'completed' }),
    ])
    await selectFilter(wrapper, 'expired')

    const card = wrapper.find('.scenario-card')
    expect(card.classes()).toContain('is-expired')

    // The grey veil must not swallow the click.
    await card.trigger('click')
    expect(pushSpy).toHaveBeenCalledWith(
      expect.objectContaining({ params: { scenarioId: 660 } })
    )
  })
})

// ==================== Live access grants (Socket.IO) ====================
//
// When someone grants this user access to a scenario, the backend pushes it to
// their personal invite room. Before this, a rater sitting on the hub had no
// idea a study had been shared until they reloaded the page.

describe('EvaluationHub live access grants', () => {
  const granted = (over = {}) => ({
    scenario: scenario({ id: 869, scenario_name: 'Konsens Grenzfaelle', status: 'evaluating', ...over }),
  })

  it('EVHUB_015: subscribes to its own invite room on mount', async () => {
    await mountHub([])
    expect(socketStub.emit).toHaveBeenCalledWith('scenario:subscribe_invites', {})
  })

  it('EVHUB_016: inserts a scenario pushed in live', async () => {
    const wrapper = await mountHub([])
    expect(titles(wrapper)).toEqual([])

    socketHandlers['scenario:access_granted'](granted())
    await wrapper.vm.$nextTick()

    expect(titles(wrapper)).toContain('Konsens Grenzfaelle')
  })

  it('EVHUB_017: marks the new card so it animates', async () => {
    const wrapper = await mountHub([])
    socketHandlers['scenario:access_granted'](granted())
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.scenario-card').classes()).toContain('is-new')
    expect(wrapper.find('.new-chip').exists()).toBe(true)
  })

  it('EVHUB_018: updates in place instead of duplicating a known scenario', async () => {
    const wrapper = await mountHub([
      scenario({ id: 869, scenario_name: 'Alt', status: 'evaluating' }),
    ])

    socketHandlers['scenario:access_granted'](granted({ scenario_name: 'Neu' }))
    await wrapper.vm.$nextTick()

    expect(titles(wrapper)).toEqual(['Neu'])
  })

  it('EVHUB_019: ignores malformed payloads', async () => {
    const wrapper = await mountHub([])

    socketHandlers['scenario:access_granted'](undefined)
    socketHandlers['scenario:access_granted']({})
    socketHandlers['scenario:access_granted']({ scenario: {} })
    await wrapper.vm.$nextTick()

    expect(titles(wrapper)).toEqual([])
  })

  it('EVHUB_020: re-subscribes after a reconnect', async () => {
    await mountHub([])
    socketStub.emit.mockClear()

    // Room membership lives server-side and is lost when the socket drops.
    socketHandlers['connect']()

    expect(socketStub.emit).toHaveBeenCalledWith('scenario:subscribe_invites', {})
  })
})
