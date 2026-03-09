/**
 * useGitStatus Composable Tests
 *
 * Tests for Git status state management in collab workspaces.
 * Test IDs: GIT_STAT_001 - GIT_STAT_065
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key, params) => `${key}${params ? JSON.stringify(params) : ''}`),
    locale: ref('de')
  }))
}))

// Mock authStorage
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: { token: 'llars_token' },
  getAuthStorageItem: vi.fn(() => 'test-token')
}))

// Mock socketService
const mockSocket = {
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn(),
  connected: false
}
vi.mock('@/services/socketService', () => ({
  getSocket: vi.fn(() => mockSocket)
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

// Mock Vue lifecycle hooks
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import axios from 'axios'

let useGitStatus

describe('useGitStatus', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    mockSocket.on.mockReset()
    mockSocket.off.mockReset()
    mockSocket.emit.mockReset()
    mockSocket.connected = false

    const module = await import('@/composables/useGitStatus')
    useGitStatus = module.useGitStatus
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('GIT_STAT_001: returns all expected state properties', () => {
      const result = useGitStatus(ref(1), { autoSetup: false })
      expect(result).toHaveProperty('changedFiles')
      expect(result).toHaveProperty('deletedFiles')
      expect(result).toHaveProperty('selectedFiles')
      expect(result).toHaveProperty('checkingChanges')
      expect(result).toHaveProperty('loadError')
      expect(result).toHaveProperty('restoringFile')
      expect(result).toHaveProperty('commitMessage')
      expect(result).toHaveProperty('committing')
      expect(result).toHaveProperty('commitError')
      expect(result).toHaveProperty('recentCommits')
      expect(result).toHaveProperty('loadingCommits')
      expect(result).toHaveProperty('rollingBack')
      expect(result).toHaveProperty('showRollbackConfirm')
      expect(result).toHaveProperty('rollbackTarget')
      expect(result).toHaveProperty('forceRollback')
      expect(result).toHaveProperty('forceRollbackDetails')
    })

    it('GIT_STAT_002: returns all expected computed properties', () => {
      const result = useGitStatus(ref(1), { autoSetup: false })
      expect(result).toHaveProperty('changedCount')
      expect(result).toHaveProperty('deletedCount')
      expect(result).toHaveProperty('totalChanges')
      expect(result).toHaveProperty('allSelected')
      expect(result).toHaveProperty('someSelected')
      expect(result).toHaveProperty('totalInsertions')
      expect(result).toHaveProperty('totalDeletions')
      expect(result).toHaveProperty('canSubmitCommit')
    })

    it('GIT_STAT_003: returns all expected methods', () => {
      const result = useGitStatus(ref(1), { autoSetup: false })
      expect(typeof result.formatDate).toBe('function')
      expect(typeof result.getFileIcon).toBe('function')
      expect(typeof result.getFileIconColor).toBe('function')
      expect(typeof result.getStatusBadge).toBe('function')
      expect(typeof result.toggleFile).toBe('function')
      expect(typeof result.selectAll).toBe('function')
      expect(typeof result.deselectAll).toBe('function')
      expect(typeof result.toggleSelectAll).toBe('function')
      expect(typeof result.checkForChanges).toBe('function')
      expect(typeof result.loadRecentCommits).toBe('function')
      expect(typeof result.submitCommit).toBe('function')
      expect(typeof result.quickCommit).toBe('function')
      expect(typeof result.executeRollback).toBe('function')
      expect(typeof result.confirmRollback).toBe('function')
      expect(typeof result.cancelRollback).toBe('function')
      expect(typeof result.restoreFile).toBe('function')
      expect(typeof result.updateFileDiff).toBe('function')
      expect(typeof result.reset).toBe('function')
      expect(typeof result.refresh).toBe('function')
      expect(typeof result.setupSocket).toBe('function')
      expect(typeof result.cleanupSocket).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('GIT_STAT_004: starts with empty changed files', () => {
      const { changedFiles } = useGitStatus(ref(1), { autoSetup: false })
      expect(changedFiles.value).toEqual([])
    })

    it('GIT_STAT_005: starts with empty deleted files', () => {
      const { deletedFiles } = useGitStatus(ref(1), { autoSetup: false })
      expect(deletedFiles.value).toEqual([])
    })

    it('GIT_STAT_006: starts with empty commit message', () => {
      const { commitMessage } = useGitStatus(ref(1), { autoSetup: false })
      expect(commitMessage.value).toBe('')
    })

    it('GIT_STAT_007: entityMode defaults to workspace', () => {
      const { entityMode } = useGitStatus(ref(1), { autoSetup: false })
      expect(entityMode).toBe('workspace')
    })
  })

  // ==================== Computed Properties ====================

  describe('Computed Properties', () => {
    it('GIT_STAT_008: changedCount reflects number of changed files', () => {
      const { changedFiles, changedCount } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]
      expect(changedCount.value).toBe(2)
    })

    it('GIT_STAT_009: deletedCount reflects number of deleted files', () => {
      const { deletedFiles, deletedCount } = useGitStatus(ref(1), { autoSetup: false })
      deletedFiles.value = [{ id: 1 }]
      expect(deletedCount.value).toBe(1)
    })

    it('GIT_STAT_010: totalChanges sums changed and deleted', () => {
      const { changedFiles, deletedFiles, totalChanges } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]
      deletedFiles.value = [{ id: 3 }]
      expect(totalChanges.value).toBe(3)
    })

    it('GIT_STAT_011: allSelected true when all changed files selected', () => {
      const { changedFiles, selectedFiles, allSelected } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]
      selectedFiles.value = [1, 2]
      expect(allSelected.value).toBe(true)
    })

    it('GIT_STAT_012: allSelected false when no files', () => {
      const { allSelected } = useGitStatus(ref(1), { autoSetup: false })
      expect(allSelected.value).toBe(false)
    })

    it('GIT_STAT_013: someSelected true when partial selection', () => {
      const { changedFiles, selectedFiles, someSelected } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }, { id: 3 }]
      selectedFiles.value = [1]
      expect(someSelected.value).toBe(true)
    })

    it('GIT_STAT_014: totalInsertions sums selected file insertions', () => {
      const { changedFiles, selectedFiles, totalInsertions } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [
        { id: 1, insertions: 10 },
        { id: 2, insertions: 5 },
        { id: 3, insertions: 20 }
      ]
      selectedFiles.value = [1, 3]
      expect(totalInsertions.value).toBe(30)
    })

    it('GIT_STAT_015: totalDeletions sums selected file deletions', () => {
      const { changedFiles, selectedFiles, totalDeletions } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [
        { id: 1, deletions: 3 },
        { id: 2, deletions: 7 }
      ]
      selectedFiles.value = [1, 2]
      expect(totalDeletions.value).toBe(10)
    })

    it('GIT_STAT_016: canSubmitCommit requires message and selected files (workspace)', () => {
      const { commitMessage, selectedFiles, canSubmitCommit } = useGitStatus(ref(1), { autoSetup: false })
      expect(canSubmitCommit.value).toBe(false)

      commitMessage.value = 'Fix bugs'
      expect(canSubmitCommit.value).toBe(false)

      selectedFiles.value = [1]
      expect(canSubmitCommit.value).toBe(true)
    })

    it('GIT_STAT_017: canSubmitCommit in single mode checks summary', () => {
      const summary = ref({ hasChanges: true, totalChangedLines: 5 })
      const { commitMessage, canSubmitCommit } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single',
        summary
      })

      commitMessage.value = 'Update'
      expect(canSubmitCommit.value).toBe(true)
    })

    it('GIT_STAT_018: canSubmitCommit false in single mode without changes', () => {
      const summary = ref({ hasChanges: false, totalChangedLines: 0 })
      const { commitMessage, canSubmitCommit } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single',
        summary
      })

      commitMessage.value = 'Update'
      expect(canSubmitCommit.value).toBe(false)
    })
  })

  // ==================== Helper Functions ====================

  describe('Helper Functions', () => {
    it('GIT_STAT_019: getFileIcon returns correct icon for .tex', () => {
      const { getFileIcon } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIcon('document.tex')).toBe('mdi-file-document')
    })

    it('GIT_STAT_020: getFileIcon returns correct icon for .bib', () => {
      const { getFileIcon } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIcon('refs.bib')).toBe('zotero')
    })

    it('GIT_STAT_021: getFileIcon returns default for unknown extension', () => {
      const { getFileIcon } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIcon('file.xyz')).toBe('mdi-file-document-outline')
    })

    it('GIT_STAT_022: getFileIconColor returns green for .tex', () => {
      const { getFileIconColor } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIconColor('document.tex')).toBe('green')
    })

    it('GIT_STAT_023: getFileIconColor returns orange for .sty', () => {
      const { getFileIconColor } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIconColor('style.sty')).toBe('orange')
    })

    it('GIT_STAT_024: getFileIconColor returns purple for .cls', () => {
      const { getFileIconColor } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIconColor('class.cls')).toBe('purple')
    })

    it('GIT_STAT_025: getFileIconColor returns undefined for .bib', () => {
      const { getFileIconColor } = useGitStatus(ref(1), { autoSetup: false })
      expect(getFileIconColor('refs.bib')).toBeUndefined()
    })

    it('GIT_STAT_026: getStatusBadge returns D for deleted files', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'D' })
      expect(badge.text).toBe('D')
      expect(badge.color).toBe('error')
    })

    it('GIT_STAT_027: getStatusBadge returns A for added files', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'A' })
      expect(badge.text).toBe('A')
      expect(badge.color).toBe('info')
    })

    it('GIT_STAT_028: getStatusBadge returns A for files without baseline', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'M', has_baseline: false })
      expect(badge.text).toBe('A')
    })

    it('GIT_STAT_029: getStatusBadge returns M for modified files', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'M', has_baseline: true })
      expect(badge.text).toBe('M')
      expect(badge.color).toBe('warning')
    })

    it('GIT_STAT_030: getStatusBadge returns R for renamed files', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'R', has_baseline: true })
      expect(badge.text).toBe('R')
      expect(badge.color).toBe('purple')
    })

    it('GIT_STAT_031: getStatusBadge returns arrow for moved files', () => {
      const { getStatusBadge } = useGitStatus(ref(1), { autoSetup: false })
      const badge = getStatusBadge({ status: 'V', has_baseline: true })
      expect(badge.text).toBe('\u2192')
      expect(badge.color).toBe('cyan')
    })

    it('GIT_STAT_032: formatDate returns dash for null', () => {
      const { formatDate } = useGitStatus(ref(1), { autoSetup: false })
      expect(formatDate(null)).toBe('\u2014')
    })

    it('GIT_STAT_033: formatDate returns just now for recent date', () => {
      const { formatDate } = useGitStatus(ref(1), { autoSetup: false })
      const justNow = new Date().toISOString()
      const result = formatDate(justNow)
      expect(result).toContain('workspaceGit.relative.justNow')
    })
  })

  // ==================== Selection ====================

  describe('Selection', () => {
    it('GIT_STAT_034: toggleFile adds file to selection', () => {
      const { selectedFiles, toggleFile } = useGitStatus(ref(1), { autoSetup: false })
      toggleFile(1)
      expect(selectedFiles.value).toContain(1)
    })

    it('GIT_STAT_035: toggleFile removes file from selection', () => {
      const { selectedFiles, toggleFile } = useGitStatus(ref(1), { autoSetup: false })
      selectedFiles.value = [1, 2]
      toggleFile(1)
      expect(selectedFiles.value).toEqual([2])
    })

    it('GIT_STAT_036: selectAll selects all changed files', () => {
      const { changedFiles, selectedFiles, selectAll } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }, { id: 3 }]
      selectAll()
      expect(selectedFiles.value).toEqual([1, 2, 3])
    })

    it('GIT_STAT_037: deselectAll clears selection', () => {
      const { selectedFiles, deselectAll } = useGitStatus(ref(1), { autoSetup: false })
      selectedFiles.value = [1, 2, 3]
      deselectAll()
      expect(selectedFiles.value).toEqual([])
    })

    it('GIT_STAT_038: toggleSelectAll selects when true', () => {
      const { changedFiles, selectedFiles, toggleSelectAll } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]
      toggleSelectAll(true)
      expect(selectedFiles.value).toEqual([1, 2])
    })

    it('GIT_STAT_039: toggleSelectAll deselects when false', () => {
      const { selectedFiles, toggleSelectAll } = useGitStatus(ref(1), { autoSetup: false })
      selectedFiles.value = [1, 2]
      toggleSelectAll(false)
      expect(selectedFiles.value).toEqual([])
    })
  })

  // ==================== API Methods ====================

  describe('checkForChanges', () => {
    it('GIT_STAT_040: loads changed files from API', async () => {
      axios.get.mockResolvedValue({
        data: {
          changed_files: [{ id: 1, insertions: 5, deletions: 2 }],
          deleted_files: [{ id: 2 }]
        }
      })

      const { checkForChanges, changedFiles, deletedFiles } = useGitStatus(ref(1), { autoSetup: false })
      await checkForChanges()

      expect(changedFiles.value).toHaveLength(1)
      expect(deletedFiles.value).toHaveLength(1)
    })

    it('GIT_STAT_041: skips API call for single entity mode', async () => {
      const { checkForChanges } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single'
      })
      await checkForChanges()
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('GIT_STAT_042: skips API call when no entityId', async () => {
      const { checkForChanges } = useGitStatus(ref(null), { autoSetup: false })
      await checkForChanges()
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('GIT_STAT_043: handles API error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      const { checkForChanges, loadError, changedFiles } = useGitStatus(ref(1), { autoSetup: false })
      await checkForChanges()

      expect(loadError.value).toBe('Not found')
      expect(changedFiles.value).toEqual([])
    })

    it('GIT_STAT_044: silent mode does not show loading state', async () => {
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const { checkForChanges, checkingChanges } = useGitStatus(ref(1), { autoSetup: false })
      await checkForChanges({ silent: true })

      expect(checkingChanges.value).toBe(false)
    })

    it('GIT_STAT_045: auto-selects new files after check', async () => {
      axios.get.mockResolvedValue({
        data: {
          changed_files: [
            { id: 1, insertions: 5, deletions: 2 },
            { id: 2, insertions: 3, deletions: 1 }
          ],
          deleted_files: []
        }
      })

      const { checkForChanges, selectedFiles } = useGitStatus(ref(1), { autoSetup: false })
      await checkForChanges()

      expect(selectedFiles.value).toContain(1)
      expect(selectedFiles.value).toContain(2)
    })
  })

  describe('loadRecentCommits', () => {
    it('GIT_STAT_046: loads commits in single entity mode', async () => {
      axios.get.mockResolvedValue({
        data: {
          commits: [
            { id: 1, message: 'Initial', author: 'user1', created_at: '2025-01-01' }
          ]
        }
      })

      const { loadRecentCommits, recentCommits } = useGitStatus(ref(10), {
        autoSetup: false,
        entityMode: 'single',
        apiPrefix: '/api/prompts'
      })
      await loadRecentCommits()

      expect(recentCommits.value).toHaveLength(1)
      expect(recentCommits.value[0].author_username).toBe('user1')
    })

    it('GIT_STAT_047: skips when no entityId', async () => {
      const { loadRecentCommits } = useGitStatus(ref(null), { autoSetup: false })
      await loadRecentCommits()
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('GIT_STAT_048: handles commit load error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const { loadRecentCommits, recentCommits } = useGitStatus(ref(1), { autoSetup: false })
      await loadRecentCommits()

      expect(recentCommits.value).toEqual([])
    })
  })

  describe('submitCommit', () => {
    it('GIT_STAT_049: commits selected files in workspace mode', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const { submitCommit, commitMessage, selectedFiles, changedFiles } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]
      selectedFiles.value = [1, 2]
      commitMessage.value = 'Fix issues'

      const result = await submitCommit()

      expect(result).toBe(true)
      expect(axios.post).toHaveBeenCalled()
      expect(commitMessage.value).toBe('')
    })

    it('GIT_STAT_050: returns false when canSubmitCommit is false', async () => {
      const { submitCommit } = useGitStatus(ref(1), { autoSetup: false })
      const result = await submitCommit()
      expect(result).toBe(false)
    })

    it('GIT_STAT_051: calls beforeCommit hook', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const beforeCommit = vi.fn()
      const { submitCommit, commitMessage, selectedFiles, changedFiles } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }]
      selectedFiles.value = [1]
      commitMessage.value = 'Update'

      await submitCommit({ beforeCommit })

      expect(beforeCommit).toHaveBeenCalledWith([1])
    })

    it('GIT_STAT_052: handles commit error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Commit failed' } }
      })

      const { submitCommit, commitMessage, selectedFiles, changedFiles, commitError } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }]
      selectedFiles.value = [1]
      commitMessage.value = 'Update'

      const result = await submitCommit()

      expect(result).toBe(false)
      expect(commitError.value).toBe('Commit failed')
    })

    it('GIT_STAT_053: commits in single entity mode', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({ data: { commits: [] } })

      const summary = ref({ hasChanges: true, totalChangedLines: 5 })
      const getContent = vi.fn(() => 'current content')

      const { submitCommit, commitMessage } = useGitStatus(ref(10), {
        autoSetup: false,
        entityMode: 'single',
        apiPrefix: '/api/prompts',
        summary,
        getContent
      })
      commitMessage.value = 'Save changes'

      const result = await submitCommit()

      expect(result).toBe(true)
      expect(getContent).toHaveBeenCalled()
    })
  })

  describe('quickCommit', () => {
    it('GIT_STAT_054: quick commits all files in workspace mode', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const { quickCommit, changedFiles } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }, { id: 2 }]

      const result = await quickCommit('Auto-commit')

      expect(result).toBe(true)
    })

    it('GIT_STAT_055: returns false with empty message', async () => {
      const { quickCommit } = useGitStatus(ref(1), { autoSetup: false })
      const result = await quickCommit('')
      expect(result).toBe(false)
    })

    it('GIT_STAT_056: returns false with no changed files in workspace mode', async () => {
      const { quickCommit } = useGitStatus(ref(1), { autoSetup: false })
      const result = await quickCommit('Commit')
      expect(result).toBe(false)
    })
  })

  // ==================== Rollback ====================

  describe('Rollback', () => {
    it('GIT_STAT_057: confirmRollback sets target and shows dialog', () => {
      const { confirmRollback, rollbackTarget, showRollbackConfirm } = useGitStatus(ref(1), { autoSetup: false })
      const file = { id: 1, name: 'test.tex' }
      confirmRollback(file)

      expect(rollbackTarget.value).toEqual(file)
      expect(showRollbackConfirm.value).toBe(true)
    })

    it('GIT_STAT_058: cancelRollback clears state', () => {
      const { confirmRollback, cancelRollback, rollbackTarget, showRollbackConfirm } = useGitStatus(ref(1), { autoSetup: false })
      confirmRollback({ id: 1 })
      cancelRollback()

      expect(rollbackTarget.value).toBeNull()
      expect(showRollbackConfirm.value).toBe(false)
    })

    it('GIT_STAT_059: executeRollback returns false without target', async () => {
      const { executeRollback } = useGitStatus(ref(1), { autoSetup: false })
      const result = await executeRollback()
      expect(result).toBe(false)
    })

    it('GIT_STAT_060: executeRollback calls API and returns result', async () => {
      axios.post.mockResolvedValue({ data: { baseline: 'content' } })
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const { confirmRollback, executeRollback } = useGitStatus(ref(1), { autoSetup: false })
      confirmRollback({ id: 5 })
      const result = await executeRollback()

      expect(result).toEqual({ documentId: 5, baseline: 'content' })
    })
  })

  // ==================== Restore ====================

  describe('restoreFile', () => {
    it('GIT_STAT_061: restores a deleted file', async () => {
      axios.post.mockResolvedValue({ data: {} })
      axios.get.mockResolvedValue({
        data: { changed_files: [], deleted_files: [] }
      })

      const { restoreFile } = useGitStatus(ref(1), { autoSetup: false })
      const result = await restoreFile({ id: 3 })

      expect(result).toBe(3)
    })

    it('GIT_STAT_062: returns false for null file', async () => {
      const { restoreFile } = useGitStatus(ref(1), { autoSetup: false })
      const result = await restoreFile(null)
      expect(result).toBe(false)
    })
  })

  // ==================== Real-time Updates ====================

  describe('updateFileDiff', () => {
    it('GIT_STAT_063: updates file diff data', () => {
      const { changedFiles, updateFileDiff } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1, insertions: 5, deletions: 2 }]

      updateFileDiff({ documentId: 1, insertions: 10, deletions: 3 })

      expect(changedFiles.value[0].insertions).toBe(10)
      expect(changedFiles.value[0].deletions).toBe(3)
    })

    it('GIT_STAT_064: ignores update without documentId', () => {
      const { changedFiles, updateFileDiff } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1, insertions: 5 }]

      updateFileDiff({})
      expect(changedFiles.value[0].insertions).toBe(5)
    })
  })

  // ==================== Lifecycle ====================

  describe('Lifecycle', () => {
    it('GIT_STAT_065: reset clears all state', () => {
      const { changedFiles, selectedFiles, commitMessage, recentCommits, reset } = useGitStatus(ref(1), { autoSetup: false })
      changedFiles.value = [{ id: 1 }]
      selectedFiles.value = [1]
      commitMessage.value = 'Test'
      recentCommits.value = [{ id: 1 }]

      reset()

      expect(changedFiles.value).toEqual([])
      expect(selectedFiles.value).toEqual([])
      expect(commitMessage.value).toBe('')
      expect(recentCommits.value).toEqual([])
    })
  })

  // ==================== Single Mode Computed ====================

  describe('Single Mode Computed', () => {
    it('GIT_STAT_066: singleModeHasChanges returns false in workspace mode', () => {
      const { singleModeHasChanges } = useGitStatus(ref(1), { autoSetup: false })
      expect(singleModeHasChanges.value).toBe(false)
    })

    it('GIT_STAT_067: singleModeHasChanges returns true when summary has changes', () => {
      const summary = ref({ hasChanges: true })
      const { singleModeHasChanges } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single',
        summary
      })
      expect(singleModeHasChanges.value).toBe(true)
    })

    it('GIT_STAT_068: singleModeInsertions returns 0 in workspace mode', () => {
      const { singleModeInsertions } = useGitStatus(ref(1), { autoSetup: false })
      expect(singleModeInsertions.value).toBe(0)
    })

    it('GIT_STAT_069: singleModeInsertions returns summary insertions', () => {
      const summary = ref({ insertions: 15 })
      const { singleModeInsertions } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single',
        summary
      })
      expect(singleModeInsertions.value).toBe(15)
    })

    it('GIT_STAT_070: singleModeDeletions returns summary deletions', () => {
      const summary = ref({ deletions: 8 })
      const { singleModeDeletions } = useGitStatus(ref(1), {
        autoSetup: false,
        entityMode: 'single',
        summary
      })
      expect(singleModeDeletions.value).toBe(8)
    })
  })
})
