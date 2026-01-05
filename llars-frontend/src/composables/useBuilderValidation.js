/**
 * Chatbot Builder Validation Composable
 *
 * Provides validation rules and helper functions for the chatbot builder wizard.
 */

export function useBuilderValidation() {
  const FALLBACK_URL = 'https://www.dg-agentur.de/'
  const SCHEME_REGEX = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//

  const getEffectiveUrl = (value) => {
    if (!value || !value.trim()) return ''
    const trimmed = value.trim()
    if (SCHEME_REGEX.test(trimmed)) {
      return trimmed
    }
    return FALLBACK_URL
  }

  // Validation rules
  const rules = {
    required: v => !!(v && v.trim()) || 'Pflichtfeld',
    url: v => {
      if (!v || !v.trim()) return true
      const trimmed = v.trim()
      if (!SCHEME_REGEX.test(trimmed)) return true
      try {
        const parsedUrl = new URL(trimmed)
        if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
          return 'URL muss mit http:// oder https:// beginnen'
        }
        return true
      } catch {
        return 'Ungültige URL'
      }
    }
  }

  // Helper functions
  const formatDuration = (seconds) => {
    if (!seconds) return '0s'
    if (seconds < 60) return `${Math.round(seconds)}s`
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}m ${secs}s`
  }

  const extractPageTitle = (url) => {
    try {
      const urlObj = new URL(url)
      const path = urlObj.pathname
      if (path === '/' || path === '') return urlObj.hostname
      return path.split('/').filter(Boolean).pop() || urlObj.hostname
    } catch {
      return url
    }
  }

  const validateUrl = (url) => {
    if (!url || !url.trim()) {
      return { valid: false, error: 'URL ist erforderlich' }
    }
    try {
      const parsedUrl = new URL(getEffectiveUrl(url))
      if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
        return { valid: false, error: 'URL muss mit http:// oder https:// beginnen' }
      }
      return { valid: true, error: null }
    } catch {
      return { valid: false, error: 'Ungültige URL' }
    }
  }

  const validateConfig = (config) => {
    const errors = {}

    if (!config.name) {
      errors.name = 'Interner Name ist erforderlich'
    }

    if (!config.displayName) {
      errors.displayName = 'Anzeigename ist erforderlich'
    }

    if (!config.systemPrompt) {
      errors.systemPrompt = 'System Prompt ist erforderlich'
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors
    }
  }

  return {
    rules,
    formatDuration,
    extractPageTitle,
    validateUrl,
    validateConfig
  }
}

export default useBuilderValidation
