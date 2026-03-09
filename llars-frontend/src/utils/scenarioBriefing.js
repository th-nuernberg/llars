function asConfigObject(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {}
  }
  return value
}

function getEvalConfig(config) {
  const root = asConfigObject(config)
  const evalConfig = asConfigObject(root.eval_config)
  return asConfigObject(evalConfig.config || evalConfig)
}

export function getLocalizedText(value, locale = 'de') {
  if (!value) return ''
  if (typeof value === 'string') return value.trim()
  if (typeof value !== 'object' || Array.isArray(value)) return ''

  const localized = value[locale]
  if (typeof localized === 'string' && localized.trim()) {
    return localized.trim()
  }

  for (const fallbackKey of ['de', 'en']) {
    const fallback = value[fallbackKey]
    if (typeof fallback === 'string' && fallback.trim()) {
      return fallback.trim()
    }
  }

  for (const entry of Object.values(value)) {
    if (typeof entry === 'string' && entry.trim()) {
      return entry.trim()
    }
  }

  return ''
}

export function setLocalizedText(currentValue, nextValue, locale = 'de') {
  const text = nextValue || ''

  if (currentValue && typeof currentValue === 'object' && !Array.isArray(currentValue)) {
    return {
      ...currentValue,
      [locale]: text
    }
  }

  return {
    de: locale === 'de' ? text : (typeof currentValue === 'string' ? currentValue : ''),
    en: locale === 'en' ? text : (typeof currentValue === 'string' ? currentValue : '')
  }
}

export function criteriaListToMarkdown(criteria, locale = 'de') {
  if (!Array.isArray(criteria) || criteria.length === 0) {
    return ''
  }

  const lines = criteria
    .map((criterion) => {
      if (typeof criterion === 'string') {
        const text = criterion.trim()
        return text ? `- ${text}` : ''
      }

      if (!criterion || typeof criterion !== 'object') {
        return ''
      }

      const name = getLocalizedText(
        criterion.name || criterion.label || criterion.id,
        locale
      )

      if (!name) {
        return ''
      }

      const weight = criterion.weight
      if (typeof weight === 'number' && Number.isFinite(weight) && weight > 0 && weight < 1) {
        return `- ${name} (${Math.round(weight * 100)}%)`
      }

      return `- ${name}`
    })
    .filter(Boolean)

  return lines.join('\n')
}

export function resolveTaskMarkdown(config, locale = 'de') {
  const root = asConfigObject(config)
  const evalConfig = getEvalConfig(root)

  return (
    getLocalizedText(evalConfig.taskDescriptionMarkdown, locale) ||
    getLocalizedText(evalConfig.task_description_markdown, locale) ||
    getLocalizedText(evalConfig.question, locale) ||
    getLocalizedText(root.taskDescriptionMarkdown, locale) ||
    getLocalizedText(root.task_description_markdown, locale) ||
    getLocalizedText(root.task_description, locale) ||
    getLocalizedText(root.description, locale)
  )
}

export function resolveCriteriaMarkdown(config, locale = 'de') {
  const root = asConfigObject(config)
  const evalConfig = getEvalConfig(root)

  return (
    getLocalizedText(evalConfig.criteriaMarkdown, locale) ||
    getLocalizedText(evalConfig.criteria_markdown, locale) ||
    getLocalizedText(root.criteriaMarkdown, locale) ||
    getLocalizedText(root.evaluation_criteria_markdown, locale) ||
    criteriaListToMarkdown(evalConfig.criteria, locale) ||
    criteriaListToMarkdown(root.evaluation_criteria, locale)
  )
}

export function stripMarkdown(markdown = '') {
  if (!markdown) return ''

  return markdown
    .replace(/!\[[^\]]*]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)]\([^)]*\)/g, '$1')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*>+\s?/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/[*_~]/g, '')
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

export function truncateText(text = '', maxLength = 140) {
  if (!text || text.length <= maxLength) {
    return text
  }

  return `${text.slice(0, maxLength - 1).trimEnd()}…`
}
