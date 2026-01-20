/**
 * Ranker Features Composable
 *
 * Handles feature grouping, localStorage persistence, and feature ordering.
 * Extracted from RankerDetail.vue for better maintainability.
 *
 * IMPORTANT: Features are always loaded from the server.
 * localStorage only stores bucket assignments (feature_id -> bucket mapping)
 * to preserve user's ranking progress between page reloads.
 */

import { ref } from 'vue';

const STORAGE_KEY = 'rankerDetail_buckets';

export function useRankerFeatures() {
  const features = ref([]);
  const groupedFeatures = ref([]);
  const localStorageKey = ref('');
  const ranked = ref(null);

  /**
   * Save bucket assignments to localStorage.
   * Only stores feature_id -> bucket mapping, NOT feature content.
   */
  function saveToLocalStorage(threadId) {
    const key = `${STORAGE_KEY}_${threadId}`;
    const bucketAssignments = {};

    groupedFeatures.value.forEach(group => {
      group.goodList.forEach((f, idx) => {
        bucketAssignments[f.feature_id] = { bucket: 'good', position: idx };
      });
      group.averageList.forEach((f, idx) => {
        bucketAssignments[f.feature_id] = { bucket: 'average', position: idx };
      });
      group.badList.forEach((f, idx) => {
        bucketAssignments[f.feature_id] = { bucket: 'bad', position: idx };
      });
      // neutral items don't need to be saved (default state)
    });

    localStorage.setItem(key, JSON.stringify(bucketAssignments));
  }

  /**
   * Get bucket assignments from localStorage.
   * Returns a map of feature_id -> {bucket, position} or null if no data.
   */
  function getBucketAssignments(threadId) {
    const key = `${STORAGE_KEY}_${threadId}`;
    const savedData = localStorage.getItem(key);

    if (savedData) {
      try {
        return JSON.parse(savedData);
      } catch (e) {
        console.warn('Failed to parse localStorage bucket assignments:', e);
        return null;
      }
    }
    return null;
  }

  /**
   * Apply localStorage bucket assignments to server-fetched features.
   * Features are matched by feature_id. Unknown features go to neutral.
   */
  function applyLocalStorageBuckets(featureMap, threadId) {
    const bucketAssignments = getBucketAssignments(threadId);
    if (!bucketAssignments) return featureMap;

    // Redistribute features based on saved bucket assignments
    featureMap.forEach((group, type) => {
      const allFeatures = [
        ...group.goodList,
        ...group.averageList,
        ...group.badList,
        ...group.neutralList
      ];

      // Reset lists
      group.goodList = [];
      group.averageList = [];
      group.badList = [];
      group.neutralList = [];

      // Sort features into buckets based on saved assignments
      allFeatures.forEach(feature => {
        const assignment = bucketAssignments[feature.feature_id];
        if (assignment) {
          if (assignment.bucket === 'good') {
            group.goodList.push({ ...feature, position: assignment.position });
          } else if (assignment.bucket === 'average') {
            group.averageList.push({ ...feature, position: assignment.position });
          } else if (assignment.bucket === 'bad') {
            group.badList.push({ ...feature, position: assignment.position });
          } else {
            group.neutralList.push(feature);
          }
        } else {
          // No saved assignment -> neutral
          group.neutralList.push(feature);
        }
      });

      // Sort by position within each bucket
      group.goodList.sort((a, b) => (a.position || 0) - (b.position || 0));
      group.averageList.sort((a, b) => (a.position || 0) - (b.position || 0));
      group.badList.sort((a, b) => (a.position || 0) - (b.position || 0));
    });

    return featureMap;
  }

  /**
   * @deprecated Use applyLocalStorageBuckets instead.
   * Kept for backwards compatibility during transition.
   */
  function loadFromLocalStorage(threadId) {
    // This function no longer directly loads features.
    // Return false to force server fetch.
    return false;
  }

  // Group features by type
  function groupFeaturesByType(featureList) {
    const featureMap = new Map();
    featureList.forEach((f, index) => {
      if (!featureMap.has(f.type)) {
        featureMap.set(f.type, {
          type: f.type,
          goodList: [],
          averageList: [],
          badList: [],
          neutralList: []
        });
      }

      // Place feature initially in neutral list
      featureMap.get(f.type).neutralList.push({
        model_name: f.model_name,
        content: f.content,
        feature_id: f.feature_id,
        position: index,
        minimized: true,
      });
    });
    return featureMap;
  }

  // Apply server ranking to feature map
  function applyServerRanking(featureMap, serverRanking) {
    serverRanking.forEach(serverGroup => {
      if (featureMap.has(serverGroup.type)) {
        featureMap.get(serverGroup.type).goodList = serverGroup.goodList || [];
        featureMap.get(serverGroup.type).averageList = serverGroup.averageList || [];
        featureMap.get(serverGroup.type).badList = serverGroup.badList || [];
        featureMap.get(serverGroup.type).neutralList = serverGroup.neutralList || [];
      }
    });
    return featureMap;
  }

  // Apply feature order from saved data
  function applyFeatureOrder(orderedFeatures) {
    const featureMap = new Map();

    orderedFeatures.forEach(f => {
      if (!featureMap.has(f.type)) {
        featureMap.set(f.type, {
          type: f.type,
          goodList: [],
          averageList: [],
          badList: [],
          neutralList: []
        });
      }

      f.details.forEach(detail => {
        const featureGroup = featureMap.get(f.type);

        if (detail.bucket === 'Gut') {
          featureGroup.goodList.push(detail);
        } else if (detail.bucket === 'Mittel') {
          featureGroup.averageList.push(detail);
        } else if (detail.bucket === 'Schlecht') {
          featureGroup.badList.push(detail);
        } else {
          featureGroup.neutralList.push(detail);
        }
      });
    });

    groupedFeatures.value = Array.from(featureMap.values());
  }

  // Save feature order to localStorage
  function saveFeatureOrderToLocalStorage() {
    const orderedFeatures = groupedFeatures.value.map(group => ({
      type: group.type,
      details: group.details?.map((detail, index) => ({
        model_name: detail.model_name,
        content: detail.content,
        feature_id: detail.feature_id,
        position: index
      })) || []
    }));
    localStorage.setItem(localStorageKey.value, JSON.stringify(orderedFeatures));
  }

  // Prepare features for server save
  function prepareForServerSave() {
    return groupedFeatures.value.map(group => {
      return {
        type: group.type,
        details: [
          ...group.goodList.map((detail, index) => ({
            model_name: detail.model_name,
            content: detail.content,
            position: index,
            bucket: 'Gut'
          })),
          ...group.averageList.map((detail, index) => ({
            model_name: detail.model_name,
            content: detail.content,
            position: index,
            bucket: 'Mittel'
          })),
          ...group.badList.map((detail, index) => ({
            model_name: detail.model_name,
            content: detail.content,
            position: index,
            bucket: 'Schlecht'
          }))
        ]
      };
    });
  }

  return {
    // State
    features,
    groupedFeatures,
    localStorageKey,
    ranked,

    // Methods
    saveToLocalStorage,
    loadFromLocalStorage,  // deprecated, always returns false
    applyLocalStorageBuckets,
    groupFeaturesByType,
    applyServerRanking,
    applyFeatureOrder,
    saveFeatureOrderToLocalStorage,
    prepareForServerSave
  };
}
