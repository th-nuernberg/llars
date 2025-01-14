<template>
  <v-container class="admin-scenarios">
    <!-- Header Section -->
    <v-row>
      <v-col cols="12">
        <v-card class="title-card">
          <v-card-title class="text-h4">Szenarios</v-card-title>
          <v-card-subtitle>Übersicht der E-Mail-Bewertungen</v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <!-- Controls Row -->
    <v-row class="mt-4 mb-4">
      <!-- Search Field -->
      <v-col cols="12" md="4">
        <v-text-field
          v-model="searchQuery"
          label="Nach Namen suchen"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          @update:model-value="filterScenarios"
        ></v-text-field>
      </v-col>

      <!-- Status Filter -->
      <v-col cols="12" md="4">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Status Filter"
          variant="outlined"
          density="comfortable"
          hide-details
          @update:model-value="filterScenarios"
        ></v-select>
      </v-col>

      <!-- Create Button Column -->
      <v-col cols="12" md="4" class="d-flex justify-end">
        <CreateScenarioDialog/>
      </v-col>
    </v-row>

    <!-- Scenarios Table -->
    <v-card>
      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Kategorie</th>
              <th>Beginn</th>
              <th>Ende</th>
              <th>Status</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="scenario in filteredScenarios"
              :key="scenario.scenario_id"
              class="scenario-row"
            >
              <td>{{ scenario.name }}</td>
              <td>{{ getFunctionTypeName(scenario.function_type_name) }}</td>
              <td>{{ formatDate(scenario.begin_date) }}</td>
              <td>{{ formatDate(scenario.end_date) }}</td>
              <td>
                <v-chip
                  :color="getStatusColor(scenario.status)"
                  :text-color="getStatusTextColor(scenario.status)"
                  size="small"
                >
                  {{ scenario.status }}
                </v-chip>
              </td>
              <td>
                <v-btn
                  density="comfortable"
                  variant="flat"
                  class="details-btn"
                  @click="navigateToDetails(scenario)"
                >
                  Detailansicht
                </v-btn>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- Create Scenario Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="800px">
      <CreateScenarioDialog :dialog="showCreateDialog" @close="showCreateDialog = false" />
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import CreateScenarioDialog from "@/components/parts/CreateScenarioDialog.vue";

const router = useRouter();
const scenarios = ref([]);
const searchQuery = ref('');
const statusFilter = ref('aktiv'); // Default filter set to 'aktiv'
const showCreateDialog = ref(false); // Controls visibility of the dialog

// Define status options for the filter dropdown
const statusOptions = [
  { title: 'Alle', value: 'all' },
  { title: 'Aktiv', value: 'aktiv' },
  { title: 'Ausstehend', value: 'ausstehend' },
  { title: 'Beendet', value: 'beendet' }
];

// Computed property for filtered scenarios
const filteredScenarios = computed(() => {
  return scenarios.value.filter(scenario => {
    // Apply name search filter
    const matchesSearch = scenario.name.toLowerCase()
      .includes(searchQuery.value.toLowerCase());

    // Apply status filter
    const matchesStatus = statusFilter.value === 'all' ||
      scenario.status === statusFilter.value;

    return matchesSearch && matchesStatus;
  });
});

// Fetch scenarios from the backend
const fetchScenarios = async () => {
  try {
    const response = await axios.get('/api/admin/scenarios', {
      headers: {
        'Authorization': localStorage.getItem('api_key')
      }
    });
    scenarios.value = response.data.scenarios;
  } catch (error) {
    console.error('Error fetching scenarios:', error);
  }
};

// Format date helper
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

// Function type name mapping
const getFunctionTypeName = (type) => {
  const typeMap = {
    'mail_rating': 'Verlaufs Generierung',
    'rating': 'Rating',
    'ranking': 'Ranking'
  };
  return typeMap[type] || type;
};

// Status color mapping
const getStatusColor = (status) => {
  const colorMap = {
    'aktiv': 'success',
    'beendet': 'grey',
    'ausstehend': 'warning'
  };
  return colorMap[status] || 'error';
};

const getStatusTextColor = (status) => {
  return status === 'beendet' ? 'white' : 'black';
};

// Navigation function
const navigateToDetails = (scenario) => {
  const routeMap = {
    'mail_rating': '/AdminHistoryGenerator',
    'rating': '/admin/rater',
    'ranking': '/AdminRanker'
  };

  const baseRoute = routeMap[scenario.function_type_name];
  if (baseRoute) {
    router.push(`${baseRoute}/scenario/${scenario.scenario_id}`);
  }
};

onMounted(() => {
  fetchScenarios();
});
</script>

<style scoped>
/* Previous styles remain the same */
.admin-scenarios {
  margin-top: 20px;
  padding: 16px;
}

.title-card {
  background-color: #b0ca97;
}

.title-card .v-card-title {
  color: #ffffff;
}

.title-card .v-card-subtitle {
  color: #e6f2d5;
}

.v-table {
  background-color: white;
  border-radius: 8px;
}

.v-table th {
  background-color: #f5f5f5;
  color: #2f4f4f;
  font-weight: bold;
  text-transform: none;
}

.v-table td {
  color: #556b2f;
}

.scenario-row {
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.scenario-row:hover {
  background-color: #e8f5e9;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.details-btn {
  background-color: #b0ca97 !important;
  color: white !important;
}

.details-btn:hover {
  background-color: #9db888 !important;
  box-shadow: 0 2px 8px rgba(176, 202, 151, 0.4);
}
</style>
