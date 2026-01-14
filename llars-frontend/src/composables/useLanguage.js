/**
 * useLanguage Composable
 * Manages language switching between German and English
 *
 * @module useLanguage
 */

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LANGUAGE_STORAGE_KEY, SUPPORTED_LANGUAGES, getInitialLanguage } from '@/i18n'
import { logI18nParams } from '@/utils/logI18n'

// Shared state (singleton pattern - same as useAppTheme)
const currentLanguage = ref(getInitialLanguage())

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
      logI18nParams('warn', 'logs.language.invalid', { lang })
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

    logI18nParams('log', 'logs.language.changed', { lang })
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

  const savedLang = getInitialLanguage()
  currentLanguage.value = savedLang

  // Set HTML lang attribute for accessibility and SEO
  document.documentElement.setAttribute('lang', savedLang)

  logI18nParams('log', 'logs.language.initialized', { lang: savedLang })
}
