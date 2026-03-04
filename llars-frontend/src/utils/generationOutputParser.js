const THINK_BLOCK_REGEX = /<\s*(think|thinking)\s*>([\s\S]*?)<\s*\/\s*\1\s*>/gi
const THINK_TAG_REGEX = /<\s*\/?\s*(think|thinking)\s*>/gi

const normalize = (value = '') => String(value).replace(/\r\n/g, '\n')

export function parseGenerationOutput(rawContent) {
  const text = normalize(rawContent || '')
  if (!text) {
    return {
      visibleContent: '',
      thoughtsContent: '',
      hasThoughts: false
    }
  }

  const thoughtChunks = []

  let visible = text.replace(THINK_BLOCK_REGEX, (_, _tag, inner = '') => {
    const chunk = normalize(inner).trim()
    if (chunk) thoughtChunks.push(chunk)
    return ''
  })

  const danglingOpen = visible.match(/<\s*(think|thinking)\s*>/i)
  if (danglingOpen && typeof danglingOpen.index === 'number') {
    const thoughtTail = normalize(visible.slice(danglingOpen.index).replace(THINK_TAG_REGEX, '')).trim()
    if (thoughtTail) thoughtChunks.push(thoughtTail)
    visible = visible.slice(0, danglingOpen.index)
  }

  visible = normalize(visible.replace(THINK_TAG_REGEX, '')).trim()
  const thoughtsContent = thoughtChunks.join('\n\n').trim()

  return {
    visibleContent: visible,
    thoughtsContent,
    hasThoughts: thoughtsContent.length > 0
  }
}

export function previewGenerationOutput(rawContent, maxLength = 200) {
  const { visibleContent } = parseGenerationOutput(rawContent)
  if (!visibleContent) return ''
  if (visibleContent.length <= maxLength) return visibleContent
  return `${visibleContent.slice(0, Math.max(0, maxLength - 3))}...`
}

