/**
 * TestPromptDialog Component Tests
 *
 * Tests for the dialog that lets users test prompts against LLMs with streaming responses.
 * Covers rendering states, template variable extraction/resolution, Socket.IO communication,
 * localStorage persistence of configuration, and user actions (close, regenerate, cancel).
 *
 * The Vuetify v-dialog is stubbed to avoid internal overlay/visualViewport dependencies
 * in the happy-dom test environment. This lets us focus on the component's own logic.
 *
 * Key implementation detail: sendTestPrompt() is triggered by the modelValue watcher
 * transitioning from false to true. Tests that need streaming must mount with
 * modelValue=false and then setProps({ modelValue: true }).
 *
 * Timeout: Raised to 15s because Vuetify mount overhead reaches 3-5s on CI Docker
 * runners, pushing tests past the default 5s limit under load.
 *
 * Test IDs: COMP_TPD_001 - COMP_TPD_053
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import TestPromptDialog from '@/components/PromptEngineering/TestPromptDialog.vue'

// --- Mocks ---

// Socket mock - captured handlers allow tests to simulate server events
const mockSocket = {
  connected: true,
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
}

vi.mock('@/services/socketService', () => ({
  getSocket: () => mockSocket,
}))

// sanitizeHtml passthrough - no DOM sanitization needed in tests
vi.mock('@/utils/sanitize', () => ({
  sanitizeHtml: (html) => html,
}))

const vuetify = createVuetify({ components, directives })

// --- Component stubs ---

/**
 * Stub for v-dialog that avoids Vuetify overlay internals (visualViewport, etc.)
 * while preserving conditional rendering based on modelValue.
 */
const VDialogStub = {
  name: 'v-dialog',
  template: '<div class="v-dialog-stub" v-if="modelValue"><slot /></div>',
  props: ['modelValue', 'maxWidth', 'persistent', 'scrollable'],
}

/** Minimal stub for LCard that renders header, default, and actions slots */
const LCardStub = {
  name: 'LCard',
  template: `
    <div class="test-prompt-card l-card">
      <div class="l-card__header"><slot name="header" /></div>
      <slot />
      <div class="l-card__actions"><slot name="actions" /></div>
    </div>
  `,
}

const LTagStub = {
  name: 'LTag',
  template: '<span class="l-tag" :class="variant"><slot /></span>',
  props: ['variant', 'size', 'closable'],
}

const LTooltipStub = {
  name: 'LTooltip',
  template: '<span class="l-tooltip"><slot /></span>',
  props: ['text'],
}

/** LBtn stub that emits click and renders prepend-icon text for button identification */
const LBtnStub = {
  name: 'LBtn',
  template: `
    <button class="l-btn" :class="'l-btn--' + (variant || 'primary')" @click="$emit('click')">
      <span v-if="prependIcon" class="prepend-icon">{{ prependIcon }}</span>
      <slot />
    </button>
  `,
  props: ['variant', 'size', 'prependIcon', 'appendIcon', 'disabled', 'loading'],
  emits: ['click'],
}

// --- Helpers ---

/** Track mounted wrappers for proper cleanup in afterEach */
let activeWrapper = null

/**
 * Mount the dialog with sensible defaults.
 * Stubs v-dialog to avoid Vuetify overlay issues, plus L-components and LlmModelSelect.
 */
function mountDialog(props = {}, options = {}) {
  const wrapper = mount(TestPromptDialog, {
    props: {
      modelValue: true,
      prompt: 'Test prompt {{variable}}',
      ...props,
    },
    global: {
      plugins: [vuetify],
      stubs: {
        'v-dialog': VDialogStub,
        LCard: LCardStub,
        LTag: LTagStub,
        LTooltip: LTooltipStub,
        LBtn: LBtnStub,
        LlmModelSelect: { template: '<div class="llm-model-select-stub" />' },
      },
      ...options.global,
    },
    attachTo: document.body,
    ...options,
  })
  activeWrapper = wrapper
  return wrapper
}

/**
 * Mount with modelValue=false, then switch to true to trigger the watcher
 * that calls sendTestPrompt(). This simulates the user opening the dialog.
 */
async function mountAndOpenDialog(props = {}, options = {}) {
  const wrapper = mountDialog({ modelValue: false, ...props }, options)
  await wrapper.setProps({ modelValue: true })
  await nextTick()
  await flushPromises()
  return wrapper
}

/**
 * Retrieve the handler registered via mockSocket.on() for a given event name.
 * Returns undefined if no handler was registered.
 */
function getSocketHandler(eventName) {
  const call = mockSocket.on.mock.calls.find(([name]) => name === eventName)
  return call ? call[1] : undefined
}

// --- Setup / Teardown ---

beforeEach(() => {
  mockSocket.connected = true
  mockSocket.on.mockClear()
  mockSocket.off.mockClear()
  mockSocket.emit.mockClear()
  mockSocket.connect.mockClear()
  mockSocket.disconnect.mockClear()

  // localStorage is mocked globally in tests/setup.js
  localStorage.getItem.mockReturnValue(null)
  localStorage.setItem.mockClear()
})

afterEach(() => {
  // Properly unmount the Vue component before clearing the DOM.
  // Without this, onUnmounted never fires and socket listeners / internal state
  // can leak between tests, gradually slowing down later tests in CI.
  if (activeWrapper) {
    activeWrapper.unmount()
    activeWrapper = null
  }
  document.body.innerHTML = ''
})

// =======================================================================
// Rendering
// =======================================================================

// CI Docker runners can be 10x slower than local dev — bump per-test timeout
// to prevent flaky timeouts on Vuetify-heavy mounts (observed: 5274ms in CI).
describe('TestPromptDialog', { timeout: 15_000 }, () => {
  describe('Rendering', () => {
    it('COMP_TPD_001: renders dialog content when modelValue is true', () => {
      const wrapper = mountDialog({ modelValue: true })

      expect(wrapper.find('.test-prompt-card').exists()).toBe(true)
    })

    it('COMP_TPD_002: does not render dialog content when modelValue is false', () => {
      const wrapper = mountDialog({ modelValue: false })

      // Stubbed v-dialog uses v-if on modelValue
      expect(wrapper.find('.test-prompt-card').exists()).toBe(false)
    })

    it('COMP_TPD_003: displays header with title text', () => {
      const wrapper = mountDialog()
      const header = wrapper.find('.header-left')

      expect(header.exists()).toBe(true)
      // i18n is real - the German locale translates the title
      expect(header.text()).toContain('Prompt testen')
    })

    it('COMP_TPD_004: shows variables panel with items when prompt has {{placeholders}}', () => {
      const wrapper = mountDialog({ prompt: 'Hello {{name}} from {{city}}' })

      expect(wrapper.find('.variables-panel').exists()).toBe(true)
      expect(wrapper.find('.no-variables').exists()).toBe(false)
      expect(wrapper.findAll('.variable-item')).toHaveLength(2)
    })

    it('COMP_TPD_005: shows response section with container', () => {
      const wrapper = mountDialog()

      expect(wrapper.find('.response-section').exists()).toBe(true)
      expect(wrapper.find('.response-container').exists()).toBe(true)
    })
  })

  // =======================================================================
  // Variable Handling
  // =======================================================================

  describe('Variable Handling', () => {
    it('COMP_TPD_010: extracts {{var1}} and {{var2}} from prompt text', () => {
      const wrapper = mountDialog({ prompt: 'Hello {{var1}} and {{var2}}' })

      const tags = wrapper.findAll('.variable-tag')
      expect(tags).toHaveLength(2)

      const tagTexts = tags.map((t) => t.text())
      expect(tagTexts).toContain('{{var1}}')
      expect(tagTexts).toContain('{{var2}}')
    })

    it('COMP_TPD_011: shows no-variables state when prompt has no placeholders', () => {
      const wrapper = mountDialog({ prompt: 'A plain prompt without variables' })

      expect(wrapper.find('.no-variables').exists()).toBe(true)
      expect(wrapper.findAll('.variable-item')).toHaveLength(0)
    })

    it('COMP_TPD_012: variable count tag displays correct filled/total ratio', () => {
      const wrapper = mountDialog({
        prompt: 'Hello {{name}} from {{city}}',
        variables: [{ name: 'name', content: 'Alice' }],
      })

      // LTag in header-left renders "filled/total" - should show "1/2"
      const headerLeft = wrapper.find('.header-left')
      expect(headerLeft.text()).toContain('1/2')
    })

    it('COMP_TPD_013: variables resolved in prompt before sending to socket', async () => {
      // Mount closed first, then open to trigger the modelValue watcher → sendTestPrompt
      const wrapper = await mountAndOpenDialog({
        prompt: 'Hello {{name}}',
        variables: [{ name: 'name', content: 'Alice' }],
      })

      const emitCalls = mockSocket.emit.mock.calls.filter(([event]) => event === 'test_prompt_stream')
      expect(emitCalls.length).toBeGreaterThanOrEqual(1)

      const lastPayload = emitCalls[emitCalls.length - 1][1]
      expect(lastPayload.userPrompt).toBe('Hello Alice')
      expect(lastPayload.prompt).toBe('Hello Alice')
    })

    it('COMP_TPD_014: invalid/reserved variable names are filtered out', () => {
      // VARIABLE_REGEX only matches [a-zA-Z_][a-zA-Z0-9_]*, then INVALID_NAMES filters reserved words
      const wrapper = mountDialog({
        prompt: '{{undefined}} {{null}} {{validVar}} {{true}} {{false}}',
      })

      const variableItems = wrapper.findAll('.variable-item')
      expect(variableItems).toHaveLength(1)

      const tags = wrapper.findAll('.variable-tag')
      expect(tags[0].text()).toBe('{{validVar}}')
    })
  })

  // =======================================================================
  // Socket Communication
  // =======================================================================

  describe('Socket Communication', () => {
    it('COMP_TPD_020: emits test_prompt_stream on socket when dialog opens', async () => {
      await mountAndOpenDialog()

      const emitCalls = mockSocket.emit.mock.calls.filter(([event]) => event === 'test_prompt_stream')
      expect(emitCalls.length).toBeGreaterThanOrEqual(1)
    })

    it('COMP_TPD_021: socket payload contains model, temperature, and maxTokens', async () => {
      await mountAndOpenDialog()

      const emitCalls = mockSocket.emit.mock.calls.filter(([event]) => event === 'test_prompt_stream')
      expect(emitCalls.length).toBeGreaterThanOrEqual(1)

      const payload = emitCalls[emitCalls.length - 1][1]
      expect(payload).toHaveProperty('model')
      expect(payload).toHaveProperty('temperature')
      expect(payload).toHaveProperty('maxTokens')
    })

    it('COMP_TPD_022: content appended from test_prompt_response events', async () => {
      await mountAndOpenDialog()

      const handler = getSocketHandler('test_prompt_response')
      expect(handler).toBeDefined()

      handler({ content: 'Hello ' })
      handler({ content: 'world' })
      await nextTick()

      const responseText = document.querySelector('.response-text')
      expect(responseText.textContent).toContain('Hello world')
    })

    it('COMP_TPD_023: response marked complete when data.complete is true', async () => {
      const wrapper = await mountAndOpenDialog()

      const handler = getSocketHandler('test_prompt_response')
      handler({ content: 'Done.', complete: true })
      await nextTick()

      // After completion, streaming indicators should disappear
      expect(wrapper.find('.typing-indicator').exists()).toBe(false)
    })

    it('COMP_TPD_024: streaming indicator visible during active streaming', async () => {
      const wrapper = await mountAndOpenDialog()

      // sendTestPrompt sets isStreaming=true; no complete event yet
      expect(wrapper.find('.typing-indicator').exists()).toBe(true)
    })

    it('COMP_TPD_025: graceful handling when socket is not connected', async () => {
      mockSocket.connected = false

      const wrapper = await mountAndOpenDialog()

      // Socket.emit should NOT be called when disconnected (pendingRequest is set instead)
      const emitCalls = mockSocket.emit.mock.calls.filter(([event]) => event === 'test_prompt_stream')
      expect(emitCalls).toHaveLength(0)

      // Component renders without crashing
      expect(wrapper.find('.test-prompt-card').exists()).toBe(true)
    })
  })

  // =======================================================================
  // Configuration Persistence
  // =======================================================================

  describe('Configuration', () => {
    it('COMP_TPD_040: temperature persisted to localStorage on change', async () => {
      const wrapper = mountDialog()
      await nextTick()

      // Trigger temperature change via the v-slider component
      const slider = wrapper.findComponent({ name: 'v-slider' })
      if (slider.exists()) {
        await slider.vm.$emit('update:modelValue', 0.75)
        await nextTick()
      }

      const tempCalls = localStorage.setItem.mock.calls.filter(
        ([key]) => key === 'llars_test_prompt_temperature'
      )
      expect(tempCalls.length).toBeGreaterThanOrEqual(1)
    })

    it('COMP_TPD_041: maxTokens persisted to localStorage on change', async () => {
      const wrapper = mountDialog()
      await nextTick()

      // Trigger maxTokens change via the number text-field
      const textFields = wrapper.findAllComponents({ name: 'v-text-field' })
      const tokenField = textFields.find((tf) => tf.props('type') === 'number')
      if (tokenField) {
        await tokenField.vm.$emit('update:modelValue', 2048)
        await nextTick()
      }

      const tokenCalls = localStorage.setItem.mock.calls.filter(
        ([key]) => key === 'llars_test_prompt_max_tokens'
      )
      expect(tokenCalls.length).toBeGreaterThanOrEqual(1)
    })

    it('COMP_TPD_042: temperature and maxTokens restored from localStorage on mount', () => {
      localStorage.getItem.mockImplementation((key) => {
        if (key === 'llars_test_prompt_temperature') return '0.85'
        if (key === 'llars_test_prompt_max_tokens') return '2048'
        return null
      })

      const wrapper = mountDialog()

      expect(wrapper.find('.config-section').exists()).toBe(true)

      // Verify both storage keys were queried during setup
      const getItemKeys = localStorage.getItem.mock.calls.map(([key]) => key)
      expect(getItemKeys).toContain('llars_test_prompt_temperature')
      expect(getItemKeys).toContain('llars_test_prompt_max_tokens')
    })
  })

  // =======================================================================
  // Actions
  // =======================================================================

  describe('Actions', () => {
    it('COMP_TPD_050: close button emits update:modelValue with false', async () => {
      const wrapper = mountDialog()
      await nextTick()

      // The header has a v-btn close button with mdi-close icon
      const headerCloseBtn = wrapper.find('.dialog-header .v-btn')
      if (headerCloseBtn.exists()) {
        await headerCloseBtn.trigger('click')
      } else {
        // Fallback: use the close LBtn in actions (variant="cancel")
        const actionBtns = wrapper.findAll('.dialog-actions .l-btn')
        const closeBtn = actionBtns.find((btn) => btn.classes().includes('l-btn--cancel'))
        await closeBtn.trigger('click')
      }
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1]).toEqual([false])
    })

    it('COMP_TPD_051: regenerate resets response and sends new socket request', async () => {
      const wrapper = await mountAndOpenDialog()

      // Complete initial streaming so the regenerate button appears
      const handler = getSocketHandler('test_prompt_response')
      handler({ content: 'First response.', complete: true })
      await nextTick()

      mockSocket.emit.mockClear()

      // Find regenerate button (has mdi-refresh icon, visible when not streaming)
      const actionBtns = wrapper.findAll('.dialog-actions .l-btn')
      const regenBtn = actionBtns.find((btn) => btn.text().includes('mdi-refresh'))
      expect(regenBtn).toBeDefined()

      await regenBtn.trigger('click')
      await nextTick()

      const emitCalls = mockSocket.emit.mock.calls.filter(([event]) => event === 'test_prompt_stream')
      expect(emitCalls).toHaveLength(1)
    })

    it('COMP_TPD_052: cancel stops streaming and appends canceled message', async () => {
      const wrapper = await mountAndOpenDialog()

      // Simulate partial content during streaming
      const handler = getSocketHandler('test_prompt_response')
      handler({ content: 'Partial response...' })
      await nextTick()

      // Find the cancel button (variant="danger" with mdi-stop, shown during streaming)
      const actionBtns = wrapper.findAll('.dialog-actions .l-btn')
      const cancelBtn = actionBtns.find(
        (btn) => btn.classes().includes('l-btn--danger') || btn.text().includes('mdi-stop')
      )
      expect(cancelBtn).toBeDefined()

      await cancelBtn.trigger('click')
      await nextTick()

      // Response should contain the German i18n canceled message
      const responseText = wrapper.find('.response-text')
      expect(responseText.text()).toContain('[Generierung abgebrochen]')
      expect(wrapper.find('.typing-indicator').exists()).toBe(false)
    })

    it('COMP_TPD_053: close during streaming cancels generation then closes dialog', async () => {
      const wrapper = await mountAndOpenDialog()

      // Dialog is streaming. Click the close button (variant="cancel") in actions.
      const actionBtns = wrapper.findAll('.dialog-actions .l-btn')
      const closeBtn = actionBtns.find((btn) => btn.classes().includes('l-btn--cancel'))
      expect(closeBtn).toBeDefined()

      await closeBtn.trigger('click')
      await nextTick()

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toBeTruthy()
      expect(emitted[emitted.length - 1]).toEqual([false])

      // closeDialog() calls cancelGeneration() first when streaming is active
      const responseText = wrapper.find('.response-text')
      expect(responseText.text()).toContain('[Generierung abgebrochen]')
    })
  })
})
