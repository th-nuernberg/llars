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
                  Säulen auswählen (1-5)
                </div>
                <v-chip-group
                  v-model="config.selectedPillars"
                  multiple
                  column
                  mandatory
                >
                  <v-chip
                    v-for="pillar in availablePillars"
                    :key="pillar.id"
                    :value="pillar.id"
                    :disabled="config.selectedPillars.length >= 5 && !config.selectedPillars.includes(pillar.id)"
                    filter
                    variant="outlined"
                    color="primary"
                  >
                    <v-icon start>{{ pillar.icon }}</v-icon>
                    {{ pillar.name }}
                  </v-chip>
                </v-chip-group>
                <div v-if="config.selectedPillars.length === 0" class="text-error text-caption mt-1">
                  Bitte wählen Sie mindestens eine Säule aus
                </div>
                <div v-else class="text-medium-emphasis text-caption mt-1">
                  {{ config.selectedPillars.length }} von 5 Säulen ausgewählt
                </div>
              </div>

              <!-- Comparison Mode -->
              <div class="mb-6">
                <div class="text-subtitle-1 font-weight-bold mb-2">
                  <v-icon class="mr-1">mdi-compare</v-icon>
                  Vergleichs-Modus
                </div>
                <v-radio-group v-model="config.comparisonMode" inline>
                  <v-radio
                    label="Alle Paare"
                    value="all_pairs"
                    class="mr-4"
                  >
                    <template v-slot:label>
                      <div>
                        <div class="font-weight-medium">Alle Paare</div>
                        <div class="text-caption text-medium-emphasis">
                          Jede Säule wird mit jeder anderen verglichen
                        </div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio
                    label="Spezifisch"
                    value="specific"
                  >
                    <template v-slot:label>
                      <div>
                        <div class="font-weight-medium">Spezifisch</div>
                        <div class="text-caption text-medium-emphasis">
                          Nur bestimmte Paarungen vergleichen
                        </div>
                      </div>
                    </template>
                  </v-radio>
                </v-radio-group>
              </div>

              <!-- Samples per Pillar -->
              <div class="mb-6">
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
                  Anzahl der Konversations-Samples, die pro Säule bewertet werden
                </div>
              </div>

              <!-- Position Swap -->
              <div class="mb-4">
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
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        Führt jeden Vergleich zweimal durch mit vertauschten Positionen (A↔B)
                        um Position-Bias zu reduzieren
                      </div>
                    </div>
                  </template>
                </v-switch>
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
            <!-- Stats -->
            <div class="summary-item mb-4">
              <div class="text-caption text-medium-emphasis">Ausgewählte Säulen</div>
              <div class="text-h5 font-weight-bold">{{ config.selectedPillars.length }}</div>
            </div>

            <div class="summary-item mb-4">
              <div class="text-caption text-medium-emphasis">Samples pro Säule</div>
              <div class="text-h5 font-weight-bold">{{ config.samplesPerPillar }}</div>
            </div>

            <div class="summary-item mb-4">
              <div class="text-caption text-medium-emphasis">Vergleichs-Paare</div>
              <div class="text-h5 font-weight-bold">{{ estimatedPairs }}</div>
            </div>

            <div class="summary-item mb-4">
              <div class="text-caption text-medium-emphasis">Position-Swap</div>
              <div class="text-h5 font-weight-bold">
                {{ config.positionSwap ? 'Ja (2x)' : 'Nein' }}
              </div>
            </div>

            <v-divider class="my-4"></v-divider>

            <!-- Total Comparisons -->
            <div class="summary-total">
              <div class="text-subtitle-2 text-medium-emphasis mb-1">
                Geschätzte Gesamt-Vergleiche
              </div>
              <div class="text-h4 font-weight-bold text-primary">
                {{ estimatedComparisons }}
              </div>
              <div class="text-caption text-medium-emphasis mt-2">
                ≈ {{ estimatedDuration }} Minuten
              </div>
            </div>

            <v-divider class="my-4"></v-divider>

            <!-- Selected Pillars List -->
            <div v-if="config.selectedPillars.length > 0">
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
              class="mt-4"
            >
              Die Session wird nach dem Erstellen automatisch in die Warteschlange eingereiht.
            </v-alert>
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
              Session erstellen
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
              <strong>Paare:</strong> {{ estimatedPairsFormula }}
            </div>
            <div class="mb-2">
              <strong>Vergleiche:</strong> {{ estimatedPairs }} Paare × {{ config.samplesPerPillar }} Samples
              {{ config.positionSwap ? ' × 2 (Swap)' : '' }}
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
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

// Form
const form = ref(null);
const valid = ref(false);
const creating = ref(false);

// Available Pillars
const availablePillars = ref([
  { id: 1, name: 'Säule 1', icon: 'mdi-numeric-1-box' },
  { id: 2, name: 'Säule 2', icon: 'mdi-numeric-2-box' },
  { id: 3, name: 'Säule 3', icon: 'mdi-numeric-3-box' },
  { id: 4, name: 'Säule 4', icon: 'mdi-numeric-4-box' },
  { id: 5, name: 'Säule 5', icon: 'mdi-numeric-5-box' }
]);

// Configuration
const config = ref({
  sessionName: '',
  selectedPillars: [],
  comparisonMode: 'all_pairs',
  samplesPerPillar: 10,
  positionSwap: true
});

// Computed
const estimatedPairs = computed(() => {
  const n = config.value.selectedPillars.length;
  if (n < 2) return 0;
  // Formula for all pairs: n * (n - 1) / 2
  return (n * (n - 1)) / 2;
});

const estimatedPairsFormula = computed(() => {
  const n = config.value.selectedPillars.length;
  if (n < 2) return '0';
  return `${n} × ${n - 1} / 2 = ${estimatedPairs.value}`;
});

const estimatedComparisons = computed(() => {
  const pairs = estimatedPairs.value;
  const samples = config.value.samplesPerPillar;
  const multiplier = config.value.positionSwap ? 2 : 1;
  return pairs * samples * multiplier;
});

const estimatedDuration = computed(() => {
  // Assume ~10 seconds per comparison
  const seconds = estimatedComparisons.value * 10;
  return Math.ceil(seconds / 60);
});

const canCreate = computed(() => {
  return (
    valid.value &&
    config.value.sessionName.trim() !== '' &&
    config.value.selectedPillars.length >= 2
  );
});

// Methods
const getPillarName = (id) => {
  const pillar = availablePillars.value.find(p => p.id === id);
  return pillar ? pillar.name : `Säule ${id}`;
};

const createSession = async () => {
  // Validate form
  const { valid: isValid } = await form.value.validate();
  if (!isValid) return;

  creating.value = true;
  try {
    const payload = {
      session_name: config.value.sessionName,
      pillar_ids: config.value.selectedPillars,
      comparison_mode: config.value.comparisonMode,
      samples_per_pillar: config.value.samplesPerPillar,
      position_swap: config.value.positionSwap
    };

    // Use debug endpoint in development mode to avoid auth issues
    const isDev = import.meta.env.DEV || import.meta.env.MODE === 'development';
    const createEndpoint = isDev
      ? '/api/judge/sessions-debug'
      : '/api/judge/sessions';

    const response = await axios.post(createEndpoint, payload);
    const sessionId = response.data.session_id;

    // Auto-start the session immediately after creation
    try {
      const startEndpoint = isDev
        ? `/api/judge/sessions/${sessionId}/start-debug`
        : `/api/judge/sessions/${sessionId}/start`;
      await axios.post(startEndpoint);
      console.log(`Session ${sessionId} auto-started`);
    } catch (startError) {
      console.warn('Auto-start failed, session can be started manually:', startError);
    }

    // Navigate to session detail
    router.push({ name: 'JudgeSession', params: { id: sessionId } });
  } catch (error) {
    console.error('Error creating session:', error);
    alert('Fehler beim Erstellen der Session. Bitte versuchen Sie es erneut.');
  } finally {
    creating.value = false;
  }
};
</script>

<style scoped>
.judge-config {
  max-width: 1400px;
  margin: 0 auto;
}

.summary-item {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
}

.summary-total {
  text-align: center;
  padding: 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-primary), 0.05) 100%);
  border-radius: 8px;
}
</style>
