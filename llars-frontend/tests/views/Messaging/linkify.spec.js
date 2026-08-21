/**
 * linkifyMessage Utility Tests
 *
 * Tests URL detection, HTML escaping, URL shortening, and trailing punctuation handling.
 * Test IDs: LINK_001 - LINK_025
 */

import { describe, it, expect } from 'vitest'
import { linkifyMessage } from '@/views/Messaging/utils/linkify'

describe('linkifyMessage', () => {
  // ==================== Basic Behavior ====================

  describe('basic', () => {
    it('LINK_001: returns empty string for null input', () => {
      expect(linkifyMessage(null)).toBe('')
    })

    it('LINK_002: returns empty string for undefined input', () => {
      expect(linkifyMessage(undefined)).toBe('')
    })

    it('LINK_003: returns empty string for empty string', () => {
      expect(linkifyMessage('')).toBe('')
    })

    it('LINK_004: returns escaped text with no URLs', () => {
      expect(linkifyMessage('Hello world')).toBe('Hello world')
    })
  })

  // ==================== URL Detection ====================

  describe('URL detection', () => {
    it('LINK_005: detects http URL', () => {
      const result = linkifyMessage('Visit http://example.com')
      expect(result).toContain('<a href="http://example.com"')
      expect(result).toContain('target="_blank"')
      expect(result).toContain('rel="noopener noreferrer"')
    })

    it('LINK_006: detects https URL', () => {
      const result = linkifyMessage('Visit https://example.com')
      expect(result).toContain('<a href="https://example.com"')
    })

    it('LINK_007: detects URL with path', () => {
      const result = linkifyMessage('See https://example.com/path/to/page')
      expect(result).toContain('href="https://example.com/path/to/page"')
    })

    it('LINK_008: detects multiple URLs', () => {
      const result = linkifyMessage('Visit https://a.com and https://b.com')
      expect(result).toContain('href="https://a.com"')
      expect(result).toContain('href="https://b.com"')
    })

    it('LINK_009: preserves text between URLs', () => {
      const result = linkifyMessage('Before https://a.com middle https://b.com after')
      expect(result).toContain('Before ')
      expect(result).toContain(' middle ')
      expect(result).toContain(' after')
    })
  })

  // ==================== HTML Escaping ====================

  describe('HTML escaping', () => {
    it('LINK_010: escapes angle brackets in non-URL text', () => {
      const result = linkifyMessage('Use <script> tags carefully')
      expect(result).toContain('&lt;script&gt;')
      expect(result).not.toContain('<script>')
    })

    it('LINK_011: escapes ampersands in non-URL text', () => {
      const result = linkifyMessage('A & B are here')
      expect(result).toContain('A &amp; B are here')
    })

    it('LINK_012: escapes quotes in non-URL text', () => {
      const result = linkifyMessage('He said "hello"')
      expect(result).toContain('&quot;hello&quot;')
    })
  })

  // ==================== Trailing Punctuation ====================

  describe('trailing punctuation', () => {
    it('LINK_013: strips trailing period from URL', () => {
      const result = linkifyMessage('Visit https://example.com.')
      expect(result).toContain('href="https://example.com"')
      expect(result).toMatch(/\.(?!.*href)/) // period after the link
    })

    it('LINK_014: strips trailing comma from URL', () => {
      const result = linkifyMessage('https://example.com, then')
      expect(result).toContain('href="https://example.com"')
    })

    it('LINK_015: strips trailing exclamation from URL', () => {
      const result = linkifyMessage('Check https://example.com!')
      expect(result).toContain('href="https://example.com"')
    })
  })

  // ==================== URL Shortening ====================

  describe('URL shortening', () => {
    it('LINK_016: shortens very long URLs in display text', () => {
      const longUrl = 'https://example.com/' + 'a'.repeat(100)
      const result = linkifyMessage(longUrl)
      expect(result).toContain('...')
      // The href should contain the full URL
      expect(result).toContain(`href="${longUrl}"`)
    })

    it('LINK_017: does not shorten short URLs', () => {
      const result = linkifyMessage('https://example.com/short')
      expect(result).not.toContain('...')
    })
  })

  // ==================== Edge Cases ====================

  describe('edge cases', () => {
    it('LINK_018: handles URL at start of text', () => {
      const result = linkifyMessage('https://example.com is great')
      expect(result).toContain('<a href="https://example.com"')
      expect(result).toContain(' is great')
    })

    it('LINK_019: handles URL at end of text', () => {
      const result = linkifyMessage('Visit https://example.com')
      expect(result).toContain('<a href="https://example.com"')
    })

    it('LINK_020: handles URL with query parameters', () => {
      const result = linkifyMessage('https://example.com/search?q=test&lang=en')
      expect(result).toContain('href="https://example.com/search?q=test&amp;lang=en"')
    })

    it('LINK_021: handles URL with hash fragment', () => {
      const result = linkifyMessage('https://example.com/page#section')
      expect(result).toContain('href="https://example.com/page#section"')
    })

    it('LINK_022: adds message-link class to links', () => {
      const result = linkifyMessage('https://example.com')
      expect(result).toContain('class="message-link"')
    })
  })
})
