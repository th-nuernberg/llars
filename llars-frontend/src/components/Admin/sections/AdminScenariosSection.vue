<template>
  <div class="admin-scenarios">
    <!-- Controls Row -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="searchQuery"
          label="Nach Namen suchen"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Status Filter"
          variant="outlined"
          density="comfortable"
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="typeFilter"
          :items="typeOptions"
          label="Typ Filter"
          variant="outlined"
          density="comfortable"
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <CreateScenarioDialog @scenarioCreated="fetchScenarios" />
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="success">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-check-circle</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ scenarioStats.aktiv }}</div>
              <div class="text-caption">Aktiv</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="warning">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-clock-outline</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ scenarioStats.ausstehend }}</div>
              <div class="text-caption">Ausstehend</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="grey">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-check-all</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ scenarioStats.beendet }}</div>
              <div class="text-caption">Beendet</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="6" md="3">
        <v-card variant="tonal" color="primary">
          <v-card-text class="d-flex align-center">
            <v-icon size="32" class="mr-3">mdi-sigma</v-icon>
            <div>
              <div class="text-h5 font-weight-bold">{{ scenarios.length }}</div>
              <div class="text-caption">Gesamt</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Scenarios Table -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="filteredScenarios"
          :loading="loading"
          :items-per-page="10"
          class="elevation-0"
          @click:row="(event, { item }) => viewScenarioStats(item)"
        >
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center">
              <v-icon :color="getTypeColor(item.function_type_name)" class="mr-2">
                {{ getTypeIcon(item.function_type_name) }}
              </v-icon>
              <span class="font-weight-medium">{{ item.name }}</span>
            </div>
          </template>

          <template v-slot:item.function_type_name="{ item }">
            <v-chip size="small" :color="getTypeColor(item.function_type_name)" variant="flat">
              {{ getFunctionTypeName(item.function_type_name) }}
            </v-chip>
          </template>

          <template v-slot:item.begin_date="{ item }">
            {{ formatDate(item.begin_date) }}
          </template>

          <template v-slot:item.end_date="{ item }">
            <span :class="{ 'text-warning': isExpiringSoon(item.end_date), 'text-error': isExpired(item.end_date) }">
              {{ formatDate(item.end_date) }}
            </span>
          </template>

          <template v-slot:item.status="{ item }">
            <v-chip :color="getStatusColor(item.status)" size="small">
              {{ item.status }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              variant="text"
              size="small"
              @click.stop="viewScenarioStats(item)"
            >
              <v-icon>mdi-chart-bar</v-icon>
              <v-tooltip activator="parent" location="top">Statistiken</v-tooltip>
            </v-btn>
            <ScenarioDetailDialog
              :scenario-id="item.scenario_id"
              @scenarioEdited="fetchScenarios"
            />
            <v-btn
              icon
              variant="text"
              size="small"
              color="error"
              @click.stop="confirmDelete(item)"
            >
              <v-icon>mdi-delete</v-icon>
              <v-tooltip activator="parent" location="top">Löschen</v-tooltip>
            </v-btn>
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8">
              <v-icon size="48" class="mb-2 text-medium-emphasis">mdi-clipboard-outline</v-icon>
              <div class="text-medium-emphasis">Keine Szenarien gefunden</div>
              <v-btn color="primary" class="mt-4" @click="fetchScenarios">
                <v-icon start>mdi-refresh</v-icon>
                Aktualisieren
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Scenario Stats Dialog -->
    <v-dialog v-model="statsDialog" max-width="900" scrollable>
      <v-card v-if="selectedScenario">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-chart-bar</v-icon>
          {{ selectedScenario.name }} - Fortschrittsstatistiken
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="statsDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-progress-linear v-if="loadingStats" indeterminate color="primary"></v-progress-linear>

          <!-- User Progress Table -->
          <v-data-table
            v-else
            :headers="statsHeaders"
            :items="userStats"
            :items-per-page="10"
            class="elevation-0"
          >
            <template v-slot:item.username="{ item }">
              <div class="d-flex align-center">
                <v-avatar size="32" color="primary" class="mr-2">
                  <span class="text-caption">{{ item.username.charAt(0).toUpperCase() }}</span>
                </v-avatar>
                {{ item.username }}
              </div>
            </template>

            <template v-slot:item.progress="{ item }">
              <v-progress-linear
                :model-value="calculateProgress(item)"
                height="20"
                rounded
                color="primary"
              >
                <template v-slot:default="{ value }">
                  <strong>{{ Math.round(value) }}%</strong>
                </template>
              </v-progress-linear>
            </template>

            <template v-slot:item.completed="{ item }">
              {{ item.ranked_threads_count || 0 }} / {{ item.total_threads || 0 }}
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Szenario löschen?
        </v-card-title>
        <v-card-text>
          Möchten Sie das Szenario "{{ scenarioToDelete?.name }}" wirklich löschen?
          Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" variant="flat" @click="deleteScenario" :loading="deleting">
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import CreateScenarioDialog from '@/components/parts/CreateScenarioDialog.vue';
import ScenarioDetailDialog from '@/components/parts/ScenarioDetailsDialog.vue';

// State
const scenarios = ref([]);
const searchQuery = ref('');
const statusFilter = ref('all');
const typeFilter = ref('all');
const loading = ref(false);

// Stats dialog
const statsDialog = ref(false);
const selectedScenario = ref(null);
const userStats = ref([]);
const loadingStats = ref(false);

// Delete dialog
const deleteDialog = ref(false);
const scenarioToDelete = ref(null);
const deleting = ref(false);

// Options
const statusOptions = [
  { title: 'Alle', value: 'all' },
  { title: 'Aktiv', value: 'aktiv' },
  { title: 'Ausstehend', value: 'ausstehend' },
  { title: 'Beendet', value: 'beendet' }
];

const typeOptions = [
  { title: 'Alle', value: 'all' },
  { title: 'Ranking', value: 'ranking' },
  { title: 'Rating', value: 'rating' },
  { title: 'Verlaufsbewertung', value: 'mail_rating' }
];

// Table headers
const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Typ', key: 'function_type_name', sortable: true },
  { title: 'Beginn', key: 'begin_date', sortable: true },
  { title: 'Ende', key: 'end_date', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
];

const statsHeaders = [
  { title: 'Benutzer', key: 'username', sortable: true },
  { title: 'Fortschritt', key: 'progress', sortable: false },
  { title: 'Abgeschlossen', key: 'completed', sortable: true }
];

// Computed
const filteredScenarios = computed(() => {
  return scenarios.value.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(searchQuery.value.toLowerCase());
    const matchesStatus = statusFilter.value === 'all' || s.status === statusFilter.value;
    const matchesType = typeFilter.value === 'all' || s.function_type_name === typeFilter.value;
    return matchesSearch && matchesStatus && matchesType;
  });
});

const scenarioStats = computed(() => {
  return {
    aktiv: scenarios.value.filter(s => s.status === 'aktiv').length,
    ausstehend: scenarios.value.filter(s => s.status === 'ausstehend').length,
    beendet: scenarios.value.filter(s => s.status === 'beendet').length
  };
});

// Helper functions
const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

const getFunctionTypeName = (type) => {
  const typeMap = {
    'mail_rating': 'Verlaufsbewertung',
    'rating': 'Rating',
    'ranking': 'Ranking'
  };
  return typeMap[type] || type;
};

const getTypeColor = (type) => {
  const colorMap = {
    'mail_rating': 'purple',
    'rating': 'orange',
    'ranking': 'blue'
  };
  return colorMap[type] || 'grey';
};

const getTypeIcon = (type) => {
  const iconMap = {
    'mail_rating': 'mdi-email-outline',
    'rating': 'mdi-star-outline',
    'ranking': 'mdi-format-list-numbered'
  };
  return iconMap[type] || 'mdi-clipboard-outline';
};

const getStatusColor = (status) => {
  const colorMap = {
    'aktiv': 'success',
    'beendet': 'grey',
    'ausstehend': 'warning'
  };
  return colorMap[status] || 'error';
};

const isExpiringSoon = (dateString) => {
  if (!dateString) return false;
  const endDate = new Date(dateString);
  const daysUntilEnd = (endDate - new Date()) / (1000 * 60 * 60 * 24);
  return daysUntilEnd <= 7 && daysUntilEnd > 0;
};

const isExpired = (dateString) => {
  if (!dateString) return false;
  return new Date(dateString) < new Date();
};

const calculateProgress = (user) => {
  if (!user.total_threads || user.total_threads === 0) return 0;
  return ((user.ranked_threads_count || 0) / user.total_threads) * 100;
};

// API calls
const fetchScenarios = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/admin/scenarios');
    scenarios.value = response.data.scenarios || [];
  } catch (error) {
    console.error('Error fetching scenarios:', error);
    scenarios.value = [];
  }
  loading.value = false;
};

const viewScenarioStats = async (scenario) => {
  selectedScenario.value = scenario;
  statsDialog.value = true;
  loadingStats.value = true;

  try {
    const response = await axios.get(`/api/admin/scenario/${scenario.scenario_id}/user_stats`);
    userStats.value = response.data.user_stats || [];
  } catch (error) {
    console.error('Error fetching user stats:', error);
    userStats.value = [];
  }

  loadingStats.value = false;
};

const confirmDelete = (scenario) => {
  scenarioToDelete.value = scenario;
  deleteDialog.value = true;
};

const deleteScenario = async () => {
  if (!scenarioToDelete.value) return;

  deleting.value = true;
  try {
    await axios.delete(`/api/admin/delete_scenario/${scenarioToDelete.value.scenario_id}`);
    deleteDialog.value = false;
    scenarioToDelete.value = null;
    await fetchScenarios();
  } catch (error) {
    console.error('Error deleting scenario:', error);
  }
  deleting.value = false;
};

onMounted(() => {
  fetchScenarios();
});
</script>

<style scoped>
:deep(.v-data-table tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

:deep(.v-data-table tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
