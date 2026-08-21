/**
 * Sprachabhängige MkDocs-Doku-URLs.
 *
 * Die Doku existiert zweisprachig (mkdocs-static-i18n): Deutsch ist die
 * Standard-/Primärsprache und liegt unter /mkdocs/, Englisch unter /mkdocs/en/.
 * Beim Öffnen aus LLARS soll die zur aktuellen UI-Sprache passende Version
 * geöffnet werden; INNERHALB von MkDocs kann die Sprache weiterhin über den
 * eigenen Sprachumschalter gewechselt werden.
 */

/**
 * Basispfad der Doku für eine gegebene Locale ('de' | 'en' | ...).
 * Alles außer Englisch fällt auf die deutsche Standardsprache zurück.
 */
export function docsBasePathForLocale(locale) {
  return String(locale || 'de').startsWith('en') ? '/mkdocs/en/' : '/mkdocs/'
}

/**
 * Vollständige Doku-URL (mit Origin) für eine gegebene Locale, optional mit
 * angehängtem Unterpfad (z.B. 'entwickler/evaluation-datenformate/').
 */
export function docsUrlForLocale(locale, subPath = '') {
  const base = docsBasePathForLocale(locale)
  const clean = String(subPath || '').replace(/^\/+/, '')
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return `${origin}${base}${clean}`
}
