/**
 * LabelingConfigEditor Co-Pilot + Parts Section Tests
 *
 * Covers the co-pilot configuration block (toggle, default prompt,
 * placeholder chips, emitted config shape) and the parts/phases section
 * (boundary-based part list, opt-in payload contract). The category-editor
 * basics are exercised implicitly through the emit-shape assertions.
 *
 * Test IDs: COPILOT_UI_001 - COPILOT_UI_007, PARTS_UI_001 - PARTS_UI_006
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LabelingConfigEditor from '@/views/ScenarioManager/components/config/LabelingConfigEditor.vue'

const vuetify = createVuetify({ components, directives })

// Stubs: draggable pulls in sortablejs, LlmModelSelect fetches models via
// axios on mount — neither is under test here.
const stubs = {
  draggable: { template: '<div class="draggable-stub" />' },
  LlmModelSelect: {
    name: 'LlmModelSelect',
    props: ['modelValue', 'label'],
    template: '<div class="llm-model-select-stub" />',
  },
  LSwitch: {
    name: 'LSwitch',
    props: ['modelValue', 'label'],
    emits: ['update:modelValue'],
    template:
      '<input type="checkbox" class="lswitch-stub" :checked="modelValue" ' +
      '@change="$emit(\'update:modelValue\', $event.target.checked)" />',
  },
  LTag: { name: 'LTag', template: '<span class="ltag-stub"><slot /></span>' },
  LBtn: { name: 'LBtn', template: '<button class="lbtn-stub"><slot /></button>' },
}

const baseConfig = {
  type: 'multiclass',
  categories: [
    { id: 'a', name: { de: 'A', en: 'A' }, color: '#98d4bb', icon: 'mdi-tag' },
    { id: 'b', name: { de: 'B', en: 'B' }, color: '#e8a087', icon: 'mdi-tag' },
  ],
  allowUnsure: true,
}

function mountEditor(modelValue = baseConfig, extraProps = {}) {
  return mount(LabelingConfigEditor, {
    props: { modelValue, ...extraProps },
    global: { plugins: [vuetify], stubs },
  })
}

function lastEmitted(wrapper) {
  const events = wrapper.emitted('update:modelValue')
  return events[events.length - 1][0]
}

describe('LabelingConfigEditor — Co-Pilot section', () => {
  it('COPILOT_UI_001: renders the co-pilot section with a toggle', () => {
    const wrapper = mountEditor()
    const section = wrapper.find('.copilot-section')
    expect(section.exists()).toBe(true)
    expect(section.find('.lswitch-stub').exists()).toBe(true)
    // Detail fields stay hidden while disabled
    expect(section.find('.prompt-textarea').exists()).toBe(false)
  })

  it('COPILOT_UI_002: enabling the toggle emits copilot.enabled=true with a default prompt', async () => {
    const wrapper = mountEditor()
    await wrapper.find('.copilot-section .lswitch-stub').setValue(true)

    const emitted = lastEmitted(wrapper)
    expect(emitted.copilot.enabled).toBe(true)
    // Default prompt is prefilled and carries all four placeholders
    for (const ph of ['{item}', '{context}', '{labels}', '{codebook}']) {
      expect(emitted.copilot.prompt).toContain(ph)
    }
  })

  it('COPILOT_UI_003: shows detail fields when copilot is enabled via props', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      copilot: { enabled: true, model_id: 'm', prompt: 'P {item}', top_k: 2, hidden_control_ratio: 0.15 },
    })
    // initFromProps runs in onMounted — flush the resulting re-render first
    await wrapper.vm.$nextTick()
    const section = wrapper.find('.copilot-section')
    expect(section.find('.llm-model-select-stub').exists()).toBe(true)
    expect(section.find('.prompt-textarea').exists()).toBe(true)
    expect(section.text()).toContain('15%')
  })

  it('COPILOT_UI_004: initializes fields from an existing copilot config', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      copilot: { enabled: true, prompt: 'Mein VRM-Prompt {item}', codebook: 'Regeln', top_k: 2 },
    })
    await wrapper.vm.$nextTick()
    const textarea = wrapper.find('.prompt-textarea textarea')
    expect(textarea.element.value).toContain('Mein VRM-Prompt {item}')
  })

  it('COPILOT_UI_005: clicking a placeholder chip appends it to the prompt and emits', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      copilot: { enabled: true, prompt: 'Basis-Prompt' },
    })
    await wrapper.vm.$nextTick()
    const chips = wrapper.findAll('.placeholder-chip')
    expect(chips.length).toBe(4)
    await chips[0].trigger('click')

    const emitted = lastEmitted(wrapper)
    expect(emitted.copilot.prompt).toBe('Basis-Prompt\n{item}')
  })

  it('COPILOT_UI_006: every emitted update carries the copilot block (nothing gets lost)', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      copilot: { enabled: true, prompt: 'P', model_id: 'x', top_k: 2, hidden_control_ratio: 0.2 },
    })
    // Trigger an unrelated update (unsure toggle outside the copilot section)
    const switches = wrapper.findAll('.lswitch-stub')
    await switches[0].setValue(false)

    const emitted = lastEmitted(wrapper)
    expect(emitted.copilot).toMatchObject({
      enabled: true, prompt: 'P', model_id: 'x', top_k: 2, hidden_control_ratio: 0.2,
    })
    expect(emitted.categories).toHaveLength(2)
  })

  it('COPILOT_UI_007: disabled copilot still emits enabled=false (explicit off, not undefined)', async () => {
    const wrapper = mountEditor()
    const switches = wrapper.findAll('.copilot-section .lswitch-stub')
    await switches[0].setValue(true)
    await switches[0].setValue(false)

    const emitted = lastEmitted(wrapper)
    expect(emitted.copilot.enabled).toBe(false)
  })
})

describe('LabelingConfigEditor — Parts / Phases section', () => {
  it('PARTS_UI_001: renders the parts section with a toggle, rows hidden while off', () => {
    const wrapper = mountEditor()
    const section = wrapper.find('.parts-section')
    expect(section.exists()).toBe(true)
    expect(section.find('.lswitch-stub').exists()).toBe(true)
    expect(section.find('.part-row').exists()).toBe(false)
  })

  it('PARTS_UI_002: enabling seeds two parts (sized + rest) and emits the parts config', async () => {
    const wrapper = mountEditor(baseConfig, { itemCount: 10 })
    await wrapper.find('.parts-section .lswitch-stub').setValue(true)

    const emitted = lastEmitted(wrapper)
    expect(emitted.parts.enabled).toBe(true)
    expect(emitted.parts.list).toHaveLength(2)
    // first part gets a size (half the uploaded items), last part is "rest"
    expect(emitted.parts.list[0].size).toBe(5)
    expect(emitted.parts.list[1].size).toBeUndefined()
    expect(emitted.parts.list[0].id).toBe('p1')
    expect(emitted.parts.list[0].order).toBe('sequential')
  })

  it('PARTS_UI_003: toggle off emits NO parts key at all (opt-in contract)', async () => {
    const wrapper = mountEditor()
    const toggle = wrapper.find('.parts-section .lswitch-stub')
    await toggle.setValue(true)
    expect(lastEmitted(wrapper).parts).toBeDefined()

    await toggle.setValue(false)
    const emitted = lastEmitted(wrapper)
    expect('parts' in emitted).toBe(false)
  })

  it('PARTS_UI_004: per-part copilot switch only appears when the copilot master is on', async () => {
    // master off: each part row shows exactly one switch (locked)
    const off = mountEditor({
      ...baseConfig,
      parts: { enabled: true, list: [{ id: 'p1', size: 3 }, { id: 'p2' }] },
    })
    await off.vm.$nextTick()
    expect(off.find('.part-row').findAll('.lswitch-stub')).toHaveLength(1)

    // master on: copilot switch + locked switch per part
    const on = mountEditor({
      ...baseConfig,
      copilot: { enabled: true, prompt: 'P' },
      parts: { enabled: true, list: [{ id: 'p1', size: 3 }, { id: 'p2' }] },
    })
    await on.vm.$nextTick()
    expect(on.find('.part-row').findAll('.lswitch-stub')).toHaveLength(2)
  })

  it('PARTS_UI_005: initializes rows from an existing parts config', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      parts: {
        enabled: true,
        list: [
          { id: 'p1', name: 'Kalibrierung 1', size: 100 },
          { id: 'p2', name: 'Kalibrierung 2', size: 50, locked: true },
          { id: 'p3', name: 'Hauptphase', locked: true },
        ],
      },
    })
    await wrapper.vm.$nextTick()
    const rows = wrapper.findAll('.part-row')
    expect(rows).toHaveLength(3)
    expect(rows[0].find('input').element.value).toBe('Kalibrierung 1')
  })

  it('PARTS_UI_006: emitted parts keep locked flags and normalize copilot under the master switch', async () => {
    const wrapper = mountEditor({
      ...baseConfig,
      // master OFF, but a part claims copilot=true → must be normalized to false
      parts: {
        enabled: true,
        list: [
          { id: 'p1', size: 3, copilot: true },
          { id: 'p2', locked: true },
        ],
      },
    })
    await wrapper.vm.$nextTick()
    // trigger an update via a switch that actually flips state
    // (allowUnsure starts true) to capture the emitted payload
    const unsureSwitch = wrapper.findAll('.config-options .lswitch-stub').at(-1)
    await unsureSwitch.setValue(false)

    const emitted = lastEmitted(wrapper)
    expect(emitted.parts.list[0].copilot).toBe(false)
    expect(emitted.parts.list[1].locked).toBe(true)
  })
})
