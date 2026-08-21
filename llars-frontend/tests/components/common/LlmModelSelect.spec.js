/**
 * LlmModelSelect Component Tests
 *
 * Tests for the LLARS LLM model selection autocomplete component.
 * Features: model loading, selection, v-model, vision/reasoning filters.
 * Test IDs: COMP_LMS_001 - COMP_LMS_025
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

const vuetify = createVuetify({ components, directives })

const mockModels = [
  {
    model_id: 'Global/OpenAI/gpt-5-nano',
    display_name: 'GPT-5 Nano',
    provider: 'openai',
    supports_vision: false,
    supports_reasoning: false,
    is_default: true,
    context_window: 128000,
    max_output_tokens: 4096
  },
  {
    model_id: 'Global/Mistral/Mistral-Small',
    display_name: 'Mistral Small',
    provider: 'litellm',
    supports_vision: true,
    supports_reasoning: false,
    is_default: false,
    context_window: 32000,
    max_output_tokens: 2048
  }
]

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

vi.mock('@/composables/usePermissions', () => ({
  usePermissions: vi.fn(() => ({
    hasPermission: vi.fn(() => false),
    fetchPermissions: vi.fn()
  }))
}))

vi.mock('@/utils/formatters', () => ({
  parseUserProviderModelId: vi.fn((id) => {
    if (!id || !id.startsWith('user-provider:')) return null
    return {
      displayName: 'User Model',
      providerLabel: 'User Provider'
    }
  })
}))

import axios from 'axios'

function mountComponent(props = {}, options = {}) {
  return mount(LlmModelSelect, {
    props,
    global: {
      plugins: [vuetify],
      ...options.global
    },
    ...options
  })
}

describe('LlmModelSelect', () => {
  beforeEach(() => {
    vi.mocked(axios.get).mockImplementation((url) => {
      if (url === '/api/llm/models/available') {
        return Promise.resolve({ data: { models: mockModels } })
      }
      if (url === '/api/user/providers/available') {
        return Promise.resolve({ data: { providers: [] } })
      }
      return Promise.resolve({ data: {} })
    })
    vi.mocked(axios.post).mockResolvedValue({ data: {} })
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_LMS_001: renders autocomplete component', async () => {
      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'VAutocomplete' }).exists()).toBe(true)
    })

    it('COMP_LMS_002: shows default label', async () => {
      const wrapper = mountComponent()
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('label')).toBe('LLM Modell')
    })

    it('COMP_LMS_003: shows custom label', async () => {
      const wrapper = mountComponent({ label: 'Choose Model' })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('label')).toBe('Choose Model')
    })

    it('COMP_LMS_004: renders with empty models list', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: { models: [] } })

      const wrapper = mountComponent()
      await flushPromises()

      // The no-data slot only renders when autocomplete menu is open
      // Verify the component still renders correctly with no models loaded
      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.exists()).toBe(true)
      expect(autocomplete.props('items')).toEqual([])
    })
  })

  // ==================== Model Loading Tests ====================

  describe('Model Loading', () => {
    it('COMP_LMS_005: fetches models on mount', async () => {
      mountComponent()
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        '/api/llm/models/available',
        expect.objectContaining({
          params: expect.objectContaining({
            model_type: 'llm',
            active_only: true
          })
        })
      )
    })

    it('COMP_LMS_006: fetches user providers when includeUserProviders is true', async () => {
      mountComponent({ includeUserProviders: true })
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith('/api/user/providers/available')
    })

    it('COMP_LMS_007: does not fetch user providers when includeUserProviders is false', async () => {
      mountComponent({ includeUserProviders: false })
      await flushPromises()

      expect(axios.get).not.toHaveBeenCalledWith('/api/user/providers/available')
    })

    it('COMP_LMS_008: emits models-loaded after loading', async () => {
      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.emitted('models-loaded')).toBeTruthy()
      expect(wrapper.emitted('models-loaded')[0][0]).toEqual(mockModels)
    })

    it('COMP_LMS_009: handles API error gracefully', async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const wrapper = mountComponent()
      await flushPromises()

      expect(wrapper.emitted('models-loaded')).toBeTruthy()
      expect(wrapper.emitted('models-loaded')[0][0]).toEqual([])
      consoleSpy.mockRestore()
    })
  })

  // ==================== Selection Tests ====================

  describe('Selection', () => {
    it('COMP_LMS_010: auto-selects default model when no value', async () => {
      const wrapper = mountComponent({ modelValue: null, autoSelectDefault: true })
      await flushPromises()

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['Global/OpenAI/gpt-5-nano'])
    })

    it('COMP_LMS_011: does not auto-select when autoSelectDefault is false', async () => {
      const wrapper = mountComponent({ modelValue: null, autoSelectDefault: false })
      await flushPromises()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })

    it('COMP_LMS_012: does not auto-select when value already set', async () => {
      const wrapper = mountComponent({
        modelValue: 'Global/Mistral/Mistral-Small',
        autoSelectDefault: true
      })
      await flushPromises()

      // Should not emit if model value is already set
      const emissions = wrapper.emitted('update:modelValue') || []
      const autoSelections = emissions.filter(e => e[0] === 'Global/OpenAI/gpt-5-nano')
      expect(autoSelections.length).toBe(0)
    })

    it('COMP_LMS_013: emits update:modelValue on selection change', async () => {
      const wrapper = mountComponent({ modelValue: 'Global/OpenAI/gpt-5-nano' })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      await autocomplete.vm.$emit('update:modelValue', 'Global/Mistral/Mistral-Small')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    })
  })

  // ==================== Multiple Selection Tests ====================

  describe('Multiple Selection', () => {
    it('COMP_LMS_014: enables multiple selection when multiple is true', async () => {
      const wrapper = mountComponent({ multiple: true, modelValue: [] })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('multiple')).toBe(true)
    })

    it('COMP_LMS_015: shows chips in multiple mode', async () => {
      const wrapper = mountComponent({ multiple: true, modelValue: [] })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('chips')).toBe(true)
    })

    it('COMP_LMS_016: does not auto-select in multiple mode', async () => {
      const wrapper = mountComponent({
        multiple: true,
        modelValue: [],
        autoSelectDefault: true
      })
      await flushPromises()

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })
  })

  // ==================== Props Tests ====================

  describe('Props', () => {
    it('COMP_LMS_017: passes disabled prop to autocomplete', async () => {
      const wrapper = mountComponent({ disabled: true })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('disabled')).toBe(true)
    })

    it('COMP_LMS_018: passes clearable prop to autocomplete', async () => {
      const wrapper = mountComponent({ clearable: true })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('clearable')).toBe(true)
    })

    it('COMP_LMS_019: passes hideDetails prop to autocomplete', async () => {
      const wrapper = mountComponent({ hideDetails: true })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('hideDetails')).toBe(true)
    })

    it('COMP_LMS_020: passes variant prop to autocomplete', async () => {
      const wrapper = mountComponent({ variant: 'filled' })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      expect(autocomplete.props('variant')).toBe('filled')
    })

    it('COMP_LMS_021: generates required validation rule', async () => {
      const wrapper = mountComponent({ required: true })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      const rules = autocomplete.props('rules')
      expect(rules.length).toBe(1)
      // Rule should fail for empty value
      expect(rules[0](null)).not.toBe(true)
      // Rule should pass for valid value
      expect(rules[0]('some-model')).toBe(true)
    })
  })

  // ==================== Filter Tests ====================

  describe('Filters', () => {
    it('COMP_LMS_022: passes visionOnly filter to API', async () => {
      mountComponent({ visionOnly: true })
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        '/api/llm/models/available',
        expect.objectContaining({
          params: expect.objectContaining({
            vision_only: true
          })
        })
      )
    })

    it('COMP_LMS_023: passes reasoningOnly filter to API', async () => {
      mountComponent({ reasoningOnly: true })
      await flushPromises()

      expect(axios.get).toHaveBeenCalledWith(
        '/api/llm/models/available',
        expect.objectContaining({
          params: expect.objectContaining({
            reasoning_only: true
          })
        })
      )
    })
  })

  // ==================== Current Value Preservation Tests ====================

  describe('Current Value Preservation', () => {
    it('COMP_LMS_024: preserves current model even if not in API response', async () => {
      const wrapper = mountComponent({
        modelValue: 'custom-model-id'
      })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      const items = autocomplete.props('items')
      // Should contain the custom model that was not in the API response
      const customItem = items.find(i => i.value === 'custom-model-id')
      expect(customItem).toBeTruthy()
    })

    it('COMP_LMS_025: does not duplicate model if already in API response', async () => {
      const wrapper = mountComponent({
        modelValue: 'Global/OpenAI/gpt-5-nano'
      })
      await flushPromises()

      const autocomplete = wrapper.findComponent({ name: 'VAutocomplete' })
      const items = autocomplete.props('items')
      const matching = items.filter(i => i.value === 'Global/OpenAI/gpt-5-nano')
      expect(matching.length).toBe(1)
    })
  })
})
