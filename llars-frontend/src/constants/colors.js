/**
 * LLARS Design System Colors
 * Central color definitions for consistent styling across the application
 */

// Collaboration color presets (for user cursor/highlight colors)
// Note: Purple/violet colors are reserved for AI - don't add them here
export const COLLAB_COLOR_PRESETS = [
  '#b0ca97', // primary - sage green
  '#98d4bb', // success - soft mint
  '#88c4c8', // accent - soft teal
  '#D1BC8A', // secondary - golden beige
  '#a8c5e2', // info - soft blue
  '#f0b6c2', // pink - soft rose
  '#e8c87a', // warning - soft gold
  '#FF6B6B', // coral red
  '#4ECDC4', // turquoise
  '#45B7D1', // sky blue
  '#E67E22', // orange
  '#27AE60'  // emerald green
]

// LLARS brand colors (hex without #)
export const LLARS_COLORS = [
  'b0ca97', // primary - sage green
  '98d4bb', // success - soft mint
  'a8c5e2', // info - soft blue
  'e8c87a', // warning - soft gold
  '88c4c8', // accent - soft teal
  'D1BC8A', // secondary - golden beige
  'e8a087', // danger - soft coral
  'c5b4e3', // purple - soft lavender (for generated avatars only)
  'f0b6c2'  // pink - soft rose
]

// AI Reserved color range (purple/violet spectrum)
// This entire range is reserved for LLARS AI assistant
export const AI_RESERVED_COLOR = '#9B59B6'

/**
 * Convert hex color to HSL
 * @param {string} hex - Hex color string (with or without #)
 * @returns {{h: number, s: number, l: number}} HSL values (h: 0-360, s: 0-100, l: 0-100)
 */
export function hexToHsl(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  if (!result) return { h: 0, s: 0, l: 0 }

  let r = parseInt(result[1], 16) / 255
  let g = parseInt(result[2], 16) / 255
  let b = parseInt(result[3], 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  let h, s
  const l = (max + min) / 2

  if (max === min) {
    h = s = 0
  } else {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break
      case g: h = ((b - r) / d + 2) / 6; break
      case b: h = ((r - g) / d + 4) / 6; break
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100)
  }
}

/**
 * Check if a color is in the AI reserved purple/violet range
 * Purple/violet hues are approximately 270-330 degrees on the color wheel
 * @param {string} color - Hex color to check
 * @returns {boolean} True if color is in the reserved range
 */
export function isColorInAiReservedRange(color) {
  const hsl = hexToHsl(color)
  // Purple/violet range: hue 260-320, with reasonable saturation (>20%) and not too dark/light
  const isInPurpleHueRange = hsl.h >= 260 && hsl.h <= 320
  const hasEnoughSaturation = hsl.s >= 20
  const isNotExtreme = hsl.l >= 20 && hsl.l <= 85

  return isInPurpleHueRange && hasEnoughSaturation && isNotExtreme
}
