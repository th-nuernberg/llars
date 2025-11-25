<template>
  <div class="admin-overview">
    <!-- Stats Cards Row -->
    <v-row>
      <v-col cols="12" sm="6" lg="3" v-for="stat in stats" :key="stat.title">
        <v-card class="stat-card" :loading="loading">
          <v-card-text class="d-flex align-center">
            <v-avatar :color="stat.color" size="56" class="mr-4">
              <v-icon :icon="stat.icon" color="white" size="28"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">{{ stat.value }}</div>
              <div class="text-subtitle-2 text-medium-emphasis">{{ stat.title }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Row -->
    <v-row class="mt-4">
      <!-- Recent Activity -->
      <v-col cols="12" lg="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-clock-outline</v-icon>
            Letzte Aktivitäten
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-list lines="two" v-if="recentActivities.length > 0">
              <v-list-item
                v-for="(activity, index) in recentActivities"
                :key="index"
                :prepend-icon="activity.icon"
              >
                <v-list-item-title>{{ activity.title }}</v-list-item-title>
                <v-list-item-subtitle>{{ activity.subtitle }}</v-list-item-subtitle>
                <template v-slot:append>
                  <span class="text-caption text-medium-emphasis">{{ activity.time }}</span>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-information-outline</v-icon>
              <div>Keine kürzlichen Aktivitäten</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Quick Actions -->
      <v-col cols="12" lg="4">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-lightning-bolt</v-icon>
            Schnellaktionen
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="action in quickActions"
                :key="action.title"
                :prepend-icon="action.icon"
                @click="action.action"
                class="quick-action-item"
                rounded
              >
                <v-list-item-title>{{ action.title }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Warnings Card -->
        <v-card class="mt-4" v-if="warnings.length > 0">
          <v-card-title class="d-flex align-center text-warning">
            <v-icon class="mr-2" color="warning">mdi-alert</v-icon>
            Hinweise
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
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
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Scenarios Overview -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-clipboard-list</v-icon>
            Aktive Szenarien
            <v-spacer></v-spacer>
            <v-btn variant="text" color="primary" @click="$parent.$parent.activeSection = 'scenarios'">
              Alle anzeigen
              <v-icon end>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <v-table v-if="activeScenarios.length > 0">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Typ</th>
                  <th>Status</th>
                  <th>Fortschritt</th>
                  <th>Enddatum</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="scenario in activeScenarios" :key="scenario.scenario_id">
                  <td>{{ scenario.name }}</td>
                  <td>
                    <v-chip size="small" variant="outlined">
                      {{ getFunctionTypeName(scenario.function_type_name) }}
                    </v-chip>
                  </td>
                  <td>
                    <v-chip :color="getStatusColor(scenario.status)" size="small">
                      {{ scenario.status }}
                    </v-chip>
                  </td>
                  <td style="width: 200px;">
                    <v-progress-linear
                      :model-value="scenario.progress || 0"
                      height="20"
                      rounded
                      color="primary"
                    >
                      <template v-slot:default="{ value }">
                        <strong>{{ Math.round(value) }}%</strong>
                      </template>
                    </v-progress-linear>
                  </td>
                  <td>{{ formatDate(scenario.end_date) }}</td>
                </tr>
              </tbody>
            </v-table>
            <div v-else class="text-center py-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-clipboard-outline</v-icon>
              <div>Keine aktiven Szenarien</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const loading = ref(true);

// Stats data
const stats = ref([
  { title: 'Benutzer', value: '0', icon: 'mdi-account-group', color: 'primary' },
  { title: 'Aktive Szenarien', value: '0', icon: 'mdi-clipboard-check', color: 'success' },
  { title: 'RAG Dokumente', value: '0', icon: 'mdi-file-document-multiple', color: 'info' },
  { title: 'Abschlussrate', value: '0%', icon: 'mdi-chart-line', color: 'warning' },
]);

// Recent activities
const recentActivities = ref([]);

// Warnings
const warnings = ref([]);

// Active scenarios
const activeScenarios = ref([]);

// Quick actions
const quickActions = [
  {
    title: 'Neues Szenario erstellen',
    icon: 'mdi-plus-circle',
    action: () => { /* Will be handled by parent */ }
  },
  {
    title: 'Benutzer verwalten',
    icon: 'mdi-account-cog',
    action: () => { /* Will be handled by parent */ }
  },
  {
    title: 'Dokument hochladen',
    icon: 'mdi-upload',
    action: () => { /* Will be handled by parent */ }
  },
];

// Helper functions
const getFunctionTypeName = (type) => {
  const typeMap = {
    'mail_rating': 'Verlaufsbewertung',
    'rating': 'Rating',
    'ranking': 'Ranking'
  };
  return typeMap[type] || type;
};

const getStatusColor = (status) => {
  const colorMap = {
    'aktiv': 'success',
    'beendet': 'grey',
    'ausstehend': 'warning'
  };
  return colorMap[status] || 'error';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

// Fetch dashboard data
const fetchDashboardData = async () => {
  loading.value = true;

  try {
    // Fetch scenarios
    const scenariosResponse = await axios.get('/api/admin/scenarios');
    const scenarios = scenariosResponse.data.scenarios || [];

    // Calculate stats
    const activeCount = scenarios.filter(s => s.status === 'aktiv').length;
    stats.value[1].value = activeCount.toString();

    // Filter active scenarios for display
    activeScenarios.value = scenarios.filter(s => s.status === 'aktiv').slice(0, 5);

    // Check for warnings
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

  } catch (error) {
    console.error('Error fetching scenarios:', error);
  }

  try {
    // Fetch RAG stats
    const ragResponse = await axios.get('/api/rag/stats');
    // Handle both old format (total_documents) and new format (stats.documents.total)
    const totalDocs = ragResponse.data.total_documents
      || ragResponse.data.stats?.documents?.total
      || 0;
    stats.value[2].value = totalDocs.toString();
  } catch (error) {
    console.error('Error fetching RAG stats:', error);
  }

  try {
    // Fetch user count (from permissions API)
    const permResponse = await axios.get('/api/permissions/roles');
    // We don't have a direct user count endpoint, so we'll estimate
    stats.value[0].value = '-';
  } catch (error) {
    console.error('Error fetching user stats:', error);
  }

  loading.value = false;
};

onMounted(() => {
  fetchDashboardData();
});
</script>

<style scoped>
.stat-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.quick-action-item {
  cursor: pointer;
  margin: 4px 0;
  transition: background-color 0.2s ease;
}

.quick-action-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>
