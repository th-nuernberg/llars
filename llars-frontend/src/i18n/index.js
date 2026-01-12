/**
 * Vue I18n Configuration
 * Manages internationalization for the LLARS application
 *
 * @module i18n
 */

import { createI18n } from 'vue-i18n'
import de from '@/locales/de.json'
import en from '@/locales/en.json'

export const LANGUAGE_STORAGE_KEY = 'llars-language'
export const DEFAULT_LANGUAGE = 'de'
export const SUPPORTED_LANGUAGES = ['de', 'en']

/**
 * Get the saved language from localStorage or return default
 * @returns {string} The language code ('de' or 'en')
 */
function getSavedLanguage() {
  if (typeof window === 'undefined') return DEFAULT_LANGUAGE

  try {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY)
    if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
      return saved
    }
  } catch (e) {
    // localStorage not available (e.g., Safari private mode)
  }

  return DEFAULT_LANGUAGE
}

/**
 * Create and configure the i18n instance
 */
export const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: getSavedLanguage(),
  fallbackLocale: DEFAULT_LANGUAGE,
  messages: {
    de,
    en
  },
  // Suppress warnings for missing translations during development
  missingWarn: false,
  fallbackWarn: false
})

export default i18n
