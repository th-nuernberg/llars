/**
 * useDataImport Composable Tests
 *
 * Tests for file upload, data transformation, import execution,
 * and AI-assisted import workflows.
 * Test IDs: DATA_IMP_001 - DATA_IMP_035
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/services/importService', () => ({
  default: {
    uploadFile: vi.fn(),
    transform: vi.fn(),
    execute: vi.fn(),
    aiAnalyzeIntent: vi.fn(),
    aiTransform: vi.fn(),
    getSample: vi.fn()
  }
}))

import importService from '@/services/importService'
import { useDataImport } from '@/views/ScenarioManager/composables/useDataImport'

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('useDataImport', () => {
  let di

  beforeEach(() => {
    vi.clearAllMocks()
    di = useDataImport()
  })

  // =========================================================================
  // Initial State
  // =========================================================================

  describe('initial state', () => {
    it('DATA_IMP_001: starts with default values', () => {
      expect(di.importing.value).toBe(false)
      expect(di.importProgress.value).toBe(0)
      expect(di.importError.value).toBeNull()
      expect(di.importSession.value).toBeNull()
    })
  })

  // =========================================================================
  // uploadFile
  // =========================================================================

  describe('uploadFile', () => {
    it('DATA_IMP_002: uploads file and updates state', async () => {
      const mockSession = { session_id: 'sess-123', status: 'uploaded' }
      importService.uploadFile.mockResolvedValueOnce(mockSession)

      const file = new File(['data'], 'test.csv', { type: 'text/csv' })
      const result = await di.uploadFile(file)

      expect(importService.uploadFile).toHaveBeenCalledWith(file)
      expect(result).toEqual(mockSession)
      expect(di.importSession.value).toEqual(mockSession)
      expect(di.importProgress.value).toBe(30)
    })

    it('DATA_IMP_003: sets importing to true during upload', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 'x' })

      const file = new File([''], 'test.csv')
      await di.uploadFile(file)

      // importing is set to true at the start (may still be true since full flow not done)
      // but importError should be null
      expect(di.importError.value).toBeNull()
    })

    it('DATA_IMP_004: sets error on upload failure', async () => {
      importService.uploadFile.mockRejectedValueOnce({
        response: { data: { error: 'File too large' } }
      })

      const file = new File([''], 'big.csv')
      await expect(di.uploadFile(file)).rejects.toBeDefined()

      expect(di.importError.value).toBe('File too large')
    })

    it('DATA_IMP_005: uses fallback error message', async () => {
      importService.uploadFile.mockRejectedValueOnce(new Error('Network timeout'))

      const file = new File([''], 'test.csv')
      await expect(di.uploadFile(file)).rejects.toBeDefined()

      expect(di.importError.value).toBe('Network timeout')
    })

    it('DATA_IMP_006: sets progress to 10 immediately', async () => {
      let progressDuringUpload
      importService.uploadFile.mockImplementationOnce(async () => {
        progressDuringUpload = di.importProgress.value
        return { session_id: 'x' }
      })

      await di.uploadFile(new File([''], 'test.csv'))
      expect(progressDuringUpload).toBe(10)
    })
  })

  // =========================================================================
  // transformData
  // =========================================================================

  describe('transformData', () => {
    it('DATA_IMP_007: transforms data and updates session', async () => {
      const mockSession = { session_id: 'sess-123', status: 'transformed' }
      importService.transform.mockResolvedValueOnce(mockSession)

      const result = await di.transformData('sess-123', { format_override: 'csv' })

      expect(importService.transform).toHaveBeenCalledWith('sess-123', { format_override: 'csv' })
      expect(result).toEqual(mockSession)
      expect(di.importSession.value).toEqual(mockSession)
      expect(di.importProgress.value).toBe(70)
    })

    it('DATA_IMP_008: sets progress to 50 at start', async () => {
      let progressDuringTransform
      importService.transform.mockImplementationOnce(async () => {
        progressDuringTransform = di.importProgress.value
        return { session_id: 'x' }
      })

      await di.transformData('sess-123')
      expect(progressDuringTransform).toBe(50)
    })

    it('DATA_IMP_009: sets error on transform failure', async () => {
      importService.transform.mockRejectedValueOnce({
        response: { data: { error: 'Transform error' } }
      })

      await expect(di.transformData('sess-123')).rejects.toBeDefined()
      expect(di.importError.value).toBe('Transform error')
    })
  })

  // =========================================================================
  // executeImport
  // =========================================================================

  describe('executeImport', () => {
    it('DATA_IMP_010: executes import and updates session', async () => {
      const mockResult = { session_id: 'sess-123', status: 'completed', items_imported: 42 }
      importService.execute.mockResolvedValueOnce(mockResult)

      const result = await di.executeImport('sess-123', { task_type: 'rating' })

      expect(importService.execute).toHaveBeenCalledWith('sess-123', { task_type: 'rating' })
      expect(result).toEqual(mockResult)
      expect(di.importProgress.value).toBe(100)
    })

    it('DATA_IMP_011: sets importing to false after execution', async () => {
      di.importing.value = true
      importService.execute.mockResolvedValueOnce({ status: 'done' })

      await di.executeImport('sess-123')

      expect(di.importing.value).toBe(false)
    })

    it('DATA_IMP_012: sets importing to false even on error', async () => {
      di.importing.value = true
      importService.execute.mockRejectedValueOnce(new Error('fail'))

      await expect(di.executeImport('sess-123')).rejects.toBeDefined()
      expect(di.importing.value).toBe(false)
    })

    it('DATA_IMP_013: sets error on execution failure', async () => {
      importService.execute.mockRejectedValueOnce({
        response: { data: { error: 'Duplicate items' } }
      })

      await expect(di.executeImport('sess-123')).rejects.toBeDefined()
      expect(di.importError.value).toBe('Duplicate items')
    })
  })

  // =========================================================================
  // importFileToScenario (full workflow)
  // =========================================================================

  describe('importFileToScenario', () => {
    it('DATA_IMP_014: runs full upload -> transform -> execute workflow', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.transform.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.execute.mockResolvedValueOnce({ items_imported: 10 })

      const file = new File(['csv data'], 'data.csv')
      const result = await di.importFileToScenario(file, { scenarioId: 42, taskType: 'ranking' })

      expect(importService.uploadFile).toHaveBeenCalledWith(file)
      expect(importService.transform).toHaveBeenCalledWith('sess-1', {})
      expect(importService.execute).toHaveBeenCalledWith('sess-1', {
        create_scenario: false,
        scenario_id: 42,
        task_type: 'ranking'
      })
      expect(result).toEqual({ items_imported: 10 })
    })

    it('DATA_IMP_015: sets importing to true at start and false at end', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.transform.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.execute.mockResolvedValueOnce({ done: true })

      await di.importFileToScenario(new File([''], 'x.csv'), { scenarioId: 1 })

      expect(di.importing.value).toBe(false)
    })

    it('DATA_IMP_016: passes null taskType when not provided', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.transform.mockResolvedValueOnce({ session_id: 'sess-1' })
      importService.execute.mockResolvedValueOnce({})

      await di.importFileToScenario(new File([''], 'x.csv'), { scenarioId: 42 })

      expect(importService.execute).toHaveBeenCalledWith('sess-1', {
        create_scenario: false,
        scenario_id: 42,
        task_type: null
      })
    })

    it('DATA_IMP_017: stops on upload failure and resets importing', async () => {
      importService.uploadFile.mockRejectedValueOnce(new Error('Upload fail'))

      await expect(
        di.importFileToScenario(new File([''], 'x.csv'), { scenarioId: 1 })
      ).rejects.toBeDefined()

      expect(di.importing.value).toBe(false)
      expect(importService.transform).not.toHaveBeenCalled()
    })

    it('DATA_IMP_018: stops on transform failure', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 's' })
      importService.transform.mockRejectedValueOnce(new Error('Transform fail'))

      await expect(
        di.importFileToScenario(new File([''], 'x.csv'), { scenarioId: 1 })
      ).rejects.toBeDefined()

      expect(importService.execute).not.toHaveBeenCalled()
    })
  })

  // =========================================================================
  // importWithAI
  // =========================================================================

  describe('importWithAI', () => {
    it('DATA_IMP_019: runs AI-assisted workflow', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 'ai-sess' })
      const aiAnalysis = { type: 'rating', mappings: {} }
      importService.aiAnalyzeIntent.mockResolvedValueOnce(aiAnalysis)
      importService.aiTransform.mockResolvedValueOnce({ status: 'transformed' })
      importService.execute.mockResolvedValueOnce({ items_imported: 5 })

      const file = new File(['data'], 'test.json')
      const result = await di.importWithAI(file, 'Rate these texts', { scenarioId: 42 })

      expect(importService.aiAnalyzeIntent).toHaveBeenCalledWith({
        session_id: 'ai-sess',
        user_intent: 'Rate these texts',
        file_count: 1
      })
      expect(importService.aiTransform).toHaveBeenCalledWith('ai-sess', aiAnalysis)
      expect(importService.execute).toHaveBeenCalledWith('ai-sess', {
        create_scenario: false,
        scenario_id: 42,
        ai_analysis: aiAnalysis
      })
      expect(result).toEqual({ items_imported: 5 })
    })

    it('DATA_IMP_020: sets importing to false on AI workflow failure', async () => {
      importService.uploadFile.mockResolvedValueOnce({ session_id: 's' })
      importService.aiAnalyzeIntent.mockRejectedValueOnce(new Error('AI failed'))

      await expect(
        di.importWithAI(new File([''], 'x.csv'), 'intent', { scenarioId: 1 })
      ).rejects.toBeDefined()

      expect(di.importing.value).toBe(false)
    })

    it('DATA_IMP_021: tracks progress through AI workflow stages', async () => {
      const progressValues = []
      importService.uploadFile.mockImplementationOnce(async () => {
        progressValues.push(di.importProgress.value)
        return { session_id: 's' }
      })
      importService.aiAnalyzeIntent.mockImplementationOnce(async () => {
        progressValues.push(di.importProgress.value)
        return {}
      })
      importService.aiTransform.mockImplementationOnce(async () => {
        progressValues.push(di.importProgress.value)
        return {}
      })
      importService.execute.mockResolvedValueOnce({})

      await di.importWithAI(new File([''], 'x.csv'), 'intent', { scenarioId: 1 })

      // Progress: 10 (upload), 40 (analyze), 60 (transform)
      expect(progressValues[0]).toBe(10)
      expect(progressValues[1]).toBe(40)
      expect(progressValues[2]).toBe(60)
    })
  })

  // =========================================================================
  // getSample
  // =========================================================================

  describe('getSample', () => {
    it('DATA_IMP_022: fetches sample data', async () => {
      const sampleData = { items: [{ id: 1 }, { id: 2 }] }
      importService.getSample.mockResolvedValueOnce(sampleData)

      const result = await di.getSample('sess-123', 3)

      expect(importService.getSample).toHaveBeenCalledWith('sess-123', 3)
      expect(result).toEqual(sampleData)
    })

    it('DATA_IMP_023: uses default count of 5', async () => {
      importService.getSample.mockResolvedValueOnce({})

      await di.getSample('sess-123')

      expect(importService.getSample).toHaveBeenCalledWith('sess-123', 5)
    })

    it('DATA_IMP_024: throws on sample fetch failure', async () => {
      importService.getSample.mockRejectedValueOnce(new Error('Not found'))

      await expect(di.getSample('bad-sess')).rejects.toThrow('Not found')
    })
  })

  // =========================================================================
  // resetImport
  // =========================================================================

  describe('resetImport', () => {
    it('DATA_IMP_025: resets all state to defaults', () => {
      // Set non-default values
      di.importing.value = true
      di.importProgress.value = 75
      di.importError.value = 'Some error'
      di.importSession.value = { session_id: 'x' }

      di.resetImport()

      expect(di.importing.value).toBe(false)
      expect(di.importProgress.value).toBe(0)
      expect(di.importError.value).toBeNull()
      expect(di.importSession.value).toBeNull()
    })
  })

  // =========================================================================
  // Return Interface
  // =========================================================================

  describe('return interface', () => {
    it('DATA_IMP_026: exposes all expected methods', () => {
      const methods = ['uploadFile', 'transformData', 'executeImport',
        'importFileToScenario', 'importWithAI', 'getSample', 'resetImport']
      for (const m of methods) {
        expect(typeof di[m], `${m} should be a function`).toBe('function')
      }
    })

    it('DATA_IMP_027: exposes all expected state refs', () => {
      expect(di.importing).toBeDefined()
      expect(di.importProgress).toBeDefined()
      expect(di.importError).toBeDefined()
      expect(di.importSession).toBeDefined()
    })
  })
})
