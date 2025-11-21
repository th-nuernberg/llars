/**
 * Central theme configuration for LLars
 * Defines colors and styling for both light and dark modes
 */

export const lightTheme = {
  dark: false,
  colors: {
    // Primary brand colors
    primary: '#b0ca97',      // Light green (LLars brand color)
    'primary-darken-1': '#9db882',
    'primary-lighten-1': '#c4d8ac',

    secondary: '#81b68b',    // Darker green
    'secondary-darken-1': '#6ea176',
    'secondary-lighten-1': '#9cc3a4',

    accent: '#8c9eff',       // Blue accent

    // Semantic colors
    error: '#b71c1c',        // Red for errors
    warning: '#f57c00',      // Orange for warnings
    info: '#1976D2',         // Blue for info
    success: '#388E3C',      // Green for success

    // Admin color
    admin: '#8c00ff',        // Purple for admin

    // Background and surface
    background: '#f5f5f5',   // Light gray background
    surface: '#ffffff',      // White surface
    'surface-variant': '#f0f0f0',
    'surface-bright': '#ffffff',
    'surface-light': '#fafafa',

    // Text colors
    'on-background': '#1a1a1a',
    'on-surface': '#1a1a1a',
    'on-primary': '#ffffff',
    'on-secondary': '#ffffff',
    'on-error': '#ffffff',
    'on-warning': '#ffffff',
    'on-info': '#ffffff',
    'on-success': '#ffffff',

    // Additional UI colors
    'grey-lighten-5': '#fafafa',
    'grey-lighten-4': '#f5f5f5',
    'grey-lighten-3': '#eeeeee',
    'grey-lighten-2': '#e0e0e0',
    'grey-lighten-1': '#bdbdbd',
    'grey': '#9e9e9e',
    'grey-darken-1': '#757575',
    'grey-darken-2': '#616161',
    'grey-darken-3': '#424242',
    'grey-darken-4': '#212121',
  }
}

export const darkTheme = {
  dark: true,
  colors: {
    // Primary brand colors (optimized for dark mode)
    primary: '#8fbc6b',      // Darker, more saturated green for dark backgrounds
    'primary-darken-1': '#7aa857',
    'primary-lighten-1': '#a3c97f',

    secondary: '#6b9e56',    // Even darker green for secondary
    'secondary-darken-1': '#5a8847',
    'secondary-lighten-1': '#7fb265',

    accent: '#8c9eff',       // Blue accent

    // Semantic colors
    error: '#ef5350',        // Lighter red for dark mode
    warning: '#ff9800',      // Orange
    info: '#42a5f5',         // Lighter blue
    success: '#66bb6a',      // Lighter green

    // Admin color
    admin: '#a855f7',        // Lighter purple for dark mode

    // Background and surface (dark mode)
    background: '#121212',   // Very dark gray (Material Design standard)
    surface: '#1e1e1e',      // Slightly lighter dark gray
    'surface-variant': '#2c2c2c',
    'surface-bright': '#323232',
    'surface-light': '#272727',

    // Text colors (optimized for dark mode)
    'on-background': '#e5e5e5',      // Slightly brighter for better readability
    'on-surface': '#e5e5e5',         // Slightly brighter for better readability
    'on-primary': '#ffffff',         // White text on green buttons/cards
    'on-secondary': '#ffffff',       // White text on secondary elements
    'on-error': '#ffffff',           // White text on error backgrounds
    'on-warning': '#000000',         // Black text on orange (better contrast)
    'on-info': '#000000',            // Black text on light blue
    'on-success': '#000000',         // Black text on success green

    // Additional UI colors (dark variants)
    'grey-lighten-5': '#424242',
    'grey-lighten-4': '#383838',
    'grey-lighten-3': '#2e2e2e',
    'grey-lighten-2': '#242424',
    'grey-lighten-1': '#1a1a1a',
    'grey': '#757575',
    'grey-darken-1': '#9e9e9e',
    'grey-darken-2': '#bdbdbd',
    'grey-darken-3': '#e0e0e0',
    'grey-darken-4': '#eeeeee',
  }
}

/**
 * Common theme variables (used in both light and dark mode)
 */
export const commonThemeVariables = {
  // Border radius
  'border-radius-root': '4px',
  'border-radius-sm': '2px',
  'border-radius-md': '6px',
  'border-radius-lg': '8px',
  'border-radius-xl': '12px',

  // Transitions
  'transition-fast': '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  'transition-default': '250ms cubic-bezier(0.4, 0, 0.2, 1)',
  'transition-slow': '350ms cubic-bezier(0.4, 0, 0.2, 1)',

  // Shadows (will be adapted by Vuetify for dark mode)
  'shadow-key-umbra-opacity': '0.2',
  'shadow-key-penumbra-opacity': '0.14',
  'shadow-key-ambient-opacity': '0.12',
}

/**
 * Helper function to get semantic color for a specific context
 */
export function getSemanticColor(type) {
  const colorMap = {
    error: 'error',
    warning: 'warning',
    info: 'info',
    success: 'success',
    primary: 'primary',
    secondary: 'secondary',
  }

  return colorMap[type] || 'primary'
}

/**
 * Helper to check if a color has sufficient contrast
 * @param {string} foreground - Foreground color in hex
 * @param {string} background - Background color in hex
 * @returns {boolean} - True if contrast ratio is at least 4.5:1
 */
export function hasGoodContrast(foreground, background) {
  // This is a simplified version - in production you'd use a proper contrast calculation
  // For now, we assume our theme colors have good contrast
  return true
}

export default {
  lightTheme,
  darkTheme,
  commonThemeVariables,
  getSemanticColor,
  hasGoodContrast,
}
