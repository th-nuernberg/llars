/**
 * Tests for useBuilderValidation composable
 *
 * Test IDs: BVAL_001 - BVAL_055
 *
 * Coverage:
 * - Exports and structure
 * - rules.required validation
 * - rules.url validation
 * - formatDuration helper
 * - extractPageTitle helper
 * - validateUrl function
 * - validateConfig function
 * - Edge cases
 */

import { describe, it, expect } from 'vitest'
import { useBuilderValidation } from '@/composables/useBuilderValidation'

describe('useBuilderValidation Composable', () => {
  describe('Exports', () => {
    it('BVAL_001: exports useBuilderValidation function', () => {
      expect(typeof useBuilderValidation).toBe('function')
    })

    it('BVAL_002: returns all expected properties', () => {
      const result = useBuilderValidation()

      expect(result).toHaveProperty('rules')
      expect(result).toHaveProperty('formatDuration')
      expect(result).toHaveProperty('extractPageTitle')
      expect(result).toHaveProperty('validateUrl')
      expect(result).toHaveProperty('validateConfig')
    })

    it('BVAL_003: rules is an object', () => {
      const { rules } = useBuilderValidation()
      expect(typeof rules).toBe('object')
    })

    it('BVAL_004: rules has required and url validators', () => {
      const { rules } = useBuilderValidation()
      expect(typeof rules.required).toBe('function')
      expect(typeof rules.url).toBe('function')
    })

    it('BVAL_005: formatDuration is a function', () => {
      const { formatDuration } = useBuilderValidation()
      expect(typeof formatDuration).toBe('function')
    })

    it('BVAL_006: extractPageTitle is a function', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(typeof extractPageTitle).toBe('function')
    })

    it('BVAL_007: validateUrl is a function', () => {
      const { validateUrl } = useBuilderValidation()
      expect(typeof validateUrl).toBe('function')
    })

    it('BVAL_008: validateConfig is a function', () => {
      const { validateConfig } = useBuilderValidation()
      expect(typeof validateConfig).toBe('function')
    })
  })

  describe('rules.required', () => {
    it('BVAL_009: returns true for truthy string', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required('hello')).toBe(true)
    })

    it('BVAL_010: returns error message for empty string', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required('')).toBe('Pflichtfeld')
    })

    it('BVAL_011: returns error message for null', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required(null)).toBe('Pflichtfeld')
    })

    it('BVAL_012: returns error message for undefined', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required(undefined)).toBe('Pflichtfeld')
    })

    it('BVAL_013: returns true for number', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required(42)).toBe(true)
    })

    it('BVAL_014: returns error message for zero', () => {
      const { rules } = useBuilderValidation()
      // 0 is falsy, so should return error
      expect(rules.required(0)).toBe('Pflichtfeld')
    })

    it('BVAL_015: returns true for array', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required([1, 2, 3])).toBe(true)
    })

    it('BVAL_016: returns true for object', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required({ key: 'value' })).toBe(true)
    })

    it('BVAL_017: returns true for whitespace string', () => {
      const { rules } = useBuilderValidation()
      // Whitespace is truthy
      expect(rules.required('   ')).toBe(true)
    })
  })

  describe('rules.url', () => {
    it('BVAL_018: returns true for valid http URL', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('http://example.com')).toBe(true)
    })

    it('BVAL_019: returns true for valid https URL', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('https://example.com')).toBe(true)
    })

    it('BVAL_020: returns true for URL with path', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('https://example.com/path/to/page')).toBe(true)
    })

    it('BVAL_021: returns true for URL with query params', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('https://example.com?foo=bar&baz=qux')).toBe(true)
    })

    it('BVAL_022: returns true for empty value (optional)', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('')).toBe(true)
    })

    it('BVAL_023: returns true for null (optional)', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url(null)).toBe(true)
    })

    it('BVAL_024: returns true for undefined (optional)', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url(undefined)).toBe(true)
    })

    it('BVAL_025: returns error for invalid URL', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('not-a-url')).toBe('Ungültige URL')
    })

    it('BVAL_026: returns error for URL without protocol', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('example.com')).toBe('Ungültige URL')
    })

    it('BVAL_027: returns error for malformed URL', () => {
      const { rules } = useBuilderValidation()
      expect(rules.url('http://')).toBe('Ungültige URL')
    })
  })

  describe('formatDuration', () => {
    it('BVAL_028: formats 0 seconds as 0s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(0)).toBe('0s')
    })

    it('BVAL_029: formats null as 0s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(null)).toBe('0s')
    })

    it('BVAL_030: formats undefined as 0s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(undefined)).toBe('0s')
    })

    it('BVAL_031: formats seconds under 60 as Xs', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(45)).toBe('45s')
    })

    it('BVAL_032: formats exactly 60 seconds as 1m 0s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(60)).toBe('1m 0s')
    })

    it('BVAL_033: formats 90 seconds as 1m 30s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(90)).toBe('1m 30s')
    })

    it('BVAL_034: formats 125 seconds as 2m 5s', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(125)).toBe('2m 5s')
    })

    it('BVAL_035: rounds fractional seconds', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(45.7)).toBe('46s')
    })

    it('BVAL_036: rounds fractional seconds in minutes', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(90.4)).toBe('1m 30s')
    })

    it('BVAL_037: handles large values', () => {
      const { formatDuration } = useBuilderValidation()
      expect(formatDuration(3661)).toBe('61m 1s')
    })
  })

  describe('extractPageTitle', () => {
    it('BVAL_038: extracts hostname for root path', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/')).toBe('example.com')
    })

    it('BVAL_039: extracts hostname for empty path', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com')).toBe('example.com')
    })

    it('BVAL_040: extracts last path segment', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/docs/getting-started')).toBe('getting-started')
    })

    it('BVAL_041: extracts single path segment', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/about')).toBe('about')
    })

    it('BVAL_042: handles trailing slash', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/docs/')).toBe('docs')
    })

    it('BVAL_043: returns url for invalid URL', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('not-a-url')).toBe('not-a-url')
    })

    it('BVAL_044: handles URL with query params', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/page?foo=bar')).toBe('page')
    })

    it('BVAL_045: handles subdomain', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://docs.example.com/')).toBe('docs.example.com')
    })
  })

  describe('validateUrl', () => {
    it('BVAL_046: returns valid for valid URL', () => {
      const { validateUrl } = useBuilderValidation()
      const result = validateUrl('https://example.com')

      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })

    it('BVAL_047: returns invalid for empty URL', () => {
      const { validateUrl } = useBuilderValidation()
      const result = validateUrl('')

      expect(result.valid).toBe(false)
      expect(result.error).toBe('URL ist erforderlich')
    })

    it('BVAL_048: returns invalid for null URL', () => {
      const { validateUrl } = useBuilderValidation()
      const result = validateUrl(null)

      expect(result.valid).toBe(false)
      expect(result.error).toBe('URL ist erforderlich')
    })

    it('BVAL_049: returns invalid for malformed URL', () => {
      const { validateUrl } = useBuilderValidation()
      const result = validateUrl('not-a-valid-url')

      expect(result.valid).toBe(false)
      expect(result.error).toBe('Ungültige URL')
    })

    it('BVAL_050: returns valid for complex URL', () => {
      const { validateUrl } = useBuilderValidation()
      const result = validateUrl('https://sub.example.com:8080/path?query=value#hash')

      expect(result.valid).toBe(true)
      expect(result.error).toBe(null)
    })
  })

  describe('validateConfig', () => {
    it('BVAL_051: returns valid for complete config', () => {
      const { validateConfig } = useBuilderValidation()
      const result = validateConfig({
        name: 'my-chatbot',
        displayName: 'My Chatbot',
        systemPrompt: 'You are a helpful assistant.'
      })

      expect(result.valid).toBe(true)
      expect(Object.keys(result.errors).length).toBe(0)
    })

    it('BVAL_052: returns error for missing name', () => {
      const { validateConfig } = useBuilderValidation()
      const result = validateConfig({
        displayName: 'My Chatbot',
        systemPrompt: 'You are a helpful assistant.'
      })

      expect(result.valid).toBe(false)
      expect(result.errors.name).toBe('Interner Name ist erforderlich')
    })

    it('BVAL_053: returns error for missing displayName', () => {
      const { validateConfig } = useBuilderValidation()
      const result = validateConfig({
        name: 'my-chatbot',
        systemPrompt: 'You are a helpful assistant.'
      })

      expect(result.valid).toBe(false)
      expect(result.errors.displayName).toBe('Anzeigename ist erforderlich')
    })

    it('BVAL_054: returns error for missing systemPrompt', () => {
      const { validateConfig } = useBuilderValidation()
      const result = validateConfig({
        name: 'my-chatbot',
        displayName: 'My Chatbot'
      })

      expect(result.valid).toBe(false)
      expect(result.errors.systemPrompt).toBe('System Prompt ist erforderlich')
    })

    it('BVAL_055: returns multiple errors for empty config', () => {
      const { validateConfig } = useBuilderValidation()
      const result = validateConfig({})

      expect(result.valid).toBe(false)
      expect(result.errors.name).toBe('Interner Name ist erforderlich')
      expect(result.errors.displayName).toBe('Anzeigename ist erforderlich')
      expect(result.errors.systemPrompt).toBe('System Prompt ist erforderlich')
    })
  })

  describe('Edge Cases', () => {
    it('BVAL_056: multiple instances return same structure', () => {
      const instance1 = useBuilderValidation()
      const instance2 = useBuilderValidation()

      expect(Object.keys(instance1)).toEqual(Object.keys(instance2))
    })

    it('BVAL_057: rules.required handles boolean true', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required(true)).toBe(true)
    })

    it('BVAL_058: rules.required handles boolean false', () => {
      const { rules } = useBuilderValidation()
      expect(rules.required(false)).toBe('Pflichtfeld')
    })

    it('BVAL_059: formatDuration handles negative values', () => {
      const { formatDuration } = useBuilderValidation()
      // Negative values are truthy, so won't return '0s'
      const result = formatDuration(-30)
      // -30 < 60, so should format as seconds
      expect(result).toBe('-30s')
    })

    it('BVAL_060: extractPageTitle handles file extension', () => {
      const { extractPageTitle } = useBuilderValidation()
      expect(extractPageTitle('https://example.com/docs/guide.html')).toBe('guide.html')
    })
  })
})
