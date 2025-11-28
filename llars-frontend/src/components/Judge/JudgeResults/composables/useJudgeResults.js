/**
 * Judge Results Composable
 *
 * Handles loading session, results, comparisons, and analysis data.
 * Extracted from JudgeResults.vue for better maintainability.
 */

import { ref, computed } from 'vue';
import axios from 'axios';

export function useJudgeResults(sessionId) {
  // State
  const loading = ref(false);
  const session = ref(null);
  const results = ref(null);
  const allComparisons = ref([]);
  const verbosityAnalysis = ref(null);
  const threadPerformance = ref(null);
  const positionSwapDetailed = ref(null);

  // Expanded row states
  const expandedRows = ref([]);
  const expandedThreadRows = ref([]);
  const expandedSwapPairs = ref([]);

  // Computed: Pillar Ranking (sorted by score)
  const pillarRanking = computed(() => {
    if (!results.value?.pillar_metrics) return [];
    return [...results.value.pillar_metrics].sort((a, b) => b.score - a.score);
  });

  // Computed: Pillar List (unsorted)
  const pillarList = computed(() => {
    if (!results.value?.pillar_metrics) return [];
    return results.value.pillar_metrics;
  });

  // Computed: Pillar Metrics (alias)
  const pillarMetrics = computed(() => {
    if (!results.value?.pillar_metrics) return [];
    return results.value.pillar_metrics;
  });

  // Computed: Top Pillar
  const topPillar = computed(() => {
    return pillarRanking.value[0] || null;
  });

  // Computed: Average Confidence
  const averageConfidence = computed(() => {
    if (!results.value?.pillar_metrics || results.value.pillar_metrics.length === 0) return 0;
    const sum = results.value.pillar_metrics.reduce((acc, p) => acc + p.avg_confidence, 0);
    return Math.round((sum / results.value.pillar_metrics.length) * 100);
  });

  // Computed: Session Duration
  const duration = computed(() => {
    if (!session.value?.created_at || !session.value?.completed_at) return '-';
    const start = new Date(session.value.created_at);
    const end = new Date(session.value.completed_at);
    const diff = end - start;
    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  });

  // Computed: Position Swap Consistency Analysis (Legacy)
  const positionSwapAnalysis = computed(() => {
    if (!allComparisons.value || allComparisons.value.length === 0) {
      return { pairs: [], consistent: 0, total: 0, consistencyRate: 0 };
    }

    // Group comparisons by pillar pair (regardless of position)
    const pairGroups = {};

    for (const comp of allComparisons.value) {
      if (!comp.winner) continue;

      // Create a consistent key for the pair (sorted pillar IDs)
      const sortedPillars = [comp.pillar_a, comp.pillar_b].sort((a, b) => a - b);
      const pairKey = `${sortedPillars[0]}_${sortedPillars[1]}`;

      if (!pairGroups[pairKey]) {
        pairGroups[pairKey] = {
          pillar_a: sortedPillars[0],
          pillar_b: sortedPillars[1],
          pillar_a_name: comp.pillar_a === sortedPillars[0] ? comp.pillar_a_name : comp.pillar_b_name,
          pillar_b_name: comp.pillar_a === sortedPillars[1] ? comp.pillar_a_name : comp.pillar_b_name,
          original: null,
          swapped: null
        };
      }

      // Determine if this is position_order 1 (original) or 2 (swapped)
      if (comp.position_order === 1) {
        pairGroups[pairKey].original = comp;
      } else if (comp.position_order === 2) {
        pairGroups[pairKey].swapped = comp;
      }
    }

    // Analyze consistency for pairs with both positions
    const pairs = [];
    let consistent = 0;
    let total = 0;

    for (const [key, group] of Object.entries(pairGroups)) {
      if (group.original && group.swapped) {
        total++;

        // Determine the "real" winner based on position
        const originalRealWinner = group.original.winner === 'A'
          ? group.original.pillar_a
          : group.original.pillar_b;

        const swappedRealWinner = group.swapped.winner === 'A'
          ? group.swapped.pillar_a
          : group.swapped.pillar_b;

        const isConsistent = originalRealWinner === swappedRealWinner;
        if (isConsistent) consistent++;

        pairs.push({
          pillar_a_name: group.pillar_a_name,
          pillar_b_name: group.pillar_b_name,
          originalWinner: group.original.winner,
          originalConfidence: group.original.confidence_score || 0,
          swappedWinner: group.swapped.winner,
          swappedConfidence: group.swapped.confidence_score || 0,
          isConsistent
        });
      }
    }

    return {
      pairs,
      consistent,
      total,
      consistencyRate: total > 0 ? consistent / total : 0
    };
  });

  // Verbosity computed
  const lengthDiff = computed(() => {
    if (!verbosityAnalysis.value) return '-';
    const diff = verbosityAnalysis.value.avg_length_winner - verbosityAnalysis.value.avg_length_loser;
    const sign = diff > 0 ? '+' : '';
    return `${sign}${Math.round(diff).toLocaleString()}`;
  });

  const lengthDiffClass = computed(() => {
    if (!verbosityAnalysis.value) return '';
    const diff = verbosityAnalysis.value.avg_length_winner - verbosityAnalysis.value.avg_length_loser;
    if (diff > 500) return 'text-warning';
    if (diff < -500) return 'text-info';
    return 'text-success';
  });

  // Verbosity Bias Color
  const verbosityBiasColor = computed(() => {
    if (!verbosityAnalysis.value) return 'grey';
    const rate = verbosityAnalysis.value.verbosity_bias_rate;
    if (rate > 0.6) return 'warning';
    if (rate < 0.4) return 'info';
    return 'success';
  });

  // Verbosity Bias Type
  const verbosityBiasType = computed(() => {
    if (!verbosityAnalysis.value) return 'info';
    const rate = verbosityAnalysis.value.verbosity_bias_rate;
    if (rate > 0.6) return 'warning';
    if (rate < 0.4) return 'info';
    return 'success';
  });

  // Methods
  const loadResults = async () => {
    loading.value = true;
    try {
      // Load session info
      const sessionResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}`
      );
      session.value = sessionResponse.data;

      // Load results
      const resultsResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/results`
      );
      results.value = resultsResponse.data;

      // Load all comparisons
      const comparisonsResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/comparisons`
      );
      allComparisons.value = comparisonsResponse.data;

      // Load verbosity analysis
      try {
        const verbosityResponse = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/verbosity-analysis`
        );
        verbosityAnalysis.value = verbosityResponse.data;
      } catch (verbosityError) {
        console.warn('Could not load verbosity analysis:', verbosityError);
      }

      // Load thread performance analysis
      try {
        const threadPerfResponse = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/thread-performance`
        );
        threadPerformance.value = threadPerfResponse.data;
      } catch (threadPerfError) {
        console.warn('Could not load thread performance:', threadPerfError);
      }

      // Load detailed position-swap analysis
      try {
        const swapResponse = await axios.get(
          `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/position-swap-analysis`
        );
        positionSwapDetailed.value = swapResponse.data;
      } catch (swapError) {
        console.warn('Could not load position-swap analysis:', swapError);
      }
    } catch (error) {
      console.error('Error loading results:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  return {
    // State
    loading,
    session,
    results,
    allComparisons,
    verbosityAnalysis,
    threadPerformance,
    positionSwapDetailed,

    // Expanded row states
    expandedRows,
    expandedThreadRows,
    expandedSwapPairs,

    // Computed - Pillar data
    pillarRanking,
    pillarList,
    pillarMetrics,
    topPillar,
    averageConfidence,
    duration,

    // Computed - Analysis
    positionSwapAnalysis,

    // Computed - Verbosity
    lengthDiff,
    lengthDiffClass,
    verbosityBiasColor,
    verbosityBiasType,

    // Methods
    loadResults
  };
}
