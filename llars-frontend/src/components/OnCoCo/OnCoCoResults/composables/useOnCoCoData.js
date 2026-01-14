/**
 * OnCoCo Data Composable
 *
 * Handles loading distribution, transitions, heatmaps, comparison data.
 * Extracted from OnCoCoResults.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useOnCoCoData(analysisId, analysisRef) {
  // Distribution State
  const distributionPillar = ref(null);
  const distributionLevel = ref('level2');
  const distributionRole = ref('');
  const distributionData = ref([]);
  const loadingDistribution = ref(false);

  // Transitions State
  const transitionPillar = ref(null);
  const transitionLevel = ref('level2');
  const transitionRole = ref('');
  const transitionsData = ref({ links: [] });
  const loadingTransitions = ref(false);

  // Heatmap State
  const heatmapData = ref({});
  const loadingHeatmaps = ref(false);
  const showHeatmapValues = ref(false);
  const heatmapColorMode = ref('count');

  // Synchronized hover state
  const hoveredTransition = ref(null);

  // Comparison State
  const comparisonData = ref([]);
  const loadingComparison = ref(false);

  // Matrix Comparison State
  const matrixComparisonData = ref(null);
  const loadingMatrixComparison = ref(false);

  // Sentences State
  const sentencePillar = ref(null);
  const sentenceRole = ref('');
  const sentenceLabel = ref('');
  const sentences = ref([]);
  const sentencesTotal = ref(0);
  const sentencesOffset = ref(0);
  const loadingSentences = ref(false);

  // Computed
  const maxDistributionCount = computed(() => {
    if (distributionData.value.length === 0) return 1;
    return Math.max(...distributionData.value.map(d => d.count));
  });

  const topTransitions = computed(() => {
    return transitionsData.value.links?.slice(0, 20) || [];
  });

  const roleFilterOptions = computed(() => [
    { title: 'Alle (Berater & Ratsuchend)', value: '' },
    { title: 'Nur Berater', value: 'counselor' },
    { title: 'Nur Ratsuchend', value: 'client' }
  ]);

  // Quick Stats Computed Properties
  const quickStatsSimilarity = computed(() => {
    if (!matrixComparisonData.value?.pairwise_comparisons?.length) return 0;
    const comparisons = matrixComparisonData.value.pairwise_comparisons;
    const avgNormFrob = comparisons.reduce((sum, c) => sum + (c.effect_size?.normalized_frobenius || 0), 0) / comparisons.length;
    return Math.max(0, 1 - avgNormFrob);
  });

  const quickStatsFrobenius = computed(() => {
    if (!matrixComparisonData.value?.pairwise_comparisons?.length) return 0;
    const comparisons = matrixComparisonData.value.pairwise_comparisons;
    return comparisons.reduce((sum, c) => sum + (c.metrics?.frobenius_distance || 0), 0) / comparisons.length;
  });

  const quickStatsPValue = computed(() => {
    if (!matrixComparisonData.value?.pairwise_comparisons?.length) return 1;
    const comparisons = matrixComparisonData.value.pairwise_comparisons;
    return Math.min(...comparisons.map(c => c.statistical_tests?.permutation_test?.p_value || 1));
  });

  const quickStatsChiSignificant = computed(() => {
    if (!matrixComparisonData.value?.pairwise_comparisons?.length) return 0;
    const comparisons = matrixComparisonData.value.pairwise_comparisons;
    return comparisons.reduce((sum, c) => sum + (c.statistical_tests?.chi_square?.significant_rows || 0), 0);
  });

  const quickStatsChiTotal = computed(() => {
    if (!matrixComparisonData.value?.pairwise_comparisons?.length) return 0;
    const comparisons = matrixComparisonData.value.pairwise_comparisons;
    return comparisons.reduce((sum, c) => sum + (c.statistical_tests?.chi_square?.total_rows || 0), 0);
  });

  // Methods
  const loadDistribution = async () => {
    loadingDistribution.value = true;
    try {
      const params = new URLSearchParams();
      if (distributionPillar.value) params.append('pillar', distributionPillar.value);
      params.append('level', distributionLevel.value);
      if (distributionRole.value) params.append('role', distributionRole.value);

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/distribution?${params}`
      );
      distributionData.value = response.data.distribution || [];
    } catch (error) {
      console.error('Fehler beim Laden der Verteilung:', error);
    } finally {
      loadingDistribution.value = false;
    }
  };

  const loadTransitions = async () => {
    loadingTransitions.value = true;
    try {
      const params = new URLSearchParams();
      if (transitionPillar.value) params.append('pillar', transitionPillar.value);
      params.append('level', transitionLevel.value);
      if (transitionRole.value) params.append('role', transitionRole.value);
      params.append('format', 'list');

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/transition-matrix?${params}`
      );
      transitionsData.value = response.data;
    } catch (error) {
      console.error('Fehler beim Laden der Uebergaenge:', error);
    } finally {
      loadingTransitions.value = false;
    }
  };

  const loadHeatmaps = async () => {
    if (!analysisRef.value?.config?.pillars) return;

    loadingHeatmaps.value = true;
    heatmapData.value = {};

    try {
      const pillars = analysisRef.value.config.pillars;
      const level = transitionLevel.value;
      const role = transitionRole.value;

      const promises = pillars.map(async (pillarNum) => {
        const params = new URLSearchParams();
        params.append('pillar', pillarNum);
        params.append('level', level);
        if (role) params.append('role', role);
        params.append('format', 'matrix');

        const response = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/transition-matrix?${params}`
        );

        return { pillarNum, data: response.data };
      });

      const results = await Promise.all(promises);

      const newData = {};
      for (const { pillarNum, data } of results) {
        newData[pillarNum] = {
          labels: data.labels || [],
          labelDisplays: data.label_displays || {},
          counts: data.counts || {},
          probabilities: data.probabilities || {},
          totalTransitions: data.total_transitions || 0
        };
      }
      heatmapData.value = newData;
    } catch (error) {
      console.error('Fehler beim Laden der Heatmaps:', error);
    } finally {
      loadingHeatmaps.value = false;
    }
  };

  const loadComparison = async () => {
    loadingComparison.value = true;
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/comparison`
      );
      comparisonData.value = response.data.pillars || [];
    } catch (error) {
      console.error('Fehler beim Laden des Vergleichs:', error);
    } finally {
      loadingComparison.value = false;
    }
  };

  const loadMatrixComparison = async () => {
    loadingMatrixComparison.value = true;
    try {
      const params = new URLSearchParams();
      params.append('level', transitionLevel.value);
      if (transitionRole.value) params.append('role', transitionRole.value);

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/matrix-comparison?${params}`
      );
      matrixComparisonData.value = response.data;
    } catch (error) {
      console.error('Fehler beim Laden des Matrixvergleichs:', error);
      matrixComparisonData.value = null;
    } finally {
      loadingMatrixComparison.value = false;
    }
  };

  const loadSentences = async (reset = true) => {
    loadingSentences.value = true;
    if (reset) {
      sentences.value = [];
      sentencesOffset.value = 0;
    }

    try {
      const params = new URLSearchParams();
      if (sentencePillar.value) params.append('pillar', sentencePillar.value);
      if (sentenceRole.value) params.append('role', sentenceRole.value);
      if (sentenceLabel.value) params.append('label', sentenceLabel.value);
      params.append('limit', '50');
      params.append('offset', sentencesOffset.value);

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId.value}/sentences?${params}`
      );

      if (reset) {
        sentences.value = response.data.sentences || [];
      } else {
        sentences.value = [...sentences.value, ...(response.data.sentences || [])];
      }
      sentencesTotal.value = response.data.total || 0;
      sentencesOffset.value += response.data.sentences?.length || 0;
    } catch (error) {
      console.error('Fehler beim Laden der Saetze:', error);
    } finally {
      loadingSentences.value = false;
    }
  };

  const loadMoreSentences = () => {
    loadSentences(false);
  };

  const loadAllData = async () => {
    await loadDistribution();
    await loadTransitions();
    await loadHeatmaps();
    await loadComparison();
    await loadMatrixComparison();
  };

  // Heatmap helpers
  const getTransitionCount = (pillarNum, from, to) => {
    return heatmapData.value[pillarNum]?.counts?.[from]?.[to] || 0;
  };

  const getTransitionProbability = (pillarNum, from, to) => {
    return heatmapData.value[pillarNum]?.probabilities?.[from]?.[to] || 0;
  };

  const onHeatmapCellHover = (data) => {
    const fromDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.from] || data.from;
    const toDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.to] || data.to;
    hoveredTransition.value = {
      from: data.from,
      to: data.to,
      fromDisplay,
      toDisplay,
      pillar: data.pillar
    };
  };

  const onHeatmapCellLeave = () => {
    hoveredTransition.value = null;
  };

  const onHighlightTransition = (transition) => {
    if (transition) {
      hoveredTransition.value = {
        from: transition.from_label,
        to: transition.to_label,
        fromDisplay: transition.from_display || transition.from_label,
        toDisplay: transition.to_display || transition.to_label,
        pillar: null
      };
    } else {
      hoveredTransition.value = null;
    }
  };

  return {
    // Distribution State
    distributionPillar,
    distributionLevel,
    distributionRole,
    distributionData,
    loadingDistribution,
    maxDistributionCount,

    // Transitions State
    transitionPillar,
    transitionLevel,
    transitionRole,
    transitionsData,
    loadingTransitions,
    topTransitions,

    // Heatmap State
    heatmapData,
    loadingHeatmaps,
    showHeatmapValues,
    heatmapColorMode,
    hoveredTransition,

    // Comparison State
    comparisonData,
    loadingComparison,
    matrixComparisonData,
    loadingMatrixComparison,

    // Sentences State
    sentencePillar,
    sentenceRole,
    sentenceLabel,
    sentences,
    sentencesTotal,
    loadingSentences,

    // Computed
    roleFilterOptions,
    quickStatsSimilarity,
    quickStatsFrobenius,
    quickStatsPValue,
    quickStatsChiSignificant,
    quickStatsChiTotal,

    // Methods
    loadDistribution,
    loadTransitions,
    loadHeatmaps,
    loadComparison,
    loadMatrixComparison,
    loadSentences,
    loadMoreSentences,
    loadAllData,
    getTransitionCount,
    getTransitionProbability,
    onHeatmapCellHover,
    onHeatmapCellLeave,
    onHighlightTransition
  };
}
