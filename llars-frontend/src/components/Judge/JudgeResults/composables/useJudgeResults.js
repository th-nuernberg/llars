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

  // Computed
  const topPillar = computed(() => {
    if (!results.value?.pillar_rankings?.length) return null;
    return results.value.pillar_rankings[0];
  });

  const averageConfidence = computed(() => {
    if (!results.value?.average_confidence) return 0;
    return Math.round(results.value.average_confidence * 100);
  });

  const duration = computed(() => {
    if (!session.value?.started_at || !session.value?.completed_at) return '-';
    const start = new Date(session.value.started_at);
    const end = new Date(session.value.completed_at);
    const diffMs = end - start;
    const diffMins = Math.round(diffMs / 60000);
    if (diffMins < 60) return `${diffMins}m`;
    const hours = Math.floor(diffMins / 60);
    const mins = diffMins % 60;
    return `${hours}h ${mins}m`;
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

    // Computed
    topPillar,
    averageConfidence,
    duration,
    lengthDiff,
    lengthDiffClass,

    // Methods
    loadResults
  };
}
