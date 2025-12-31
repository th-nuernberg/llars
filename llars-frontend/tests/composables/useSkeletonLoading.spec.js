/**
 * Tests for useSkeletonLoading composable
 *
 * Test IDs: SKEL_001 - SKEL_050
 *
 * Coverage:
 * - Exports and initialization
 * - Default sections initialization
 * - isLoading function
 * - setLoading function
 * - startLoading / stopLoading functions
 * - withLoading async wrapper
 * - initLoadingSections function
 * - anyLoading / allLoaded functions
 * - Multiple instances (isolated state)
 * - Edge cases
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useSkeletonLoading, SKELETON_TYPES } from '@/composables/useSkeletonLoading'

describe('useSkeletonLoading Composable', () => {
  describe('Exports', () => {
    it('SKEL_001: exports useSkeletonLoading function', () => {
      expect(typeof useSkeletonLoading).toBe('function')
    })

    it('SKEL_002: exports SKELETON_TYPES constant', () => {
      expect(SKELETON_TYPES).toBeDefined()
      expect(typeof SKELETON_TYPES).toBe('object')
    })

    it('SKEL_003: returns all expected properties', () => {
      const result = useSkeletonLoading()

      expect(result).toHaveProperty('loadingStates')
      expect(result).toHaveProperty('isLoading')
      expect(result).toHaveProperty('setLoading')
      expect(result).toHaveProperty('startLoading')
      expect(result).toHaveProperty('stopLoading')
      expect(result).toHaveProperty('withLoading')
      expect(result).toHaveProperty('initLoadingSections')
      expect(result).toHaveProperty('anyLoading')
      expect(result).toHaveProperty('allLoaded')
    })

    it('SKEL_004: isLoading is a function', () => {
      const { isLoading } = useSkeletonLoading()
      expect(typeof isLoading).toBe('function')
    })

    it('SKEL_005: setLoading is a function', () => {
      const { setLoading } = useSkeletonLoading()
      expect(typeof setLoading).toBe('function')
    })

    it('SKEL_006: withLoading is a function', () => {
      const { withLoading } = useSkeletonLoading()
      expect(typeof withLoading).toBe('function')
    })
  })

  describe('SKELETON_TYPES Constant', () => {
    it('SKEL_007: SKELETON_TYPES has STAT_CARD', () => {
      expect(SKELETON_TYPES.STAT_CARD).toBe('card')
    })

    it('SKEL_008: SKELETON_TYPES has TABLE_FULL', () => {
      expect(SKELETON_TYPES.TABLE_FULL).toBe('table-heading, table-thead, table-tbody, table-tfoot')
    })

    it('SKEL_009: SKELETON_TYPES has TABLE_SIMPLE', () => {
      expect(SKELETON_TYPES.TABLE_SIMPLE).toBe('table-thead, table-tbody')
    })

    it('SKEL_010: SKELETON_TYPES has CARD_WITH_AVATAR', () => {
      expect(SKELETON_TYPES.CARD_WITH_AVATAR).toBe('card-avatar')
    })

    it('SKEL_011: SKELETON_TYPES has LIST_WITH_AVATAR', () => {
      expect(SKELETON_TYPES.LIST_WITH_AVATAR).toBe('list-item-avatar@3')
    })

    it('SKEL_012: SKELETON_TYPES has ARTICLE', () => {
      expect(SKELETON_TYPES.ARTICLE).toBe('article')
    })

    it('SKEL_013: SKELETON_TYPES has CHART', () => {
      expect(SKELETON_TYPES.CHART).toBe('card')
    })
  })

  describe('Default Initialization', () => {
    it('SKEL_014: initializes with empty loadingStates when no sections provided', () => {
      const { loadingStates } = useSkeletonLoading()
      expect(Object.keys(loadingStates).length).toBe(0)
    })

    it('SKEL_015: initializes default sections as loading=true', () => {
      const { loadingStates, isLoading } = useSkeletonLoading(['stats', 'table'])

      expect(loadingStates.stats).toBe(true)
      expect(loadingStates.table).toBe(true)
      expect(isLoading('stats')).toBe(true)
      expect(isLoading('table')).toBe(true)
    })

    it('SKEL_016: handles single section in array', () => {
      const { isLoading } = useSkeletonLoading(['content'])
      expect(isLoading('content')).toBe(true)
    })

    it('SKEL_017: handles many default sections', () => {
      const sections = ['a', 'b', 'c', 'd', 'e']
      const { isLoading } = useSkeletonLoading(sections)

      sections.forEach(section => {
        expect(isLoading(section)).toBe(true)
      })
    })

    it('SKEL_018: handles empty array', () => {
      const { loadingStates } = useSkeletonLoading([])
      expect(Object.keys(loadingStates).length).toBe(0)
    })

    it('SKEL_019: handles non-array defaultSections gracefully', () => {
      // Should not throw when passed non-array
      expect(() => useSkeletonLoading('invalid')).not.toThrow()
      expect(() => useSkeletonLoading(null)).not.toThrow()
      expect(() => useSkeletonLoading(undefined)).not.toThrow()
    })
  })

  describe('isLoading Function', () => {
    it('SKEL_020: returns false for unknown section', () => {
      const { isLoading } = useSkeletonLoading()
      expect(isLoading('unknown')).toBe(false)
    })

    it('SKEL_021: returns true for section set to loading', () => {
      const { isLoading, setLoading } = useSkeletonLoading()
      setLoading('test', true)
      expect(isLoading('test')).toBe(true)
    })

    it('SKEL_022: returns false for section set to not loading', () => {
      const { isLoading, setLoading } = useSkeletonLoading()
      setLoading('test', true)
      setLoading('test', false)
      expect(isLoading('test')).toBe(false)
    })

    it('SKEL_023: handles empty string section name', () => {
      const { isLoading, setLoading } = useSkeletonLoading()
      setLoading('', true)
      expect(isLoading('')).toBe(true)
    })
  })

  describe('setLoading Function', () => {
    it('SKEL_024: sets loading state to true', () => {
      const { loadingStates, setLoading } = useSkeletonLoading()
      setLoading('section1', true)
      expect(loadingStates.section1).toBe(true)
    })

    it('SKEL_025: sets loading state to false', () => {
      const { loadingStates, setLoading } = useSkeletonLoading()
      setLoading('section1', true)
      setLoading('section1', false)
      expect(loadingStates.section1).toBe(false)
    })

    it('SKEL_026: can set multiple sections', () => {
      const { loadingStates, setLoading } = useSkeletonLoading()
      setLoading('a', true)
      setLoading('b', true)
      setLoading('c', false)

      expect(loadingStates.a).toBe(true)
      expect(loadingStates.b).toBe(true)
      expect(loadingStates.c).toBe(false)
    })

    it('SKEL_027: overwrites existing state', () => {
      const { loadingStates, setLoading } = useSkeletonLoading(['existing'])
      expect(loadingStates.existing).toBe(true)

      setLoading('existing', false)
      expect(loadingStates.existing).toBe(false)
    })
  })

  describe('startLoading Function', () => {
    it('SKEL_028: sets section to loading', () => {
      const { isLoading, startLoading } = useSkeletonLoading()
      startLoading('section')
      expect(isLoading('section')).toBe(true)
    })

    it('SKEL_029: can start loading on already loading section', () => {
      const { isLoading, startLoading } = useSkeletonLoading(['section'])
      expect(isLoading('section')).toBe(true)
      startLoading('section')
      expect(isLoading('section')).toBe(true)
    })

    it('SKEL_030: starts loading on previously stopped section', () => {
      const { isLoading, startLoading, stopLoading } = useSkeletonLoading()
      startLoading('section')
      stopLoading('section')
      expect(isLoading('section')).toBe(false)

      startLoading('section')
      expect(isLoading('section')).toBe(true)
    })
  })

  describe('stopLoading Function', () => {
    it('SKEL_031: stops loading for section', () => {
      const { isLoading, startLoading, stopLoading } = useSkeletonLoading()
      startLoading('section')
      stopLoading('section')
      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_032: can stop loading on non-loading section', () => {
      const { isLoading, stopLoading } = useSkeletonLoading()
      stopLoading('section')
      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_033: stops loading on default section', () => {
      const { isLoading, stopLoading } = useSkeletonLoading(['section'])
      expect(isLoading('section')).toBe(true)
      stopLoading('section')
      expect(isLoading('section')).toBe(false)
    })
  })

  describe('withLoading Function', () => {
    it('SKEL_034: sets loading before async function', async () => {
      const { isLoading, withLoading } = useSkeletonLoading()
      let loadingDuringExecution = false

      await withLoading('section', async () => {
        loadingDuringExecution = isLoading('section')
      })

      expect(loadingDuringExecution).toBe(true)
    })

    it('SKEL_035: clears loading after async function completes', async () => {
      const { isLoading, withLoading } = useSkeletonLoading()

      await withLoading('section', async () => {
        // Simulate async work
        await new Promise(resolve => setTimeout(resolve, 10))
      })

      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_036: returns result of async function', async () => {
      const { withLoading } = useSkeletonLoading()

      const result = await withLoading('section', async () => {
        return { data: 'test' }
      })

      expect(result).toEqual({ data: 'test' })
    })

    it('SKEL_037: clears loading even when async function throws', async () => {
      const { isLoading, withLoading } = useSkeletonLoading()

      try {
        await withLoading('section', async () => {
          throw new Error('Test error')
        })
      } catch (e) {
        // Expected
      }

      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_038: propagates error from async function', async () => {
      const { withLoading } = useSkeletonLoading()

      await expect(
        withLoading('section', async () => {
          throw new Error('Test error')
        })
      ).rejects.toThrow('Test error')
    })

    it('SKEL_039: handles synchronous function', async () => {
      const { isLoading, withLoading } = useSkeletonLoading()

      const result = await withLoading('section', () => {
        return 42
      })

      expect(result).toBe(42)
      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_040: can run multiple withLoading concurrently', async () => {
      const { isLoading, withLoading } = useSkeletonLoading()

      const promise1 = withLoading('section1', async () => {
        await new Promise(resolve => setTimeout(resolve, 20))
        return 1
      })

      const promise2 = withLoading('section2', async () => {
        await new Promise(resolve => setTimeout(resolve, 10))
        return 2
      })

      // Both should be loading
      expect(isLoading('section1')).toBe(true)
      expect(isLoading('section2')).toBe(true)

      const [result1, result2] = await Promise.all([promise1, promise2])

      expect(result1).toBe(1)
      expect(result2).toBe(2)
      expect(isLoading('section1')).toBe(false)
      expect(isLoading('section2')).toBe(false)
    })
  })

  describe('initLoadingSections Function', () => {
    it('SKEL_041: initializes multiple sections as loading', () => {
      const { isLoading, initLoadingSections } = useSkeletonLoading()

      initLoadingSections(['a', 'b', 'c'])

      expect(isLoading('a')).toBe(true)
      expect(isLoading('b')).toBe(true)
      expect(isLoading('c')).toBe(true)
    })

    it('SKEL_042: does not affect existing sections not in array', () => {
      const { isLoading, setLoading, initLoadingSections } = useSkeletonLoading()

      setLoading('existing', false)
      initLoadingSections(['new1', 'new2'])

      expect(isLoading('existing')).toBe(false)
      expect(isLoading('new1')).toBe(true)
      expect(isLoading('new2')).toBe(true)
    })

    it('SKEL_043: overwrites existing section state', () => {
      const { isLoading, setLoading, initLoadingSections } = useSkeletonLoading()

      setLoading('section', false)
      expect(isLoading('section')).toBe(false)

      initLoadingSections(['section'])
      expect(isLoading('section')).toBe(true)
    })
  })

  describe('anyLoading Function', () => {
    it('SKEL_044: returns false when no sections exist', () => {
      const { anyLoading } = useSkeletonLoading()
      expect(anyLoading()).toBe(false)
    })

    it('SKEL_045: returns true when at least one section is loading', () => {
      const { anyLoading, setLoading } = useSkeletonLoading()

      setLoading('a', false)
      setLoading('b', true)
      setLoading('c', false)

      expect(anyLoading()).toBe(true)
    })

    it('SKEL_046: returns false when all sections finished loading', () => {
      const { anyLoading, setLoading } = useSkeletonLoading()

      setLoading('a', false)
      setLoading('b', false)
      setLoading('c', false)

      expect(anyLoading()).toBe(false)
    })

    it('SKEL_047: returns true for default sections initially', () => {
      const { anyLoading } = useSkeletonLoading(['section1', 'section2'])
      expect(anyLoading()).toBe(true)
    })
  })

  describe('allLoaded Function', () => {
    it('SKEL_048: returns true when no sections exist', () => {
      const { allLoaded } = useSkeletonLoading()
      expect(allLoaded()).toBe(true)
    })

    it('SKEL_049: returns false when any section is still loading', () => {
      const { allLoaded, setLoading } = useSkeletonLoading()

      setLoading('a', false)
      setLoading('b', true)

      expect(allLoaded()).toBe(false)
    })

    it('SKEL_050: returns true when all sections finished loading', () => {
      const { allLoaded, setLoading } = useSkeletonLoading()

      setLoading('a', false)
      setLoading('b', false)
      setLoading('c', false)

      expect(allLoaded()).toBe(true)
    })

    it('SKEL_051: returns false for default sections initially', () => {
      const { allLoaded } = useSkeletonLoading(['section1'])
      expect(allLoaded()).toBe(false)
    })

    it('SKEL_052: returns true after stopping all default sections', () => {
      const { allLoaded, stopLoading } = useSkeletonLoading(['a', 'b'])

      stopLoading('a')
      stopLoading('b')

      expect(allLoaded()).toBe(true)
    })
  })

  describe('Multiple Instances', () => {
    it('SKEL_053: each instance has isolated state', () => {
      const instance1 = useSkeletonLoading()
      const instance2 = useSkeletonLoading()

      instance1.setLoading('section', true)

      expect(instance1.isLoading('section')).toBe(true)
      expect(instance2.isLoading('section')).toBe(false)
    })

    it('SKEL_054: instances do not share loadingStates', () => {
      const instance1 = useSkeletonLoading(['shared'])
      const instance2 = useSkeletonLoading()

      expect(instance1.isLoading('shared')).toBe(true)
      expect(instance2.isLoading('shared')).toBe(false)
    })

    it('SKEL_055: changes in one instance do not affect another', () => {
      const instance1 = useSkeletonLoading(['section'])
      const instance2 = useSkeletonLoading(['section'])

      instance1.stopLoading('section')

      expect(instance1.isLoading('section')).toBe(false)
      expect(instance2.isLoading('section')).toBe(true)
    })
  })

  describe('Edge Cases', () => {
    it('SKEL_056: handles section names with special characters', () => {
      const { isLoading, setLoading } = useSkeletonLoading()

      setLoading('section-with-dash', true)
      setLoading('section.with.dots', true)
      setLoading('section:with:colons', true)

      expect(isLoading('section-with-dash')).toBe(true)
      expect(isLoading('section.with.dots')).toBe(true)
      expect(isLoading('section:with:colons')).toBe(true)
    })

    it('SKEL_057: handles numeric section names', () => {
      const { isLoading, setLoading } = useSkeletonLoading()

      setLoading('123', true)
      setLoading('456', false)

      expect(isLoading('123')).toBe(true)
      expect(isLoading('456')).toBe(false)
    })

    it('SKEL_058: handles rapid state changes', () => {
      const { isLoading, setLoading } = useSkeletonLoading()

      for (let i = 0; i < 100; i++) {
        setLoading('section', i % 2 === 0)
      }

      // Last iteration: 99 % 2 === 1, so false
      expect(isLoading('section')).toBe(false)
    })

    it('SKEL_059: loadingStates is reactive', () => {
      const { loadingStates, setLoading } = useSkeletonLoading()

      setLoading('test', true)
      expect(loadingStates.test).toBe(true)

      setLoading('test', false)
      expect(loadingStates.test).toBe(false)
    })

    it('SKEL_060: can delete section from loadingStates', () => {
      const { loadingStates, setLoading, isLoading } = useSkeletonLoading()

      setLoading('toDelete', true)
      expect(isLoading('toDelete')).toBe(true)

      delete loadingStates.toDelete
      expect(isLoading('toDelete')).toBe(false)
    })
  })
})
