/**
 * KatexFormula Component Tests
 *
 * Tests for the LLARS KaTeX formula rendering component.
 * Test IDs: COMP_KTX_001 - COMP_KTX_040
 *
 * Coverage:
 * - Rendering and structure
 * - Formula prop
 * - Display mode
 * - KaTeX rendering
 * - Error handling
 * - CSS classes
 * - Reactivity
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import KatexFormula from '@/components/common/KatexFormula.vue'

// Mock KaTeX
const mockRenderToString = vi.fn()
vi.mock('katex', () => ({
  default: {
    renderToString: (...args) => mockRenderToString(...args)
  }
}))

// Mock KaTeX CSS
vi.mock('katex/dist/katex.min.css', () => ({}))

function mountKatexFormula(props = {}, options = {}) {
  return mount(KatexFormula, {
    props: {
      formula: 'x^2',
      ...props
    },
    ...options
  })
}

describe('KatexFormula', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default mock implementation
    mockRenderToString.mockImplementation((formula, options) => {
      return `<span class="katex">${formula}</span>`
    })
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_KTX_001: renders with required formula prop', () => {
      const wrapper = mountKatexFormula({ formula: 'E=mc^2' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.katex-formula').exists()).toBe(true)
    })

    it('COMP_KTX_002: has katex-formula class', () => {
      const wrapper = mountKatexFormula()

      expect(wrapper.classes()).toContain('katex-formula')
    })

    it('COMP_KTX_003: renders as span element', () => {
      const wrapper = mountKatexFormula()

      expect(wrapper.element.tagName).toBe('SPAN')
    })

    it('COMP_KTX_004: renders formula content via v-html', () => {
      mockRenderToString.mockReturnValue('<span class="katex">rendered</span>')
      const wrapper = mountKatexFormula({ formula: 'x^2' })

      expect(wrapper.html()).toContain('rendered')
    })
  })

  // ==================== Formula Prop Tests ====================

  describe('Formula Prop', () => {
    it('COMP_KTX_005: passes formula to KaTeX', () => {
      mountKatexFormula({ formula: 'a^2 + b^2 = c^2' })

      expect(mockRenderToString).toHaveBeenCalledWith(
        'a^2 + b^2 = c^2',
        expect.any(Object)
      )
    })

    it('COMP_KTX_006: renders simple formula', () => {
      mockRenderToString.mockReturnValue('<span>x²</span>')
      const wrapper = mountKatexFormula({ formula: 'x^2' })

      expect(wrapper.html()).toContain('x²')
    })

    it('COMP_KTX_007: renders fraction formula', () => {
      mockRenderToString.mockReturnValue('<span class="katex-frac">1/2</span>')
      const wrapper = mountKatexFormula({ formula: '\\frac{1}{2}' })

      expect(mockRenderToString).toHaveBeenCalledWith(
        '\\frac{1}{2}',
        expect.any(Object)
      )
    })

    it('COMP_KTX_008: renders Greek letters', () => {
      mockRenderToString.mockReturnValue('<span>α β γ</span>')
      const wrapper = mountKatexFormula({ formula: '\\alpha \\beta \\gamma' })

      expect(mockRenderToString).toHaveBeenCalledWith(
        '\\alpha \\beta \\gamma',
        expect.any(Object)
      )
    })

    it('COMP_KTX_009: renders sum notation', () => {
      const formula = '\\sum_{i=1}^{n} i'
      mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_010: renders integral notation', () => {
      const formula = '\\int_0^1 x dx'
      mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })
  })

  // ==================== Display Mode Tests ====================

  describe('Display Mode', () => {
    it('COMP_KTX_011: does not have display-mode class by default', () => {
      const wrapper = mountKatexFormula()

      expect(wrapper.classes()).not.toContain('display-mode')
    })

    it('COMP_KTX_012: has display-mode class when displayMode is true', () => {
      const wrapper = mountKatexFormula({ displayMode: true })

      expect(wrapper.classes()).toContain('display-mode')
    })

    it('COMP_KTX_013: passes displayMode false to KaTeX by default', () => {
      mountKatexFormula()

      expect(mockRenderToString).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ displayMode: false })
      )
    })

    it('COMP_KTX_014: passes displayMode true to KaTeX when enabled', () => {
      mountKatexFormula({ displayMode: true })

      expect(mockRenderToString).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ displayMode: true })
      )
    })

    it('COMP_KTX_015: does not have display-mode class when displayMode is false', () => {
      const wrapper = mountKatexFormula({ displayMode: false })

      expect(wrapper.classes()).not.toContain('display-mode')
    })
  })

  // ==================== KaTeX Options Tests ====================

  describe('KaTeX Options', () => {
    it('COMP_KTX_016: passes throwOnError as false', () => {
      mountKatexFormula()

      expect(mockRenderToString).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ throwOnError: false })
      )
    })

    it('COMP_KTX_017: KaTeX is called with correct options object', () => {
      mountKatexFormula({ formula: 'x', displayMode: true })

      expect(mockRenderToString).toHaveBeenCalledWith('x', {
        throwOnError: false,
        displayMode: true
      })
    })
  })

  // ==================== Error Handling Tests ====================

  describe('Error Handling', () => {
    it('COMP_KTX_018: falls back to raw formula on error', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockRenderToString.mockImplementation(() => {
        throw new Error('KaTeX parse error')
      })

      const wrapper = mountKatexFormula({ formula: 'invalid \\latex' })

      expect(wrapper.text()).toBe('invalid \\latex')
      consoleSpy.mockRestore()
    })

    it('COMP_KTX_019: logs error to console on KaTeX failure', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const error = new Error('KaTeX error')
      mockRenderToString.mockImplementation(() => {
        throw error
      })

      mountKatexFormula({ formula: 'bad formula' })

      expect(consoleSpy).toHaveBeenCalledWith('KaTeX error:', error)
      consoleSpy.mockRestore()
    })

    it('COMP_KTX_020: renders fallback without crashing', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      mockRenderToString.mockImplementation(() => {
        throw new Error('Parse error')
      })

      const wrapper = mountKatexFormula({ formula: '\\invalid' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.katex-formula').exists()).toBe(true)
      consoleSpy.mockRestore()
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_KTX_021: re-renders when formula changes', async () => {
      const wrapper = mountKatexFormula({ formula: 'x^2' })

      expect(mockRenderToString).toHaveBeenCalledWith('x^2', expect.any(Object))

      await wrapper.setProps({ formula: 'y^3' })

      expect(mockRenderToString).toHaveBeenCalledWith('y^3', expect.any(Object))
    })

    it('COMP_KTX_022: re-renders when displayMode changes', async () => {
      const wrapper = mountKatexFormula({ formula: 'x', displayMode: false })

      expect(wrapper.classes()).not.toContain('display-mode')

      await wrapper.setProps({ displayMode: true })

      expect(wrapper.classes()).toContain('display-mode')
    })

    it('COMP_KTX_023: updates KaTeX options when displayMode changes', async () => {
      mockRenderToString.mockClear()
      const wrapper = mountKatexFormula({ formula: 'x', displayMode: false })

      await wrapper.setProps({ displayMode: true })

      // Check that the last call has displayMode: true
      const calls = mockRenderToString.mock.calls
      const lastCall = calls[calls.length - 1]
      expect(lastCall[1].displayMode).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_KTX_024: handles empty formula string', () => {
      const wrapper = mountKatexFormula({ formula: '' })

      expect(wrapper.exists()).toBe(true)
      expect(mockRenderToString).toHaveBeenCalledWith('', expect.any(Object))
    })

    it('COMP_KTX_025: handles whitespace-only formula', () => {
      const wrapper = mountKatexFormula({ formula: '   ' })

      expect(wrapper.exists()).toBe(true)
      expect(mockRenderToString).toHaveBeenCalledWith('   ', expect.any(Object))
    })

    it('COMP_KTX_026: handles very long formula', () => {
      const longFormula = '\\sum_{i=1}^{n} \\frac{1}{i^2} + \\int_0^\\infty e^{-x^2} dx'
      const wrapper = mountKatexFormula({ formula: longFormula })

      expect(mockRenderToString).toHaveBeenCalledWith(longFormula, expect.any(Object))
    })

    it('COMP_KTX_027: handles formula with special characters', () => {
      const formula = '\\{ x | x > 0 \\}'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_028: handles matrix notation', () => {
      const formula = '\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_029: handles subscript and superscript', () => {
      const formula = 'x_1^2 + x_2^2'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_030: handles square root', () => {
      const formula = '\\sqrt{x^2 + y^2}'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_031: multiple instances are independent', () => {
      mockRenderToString.mockClear()

      const wrapper1 = mountKatexFormula({ formula: 'a' })
      const wrapper2 = mountKatexFormula({ formula: 'b' })
      const wrapper3 = mountKatexFormula({ formula: 'c', displayMode: true })

      expect(mockRenderToString).toHaveBeenCalledTimes(3)
      expect(wrapper1.classes()).not.toContain('display-mode')
      expect(wrapper2.classes()).not.toContain('display-mode')
      expect(wrapper3.classes()).toContain('display-mode')
    })

    it('COMP_KTX_032: handles Unicode characters in formula', () => {
      const formula = 'α + β = γ'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_033: handles newline in formula', () => {
      const formula = 'x \\\\ y'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_034: handles formula with text command', () => {
      const formula = '\\text{if } x > 0'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_035: KaTeX output is rendered as HTML', () => {
      mockRenderToString.mockReturnValue('<span class="katex"><span class="katex-html">test</span></span>')
      const wrapper = mountKatexFormula({ formula: 'x' })

      expect(wrapper.find('.katex').exists()).toBe(true)
      expect(wrapper.find('.katex-html').exists()).toBe(true)
    })

    it('COMP_KTX_036: handles rapid formula updates', async () => {
      const wrapper = mountKatexFormula({ formula: 'a' })

      await wrapper.setProps({ formula: 'b' })
      await wrapper.setProps({ formula: 'c' })
      await wrapper.setProps({ formula: 'd' })

      const calls = mockRenderToString.mock.calls
      expect(calls[calls.length - 1][0]).toBe('d')
    })

    it('COMP_KTX_037: handles chemical equations', () => {
      const formula = 'H_2O + CO_2'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_038: handles limits notation', () => {
      const formula = '\\lim_{x \\to \\infty} f(x)'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_039: handles binomial coefficient', () => {
      const formula = '\\binom{n}{k}'
      const wrapper = mountKatexFormula({ formula })

      expect(mockRenderToString).toHaveBeenCalledWith(formula, expect.any(Object))
    })

    it('COMP_KTX_040: component works with only required prop', () => {
      mockRenderToString.mockReturnValue('<span>formula</span>')
      const wrapper = mount(KatexFormula, {
        props: {
          formula: 'x'
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.katex-formula').exists()).toBe(true)
    })
  })
})
