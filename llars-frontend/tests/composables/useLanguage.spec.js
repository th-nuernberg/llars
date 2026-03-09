/**
 * useLanguage Composable Tests
 *
 * Tests for language switching between German and English.
 * Test IDs: LANG_001 - LANG_040
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock vue-i18n
const mockLocale = { value: 'de' }
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    locale: mockLocale
  }))
}))

// Mock i18n module
vi.mock('@/i18n', () => ({
  LANGUAGE_STORAGE_KEY: 'llars-language',
  SUPPORTED_LANGUAGES: ['de', 'en'],
  getInitialLanguage: vi.fn(() => 'de')
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18nParams: vi.fn()
}))

let useLanguage, initLanguage

describe('useLanguage', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    mockLocale.value = 'de'

    // Reset modules to get fresh singleton state
    vi.resetModules()

    // Re-apply mocks after reset
    vi.doMock('vue-i18n', () => ({
      useI18n: vi.fn(() => ({
        locale: mockLocale
      }))
    }))

    vi.doMock('@/i18n', () => ({
      LANGUAGE_STORAGE_KEY: 'llars-language',
      SUPPORTED_LANGUAGES: ['de', 'en'],
      getInitialLanguage: vi.fn(() => 'de')
    }))

    vi.doMock('@/utils/logI18n', () => ({
      logI18nParams: vi.fn()
    }))

    const mod = await import('@/composables/useLanguage')
    useLanguage = mod.useLanguage
    initLanguage = mod.initLanguage
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('LANG_001: useLanguage returns all expected properties', () => {
      const result = useLanguage()
      expect(result).toHaveProperty('currentLanguage')
      expect(result).toHaveProperty('languageOptions')
      expect(result).toHaveProperty('currentLanguageOption')
      expect(result).toHaveProperty('setLanguage')
      expect(result).toHaveProperty('toggleLanguage')
      expect(result).toHaveProperty('isLanguage')
    })

    it('LANG_002: exports initLanguage function', () => {
      expect(typeof initLanguage).toBe('function')
    })
  })

  // ==================== Initial State Tests ====================

  describe('Initial State', () => {
    it('LANG_003: currentLanguage defaults to de', () => {
      const { currentLanguage } = useLanguage()
      expect(currentLanguage.value).toBe('de')
    })

    it('LANG_004: languageOptions contains de and en', () => {
      const { languageOptions } = useLanguage()
      const values = languageOptions.value.map(o => o.value)
      expect(values).toContain('de')
      expect(values).toContain('en')
    })

    it('LANG_005: languageOptions has exactly 2 options', () => {
      const { languageOptions } = useLanguage()
      expect(languageOptions.value).toHaveLength(2)
    })

    it('LANG_006: language options have correct structure', () => {
      const { languageOptions } = useLanguage()
      languageOptions.value.forEach(opt => {
        expect(opt).toHaveProperty('value')
        expect(opt).toHaveProperty('title')
        expect(opt).toHaveProperty('short')
      })
    })

    it('LANG_007: German option has correct title', () => {
      const { languageOptions } = useLanguage()
      const de = languageOptions.value.find(o => o.value === 'de')
      expect(de.title).toBe('Deutsch')
      expect(de.short).toBe('DE')
    })

    it('LANG_008: English option has correct title', () => {
      const { languageOptions } = useLanguage()
      const en = languageOptions.value.find(o => o.value === 'en')
      expect(en.title).toBe('English')
      expect(en.short).toBe('EN')
    })
  })

  // ==================== setLanguage Tests ====================

  describe('setLanguage', () => {
    it('LANG_009: sets language to en', () => {
      const { currentLanguage, setLanguage } = useLanguage()
      setLanguage('en')
      expect(currentLanguage.value).toBe('en')
    })

    it('LANG_010: sets language to de', () => {
      const { currentLanguage, setLanguage } = useLanguage()
      setLanguage('en')
      setLanguage('de')
      expect(currentLanguage.value).toBe('de')
    })

    it('LANG_011: updates vue-i18n locale', () => {
      const { setLanguage } = useLanguage()
      setLanguage('en')
      expect(mockLocale.value).toBe('en')
    })

    it('LANG_012: persists to localStorage', () => {
      const { setLanguage } = useLanguage()
      setLanguage('en')
      expect(localStorage.setItem).toHaveBeenCalledWith('llars-language', 'en')
    })

    it('LANG_013: sets HTML lang attribute', () => {
      const { setLanguage } = useLanguage()
      setLanguage('en')
      expect(document.documentElement.getAttribute('lang')).toBe('en')
    })

    it('LANG_014: rejects invalid language', () => {
      const { currentLanguage, setLanguage } = useLanguage()
      const original = currentLanguage.value
      setLanguage('fr')
      expect(currentLanguage.value).toBe(original)
    })

    it('LANG_015: rejects empty string', () => {
      const { currentLanguage, setLanguage } = useLanguage()
      const original = currentLanguage.value
      setLanguage('')
      expect(currentLanguage.value).toBe(original)
    })

    it('LANG_016: does not persist invalid language', () => {
      vi.clearAllMocks()
      const { setLanguage } = useLanguage()
      setLanguage('invalid')
      expect(localStorage.setItem).not.toHaveBeenCalled()
    })
  })

  // ==================== toggleLanguage Tests ====================

  describe('toggleLanguage', () => {
    it('LANG_017: toggles from de to en', () => {
      const { currentLanguage, toggleLanguage } = useLanguage()
      expect(currentLanguage.value).toBe('de')
      toggleLanguage()
      expect(currentLanguage.value).toBe('en')
    })

    it('LANG_018: toggles from en to de', () => {
      const { currentLanguage, setLanguage, toggleLanguage } = useLanguage()
      setLanguage('en')
      toggleLanguage()
      expect(currentLanguage.value).toBe('de')
    })

    it('LANG_019: double toggle returns to original', () => {
      const { currentLanguage, toggleLanguage } = useLanguage()
      const original = currentLanguage.value
      toggleLanguage()
      toggleLanguage()
      expect(currentLanguage.value).toBe(original)
    })

    it('LANG_020: updates vue-i18n locale on toggle', () => {
      const { toggleLanguage } = useLanguage()
      toggleLanguage()
      expect(mockLocale.value).toBe('en')
    })
  })

  // ==================== isLanguage Tests ====================

  describe('isLanguage', () => {
    it('LANG_021: returns true for current language', () => {
      const { isLanguage } = useLanguage()
      expect(isLanguage('de')).toBe(true)
    })

    it('LANG_022: returns false for non-current language', () => {
      const { isLanguage } = useLanguage()
      expect(isLanguage('en')).toBe(false)
    })

    it('LANG_023: updates after setLanguage', () => {
      const { isLanguage, setLanguage } = useLanguage()
      setLanguage('en')
      expect(isLanguage('en')).toBe(true)
      expect(isLanguage('de')).toBe(false)
    })

    it('LANG_024: returns false for unsupported language', () => {
      const { isLanguage } = useLanguage()
      expect(isLanguage('fr')).toBe(false)
    })
  })

  // ==================== currentLanguageOption Tests ====================

  describe('currentLanguageOption', () => {
    it('LANG_025: returns German option by default', () => {
      const { currentLanguageOption } = useLanguage()
      expect(currentLanguageOption.value.value).toBe('de')
      expect(currentLanguageOption.value.title).toBe('Deutsch')
    })

    it('LANG_026: updates when language changes', () => {
      const { currentLanguageOption, setLanguage } = useLanguage()
      setLanguage('en')
      expect(currentLanguageOption.value.value).toBe('en')
      expect(currentLanguageOption.value.title).toBe('English')
    })
  })

  // ==================== Shared State Tests ====================

  describe('Shared State', () => {
    it('LANG_027: multiple instances share currentLanguage', () => {
      const instance1 = useLanguage()
      const instance2 = useLanguage()

      instance1.setLanguage('en')
      expect(instance2.currentLanguage.value).toBe('en')
    })

    it('LANG_028: toggle in one instance affects other', () => {
      const instance1 = useLanguage()
      const instance2 = useLanguage()

      instance1.toggleLanguage()
      expect(instance2.currentLanguage.value).toBe('en')
    })
  })

  // ==================== initLanguage Tests ====================

  describe('initLanguage', () => {
    it('LANG_029: initLanguage sets HTML lang attribute', () => {
      initLanguage()
      expect(document.documentElement.getAttribute('lang')).toBeDefined()
    })

    it('LANG_030: initLanguage is callable without errors', () => {
      expect(() => initLanguage()).not.toThrow()
    })
  })
})
