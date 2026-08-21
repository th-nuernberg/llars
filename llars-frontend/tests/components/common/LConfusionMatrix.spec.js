/**
 * LConfusionMatrix Component Tests
 *
 * Tests for the LLARS confusion matrix / heatmap component.
 * Supports binary classification (TP/FP/TN/FN) and multi-class matrices.
 * Test IDs: COMP_CM_001 - COMP_CM_035
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LConfusionMatrix from '@/components/common/LConfusionMatrix.vue'

const vuetify = createVuetify({ components, directives })

const binaryMatrix = {
  truePositive: 20,
  falsePositive: 4,
  trueNegative: 18,
  falseNegative: 2
}

const multiClassData = [[10, 2, 1], [3, 15, 0], [1, 0, 12]]
const multiClassRows = [
  { label: 'Cat A', icon: 'mdi-tag' },
  { label: 'Cat B' },
  { label: 'Cat C' }
]
const multiClassColumns = [
  { label: 'Cat A' },
  { label: 'Cat B' },
  { label: 'Cat C' }
]

function mountComponent(props = {}, options = {}) {
  return mount(LConfusionMatrix, {
    props,
    global: {
      plugins: [vuetify],
      stubs: {
        LTooltip: { template: '<span><slot /></span>' }
      },
      ...options.global
    },
    ...options
  })
}

describe('LConfusionMatrix', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_CM_001: renders with binary matrix prop', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-confusion-matrix').exists()).toBe(true)
    })

    it('COMP_CM_002: renders with multi-class data', () => {
      const wrapper = mountComponent({
        rows: multiClassRows,
        columns: multiClassColumns,
        data: multiClassData
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-confusion-matrix').exists()).toBe(true)
    })

    it('COMP_CM_003: renders header with default title', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      expect(wrapper.find('.matrix-title').exists()).toBe(true)
    })

    it('COMP_CM_004: renders custom title', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        title: 'My Custom Matrix'
      })

      expect(wrapper.find('.matrix-title').text()).toContain('My Custom Matrix')
    })
  })

  // ==================== Binary Matrix Tests ====================

  describe('Binary Matrix', () => {
    it('COMP_CM_005: correctly renders TP, FP, FN, TN values', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      const valueCells = wrapper.findAll('.value-cell .cell-value')
      expect(valueCells.length).toBe(4)

      const values = valueCells.map(v => parseInt(v.text()))
      expect(values).toContain(20) // TP
      expect(values).toContain(4)  // FP
      expect(values).toContain(2)  // FN
      expect(values).toContain(18) // TN
    })

    it('COMP_CM_006: shows cell labels (TP, FP, FN, TN) by default', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        showCellLabels: true
      })

      const cellLabels = wrapper.findAll('.cell-label')
      const labelTexts = cellLabels.map(l => l.text())
      expect(labelTexts).toContain('TP')
      expect(labelTexts).toContain('FP')
      expect(labelTexts).toContain('FN')
      expect(labelTexts).toContain('TN')
    })

    it('COMP_CM_007: hides cell labels when showCellLabels is false', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        showCellLabels: false
      })

      expect(wrapper.findAll('.cell-label').length).toBe(0)
    })

    it('COMP_CM_008: computes correct row totals', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Row 0: TP(20) + FP(4) = 24
      // Row 1: FN(2) + TN(18) = 20
      const totalCells = wrapper.findAll('.matrix-row:not(.header-row):not(.totals-row):not(.axis-row) .total-cell')
      const totals = totalCells.map(c => parseInt(c.text()))
      expect(totals).toContain(24)
      expect(totals).toContain(20)
    })

    it('COMP_CM_009: computes correct grand total', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      const grandTotal = wrapper.find('.grand-total')
      expect(grandTotal.exists()).toBe(true)
      expect(parseInt(grandTotal.text())).toBe(44) // 20+4+2+18
    })

    it('COMP_CM_010: generates default binary row/column labels', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      const rowHeaders = wrapper.findAll('.row-header')
      expect(rowHeaders.length).toBeGreaterThan(0)

      const headerCells = wrapper.findAll('.header-cell')
      expect(headerCells.length).toBeGreaterThan(0)
    })

    it('COMP_CM_011: uses custom labels for binary matrix', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        labels: {
          actualFake: 'Custom Actual Fake',
          predictedFake: 'Custom Predicted Fake'
        }
      })

      const allText = wrapper.text()
      expect(allText).toContain('Custom Actual Fake')
      expect(allText).toContain('Custom Predicted Fake')
    })
  })

  // ==================== Multi-class Matrix Tests ====================

  describe('Multi-class Matrix', () => {
    it('COMP_CM_012: renders correct number of cells for 3x3 matrix', () => {
      const wrapper = mountComponent({
        rows: multiClassRows,
        columns: multiClassColumns,
        data: multiClassData
      })

      const valueCells = wrapper.findAll('.value-cell')
      expect(valueCells.length).toBe(9)
    })

    it('COMP_CM_013: renders row and column labels', () => {
      const wrapper = mountComponent({
        rows: multiClassRows,
        columns: multiClassColumns,
        data: multiClassData
      })

      const text = wrapper.text()
      expect(text).toContain('Cat A')
      expect(text).toContain('Cat B')
      expect(text).toContain('Cat C')
    })

    it('COMP_CM_014: does not show cell labels (TP/FP etc.) for multi-class', () => {
      const wrapper = mountComponent({
        rows: multiClassRows,
        columns: multiClassColumns,
        data: multiClassData,
        showCellLabels: true
      })

      const cellLabels = wrapper.findAll('.cell-label')
      // Multi-class getCellLabel returns '' for non-binary
      cellLabels.forEach(label => {
        expect(label.text()).toBe('')
      })
    })
  })

  // ==================== Metrics Tests ====================

  describe('Metrics', () => {
    it('COMP_CM_015: shows metrics summary for binary matrix by default', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        showMetrics: true
      })

      expect(wrapper.find('.metrics-summary').exists()).toBe(true)
    })

    it('COMP_CM_016: hides metrics when showMetrics is false', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        showMetrics: false
      })

      expect(wrapper.find('.metrics-summary').exists()).toBe(false)
    })

    it('COMP_CM_017: does not show metrics for multi-class matrix', () => {
      const wrapper = mountComponent({
        rows: multiClassRows,
        columns: multiClassColumns,
        data: multiClassData,
        showMetrics: true
      })

      expect(wrapper.find('.metrics-summary').exists()).toBe(false)
    })

    it('COMP_CM_018: calculates correct accuracy', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Accuracy = (TP + TN) / Total = (20 + 18) / 44 = 86.4%
      const metricItems = wrapper.findAll('.metric-item')
      const accuracyItem = metricItems[0]
      expect(accuracyItem.find('.metric-value').text()).toContain('86.4%')
    })

    it('COMP_CM_019: calculates correct precision', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Precision = TP / (TP + FP) = 20 / 24 = 83.3%
      const metricItems = wrapper.findAll('.metric-item')
      const precisionItem = metricItems[1]
      expect(precisionItem.find('.metric-value').text()).toContain('83.3%')
    })

    it('COMP_CM_020: calculates correct recall', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Recall = TP / (TP + FN) = 20 / 22 = 90.9%
      const metricItems = wrapper.findAll('.metric-item')
      const recallItem = metricItems[2]
      expect(recallItem.find('.metric-value').text()).toContain('90.9%')
    })

    it('COMP_CM_021: calculates correct F1 score', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Precision = 83.3%, Recall = 90.9%
      // F1 = 2 * (0.833 * 0.909) / (0.833 + 0.909) = 0.87
      const metricItems = wrapper.findAll('.metric-item')
      const f1Item = metricItems[3]
      expect(f1Item.find('.metric-value').text()).toContain('0.8')
    })

    it('COMP_CM_022: applies metric class for excellent (>= 80)', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      // Accuracy 86.4% should get 'excellent' class
      const metricItems = wrapper.findAll('.metric-item')
      expect(metricItems[0].find('.metric-value').classes()).toContain('excellent')
    })

    it('COMP_CM_023: handles zero total gracefully', () => {
      const wrapper = mountComponent({
        matrix: { truePositive: 0, falsePositive: 0, trueNegative: 0, falseNegative: 0 }
      })

      const metricItems = wrapper.findAll('.metric-item')
      metricItems.forEach(item => {
        expect(item.find('.metric-value').text()).toBe('-')
      })
    })
  })

  // ==================== Size & Style Tests ====================

  describe('Size Variants', () => {
    it('COMP_CM_024: applies default size class', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      expect(wrapper.find('.l-confusion-matrix').classes()).toContain('size-default')
    })

    it('COMP_CM_025: applies compact size class', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, size: 'compact' })

      expect(wrapper.find('.l-confusion-matrix').classes()).toContain('size-compact')
    })

    it('COMP_CM_026: applies large size class', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, size: 'large' })

      expect(wrapper.find('.l-confusion-matrix').classes()).toContain('size-large')
    })
  })

  // ==================== Color Coding Tests ====================

  describe('Color Coding', () => {
    it('COMP_CM_027: diagonal cells get correct class', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      const valueCells = wrapper.findAll('.value-cell')
      // Cell [0,0] (TP) is diagonal - correct
      expect(valueCells[0].classes()).toContain('correct')
      // Cell [0,1] (FP) is off-diagonal - incorrect
      expect(valueCells[1].classes()).toContain('incorrect')
    })

    it('COMP_CM_028: applies heatmap class when useHeatmap is true', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, useHeatmap: true })

      const valueCells = wrapper.findAll('.value-cell')
      valueCells.forEach(cell => {
        expect(cell.classes()).toContain('heatmap')
      })
    })

    it('COMP_CM_029: heatmap cells have background color styles', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, useHeatmap: true })

      const valueCells = wrapper.findAll('.value-cell')
      valueCells.forEach(cell => {
        const style = cell.attributes('style')
        expect(style).toContain('background-color')
      })
    })

    it('COMP_CM_030: no background styles when useHeatmap is false', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, useHeatmap: false })

      const valueCells = wrapper.findAll('.value-cell')
      valueCells.forEach(cell => {
        const style = cell.attributes('style') || ''
        expect(style).not.toContain('background-color')
      })
    })
  })

  // ==================== Controls Tests ====================

  describe('Controls', () => {
    it('COMP_CM_031: shows controls by default', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      expect(wrapper.find('.matrix-controls').exists()).toBe(true)
    })

    it('COMP_CM_032: hides controls when showControls is false', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, showControls: false })

      expect(wrapper.find('.matrix-controls').exists()).toBe(false)
    })
  })

  // ==================== Legend Tests ====================

  describe('Legend', () => {
    it('COMP_CM_033: hides legend by default', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      expect(wrapper.find('.matrix-legend').exists()).toBe(false)
    })

    it('COMP_CM_034: shows legend when showLegend is true (binary)', () => {
      const wrapper = mountComponent({ matrix: binaryMatrix, showLegend: true })

      expect(wrapper.find('.matrix-legend').exists()).toBe(true)
      const legendItems = wrapper.findAll('.legend-item')
      expect(legendItems.length).toBe(4) // TP, FP, FN, TN
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_CM_035: emits cell-click with row, col, value on cell click', async () => {
      const wrapper = mountComponent({ matrix: binaryMatrix })

      const valueCells = wrapper.findAll('.value-cell')
      await valueCells[0].trigger('click')

      expect(wrapper.emitted('cell-click')).toBeTruthy()
      expect(wrapper.emitted('cell-click')[0][0]).toEqual({
        row: 0,
        col: 0,
        value: 20
      })
    })
  })

  // ==================== Axis Labels Tests ====================

  describe('Axis Labels', () => {
    it('COMP_CM_036: renders custom axis labels', () => {
      const wrapper = mountComponent({
        matrix: binaryMatrix,
        xAxisLabel: 'Actual Class',
        yAxisLabel: 'Predicted Class'
      })

      expect(wrapper.find('.x-axis').text()).toBe('Actual Class')
      expect(wrapper.find('.y-axis').text()).toBe('Predicted Class')
    })
  })
})
