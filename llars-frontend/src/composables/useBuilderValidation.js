/**
 * Chatbot Builder Validation Composable
 *
 * Provides validation rules and helper functions for the chatbot builder wizard.
 */

export function useBuilderValidation() {
  const isValidHttpUrl = (value) => {
    if (typeof value !== 'string') return false
    const trimmed = value.trim()
    if (!trimmed) return false
    try {
      const parsedUrl = new URL(trimmed)
      return ['http:', 'https:'].includes(parsedUrl.protocol)
    } catch {
      return false
    }
  }

  // Validation rules
  const rules = {
    required: v => {
      if (v === null || v === undefined) return 'Pflichtfeld'
      if (typeof v === 'string') return v.length > 0 || 'Pflichtfeld'
      if (typeof v === 'number') return v !== 0 || 'Pflichtfeld'
      if (typeof v === 'boolean') return v || 'Pflichtfeld'
      if (Array.isArray(v)) return v.length > 0 || 'Pflichtfeld'
      if (typeof v === 'object') return Object.keys(v).length > 0 || 'Pflichtfeld'
      return v ? true : 'Pflichtfeld'
    },
    url: v => {
      if (v === null || v === undefined || v === '') return true
      if (typeof v !== 'string') return 'Ungültige URL'
      const trimmed = v.trim()
      if (!trimmed) return true
      return isValidHttpUrl(trimmed) || 'Ungültige URL'
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
    if (typeof url !== 'string' || !url.trim()) {
      return { valid: false, error: 'URL ist erforderlich' }
    }
    try {
      return isValidHttpUrl(url) ? { valid: true, error: null } : { valid: false, error: 'Ungültige URL' }
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
