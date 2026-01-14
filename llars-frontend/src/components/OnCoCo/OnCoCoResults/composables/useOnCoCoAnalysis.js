import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

/**
 * Composable for managing OnCoCo analysis state and API calls
 *
 * @param {string|number} analysisId - The analysis ID to load
 * @returns {Object} Analysis state and functions
 */
export function useOnCoCoAnalysis(analysisId) {
  const { t } = useI18n();
  // ========================================
  // State
  // ========================================

  // Main analysis data
  const analysis = ref(null);
  const loading = ref(false);
  const starting = ref(false);
  const resuming = ref(false);

  // Live data from Socket.IO
  const liveData = ref({
    hardware: null,
    current_thread: null,
    current_message: null,
    timing: null
  });

  // Stuck detection
  const lastUpdateTime = ref(Date.now());
  const stuckThresholdSeconds = 30;

  // Distribution data
  const distributionPillar = ref(null);
  const distributionLevel = ref('level2');
  const distributionRole = ref('');
  const distributionData = ref([]);
  const loadingDistribution = ref(false);

  // Transitions data
  const transitionPillar = ref(null);
  const transitionLevel = ref('level2');
  const transitionRole = ref('');
  const transitionsData = ref({ links: [] });
  const loadingTransitions = ref(false);

  // Heatmap data (per pillar)
  const heatmapData = ref({});
  const loadingHeatmaps = ref(false);
  const showHeatmapValues = ref(false);
  const heatmapColorMode = ref('count');

  // Synchronized hover state
  const hoveredTransition = ref(null);

  // Matrix Comparison data
  const matrixComparisonData = ref(null);
  const loadingMatrixComparison = ref(false);

  // Sentences data
  const sentencePillar = ref(null);
  const sentenceRole = ref('');
  const sentenceLabel = ref('');
  const sentences = ref([]);
  const sentencesTotal = ref(0);
  const sentencesOffset = ref(0);
  const loadingSentences = ref(false);

  // ========================================
  // Computed Properties
  // ========================================

  const pillarOptions = computed(() => {
    if (!analysis.value?.pillar_statistics) return [];
    return [
      { title: t('oncoco.results.filters.allPillars'), value: null },
      ...Object.keys(analysis.value.pillar_statistics).map(p => ({
        title: t('oncoco.results.pillarLabel', { id: p }),
        value: parseInt(p)
      }))
    ];
  });

  const maxDistributionCount = computed(() => {
    if (distributionData.value.length === 0) return 1;
    return Math.max(...distributionData.value.map(d => d.count));
  });

  const roleFilterOptions = computed(() => [
    { title: t('oncoco.results.roles.allLong'), value: '' },
    { title: t('oncoco.results.roles.counselorOnly'), value: 'counselor' },
    { title: t('oncoco.results.roles.clientOnly'), value: 'client' }
  ]);

  const topTransitions = computed(() => {
    return transitionsData.value.links?.slice(0, 20) || [];
  });

  // Stuck detection
  const stuckDuration = computed(() => {
    return Math.round((Date.now() - lastUpdateTime.value) / 1000);
  });

  const isStuck = computed(() => {
    if (analysis.value?.status !== 'running') return false;
    const secondsSinceUpdate = (Date.now() - lastUpdateTime.value) / 1000;
    return secondsSinceUpdate > stuckThresholdSeconds && !liveData.value.timing;
  });

  // Quick Stats for QuickStatsBar
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

  // ========================================
  // API Functions
  // ========================================

  /**
   * Load main analysis data
   */
  const loadAnalysis = async () => {
    loading.value = true;
    try {
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}`
      );
      analysis.value = response.data;

      if (analysis.value.status === 'completed') {
        await Promise.all([
          loadDistribution(),
          loadTransitions(),
          loadHeatmaps(),
          loadMatrixComparison()
        ]);
      }
    } catch (error) {
      console.error('[OnCoCo Analysis] Error loading analysis:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  /**
   * Start analysis
   */
  const startAnalysis = async () => {
    starting.value = true;
    try {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/start`,
        {},
        { headers: { 'Content-Type': 'application/json' } }
      );
      lastUpdateTime.value = Date.now();
      await loadAnalysis();
    } catch (error) {
      console.error('[OnCoCo Analysis] Error starting analysis:', error);
      throw error;
    } finally {
      starting.value = false;
    }
  };

  /**
   * Resume stuck analysis
   */
  const resumeAnalysis = async () => {
    resuming.value = true;
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/start`,
        { force: true }
      );
      console.log('[OnCoCo Analysis] Analysis resumed:', response.data);
      lastUpdateTime.value = Date.now();
      await loadAnalysis();
    } catch (error) {
      console.error('[OnCoCo Analysis] Error resuming analysis:', error);
      throw error;
    } finally {
      resuming.value = false;
    }
  };

  /**
   * Load distribution data
   */
  const loadDistribution = async () => {
    loadingDistribution.value = true;
    try {
      const params = new URLSearchParams();
      if (distributionPillar.value) params.append('pillar', distributionPillar.value);
      params.append('level', distributionLevel.value);
      if (distributionRole.value) params.append('role', distributionRole.value);

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/distribution?${params}`
      );
      distributionData.value = response.data.distribution || [];
    } catch (error) {
      console.error('[OnCoCo Analysis] Error loading distribution:', error);
      distributionData.value = [];
    } finally {
      loadingDistribution.value = false;
    }
  };

  /**
   * Load transitions data (list format for top transitions)
   */
  const loadTransitions = async () => {
    loadingTransitions.value = true;
    try {
      const params = new URLSearchParams();
      if (transitionPillar.value) params.append('pillar', transitionPillar.value);
      params.append('level', transitionLevel.value);
      if (transitionRole.value) params.append('role', transitionRole.value);
      params.append('format', 'list');

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/transition-matrix?${params}`
      );
      transitionsData.value = response.data;
    } catch (error) {
      console.error('[OnCoCo Analysis] Error loading transitions:', error);
      transitionsData.value = { links: [] };
    } finally {
      loadingTransitions.value = false;
    }
  };

  /**
   * Load heatmaps (matrix format for each pillar)
   */
  const loadHeatmaps = async () => {
    if (!analysis.value?.config?.pillars) return;

    loadingHeatmaps.value = true;
    heatmapData.value = {};

    try {
      const pillars = analysis.value.config.pillars;
      const level = transitionLevel.value;
      const role = transitionRole.value;

      const promises = pillars.map(async (pillarNum) => {
        const params = new URLSearchParams();
        params.append('pillar', pillarNum);
        params.append('level', level);
        if (role) params.append('role', role);
        params.append('format', 'matrix');

        const response = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/transition-matrix?${params}`
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
      console.error('[OnCoCo Analysis] Error loading heatmaps:', error);
    } finally {
      loadingHeatmaps.value = false;
    }
  };

  /**
   * Load matrix comparison data
   */
  const loadMatrixComparison = async () => {
    loadingMatrixComparison.value = true;
    try {
      const params = new URLSearchParams();
      params.append('level', transitionLevel.value);
      if (transitionRole.value) params.append('role', transitionRole.value);

      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/matrix-comparison?${params}`
      );
      matrixComparisonData.value = response.data;
    } catch (error) {
      console.error('[OnCoCo Analysis] Error loading matrix comparison:', error);
      matrixComparisonData.value = null;
    } finally {
      loadingMatrixComparison.value = false;
    }
  };

  /**
   * Load sentences data
   * @param {boolean} reset - Whether to reset pagination
   */
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
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/sentences?${params}`
      );

      if (reset) {
        sentences.value = response.data.sentences || [];
      } else {
        sentences.value = [...sentences.value, ...(response.data.sentences || [])];
      }
      sentencesTotal.value = response.data.total || 0;
      sentencesOffset.value += response.data.sentences?.length || 0;
    } catch (error) {
      console.error('[OnCoCo Analysis] Error loading sentences:', error);
    } finally {
      loadingSentences.value = false;
    }
  };

  /**
   * Load more sentences (pagination)
   */
  const loadMoreSentences = () => {
    loadSentences(false);
  };

  /**
   * Update live data from Socket.IO progress event
   * @param {Object} data - Progress data from socket
   */
  const updateLiveData = (data) => {
    if (analysis.value && data.analysis_id === parseInt(analysisId)) {
      // Update basic progress
      analysis.value.processed_threads = data.processed_threads;
      analysis.value.total_threads = data.total_threads;
      analysis.value.total_sentences = data.total_sentences;
      analysis.value.progress = data.progress;

      // Update live data for detailed display
      liveData.value = {
        hardware: data.hardware,
        current_thread: data.current_thread,
        current_message: data.current_message,
        timing: data.timing
      };

      // Update last update time for stuck detection
      lastUpdateTime.value = Date.now();
    }
  };

  /**
   * Clear live data (called when analysis completes)
   */
  const clearLiveData = () => {
    liveData.value = {
      hardware: null,
      current_thread: null,
      current_message: null,
      timing: null
    };
  };

  /**
   * Get transition count for a specific pillar and transition
   */
  const getTransitionCount = (pillarNum, from, to) => {
    return heatmapData.value[pillarNum]?.counts?.[from]?.[to] || 0;
  };

  /**
   * Get transition probability for a specific pillar and transition
   */
  const getTransitionProbability = (pillarNum, from, to) => {
    return heatmapData.value[pillarNum]?.probabilities?.[from]?.[to] || 0;
  };

  // ========================================
  // Return Public API
  // ========================================

  return {
    // State
    analysis,
    loading,
    starting,
    resuming,
    liveData,
    lastUpdateTime,

    // Stuck detection
    stuckDuration,
    isStuck,

    // Distribution
    distributionPillar,
    distributionLevel,
    distributionRole,
    distributionData,
    loadingDistribution,
    maxDistributionCount,

    // Transitions
    transitionPillar,
    transitionLevel,
    transitionRole,
    transitionsData,
    loadingTransitions,
    topTransitions,

    // Heatmaps
    heatmapData,
    loadingHeatmaps,
    showHeatmapValues,
    heatmapColorMode,
    hoveredTransition,

    // Matrix Comparison
    matrixComparisonData,
    loadingMatrixComparison,
    quickStatsSimilarity,
    quickStatsFrobenius,
    quickStatsPValue,
    quickStatsChiSignificant,
    quickStatsChiTotal,

    // Sentences
    sentencePillar,
    sentenceRole,
    sentenceLabel,
    sentences,
    sentencesTotal,
    loadingSentences,

    // Computed
    pillarOptions,
    roleFilterOptions,

    // Functions
    loadAnalysis,
    startAnalysis,
    resumeAnalysis,
    loadDistribution,
    loadTransitions,
    loadHeatmaps,
    loadMatrixComparison,
    loadSentences,
    loadMoreSentences,
    updateLiveData,
    clearLiveData,
    getTransitionCount,
    getTransitionProbability
  };
}
