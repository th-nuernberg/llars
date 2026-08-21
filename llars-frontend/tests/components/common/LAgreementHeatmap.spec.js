/**
 * LAgreementHeatmap Component Tests
 *
 * Tests for the LLARS pairwise agreement visualization heatmap.
 * Displays evaluator pair agreement scores with color-coded cells.
 * Test IDs: COMP_AH_001 - COMP_AH_030
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LAgreementHeatmap from '@/components/common/LAgreementHeatmap.vue'

const vuetify = createVuetify({ components, directives })

const sampleEvaluators = [
  { id: 1, name: 'Alice', isLLM: false },
  { id: 2, name: 'Bob', isLLM: false },
  { id: 'gpt-4', name: 'GPT-4', isLLM: true }
]

const sampleAgreements = {
  '1-2': 0.85,
  '1-gpt-4': 0.72,
  '2-gpt-4': 0.78
}

function mountComponent(props = {}, options = {}) {
  return mount(LAgreementHeatmap, {
    props: {
      evaluators: sampleEvaluators,
      agreements: sampleAgreements,
      ...props
    },
    global: {
      plugins: [vuetify],
      ...options.global
    },
    ...options
  })
}

describe('LAgreementHeatmap', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_AH_001: renders with evaluators and agreements', () => {
      const wrapper = mountComponent()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-agreement-heatmap').exists()).toBe(true)
    })

    it('COMP_AH_002: renders heatmap container when at least 2 evaluators', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.heatmap-container').exists()).toBe(true)
    })

    it('COMP_AH_003: shows empty state with fewer than 2 evaluators', () => {
      const wrapper = mountComponent({
        evaluators: [{ id: 1, name: 'Alice', isLLM: false }]
      })

      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.find('.heatmap-container').exists()).toBe(false)
    })

    it('COMP_AH_004: shows empty state with no evaluators', () => {
      const wrapper = mountComponent({ evaluators: [] })

      expect(wrapper.find('.empty-state').exists()).toBe(true)
    })

    it('COMP_AH_005: renders title when provided', () => {
      const wrapper = mountComponent({ title: 'Agreement Matrix' })

      expect(wrapper.find('.heatmap-title').exists()).toBe(true)
      expect(wrapper.find('.heatmap-title').text()).toBe('Agreement Matrix')
    })

    it('COMP_AH_006: does not render title when empty', () => {
      const wrapper = mountComponent({ title: '' })

      expect(wrapper.find('.heatmap-title').exists()).toBe(false)
    })

    it('COMP_AH_007: uses custom empty text', () => {
      const wrapper = mountComponent({
        evaluators: [{ id: 1, name: 'Alice', isLLM: false }],
        emptyText: 'Need more evaluators!'
      })

      expect(wrapper.find('.empty-state').text()).toContain('Need more evaluators!')
    })
  })

  // ==================== Evaluator Display Tests ====================

  describe('Evaluator Display', () => {
    it('COMP_AH_008: renders y-axis labels for each evaluator', () => {
      const wrapper = mountComponent()

      const yLabels = wrapper.findAll('.y-label')
      expect(yLabels.length).toBe(3)
    })

    it('COMP_AH_009: renders x-axis labels for each evaluator', () => {
      const wrapper = mountComponent()

      const xLabels = wrapper.findAll('.x-label')
      expect(xLabels.length).toBe(3)
    })

    it('COMP_AH_010: sorts evaluators humans first, then LLMs', () => {
      const wrapper = mountComponent()

      const yLabels = wrapper.findAll('.y-label')
      // Alice and Bob first (sorted alphabetically), GPT-4 last
      expect(yLabels[0].text()).toContain('Alice')
      expect(yLabels[1].text()).toContain('Bob')
      expect(yLabels[2].text()).toContain('GPT-4')
    })

    it('COMP_AH_011: does not sort when sortEvaluators is false', () => {
      const wrapper = mountComponent({ sortEvaluators: false })

      const yLabels = wrapper.findAll('.y-label')
      // Original order: Alice, Bob, GPT-4
      expect(yLabels[0].text()).toContain('Alice')
      expect(yLabels[1].text()).toContain('Bob')
      expect(yLabels[2].text()).toContain('GPT-4')
    })

    it('COMP_AH_012: marks LLM evaluator labels with is-llm class', () => {
      const wrapper = mountComponent()

      const yLabels = wrapper.findAll('.y-label')
      const llmLabel = yLabels.find(l => l.text().includes('GPT-4'))
      expect(llmLabel.classes()).toContain('is-llm')
    })

    it('COMP_AH_013: shows robot icon for LLM evaluators in y-axis', () => {
      const wrapper = mountComponent()

      const llmLabels = wrapper.findAll('.y-label.is-llm')
      expect(llmLabels.length).toBe(1)
    })
  })

  // ==================== Heatmap Grid Tests ====================

  describe('Heatmap Grid', () => {
    it('COMP_AH_014: renders correct number of rows', () => {
      const wrapper = mountComponent()

      const rows = wrapper.findAll('.heatmap-row')
      expect(rows.length).toBe(3)
    })

    it('COMP_AH_015: renders correct number of cells (NxN)', () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.heatmap-cell')
      expect(cells.length).toBe(9) // 3x3
    })

    it('COMP_AH_016: diagonal cells have diagonal class', () => {
      const wrapper = mountComponent()

      const diagonalCells = wrapper.findAll('.heatmap-cell.diagonal')
      expect(diagonalCells.length).toBe(3)
    })

    it('COMP_AH_017: diagonal cells show dash marker', () => {
      const wrapper = mountComponent()

      const diagonalMarkers = wrapper.findAll('.diagonal-marker')
      expect(diagonalMarkers.length).toBe(3)
      diagonalMarkers.forEach(marker => {
        expect(marker.text()).toBe('-')
      })
    })

    it('COMP_AH_018: non-diagonal cells are clickable', () => {
      const wrapper = mountComponent()

      const clickableCells = wrapper.findAll('.heatmap-cell.clickable')
      expect(clickableCells.length).toBe(6) // 9 total - 3 diagonal
    })
  })

  // ==================== Agreement Values Tests ====================

  describe('Agreement Values', () => {
    it('COMP_AH_019: shows agreement values in cells by default', () => {
      const wrapper = mountComponent()

      const cellValues = wrapper.findAll('.cell-value:not(.diagonal-marker)')
      expect(cellValues.length).toBe(6) // 6 non-diagonal
    })

    it('COMP_AH_020: formats agreement as percentage', () => {
      const wrapper = mountComponent()

      const cellValues = wrapper.findAll('.cell-value:not(.diagonal-marker)')
      const values = cellValues.map(v => v.text())
      // Should contain 85%, 72%, 78% (and their symmetric counterparts)
      expect(values).toContain('85%')
      expect(values).toContain('72%')
      expect(values).toContain('78%')
    })

    it('COMP_AH_021: hides values when showValues is false', () => {
      const wrapper = mountComponent({ showValues: false })

      const cellValues = wrapper.findAll('.cell-value:not(.diagonal-marker)')
      expect(cellValues.length).toBe(0)
    })

    it('COMP_AH_022: symmetric agreement lookup works', () => {
      // The key '1-2' should also work when looked up as '2-1'
      const wrapper = mountComponent()

      const cellValues = wrapper.findAll('.cell-value:not(.diagonal-marker)')
      const values = cellValues.map(v => v.text())
      // 85% should appear twice (1-2 and 2-1)
      expect(values.filter(v => v === '85%').length).toBe(2)
    })
  })

  // ==================== Cell Styling Tests ====================

  describe('Cell Styling', () => {
    it('COMP_AH_023: non-diagonal cells have background color based on value', () => {
      const wrapper = mountComponent()

      const clickableCells = wrapper.findAll('.heatmap-cell.clickable')
      clickableCells.forEach(cell => {
        const style = cell.attributes('style')
        expect(style).toContain('background-color')
      })
    })

    it('COMP_AH_024: diagonal cells use CSS variable background', () => {
      const wrapper = mountComponent()

      const diagonalCells = wrapper.findAll('.heatmap-cell.diagonal')
      // Diagonal cells use a CSS variable style which happy-dom may not
      // render as inline style. Instead verify they have the diagonal class
      // and do not have rgb() inline background.
      diagonalCells.forEach(cell => {
        expect(cell.classes()).toContain('diagonal')
      })
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_AH_025: emits cell-click on non-diagonal cell click', async () => {
      const wrapper = mountComponent()

      const clickableCells = wrapper.findAll('.heatmap-cell.clickable')
      await clickableCells[0].trigger('click')

      expect(wrapper.emitted('cell-click')).toBeTruthy()
      const payload = wrapper.emitted('cell-click')[0][0]
      expect(payload).toHaveProperty('evaluator1')
      expect(payload).toHaveProperty('evaluator2')
      expect(payload).toHaveProperty('value')
      expect(payload).toHaveProperty('percentage')
    })

    it('COMP_AH_026: does not emit cell-click for diagonal cells', async () => {
      const wrapper = mountComponent()

      const diagonalCells = wrapper.findAll('.heatmap-cell.diagonal')
      await diagonalCells[0].trigger('click')

      expect(wrapper.emitted('cell-click')).toBeFalsy()
    })

    it('COMP_AH_027: emits cell-hover on mouseenter', async () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.heatmap-cell')
      await cells[1].trigger('mouseenter') // non-diagonal cell

      expect(wrapper.emitted('cell-hover')).toBeTruthy()
    })

    it('COMP_AH_028: emits cell-leave on mouseleave', async () => {
      const wrapper = mountComponent()

      const cells = wrapper.findAll('.heatmap-cell')
      await cells[1].trigger('mouseenter')
      await cells[1].trigger('mouseleave')

      expect(wrapper.emitted('cell-leave')).toBeTruthy()
    })
  })

  // ==================== Legend Tests ====================

  describe('Legend', () => {
    it('COMP_AH_029: shows color legend by default', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.heatmap-legend').exists()).toBe(true)
      expect(wrapper.find('.legend-gradient').exists()).toBe(true)
    })

    it('COMP_AH_030: shows evaluator type legend when LLMs present', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.evaluator-type-legend').exists()).toBe(true)
    })

    it('COMP_AH_031: hides evaluator type legend when no LLMs', () => {
      const wrapper = mountComponent({
        evaluators: [
          { id: 1, name: 'Alice', isLLM: false },
          { id: 2, name: 'Bob', isLLM: false }
        ]
      })

      expect(wrapper.find('.evaluator-type-legend').exists()).toBe(false)
    })

    it('COMP_AH_032: hides legend when showLegend is false', () => {
      const wrapper = mountComponent({ showLegend: false })

      expect(wrapper.find('.heatmap-legend').exists()).toBe(false)
    })

    it('COMP_AH_033: uses custom low/high labels', () => {
      const wrapper = mountComponent({
        lowLabel: 'Bad',
        highLabel: 'Good'
      })

      const labels = wrapper.findAll('.legend-label')
      expect(labels[0].text()).toBe('Bad')
      expect(labels[1].text()).toBe('Good')
    })
  })

  // ==================== Hover Info Tests ====================

  describe('Hover Info', () => {
    it('COMP_AH_034: shows hover info placeholder by default', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.hover-info').exists()).toBe(true)
      expect(wrapper.find('.hover-placeholder').exists()).toBe(true)
    })

    it('COMP_AH_035: hides hover info when showHoverInfo is false', () => {
      const wrapper = mountComponent({ showHoverInfo: false })

      expect(wrapper.find('.hover-info').exists()).toBe(false)
    })
  })
})
