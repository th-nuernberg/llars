/**
 * useLanguage Composable
 * Manages language switching between German and English
 *
 * @module useLanguage
 */

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LANGUAGE_STORAGE_KEY, DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES } from '@/i18n'

// Shared state (singleton pattern - same as useAppTheme)
const currentLanguage = ref(DEFAULT_LANGUAGE)

// Initialize from localStorage on module load
if (typeof window !== 'undefined') {
  try {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY)
    if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
      currentLanguage.value = saved
    }
  } catch (e) {
    // localStorage not available
  }
}

/**
 * Composable for managing application language
 * @returns {Object} Language state and methods
 */
export function useLanguage() {
  const { locale } = useI18n()

  /**
   * Available language options for UI display
   */
  const languageOptions = computed(() => [
    { value: 'de', title: 'Deutsch', short: 'DE' },
    { value: 'en', title: 'English', short: 'EN' }
  ])

  /**
   * Get the current language option details
   */
  const currentLanguageOption = computed(() => {
    return languageOptions.value.find(opt => opt.value === currentLanguage.value)
  })

  /**
   * Set the application language
   * @param {string} lang - Language code ('de' or 'en')
   */
  const setLanguage = (lang) => {
    if (!SUPPORTED_LANGUAGES.includes(lang)) {
      console.warn(`Invalid language: ${lang}`)
      return
    }

    currentLanguage.value = lang
    locale.value = lang

    // Persist to localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
      } catch (e) {
        // localStorage not available
      }

      // Set HTML lang attribute for accessibility
      document.documentElement.setAttribute('lang', lang)
    }

    console.log(`Language changed to: ${lang}`)
  }

  /**
   * Toggle between German and English
   */
  const toggleLanguage = () => {
    const newLang = currentLanguage.value === 'de' ? 'en' : 'de'
    setLanguage(newLang)
  }

  /**
   * Check if current language matches
   * @param {string} lang - Language code to check
   * @returns {boolean}
   */
  const isLanguage = (lang) => {
    return currentLanguage.value === lang
  }

  return {
    // State
    currentLanguage,
    languageOptions,
    currentLanguageOption,

    // Methods
    setLanguage,
    toggleLanguage,
    isLanguage
  }
}

/**
 * Initialize language on app startup (called from main.js)
 * Sets the HTML lang attribute based on saved preference
 */
export function initLanguage() {
  if (typeof window === 'undefined') return

  // Load saved language preference
  let savedLang = DEFAULT_LANGUAGE
  try {
    const stored = localStorage.getItem(LANGUAGE_STORAGE_KEY)
    if (stored && SUPPORTED_LANGUAGES.includes(stored)) {
      savedLang = stored
    }
  } catch (e) {
    // localStorage not available
  }

  currentLanguage.value = savedLang

  // Set HTML lang attribute for accessibility and SEO
  document.documentElement.setAttribute('lang', savedLang)

  console.log(`Language initialized: ${savedLang}`)
}
