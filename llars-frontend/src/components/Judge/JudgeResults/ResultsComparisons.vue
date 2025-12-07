<template>
  <v-row class="mt-4">
    <v-col cols="12">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-format-list-bulleted-square</v-icon>
          Alle Vergleiche ({{ comparisons.length }})
        </v-card-title>
        <v-divider></v-divider>

        <v-skeleton-loader v-if="loading" type="table-thead, table-tbody" />
        <v-data-table
          v-else
          :headers="headers"
          :items="comparisons"
          :items-per-page="20"
          class="comparisons-table"
          show-expand
          v-model:expanded="expandedRows"
        >
          <!-- Index -->
          <template v-slot:item.comparison_index="{ item }">
            <span class="font-weight-bold">#{{ item.comparison_index + 1 }}</span>
          </template>

          <!-- Matchup -->
          <template v-slot:item.matchup="{ item }">
            <div class="d-flex align-center gap-2">
              <v-chip size="small" color="blue" variant="outlined">
                {{ item.pillar_a_name }}
              </v-chip>
              <v-icon size="small">mdi-sword-cross</v-icon>
              <v-chip size="small" color="green" variant="outlined">
                {{ item.pillar_b_name }}
              </v-chip>
              <v-chip v-if="item.position_order === 2" size="x-small" color="warning" variant="tonal">
                <v-icon start size="x-small">mdi-swap-horizontal</v-icon>
                Swapped
              </v-chip>
            </div>
          </template>

          <!-- Winner -->
          <template v-slot:item.winner="{ item }">
            <v-chip
              size="small"
              :color="item.winner === 'A' ? 'blue' : item.winner === 'B' ? 'green' : 'grey'"
              variant="flat"
            >
              <v-icon start size="small">mdi-trophy</v-icon>
              {{ item.winner }}
            </v-chip>
          </template>

          <!-- Confidence -->
          <template v-slot:item.confidence_score="{ item }">
            <v-chip
              size="small"
              :color="getConfidenceColor(item.confidence_score)"
              variant="outlined"
            >
              {{ Math.round(item.confidence_score * 100) }}%
            </v-chip>
          </template>

          <!-- Evaluated At -->
          <template v-slot:item.evaluated_at="{ item }">
            {{ formatDate(item.evaluated_at) }}
          </template>

          <!-- Expanded Row - LLM Output -->
          <template v-slot:expanded-row="{ columns, item }">
            <tr>
              <td :colspan="columns.length" class="expanded-content pa-4">
                <v-card variant="outlined">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2" size="small">mdi-robot</v-icon>
                    LLM Raw Output
                  </v-card-title>
                  <v-divider></v-divider>
                  <v-card-text>
                    <!-- Reasoning -->
                    <div v-if="item.reasoning" class="mb-4">
                      <div class="text-subtitle-2 font-weight-bold mb-2">Begründung:</div>
                      <div class="reasoning-text">{{ item.reasoning }}</div>
                    </div>

                    <!-- Scores -->
                    <div v-if="item.scores" class="mb-4">
                      <div class="text-subtitle-2 font-weight-bold mb-2">Einzelbewertungen:</div>
                      <v-table density="compact">
                        <thead>
                          <tr>
                            <th>Kriterium</th>
                            <th class="text-center">A</th>
                            <th class="text-center">B</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(score, criterion) in item.scores" :key="criterion">
                            <td>{{ formatCriterionName(criterion) }}</td>
                            <td class="text-center">
                              <v-chip size="x-small" :color="getScoreColor(score.a)">{{ score.a }}</v-chip>
                            </td>
                            <td class="text-center">
                              <v-chip size="x-small" :color="getScoreColor(score.b)">{{ score.b }}</v-chip>
                            </td>
                          </tr>
                        </tbody>
                      </v-table>
                    </div>

                    <!-- Raw Response -->
                    <v-expansion-panels v-if="item.raw_response">
                      <v-expansion-panel>
                        <v-expansion-panel-title>
                          <v-icon class="mr-2" size="small">mdi-code-json</v-icon>
                          Raw LLM Response ({{ item.raw_response?.length || 0 }} Zeichen)
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <pre class="raw-output">{{ item.raw_response }}</pre>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-card-text>
                </v-card>
              </td>
            </tr>
          </template>
        </v-data-table>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
import { ref } from 'vue';
import { COMPARISON_HEADERS } from './composables';

const props = defineProps({
  loading: { type: Boolean, default: false },
  comparisons: { type: Array, default: () => [] },
  getConfidenceColor: { type: Function, required: true },
  getScoreColor: { type: Function, required: true },
  formatDate: { type: Function, required: true },
  formatCriterionName: { type: Function, required: true }
});

const expandedRows = ref([]);
const headers = COMPARISON_HEADERS;
</script>

<style scoped>
.comparisons-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.expanded-content {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
}

.reasoning-text {
  background-color: rgba(var(--v-theme-surface), 0.8);
  padding: 12px;
  border-radius: 6px;
  font-style: italic;
  line-height: 1.6;
  border-left: 3px solid rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-surface));
}

.raw-output {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 12px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}
</style>
