<template>
  <v-card class="kia-sync-card" variant="outlined">
    <!-- Header -->
    <div class="kia-header">
      <div class="d-flex align-center">
        <div class="gitlab-icon-wrapper">
          <LIcon size="20" color="white">mdi-gitlab</LIcon>
        </div>
        <div class="ml-3">
          <div class="text-subtitle-2 font-weight-bold">{{ $t('oncoco.kiaSync.title') }}</div>
          <div class="text-caption text-medium-emphasis">
            <span v-if="gitlabConnected" class="text-success">
              <LIcon size="12" class="mr-1">mdi-check-circle</LIcon>{{ $t('oncoco.kiaSync.connected') }}
            </span>
            <span v-else class="text-warning">
              <LIcon size="12" class="mr-1">mdi-alert</LIcon>{{ $t('oncoco.kiaSync.disconnected') }}
            </span>
          </div>
        </div>
      </div>
      <div class="d-flex align-center ga-1">
        <v-chip v-if="totalThreads > 0" size="small" color="primary" variant="flat">
          {{ $t('oncoco.kiaSync.threads', { count: totalThreads }) }}
        </v-chip>
        <v-btn
          icon
          variant="text"
          size="x-small"
          :loading="checking"
          @click="checkStatus"
        >
          <LIcon size="18">mdi-refresh</LIcon>
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
              <LIcon size="12">mdi-database</LIcon>
              {{ pillar.db_thread_count }}
            </span>
            <span v-if="pillar.gitlab_file_count > 0" class="stat-item">
              <LIcon size="12">mdi-file-document-multiple</LIcon>
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
          <LIcon size="16">mdi-sync</LIcon>
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
        {{ $t('oncoco.kiaSync.actions.syncAll') }}
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
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const emit = defineEmits(['loaded']);
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const { t } = useI18n();

const loading = ref(true);
const checking = ref(false);
const syncing = ref({});
const syncingAll = ref(false);
const lastSyncResult = ref(null);
const pillars = ref({});
const totalThreads = ref(0);
const gitlabConnected = ref(false);

const hasAvailablePillars = computed(() => {
  return Object.values(pillars.value).some(p => p.gitlab_status === 'available');
});

const pillarColors = {
  1: '#f44336', 2: '#ff9800', 3: '#4caf50', 4: '#2196f3', 5: '#9c27b0'
};

const getPillarColor = (num) => pillarColors[num] || '#9e9e9e';

const getStatusText = (status) => {
  const texts = {
    'available': t('oncoco.kiaSync.status.available'),
    'not_found': t('oncoco.kiaSync.status.notFound'),
    'error': t('oncoco.kiaSync.status.error'),
    'syncing': t('oncoco.kiaSync.status.syncing')
  };
  return texts[status] || status;
};

const checkStatus = async () => {
  checking.value = true;
  try {
    const response = await axios.get(`${API_BASE}/api/oncoco/pillars`);
    if (response.data) {
      pillars.value = response.data.pillars || {};
      totalThreads.value = response.data.total_threads || 0;
      gitlabConnected.value = response.data.gitlab_connected || false;
    }
  } catch (error) {
    if (error.response?.status !== 401) {
      lastSyncResult.value = {
        success: false,
        message: error.response?.data?.error || t('oncoco.kiaSync.errors.statusFailed')
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
    const response = await axios.post(`${API_BASE}/api/oncoco/pillars/sync`, {
      pillar: num
    });
    lastSyncResult.value = {
      success: response.data.success,
      message: response.data.success
        ? t('oncoco.kiaSync.messages.pillarSuccess', { id: num, count: response.data.threads_created || 0 })
        : t('oncoco.kiaSync.messages.pillarError', { id: num, message: response.data.errors?.[0] || t('oncoco.kiaSync.status.error') })
    };
    await checkStatus();
  } catch (error) {
    lastSyncResult.value = {
      success: false,
      message: t('oncoco.kiaSync.messages.pillarError', { id: num, message: error.response?.data?.error || error.message })
    };
  } finally {
    syncing.value[num] = false;
  }
};

const syncAll = async () => {
  syncingAll.value = true;
  try {
    const response = await axios.post(`${API_BASE}/api/oncoco/pillars/sync`, {});
    lastSyncResult.value = {
      success: response.data.total_success > 0,
      message: t('oncoco.kiaSync.messages.syncAll', { count: response.data.total_threads_created || 0 })
    };
    await checkStatus();
  } catch (error) {
    lastSyncResult.value = {
      success: false,
      message: error.response?.data?.error || t('oncoco.kiaSync.errors.syncFailed')
    };
  } finally {
    syncingAll.value = false;
  }
};

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
