/**
 * JudgeResults Constants
 *
 * Table headers and constant configurations for the results view.
 */

// Metrics Table Headers
export const buildMetricsHeaders = (t) => [
  { title: t('judge.results.metrics.columns.pillar'), key: 'name', sortable: true },
  { title: t('judge.results.metrics.columns.wins'), key: 'wins', sortable: true },
  { title: t('judge.results.metrics.columns.losses'), key: 'losses', sortable: true },
  { title: t('judge.results.metrics.columns.winRate'), key: 'win_rate', sortable: true },
  { title: t('judge.results.metrics.columns.avgConfidence'), key: 'avg_confidence', sortable: true },
  { title: t('judge.results.metrics.columns.score'), key: 'score', sortable: true },
  { title: t('judge.results.metrics.columns.comparisons'), key: 'total_comparisons', sortable: true }
];

// Comparison Table Headers
export const buildComparisonHeaders = (t) => [
  { title: t('judge.results.comparisons.columns.index'), key: 'comparison_index', sortable: true },
  { title: t('judge.results.comparisons.columns.matchup'), key: 'matchup', sortable: false },
  { title: t('judge.results.comparisons.columns.winner'), key: 'winner', sortable: true },
  { title: t('judge.results.comparisons.columns.confidence'), key: 'confidence_score', sortable: true },
  { title: t('judge.results.comparisons.columns.evaluatedAt'), key: 'evaluated_at', sortable: true }
];

// Position Swap Analysis Headers (Legacy)
export const buildSwapHeaders = (t) => [
  { title: t('judge.results.positionSwap.legacy.columns.matchup'), key: 'matchup', sortable: false },
  { title: t('judge.results.positionSwap.legacy.columns.original'), key: 'original', sortable: false },
  { title: t('judge.results.positionSwap.legacy.columns.swapped'), key: 'swapped', sortable: false },
  { title: t('judge.results.positionSwap.legacy.columns.consistent'), key: 'consistent', sortable: true }
];

// Detailed Position Swap Analysis Headers
export const buildDetailedSwapHeaders = (t) => [
  { title: t('judge.results.positionSwap.columns.threads'), key: 'threads', sortable: false },
  { title: t('judge.results.positionSwap.columns.original'), key: 'original', sortable: false },
  { title: t('judge.results.positionSwap.columns.swapped'), key: 'swapped', sortable: false },
  { title: t('judge.results.positionSwap.columns.consistency'), key: 'consistency', sortable: true },
  { title: t('judge.results.positionSwap.columns.bias'), key: 'bias', sortable: true },
  { title: t('judge.results.positionSwap.columns.confidenceDelta'), key: 'conf_delta', sortable: true }
];

// Thread Performance Headers
export const buildThreadHeaders = (t) => [
  { title: t('judge.results.threadPerformance.columns.thread'), key: 'thread_id', sortable: true },
  { title: t('judge.results.threadPerformance.columns.pillar'), key: 'pillar', sortable: true },
  { title: t('judge.results.threadPerformance.columns.usageCount'), key: 'usage_count', sortable: true },
  { title: t('judge.results.threadPerformance.columns.wins'), key: 'wins', sortable: true },
  { title: t('judge.results.threadPerformance.columns.losses'), key: 'losses', sortable: true },
  { title: t('judge.results.threadPerformance.columns.winRate'), key: 'win_rate', sortable: true },
  { title: t('judge.results.threadPerformance.columns.likertConsistency'), key: 'likert_consistency_score', sortable: true },
  { title: t('judge.results.threadPerformance.columns.status'), key: 'status', sortable: false }
];

// Likert Metrics for iteration
export const LIKERT_METRICS = [
  'counsellor_coherence',
  'client_coherence',
  'quality',
  'empathy',
  'authenticity',
  'solution_orientation'
];
