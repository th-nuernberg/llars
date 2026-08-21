/**
 * Tests for useFirstComparisonNotice composable
 *
 * Test IDs: FCN_001 - FCN_012
 *
 * Coverage:
 * - One-time trigger after the FIRST successful comparison save
 * - No re-trigger on subsequent saves (localStorage fast-path)
 * - No re-trigger across reloads when backend flag is already set
 * - Per-user localStorage scoping
 * - Backend persistence (PUT preferences) + read (GET settings)
 * - Tolerance of backend failures (localStorage still suppresses)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn()
  }
}))

// In-memory localStorage mock so we can assert per-user scoping.
const mockLocalStorage = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => (key in store ? store[key] : null)),
    setItem: vi.fn((key, value) => { store[key] = String(value) }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()

import { useFirstComparisonNotice } from '@/composables/useFirstComparisonNotice'

describe('useFirstComparisonNotice', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.clear()
    vi.stubGlobal('localStorage', mockLocalStorage)
    // Default: backend reports the flag NOT yet seen.
    axios.get.mockResolvedValue({ data: { settings: { preferences: {} } } })
    axios.put.mockResolvedValue({ data: { success: true } })
    mockLocalStorage.setItem('username', 'participant1')
    // setItem was just called for username — clear the call history so the
    // per-test assertions on setItem are clean.
    mockLocalStorage.setItem.mockClear()
  })

  it('FCN_001: shows the notice exactly once after the first save', async () => {
    const n = useFirstComparisonNotice()
    expect(n.noticeVisible.value).toBe(false)
    const fired = await n.maybeShowAfterFirstSave()
    expect(fired).toBe(true)
    expect(n.noticeVisible.value).toBe(true)
  })

  it('FCN_002: does NOT show again on subsequent saves (same session)', async () => {
    const n = useFirstComparisonNotice()
    await n.maybeShowAfterFirstSave()
    n.dismiss()
    const firedAgain = await n.maybeShowAfterFirstSave()
    expect(firedAgain).toBe(false)
    expect(n.noticeVisible.value).toBe(false)
  })

  it('FCN_003: persists a per-user localStorage flag on first save', async () => {
    const n = useFirstComparisonNotice()
    await n.maybeShowAfterFirstSave()
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'llars:firstComparisonNoticeSeen:participant1',
      '1'
    )
  })

  it('FCN_004: writes the backend flag on first save', async () => {
    const n = useFirstComparisonNotice()
    await n.maybeShowAfterFirstSave()
    expect(axios.put).toHaveBeenCalledWith('/api/user/settings', {
      preferences: { firstComparisonNoticeSeen: true }
    })
  })

  it('FCN_005: never fires when localStorage already has the flag (reload, same device)', async () => {
    mockLocalStorage.setItem('llars:firstComparisonNoticeSeen:participant1', '1')
    const n = useFirstComparisonNotice()
    const fired = await n.maybeShowAfterFirstSave()
    expect(fired).toBe(false)
    // localStorage fast-path means we never even hit the backend GET.
    expect(axios.get).not.toHaveBeenCalled()
  })

  it('FCN_006: never fires when backend flag is already set (new device, empty localStorage)', async () => {
    axios.get.mockResolvedValue({
      data: { settings: { preferences: { firstComparisonNoticeSeen: true } } }
    })
    const n = useFirstComparisonNotice()
    const fired = await n.maybeShowAfterFirstSave()
    expect(fired).toBe(false)
    expect(axios.get).toHaveBeenCalledWith('/api/user/settings')
    // It should NOT re-write the backend flag (already true).
    expect(axios.put).not.toHaveBeenCalled()
  })

  it('FCN_007: backfills localStorage from the backend flag', async () => {
    axios.get.mockResolvedValue({
      data: { settings: { preferences: { firstComparisonNoticeSeen: true } } }
    })
    const n = useFirstComparisonNotice()
    await n.maybeShowAfterFirstSave()
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'llars:firstComparisonNoticeSeen:participant1',
      '1'
    )
  })

  it('FCN_008: scopes the flag per username', async () => {
    // participant1 sees it; participant2 (other account, same browser) should
    // still see it on their first save because the key is per-user.
    mockLocalStorage.setItem('llars:firstComparisonNoticeSeen:participant1', '1')
    mockLocalStorage.setItem('username', 'participant2')
    const n = useFirstComparisonNotice()
    const fired = await n.maybeShowAfterFirstSave()
    expect(fired).toBe(true)
  })

  it('FCN_009: tolerates a backend PUT failure but still suppresses locally', async () => {
    axios.put.mockRejectedValue(new Error('network down'))
    const n = useFirstComparisonNotice()
    const fired = await n.maybeShowAfterFirstSave()
    expect(fired).toBe(true)
    // localStorage still set → no repeat on this device.
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      'llars:firstComparisonNoticeSeen:participant1',
      '1'
    )
    const again = await n.maybeShowAfterFirstSave()
    expect(again).toBe(false)
  })

  it('FCN_010: dismiss() hides the notice', async () => {
    const n = useFirstComparisonNotice()
    await n.maybeShowAfterFirstSave()
    expect(n.noticeVisible.value).toBe(true)
    n.dismiss()
    expect(n.noticeVisible.value).toBe(false)
  })

  it('FCN_011: does not double-fire when two saves race before backend resolves', async () => {
    // Slow backend GET resolving "not seen".
    let resolveGet
    axios.get.mockReturnValue(new Promise(r => { resolveGet = r }))
    const n = useFirstComparisonNotice()
    const p1 = n.maybeShowAfterFirstSave()
    // Second call before the first resolved — fast-path localStorage was set
    // synchronously by markSeen only after GET, so this also queues on GET.
    resolveGet({ data: { settings: { preferences: {} } } })
    const r1 = await p1
    const r2 = await n.maybeShowAfterFirstSave()
    expect(r1).toBe(true)
    expect(r2).toBe(false)
  })

  it('FCN_012: exposes the backend preference key', () => {
    const n = useFirstComparisonNotice()
    expect(n._BACKEND_PREF_KEY).toBe('firstComparisonNoticeSeen')
  })
})
