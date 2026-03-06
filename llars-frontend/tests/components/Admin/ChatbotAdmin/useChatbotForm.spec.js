/**
 * useChatbotForm Composable Tests
 *
 * Tests for chatbot editor form data, validation, and state management.
 * Test IDs: CBFORM_001 - CBFORM_040
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useChatbotForm } from '@/components/Admin/ChatbotAdmin/ChatbotEditor/composables/useChatbotForm'

describe('useChatbotForm', () => {
  let form

  beforeEach(() => {
    form = useChatbotForm()
  })

  // ==================== Initial State Tests ====================

  describe('initial state', () => {
    it('CBFORM_001: starts with default form data', () => {
      const { formData } = form
      expect(formData.value.name).toBe('')
      expect(formData.value.display_name).toBe('')
      expect(formData.value.description).toBe('')
      expect(formData.value.icon).toBe('mdi-robot')
      expect(formData.value.color).toBe('#b0ca97')
      expect(formData.value.system_prompt).toBe('')
      expect(formData.value.model_name).toBe('')
    })

    it('CBFORM_002: starts with default model parameters', () => {
      expect(form.formData.value.temperature).toBe(0.7)
      expect(form.formData.value.max_tokens).toBe(2000)
      expect(form.formData.value.top_p).toBe(1.0)
    })

    it('CBFORM_003: starts with RAG disabled', () => {
      expect(form.formData.value.rag_enabled).toBe(false)
      expect(form.formData.value.rag_retrieval_k).toBe(5)
      expect(form.formData.value.rag_min_relevance).toBe(0.6)
      expect(form.formData.value.rag_include_sources).toBe(true)
    })

    it('CBFORM_004: starts with is_active true and is_public false', () => {
      expect(form.formData.value.is_active).toBe(true)
      expect(form.formData.value.is_public).toBe(false)
    })

    it('CBFORM_005: starts with empty collection_ids', () => {
      expect(form.formData.value.collection_ids).toEqual([])
    })

    it('CBFORM_006: starts with default prompt settings', () => {
      const ps = form.formData.value.prompt_settings
      expect(ps.rag_require_citations).toBe(true)
      expect(ps.rag_use_cross_encoder).toBe(true)
      expect(ps.agent_mode).toBe('standard')
      expect(ps.web_search_enabled).toBe(false)
    })

    it('CBFORM_007: starts with general tab active', () => {
      expect(form.activeTab.value).toBe('general')
    })

    it('CBFORM_008: starts with prompt line count of 10', () => {
      expect(form.promptLineCount.value).toBe(10)
    })
  })

  // ==================== Options Tests ====================

  describe('options', () => {
    it('CBFORM_009: provides icon options', () => {
      expect(form.iconOptions.length).toBeGreaterThan(0)
      expect(form.iconOptions[0]).toHaveProperty('title')
      expect(form.iconOptions[0]).toHaveProperty('value')
      expect(form.iconOptions.find(o => o.value === 'mdi-robot')).toBeDefined()
    })

    it('CBFORM_010: provides prompt templates', () => {
      expect(form.promptTemplates.length).toBeGreaterThan(0)
      expect(form.promptTemplates[0]).toHaveProperty('name')
      expect(form.promptTemplates[0]).toHaveProperty('icon')
      expect(form.promptTemplates[0]).toHaveProperty('prompt')
    })

    it('CBFORM_011: provides validation rules', () => {
      expect(form.rules.required('value')).toBe(true)
      expect(form.rules.required('')).toBe('Dieses Feld ist erforderlich')
      expect(form.rules.required(null)).toBe('Dieses Feld ist erforderlich')
    })
  })

  // ==================== updateLineCount Tests ====================

  describe('updateLineCount', () => {
    it('CBFORM_012: calculates line count from prompt', () => {
      form.formData.value.system_prompt = 'Line 1\nLine 2\nLine 3'
      form.updateLineCount()
      expect(form.promptLineCount.value).toBe(10) // minimum 10
    })

    it('CBFORM_013: respects minimum of 10 lines', () => {
      form.formData.value.system_prompt = 'Short'
      form.updateLineCount()
      expect(form.promptLineCount.value).toBe(10)
    })

    it('CBFORM_014: handles long prompts', () => {
      form.formData.value.system_prompt = Array(20).fill('Line').join('\n')
      form.updateLineCount()
      expect(form.promptLineCount.value).toBe(20)
    })

    it('CBFORM_015: handles empty prompt', () => {
      form.formData.value.system_prompt = ''
      form.updateLineCount()
      expect(form.promptLineCount.value).toBe(10)
    })
  })

  // ==================== applyPromptTemplate Tests ====================

  describe('applyPromptTemplate', () => {
    it('CBFORM_016: applies template prompt', () => {
      const template = form.promptTemplates[0]
      form.applyPromptTemplate(template)
      expect(form.formData.value.system_prompt).toBe(template.prompt)
    })

    it('CBFORM_017: updates line count after applying template', () => {
      const longTemplate = { prompt: Array(15).fill('Line').join('\n') }
      form.applyPromptTemplate(longTemplate)
      expect(form.promptLineCount.value).toBe(15)
    })
  })

  // ==================== toggleCollection Tests ====================

  describe('toggleCollection', () => {
    it('CBFORM_018: adds collection when not selected', () => {
      form.toggleCollection(1)
      expect(form.formData.value.collection_ids).toContain(1)
    })

    it('CBFORM_019: removes collection when already selected', () => {
      form.formData.value.collection_ids = [1, 2, 3]
      form.toggleCollection(2)
      expect(form.formData.value.collection_ids).not.toContain(2)
      expect(form.formData.value.collection_ids).toEqual([1, 3])
    })

    it('CBFORM_020: toggle is idempotent (add then remove)', () => {
      form.toggleCollection(5)
      expect(form.formData.value.collection_ids).toContain(5)
      form.toggleCollection(5)
      expect(form.formData.value.collection_ids).not.toContain(5)
    })
  })

  // ==================== isCollectionSelected Tests ====================

  describe('isCollectionSelected', () => {
    it('CBFORM_021: returns true for selected collection', () => {
      form.formData.value.collection_ids = [1, 2, 3]
      expect(form.isCollectionSelected.value(2)).toBe(true)
    })

    it('CBFORM_022: returns false for unselected collection', () => {
      form.formData.value.collection_ids = [1, 3]
      expect(form.isCollectionSelected.value(2)).toBe(false)
    })
  })

  // ==================== resetForm Tests ====================

  describe('resetForm', () => {
    it('CBFORM_023: resets all form fields to defaults', () => {
      form.formData.value.name = 'Modified Bot'
      form.formData.value.temperature = 0.9
      form.formData.value.collection_ids = [1, 2]
      form.formData.value.rag_enabled = true

      form.resetForm()

      expect(form.formData.value.name).toBe('')
      expect(form.formData.value.temperature).toBe(0.7)
      expect(form.formData.value.collection_ids).toEqual([])
      expect(form.formData.value.rag_enabled).toBe(false)
    })

    it('CBFORM_024: resets prompt line count', () => {
      form.promptLineCount.value = 25
      form.resetForm()
      expect(form.promptLineCount.value).toBe(10)
    })

    it('CBFORM_025: resets prompt settings to defaults', () => {
      form.formData.value.prompt_settings.agent_mode = 'react'
      form.resetForm()
      expect(form.formData.value.prompt_settings.agent_mode).toBe('standard')
    })
  })

  // ==================== loadChatbot Tests ====================

  describe('loadChatbot', () => {
    it('CBFORM_026: loads chatbot data into form', () => {
      form.loadChatbot({
        name: 'Test Bot',
        display_name: 'Test',
        description: 'A test bot',
        model_name: 'gpt-4',
        temperature: 0.5,
        collections: [{ id: 1 }, { id: 2 }]
      })

      expect(form.formData.value.name).toBe('Test Bot')
      expect(form.formData.value.display_name).toBe('Test')
      expect(form.formData.value.model_name).toBe('gpt-4')
      expect(form.formData.value.temperature).toBe(0.5)
      expect(form.formData.value.collection_ids).toEqual([1, 2])
    })

    it('CBFORM_027: merges prompt settings with defaults', () => {
      form.loadChatbot({
        prompt_settings: { agent_mode: 'react' }
      })

      expect(form.formData.value.prompt_settings.agent_mode).toBe('react')
      // Defaults should still be present
      expect(form.formData.value.prompt_settings.rag_require_citations).toBe(true)
    })

    it('CBFORM_028: handles null chatbot (resets)', () => {
      form.formData.value.name = 'Modified'
      form.loadChatbot(null)
      expect(form.formData.value.name).toBe('')
    })

    it('CBFORM_029: handles missing collections', () => {
      form.loadChatbot({ name: 'Bot' })
      expect(form.formData.value.collection_ids).toEqual([])
    })

    it('CBFORM_030: normalizes model_name string', () => {
      form.loadChatbot({ model_name: '  gpt-4  ' })
      expect(form.formData.value.model_name).toBe('gpt-4')
    })

    it('CBFORM_031: normalizes model_name object', () => {
      form.loadChatbot({ model_name: { value: 'gpt-4o' } })
      expect(form.formData.value.model_name).toBe('gpt-4o')
    })

    it('CBFORM_032: handles null model_name', () => {
      form.loadChatbot({ model_name: null })
      // Should fall back to original null
      expect(form.formData.value.model_name).toBeNull()
    })

    it('CBFORM_033: handles whitespace model_name (falls back to raw value)', () => {
      form.loadChatbot({ model_name: '   ' })
      // normalizeModelName returns null, but fallback is chatbot.model_name ('   ')
      // This is expected behavior - prepareForSave will clean it
      expect(form.formData.value.model_name).toBe('   ')
    })
  })

  // ==================== prepareForSave Tests ====================

  describe('prepareForSave', () => {
    it('CBFORM_034: returns form data copy', () => {
      form.formData.value.name = 'My Bot'
      form.formData.value.model_name = 'gpt-4'
      const data = form.prepareForSave(false)
      expect(data.name).toBe('My Bot')
      expect(data.model_name).toBe('gpt-4')
    })

    it('CBFORM_035: adds id when editing', () => {
      const data = form.prepareForSave(true, 42)
      expect(data.id).toBe(42)
    })

    it('CBFORM_036: does not add id when creating', () => {
      const data = form.prepareForSave(false)
      expect(data.id).toBeUndefined()
    })

    it('CBFORM_037: normalizes model_name in saved data', () => {
      form.formData.value.model_name = '  gpt-4  '
      const data = form.prepareForSave(false)
      expect(data.model_name).toBe('gpt-4')
    })

    it('CBFORM_038: removes model_name when empty', () => {
      form.formData.value.model_name = ''
      const data = form.prepareForSave(false)
      expect(data.model_name).toBeUndefined()
    })

    it('CBFORM_039: handles object model_name', () => {
      form.formData.value.model_name = { model_id: 'claude-3' }
      const data = form.prepareForSave(false)
      expect(data.model_name).toBe('claude-3')
    })

    it('CBFORM_040: returns different object each time (no reference sharing)', () => {
      form.formData.value.name = 'Bot'
      const data1 = form.prepareForSave(false)
      const data2 = form.prepareForSave(false)
      expect(data1).not.toBe(data2)
      expect(data1).toEqual(data2)
    })
  })
})
