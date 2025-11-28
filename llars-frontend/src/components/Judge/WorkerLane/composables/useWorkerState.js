/**
 * Worker State Composable
 *
 * Manages worker status, progress, and pillar configuration.
 * Extracted from WorkerLane.vue for better maintainability.
 */

import { computed } from 'vue';

// Pillar Configuration
export const PILLAR_CONFIG = {
  1: { name: 'Rollenspiele', icon: 'mdi-theater', color: '#E91E63', short: 'S1' },
  2: { name: 'Feature', icon: 'mdi-star', color: '#9C27B0', short: 'S2' },
  3: { name: 'Anonymisiert', icon: 'mdi-incognito', color: '#2196F3', short: 'S3' },
  4: { name: 'Synthetisch', icon: 'mdi-robot', color: '#FF9800', short: 'S4' },
  5: { name: 'Live-Tests', icon: 'mdi-lightning-bolt', color: '#4CAF50', short: 'S5' }
};

// Criteria Configuration
export const CRITERIA_CONFIG = [
  { key: 'counsellor_coherence', short: 'BK', full: 'Berater-Kohärenz' },
  { key: 'client_coherence', short: 'KK', full: 'Klienten-Kohärenz' },
  { key: 'quality', short: 'Q', full: 'Qualität' },
  { key: 'empathy', short: 'E', full: 'Empathie' },
  { key: 'authenticity', short: 'A', full: 'Authentizität' },
  { key: 'solution_orientation', short: 'LO', full: 'Lösungsorientierung' }
];

// Step Configuration
export const STEP_CONFIG = [
  { key: 'step_1', short: 'BK', title: 'Berater-Kohärenz' },
  { key: 'step_2', short: 'KK', title: 'Klienten-Kohärenz' },
  { key: 'step_3', short: 'Q', title: 'Qualität' },
  { key: 'step_4', short: 'E', title: 'Empathie' },
  { key: 'step_5', short: 'A', title: 'Authentizität' },
  { key: 'step_6', short: 'LO', title: 'Lösungsorientierung' }
];

// Worker colors
export const WORKER_COLORS = ['blue', 'purple', 'teal', 'orange', 'pink'];

export function useWorkerState(props) {
  // Computed
  const workerColorName = computed(() => WORKER_COLORS[props.workerId % WORKER_COLORS.length]);

  const isActive = computed(() => props.currentComparison !== null || props.streamContent.length > 0);

  const statusType = computed(() => {
    if (props.isStreaming) return 'streaming';
    if (props.currentComparison) return 'active';
    return 'idle';
  });

  const statusColor = computed(() => {
    if (props.isStreaming) return 'warning';
    if (props.currentComparison) return 'info';
    return 'grey';
  });

  const statusIcon = computed(() => {
    if (props.isStreaming) return 'mdi-loading';
    if (props.currentComparison) return 'mdi-play-circle';
    return 'mdi-sleep';
  });

  const statusText = computed(() => {
    if (props.isStreaming) return 'Streamt';
    if (props.currentComparison) return 'Aktiv';
    return 'Wartet';
  });

  // Progress ring calculations
  const progressCircumference = computed(() => 2 * Math.PI * 18);

  const progressOffset = (completedSteps) => {
    const progress = completedSteps / 6;
    return progressCircumference.value * (1 - progress);
  };

  // Pillar helpers
  const getPillarIcon = (pillarId) => {
    return PILLAR_CONFIG[pillarId]?.icon || 'mdi-help-circle';
  };

  const getPillarShortName = (pillarName) => {
    if (!pillarName) return '';
    const match = pillarName.match(/Säule\s*(\d)/i);
    if (match) return `S${match[1]}`;
    return pillarName.split(' ')[0].substring(0, 6);
  };

  // Text helper
  const truncateText = (text, maxLength) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return {
    // Computed
    workerColorName,
    isActive,
    statusType,
    statusColor,
    statusIcon,
    statusText,
    progressCircumference,

    // Methods
    progressOffset,
    getPillarIcon,
    getPillarShortName,
    truncateText
  };
}
