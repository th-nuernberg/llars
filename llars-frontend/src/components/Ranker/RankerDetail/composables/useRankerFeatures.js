/**
 * Ranker Features Composable
 *
 * Handles feature grouping, localStorage persistence, and feature ordering.
 * Extracted from RankerDetail.vue for better maintainability.
 */

import { ref } from 'vue';

const STORAGE_KEY = 'rankerDetail_data';

export function useRankerFeatures() {
  const features = ref([]);
  const groupedFeatures = ref([]);
  const localStorageKey = ref('');
  const ranked = ref(null);

  // Save to LocalStorage with threadId
  function saveToLocalStorage(threadId) {
    const key = `${STORAGE_KEY}_${threadId}`;
    const data = groupedFeatures.value.map(group => ({
      type: group.type,
      goodList: group.goodList,
      averageList: group.averageList,
      badList: group.badList,
      neutralList: group.neutralList,
    }));
    localStorage.setItem(key, JSON.stringify(data));
  }

  // Load from LocalStorage with threadId
  function loadFromLocalStorage(threadId) {
    const key = `${STORAGE_KEY}_${threadId}`;
    const savedData = localStorage.getItem(key);

    if (savedData) {
      const parsedData = JSON.parse(savedData);
      groupedFeatures.value = parsedData.map(group => ({
        type: group.type,
        goodList: group.goodList || [],
        averageList: group.averageList || [],
        badList: group.badList || [],
        neutralList: group.neutralList || []
      }));
      return true;
    }
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
    loadFromLocalStorage,
    groupFeaturesByType,
    applyServerRanking,
    applyFeatureOrder,
    saveFeatureOrderToLocalStorage,
    prepareForServerSave
  };
}
