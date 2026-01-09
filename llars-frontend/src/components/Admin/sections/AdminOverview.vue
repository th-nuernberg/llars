<template>
  <div class="admin-overview">
    <!-- Row 1: Stats Cards -->
    <LSkeleton v-if="isLoading('stats')" type="stat-card" :count="4" />
    <div v-else class="stats-row">
      <LStatCard
        v-for="stat in stats"
        :key="stat.title"
        :value="stat.value"
        :label="stat.title"
        :icon="stat.icon"
        :color="stat.color"
        size="sm"
      />
    </div>

    <!-- Row 2: Health Bar -->
    <SystemHealthBar @navigate="navigateToSection" class="health-bar" />

    <!-- Row 3: Main Content (Activities + Quick Actions) -->
    <div class="main-row">
      <!-- Recent Activity -->
      <div class="activity-panel">
        <div class="panel-header">
          <LIcon size="18" class="mr-2">mdi-clock-outline</LIcon>
          <span class="panel-title">Letzte Aktivitäten</span>
          <!-- Legend -->
          <div class="activity-legend">
            <LTooltip v-for="legend in activityLegend" :key="legend.type" :text="legend.label">
              <div class="legend-dot" :style="{ backgroundColor: legend.color }" />
            </LTooltip>
          </div>
        </div>
        <div class="panel-content">
          <LSkeleton v-if="isLoading('activities')" type="activity-list" :count="5" />
          <div v-else-if="recentActivities.length > 0" class="activity-list">
            <div
              v-for="(activity, index) in recentActivities"
              :key="index"
              class="activity-item activity-item--clickable"
              @click="openActivityDetail(activity)"
            >
              <div class="activity-icon" :style="{ backgroundColor: activity.color }">
                <LIcon size="16" color="white">{{ activity.icon }}</LIcon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-meta">{{ activity.subtitle }}</div>
              </div>
              <LTag :variant="activity.variant" size="sm" class="activity-time">{{ activity.time }}</LTag>
            </div>
          </div>
          <div v-else class="empty-state-sm">
            <LIcon size="32" class="text-medium-emphasis">mdi-information-outline</LIcon>
            <span class="text-medium-emphasis">Keine Aktivitäten</span>
          </div>
        </div>
      </div>

      <!-- Activity Detail Dialog -->
      <v-dialog v-model="activityDialog" max-width="500">
        <v-card v-if="selectedActivity" class="activity-detail-card">
          <v-card-title class="d-flex align-center pa-4">
            <div class="activity-detail-icon" :style="{ backgroundColor: selectedActivity.color }">
              <LIcon size="24" color="white">{{ selectedActivity.icon }}</LIcon>
            </div>
            <div class="ml-3">
              <div class="text-subtitle-1 font-weight-bold">{{ selectedActivity.categoryLabel }}</div>
              <div class="text-caption text-medium-emphasis">{{ selectedActivity.time }}</div>
            </div>
            <v-spacer />
            <v-btn icon variant="text" size="small" @click="activityDialog = false">
              <LIcon>mdi-close</LIcon>
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-4">
            <div class="detail-row">
              <span class="detail-label">Ereignis</span>
              <span class="detail-value">{{ selectedActivity.title }}</span>
            </div>
            <div v-if="selectedActivity.username" class="detail-row">
              <span class="detail-label">Benutzer</span>
              <LTag variant="info" size="sm">{{ selectedActivity.username }}</LTag>
            </div>
            <div v-if="selectedActivity.eventType" class="detail-row">
              <span class="detail-label">Typ</span>
              <LTag :variant="selectedActivity.variant" size="sm">{{ selectedActivity.eventType }}</LTag>
            </div>
            <div v-if="selectedActivity.severity" class="detail-row">
              <span class="detail-label">Schwere</span>
              <LTag :variant="getSeverityVariant(selectedActivity.severity)" size="sm">{{ selectedActivity.severity }}</LTag>
            </div>
            <div v-if="selectedActivity.entityType" class="detail-row">
              <span class="detail-label">Entität</span>
              <span class="detail-value">{{ selectedActivity.entityType }}{{ selectedActivity.entityId ? `: ${selectedActivity.entityId}` : '' }}</span>
            </div>
            <div v-if="selectedActivity.fullTime" class="detail-row">
              <span class="detail-label">Zeitpunkt</span>
              <span class="detail-value">{{ selectedActivity.fullTime }}</span>
            </div>
          </v-card-text>
          <v-divider />
          <v-card-actions class="pa-3">
            <LBtn variant="text" prepend-icon="mdi-open-in-new" @click="goToSystemEvents">
              Alle Events anzeigen
            </LBtn>
            <v-spacer />
            <LBtn variant="secondary" @click="activityDialog = false">Schließen</LBtn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- Quick Actions -->
      <div class="actions-panel">
        <div class="panel-header">
          <LIcon size="18" class="mr-2">mdi-lightning-bolt</LIcon>
          <span class="panel-title">Schnellaktionen</span>
        </div>
        <div class="panel-content">
          <div class="quick-actions-grid">
            <div
              v-for="action in quickActions"
              :key="action.title"
              class="quick-action-btn"
              @click="action.action"
            >
              <LIcon size="20">{{ action.icon }}</LIcon>
              <span>{{ action.shortTitle || action.title }}</span>
            </div>
          </div>
          <!-- Warnings inline -->
          <div v-if="warnings.length > 0" class="warnings-section">
            <v-alert
              v-for="(warning, index) in warnings"
              :key="index"
              :type="warning.type"
              variant="tonal"
              density="compact"
              class="warning-alert"
            >
              {{ warning.message }}
            </v-alert>
          </div>
        </div>
      </div>
    </div>

    <!-- Row 4: Scenarios -->
    <div class="scenarios-panel">
      <div class="panel-header">
        <LIcon size="18" class="mr-2">mdi-clipboard-list</LIcon>
        <span class="panel-title">Aktive Szenarien</span>
        <LBtn variant="text" size="small" append-icon="mdi-arrow-right" @click="$parent.$parent.activeSection = 'scenarios'">
          Alle
        </LBtn>
      </div>
      <div class="panel-content">
        <LSkeleton v-if="isLoading('scenarios')" type="table" :count="3" :columns="4" />
        <div v-else-if="activeScenarios.length > 0" class="scenarios-table-wrapper">
          <table class="scenarios-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Typ</th>
                <th>Fortschritt</th>
                <th>Enddatum</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in activeScenarios" :key="item.id">
                <td>
                  <div class="d-flex align-center">
                    <LIcon :color="getTypeColor(item.function_type_name)" size="16" class="mr-2">
                      {{ getTypeIcon(item.function_type_name) }}
                    </LIcon>
                    <span class="scenario-name">{{ item.name }}</span>
                  </div>
                </td>
                <td>
                  <LTag :variant="getTypeVariant(item.function_type_name)" size="sm">
                    {{ getFunctionTypeName(item.function_type_name) }}
                  </LTag>
                </td>
                <td>
                  <div class="progress-cell">
                    <v-progress-linear
                      :model-value="item.progress || 0"
                      height="6"
                      rounded
                      color="primary"
                      class="progress-bar"
                    />
                    <span class="progress-label">{{ Math.round(item.progress || 0) }}%</span>
                  </div>
                </td>
                <td>
                  <LTag :variant="isExpiringSoon(item.end_date) ? 'warning' : 'gray'" size="sm">
                    {{ formatDate(item.end_date) }}
                  </LTag>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state-sm">
          <LIcon size="32" class="text-medium-emphasis">mdi-clipboard-outline</LIcon>
          <span class="text-medium-emphasis">Keine aktiven Szenarien</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { getAnalyticsConfig } from '@/plugins/llars-metrics';
import SystemHealthBar from './SystemHealth/SystemHealthBar.vue';

const router = useRouter();

const { isLoading, setLoading, withLoading } = useSkeletonLoading(['stats', 'activities', 'scenarios']);

// Stats data
const stats = ref([
  { title: 'Benutzer', value: '0', icon: 'mdi-account-group', color: '#b0ca97' },
  { title: 'Aktive Szenarien', value: '0', icon: 'mdi-clipboard-check', color: '#98d4bb' },
  { title: 'RAG Dokumente', value: '0', icon: 'mdi-file-document-multiple', color: '#a8c5e2' },
  { title: 'Abschlussrate', value: '0%', icon: 'mdi-chart-line', color: '#e8c87a' },
]);

// Recent activities
const recentActivities = ref([]);

// Activity dialog
const activityDialog = ref(false);
const selectedActivity = ref(null);

// Activity legend for header
const activityLegend = [
  { type: 'auth', label: 'Login/Logout', color: '#4CAF50' },
  { type: 'chatbot', label: 'Chatbot', color: '#9C27B0' },
  { type: 'scenario', label: 'Szenarien', color: '#2196F3' },
  { type: 'rag', label: 'RAG/Dokumente', color: '#00BCD4' },
  { type: 'error', label: 'Fehler', color: '#f44336' },
  { type: 'system', label: 'System', color: '#607D8B' },
];

// Warnings
const warnings = ref([]);

// Active scenarios
const activeScenarios = ref([]);

// Table headers
const scenarioHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Typ', key: 'function_type_name', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Fortschritt', key: 'progress', sortable: true, width: '180px' },
  { title: 'Enddatum', key: 'end_date', sortable: true },
];

const buildMatomoBaseUrl = () => {
  const configured = String(getAnalyticsConfig()?.matomo_base_url || '/analytics/').trim();
  if (configured.startsWith('http://') || configured.startsWith('https://')) {
    return configured.endsWith('/') ? configured : `${configured}/`;
  }
  if (configured.startsWith('/')) {
    return configured.endsWith('/') ? configured : `${configured}/`;
  }
  return `/${configured.endsWith('/') ? configured : `${configured}/`}`;
};

const openMatomoSso = () => {
  const baseUrl = buildMatomoBaseUrl();
  window.open(`${baseUrl}index.php?module=RebelOIDC&action=signIn&provider=oidc`, '_blank', 'noopener');
};

// Quick actions
const quickActions = [
  { title: 'Matomo Analytics öffnen', shortTitle: 'Analytics', icon: 'mdi-chart-bar', action: openMatomoSso },
  { title: 'Neues Szenario erstellen', shortTitle: 'Szenario', icon: 'mdi-plus-circle', action: () => navigateToSection('scenarios') },
  { title: 'Benutzer verwalten', shortTitle: 'Benutzer', icon: 'mdi-account-cog', action: () => navigateToSection('users') },
  { title: 'Dokument hochladen', shortTitle: 'RAG Docs', icon: 'mdi-upload', action: () => navigateToSection('rag') },
];

// Navigate to a specific admin section via router query param
function navigateToSection(section) {
  router.push({ path: '/admin', query: { tab: section } });
}

// Open activity detail dialog
function openActivityDetail(activity) {
  selectedActivity.value = activity;
  activityDialog.value = true;
}

// Navigate to system events tab
function goToSystemEvents() {
  activityDialog.value = false;
  navigateToSection('system');
}

// Get severity variant for tag
const getSeverityVariant = (severity) => {
  const variants = {
    'error': 'danger',
    'warning': 'warning',
    'info': 'info',
    'debug': 'gray'
  };
  return variants[severity] || 'gray';
};

// Get category label for event type
const getCategoryLabel = (eventType) => {
  const categories = {
    'auth_login': 'Authentifizierung',
    'auth_logout': 'Authentifizierung',
    'scenario_created': 'Szenario',
    'scenario_updated': 'Szenario',
    'scenario_deleted': 'Szenario',
    'chatbot_created': 'Chatbot',
    'chatbot_updated': 'Chatbot',
    'chatbot_message': 'Chatbot',
    'rag_upload': 'RAG Dokumente',
    'rag_delete': 'RAG Dokumente',
    'user_created': 'Benutzerverwaltung',
    'permission_changed': 'Berechtigungen',
    'system_startup': 'System',
    'llm_request': 'LLM Anfrage',
    'error': 'Fehler',
  };
  return categories[eventType] || 'System Event';
};

// Helper functions
const getFunctionTypeName = (type) => {
  const typeMap = {
    'mail_rating': 'Verlaufsbewertung',
    'rating': 'Rating',
    'ranking': 'Ranking'
  };
  return typeMap[type] || type;
};

const getTypeIcon = (type) => {
  const iconMap = {
    'mail_rating': 'mdi-email-check',
    'rating': 'mdi-star',
    'ranking': 'mdi-format-list-numbered'
  };
  return iconMap[type] || 'mdi-clipboard-outline';
};

const getTypeColor = (type) => {
  const colorMap = {
    'mail_rating': 'accent',
    'rating': 'warning',
    'ranking': 'info'
  };
  return colorMap[type] || 'grey';
};

const getTypeVariant = (type) => {
  const variantMap = {
    'mail_rating': 'accent',
    'rating': 'warning',
    'ranking': 'info'
  };
  return variantMap[type] || 'gray';
};

const getStatusVariant = (status) => {
  const variantMap = {
    'aktiv': 'success',
    'beendet': 'gray',
    'ausstehend': 'warning'
  };
  return variantMap[status] || 'danger';
};

const isExpiringSoon = (dateString) => {
  if (!dateString) return false;
  const endDate = new Date(dateString);
  const daysUntilEnd = (endDate - new Date()) / (1000 * 60 * 60 * 24);
  return daysUntilEnd <= 7 && daysUntilEnd > 0;
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

// Helper to get icon, color and variant for event type
const getEventStyle = (eventType, severity) => {
  const eventStyles = {
    'auth_login': { icon: 'mdi-login', color: '#4CAF50', variant: 'success' },
    'auth_logout': { icon: 'mdi-logout', color: '#9E9E9E', variant: 'gray' },
    'scenario_created': { icon: 'mdi-clipboard-plus', color: '#2196F3', variant: 'info' },
    'scenario_updated': { icon: 'mdi-clipboard-edit', color: '#FF9800', variant: 'warning' },
    'scenario_deleted': { icon: 'mdi-clipboard-remove', color: '#f44336', variant: 'danger' },
    'chatbot_created': { icon: 'mdi-robot', color: '#9C27B0', variant: 'accent' },
    'chatbot_updated': { icon: 'mdi-robot-outline', color: '#9C27B0', variant: 'accent' },
    'chatbot_message': { icon: 'mdi-message-text', color: '#9C27B0', variant: 'accent' },
    'rag_upload': { icon: 'mdi-file-upload', color: '#00BCD4', variant: 'info' },
    'rag_delete': { icon: 'mdi-file-remove', color: '#f44336', variant: 'danger' },
    'user_created': { icon: 'mdi-account-plus', color: '#4CAF50', variant: 'success' },
    'permission_changed': { icon: 'mdi-shield-account', color: '#FF9800', variant: 'warning' },
    'system_startup': { icon: 'mdi-power', color: '#4CAF50', variant: 'success' },
    'llm_request': { icon: 'mdi-brain', color: '#E91E63', variant: 'accent' },
    'error': { icon: 'mdi-alert-circle', color: '#f44336', variant: 'danger' },
  };

  if (eventStyles[eventType]) return eventStyles[eventType];
  if (severity === 'error') return { icon: 'mdi-alert-circle', color: '#f44336', variant: 'danger' };
  if (severity === 'warning') return { icon: 'mdi-alert', color: '#FF9800', variant: 'warning' };
  return { icon: 'mdi-information-outline', color: '#607D8B', variant: 'gray' };
};

// Helper to format relative time
const formatRelativeTime = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Gerade eben';
  if (diffMins < 60) return `vor ${diffMins} Min.`;
  if (diffHours < 24) return `vor ${diffHours} Std.`;
  if (diffDays < 7) return `vor ${diffDays} Tag${diffDays > 1 ? 'en' : ''}`;
  return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
};

// Fetch dashboard data - parallel API calls for faster loading
const fetchDashboardData = async () => {
  // Start all loading states
  setLoading('stats', true);
  setLoading('activities', true);
  setLoading('scenarios', true);

  // Execute all API calls in parallel
  const [ragResult, permResult, scenariosResult, eventsResult] = await Promise.allSettled([
    axios.get('/api/rag/stats'),
    axios.get('/api/permissions/roles'),
    axios.get('/api/admin/scenarios'),
    axios.get('/api/admin/system/events', { params: { limit: 10 } })
  ]);

  // Process RAG stats
  if (ragResult.status === 'fulfilled') {
    const totalDocs = ragResult.value.data.total_documents
      || ragResult.value.data.stats?.documents?.total
      || 0;
    stats.value[2].value = totalDocs.toString();
  } else {
    console.error('Error fetching RAG stats:', ragResult.reason);
  }

  // Process permissions/users
  if (permResult.status === 'fulfilled') {
    stats.value[0].value = '-';
  } else {
    console.error('Error fetching user stats:', permResult.reason);
  }

  setLoading('stats', false);

  // Process system events for recent activities
  if (eventsResult.status === 'fulfilled') {
    const events = eventsResult.value.data?.events || [];
    recentActivities.value = events.slice(0, 8).map(event => {
      const style = getEventStyle(event.event_type, event.severity);
      return {
        // Display fields
        icon: style.icon,
        color: style.color,
        variant: style.variant,
        title: event.message || event.event_type,
        subtitle: event.username ? `von ${event.username}` : (event.entity_type || ''),
        time: formatRelativeTime(event.created_at),
        // Detail fields for popup
        eventType: event.event_type,
        categoryLabel: getCategoryLabel(event.event_type),
        username: event.username,
        severity: event.severity,
        entityType: event.entity_type,
        entityId: event.entity_id,
        fullTime: new Date(event.created_at).toLocaleString('de-DE', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        }),
        rawEvent: event
      };
    });
  } else {
    console.error('Error fetching system events:', eventsResult.reason);
  }

  setLoading('activities', false);

  // Process scenarios
  if (scenariosResult.status === 'fulfilled') {
    const scenarios = scenariosResult.value.data.scenarios || [];

    const activeCount = scenarios.filter(s => s.status === 'aktiv').length;
    stats.value[1].value = activeCount.toString();

    activeScenarios.value = scenarios.filter(s => s.status === 'aktiv').slice(0, 5);

    const expiringScenarios = scenarios.filter(s => {
      if (!s.end_date || s.status !== 'aktiv') return false;
      const endDate = new Date(s.end_date);
      const daysUntilEnd = (endDate - new Date()) / (1000 * 60 * 60 * 24);
      return daysUntilEnd <= 7 && daysUntilEnd > 0;
    });

    if (expiringScenarios.length > 0) {
      warnings.value.push({
        type: 'warning',
        message: `${expiringScenarios.length} Szenario(s) laufen in den nächsten 7 Tagen ab`
      });
    }
  } else {
    console.error('Error fetching scenarios:', scenariosResult.reason);
  }

  setLoading('scenarios', false);
};

onMounted(() => {
  fetchDashboardData();
});
</script>

<style scoped>
/* Viewport-filling layout */
.admin-overview {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
  overflow: hidden;
}

/* Row 1: Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  flex-shrink: 0;
}

/* Row 2: Health Bar */
.health-bar {
  flex-shrink: 0;
  margin: 0 !important;
}

/* Row 3: Main Content */
.main-row {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

/* Row 4: Scenarios */
.scenarios-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Panel Base Styles */
.activity-panel,
.actions-panel {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-height: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.875rem;
  font-weight: 600;
  flex: 1;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* Activity List */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  transition: background 0.15s ease;
}

.activity-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-meta {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.activity-time {
  flex-shrink: 0;
}

.activity-item--clickable {
  cursor: pointer;
}

.activity-item--clickable:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

/* Activity Legend */
.activity-legend {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  cursor: help;
  transition: transform 0.15s ease;
}

.legend-dot:hover {
  transform: scale(1.3);
}

/* Activity Detail Dialog */
.activity-detail-card {
  border-radius: 12px !important;
}

.activity-detail-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-weight: 500;
}

.detail-value {
  font-size: 0.85rem;
  font-weight: 500;
  text-align: right;
  max-width: 60%;
  word-break: break-word;
}

/* Quick Actions Grid */
.quick-actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 8px;
  border-radius: 8px;
  background: rgba(var(--v-theme-primary), 0.05);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

.quick-action-btn:hover {
  background: rgba(var(--v-theme-primary), 0.12);
  transform: translateY(-2px);
}

.quick-action-btn span {
  font-size: 0.7rem;
  font-weight: 500;
}

/* Warnings */
.warnings-section {
  margin-top: 8px;
}

.warning-alert {
  font-size: 0.75rem;
}

/* Scenarios Table */
.scenarios-table-wrapper {
  overflow-x: auto;
}

.scenarios-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.scenarios-table th,
.scenarios-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.scenarios-table th {
  font-weight: 600;
  font-size: 0.7rem;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.scenarios-table tbody tr:hover {
  background: rgba(var(--v-theme-primary), 0.03);
}

.scenario-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.progress-bar {
  flex: 1;
}

.progress-label {
  font-size: 0.75rem;
  font-weight: 500;
  min-width: 35px;
  text-align: right;
}

/* Empty State */
.empty-state-sm {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  text-align: center;
  font-size: 0.8rem;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(4, 1fr);
  }

  .main-row {
    grid-template-columns: 1fr 240px;
  }
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .main-row {
    grid-template-columns: 1fr;
  }
}
</style>
