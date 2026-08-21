/**
 * ConversationLabelingInterface Tests
 *
 * Test IDs: CONVLAB_001 - CONVLAB_023
 *
 * One item is a whole conversation; one decision is a single span inside it.
 * The behaviours locked in here are the ones the study depends on, not the
 * cosmetics:
 *
 *  - resume at the first UNDECIDED span (a conversation is ~20 min of work)
 *  - auto-save on selection (embedded mode has no save button at all — an
 *    interface that waits for one persists nothing, which once left a
 *    production labeling study with an empty results table)
 *  - already-decided spans show their label inline (this is how a rater sees
 *    two identical labels in a row — the block-merge signal)
 *  - keyboard: digits pick, Enter advances, Backspace steps back
 *  - co-pilot suggestions are never pre-selected
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as vuetifyComponents from 'vuetify/components'
import * as vuetifyDirectives from 'vuetify/directives'
import ConversationLabelingInterface from '@/views/Evaluation/interfaces/ConversationLabelingInterface.vue'

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

const SCENARIO_ID = 900
const ITEM_ID = 5001

const MSG_TEXT = 'Sehr geehrte Frau Schmidt. Ich bin Dr. Becker. Wie geht es Ihnen?'

const SPANS = [
  { span_id: 'm2-s01', message_index: 1, message_id: 2, span_index: 0, start: 0, end: 26 },
  { span_id: 'm2-s02', message_index: 1, message_id: 2, span_index: 1, start: 27, end: 46 },
  { span_id: 'm2-s03', message_index: 1, message_id: 2, span_index: 2, start: 47, end: 64 },
]

const CONFIG = {
  eval_config: {
    config: {
      labels: [
        { id: 'D', label: { de: 'Disclosure', en: 'Disclosure' }, color: '#b0ca97' },
        { id: 'E', label: { de: 'Edification', en: 'Edification' }, color: '#88c4c8' },
        { id: 'A', label: { de: 'Advisement', en: 'Advisement' }, color: '#e8a087' },
      ],
      allowUnsure: true,
      context_window: 3,
      future_spans: 'dimmed',
      no_future_messages: true,
    },
  },
}

function sessionItem(over = {}) {
  return {
    id: ITEM_ID,
    thread_id: ITEM_ID,
    metadata_json: {
      conversation_labeling: { spans: SPANS, labelable_messages: [1] },
    },
    evaluation: null,
    copilot_suggestion: null,
    ...over,
  }
}

const THREAD = {
  thread: {
    messages: [
      { id: 10, sender: 'Ratsuchende', content: 'Mein Sohn hat Probleme.' },
      { id: 11, sender: 'Beratende', content: MSG_TEXT },
    ],
  },
}

function installAxios(items) {
  axios.get.mockImplementation((url) => {
    if (url.includes('/api/evaluation/session/')) {
      return Promise.resolve({ data: { items } })
    }
    if (url.includes('/threads/')) {
      return Promise.resolve({ data: JSON.parse(JSON.stringify(THREAD)) })
    }
    return Promise.resolve({ data: {} })
  })
  axios.post.mockResolvedValue({ data: { success: true } })
}

async function mountInterface(items = [sessionItem()]) {
  installAxios(items)
  const wrapper = mount(ConversationLabelingInterface, {
    props: { scenarioId: SCENARIO_ID, config: CONFIG, scenario: { id: SCENARIO_ID } },
    global: {
      plugins: [vuetify],
      stubs: {
        LEvaluationLayout: { template: '<div><slot /></div>' },
        LBtn: { template: '<button class="l-btn" @click="$emit(\'click\')"><slot /></button>' },
        LIcon: true,
        LTag: { template: '<span><slot /></span>' },
        // LMessage exposes a default slot; the spans are rendered INTO it, so
        // the stub must render the slot or nothing would be testable.
        LMessage: {
          props: ['sender', 'senderType'],
          template: '<div class="l-message" :data-sender-type="senderType"><span class="l-sender">{{ sender }}</span><div class="l-message__body"><slot /></div></div>',
        },
        'v-checkbox': {
          props: ['modelValue', 'label'],
          emits: ['update:modelValue'],
          template: '<button class="unsure-box" @click="$emit(\'update:modelValue\', !modelValue)">{{ label }}</button>',
        },
        'v-switch': {
          props: ['modelValue', 'label'],
          emits: ['update:modelValue'],
          template: '<button class="autoadvance-switch" @click="$emit(\'update:modelValue\', !modelValue)">{{ label }}</button>',
        },
        'v-spacer': true,
        // No emits declared on purpose: the @click in the template then falls
        // through as a native listener on the root button.
        LIconBtn: {
          props: ['icon', 'disabled'],
          template: '<button class="l-icon-btn" :data-icon="icon" :disabled="disabled"></button>',
        },
        'v-textarea': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<textarea class="feedback-box" :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)"></textarea>',
        },
      },
      mocks: { $t: (key, params) => (params ? `${key}:${JSON.stringify(params)}` : key) },
    },
  })
  await flushPromises()
  await wrapper.vm.$nextTick()
  return wrapper
}

const categoryButtons = (w) => w.findAll('.l-label-btn')
const focusText = (w) => w.find('.focus-span').text()
const press = (key) => window.dispatchEvent(new KeyboardEvent('keydown', { key }))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ConversationLabelingInterface', () => {

  it('CONVLAB_001: renders the conversation history and the focus span', async () => {
    const w = await mountInterface()
    expect(w.text()).toContain('Mein Sohn hat Probleme.')
    expect(focusText(w)).toBe(MSG_TEXT.slice(0, 26))
  })

  it('CONVLAB_002: starts on the first span when nothing is decided', async () => {
    const w = await mountInterface()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[0].start, SPANS[0].end))
  })

  it('CONVLAB_003: resumes at the first UNDECIDED span', async () => {
    // The core resume requirement: ~20 minutes per conversation means landing
    // back at span 1 would be a real loss of work.
    const w = await mountInterface([sessionItem({
      evaluation: { spans: { 'm2-s01': { category_id: 'D', is_unsure: false } } },
    })])
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[1].start, SPANS[1].end))
  })

  it('CONVLAB_004: shows the label of already-decided spans inline', async () => {
    // This is what makes the rater's own sequence visible — two identical
    // chips in a row are the block-merge signal.
    const w = await mountInterface([sessionItem({
      evaluation: { spans: { 'm2-s01': { category_id: 'D', is_unsure: false } } },
    })])
    expect(w.findAll('.span-chip').length).toBe(1)
  })

  it('CONVLAB_005: auto-saves on selection without any save button', async () => {
    const w = await mountInterface()
    await categoryButtons(w)[0].trigger('click')
    await flushPromises()

    expect(axios.post).toHaveBeenCalledTimes(1)
    const [url, body] = axios.post.mock.calls[0]
    expect(url).toContain(`/api/evaluation/session/${SCENARIO_ID}/items/${ITEM_ID}/evaluate`)
    expect(body.function_type).toBe('conversation_labeling')
    expect(body.span_id).toBe('m2-s01')
    expect(body.category_id).toBe('D')
  })

  it('CONVLAB_006: sends a span_id on every save', async () => {
    // Without it the backend would write one row per item and the second span
    // would collide with the unique key.
    const w = await mountInterface()
    await categoryButtons(w)[1].trigger('click')
    await flushPromises()
    expect(axios.post.mock.calls[0][1].span_id).toBe('m2-s01')
  })

  it('CONVLAB_007: digit keys pick the matching label', async () => {
    const w = await mountInterface()
    press('2')
    await flushPromises()
    expect(axios.post.mock.calls[0][1].category_id).toBe('E')
  })

  it('CONVLAB_008: auto-advance moves to the next span after a decision', async () => {
    // On by default: at ~92 decisions per conversation, clicking back into the
    // text every time is the dominant cost of the task.
    const w = await mountInterface()
    await categoryButtons(w)[0].trigger('click')
    await flushPromises()
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[1].start, SPANS[1].end))
  })

  it('CONVLAB_017: auto-advance can be switched off', async () => {
    const w = await mountInterface()
    await w.find('.autoadvance-switch').trigger('click')
    await w.vm.$nextTick()
    await categoryButtons(w)[0].trigger('click')
    await flushPromises()
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[0].start, SPANS[0].end))
  })

  it('CONVLAB_018: deselecting does NOT auto-advance', async () => {
    // Clearing a label is a correction, not progress — jumping away would
    // strand the rater on the wrong span.
    const w = await mountInterface()
    await w.find('.autoadvance-switch').trigger('click')   // off
    await w.vm.$nextTick()
    await categoryButtons(w)[0].trigger('click')           // set
    await flushPromises()
    await categoryButtons(w)[0].trigger('click')           // clear
    await flushPromises()
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[0].start, SPANS[0].end))
  })

  it('CONVLAB_019: renders the conversation as speech bubbles', async () => {
    const w = await mountInterface()
    const bubbles = w.findAll('.l-message')
    expect(bubbles.length).toBeGreaterThanOrEqual(2)
    // Client turn vs counsellor turn must be visually distinct.
    expect(bubbles[0].attributes('data-sender-type')).toBe('client')
    expect(bubbles[1].attributes('data-sender-type')).toBe('advisor')
  })

  it('CONVLAB_009: Enter on an untouched span does NOT skip it', async () => {
    // Skipping would leave a silent hole in the sequence.
    const w = await mountInterface()
    press('Enter')
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[0].start, SPANS[0].end))
  })

  it('CONVLAB_010: Backspace steps back one span', async () => {
    const w = await mountInterface()
    press('1')                       // decides span 1, auto-advances to span 2
    await flushPromises()
    await w.vm.$nextTick()
    press('Backspace')
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[0].start, SPANS[0].end))
  })

  it('CONVLAB_011: keyboard is ignored while typing in a field', async () => {
    await mountInterface()
    const input = document.createElement('input')
    document.body.appendChild(input)
    input.dispatchEvent(new KeyboardEvent('keydown', { key: '1', bubbles: true }))
    await flushPromises()
    expect(axios.post).not.toHaveBeenCalled()
    input.remove()
  })

  it('CONVLAB_012: clicking a span in the history focuses it', async () => {
    const w = await mountInterface()
    const spans = w.findAll('.l-message__body .span')
    const clickable = spans.filter(s => !s.classes().includes('span-gap'))
    await clickable[clickable.length - 1].trigger('click')
    await w.vm.$nextTick()
    expect(focusText(w)).toBe(MSG_TEXT.slice(SPANS[2].start, SPANS[2].end))
  })

  it('CONVLAB_013: "unsure" counts as a decision and is saved', async () => {
    const w = await mountInterface()
    await w.find('.unsure-box').trigger('click')
    await flushPromises()
    const body = axios.post.mock.calls[0][1]
    expect(body.is_unsure).toBe(true)
    expect(body.category_id).toBeNull()
  })

  it('CONVLAB_014: co-pilot suggestions are shown but never pre-selected', async () => {
    const w = await mountInterface([sessionItem({
      copilot_suggestion: { spans: { 'm2-s01': { suggestions: [{ label_id: 'E' }] } } },
    })])
    expect(w.find('.copilot-card').exists()).toBe(true)
    // Nothing selected, nothing saved, until the rater acts.
    expect(w.findAll('.l-label-btn.selected').length).toBe(0)
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('CONVLAB_015: applying a suggestion saves it as a normal decision', async () => {
    const w = await mountInterface([sessionItem({
      copilot_suggestion: { spans: { 'm2-s01': { suggestions: [{ label_id: 'E' }] } } },
    })])
    await w.find('.copilot-card .l-btn').trigger('click')
    await flushPromises()
    expect(axios.post.mock.calls[0][1].category_id).toBe('E')
  })

  it('CONVLAB_016: later messages stay hidden when no_future_messages is set', async () => {
    // PsyDefDetect convention: context up to and including the target span.
    const w = await mountInterface()
    expect(w.text()).toContain('Mein Sohn hat Probleme.')
    expect(w.find('.hidden-hint').exists()).toBe(false) // target is the last message
  })
})

describe('ConversationLabelingInterface span splitting', () => {
  // Hidden by design: the unitizing is frozen at import time, so splitting is
  // the sanctioned exception and must never sit in the primary flow.

  it('CONVLAB_020: the split control is not part of the normal flow', async () => {
    const w = await mountInterface()
    // Present but quiet — and the panel itself only appears on demand.
    expect(w.find('.split-trigger').exists()).toBe(true)
    expect(w.find('.split-panel').exists()).toBe(false)
  })

  it('CONVLAB_021: opening it reveals a character-level cut picker', async () => {
    const w = await mountInterface()
    await w.find('.split-trigger').trigger('click')
    await w.vm.$nextTick()
    expect(w.find('.split-panel').exists()).toBe(true)
    // One clickable position per character of the focus span.
    expect(w.findAll('.split-char').length).toBe(MSG_TEXT.slice(0, 26).length)
  })

  it('CONVLAB_022: posts the offset in MESSAGE coordinates', async () => {
    // The endpoint speaks the same coordinate system as span.start/end.
    // Sending an in-span index would silently cut the wrong place.
    const w = await mountInterface()
    await w.find('.split-trigger').trigger('click')
    await w.vm.$nextTick()
    await w.findAll('.split-char')[10].trigger('click')
    await w.vm.$nextTick()

    axios.post.mockResolvedValueOnce({
      data: { success: true, new_span_ids: ['m2-s01+a', 'm2-s01+b'], spans: SPANS },
    })
    const buttons = w.findAll('.l-btn')
    await buttons[buttons.length - 1].trigger('click')
    await flushPromises()

    const call = axios.post.mock.calls.find(c => String(c[0]).includes('/spans/split'))
    expect(call).toBeTruthy()
    expect(call[1]).toEqual({ span_id: 'm2-s01', offset: SPANS[0].start + 10 })
  })

  it('CONVLAB_023: navigating away closes the split panel', async () => {
    // An open cut point belongs to the span it was opened on — carrying it to
    // the next span would cut in the wrong place.
    const w = await mountInterface()
    await w.find('.split-trigger').trigger('click')
    await w.vm.$nextTick()
    expect(w.find('.split-panel').exists()).toBe(true)

    press('1')                 // decide + auto-advance
    await flushPromises()
    await w.vm.$nextTick()
    expect(w.find('.split-panel').exists()).toBe(false)
  })

  // --- co-pilot helpfulness and per-span notes ------------------------------

  const withCopilot = () => sessionItem({
    copilot_suggestion: { spans: { 'm2-s01': { suggestions: [{ label_id: 'E' }] } } },
  })

  const lastEvaluateCall = () =>
    [...axios.post.mock.calls].reverse().find(c => String(c[0]).includes('/evaluate'))

  /**
   * Decide the current span WITHOUT moving on. Auto-advance is on by default,
   * so a plain press() would leave the span under test — and the co-pilot card
   * belongs to the span it was suggested for, so it would vanish with it.
   */
  async function decideAndStay(w) {
    await w.find('.autoadvance-switch').trigger('click')
    press('1')
    await flushPromises()
  }

  it('CONVLAB_024: helpfulness vote rides along with the span save', async () => {
    // The log row is keyed by span, so the vote has to travel with THAT span's
    // save — an item-level vote could not say which suggestion it judged.
    const w = await mountInterface([withCopilot()])
    await decideAndStay(w)

    await w.findAll('.copilot-header .l-icon-btn')[0].trigger('click')
    await flushPromises()

    const call = lastEvaluateCall()
    expect(call[1].span_id).toBe('m2-s01')
    expect(call[1].copilot.helpful).toBe(true)
  })

  it('CONVLAB_025: clicking the active thumb clears the vote again', async () => {
    // Without a way back, a mis-click would be permanent study data.
    const w = await mountInterface([withCopilot()])
    await decideAndStay(w)

    await w.findAll('.copilot-header .l-icon-btn')[0].trigger('click')
    await flushPromises()
    await w.findAll('.copilot-header .l-icon-btn')[0].trigger('click')
    await flushPromises()

    expect(lastEvaluateCall()[1].copilot.helpful).toBe(null)
  })

  it('CONVLAB_026: typing a note does not post per keystroke', async () => {
    vi.useFakeTimers()
    try {
      const w = await mountInterface()
      await decideAndStay(w)
      const afterLabel = axios.post.mock.calls.length

      const box = w.find('.feedback-box')
      for (const value of ['G', 'Gr', 'Gre', 'Gren']) {
        await box.setValue(value)
      }
      expect(axios.post.mock.calls.length).toBe(afterLabel)

      vi.advanceTimersByTime(1000)
      await flushPromises()
      expect(lastEvaluateCall()[1].feedback).toBe('Gren')
    } finally {
      vi.useRealTimers()
    }
  })

  it('CONVLAB_027: leaving a span writes its pending note to that span', async () => {
    // The debounce must not outlive the span it belongs to, or the note lands
    // on whichever span the rater moved to next.
    vi.useFakeTimers()
    try {
      const w = await mountInterface()
      await decideAndStay(w)
      await w.find('.feedback-box').setValue('Grenzfall')

      // Move on before the debounce would have fired. `.span` also matches the
      // untouchable gaps between spans, so filter them out first.
      const clickable = w.findAll('.l-message__body .span')
        .filter(s => !s.classes().includes('span-gap'))
      await clickable[clickable.length - 1].trigger('click')
      await flushPromises()

      const noteCall = [...axios.post.mock.calls]
        .find(c => String(c[0]).includes('/evaluate') && c[1].feedback === 'Grenzfall')
      expect(noteCall).toBeTruthy()
      expect(noteCall[1].span_id).toBe('m2-s01')
    } finally {
      vi.useRealTimers()
    }
  })

  // --- merging spans back together -----------------------------------------

  const CONTIGUOUS = [
    { span_id: 'm2-s01', message_index: 1, message_id: 2, span_index: 0, start: 0, end: 26 },
    { span_id: 'm2-s02', message_index: 1, message_id: 2, span_index: 1, start: 26, end: 46 },
    { span_id: 'm2-s03', message_index: 1, message_id: 2, span_index: 2, start: 46, end: 64 },
  ]

  const contiguousItem = (over = {}) => sessionItem({
    metadata_json: { conversation_labeling: { spans: CONTIGUOUS, labelable_messages: [1] } },
    ...over,
  })

  const spanEls = (w) =>
    w.findAll('.l-message__body .span').filter(s => !s.classes().includes('span-gap'))

  const ctrlClick = (el) => el.trigger('click', { ctrlKey: true })

  it('CONVLAB_028: the merge control is disabled until spans are marked', async () => {
    // A control that guesses which neighbour it means reads as arbitrary. It
    // stays visible but dead until the rater has said what to merge.
    const w = await mountInterface([contiguousItem()])
    const btn = w.find('.merge-trigger')
    expect(btn.exists()).toBe(true)
    expect(btn.attributes('disabled')).toBeDefined()
  })

  it('CONVLAB_029: ctrl-clicking two neighbours enables it and merges them', async () => {
    const w = await mountInterface([contiguousItem()])
    const spans = spanEls(w)
    await ctrlClick(spans[0])
    await ctrlClick(spans[1])
    await w.vm.$nextTick()

    const btn = w.find('.merge-trigger')
    expect(btn.attributes('disabled')).toBeUndefined()
    expect(w.findAll('.span-marked').length).toBe(2)

    axios.post.mockResolvedValueOnce({
      data: { success: true, new_span_id: 'm2-s01+m', spans: [CONTIGUOUS[2]] },
    })
    await btn.trigger('click')
    await flushPromises()

    const call = axios.post.mock.calls.find(c => String(c[0]).includes('/spans/merge'))
    expect(call).toBeTruthy()
    expect(call[1]).toEqual({ span_ids: ['m2-s01', 'm2-s02'] })
  })

  it('CONVLAB_031: marking a non-consecutive pair leaves it disabled', async () => {
    // Spans 1 and 3 without 2 would swallow 2 into the merged unit. The button
    // must show that instead of letting the server reject the click.
    const w = await mountInterface([contiguousItem()])
    const spans = spanEls(w)
    await ctrlClick(spans[0])
    await ctrlClick(spans[2])
    await w.vm.$nextTick()

    expect(w.findAll('.span-marked').length).toBe(2)
    expect(w.find('.merge-trigger').attributes('disabled')).toBeDefined()
  })

  it('CONVLAB_032: a plain click navigates and clears the marking', async () => {
    // Otherwise a stale selection from minutes ago would silently arm the
    // merge button while the rater is somewhere else entirely.
    const w = await mountInterface([contiguousItem()])
    const spans = spanEls(w)
    await ctrlClick(spans[0])
    await ctrlClick(spans[1])
    await w.vm.$nextTick()
    expect(w.findAll('.span-marked').length).toBe(2)

    await spans[2].trigger('click')
    await w.vm.$nextTick()
    expect(w.findAll('.span-marked').length).toBe(0)
    expect(w.find('.merge-trigger').attributes('disabled')).toBeDefined()
  })

  it('CONVLAB_030: identical labels only MARK the pair, never merge it', async () => {
    // "Label both the same and they merge anyway" must stay a marking plus a
    // click. The segmentation is shared across raters, so acting on one
    // rater's labels would change the units under everyone else and delete
    // their votes on both halves.
    const w = await mountInterface([contiguousItem({
      evaluation: {
        spans: {
          'm2-s01': { category_id: 'D', is_unsure: false },
          'm2-s02': { category_id: 'D', is_unsure: false },
        },
      },
    })])

    const prompt = w.find('.same-label-merge')
    expect(prompt.exists()).toBe(true)
    expect(axios.post.mock.calls.filter(c => String(c[0]).includes('/spans/merge'))).toHaveLength(0)

    await prompt.trigger('click')
    await w.vm.$nextTick()
    // Marked, not merged.
    expect(w.findAll('.span-marked').length).toBe(2)
    expect(axios.post.mock.calls.filter(c => String(c[0]).includes('/spans/merge'))).toHaveLength(0)
    expect(w.find('.merge-trigger').attributes('disabled')).toBeUndefined()
  })
})

