/**
 * LabelingInterface Tests
 *
 * Test IDs: LABEL_001 - LABEL_018
 *
 * Regression coverage for two production incidents:
 *
 * 1. (scenario 660) Labeling evaluations were never persisted: when embedded in
 *    EvaluationSession (hideNavigation), LEvaluationLayout hides the action bar
 *    and with it the only "Save" button, so labels were lost. The interface
 *    auto-saves on selection (mirroring ComparisonInterface / RatingInterface).
 *
 * 2. (scenario 758, question-first labeling) A rater answered two of three
 *    decision questions and navigated on — nothing was saved, because the
 *    auto-save gate required a COMPLETE (derivable) label. Every click now
 *    persists: the POST carries `category_id: null` plus the partial
 *    `answers_json`, the item counts as "in Bearbeitung" (item-progress, no
 *    item-completed), and navigation awaits the in-flight save.
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
  // Mirrors the backend contract: a row with a label (or "unsure") is done, a
  // row that only carries answers/feedback is in_progress.
  axios.post.mockImplementation((url, body) => Promise.resolve({
    data: {
      success: true,
      status: (body?.category_id || body?.is_unsure) ? 'done' : 'in_progress'
    }
  }))
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

  // ---------------------------------------------------------------------------
  // Question-first labeling + second choice (LABEL_009 - LABEL_013).
  // The rater answers decision questions (VRM: three questions, S or G each);
  // the label is DERIVED from the answer key and never pre-selected.
  // ---------------------------------------------------------------------------
  const CATS = [
    { id: 'D', name: { de: 'D — Offenlegung' }, color: '#e8a087' },
    { id: 'Q', name: { de: 'Q — Frage' }, color: '#c9b8d8' },
    { id: 'A', name: { de: 'A — Ratschlag' }, color: '#88c4c8' },
  ]
  const QUESTION = (id, title) => ({
    id,
    title: { de: title },
    text: { de: `${title}?` },
    options: [
      { id: 'S', label: { de: 'Sprecher:in' } },
      { id: 'G', label: { de: 'Gegenüber' }, hint: { de: 'dein Erleben' } },
    ],
  })
  const QUESTIONS_CONFIG = {
    eval_config: {
      config: {
        allowUnsure: false,
        second_choice: true,
        categories: CATS,
        questions: {
          enabled: true,
          sliders: false,
          items: [QUESTION('q1', 'Thema'), QUESTION('q2', 'Präsupposition'), QUESTION('q3', 'Bezugsrahmen')],
          mapping: { SSS: 'D', GSS: 'Q', SGS: 'A' },
        },
      },
    },
  }

  async function answer(wrapper, qid, opt) {
    await wrapper.find(`[data-test="answer-${qid}-${opt}"]`).trigger('click')
    await flushPromises()
  }

  it('LABEL_009: answering all questions derives the label and POSTs answers_json', async () => {
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()

    expect(wrapper.find('[data-test="questions-section"]').exists()).toBe(true)
    await answer(wrapper, 'q1', 'S')
    await answer(wrapper, 'q2', 'S')
    // Two of three answered: no label derived yet, but both answers are saved
    // (one POST per click) — see LABEL_014.
    expect(axios.post).toHaveBeenCalledTimes(2)
    expect(axios.post.mock.calls.every(([, b]) => b.category_id === null)).toBe(true)

    await answer(wrapper, 'q3', 'S')
    expect(axios.post).toHaveBeenCalledTimes(3)
    const body = axios.post.mock.calls[2][1]
    expect(body.category_id).toBe('D')
    expect(body.answers_json).toMatchObject({ q1: 'S', q2: 'S', q3: 'S', derived: 'D', source: 'questions' })
    expect(wrapper.find('[data-test="derived-label"]').text()).toContain('D — Offenlegung')
  })

  it('LABEL_010: direct choice is collapsed by default and answers the questions backwards', async () => {
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()

    // v-show toggles an inline display:none (the wrapper is not attached to
    // a document, so isVisible() is not reliable here).
    const buttons = wrapper.find('[data-test="category-buttons"]')
    expect(buttons.attributes('style') || '').toContain('display: none')
    await wrapper.find('[data-test="direct-toggle"]').trigger('click')
    expect(buttons.attributes('style') || '').not.toContain('display: none')

    await wrapper.findAll('.l-label-btn')[1].trigger('click') // Q
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(1)
    const body = axios.post.mock.calls[0][1]
    expect(body.category_id).toBe('Q')
    expect(body.answers_json).toMatchObject({ q1: 'G', q2: 'S', q3: 'S', derived: 'Q', source: 'direct' })
    expect(wrapper.find('[data-test="answer-q1-G"]').classes()).toContain('active')
  })

  it('LABEL_011: second choice is offered only after a first label and is saved separately', async () => {
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()
    expect(wrapper.find('[data-test="second-choice"]').exists()).toBe(false)

    await answer(wrapper, 'q1', 'S')
    await answer(wrapper, 'q2', 'G')
    await answer(wrapper, 'q3', 'S') // → A
    expect(wrapper.find('[data-test="second-choice"]').exists()).toBe(true)
    // The first choice is never offered as its own second choice.
    expect(wrapper.find('[data-test="second-A"]').exists()).toBe(false)

    await wrapper.find('[data-test="second-Q"]').trigger('click')
    await flushPromises()
    const last = axios.post.mock.calls.at(-1)[1]
    expect(last.category_id).toBe('A')
    expect(last.second_choice_id).toBe('Q')
  })

  it('LABEL_012: pending feedback is flushed before navigating to the next item', async () => {
    const wrapper = mountInterface()
    await flushPromises()
    await wrapper.findAll('.l-label-btn')[0].trigger('click')
    await flushPromises()
    expect(axios.post).toHaveBeenCalledTimes(1)

    // Type a comment and navigate BEFORE the 800 ms debounce fires — the
    // old code cleared the timer and reset the textarea, losing the comment.
    wrapper.vm.feedback = 'knapper Fall, Q auch vertretbar'
    await flushPromises()
    await wrapper.vm.goNext()
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(2)
    const [url, body] = axios.post.mock.calls[1]
    expect(url).toBe(`${EVALUATE_URL}/11592/evaluate`)
    expect(body.feedback).toBe('knapper Fall, Q auch vertretbar')
  })

  it('LABEL_013: restoring saved answers + second choice does not re-POST', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('/api/evaluation/session/')) {
        return Promise.resolve({
          data: {
            items: [{
              thread_id: 11592, evaluated: true,
              evaluation: {
                category_id: 'Q', is_unsure: false, feedback: '',
                second_choice_id: 'A',
                answers_json: { q1: 'G', q2: 'S', q3: 'S', derived: 'Q', source: 'questions' },
              },
            }],
          },
        })
      }
      return Promise.resolve({ data: { thread: { messages: [] } } })
    })
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()

    expect(axios.post).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="answer-q1-G"]').classes()).toContain('active')
    expect(wrapper.find('[data-test="derived-label"]').text()).toContain('Q — Frage')
    expect(wrapper.find('[data-test="second-A"]').classes()).toContain('active')
  })

  // ---------------------------------------------------------------------------
  // Partial saves (LABEL_014 - LABEL_018). Prod scenario 758: a rater answered
  // two of three questions, clicked Next, and NOTHING was stored because the
  // auto-save gate was `canSubmit` (a derivable label). Every click persists
  // now; the item is "in Bearbeitung" until the label is complete.
  // ---------------------------------------------------------------------------

  it('LABEL_014: answering ONE question POSTs immediately with category_id null', async () => {
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()

    await answer(wrapper, 'q1', 'S')

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url, body] = axios.post.mock.calls[0]
    expect(url).toBe(`${EVALUATE_URL}/11592/evaluate`)
    // The study invariant: a partial save must NEVER write a label.
    expect(body.category_id).toBeNull()
    expect(body.is_unsure).toBe(false)
    expect(body.answers_json).toMatchObject({ q1: 'S', derived: null, source: 'questions' })
    expect(body.answers_json.q2).toBeUndefined()
  })

  it('LABEL_015: moving a lean slider saves (debounced) without a label', async () => {
    const SLIDER_CONFIG = {
      eval_config: {
        config: {
          ...QUESTIONS_CONFIG.eval_config.config,
          questions: { ...QUESTIONS_CONFIG.eval_config.config.questions, sliders: true }
        }
      }
    }
    const wrapper = mountInterface({ config: SLIDER_CONFIG })
    await flushPromises()

    // Only setTimeout/clearTimeout are faked so flushPromises (setImmediate)
    // keeps working while we jump over the 300 ms slider debounce.
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    try {
      wrapper.vm.setLean('q1', 80)
      await wrapper.vm.$nextTick()
      expect(axios.post).not.toHaveBeenCalled() // still debouncing
      vi.advanceTimersByTime(350)
    } finally {
      vi.useRealTimers()
    }
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(1)
    const body = axios.post.mock.calls[0][1]
    expect(body.category_id).toBeNull()
    expect(body.answers_json.lean).toEqual({ q1: 80 })
  })

  it('LABEL_016: a partial save reports in_progress and does NOT complete the item', async () => {
    // Non-embedded so the panel header (status tag) renders.
    const wrapper = mountInterface({ config: QUESTIONS_CONFIG, hideNavigation: false })
    await flushPromises()
    expect(wrapper.find('[data-test="header-status"]').attributes('data-status')).toBe('pending')

    await answer(wrapper, 'q1', 'S')
    await answer(wrapper, 'q2', 'G')

    const progress = wrapper.emitted('item-progress')
    expect(progress).toBeTruthy()
    expect(progress.at(-1)[0]).toEqual({ itemId: 11592, status: 'in_progress' })
    // Two of three answers are not an evaluation — the session must not count it.
    expect(wrapper.emitted('item-completed')).toBeFalsy()
    expect(wrapper.emitted('all-completed')).toBeFalsy()
    expect(wrapper.emitted('status-change').at(-1)[0]).toBe('in_progress')
    expect(wrapper.find('[data-test="header-status"]').attributes('data-status')).toBe('in_progress')

    // Completing the label flips both the status and the completion emit.
    await answer(wrapper, 'q3', 'S')
    expect(wrapper.emitted('item-completed').at(-1)[0]).toBe(11592)
    expect(wrapper.emitted('item-progress').at(-1)[0]).toEqual({ itemId: 11592, status: 'done' })
    expect(wrapper.find('[data-test="header-status"]').attributes('data-status')).toBe('done')
  })

  it('LABEL_017: navigating after a partial answer awaits the in-flight save', async () => {
    let resolvePost
    axios.post.mockImplementationOnce(() => new Promise((resolve) => { resolvePost = resolve }))

    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()
    await answer(wrapper, 'q1', 'S')
    expect(axios.post).toHaveBeenCalledTimes(1)

    let navigated = false
    const navigation = wrapper.vm.goNext().then(() => { navigated = true })
    await flushPromises()
    // The POST is still on the wire — the item must not switch underneath it.
    expect(navigated).toBe(false)
    expect(wrapper.vm.currentItemIndex).toBe(0)

    resolvePost({ data: { success: true, status: 'in_progress' } })
    await navigation
    await flushPromises()

    expect(navigated).toBe(true)
    expect(axios.post.mock.calls[0][0]).toBe(`${EVALUATE_URL}/11592/evaluate`)
    expect(wrapper.vm.currentItemIndex).toBe(1)
  })

  it('LABEL_018: a partial prefill (no category, answers present) is restored', async () => {
    axios.get.mockImplementation((url) => {
      if (url.includes('/api/evaluation/session/')) {
        return Promise.resolve({
          data: {
            items: [{
              thread_id: 11592, evaluated: false,
              evaluation: {
                category_id: null, is_unsure: false, feedback: '', second_choice_id: null,
                answers_json: { q1: 'G', q2: 'S', derived: null, source: 'questions' },
              },
            }],
          },
        })
      }
      return Promise.resolve({ data: { thread: { messages: [] } } })
    })

    const wrapper = mountInterface({ config: QUESTIONS_CONFIG })
    await flushPromises()

    // Restoring is programmatic — it must never re-POST.
    expect(axios.post).not.toHaveBeenCalled()
    expect(wrapper.find('[data-test="answer-q1-G"]').classes()).toContain('active')
    expect(wrapper.find('[data-test="answer-q2-S"]').classes()).toContain('active')
    // The third question stays unanswered and no label is pre-selected.
    expect(wrapper.find('[data-test="answer-q3-S"]').classes()).not.toContain('active')
    expect(wrapper.find('[data-test="answer-q3-G"]').classes()).not.toContain('active')
    expect(wrapper.find('[data-test="second-choice"]').exists()).toBe(false)
    // Session sidebar/footer: the item is in progress, not pending.
    expect(wrapper.emitted('status-change').at(-1)[0]).toBe('in_progress')
  })
})
