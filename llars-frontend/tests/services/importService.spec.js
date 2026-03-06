/**
 * Import Service Tests
 *
 * Tests for the LLARS data import wizard API client.
 * Test IDs: SVC_IMP_001 - SVC_IMP_050
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

import importService from '@/services/importService'

describe('importService - Format & Upload', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_001: getFormats sends GET to /api/import/formats', async () => {
    axios.get.mockResolvedValue({ data: { formats: ['csv', 'json'] } })

    const result = await importService.getFormats()

    expect(axios.get).toHaveBeenCalledWith('/api/import/formats')
    expect(result).toEqual({ formats: ['csv', 'json'] })
  })

  it('SVC_IMP_002: uploadFile sends POST with FormData and multipart header', async () => {
    const file = new File(['content'], 'test.csv', { type: 'text/csv' })
    axios.post.mockResolvedValue({ data: { session_id: 'abc123' } })

    const result = await importService.uploadFile(file)

    expect(axios.post).toHaveBeenCalledWith(
      '/api/import/upload',
      expect.any(FormData),
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    expect(result).toEqual({ session_id: 'abc123' })
  })

  it('SVC_IMP_003: uploadFile appends file to FormData', async () => {
    const file = new File(['data'], 'data.json')
    axios.post.mockResolvedValue({ data: {} })

    await importService.uploadFile(file)

    const formData = axios.post.mock.calls[0][1]
    expect(formData).toBeInstanceOf(FormData)
    expect(formData.get('file')).toBeTruthy()
  })
})

describe('importService - Session Management', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_004: getSession sends GET with session ID', async () => {
    axios.get.mockResolvedValue({ data: { status: 'active' } })

    const result = await importService.getSession('sess-1')

    expect(axios.get).toHaveBeenCalledWith('/api/import/session/sess-1')
    expect(result).toEqual({ status: 'active' })
  })

  it('SVC_IMP_005: getSample sends GET with default count=5', async () => {
    axios.get.mockResolvedValue({ data: { items: [] } })

    await importService.getSample('sess-1')

    expect(axios.get).toHaveBeenCalledWith('/api/import/session/sess-1/sample', {
      params: { count: 5 }
    })
  })

  it('SVC_IMP_006: getSample sends GET with custom count', async () => {
    axios.get.mockResolvedValue({ data: { items: [] } })

    await importService.getSample('sess-1', 10)

    expect(axios.get).toHaveBeenCalledWith('/api/import/session/sess-1/sample', {
      params: { count: 10 }
    })
  })

  it('SVC_IMP_007: deleteSession sends DELETE with session ID', async () => {
    axios.delete.mockResolvedValue({ data: { deleted: true } })

    const result = await importService.deleteSession('sess-1')

    expect(axios.delete).toHaveBeenCalledWith('/api/import/session/sess-1')
    expect(result).toEqual({ deleted: true })
  })
})

describe('importService - Transform & Validate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_008: transform sends POST with session_id and default options', async () => {
    axios.post.mockResolvedValue({ data: { success: true } })

    await importService.transform('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/transform', {
      session_id: 'sess-1',
      options: {}
    })
  })

  it('SVC_IMP_009: transform sends POST with custom options', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await importService.transform('sess-1', { format: 'csv', delimiter: ';' })

    expect(axios.post).toHaveBeenCalledWith('/api/import/transform', {
      session_id: 'sess-1',
      options: { format: 'csv', delimiter: ';' }
    })
  })

  it('SVC_IMP_010: validate sends POST with session_id', async () => {
    axios.post.mockResolvedValue({ data: { valid: true } })

    const result = await importService.validate('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/validate', {
      session_id: 'sess-1'
    })
    expect(result).toEqual({ valid: true })
  })
})

describe('importService - Execute Import', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_011: execute sends POST with session_id and default options', async () => {
    axios.post.mockResolvedValue({ data: { imported: 10 } })

    await importService.execute('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/execute', {
      session_id: 'sess-1'
    })
  })

  it('SVC_IMP_012: execute sends POST with additional options spread', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await importService.execute('sess-1', { scenario_id: 5, overwrite: true })

    expect(axios.post).toHaveBeenCalledWith('/api/import/execute', {
      session_id: 'sess-1',
      scenario_id: 5,
      overwrite: true
    })
  })

  it('SVC_IMP_013: execute returns response data', async () => {
    const responseData = { imported: 42, scenario_id: 7 }
    axios.post.mockResolvedValue({ data: responseData })

    const result = await importService.execute('sess-1')

    expect(result).toEqual(responseData)
  })
})

describe('importService - AI-Assisted Endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_014: aiAnalyze sends POST with session_id', async () => {
    axios.post.mockResolvedValue({ data: { analysis: {} } })

    await importService.aiAnalyze('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/analyze', {
      session_id: 'sess-1'
    })
  })

  it('SVC_IMP_015: aiAnalyzeIntent sends POST with full params', async () => {
    const params = {
      session_id: 'sess-1',
      user_intent: 'Compare two summaries',
      file_count: 2
    }
    axios.post.mockResolvedValue({ data: { type: 'comparison' } })

    await importService.aiAnalyzeIntent(params)

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/analyze-intent', params)
  })

  it('SVC_IMP_016: aiTransform sends POST with session_id and ai_analysis', async () => {
    const aiAnalysis = { type: 'rating', field_mapping: {} }
    axios.post.mockResolvedValue({ data: {} })

    await importService.aiTransform('sess-1', aiAnalysis)

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/transform', {
      session_id: 'sess-1',
      ai_analysis: aiAnalysis
    })
  })

  it('SVC_IMP_017: aiTransformScript sends POST with default empty field hints', async () => {
    axios.post.mockResolvedValue({ data: { script: 'code' } })

    await importService.aiTransformScript('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/transform-script', {
      session_id: 'sess-1',
      field_hints: {}
    })
  })

  it('SVC_IMP_018: aiTransformScript sends POST with custom field hints', async () => {
    const hints = { content_field: 'text_column' }
    axios.post.mockResolvedValue({ data: {} })

    await importService.aiTransformScript('sess-1', hints)

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/transform-script', {
      session_id: 'sess-1',
      field_hints: hints
    })
  })

  it('SVC_IMP_019: aiSuggest sends POST with default empty mapping', async () => {
    axios.post.mockResolvedValue({ data: { suggestions: [] } })

    await importService.aiSuggest('sess-1')

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/suggest', {
      session_id: 'sess-1',
      current_mapping: {}
    })
  })

  it('SVC_IMP_020: aiSuggest sends POST with custom mapping', async () => {
    const mapping = { title: 'col_a', content: 'col_b' }
    axios.post.mockResolvedValue({ data: {} })

    await importService.aiSuggest('sess-1', mapping)

    expect(axios.post).toHaveBeenCalledWith('/api/import/ai/suggest', {
      session_id: 'sess-1',
      current_mapping: mapping
    })
  })
})

describe('importService - Chat Stream Helpers', () => {
  it('SVC_IMP_021: getChatStreamUrl returns correct endpoint', () => {
    const url = importService.getChatStreamUrl()
    expect(url).toBe('/api/import/ai/chat-stream')
  })

  it('SVC_IMP_022: buildChatStreamBody returns JSON string', () => {
    const body = importService.buildChatStreamBody('sess-1', [{ role: 'user', content: 'Hello' }])

    const parsed = JSON.parse(body)
    expect(parsed.session_id).toBe('sess-1')
    expect(parsed.messages).toHaveLength(1)
    expect(parsed.messages[0]).toEqual({ role: 'user', content: 'Hello' })
    expect(parsed.current_config).toEqual({})
  })

  it('SVC_IMP_023: buildChatStreamBody includes current config', () => {
    const config = { format: 'csv', delimiter: ',' }
    const body = importService.buildChatStreamBody('sess-1', [], config)

    const parsed = JSON.parse(body)
    expect(parsed.current_config).toEqual(config)
  })

  it('SVC_IMP_024: buildChatStreamBody maps messages to role/content only', () => {
    const messages = [
      { role: 'user', content: 'Hello', extra_field: 'ignored' },
      { role: 'assistant', content: 'Hi there', timestamp: '2026-01-01' }
    ]
    const body = importService.buildChatStreamBody('sess-1', messages)

    const parsed = JSON.parse(body)
    expect(parsed.messages[0]).toEqual({ role: 'user', content: 'Hello' })
    expect(parsed.messages[1]).toEqual({ role: 'assistant', content: 'Hi there' })
    expect(parsed.messages[0].extra_field).toBeUndefined()
  })
})

describe('importService - importFromData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_025: importFromData sends POST with required params', async () => {
    const data = [{ text: 'item 1' }]
    axios.post.mockResolvedValue({ data: { imported: 1 } })

    await importService.importFromData(data, 5, 'rating')

    expect(axios.post).toHaveBeenCalledWith('/api/import/from-data', {
      data,
      scenario_id: 5,
      task_type: 'rating',
      source_name: 'Wizard Import'
    })
  })

  it('SVC_IMP_026: importFromData uses custom source name', async () => {
    const data = [{ text: 'item' }]
    axios.post.mockResolvedValue({ data: {} })

    await importService.importFromData(data, 5, 'ranking', 'Custom Source')

    expect(axios.post).toHaveBeenCalledWith('/api/import/from-data', {
      data,
      scenario_id: 5,
      task_type: 'ranking',
      source_name: 'Custom Source'
    })
  })

  it('SVC_IMP_027: importFromData includes field_mapping when provided', async () => {
    const data = [{ text: 'item' }]
    const fieldMapping = { content: 'text', label: 'title' }
    axios.post.mockResolvedValue({ data: {} })

    await importService.importFromData(data, 5, 'rating', 'Import', fieldMapping)

    expect(axios.post).toHaveBeenCalledWith('/api/import/from-data', {
      data,
      scenario_id: 5,
      task_type: 'rating',
      source_name: 'Import',
      field_mapping: fieldMapping
    })
  })

  it('SVC_IMP_028: importFromData omits field_mapping when null', async () => {
    const data = [{ text: 'item' }]
    axios.post.mockResolvedValue({ data: {} })

    await importService.importFromData(data, 5, 'rating', 'Import', null)

    const payload = axios.post.mock.calls[0][1]
    expect(payload).not.toHaveProperty('field_mapping')
  })

  it('SVC_IMP_029: importFromData returns response data', async () => {
    const responseData = { imported: 5, scenario_id: 10 }
    axios.post.mockResolvedValue({ data: responseData })

    const result = await importService.importFromData([], 10, 'comparison')

    expect(result).toEqual(responseData)
  })
})

describe('importService - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_IMP_030: getFormats rejects on network error', async () => {
    axios.get.mockRejectedValue(new Error('Network Error'))

    await expect(importService.getFormats()).rejects.toThrow('Network Error')
  })

  it('SVC_IMP_031: uploadFile rejects on 413 payload too large', async () => {
    const error = { response: { status: 413 } }
    axios.post.mockRejectedValue(error)

    await expect(importService.uploadFile(new File(['x'], 'big.csv'))).rejects.toEqual(error)
  })

  it('SVC_IMP_032: execute rejects on 422 validation error', async () => {
    const error = { response: { status: 422 } }
    axios.post.mockRejectedValue(error)

    await expect(importService.execute('sess-1')).rejects.toEqual(error)
  })
})
