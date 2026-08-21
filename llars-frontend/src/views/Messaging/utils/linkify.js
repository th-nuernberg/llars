/**
 * URL linkification for chat messages.
 *
 * Detects URLs in plain text and wraps them in <a> tags.
 * Output is sanitized via DOMPurify before rendering (v-html).
 */

const URL_REGEX = /https?:\/\/[^\s<>\[\](){}'",;]+/gi

const TRAILING_PUNCT = /[.,;:!?)]+$/

/**
 * Shorten a URL for display if it exceeds maxLen characters.
 * Keeps the protocol + domain and truncates the path.
 */
function shortenUrl(url, maxLen = 60) {
  if (url.length <= maxLen) return url

  try {
    const parsed = new URL(url)
    const base = parsed.origin
    const rest = url.slice(base.length)
    const available = maxLen - base.length - 3 // 3 for "..."
    if (available <= 0) return base + '/...'
    return base + rest.slice(0, available) + '...'
  } catch {
    return url.slice(0, maxLen - 3) + '...'
  }
}

/**
 * Escape HTML special characters to prevent XSS in non-link text segments.
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Convert URLs in a plain-text message to clickable <a> tags.
 *
 * - Detects http/https URLs
 * - Strips trailing punctuation that's likely not part of the URL
 * - Shortens long display text
 * - Escapes non-link text to prevent XSS
 *
 * The result should still be passed through sanitizeHtml() before v-html.
 *
 * @param {string} text - Raw message content (plain text)
 * @returns {string} HTML string with URLs wrapped in <a> tags
 */
export function linkifyMessage(text) {
  if (!text) return ''

  const parts = []
  let lastIndex = 0

  // Reset regex state
  URL_REGEX.lastIndex = 0

  let match
  while ((match = URL_REGEX.exec(text)) !== null) {
    let url = match[0]
    const matchStart = match.index

    // Add text before this URL (escaped)
    if (matchStart > lastIndex) {
      parts.push(escapeHtml(text.slice(lastIndex, matchStart)))
    }

    // Strip trailing punctuation that's likely sentence-ending, not part of URL
    let trailingChars = ''
    const trailingMatch = url.match(TRAILING_PUNCT)
    if (trailingMatch) {
      // Don't strip if it looks like part of the URL path (e.g. closing paren in Wikipedia URLs)
      const openParens = (url.match(/\(/g) || []).length
      const closeParens = (url.match(/\)/g) || []).length
      if (closeParens > openParens) {
        // Strip only the excess closing parens and any trailing punct
        const excess = trailingMatch[0]
        url = url.slice(0, -excess.length)
        trailingChars = excess
      } else if (!url.includes('(') || !trailingMatch[0].startsWith(')')) {
        url = url.slice(0, -trailingMatch[0].length)
        trailingChars = trailingMatch[0]
      }
    }

    const displayText = escapeHtml(shortenUrl(url))
    parts.push(
      `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="message-link">${displayText}</a>`
    )

    if (trailingChars) {
      parts.push(escapeHtml(trailingChars))
    }

    lastIndex = matchStart + match[0].length
  }

  // Add remaining text after last URL
  if (lastIndex < text.length) {
    parts.push(escapeHtml(text.slice(lastIndex)))
  }

  return parts.join('')
}
