/**
 * JudgeResults Constants
 *
 * Table headers and constant configurations for the results view.
 */

// Metrics Table Headers
export const METRICS_HEADERS = [
  { title: 'Säule', key: 'name', sortable: true },
  { title: 'Siege', key: 'wins', sortable: true },
  { title: 'Niederlagen', key: 'losses', sortable: true },
  { title: 'Siegrate', key: 'win_rate', sortable: true },
  { title: 'Ø Konfidenz', key: 'avg_confidence', sortable: true },
  { title: 'Score', key: 'score', sortable: true },
  { title: 'Vergleiche', key: 'total_comparisons', sortable: true }
];

// Comparison Table Headers
export const COMPARISON_HEADERS = [
  { title: '#', key: 'comparison_index', sortable: true },
  { title: 'Paarung', key: 'matchup', sortable: false },
  { title: 'Gewinner', key: 'winner', sortable: true },
  { title: 'Konfidenz', key: 'confidence_score', sortable: true },
  { title: 'Zeitpunkt', key: 'evaluated_at', sortable: true }
];

// Position Swap Analysis Headers (Legacy)
export const SWAP_HEADERS = [
  { title: 'Paarung', key: 'matchup', sortable: false },
  { title: 'Original (Pos 1)', key: 'original', sortable: false },
  { title: 'Swapped (Pos 2)', key: 'swapped', sortable: false },
  { title: 'Konsistent', key: 'consistent', sortable: true }
];

// Detailed Position Swap Analysis Headers
export const DETAILED_SWAP_HEADERS = [
  { title: 'Threads', key: 'threads', sortable: false },
  { title: 'Original', key: 'original', sortable: false },
  { title: 'Swapped', key: 'swapped', sortable: false },
  { title: 'Konsistenz', key: 'consistency', sortable: true },
  { title: 'Bias', key: 'bias', sortable: true },
  { title: 'Konf. Δ', key: 'conf_delta', sortable: true }
];

// Thread Performance Headers
export const THREAD_HEADERS = [
  { title: 'Thread', key: 'thread_id', sortable: true },
  { title: 'Säule', key: 'pillar', sortable: true },
  { title: 'Verwendungen', key: 'usage_count', sortable: true },
  { title: 'Siege', key: 'wins', sortable: true },
  { title: 'Niederlagen', key: 'losses', sortable: true },
  { title: 'Win-Rate', key: 'win_rate', sortable: true },
  { title: 'Likert-Konsistenz', key: 'likert_consistency_score', sortable: true },
  { title: 'Status', key: 'status', sortable: false }
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
