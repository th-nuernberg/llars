/**
 * LRatingDistribution Component Tests
 *
 * Tests for the LLARS rating distribution heatmap component.
 * Displays distribution of ratings across a scale with color intensity.
 * Test IDs: COMP_RD_001 - COMP_RD_030
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LRatingDistribution from '@/components/common/LRatingDistribution.vue'

const vuetify = createVuetify({ components, directives })

const sampleItems = [
  { value: 1, count: 5, percentage: 10 },
  { value: 2, count: 10, percentage: 20 },
  { value: 3, count: 15, percentage: 30 },
  { value: 4, count: 12, percentage: 24 },
  { value: 5, count: 8, percentage: 16 }
]

function mountComponent(props = {}, options = {}) {
  return mount(LRatingDistribution, {
    props: {
      items: sampleItems,
      scaleMin: 1,
      scaleMax: 5,
      ...props
    },
    global: {
      plugins: [vuetify],
      ...options.global
    },
    ...options
  })
}

describe('LRatingDistribution', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_RD_001: renders with items', () => {
      const wrapper = mountComponent()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-rating-distribution').exists()).toBe(true)
    })

    it('COMP_RD_002: renders distribution grid with items', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.distribution-grid').exists()).toBe(true)
    })

    it('COMP_RD_003: renders correct number of cells', () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.distribution-cell')
      expect(cells.length).toBe(5)
    })

    it('COMP_RD_004: renders header by default', () => {
      const wrapper = mountComponent({ label: 'Test Dimension' })

      expect(wrapper.find('.distribution-header').exists()).toBe(true)
    })

    it('COMP_RD_005: hides header when showHeader is false', () => {
      const wrapper = mountComponent({ showHeader: false })

      expect(wrapper.find('.distribution-header').exists()).toBe(false)
    })
  })

  // ==================== Value Display Tests ====================

  describe('Value Display', () => {
    it('COMP_RD_006: shows cell value (scale value)', () => {
      const wrapper = mountComponent()

      const cellValues = wrapper.findAll('.cell-value')
      const values = cellValues.map(v => v.text())
      expect(values).toContain('1')
      expect(values).toContain('5')
    })

    it('COMP_RD_007: shows cell count', () => {
      const wrapper = mountComponent()

      const cellCounts = wrapper.findAll('.cell-count')
      const counts = cellCounts.map(c => c.text())
      expect(counts).toContain('5')
      expect(counts).toContain('15')
    })

    it('COMP_RD_008: shows cell percentage', () => {
      const wrapper = mountComponent()

      const cellPercents = wrapper.findAll('.cell-percent')
      const percents = cellPercents.map(p => p.text())
      expect(percents).toContain('10%')
      expect(percents).toContain('30%')
    })

    it('COMP_RD_009: formats null percentage as dash', () => {
      const wrapper = mountComponent({
        items: [{ value: 1, count: 0, percentage: null }]
      })

      const cellPercent = wrapper.find('.cell-percent')
      expect(cellPercent.text()).toBe('-')
    })
  })

  // ==================== Color Mapping Tests ====================

  describe('Color Mapping', () => {
    it('COMP_RD_010: applies background color to cells', () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.distribution-cell')
      cells.forEach(cell => {
        const style = cell.attributes('style')
        expect(style).toContain('background-color')
      })
    })

    it('COMP_RD_011: uses emptyColor for 0 percentage', () => {
      const wrapper = mountComponent({
        items: [{ value: 1, count: 0, percentage: 0 }],
        emptyColor: '#f0f0f0'
      })

      const cell = wrapper.find('.distribution-cell')
      const style = cell.attributes('style')
      expect(style).toContain('#f0f0f0')
    })

    it('COMP_RD_012: higher percentage produces more intense color', () => {
      const wrapper = mountComponent({
        items: [
          { value: 1, count: 1, percentage: 10 },
          { value: 2, count: 10, percentage: 90 }
        ]
      })

      const cells = wrapper.findAll('.distribution-cell')
      const lowStyle = cells[0].attributes('style')
      const highStyle = cells[1].attributes('style')
      // Both should have background-color, but they differ
      expect(lowStyle).toContain('background-color')
      expect(highStyle).toContain('background-color')
      expect(lowStyle).not.toBe(highStyle)
    })

    it('COMP_RD_013: uses custom primary color', () => {
      const wrapper = mountComponent({
        items: [{ value: 1, count: 5, percentage: 50 }],
        primaryColor: '#ff0000'
      })

      const cell = wrapper.find('.distribution-cell')
      const style = cell.attributes('style')
      expect(style).toContain('background-color')
    })
  })

  // ==================== Header Tests ====================

  describe('Header', () => {
    it('COMP_RD_014: displays label in header', () => {
      const wrapper = mountComponent({ label: 'Coherence' })

      expect(wrapper.find('.distribution-label').text()).toBe('Coherence')
    })

    it('COMP_RD_015: displays scale range in header', () => {
      const wrapper = mountComponent({ scaleMin: 1, scaleMax: 5 })

      const scaleText = wrapper.find('.distribution-scale')
      expect(scaleText.exists()).toBe(true)
      expect(scaleText.text()).toContain('1')
      expect(scaleText.text()).toContain('5')
    })

    it('COMP_RD_016: hides scale range when both min and max are null', () => {
      const wrapper = mountComponent({
        scaleMin: null,
        scaleMax: null
      })

      expect(wrapper.find('.distribution-scale').exists()).toBe(false)
    })
  })

  // ==================== Size Variant Tests ====================

  describe('Size Variants', () => {
    it('COMP_RD_017: applies default size class', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-rating-distribution').classes()).toContain('size-default')
    })

    it('COMP_RD_018: applies compact size class', () => {
      const wrapper = mountComponent({ size: 'compact' })

      expect(wrapper.find('.l-rating-distribution').classes()).toContain('size-compact')
    })

    it('COMP_RD_019: applies large size class', () => {
      const wrapper = mountComponent({ size: 'large' })

      expect(wrapper.find('.l-rating-distribution').classes()).toContain('size-large')
    })
  })

  // ==================== Empty State Tests ====================

  describe('Empty State', () => {
    it('COMP_RD_020: shows empty grid when no items but scale provided', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 1,
        scaleMax: 5
      })

      expect(wrapper.find('.empty-grid').exists()).toBe(true)
    })

    it('COMP_RD_021: empty grid shows correct number of empty cells', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 1,
        scaleMax: 5,
        scaleStep: 1
      })

      const emptyCells = wrapper.findAll('.empty-cell')
      expect(emptyCells.length).toBe(5)
    })

    it('COMP_RD_022: empty cells show value and zero count', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 1,
        scaleMax: 3,
        scaleStep: 1
      })

      const cellValues = wrapper.findAll('.empty-cell .cell-value')
      expect(cellValues[0].text()).toBe('1')
      expect(cellValues[1].text()).toBe('2')
      expect(cellValues[2].text()).toBe('3')

      const cellCounts = wrapper.findAll('.empty-cell .cell-count')
      cellCounts.forEach(c => expect(c.text()).toBe('0'))
    })

    it('COMP_RD_023: shows no-data panel when no items and no scale', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: null,
        scaleMax: null
      })

      expect(wrapper.find('.no-data-panel').exists()).toBe(true)
    })

    it('COMP_RD_024: shows empty text hint when no items', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 1,
        scaleMax: 5,
        emptyText: 'No ratings yet'
      })

      expect(wrapper.find('.no-data-hint').text()).toContain('No ratings yet')
    })
  })

  // ==================== Clickable Tests ====================

  describe('Clickable', () => {
    it('COMP_RD_025: cells are not clickable by default', () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.distribution-cell')
      cells.forEach(cell => {
        expect(cell.classes()).not.toContain('clickable')
      })
    })

    it('COMP_RD_026: cells become clickable when clickable is true', () => {
      const wrapper = mountComponent({ clickable: true })

      const cells = wrapper.findAll('.distribution-cell')
      cells.forEach(cell => {
        expect(cell.classes()).toContain('clickable')
      })
    })

    it('COMP_RD_027: emits cell-click when clickable cell is clicked', async () => {
      const wrapper = mountComponent({ clickable: true })

      const cells = wrapper.findAll('.distribution-cell')
      await cells[0].trigger('click')

      expect(wrapper.emitted('cell-click')).toBeTruthy()
      expect(wrapper.emitted('cell-click')[0][0]).toEqual(sampleItems[0])
    })

    it('COMP_RD_028: does not emit cell-click when not clickable', async () => {
      const wrapper = mountComponent({ clickable: false })

      const cells = wrapper.findAll('.distribution-cell')
      await cells[0].trigger('click')

      expect(wrapper.emitted('cell-click')).toBeFalsy()
    })
  })

  // ==================== Scale Step Tests ====================

  describe('Scale Step', () => {
    it('COMP_RD_029: respects custom scale step for empty grid', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 0,
        scaleMax: 10,
        scaleStep: 2
      })

      const emptyCells = wrapper.findAll('.empty-cell')
      // Values: 0, 2, 4, 6, 8, 10 = 6 cells
      expect(emptyCells.length).toBe(6)
    })

    it('COMP_RD_030: uses default step of 1', () => {
      const wrapper = mountComponent({
        items: [],
        scaleMin: 1,
        scaleMax: 3
      })

      const emptyCells = wrapper.findAll('.empty-cell')
      expect(emptyCells.length).toBe(3)
    })
  })
})
