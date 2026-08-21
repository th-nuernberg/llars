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

// getSystemLanguage helper removed — see getInitialLanguage above.
// LLARS defaults to DE for new visitors; users opt into EN explicitly.

/**
 * Get the saved language from localStorage or fall back to the default.
 *
 * LLARS defaults to German for any new visitor — the platform's home
 * country, the source language of all study material, and what the
 * outreach mails are written in. Browser-language sniffing is
 * intentionally skipped: an EN-browser user who lands on a DE study
 * link should see DE first and switch manually if desired (saved to
 * localStorage for next visits).
 *
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

  return DEFAULT_LANGUAGE
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
