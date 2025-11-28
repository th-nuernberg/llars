/**
 * Judge Config Computed Composable
 *
 * All computed properties for the configuration form.
 */

import { computed } from 'vue';

export function useJudgeConfigComputed(config, availablePillars, estimate, limitThreadsEnabled) {
  /**
   * Minimum pillars required based on mode.
   */
  const minPillarsRequired = computed(() => {
    return config.value.comparisonMode === 'free_for_all' ? 1 : 2;
  });

  /**
   * Total thread count for selected pillars.
   */
  const selectedThreadCount = computed(() => {
    return config.value.selectedPillars.reduce((sum, id) => {
      const pillar = availablePillars.value.find(p => p.id === id);
      return sum + (pillar?.threadCount || 0);
    }, 0);
  });

  /**
   * Display name for current mode.
   */
  const modeDisplayName = computed(() => {
    const modes = {
      'pillar_sample': 'Säulen-Stichprobe',
      'round_robin': 'Round Robin',
      'free_for_all': 'Jeder gegen Jeden'
    };
    return modes[config.value.comparisonMode] || config.value.comparisonMode;
  });

  /**
   * Color for mode chip.
   */
  const modeColor = computed(() => {
    const colors = {
      'pillar_sample': 'success',
      'round_robin': 'warning',
      'free_for_all': 'error'
    };
    return colors[config.value.comparisonMode] || 'primary';
  });

  /**
   * Description for current mode.
   */
  const modeDescription = computed(() => {
    const descriptions = {
      'pillar_sample': 'Zufällige Samples pro Säulen-Paar',
      'round_robin': 'Jeder Thread gegen jeden (innerhalb Säulen-Paare)',
      'free_for_all': 'Jeder Thread gegen jeden (alle)'
    };
    return descriptions[config.value.comparisonMode] || '';
  });

  /**
   * Estimated number of pillar pairs.
   */
  const estimatedPairs = computed(() => {
    const n = config.value.selectedPillars.length;
    if (n < 2) return 0;
    return (n * (n - 1)) / 2;
  });

  /**
   * Estimated total comparisons.
   */
  const estimatedComparisons = computed(() => {
    if (estimate.value?.total_comparisons) {
      return estimate.value.total_comparisons;
    }
    // Fallback calculation for pillar_sample
    const pairs = estimatedPairs.value;
    const samples = config.value.samplesPerPillar;
    const swapMultiplier = config.value.positionSwap ? 2 : 1;
    const repetitions = config.value.repetitionsPerPair;
    return pairs * samples * swapMultiplier * repetitions;
  });

  /**
   * Estimated duration in minutes.
   */
  const estimatedDuration = computed(() => {
    if (estimate.value?.estimated_duration_minutes) {
      return estimate.value.estimated_duration_minutes;
    }
    // Fallback: ~10 seconds per comparison
    const seconds = estimatedComparisons.value * 10;
    return Math.ceil(seconds / 60);
  });

  /**
   * Duration for selected worker count.
   */
  const selectedDuration = computed(() => {
    if (estimate.value?.estimated_duration_by_workers) {
      return estimate.value.estimated_duration_by_workers[config.value.workerCount] || estimatedDuration.value;
    }
    return estimatedDuration.value / config.value.workerCount;
  });

  /**
   * Whether session can be created.
   */
  const canCreate = computed(() => {
    return (
      config.value.sessionName.trim() !== '' &&
      config.value.selectedPillars.length >= minPillarsRequired.value
    );
  });

  return {
    minPillarsRequired,
    selectedThreadCount,
    modeDisplayName,
    modeColor,
    modeDescription,
    estimatedPairs,
    estimatedComparisons,
    estimatedDuration,
    selectedDuration,
    canCreate
  };
}
