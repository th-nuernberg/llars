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
          Zurueck zur Uebersicht
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
                  <div class="text-caption text-medium-emphasis">Saetze analysiert</div>
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
              <span>Analyse laeuft...</span>
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
                        <span class="text-caption">Saeule:</span>
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
                        <span class="text-caption">Saetze/Sek:</span>
                        <span class="font-weight-bold">{{ liveData.timing.sentences_per_second?.toFixed(1) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Vergangen:</span>
                        <span class="font-weight-bold">{{ formatDuration(liveData.timing.elapsed_seconds) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">Geschaetzt:</span>
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

      <!-- Results Tabs (only show when completed) -->
      <template v-if="analysis.status === 'completed'">
        <v-row>
          <v-col cols="12">
            <v-card>
              <v-tabs v-model="activeTab" color="primary">
                <v-tab value="overview">Uebersicht</v-tab>
                <v-tab value="distribution">Verteilung</v-tab>
                <v-tab value="transitions">Transitionen</v-tab>
                <v-tab value="comparison">Saeulen-Vergleich</v-tab>
                <v-tab value="sentences">Saetze</v-tab>
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
                            Saeule {{ pillarNum }}
                          </v-card-title>
                          <v-card-text>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Saetze:</span>
                              <span class="font-weight-bold">{{ stats.total_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Berater-Saetze:</span>
                              <span class="font-weight-bold text-primary">{{ stats.counselor_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">Klient-Saetze:</span>
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
                          label="Saeule"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionLevel"
                          :items="[{title: 'Level 2 (aggregiert)', value: 'level2'}, {title: 'Vollstaendig', value: 'full'}]"
                          label="Detailstufe"
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

                  <!-- Transitions Tab -->
                  <v-window-item value="transitions">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="transitionPillar"
                          :items="pillarOptions"
                          label="Saeule"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="transitionLevel"
                          :items="[{title: 'Level 2 (aggregiert)', value: 'level2'}, {title: 'Vollstaendig', value: 'full'}]"
                          label="Detailstufe"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                    </v-row>

                    <v-progress-linear v-if="loadingTransitions" indeterminate></v-progress-linear>

                    <!-- Top Transitions List -->
                    <div class="text-subtitle-1 font-weight-bold mb-2">
                      Top 20 Transitionen
                    </div>
                    <v-list density="compact">
                      <v-list-item
                        v-for="(link, idx) in topTransitions"
                        :key="idx"
                      >
                        <template v-slot:prepend>
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
                  </v-window-item>

                  <!-- Pillar Comparison Tab -->
                  <v-window-item value="comparison">
                    <v-progress-linear v-if="loadingComparison" indeterminate></v-progress-linear>

                    <v-row v-if="comparisonData.length > 0">
                      <v-col cols="12">
                        <v-data-table
                          :headers="comparisonHeaders"
                          :items="comparisonData"
                          density="compact"
                        >
                          <template v-slot:item.pillar_name="{ item }">
                            <div class="font-weight-bold">{{ item.pillar_name }}</div>
                          </template>
                          <template v-slot:item.counselor_ratio="{ item }">
                            <v-progress-linear
                              :model-value="item.metrics.counselor_ratio * 100"
                              height="20"
                              rounded
                              color="primary"
                            >
                              <template v-slot:default>
                                <strong>{{ (item.metrics.counselor_ratio * 100).toFixed(1) }}%</strong>
                              </template>
                            </v-progress-linear>
                          </template>
                          <template v-slot:item.impact_factor_ratio="{ item }">
                            {{ (item.metrics.impact_factor_ratio * 100).toFixed(1) }}%
                          </template>
                          <template v-slot:item.resource_activation_score="{ item }">
                            {{ (item.metrics.resource_activation_score * 100).toFixed(1) }}%
                          </template>
                          <template v-slot:item.mi_score="{ item }">
                            {{ item.metrics.mi_score?.toFixed(3) }}
                          </template>
                          <template v-slot:item.avg_confidence="{ item }">
                            {{ (item.metrics.avg_confidence * 100).toFixed(1) }}%
                          </template>
                        </v-data-table>
                      </v-col>
                    </v-row>
                  </v-window-item>

                  <!-- Sentences Tab -->
                  <v-window-item value="sentences">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="sentencePillar"
                          :items="pillarOptions"
                          label="Saeule"
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import { io } from 'socket.io-client';

const router = useRouter();
const route = useRoute();

// Socket.IO connection
let socket = null;

// State
const loading = ref(false);
const starting = ref(false);
const resuming = ref(false);
const analysis = ref(null);
const activeTab = ref('overview');

// Stuck detection
const lastUpdateTime = ref(Date.now());
const stuckThresholdSeconds = 30; // Consider stuck after 30s without updates

// Live data from Socket.IO
const liveData = ref({
  hardware: null,
  current_thread: null,
  current_message: null,
  timing: null
});

// Distribution State
const distributionPillar = ref(null);
const distributionLevel = ref('level2');
const distributionData = ref([]);
const loadingDistribution = ref(false);

// Transitions State
const transitionPillar = ref(null);
const transitionLevel = ref('level2');
const transitionsData = ref({ links: [] });
const loadingTransitions = ref(false);

// Comparison State
const comparisonData = ref([]);
const loadingComparison = ref(false);

// Sentences State
const sentencePillar = ref(null);
const sentenceRole = ref('');
const sentenceLabel = ref('');
const sentences = ref([]);
const sentencesTotal = ref(0);
const sentencesOffset = ref(0);
const loadingSentences = ref(false);

// Computed
const pillarOptions = computed(() => {
  if (!analysis.value?.pillar_statistics) return [];
  return [
    { title: 'Alle Saeulen', value: null },
    ...Object.keys(analysis.value.pillar_statistics).map(p => ({
      title: `Saeule ${p}`,
      value: parseInt(p)
    }))
  ];
});

const maxDistributionCount = computed(() => {
  if (distributionData.value.length === 0) return 1;
  return Math.max(...distributionData.value.map(d => d.count));
});

const topTransitions = computed(() => {
  return transitionsData.value.links?.slice(0, 20) || [];
});

// Stuck detection computed properties
const stuckDuration = computed(() => {
  return Math.round((Date.now() - lastUpdateTime.value) / 1000);
});

const isStuck = computed(() => {
  // Only check if analysis is running and we haven't received updates
  if (analysis.value?.status !== 'running') return false;
  const secondsSinceUpdate = (Date.now() - lastUpdateTime.value) / 1000;
  return secondsSinceUpdate > stuckThresholdSeconds && !liveData.value.timing;
});

// Headers
const distributionHeaders = [
  { title: 'Label', key: 'label', sortable: true },
  { title: 'Rolle', key: 'role', sortable: true },
  { title: 'Anzahl', key: 'count', sortable: true, width: '300px' }
];

const comparisonHeaders = [
  { title: 'Saeule', key: 'pillar_name', sortable: true },
  { title: 'Saetze', key: 'metrics.total_sentences', sortable: true },
  { title: 'Berater-Anteil', key: 'counselor_ratio', sortable: true, width: '200px' },
  { title: 'Impact Factor', key: 'impact_factor_ratio', sortable: true },
  { title: 'Ressourcen-Aktivierung', key: 'resource_activation_score', sortable: true },
  { title: 'MI Score', key: 'mi_score', sortable: true },
  { title: 'Konfidenz', key: 'avg_confidence', sortable: true }
];

const sentenceHeaders = [
  { title: 'Satz', key: 'sentence_text', sortable: false, width: '40%' },
  { title: 'Rolle', key: 'role', sortable: true },
  { title: 'Label', key: 'label', sortable: true },
  { title: 'Konfidenz', key: 'confidence', sortable: true, width: '150px' },
  { title: 'Saeule', key: 'pillar_number', sortable: true }
];

// Load Analysis
const loadAnalysis = async () => {
  loading.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}`
    );
    analysis.value = response.data;

    if (analysis.value.status === 'completed') {
      await loadDistribution();
      await loadTransitions();
      await loadComparison();
    }
  } catch (error) {
    console.error('Error loading analysis:', error);
  } finally {
    loading.value = false;
  }
};

// Start Analysis
const startAnalysis = async () => {
  starting.value = true;
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/start`,
      {},
      { headers: { 'Content-Type': 'application/json' } }
    );
    // Reset stuck detection
    lastUpdateTime.value = Date.now();
    // Reload to get updated status
    await loadAnalysis();
  } catch (error) {
    console.error('Error starting analysis:', error);
  } finally {
    starting.value = false;
  }
};

// Resume stuck Analysis
const resumeAnalysis = async () => {
  resuming.value = true;
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/start`,
      { force: true }
    );
    console.log('[OnCoCo] Analysis resumed:', response.data);
    // Reset stuck detection
    lastUpdateTime.value = Date.now();
    // Reload to get updated status
    await loadAnalysis();
  } catch (error) {
    console.error('Error resuming analysis:', error);
  } finally {
    resuming.value = false;
  }
};

// Load Distribution
const loadDistribution = async () => {
  loadingDistribution.value = true;
  try {
    const params = new URLSearchParams();
    if (distributionPillar.value) params.append('pillar', distributionPillar.value);
    params.append('level', distributionLevel.value);

    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/distribution?${params}`
    );
    distributionData.value = response.data.distribution || [];
  } catch (error) {
    console.error('Error loading distribution:', error);
  } finally {
    loadingDistribution.value = false;
  }
};

// Load Transitions
const loadTransitions = async () => {
  loadingTransitions.value = true;
  try {
    const params = new URLSearchParams();
    if (transitionPillar.value) params.append('pillar', transitionPillar.value);
    params.append('level', transitionLevel.value);
    params.append('format', 'list');

    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/transition-matrix?${params}`
    );
    transitionsData.value = response.data;
  } catch (error) {
    console.error('Error loading transitions:', error);
  } finally {
    loadingTransitions.value = false;
  }
};

// Load Comparison
const loadComparison = async () => {
  loadingComparison.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/comparison`
    );
    comparisonData.value = response.data.pillars || [];
  } catch (error) {
    console.error('Error loading comparison:', error);
  } finally {
    loadingComparison.value = false;
  }
};

// Load Sentences
const loadSentences = async (reset = true) => {
  loadingSentences.value = true;
  if (reset) {
    sentences.value = [];
    sentencesOffset.value = 0;
  }

  try {
    const params = new URLSearchParams();
    if (sentencePillar.value) params.append('pillar', sentencePillar.value);
    if (sentenceRole.value) params.append('role', sentenceRole.value);
    if (sentenceLabel.value) params.append('label', sentenceLabel.value);
    params.append('limit', '50');
    params.append('offset', sentencesOffset.value);

    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${route.params.id}/sentences?${params}`
    );

    if (reset) {
      sentences.value = response.data.sentences || [];
    } else {
      sentences.value = [...sentences.value, ...(response.data.sentences || [])];
    }
    sentencesTotal.value = response.data.total || 0;
    sentencesOffset.value += response.data.sentences?.length || 0;
  } catch (error) {
    console.error('Error loading sentences:', error);
  } finally {
    loadingSentences.value = false;
  }
};

const loadMoreSentences = () => {
  loadSentences(false);
};

// Watchers
watch([distributionPillar, distributionLevel], () => {
  if (analysis.value?.status === 'completed') {
    loadDistribution();
  }
});

watch([transitionPillar, transitionLevel], () => {
  if (analysis.value?.status === 'completed') {
    loadTransitions();
  }
});

// Utility Functions
const getStatusColor = (status) => {
  const colors = {
    pending: 'grey',
    running: 'info',
    completed: 'success',
    failed: 'error'
  };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = {
    pending: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  };
  return icons[status] || 'mdi-help-circle';
};

const getStatusText = (status) => {
  const texts = {
    pending: 'Ausstehend',
    running: 'Laeuft',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen'
  };
  return texts[status] || status;
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

const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '0s';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
};

// Socket.IO Setup
const setupSocket = () => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL;
  socket = io(baseUrl, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
  });

  socket.on('connect', () => {
    console.log('[OnCoCo Socket] Connected');
    // Join analysis room
    socket.emit('oncoco:join_analysis', { analysis_id: parseInt(route.params.id) });
  });

  socket.on('oncoco:joined', (data) => {
    console.log('[OnCoCo Socket] Joined room:', data);
  });

  socket.on('oncoco:progress', (data) => {
    console.log('[OnCoCo Socket] Progress update:', data);
    if (analysis.value && data.analysis_id === parseInt(route.params.id)) {
      // Update basic progress
      analysis.value.processed_threads = data.processed_threads;
      analysis.value.total_threads = data.total_threads;
      analysis.value.total_sentences = data.total_sentences;
      analysis.value.progress = data.progress;

      // Update live data for detailed display
      liveData.value = {
        hardware: data.hardware,
        current_thread: data.current_thread,
        current_message: data.current_message,
        timing: data.timing
      };

      // Update last update time for stuck detection
      lastUpdateTime.value = Date.now();
    }
  });

  socket.on('oncoco:complete', async (data) => {
    console.log('[OnCoCo Socket] Analysis complete:', data);
    if (data.analysis_id === parseInt(route.params.id)) {
      // Clear live data
      liveData.value = {
        hardware: null,
        current_thread: null,
        current_message: null,
        timing: null
      };
      // Reload full analysis data to get results
      await loadAnalysis();
    }
  });

  socket.on('oncoco:error', (data) => {
    console.error('[OnCoCo Socket] Error:', data);
  });

  socket.on('disconnect', () => {
    console.log('[OnCoCo Socket] Disconnected');
  });
};

const cleanupSocket = () => {
  if (socket) {
    socket.emit('oncoco:leave_analysis', { analysis_id: parseInt(route.params.id) });
    socket.disconnect();
    socket = null;
  }
};

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
  max-width: 1400px;
  margin: 0 auto;
}

.sentence-text {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
