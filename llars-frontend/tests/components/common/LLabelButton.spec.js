/**
 * LLabelButton Component Tests
 *
 * Tests for the label choice button used by every labeling surface.
 * Focus: the codebook layer (rule + anchors) added for the VRM study, and the
 * colour rule that makes "chosen" unmistakable across ~92 decisions in a row.
 * Test IDs: COMP_LBB_001 - COMP_LBB_012
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LLabelButton from '@/components/common/LLabelButton.vue'

const vuetify = createVuetify({ components, directives })

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ locale: { value: 'de' } })
}))

const K = {
  id: 'K',
  label: { de: 'K — Acknowledgement', en: 'K — Acknowledgment' },
  description: { de: 'Signal ohne eigenen Inhalt.', en: 'A signal carrying no content.' },
  color: '#E8C4A0'
}

function mountBtn(category = K, props = {}) {
  return mount(LLabelButton, {
    props: { category, ...props },
    global: { plugins: [vuetify] }
  })
}

/**
 * Vuetify teleports tooltip content and only renders it once opened, so the
 * slot is invisible to wrapper.html(). Stubbing VTooltip renders the slot
 * eagerly — which is what these tests are about: the CONTENT we put in it.
 * Whether Vuetify opens on hover is Vuetify's business, not ours.
 */
function mountWithTip(category) {
  return mount(LLabelButton, {
    props: { category },
    global: {
      plugins: [vuetify],
      stubs: { VTooltip: { template: '<div class="tip-stub"><slot /></div>' } }
    }
  })
}

describe('LLabelButton', () => {
  describe('Rendering', () => {
    it('COMP_LBB_001: renders the localised name and description', () => {
      const wrapper = mountBtn()
      expect(wrapper.find('.l-label-btn__name').text()).toBe('K — Acknowledgement')
      expect(wrapper.find('.l-label-btn__desc').text()).toBe('Signal ohne eigenen Inhalt.')
    })

    it('COMP_LBB_002: falls back to the id when no label is given', () => {
      const wrapper = mountBtn({ id: 'Q' })
      expect(wrapper.find('.l-label-btn__name').text()).toBe('Q')
    })

    it('COMP_LBB_003: emits select with the category id', async () => {
      const wrapper = mountBtn()
      await wrapper.find('button').trigger('click')
      expect(wrapper.emitted('select')[0]).toEqual(['K'])
    })

    it('COMP_LBB_004: fills only when selected — a suggestion must never look chosen', () => {
      const unselected = mountBtn(K)
      expect(unselected.find('button').attributes('style')).toContain('transparent')

      const selected = mountBtn(K, { modelValue: 'K' })
      expect(selected.find('button').classes()).toContain('selected')
      expect(selected.find('button').attributes('style')).toContain('#E8C4A0')
    })
  })

  // The codebook layer: without rule/anchors the button must behave exactly as
  // before, so existing label sets are unaffected.
  describe('Codebook (rule + anchors)', () => {
    it('COMP_LBB_005: shows no codebook marker when neither rule nor anchors exist', () => {
      const wrapper = mountWithTip(K)
      expect(wrapper.find('.l-label-btn__more').exists()).toBe(false)
      expect(wrapper.find('.tip-stub').exists()).toBe(false)
    })

    it('COMP_LBB_006: shows the marker as soon as a rule is given', () => {
      const wrapper = mountBtn({ ...K, rule: { de: 'Trägt es Inhalt? Dann kein K.', en: 'x' } })
      expect(wrapper.find('.l-label-btn__more').exists()).toBe(true)
    })

    it('COMP_LBB_007: shows the marker for anchors alone', () => {
      const wrapper = mountBtn({ ...K, anchors: { de: ['Hallo!'], en: [] } })
      expect(wrapper.find('.l-label-btn__more').exists()).toBe(true)
    })

    it('COMP_LBB_008: renders rule and anchors in the tooltip', () => {
      const wrapper = mountWithTip({
        ...K,
        rule: { de: 'Trägt die Äußerung eigenen Inhalt? Dann kein K.', en: 'x' },
        anchors: { de: ['„Hallo und herzlich willkommen!“ → K'], en: ['x'] }
      })
      const html = wrapper.find('.tip-stub').html()
      expect(html).toContain('Trägt die Äußerung eigenen Inhalt? Dann kein K.')
      expect(html).toContain('„Hallo und herzlich willkommen!“ → K')
    })

    it('COMP_LBB_009: falls back to the other language when the active one is empty', () => {
      // Anchors are real corpus sentences and often have no counterpart in the
      // other language — showing nothing would be worse than showing German.
      const wrapper = mountWithTip({ ...K, anchors: { de: [], en: ['Hello.'] } })
      expect(wrapper.find('.tip-stub').text()).toContain('Hello.')
    })

    it('COMP_LBB_010: accepts a plain array of anchors (unlocalised config)', () => {
      const wrapper = mountWithTip({ ...K, anchors: ['Guten Abend'] })
      expect(wrapper.find('.tip-stub').text()).toContain('Guten Abend')
    })

    it('COMP_LBB_011: tolerates an empty anchors object without showing a marker', () => {
      const wrapper = mountBtn({ ...K, anchors: { de: [], en: [] } })
      expect(wrapper.find('.l-label-btn__more').exists()).toBe(false)
    })

    it('COMP_LBB_012: keeps the hotkey and the codebook marker apart', () => {
      const wrapper = mountBtn({ ...K, rule: { de: 'r', en: 'r' } }, { hotkey: 6 })
      expect(wrapper.find('.l-label-btn__hotkey').text()).toBe('6')
      expect(wrapper.find('.l-label-btn__more').text()).toBe('?')
    })
  })
})
