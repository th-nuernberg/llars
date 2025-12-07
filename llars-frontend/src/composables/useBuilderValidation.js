/**
 * Chatbot Builder Validation Composable
 *
 * Provides validation rules and helper functions for the chatbot builder wizard.
 */

export function useBuilderValidation() {
  // Validation rules
  const rules = {
    required: v => !!v || 'Pflichtfeld',
    url: v => {
      if (!v) return true
      try {
        new URL(v)
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
    if (!url) {
      return { valid: false, error: 'URL ist erforderlich' }
    }
    try {
      new URL(url)
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
