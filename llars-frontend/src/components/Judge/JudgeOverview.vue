<template>
  <v-container class="judge-overview">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <div>
            <h1 class="text-h4 font-weight-bold">LLM-as-Judge</h1>
            <p class="text-subtitle-1 text-medium-emphasis">
              Automatisierte Bewertung von Prompt-Säulen mit KI
            </p>
          </div>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            size="large"
            @click="navigateToConfig"
          >
            Neue Session erstellen
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
              <v-icon icon="mdi-folder-multiple" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ totalSessions }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Gesamt Sessions</div>
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
              <div class="text-h4 font-weight-bold">{{ completedSessions }}</div>
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
              <div class="text-h4 font-weight-bold">{{ runningSessions }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">Laufend</div>
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
              <div class="text-h4 font-weight-bold">{{ queuedSessions }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">In Warteschlange</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- KIA Data Sync -->
    <v-row class="mb-4">
      <v-col cols="12">
        <KIADataSync />
      </v-col>
    </v-row>

    <!-- Sessions Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
            Meine Judge Sessions
            <v-spacer></v-spacer>
            <!-- Filter Chips -->
            <v-chip-group v-model="statusFilter" mandatory class="mr-2">
              <v-chip value="all" size="small">Alle</v-chip>
              <v-chip value="running" size="small" color="info">Laufend</v-chip>
              <v-chip value="completed" size="small" color="success">Abgeschlossen</v-chip>
              <v-chip value="failed" size="small" color="error">Fehlgeschlagen</v-chip>
            </v-chip-group>
            <v-btn
              icon="mdi-refresh"
              variant="text"
              @click="loadSessions"
              :loading="loading"
            ></v-btn>
          </v-card-title>
          <v-divider></v-divider>

          <!-- Loading State -->
          <v-progress-linear v-if="loading" indeterminate></v-progress-linear>

          <!-- Sessions Data Table -->
          <v-data-table
            :headers="headers"
            :items="filteredSessions"
            :loading="loading"
            :items-per-page="10"
            class="sessions-table"
            @click:row="navigateToSession"
          >
            <!-- Session Name -->
            <template v-slot:item.session_name="{ item }">
              <div class="font-weight-medium">{{ item.session_name }}</div>
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
                {{ item.pillar_count }} Säulen
              </v-chip>
            </template>

            <!-- Comparisons -->
            <template v-slot:item.total_comparisons="{ item }">
              <div class="text-center">
                <div class="text-subtitle-2 font-weight-bold">
                  {{ item.completed_comparisons || 0 }} / {{ item.total_comparisons || 0 }}
                </div>
                <div class="text-caption text-medium-emphasis">Vergleiche</div>
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
                      @click.stop="navigateToSession(null, { item })"
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
                      @click.stop="navigateToResults(item.session_id)"
                    ></v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="Löschen" location="top">
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
                <v-icon size="64" color="grey-lighten-1">mdi-folder-open</v-icon>
                <div class="text-h6 mt-4 text-medium-emphasis">Keine Sessions gefunden</div>
                <div class="text-body-2 text-medium-emphasis mb-4">
                  Erstellen Sie Ihre erste Judge Session, um zu beginnen
                </div>
                <v-btn color="primary" prepend-icon="mdi-plus" @click="navigateToConfig">
                  Neue Session erstellen
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
          Session löschen?
        </v-card-title>
        <v-card-text>
          Möchten Sie die Session <strong>{{ deleteItem?.session_name }}</strong> wirklich löschen?
          Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" variant="flat" @click="deleteSession" :loading="deleting">
            Löschen
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
import KIADataSync from './KIADataSync.vue';

const router = useRouter();

// State
const sessions = ref([]);
const loading = ref(false);
const statusFilter = ref('all');
const deleteDialog = ref(false);
const deleteItem = ref(null);
const deleting = ref(false);

// Table Headers
const headers = [
  { title: 'Session Name', key: 'session_name', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Fortschritt', key: 'progress', sortable: true },
  { title: 'Säulen', key: 'pillar_count', sortable: true },
  { title: 'Vergleiche', key: 'total_comparisons', sortable: true },
  { title: 'Erstellt am', key: 'created_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'center' }
];

// Computed Stats
const totalSessions = computed(() => sessions.value.length);
const completedSessions = computed(() =>
  sessions.value.filter(s => s.status === 'completed').length
);
const runningSessions = computed(() =>
  sessions.value.filter(s => s.status === 'running').length
);
const queuedSessions = computed(() =>
  sessions.value.filter(s => s.status === 'queued').length
);

// Filtered Sessions
const filteredSessions = computed(() => {
  if (statusFilter.value === 'all') {
    return sessions.value;
  }
  return sessions.value.filter(s => s.status === statusFilter.value);
});

// Load Sessions
const loadSessions = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions`);
    sessions.value = response.data;
  } catch (error) {
    console.error('Error loading sessions:', error);
  } finally {
    loading.value = false;
  }
};

// Navigation
const navigateToConfig = () => {
  router.push({ name: 'JudgeConfig' });
};

const navigateToSession = (event, row) => {
  // Handle both @click:row event signature and direct button click
  const item = row?.item || row;
  if (item?.session_id) {
    router.push({ name: 'JudgeSession', params: { id: item.session_id } });
  } else {
    console.error('Missing session_id in item:', item);
  }
};

const navigateToResults = (sessionId) => {
  router.push({ name: 'JudgeResults', params: { id: sessionId } });
};

// Delete Session
const confirmDelete = (item) => {
  deleteItem.value = item;
  deleteDialog.value = true;
};

const deleteSession = async () => {
  deleting.value = true;
  try {
    await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${deleteItem.value.session_id}`
    );
    await loadSessions();
    deleteDialog.value = false;
    deleteItem.value = null;
  } catch (error) {
    console.error('Error deleting session:', error);
  } finally {
    deleting.value = false;
  }
};

// Utility Functions
const getStatusColor = (status) => {
  const colors = {
    created: 'grey',
    queued: 'warning',
    running: 'info',
    paused: 'orange',
    completed: 'success',
    failed: 'error'
  };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = {
    created: 'mdi-file-document',
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    paused: 'mdi-pause-circle',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  };
  return icons[status] || 'mdi-help-circle';
};

const getStatusText = (status) => {
  const texts = {
    created: 'Erstellt',
    queued: 'In Warteschlange',
    running: 'Läuft',
    paused: 'Pausiert',
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

// Lifecycle
onMounted(() => {
  loadSessions();
});
</script>

<style scoped>
.judge-overview {
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

.sessions-table :deep(tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.sessions-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
