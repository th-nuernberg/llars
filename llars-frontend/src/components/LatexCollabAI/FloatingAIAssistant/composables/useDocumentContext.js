/**
 * useDocumentContext - Extract context from LaTeX documents
 *
 * Provides reactive document context via regex extraction:
 * - Title, author, abstract
 * - Sections with line numbers
 * - Current section based on cursor position
 * - Document class, packages
 */

import { ref, computed, watch } from 'vue'

// LaTeX regex patterns
const PATTERNS = {
  title: /\\title\s*(?:\[[^\]]*\])?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}/,
  author: /\\author\s*(?:\[[^\]]*\])?\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}/,
  abstract: /\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}/,
  documentClass: /\\documentclass(?:\[[^\]]*\])?\{([^}]*)\}/,
  usePackage: /\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}/g,
  section: /\\(section|subsection|subsubsection|chapter)\*?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}/g,
  label: /\\label\{([^}]*)\}/g,
  cite: /\\cite(?:\[[^\]]*\])?\{([^}]*)\}/g
}

export function useDocumentContext(editorRef) {
  // State
  const content = ref('')
  const cursorLine = ref(0)
  const selectionText = ref('')
  const selectionRange = ref({ from: 0, to: 0 })
  const fileName = ref('')

  // Extracted data
  const title = computed(() => {
    const match = content.value.match(PATTERNS.title)
    return match ? cleanLatexBraces(match[1]) : ''
  })

  const author = computed(() => {
    const match = content.value.match(PATTERNS.author)
    return match ? cleanLatexBraces(match[1]) : ''
  })

  const abstract = computed(() => {
    const match = content.value.match(PATTERNS.abstract)
    return match ? match[1].trim() : ''
  })

  const documentClass = computed(() => {
    const match = content.value.match(PATTERNS.documentClass)
    return match ? match[1] : ''
  })

  const packages = computed(() => {
    const pkgs = []
    let match
    const regex = new RegExp(PATTERNS.usePackage.source, 'g')
    while ((match = regex.exec(content.value)) !== null) {
      pkgs.push(...match[1].split(',').map(p => p.trim()))
    }
    return pkgs
  })

  const sections = computed(() => {
    const result = []
    let match
    const regex = new RegExp(PATTERNS.section.source, 'g')
    const lines = content.value.split('\n')

    while ((match = regex.exec(content.value)) !== null) {
      const level = getSectionLevel(match[1])
      const title = cleanLatexBraces(match[2])
      const lineNumber = getLineNumber(content.value, match.index)

      result.push({
        level,
        type: match[1],
        title,
        line: lineNumber,
        index: match.index
      })
    }

    return result
  })

  const currentSection = computed(() => {
    if (sections.value.length === 0) return null

    // Find the section that contains the current cursor line
    let current = null
    for (const section of sections.value) {
      if (section.line <= cursorLine.value) {
        current = section
      } else {
        break
      }
    }

    return current
  })

  const wordCount = computed(() => {
    // Remove LaTeX commands and count words
    const text = content.value
      .replace(/\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?/g, ' ')
      .replace(/[{}\\]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()

    return text ? text.split(/\s+/).length : 0
  })

  const citations = computed(() => {
    const cites = new Set()
    let match
    const regex = new RegExp(PATTERNS.cite.source, 'g')
    while ((match = regex.exec(content.value)) !== null) {
      match[1].split(',').forEach(c => cites.add(c.trim()))
    }
    return Array.from(cites)
  })

  // Full context object for API calls
  const context = computed(() => ({
    title: title.value,
    author: author.value,
    abstract: abstract.value,
    documentClass: documentClass.value,
    packages: packages.value,
    sections: sections.value,
    currentSection: currentSection.value,
    cursorLine: cursorLine.value,
    selection: {
      text: selectionText.value,
      from: selectionRange.value.from,
      to: selectionRange.value.to,
      hasSelection: selectionText.value.length > 0
    },
    wordCount: wordCount.value,
    citations: citations.value,
    fileName: fileName.value
  }))

  // Helper functions
  function cleanLatexBraces(text) {
    // Remove nested braces but keep content
    return text.replace(/\{([^{}]*)\}/g, '$1').trim()
  }

  function getSectionLevel(type) {
    switch (type) {
      case 'chapter': return 0
      case 'section': return 1
      case 'subsection': return 2
      case 'subsubsection': return 3
      default: return 1
    }
  }

  function getLineNumber(text, index) {
    return text.substring(0, index).split('\n').length
  }

  // Update functions (called by parent component)
  function updateContent(newContent) {
    content.value = newContent || ''
  }

  function updateCursor(line) {
    cursorLine.value = line
  }

  function updateSelection(text, from, to) {
    selectionText.value = text || ''
    selectionRange.value = { from: from || 0, to: to || 0 }
  }

  function updateFileName(name) {
    fileName.value = name || ''
  }

  // Find element positions in document
  function findTitlePosition() {
    const match = content.value.match(PATTERNS.title)
    if (match) {
      return {
        from: match.index,
        to: match.index + match[0].length,
        content: match[0]
      }
    }
    return null
  }

  function findAbstractPosition() {
    const match = content.value.match(PATTERNS.abstract)
    if (match) {
      return {
        from: match.index,
        to: match.index + match[0].length,
        contentFrom: match.index + '\\begin{abstract}'.length,
        contentTo: match.index + match[0].length - '\\end{abstract}'.length,
        content: match[1].trim()
      }
    }
    return null
  }

  function findSectionPosition(sectionTitle) {
    const section = sections.value.find(s => s.title === sectionTitle)
    if (section) {
      // Find the full section command
      const searchStart = Math.max(0, section.index - 50)
      const searchText = content.value.substring(searchStart, section.index + 200)
      const sectionPattern = new RegExp(
        `\\\\${section.type}\\*?\\s*(?:\\[[^\\]]*\\])?\\s*\\{[^}]*${escapeRegex(sectionTitle)}[^}]*\\}`
      )
      const match = searchText.match(sectionPattern)
      if (match) {
        return {
          from: searchStart + match.index,
          to: searchStart + match.index + match[0].length,
          content: match[0]
        }
      }
    }
    return null
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  }

  return {
    // Reactive state
    content,
    cursorLine,
    selectionText,
    selectionRange,
    fileName,

    // Computed context
    title,
    author,
    abstract,
    documentClass,
    packages,
    sections,
    currentSection,
    wordCount,
    citations,
    context,

    // Update methods
    updateContent,
    updateCursor,
    updateSelection,
    updateFileName,

    // Position finders
    findTitlePosition,
    findAbstractPosition,
    findSectionPosition
  }
}

export default useDocumentContext
