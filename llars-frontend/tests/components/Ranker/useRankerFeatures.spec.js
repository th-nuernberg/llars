/**
 * useRankerFeatures Composable Tests
 *
 * Tests for feature grouping, bucket assignment, localStorage persistence, and server save.
 * Test IDs: RANK_FEAT_001 - RANK_FEAT_045
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useRankerFeatures } from '@/components/Ranker/RankerDetail/composables/useRankerFeatures'

describe('useRankerFeatures', () => {
  let rf

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.getItem.mockReturnValue(null)
    localStorage.setItem.mockClear()
    rf = useRankerFeatures()
  })

  // ==================== Initial State Tests ====================

  describe('initial state', () => {
    it('RANK_FEAT_001: starts with empty features', () => {
      expect(rf.features.value).toEqual([])
    })

    it('RANK_FEAT_002: starts with empty groupedFeatures', () => {
      expect(rf.groupedFeatures.value).toEqual([])
    })

    it('RANK_FEAT_003: starts with empty localStorageKey', () => {
      expect(rf.localStorageKey.value).toBe('')
    })

    it('RANK_FEAT_004: starts with null ranked', () => {
      expect(rf.ranked.value).toBeNull()
    })
  })

  // ==================== groupFeaturesByType Tests ====================

  describe('groupFeaturesByType', () => {
    it('RANK_FEAT_005: groups features by type', () => {
      const features = [
        { type: 'summary', model_name: 'gpt-4', content: 'Summary 1', feature_id: 'f1' },
        { type: 'summary', model_name: 'claude', content: 'Summary 2', feature_id: 'f2' },
        { type: 'translation', model_name: 'gpt-4', content: 'Trans 1', feature_id: 'f3' }
      ]

      const featureMap = rf.groupFeaturesByType(features)

      expect(featureMap.size).toBe(2)
      expect(featureMap.has('summary')).toBe(true)
      expect(featureMap.has('translation')).toBe(true)
    })

    it('RANK_FEAT_006: places all features in neutralList initially', () => {
      const features = [
        { type: 'summary', model_name: 'gpt-4', content: 'S1', feature_id: 'f1' },
        { type: 'summary', model_name: 'claude', content: 'S2', feature_id: 'f2' }
      ]

      const featureMap = rf.groupFeaturesByType(features)
      const summaryGroup = featureMap.get('summary')

      expect(summaryGroup.neutralList).toHaveLength(2)
      expect(summaryGroup.goodList).toHaveLength(0)
      expect(summaryGroup.averageList).toHaveLength(0)
      expect(summaryGroup.badList).toHaveLength(0)
    })

    it('RANK_FEAT_007: sets minimized to true for all features', () => {
      const features = [
        { type: 'test', model_name: 'm', content: 'c', feature_id: 'f1' }
      ]
      const featureMap = rf.groupFeaturesByType(features)
      expect(featureMap.get('test').neutralList[0].minimized).toBe(true)
    })

    it('RANK_FEAT_008: preserves feature data (model_name, content, feature_id)', () => {
      const features = [
        { type: 'test', model_name: 'gpt-4', content: 'Test content', feature_id: 'abc123' }
      ]
      const featureMap = rf.groupFeaturesByType(features)
      const feature = featureMap.get('test').neutralList[0]
      expect(feature.model_name).toBe('gpt-4')
      expect(feature.content).toBe('Test content')
      expect(feature.feature_id).toBe('abc123')
    })

    it('RANK_FEAT_009: handles empty feature list', () => {
      const featureMap = rf.groupFeaturesByType([])
      expect(featureMap.size).toBe(0)
    })
  })

  // ==================== applyServerRanking Tests ====================

  describe('applyServerRanking', () => {
    it('RANK_FEAT_010: applies new format with details array', () => {
      const features = [
        { type: 'summary', model_name: 'gpt-4', content: 'Good one', feature_id: 'f1' },
        { type: 'summary', model_name: 'claude', content: 'Average', feature_id: 'f2' },
        { type: 'summary', model_name: 'llama', content: 'Bad', feature_id: 'f3' }
      ]

      const featureMap = rf.groupFeaturesByType(features)

      const serverRanking = [{
        type: 'summary',
        details: [
          { feature_id: 'f1', content: 'Good one', bucket: 'Gut' },
          { feature_id: 'f2', content: 'Average', bucket: 'Mittel' },
          { feature_id: 'f3', content: 'Bad', bucket: 'Schlecht' }
        ]
      }]

      rf.applyServerRanking(featureMap, serverRanking)

      const group = featureMap.get('summary')
      expect(group.goodList).toHaveLength(1)
      expect(group.averageList).toHaveLength(1)
      expect(group.badList).toHaveLength(1)
      expect(group.goodList[0].feature_id).toBe('f1')
    })

    it('RANK_FEAT_011: applies legacy format with direct lists', () => {
      const features = [
        { type: 'test', model_name: 'm', content: 'c', feature_id: 'f1' }
      ]
      const featureMap = rf.groupFeaturesByType(features)

      const serverRanking = [{
        type: 'test',
        goodList: [{ model_name: 'm', content: 'c', feature_id: 'f1' }],
        averageList: [],
        badList: [],
        neutralList: []
      }]

      rf.applyServerRanking(featureMap, serverRanking)
      expect(featureMap.get('test').goodList).toHaveLength(1)
    })

    it('RANK_FEAT_012: puts unmatched features in neutral', () => {
      const features = [
        { type: 'sum', model_name: 'a', content: 'A', feature_id: 'f1' },
        { type: 'sum', model_name: 'b', content: 'B', feature_id: 'f2' }
      ]
      const featureMap = rf.groupFeaturesByType(features)

      // Server only placed f1
      const serverRanking = [{
        type: 'sum',
        details: [
          { feature_id: 'f1', content: 'A', bucket: 'Gut' }
        ]
      }]

      rf.applyServerRanking(featureMap, serverRanking)
      const group = featureMap.get('sum')
      expect(group.goodList).toHaveLength(1)
      expect(group.neutralList).toHaveLength(1)
      expect(group.neutralList[0].feature_id).toBe('f2')
    })

    it('RANK_FEAT_013: handles unknown types gracefully', () => {
      const features = [
        { type: 'summary', model_name: 'm', content: 'c', feature_id: 'f1' }
      ]
      const featureMap = rf.groupFeaturesByType(features)

      // Server sends different type
      const serverRanking = [{
        type: 'nonexistent',
        details: [{ feature_id: 'x', bucket: 'Gut' }]
      }]

      // Should not throw
      rf.applyServerRanking(featureMap, serverRanking)
      // Original data unchanged
      expect(featureMap.get('summary').neutralList).toHaveLength(1)
    })
  })

  // ==================== saveToLocalStorage Tests ====================

  describe('saveToLocalStorage', () => {
    it('RANK_FEAT_014: saves bucket assignments to localStorage', () => {
      rf.groupedFeatures.value = [{
        type: 'summary',
        goodList: [{ feature_id: 'f1' }],
        averageList: [{ feature_id: 'f2' }],
        badList: [{ feature_id: 'f3' }]
      }]

      rf.saveToLocalStorage('thread-123')

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'rankerDetail_buckets_thread-123',
        expect.any(String)
      )

      const savedData = JSON.parse(localStorage.setItem.mock.calls[0][1])
      expect(savedData.f1).toEqual({ bucket: 'good', position: 0 })
      expect(savedData.f2).toEqual({ bucket: 'average', position: 0 })
      expect(savedData.f3).toEqual({ bucket: 'bad', position: 0 })
    })

    it('RANK_FEAT_015: saves correct positions for multiple items', () => {
      rf.groupedFeatures.value = [{
        type: 'summary',
        goodList: [{ feature_id: 'f1' }, { feature_id: 'f2' }],
        averageList: [],
        badList: []
      }]

      rf.saveToLocalStorage('t1')
      const savedData = JSON.parse(localStorage.setItem.mock.calls[0][1])
      expect(savedData.f1.position).toBe(0)
      expect(savedData.f2.position).toBe(1)
    })
  })

  // ==================== getBucketAssignments Tests ====================

  describe('getBucketAssignments (via applyLocalStorageBuckets)', () => {
    it('RANK_FEAT_016: returns null when no saved data', () => {
      localStorage.getItem.mockReturnValue(null)
      const features = [{ type: 'test', model_name: 'm', content: 'c', feature_id: 'f1' }]
      const featureMap = rf.groupFeaturesByType(features)
      const result = rf.applyLocalStorageBuckets(featureMap, 'thread-1')
      // Should return unchanged
      expect(result.get('test').neutralList).toHaveLength(1)
    })

    it('RANK_FEAT_017: applies saved bucket assignments', () => {
      const savedAssignments = {
        f1: { bucket: 'good', position: 0 },
        f2: { bucket: 'bad', position: 0 }
      }
      localStorage.getItem.mockReturnValue(JSON.stringify(savedAssignments))

      const features = [
        { type: 'test', model_name: 'a', content: 'A', feature_id: 'f1' },
        { type: 'test', model_name: 'b', content: 'B', feature_id: 'f2' },
        { type: 'test', model_name: 'c', content: 'C', feature_id: 'f3' }
      ]
      const featureMap = rf.groupFeaturesByType(features)
      rf.applyLocalStorageBuckets(featureMap, 'thread-1')

      const group = featureMap.get('test')
      expect(group.goodList).toHaveLength(1)
      expect(group.goodList[0].feature_id).toBe('f1')
      expect(group.badList).toHaveLength(1)
      expect(group.badList[0].feature_id).toBe('f2')
      expect(group.neutralList).toHaveLength(1)
      expect(group.neutralList[0].feature_id).toBe('f3')
    })

    it('RANK_FEAT_018: handles corrupted localStorage gracefully', () => {
      localStorage.getItem.mockReturnValue('invalid json{{{')
      const features = [{ type: 'test', model_name: 'm', content: 'c', feature_id: 'f1' }]
      const featureMap = rf.groupFeaturesByType(features)
      // Should not throw
      rf.applyLocalStorageBuckets(featureMap, 'thread-1')
      expect(featureMap.get('test').neutralList).toHaveLength(1)
    })

    it('RANK_FEAT_019: sorts by saved position within buckets', () => {
      const saved = {
        f1: { bucket: 'good', position: 1 },
        f2: { bucket: 'good', position: 0 }
      }
      localStorage.getItem.mockReturnValue(JSON.stringify(saved))

      const features = [
        { type: 't', model_name: 'a', content: 'A', feature_id: 'f1' },
        { type: 't', model_name: 'b', content: 'B', feature_id: 'f2' }
      ]
      const featureMap = rf.groupFeaturesByType(features)
      rf.applyLocalStorageBuckets(featureMap, 'x')

      const group = featureMap.get('t')
      expect(group.goodList[0].feature_id).toBe('f2') // position 0 first
      expect(group.goodList[1].feature_id).toBe('f1') // position 1 second
    })
  })

  // ==================== loadFromLocalStorage Tests ====================

  describe('loadFromLocalStorage (deprecated)', () => {
    it('RANK_FEAT_020: always returns false', () => {
      expect(rf.loadFromLocalStorage('any')).toBe(false)
    })
  })

  // ==================== applyFeatureOrder Tests ====================

  describe('applyFeatureOrder', () => {
    it('RANK_FEAT_021: applies ordered features to groupedFeatures', () => {
      const ordered = [
        {
          type: 'summary',
          details: [
            { model_name: 'gpt-4', content: 'Good', feature_id: 'f1', bucket: 'Gut' },
            { model_name: 'claude', content: 'Mid', feature_id: 'f2', bucket: 'Mittel' },
            { model_name: 'llama', content: 'Bad', feature_id: 'f3', bucket: 'Schlecht' }
          ]
        }
      ]

      rf.applyFeatureOrder(ordered)

      expect(rf.groupedFeatures.value).toHaveLength(1)
      expect(rf.groupedFeatures.value[0].goodList).toHaveLength(1)
      expect(rf.groupedFeatures.value[0].averageList).toHaveLength(1)
      expect(rf.groupedFeatures.value[0].badList).toHaveLength(1)
    })

    it('RANK_FEAT_022: handles neutral bucket', () => {
      const ordered = [
        {
          type: 'test',
          details: [
            { model_name: 'm', content: 'c', feature_id: 'f1', bucket: 'Neutral' }
          ]
        }
      ]

      rf.applyFeatureOrder(ordered)
      expect(rf.groupedFeatures.value[0].neutralList).toHaveLength(1)
    })

    it('RANK_FEAT_023: handles multiple types', () => {
      const ordered = [
        { type: 'summary', details: [{ feature_id: 'f1', bucket: 'Gut' }] },
        { type: 'translation', details: [{ feature_id: 'f2', bucket: 'Mittel' }] }
      ]

      rf.applyFeatureOrder(ordered)
      expect(rf.groupedFeatures.value).toHaveLength(2)
    })
  })

  // ==================== prepareForServerSave Tests ====================

  describe('prepareForServerSave', () => {
    it('RANK_FEAT_024: formats data for server', () => {
      rf.groupedFeatures.value = [{
        type: 'summary',
        goodList: [{ model_name: 'gpt-4', content: 'Good content' }],
        averageList: [{ model_name: 'claude', content: 'Mid content' }],
        badList: [{ model_name: 'llama', content: 'Bad content' }]
      }]

      const result = rf.prepareForServerSave()

      expect(result).toHaveLength(1)
      expect(result[0].type).toBe('summary')
      expect(result[0].details).toHaveLength(3)

      const good = result[0].details.find(d => d.bucket === 'Gut')
      expect(good.model_name).toBe('gpt-4')
      expect(good.position).toBe(0)

      const mid = result[0].details.find(d => d.bucket === 'Mittel')
      expect(mid.model_name).toBe('claude')

      const bad = result[0].details.find(d => d.bucket === 'Schlecht')
      expect(bad.model_name).toBe('llama')
    })

    it('RANK_FEAT_025: assigns correct positions within buckets', () => {
      rf.groupedFeatures.value = [{
        type: 'test',
        goodList: [
          { model_name: 'a', content: 'A' },
          { model_name: 'b', content: 'B' }
        ],
        averageList: [],
        badList: []
      }]

      const result = rf.prepareForServerSave()
      const details = result[0].details
      expect(details[0].position).toBe(0)
      expect(details[1].position).toBe(1)
    })

    it('RANK_FEAT_026: handles empty groups', () => {
      rf.groupedFeatures.value = [{
        type: 'empty',
        goodList: [],
        averageList: [],
        badList: []
      }]

      const result = rf.prepareForServerSave()
      expect(result[0].details).toHaveLength(0)
    })

    it('RANK_FEAT_027: does not include neutral items in server save', () => {
      rf.groupedFeatures.value = [{
        type: 'test',
        goodList: [{ model_name: 'a', content: 'A' }],
        averageList: [],
        badList: [],
        neutralList: [{ model_name: 'b', content: 'B' }]
      }]

      const result = rf.prepareForServerSave()
      expect(result[0].details).toHaveLength(1)
      expect(result[0].details[0].bucket).toBe('Gut')
    })
  })
})
