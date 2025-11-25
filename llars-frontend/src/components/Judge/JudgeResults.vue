<template>
  <v-container class="judge-results">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.push({ name: 'JudgeSession', params: { id: sessionId } })"
          ></v-btn>
          <div class="ml-2">
            <h1 class="text-h4 font-weight-bold">Auswertung</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              {{ session?.session_name }} - {{ session?.pillar_count }} Säulen
            </p>
          </div>
          <v-spacer></v-spacer>

          <!-- Export Buttons -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                color="primary"
                prepend-icon="mdi-download"
              >
                Export
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="exportCSV">
                <template v-slot:prepend>
                  <v-icon>mdi-file-delimited</v-icon>
                </template>
                <v-list-item-title>Als CSV</v-list-item-title>
              </v-list-item>
              <v-list-item @click="exportJSON">
                <template v-slot:prepend>
                  <v-icon>mdi-code-json</v-icon>
                </template>
                <v-list-item-title>Als JSON</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </v-col>
    </v-row>

    <!-- Session Summary Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="primary" size="56" class="mr-4">
              <v-icon icon="mdi-compare" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ results?.total_comparisons || 0 }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Gesamt Vergleiche</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="success" size="56" class="mr-4">
              <v-icon icon="mdi-trophy" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ topPillar?.name || '-' }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Beste Säule</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" size="56" class="mr-4">
              <v-icon icon="mdi-percent" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ averageConfidence }}%</div>
              <div class="text-subtitle-2 text-medium-emphasis">Ø Konfidenz</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="warning" size="56" class="mr-4">
              <v-icon icon="mdi-clock-outline" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ duration }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Laufzeit</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Pillar Ranking -->
    <v-row class="mb-4">
      <v-col cols="12" lg="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-podium</v-icon>
            Säulen-Ranking
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="(pillar, index) in pillarRanking"
                :key="pillar.pillar_id"
                class="ranking-item mb-2"
              >
                <template v-slot:prepend>
                  <v-avatar
                    :color="getRankColor(index)"
                    size="48"
                    class="mr-3"
                  >
                    <span class="text-h6 font-weight-bold">{{ index + 1 }}</span>
                  </v-avatar>
                </template>

                <v-list-item-title class="text-h6 font-weight-bold">
                  {{ pillar.name }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <div class="d-flex align-center mt-2">
                    <v-chip size="small" color="success" variant="outlined" class="mr-2">
                      {{ pillar.wins }} Siege
                    </v-chip>
                    <v-chip size="small" color="error" variant="outlined" class="mr-2">
                      {{ pillar.losses }} Niederlagen
                    </v-chip>
                    <v-chip size="small" color="grey" variant="outlined">
                      {{ Math.round(pillar.win_rate * 100) }}% Siegrate
                    </v-chip>
                  </div>
                </v-list-item-subtitle>

                <template v-slot:append>
                  <div class="text-right">
                    <div class="text-h5 font-weight-bold text-primary">
                      {{ pillar.score.toFixed(2) }}
                    </div>
                    <div class="text-caption text-medium-emphasis">Score</div>
                  </div>
                </template>
              </v-list-item>
            </v-list>

            <!-- Empty State -->
            <div v-if="pillarRanking.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-line</v-icon>
              <div class="text-h6 mt-4 text-medium-emphasis">Keine Daten verfügbar</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Win Matrix Heatmap -->
      <v-col cols="12" lg="6">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-grid</v-icon>
            Vergleichs-Matrix
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <div class="matrix-container">
              <table class="win-matrix">
                <thead>
                  <tr>
                    <th class="corner-cell"></th>
                    <th v-for="pillar in pillarList" :key="'header-' + pillar.pillar_id" class="header-cell">
                      {{ pillar.name }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pillarA in pillarList" :key="'row-' + pillarA.pillar_id">
                    <th class="row-header">{{ pillarA.name }}</th>
                    <td
                      v-for="pillarB in pillarList"
                      :key="'cell-' + pillarA.pillar_id + '-' + pillarB.pillar_id"
                      class="matrix-cell"
                      :class="getMatrixCellClass(pillarA.pillar_id, pillarB.pillar_id)"
                      :style="getMatrixCellStyle(pillarA.pillar_id, pillarB.pillar_id)"
                    >
                      {{ getMatrixValue(pillarA.pillar_id, pillarB.pillar_id) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="text-caption text-medium-emphasis mt-2 text-center">
              Zeile = Angreifer, Spalte = Verteidiger. Werte = Anzahl Siege.
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Metrics Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-chart-bar</v-icon>
            Detaillierte Metriken
          </v-card-title>
          <v-divider></v-divider>

          <v-data-table
            :headers="metricsHeaders"
            :items="pillarMetrics"
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

    <!-- Comparison Details -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-format-list-bulleted-square</v-icon>
            Alle Vergleiche ({{ allComparisons.length }})
          </v-card-title>
          <v-divider></v-divider>

          <v-data-table
            :headers="comparisonHeaders"
            :items="allComparisons"
            :items-per-page="20"
            class="comparisons-table"
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
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const sessionId = route.params.id;

// State
const session = ref(null);
const results = ref(null);
const allComparisons = ref([]);
const loading = ref(false);

// Metrics Table Headers
const metricsHeaders = [
  { title: 'Säule', key: 'name', sortable: true },
  { title: 'Siege', key: 'wins', sortable: true },
  { title: 'Niederlagen', key: 'losses', sortable: true },
  { title: 'Siegrate', key: 'win_rate', sortable: true },
  { title: 'Ø Konfidenz', key: 'avg_confidence', sortable: true },
  { title: 'Score', key: 'score', sortable: true },
  { title: 'Vergleiche', key: 'total_comparisons', sortable: true }
];

// Comparison Table Headers
const comparisonHeaders = [
  { title: '#', key: 'comparison_index', sortable: true },
  { title: 'Paarung', key: 'matchup', sortable: false },
  { title: 'Gewinner', key: 'winner', sortable: true },
  { title: 'Konfidenz', key: 'confidence_score', sortable: true },
  { title: 'Zeitpunkt', key: 'evaluated_at', sortable: true }
];

// Computed
const pillarRanking = computed(() => {
  if (!results.value?.pillar_metrics) return [];
  return [...results.value.pillar_metrics].sort((a, b) => b.score - a.score);
});

const pillarList = computed(() => {
  if (!results.value?.pillar_metrics) return [];
  return results.value.pillar_metrics;
});

const pillarMetrics = computed(() => {
  if (!results.value?.pillar_metrics) return [];
  return results.value.pillar_metrics;
});

const topPillar = computed(() => {
  return pillarRanking.value[0] || null;
});

const averageConfidence = computed(() => {
  if (!results.value?.pillar_metrics || results.value.pillar_metrics.length === 0) return 0;
  const sum = results.value.pillar_metrics.reduce((acc, p) => acc + p.avg_confidence, 0);
  return Math.round((sum / results.value.pillar_metrics.length) * 100);
});

const duration = computed(() => {
  if (!session.value?.created_at || !session.value?.completed_at) return '-';
  const start = new Date(session.value.created_at);
  const end = new Date(session.value.completed_at);
  const diff = end - start;
  const minutes = Math.floor(diff / 60000);
  const seconds = Math.floor((diff % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
});

// Load Results
const loadResults = async () => {
  loading.value = true;
  try {
    // Load session info
    const sessionResponse = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}`
    );
    session.value = sessionResponse.data;

    // Load results
    const resultsResponse = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/results`
    );
    results.value = resultsResponse.data;

    // Load all comparisons
    const comparisonsResponse = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/comparisons`
    );
    allComparisons.value = comparisonsResponse.data;
  } catch (error) {
    console.error('Error loading results:', error);
  } finally {
    loading.value = false;
  }
};

// Matrix Functions
const getMatrixValue = (pillarA, pillarB) => {
  if (pillarA === pillarB) return '-';
  if (!results.value?.win_matrix) return '0';

  const key = `${pillarA}_vs_${pillarB}`;
  return results.value.win_matrix[key] || 0;
};

const getMatrixCellClass = (pillarA, pillarB) => {
  if (pillarA === pillarB) return 'diagonal-cell';
  return '';
};

const getMatrixCellStyle = (pillarA, pillarB) => {
  if (pillarA === pillarB) return {};

  const value = getMatrixValue(pillarA, pillarB);
  const maxValue = Math.max(
    ...Object.values(results.value?.win_matrix || {})
  );

  if (maxValue === 0) return {};

  const intensity = value / maxValue;
  const hue = 120; // Green hue
  const saturation = 60;
  const lightness = 90 - (intensity * 40); // Lighter = less wins

  return {
    backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
    fontWeight: intensity > 0.5 ? 'bold' : 'normal'
  };
};

// Utility Functions
const getRankColor = (index) => {
  const colors = ['warning', 'grey-lighten-1', 'orange-lighten-1', 'grey-lighten-2', 'grey-lighten-3'];
  return colors[index] || 'grey';
};

const getWinRateColor = (winRate) => {
  if (winRate >= 0.7) return 'success';
  if (winRate >= 0.5) return 'info';
  if (winRate >= 0.3) return 'warning';
  return 'error';
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'info';
  if (confidence >= 0.4) return 'warning';
  return 'error';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Export Functions
const exportCSV = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/export/csv`,
      { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `judge_results_${sessionId}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error exporting CSV:', error);
  }
};

const exportJSON = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/export/json`
    );

    const dataStr = JSON.stringify(response.data, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = window.URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `judge_results_${sessionId}.json`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error exporting JSON:', error);
  }
};

// Lifecycle
onMounted(() => {
  loadResults();
});
</script>

<style scoped>
.judge-results {
  max-width: 1600px;
  margin: 0 auto;
}

.stat-card {
  height: 100%;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.ranking-item {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px;
  transition: background-color 0.2s ease;
}

.ranking-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.matrix-container {
  overflow-x: auto;
}

.win-matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.win-matrix th,
.win-matrix td {
  padding: 12px;
  text-align: center;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.win-matrix .corner-cell {
  background-color: rgb(var(--v-theme-surface-variant));
}

.win-matrix .header-cell,
.win-matrix .row-header {
  background-color: rgb(var(--v-theme-surface-variant));
  font-weight: bold;
  font-size: 12px;
}

.win-matrix .matrix-cell {
  transition: all 0.2s ease;
  font-weight: 500;
}

.win-matrix .matrix-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.win-matrix .diagonal-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.38);
}

.metrics-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.comparisons-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
