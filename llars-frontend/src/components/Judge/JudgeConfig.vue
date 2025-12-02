<template>
  <v-container class="judge-config">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.push({ name: 'JudgeOverview' })"
          ></v-btn>
          <div class="ml-2">
            <h1 class="text-h4 font-weight-bold">Neue Judge Session</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Konfigurieren Sie die automatisierte Bewertung
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <v-row>
      <!-- Configuration Form -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-cog</v-icon>
            Konfiguration
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-form ref="form" v-model="valid">
              <!-- Session Name -->
              <v-text-field
                v-model="config.sessionName"
                label="Session Name"
                hint="Geben Sie einen beschreibenden Namen für diese Session ein"
                :rules="[v => !!v || 'Session Name ist erforderlich']"
                prepend-icon="mdi-label"
                variant="outlined"
                class="mb-4"
              ></v-text-field>

              <!-- Pillar Selection -->
              <div class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-pillar</v-icon>
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
                  >
                    <v-icon start>{{ pillar.icon }}</v-icon>
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
              <div class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-compare</v-icon>
                  Vergleichs-Modus
                </div>
                <v-radio-group v-model="config.comparisonMode" class="comparison-mode-group">
                  <!-- Pillar Sample -->
                  <v-radio value="pillar_sample">
                    <template v-slot:label>
                      <div class="radio-label">
                        <div class="d-flex align-center">
                          <span class="font-weight-medium">Säulen-Stichprobe</span>
                          <v-chip size="x-small" color="success" class="ml-2">Schnell</v-chip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          Zufällige Samples pro Säulen-Paar. Schneller Überblick welche Säule besser ist.
                        </div>
                      </div>
                    </template>
                  </v-radio>

                  <!-- Round Robin -->
                  <v-radio value="round_robin" class="mt-3">
                    <template v-slot:label>
                      <div class="radio-label">
                        <div class="d-flex align-center">
                          <span class="font-weight-medium">Round Robin</span>
                          <v-chip size="x-small" color="warning" class="ml-2">Mittel</v-chip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          Jeder Thread einer Säule gegen jeden Thread der anderen Säule.
                          Ermöglicht Thread-Level Statistiken.
                        </div>
                      </div>
                    </template>
                  </v-radio>

                  <!-- Free For All -->
                  <v-radio value="free_for_all" class="mt-3">
                    <template v-slot:label>
                      <div class="radio-label">
                        <div class="d-flex align-center">
                          <span class="font-weight-medium">Jeder gegen Jeden</span>
                          <v-chip size="x-small" color="error" class="ml-2">Umfangreich</v-chip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          Jeder Thread gegen jeden anderen Thread. Vollständiges Ranking mit ELO-Scores.
                          <strong>Achtung:</strong> Kann bei vielen Threads sehr lange dauern!
                        </div>
                      </div>
                    </template>
                  </v-radio>
                </v-radio-group>
              </div>

              <!-- Samples per Pillar (only for pillar_sample mode) -->
              <div v-if="config.comparisonMode === 'pillar_sample'" class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-numeric</v-icon>
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
                >
                  <template v-slot:prepend>
                    <v-text-field
                      v-model.number="config.samplesPerPillar"
                      type="number"
                      style="width: 80px"
                      density="compact"
                      hide-details
                      variant="outlined"
                      :min="1"
                      :max="50"
                    ></v-text-field>
                  </template>
                </v-slider>
                <div class="text-caption text-medium-emphasis">
                  Anzahl der Konversations-Samples, die pro Säule zufällig ausgewählt werden
                </div>
              </div>

              <!-- Max Threads per Pillar (for round_robin and free_for_all) -->
              <div v-if="config.comparisonMode !== 'pillar_sample'" class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-filter-variant</v-icon>
                  Max. Threads pro Säule
                  <v-chip
                    v-if="config.maxThreadsPerPillar"
                    size="x-small"
                    color="info"
                    class="ml-2"
                  >
                    Limitiert auf {{ config.maxThreadsPerPillar }}
                  </v-chip>
                </div>
                <v-switch
                  v-model="limitThreadsEnabled"
                  color="primary"
                  hide-details
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
                  :tick-labels="['5', '10', '15', '20', '25', '30', '35', '40', '45', '50']"
                >
                  <template v-slot:prepend>
                    <v-text-field
                      v-model.number="config.maxThreadsPerPillar"
                      type="number"
                      style="width: 80px"
                      density="compact"
                      hide-details
                      variant="outlined"
                      :min="5"
                      :max="50"
                    ></v-text-field>
                  </template>
                </v-slider>
                <div class="text-caption text-medium-emphasis">
                  Begrenzt die Anzahl Threads pro Säule (zufällige Auswahl).
                  Reduziert die Laufzeit erheblich.
                </div>
              </div>

              <!-- Position Swap -->
              <div class="mb-6">
                <v-switch
                  v-model="config.positionSwap"
                  color="primary"
                  hide-details
                >
                  <template v-slot:label>
                    <div>
                      <div class="font-weight-medium">
                        <v-icon class="mr-1">mdi-swap-horizontal</v-icon>
                        Position-Swap aktivieren
                        <v-chip size="x-small" color="info" class="ml-2">Empfohlen</v-chip>
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Führt jeden Vergleich zweimal durch mit vertauschten Positionen (A↔B)
                        um Position-Bias zu eliminieren (MT-Bench Methodik)
                      </div>
                    </div>
                  </template>
                </v-switch>
              </div>

              <!-- Worker Count -->
              <div class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-server</v-icon>
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
                ></v-slider>
                <v-alert
                  v-if="config.workerCount > 1"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mt-2"
                >
                  <strong>{{ config.workerCount }} Worker</strong> arbeiten parallel.
                  Die Live-Ansicht zeigt alle Worker nebeneinander.
                  <div class="text-caption mt-1">
                    Geschätzte Beschleunigung: ~{{ config.workerCount }}x schneller
                  </div>
                </v-alert>
              </div>

              <!-- Repetitions per Pair (only for pillar_sample mode) -->
              <div v-if="config.comparisonMode === 'pillar_sample'" class="mb-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-repeat</v-icon>
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
                >
                  <template v-slot:prepend>
                    <v-text-field
                      v-model.number="config.repetitionsPerPair"
                      type="number"
                      style="width: 80px"
                      density="compact"
                      hide-details
                      variant="outlined"
                      :min="1"
                      :max="5"
                    ></v-text-field>
                  </template>
                </v-slider>
                <div class="text-caption text-medium-emphasis">
                  Wie oft jedes Sample-Paar verglichen wird (für statistische Stabilität).
                  Bei >1 werden verschiedene Threads aus den Säulen gewählt.
                </div>
              </div>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Summary Card -->
      <v-col cols="12" md="4">
        <v-card color="surface-variant">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-information</v-icon>
            Zusammenfassung
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <!-- Loading state for estimate -->
            <div v-if="estimateLoading" class="text-center py-4">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <div class="text-caption mt-2">Berechne Schätzung...</div>
            </div>

            <template v-else>
              <!-- Mode Badge -->
              <div class="summary-item mb-4">
                <div class="text-caption text-medium-emphasis">Vergleichs-Modus</div>
                <div class="d-flex align-center mt-1">
                  <v-chip
                    :color="modeColor"
                    size="small"
                  >
                    {{ modeDisplayName }}
                  </v-chip>
                </div>
              </div>

              <!-- Thread Stats -->
              <div class="summary-item mb-4">
                <div class="text-caption text-medium-emphasis">Threads</div>
                <div class="text-h5 font-weight-bold">
                  {{ estimate?.total_threads || selectedThreadCount || 0 }}
                </div>
                <div v-if="estimate?.threads_per_pillar" class="text-caption">
                  <span v-for="(count, pillar) in estimate.threads_per_pillar" :key="pillar">
                    S{{ pillar }}: {{ count }}
                    <span v-if="pillar != Object.keys(estimate.threads_per_pillar).pop()">, </span>
                  </span>
                </div>
              </div>

              <!-- Position Swap -->
              <div class="summary-item mb-4">
                <div class="text-caption text-medium-emphasis">Position-Swap</div>
                <div class="text-h5 font-weight-bold">
                  {{ config.positionSwap ? 'Ja (×2)' : 'Nein' }}
                </div>
              </div>

              <v-divider class="my-4"></v-divider>

              <!-- Total Comparisons -->
              <div class="summary-total">
                <div class="text-subtitle-2 text-medium-emphasis mb-1">
                  Gesamt-Vergleiche
                </div>
                <div class="text-h3 font-weight-bold text-primary">
                  {{ formatNumber(estimate?.total_comparisons || estimatedComparisons) }}
                </div>
                <div v-if="estimate?.base_comparisons" class="text-caption text-medium-emphasis">
                  ({{ formatNumber(estimate.base_comparisons) }} Basis {{ config.positionSwap ? '× 2 Swap' : '' }})
                </div>
              </div>

              <v-divider class="my-4"></v-divider>

              <!-- Duration Estimates -->
              <div class="summary-item mb-4">
                <div class="text-caption text-medium-emphasis mb-2">Geschätzte Laufzeit</div>
                <div v-if="estimate?.estimated_duration_by_workers" class="duration-grid">
                  <div
                    v-for="(duration, workers) in estimate.estimated_duration_by_workers"
                    :key="workers"
                    class="duration-item"
                    :class="{ 'active': config.workerCount == workers }"
                  >
                    <div class="text-caption">{{ workers }} Worker</div>
                    <div class="font-weight-bold">{{ formatDuration(duration) }}</div>
                  </div>
                </div>
                <div v-else class="text-h6 font-weight-bold">
                  {{ formatDuration(estimatedDuration) }}
                </div>
              </div>

              <!-- Warning for long duration -->
              <v-alert
                v-if="selectedDuration > 120"
                type="warning"
                variant="tonal"
                density="compact"
                class="mb-4"
              >
                <div class="font-weight-medium">Lange Laufzeit</div>
                <div class="text-caption">
                  Diese Session dauert voraussichtlich
                  <strong>{{ formatDuration(selectedDuration) }}</strong>.
                  <span v-if="config.comparisonMode !== 'pillar_sample'">
                    Erwäge "Max. Threads pro Säule" zu begrenzen.
                  </span>
                </div>
              </v-alert>

              <!-- Selected Pillars List -->
              <div v-if="config.selectedPillars.length > 0" class="mb-4">
                <div class="text-subtitle-2 font-weight-bold mb-2">Ausgewählte Säulen:</div>
                <v-chip
                  v-for="pillarId in config.selectedPillars"
                  :key="pillarId"
                  size="small"
                  class="mb-1 mr-1"
                  color="primary"
                >
                  {{ getPillarName(pillarId) }}
                </v-chip>
              </div>

              <!-- Info Alert -->
              <v-alert
                type="info"
                variant="tonal"
                density="compact"
              >
                Die Session wird nach dem Erstellen automatisch gestartet.
              </v-alert>
            </template>
          </v-card-text>

          <!-- Create Button -->
          <v-card-actions class="pa-4">
            <v-btn
              block
              color="primary"
              size="large"
              prepend-icon="mdi-play"
              :disabled="!canCreate"
              :loading="creating"
              @click="createSession"
            >
              Session erstellen & starten
            </v-btn>
          </v-card-actions>
        </v-card>

        <!-- Calculation Info -->
        <v-card class="mt-4">
          <v-card-title class="text-subtitle-1">
            <v-icon class="mr-1" size="small">mdi-calculator</v-icon>
            Berechnungsdetails
          </v-card-title>
          <v-card-text class="text-caption">
            <div class="mb-2">
              <strong>Modus:</strong> {{ modeDescription }}
            </div>
            <div v-if="config.comparisonMode === 'pillar_sample'" class="mb-2">
              <strong>Formel:</strong> {{ estimatedPairs }} Paare × {{ config.samplesPerPillar }} Samples
              {{ config.positionSwap ? '× 2' : '' }}
              {{ config.repetitionsPerPair > 1 ? `× ${config.repetitionsPerPair}` : '' }}
            </div>
            <div v-else-if="config.comparisonMode === 'round_robin'" class="mb-2">
              <strong>Formel:</strong> Σ(n<sub>i</sub> × n<sub>j</sub>) für alle Säulen-Paare
              {{ config.positionSwap ? '× 2' : '' }}
            </div>
            <div v-else class="mb-2">
              <strong>Formel:</strong> N × (N-1) / 2
              {{ config.positionSwap ? '× 2' : '' }}
            </div>
            <div>
              <strong>Dauer:</strong> ≈ 10 Sekunden pro Vergleich
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { watch, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  useJudgeConfigState,
  useJudgeConfigComputed,
  useJudgeConfigActions
} from './JudgeConfig/index';

const router = useRouter();

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
onMounted(() => {
  initializeDefaultPillars();
  fetchEstimate();
});
</script>

<style scoped>
.judge-config {
  max-width: 1400px;
  margin: 0 auto;
}

.comparison-mode-group :deep(.v-selection-control) {
  align-items: flex-start;
}

.radio-label {
  padding: 8px 0;
}

.summary-item {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface-variant), 0.6);
  border-radius: 8px;
}

.summary-total {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.15) 0%, rgba(var(--v-theme-primary), 0.08) 100%);
  border-radius: 8px;
}

.duration-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
}

.duration-item {
  text-align: center;
  padding: 6px 4px;
  border-radius: 6px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  transition: all 0.2s ease;
  /* Ensure text is readable in light mode */
  color: rgb(var(--v-theme-on-surface));
}

.duration-item.active {
  background: rgba(var(--v-theme-primary), 0.25);
  border: 1px solid rgba(var(--v-theme-primary), 0.6);
}

.duration-item .text-caption {
  font-size: 10px;
  /* Inherit color from parent for proper theme support */
  color: inherit;
  opacity: 0.85;
}

.duration-item .font-weight-bold {
  font-size: 11px;
  color: inherit;
}
</style>
