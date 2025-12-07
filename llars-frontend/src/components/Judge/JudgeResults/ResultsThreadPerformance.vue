<template>
  <v-row class="mt-4" v-if="performance">
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-details</v-icon>
          Thread-Performance Analyse
          <v-chip class="ml-3" color="info" size="small">
            {{ performance.total_threads }} Threads
          </v-chip>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="card, table" />
          <template v-else>
            <!-- Summary Cards -->
            <v-row class="mb-4">
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-primary">{{ performance.total_threads }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Threads verwendet</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-info">{{ performance.avg_usage_per_thread }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Ø Verwendungen</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-success">{{ performance.consistent_winners?.length || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Konsistente Gewinner</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-error">{{ performance.consistent_losers?.length || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Konsistente Verlierer</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Coverage Stats -->
            <v-alert
              v-if="performance.coverage_stats"
              :type="performance.coverage_stats.under_sampled_count > performance.coverage_stats.evenly_sampled_count ? 'warning' : 'success'"
              variant="tonal"
              class="mb-4"
            >
              <strong>Sampling Coverage:</strong>
              {{ performance.coverage_stats.evenly_sampled_count }} gleichmäßig,
              {{ performance.coverage_stats.over_sampled_count }} über-verwendet,
              {{ performance.coverage_stats.under_sampled_count }} unter-verwendet
            </v-alert>

            <!-- Likert Consistency Global -->
            <v-card variant="outlined" class="mb-4" v-if="performance.likert_consistency?.global">
              <v-card-title class="text-subtitle-1">
                <v-icon class="mr-2" size="small">mdi-chart-bell-curve</v-icon>
                Globale Likert-Konsistenz
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6" lg="4" v-for="(data, metric) in performance.likert_consistency.global" :key="metric">
                    <div class="d-flex align-center justify-space-between mb-1">
                      <span class="text-body-2">{{ formatLikertMetric(metric) }}</span>
                      <v-chip
                        size="x-small"
                        :color="data.is_consistent ? 'success' : 'warning'"
                      >
                        {{ data.is_consistent ? 'Konsistent' : 'Variabel' }}
                      </v-chip>
                    </div>
                    <div class="d-flex align-center gap-2">
                      <v-progress-linear
                        :model-value="(data.mean / 5) * 100"
                        height="8"
                        rounded
                        color="primary"
                        class="flex-grow-1"
                      ></v-progress-linear>
                      <span class="text-caption text-medium-emphasis" style="min-width: 80px">
                        Ø {{ data.mean }} (σ {{ data.std_dev }})
                      </span>
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Consistent Winners/Losers -->
            <v-row class="mb-4" v-if="performance.consistent_winners?.length || performance.consistent_losers?.length">
              <v-col cols="12" md="6" v-if="performance.consistent_winners?.length">
                <v-card variant="tonal" color="success">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2" size="small">mdi-trophy</v-icon>
                    Konsistente Gewinner (≥70% Win-Rate)
                  </v-card-title>
                  <v-card-text>
                    <v-chip
                      v-for="thread in performance.consistent_winners.slice(0, 10)"
                      :key="thread.thread_id"
                      size="small"
                      class="ma-1"
                      color="success"
                      variant="flat"
                    >
                      Thread #{{ thread.thread_id }}
                      <span class="ml-1 text-caption">({{ getPillarName(thread.pillar) }}, {{ Math.round(thread.win_rate * 100) }}%)</span>
                    </v-chip>
                    <div v-if="performance.consistent_winners.length > 10" class="text-caption mt-2">
                      ... und {{ performance.consistent_winners.length - 10 }} weitere
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="6" v-if="performance.consistent_losers?.length">
                <v-card variant="tonal" color="error">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2" size="small">mdi-alert-circle</v-icon>
                    Konsistente Verlierer (≥70% Loss-Rate)
                  </v-card-title>
                  <v-card-text>
                    <v-chip
                      v-for="thread in performance.consistent_losers.slice(0, 10)"
                      :key="thread.thread_id"
                      size="small"
                      class="ma-1"
                      color="error"
                      variant="flat"
                    >
                      Thread #{{ thread.thread_id }}
                      <span class="ml-1 text-caption">({{ getPillarName(thread.pillar) }}, {{ Math.round(thread.loss_rate * 100) }}%)</span>
                    </v-chip>
                    <div v-if="performance.consistent_losers.length > 10" class="text-caption mt-2">
                      ... und {{ performance.consistent_losers.length - 10 }} weitere
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Thread Table -->
            <v-data-table
              :headers="threadHeaders"
              :items="performance.threads"
              :items-per-page="10"
              density="compact"
              class="thread-table"
              show-expand
              v-model:expanded="expandedThreadRows"
            >
              <!-- Thread ID -->
              <template v-slot:item.thread_id="{ item }">
                <span class="font-weight-medium">#{{ item.thread_id }}</span>
              </template>

              <!-- Pillar -->
              <template v-slot:item.pillar="{ item }">
                <v-chip size="x-small" color="primary" variant="outlined">
                  {{ getPillarName(item.pillar) }}
                </v-chip>
              </template>

              <!-- Usage Count -->
              <template v-slot:item.usage_count="{ item }">
                <v-chip
                  size="x-small"
                  :color="item.usage_count > performance.avg_usage_per_thread * 1.5 ? 'warning' : item.usage_count < performance.avg_usage_per_thread * 0.5 ? 'error' : 'grey'"
                >
                  {{ item.usage_count }}x
                </v-chip>
              </template>

              <!-- Wins -->
              <template v-slot:item.wins="{ item }">
                <span class="text-success font-weight-medium">{{ item.wins }}</span>
              </template>

              <!-- Losses -->
              <template v-slot:item.losses="{ item }">
                <span class="text-error font-weight-medium">{{ item.losses }}</span>
              </template>

              <!-- Win Rate -->
              <template v-slot:item.win_rate="{ item }">
                <v-progress-linear
                  :model-value="item.win_rate * 100"
                  height="16"
                  rounded
                  :color="getWinRateColor(item.win_rate)"
                  style="min-width: 80px"
                >
                  <template v-slot:default="{ value }">
                    <span class="text-caption">{{ Math.round(value) }}%</span>
                  </template>
                </v-progress-linear>
              </template>

              <!-- Likert Consistency -->
              <template v-slot:item.likert_consistency_score="{ item }">
                <v-chip
                  size="x-small"
                  :color="getLikertConsistencyColor(item.likert_consistency_score)"
                >
                  {{ Math.round(item.likert_consistency_score * 100) }}%
                </v-chip>
              </template>

              <!-- Status -->
              <template v-slot:item.status="{ item }">
                <v-icon v-if="item.is_consistent_winner" color="success" size="small">mdi-trophy</v-icon>
                <v-icon v-else-if="item.is_consistent_loser" color="error" size="small">mdi-alert-circle</v-icon>
                <v-icon v-else color="grey" size="small">mdi-minus</v-icon>
              </template>

              <!-- Expanded Row - Likert Details -->
              <template v-slot:expanded-row="{ columns, item }">
                <tr>
                  <td :colspan="columns.length" class="expanded-content pa-4">
                    <v-card variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2" size="small">mdi-chart-bar</v-icon>
                        Likert-Scores für Thread #{{ item.thread_id }}
                      </v-card-title>
                      <v-divider></v-divider>
                      <v-card-text>
                        <v-row v-if="item.likert_scores && Object.keys(item.likert_scores).length > 0">
                          <v-col cols="12" md="6" lg="4" v-for="(data, metric) in item.likert_scores" :key="metric">
                            <div class="d-flex align-center justify-space-between mb-1">
                              <span class="text-body-2">{{ formatLikertMetric(metric) }}</span>
                              <v-chip
                                size="x-small"
                                :color="data.is_consistent ? 'success' : 'warning'"
                              >
                                {{ data.count }}x bewertet
                              </v-chip>
                            </div>
                            <div class="d-flex align-center gap-2 mb-2">
                              <v-progress-linear
                                :model-value="(data.mean / 5) * 100"
                                height="12"
                                rounded
                                :color="getScoreColor(data.mean)"
                                class="flex-grow-1"
                              ></v-progress-linear>
                              <span class="text-caption" style="min-width: 100px">
                                Ø {{ data.mean }} ({{ data.min }}-{{ data.max }})
                              </span>
                            </div>
                            <div class="text-caption text-medium-emphasis">
                              σ = {{ data.std_dev }}
                              <v-icon v-if="data.is_consistent" size="x-small" color="success" class="ml-1">mdi-check</v-icon>
                              <v-icon v-else size="x-small" color="warning" class="ml-1">mdi-alert</v-icon>
                            </div>
                          </v-col>
                        </v-row>
                        <div v-else class="text-center text-medium-emphasis py-4">
                          Keine Likert-Daten verfügbar
                        </div>
                      </v-card-text>
                    </v-card>
                  </td>
                </tr>
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
import { THREAD_HEADERS } from './composables';

const props = defineProps({
  loading: { type: Boolean, default: false },
  performance: { type: Object, default: null },
  formatLikertMetric: { type: Function, required: true },
  getPillarName: { type: Function, required: true },
  getWinRateColor: { type: Function, required: true },
  getLikertConsistencyColor: { type: Function, required: true },
  getScoreColor: { type: Function, required: true }
});

const expandedThreadRows = ref([]);
const threadHeaders = THREAD_HEADERS;
</script>

<style scoped>
.thread-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.thread-table :deep(.v-data-table__td) {
  padding: 8px 12px;
}

.expanded-content {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
}
</style>
