/**
 * useAppTheme Composable
 * Manages theme switching between light, dark, and system preference
 */

import { ref, computed, watch, onMounted } from 'vue'
import { useTheme } from 'vuetify'

// Shared state (singleton pattern)
const THEME_STORAGE_KEY = 'llars-theme-preference'
const themePreference = ref(localStorage.getItem(THEME_STORAGE_KEY) || 'system')
const systemPrefersDark = ref(false)

// Media query for system color scheme
let mediaQuery = null

export function useAppTheme() {
  const vuetifyTheme = useTheme()

  /**
   * Initialize system preference detection
   */
  const initSystemPreference = () => {
    if (typeof window === 'undefined') return

    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = mediaQuery.matches

    // Listen for system preference changes
    const handleChange = (e) => {
      systemPrefersDark.value = e.matches
      if (themePreference.value === 'system') {
        applyTheme()
      }
    }

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange)
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange)
    }
  }

  /**
   * Apply the current theme based on preference
   */
  const applyTheme = () => {
    let targetTheme = 'light'

    if (themePreference.value === 'dark') {
      targetTheme = 'dark'
    } else if (themePreference.value === 'light') {
      targetTheme = 'light'
    } else if (themePreference.value === 'system') {
      targetTheme = systemPrefersDark.value ? 'dark' : 'light'
    }

    // Update Vuetify theme
    if (typeof vuetifyTheme.change === 'function') {
      vuetifyTheme.change(targetTheme)
    } else {
      vuetifyTheme.global.name.value = targetTheme
    }

    // Update HTML attribute for custom CSS
    document.documentElement.setAttribute('data-theme', targetTheme)

    console.log(`Theme applied: ${targetTheme} (preference: ${themePreference.value})`)
  }

  /**
   * Set theme preference (system, light, or dark)
   */
  const setThemePreference = (preference) => {
    if (!['system', 'light', 'dark'].includes(preference)) {
      console.warn(`Invalid theme preference: ${preference}`)
      return
    }

    themePreference.value = preference
    localStorage.setItem(THEME_STORAGE_KEY, preference)
    applyTheme()
  }

  /**
   * Toggle between light and dark (ignores system)
   */
  const toggleTheme = () => {
    const currentTheme = vuetifyTheme.global.current.value.dark ? 'dark' : 'light'
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
    setThemePreference(newTheme)
  }

  /**
   * Get the current active theme name
   */
  const currentTheme = computed(() => {
    return vuetifyTheme.global.current.value.dark ? 'dark' : 'light'
  })

  /**
   * Check if current theme is dark
   */
  const isDark = computed(() => {
    return vuetifyTheme.global.current.value.dark
  })

  /**
   * Get available theme options for UI
   */
  const themeOptions = computed(() => [
    { value: 'system', title: 'System', icon: 'mdi-brightness-auto' },
    { value: 'light', title: 'Hell', icon: 'mdi-white-balance-sunny' },
    { value: 'dark', title: 'Dunkel', icon: 'mdi-moon-waning-crescent' },
  ])

  /**
   * Get current theme option details
   */
  const currentThemeOption = computed(() => {
    return themeOptions.value.find(opt => opt.value === themePreference.value)
  })

  // Watch for preference changes
  watch(themePreference, () => {
    applyTheme()
  })

  // Initialize on mount
  onMounted(() => {
    initSystemPreference()
    applyTheme()
  })

  return {
    // State
    themePreference,
    currentTheme,
    isDark,
    systemPrefersDark,

    // Options
    themeOptions,
    currentThemeOption,

    // Methods
    setThemePreference,
    toggleTheme,
    applyTheme,
  }
}

/**
 * Initialize theme on app startup (called from main.js)
 */
export function initAppTheme() {
  const { applyTheme } = useAppTheme()

  // Check if window is available (SSR guard)
  if (typeof window === 'undefined') return

  // Apply saved theme immediately
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'system'
  themePreference.value = savedTheme

  // Detect system preference
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  systemPrefersDark.value = mq.matches

  // Apply theme
  applyTheme()

  console.log('App theme initialized')
}
