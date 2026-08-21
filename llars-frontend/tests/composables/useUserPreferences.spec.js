/**
 * useUserPreferences Tests
 *
 * Test IDs: USERPREF_001 - USERPREF_005
 *
 * Deckt die Per-User-Präferenz "Leertaste = Weiter" ab: Standard AUS,
 * Persistenz im Backend (PUT /api/user/settings) + localStorage-Cache, und das
 * Laden des Server-Werts beim ersten Konsumenten. Der Modul-Singleton wird pro
 * Test via resetModules frisch geladen.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({ default: { get: vi.fn(), put: vi.fn() } }))

const KEY = 'llars:pref:spacebarAdvance'

describe('useUserPreferences', () => {
  let store

  beforeEach(() => {
    vi.resetModules()
    store = {}
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((k) => (k in store ? store[k] : null)),
      setItem: vi.fn((k, v) => { store[k] = String(v) }),
      removeItem: vi.fn((k) => { delete store[k] }),
    })
  })

  it('USERPREF_001: spacebarAdvance defaults to false (no cache, empty server prefs)', async () => {
    const axios = (await import('axios')).default
    axios.get.mockResolvedValue({ data: { settings: { preferences: {} } } })
    const { useUserPreferences } = await import('@/composables/useUserPreferences')
    const { spacebarAdvance } = useUserPreferences()
    expect(spacebarAdvance.value).toBe(false)
  })

  it('USERPREF_002: reads cached "true" from localStorage synchronously', async () => {
    store[KEY] = 'true'
    const axios = (await import('axios')).default
    axios.get.mockResolvedValue({ data: { settings: { preferences: {} } } })
    const { useUserPreferences } = await import('@/composables/useUserPreferences')
    const { spacebarAdvance } = useUserPreferences()
    // Cache is available immediately, before the (empty) server response lands.
    expect(spacebarAdvance.value).toBe(true)
  })

  it('USERPREF_003: setSpacebarAdvance persists to backend and localStorage', async () => {
    const axios = (await import('axios')).default
    axios.get.mockResolvedValue({ data: { settings: { preferences: {} } } })
    axios.put.mockResolvedValue({ data: {} })
    const { useUserPreferences } = await import('@/composables/useUserPreferences')
    const { spacebarAdvance, setSpacebarAdvance } = useUserPreferences()

    await setSpacebarAdvance(true)

    expect(spacebarAdvance.value).toBe(true)
    expect(store[KEY]).toBe('true')
    expect(axios.put).toHaveBeenCalledWith('/api/user/settings', { preferences: { spacebarAdvance: true } })
  })

  it('USERPREF_004: loads the server value on first use and corrects the ref', async () => {
    const axios = (await import('axios')).default
    axios.get.mockResolvedValue({ data: { settings: { preferences: { spacebarAdvance: true } } } })
    const { useUserPreferences } = await import('@/composables/useUserPreferences')
    const { spacebarAdvance } = useUserPreferences()

    // loadFromServer runs on first consumer; flush the microtask queue.
    await Promise.resolve()
    await Promise.resolve()

    expect(spacebarAdvance.value).toBe(true)
    expect(axios.get).toHaveBeenCalledWith('/api/user/settings')
  })

  it('USERPREF_005: a failed server load keeps the cached value (no throw)', async () => {
    store[KEY] = 'true'
    const axios = (await import('axios')).default
    axios.get.mockRejectedValue(new Error('offline'))
    const { useUserPreferences } = await import('@/composables/useUserPreferences')
    const { spacebarAdvance } = useUserPreferences()

    await Promise.resolve()
    await Promise.resolve()

    // Cached value survives an unreachable server.
    expect(spacebarAdvance.value).toBe(true)
  })
})
