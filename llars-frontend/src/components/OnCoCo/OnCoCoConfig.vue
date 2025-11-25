<template>
  <v-container class="oncoco-config">
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

    <v-row>
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-cog</v-icon>
            Neue OnCoCo Analyse konfigurieren
          </v-card-title>

          <v-card-text>
            <v-form ref="formRef" v-model="formValid">
              <!-- Analysis Name -->
              <v-text-field
                v-model="config.name"
                label="Analyse Name"
                placeholder="z.B. OnCoCo Analyse Saeule 1+3"
                :rules="[v => !!v || 'Name ist erforderlich']"
                prepend-icon="mdi-label"
                variant="outlined"
                class="mb-4"
              ></v-text-field>

              <!-- Pillar Selection -->
              <div class="text-subtitle-1 font-weight-medium mb-2">
                <v-icon class="mr-1">mdi-database</v-icon>
                Saeulen auswaehlen
              </div>
              <v-row class="mb-4">
                <v-col
                  v-for="(pillar, pillarNum) in availablePillars"
                  :key="pillarNum"
                  cols="12"
                  sm="6"
                  md="4"
                >
                  <v-card
                    :variant="config.pillars.includes(Number(pillarNum)) ? 'tonal' : 'outlined'"
                    :color="config.pillars.includes(Number(pillarNum)) ? 'primary' : undefined"
                    class="pillar-card"
                    @click="togglePillar(Number(pillarNum))"
                  >
                    <v-card-text>
                      <div class="d-flex align-center">
                        <v-checkbox
                          :model-value="config.pillars.includes(Number(pillarNum))"
                          hide-details
                          density="compact"
                          @click.stop
                          @update:model-value="togglePillar(Number(pillarNum))"
                        ></v-checkbox>
                        <div class="ml-2">
                          <div class="font-weight-bold">Saeule {{ pillarNum }}</div>
                          <div class="text-caption">{{ pillar.name }}</div>
                        </div>
                      </div>
                      <v-divider class="my-2"></v-divider>
                      <div class="d-flex justify-space-between text-caption">
                        <span>Threads:</span>
                        <span class="font-weight-bold">{{ pillar.db_thread_count || 0 }}</span>
                      </div>
                      <div class="d-flex justify-space-between text-caption">
                        <span>Status:</span>
                        <v-chip
                          :color="pillar.db_thread_count > 0 ? 'success' : 'warning'"
                          size="x-small"
                        >
                          {{ pillar.db_thread_count > 0 ? 'Bereit' : 'Sync erforderlich' }}
                        </v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Advanced Options -->
              <v-expansion-panels class="mb-4">
                <v-expansion-panel>
                  <v-expansion-panel-title>
                    <v-icon class="mr-2">mdi-tune</v-icon>
                    Erweiterte Optionen
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="config.use_level2"
                      label="Level-2 Aggregation verwenden"
                      hint="Fasst die 68 Kategorien in 18 uebergeordnete Gruppen zusammen"
                      persistent-hint
                      color="primary"
                    ></v-switch>

                    <v-slider
                      v-model="config.batch_size"
                      label="Batch-Groesse"
                      min="4"
                      max="64"
                      step="4"
                      thumb-label
                      hint="Anzahl Saetze pro GPU-Batch (hoeher = schneller, aber mehr Speicher)"
                      persistent-hint
                      class="mt-4"
                    ></v-slider>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-form>
          </v-card-text>

          <v-card-actions class="pa-4">
            <v-btn
              variant="text"
              @click="router.push({ name: 'OnCoCoOverview' })"
            >
              Abbrechen
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              variant="flat"
              prepend-icon="mdi-content-save"
              :disabled="!formValid || config.pillars.length === 0"
              :loading="creating"
              @click="createAnalysis"
            >
              Analyse erstellen
            </v-btn>
            <v-btn
              color="success"
              variant="flat"
              prepend-icon="mdi-play"
              :disabled="!formValid || config.pillars.length === 0"
              :loading="creating"
              @click="createAndStartAnalysis"
            >
              Erstellen & Starten
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Info Panel -->
      <v-col cols="12" md="4">
        <v-card class="mb-4">
          <v-card-title>
            <v-icon class="mr-2" color="info">mdi-information</v-icon>
            Ueber OnCoCo
          </v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-3">
              Das OnCoCo-Modell (Online Counseling Conversations) klassifiziert
              Beratungsgespraeche auf Satzebene in 68 Kategorien.
            </p>
            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">Kategorien</div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>Berater (CO):</span>
              <span class="font-weight-bold">40</span>
            </div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>Klient (CL):</span>
              <span class="font-weight-bold">28</span>
            </div>
            <v-divider class="my-3"></v-divider>
            <div class="text-subtitle-2 font-weight-bold mb-2">Metriken</div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>Genauigkeit:</span>
              <span class="font-weight-bold">~80%</span>
            </div>
            <div class="d-flex justify-space-between text-body-2 mb-1">
              <span>F1 Makro:</span>
              <span class="font-weight-bold">0.78</span>
            </div>
          </v-card-text>
        </v-card>

        <v-card>
          <v-card-title>
            <v-icon class="mr-2" color="warning">mdi-alert</v-icon>
            Hinweise
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal" density="compact" class="mb-2">
              Die Analyse kann je nach Datenmenge einige Minuten dauern.
            </v-alert>
            <v-alert type="warning" variant="tonal" density="compact">
              Stellen Sie sicher, dass die ausgewaehlten Saeulen synchronisiert sind.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

// Form State
const formRef = ref(null);
const formValid = ref(false);
const creating = ref(false);

const config = reactive({
  name: '',
  pillars: [1, 3, 5],  // Default active pillars
  use_level2: true,
  batch_size: 16
});

const availablePillars = ref({});

// Load Pillar Status
const loadPillarStatus = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/pillars`);
    availablePillars.value = response.data.pillars || {};
  } catch (error) {
    console.error('Error loading pillar status:', error);
  }
};

// Toggle Pillar Selection
const togglePillar = (pillarNum) => {
  const idx = config.pillars.indexOf(pillarNum);
  if (idx > -1) {
    config.pillars.splice(idx, 1);
  } else {
    config.pillars.push(pillarNum);
    config.pillars.sort();
  }
};

// Create Analysis
const createAnalysis = async (startImmediately = false) => {
  if (!formValid.value || config.pillars.length === 0) return;

  creating.value = true;
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses`,
      {
        name: config.name,
        pillars: config.pillars,
        use_level2: config.use_level2,
        batch_size: config.batch_size
      }
    );

    const analysisId = response.data.id;

    if (startImmediately) {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/start`
      );
    }

    router.push({ name: 'OnCoCoResults', params: { id: analysisId } });
  } catch (error) {
    console.error('Error creating analysis:', error);
  } finally {
    creating.value = false;
  }
};

const createAndStartAnalysis = () => {
  createAnalysis(true);
};

// Lifecycle
onMounted(() => {
  loadPillarStatus();
});
</script>

<style scoped>
.oncoco-config {
  max-width: 1200px;
  margin: 0 auto;
}

.pillar-card {
  cursor: pointer;
  transition: all 0.2s ease;
}

.pillar-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
