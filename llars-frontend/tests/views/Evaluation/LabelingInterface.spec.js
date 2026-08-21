/**
 * LabelingInterface Tests
 *
 * Test IDs: LABEL_001 - LABEL_006
 *
 * Regression coverage for the production incident where labeling evaluations
 * were never persisted: when embedded in EvaluationSession (hideNavigation),
 * LEvaluationLayout hides the action bar and with it the only "Save" button,
 * so labels were lost. The interface now auto-saves on selection (mirroring
 * ComparisonInterface / RatingInterface). These tests lock that behaviour in.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as vuetifyComponents from 'vuetify/components'
import * as vuetifyDirectives from 'vuetify/directives'
import LabelingInterface from '@/views/Evaluation/interfaces/LabelingInterface.vue'

const vuetify = createVuetify({ components: vuetifyComponents, directives: vuetifyDirectives })

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }))
import axios from 'axios'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn() }),
}))

vi.mock('@/composables/usePanelResize', () => ({
  usePanelResize: () => ({
    containerRef: ref(null),
    leftPanelStyle: () => ({}),
    rightPanelStyle: () => ({}),
    startResize: vi.fn(),
    isResizing: ref(false),
  }),
}))

vi.mock('@/composables/useMobile', () => ({
  useMobile: () => ({ isMobile: ref(false) }),
}))

const SCENARIO_ID = 660
const EVALUATE_URL = `/api/evaluation/session/${SCENARIO_ID}/items`

// config_json shape produced by api_v1 scenarios (nested under eval_config.config)
const CONFIG = {
  eval_config: {
    config: {
      allowUnsure: true,
      categories: [
        { id: 'cat_include', name: { de: 'include', en: 'include' }, color: '#98d4bb' },
        { id: 'cat_exclude', name: { de: 'exclude', en: 'exclude' }, color: '#e8a087' },
      ],
    },
  },
}

const SESSION_ITEMS = [
  { thread_id: 11592, evaluated: false, evaluation: null },
  { thread_id: 11593, evaluated: false, evaluation: null },
]

function installAxios() {
  axios.get.mockImplementation((url) => {
    if (url.includes('/api/evaluation/session/')) {
      return Promise.resolve({ data: { items: JSON.parse(JSON.stringify(SESSION_ITEMS)) } })
    }
    // thread detail
    return Promise.resolve({ data: { thread: { messages: [{ sender: 'x', content: 'Some abstract' }] } } })
  })
  axios.post.mockResolvedValue({ data: { success: true, status: 'completed' } })
}

function mountInterface(props = {}) {
  return mount(LabelingInterface, {
    props: {
      scenarioId: SCENARIO_ID,
      scenario: { can_evaluate: true },
      config: CONFIG,
      hideNavigation: true, // embedded mode — the scenario where the bug lived
      ...props,
    },
    global: {
      plugins: [vuetify],
      stubs: {
        // Render only the default slot so the category buttons appear; the
        // action-bar-right slot (the old save button) is intentionally NOT
        // rendered here, reproducing embedded mode.
        LEvaluationLayout: { template: '<div><slot /></div>' },
        LIconBtn: true,
        LTag: true,
        LBtn: true,
        LMessageList: true,
        'v-checkbox': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input type="checkbox" :checked="modelValue" @change="$emit(\'update:modelValue\', $event.target.checked)" />',
        },
        'v-textarea': true,
        'v-dialog': true,
        'v-spacer': true,
        'v-progress-circular': true,
        'v-skeleton-loader': true,
      },
    },
  })
}

describe('LabelingInterface auto-save', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    installAxios()
  })

  it('LABEL_001: loads session items on mount', async () => {
    const wrapper = mountInterface()
    await flushPromises()
    expect(axios.get).toHaveBeenCalledWith(`/api/evaluation/session/${SCENARIO_ID}`)
    expect(wrapper.findAll('.l-label-btn').length).toBe(2)
  })

  it('LABEL_002: auto-saves (POSTs) immediately when a category is selected', async () => {
    const wrapper = mountInterface()
    await flushPromises()

    await wrapper.findAll('.l-label-btn')[0].trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url, body] = axios.post.mock.calls[0]
    expect(url).toBe(`${EVALUATE_URL}/11592/evaluate`)
    expect(body).toMatchObject({
      function_type: 'labeling',
      category_id: 'cat_include',
      is_unsure: false,
    })
  })

  it('LABEL_003: does NOT POST while merely loading/navigating items', async () => {
    mountInterface()
    await flushPromises()
    // Mounting + initial item load must never trigger a save on its own.
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('LABEL_004: selecting "unsure" auto-saves with is_unsure=true and no category', async () => {
    const wrapper = mountInterface()
    await flushPromises()

    await wrapper.find('input[type="checkbox"]').setValue(true)
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(1)
    const body = axios.post.mock.calls[0][1]
    expect(body.is_unsure).toBe(true)
    expect(body.category_id).toBeNull()
  })

  it('LABEL_005: read-only users (can_evaluate=false) cannot save', async () => {
    const wrapper = mountInterface({ scenario: { can_evaluate: false } })
    await flushPromises()

    await wrapper.findAll('.l-label-btn')[0].trigger('click')
    await flushPromises()

    expect(axios.post).not.toHaveBeenCalled()
  })

  it('LABEL_006: restoring a previously-saved label does not re-POST', async () => {
    // Item already labeled — the prefill must not trigger an auto-save.
    axios.get.mockImplementation((url) => {
      if (url.includes('/api/evaluation/session/')) {
        return Promise.resolve({
          data: { items: [{ thread_id: 11592, evaluated: true, evaluation: { category_id: 'cat_exclude', is_unsure: false, feedback: '' } }] },
        })
      }
      return Promise.resolve({ data: { thread: { messages: [] } } })
    })

    mountInterface()
    await flushPromises()
    expect(axios.post).not.toHaveBeenCalled()
  })

  // Regression (prod scenario 660): the footer status tag showed the OVERALL
  // labeling progress instead of the CURRENT item's status. So a fresh, untouched
  // item read "In Bearbeitung" (because ANOTHER item was already done), and
  // navigating back to a completed item wrongly read "In Bearbeitung" instead of
  // "Abgeschlossen". The interface now emits the current item's status.
  const MIXED_ITEMS = [
    { thread_id: 11678, evaluated: true, evaluation: { category_id: 'cat_include', is_unsure: false } },
    { thread_id: 11679, evaluated: false, evaluation: null },
  ]
  function installMixedAxios() {
    axios.get.mockImplementation((url) => {
      if (url.includes('/api/evaluation/session/')) {
        return Promise.resolve({ data: { items: JSON.parse(JSON.stringify(MIXED_ITEMS)) } })
      }
      return Promise.resolve({ data: { thread: { messages: [] } } })
    })
  }

  it('LABEL_007: status-change reflects the CURRENT fresh item as pending (not overall in_progress)', async () => {
    installMixedAxios()
    // Land on the untouched second item while the first is already done.
    const wrapper = mountInterface({ initialItemId: 11679 })
    await flushPromises()
    const emits = wrapper.emitted('status-change')
    expect(emits).toBeTruthy()
    // The LAST emitted status must be the current item's: pending — NOT the
    // aggregate 'in_progress' (which the old code emitted since 1 of 2 was done).
    expect(emits[emits.length - 1][0]).toBe('pending')
  })

  it('LABEL_008: status-change of a completed item stays done (no regression to in_progress)', async () => {
    installMixedAxios()
    // Navigate back to the already-completed first item.
    const wrapper = mountInterface({ initialItemId: 11678 })
    await flushPromises()
    const emits = wrapper.emitted('status-change')
    expect(emits).toBeTruthy()
    expect(emits[emits.length - 1][0]).toBe('done')
  })
})
