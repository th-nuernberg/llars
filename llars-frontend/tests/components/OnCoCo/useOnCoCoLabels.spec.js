/**
 * useOnCoCoLabels Constants Tests
 *
 * Tests for label categories, definitions, and helper functions.
 * Test IDs: ONCOCO_LBL_001 - ONCOCO_LBL_015
 */

import { describe, it, expect } from 'vitest'
import {
  LABEL_CATEGORIES,
  LABEL_DEFINITIONS
} from '@/components/OnCoCo/OnCoCoResults/composables/useOnCoCoLabels'

describe('useOnCoCoLabels', () => {
  // ==================== LABEL_CATEGORIES ====================

  describe('LABEL_CATEGORIES', () => {
    it('ONCOCO_LBL_001: has 4 main categories', () => {
      expect(Object.keys(LABEL_CATEGORIES)).toHaveLength(4)
    })

    it('ONCOCO_LBL_002: COUNSELOR_IMPACT_FACTORS has correct prefix', () => {
      expect(LABEL_CATEGORIES.COUNSELOR_IMPACT_FACTORS.prefix).toBe('CO-IF')
    })

    it('ONCOCO_LBL_003: COUNSELOR_BASIC_VARIABLES has correct prefix', () => {
      expect(LABEL_CATEGORIES.COUNSELOR_BASIC_VARIABLES.prefix).toBe('CO-BV')
    })

    it('ONCOCO_LBL_004: CLIENT_RESPONSES has correct prefix', () => {
      expect(LABEL_CATEGORIES.CLIENT_RESPONSES.prefix).toBe('CL')
    })

    it('ONCOCO_LBL_005: META has correct prefix', () => {
      expect(LABEL_CATEGORIES.META.prefix).toBe('META')
    })

    it('ONCOCO_LBL_006: each category has name, prefix, description, and labels', () => {
      Object.values(LABEL_CATEGORIES).forEach(cat => {
        expect(cat).toHaveProperty('name')
        expect(cat).toHaveProperty('prefix')
        expect(cat).toHaveProperty('description')
        expect(cat).toHaveProperty('labels')
        expect(Array.isArray(cat.labels)).toBe(true)
        expect(cat.labels.length).toBeGreaterThan(0)
      })
    })

    it('ONCOCO_LBL_007: COUNSELOR_IMPACT_FACTORS has 4 labels', () => {
      expect(LABEL_CATEGORIES.COUNSELOR_IMPACT_FACTORS.labels).toHaveLength(4)
    })

    it('ONCOCO_LBL_008: CLIENT_RESPONSES has 7 labels', () => {
      expect(LABEL_CATEGORIES.CLIENT_RESPONSES.labels).toHaveLength(7)
    })
  })

  // ==================== LABEL_DEFINITIONS ====================

  describe('LABEL_DEFINITIONS', () => {
    it('ONCOCO_LBL_009: has definitions for all category labels', () => {
      Object.values(LABEL_CATEGORIES).forEach(cat => {
        cat.labels.forEach(label => {
          expect(LABEL_DEFINITIONS).toHaveProperty(label)
        })
      })
    })

    it('ONCOCO_LBL_010: each definition has required fields', () => {
      Object.values(LABEL_DEFINITIONS).forEach(def => {
        expect(def).toHaveProperty('display')
        expect(def).toHaveProperty('shortDisplay')
        expect(def).toHaveProperty('category')
        expect(def).toHaveProperty('role')
        expect(def).toHaveProperty('color')
      })
    })

    it('ONCOCO_LBL_011: counselor labels have role=counselor', () => {
      expect(LABEL_DEFINITIONS['CO-IF-AC'].role).toBe('counselor')
      expect(LABEL_DEFINITIONS['CO-BV-PS'].role).toBe('counselor')
    })

    it('ONCOCO_LBL_012: client labels have role=client', () => {
      expect(LABEL_DEFINITIONS['CL-RE'].role).toBe('client')
      expect(LABEL_DEFINITIONS['CL-PE'].role).toBe('client')
    })

    it('ONCOCO_LBL_013: colors are valid hex values', () => {
      Object.values(LABEL_DEFINITIONS).forEach(def => {
        expect(def.color).toMatch(/^#[0-9A-Fa-f]{6}$/)
      })
    })
  })
})
