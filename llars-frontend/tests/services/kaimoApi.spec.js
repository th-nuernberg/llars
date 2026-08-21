/**
 * Kaimo API Service Tests
 *
 * Tests for the Kaimo case management API client.
 * Test IDs: SVC_KAI_001 - SVC_KAI_060
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: {
    token: 'auth_token'
  },
  getAuthStorageItem: vi.fn(() => 'test-token-123')
}))

import {
  getKaimoCases,
  getKaimoCase,
  createKaimoCase,
  publishKaimoCase,
  exportKaimoCase,
  importKaimoCase,
  updateKaimoCase,
  deleteKaimoCase,
  getKaimoCaseAdmin,
  getKaimoAdminCases,
  createKaimoDocument,
  updateKaimoDocument,
  deleteKaimoDocument,
  createKaimoHint,
  updateKaimoHint,
  deleteKaimoHint,
  getKaimoCaseResults,
  getKaimoCategories,
  startKaimoAssessment,
  getKaimoAssessment,
  saveHintAssignment,
  completeAssessment,
  getKaimoUserCategories,
  shareKaimoCase,
  unshareKaimoCase,
  getKaimoCaseShares
} from '@/services/kaimoApi'

const expectedHeaders = { Authorization: 'Bearer test-token-123' }

describe('kaimoApi - User Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_001: getKaimoCases sends GET to /api/kaimo/cases with auth header', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getKaimoCases()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_002: getKaimoCases returns response data', async () => {
    const cases = [{ id: 1, name: 'Case 1' }]
    axios.get.mockResolvedValue({ data: cases })

    const result = await getKaimoCases()

    expect(result).toEqual(cases)
  })

  it('SVC_KAI_003: getKaimoCase sends GET with case ID', async () => {
    axios.get.mockResolvedValue({ data: { id: 5 } })

    await getKaimoCase(5)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases/5'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_004: getKaimoCase returns unwrapped data', async () => {
    const caseData = { id: 5, name: 'Test Case' }
    axios.get.mockResolvedValue({ data: caseData })

    const result = await getKaimoCase(5)

    expect(result).toEqual(caseData)
  })
})

describe('kaimoApi - Admin Cases', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_005: createKaimoCase sends POST to admin endpoint', async () => {
    const payload = { name: 'New Case', description: 'Test' }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await createKaimoCase(payload)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_006: publishKaimoCase sends POST with empty body', async () => {
    axios.post.mockResolvedValue({ data: { published: true } })

    await publishKaimoCase(3)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/3/publish'),
      {},
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_007: updateKaimoCase sends PUT with payload', async () => {
    const payload = { name: 'Updated' }
    axios.put.mockResolvedValue({ data: { id: 3 } })

    await updateKaimoCase(3, payload)

    expect(axios.put).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/3'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_008: deleteKaimoCase sends DELETE without force', async () => {
    axios.delete.mockResolvedValue({ data: { success: true } })

    await deleteKaimoCase(3)

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/3'),
      { headers: expectedHeaders }
    )
    expect(axios.delete.mock.calls[0][0]).not.toContain('force')
  })

  it('SVC_KAI_009: deleteKaimoCase sends DELETE with force=true', async () => {
    axios.delete.mockResolvedValue({ data: { success: true } })

    await deleteKaimoCase(3, true)

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/3?force=true'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_010: getKaimoCaseAdmin sends GET to admin case endpoint', async () => {
    axios.get.mockResolvedValue({ data: { id: 3 } })

    await getKaimoCaseAdmin(3)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/3'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_011: getKaimoAdminCases sends GET to admin cases list', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getKaimoAdminCases()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Export/Import', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_012: exportKaimoCase without assessments omits param', async () => {
    axios.get.mockResolvedValue({ data: { export: {} } })

    await exportKaimoCase(3)

    const url = axios.get.mock.calls[0][0]
    expect(url).toContain('/api/kaimo/admin/cases/3/export')
    expect(url).not.toContain('include_assessments')
  })

  it('SVC_KAI_013: exportKaimoCase with assessments adds query param', async () => {
    axios.get.mockResolvedValue({ data: { export: {} } })

    await exportKaimoCase(3, true)

    const url = axios.get.mock.calls[0][0]
    expect(url).toContain('include_assessments=true')
  })

  it('SVC_KAI_014: importKaimoCase sends POST with export data', async () => {
    const exportData = { case: { id: 1 } }
    axios.post.mockResolvedValue({ data: { id: 2 } })

    await importKaimoCase(exportData)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/import'),
      {
        export: exportData,
        name_override: null,
        status_override: null,
        publish: false
      },
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_015: importKaimoCase passes override options', async () => {
    const exportData = { case: { id: 1 } }
    axios.post.mockResolvedValue({ data: { id: 2 } })

    await importKaimoCase(exportData, {
      nameOverride: 'New Name',
      statusOverride: 'draft',
      publish: true
    })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/import'),
      {
        export: exportData,
        name_override: 'New Name',
        status_override: 'draft',
        publish: true
      },
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Documents', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_016: createKaimoDocument sends POST to case documents endpoint', async () => {
    const payload = { title: 'Doc', content: 'text' }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await createKaimoDocument(5, payload)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/documents'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_017: updateKaimoDocument sends PUT with case and doc IDs', async () => {
    const payload = { content: 'updated' }
    axios.put.mockResolvedValue({ data: { id: 10 } })

    await updateKaimoDocument(5, 10, payload)

    expect(axios.put).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/documents/10'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_018: deleteKaimoDocument sends DELETE with case and doc IDs', async () => {
    axios.delete.mockResolvedValue({ data: { success: true } })

    await deleteKaimoDocument(5, 10)

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/documents/10'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Hints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_019: createKaimoHint sends POST to case hints endpoint', async () => {
    const payload = { text: 'Hint text' }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await createKaimoHint(5, payload)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/hints'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_020: updateKaimoHint sends PUT with case and hint IDs', async () => {
    const payload = { text: 'Updated hint' }
    axios.put.mockResolvedValue({ data: { id: 20 } })

    await updateKaimoHint(5, 20, payload)

    expect(axios.put).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/hints/20'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_021: deleteKaimoHint sends DELETE with case and hint IDs', async () => {
    axios.delete.mockResolvedValue({ data: { success: true } })

    await deleteKaimoHint(5, 20)

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/hints/20'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Results & Categories', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_022: getKaimoCaseResults sends GET with case ID', async () => {
    axios.get.mockResolvedValue({ data: { results: [] } })

    await getKaimoCaseResults(5)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/cases/5/results'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_023: getKaimoCategories sends GET to admin categories', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getKaimoCategories()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/admin/categories'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Assessment Workflow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_024: startKaimoAssessment sends POST with empty body', async () => {
    axios.post.mockResolvedValue({ data: { assessment_id: 1 } })

    await startKaimoAssessment(5)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases/5/start'),
      {},
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_025: getKaimoAssessment sends GET with assessment ID', async () => {
    axios.get.mockResolvedValue({ data: { id: 10 } })

    await getKaimoAssessment(10)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/assessments/10'),
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_026: saveHintAssignment sends PUT with assessment and hint IDs', async () => {
    const payload = { assigned: true, note: 'Test' }
    axios.put.mockResolvedValue({ data: { success: true } })

    await saveHintAssignment(10, 3, payload)

    expect(axios.put).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/assessments/10/hints/3'),
      payload,
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_027: completeAssessment sends POST with payload', async () => {
    const payload = { verdict: 'guilty' }
    axios.post.mockResolvedValue({ data: { completed: true } })

    await completeAssessment(10, payload)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/assessments/10/complete'),
      payload,
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - User Categories', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_028: getKaimoUserCategories sends GET to user categories', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getKaimoUserCategories()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/categories'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Sharing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_029: shareKaimoCase sends POST with shared_with username', async () => {
    axios.post.mockResolvedValue({ data: { success: true } })

    await shareKaimoCase(5, 'evaluator')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases/5/share'),
      { shared_with: 'evaluator' },
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_030: unshareKaimoCase sends POST with unshare_with username', async () => {
    axios.post.mockResolvedValue({ data: { success: true } })

    await unshareKaimoCase(5, 'evaluator')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases/5/unshare'),
      { unshare_with: 'evaluator' },
      { headers: expectedHeaders }
    )
  })

  it('SVC_KAI_031: getKaimoCaseShares sends GET to shares endpoint', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getKaimoCaseShares(5)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/kaimo/cases/5/shares'),
      { headers: expectedHeaders }
    )
  })
})

describe('kaimoApi - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_032: getKaimoCases rejects on network error', async () => {
    axios.get.mockRejectedValue(new Error('Network Error'))

    await expect(getKaimoCases()).rejects.toThrow('Network Error')
  })

  it('SVC_KAI_033: createKaimoCase rejects on 400 bad request', async () => {
    const error = { response: { status: 400, data: { message: 'Invalid' } } }
    axios.post.mockRejectedValue(error)

    await expect(createKaimoCase({})).rejects.toEqual(error)
  })

  it('SVC_KAI_034: deleteKaimoCase rejects on 403 forbidden', async () => {
    const error = { response: { status: 403 } }
    axios.delete.mockRejectedValue(error)

    await expect(deleteKaimoCase(1)).rejects.toEqual(error)
  })
})

describe('kaimoApi - Data Unwrapping', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_KAI_035: all functions return res.data (not full response)', async () => {
    const innerData = { id: 1, name: 'Test' }
    axios.get.mockResolvedValue({ data: innerData })
    axios.post.mockResolvedValue({ data: innerData })

    const getResult = await getKaimoCases()
    expect(getResult).toEqual(innerData)

    const postResult = await createKaimoCase({})
    expect(postResult).toEqual(innerData)
  })
})
