<template>
  <v-card class="kia-sync-card" variant="outlined">
    <!-- Header -->
    <div class="kia-header">
      <div class="d-flex align-center">
        <div class="gitlab-icon-wrapper">
          <v-icon size="20" color="white">mdi-gitlab</v-icon>
        </div>
        <div class="ml-3">
          <div class="text-subtitle-2 font-weight-bold">KIA Datenquellen</div>
          <div class="text-caption text-medium-emphasis">
            <span v-if="gitlabConnected" class="text-success">
              <v-icon size="12" class="mr-1">mdi-check-circle</v-icon>Verbunden
            </span>
            <span v-else class="text-warning">
              <v-icon size="12" class="mr-1">mdi-alert</v-icon>Token erforderlich
            </span>
          </div>
        </div>
      </div>
      <div class="d-flex align-center ga-1">
        <v-chip v-if="totalThreads > 0" size="small" color="primary" variant="flat">
          {{ totalThreads }} Threads
        </v-chip>
        <v-btn
          icon
          variant="text"
          size="x-small"
          :loading="checking"
          @click="forceRefresh"
        >
          <v-icon size="18">mdi-refresh</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- Pillars Grid -->
    <div class="pillars-grid" v-if="!loading">
      <div
        v-for="(pillar, num) in pillars"
        :key="num"
        class="pillar-item"
        :class="{ 'pillar-available': pillar.gitlab_status === 'available' }"
      >
        <div class="pillar-badge" :style="{ backgroundColor: getPillarColor(num) }">
          {{ num }}
        </div>
        <div class="pillar-info">
          <div class="pillar-name">{{ pillar.name }}</div>
          <div class="pillar-stats">
            <span v-if="pillar.db_thread_count > 0" class="stat-item">
              <v-icon size="12">mdi-database</v-icon>
              {{ pillar.db_thread_count }}
            </span>
            <span v-if="pillar.gitlab_file_count > 0" class="stat-item">
              <v-icon size="12">mdi-file-document-multiple</v-icon>
              {{ pillar.gitlab_file_count }}
            </span>
            <span v-if="pillar.gitlab_status !== 'available'" class="stat-item text-medium-emphasis">
              {{ getStatusText(pillar.gitlab_status) }}
            </span>
          </div>
        </div>
        <v-btn
          v-if="pillar.gitlab_status === 'available'"
          icon
          variant="text"
          size="x-small"
          :loading="syncing[num]"
          @click="syncPillar(num)"
          class="sync-btn"
        >
          <v-icon size="16">mdi-sync</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="pillars-grid">
      <v-skeleton-loader v-for="n in 5" :key="n" type="list-item" class="pillar-skeleton" />
    </div>

    <!-- Footer Actions -->
    <div class="kia-footer" v-if="gitlabConnected && hasAvailablePillars">
      <v-btn
        size="small"
        color="primary"
        variant="tonal"
        :loading="syncingAll"
        prepend-icon="mdi-cloud-sync"
        @click="syncAll"
      >
        Alle synchronisieren
      </v-btn>
    </div>

    <!-- Token Config (shown if not connected) -->
    <div class="kia-footer" v-else-if="!gitlabConnected && !loading">
      <v-btn
        size="small"
        variant="outlined"
        prepend-icon="mdi-key"
        @click="showTokenDialog = true"
      >
        Token konfigurieren
      </v-btn>
    </div>

    <!-- Sync Result -->
    <v-slide-y-transition>
      <v-alert
        v-if="lastSyncResult"
        :type="lastSyncResult.success ? 'success' : 'error'"
        variant="tonal"
        density="compact"
        class="ma-2 mt-0"
        closable
        @click:close="lastSyncResult = null"
      >
        <span class="text-caption">{{ lastSyncResult.message }}</span>
      </v-alert>
    </v-slide-y-transition>

    <!-- Token Dialog -->
    <v-dialog v-model="showTokenDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="orange">mdi-gitlab</v-icon>
          GitLab Token
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="gitlabToken"
            label="Personal Access Token"
            type="password"
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-key"
            hint="Mit read_repository Berechtigung"
            persistent-hint
          />
        </v-card-text>
        <v-card-actions>
          <v-btn
            variant="text"
            size="small"
            href="https://git.informatik.fh-nuernberg.de/-/user_settings/personal_access_tokens"
            target="_blank"
          >
            <v-icon start size="16">mdi-open-in-new</v-icon>
            Token erstellen
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="showTokenDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="savingToken" @click="saveToken">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useKIAStatusCache } from '@/composables/useKIAStatusCache';

const emit = defineEmits(['loaded']);
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const { state: kiaState, fetchStatus, clearCache } = useKIAStatusCache();

const loading = ref(true);
const checking = ref(false);
const syncing = ref({});
const syncingAll = ref(false);
const lastSyncResult = ref(null);
const showTokenDialog = ref(false);
const gitlabToken = ref('');
const savingToken = ref(false);

const pillars = computed(() => kiaState.pillars);
const totalThreads = computed(() => kiaState.totalThreads);
const gitlabConnected = computed(() => kiaState.gitlabConnected);

const hasAvailablePillars = computed(() => {
  return Object.values(pillars.value).some(p => p.gitlab_status === 'available');
});

const pillarColors = {
  1: '#f44336', 2: '#ff9800', 3: '#4caf50', 4: '#2196f3', 5: '#9c27b0'
};

const getPillarColor = (num) => pillarColors[num] || '#9e9e9e';

const getStatusText = (status) => {
  const texts = {
    'available': 'Bereit',
    'not_found': 'Nicht vorhanden',
    'error': 'Fehler',
    'syncing': 'Lädt...'
  };
  return texts[status] || status;
};

const checkStatus = async (force = false) => {
  checking.value = true;
  try {
    await fetchStatus(force);
  } catch (error) {
    if (error.response?.status !== 401) {
      lastSyncResult.value = {
        success: false,
        message: error.response?.data?.error || 'Status-Abfrage fehlgeschlagen'
      };
    }
  } finally {
    checking.value = false;
    loading.value = false;
    emit('loaded');
  }
};

const syncPillar = async (num) => {
  syncing.value[num] = true;
  try {
    const response = await axios.post(`${API_BASE}/api/judge/kia/sync/${num}`);
    lastSyncResult.value = {
      success: response.data.success,
      message: response.data.success
        ? `Säule ${num}: ${response.data.threads_created} Threads erstellt`
        : `Säule ${num}: ${response.data.errors?.[0] || 'Fehler'}`
    };
    clearCache();
    await checkStatus(true);
  } catch (error) {
    lastSyncResult.value = {
      success: false,
      message: `Säule ${num}: ${error.response?.data?.error || error.message}`
    };
  } finally {
    syncing.value[num] = false;
  }
};

const syncAll = async () => {
  syncingAll.value = true;
  try {
    const response = await axios.post(`${API_BASE}/api/judge/kia/sync`, {});
    lastSyncResult.value = {
      success: response.data.total_success > 0,
      message: `${response.data.total_threads_created} Threads erstellt`
    };
    clearCache();
    await checkStatus(true);
  } catch (error) {
    lastSyncResult.value = {
      success: false,
      message: error.response?.data?.error || 'Sync fehlgeschlagen'
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
      clearCache();
      await checkStatus(true);
    }
  } catch (error) {
    lastSyncResult.value = {
      success: false,
      message: error.response?.data?.error || 'Token-Speicherung fehlgeschlagen'
    };
  } finally {
    savingToken.value = false;
  }
};

const forceRefresh = () => checkStatus(true);

onMounted(() => checkStatus());
</script>

<style scoped>
.kia-sync-card {
  border-radius: 12px;
  overflow: hidden;
}

.kia-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(252, 109, 38, 0.08) 0%, rgba(226, 67, 41, 0.08) 100%);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.gitlab-icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #fc6d26 0%, #e24329 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.pillars-grid {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
}

.pillar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  transition: background 0.2s;
}

.pillar-item:hover {
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.pillar-item.pillar-available {
  background: rgba(76, 175, 80, 0.08);
}

.pillar-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.pillar-info {
  flex: 1;
  min-width: 0;
}

.pillar-name {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pillar-stats {
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.sync-btn {
  opacity: 0.7;
  transition: opacity 0.2s;
}

.pillar-item:hover .sync-btn {
  opacity: 1;
}

.kia-footer {
  padding: 8px 16px 12px;
  display: flex;
  justify-content: flex-end;
}

.pillar-skeleton {
  height: 44px;
  border-radius: 8px;
}
</style>
