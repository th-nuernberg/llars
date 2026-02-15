/**
 * User display utilities for avatars and name formatting
 */

import { LLARS_COLORS } from '@/constants/colors'

/**
 * Generate a consistent color from a seed string
 * @param {string} seed - Seed string (username, avatar_seed, etc.)
 * @returns {string} Hex color without #
 */
export function getColorFromSeed(seed) {
  const str = seed || 'default'
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash)
  }
  return LLARS_COLORS[Math.abs(hash) % LLARS_COLORS.length]
}

/**
 * Generate DiceBear avatar URL with initials style for humans
 * Note: bottts-neutral (robots) should only be used for AI/bot avatars
 * @param {string} seed - Seed for avatar generation
 * @param {number} size - Avatar size in pixels (default: 80)
 * @param {string} variant - Avatar variant (default: 'initials', use 'bottts-neutral' for bots)
 * @returns {string} DiceBear avatar URL
 */
export function getDiceBearUrl(seed, size = 80, variant = 'initials') {
  const safeSeed = seed || '?'
  const bgColor = getColorFromSeed(safeSeed)
  return `https://api.dicebear.com/7.x/${variant}/svg?seed=${encodeURIComponent(safeSeed)}&size=${size}&backgroundColor=${bgColor}`
}

/**
 * Get avatar URL for a user object
 * Prioritizes custom avatar, falls back to DiceBear
 * @param {Object} user - User object with avatar_url, avatar_seed, username
 * @param {string} apiBase - API base URL (default: from env)
 * @returns {string} Avatar URL
 */
export function getAvatarUrl(user, apiBase = null) {
  const base = apiBase || import.meta.env.VITE_API_BASE_URL || ''

  if (!user) return getDiceBearUrl('?')

  // If user has custom avatar, use it
  if (user.avatar_url) {
    // If it's already a full URL, return as-is
    if (user.avatar_url.startsWith('http')) {
      return user.avatar_url
    }
    return base + user.avatar_url
  }

  // Otherwise use DiceBear with avatar_seed or username
  return getDiceBearUrl(user.avatar_seed || user.username || '?')
}

/**
 * Format username to display name with proper capitalization
 * e.g., "john_doe" -> "John Doe", "john.doe" -> "John Doe"
 * @param {string} username - Username to format
 * @returns {string} Formatted display name
 */
export function formatDisplayName(username) {
  if (!username) return ''
  return username
    .replace(/[._-]/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ')
}

/**
 * Format a date relative to now (German)
 * @param {string} isoDate - ISO date string
 * @returns {string} Relative date string
 */
export function formatRelativeDate(isoDate) {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Heute'
  if (diffDays === 1) return 'Gestern'
  if (diffDays < 7) return `Vor ${diffDays} Tagen`
  if (diffDays < 30) return `Vor ${Math.floor(diffDays / 7)} Wo.`
  return date.toLocaleDateString('de-DE', { day: 'numeric', month: 'short' })
}
