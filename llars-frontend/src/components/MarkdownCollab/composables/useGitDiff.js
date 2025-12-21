/**
 * useGitDiff - Character-level diff comparison against Git baseline
 *
 * Provides PyCharm-like diff highlighting:
 * - Compares current content against the last commit (baseline)
 * - Returns character-level diffs for inline highlighting
 * - Supports gutter markers for deletions
 */

import { ref } from 'vue'
import DiffMatchPatch from 'diff-match-patch'
import axios from 'axios'
import { Decoration } from '@codemirror/view'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

// Diff operation constants from diff-match-patch
const DIFF_DELETE = -1
const DIFF_INSERT = 1
const DIFF_EQUAL = 0

export function useGitDiff() {
  const dmp = new DiffMatchPatch()
  const gitBaseline = ref(null)
  const baselineCommitId = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  function authHeaders() {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  /**
   * Load the baseline content from the last commit
   */
  async function loadBaseline(documentId) {
    if (!documentId) return

    isLoading.value = true
    error.value = null

    try {
      const res = await axios.get(
        `${API_BASE}/api/markdown-collab/documents/${documentId}/baseline`,
        { headers: authHeaders() }
      )

      if (res.data.success) {
        gitBaseline.value = res.data.baseline
        baselineCommitId.value = res.data.commit_id
      } else {
        gitBaseline.value = null
        baselineCommitId.value = null
      }
    } catch (e) {
      console.error('Failed to load baseline:', e)
      error.value = e?.message || 'Failed to load baseline'
      gitBaseline.value = null
      baselineCommitId.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Compute character-level diffs between baseline and current content
   * Returns array of [operation, text] tuples
   */
  function computeCharacterDiffs(currentContent) {
    // No baseline = no diffs (new document without commits)
    if (gitBaseline.value === null || gitBaseline.value === undefined) {
      return []
    }

    const baseline = gitBaseline.value || ''
    const current = currentContent || ''

    // If content is identical to baseline, no diffs
    if (baseline === current) {
      return []
    }

    // Compute character-level diff
    const diffs = dmp.diff_main(baseline, current)

    // Clean up diffs for better readability (merge adjacent edits)
    dmp.diff_cleanupSemantic(diffs)

    return diffs
  }

  /**
   * Convert diffs to CodeMirror decorations for inline highlighting
   * Returns { decorations: Decoration[], deletedLines: Set<number> }
   */
  function diffsToDecorations(diffs, view) {
    if (!diffs || diffs.length === 0 || !view) {
      return { decorations: [], deletedLines: new Set() }
    }

    const decorations = []
    const deletedLines = new Set()
    let currentPos = 0

    for (const [op, text] of diffs) {
      if (op === DIFF_EQUAL) {
        // Unchanged text - just advance position
        currentPos += text.length
      } else if (op === DIFF_INSERT) {
        // Inserted text - highlight with green background
        const from = currentPos
        const to = currentPos + text.length

        // Ensure positions are within document bounds
        const docLen = view.state.doc.length
        const safeFrom = Math.min(from, docLen)
        const safeTo = Math.min(to, docLen)

        if (safeFrom < safeTo) {
          decorations.push(
            Decoration.mark({
              class: 'cm-diff-insert'
            }).range(safeFrom, safeTo)
          )
        }

        currentPos += text.length
      } else if (op === DIFF_DELETE) {
        // Deleted text - mark the line in gutter (text doesn't exist in current doc)
        // Find which line this deletion occurred at
        if (currentPos <= view.state.doc.length) {
          try {
            const line = view.state.doc.lineAt(currentPos)
            deletedLines.add(line.number)
          } catch {
            // Position might be at end of document
            if (view.state.doc.lines > 0) {
              deletedLines.add(view.state.doc.lines)
            }
          }
        }
        // Don't advance currentPos for deletions (text doesn't exist in current)
      }
    }

    return { decorations, deletedLines }
  }

  /**
   * Check if there are any uncommitted changes
   */
  function hasChanges(currentContent) {
    if (gitBaseline.value === null || gitBaseline.value === undefined) {
      return false
    }
    return gitBaseline.value !== currentContent
  }

  /**
   * Get summary of changes for display
   */
  function getChangeSummary(diffs) {
    if (!diffs || diffs.length === 0) {
      return { insertions: 0, deletions: 0, changes: 0 }
    }

    let insertions = 0
    let deletions = 0

    for (const [op, text] of diffs) {
      if (op === DIFF_INSERT) {
        insertions += text.length
      } else if (op === DIFF_DELETE) {
        deletions += text.length
      }
    }

    return {
      insertions,
      deletions,
      changes: insertions + deletions
    }
  }

  /**
   * Update baseline after successful commit
   */
  function updateBaseline(newContent) {
    gitBaseline.value = newContent
  }

  return {
    gitBaseline,
    baselineCommitId,
    isLoading,
    error,
    loadBaseline,
    computeCharacterDiffs,
    diffsToDecorations,
    hasChanges,
    getChangeSummary,
    updateBaseline
  }
}
