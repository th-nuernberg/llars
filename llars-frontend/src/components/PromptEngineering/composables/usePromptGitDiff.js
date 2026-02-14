/**
 * usePromptGitDiff - Track changes for Prompt Engineering Git versioning
 *
 * Provides:
 * - Change tracking for prompt blocks
 * - User contribution summary
 * - Baseline comparison
 */

import { ref, computed } from 'vue'
import DiffMatchPatch from 'diff-match-patch'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

// Diff operation constants from diff-match-patch
const DIFF_DELETE = -1
const DIFF_INSERT = 1

export function usePromptGitDiff(promptId, users = {}) {
  const dmp = new DiffMatchPatch()
  const baseline = ref(null) // Last committed snapshot
  const baselineCommitId = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Track user changes since last baseline load
  const userChanges = ref({}) // { username: { color, changedLines: number } }

  function authHeaders() {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  /**
   * Load the baseline content from the last commit
   */
  async function loadBaseline(id = null) {
    const promptIdVal = id || promptId.value
    if (!promptIdVal) return

    isLoading.value = true
    error.value = null

    try {
      const res = await axios.get(
        `${API_BASE}/api/prompts/${promptIdVal}/baseline`,
        { headers: authHeaders() }
      )

      if (res.data.success && res.data.baseline) {
        baseline.value = res.data.baseline.content_snapshot
        baselineCommitId.value = res.data.baseline.commit_id
      } else {
        baseline.value = null
        baselineCommitId.value = null
      }
      // Reset user changes after loading new baseline
      userChanges.value = {}
    } catch (e) {
      console.error('Failed to load prompt baseline:', e)
      error.value = e?.message || 'Failed to load baseline'
      baseline.value = null
      baselineCommitId.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Compute the diff summary between baseline and current content
   */
  function computeDiffSummary(currentContent) {
    const baselineContent = baseline.value ?? ''
    const current = currentContent || ''

    if (baselineContent === current) {
      return { insertions: 0, deletions: 0, hasChanges: false, totalChangedLines: 0 }
    }

    const diffs = dmp.diff_main(baselineContent, current)
    dmp.diff_cleanupSemantic(diffs)

    let insertions = 0
    let deletions = 0

    for (const [op, text] of diffs) {
      if (op === DIFF_INSERT) {
        // Count lines inserted
        insertions += (text.match(/\n/g) || []).length + (text.length > 0 ? 1 : 0)
      } else if (op === DIFF_DELETE) {
        // Count lines deleted
        deletions += (text.match(/\n/g) || []).length + (text.length > 0 ? 1 : 0)
      }
    }

    return {
      insertions,
      deletions,
      hasChanges: insertions > 0 || deletions > 0,
      totalChangedLines: insertions + deletions
    }
  }

  /**
   * Track a user's change contribution
   */
  function trackUserChange(username, color, linesChanged = 1) {
    if (!username) return

    if (!userChanges.value[username]) {
      userChanges.value[username] = { color: color || '#9e9e9e', changedLines: 0 }
    }
    userChanges.value[username].changedLines += linesChanged
    if (color) {
      userChanges.value[username].color = color
    }
  }

  /**
   * Get the full change summary for commits
   */
  function getChangeSummary(currentContent) {
    const diff = computeDiffSummary(currentContent)

    // Convert userChanges to array format
    const usersArray = Object.entries(userChanges.value).map(([username, data]) => ({
      username,
      color: data.color,
      changedLines: data.changedLines
    }))

    return {
      ...diff,
      users: usersArray
    }
  }

  /**
   * Check if there are uncommitted changes
   */
  function hasChanges(currentContent) {
    if (baseline.value === null || baseline.value === undefined) {
      return (currentContent || '').length > 0
    }
    return baseline.value !== (currentContent || '')
  }

  /**
   * Update baseline after successful commit
   */
  function updateBaseline(newContent) {
    baseline.value = newContent
    userChanges.value = {} // Reset tracking
  }

  /**
   * Reset tracking (e.g., after commit)
   */
  function resetTracking() {
    userChanges.value = {}
  }

  /**
   * Compute per-block character diffs between baseline and current content.
   * Returns { blockTitle: { insertions: N, deletions: N, isNew?: bool, isDeleted?: bool } }
   */
  function computeBlockCharDiffs(currentContentJson) {
    let baselineObj, currentObj
    try {
      baselineObj = baseline.value ? JSON.parse(baseline.value) : {}
      currentObj = JSON.parse(currentContentJson || '{}')
    } catch {
      return {}
    }

    const result = {}
    const allKeys = new Set([...Object.keys(baselineObj), ...Object.keys(currentObj)])

    for (const title of allKeys) {
      const inBaseline = title in baselineObj
      const inCurrent = title in currentObj
      const oldText = baselineObj[title] || ''
      const newText = currentObj[title] || ''

      const isNew = !inBaseline && inCurrent
      const isDeleted = inBaseline && !inCurrent

      if (oldText === newText && !isNew && !isDeleted) {
        result[title] = { insertions: 0, deletions: 0 }
        continue
      }

      const diffs = dmp.diff_main(oldText, newText)
      dmp.diff_cleanupSemantic(diffs)

      let ins = 0
      let del = 0
      for (const [op, text] of diffs) {
        if (op === DIFF_INSERT) ins += text.length
        else if (op === DIFF_DELETE) del += text.length
      }

      result[title] = { insertions: ins, deletions: del, ...(isNew && { isNew: true }), ...(isDeleted && { isDeleted: true }) }
    }

    return result
  }

  return {
    baseline,
    baselineCommitId,
    isLoading,
    error,
    userChanges,
    loadBaseline,
    computeDiffSummary,
    computeBlockCharDiffs,
    trackUserChange,
    getChangeSummary,
    hasChanges,
    updateBaseline,
    resetTracking
  }
}
