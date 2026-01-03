/**
 * useLatexOutline.js
 *
 * Composable for document outline/structure in LaTeX workspace.
 * Parses LaTeX sections, chapters, etc. and provides navigation.
 */

import { ref, computed, onUnmounted } from 'vue'

const OUTLINE_COLLAPSED_KEY = 'latex-outline-collapsed'

// LaTeX sectioning command levels
const outlineCommandLevels = {
  part: { level: 0, label: 'Teil' },
  chapter: { level: 1, label: 'Kapitel' },
  section: { level: 2, label: 'Abschnitt' },
  subsection: { level: 3, label: 'Unterabschnitt' },
  subsubsection: { level: 4, label: 'Unter-Unterabschnitt' },
  paragraph: { level: 5, label: 'Paragraph' }
}

// Regex pattern to match LaTeX sectioning commands
const outlinePattern = /\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*(?:\[[^\]]*])?\s*\{([^}]*)\}/g

/**
 * Build hierarchical outline from LaTeX text
 * @param {string} text - LaTeX document text
 * @returns {Array} Hierarchical outline items
 */
export function buildOutline(text) {
  if (!text) return []
  const items = []
  const stack = []
  const lines = text.split('\n')
  const lineStarts = []
  let offset = 0
  for (const line of lines) {
    lineStarts.push(offset)
    offset += line.length + 1
  }

  outlinePattern.lastIndex = 0
  let match = outlinePattern.exec(text)
  let lineIndex = 0
  while (match) {
    const matchIndex = match.index
    while (lineIndex + 1 < lineStarts.length && lineStarts[lineIndex + 1] <= matchIndex) {
      lineIndex += 1
    }
    const line = lines[lineIndex] || ''
    const trimmed = line.trim()
    if (trimmed && !trimmed.startsWith('%')) {
      const colIndex = matchIndex - lineStarts[lineIndex]
      const leading = line.slice(0, Math.max(0, colIndex))
      if (!leading.includes('%')) {
        const cmd = match[1]
        const meta = outlineCommandLevels[cmd] || { level: 9, label: cmd }
        const title = (match[2] || '').trim() || meta.label
        const item = {
          id: `${cmd}:${lineIndex + 1}:${title}`,
          title,
          line: lineIndex + 1,
          level: meta.level,
          children: []
        }

        while (stack.length && stack[stack.length - 1].level >= item.level) {
          stack.pop()
        }
        if (stack.length) {
          stack[stack.length - 1].children.push(item)
        } else {
          items.push(item)
        }
        stack.push(item)
      }
    }
    match = outlinePattern.exec(text)
  }

  return items
}

/**
 * Create LaTeX outline composable
 * @param {Object} options - Configuration options
 * @param {Ref<Object>} options.selectedNode - Currently selected document node
 * @param {Ref<Object>} options.editorRef - Editor component ref
 * @returns {Object} Composable state and methods
 */
export function useLatexOutline({
  selectedNode,
  editorRef
}) {
  // State
  // Default to collapsed unless user explicitly expanded it before
  const outlineCollapsed = ref(localStorage.getItem(OUTLINE_COLLAPSED_KEY) !== 'false')
  const outlineItems = ref([])
  const outlineCollapsedIds = ref(new Set())

  // Timer for debounced updates
  let outlineUpdateTimer = null
  let lastOutlineText = ''

  // Computed: Flattened items with collapse state
  const outlineFlatItems = computed(() => {
    const items = []
    const collapsed = outlineCollapsedIds.value
    const walk = (nodes, depth) => {
      for (const node of nodes) {
        const hasChildren = Array.isArray(node.children) && node.children.length > 0
        items.push({ ...node, depth, hasChildren })
        if (hasChildren && !collapsed.has(node.id)) {
          walk(node.children, depth + 1)
        }
      }
    }
    walk(outlineItems.value || [], 0)
    return items
  })

  // Computed: Empty label based on document state
  const outlineEmptyLabel = computed(() => {
    if (selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id) {
      return 'Keine Kapitel gefunden'
    }
    return 'Kein Dokument'
  })

  // Methods
  function toggleOutlineCollapsed() {
    outlineCollapsed.value = !outlineCollapsed.value
    localStorage.setItem(OUTLINE_COLLAPSED_KEY, outlineCollapsed.value ? 'true' : 'false')
  }

  function isOutlineItemCollapsed(id) {
    return outlineCollapsedIds.value.has(id)
  }

  function toggleOutlineItem(id) {
    const next = new Set(outlineCollapsedIds.value)
    if (next.has(id)) {
      next.delete(id)
    } else {
      next.add(id)
    }
    outlineCollapsedIds.value = next
  }

  function updateOutline(text) {
    if (text === lastOutlineText) return
    lastOutlineText = text
    const nextItems = buildOutline(text)
    outlineItems.value = nextItems

    // Clean up collapsed IDs for items that no longer exist
    const validIds = new Set()
    const collect = (nodes) => {
      for (const node of nodes) {
        validIds.add(node.id)
        if (node.children?.length) collect(node.children)
      }
    }
    collect(nextItems)

    if (outlineCollapsedIds.value.size) {
      const next = new Set()
      outlineCollapsedIds.value.forEach((id) => {
        if (validIds.has(id)) next.add(id)
      })
      outlineCollapsedIds.value = next
    }
  }

  function scheduleOutlineUpdate(text) {
    if (outlineUpdateTimer) clearTimeout(outlineUpdateTimer)
    outlineUpdateTimer = setTimeout(() => {
      updateOutline(text)
    }, 200)
  }

  function jumpToOutlineItem(item) {
    if (!item?.line) return
    editorRef.value?.jumpToLine?.(item.line, 1)
  }

  function resetOutline() {
    outlineItems.value = []
    outlineCollapsedIds.value = new Set()
    lastOutlineText = ''
  }

  // Cleanup
  onUnmounted(() => {
    if (outlineUpdateTimer) clearTimeout(outlineUpdateTimer)
  })

  return {
    // State
    outlineCollapsed,
    outlineItems,
    outlineCollapsedIds,

    // Computed
    outlineFlatItems,
    outlineEmptyLabel,

    // Methods
    toggleOutlineCollapsed,
    isOutlineItemCollapsed,
    toggleOutlineItem,
    updateOutline,
    scheduleOutlineUpdate,
    jumpToOutlineItem,
    resetOutline
  }
}
