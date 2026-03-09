/**
 * Zotero Service Tests
 *
 * Tests for the Zotero integration API client.
 * Test IDs: SVC_ZOT_001 - SVC_ZOT_045
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    patch: vi.fn()
  }
}))

vi.mock('@/config.js', () => ({
  BASE_URL: ''
}))

vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: {
    token: 'auth_token'
  },
  getAuthStorageItem: vi.fn(() => 'zotero-test-token')
}))

import {
  checkOAuthAvailable,
  getConnectionStatus,
  startOAuth,
  connectWithApiKey,
  disconnect,
  getLibraries,
  getCollections,
  getWorkspaceLibraries,
  addWorkspaceLibrary,
  removeWorkspaceLibrary,
  syncLibrary,
  updateLibrarySettings,
  getSyncLogs
} from '@/services/zoteroService'

const expectedHeaders = { Authorization: 'Bearer zotero-test-token' }

describe('zoteroService - OAuth & Connection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_001: checkOAuthAvailable sends GET to /api/zotero/oauth-available', async () => {
    axios.get.mockResolvedValue({ data: { available: true } })

    const result = await checkOAuthAvailable()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/oauth-available'),
      expect.objectContaining({ headers: expectedHeaders })
    )
    expect(result).toEqual({ available: true })
  })

  it('SVC_ZOT_002: getConnectionStatus sends GET to /api/zotero/status', async () => {
    axios.get.mockResolvedValue({ data: { connected: true } })

    const result = await getConnectionStatus()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/status'),
      expect.objectContaining({ headers: expectedHeaders })
    )
    expect(result).toEqual({ connected: true })
  })

  it('SVC_ZOT_003: startOAuth sends POST to /api/zotero/connect/oauth/start', async () => {
    axios.post.mockResolvedValue({ data: { auth_url: 'https://zotero.org/oauth' } })

    const result = await startOAuth()

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/connect/oauth/start'),
      {},
      expect.objectContaining({ headers: expectedHeaders })
    )
    expect(result).toEqual({ auth_url: 'https://zotero.org/oauth' })
  })

  it('SVC_ZOT_004: connectWithApiKey sends POST with api_key', async () => {
    axios.post.mockResolvedValue({ data: { connected: true } })

    await connectWithApiKey('my-api-key')

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/connect/api-key'),
      { api_key: 'my-api-key' },
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_005: disconnect sends DELETE to /api/zotero/disconnect', async () => {
    axios.delete.mockResolvedValue({ data: { disconnected: true } })

    const result = await disconnect()

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/disconnect'),
      expect.objectContaining({ headers: expectedHeaders })
    )
    expect(result).toEqual({ disconnected: true })
  })
})

describe('zoteroService - Libraries', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_006: getLibraries sends GET to /api/zotero/libraries', async () => {
    axios.get.mockResolvedValue({ data: [{ id: 1, name: 'My Library' }] })

    const result = await getLibraries()

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/libraries'),
      expect.objectContaining({ headers: expectedHeaders })
    )
    expect(result).toEqual([{ id: 1, name: 'My Library' }])
  })

  it('SVC_ZOT_007: getCollections sends GET with library type and ID', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getCollections('user', '12345')

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/libraries/user/12345/collections'),
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_008: getCollections handles group library type', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getCollections('group', '67890')

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/libraries/group/67890/collections'),
      expect.objectContaining({ headers: expectedHeaders })
    )
  })
})

describe('zoteroService - Workspace Libraries', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_009: getWorkspaceLibraries sends GET with workspace ID', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getWorkspaceLibraries(3)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries'),
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_010: addWorkspaceLibrary sends POST with library data', async () => {
    const libraryData = { library_type: 'user', library_id: '123', collection_key: 'ABC' }
    axios.post.mockResolvedValue({ data: { id: 1 } })

    await addWorkspaceLibrary(3, libraryData)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries'),
      libraryData,
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_011: removeWorkspaceLibrary sends DELETE with workspace and library IDs', async () => {
    axios.delete.mockResolvedValue({ data: { deleted: true } })

    await removeWorkspaceLibrary(3, 7)

    expect(axios.delete).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries/7'),
      expect.objectContaining({ headers: expectedHeaders })
    )
  })
})

describe('zoteroService - Sync & Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_012: syncLibrary sends POST with workspace and library IDs', async () => {
    axios.post.mockResolvedValue({ data: { synced: true } })

    await syncLibrary(3, 7)

    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries/7/sync'),
      {},
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_013: updateLibrarySettings sends PATCH with settings', async () => {
    const settings = { auto_sync: true, sync_interval: 3600 }
    axios.patch.mockResolvedValue({ data: { updated: true } })

    await updateLibrarySettings(3, 7, settings)

    expect(axios.patch).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries/7/settings'),
      settings,
      expect.objectContaining({ headers: expectedHeaders })
    )
  })

  it('SVC_ZOT_014: getSyncLogs sends GET with default limit=20', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getSyncLogs(3, 7)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries/7/logs'),
      expect.objectContaining({
        headers: expectedHeaders,
        params: { limit: 20 }
      })
    )
  })

  it('SVC_ZOT_015: getSyncLogs sends GET with custom limit', async () => {
    axios.get.mockResolvedValue({ data: [] })

    await getSyncLogs(3, 7, 50)

    expect(axios.get).toHaveBeenCalledWith(
      expect.stringContaining('/api/zotero/workspaces/3/libraries/7/logs'),
      expect.objectContaining({
        params: { limit: 50 }
      })
    )
  })
})

describe('zoteroService - Auth Headers', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_016: all GET calls include auth headers', async () => {
    axios.get.mockResolvedValue({ data: {} })

    await checkOAuthAvailable()
    await getConnectionStatus()
    await getLibraries()

    for (const call of axios.get.mock.calls) {
      expect(call[1].headers).toEqual(expectedHeaders)
    }
  })

  it('SVC_ZOT_017: all POST calls include auth headers', async () => {
    axios.post.mockResolvedValue({ data: {} })

    await startOAuth()
    await connectWithApiKey('key')
    await addWorkspaceLibrary(1, {})

    for (const call of axios.post.mock.calls) {
      expect(call[2].headers).toEqual(expectedHeaders)
    }
  })

  it('SVC_ZOT_018: all DELETE calls include auth headers', async () => {
    axios.delete.mockResolvedValue({ data: {} })

    await disconnect()
    await removeWorkspaceLibrary(1, 1)

    for (const call of axios.delete.mock.calls) {
      expect(call[1].headers).toEqual(expectedHeaders)
    }
  })

  it('SVC_ZOT_019: PATCH calls include auth headers', async () => {
    axios.patch.mockResolvedValue({ data: {} })

    await updateLibrarySettings(1, 1, {})

    expect(axios.patch.mock.calls[0][2].headers).toEqual(expectedHeaders)
  })
})

describe('zoteroService - Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_020: network errors propagate', async () => {
    axios.get.mockRejectedValue(new Error('Network Error'))

    await expect(checkOAuthAvailable()).rejects.toThrow('Network Error')
  })

  it('SVC_ZOT_021: 401 errors propagate', async () => {
    const error = { response: { status: 401 } }
    axios.get.mockRejectedValue(error)

    await expect(getLibraries()).rejects.toEqual(error)
  })

  it('SVC_ZOT_022: 403 errors propagate', async () => {
    const error = { response: { status: 403 } }
    axios.post.mockRejectedValue(error)

    await expect(syncLibrary(1, 1)).rejects.toEqual(error)
  })
})

describe('zoteroService - Data Unwrapping', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('SVC_ZOT_023: all functions return response.data (not full response)', async () => {
    const innerData = { status: 'ok' }
    axios.get.mockResolvedValue({ data: innerData })

    const result = await checkOAuthAvailable()

    expect(result).toEqual(innerData)
    expect(result).not.toHaveProperty('data')
  })

  it('SVC_ZOT_024: POST functions return response.data', async () => {
    const innerData = { url: 'https://zotero.org' }
    axios.post.mockResolvedValue({ data: innerData })

    const result = await startOAuth()

    expect(result).toEqual(innerData)
  })
})

describe('zoteroService - Default Export', () => {
  it('SVC_ZOT_025: default export contains all functions', async () => {
    const mod = await import('@/services/zoteroService')
    const defaultExport = mod.default

    expect(defaultExport.checkOAuthAvailable).toBeDefined()
    expect(defaultExport.getConnectionStatus).toBeDefined()
    expect(defaultExport.startOAuth).toBeDefined()
    expect(defaultExport.connectWithApiKey).toBeDefined()
    expect(defaultExport.disconnect).toBeDefined()
    expect(defaultExport.getLibraries).toBeDefined()
    expect(defaultExport.getCollections).toBeDefined()
    expect(defaultExport.getWorkspaceLibraries).toBeDefined()
    expect(defaultExport.addWorkspaceLibrary).toBeDefined()
    expect(defaultExport.removeWorkspaceLibrary).toBeDefined()
    expect(defaultExport.syncLibrary).toBeDefined()
    expect(defaultExport.updateLibrarySettings).toBeDefined()
    expect(defaultExport.getSyncLogs).toBeDefined()
  })
})
