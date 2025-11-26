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

    <!-- Position Swap Consistency Analysis (Detailed) -->
    <v-row class="mt-4" v-if="positionSwapDetailed && positionSwapDetailed.summary">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center flex-wrap">
            <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
            Position-Swap Konsistenz (MT-Bench Methodik)
            <v-chip
              class="ml-3"
              :color="getConsistencyQualityColor(positionSwapDetailed.interpretation?.overall_quality)"
              size="small"
            >
              {{ Math.round(positionSwapDetailed.summary.consistency_rate * 100) }}% konsistent
            </v-chip>
            <v-chip
              class="ml-2"
              :color="positionSwapDetailed.position_bias?.dominant_bias === 'balanced' ? 'success' : 'warning'"
              size="small"
              variant="outlined"
            >
              {{ getBiasLabel(positionSwapDetailed.position_bias?.dominant_bias) }}
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <!-- Interpretation Alert -->
            <v-alert
              :type="positionSwapDetailed.interpretation?.overall_quality === 'excellent' ? 'success' :
                     positionSwapDetailed.interpretation?.overall_quality === 'good' ? 'info' :
                     positionSwapDetailed.interpretation?.overall_quality === 'fair' ? 'warning' : 'error'"
              variant="tonal"
              class="mb-4"
            >
              <div v-for="(rec, idx) in positionSwapDetailed.interpretation?.recommendations" :key="idx">
                {{ rec }}
              </div>
            </v-alert>

            <!-- Summary Cards -->
            <v-row class="mb-4">
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-primary">{{ positionSwapDetailed.summary.total_swap_pairs }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Swap-Paare</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-success">{{ positionSwapDetailed.summary.consistent_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Konsistent (Win)
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-info">{{ positionSwapDetailed.summary.consistent_ties }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Konsistent (Tie)
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-error">{{ positionSwapDetailed.summary.inconsistent }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Inkonsistent
                    <a href="https://arxiv.org/abs/2306.05685" target="_blank" class="source-link" title="Zheng et al. 2023">¹</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-warning">{{ positionSwapDetailed.position_bias?.primacy_count || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Primacy Bias
                    <a href="https://arxiv.org/abs/2406.07791" target="_blank" class="source-link" title="Shi et al. 2024">²</a>
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="2">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-purple">{{ positionSwapDetailed.position_bias?.recency_count || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">
                    Recency Bias
                    <a href="https://arxiv.org/abs/2406.07791" target="_blank" class="source-link" title="Shi et al. 2024">²</a>
                  </div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Likert Stability Analysis -->
            <v-card variant="outlined" class="mb-4" v-if="positionSwapDetailed.likert_stability && Object.keys(positionSwapDetailed.likert_stability).length">
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
                  <v-col cols="12" md="6" lg="4" v-for="(data, metric) in positionSwapDetailed.likert_stability" :key="metric">
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
            <v-card variant="outlined" v-if="positionSwapDetailed.pairs?.length">
              <v-card-title class="text-subtitle-1 d-flex align-center">
                <v-icon class="mr-2" size="small">mdi-table</v-icon>
                Detaillierte Paar-Analyse
                <v-chip size="x-small" class="ml-2" color="info">
                  {{ positionSwapDetailed.pairs.length }} Paare
                </v-chip>
              </v-card-title>
              <v-divider></v-divider>
              <v-data-table
                :headers="detailedSwapHeaders"
                :items="positionSwapDetailed.pairs"
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
                              <tr v-for="metric in ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation']" :key="metric">
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
            <v-expansion-panels class="mt-4" v-if="positionSwapDetailed.methodology">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon class="mr-2" size="small">mdi-book-open-variant</v-icon>
                  Methodik & Referenzen
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="mb-2"><strong>{{ positionSwapDetailed.methodology.description }}</strong></p>

                  <!-- Metrics with Sources -->
                  <v-list density="compact">
                    <v-list-item v-for="(data, metric) in positionSwapDetailed.methodology.metrics_explanation" :key="metric">
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
                      v-for="(ref, idx) in positionSwapDetailed.methodology.references"
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
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Legacy Position Swap Analysis (Fallback) -->
    <v-row class="mt-4" v-else-if="positionSwapAnalysis.pairs.length > 0">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-swap-horizontal</v-icon>
            Position-Swap Konsistenz
            <v-chip
              class="ml-3"
              :color="positionSwapAnalysis.consistencyRate >= 0.8 ? 'success' : positionSwapAnalysis.consistencyRate >= 0.6 ? 'warning' : 'error'"
              size="small"
            >
              {{ Math.round(positionSwapAnalysis.consistencyRate * 100) }}% konsistent
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-alert
              :type="positionSwapAnalysis.consistencyRate >= 0.8 ? 'success' : positionSwapAnalysis.consistencyRate >= 0.6 ? 'warning' : 'error'"
              variant="tonal"
              class="mb-4"
            >
              <strong>{{ positionSwapAnalysis.consistent }}</strong> von <strong>{{ positionSwapAnalysis.total }}</strong> Swap-Paaren
              zeigten konsistente Ergebnisse (gleicher Gewinner unabhängig von Position A/B).
            </v-alert>

            <v-data-table
              :headers="swapHeaders"
              :items="positionSwapAnalysis.pairs"
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
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Verbosity Bias Analysis -->
    <v-row class="mt-4" v-if="verbosityAnalysis">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-text-long</v-icon>
            Verbosity Bias Analyse
            <v-chip
              class="ml-3"
              :color="verbosityBiasColor"
              size="small"
            >
              {{ Math.round(verbosityAnalysis.verbosity_bias_rate * 100) }}% längerer gewinnt
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-alert
              :type="verbosityBiasType"
              variant="tonal"
              class="mb-4"
            >
              <template v-if="verbosityAnalysis.verbosity_bias_rate > 0.6">
                <strong>Warnung:</strong> Das LLM zeigt einen starken Verbosity Bias - längere Threads werden bevorzugt.
              </template>
              <template v-else-if="verbosityAnalysis.verbosity_bias_rate < 0.4">
                <strong>Info:</strong> Das LLM bevorzugt kürzere Threads - möglicherweise negatives Verbosity Bias.
              </template>
              <template v-else>
                <strong>Gut:</strong> Keine signifikante Präferenz für Thread-Länge erkannt.
              </template>
            </v-alert>

            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-success">{{ verbosityAnalysis.longer_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Längerer Thread gewinnt</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-error">{{ verbosityAnalysis.shorter_wins }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Kürzerer Thread gewinnt</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h3 font-weight-bold text-grey">{{ verbosityAnalysis.ties }}</div>
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
                      <td class="text-right font-weight-bold">{{ Math.round(verbosityAnalysis.avg_length_winner).toLocaleString() }}</td>
                    </tr>
                    <tr>
                      <td>Verlierer</td>
                      <td class="text-right font-weight-bold">{{ Math.round(verbosityAnalysis.avg_length_loser).toLocaleString() }}</td>
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
                  :model-value="verbosityAnalysis.verbosity_bias_rate * 100"
                  height="30"
                  rounded
                  :color="verbosityBiasColor"
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
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Thread Performance Analysis -->
    <v-row class="mt-4" v-if="threadPerformance">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-account-details</v-icon>
            Thread-Performance Analyse
            <v-chip class="ml-3" color="info" size="small">
              {{ threadPerformance.total_threads }} Threads
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <!-- Summary Cards -->
            <v-row class="mb-4">
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-primary">{{ threadPerformance.total_threads }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Threads verwendet</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-info">{{ threadPerformance.avg_usage_per_thread }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Ø Verwendungen</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-success">{{ threadPerformance.consistent_winners?.length || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Konsistente Gewinner</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="3">
                <v-card variant="outlined" class="text-center pa-3">
                  <div class="text-h4 font-weight-bold text-error">{{ threadPerformance.consistent_losers?.length || 0 }}</div>
                  <div class="text-subtitle-2 text-medium-emphasis">Konsistente Verlierer</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Coverage Stats -->
            <v-alert
              v-if="threadPerformance.coverage_stats"
              :type="threadPerformance.coverage_stats.under_sampled_count > threadPerformance.coverage_stats.evenly_sampled_count ? 'warning' : 'success'"
              variant="tonal"
              class="mb-4"
            >
              <strong>Sampling Coverage:</strong>
              {{ threadPerformance.coverage_stats.evenly_sampled_count }} gleichmäßig,
              {{ threadPerformance.coverage_stats.over_sampled_count }} über-verwendet,
              {{ threadPerformance.coverage_stats.under_sampled_count }} unter-verwendet
            </v-alert>

            <!-- Likert Consistency Global -->
            <v-card variant="outlined" class="mb-4" v-if="threadPerformance.likert_consistency?.global">
              <v-card-title class="text-subtitle-1">
                <v-icon class="mr-2" size="small">mdi-chart-bell-curve</v-icon>
                Globale Likert-Konsistenz
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text>
                <v-row>
                  <v-col cols="12" md="6" lg="4" v-for="(data, metric) in threadPerformance.likert_consistency.global" :key="metric">
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
            <v-row class="mb-4" v-if="threadPerformance.consistent_winners?.length || threadPerformance.consistent_losers?.length">
              <v-col cols="12" md="6" v-if="threadPerformance.consistent_winners?.length">
                <v-card variant="tonal" color="success">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2" size="small">mdi-trophy</v-icon>
                    Konsistente Gewinner (≥70% Win-Rate)
                  </v-card-title>
                  <v-card-text>
                    <v-chip
                      v-for="thread in threadPerformance.consistent_winners.slice(0, 10)"
                      :key="thread.thread_id"
                      size="small"
                      class="ma-1"
                      color="success"
                      variant="flat"
                    >
                      Thread #{{ thread.thread_id }}
                      <span class="ml-1 text-caption">({{ getPillarName(thread.pillar) }}, {{ Math.round(thread.win_rate * 100) }}%)</span>
                    </v-chip>
                    <div v-if="threadPerformance.consistent_winners.length > 10" class="text-caption mt-2">
                      ... und {{ threadPerformance.consistent_winners.length - 10 }} weitere
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="6" v-if="threadPerformance.consistent_losers?.length">
                <v-card variant="tonal" color="error">
                  <v-card-title class="text-subtitle-1">
                    <v-icon class="mr-2" size="small">mdi-alert-circle</v-icon>
                    Konsistente Verlierer (≥70% Loss-Rate)
                  </v-card-title>
                  <v-card-text>
                    <v-chip
                      v-for="thread in threadPerformance.consistent_losers.slice(0, 10)"
                      :key="thread.thread_id"
                      size="small"
                      class="ma-1"
                      color="error"
                      variant="flat"
                    >
                      Thread #{{ thread.thread_id }}
                      <span class="ml-1 text-caption">({{ getPillarName(thread.pillar) }}, {{ Math.round(thread.loss_rate * 100) }}%)</span>
                    </v-chip>
                    <div v-if="threadPerformance.consistent_losers.length > 10" class="text-caption mt-2">
                      ... und {{ threadPerformance.consistent_losers.length - 10 }} weitere
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Thread Table -->
            <v-data-table
              :headers="threadHeaders"
              :items="threadPerformance.threads"
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
                  :color="item.usage_count > threadPerformance.avg_usage_per_thread * 1.5 ? 'warning' : item.usage_count < threadPerformance.avg_usage_per_thread * 0.5 ? 'error' : 'grey'"
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
          </v-card-text>
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
const verbosityAnalysis = ref(null);
const threadPerformance = ref(null);
const positionSwapDetailed = ref(null);
const loading = ref(false);
const expandedRows = ref([]);
const expandedThreadRows = ref([]);
const expandedSwapPairs = ref([]);

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

// Position Swap Analysis Headers (Legacy)
const swapHeaders = [
  { title: 'Paarung', key: 'matchup', sortable: false },
  { title: 'Original (Pos 1)', key: 'original', sortable: false },
  { title: 'Swapped (Pos 2)', key: 'swapped', sortable: false },
  { title: 'Konsistent', key: 'consistent', sortable: true }
];

// Detailed Position Swap Analysis Headers
const detailedSwapHeaders = [
  { title: 'Threads', key: 'threads', sortable: false },
  { title: 'Original', key: 'original', sortable: false },
  { title: 'Swapped', key: 'swapped', sortable: false },
  { title: 'Konsistenz', key: 'consistency', sortable: true },
  { title: 'Bias', key: 'bias', sortable: true },
  { title: 'Konf. Δ', key: 'conf_delta', sortable: true }
];

// Thread Performance Headers
const threadHeaders = [
  { title: 'Thread', key: 'thread_id', sortable: true },
  { title: 'Säule', key: 'pillar', sortable: true },
  { title: 'Verwendungen', key: 'usage_count', sortable: true },
  { title: 'Siege', key: 'wins', sortable: true },
  { title: 'Niederlagen', key: 'losses', sortable: true },
  { title: 'Win-Rate', key: 'win_rate', sortable: true },
  { title: 'Likert-Konsistenz', key: 'likert_consistency_score', sortable: true },
  { title: 'Status', key: 'status', sortable: false }
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

// Position Swap Consistency Analysis
const positionSwapAnalysis = computed(() => {
  if (!allComparisons.value || allComparisons.value.length === 0) {
    return { pairs: [], consistent: 0, total: 0, consistencyRate: 0 };
  }

  // Group comparisons by pillar pair (regardless of position)
  const pairGroups = {};

  for (const comp of allComparisons.value) {
    if (!comp.winner) continue;

    // Create a consistent key for the pair (sorted pillar IDs)
    const sortedPillars = [comp.pillar_a, comp.pillar_b].sort((a, b) => a - b);
    const pairKey = `${sortedPillars[0]}_${sortedPillars[1]}`;

    if (!pairGroups[pairKey]) {
      pairGroups[pairKey] = {
        pillar_a: sortedPillars[0],
        pillar_b: sortedPillars[1],
        pillar_a_name: comp.pillar_a === sortedPillars[0] ? comp.pillar_a_name : comp.pillar_b_name,
        pillar_b_name: comp.pillar_a === sortedPillars[1] ? comp.pillar_a_name : comp.pillar_b_name,
        original: null,
        swapped: null
      };
    }

    // Determine if this is position_order 1 (original) or 2 (swapped)
    if (comp.position_order === 1) {
      pairGroups[pairKey].original = comp;
    } else if (comp.position_order === 2) {
      pairGroups[pairKey].swapped = comp;
    }
  }

  // Analyze consistency for pairs with both positions
  const pairs = [];
  let consistent = 0;
  let total = 0;

  for (const [key, group] of Object.entries(pairGroups)) {
    if (group.original && group.swapped) {
      total++;

      // Determine the "real" winner based on position
      // If original winner is A and original pillar_a matches sorted pillar_a, winner is sorted pillar_a
      // For swapped, positions are reversed
      const originalRealWinner = group.original.winner === 'A'
        ? group.original.pillar_a
        : group.original.pillar_b;

      const swappedRealWinner = group.swapped.winner === 'A'
        ? group.swapped.pillar_a
        : group.swapped.pillar_b;

      const isConsistent = originalRealWinner === swappedRealWinner;
      if (isConsistent) consistent++;

      pairs.push({
        pillar_a_name: group.pillar_a_name,
        pillar_b_name: group.pillar_b_name,
        originalWinner: group.original.winner,
        originalConfidence: group.original.confidence_score || 0,
        swappedWinner: group.swapped.winner,
        swappedConfidence: group.swapped.confidence_score || 0,
        isConsistent
      });
    }
  }

  return {
    pairs,
    consistent,
    total,
    consistencyRate: total > 0 ? consistent / total : 0
  };
});

// Verbosity Bias Computed Properties
const verbosityBiasColor = computed(() => {
  if (!verbosityAnalysis.value) return 'grey';
  const rate = verbosityAnalysis.value.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const verbosityBiasType = computed(() => {
  if (!verbosityAnalysis.value) return 'info';
  const rate = verbosityAnalysis.value.verbosity_bias_rate;
  if (rate > 0.6) return 'warning';
  if (rate < 0.4) return 'info';
  return 'success';
});

const lengthDiffFormatted = computed(() => {
  if (!verbosityAnalysis.value) return '-';
  const diff = verbosityAnalysis.value.avg_length_winner - verbosityAnalysis.value.avg_length_loser;
  const sign = diff > 0 ? '+' : '';
  return `${sign}${Math.round(diff).toLocaleString()}`;
});

const lengthDiffClass = computed(() => {
  if (!verbosityAnalysis.value) return '';
  const diff = verbosityAnalysis.value.avg_length_winner - verbosityAnalysis.value.avg_length_loser;
  if (diff > 500) return 'text-warning';
  if (diff < -500) return 'text-info';
  return 'text-success';
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

    // Load verbosity analysis
    try {
      const verbosityResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/verbosity-analysis`
      );
      verbosityAnalysis.value = verbosityResponse.data;
    } catch (verbosityError) {
      console.warn('Could not load verbosity analysis:', verbosityError);
    }

    // Load thread performance analysis
    try {
      const threadPerfResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/thread-performance`
      );
      threadPerformance.value = threadPerfResponse.data;
    } catch (threadPerfError) {
      console.warn('Could not load thread performance:', threadPerfError);
    }

    // Load detailed position-swap analysis
    try {
      const swapResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/position-swap-analysis`
      );
      positionSwapDetailed.value = swapResponse.data;
    } catch (swapError) {
      console.warn('Could not load position-swap analysis:', swapError);
    }
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

const formatCriterionName = (criterion) => {
  const names = {
    'counsellor_coherence': 'Berater-Kohärenz',
    'client_coherence': 'Klient-Kohärenz',
    'quality': 'Qualität',
    'empathy': 'Empathie',
    'authenticity': 'Authentizität',
    'solution_orientation': 'Lösungsorientierung'
  };
  return names[criterion] || criterion;
};

const getScoreColor = (score) => {
  if (score >= 4) return 'success';
  if (score >= 3) return 'info';
  if (score >= 2) return 'warning';
  return 'error';
};

// Thread Performance Helper Functions
const getLikertConsistencyColor = (score) => {
  if (score >= 0.7) return 'success';
  if (score >= 0.5) return 'warning';
  return 'error';
};

const getPillarName = (pillarId) => {
  return `Säule ${pillarId}`;
};

const formatLikertMetric = (metric) => {
  const names = {
    'counsellor_coherence': 'Berater-Kohärenz',
    'client_coherence': 'Klient-Kohärenz',
    'quality': 'Qualität',
    'empathy': 'Empathie',
    'authenticity': 'Authentizität',
    'solution_orientation': 'Lösungsorientierung'
  };
  return names[metric] || metric;
};

// Position Swap Analysis Helper Functions
const getConsistencyQualityColor = (quality) => {
  const colors = {
    'excellent': 'success',
    'good': 'info',
    'fair': 'warning',
    'poor': 'error'
  };
  return colors[quality] || 'grey';
};

const getBiasLabel = (bias) => {
  const labels = {
    'primacy': 'Primacy Bias',
    'recency': 'Recency Bias',
    'balanced': 'Ausbalanciert'
  };
  return labels[bias] || 'Unbekannt';
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

/* Expanded Row Styles */
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

.thread-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.thread-table :deep(.v-data-table__td) {
  padding: 8px 12px;
}

/* Source Footnote Links */
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

/* Reference Links in Methodology Section */
.reference-link {
  color: rgb(var(--v-theme-primary));
  text-decoration: none;
  transition: color 0.2s ease;
}

.reference-link:hover {
  text-decoration: underline;
  color: rgb(var(--v-theme-secondary));
}

/* Position-Swap Analysis Styles */
.swap-summary-card {
  text-align: center;
  padding: 16px;
}

.swap-summary-card .text-h5 {
  line-height: 1.2;
}

.likert-comparison-row {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 4px;
  margin: 4px 0;
  padding: 8px 12px;
}

.likert-comparison-row:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}
</style>
