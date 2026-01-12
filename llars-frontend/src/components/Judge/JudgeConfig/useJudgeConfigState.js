/**
 * Judge Config State Composable
 *
 * Manages form state, configuration, and available pillars.
 */

import { ref, watch } from 'vue';

export function useJudgeConfigState() {
  // Form refs
  const form = ref(null);
  const valid = ref(false);
  const creating = ref(false);

  // Estimate state
  const estimate = ref(null);
  const estimateLoading = ref(false);

  // Thread limit toggle
  const limitThreadsEnabled = ref(false);

  // Available Pillars
  const availablePillars = ref([
    { id: 1, nameKey: 'judge.pillars.items.roleplay', icon: 'mdi-theater', enabled: true, threadCount: 0 },
    { id: 2, nameKey: 'judge.pillars.items.feature', icon: 'mdi-star', enabled: false, threadCount: 0 },
    { id: 3, nameKey: 'judge.pillars.items.anonymized', icon: 'llars:anonymize', enabled: true, threadCount: 0 },
    { id: 4, nameKey: 'judge.pillars.items.synthetic', icon: 'mdi-robot', enabled: false, threadCount: 0 },
    { id: 5, nameKey: 'judge.pillars.items.liveTests', icon: 'mdi-lightning-bolt', enabled: true, threadCount: 0 }
  ]);

  // Configuration
  const config = ref({
    sessionName: '',
    selectedPillars: [],
    comparisonMode: 'pillar_sample',
    samplesPerPillar: 10,
    maxThreadsPerPillar: 15,
    positionSwap: true,
    repetitionsPerPair: 1,
    workerCount: 3
  });

  /**
   * Setup watcher for limit toggle.
   */
  const setupLimitWatcher = () => {
    watch(limitThreadsEnabled, (enabled) => {
      if (!enabled) {
        config.value.maxThreadsPerPillar = null;
      } else {
        config.value.maxThreadsPerPillar = 15;
      }
    });
  };

  /**
   * Pre-select default pillars on mount.
   */
  const initializeDefaultPillars = () => {
    config.value.selectedPillars = [1, 3, 5];
  };

  /**
   * Update thread counts from estimate response.
   */
  const updateThreadCounts = (threadsPerPillar) => {
    if (!threadsPerPillar) return;

    for (const [pillarId, count] of Object.entries(threadsPerPillar)) {
      const pillar = availablePillars.value.find(p => p.id === parseInt(pillarId));
      if (pillar) {
        pillar.threadCount = count;
      }
    }
  };

  return {
    // Refs
    form,
    valid,
    creating,
    estimate,
    estimateLoading,
    limitThreadsEnabled,
    availablePillars,
    config,

    // Methods
    setupLimitWatcher,
    initializeDefaultPillars,
    updateThreadCounts
  };
}
