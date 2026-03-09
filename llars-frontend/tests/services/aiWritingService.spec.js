/**
 * AI Writing Service Tests
 *
 * Tests for the AI writing assistant API client.
 * Test IDs: SVC_AIW_001 - SVC_AIW_055
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

vi.mock('@/config.js', () => ({
  BASE_URL: ''
}))

vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: {
    token: 'auth_token'
  },
  getAuthStorageItem: vi.fn(() => 'ai-writing-token')
}))

import {
  complete,
  rewrite,
  expand,
  summarize,
  generateAbstract,
  suggestTitles,
  fixLatex,
  chat,
  streamChat,
  executeCommand,
  findCitations,
  reviewCitations,
  ignoreWarning,
  checkHealth
} from '@/services/aiWritingService'

const expectedHeaders = { Authorization: 'Bearer ai-writing-token' }

describe('aiWritingService - Text Completion', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_001: complete sends POST to /api/ai-writing/complete', async () => {
    axios.post.mockResolvedValue({ data: { completion: 'text' } })

    await complete({ context: 'Hello', cursor_position: 5 })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/complete'),
      {
        context: 'Hello',
        cursor_position: 5,
        document_type: 'latex',
        max_tokens: 100,
        temperature: 0.3
      },
      expect.objectContaining({ headers: expectedHeaders, timeout: 60000 })
    )
  })

  it('SVC_AIW_002: complete uses custom document_type', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await complete({ context: 'text', cursor_position: 0, document_type: 'markdown' })

    const body = axios.post.mock.calls[0][1]
    expect(body.document_type).toBe('markdown')
  })

  it('SVC_AIW_003: complete uses custom max_tokens and temperature', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await complete({ context: 'text', cursor_position: 0, max_tokens: 200, temperature: 0.8 })

    const body = axios.post.mock.calls[0][1]
    expect(body.max_tokens).toBe(200)
    expect(body.temperature).toBe(0.8)
  })

  it('SVC_AIW_004: complete returns response data', async () => {
    const responseData = { completion: 'completed text', confidence: 0.9, alternatives: [] }
    axios.post.mockResolvedValue({ data: responseData })

    const result = await complete({ context: 'text', cursor_position: 0 })

    expect(result).toEqual(responseData)
  })
})

describe('aiWritingService - Text Manipulation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_005: rewrite sends POST with default style=academic', async () => {
    axios.post.mockResolvedValue({ data: { result: 'rewritten' } })

    await rewrite({ text: 'some text' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/rewrite'),
      { text: 'some text', style: 'academic', context: '' },
      expect.any(Object)
    )
  })

  it('SVC_AIW_006: rewrite uses custom style', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await rewrite({ text: 'text', style: 'concise' })

    const body = axios.post.mock.calls[0][1]
    expect(body.style).toBe('concise')
  })

  it('SVC_AIW_007: rewrite passes context', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await rewrite({ text: 'text', context: 'surrounding context' })

    const body = axios.post.mock.calls[0][1]
    expect(body.context).toBe('surrounding context')
  })

  it('SVC_AIW_008: expand sends POST with text and default empty context', async () => {
    axios.post.mockResolvedValue({ data: { result: 'expanded' } })

    await expand({ text: 'brief text' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/expand'),
      { text: 'brief text', context: '' },
      expect.any(Object)
    )
  })

  it('SVC_AIW_009: expand passes custom context', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await expand({ text: 'text', context: 'context here' })

    const body = axios.post.mock.calls[0][1]
    expect(body.context).toBe('context here')
  })

  it('SVC_AIW_010: summarize sends POST with text', async () => {
    axios.post.mockResolvedValue({ data: { result: 'summary' } })

    await summarize({ text: 'long text to summarize' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/summarize'),
      { text: 'long text to summarize' },
      expect.any(Object)
    )
  })
})

describe('aiWritingService - Document Operations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_011: generateAbstract sends POST with content', async () => {
    axios.post.mockResolvedValue({ data: { abstract: 'Generated abstract', word_count: 150 } })

    const result = await generateAbstract('Full document content')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/abstract'),
      { content: 'Full document content' },
      expect.any(Object)
    )
    expect(result).toEqual({ abstract: 'Generated abstract', word_count: 150 })
  })

  it('SVC_AIW_012: suggestTitles sends POST with default 5 suggestions', async () => {
    axios.post.mockResolvedValue({ data: { titles: ['Title 1'] } })

    await suggestTitles('document content')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/titles'),
      { content: 'document content', num_suggestions: 5 },
      expect.any(Object)
    )
  })

  it('SVC_AIW_013: suggestTitles uses custom number of suggestions', async () => {
    axios.post.mockResolvedValue({ data: { titles: [] } })

    await suggestTitles('content', 10)

    const body = axios.post.mock.calls[0][1]
    expect(body.num_suggestions).toBe(10)
  })

  it('SVC_AIW_014: fixLatex sends POST with content', async () => {
    axios.post.mockResolvedValue({ data: { errors: [], suggestions: [] } })

    await fixLatex('\\begin{document} text')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/fix-latex'),
      { content: '\\begin{document} text' },
      expect.any(Object)
    )
  })
})

describe('aiWritingService - Chat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_015: chat sends POST with stream=false', async () => {
    axios.post.mockResolvedValue({ data: { response: 'Hello', artifacts: [] } })

    await chat({ message: 'Help me write' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/chat'),
      {
        message: 'Help me write',
        document_content: '',
        history: [],
        stream: false
      },
      expect.any(Object)
    )
  })

  it('SVC_AIW_016: chat passes document content and history', async () => {
    axios.post.mockResolvedValue({ data: {} })

    const history = [{ role: 'user', content: 'Hi' }, { role: 'assistant', content: 'Hello' }]
    await chat({ message: 'Continue', document_content: 'doc text', history })

    const body = axios.post.mock.calls[0][1]
    expect(body.document_content).toBe('doc text')
    expect(body.history).toEqual(history)
  })

  it('SVC_AIW_017: chat defaults document_content and history', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await chat({ message: 'test' })

    const body = axios.post.mock.calls[0][1]
    expect(body.document_content).toBe('')
    expect(body.history).toEqual([])
  })
})

describe('aiWritingService - Stream Chat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_018: streamChat uses native fetch (not axios)', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":"Hello","done":false}\n') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":" world","done":true,"artifacts":[]}\n') })
        .mockResolvedValueOnce({ done: true, value: undefined })
    }

    global.fetch = vi.fn().mockResolvedValue({
      body: { getReader: () => mockReader }
    })

    const onChunk = vi.fn()
    const result = await streamChat({ message: 'Hello' }, onChunk)

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/chat'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ai-writing-token'
        })
      })
    )

    expect(result.response).toBe('Hello world')

    // Clean up
    delete global.fetch
  })

  it('SVC_AIW_019: streamChat sends stream=true in body', async () => {
    const mockReader = {
      read: vi.fn().mockResolvedValueOnce({ done: true, value: undefined })
    }
    global.fetch = vi.fn().mockResolvedValue({
      body: { getReader: () => mockReader }
    })

    await streamChat({ message: 'test' }, vi.fn())

    const fetchBody = JSON.parse(global.fetch.mock.calls[0][1].body)
    expect(fetchBody.stream).toBe(true)

    delete global.fetch
  })

  it('SVC_AIW_020: streamChat calls onChunk for each data chunk', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":"A","done":false}\n') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":"B","done":true,"artifacts":["art"]}\n') })
        .mockResolvedValueOnce({ done: true, value: undefined })
    }
    global.fetch = vi.fn().mockResolvedValue({
      body: { getReader: () => mockReader }
    })

    const onChunk = vi.fn()
    const result = await streamChat({ message: 'test' }, onChunk)

    expect(onChunk).toHaveBeenCalledWith('A', false)
    expect(onChunk).toHaveBeenCalledWith('B', true)
    expect(result.artifacts).toEqual(['art'])

    delete global.fetch
  })

  it('SVC_AIW_021: streamChat handles malformed JSON gracefully', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: not-json\n') })
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":"ok","done":false}\n') })
        .mockResolvedValueOnce({ done: true, value: undefined })
    }
    global.fetch = vi.fn().mockResolvedValue({
      body: { getReader: () => mockReader }
    })

    const onChunk = vi.fn()
    // Should not throw
    const result = await streamChat({ message: 'test' }, onChunk)

    expect(onChunk).toHaveBeenCalledTimes(1)
    expect(result.response).toBe('ok')

    delete global.fetch
  })

  it('SVC_AIW_022: streamChat works without onChunk callback', async () => {
    const mockReader = {
      read: vi.fn()
        .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('data: {"delta":"text","done":false}\n') })
        .mockResolvedValueOnce({ done: true, value: undefined })
    }
    global.fetch = vi.fn().mockResolvedValue({
      body: { getReader: () => mockReader }
    })

    // Should not throw when onChunk is undefined
    const result = await streamChat({ message: 'test' })
    expect(result.response).toBe('text')

    delete global.fetch
  })
})

describe('aiWritingService - Commands', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_023: executeCommand sends POST with command and defaults', async () => {
    axios.post.mockResolvedValue({ data: { response: 'done' } })

    await executeCommand({ command: 'cite' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/command'),
      {
        command: 'cite',
        args: '',
        selected_text: '',
        document_content: ''
      },
      expect.any(Object)
    )
  })

  it('SVC_AIW_024: executeCommand passes all parameters', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await executeCommand({
      command: 'rewrite',
      args: '--style=concise',
      selected_text: 'some text',
      document_content: 'full doc'
    })

    const body = axios.post.mock.calls[0][1]
    expect(body.command).toBe('rewrite')
    expect(body.args).toBe('--style=concise')
    expect(body.selected_text).toBe('some text')
    expect(body.document_content).toBe('full doc')
  })
})

describe('aiWritingService - Citations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_025: findCitations sends POST with defaults', async () => {
    axios.post.mockResolvedValue({ data: { citations: [] } })

    await findCitations({ claim: 'LLMs are effective' })

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/find-citations'),
      {
        claim: 'LLMs are effective',
        context: '',
        collection_ids: [],
        limit: 10,
        format: 'bibtex'
      },
      expect.any(Object)
    )
  })

  it('SVC_AIW_026: findCitations passes custom parameters', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await findCitations({
      claim: 'claim',
      context: 'surrounding text',
      collection_ids: [1, 2],
      limit: 5,
      format: 'apa'
    })

    const body = axios.post.mock.calls[0][1]
    expect(body.context).toBe('surrounding text')
    expect(body.collection_ids).toEqual([1, 2])
    expect(body.limit).toBe(5)
    expect(body.format).toBe('apa')
  })

  it('SVC_AIW_027: reviewCitations sends POST with content', async () => {
    axios.post.mockResolvedValue({ data: { warnings: [], statistics: {} } })

    await reviewCitations('document content here')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/review-citations'),
      { content: 'document content here' },
      expect.any(Object)
    )
  })

  it('SVC_AIW_028: ignoreWarning sends POST with document ID and text', async () => {
    axios.post.mockResolvedValue({ data: { success: true } })

    await ignoreWarning(42, 'warning text')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/ignore-warning'),
      { document_id: 42, text: 'warning text' },
      expect.any(Object)
    )
  })
})

describe('aiWritingService - Health', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_029: checkHealth sends GET to /api/ai-writing/health', async () => {
    axios.get.mockResolvedValue({ data: { status: 'ok', model: 'gpt-4' } })

    const result = await checkHealth()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/ai-writing/health'),
      expect.objectContaining({ headers: expectedHeaders, timeout: 30000 })
    )
    expect(result).toEqual({ status: 'ok', model: 'gpt-4' })
  })
})

describe('aiWritingService - Timeouts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_030: POST operations use 60s timeout', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await complete({ context: 'x', cursor_position: 0 })

    const config = axios.post.mock.calls[0][2]
    expect(config.timeout).toBe(60000)
  })

  it('SVC_AIW_031: GET operations use 30s timeout', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await checkHealth()

    const config = axios.get.mock.calls[0][1]
    expect(config.timeout).toBe(30000)
  })
})

describe('aiWritingService - Auth Headers', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_032: all POST calls include auth headers', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await complete({ context: 'x', cursor_position: 0 })
    await rewrite({ text: 'x' })
    await expand({ text: 'x' })

    for (const call of axios.post.mock.calls) {
      expect(call[2].headers).toEqual(expectedHeaders)
    }
  })

  it('SVC_AIW_033: GET calls include auth headers', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await checkHealth()

    expect(axios.get.mock.calls[0][1].headers).toEqual(expectedHeaders)
  })
})

describe('aiWritingService - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_AIW_034: network errors propagate from POST', async () => {
    axios.post.mockRejectedValue(new Error('Timeout'))

    await expect(complete({ context: 'x', cursor_position: 0 })).rejects.toThrow('Timeout')
  })

  it('SVC_AIW_035: 500 errors propagate', async () => {
    const error = { response: { status: 500 } }
    axios.post.mockRejectedValue(error)

    await expect(rewrite({ text: 'x' })).rejects.toEqual(error)
  })

  it('SVC_AIW_036: 401 errors propagate from GET', async () => {
    const error = { response: { status: 401 } }
    axios.get.mockRejectedValue(error)

    await expect(checkHealth()).rejects.toEqual(error)
  })
})

describe('aiWritingService - Default Export', () => {
  it('SVC_AIW_037: default export contains all functions', async () => {
    const mod = await import('@/services/aiWritingService')
    const defaultExport = mod.default

    expect(defaultExport.complete).toBeDefined()
    expect(defaultExport.rewrite).toBeDefined()
    expect(defaultExport.expand).toBeDefined()
    expect(defaultExport.summarize).toBeDefined()
    expect(defaultExport.generateAbstract).toBeDefined()
    expect(defaultExport.suggestTitles).toBeDefined()
    expect(defaultExport.fixLatex).toBeDefined()
    expect(defaultExport.chat).toBeDefined()
    expect(defaultExport.streamChat).toBeDefined()
    expect(defaultExport.executeCommand).toBeDefined()
    expect(defaultExport.findCitations).toBeDefined()
    expect(defaultExport.reviewCitations).toBeDefined()
    expect(defaultExport.ignoreWarning).toBeDefined()
    expect(defaultExport.checkHealth).toBeDefined()
  })
})
