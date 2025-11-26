<template>
  <v-card>
    <v-card-title class="d-flex align-center justify-space-between">
      <div class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-database-sync</v-icon>
        KIA Daten Synchronisation
      </div>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        :loading="checking"
        @click="checkStatus"
        title="Status aktualisieren"
      ></v-btn>
    </v-card-title>
    <v-divider></v-divider>

    <!-- GitLab Connection Status -->
    <v-card-text>
      <v-alert
        v-if="!gitlabConnected && !loading"
        type="warning"
        variant="tonal"
        class="mb-4"
      >
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-gitlab</v-icon>
          <div>
            <div class="font-weight-bold">GitLab Token erforderlich</div>
            <div class="text-caption">
              Um KIA-Daten aus dem Repository zu laden, benötigen Sie einen GitLab Personal Access Token.
            </div>
          </div>
        </div>
      </v-alert>

      <v-alert
        v-if="gitlabConnected"
        type="success"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        <div class="d-flex align-center">
          <v-icon class="mr-2">mdi-gitlab</v-icon>
          Mit GitLab verbunden
        </div>
      </v-alert>

      <!-- Pillar Status Grid -->
      <div class="text-subtitle-1 font-weight-bold mb-2">
        <v-icon class="mr-1">mdi-pillar</v-icon>
        Säulen-Status
      </div>

      <v-skeleton-loader v-if="loading" type="list-item@5"></v-skeleton-loader>

      <v-list v-else density="compact" class="pillar-list">
        <v-list-item
          v-for="(pillar, num) in pillars"
          :key="num"
          :class="{ 'pillar-available': pillar.gitlab_status === 'available' }"
        >
          <template v-slot:prepend>
            <v-avatar :color="getPillarColor(num)" size="36">
              {{ num }}
            </v-avatar>
          </template>

          <v-list-item-title class="font-weight-medium">
            {{ pillar.name }}
          </v-list-item-title>

          <v-list-item-subtitle class="pillar-subtitle">
            <div class="d-flex align-center flex-wrap ga-2 mt-1">
              <!-- GitLab Status -->
              <v-chip
                size="small"
                :color="getStatusColor(pillar.gitlab_status)"
                variant="flat"
                class="status-chip"
              >
                <v-icon start size="14">{{ getStatusIcon(pillar.gitlab_status) }}</v-icon>
                {{ getStatusText(pillar.gitlab_status) }}
                <span v-if="pillar.gitlab_file_count > 0" class="ml-1">
                  ({{ pillar.gitlab_file_count }} Dateien)
                </span>
              </v-chip>

              <!-- DB Status -->
              <v-chip
                size="small"
                :color="pillar.db_thread_count > 0 ? 'success' : 'grey'"
                variant="tonal"
                class="status-chip"
              >
                <v-icon start size="14">mdi-database</v-icon>
                {{ pillar.db_thread_count || 0 }} Threads
              </v-chip>

              <!-- Message Count -->
              <v-chip
                v-if="pillar.db_message_count > 0"
                size="small"
                variant="outlined"
                class="status-chip"
              >
                <v-icon start size="14">mdi-message-text</v-icon>
                {{ pillar.db_message_count }} Nachrichten
              </v-chip>
            </div>
          </v-list-item-subtitle>

          <template v-slot:append>
            <v-btn
              v-if="pillar.gitlab_status === 'available'"
              icon
              variant="text"
              size="small"
              :loading="syncing[num]"
              @click="syncPillar(num)"
              title="Diese Säule synchronisieren"
            >
              <v-icon>mdi-sync</v-icon>
            </v-btn>
            <v-tooltip v-else location="top">
              <template v-slot:activator="{ props }">
                <v-icon
                  v-bind="props"
                  color="grey"
                  size="small"
                >
                  mdi-information-outline
                </v-icon>
              </template>
              {{ pillar.error || 'Nicht verfügbar' }}
            </v-tooltip>
          </template>
        </v-list-item>
      </v-list>

      <!-- Summary -->
      <v-divider class="my-4"></v-divider>

      <div class="d-flex justify-space-between align-center">
        <div>
          <div class="text-caption text-medium-emphasis">Gesamt in Datenbank</div>
          <div class="text-h5 font-weight-bold">{{ totalThreads }} Threads</div>
        </div>

        <v-btn
          color="primary"
          :disabled="!hasAvailablePillars || syncingAll"
          :loading="syncingAll"
          prepend-icon="mdi-cloud-download"
          @click="syncAll"
        >
          Alle synchronisieren
        </v-btn>
      </div>

      <!-- Sync Results -->
      <v-expand-transition>
        <v-alert
          v-if="lastSyncResult"
          :type="lastSyncResult.success ? 'success' : 'error'"
          variant="tonal"
          class="mt-4"
          closable
          @click:close="lastSyncResult = null"
        >
          <div class="font-weight-bold">
            {{ lastSyncResult.message }}
          </div>
          <div v-if="lastSyncResult.details" class="text-caption mt-1">
            {{ lastSyncResult.details }}
          </div>
        </v-alert>
      </v-expand-transition>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Emit event when loaded
const emit = defineEmits(['loaded']);

// State
const loading = ref(true);
const checking = ref(false);
const pillars = ref({});
const totalThreads = ref(0);
const gitlabConnected = ref(false);
const syncing = ref({});
const syncingAll = ref(false);
const lastSyncResult = ref(null);

// Pillar colors
const pillarColors = {
  1: 'red',
  2: 'orange',
  3: 'green',
  4: 'blue',
  5: 'purple'
};

// Computed
const hasAvailablePillars = computed(() => {
  return Object.values(pillars.value).some(p => p.gitlab_status === 'available');
});

// Methods
const getPillarColor = (num) => pillarColors[num] || 'grey';

const getStatusColor = (status) => {
  switch (status) {
    case 'available': return 'success';
    case 'not_found': return 'grey';
    case 'error': return 'error';
    case 'syncing': return 'info';
    default: return 'grey';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'available': return 'mdi-check-circle';
    case 'not_found': return 'mdi-close-circle';
    case 'error': return 'mdi-alert-circle';
    case 'syncing': return 'mdi-sync';
    default: return 'mdi-help-circle';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'available': return 'Verfügbar';
    case 'not_found': return 'Nicht gefunden';
    case 'error': return 'Fehler';
    case 'syncing': return 'Synchronisiere...';
    default: return 'Unbekannt';
  }
};

const checkStatus = async () => {
  checking.value = true;
  try {
    const response = await axios.get(`${API_BASE}/api/oncoco/pillars`);
    pillars.value = response.data.pillars || {};
    totalThreads.value = response.data.total_threads || 0;
    gitlabConnected.value = response.data.gitlab_connected || false;
  } catch (error) {
    console.error('Error checking KIA status:', error);
    if (error.response?.status !== 401) {
      lastSyncResult.value = {
        success: false,
        message: 'Fehler beim Abrufen des Status',
        details: error.response?.data?.error || error.message
      };
    }
  } finally {
    checking.value = false;
    loading.value = false;
    emit('loaded');
  }
};

const syncPillar = async (pillarNumber) => {
  syncing.value[pillarNumber] = true;
  if (pillars.value[pillarNumber]) {
    pillars.value[pillarNumber].gitlab_status = 'syncing';
  }

  try {
    const response = await axios.post(`${API_BASE}/api/oncoco/pillars/sync`, {
      pillars: [parseInt(pillarNumber)]
    });

    const pillarResult = response.data.results?.[pillarNumber];

    lastSyncResult.value = {
      success: pillarResult?.success ?? response.data.success,
      message: pillarResult?.success
        ? `Säule ${pillarNumber} erfolgreich synchronisiert`
        : `Fehler bei Säule ${pillarNumber}`,
      details: pillarResult?.success
        ? `${pillarResult.threads_synced || 0} Threads synchronisiert`
        : pillarResult?.error || 'Unbekannter Fehler'
    };

    // Refresh status
    await checkStatus();
  } catch (error) {
    console.error('Error syncing pillar:', error);
    lastSyncResult.value = {
      success: false,
      message: `Fehler bei Säule ${pillarNumber}`,
      details: error.response?.data?.error || error.message
    };
    if (pillars.value[pillarNumber]) {
      pillars.value[pillarNumber].gitlab_status = 'error';
    }
  } finally {
    syncing.value[pillarNumber] = false;
  }
};

const syncAll = async () => {
  syncingAll.value = true;

  try {
    const response = await axios.post(`${API_BASE}/api/oncoco/pillars/sync`, {
      pillars: [1, 3, 5]
    });

    const totalSuccess = Object.values(response.data.results || {}).filter(r => r.success).length;
    const totalThreadsSynced = Object.values(response.data.results || {}).reduce((sum, r) => sum + (r.threads_synced || 0), 0);

    lastSyncResult.value = {
      success: totalSuccess > 0,
      message: `Synchronisation abgeschlossen`,
      details: `${totalSuccess} Säulen erfolgreich, ${totalThreadsSynced} Threads synchronisiert`
    };

    // Refresh status
    await checkStatus();
  } catch (error) {
    console.error('Error syncing all:', error);
    lastSyncResult.value = {
      success: false,
      message: 'Fehler bei der Synchronisation',
      details: error.response?.data?.error || error.message
    };
  } finally {
    syncingAll.value = false;
  }
};

// Lifecycle
onMounted(() => {
  checkStatus();
});
</script>

<style scoped>
.pillar-list {
  background: transparent;
}

.pillar-list :deep(.v-list-item) {
  margin-bottom: 8px;
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 12px 16px;
}

.pillar-list :deep(.v-list-item-title) {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 600;
  font-size: 1rem;
}

.pillar-list :deep(.v-list-item-subtitle) {
  color: rgba(var(--v-theme-on-surface), 0.7);
  opacity: 1;
  overflow: visible;
  white-space: normal;
  -webkit-line-clamp: unset;
}

.pillar-subtitle {
  margin-top: 4px;
}

.status-chip {
  font-size: 0.75rem;
  font-weight: 500;
}

.pillar-available {
  background: rgba(var(--v-theme-success), 0.1) !important;
}
</style>
