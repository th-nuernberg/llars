<template>
  <v-container class="oncoco-results">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-btn
          variant="text"
          prepend-icon="mdi-arrow-left"
          @click="router.push({ name: 'OnCoCoOverview' })"
        >
          Zurück zur Übersicht
        </v-btn>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <template v-if="analysis">
      <!-- Analysis Info Header -->
      <v-row class="mb-4">
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
              {{ analysis.name }}
              <v-spacer></v-spacer>
              <v-chip
                :color="getStatusColor(analysis.status)"
                :prepend-icon="getStatusIcon(analysis.status)"
              >
                {{ getStatusText(analysis.status) }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">Fortschritt</div>
                  <v-progress-linear
                    :model-value="analysis.progress || 0"
                    height="24"
                    rounded
                    :color="analysis.status === 'completed' ? 'success' : 'primary'"
                    class="mt-1"
                  >
                    <template v-slot:default="{ value }">
                      <strong>{{ Math.round(value) }}%</strong>
                    </template>
                  </v-progress-linear>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">Threads</div>
                  <div class="text-h6">{{ analysis.processed_threads }} / {{ analysis.total_threads }}</div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">Sätze analysiert</div>
                  <div class="text-h6">{{ analysis.total_sentences?.toLocaleString() || 0 }}</div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">Erstellt</div>
                  <div class="text-body-1">{{ formatDate(analysis.created_at) }}</div>
                </v-col>
              </v-row>

              <!-- Start Button if pending -->
              <v-btn
                v-if="analysis.status === 'pending'"
                color="primary"
                variant="flat"
                prepend-icon="mdi-play"
                @click="startAnalysis"
                :loading="starting"
                class="mt-4"
              >
                Analyse starten
              </v-btn>

              <!-- Resume Button if stuck in running status (no Socket.IO updates) -->
              <div v-if="analysis.status === 'running' && isStuck" class="mt-4">
                <v-alert type="warning" density="compact" class="mb-3">
                  Die Analyse scheint festgefahren zu sein (keine Updates seit {{ stuckDuration }}s).
                  Dies kann nach einem Server-Neustart passieren.
                </v-alert>
                <v-btn
                  color="warning"
                  variant="flat"
                  prepend-icon="mdi-refresh"
                  @click="resumeAnalysis"
                  :loading="resuming"
                >
                  Analyse fortsetzen
                </v-btn>
              </div>

              <!-- Retry Button if failed -->
              <div v-if="analysis.status === 'failed'" class="mt-4">
                <v-alert type="error" density="compact" class="mb-3">
                  {{ analysis.error_message || 'Analyse fehlgeschlagen' }}
                </v-alert>
                <v-btn
                  color="warning"
                  variant="flat"
                  prepend-icon="mdi-refresh"
                  @click="startAnalysis"
                  :loading="starting"
                >
                  Erneut versuchen
                </v-btn>
              </div>

            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Live Status Panel (only show when running) -->
      <v-row v-if="analysis.status === 'running'" class="mb-4">
        <v-col cols="12">
          <v-card color="primary" variant="tonal">
            <v-card-title class="d-flex align-center">
              <v-progress-circular indeterminate size="24" class="mr-3"></v-progress-circular>
              <span>Analyse läuft...</span>
              <v-spacer></v-spacer>
              <v-chip color="success" size="small" v-if="liveData.timing">
                {{ formatDuration(liveData.timing.elapsed_seconds) }} vergangen
              </v-chip>
            </v-card-title>

            <v-card-text>
              <v-row>
                <!-- Hardware Info -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <v-icon class="mr-2">mdi-chip</v-icon>
                      Hardware
                    </v-card-title>
                    <v-card-text v-if="liveData.hardware">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Device:</span>
                        <span class="font-weight-bold">{{ liveData.hardware.device_type }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Device Name:</span>
                        <span class="font-weight-bold text-truncate" style="max-width: 150px;">{{ liveData.hardware.device_name }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">CPU Cores:</span>
                        <span class="font-weight-bold">{{ liveData.hardware.cpu_count }} / {{ liveData.hardware.cpu_count_logical }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">CPU Usage:</span>
                        <v-progress-linear
                          :model-value="liveData.hardware.cpu_percent"
                          height="16"
                          rounded
                          color="primary"
                          style="max-width: 100px;"
                        >
                          <small>{{ liveData.hardware.cpu_percent }}%</small>
                        </v-progress-linear>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Memory:</span>
                        <span class="font-weight-bold">{{ liveData.hardware.memory_used_gb }} / {{ liveData.hardware.memory_total_gb }} GB</span>
                      </div>
                      <div class="d-flex justify-space-between" v-if="liveData.hardware.model_size_mb">
                        <span class="text-caption">Model Size:</span>
                        <span class="font-weight-bold">{{ liveData.hardware.model_size_mb }} MB</span>
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      Warte auf Daten...
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Current Processing -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <v-icon class="mr-2">mdi-file-document-outline</v-icon>
                      Aktueller Thread
                    </v-card-title>
                    <v-card-text v-if="liveData.current_thread">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Säule:</span>
                        <v-chip size="x-small" color="primary">{{ liveData.current_thread.pillar_name }}</v-chip>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Thread ID:</span>
                        <span class="font-weight-bold">{{ liveData.current_thread.thread_id }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Nachrichten:</span>
                        <span class="font-weight-bold">{{ liveData.current_thread.message_count }}</span>
                      </div>
                      <v-divider class="my-2"></v-divider>
                      <div v-if="liveData.current_message">
                        <div class="d-flex justify-space-between mb-2">
                          <span class="text-caption">Nachricht:</span>
                          <span class="font-weight-bold">{{ liveData.current_message.message_index }} / {{ liveData.current_message.total_messages }}</span>
                        </div>
                        <div class="d-flex justify-space-between mb-2">
                          <span class="text-caption">Sender:</span>
                          <span class="font-weight-bold text-truncate" style="max-width: 120px;">{{ liveData.current_message.sender }}</span>
                        </div>
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      Warte auf Daten...
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Performance -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <v-icon class="mr-2">mdi-speedometer</v-icon>
                      Performance
                    </v-card-title>
                    <v-card-text v-if="liveData.timing">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Threads/Sek:</span>
                        <span class="font-weight-bold">{{ liveData.timing.threads_per_second?.toFixed(3) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Sätze/Sek:</span>
                        <span class="font-weight-bold">{{ liveData.timing.sentences_per_second?.toFixed(1) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Vergangen:</span>
                        <span class="font-weight-bold">{{ formatDuration(liveData.timing.elapsed_seconds) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Geschätzt:</span>
                        <span class="font-weight-bold text-warning">{{ formatDuration(liveData.timing.eta_seconds) }}</span>
                      </div>
                      <v-divider class="my-2"></v-divider>
                      <div class="text-caption text-medium-emphasis">
                        Worker: 1 (Single-Threaded)
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      Warte auf Daten...
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Last Classified Sentence -->
              <v-row class="mt-3" v-if="liveData.timing?.last_sentence">
                <v-col cols="12">
                  <v-card variant="outlined">
                    <v-card-title class="text-subtitle-1 py-2">
                      <v-icon class="mr-2">mdi-message-text</v-icon>
                      Zuletzt klassifiziert
                    </v-card-title>
                    <v-card-text class="py-2">
                      <div class="d-flex align-center">
                        <v-chip
                          :color="liveData.timing.last_sentence.role === 'counselor' ? 'primary' : 'secondary'"
                          size="small"
                          class="mr-3"
                        >
                          {{ liveData.timing.last_sentence.role === 'counselor' ? 'Berater' : 'Klient' }}
                        </v-chip>
                        <span class="text-body-2 mr-3" style="flex: 1;">
                          "{{ liveData.timing.last_sentence.text }}"
                        </span>
                        <v-chip color="info" size="small" class="mr-2">
                          {{ liveData.timing.last_sentence.label_display }}
                        </v-chip>
                        <v-chip
                          :color="liveData.timing.last_sentence.confidence > 80 ? 'success' : liveData.timing.last_sentence.confidence > 50 ? 'warning' : 'error'"
                          size="small"
                        >
                          {{ liveData.timing.last_sentence.confidence }}%
                        </v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Info when not completed -->
      <v-row v-if="analysis.status === 'pending'">
        <v-col cols="12">
          <v-alert type="info" prominent>
            <v-alert-title>Analyse noch nicht gestartet</v-alert-title>
            Starten Sie die Analyse mit dem Button oben, um Ergebnisse zu generieren.
          </v-alert>
        </v-col>
      </v-row>

      <v-row v-if="analysis.status === 'failed'">
        <v-col cols="12">
          <v-alert type="error" prominent>
            <v-alert-title>Analyse fehlgeschlagen</v-alert-title>
            {{ analysis.error_message || 'Ein unbekannter Fehler ist aufgetreten. Bitte versuchen Sie es erneut.' }}
          </v-alert>
        </v-col>
      </v-row>

      <!-- Results Tabs (only show when completed) -->
      <template v-if="analysis.status === 'completed'">
        <v-row>
          <v-col cols="12">
            <v-card>
              <v-tabs v-model="activeTab" color="primary">
                <v-tab value="overview">Übersicht</v-tab>
                <v-tab value="distribution">Verteilung</v-tab>
                <v-tab value="transitions">Transitionen & Vergleich</v-tab>
                <v-tab value="sentences">Sätze</v-tab>
              </v-tabs>

              <v-card-text>
                <v-window v-model="activeTab">
                  <!-- Overview Tab -->
                  <v-window-item value="overview">
                    <v-row>
                      <v-col
                        v-for="(stats, pillarNum) in analysis.pillar_statistics"
                        :key="pillarNum"
                        cols="12"
                        md="4"
                      >
                        <v-card variant="outlined">
                          <v-card-title class="text-subtitle-1">
                            Säule {{ pillarNum }}
                          </v-card-title>
                          <v-card-text>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Sätze:</span>
                              <span class="font-weight-bold">{{ stats.total_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Berater-Sätze:</span>
                              <span class="font-weight-bold text-primary">{{ stats.counselor_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Klient-Sätze:</span>
                              <span class="font-weight-bold text-secondary">{{ stats.client_sentences?.toLocaleString() }}</span>
                            </div>
                            <v-divider class="my-2"></v-divider>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Impact Factor Ratio:</span>
                              <span class="font-weight-bold">{{ (stats.impact_factor_ratio * 100).toFixed(1) }}%</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Ressourcen-Aktivierung:</span>
                              <span class="font-weight-bold">{{ (stats.resource_activation_score * 100).toFixed(1) }}%</span>
                            </div>
                            <div class="d-flex justify-space-between">
                              <span class="text-caption">Mutual Information:</span>
                              <span class="font-weight-bold">{{ stats.mi_score?.toFixed(3) }}</span>
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-window-item>

                  <!-- Distribution Tab -->
                  <v-window-item value="distribution">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionPillar"
                          :items="pillarOptions"
                          label="Säule"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionLevel"
                          :items="[{title: 'Level 2 (aggregiert)', value: 'level2'}, {title: 'Vollständig', value: 'full'}]"
                          label="Detailstufe"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionRole"
                          :items="roleFilterOptions"
                          label="Rolle"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                    </v-row>

                    <v-progress-linear v-if="loadingDistribution" indeterminate></v-progress-linear>

                    <!-- Distribution Table -->
                    <v-data-table
                      :headers="distributionHeaders"
                      :items="distributionData"
                      :loading="loadingDistribution"
                      :items-per-page="20"
                      density="compact"
                    >
                      <template v-slot:item.label="{ item }">
                        <div>
                          <span class="font-weight-medium">{{ item.display_name }}</span>
                          <div class="text-caption text-medium-emphasis">{{ item.label }}</div>
                        </div>
                      </template>
                      <template v-slot:item.role="{ item }">
                        <v-chip
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                          size="x-small"
                        >
                          {{ item.role === 'counselor' ? 'Berater' : 'Klient' }}
                        </v-chip>
                      </template>
                      <template v-slot:item.count="{ item }">
                        <v-progress-linear
                          :model-value="(item.count / maxDistributionCount) * 100"
                          height="20"
                          rounded
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                        >
                          <template v-slot:default>
                            <strong>{{ item.count.toLocaleString() }}</strong>
                          </template>
                        </v-progress-linear>
                      </template>
                    </v-data-table>
                  </v-window-item>

                  <!-- Transitions & Comparison Tab -->
                  <v-window-item value="transitions">
                    <!-- Controls -->
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionPillar"
                          :items="pillarOptions"
                          label="Säule"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionLevel"
                          :items="[{title: 'Level 2 (aggregiert)', value: 'level2'}, {title: 'Vollständig', value: 'full'}]"
                          label="Detailstufe"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionRole"
                          :items="roleFilterOptions"
                          label="Rolle"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="heatmapColorMode"
                          :items="[{title: 'Anzahl', value: 'count'}, {title: 'Wahrscheinlichkeit', value: 'probability'}]"
                          label="Heatmap Farbmodus"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2" class="d-flex align-center">
                        <v-switch
                          v-model="showHeatmapValues"
                          label="Werte anzeigen"
                          density="compact"
                          hide-details
                          color="primary"
                        ></v-switch>
                      </v-col>
                    </v-row>

                    <v-progress-linear v-if="loadingTransitions || loadingHeatmaps || loadingMatrixComparison" indeterminate></v-progress-linear>

                    <!-- Quick Stats Bar -->
                    <QuickStatsBar
                      v-if="matrixComparisonData"
                      :similarity="quickStatsSimilarity"
                      :frobenius-distance="quickStatsFrobenius"
                      :p-value="quickStatsPValue"
                      :chi-square-significant="quickStatsChiSignificant"
                      :chi-square-total="quickStatsChiTotal"
                      :loading="loadingMatrixComparison"
                      @show-methodology="showMethodologyDialog = true"
                    />

                    <!-- Transition Heatmaps per Pillar -->
                    <div class="text-h6 font-weight-bold mb-3">
                      <v-icon start>mdi-grid</v-icon>
                      Transitions-Heatmaps pro Säule
                    </div>

                    <v-row v-if="Object.keys(heatmapData).length > 0" class="heatmap-row">
                      <v-col
                        v-for="(data, pillarNum) in heatmapData"
                        :key="'heatmap-' + pillarNum"
                        cols="12"
                        lg="4"
                        md="6"
                        class="heatmap-col"
                      >
                        <v-card variant="outlined" class="h-100 heatmap-card">
                          <v-card-title class="text-subtitle-1 py-2">
                            <v-icon start size="small" color="primary">mdi-chart-box</v-icon>
                            {{ getPillarName(pillarNum) }}
                            <v-chip size="x-small" class="ml-2" variant="tonal">
                              {{ data.totalTransitions }} Transitionen
                            </v-chip>
                          </v-card-title>
                          <v-card-text class="pt-0 heatmap-content">
                            <TransitionHeatmap
                              :counts="data.counts"
                              :probabilities="data.probabilities"
                              :labels="data.labels"
                              :label-displays="data.labelDisplays"
                              :show-values="showHeatmapValues"
                              :color-mode="heatmapColorMode"
                              :pillar-name="getPillarName(pillarNum)"
                              :pillar-number="pillarNum"
                              :external-highlight="hoveredTransition"
                              @cell-hover="onHeatmapCellHover"
                              @cell-leave="onHeatmapCellLeave"
                            />
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>

                    <!-- Synchronized Comparison Panel -->
                    <v-expand-transition>
                      <v-card v-if="hoveredTransition" variant="tonal" color="primary" class="mt-3">
                        <v-card-title class="text-subtitle-1 py-2">
                          <v-icon start size="small">mdi-compare</v-icon>
                          Vergleich: {{ hoveredTransition.fromDisplay }}
                          <v-icon size="x-small" class="mx-1">mdi-arrow-right</v-icon>
                          {{ hoveredTransition.toDisplay }}
                        </v-card-title>
                        <v-card-text class="py-2">
                          <v-row dense>
                            <v-col
                              v-for="(data, pillarNum) in heatmapData"
                              :key="'compare-' + pillarNum"
                              cols="12"
                              :sm="12 / Object.keys(heatmapData).length"
                            >
                              <div class="text-center">
                                <div class="text-caption text-medium-emphasis">{{ getPillarName(pillarNum) }}</div>
                                <div class="text-h5 font-weight-bold">
                                  {{ getTransitionCount(pillarNum, hoveredTransition.from, hoveredTransition.to) }}
                                </div>
                                <div class="text-caption">
                                  {{ (getTransitionProbability(pillarNum, hoveredTransition.from, hoveredTransition.to) * 100).toFixed(1) }}%
                                </div>
                              </div>
                            </v-col>
                          </v-row>
                        </v-card-text>
                      </v-card>
                    </v-expand-transition>

                    <v-alert v-if="!loadingHeatmaps && Object.keys(heatmapData).length === 0" type="info" variant="tonal" class="mb-4">
                      Keine Heatmap-Daten verfügbar. Bitte warten Sie bis die Analyse abgeschlossen ist.
                    </v-alert>

                    <v-divider class="my-4"></v-divider>

                    <!-- Pillar Comparison Panel (NEW - replaces old Statistics tab) -->
                    <PillarComparisonPanel
                      v-if="matrixComparisonData?.pairwise_comparisons?.length > 0"
                      :comparisons="matrixComparisonData.pairwise_comparisons"
                      :loading="loadingMatrixComparison"
                      @highlight-transition="onHighlightTransition"
                    />

                    <v-divider class="my-4"></v-divider>

                    <!-- Top Transitions List (Collapsible) -->
                    <v-expansion-panels variant="accordion">
                      <v-expansion-panel>
                        <v-expansion-panel-title>
                          <v-icon start>mdi-format-list-numbered</v-icon>
                          Top 20 Transitionen
                          <span v-if="transitionPillar" class="text-caption ml-2">(Säule {{ transitionPillar }})</span>
                          <span v-else class="text-caption ml-2">(Alle Säulen)</span>
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <v-list density="compact" v-if="topTransitions.length > 0">
                            <v-list-item
                              v-for="(link, idx) in topTransitions"
                              :key="idx"
                            >
                              <template v-slot:prepend>
                                <span class="text-caption text-medium-emphasis mr-3" style="width: 20px;">{{ idx + 1 }}.</span>
                                <v-chip
                                  size="small"
                                  :color="link.source.startsWith('CO-') ? 'primary' : 'secondary'"
                                  class="mr-2"
                                >
                                  {{ link.source_display }}
                                </v-chip>
                              </template>
                              <v-list-item-title class="d-flex align-center">
                                <v-icon size="small" class="mx-2">mdi-arrow-right</v-icon>
                                <v-chip
                                  size="small"
                                  :color="link.target.startsWith('CO-') ? 'primary' : 'secondary'"
                                >
                                  {{ link.target_display }}
                                </v-chip>
                              </v-list-item-title>
                              <template v-slot:append>
                                <div class="text-right">
                                  <div class="font-weight-bold">{{ link.value }}</div>
                                  <div class="text-caption">{{ (link.probability * 100).toFixed(1) }}%</div>
                                </div>
                              </template>
                            </v-list-item>
                          </v-list>
                          <v-alert v-else-if="!loadingTransitions" type="info" variant="tonal">
                            Keine Transitions-Daten verfügbar.
                          </v-alert>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-window-item>

                  <!-- Methodology Dialog -->
                  <v-dialog v-model="showMethodologyDialog" max-width="900" scrollable>
                    <v-card class="methodology-dialog-card" rounded="lg">
                      <!-- Dialog Header with Close Button -->
                      <v-toolbar color="primary" density="compact">
                        <v-icon class="ml-2">mdi-chart-scatter-plot</v-icon>
                        <v-toolbar-title class="text-body-1 font-weight-medium">
                          Statistische Matrix-Vergleichsmetriken
                        </v-toolbar-title>
                        <v-spacer></v-spacer>
                        <v-btn
                          icon="mdi-close"
                          variant="text"
                          @click="showMethodologyDialog = false"
                        ></v-btn>
                      </v-toolbar>

                      <!-- Content with padding -->
                      <v-card-text class="pa-6">
                        <MatrixComparisonMetrics :analysis-id="route.params.id" hide-header />
                      </v-card-text>
                    </v-card>
                  </v-dialog>

                  <!-- Sentences Tab -->
                  <v-window-item value="sentences">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="sentencePillar"
                          :items="pillarOptions"
                          label="Säule"
                          variant="outlined"
                          density="compact"
                          clearable
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="sentenceRole"
                          :items="[{title: 'Alle', value: ''}, {title: 'Berater', value: 'counselor'}, {title: 'Klient', value: 'client'}]"
                          label="Rolle"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-text-field
                          v-model="sentenceLabel"
                          label="Label Filter"
                          placeholder="z.B. CO-IF-AC"
                          variant="outlined"
                          density="compact"
                          clearable
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-btn
                          color="primary"
                          variant="flat"
                          @click="loadSentences"
                          :loading="loadingSentences"
                          block
                        >
                          Laden
                        </v-btn>
                      </v-col>
                    </v-row>

                    <v-data-table
                      :headers="sentenceHeaders"
                      :items="sentences"
                      :loading="loadingSentences"
                      :items-per-page="20"
                      density="compact"
                    >
                      <template v-slot:item.sentence_text="{ item }">
                        <div class="sentence-text">{{ item.sentence_text }}</div>
                      </template>
                      <template v-slot:item.role="{ item }">
                        <v-chip
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                          size="x-small"
                        >
                          {{ item.role === 'counselor' ? 'Berater' : 'Klient' }}
                        </v-chip>
                      </template>
                      <template v-slot:item.label="{ item }">
                        <div>
                          <div class="font-weight-medium">{{ item.label_display }}</div>
                          <div class="text-caption text-medium-emphasis">{{ item.label }}</div>
                        </div>
                      </template>
                      <template v-slot:item.confidence="{ item }">
                        <v-progress-linear
                          :model-value="item.confidence * 100"
                          height="16"
                          rounded
                          :color="item.confidence > 0.8 ? 'success' : item.confidence > 0.5 ? 'warning' : 'error'"
                        >
                          <template v-slot:default>
                            <small>{{ (item.confidence * 100).toFixed(0) }}%</small>
                          </template>
                        </v-progress-linear>
                      </template>
                    </v-data-table>

                    <div class="text-center mt-4" v-if="sentencesTotal > sentences.length">
                      <v-btn
                        variant="outlined"
                        @click="loadMoreSentences"
                        :loading="loadingSentences"
                      >
                        Mehr laden ({{ sentences.length }} / {{ sentencesTotal }})
                      </v-btn>
                    </div>
                  </v-window-item>
                </v-window>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </template>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import TransitionHeatmap from './TransitionHeatmap.vue';
import MatrixComparisonMetrics from './MatrixComparisonMetrics.vue';
import QuickStatsBar from './QuickStatsBar.vue';
import PillarComparisonPanel from './PillarComparisonPanel.vue';
import {
  useOnCoCoAnalysis,
  useOnCoCoSocket,
  useOnCoCoHelpers
} from './OnCoCoResults/composables';

const router = useRouter();
const route = useRoute();

// Local UI State
const activeTab = ref('overview');
const showMethodologyDialog = ref(false);

// Initialize composables
const analysisId = route.params.id;

const {
  // State
  analysis,
  loading,
  starting,
  resuming,
  liveData,
  // Stuck detection
  stuckDuration,
  isStuck,
  // Distribution
  distributionPillar,
  distributionLevel,
  distributionRole,
  distributionData,
  loadingDistribution,
  maxDistributionCount,
  // Transitions
  transitionPillar,
  transitionLevel,
  transitionRole,
  loadingTransitions,
  topTransitions,
  // Heatmaps
  heatmapData,
  loadingHeatmaps,
  showHeatmapValues,
  heatmapColorMode,
  hoveredTransition,
  // Matrix Comparison
  matrixComparisonData,
  loadingMatrixComparison,
  quickStatsSimilarity,
  quickStatsFrobenius,
  quickStatsPValue,
  quickStatsChiSignificant,
  quickStatsChiTotal,
  // Sentences
  sentencePillar,
  sentenceRole,
  sentenceLabel,
  sentences,
  sentencesTotal,
  loadingSentences,
  // Computed
  pillarOptions,
  roleFilterOptions,
  // Functions
  loadAnalysis,
  startAnalysis,
  resumeAnalysis,
  loadDistribution,
  loadTransitions,
  loadHeatmaps,
  loadMatrixComparison,
  loadSentences,
  loadMoreSentences,
  updateLiveData,
  clearLiveData,
  getTransitionCount,
  getTransitionProbability
} = useOnCoCoAnalysis(analysisId);

const {
  getStatusColor,
  getStatusIcon,
  getStatusText,
  getPillarName,
  formatDate,
  formatDuration,
  distributionHeaders,
  comparisonHeaders,
  sentenceHeaders
} = useOnCoCoHelpers();

// Socket.IO setup with callbacks
const analysisIdRef = ref(analysisId);
const { setupSocket, cleanupSocket } = useOnCoCoSocket(analysisIdRef, {
  onProgress: (data) => {
    updateLiveData(data);
  },
  onComplete: async (data) => {
    clearLiveData();
    await loadAnalysis();
  },
  onError: (data) => {
    console.error('[OnCoCo] Socket error:', data);
  }
});

// Heatmap Cell Hover Handlers
const onHeatmapCellHover = (data) => {
  const fromDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.from] || data.from;
  const toDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.to] || data.to;
  hoveredTransition.value = {
    from: data.from,
    to: data.to,
    fromDisplay,
    toDisplay,
    pillar: data.pillar
  };
};

const onHeatmapCellLeave = () => {
  hoveredTransition.value = null;
};

// Handle highlight from PillarComparisonPanel
const onHighlightTransition = (transition) => {
  if (transition) {
    hoveredTransition.value = {
      from: transition.from_label,
      to: transition.to_label,
      fromDisplay: transition.from_display || transition.from_label,
      toDisplay: transition.to_display || transition.to_label,
      pillar: null
    };
  } else {
    hoveredTransition.value = null;
  }
};

// Watchers for filter changes
watch([distributionPillar, distributionLevel, distributionRole], () => {
  if (analysis.value?.status === 'completed') {
    loadDistribution();
  }
});

watch([transitionPillar, transitionLevel, transitionRole], () => {
  if (analysis.value?.status === 'completed') {
    loadTransitions();
    loadHeatmaps();
    loadMatrixComparison();
  }
});

// Lifecycle
onMounted(() => {
  loadAnalysis();
  setupSocket();
});

onUnmounted(() => {
  cleanupSocket();
});
</script>

<style scoped>
.oncoco-results {
  max-width: 1600px;
  margin: 0 auto;
}

.sentence-text {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Heatmap Layout Fixes */
.heatmap-row {
  flex-wrap: wrap;
}

.heatmap-col {
  min-width: 0; /* Allow flex shrinking */
}

.heatmap-card {
  overflow: hidden;
}

.heatmap-content {
  overflow-x: auto;
  overflow-y: visible;
  padding-bottom: 12px;
}

/* Ensure cards don't overlap */
.heatmap-card :deep(.v-card-text) {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Better spacing for tabs on mobile */
@media (max-width: 960px) {
  .heatmap-col {
    margin-bottom: 16px;
  }
}

/* Methodology Dialog Styles */
.methodology-dialog-card {
  background-color: rgb(var(--v-theme-surface)) !important;
  overflow: hidden;
}

.methodology-dialog-card .v-toolbar {
  flex-shrink: 0;
}

.methodology-dialog-card .v-card-text {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
