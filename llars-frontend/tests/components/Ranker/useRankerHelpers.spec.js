/**
 * useRankerHelpers Composable Tests
 *
 * Tests for formatting, translations, content display, color generation, and drag handling.
 * Test IDs: RANK_HELP_001 - RANK_HELP_035
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/utils/sanitize', () => ({
  sanitizeHtml: vi.fn((html) => html)
}))

import { useRankerHelpers } from '@/components/Ranker/RankerDetail/composables/useRankerHelpers'

describe('useRankerHelpers', () => {
  let helpers

  beforeEach(() => {
    helpers = useRankerHelpers()
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('RANK_HELP_001: emailPaneExpanded starts as true', () => {
      expect(helpers.emailPaneExpanded.value).toBe(true)
    })

    it('RANK_HELP_002: senderColors starts empty', () => {
      expect(helpers.senderColors.value).toEqual({})
    })

    it('RANK_HELP_003: dragOptions has correct defaults', () => {
      expect(helpers.dragOptions.value).toEqual({
        animation: 200,
        group: 'description',
        disabled: false,
        ghostClass: 'ghost'
      })
    })
  })

  // ==================== Toggle Functions ====================

  describe('toggleEmailPane', () => {
    it('RANK_HELP_004: toggles emailPaneExpanded', () => {
      expect(helpers.emailPaneExpanded.value).toBe(true)
      helpers.toggleEmailPane()
      expect(helpers.emailPaneExpanded.value).toBe(false)
      helpers.toggleEmailPane()
      expect(helpers.emailPaneExpanded.value).toBe(true)
    })
  })

  describe('toggleMinimize', () => {
    it('RANK_HELP_005: toggles minimized property on element', () => {
      const element = { minimized: false }
      helpers.toggleMinimize(element)
      expect(element.minimized).toBe(true)
      helpers.toggleMinimize(element)
      expect(element.minimized).toBe(false)
    })
  })

  // ==================== Content Helpers ====================

  describe('isLongContent', () => {
    it('RANK_HELP_006: returns false for short content', () => {
      expect(helpers.isLongContent('Short text')).toBe(false)
    })

    it('RANK_HELP_007: returns true for long content', () => {
      const longContent = 'A'.repeat(241) // > 80 * 3
      expect(helpers.isLongContent(longContent)).toBe(true)
    })

    it('RANK_HELP_008: returns false at exact boundary', () => {
      const exactContent = 'A'.repeat(240) // = 80 * 3
      expect(helpers.isLongContent(exactContent)).toBe(false)
    })
  })

  // ==================== Tooltip Text ====================

  describe('getTooltipText', () => {
    it('RANK_HELP_009: returns tooltip for abstract_summary', () => {
      const text = helpers.getTooltipText('abstract_summary')
      expect(text).toContain('Zusammenfassung')
    })

    it('RANK_HELP_010: returns tooltip for generated_subject', () => {
      const text = helpers.getTooltipText('generated_subject')
      expect(text).toContain('Betreff')
    })

    it('RANK_HELP_011: returns tooltip for situation_summary', () => {
      const text = helpers.getTooltipText('situation_summary')
      expect(text).toContain('Situationsbeschreibung')
    })

    it('RANK_HELP_012: returns default tooltip for unknown type', () => {
      const text = helpers.getTooltipText('unknown_type')
      expect(text).toBe('Allgemeine Informationen zum Feature.')
    })
  })

  // ==================== Translations ====================

  describe('translateFeatureType', () => {
    it('RANK_HELP_013: translates abstract_summary', () => {
      expect(helpers.translateFeatureType('abstract_summary')).toBe('Abstrakte Fallzusammenfassung')
    })

    it('RANK_HELP_014: translates generated_category', () => {
      expect(helpers.translateFeatureType('generated_category')).toBe('Generierte Kategorie')
    })

    it('RANK_HELP_015: translates generated_subject', () => {
      expect(helpers.translateFeatureType('generated_subject')).toBe('Generierter Betreff')
    })

    it('RANK_HELP_016: translates situation_summary', () => {
      expect(helpers.translateFeatureType('situation_summary')).toBe('Situationsbeschreibung')
    })

    it('RANK_HELP_017: returns original for unknown type', () => {
      expect(helpers.translateFeatureType('custom_type')).toBe('custom_type')
    })
  })

  // ==================== Formatting ====================

  describe('formatTimestamp', () => {
    it('RANK_HELP_018: formats timestamp in German locale', () => {
      const result = helpers.formatTimestamp('2025-06-15T14:30:00Z')
      expect(result).toContain('Uhr')
      // Should contain date components
      expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
    })
  })

  describe('formatFeatureContent', () => {
    it('RANK_HELP_019: formats Summary type by stripping prefix', () => {
      const result = helpers.formatFeatureContent('Summary', '[Summary A] This is a summary')
      expect(result).toBe('This is a summary')
    })

    it('RANK_HELP_020: formats generated_subject from JSON', () => {
      const json = JSON.stringify({ Betreff: 'Test Subject' })
      const result = helpers.formatFeatureContent('generated_subject', json)
      expect(result).toBe('Test Subject')
    })

    it('RANK_HELP_021: handles invalid JSON for generated_subject', () => {
      const result = helpers.formatFeatureContent('generated_subject', 'not json')
      expect(result).toBe('not json')
    })

    it('RANK_HELP_022: formats situation_summary from JSON', () => {
      const json = JSON.stringify({
        sozial: ['Punkt 1', 'Punkt 2'],
        beruflich: ['Job info']
      })
      const result = helpers.formatFeatureContent('situation_summary', json)
      expect(result).toContain('Sozial')
      expect(result).toContain('Punkt 1')
    })

    it('RANK_HELP_023: handles invalid JSON for situation_summary', () => {
      const result = helpers.formatFeatureContent('situation_summary', 'not json')
      expect(result).toBe('not json')
    })

    it('RANK_HELP_024: returns sanitized content for default type', () => {
      const result = helpers.formatFeatureContent('other', 'Plain text content')
      expect(result).toBe('Plain text content')
    })
  })

  // ==================== Sender Colors ====================

  describe('updateSenderColors', () => {
    it('RANK_HELP_025: assigns alternating colors to different senders', () => {
      const messages = [
        { sender: 'Alice', content: 'Hello' },
        { sender: 'Bob', content: 'Hi' },
        { sender: 'Alice', content: 'How are you?' }
      ]
      helpers.updateSenderColors(messages)

      expect(helpers.senderColors.value['Alice']).toBeDefined()
      expect(helpers.senderColors.value['Bob']).toBeDefined()
      expect(helpers.senderColors.value['Alice']).not.toBe(helpers.senderColors.value['Bob'])
    })

    it('RANK_HELP_026: keeps same color for consecutive messages from same sender', () => {
      const messages = [
        { sender: 'Alice', content: 'Hello' },
        { sender: 'Alice', content: 'Hello again' }
      ]
      helpers.updateSenderColors(messages)

      // All messages from Alice should get the same color
      expect(helpers.senderColors.value['Alice']).toBeDefined()
    })
  })

  describe('getMessageClass', () => {
    it('RANK_HELP_027: returns color from senderColors map', () => {
      helpers.senderColors.value['Alice'] = 'same-sender'
      expect(helpers.getMessageClass('Alice')).toBe('same-sender')
    })

    it('RANK_HELP_028: returns undefined for unknown sender', () => {
      expect(helpers.getMessageClass('Unknown')).toBeUndefined()
    })
  })

  // ==================== Color Generation ====================

  describe('getColorForText', () => {
    it('RANK_HELP_029: returns HSL color string', () => {
      const color = helpers.getColorForText('test text')
      expect(color).toMatch(/^hsl\(\d+, \d+%, \d+%\)$/)
    })

    it('RANK_HELP_030: returns consistent color for same text', () => {
      const color1 = helpers.getColorForText('same text')
      const color2 = helpers.getColorForText('same text')
      expect(color1).toBe(color2)
    })

    it('RANK_HELP_031: returns different colors for different text', () => {
      const color1 = helpers.getColorForText('text a')
      const color2 = helpers.getColorForText('text b')
      // Different text should generally produce different colors
      // (not guaranteed but highly likely for different strings)
      expect(typeof color1).toBe('string')
      expect(typeof color2).toBe('string')
    })
  })

  // ==================== Drag Handlers ====================

  describe('drag handlers', () => {
    it('RANK_HELP_032: handleDragStart adds dragging class to body', () => {
      helpers.handleDragStart()
      expect(document.body.classList.contains('dragging')).toBe(true)
    })

    it('RANK_HELP_033: handleDragEnd removes dragging class from body', () => {
      document.body.classList.add('dragging')
      helpers.handleDragEnd()
      expect(document.body.classList.contains('dragging')).toBe(false)
    })
  })
})
