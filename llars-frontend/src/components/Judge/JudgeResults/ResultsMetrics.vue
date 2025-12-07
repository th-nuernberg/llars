<template>
  <v-row>
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-chart-bar</v-icon>
          Detaillierte Metriken
        </v-card-title>
        <v-divider></v-divider>

        <v-skeleton-loader v-if="loading" type="table-thead, table-tbody" />
        <v-data-table
          v-else
          :headers="headers"
          :items="metrics"
          :items-per-page="10"
          class="metrics-table"
        >
          <!-- Pillar Name -->
          <template v-slot:item.name="{ item }">
            <div class="font-weight-bold">{{ item.name }}</div>
          </template>

          <!-- Wins -->
          <template v-slot:item.wins="{ item }">
            <v-chip size="small" color="success" variant="flat">
              {{ item.wins }}
            </v-chip>
          </template>

          <!-- Losses -->
          <template v-slot:item.losses="{ item }">
            <v-chip size="small" color="error" variant="flat">
              {{ item.losses }}
            </v-chip>
          </template>

          <!-- Win Rate -->
          <template v-slot:item.win_rate="{ item }">
            <div class="d-flex align-center">
              <v-progress-linear
                :model-value="item.win_rate * 100"
                height="20"
                rounded
                :color="getWinRateColor(item.win_rate)"
                class="flex-grow-1"
              >
                <template v-slot:default="{ value }">
                  <strong>{{ Math.round(value) }}%</strong>
                </template>
              </v-progress-linear>
            </div>
          </template>

          <!-- Avg Confidence -->
          <template v-slot:item.avg_confidence="{ item }">
            {{ Math.round(item.avg_confidence * 100) }}%
          </template>

          <!-- Score -->
          <template v-slot:item.score="{ item }">
            <div class="text-h6 font-weight-bold text-primary">
              {{ item.score.toFixed(2) }}
            </div>
          </template>

          <!-- Total Comparisons -->
          <template v-slot:item.total_comparisons="{ item }">
            {{ item.total_comparisons }}
          </template>
        </v-data-table>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { METRICS_HEADERS } from './composables';

const props = defineProps({
  loading: { type: Boolean, default: false },
  metrics: { type: Array, default: () => [] },
  getWinRateColor: { type: Function, required: true }
});

const headers = METRICS_HEADERS;
</script>

<style scoped>
.metrics-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
