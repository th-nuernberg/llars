/**
 * Web Worker for instant regex-based entity preview.
 * Provides immediate feedback while the real NER model processes in the background.
 *
 * This is a PREVIEW only - results are approximate and will be replaced
 * by the actual NER model results when available.
 */

// German regex patterns for common entity types
const PATTERNS = {
  // Email addresses
  EMAIL: {
    regex: /[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}/g,
    label: 'EMAIL'
  },
  // German phone numbers (various formats)
  PHONE: {
    regex: /(?:\+49|0049|0)\s*(?:\d{2,4}[-\s]?)?\d{3,}[-\s]?\d{2,}/g,
    label: 'PHONE'
  },
  // Dates in German format (DD.MM.YYYY or DD/MM/YYYY)
  DATE: {
    regex: /\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b/g,
    label: 'DATE'
  },
  // German postal codes (5 digits)
  PLZ: {
    regex: /\b\d{5}\b/g,
    label: 'PLZ'
  },
  // Time (HH:MM or HH:MM:SS)
  TIME: {
    regex: /\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:Uhr)?\b/gi,
    label: 'TIME'
  },
  // German social security number (Sozialversicherungsnummer)
  SVN: {
    regex: /\b\d{2}\s*\d{6}\s*[A-Z]\s*\d{3}\b/g,
    label: 'SVN'
  },
  // Swiss AHV number
  AHV: {
    regex: /\b756\.\d{4}\.\d{4}\.\d{2}\b/g,
    label: 'AHV'
  },
  // IBAN
  IBAN: {
    regex: /\b[A-Z]{2}\d{2}\s*(?:\d{4}\s*){4,7}\d{0,2}\b/g,
    label: 'IBAN'
  },
  // URLs
  URL: {
    regex: /https?:\/\/[^\s<>"{}|\\^`[\]]+/gi,
    label: 'URL'
  },
  // Street addresses (German/Swiss)
  STREET: {
    regex: /\b[A-ZÄÖÜ][a-zäöüß]+(?:straße|strasse|str\.|gasse|weg|platz|allee|ring)\s*\d+\s*[a-zA-Z]?\b/gi,
    label: 'STREET'
  }
}

// Simple name pattern (capitalized words that might be names)
// This is very approximate - real NER is needed for accuracy
const NAME_PATTERN = {
  // Matches "Frau/Herr Lastname" or "Firstname Lastname" patterns
  regex: /\b(?:(?:Frau|Herr|Dr\.|Prof\.)\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+){1,2}\b/g,
  label: 'PER'
}

/**
 * Find all regex matches in text
 */
function findMatches(text) {
  const entities = []
  let idCounter = 0

  // Find pattern-based entities
  for (const [type, { regex, label }] of Object.entries(PATTERNS)) {
    // Reset regex lastIndex
    regex.lastIndex = 0
    let match
    while ((match = regex.exec(text)) !== null) {
      entities.push({
        id: `preview_${idCounter++}`,
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
        label,
        type,
        isPreview: true
      })
    }
  }

  // Find potential names (less reliable, marked as preview)
  NAME_PATTERN.regex.lastIndex = 0
  let nameMatch
  while ((nameMatch = NAME_PATTERN.regex.exec(text)) !== null) {
    // Skip if it overlaps with an existing entity
    const start = nameMatch.index
    const end = start + nameMatch[0].length
    const overlaps = entities.some(e =>
      (start >= e.start && start < e.end) ||
      (end > e.start && end <= e.end) ||
      (start <= e.start && end >= e.end)
    )
    if (!overlaps) {
      entities.push({
        id: `preview_${idCounter++}`,
        start,
        end,
        text: nameMatch[0],
        label: 'PER',
        type: 'NAME',
        isPreview: true
      })
    }
  }

  // Sort by start position
  entities.sort((a, b) => a.start - b.start)

  // Remove overlapping entities (keep the first/longest)
  const filtered = []
  let lastEnd = -1
  for (const ent of entities) {
    if (ent.start >= lastEnd) {
      filtered.push(ent)
      lastEnd = ent.end
    }
  }

  return filtered
}

/**
 * Group entities by their text (for replacement mapping)
 */
function groupEntities(entities) {
  const groupMap = new Map()

  for (const ent of entities) {
    const key = `${ent.label}:${ent.text.toLowerCase()}`
    if (!groupMap.has(key)) {
      groupMap.set(key, {
        group_id: `preview_group_${groupMap.size}`,
        label: ent.label,
        original: ent.text,
        replacement: `[${ent.label}]`,
        count: 0,
        mode: 'preview',
        isPreview: true
      })
    }
    const group = groupMap.get(key)
    group.count++
    ent.group_id = group.group_id
  }

  return Array.from(groupMap.values())
}

/**
 * Generate preview output text
 */
function generateOutput(text, entities, groups) {
  const groupMap = new Map(groups.map(g => [g.group_id, g]))

  let output = ''
  let cursor = 0
  let offset = 0

  for (const ent of entities) {
    const group = groupMap.get(ent.group_id)
    const replacement = group ? group.replacement : ent.text

    output += text.slice(cursor, ent.start)
    ent.output_start = ent.start + offset
    ent.output_end = ent.output_start + replacement.length
    output += replacement
    offset += replacement.length - (ent.end - ent.start)
    cursor = ent.end
  }
  output += text.slice(cursor)

  return output
}

// Handle messages from main thread
self.onmessage = function(e) {
  const { type, text, requestId } = e.data

  if (type === 'analyze') {
    try {
      const entities = findMatches(text)
      const groups = groupEntities(entities)
      const outputText = generateOutput(text, entities, groups)

      self.postMessage({
        type: 'result',
        requestId,
        entities,
        groups,
        outputText,
        isPreview: true
      })
    } catch (error) {
      self.postMessage({
        type: 'error',
        requestId,
        error: error.message
      })
    }
  }
}
