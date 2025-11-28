/**
 * Session Constants
 *
 * Shared constants for JudgeSession component.
 */

// Worker colors for fullscreen display
export const WORKER_COLORS = ['blue', 'purple', 'teal', 'orange', 'pink'];

// Pillar Configuration
export const PILLAR_CONFIG = {
  1: { name: 'Rollenspiele', icon: 'mdi-theater', color: '#E91E63', short: 'S1' },
  2: { name: 'Feature', icon: 'mdi-star', color: '#9C27B0', short: 'S2' },
  3: { name: 'Anonymisiert', icon: 'mdi-incognito', color: '#2196F3', short: 'S3' },
  4: { name: 'Synthetisch', icon: 'mdi-robot', color: '#FF9800', short: 'S4' },
  5: { name: 'Live-Tests', icon: 'mdi-lightning-bolt', color: '#4CAF50', short: 'S5' }
};

// Pillar name helper (legacy)
export const PILLAR_NAMES = {
  1: "Rollenspiele",
  2: "Feature Säule 1",
  3: "Anonymisierte Daten",
  4: "Synthetisch",
  5: "Live-Test"
};

// Step definitions with German titles
export const STEP_DEFINITIONS = {
  'step_1': { title: 'Analyse Berater-Kohärenz', icon: 'mdi-account-tie' },
  'step_2': { title: 'Analyse Klienten-Kohärenz', icon: 'mdi-account' },
  'step_3': { title: 'Analyse Beratungsqualität', icon: 'mdi-star' },
  'step_4': { title: 'Analyse Empathie', icon: 'mdi-heart' },
  'step_5': { title: 'Analyse Authentizität', icon: 'mdi-check-decagram' },
  'step_6': { title: 'Analyse Lösungsorientierung', icon: 'mdi-lightbulb' }
};

// Score criteria mapping
export const SCORE_CRITERIA = [
  { key: 'counsellor_coherence', label: 'Berater-Kohärenz' },
  { key: 'client_coherence', label: 'Klienten-Kohärenz' },
  { key: 'quality', label: 'Qualität' },
  { key: 'empathy', label: 'Empathie' },
  { key: 'authenticity', label: 'Authentizität' },
  { key: 'solution_orientation', label: 'Lösungsorientierung' }
];

// Queue Table Headers
export const QUEUE_HEADERS = [
  { title: '#', key: 'queue_position', sortable: true, width: '60px' },
  { title: 'Status', key: 'status', sortable: true, width: '120px' },
  { title: 'Säule A', key: 'pillar_a', sortable: false },
  { title: '', key: 'vs', sortable: false, width: '50px' },
  { title: 'Säule B', key: 'pillar_b', sortable: false },
  { title: 'Ergebnis', key: 'result', sortable: false, width: '100px' }
];

// History Table Headers
export const HISTORY_HEADERS = [
  { title: '#', key: 'comparison_index', sortable: true },
  { title: 'Säulen', key: 'pillars', sortable: false },
  { title: 'Gewinner', key: 'winner', sortable: true },
  { title: 'Konfidenz', key: 'confidence_score', sortable: true },
  { title: 'Zeitpunkt', key: 'evaluated_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false }
];
