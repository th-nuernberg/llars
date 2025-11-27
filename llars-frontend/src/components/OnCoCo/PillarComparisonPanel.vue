<template>
  <v-card variant="outlined" class="pillar-comparison-panel">
    <v-card-title class="d-flex align-center py-2">
      <v-icon start color="primary">mdi-compare-horizontal</v-icon>
      Paarweise Säulen-Vergleiche
    </v-card-title>

    <!-- Pillar Pair Tabs -->
    <v-tabs v-model="selectedPairIndex" color="primary" density="compact" class="px-4">
      <v-tab
        v-for="(pair, idx) in pillarPairs"
        :key="pair.key"
        :value="idx"
      >
        <v-chip size="small" :color="getPillarColor(pair.pillarA)" class="mr-1">{{ pair.labelA }}</v-chip>
        <v-icon size="x-small">mdi-swap-horizontal</v-icon>
        <v-chip size="small" :color="getPillarColor(pair.pillarB)" class="ml-1">{{ pair.labelB }}</v-chip>
      </v-tab>
    </v-tabs>

    <v-divider></v-divider>

    <v-card-text>
      <!-- Loading State -->
      <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

      <template v-if="currentComparison">
        <v-row>
          <!-- Left Column: Top Differences -->
          <v-col cols="12" md="6">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon start size="small">mdi-arrow-split-vertical</v-icon>
              Größte Unterschiede
            </div>

            <v-list density="compact" class="differences-list" v-if="currentComparison.outlier_transitions?.length > 0">
              <v-list-item
                v-for="(diff, idx) in currentComparison.outlier_transitions.slice(0, 8)"
                :key="idx"
                class="px-2"
                @click="$emit('highlight-transition', { from: diff.from_label, to: diff.to_label })"
              >
                <template v-slot:prepend>
                  <v-icon
                    :color="diff.difference > 0 ? 'success' : 'error'"
                    size="small"
                    class="mr-2"
                  >
                    {{ diff.difference > 0 ? 'mdi-arrow-up-bold' : 'mdi-arrow-down-bold' }}
                  </v-icon>
                </template>

                <v-list-item-title class="text-body-2">
                  {{ diff.from_label }} → {{ diff.to_label }}
                </v-list-item-title>

                <template v-slot:append>
                  <div class="d-flex align-center">
                    <v-chip
                      size="x-small"
                      :color="diff.difference > 0 ? 'success' : 'error'"
                      variant="tonal"
                      class="mr-2"
                    >
                      {{ diff.difference > 0 ? '+' : '' }}{{ (diff.difference * 100).toFixed(1) }}%
                    </v-chip>
                    <span class="text-caption text-medium-emphasis">
                      z={{ diff.z_score?.toFixed(1) }}
                    </span>
                  </div>
                </template>
              </v-list-item>
            </v-list>

            <v-alert v-else type="info" variant="tonal" density="compact">
              Keine signifikanten Unterschiede gefunden (z-score > 2)
            </v-alert>
          </v-col>

          <!-- Right Column: Statistics -->
          <v-col cols="12" md="6">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon start size="small">mdi-chart-box</v-icon>
              Statistische Metriken
            </div>

            <div class="metrics-grid">
              <!-- Frobenius Distance -->
              <div class="metric-card">
                <div class="d-flex justify-space-between align-center mb-1">
                  <span class="text-caption">Frobenius-Distanz</span>
                  <span class="font-weight-bold">{{ formatNum(currentComparison.metrics?.frobenius_distance, 3) }}</span>
                </div>
                <v-progress-linear
                  :model-value="Math.min((currentComparison.metrics?.frobenius_distance || 0) * 50, 100)"
                  height="6"
                  rounded
                  :color="getFrobeniusColor(currentComparison.metrics?.frobenius_distance || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ getFrobeniusInterpretation(currentComparison.metrics?.frobenius_distance || 0) }}
                </div>
              </div>

              <!-- JSD Mean -->
              <div class="metric-card">
                <div class="d-flex justify-space-between align-center mb-1">
                  <span class="text-caption">JSD Mittelwert</span>
                  <span class="font-weight-bold">{{ formatNum(currentComparison.metrics?.mean_jsd, 3) }}</span>
                </div>
                <v-progress-linear
                  :model-value="(currentComparison.metrics?.mean_jsd || 0) * 100"
                  height="6"
                  rounded
                  :color="getJSDColor(currentComparison.metrics?.mean_jsd || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  Max: {{ formatNum(currentComparison.metrics?.max_jsd, 3) }}
                </div>
              </div>

              <!-- Permutation Test -->
              <div class="metric-card" v-if="currentComparison.statistical_tests?.permutation_test">
                <div class="d-flex justify-space-between align-center mb-1">
                  <span class="text-caption">Permutationstest</span>
                  <v-chip
                    :color="getSignificanceColor(currentComparison.statistical_tests.permutation_test.p_value)"
                    size="x-small"
                  >
                    p={{ formatPValue(currentComparison.statistical_tests.permutation_test.p_value) }}
                  </v-chip>
                </div>
                <div class="text-caption mt-1">
                  <v-icon
                    :color="currentComparison.statistical_tests.permutation_test.p_value < 0.05 ? 'success' : 'warning'"
                    size="x-small"
                    class="mr-1"
                  >
                    {{ currentComparison.statistical_tests.permutation_test.p_value < 0.05 ? 'mdi-check-circle' : 'mdi-minus-circle' }}
                  </v-icon>
                  {{ currentComparison.statistical_tests.permutation_test.p_value < 0.05
                    ? 'Signifikanter Unterschied'
                    : 'Nicht signifikant' }}
                </div>
              </div>

              <!-- Effect Size -->
              <div class="metric-card" v-if="currentComparison.effect_size">
                <div class="d-flex justify-space-between align-center mb-1">
                  <span class="text-caption">Effektstärke (norm.)</span>
                  <span class="font-weight-bold">{{ formatNum(currentComparison.effect_size.normalized_frobenius, 3) }}</span>
                </div>
                <v-progress-linear
                  :model-value="Math.min((currentComparison.effect_size.normalized_frobenius || 0) * 200, 100)"
                  height="6"
                  rounded
                  :color="getEffectSizeColor(currentComparison.effect_size.normalized_frobenius || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ getEffectSizeInterpretation(currentComparison.effect_size.normalized_frobenius || 0) }}
                </div>
              </div>

              <!-- Chi-Square -->
              <div class="metric-card" v-if="currentComparison.statistical_tests?.chi_square">
                <div class="d-flex justify-space-between align-center mb-1">
                  <span class="text-caption">Chi-Quadrat-Test</span>
                  <v-chip
                    :color="getChiSquareColor(currentComparison.statistical_tests.chi_square)"
                    size="x-small"
                  >
                    {{ currentComparison.statistical_tests.chi_square.significant_rows || 0 }} /
                    {{ currentComparison.statistical_tests.chi_square.total_rows || 0 }}
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis mt-1">
                  Zustände mit sig. unterschiedlichen Verteilungen
                </div>
              </div>
            </div>
          </v-col>
        </v-row>

        <!-- Expandable Details -->
        <v-expansion-panels class="mt-4" variant="accordion">
          <!-- Missing Transitions -->
          <v-expansion-panel v-if="hasMissingTransitions">
            <v-expansion-panel-title>
              <v-icon start size="small">mdi-help-circle-outline</v-icon>
              Fehlende Transitionen
              <v-chip size="x-small" class="ml-2" variant="tonal">
                {{ totalMissingTransitions }}
              </v-chip>
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col cols="12" md="6" v-if="currentComparison.missing_transitions?.missing_in_A?.length > 0">
                  <div class="text-caption font-weight-bold mb-2">
                    Nur in {{ currentPillarNames.labelB }}:
                  </div>
                  <v-chip
                    v-for="(trans, idx) in currentComparison.missing_transitions.missing_in_A.slice(0, 10)"
                    :key="'a-' + idx"
                    size="x-small"
                    variant="outlined"
                    class="ma-1"
                  >
                    {{ trans.from_label }} → {{ trans.to_label }}
                  </v-chip>
                  <span v-if="currentComparison.missing_transitions.missing_in_A.length > 10" class="text-caption">
                    +{{ currentComparison.missing_transitions.missing_in_A.length - 10 }} weitere
                  </span>
                </v-col>
                <v-col cols="12" md="6" v-if="currentComparison.missing_transitions?.missing_in_B?.length > 0">
                  <div class="text-caption font-weight-bold mb-2">
                    Nur in {{ currentPillarNames.labelA }}:
                  </div>
                  <v-chip
                    v-for="(trans, idx) in currentComparison.missing_transitions.missing_in_B.slice(0, 10)"
                    :key="'b-' + idx"
                    size="x-small"
                    variant="outlined"
                    class="ma-1"
                  >
                    {{ trans.from_label }} → {{ trans.to_label }}
                  </v-chip>
                  <span v-if="currentComparison.missing_transitions.missing_in_B.length > 10" class="text-caption">
                    +{{ currentComparison.missing_transitions.missing_in_B.length - 10 }} weitere
                  </span>
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Chi-Square Details -->
          <v-expansion-panel v-if="currentComparison.statistical_tests?.chi_square?.row_details">
            <v-expansion-panel-title>
              <v-icon start size="small">mdi-chart-bar</v-icon>
              Chi-Quadrat Details pro Zustand
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-data-table
                :headers="chiSquareHeaders"
                :items="chiSquareDetailItems"
                density="compact"
                :items-per-page="10"
              >
                <template v-slot:item.state="{ item }">
                  <span class="font-weight-medium">{{ item.state }}</span>
                </template>
                <template v-slot:item.significant="{ item }">
                  <v-icon :color="item.significant ? 'success' : 'grey'" size="small">
                    {{ item.significant ? 'mdi-check-circle' : 'mdi-minus-circle' }}
                  </v-icon>
                </template>
              </v-data-table>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </template>

      <!-- No Data State -->
      <v-alert v-else-if="!loading" type="info" variant="tonal">
        Keine Vergleichsdaten verfügbar. Bitte warten Sie bis die Analyse abgeschlossen ist.
      </v-alert>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  comparisons: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
});

defineEmits(['highlight-transition']);

const selectedPairIndex = ref(0);

// Pillar names mapping
const pillarNames = {
  1: 'Rollenspiele',
  3: 'Anonymisiert',
  5: 'Live-Test'
};

const pillarColors = {
  1: 'red',
  3: 'green',
  5: 'purple'
};

// Computed
const pillarPairs = computed(() => {
  return props.comparisons.map((comp, idx) => ({
    key: `${comp.pillar_a?.number || idx}-${comp.pillar_b?.number || idx}`,
    pillarA: comp.pillar_a?.number,
    pillarB: comp.pillar_b?.number,
    labelA: pillarNames[comp.pillar_a?.number] || comp.pillar_a?.name || `Säule ${comp.pillar_a?.number}`,
    labelB: pillarNames[comp.pillar_b?.number] || comp.pillar_b?.name || `Säule ${comp.pillar_b?.number}`
  }));
});

const currentComparison = computed(() => {
  return props.comparisons[selectedPairIndex.value] || null;
});

const currentPillarNames = computed(() => {
  const pair = pillarPairs.value[selectedPairIndex.value];
  return pair || { labelA: 'Säule A', labelB: 'Säule B' };
});

const hasMissingTransitions = computed(() => {
  const missing = currentComparison.value?.missing_transitions;
  return (missing?.missing_in_A?.length || 0) > 0 || (missing?.missing_in_B?.length || 0) > 0;
});

const totalMissingTransitions = computed(() => {
  const missing = currentComparison.value?.missing_transitions;
  return (missing?.missing_in_A?.length || 0) + (missing?.missing_in_B?.length || 0);
});

const chiSquareHeaders = [
  { title: 'Zustand', key: 'state', sortable: true },
  { title: 'χ²', key: 'chi_square', sortable: true },
  { title: 'p-Wert', key: 'p_value', sortable: true },
  { title: 'Signifikant', key: 'significant', sortable: true }
];

const chiSquareDetailItems = computed(() => {
  const details = currentComparison.value?.statistical_tests?.chi_square?.row_details;
  if (!details) return [];

  return Object.entries(details)
    .filter(([_, data]) => data.valid !== false)  // Only valid tests
    .map(([state, data]) => ({
      state,
      chi_square: data.chi2?.toFixed(2) || '-',
      p_value: data.p_value?.toFixed(4) || '-',
      significant: data.p_value < 0.05
    }))
    .sort((a, b) => {
      // Sort significant first, then by p-value
      if (a.significant !== b.significant) return b.significant ? 1 : -1;
      return parseFloat(a.p_value) - parseFloat(b.p_value);
    });
});

// Helper functions
const getPillarColor = (pillarNum) => pillarColors[pillarNum] || 'grey';

const formatNum = (value, decimals = 4) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return Number(value).toFixed(decimals);
};

const formatPValue = (value) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  if (value < 0.001) return '<0.001';
  return value.toFixed(3);
};

// Color helpers
const getFrobeniusColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.4) return 'info';
  if (value < 0.6) return 'warning';
  return 'error';
};

const getFrobeniusInterpretation = (value) => {
  if (value < 0.2) return 'Sehr ähnliche Matrizen';
  if (value < 0.4) return 'Moderat unterschiedlich';
  if (value < 0.6) return 'Deutlich unterschiedlich';
  return 'Stark unterschiedlich';
};

const getJSDColor = (value) => {
  if (value < 0.1) return 'success';
  if (value < 0.3) return 'info';
  if (value < 0.5) return 'warning';
  return 'error';
};

const getSignificanceColor = (pValue) => {
  if (pValue < 0.01) return 'success';
  if (pValue < 0.05) return 'info';
  return 'grey';
};

const getEffectSizeColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.5) return 'info';
  if (value < 0.8) return 'warning';
  return 'error';
};

const getEffectSizeInterpretation = (value) => {
  if (value < 0.2) return 'Kleine Effektstärke';
  if (value < 0.5) return 'Mittlere Effektstärke';
  if (value < 0.8) return 'Große Effektstärke';
  return 'Sehr große Effektstärke';
};

const getChiSquareColor = (chiSquare) => {
  if (!chiSquare) return 'grey';
  const { significant_rows, total_rows } = chiSquare;
  if (!total_rows || total_rows === 0) return 'grey';
  const ratio = significant_rows / total_rows;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};
</script>

<style scoped>
.pillar-comparison-panel {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  overflow: hidden;
  max-width: 100%;
}

.differences-list {
  background: transparent;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
}

.differences-list :deep(.v-list-item) {
  min-height: 40px;
  border-radius: 4px;
  margin-bottom: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.differences-list :deep(.v-list-item:hover) {
  background: rgba(var(--v-theme-primary), 0.1);
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

@media (min-width: 600px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.metric-card {
  background: rgba(var(--v-theme-surface), 0.8);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
}
</style>
