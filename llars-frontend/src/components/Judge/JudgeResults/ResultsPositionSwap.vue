<template>
  <!-- Detailed Position Swap Analysis -->
  <v-row class="mt-4" v-if="detailedAnalysis && detailedAnalysis.summary">
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center flex-wrap">
          <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
          Position-Swap Konsistenz (MT-Bench Methodik)
          <v-chip
            class="ml-3"
            :color="getConsistencyQualityColor(detailedAnalysis.interpretation?.overall_quality)"
            size="small"
          >
            {{ Math.round(detailedAnalysis.summary.consistency_rate * 100) }}% konsistent
          </v-chip>
          <v-chip
            class="ml-2"
            :color="detailedAnalysis.position_bias?.dominant_bias === 'balanced' ? 'success' : 'warning'"
            size="small"
            variant="outlined"
          >
            {{ getBiasLabel(detailedAnalysis.position_bias?.dominant_bias) }}
          </v-chip>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="card, table" />
          <template v-else>
            <!-- Interpretation Alert -->
            <v-alert
              :type="detailedAnalysis.interpretation?.overall_quality === 'excellent' ? 'success' :
                     detailedAnalysis.interpretation?.overall_quality === 'good' ? 'info' :
                     detailedAnalysis.interpretation?.overall_quality === 'fair' ? 'warning' : 'error'"
              variant="tonal"
              class="mb-4"
            >
              <div v-for="(rec, idx) in detailedAnalysis.interpretation?.recommendations" :key="idx">
                {{ rec }}
              </div>
            </v-alert>

            <!-- Summary Cards -->
            <v-row class="mb-4">
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-primary">{{ detailedAnalysis.summary.total_swap_pairs }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Swap-Paare</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-success">{{ detailedAnalysis.summary.consistent_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Konsistent (Win)
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-info">{{ detailedAnalysis.summary.consistent_ties }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Konsistent (Tie)
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-error">{{ detailedAnalysis.summary.inconsistent }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Inkonsistent
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-warning">{{ detailedAnalysis.position_bias?.primacy_count || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Primacy Bias
                    <a href="https://arxiv.org/abs/2406.07791" target="_blank" class="source-link" title="Shi et al. 2024">²</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-purple">{{ detailedAnalysis.position_bias?.recency_count || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Recency Bias
                    <a href="https://arxiv.org/abs/2406.07791" target="_blank" class="source-link" title="Shi et al. 2024">²</a>
                  </div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Likert Stability Analysis -->
            <v-card variant="outlined" class="mb-4" v-if="detailedAnalysis.likert_stability && Object.keys(detailedAnalysis.likert_stability).length">
              <v-card-title class="text-subtitle-1">
                <v-icon class="mr-2" size="small">mdi-chart-bell-curve</v-icon>
                Likert-Score Stabilität bei Position-Swap
                <a href="https://arxiv.org/abs/2310.05470" target="_blank" class="source-link ml-1" title="Auto-J / Li et al. 2023">³</a>
                <v-tooltip location="top">
                  <template v-slot:activator="{ props }">
                    <v-icon v-bind="props" size="small" class="ml-2">mdi-information-outline</v-icon>
                  </template>
                  <span>Misst wie stark sich Likert-Scores für denselben Thread ändern, wenn seine Position (A↔B) getauscht wird. Niedrigere Deltas = stabiler. (Auto-J Calibration)</span>
                </v-tooltip>
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6" lg="4" v-for="(data, metric) in detailedAnalysis.likert_stability" :key="metric">
                    <div class="d-flex align-center justify-space-between mb-1">
                      <span class="text-body-2">{{ formatLikertMetric(metric) }}</span>
                      <v-chip
                        size="x-small"
                        :color="data.stability_rate >= 0.8 ? 'success' : data.stability_rate >= 0.6 ? 'warning' : 'error'"
                      >
                        {{ Math.round(data.stability_rate * 100) }}% stabil
                      </v-chip>
                    </div>
                    <div class="d-flex align-center gap-2">
                      <v-progress-linear
                        :model-value="data.stability_rate * 100"
                        height="8"
                        rounded
                        :color="data.stability_rate >= 0.8 ? 'success' : data.stability_rate >= 0.6 ? 'warning' : 'error'"
                        class="flex-grow-1"
                      ></v-progress-linear>
                      <span class="text-caption text-medium-emphasis" style="min-width: 100px">
                        Ø Δ {{ data.mean_delta }} (max {{ data.max_delta }})
                      </span>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Detailed Pair Analysis Table -->
            <v-card variant="outlined" v-if="detailedAnalysis.pairs?.length">
              <v-card-title class="text-subtitle-1 d-flex align-center">
                <v-icon class="mr-2" size="small">mdi-table</v-icon>
                Detaillierte Paar-Analyse
                <v-chip size="x-small" class="ml-2" color="info">
                  {{ detailedAnalysis.pairs.length }} Paare
                </v-chip>
              </v-card-title>
              <v-divider></v-divider>
              <v-data-table
                :headers="detailedSwapHeaders"
                :items="detailedAnalysis.pairs"
                :items-per-page="10"
                density="compact"
                show-expand
                v-model:expanded="expandedSwapPairs"
              >
                <!-- Thread IDs -->
                <template v-slot:item.threads="{ item }">
                  <span class="text-caption">T{{ item.thread_1_id }} vs T{{ item.thread_2_id }}</span>
                </template>

                <!-- Original Result -->
                <template v-slot:item.original="{ item }">
                  <div class="d-flex align-center gap-1">
                    <v-chip size="x-small" :color="item.original.winner_position === 'A' ? 'blue' : item.original.winner_position === 'B' ? 'green' : 'grey'">
                      {{ item.original.winner_position || 'TIE' }}
                    </v-chip>
                    <span class="text-caption text-medium-emphasis">
                      ({{ Math.round((item.original.confidence || 0) * 100) }}%)
                    </span>
                  </div>
                </template>

                <!-- Swapped Result -->
                <template v-slot:item.swapped="{ item }">
                  <div class="d-flex align-center gap-1">
                    <v-chip size="x-small" :color="item.swapped.winner_position === 'A' ? 'blue' : item.swapped.winner_position === 'B' ? 'green' : 'grey'">
                      {{ item.swapped.winner_position || 'TIE' }}
                    </v-chip>
                    <span class="text-caption text-medium-emphasis">
                      ({{ Math.round((item.swapped.confidence || 0) * 100) }}%)
                    </span>
                  </div>
                </template>

                <!-- Consistency -->
                <template v-slot:item.consistency="{ item }">
                  <v-chip
                    size="x-small"
                    :color="item.is_consistent ? 'success' : 'error'"
                    variant="flat"
                  >
                    <v-icon start size="x-small">{{ item.is_consistent ? 'mdi-check' : 'mdi-alert' }}</v-icon>
                    {{ item.consistency_type === 'consistent_win' ? 'Win' :
                       item.consistency_type === 'consistent_tie' ? 'Tie' :
                       'Inkonsistent' }}
                  </v-chip>
                </template>

                <!-- Bias Direction -->
                <template v-slot:item.bias="{ item }">
                  <v-chip
                    v-if="item.bias_direction && item.bias_direction !== 'mixed'"
                    size="x-small"
                    :color="item.bias_direction === 'primacy' ? 'warning' : 'purple'"
                    variant="outlined"
                  >
                    {{ item.bias_direction === 'primacy' ? 'Primacy' : 'Recency' }}
                  </v-chip>
                  <span v-else-if="item.bias_direction === 'mixed'" class="text-caption text-medium-emphasis">Mixed</span>
                  <span v-else class="text-caption text-medium-emphasis">-</span>
                </template>

                <!-- Confidence Delta -->
                <template v-slot:item.conf_delta="{ item }">
                  <span :class="item.confidence_delta > 0.2 ? 'text-warning' : 'text-success'">
                    {{ (item.confidence_delta * 100).toFixed(1) }}%
                  </span>
                </template>

                <!-- Expanded Row - Likert Details -->
                <template v-slot:expanded-row="{ columns, item }">
                  <tr>
                    <td :colspan="columns.length" class="expanded-content pa-4">
                      <v-card variant="outlined">
                        <v-card-title class="text-subtitle-2">
                          <v-icon class="mr-2" size="small">mdi-chart-bar</v-icon>
                          Likert-Score Vergleich (Original vs Swapped)
                        </v-card-title>
                        <v-divider></v-divider>
                        <v-card-text>
                          <v-table density="compact">
                            <thead>
                              <tr>
                                <th>Metrik</th>
                                <th class="text-center" colspan="2">Thread 1 (T{{ item.thread_1_id }})</th>
                                <th class="text-center" colspan="2">Thread 2 (T{{ item.thread_2_id }})</th>
                              </tr>
                              <tr>
                                <th></th>
                                <th class="text-center text-caption">Als A</th>
                                <th class="text-center text-caption">Als B</th>
                                <th class="text-center text-caption">Als B</th>
                                <th class="text-center text-caption">Als A</th>
                              </tr>
                            </thead>
                            <tbody>
                              <tr v-for="metric in likertMetrics" :key="metric">
                                <td>{{ formatLikertMetric(metric) }}</td>
                                <td class="text-center">
                                  <v-chip size="x-small" :color="getScoreColor(item.likert_comparison[metric]?.thread_1?.original_score)">
                                    {{ item.likert_comparison[metric]?.thread_1?.original_score ?? '-' }}
                                  </v-chip>
                                </td>
                                <td class="text-center">
                                  <v-chip size="x-small" :color="getScoreColor(item.likert_comparison[metric]?.thread_1?.swapped_score)">
                                    {{ item.likert_comparison[metric]?.thread_1?.swapped_score ?? '-' }}
                                  </v-chip>
                                  <span v-if="item.likert_comparison[metric]?.thread_1?.delta !== null" class="ml-1 text-caption" :class="Math.abs(item.likert_comparison[metric]?.thread_1?.delta) > 1 ? 'text-warning' : 'text-success'">
                                    ({{ item.likert_comparison[metric]?.thread_1?.delta > 0 ? '+' : '' }}{{ item.likert_comparison[metric]?.thread_1?.delta }})
                                  </span>
                                </td>
                                <td class="text-center">
                                  <v-chip size="x-small" :color="getScoreColor(item.likert_comparison[metric]?.thread_2?.original_score)">
                                    {{ item.likert_comparison[metric]?.thread_2?.original_score ?? '-' }}
                                  </v-chip>
                                </td>
                                <td class="text-center">
                                  <v-chip size="x-small" :color="getScoreColor(item.likert_comparison[metric]?.thread_2?.swapped_score)">
                                    {{ item.likert_comparison[metric]?.thread_2?.swapped_score ?? '-' }}
                                  </v-chip>
                                  <span v-if="item.likert_comparison[metric]?.thread_2?.delta !== null" class="ml-1 text-caption" :class="Math.abs(item.likert_comparison[metric]?.thread_2?.delta) > 1 ? 'text-warning' : 'text-success'">
                                    ({{ item.likert_comparison[metric]?.thread_2?.delta > 0 ? '+' : '' }}{{ item.likert_comparison[metric]?.thread_2?.delta }})
                                  </span>
                                </td>
                              </tr>
                            </tbody>
                          </v-table>
                        </v-card-text>
                      </v-card>
                    </td>
                  </tr>
                </template>
              </v-data-table>
            </v-card>

            <!-- Methodology Reference -->
            <v-expansion-panels class="mt-4" v-if="detailedAnalysis.methodology">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon class="mr-2" size="small">mdi-book-open-variant</v-icon>
                  Methodik & Referenzen
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="mb-2"><strong>{{ detailedAnalysis.methodology.description }}</strong></p>

                  <!-- Metrics with Sources -->
                  <v-list density="compact">
                    <v-list-item v-for="(data, metric) in detailedAnalysis.methodology.metrics_explanation" :key="metric">
                      <template v-slot:prepend>
                        <v-icon size="small">mdi-circle-small</v-icon>
                      </template>
                      <v-list-item-title class="text-body-2">
                        <strong>{{ metric }}:</strong>
                        {{ typeof data === 'object' ? data.description : data }}
                        <a
                          v-if="typeof data === 'object' && data.source_url"
                          :href="data.source_url"
                          target="_blank"
                          class="source-link ml-1"
                          :title="data.source"
                        >
                          [{{ data.source }}]
                        </a>
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>

                  <v-divider class="my-3"></v-divider>

                  <!-- References with clickable links -->
                  <div class="text-subtitle-2 font-weight-bold mb-2">Referenzen:</div>
                  <v-list density="compact" class="reference-list">
                    <v-list-item
                      v-for="(ref, idx) in detailedAnalysis.methodology.references"
                      :key="idx"
                      class="reference-item"
                    >
                      <template v-slot:prepend>
                        <span class="text-caption font-weight-bold mr-2">[{{ idx + 1 }}]</span>
                      </template>
                      <v-list-item-title class="text-body-2">
                        <template v-if="typeof ref === 'object'">
                          <a :href="ref.url" target="_blank" class="reference-link">
                            {{ ref.authors }} ({{ ref.year }}): {{ ref.title }}
                          </a>
                          <div class="text-caption text-medium-emphasis mt-1">
                            {{ ref.key_contribution }}
                          </div>
                        </template>
                        <template v-else>
                          {{ ref }}
                        </template>
                      </v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </template>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>

  <!-- Legacy Position Swap Analysis (Fallback) -->
  <v-row class="mt-4" v-else-if="legacyAnalysis && legacyAnalysis.pairs.length > 0">
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
          Position-Swap Konsistenz
          <v-chip
            class="ml-3"
            :color="legacyAnalysis.consistencyRate >= 0.8 ? 'success' : legacyAnalysis.consistencyRate >= 0.6 ? 'warning' : 'error'"
            size="small"
          >
            {{ Math.round(legacyAnalysis.consistencyRate * 100) }}% konsistent
          </v-chip>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="card, table" />
          <template v-else>
            <v-alert
              :type="legacyAnalysis.consistencyRate >= 0.8 ? 'success' : legacyAnalysis.consistencyRate >= 0.6 ? 'warning' : 'error'"
              variant="tonal"
              class="mb-4"
            >
              <strong>{{ legacyAnalysis.consistent }}</strong> von <strong>{{ legacyAnalysis.total }}</strong> Swap-Paaren
              zeigten konsistente Ergebnisse (gleicher Gewinner unabhängig von Position A/B).
            </v-alert>

            <v-data-table
              :headers="swapHeaders"
              :items="legacyAnalysis.pairs"
              :items-per-page="10"
              density="compact"
            >
              <template v-slot:item.matchup="{ item }">
                {{ item.pillar_a_name }} vs {{ item.pillar_b_name }}
              </template>
              <template v-slot:item.original="{ item }">
                <v-chip size="x-small" :color="item.originalWinner === 'A' ? 'blue' : 'green'">
                  {{ item.originalWinner }} ({{ Math.round(item.originalConfidence * 100) }}%)
                </v-chip>
              </template>
              <template v-slot:item.swapped="{ item }">
                <v-chip size="x-small" :color="item.swappedWinner === 'A' ? 'blue' : 'green'">
                  {{ item.swappedWinner }} ({{ Math.round(item.swappedConfidence * 100) }}%)
                </v-chip>
              </template>
              <template v-slot:item.consistent="{ item }">
                <v-icon :color="item.isConsistent ? 'success' : 'error'">
                  {{ item.isConsistent ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>
            </v-data-table>
          </template>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue';
import { SWAP_HEADERS, DETAILED_SWAP_HEADERS, LIKERT_METRICS } from './composables';

const props = defineProps({
  loading: { type: Boolean, default: false },
  detailedAnalysis: { type: Object, default: null },
  legacyAnalysis: { type: Object, default: null },
  getConsistencyQualityColor: { type: Function, required: true },
  getBiasLabel: { type: Function, required: true },
  formatLikertMetric: { type: Function, required: true },
  getScoreColor: { type: Function, required: true }
});

const expandedSwapPairs = ref([]);
const swapHeaders = SWAP_HEADERS;
const detailedSwapHeaders = DETAILED_SWAP_HEADERS;
const likertMetrics = LIKERT_METRICS;
</script>

<style scoped>
.expanded-content {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
}

.source-link {
  font-size: 10px;
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  vertical-align: super;
  margin-left: 2px;
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.source-link:hover {
  opacity: 1;
  text-decoration: underline;
}

.reference-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  transition: color 0.2s ease;
}

.reference-link:hover {
  text-decoration: underline;
  color: rgb(var(--v-theme-secondary));
}
</style>
