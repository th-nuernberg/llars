<template>
  <div class="admin-overview">
    <!-- Stats Cards Row -->
    <div class="stats-grid">
      <template v-if="isLoading('stats')">
        <v-skeleton-loader
          v-for="n in 4"
          :key="'skeleton-stat-' + n"
          type="card"
          height="100"
        />
      </template>
      <template v-else>
        <LCard
          v-for="stat in stats"
          :key="stat.title"
          :icon="stat.icon"
          :color="stat.color"
          :title="stat.value"
          :subtitle="stat.title"
          :avatar-size="48"
          class="stat-card"
        />
      </template>
    </div>

    <!-- System Health Bar -->
    <SystemHealthBar @navigate="navigateToSection" class="mb-4" />

    <!-- Main Content Row -->
    <div class="content-grid">
      <!-- Recent Activity -->
      <LCard class="activity-card">
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2">mdi-clock-outline</LIcon>
            <span class="text-h6">Letzte Aktivitäten</span>
          </div>
        </template>

        <v-list lines="two" v-if="recentActivities.length > 0" class="bg-transparent">
          <v-list-item
            v-for="(activity, index) in recentActivities"
            :key="index"
            :prepend-icon="activity.icon"
            class="activity-item"
          >
            <v-list-item-title>{{ activity.title }}</v-list-item-title>
            <v-list-item-subtitle>{{ activity.subtitle }}</v-list-item-subtitle>
            <template v-slot:append>
              <LTag variant="gray" size="sm">{{ activity.time }}</LTag>
            </template>
          </v-list-item>
        </v-list>
        <div v-else class="empty-state">
          <LIcon size="48" class="mb-2 text-medium-emphasis">mdi-information-outline</LIcon>
          <div class="text-medium-emphasis">Keine kürzlichen Aktivitäten</div>
        </div>
      </LCard>

      <!-- Right Column: Quick Actions + Warnings -->
      <div class="side-column">
        <!-- Quick Actions -->
        <LCard class="quick-actions-card">
          <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2">mdi-lightning-bolt</LIcon>
              <span class="text-h6">Schnellaktionen</span>
            </div>
          </template>

          <div class="quick-actions-list">
            <div
              v-for="action in quickActions"
              :key="action.title"
              class="quick-action-item"
              @click="action.action"
            >
              <LIcon :icon="action.icon" class="mr-3" />
              <span>{{ action.title }}</span>
              <LIcon class="ml-auto" size="small">mdi-chevron-right</LIcon>
            </div>
          </div>
        </LCard>

        <!-- Warnings Card -->
        <LCard v-if="warnings.length > 0" color="#e8c87a" class="warnings-card">
          <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2" color="warning">mdi-alert</LIcon>
              <span class="text-h6">Hinweise</span>
            </div>
          </template>

          <v-alert
            v-for="(warning, index) in warnings"
            :key="index"
            :type="warning.type"
            variant="tonal"
            density="compact"
            class="mb-2"
          >
            {{ warning.message }}
          </v-alert>
        </LCard>
      </div>
    </div>

    <!-- Scenarios Overview -->
    <LCard class="scenarios-card">
      <template #header>
        <div class="d-flex align-center justify-space-between w-100">
          <div class="d-flex align-center">
            <LIcon class="mr-2">mdi-clipboard-list</LIcon>
            <span class="text-h6">Aktive Szenarien</span>
          </div>
          <LBtn variant="text" append-icon="mdi-arrow-right" @click="$parent.$parent.activeSection = 'scenarios'">
            Alle anzeigen
          </LBtn>
        </div>
      </template>

      <v-skeleton-loader v-if="isLoading('scenarios')" type="table" />

      <v-data-table
        v-else-if="activeScenarios.length > 0"
        :headers="scenarioHeaders"
        :items="activeScenarios"
        :items-per-page="5"
        density="comfortable"
        class="scenarios-table"
      >
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <LIcon :color="getTypeColor(item.function_type_name)" class="mr-2" size="small">
              {{ getTypeIcon(item.function_type_name) }}
            </LIcon>
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <template v-slot:item.function_type_name="{ item }">
          <LTag :variant="getTypeVariant(item.function_type_name)" size="sm">
            {{ getFunctionTypeName(item.function_type_name) }}
          </LTag>
        </template>

        <template v-slot:item.status="{ item }">
          <LTag :variant="getStatusVariant(item.status)" size="sm">
            {{ item.status }}
          </LTag>
        </template>

        <template v-slot:item.progress="{ item }">
          <div class="progress-cell">
            <v-progress-linear
              :model-value="item.progress || 0"
              height="8"
              rounded
              color="primary"
            />
            <span class="progress-label">{{ Math.round(item.progress || 0) }}%</span>
          </div>
        </template>

        <template v-slot:item.end_date="{ item }">
          <LTag
            :variant="isExpiringSoon(item.end_date) ? 'warning' : 'gray'"
            size="sm"
          >
            {{ formatDate(item.end_date) }}
          </LTag>
        </template>
      </v-data-table>

      <div v-else class="empty-state">
        <LIcon size="48" class="mb-2 text-medium-emphasis">mdi-clipboard-outline</LIcon>
        <div class="text-medium-emphasis">Keine aktiven Szenarien</div>
      </div>
    </LCard>
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
  { title: 'Matomo Analytics öffnen', icon: 'mdi-chart-bar', action: openMatomoSso },
  { title: 'Neues Szenario erstellen', icon: 'mdi-plus-circle', action: () => {} },
  { title: 'Benutzer verwalten', icon: 'mdi-account-cog', action: () => {} },
  { title: 'Dokument hochladen', icon: 'mdi-upload', action: () => {} },
];

// Navigate to a specific admin section via router query param
function navigateToSection(section) {
  router.push({ path: '/admin', query: { tab: section } });
}

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

// Fetch dashboard data - parallel API calls for faster loading
const fetchDashboardData = async () => {
  // Start all loading states
  setLoading('stats', true);
  setLoading('scenarios', true);

  // Execute all API calls in parallel
  const [ragResult, permResult, scenariosResult] = await Promise.allSettled([
    axios.get('/api/rag/stats'),
    axios.get('/api/permissions/roles'),
    axios.get('/api/admin/scenarios')
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
.admin-overview {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

.side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Activity Card */
.activity-card {
  min-height: 300px;
}

.activity-item {
  border-radius: 8px;
  margin-bottom: 4px;
}

.activity-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

/* Quick Actions */
.quick-actions-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quick-action-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgb(var(--v-theme-on-surface));
}

.quick-action-item:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  transform: translateX(4px);
}

/* Scenarios Card */
.scenarios-card {
  min-height: 200px;
}

.scenarios-table {
  background: transparent !important;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-label {
  font-size: 0.85rem;
  font-weight: 500;
  min-width: 40px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
}

/* Utilities */
.w-100 {
  width: 100%;
}
</style>
