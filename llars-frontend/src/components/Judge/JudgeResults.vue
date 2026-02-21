<template>
  <div class="judge-results" :class="{ 'is-mobile': isMobile }">
    <!-- Page Header -->
    <div class="results-header">
      <div class="header-left">
        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-arrow-left"
          @click="$router.push({ name: 'JudgeSession', params: { id: sessionId } })"
        >
          {{ $t('common.back') }}
        </LBtn>
        <div class="header-title-section">
          <v-skeleton-loader v-if="isLoading('header')" type="heading" width="300" />
          <template v-else>
            <h1 class="page-title">
              <LIcon class="mr-2" color="primary">mdi-chart-box</LIcon>
              {{ $t('judge.results.title') }}
            </h1>
            <div class="page-subtitle">
              <LTag variant="primary" size="small">{{ session?.session_name }}</LTag>
              <LTag variant="gray" size="small">
                {{ $t('judge.results.pillarsCount', { count: session?.pillar_count || 0 }) }}
              </LTag>
            </div>
          </template>
        </div>
      </div>
      <div class="header-right">
        <ResultsExport
          @export-csv="exportCSV"
          @export-json="exportJSON"
        />
      </div>
    </div>

    <!-- Session Summary Cards -->
    <ResultsOverview
      :loading="isLoading('overview')"
      :total-comparisons="results?.total_comparisons || 0"
      :top-pillar="topPillar"
      :average-confidence="averageConfidence"
      :duration="duration"
    />

    <!-- Pillar Ranking & Matrix -->
    <ResultsRanking
      :loading="isLoading('ranking')"
      :pillar-ranking="pillarRanking"
      :pillar-list="pillarList"
      :get-rank-color="getRankColor"
      :get-matrix-value="getMatrixValue"
      :get-matrix-cell-class="getMatrixCellClass"
      :get-matrix-cell-style="getMatrixCellStyle"
    />

    <!-- Metrics Table -->
    <ResultsMetrics
      :loading="isLoading('metrics')"
      :metrics="pillarMetrics"
      :get-win-rate-color="getWinRateColor"
    />

    <!-- Position Swap Analysis -->
    <ResultsPositionSwap
      :loading="isLoading('positionSwap')"
      :detailed-analysis="positionSwapDetailed"
      :legacy-analysis="positionSwapAnalysis"
      :get-consistency-quality-color="getConsistencyQualityColor"
      :get-bias-label="getBiasLabel"
      :format-likert-metric="formatLikertMetric"
      :get-score-color="getScoreColor"
    />

    <!-- Verbosity Bias Analysis -->
    <ResultsVerbosity
      :loading="isLoading('verbosity')"
      :analysis="verbosityAnalysis"
    />

    <!-- Thread Performance Analysis -->
    <ResultsThreadPerformance
      :loading="isLoading('threadPerformance')"
      :performance="threadPerformance"
      :format-likert-metric="formatLikertMetric"
      :get-pillar-name="getPillarName"
      :get-win-rate-color="getWinRateColor"
      :get-likert-consistency-color="getLikertConsistencyColor"
      :get-score-color="getScoreColor"
    />

    <!-- Comparison Details -->
    <ResultsComparisons
      :loading="isLoading('comparisons')"
      :comparisons="allComparisons"
      :get-confidence-color="getConfidenceColor"
      :get-score-color="getScoreColor"
      :format-date="formatDate"
      :format-criterion-name="formatCriterionName"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { useMobile } from '@/composables/useMobile';
import {
  useJudgeResults,
  useJudgeMatrix,
  useJudgeHelpers
} from './JudgeResults/composables';

const { isMobile } = useMobile();

// Import subcomponents
import ResultsOverview from './JudgeResults/ResultsOverview.vue';
import ResultsRanking from './JudgeResults/ResultsRanking.vue';
import ResultsMetrics from './JudgeResults/ResultsMetrics.vue';
import ResultsPositionSwap from './JudgeResults/ResultsPositionSwap.vue';
import ResultsVerbosity from './JudgeResults/ResultsVerbosity.vue';
import ResultsThreadPerformance from './JudgeResults/ResultsThreadPerformance.vue';
import ResultsComparisons from './JudgeResults/ResultsComparisons.vue';
import ResultsExport from './JudgeResults/ResultsExport.vue';

const route = useRoute();
const sessionId = route.params.id;

// Skeleton loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading([
  'header',
  'overview',
  'ranking',
  'metrics',
  'positionSwap',
  'verbosity',
  'threadPerformance',
  'comparisons'
]);

// Initialize composables
const {
  // State
  session,
  results,
  allComparisons,
  verbosityAnalysis,
  threadPerformance,
  positionSwapDetailed,
  // Computed - Pillar data
  pillarRanking,
  pillarList,
  pillarMetrics,
  topPillar,
  averageConfidence,
  duration,
  // Computed - Analysis
  positionSwapAnalysis,
  // Methods
  loadResults
} = useJudgeResults(sessionId);

const {
  getMatrixValue: getMatrixValueRaw,
  getMatrixCellClass,
  getMatrixCellStyle: getMatrixCellStyleRaw
} = useJudgeMatrix(results);

const {
  getRankColor,
  getWinRateColor,
  getConfidenceColor,
  getScoreColor,
  getLikertConsistencyColor,
  getConsistencyQualityColor,
  formatDate,
  formatCriterionName,
  formatLikertMetric,
  getPillarName,
  getBiasLabel,
  exportCSV,
  exportJSON
} = useJudgeHelpers(sessionId);

// Wrapper functions for matrix (to use results.value internally)
const getMatrixValue = (pillarA, pillarB) => getMatrixValueRaw(pillarA, pillarB);
const getMatrixCellStyle = (pillarA, pillarB) => getMatrixCellStyleRaw(pillarA, pillarB);

// Lifecycle
onMounted(async () => {
  // Set all sections to loading
  setLoading('header', true);
  setLoading('overview', true);
  setLoading('ranking', true);
  setLoading('metrics', true);
  setLoading('positionSwap', true);
  setLoading('verbosity', true);
  setLoading('threadPerformance', true);
  setLoading('comparisons', true);

  try {
    await loadResults();
  } finally {
    // Turn off all loading states
    setLoading('header', false);
    setLoading('overview', false);
    setLoading('ranking', false);
    setLoading('metrics', false);
    setLoading('positionSwap', false);
    setLoading('verbosity', false);
    setLoading('threadPerformance', false);
    setLoading('comparisons', false);
  }
});
</script>

<style scoped>
.judge-results {
  max-width: 1600px;
  margin: 0 auto;
  padding: var(--llars-spacing-lg);
}

/* Page Header */
.results-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--llars-spacing-lg);
  padding-bottom: var(--llars-spacing-md);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: var(--llars-spacing-md);
}

.header-title-section {
  display: flex;
  flex-direction: column;
  gap: var(--llars-spacing-xs);
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  align-items: center;
  margin: 0;
}

.page-subtitle {
  display: flex;
  gap: var(--llars-spacing-sm);
  flex-wrap: wrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-sm);
}

/* Mobile Styles */
.judge-results.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
  padding: var(--llars-spacing-md);
}

.judge-results.is-mobile .results-header {
  flex-direction: column;
  gap: var(--llars-spacing-md);
}

.judge-results.is-mobile .header-left {
  flex-direction: column;
  width: 100%;
}

.judge-results.is-mobile .page-title {
  font-size: 1.35rem;
}

.judge-results.is-mobile .header-right {
  width: 100%;
  justify-content: flex-end;
}
</style>
