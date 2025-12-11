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
        @click="forceRefresh"
        title="Status neu laden"
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
        <v-btn
          class="mt-2"
          size="small"
          variant="outlined"
          @click="showTokenDialog = true"
        >
          Token konfigurieren
        </v-btn>
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
                {{ pillar.db_thread_count }} Threads
              </v-chip>

              <!-- Last Sync -->
              <v-chip
                v-if="pillar.last_sync"
                size="small"
                variant="outlined"
                class="status-chip"
              >
                <v-icon start size="14">mdi-clock-outline</v-icon>
                {{ formatDate(pillar.last_sync) }}
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

    <!-- Token Configuration Dialog -->
    <v-dialog v-model="showTokenDialog" max-width="500">
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-gitlab</v-icon>
          GitLab Token konfigurieren
        </v-card-title>
        <v-card-text>
          <p class="mb-4 text-body-2">
            Um auf das KIA-Repository zuzugreifen, benötigen Sie einen Personal Access Token
            mit <code>read_repository</code> Berechtigung.
          </p>
          <v-text-field
            v-model="gitlabToken"
            label="GitLab Personal Access Token"
            type="password"
            variant="outlined"
            prepend-inner-icon="mdi-key"
            hint="Token von git.informatik.fh-nuernberg.de"
            persistent-hint
          ></v-text-field>
          <v-btn
            variant="text"
            color="primary"
            size="small"
            href="https://git.informatik.fh-nuernberg.de/-/user_settings/personal_access_tokens"
            target="_blank"
            class="mt-2"
          >
            <v-icon start>mdi-open-in-new</v-icon>
            Token erstellen
          </v-btn>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showTokenDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            :loading="savingToken"
            @click="saveToken"
          >
            Speichern & Testen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useKIAStatusCache } from '@/composables/useKIAStatusCache';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

// Use cached KIA status
const { state: kiaState, fetchStatus, updateAfterSync, clearCache } = useKIAStatusCache();

// Local state
const loading = ref(true);
const checking = ref(false);
const syncing = ref({});
const syncingAll = ref(false);
const lastSyncResult = ref(null);

// Reactive bindings to cache state
const pillars = computed(() => kiaState.pillars);
const totalThreads = computed(() => kiaState.totalThreads);
const gitlabConnected = computed(() => kiaState.gitlabConnected);

// Token Dialog
const showTokenDialog = ref(false);
const gitlabToken = ref('');
const savingToken = ref(false);

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

const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const checkStatus = async (force = false) => {
  checking.value = true;
  try {
    const result = await fetchStatus(force);
    if (result.fromCache) {
      console.log('[KIADataSync] Using cached status');
    }
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
  }
};

const syncPillar = async (pillarNumber) => {
  syncing.value[pillarNumber] = true;
  // Update local state for UI feedback
  if (kiaState.pillars[pillarNumber]) {
    kiaState.pillars[pillarNumber].gitlab_status = 'syncing';
  }

  try {
    const response = await axios.post(`${API_BASE}/api/judge/kia/sync/${pillarNumber}`);

    lastSyncResult.value = {
      success: response.data.success,
      message: response.data.success
        ? `Säule ${pillarNumber} erfolgreich synchronisiert`
        : `Fehler bei Säule ${pillarNumber}`,
      details: response.data.success
        ? `${response.data.threads_created} erstellt, ${response.data.threads_updated} aktualisiert`
        : response.data.errors?.join(', ') || 'Unbekannter Fehler'
    };

    // Force refresh status and clear cache
    clearCache();
    await checkStatus(true);
  } catch (error) {
    console.error('Error syncing pillar:', error);
    lastSyncResult.value = {
      success: false,
      message: `Fehler bei Säule ${pillarNumber}`,
      details: error.response?.data?.error || error.message
    };
    if (kiaState.pillars[pillarNumber]) {
      kiaState.pillars[pillarNumber].gitlab_status = 'error';
    }
  } finally {
    syncing.value[pillarNumber] = false;
  }
};

const syncAll = async () => {
  syncingAll.value = true;

  try {
    const response = await axios.post(`${API_BASE}/api/judge/kia/sync`, {});

    lastSyncResult.value = {
      success: response.data.total_success > 0,
      message: `Synchronisation abgeschlossen`,
      details: `${response.data.total_success} Säulen erfolgreich, ` +
        `${response.data.total_threads_created} Threads erstellt, ` +
        `${response.data.total_threads_updated} aktualisiert`
    };

    // Force refresh status and clear cache
    clearCache();
    await checkStatus(true);
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

const saveToken = async () => {
  if (!gitlabToken.value.trim()) return;

  savingToken.value = true;
  try {
    const response = await axios.post(`${API_BASE}/api/judge/kia/config`, {
      gitlab_token: gitlabToken.value
    });

    if (response.data.success) {
      showTokenDialog.value = false;
      gitlabToken.value = '';
      lastSyncResult.value = {
        success: true,
        message: 'GitLab Token erfolgreich konfiguriert',
        details: 'Verbindung zum Repository hergestellt'
      };
      // Force refresh status after token change
      clearCache();
      await checkStatus(true);
    } else {
      lastSyncResult.value = {
        success: false,
        message: 'Token-Konfiguration fehlgeschlagen',
        details: response.data.message
      };
    }
  } catch (error) {
    console.error('Error saving token:', error);
    lastSyncResult.value = {
      success: false,
      message: 'Fehler beim Speichern des Tokens',
      details: error.response?.data?.error || error.message
    };
  } finally {
    savingToken.value = false;
  }
};

// Force refresh when refresh button is clicked
const forceRefresh = () => checkStatus(true);

// Lifecycle
onMounted(() => {
  checkStatus(); // Uses cache if available
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

code {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.875em;
  color: rgb(var(--v-theme-on-surface));
}
</style>
