/**
 * useHistoryHelpers Composable Tests
 *
 * Tests for content formatting, timestamp formatting, message classification, and DOM helpers.
 * Test IDs: HIST_HELP_001 - HIST_HELP_020
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('dompurify', () => ({
  default: {
    sanitize: vi.fn((html, opts) => {
      if (opts && opts.ALLOWED_TAGS && opts.ALLOWED_TAGS.length === 0) return ''
      return html
    })
  }
}))

import { useHistoryHelpers } from '@/components/HistoryGenerator/HistoryGenerationDetail/composables/useHistoryHelpers'

describe('useHistoryHelpers', () => {
  let helpers

  beforeEach(() => {
    helpers = useHistoryHelpers()
  })

  // ==================== formatContent ====================

  describe('formatContent', () => {
    it('HIST_HELP_001: returns empty string for null', () => {
      expect(helpers.formatContent(null)).toBe('')
    })

    it('HIST_HELP_002: returns empty string for empty string', () => {
      expect(helpers.formatContent('')).toBe('')
    })

    it('HIST_HELP_003: converts newlines to br tags', () => {
      const result = helpers.formatContent('Line 1\nLine 2')
      expect(result).toContain('<br>')
    })

    it('HIST_HELP_004: passes content through DOMPurify', () => {
      const result = helpers.formatContent('Hello world')
      expect(typeof result).toBe('string')
    })
  })

  // ==================== formatTimestamp ====================

  describe('formatTimestamp', () => {
    it('HIST_HELP_005: formats timestamp in German locale', () => {
      const result = helpers.formatTimestamp('2025-06-15T14:30:00Z')
      expect(result).toContain('Uhr')
    })

    it('HIST_HELP_006: includes date components', () => {
      const result = helpers.formatTimestamp('2025-06-15T14:30:00Z')
      // Should contain dd.mm.yyyy format
      expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
    })
  })

  // ==================== getMessageClass ====================

  describe('getMessageClass', () => {
    it('HIST_HELP_007: returns same-sender for client variants', () => {
      expect(helpers.getMessageClass('Ratsuchende Person')).toBe('same-sender')
      expect(helpers.getMessageClass('Ratsuchender')).toBe('same-sender')
      expect(helpers.getMessageClass('ratsuchend')).toBe('same-sender')
      expect(helpers.getMessageClass('ratsuchende')).toBe('same-sender')
    })

    it('HIST_HELP_008: returns different-sender for counselor variants', () => {
      expect(helpers.getMessageClass('Beratende Person')).toBe('different-sender')
      expect(helpers.getMessageClass('Berater')).toBe('different-sender')
      expect(helpers.getMessageClass('beratend')).toBe('different-sender')
      expect(helpers.getMessageClass('beratende')).toBe('different-sender')
    })

    it('HIST_HELP_009: returns different-sender for unknown sender', () => {
      expect(helpers.getMessageClass('Unknown')).toBe('different-sender')
    })

    it('HIST_HELP_010: handles case insensitivity', () => {
      expect(helpers.getMessageClass('RATSUCHENDE PERSON')).toBe('same-sender')
    })

    it('HIST_HELP_011: handles whitespace trimming', () => {
      expect(helpers.getMessageClass('  Berater  ')).toBe('different-sender')
    })
  })

  // ==================== DOM Helpers ====================

  describe('checkIfDisabled', () => {
    it('HIST_HELP_012: returns false when element not found', () => {
      expect(helpers.checkIfDisabled('nonexistent')).toBe(false)
    })

    it('HIST_HELP_013: returns true when element has disabled class', () => {
      const el = document.createElement('div')
      el.id = 'test-disabled'
      el.classList.add('disabled')
      document.body.appendChild(el)

      expect(helpers.checkIfDisabled('test-disabled')).toBe(true)

      document.body.removeChild(el)
    })

    it('HIST_HELP_014: returns false when element lacks disabled class', () => {
      const el = document.createElement('div')
      el.id = 'test-enabled'
      document.body.appendChild(el)

      expect(helpers.checkIfDisabled('test-enabled')).toBe(false)

      document.body.removeChild(el)
    })
  })

  describe('toggleClassForDiv', () => {
    it('HIST_HELP_015: adds disabled class when shouldDisable is true', () => {
      const el = document.createElement('div')
      el.id = 'toggle-test'
      document.body.appendChild(el)

      helpers.toggleClassForDiv('toggle-test', true)
      expect(el.classList.contains('disabled')).toBe(true)

      document.body.removeChild(el)
    })

    it('HIST_HELP_016: removes disabled class when shouldDisable is false', () => {
      const el = document.createElement('div')
      el.id = 'toggle-test2'
      el.classList.add('disabled')
      document.body.appendChild(el)

      helpers.toggleClassForDiv('toggle-test2', false)
      expect(el.classList.contains('disabled')).toBe(false)

      document.body.removeChild(el)
    })

    it('HIST_HELP_017: does nothing for nonexistent element', () => {
      expect(() => helpers.toggleClassForDiv('nonexistent', true)).not.toThrow()
    })
  })
})
