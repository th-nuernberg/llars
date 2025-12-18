<template>
  <div class="judge-overview-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="text-h5 font-weight-bold">LLM-as-Judge</h1>
        <p class="text-caption text-medium-emphasis mb-0">
          Automatisierte Bewertung von Prompt-Säulen mit KI
        </p>
      </div>
      <v-spacer></v-spacer>
      <LBtn
        variant="primary"
        prepend-icon="mdi-plus"
        @click="navigateToConfig"
      >
        Neue Session
      </LBtn>
    </div>

    <!-- Stats Row -->
    <div class="stats-row">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <v-skeleton-loader v-if="loadingStats" type="text" width="60"></v-skeleton-loader>
        <template v-else>
          <v-avatar :color="stat.color" size="40" class="stat-avatar">
            <v-icon :icon="stat.icon" color="white" size="20"></v-icon>
          </v-avatar>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </template>
      </div>
    </div>

    <!-- Main Content -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Sessions Table -->
      <div class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2" size="small">mdi-format-list-bulleted</v-icon>
          <span class="font-weight-medium">Meine Sessions</span>
          <v-spacer></v-spacer>
          <v-chip-group v-model="statusFilter" mandatory density="compact" class="filter-chips">
            <v-chip value="all" size="x-small" variant="tonal">Alle</v-chip>
            <v-chip value="running" size="x-small" variant="tonal" color="info">Laufend</v-chip>
            <v-chip value="completed" size="x-small" variant="tonal" color="success">Fertig</v-chip>
            <v-chip value="failed" size="x-small" variant="tonal" color="error">Fehler</v-chip>
          </v-chip-group>
          <v-btn
            icon="mdi-refresh"
            variant="text"
            size="small"
            @click="loadSessions"
            :loading="loading"
          ></v-btn>
        </div>
        <div class="panel-content">
          <v-skeleton-loader
            v-if="loadingTable"
            type="table-heading, table-tbody"
          ></v-skeleton-loader>
          <template v-else>
            <v-progress-linear v-if="loading && !loadingTable" indeterminate></v-progress-linear>

            <!-- Sessions List -->
            <div v-if="filteredSessions.length === 0" class="empty-state">
              <v-icon size="48" color="grey-lighten-1">mdi-folder-open</v-icon>
              <div class="text-body-1 mt-2 text-medium-emphasis">Keine Sessions</div>
              <LBtn
                variant="primary"
                prepend-icon="mdi-plus"
                class="mt-2"
                @click="navigateToConfig"
              >
                Neue Session
              </LBtn>
            </div>

            <div v-else class="sessions-list">
              <div
                v-for="session in filteredSessions"
                :key="session.session_id"
                class="session-item"
                @click="navigateToSession(session)"
              >
                <div class="session-main">
                  <div class="session-name">{{ session.session_name }}</div>
                  <div class="session-meta">
                    <LTag :variant="getStatusVariant(session.status)" size="sm">
                      {{ getStatusText(session.status) }}
                    </LTag>
                    <span class="session-date">{{ formatDate(session.created_at) }}</span>
                  </div>
                </div>
                <div class="session-progress">
                  <div class="progress-label">
                    {{ session.completed_comparisons || 0 }}/{{ session.total_comparisons || 0 }}
                  </div>
                  <v-progress-linear
                    :model-value="session.progress || 0"
                    height="6"
                    rounded
                    :color="session.progress === 100 ? 'success' : 'primary'"
                  ></v-progress-linear>
                </div>
                <div class="session-actions">
                  <v-btn
                    icon="mdi-eye"
                    size="x-small"
                    variant="text"
                    @click.stop="navigateToSession(session)"
                  ></v-btn>
                  <v-btn
                    v-if="session.status === 'completed'"
                    icon="mdi-chart-box"
                    size="x-small"
                    variant="text"
                    color="success"
                    @click.stop="navigateToResults(session.session_id)"
                  ></v-btn>
                  <v-btn
                    icon="mdi-delete"
                    size="x-small"
                    variant="text"
                    color="error"
                    @click.stop="confirmDelete(session)"
                  ></v-btn>
                </div>
              </div>
            </div>
          </template>
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

      <!-- Right Panel: KIA Data Sync -->
      <div class="right-panel" :style="rightPanelStyle()">
        <div class="panel-header">
          <v-icon class="mr-2" size="small">mdi-database-sync</v-icon>
          <span class="font-weight-medium">KIA Daten-Sync</span>
        </div>
        <div class="panel-content">
          <v-skeleton-loader
            v-if="loadingKIA"
            type="card"
            height="200"
          ></v-skeleton-loader>
          <KIADataSync v-else @loaded="loadingKIA = false" />
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-subtitle-1">
          <v-icon class="mr-2" color="error" size="small">mdi-alert-circle</v-icon>
          Session löschen?
        </v-card-title>
        <v-card-text class="text-body-2">
          <strong>{{ deleteItem?.session_name }}</strong> wird unwiderruflich gelöscht.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <LBtn variant="cancel" @click="deleteDialog = false">Abbrechen</LBtn>
          <LBtn variant="danger" @click="deleteSession" :loading="deleting">
            Löschen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { io } from 'socket.io-client';
import { usePanelResize } from '@/composables/usePanelResize';
import KIADataSync from './KIADataSync.vue';

const router = useRouter();
const socket = ref(null);

// Panel Resize
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 65,
  minLeftPercent: 50,
  maxLeftPercent: 80,
  storageKey: 'judge-overview-panel-width'
});

// State
const sessions = ref([]);
const loading = ref(false);
const statusFilter = ref('all');
const deleteDialog = ref(false);
const deleteItem = ref(null);
const deleting = ref(false);

// Skeleton Loading States
const loadingStats = ref(true);
const loadingTable = ref(true);
const loadingKIA = ref(true);

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

const stats = computed(() => [
  { label: 'Gesamt', value: totalSessions.value, icon: 'mdi-folder-multiple', color: 'primary' },
  { label: 'Fertig', value: completedSessions.value, icon: 'mdi-check-circle', color: 'success' },
  { label: 'Laufend', value: runningSessions.value, icon: 'mdi-play-circle', color: 'info' },
  { label: 'Wartend', value: queuedSessions.value, icon: 'mdi-clock-outline', color: 'warning' }
]);

// Filtered Sessions
const filteredSessions = computed(() => {
  if (statusFilter.value === 'all') {
    return sessions.value;
  }
  return sessions.value.filter(s => s.status === statusFilter.value);
});

// Load Sessions
const loadSessions = async (isInitial = false) => {
  loading.value = true;
  if (isInitial) {
    loadingTable.value = true;
    loadingStats.value = true;
  }
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions`);
    sessions.value = response.data;
  } catch (error) {
    console.error('Error loading sessions:', error);
  } finally {
    loading.value = false;
    loadingTable.value = false;
    loadingStats.value = false;
  }
};

// Navigation
const navigateToConfig = () => {
  router.push({ name: 'JudgeConfig' });
};

const navigateToSession = (session) => {
  if (session?.session_id) {
    router.push({ name: 'JudgeSession', params: { id: session.session_id } });
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

const getStatusText = (status) => {
  const texts = {
    created: 'Erstellt',
    queued: 'Wartend',
    running: 'Läuft',
    paused: 'Pausiert',
    completed: 'Fertig',
    failed: 'Fehler'
  };
  return texts[status] || status;
};

const getStatusVariant = (status) => {
  const variants = {
    created: 'gray',
    queued: 'warning',
    running: 'info',
    paused: 'warning',
    completed: 'success',
    failed: 'danger'
  };
  return variants[status] || 'gray';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// WebSocket Setup for Live Updates
const setupSocket = () => {
  const socketUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
  const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true';
  const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling'];

  socket.value = io(socketUrl, {
    path: '/socket.io',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket,
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
  });

  socket.value.on('connect', () => {
    console.log('[JudgeOverview] Socket connected');
    // Join overview room to receive updates for all sessions
    socket.value.emit('judge:join_overview');
  });

  socket.value.on('disconnect', () => {
    console.log('[JudgeOverview] Socket disconnected');
  });

  // Listen for progress updates from any session
  socket.value.on('judge:progress', (data) => {
    console.log('[JudgeOverview] Progress update:', data);
    updateSessionProgress(data.session_id, data.completed, data.total, data.percent);
  });

  // Listen for comparison completions (also updates progress)
  socket.value.on('judge:comparison_complete', (data) => {
    console.log('[JudgeOverview] Comparison complete:', data);
    if (data.completed !== undefined && data.total !== undefined) {
      const percent = data.total > 0 ? (data.completed / data.total) * 100 : 0;
      updateSessionProgress(data.session_id, data.completed, data.total, percent);
    }
  });

  // Listen for session status changes
  socket.value.on('judge:session_complete', (data) => {
    console.log('[JudgeOverview] Session complete:', data);
    updateSessionStatus(data.session_id, 'completed');
    if (data.total !== undefined) {
      updateSessionProgress(data.session_id, data.total, data.total, 100);
    }
  });

  // Listen for session start
  socket.value.on('judge:session_started', (data) => {
    console.log('[JudgeOverview] Session started:', data);
    updateSessionStatus(data.session_id, 'running');
  });

  // Listen for session pause
  socket.value.on('judge:session_paused', (data) => {
    console.log('[JudgeOverview] Session paused:', data);
    updateSessionStatus(data.session_id, 'paused');
  });
};

const cleanupSocket = () => {
  if (socket.value) {
    socket.value.emit('judge:leave_overview');
    socket.value.disconnect();
    socket.value = null;
  }
};

// Update session progress in local state
const updateSessionProgress = (sessionId, completed, total, percent) => {
  const session = sessions.value.find(s => s.session_id === sessionId);
  if (session) {
    session.completed_comparisons = completed;
    session.total_comparisons = total;
    session.progress = percent;
  }
};

// Update session status in local state
const updateSessionStatus = (sessionId, status) => {
  const session = sessions.value.find(s => s.session_id === sessionId);
  if (session) {
    session.status = status;
  }
};

// Lifecycle
onMounted(() => {
  loadSessions(true);
  setupSocket();
  setTimeout(() => {
    loadingKIA.value = false;
  }, 100);
});

onUnmounted(() => {
  cleanupSocket();
});
</script>

<style scoped>
.judge-overview-page {
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
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
}

.header-content h1 {
  margin: 0;
  line-height: 1.2;
}

/* Stats Row */
.stats-row {
  flex-shrink: 0;
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.stat-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.stat-avatar {
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-top: 2px;
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
  gap: 8px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.filter-chips {
  margin: 0;
}

.filter-chips :deep(.v-chip) {
  margin: 0 2px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
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

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
}

/* Sessions List */
.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
}

.session-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  transform: translateX(4px);
}

.session-main {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-weight: 600;
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgb(var(--v-theme-on-surface));
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.session-date {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.session-progress {
  width: 100px;
  flex-shrink: 0;
}

.progress-label {
  font-size: 0.7rem;
  text-align: right;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 2px;
}

.session-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}
</style>
