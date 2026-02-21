/**
 * Vue I18n Configuration
 * Manages internationalization for the LLARS application
 *
 * @module i18n
 */

import { createI18n } from 'vue-i18n'
import de from '@/locales/de.json'
import en from '@/locales/en.json'
import logDe from '@/locales/logs.de.json'
import logEn from '@/locales/logs.en.json'

export const LANGUAGE_STORAGE_KEY = 'llars-language'
export const DEFAULT_LANGUAGE = 'de'
export const SUPPORTED_LANGUAGES = ['de', 'en']

/**
 * Detect a supported language from the browser settings.
 * @returns {string|null} The language code ('de' or 'en') or null
 */
function getSystemLanguage() {
  if (typeof navigator === 'undefined') return null

  const candidates = Array.isArray(navigator.languages) && navigator.languages.length > 0
    ? navigator.languages
    : [navigator.language]

  for (const lang of candidates) {
    if (!lang) continue
    const code = String(lang).toLowerCase().split('-')[0]
    if (SUPPORTED_LANGUAGES.includes(code)) {
      return code
    }
  }

  return null
}

/**
 * Get the saved language from localStorage or fall back to system/default.
 * @returns {string} The language code ('de' or 'en')
 */
export function getInitialLanguage() {
  if (typeof window !== 'undefined') {
    try {
      const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY)
      if (saved && SUPPORTED_LANGUAGES.includes(saved)) {
        return saved
      }
    } catch (e) {
      // localStorage not available (e.g., Safari private mode)
    }
  }

  return getSystemLanguage() || DEFAULT_LANGUAGE
}

/**
 * Create and configure the i18n instance
 */
export const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: getInitialLanguage(),
  fallbackLocale: DEFAULT_LANGUAGE,
  messages: {
    de: { ...de, logs: logDe },
    en: { ...en, logs: logEn }
  },
  // Suppress warnings for missing translations during development
  missingWarn: false,
  fallbackWarn: false
})

export default i18n
