/**
 * Pipeline API Service Tests
 *
 * Tests for the automated LLM evaluation pipeline API client.
 * Test IDs: SVC_PIPE_001 - SVC_PIPE_035
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

import { pipelineApi } from '@/services/pipelineApi'

describe('pipelineApi - Run Management', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_001: createRun sends POST to /api/pipeline/runs', async () => {
    const data = {
      name: 'Pipeline Test',
      config: { iterations: 3 },
      candidate_models: ['gpt-4', 'claude-3'],
      auto_start: true
    }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await pipelineApi.createRun(data)

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs', data)
  })

  it('SVC_PIPE_002: getRuns sends GET with default empty params', async () => {
    axios.get.mockResolvedValue({ data: { runs: [] } })

    await pipelineApi.getRuns()

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs', { params: {} })
  })

  it('SVC_PIPE_003: getRuns sends GET with filter params', async () => {
    axios.get.mockResolvedValue({ data: { runs: [] } })

    await pipelineApi.getRuns({ status: 'completed', limit: 10 })

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs', {
      params: { status: 'completed', limit: 10 }
    })
  })

  it('SVC_PIPE_004: getRun sends GET with run ID', async () => {
    axios.get.mockResolvedValue({ data: { id: 42 } })

    await pipelineApi.getRun(42)

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/42')
  })

  it('SVC_PIPE_005: deleteRun sends DELETE with run ID', async () => {
    axios.delete.mockResolvedValue({ data: { deleted: true } })

    await pipelineApi.deleteRun(42)

    expect(axios.delete).toHaveBeenCalledWith('/api/pipeline/runs/42')
  })
})

describe('pipelineApi - Lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_006: startRun sends POST to /api/pipeline/runs/{id}/start', async () => {
    axios.post.mockResolvedValue({ data: { status: 'running' } })

    await pipelineApi.startRun(5)

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/start')
  })

  it('SVC_PIPE_007: pauseRun sends POST to /api/pipeline/runs/{id}/pause', async () => {
    axios.post.mockResolvedValue({ data: { status: 'paused' } })

    await pipelineApi.pauseRun(5)

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/pause')
  })

  it('SVC_PIPE_008: cancelRun sends POST to /api/pipeline/runs/{id}/cancel', async () => {
    axios.post.mockResolvedValue({ data: { status: 'cancelled' } })

    await pipelineApi.cancelRun(5)

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/cancel')
  })

  it('SVC_PIPE_009: submitReview sends POST with decision payload', async () => {
    axios.post.mockResolvedValue({ data: { status: 'deployed' } })

    await pipelineApi.submitReview(5, 'deploy')

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/review', {
      decision: 'deploy'
    })
  })

  it('SVC_PIPE_010: submitReview supports continue decision', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await pipelineApi.submitReview(5, 'continue')

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/review', {
      decision: 'continue'
    })
  })

  it('SVC_PIPE_011: submitReview supports reject decision', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await pipelineApi.submitReview(5, 'reject')

    expect(axios.post).toHaveBeenCalledWith('/api/pipeline/runs/5/review', {
      decision: 'reject'
    })
  })
})

describe('pipelineApi - Details', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_012: getIteration sends GET with run ID and iteration number', async () => {
    axios.get.mockResolvedValue({ data: { iteration_number: 3 } })

    await pipelineApi.getIteration(5, 3)

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/5/iterations/3')
  })

  it('SVC_PIPE_013: getBestConfigs sends GET with run ID and default params', async () => {
    axios.get.mockResolvedValue({ data: { configs: [] } })

    await pipelineApi.getBestConfigs(5)

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/5/best-configs', {
      params: {}
    })
  })

  it('SVC_PIPE_014: getBestConfigs sends GET with limit param', async () => {
    axios.get.mockResolvedValue({ data: { configs: [] } })

    await pipelineApi.getBestConfigs(5, { limit: 3 })

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/5/best-configs', {
      params: { limit: 3 }
    })
  })
})

describe('pipelineApi - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_015: createRun rejects on network error', async () => {
    axios.post.mockRejectedValue(new Error('Network Error'))

    await expect(pipelineApi.createRun({})).rejects.toThrow('Network Error')
  })

  it('SVC_PIPE_016: getRun rejects on 404', async () => {
    const error = { response: { status: 404 } }
    axios.get.mockRejectedValue(error)

    await expect(pipelineApi.getRun(999)).rejects.toEqual(error)
  })

  it('SVC_PIPE_017: startRun rejects on 409 conflict', async () => {
    const error = { response: { status: 409 } }
    axios.post.mockRejectedValue(error)

    await expect(pipelineApi.startRun(1)).rejects.toEqual(error)
  })

  it('SVC_PIPE_018: deleteRun rejects on 403 forbidden', async () => {
    const error = { response: { status: 403 } }
    axios.delete.mockRejectedValue(error)

    await expect(pipelineApi.deleteRun(1)).rejects.toEqual(error)
  })
})

describe('pipelineApi - Return Values', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_019: methods return raw axios response (not unwrapped)', async () => {
    const response = { data: { id: 1, status: 'created' } }
    axios.post.mockResolvedValue(response)

    const result = await pipelineApi.createRun({})

    expect(result).toBe(response)
  })

  it('SVC_PIPE_020: getRuns returns response with runs array', async () => {
    const response = { data: { runs: [{ id: 1 }, { id: 2 }] } }
    axios.get.mockResolvedValue(response)

    const result = await pipelineApi.getRuns()

    expect(result).toBe(response)
    expect(result.data.runs).toHaveLength(2)
  })

  it('SVC_PIPE_021: getIteration returns response with iteration data', async () => {
    const response = { data: { iteration_number: 1, metrics: {} } }
    axios.get.mockResolvedValue(response)

    const result = await pipelineApi.getIteration(1, 1)

    expect(result.data.iteration_number).toBe(1)
  })
})

describe('pipelineApi - URL Construction', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_PIPE_022: all endpoints use /api/pipeline base', async () => {
    axios.get.mockResolvedValue({ data: {} })
    axios.post.mockResolvedValue({ data: {} })
    axios.delete.mockResolvedValue({ data: {} })

    await pipelineApi.getRuns()
    await pipelineApi.createRun({})
    await pipelineApi.deleteRun(1)

    for (const call of [...axios.get.mock.calls, ...axios.post.mock.calls, ...axios.delete.mock.calls]) {
      expect(call[0]).toMatch(/^\/api\/pipeline\//)
    }
  })

  it('SVC_PIPE_023: run ID is interpolated correctly into URL', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await pipelineApi.getRun(123)

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/123')
  })

  it('SVC_PIPE_024: iteration number is interpolated correctly', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await pipelineApi.getIteration(10, 7)

    expect(axios.get).toHaveBeenCalledWith('/api/pipeline/runs/10/iterations/7')
  })
})
