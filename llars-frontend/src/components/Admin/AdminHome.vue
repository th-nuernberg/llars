<template>
  <v-container class="admin-scenarios">
    <!-- Header Section -->
    <v-row>
      <v-col cols="12">
        <v-card class="title-card">
          <v-card-title class="text-h4">Szenarios</v-card-title>
          <v-card-subtitle>Übersicht der Bewertungen</v-card-subtitle>
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
        ></v-select>
      </v-col>

      <!-- Create Button Column -->
      <v-col cols="12" md="4" class="d-flex justify-end">
        <CreateScenarioDialog @scenarioCreated="handleScenarioChanged" />
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
          <tbody v-if="filteredScenarios.length > 0">
  <tr
    v-for="scenario in filteredScenarios"
    :key="scenario.scenario_id"
    class="scenario-row"
    @click="navigateToStats(scenario)"
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
  <v-col class="d-flex align-center">
    <!-- Detail/Edit Dialog Button -->
    <ScenarioDetailDialog :scenario-id="scenario.scenario_id"
                          class="details-btn" density="compact"
                          size="small"
                          @scenarioEdited="handleScenarioChanged"/>

    <!-- Delete Button -->
    <v-btn
      density="compact"
      icon="mdi-delete-outline"
      variant="flat"
      class="delete-btn"
      @click.stop="deleteScenario(scenario)"
    ></v-btn>
  </v-col>
</td>
  </tr>
</tbody>
<tbody v-else>
  <tr>
    <td colspan="6" class="text-center">
      Keine Szenarien verfügbar. Erstellen Sie ein neues Szenario, um zu beginnen.
    </td>
  </tr>
</tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import CreateScenarioDialog from "@/components/parts/CreateScenarioDialog.vue";
import ScenarioDetailDialog from "@/components/parts/ScenarioDetailsDialog.vue";
const router = useRouter();
const scenarios = ref([]);
const searchQuery = ref('');
const statusFilter = ref('aktiv'); // Default filter set to 'aktiv'


// Define status options for the filter dropdown
const statusOptions = [
  { title: 'Alle', value: 'all' },
  { title: 'Aktiv', value: 'aktiv' },
  { title: 'Ausstehend', value: 'ausstehend' },
  { title: 'Beendet', value: 'beendet' }
];

// Computed property for filtered scenarios
const filteredScenarios = computed(() => {
  if (!scenarios.value.length) return []; // Return empty array if no scenarios

  return scenarios.value.filter(scenario => {
    if (!scenario || !scenario.name) return false; // Skip invalid scenarios

    const matchesSearch = scenario.name.toLowerCase()
      .includes(searchQuery.value.toLowerCase());

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

    // Sicherstellen, dass eine Liste zurückkommt
    scenarios.value = Array.isArray(response.data.scenarios)
      ? response.data.scenarios
      : [];
  } catch (error) {
    console.error('Error fetching scenarios:', error);

    // Leere Liste als Fallback verwenden
    scenarios.value = [];
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



const navigateToStats = (scenario) => {
  router.push({ name: 'AdminUserProgressStats', params: { id: scenario.scenario_id } });
};


// Navigation function
const deleteScenario = async (scenario) => {
  try {
    const confirmation = confirm("Sind Sie sicher, dass Sie das Szenario löschen möchten?");
        if (!confirmation) return;

    const scenarioId = scenario.scenario_id
     await axios.delete(`/api/admin/delete_scenario/${scenarioId}`, {
      headers: {
        'Authorization': localStorage.getItem('api_key')
      }
    });

    alert(`Szenario ${scenario.name} wurde erfolgreich gelöscht!`)
    await fetchScenarios();
  }
  catch (error){
    console.error("Fehler beim Erstellen des Szenarios:", error);
    alert("Szenario konnte nicht gelöscht werden")
  }

};


// Wenn ein Szenario erstellt wurde
const handleScenarioChanged= () => {
      fetchScenarios()
    }


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
  padding: 0;
  min-width: 36px;
  width: 36px;
  height: 36px;
}

.details-btn:hover {
  color: #9db888 !important;
  box-shadow: 0 2px 8px rgba(176, 202, 151, 0.4);
  background-color: #e8f5e9;
}

.delete-btn {
  margin-left: 1em;
}
.delete-btn:hover {
  color: red;
}

.v-table .text-center {
  color: #9e9e9e;
  font-style: italic;
  padding: 16px;
}
</style>
