<template>
  <v-row class="mt-4" v-if="analysis">
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-text-long</v-icon>
          Verbosity Bias Analyse
          <v-chip
            class="ml-3"
            :color="biasColor"
            size="small"
          >
            {{ Math.round(analysis.verbosity_bias_rate * 100) }}% längerer gewinnt
          </v-chip>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="card, table" />
          <template v-else>
            <v-alert
              :type="biasType"
              variant="tonal"
              class="mb-4"
            >
              <template v-if="analysis.verbosity_bias_rate > 0.6">
                <strong>Warnung:</strong> Das LLM zeigt einen starken Verbosity Bias - längere Threads werden bevorzugt.
              </template>
              <template v-else-if="analysis.verbosity_bias_rate < 0.4">
                <strong>Info:</strong> Das LLM bevorzugt kürzere Threads - möglicherweise negatives Verbosity Bias.
              </template>
              <template v-else>
                <strong>Gut:</strong> Keine signifikante Präferenz für Thread-Länge erkannt.
              </template>
            </v-alert>

            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-success">{{ analysis.longer_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Längerer Thread gewinnt</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-error">{{ analysis.shorter_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Kürzerer Thread gewinnt</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-grey">{{ analysis.ties }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Gleiche Länge / Tie</div>
                </v-card>
              </v-col>
            </v-row>

            <v-row class="mt-4">
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Durchschnittliche Länge (Zeichen)</div>
                <v-table density="compact">
                  <tbody>
                    <tr>
                      <td>Gewinner</td>
                      <td class="text-right font-weight-bold">{{ Math.round(analysis.avg_length_winner).toLocaleString() }}</td>
                    </tr>
                    <tr>
                      <td>Verlierer</td>
                      <td class="text-right font-weight-bold">{{ Math.round(analysis.avg_length_loser).toLocaleString() }}</td>
                    </tr>
                    <tr>
                      <td>Differenz</td>
                      <td class="text-right font-weight-bold" :class="lengthDiffClass">
                        {{ lengthDiffFormatted }}
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2">Bias-Interpretation</div>
                <v-progress-linear
                  :model-value="analysis.verbosity_bias_rate * 100"
                  height="30"
                  rounded
                  :color="biasColor"
                >
                  <template v-slot:default="{ value }">
                    <strong>{{ Math.round(value) }}%</strong>
                  </template>
                </v-progress-linear>
                <div class="d-flex justify-space-between text-caption text-medium-emphasis mt-1">
                  <span>Kürzerer bevorzugt</span>
                  <span>Neutral (50%)</span>
                  <span>Längerer bevorzugt</span>
                </div>
              </v-col>
            </v-row>
          </template>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  loading: { type: Boolean, default: false },
  analysis: { type: Object, default: null }
});

const biasColor = computed(() => {
  if (!props.analysis) return 'grey';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const biasType = computed(() => {
  if (!props.analysis) return 'info';
  const rate = props.analysis.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const lengthDiffFormatted = computed(() => {
  if (!props.analysis) return '-';
  const diff = props.analysis.avg_length_winner - props.analysis.avg_length_loser;
  const sign = diff > 0 ? '+' : '';
  return `${sign}${Math.round(diff).toLocaleString()}`;
});

const lengthDiffClass = computed(() => {
  if (!props.analysis) return '';
  const diff = props.analysis.avg_length_winner - props.analysis.avg_length_loser;
  if (diff > 500) return 'text-warning';
  if (diff < -500) return 'text-info';
  return 'text-success';
});
</script>

<style scoped>
</style>
