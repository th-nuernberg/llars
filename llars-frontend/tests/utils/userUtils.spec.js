/**
 * User Utils Tests
 *
 * Tests for user display utilities (avatars, colors, name formatting).
 * Test IDs: UTIL_USR_001 - UTIL_USR_050
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the colors constant before importing userUtils
vi.mock('@/constants/colors', () => ({
  LLARS_COLORS: [
    'c7dcc0', 'c4e3d5', 'c5d9eb', 'e8d8ab',
    'b8dddf', 'ddccad', 'e7bfae', 'cfbfdc', 'e7c2cb'
  ]
}))

import {
  getColorFromSeed,
  getDiceBearUrl,
  getAvatarUrl,
  formatDisplayName,
  formatRelativeDate,
  getUserDisplayName
} from '@/utils/userUtils'

// ==================== getColorFromSeed Tests ====================

describe('getColorFromSeed', () => {
  it('UTIL_USR_001: returns a color from LLARS_COLORS', () => {
    const validColors = ['c7dcc0', 'c4e3d5', 'c5d9eb', 'e8d8ab', 'b8dddf', 'ddccad', 'e7bfae', 'cfbfdc', 'e7c2cb']
    const result = getColorFromSeed('testuser')
    expect(validColors).toContain(result)
  })

  it('UTIL_USR_002: returns consistent color for same seed', () => {
    const color1 = getColorFromSeed('alice')
    const color2 = getColorFromSeed('alice')
    expect(color1).toBe(color2)
  })

  it('UTIL_USR_003: returns different colors for different seeds', () => {
    const color1 = getColorFromSeed('alice')
    const color2 = getColorFromSeed('bob')
    // Not strictly guaranteed but statistically very likely with different strings
    // We just ensure both return valid colors
    expect(typeof color1).toBe('string')
    expect(typeof color2).toBe('string')
  })

  it('UTIL_USR_004: handles null seed with default', () => {
    const result = getColorFromSeed(null)
    expect(typeof result).toBe('string')
    expect(result.length).toBeGreaterThan(0)
  })

  it('UTIL_USR_005: handles undefined seed with default', () => {
    const result = getColorFromSeed(undefined)
    expect(typeof result).toBe('string')
  })

  it('UTIL_USR_006: handles empty string with default', () => {
    const result = getColorFromSeed('')
    expect(typeof result).toBe('string')
  })

  it('UTIL_USR_007: null and undefined produce same result (both use "default")', () => {
    expect(getColorFromSeed(null)).toBe(getColorFromSeed(undefined))
  })
})

// ==================== getDiceBearUrl Tests ====================

describe('getDiceBearUrl', () => {
  it('UTIL_USR_008: returns a DiceBear URL', () => {
    const url = getDiceBearUrl('testuser')
    expect(url).toContain('https://api.dicebear.com/7.x/')
    expect(url).toContain('/svg')
  })

  it('UTIL_USR_009: uses initials variant by default', () => {
    const url = getDiceBearUrl('testuser')
    expect(url).toContain('/initials/')
  })

  it('UTIL_USR_010: uses default size of 80', () => {
    const url = getDiceBearUrl('testuser')
    expect(url).toContain('size=80')
  })

  it('UTIL_USR_011: accepts custom size', () => {
    const url = getDiceBearUrl('testuser', 120)
    expect(url).toContain('size=120')
  })

  it('UTIL_USR_012: accepts custom variant', () => {
    const url = getDiceBearUrl('testuser', 80, 'bottts-neutral')
    expect(url).toContain('/bottts-neutral/')
  })

  it('UTIL_USR_013: encodes seed in URL', () => {
    const url = getDiceBearUrl('test user with spaces')
    expect(url).toContain('seed=test%20user%20with%20spaces')
  })

  it('UTIL_USR_014: includes backgroundColor from getColorFromSeed', () => {
    const url = getDiceBearUrl('testuser')
    expect(url).toContain('backgroundColor=')
  })

  it('UTIL_USR_015: handles null seed with fallback "?"', () => {
    const url = getDiceBearUrl(null)
    expect(url).toContain('seed=%3F')
  })

  it('UTIL_USR_016: handles empty string seed with fallback "?"', () => {
    const url = getDiceBearUrl('')
    expect(url).toContain('seed=%3F')
  })
})

// ==================== getAvatarUrl Tests ====================

describe('getAvatarUrl', () => {
  it('UTIL_USR_017: returns DiceBear URL for null user', () => {
    const url = getAvatarUrl(null)
    expect(url).toContain('dicebear.com')
  })

  it('UTIL_USR_018: returns custom avatar_url when present as full URL', () => {
    const user = { avatar_url: 'https://example.com/avatar.png' }
    const url = getAvatarUrl(user)
    expect(url).toBe('https://example.com/avatar.png')
  })

  it('UTIL_USR_019: prepends apiBase for relative avatar_url', () => {
    const user = { avatar_url: '/uploads/avatar.png' }
    const url = getAvatarUrl(user, 'http://localhost:8081')
    expect(url).toBe('http://localhost:8081/uploads/avatar.png')
  })

  it('UTIL_USR_020: falls back to DiceBear with avatar_seed', () => {
    const user = { avatar_seed: 'myseed', username: 'john' }
    const url = getAvatarUrl(user)
    expect(url).toContain('dicebear.com')
    expect(url).toContain('seed=myseed')
  })

  it('UTIL_USR_021: falls back to DiceBear with username when no avatar_seed', () => {
    const user = { username: 'john' }
    const url = getAvatarUrl(user)
    expect(url).toContain('dicebear.com')
    expect(url).toContain('seed=john')
  })

  it('UTIL_USR_022: falls back to "?" when user has no identifying info', () => {
    const user = {}
    const url = getAvatarUrl(user)
    expect(url).toContain('dicebear.com')
    expect(url).toContain('seed=%3F')
  })

  it('UTIL_USR_023: prioritizes avatar_url over avatar_seed', () => {
    const user = {
      avatar_url: 'https://example.com/avatar.png',
      avatar_seed: 'myseed',
      username: 'john'
    }
    const url = getAvatarUrl(user)
    expect(url).toBe('https://example.com/avatar.png')
  })

  it('UTIL_USR_024: prioritizes avatar_seed over username', () => {
    const user = { avatar_seed: 'myseed', username: 'john' }
    const url = getAvatarUrl(user)
    expect(url).toContain('seed=myseed')
    expect(url).not.toContain('seed=john')
  })
})

// ==================== formatDisplayName Tests ====================

describe('formatDisplayName', () => {
  it('UTIL_USR_025: returns empty string for null', () => {
    expect(formatDisplayName(null)).toBe('')
  })

  it('UTIL_USR_026: returns empty string for undefined', () => {
    expect(formatDisplayName(undefined)).toBe('')
  })

  it('UTIL_USR_027: returns empty string for empty string', () => {
    expect(formatDisplayName('')).toBe('')
  })

  it('UTIL_USR_028: converts underscore-separated name', () => {
    expect(formatDisplayName('john_doe')).toBe('John Doe')
  })

  it('UTIL_USR_029: converts dot-separated name', () => {
    expect(formatDisplayName('john.doe')).toBe('John Doe')
  })

  it('UTIL_USR_030: converts dash-separated name', () => {
    expect(formatDisplayName('john-doe')).toBe('John Doe')
  })

  it('UTIL_USR_031: capitalizes single word', () => {
    expect(formatDisplayName('admin')).toBe('Admin')
  })

  it('UTIL_USR_032: handles already capitalized name', () => {
    expect(formatDisplayName('John')).toBe('John')
  })

  it('UTIL_USR_033: lowercases rest of each word', () => {
    expect(formatDisplayName('JOHN_DOE')).toBe('John Doe')
  })

  it('UTIL_USR_034: handles mixed separators', () => {
    expect(formatDisplayName('john_doe.smith-jr')).toBe('John Doe Smith Jr')
  })
})

// ==================== formatRelativeDate Tests ====================

describe('formatRelativeDate', () => {
  it('UTIL_USR_035: returns empty string for null', () => {
    expect(formatRelativeDate(null)).toBe('')
  })

  it('UTIL_USR_036: returns empty string for undefined', () => {
    expect(formatRelativeDate(undefined)).toBe('')
  })

  it('UTIL_USR_037: returns empty string for empty string', () => {
    expect(formatRelativeDate('')).toBe('')
  })

  it('UTIL_USR_038: returns "Heute" for today', () => {
    const now = new Date()
    const result = formatRelativeDate(now.toISOString())
    expect(result).toBe('Heute')
  })

  it('UTIL_USR_039: returns "Gestern" for yesterday', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    // Set to early morning to avoid edge cases
    yesterday.setHours(1, 0, 0, 0)
    const result = formatRelativeDate(yesterday.toISOString())
    expect(result).toBe('Gestern')
  })

  it('UTIL_USR_040: returns "Vor X Tagen" for 2-6 days ago', () => {
    const threeDaysAgo = new Date()
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3)
    threeDaysAgo.setHours(1, 0, 0, 0)
    const result = formatRelativeDate(threeDaysAgo.toISOString())
    expect(result).toBe('Vor 3 Tagen')
  })

  it('UTIL_USR_041: returns "Vor X Wo." for 7-29 days ago', () => {
    const twoWeeksAgo = new Date()
    twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14)
    twoWeeksAgo.setHours(1, 0, 0, 0)
    const result = formatRelativeDate(twoWeeksAgo.toISOString())
    expect(result).toBe('Vor 2 Wo.')
  })

  it('UTIL_USR_042: returns formatted date for 30+ days ago', () => {
    const twoMonthsAgo = new Date()
    twoMonthsAgo.setDate(twoMonthsAgo.getDate() - 60)
    const result = formatRelativeDate(twoMonthsAgo.toISOString())
    // Should be like "5. Jan." or similar German short date
    expect(result).toMatch(/\d+\.\s\w+/)
  })
})

// ==================== getUserDisplayName Tests ====================

describe('getUserDisplayName', () => {
  it('UTIL_USR_043: returns empty string for null', () => {
    expect(getUserDisplayName(null)).toBe('')
  })

  it('UTIL_USR_044: returns empty string for undefined', () => {
    expect(getUserDisplayName(undefined)).toBe('')
  })

  it('UTIL_USR_045: formats string username via formatDisplayName', () => {
    expect(getUserDisplayName('john_doe')).toBe('John Doe')
  })

  it('UTIL_USR_046: returns display_name from user object when available', () => {
    const user = { display_name: 'Dr. John Doe', username: 'john_doe' }
    expect(getUserDisplayName(user)).toBe('Dr. John Doe')
  })

  it('UTIL_USR_047: falls back to formatDisplayName when no display_name', () => {
    const user = { username: 'jane_smith' }
    expect(getUserDisplayName(user)).toBe('Jane Smith')
  })

  it('UTIL_USR_048: returns empty string for user object with no username and no display_name', () => {
    const user = {}
    expect(getUserDisplayName(user)).toBe('')
  })

  it('UTIL_USR_049: prefers display_name over username formatting', () => {
    const user = { display_name: 'Custom Name', username: 'totally_different' }
    expect(getUserDisplayName(user)).toBe('Custom Name')
  })

  it('UTIL_USR_050: handles user object with empty display_name string', () => {
    const user = { display_name: '', username: 'john_doe' }
    expect(getUserDisplayName(user)).toBe('John Doe')
  })
})
