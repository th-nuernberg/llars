<template>
  <v-container class="oncoco-overview">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <div>
            <h1 class="text-h4 font-weight-bold">OnCoCo Analyse</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Klassifikation von Beratungsgespraechen mit dem OnCoCo Modell
            </p>
          </div>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            size="large"
            @click="navigateToConfig"
          >
            Neue Analyse erstellen
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="primary" size="56" class="mr-4">
              <v-icon icon="mdi-chart-bar" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ totalAnalyses }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Gesamt Analysen</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="success" size="56" class="mr-4">
              <v-icon icon="mdi-check-circle" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ completedAnalyses }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Abgeschlossen</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" size="56" class="mr-4">
              <v-icon icon="mdi-play-circle" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ runningAnalyses }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Laufend</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card">
          <v-card-text class="d-flex align-center">
            <v-avatar color="purple" size="56" class="mr-4">
              <v-icon icon="mdi-tag-multiple" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ labelCount }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">OnCoCo Kategorien</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Model Info Card -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-brain</v-icon>
            OnCoCo Modell Status
            <v-spacer></v-spacer>
            <v-chip
              :color="modelInfo.model?.model_available ? 'success' : 'error'"
              size="small"
            >
              {{ modelInfo.model?.model_available ? 'Verfuegbar' : 'Nicht verfuegbar' }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <div class="text-caption text-medium-emphasis">Modell</div>
                <div class="font-weight-medium">XLM-RoBERTa-Large OnCoCo</div>
              </v-col>
              <v-col cols="12" md="4">
                <div class="text-caption text-medium-emphasis">Kategorien</div>
                <div class="font-weight-medium">
                  {{ modelInfo.labels?.counselor || 0 }} Berater +
                  {{ modelInfo.labels?.client || 0 }} Klient =
                  {{ modelInfo.labels?.total || 68 }} Total
                </div>
              </v-col>
              <v-col cols="12" md="4">
                <div class="text-caption text-medium-emphasis">Geraet</div>
                <div class="font-weight-medium">{{ modelInfo.model?.device || 'CPU' }}</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Pillar Data Status -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="primary">mdi-database</v-icon>
            KIA Daten Status
            <v-spacer></v-spacer>
            <v-btn
              variant="text"
              prepend-icon="mdi-sync"
              @click="syncPillars"
              :loading="syncing"
              size="small"
            >
              Synchronisieren
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col
                v-for="(pillar, pillarNum) in pillarStatus.pillars"
                :key="pillarNum"
                cols="12"
                md="4"
                lg="2"
              >
                <v-card
                  variant="outlined"
                  :color="getPillarColor(pillar)"
                  class="pa-3"
                >
                  <div class="text-subtitle-2 font-weight-bold mb-1">
                    Saeule {{ pillarNum }}
                  </div>
                  <div class="text-caption">{{ pillar.name }}</div>
                  <v-divider class="my-2"></v-divider>
                  <div class="d-flex justify-space-between text-caption">
                    <span>Threads:</span>
                    <span class="font-weight-bold">{{ pillar.db_thread_count || 0 }}</span>
                  </div>
                  <div class="d-flex justify-space-between text-caption">
                    <span>Nachrichten:</span>
                    <span class="font-weight-bold">{{ pillar.db_message_count || 0 }}</span>
                  </div>
                  <v-chip
                    :color="pillar.gitlab_status === 'available' ? 'success' : 'grey'"
                    size="x-small"
                    class="mt-2"
                  >
                    {{ pillar.gitlab_status }}
                  </v-chip>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Analyses Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
            Meine OnCoCo Analysen
            <v-spacer></v-spacer>
            <v-chip-group v-model="statusFilter" mandatory class="mr-2">
              <v-chip value="all" size="small">Alle</v-chip>
              <v-chip value="running" size="small" color="info">Laufend</v-chip>
              <v-chip value="completed" size="small" color="success">Abgeschlossen</v-chip>
              <v-chip value="failed" size="small" color="error">Fehlgeschlagen</v-chip>
            </v-chip-group>
            <v-btn
              icon="mdi-refresh"
              variant="text"
              @click="loadAnalyses"
              :loading="loading"
            ></v-btn>
          </v-card-title>
          <v-divider></v-divider>

          <v-progress-linear v-if="loading" indeterminate></v-progress-linear>

          <v-data-table
            :headers="headers"
            :items="filteredAnalyses"
            :loading="loading"
            :items-per-page="10"
            class="analyses-table"
            @click:row="navigateToAnalysis"
          >
            <!-- Analysis Name -->
            <template v-slot:item.name="{ item }">
              <div class="font-weight-medium">{{ item.name }}</div>
            </template>

            <!-- Status -->
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="getStatusColor(item.status)"
                :prepend-icon="getStatusIcon(item.status)"
                size="small"
                variant="flat"
              >
                {{ getStatusText(item.status) }}
              </v-chip>
            </template>

            <!-- Progress -->
            <template v-slot:item.progress="{ item }">
              <div class="d-flex align-center" style="width: 200px;">
                <v-progress-linear
                  :model-value="item.progress || 0"
                  height="20"
                  rounded
                  :color="item.progress === 100 ? 'success' : 'primary'"
                >
                  <template v-slot:default="{ value }">
                    <strong>{{ Math.round(value) }}%</strong>
                  </template>
                </v-progress-linear>
              </div>
            </template>

            <!-- Pillars -->
            <template v-slot:item.pillar_count="{ item }">
              <v-chip size="small" variant="outlined">
                {{ item.pillar_count }} Saeulen
              </v-chip>
            </template>

            <!-- Sentences -->
            <template v-slot:item.total_sentences="{ item }">
              <div class="text-center">
                <div class="text-subtitle-2 font-weight-bold">
                  {{ item.total_sentences || 0 }}
                </div>
                <div class="text-caption text-medium-emphasis">Saetze</div>
              </div>
            </template>

            <!-- Created At -->
            <template v-slot:item.created_at="{ item }">
              {{ formatDate(item.created_at) }}
            </template>

            <!-- Actions -->
            <template v-slot:item.actions="{ item }">
              <div class="d-flex gap-1">
                <v-tooltip text="Details anzeigen" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-eye"
                      size="small"
                      variant="text"
                      @click.stop="navigateToAnalysis(null, { item })"
                    ></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip v-if="item.status === 'completed'" text="Ergebnisse anzeigen" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-chart-box"
                      size="small"
                      variant="text"
                      color="success"
                      @click.stop="navigateToResults(item.id)"
                    ></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip v-if="item.status === 'pending'" text="Starten" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-play"
                      size="small"
                      variant="text"
                      color="primary"
                      @click.stop="startAnalysis(item.id)"
                      :loading="starting === item.id"
                    ></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="Loeschen" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-delete"
                      size="small"
                      variant="text"
                      color="error"
                      @click.stop="confirmDelete(item)"
                    ></v-btn>
                  </template>
                </v-tooltip>
              </div>
            </template>

            <!-- Empty State -->
            <template v-slot:no-data>
              <div class="text-center py-8">
                <v-icon size="64" color="grey-lighten-1">mdi-chart-bar</v-icon>
                <div class="text-h6 mt-4 text-medium-emphasis">Keine Analysen gefunden</div>
                <div class="text-body-2 text-medium-emphasis mb-4">
                  Erstellen Sie Ihre erste OnCoCo Analyse, um zu beginnen
                </div>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="navigateToConfig">
                  Neue Analyse erstellen
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5">
          <v-icon class="mr-2" color="error">mdi-alert-circle</v-icon>
          Analyse loeschen?
        </v-card-title>
        <v-card-text>
          Moechten Sie die Analyse <strong>{{ deleteItem?.name }}</strong> wirklich loeschen?
          Diese Aktion kann nicht rueckgaengig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" variant="flat" @click="deleteAnalysis" :loading="deleting">
            Loeschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

// State
const analyses = ref([]);
const loading = ref(false);
const statusFilter = ref('all');
const deleteDialog = ref(false);
const deleteItem = ref(null);
const deleting = ref(false);
const starting = ref(null);
const syncing = ref(false);

const modelInfo = ref({
  model: {},
  labels: {}
});
const pillarStatus = ref({
  pillars: {}
});
const labelCount = ref(68);

// Table Headers
const headers = [
  { title: 'Analyse Name', key: 'name', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Fortschritt', key: 'progress', sortable: true },
  { title: 'Saeulen', key: 'pillar_count', sortable: true },
  { title: 'Saetze', key: 'total_sentences', sortable: true },
  { title: 'Erstellt am', key: 'created_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'center' }
];

// Computed Stats
const totalAnalyses = computed(() => analyses.value.length);
const completedAnalyses = computed(() =>
  analyses.value.filter(a => a.status === 'completed').length
);
const runningAnalyses = computed(() =>
  analyses.value.filter(a => a.status === 'running').length
);

// Filtered Analyses
const filteredAnalyses = computed(() => {
  if (statusFilter.value === 'all') {
    return analyses.value;
  }
  return analyses.value.filter(a => a.status === statusFilter.value);
});

// Load Model Info
const loadModelInfo = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/info`);
    modelInfo.value = response.data;
    labelCount.value = response.data.labels?.total || 68;
  } catch (error) {
    console.error('Error loading model info:', error);
  }
};

// Load Pillar Status
const loadPillarStatus = async () => {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/pillars`);
    pillarStatus.value = response.data;
  } catch (error) {
    console.error('Error loading pillar status:', error);
  }
};

// Load Analyses
const loadAnalyses = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses`);
    analyses.value = response.data;
  } catch (error) {
    console.error('Error loading analyses:', error);
  } finally {
    loading.value = false;
  }
};

// Sync Pillars
const syncPillars = async () => {
  syncing.value = true;
  try {
    await axios.post(`${import.meta.env.VITE_API_BASE_URL}/api/oncoco/pillars/sync`, {
      pillars: [1, 3, 5]
    });
    await loadPillarStatus();
  } catch (error) {
    console.error('Error syncing pillars:', error);
  } finally {
    syncing.value = false;
  }
};

// Start Analysis
const startAnalysis = async (analysisId) => {
  starting.value = analysisId;
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${analysisId}/start`,
      {},
      { headers: { 'Content-Type': 'application/json' } }
    );
    await loadAnalyses();
  } catch (error) {
    console.error('Error starting analysis:', error);
  } finally {
    starting.value = null;
  }
};

// Navigation
const navigateToConfig = () => {
  router.push({ name: 'OnCoCoConfig' });
};

const navigateToAnalysis = (event, row) => {
  const item = row?.item || row;
  if (item?.id) {
    router.push({ name: 'OnCoCoResults', params: { id: item.id } });
  }
};

const navigateToResults = (analysisId) => {
  router.push({ name: 'OnCoCoResults', params: { id: analysisId } });
};

// Delete Analysis
const confirmDelete = (item) => {
  deleteItem.value = item;
  deleteDialog.value = true;
};

const deleteAnalysis = async () => {
  deleting.value = true;
  try {
    await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${deleteItem.value.id}`
    );
    await loadAnalyses();
    deleteDialog.value = false;
    deleteItem.value = null;
  } catch (error) {
    console.error('Error deleting analysis:', error);
  } finally {
    deleting.value = false;
  }
};

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

const getPillarColor = (pillar) => {
  if (pillar.db_thread_count > 0) return 'success';
  if (pillar.gitlab_status === 'available') return 'warning';
  return 'grey';
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

// Lifecycle
onMounted(() => {
  loadModelInfo();
  loadPillarStatus();
  loadAnalyses();
});
</script>

<style scoped>
.oncoco-overview {
  max-width: 1400px;
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

.analyses-table :deep(tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.analyses-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
