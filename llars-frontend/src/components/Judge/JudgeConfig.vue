<template>
  <div class="judge-config-page">
    <!-- Page Header -->
    <div class="page-header">
      <v-btn
        icon="mdi-arrow-left"
        variant="text"
        size="small"
        @click="$router.push({ name: 'JudgeOverview' })"
      ></v-btn>
      <div class="header-content">
        <h1 class="text-h5 font-weight-bold">Neue Judge Session</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Konfigurieren Sie die automatisierte Bewertung
        </p>
      </div>
    </div>

    <!-- Main Content with Resizable Panels -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Configuration Form -->
      <div class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2" size="small">mdi-cog</v-icon>
          <span class="font-weight-medium">Konfiguration</span>
        </div>
        <div class="panel-content">
          <v-form ref="form" v-model="valid">
            <!-- Session Name -->
            <div class="config-section">
              <v-text-field
                v-model="config.sessionName"
                label="Session Name"
                hint="Geben Sie einen beschreibenden Namen für diese Session ein"
                :rules="[v => !!v || 'Session Name ist erforderlich']"
                prepend-icon="mdi-label"
                variant="outlined"
                density="compact"
              ></v-text-field>
            </div>

            <!-- Pillar Selection -->
            <div class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-pillar</v-icon>
                Säulen auswählen
              </div>
              <v-chip-group
                v-model="config.selectedPillars"
                multiple
                column
              >
                <v-chip
                  v-for="pillar in availablePillars"
                  :key="pillar.id"
                  :value="pillar.id"
                  :disabled="!pillar.enabled"
                  filter
                  variant="outlined"
                  color="primary"
                  size="small"
                >
                  <v-icon start size="small">{{ pillar.icon }}</v-icon>
                  {{ pillar.name }}
                  <span v-if="pillar.threadCount" class="ml-1 text-caption">
                    ({{ pillar.threadCount }})
                  </span>
                </v-chip>
              </v-chip-group>
              <div v-if="config.selectedPillars.length === 0" class="text-error text-caption mt-1">
                Bitte wählen Sie mindestens {{ minPillarsRequired }} Säule(n) aus
              </div>
              <div v-else class="text-medium-emphasis text-caption mt-1">
                {{ config.selectedPillars.length }} Säule(n) ausgewählt
                <span v-if="selectedThreadCount > 0">
                  ({{ selectedThreadCount }} Threads)
                </span>
              </div>
            </div>

            <!-- Comparison Mode -->
            <div class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-compare</v-icon>
                Vergleichs-Modus
              </div>
              <v-radio-group v-model="config.comparisonMode" class="comparison-mode-group" hide-details>
                <!-- Pillar Sample -->
                <v-radio value="pillar_sample">
                  <template v-slot:label>
                    <div class="radio-label">
                      <div class="d-flex align-center">
                        <span class="font-weight-medium">Säulen-Stichprobe</span>
                        <LTag variant="success" size="sm" class="ml-2">Schnell</LTag>
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Zufällige Samples pro Säulen-Paar
                      </div>
                    </div>
                  </template>
                </v-radio>

                <!-- Round Robin -->
                <v-radio value="round_robin" class="mt-2">
                  <template v-slot:label>
                    <div class="radio-label">
                      <div class="d-flex align-center">
                        <span class="font-weight-medium">Round Robin</span>
                        <LTag variant="warning" size="sm" class="ml-2">Mittel</LTag>
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Jeder Thread gegen jeden Thread der anderen Säule
                      </div>
                    </div>
                  </template>
                </v-radio>

                <!-- Free For All -->
                <v-radio value="free_for_all" class="mt-2">
                  <template v-slot:label>
                    <div class="radio-label">
                      <div class="d-flex align-center">
                        <span class="font-weight-medium">Jeder gegen Jeden</span>
                        <LTag variant="danger" size="sm" class="ml-2">Umfangreich</LTag>
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Vollständiges Ranking mit ELO-Scores
                      </div>
                    </div>
                  </template>
                </v-radio>
              </v-radio-group>
            </div>

            <!-- Samples per Pillar (only for pillar_sample mode) -->
            <div v-if="config.comparisonMode === 'pillar_sample'" class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-numeric</v-icon>
                Samples pro Säule: {{ config.samplesPerPillar }}
              </div>
              <v-slider
                v-model="config.samplesPerPillar"
                :min="1"
                :max="50"
                step="1"
                thumb-label
                color="primary"
                track-color="grey-lighten-2"
                hide-details
              >
                <template v-slot:prepend>
                  <v-text-field
                    v-model.number="config.samplesPerPillar"
                    type="number"
                    style="width: 70px"
                    density="compact"
                    hide-details
                    variant="outlined"
                    :min="1"
                    :max="50"
                  ></v-text-field>
                </template>
              </v-slider>
            </div>

            <!-- Max Threads per Pillar (for round_robin and free_for_all) -->
            <div v-if="config.comparisonMode !== 'pillar_sample'" class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-filter-variant</v-icon>
                Max. Threads pro Säule
                <v-chip v-if="config.maxThreadsPerPillar" size="x-small" color="info" class="ml-2">
                  Limitiert auf {{ config.maxThreadsPerPillar }}
                </v-chip>
              </div>
              <v-switch
                v-model="limitThreadsEnabled"
                color="primary"
                hide-details
                density="compact"
                class="mb-2"
              >
                <template v-slot:label>
                  <span class="text-body-2">Thread-Anzahl begrenzen</span>
                </template>
              </v-switch>
              <v-slider
                v-if="limitThreadsEnabled"
                v-model="config.maxThreadsPerPillar"
                :min="5"
                :max="50"
                step="5"
                thumb-label
                color="primary"
                track-color="grey-lighten-2"
                show-ticks="always"
                hide-details
              ></v-slider>
            </div>

            <!-- Position Swap -->
            <div class="config-section">
              <v-switch
                v-model="config.positionSwap"
                color="primary"
                hide-details
                density="compact"
              >
                <template v-slot:label>
                  <div>
                    <div class="d-flex align-center">
                      <v-icon class="mr-1" size="small">mdi-swap-horizontal</v-icon>
                      <span class="font-weight-medium">Position-Swap</span>
                      <v-chip size="x-small" color="info" class="ml-2">Empfohlen</v-chip>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Eliminiert Position-Bias (MT-Bench Methodik)
                    </div>
                  </div>
                </template>
              </v-switch>
            </div>

            <!-- Worker Count -->
            <div class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-server</v-icon>
                Parallele Worker: {{ config.workerCount }}
              </div>
              <v-slider
                v-model="config.workerCount"
                :min="1"
                :max="5"
                step="1"
                thumb-label
                color="primary"
                track-color="grey-lighten-2"
                show-ticks="always"
                :tick-labels="['1', '2', '3', '4', '5']"
                hide-details
              ></v-slider>
              <v-alert
                v-if="config.workerCount > 1"
                type="info"
                variant="tonal"
                density="compact"
                class="mt-2"
              >
                <strong>{{ config.workerCount }} Worker</strong> - ~{{ config.workerCount }}x schneller
              </v-alert>
            </div>

            <!-- Repetitions per Pair (only for pillar_sample mode) -->
            <div v-if="config.comparisonMode === 'pillar_sample'" class="config-section">
              <div class="section-title">
                <v-icon class="mr-1" size="small">mdi-repeat</v-icon>
                Wiederholungen pro Paar: {{ config.repetitionsPerPair }}
              </div>
              <v-slider
                v-model="config.repetitionsPerPair"
                :min="1"
                :max="5"
                step="1"
                thumb-label
                color="primary"
                track-color="grey-lighten-2"
                show-ticks="always"
                hide-details
              ></v-slider>
              <div class="text-caption text-medium-emphasis mt-1">
                Für statistische Stabilität
              </div>
            </div>
          </v-form>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Summary -->
      <div class="right-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2" size="small">mdi-information</v-icon>
          <span class="font-weight-medium">Zusammenfassung</span>
        </div>
        <div class="panel-content">
          <v-skeleton-loader v-if="isLoading('pillars')" type="card" height="400"></v-skeleton-loader>
          <template v-else>
            <!-- Loading state for estimate -->
            <div v-if="estimateLoading" class="text-center py-4">
              <v-progress-circular indeterminate color="primary" size="32"></v-progress-circular>
              <div class="text-caption mt-2">Berechne Schätzung...</div>
            </div>

            <template v-else>
              <!-- Mode Badge -->
              <div class="summary-item">
                <div class="summary-label">Vergleichs-Modus</div>
                <v-chip :color="modeColor" size="small">
                  {{ modeDisplayName }}
                </v-chip>
              </div>

              <!-- Thread Stats -->
              <div class="summary-item">
                <div class="summary-label">Threads</div>
                <div class="summary-value">
                  {{ estimate?.total_threads || selectedThreadCount || 0 }}
                </div>
                <div v-if="estimate?.threads_per_pillar" class="text-caption text-medium-emphasis">
                  <span v-for="(count, pillar) in estimate.threads_per_pillar" :key="pillar">
                    S{{ pillar }}: {{ count }}
                    <span v-if="pillar != Object.keys(estimate.threads_per_pillar).pop()">, </span>
                  </span>
                </div>
              </div>

              <!-- Position Swap -->
              <div class="summary-item">
                <div class="summary-label">Position-Swap</div>
                <div class="summary-value">
                  {{ config.positionSwap ? 'Ja (×2)' : 'Nein' }}
                </div>
              </div>

              <!-- Total Comparisons -->
              <div class="summary-total">
                <div class="summary-label">Gesamt-Vergleiche</div>
                <div class="text-h4 font-weight-bold text-primary">
                  {{ formatNumber(estimate?.total_comparisons || estimatedComparisons) }}
                </div>
                <div v-if="estimate?.base_comparisons" class="text-caption text-medium-emphasis">
                  ({{ formatNumber(estimate.base_comparisons) }} Basis {{ config.positionSwap ? '× 2 Swap' : '' }})
                </div>
              </div>

              <!-- Duration Estimates -->
              <div class="summary-item">
                <div class="summary-label">Geschätzte Laufzeit</div>
                <div v-if="estimate?.estimated_duration_by_workers" class="duration-grid">
                  <div
                    v-for="(duration, workers) in estimate.estimated_duration_by_workers"
                    :key="workers"
                    class="duration-item"
                    :class="{ 'active': config.workerCount == workers }"
                  >
                    <div class="duration-workers">{{ workers }}W</div>
                    <div class="duration-time">{{ formatDuration(duration) }}</div>
                  </div>
                </div>
                <div v-else class="summary-value">
                  {{ formatDuration(estimatedDuration) }}
                </div>
              </div>

              <!-- Warning for long duration -->
              <v-alert
                v-if="selectedDuration > 120"
                type="warning"
                variant="tonal"
                density="compact"
                class="mb-3"
              >
                <div class="text-caption">
                  Laufzeit: <strong>{{ formatDuration(selectedDuration) }}</strong>
                </div>
              </v-alert>

              <!-- Selected Pillars -->
              <div v-if="config.selectedPillars.length > 0" class="summary-item">
                <div class="summary-label">Ausgewählte Säulen</div>
                <div class="pillar-chips">
                  <v-chip
                    v-for="pillarId in config.selectedPillars"
                    :key="pillarId"
                    size="x-small"
                    color="primary"
                    variant="tonal"
                  >
                    {{ getPillarName(pillarId) }}
                  </v-chip>
                </div>
              </div>

              <!-- Calculation Info -->
              <div class="calculation-info">
                <div class="calc-title">
                  <v-icon size="x-small" class="mr-1">mdi-calculator</v-icon>
                  Berechnungsdetails
                </div>
                <div class="text-caption text-medium-emphasis">
                  <div><strong>Modus:</strong> {{ modeDescription }}</div>
                  <div v-if="config.comparisonMode === 'pillar_sample'">
                    <strong>Formel:</strong> {{ estimatedPairs }} Paare × {{ config.samplesPerPillar }} Samples
                    {{ config.positionSwap ? '× 2' : '' }}
                  </div>
                  <div v-else-if="config.comparisonMode === 'round_robin'">
                    <strong>Formel:</strong> Σ(n<sub>i</sub> × n<sub>j</sub>) für alle Paare
                    {{ config.positionSwap ? '× 2' : '' }}
                  </div>
                  <div v-else>
                    <strong>Formel:</strong> N × (N-1) / 2 {{ config.positionSwap ? '× 2' : '' }}
                  </div>
                  <div><strong>Dauer:</strong> ≈ 10 Sek/Vergleich</div>
                </div>
              </div>

              <!-- No Data Warning -->
              <v-alert
                v-if="selectedThreadCount === 0 && !estimateLoading"
                type="warning"
                variant="tonal"
                density="compact"
                class="mt-3"
              >
                <div class="text-caption">
                  <strong>Keine Threads verfügbar.</strong><br>
                  Bitte synchronisieren Sie zuerst KIA-Daten unter
                  <router-link to="/judge" class="text-primary">LLM-as-Judge Übersicht</router-link>.
                </div>
              </v-alert>

              <!-- Info Alert -->
              <v-alert
                v-else
                type="info"
                variant="tonal"
                density="compact"
                class="mt-3"
              >
                <div class="text-caption">
                  Die Session wird automatisch gestartet.
                </div>
              </v-alert>
            </template>
          </template>
        </div>
      </div>
    </div>

    <!-- Action Bar -->
    <div class="action-bar">
      <LBtn
        variant="cancel"
        prepend-icon="mdi-arrow-left"
        @click="$router.push({ name: 'JudgeOverview' })"
      >
        Abbrechen
      </LBtn>
      <v-spacer></v-spacer>
      <LBtn
        variant="primary"
        prepend-icon="mdi-play"
        :disabled="!canCreate"
        :loading="creating"
        @click="createSession"
      >
        Session erstellen & starten
      </LBtn>
    </div>
  </div>
</template>

<script setup>
import { watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { usePanelResize } from '@/composables/usePanelResize';
import {
  useJudgeConfigState,
  useJudgeConfigComputed,
  useJudgeConfigActions
} from './JudgeConfig/index';

const router = useRouter();

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 60,
  minLeftPercent: 40,
  maxLeftPercent: 75,
  storageKey: 'judge-config-panel-width'
});

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['pillars']);

// Initialize state composable
const {
  form,
  valid,
  creating,
  estimate,
  estimateLoading,
  limitThreadsEnabled,
  availablePillars,
  config,
  setupLimitWatcher,
  initializeDefaultPillars,
  updateThreadCounts
} = useJudgeConfigState();

// Initialize computed composable
const {
  minPillarsRequired,
  selectedThreadCount,
  modeDisplayName,
  modeColor,
  modeDescription,
  estimatedPairs,
  estimatedComparisons,
  estimatedDuration,
  selectedDuration,
  canCreate
} = useJudgeConfigComputed(config, availablePillars, estimate, limitThreadsEnabled);

// Initialize actions composable
const {
  formatNumber,
  formatDuration,
  getPillarName: getPillarNameFn,
  debouncedFetchEstimate,
  fetchEstimate: fetchEstimateFn,
  createSession: createSessionFn
} = useJudgeConfigActions(config, estimate, limitThreadsEnabled, minPillarsRequired, updateThreadCounts);

// Wrapper functions
const getPillarName = (id) => getPillarNameFn(id, availablePillars);
const fetchEstimate = () => fetchEstimateFn(estimateLoading);
const createSession = () => createSessionFn(form, creating, router);

// Setup watchers
setupLimitWatcher();

// Watch for config changes to update estimate
watch(
  () => [
    config.value.selectedPillars,
    config.value.comparisonMode,
    config.value.samplesPerPillar,
    config.value.maxThreadsPerPillar,
    config.value.positionSwap
  ],
  () => {
    debouncedFetchEstimate(fetchEstimate);
  },
  { deep: true }
);

// Lifecycle
onMounted(async () => {
  await withLoading('pillars', async () => {
    initializeDefaultPillars();
    fetchEstimate();
  });
});
</script>

<style scoped>
.judge-config-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Page Header */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
}

.header-content {
  flex: 1;
}

.header-content h1 {
  margin: 0;
  line-height: 1.2;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Panels */
.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Resize Divider */
.resize-divider {
  width: 6px;
  background: rgba(var(--v-border-color), var(--v-border-opacity));
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.3);
}

.resize-handle {
  width: 2px;
  height: 32px;
  background: rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 1px;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
}

/* Config Sections */
.config-section {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.5);
}

.config-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  color: rgb(var(--v-theme-on-surface));
}

/* Radio Labels */
.comparison-mode-group :deep(.v-selection-control) {
  align-items: flex-start;
}

.radio-label {
  padding: 4px 0;
}

/* Summary Items */
.summary-item {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  margin-bottom: 12px;
}

.summary-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 4px;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.summary-total {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.15) 0%, rgba(var(--v-theme-primary), 0.08) 100%);
  border-radius: 8px;
  margin-bottom: 12px;
}

/* Duration Grid */
.duration-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
  margin-top: 8px;
}

.duration-item {
  text-align: center;
  padding: 6px 2px;
  border-radius: 6px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  transition: all 0.2s ease;
}

.duration-item.active {
  background: rgba(var(--v-theme-primary), 0.25);
  border: 1px solid rgba(var(--v-theme-primary), 0.6);
}

.duration-workers {
  font-size: 10px;
  opacity: 0.7;
}

.duration-time {
  font-size: 11px;
  font-weight: 600;
}

/* Pillar Chips */
.pillar-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

/* Calculation Info */
.calculation-info {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  margin-top: 12px;
}

.calc-title {
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

/* Action Bar */
.action-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
}
</style>
