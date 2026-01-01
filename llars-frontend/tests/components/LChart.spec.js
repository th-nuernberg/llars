/**
 * LChart Component Tests
 *
 * Tests for the LLARS chart component with canvas-based line charts.
 * Test IDs: COMP_CHT_001 - COMP_CHT_050
 *
 * Coverage:
 * - Rendering and structure
 * - Title and header
 * - Container and canvas
 * - Loading state
 * - Empty state
 * - Data props (single and multiple series)
 * - Computed properties (hasData, normalizedSeries)
 * - Height prop
 * - Color props
 * - Grid and fill props
 * - Slots (title, actions)
 * - Edge cases
 *
 * Note: Canvas drawing operations cannot be fully tested in JSDOM,
 * but structure, props, and state handling are tested thoroughly.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LChart from '@/components/common/LChart.vue'

// Mock ResizeObserver
class ResizeObserverMock {
  constructor(callback) {
    this.callback = callback
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock requestAnimationFrame
const rafMock = vi.fn((cb) => {
  cb()
  return 1
})
const cafMock = vi.fn()

beforeEach(() => {
  global.ResizeObserver = ResizeObserverMock
  global.requestAnimationFrame = rafMock
  global.cancelAnimationFrame = cafMock
})

afterEach(() => {
  vi.clearAllMocks()
})

function mountLChart(props = {}, options = {}) {
  return mount(LChart, {
    props,
    global: {
      stubs: {
        'v-progress-circular': {
          template: '<div class="v-progress-circular"><slot /></div>',
          props: ['indeterminate', 'size', 'color']
        },
        'v-icon': {
          template: '<i class="v-icon">{{ icon }}</i>',
          props: ['icon', 'size', 'color']
        }
      }
    },
    ...options
  })
}

describe('LChart', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_CHT_001: renders with default props', () => {
      const wrapper = mountLChart()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-chart').exists()).toBe(true)
    })

    it('COMP_CHT_002: has l-chart class', () => {
      const wrapper = mountLChart()

      expect(wrapper.classes()).toContain('l-chart')
    })

    it('COMP_CHT_003: renders container', () => {
      const wrapper = mountLChart()

      expect(wrapper.find('.l-chart__container').exists()).toBe(true)
    })

    it('COMP_CHT_004: renders canvas element', () => {
      const wrapper = mountLChart()

      expect(wrapper.find('canvas').exists()).toBe(true)
    })

    it('COMP_CHT_005: does not render header by default', () => {
      const wrapper = mountLChart()

      expect(wrapper.find('.l-chart__header').exists()).toBe(false)
    })
  })

  // ==================== Title/Header Tests ====================

  describe('Title and Header', () => {
    it('COMP_CHT_006: renders header when title provided', () => {
      const wrapper = mountLChart({ title: 'CPU Usage' })

      expect(wrapper.find('.l-chart__header').exists()).toBe(true)
    })

    it('COMP_CHT_007: displays title text', () => {
      const wrapper = mountLChart({ title: 'Memory Usage' })

      expect(wrapper.find('.l-chart__title').text()).toBe('Memory Usage')
    })

    it('COMP_CHT_008: does not render header with empty title', () => {
      const wrapper = mountLChart({ title: '' })

      expect(wrapper.find('.l-chart__header').exists()).toBe(false)
    })

    it('COMP_CHT_009: renders header when title slot is used', () => {
      const wrapper = mountLChart({}, {
        slots: {
          title: '<span class="custom-title">Custom Title</span>'
        }
      })

      expect(wrapper.find('.l-chart__header').exists()).toBe(true)
      expect(wrapper.find('.custom-title').exists()).toBe(true)
    })

    it('COMP_CHT_010: renders actions slot in header', () => {
      const wrapper = mountLChart(
        { title: 'Chart' },
        {
          slots: {
            actions: '<button class="action-btn">Refresh</button>'
          }
        }
      )

      expect(wrapper.find('.l-chart__header .action-btn').exists()).toBe(true)
    })
  })

  // ==================== Height Tests ====================

  describe('Height', () => {
    it('COMP_CHT_011: applies default height of 100px', () => {
      const wrapper = mountLChart()
      const style = wrapper.find('.l-chart__container').attributes('style')

      expect(style).toContain('height: 100px')
    })

    it('COMP_CHT_012: accepts number height', () => {
      const wrapper = mountLChart({ height: 200 })
      const style = wrapper.find('.l-chart__container').attributes('style')

      expect(style).toContain('height: 200px')
    })

    it('COMP_CHT_013: accepts string height', () => {
      const wrapper = mountLChart({ height: '50vh' })
      const style = wrapper.find('.l-chart__container').attributes('style')

      expect(style).toContain('height: 50vh')
    })
  })

  // ==================== Loading State Tests ====================

  describe('Loading State', () => {
    it('COMP_CHT_014: does not have loading class by default', () => {
      const wrapper = mountLChart()

      expect(wrapper.classes()).not.toContain('l-chart--loading')
    })

    it('COMP_CHT_015: has loading class when loading prop is true', () => {
      const wrapper = mountLChart({ loading: true })

      expect(wrapper.classes()).toContain('l-chart--loading')
    })

    it('COMP_CHT_016: shows loading spinner when loading', () => {
      const wrapper = mountLChart({ loading: true })

      expect(wrapper.find('.l-chart__loading').exists()).toBe(true)
      expect(wrapper.find('.v-progress-circular').exists()).toBe(true)
    })

    it('COMP_CHT_017: hides loading spinner when not loading', () => {
      const wrapper = mountLChart({ loading: false })

      expect(wrapper.find('.l-chart__loading').exists()).toBe(false)
    })
  })

  // ==================== Empty State Tests ====================

  describe('Empty State', () => {
    it('COMP_CHT_018: shows empty state when no data', () => {
      const wrapper = mountLChart({ data: [] })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(true)
    })

    it('COMP_CHT_019: shows empty icon', () => {
      const wrapper = mountLChart({ data: [] })

      expect(wrapper.find('.l-chart__empty .v-icon').exists()).toBe(true)
      expect(wrapper.find('.v-icon').text()).toContain('mdi-chart-line')
    })

    it('COMP_CHT_020: shows default empty text', () => {
      const wrapper = mountLChart({ data: [] })

      expect(wrapper.find('.l-chart__empty span').text()).toBe('Keine Daten')
    })

    it('COMP_CHT_021: shows custom empty text', () => {
      const wrapper = mountLChart({ data: [], emptyText: 'No metrics available' })

      expect(wrapper.find('.l-chart__empty span').text()).toBe('No metrics available')
    })

    it('COMP_CHT_022: hides empty state when data exists', () => {
      const wrapper = mountLChart({ data: [10, 20, 30] })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_023: hides empty state when loading', () => {
      const wrapper = mountLChart({ data: [], loading: true })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })
  })

  // ==================== Data Props Tests ====================

  describe('Data Props', () => {
    it('COMP_CHT_024: accepts single data array', () => {
      const wrapper = mountLChart({ data: [1, 2, 3, 4, 5] })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_025: accepts series array', () => {
      const wrapper = mountLChart({
        series: [
          { data: [1, 2, 3], color: 'primary', label: 'Series 1' }
        ]
      })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_026: accepts multiple series', () => {
      const wrapper = mountLChart({
        series: [
          { data: [1, 2, 3], color: 'primary', label: 'RX' },
          { data: [4, 5, 6], color: 'accent', label: 'TX' }
        ]
      })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_027: shows empty when series has no data', () => {
      const wrapper = mountLChart({
        series: [
          { data: [], color: 'primary' }
        ]
      })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(true)
    })

    it('COMP_CHT_028: hasData is true with valid single data', () => {
      const wrapper = mountLChart({ data: [10, 20] })

      // Component doesn't show empty state when hasData is true
      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_029: hasData is true when at least one series has data', () => {
      const wrapper = mountLChart({
        series: [
          { data: [], color: 'primary' },
          { data: [1, 2], color: 'accent' }
        ]
      })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })
  })

  // ==================== Default Props Tests ====================

  describe('Default Props', () => {
    it('COMP_CHT_030: default maxPoints is 60', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('maxPoints')).toBe(60)
    })

    it('COMP_CHT_031: default color is primary', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('color')).toBe('primary')
    })

    it('COMP_CHT_032: default fill is true', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('fill')).toBe(true)
    })

    it('COMP_CHT_033: default grid is true', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('grid')).toBe(true)
    })

    it('COMP_CHT_034: default lineWidth is 2', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('lineWidth')).toBe(2)
    })

    it('COMP_CHT_035: default smooth is true', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('smooth')).toBe(true)
    })

    it('COMP_CHT_036: default minY is null', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('minY')).toBe(null)
    })

    it('COMP_CHT_037: default maxY is null', () => {
      const wrapper = mountLChart()

      expect(wrapper.props('maxY')).toBe(null)
    })
  })

  // ==================== Custom Props Tests ====================

  describe('Custom Props', () => {
    it('COMP_CHT_038: accepts custom maxPoints', () => {
      const wrapper = mountLChart({ maxPoints: 120 })

      expect(wrapper.props('maxPoints')).toBe(120)
    })

    it('COMP_CHT_039: accepts custom color', () => {
      const wrapper = mountLChart({ color: 'accent' })

      expect(wrapper.props('color')).toBe('accent')
    })

    it('COMP_CHT_040: accepts fill as false', () => {
      const wrapper = mountLChart({ fill: false })

      expect(wrapper.props('fill')).toBe(false)
    })

    it('COMP_CHT_041: accepts grid as false', () => {
      const wrapper = mountLChart({ grid: false })

      expect(wrapper.props('grid')).toBe(false)
    })

    it('COMP_CHT_042: accepts custom lineWidth', () => {
      const wrapper = mountLChart({ lineWidth: 3 })

      expect(wrapper.props('lineWidth')).toBe(3)
    })

    it('COMP_CHT_043: accepts smooth as false', () => {
      const wrapper = mountLChart({ smooth: false })

      expect(wrapper.props('smooth')).toBe(false)
    })

    it('COMP_CHT_044: accepts custom minY', () => {
      const wrapper = mountLChart({ minY: 0 })

      expect(wrapper.props('minY')).toBe(0)
    })

    it('COMP_CHT_045: accepts custom maxY', () => {
      const wrapper = mountLChart({ maxY: 100 })

      expect(wrapper.props('maxY')).toBe(100)
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_CHT_046: updates when data changes', async () => {
      const wrapper = mountLChart({ data: [] })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(true)

      await wrapper.setProps({ data: [10, 20, 30] })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(false)
    })

    it('COMP_CHT_047: updates loading state reactively', async () => {
      const wrapper = mountLChart({ loading: false })

      expect(wrapper.classes()).not.toContain('l-chart--loading')

      await wrapper.setProps({ loading: true })

      expect(wrapper.classes()).toContain('l-chart--loading')
    })

    it('COMP_CHT_048: updates title reactively', async () => {
      const wrapper = mountLChart({ title: 'Original' })

      expect(wrapper.find('.l-chart__title').text()).toBe('Original')

      await wrapper.setProps({ title: 'Updated' })

      expect(wrapper.find('.l-chart__title').text()).toBe('Updated')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_CHT_049: handles null data gracefully', () => {
      const wrapper = mountLChart({ data: null })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(true)
    })

    it('COMP_CHT_050: handles undefined series gracefully', () => {
      const wrapper = mountLChart({ series: undefined })

      expect(wrapper.find('.l-chart__empty').exists()).toBe(true)
    })
  })
})
