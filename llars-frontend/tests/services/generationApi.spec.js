/**
 * Generation API Service Tests
 *
 * Tests for the batch generation job API client.
 * Test IDs: SVC_GEN_001 - SVC_GEN_040
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

import { generationApi } from '@/services/generationApi'

describe('generationApi - Job Management', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_001: createJob sends POST to /api/generation/jobs', async () => {
    const data = { name: 'Test Job', config: { sources: {} } }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await generationApi.createJob(data)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs', data)
  })

  it('SVC_GEN_002: createJob passes complete config object', async () => {
    const data = {
      name: 'Summarization Test',
      description: 'Testing',
      config: {
        sources: { type: 'scenario', scenario_id: 123 },
        prompts: [{ template_id: 1, variant_name: 'Standard' }],
        llm_models: ['gpt-4'],
        generation_params: { temperature: 0.7 }
      }
    }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await generationApi.createJob(data)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs', data)
  })

  it('SVC_GEN_003: getJobs sends GET to /api/generation/jobs', async () => {
    axios.get.mockResolvedValue({ data: { jobs: [] } })

    await generationApi.getJobs()

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs', { params: {} })
  })

  it('SVC_GEN_004: getJobs passes query params for status filter', async () => {
    axios.get.mockResolvedValue({ data: { jobs: [] } })

    await generationApi.getJobs({ status: 'completed', limit: 10 })

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs', {
      params: { status: 'completed', limit: 10 }
    })
  })

  it('SVC_GEN_005: getJob sends GET with job ID', async () => {
    axios.get.mockResolvedValue({ data: { id: 42 } })

    await generationApi.getJob(42)

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs/42')
  })

  it('SVC_GEN_006: deleteJob sends DELETE with job ID', async () => {
    axios.delete.mockResolvedValue({ data: { success: true } })

    await generationApi.deleteJob(99)

    expect(axios.delete).toHaveBeenCalledWith('/api/generation/jobs/99')
  })
})

describe('generationApi - Job Lifecycle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_007: startJob sends POST to /api/generation/jobs/{id}/start', async () => {
    axios.post.mockResolvedValue({ data: { status: 'running' } })

    await generationApi.startJob(5)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/5/start')
  })

  it('SVC_GEN_008: pauseJob sends POST to /api/generation/jobs/{id}/pause', async () => {
    axios.post.mockResolvedValue({ data: { status: 'paused' } })

    await generationApi.pauseJob(5)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/5/pause')
  })

  it('SVC_GEN_009: cancelJob sends POST to /api/generation/jobs/{id}/cancel', async () => {
    axios.post.mockResolvedValue({ data: { status: 'cancelled' } })

    await generationApi.cancelJob(5)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/5/cancel')
  })
})

describe('generationApi - Outputs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_010: getOutputs sends GET with job ID and default params', async () => {
    axios.get.mockResolvedValue({ data: { outputs: [] } })

    await generationApi.getOutputs(10)

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs/10/outputs', { params: {} })
  })

  it('SVC_GEN_011: getOutputs passes pagination and filter params', async () => {
    axios.get.mockResolvedValue({ data: { outputs: [] } })

    await generationApi.getOutputs(10, { page: 2, per_page: 20, status: 'completed', include_prompts: true })

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs/10/outputs', {
      params: { page: 2, per_page: 20, status: 'completed', include_prompts: true }
    })
  })

  it('SVC_GEN_012: getOutput sends GET with output ID', async () => {
    axios.get.mockResolvedValue({ data: { id: 55 } })

    await generationApi.getOutput(55)

    expect(axios.get).toHaveBeenCalledWith('/api/generation/outputs/55')
  })
})

describe('generationApi - Export', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_013: exportCsv sends POST with blob response type', async () => {
    const blob = new Blob(['csv-data'])
    axios.post.mockResolvedValue({ data: blob })

    await generationApi.exportCsv(7)

    expect(axios.post).toHaveBeenCalledWith(
      '/api/generation/jobs/7/export/csv',
      {},
      { responseType: 'blob' }
    )
  })

  it('SVC_GEN_014: exportCsv passes options', async () => {
    axios.post.mockResolvedValue({ data: new Blob() })

    await generationApi.exportCsv(7, { include_prompts: true, status: 'completed' })

    expect(axios.post).toHaveBeenCalledWith(
      '/api/generation/jobs/7/export/csv',
      { include_prompts: true, status: 'completed' },
      { responseType: 'blob' }
    )
  })

  it('SVC_GEN_015: exportJson sends POST to json endpoint', async () => {
    axios.post.mockResolvedValue({ data: { outputs: [] } })

    await generationApi.exportJson(7)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/7/export/json', {})
  })

  it('SVC_GEN_016: exportJson passes options', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await generationApi.exportJson(7, { include_prompts: true })

    expect(axios.post).toHaveBeenCalledWith(
      '/api/generation/jobs/7/export/json',
      { include_prompts: true }
    )
  })
})

describe('generationApi - Scenario Creation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_017: createScenario sends POST to /api/generation/jobs/{id}/to-scenario', async () => {
    const data = { scenario_name: 'Test Scenario', evaluation_type: 'ranking' }
    axios.post.mockResolvedValue({ data: { scenario_id: 100 } })

    await generationApi.createScenario(7, data)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/7/to-scenario', data)
  })

  it('SVC_GEN_018: createScenario passes optional config_json', async () => {
    const data = {
      scenario_name: 'Comparison',
      evaluation_type: 'comparison',
      config_json: { buckets: 3 }
    }
    axios.post.mockResolvedValue({ data: {} })

    await generationApi.createScenario(7, data)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/jobs/7/to-scenario', data)
  })
})

describe('generationApi - Statistics & Estimation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_019: getStatistics sends GET to /api/generation/jobs/{id}/statistics', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await generationApi.getStatistics(12)

    expect(axios.get).toHaveBeenCalledWith('/api/generation/jobs/12/statistics')
  })

  it('SVC_GEN_020: estimateCost sends POST with config wrapped in object', async () => {
    const config = {
      sources: { type: 'scenario', scenario_id: 1 },
      prompts: [{ template_id: 1 }],
      llm_models: ['gpt-4']
    }
    axios.post.mockResolvedValue({ data: { total_cost: 1.5 } })

    await generationApi.estimateCost(config)

    expect(axios.post).toHaveBeenCalledWith('/api/generation/estimate', { config })
  })
})

describe('generationApi - Settings & Health', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_021: getMaxParallel sends GET to settings endpoint', async () => {
    axios.get.mockResolvedValue({ data: { max_parallel: 5 } })

    await generationApi.getMaxParallel()

    expect(axios.get).toHaveBeenCalledWith('/api/generation/settings/max-parallel')
  })

  it('SVC_GEN_022: healthCheck sends GET to health endpoint', async () => {
    axios.get.mockResolvedValue({ data: { status: 'ok' } })

    await generationApi.healthCheck()

    expect(axios.get).toHaveBeenCalledWith('/api/generation/health')
  })
})

describe('generationApi - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_023: createJob rejects on network error', async () => {
    const error = new Error('Network Error')
    axios.post.mockRejectedValue(error)

    await expect(generationApi.createJob({})).rejects.toThrow('Network Error')
  })

  it('SVC_GEN_024: getJobs rejects on 401 unauthorized', async () => {
    const error = { response: { status: 401 } }
    axios.get.mockRejectedValue(error)

    await expect(generationApi.getJobs()).rejects.toEqual(error)
  })

  it('SVC_GEN_025: deleteJob rejects on 404 not found', async () => {
    const error = { response: { status: 404 } }
    axios.delete.mockRejectedValue(error)

    await expect(generationApi.deleteJob(999)).rejects.toEqual(error)
  })

  it('SVC_GEN_026: startJob rejects on 409 conflict', async () => {
    const error = { response: { status: 409 } }
    axios.post.mockRejectedValue(error)

    await expect(generationApi.startJob(1)).rejects.toEqual(error)
  })
})

describe('generationApi - Return Values', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_GEN_027: createJob returns axios response (not unwrapped)', async () => {
    const response = { data: { id: 1, status: 'created' } }
    axios.post.mockResolvedValue(response)

    const result = await generationApi.createJob({})

    expect(result).toBe(response)
  })

  it('SVC_GEN_028: getJobs returns axios response', async () => {
    const response = { data: { jobs: [{ id: 1 }] } }
    axios.get.mockResolvedValue(response)

    const result = await generationApi.getJobs()

    expect(result).toBe(response)
  })
})
