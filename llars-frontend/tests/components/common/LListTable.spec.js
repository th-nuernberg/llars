/**
 * LListTable Component Tests
 *
 * Tests for the LLARS CSS-grid-based table component.
 * Features: column configuration, sorting, selection, row events.
 * Test IDs: COMP_LT_TBL_001 - COMP_LT_TBL_035
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LListTable from '@/components/common/LListTable.vue'

const vuetify = createVuetify({ components, directives })

const sampleColumns = [
  { key: 'id', label: '#', width: '60px' },
  { key: 'name', label: 'Name', flex: true, sortable: true },
  { key: 'status', label: 'Status', width: '100px' }
]

const sampleItems = [
  { id: 1, name: 'Alpha', status: 'active' },
  { id: 2, name: 'Beta', status: 'pending' },
  { id: 3, name: 'Gamma', status: 'inactive' }
]

function mountComponent(props = {}, options = {}) {
  return mount(LListTable, {
    props: {
      columns: sampleColumns,
      items: sampleItems,
      ...props
    },
    global: {
      plugins: [vuetify],
      ...options.global
    },
    slots: options.slots || {
      row: `<template #row="{ item }">
        <div class="l-col">{{ item.id }}</div>
        <div class="l-col">{{ item.name }}</div>
        <div class="l-col">{{ item.status }}</div>
      </template>`
    },
    ...options
  })
}

describe('LListTable', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_LT_TBL_001: renders with required columns prop', () => {
      const wrapper = mountComponent()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-list-table').exists()).toBe(true)
    })

    it('COMP_LT_TBL_002: renders header row', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-list-header').exists()).toBe(true)
    })

    it('COMP_LT_TBL_003: renders correct number of header columns', () => {
      const wrapper = mountComponent()

      const cols = wrapper.findAll('.l-list-header .l-col')
      expect(cols.length).toBe(3)
    })

    it('COMP_LT_TBL_004: renders column labels', () => {
      const wrapper = mountComponent()

      const labels = wrapper.findAll('.l-col__label')
      expect(labels[0].text()).toBe('#')
      expect(labels[1].text()).toBe('Name')
      expect(labels[2].text()).toBe('Status')
    })

    it('COMP_LT_TBL_005: renders correct number of data rows', () => {
      const wrapper = mountComponent()

      const rows = wrapper.findAll('.l-list-row')
      expect(rows.length).toBe(3)
    })

    it('COMP_LT_TBL_006: renders row content via slot', () => {
      const wrapper = mountComponent()

      expect(wrapper.text()).toContain('Alpha')
      expect(wrapper.text()).toContain('Beta')
      expect(wrapper.text()).toContain('Gamma')
    })
  })

  // ==================== Empty State Tests ====================

  describe('Empty State', () => {
    it('COMP_LT_TBL_007: shows empty state when items is empty', () => {
      const wrapper = mountComponent({ items: [] })

      expect(wrapper.find('.l-list-empty').exists()).toBe(true)
    })

    it('COMP_LT_TBL_008: displays custom empty text', () => {
      const wrapper = mountComponent({
        items: [],
        emptyText: 'No data available'
      })

      expect(wrapper.find('.l-list-empty').text()).toContain('No data available')
    })

    it('COMP_LT_TBL_009: hides empty state when items are present', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-list-empty').exists()).toBe(false)
    })
  })

  // ==================== Column Configuration Tests ====================

  describe('Column Configuration', () => {
    it('COMP_LT_TBL_010: applies grid template from column widths', () => {
      const wrapper = mountComponent()

      const header = wrapper.find('.l-list-header')
      const style = header.attributes('style')
      // Should contain grid-template-columns with 60px for id, 1fr for name, 100px for status
      expect(style).toContain('grid-template-columns')
      expect(style).toContain('60px')
      expect(style).toContain('100px')
    })

    it('COMP_LT_TBL_011: uses flex fraction for flex columns', () => {
      const wrapper = mountComponent({
        columns: [
          { key: 'a', label: 'A', flex: true },
          { key: 'b', label: 'B', flex: 2 }
        ]
      })

      const header = wrapper.find('.l-list-header')
      const style = header.attributes('style')
      expect(style).toContain('1fr')
      expect(style).toContain('2fr')
    })

    it('COMP_LT_TBL_012: uses auto for columns without width or flex', () => {
      const wrapper = mountComponent({
        columns: [
          { key: 'a', label: 'A' }
        ]
      })

      const header = wrapper.find('.l-list-header')
      const style = header.attributes('style')
      expect(style).toContain('auto')
    })

    it('COMP_LT_TBL_013: adds actions column when actionsWidth is set', () => {
      const wrapper = mountComponent({ actionsWidth: '90px' })

      const header = wrapper.find('.l-list-header')
      const style = header.attributes('style')
      expect(style).toContain('90px')
    })
  })

  // ==================== Sorting Tests ====================

  describe('Sorting', () => {
    it('COMP_LT_TBL_014: marks sortable columns', () => {
      const wrapper = mountComponent()

      const sortable = wrapper.findAll('.l-col--sortable')
      expect(sortable.length).toBe(1) // Only 'name' is sortable
    })

    it('COMP_LT_TBL_015: emits update:sortField on sort click (ascending)', async () => {
      const wrapper = mountComponent()

      const sortableCol = wrapper.find('.l-col--sortable')
      await sortableCol.trigger('click')

      expect(wrapper.emitted('update:sortField')).toBeTruthy()
      expect(wrapper.emitted('update:sortField')[0]).toEqual(['name'])
    })

    it('COMP_LT_TBL_016: emits update:sortAsc(true) on first click', async () => {
      const wrapper = mountComponent()

      const sortableCol = wrapper.find('.l-col--sortable')
      await sortableCol.trigger('click')

      expect(wrapper.emitted('update:sortAsc')).toBeTruthy()
      expect(wrapper.emitted('update:sortAsc')[0]).toEqual([true])
    })

    it('COMP_LT_TBL_017: emits update:sortAsc(false) on second click (same field)', async () => {
      const wrapper = mountComponent({ sortField: 'name', sortAsc: true })

      const sortableCol = wrapper.find('.l-col--sortable')
      await sortableCol.trigger('click')

      expect(wrapper.emitted('update:sortAsc')).toBeTruthy()
      expect(wrapper.emitted('update:sortAsc')[0]).toEqual([false])
    })

    it('COMP_LT_TBL_018: clears sort on third click (same field, desc)', async () => {
      const wrapper = mountComponent({ sortField: 'name', sortAsc: false })

      const sortableCol = wrapper.find('.l-col--sortable')
      await sortableCol.trigger('click')

      expect(wrapper.emitted('update:sortField')).toBeTruthy()
      expect(wrapper.emitted('update:sortField')[0]).toEqual([null])
    })

    it('COMP_LT_TBL_019: emits sort-change event', async () => {
      const wrapper = mountComponent()

      const sortableCol = wrapper.find('.l-col--sortable')
      await sortableCol.trigger('click')

      expect(wrapper.emitted('sort-change')).toBeTruthy()
      expect(wrapper.emitted('sort-change')[0][0]).toEqual({ field: 'name', asc: true })
    })

    it('COMP_LT_TBL_020: shows sorted class when field is active', () => {
      const wrapper = mountComponent({ sortField: 'name' })

      const sorted = wrapper.find('.l-col--sorted')
      expect(sorted.exists()).toBe(true)
    })
  })

  // ==================== Row Click Tests ====================

  describe('Row Click', () => {
    it('COMP_LT_TBL_021: emits row-click on row click when clickable', async () => {
      const wrapper = mountComponent({ clickable: true })

      const rows = wrapper.findAll('.l-list-row')
      await rows[0].trigger('click')

      expect(wrapper.emitted('row-click')).toBeTruthy()
      expect(wrapper.emitted('row-click')[0][0]).toEqual(sampleItems[0])
    })

    it('COMP_LT_TBL_022: does not emit row-click when not clickable', async () => {
      const wrapper = mountComponent({ clickable: false })

      const rows = wrapper.findAll('.l-list-row')
      await rows[0].trigger('click')

      expect(wrapper.emitted('row-click')).toBeFalsy()
    })

    it('COMP_LT_TBL_023: applies clickable class to rows', () => {
      const wrapper = mountComponent({ clickable: true })

      const rows = wrapper.findAll('.l-list-row')
      rows.forEach(row => {
        expect(row.classes()).toContain('l-list-row--clickable')
      })
    })
  })

  // ==================== Selection Tests ====================

  describe('Selection', () => {
    it('COMP_LT_TBL_024: shows select checkboxes when selectable', () => {
      const wrapper = mountComponent({ selectable: true })

      const selectCols = wrapper.findAll('.l-col--select')
      // 1 in header + 3 in rows = 4
      expect(selectCols.length).toBe(4)
    })

    it('COMP_LT_TBL_025: hides select checkboxes by default', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-col--select').exists()).toBe(false)
    })

    it('COMP_LT_TBL_026: prepends select column to grid', () => {
      const wrapper = mountComponent({ selectable: true })

      const header = wrapper.find('.l-list-header')
      const style = header.attributes('style')
      expect(style).toContain('40px') // Select column width
    })

    it('COMP_LT_TBL_027: marks selected rows with class', () => {
      const wrapper = mountComponent({
        selectable: true,
        selectedItems: [1]
      })

      const selectedRows = wrapper.findAll('.l-list-row--selected')
      expect(selectedRows.length).toBe(1)
    })
  })

  // ==================== Styling Tests ====================

  describe('Styling', () => {
    it('COMP_LT_TBL_028: applies bordered class by default', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-list-table').classes()).toContain('l-list-table--bordered')
    })

    it('COMP_LT_TBL_029: removes bordered class when bordered is false', () => {
      const wrapper = mountComponent({ bordered: false })

      expect(wrapper.find('.l-list-table').classes()).not.toContain('l-list-table--bordered')
    })

    it('COMP_LT_TBL_030: applies striped class when striped is true', () => {
      const wrapper = mountComponent({ striped: true })

      expect(wrapper.find('.l-list-table').classes()).toContain('l-list-table--striped')
    })

    it('COMP_LT_TBL_031: does not apply striped class by default', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-list-table').classes()).not.toContain('l-list-table--striped')
    })
  })

  // ==================== Row Class Tests ====================

  describe('Row Class', () => {
    it('COMP_LT_TBL_032: applies custom row class function', () => {
      const wrapper = mountComponent({
        rowClass: (item) => item.status === 'active' ? 'row-active' : ''
      })

      const rows = wrapper.findAll('.l-list-row')
      expect(rows[0].classes()).toContain('row-active')
      expect(rows[1].classes()).not.toContain('row-active')
    })
  })

  // ==================== Actions Column Tests ====================

  describe('Actions Column', () => {
    it('COMP_LT_TBL_033: renders actions column when actionsWidth is set', () => {
      const wrapper = mountComponent({ actionsWidth: '90px' })

      const actionsCols = wrapper.findAll('.l-col--actions')
      // 1 in header + 3 in rows = 4
      expect(actionsCols.length).toBe(4)
    })

    it('COMP_LT_TBL_034: hides actions column when actionsWidth is null', () => {
      const wrapper = mountComponent({ actionsWidth: null })

      expect(wrapper.find('.l-col--actions').exists()).toBe(false)
    })
  })

  // ==================== Grid Style Tests ====================

  describe('Grid Style', () => {
    it('COMP_LT_TBL_035: rows have same grid template as header', () => {
      const wrapper = mountComponent()

      const header = wrapper.find('.l-list-header')
      const firstRow = wrapper.find('.l-list-row')

      expect(header.attributes('style')).toBe(firstRow.attributes('style'))
    })
  })
})
