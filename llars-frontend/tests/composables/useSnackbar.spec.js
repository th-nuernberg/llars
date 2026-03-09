/**
 * useSnackbar Composable Tests
 *
 * Tests for the global snackbar/toast notification system.
 * Test IDs: SNACK_001 - SNACK_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// We need fresh state for each test since useSnackbar uses module-level shared state
let useSnackbar

describe('useSnackbar', () => {
  beforeEach(async () => {
    vi.resetModules()
    const mod = await import('@/composables/useSnackbar')
    useSnackbar = mod.useSnackbar
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('SNACK_001: useSnackbar returns all expected properties', () => {
      const result = useSnackbar()
      expect(result).toHaveProperty('snackbar')
      expect(result).toHaveProperty('snackbarModel')
      expect(result).toHaveProperty('showSuccess')
      expect(result).toHaveProperty('showError')
      expect(result).toHaveProperty('showInfo')
      expect(result).toHaveProperty('showWarning')
      expect(result).toHaveProperty('showMessage')
      expect(result).toHaveProperty('hideSnackbar')
    })

    it('SNACK_002: all methods are functions', () => {
      const { showSuccess, showError, showInfo, showWarning, showMessage, hideSnackbar } = useSnackbar()
      expect(typeof showSuccess).toBe('function')
      expect(typeof showError).toBe('function')
      expect(typeof showInfo).toBe('function')
      expect(typeof showWarning).toBe('function')
      expect(typeof showMessage).toBe('function')
      expect(typeof hideSnackbar).toBe('function')
    })
  })

  // ==================== Initial State Tests ====================

  describe('Initial State', () => {
    it('SNACK_003: snackbar starts hidden', () => {
      const { snackbar } = useSnackbar()
      expect(snackbar.value.show).toBe(false)
    })

    it('SNACK_004: snackbar starts with empty message', () => {
      const { snackbar } = useSnackbar()
      expect(snackbar.value.message).toBe('')
    })

    it('SNACK_005: snackbar default color is success', () => {
      const { snackbar } = useSnackbar()
      expect(snackbar.value.color).toBe('success')
    })

    it('SNACK_006: snackbar default timeout is 4000', () => {
      const { snackbar } = useSnackbar()
      expect(snackbar.value.timeout).toBe(4000)
    })
  })

  // ==================== showSuccess Tests ====================

  describe('showSuccess', () => {
    it('SNACK_007: shows snackbar with success color', () => {
      const { snackbar, showSuccess } = useSnackbar()
      showSuccess('Operation complete')
      expect(snackbar.value.show).toBe(true)
      expect(snackbar.value.color).toBe('success')
      expect(snackbar.value.message).toBe('Operation complete')
    })

    it('SNACK_008: uses check-circle icon', () => {
      const { snackbar, showSuccess } = useSnackbar()
      showSuccess('Done')
      expect(snackbar.value.icon).toBe('mdi-check-circle')
    })

    it('SNACK_009: default timeout is 4000ms', () => {
      const { snackbar, showSuccess } = useSnackbar()
      showSuccess('Done')
      expect(snackbar.value.timeout).toBe(4000)
    })

    it('SNACK_010: accepts custom timeout', () => {
      const { snackbar, showSuccess } = useSnackbar()
      showSuccess('Done', 2000)
      expect(snackbar.value.timeout).toBe(2000)
    })
  })

  // ==================== showError Tests ====================

  describe('showError', () => {
    it('SNACK_011: shows snackbar with error color', () => {
      const { snackbar, showError } = useSnackbar()
      showError('Something went wrong')
      expect(snackbar.value.show).toBe(true)
      expect(snackbar.value.color).toBe('error')
      expect(snackbar.value.message).toBe('Something went wrong')
    })

    it('SNACK_012: uses alert-circle icon', () => {
      const { snackbar, showError } = useSnackbar()
      showError('Error')
      expect(snackbar.value.icon).toBe('mdi-alert-circle')
    })

    it('SNACK_013: default timeout is 6000ms', () => {
      const { snackbar, showError } = useSnackbar()
      showError('Error')
      expect(snackbar.value.timeout).toBe(6000)
    })

    it('SNACK_014: accepts custom timeout', () => {
      const { snackbar, showError } = useSnackbar()
      showError('Error', 10000)
      expect(snackbar.value.timeout).toBe(10000)
    })
  })

  // ==================== showInfo Tests ====================

  describe('showInfo', () => {
    it('SNACK_015: shows snackbar with info color', () => {
      const { snackbar, showInfo } = useSnackbar()
      showInfo('FYI')
      expect(snackbar.value.show).toBe(true)
      expect(snackbar.value.color).toBe('info')
      expect(snackbar.value.message).toBe('FYI')
    })

    it('SNACK_016: uses information icon', () => {
      const { snackbar, showInfo } = useSnackbar()
      showInfo('Info')
      expect(snackbar.value.icon).toBe('mdi-information')
    })

    it('SNACK_017: default timeout is 4000ms', () => {
      const { snackbar, showInfo } = useSnackbar()
      showInfo('Info')
      expect(snackbar.value.timeout).toBe(4000)
    })
  })

  // ==================== showWarning Tests ====================

  describe('showWarning', () => {
    it('SNACK_018: shows snackbar with warning color', () => {
      const { snackbar, showWarning } = useSnackbar()
      showWarning('Be careful')
      expect(snackbar.value.show).toBe(true)
      expect(snackbar.value.color).toBe('warning')
      expect(snackbar.value.message).toBe('Be careful')
    })

    it('SNACK_019: uses alert icon', () => {
      const { snackbar, showWarning } = useSnackbar()
      showWarning('Warning')
      expect(snackbar.value.icon).toBe('mdi-alert')
    })

    it('SNACK_020: default timeout is 5000ms', () => {
      const { snackbar, showWarning } = useSnackbar()
      showWarning('Warning')
      expect(snackbar.value.timeout).toBe(5000)
    })
  })

  // ==================== showMessage Tests ====================

  describe('showMessage', () => {
    it('SNACK_021: shows snackbar with primary color by default', () => {
      const { snackbar, showMessage } = useSnackbar()
      showMessage('Custom message')
      expect(snackbar.value.show).toBe(true)
      expect(snackbar.value.color).toBe('primary')
      expect(snackbar.value.message).toBe('Custom message')
    })

    it('SNACK_022: accepts custom color option', () => {
      const { snackbar, showMessage } = useSnackbar()
      showMessage('Custom', { color: 'teal' })
      expect(snackbar.value.color).toBe('teal')
    })

    it('SNACK_023: accepts custom timeout option', () => {
      const { snackbar, showMessage } = useSnackbar()
      showMessage('Custom', { timeout: 8000 })
      expect(snackbar.value.timeout).toBe(8000)
    })

    it('SNACK_024: accepts custom icon option', () => {
      const { snackbar, showMessage } = useSnackbar()
      showMessage('Custom', { icon: 'mdi-star' })
      expect(snackbar.value.icon).toBe('mdi-star')
    })

    it('SNACK_025: defaults icon to null', () => {
      const { snackbar, showMessage } = useSnackbar()
      showMessage('Custom')
      expect(snackbar.value.icon).toBeNull()
    })
  })

  // ==================== hideSnackbar Tests ====================

  describe('hideSnackbar', () => {
    it('SNACK_026: hides the snackbar', () => {
      const { snackbar, showSuccess, hideSnackbar } = useSnackbar()
      showSuccess('Visible')
      expect(snackbar.value.show).toBe(true)

      hideSnackbar()
      expect(snackbar.value.show).toBe(false)
    })

    it('SNACK_027: preserves message and color when hiding', () => {
      const { snackbar, showError, hideSnackbar } = useSnackbar()
      showError('Error message')
      hideSnackbar()

      expect(snackbar.value.show).toBe(false)
      expect(snackbar.value.message).toBe('Error message')
      expect(snackbar.value.color).toBe('error')
    })
  })

  // ==================== Singleton/Shared State Tests ====================

  describe('Shared State', () => {
    it('SNACK_028: multiple useSnackbar() calls share state', () => {
      const instance1 = useSnackbar()
      const instance2 = useSnackbar()

      instance1.showSuccess('From instance 1')

      expect(instance2.snackbar.value.show).toBe(true)
      expect(instance2.snackbar.value.message).toBe('From instance 1')
    })

    it('SNACK_029: hideSnackbar from any instance hides globally', () => {
      const instance1 = useSnackbar()
      const instance2 = useSnackbar()

      instance1.showSuccess('Visible')
      instance2.hideSnackbar()

      expect(instance1.snackbar.value.show).toBe(false)
    })

    it('SNACK_030: snackbar is readonly, snackbarModel is writable', () => {
      const { snackbar, snackbarModel } = useSnackbar()

      // snackbarModel should be the raw ref (writable)
      snackbarModel.value = {
        show: true,
        message: 'Direct write',
        color: 'accent',
        timeout: 1000,
        icon: null
      }

      // readonly snackbar should reflect the change
      expect(snackbar.value.message).toBe('Direct write')
      expect(snackbar.value.color).toBe('accent')
    })
  })
})
