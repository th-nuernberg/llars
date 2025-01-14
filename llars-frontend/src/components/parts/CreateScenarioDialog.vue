<template>
  <div>
    <v-btn
      color="primary"
      prepend-icon="mdi-plus"
      @click="openDialog"
    >
      Szenario Erstellen
    </v-btn>

    <v-dialog v-model="dialogState.showCreateDialog" max-width="1000px">
      <v-card>
        <v-card-title class="headline">Szenario erstellen</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="formData.scenarioName"
            label="Szenario Name"
            outlined
            density="comfortable"
            required
          ></v-text-field>

          <v-select
            v-model="formData.selectedCategory"
            :items="categoryItems"
            label="Kategorie"
            outlined
            density="comfortable"
            required
            @update:model-value="handleCategoryChange"
          ></v-select>

          <v-row>
            <v-col cols="12" md="6">
              <v-menu
                v-model="dateMenus.start"
                :close-on-content-click="false"
                location="start"
                transition="scale-transition"
                min-width="auto"
              >
                <template v-slot:activator="{ props }">
                  <v-text-field
                    :model-value="formatDate(formData.startDate)"
                    label="Startdatum"
                    readonly
                    v-bind="props"
                    prepend-icon="mdi-calendar"
                    outlined
                    density="comfortable"
                  ></v-text-field>
                </template>
                <v-date-picker
                  v-model="formData.startDate"
                  v-bind="datePickerProps"
                  locale="de-DE"
                  :first-day-of-week="1"
                  color="primary"
                  @click:save="dateMenus.start = false"
                ></v-date-picker>
              </v-menu>
            </v-col>
            <v-col cols="12" md="6">
              <v-menu
                v-model="dateMenus.end"
                :close-on-content-click="false"
                location="end"
                transition="scale-transition"
                min-width="auto"
              >
                <template v-slot:activator="{ props }">
                  <v-text-field
                    :model-value="formatDate(formData.endDate)"
                    label="Enddatum"
                    readonly
                    v-bind="props"
                    prepend-icon="mdi-calendar"
                    outlined
                    density="comfortable"
                ></v-text-field>
                </template>
                <v-date-picker
                  v-model="formData.endDate"
                  v-bind="datePickerProps"
                  locale="de-DE"
                  :first-day-of-week="1"
                  color="primary"
                  @click:save="dateMenus.end = false"
                ></v-date-picker>
              </v-menu>
            </v-col>
          </v-row>

          <v-expansion-panels>
            <v-expansion-panel>
    <v-expansion-panel-title>Nutzer</v-expansion-panel-title>
    <v-expansion-panel-text>
      <v-row>
        <v-col
          v-for="user in state.users"
          :key="user.id"
          cols="12"
          sm="6"
          md="4"
        >
          <v-card outlined class="user-card" density="compact">
            <v-card-item>
              <div class="text-subtitle-1 mb-1">{{ user.name }}</div>
              <div class="text-caption text-grey">ID: {{ user.id }}</div>

              <!-- Checkboxen nebeneinander -->
              <v-row class="d-flex align-center">
                <v-col cols="auto">
                  <v-checkbox
                    v-model="formData.userRoles[user.id].viewer"
                    label="Viewer"
                    density="compact"
                    hide-details
                    @change="handleCheckboxChange(user.id, 'viewer')"
                  ></v-checkbox>
                </v-col>
                <v-col cols="auto">
                  <v-checkbox
                    v-model="formData.userRoles[user.id].rater"
                    label="Rater"
                    density="compact"
                    hide-details
                    @change="handleCheckboxChange(user.id, 'rater')"
                  ></v-checkbox>
                </v-col>
              </v-row>
            </v-card-item>
          </v-card>
        </v-col>
      </v-row>
    </v-expansion-panel-text>
  </v-expansion-panel>

            <v-expansion-panel>
              <v-expansion-panel-title>
                Threads
                <v-progress-circular
                  v-if="state.isLoadingThreads"
                  indeterminate
                  size="20"
                  class="ml-2"
                ></v-progress-circular>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="threadFilter.from"
                      label="Von Thread ID"
                      type="number"
                      outlined
                      density="comfortable"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="threadFilter.to"
                      label="Bis Thread ID"
                      type="number"
                      outlined
                      density="comfortable"
                    ></v-text-field>
                  </v-col>
                </v-row>
                <div v-if="state.threads.length > 0">
                  <v-row>
                    <v-col
                      v-for="thread in filteredThreads"
                      :key="thread.thread_id"
                      cols="12"
                      sm="6"
                      md="4"
                    >
                      <v-card
                        outlined
                        class="thread-card"
                        density="compact"
                      >
                        <v-card-item>
                          <div class="d-flex align-center mb-1">
                            <div class="text-subtitle-1 text-truncate">{{ thread.subject }}</div>
                          </div>
                          <div class="d-flex justify-space-between align-center mb-1">
                            <div class="text-caption text-grey">Thread-ID: {{ thread.thread_id }}</div>
                            <div class="text-caption">{{ thread.sender }}</div>
                          </div>
                          <v-checkbox
                            v-model="formData.selectedThreads"
                            :value="thread.thread_id"
                            label="Auswählen"
                            density="compact"
                            hide-details
                            class="mt-1"
                          ></v-checkbox>
                        </v-card-item>
                      </v-card>
                    </v-col>
                  </v-row>
                </div>
                <div v-else-if="!formData.selectedCategory" class="text-center py-4">
                  Bitte wählen Sie zuerst eine Kategorie aus
                </div>
                <div v-else-if="!state.isLoadingThreads" class="text-center py-4">
                  Keine Threads für diese Kategorie gefunden
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="closeDialog" color="red">Abbrechen</v-btn>
          <v-btn @click="submitScenario" :disabled="!isFormValid" color="green">Anlegen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {ref, reactive, onMounted, computed} from 'vue';
import axios from 'axios';

export default {
  name: 'ScenarioDialog',

  setup() {
    const dialogState = reactive({
      showCreateDialog: false
    });

    const dateMenus = reactive({
      start: false,
      end: false
    });

    const state = reactive({
      categories: [],
      users: [],
      threads: [],
      isLoadingThreads: false
    });

    const formData = reactive({
    scenarioName: '',
    selectedCategory: null,
    startDate: null,
    endDate: null,
    userRoles: {},
    selectedThreads: []
    });

  const isFormValid = computed(() => {
  const raters = Object.entries(formData.userRoles).filter(([, role]) => role.rater).map(([id]) => Number(id));
  const viewers = Object.entries(formData.userRoles).filter(([, role]) => role.viewer).map(([id]) => Number(id));

  // Bedingungen prüfen
  return formData.scenarioName &&
         formData.selectedCategory &&
         formData.startDate &&
         formData.endDate &&
         raters.length > 0 &&
         viewers.length > 0 &&
         formData.selectedThreads.length > 0;
});


    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    };

    const datePickerProps = {
      locale: 'de-DE',
      firstDayOfWeek: 1,
      color: 'primary',
      titles: {
        prev: 'Vorheriger Monat',
        next: 'Nächster Monat',
        current: 'Aktueller Monat'
      },
      dayNames: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'],
      monthNames: [
        'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
        'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
      ]
    };

    const threadFilter = reactive({
      from: null,
      to: null
    });

    const categoryNameMapping = {
      'rating': 'Rating',
      'mail_rating': 'Verlauf Generierung',
      'ranking': 'Ranking'
    };

    const categoryItems = computed(() => {
      return state.categories.map(category => ({
        value: category.function_type_id,
        title: categoryNameMapping[category.name] || category.name,
        raw: category
      }));
    });

    const filteredThreads = computed(() => {
      if (!state.threads) return [];

      return state.threads.filter(thread => {
        if (!threadFilter.from && !threadFilter.to) return true;

        const threadId = thread.thread_id;
        const fromCondition = !threadFilter.from || threadId >= threadFilter.from;
        const toCondition = !threadFilter.to || threadId <= threadFilter.to;

        return fromCondition && toCondition;
      });
    });

    const getAuthHeaders = () => ({
      headers: {
        'Authorization': localStorage.getItem('api_key')
      }
    });

    const fetchCategories = async () => {
      try {
        const response = await axios.get("/api/admin/get_function_types", getAuthHeaders());
        state.categories = response.data;
      } catch (error) {
        console.error("Fehler beim Laden der Kategorien:", error);
        handleApiError(error);
      }
    };


    const fetchUsers = async () => {
      try {
    const response = await axios.get("/api/admin/get_users", getAuthHeaders());
    state.users = response.data;
    // Initialisiere die userRoles für jeden Nutzer mit viewer und rater als false
    state.users.forEach(user => {
      formData.userRoles[user.id] = {
        viewer: false,
        rater: false
      };
    });
  } catch (error) {
    console.error("Fehler beim Laden der User:", error);
    handleApiError(error);
  }
};


    const fetchThreads = async (categoryId) => {
      if (!categoryId) {
        state.threads = [];
        return;
      }

      state.isLoadingThreads = true;
      try {
        const response = await axios.get(
          `/api/admin/get_threads_from_function_type/${categoryId}`,
          getAuthHeaders()
        );
        state.threads = response.data;
      } catch (error) {
        console.error("Fehler beim Laden der Threads:", error);
        handleApiError(error);
        state.threads = [];
      } finally {
        state.isLoadingThreads = false;
      }
    };

    const handleCategoryChange = async (newCategoryId) => {
      formData.selectedThreads = [];
      await fetchThreads(newCategoryId);
    };

const handleCheckboxChange = (userId, role) => {
  // Wenn 'viewer' aktiviert wird, setze 'rater' auf false und umgekehrt
  if (role === 'viewer') {
    // Wenn 'viewer' ausgewählt wird, 'rater' deaktivieren
    formData.userRoles[userId].rater = false;
  } else if (role === 'rater') {
    // Wenn 'rater' ausgewählt wird, 'viewer' deaktivieren
    formData.userRoles[userId].viewer = false;
  }
};

    const handleApiError = (error) => {
      if (error.response?.status === 401) {
        alert('Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.');
      }
    };

    const openDialog = () => {
      dialogState.showCreateDialog = true;
    };

    const closeDialog = () => {
      dialogState.showCreateDialog = false;
      resetForm();
    };

    const resetForm = () => {
      formData.scenarioName = '';
      formData.selectedCategory = null;
      formData.startDate = null;
      formData.endDate = null;
      formData.userRoles = {};
      formData.selectedThreads = [];
      state.threads = [];
      threadFilter.from = null;
      threadFilter.to = null;
    };

    const submitScenario = async () => {
  // Validierung der Eingabefelder
  if (!formData.scenarioName) {
    alert("Bitte einen Szenario Namen angeben.");
    return;
  }

  if (!formData.selectedCategory) {
    alert("Bitte eine Kategorie auswählen.");
    return;
  }

  if (!formData.startDate || !formData.endDate) {
    alert("Bitte ein Start- und Enddatum auswählen.");
    return;
  }

  // Überprüfe, ob mindestens ein Rater ausgewählt wurde
  const raters = Object.entries(formData.userRoles)
    .filter(([, role]) => role.rater) // Nur Benutzer mit der 'rater' Rolle
    .map(([id]) => Number(id));

  if (raters.length === 0) {
    alert("Bitte mindestens einen Rater auswählen.");
    return;
  }

  // Überprüfe, ob mindestens ein Viewer ausgewählt wurde
  const viewers = Object.entries(formData.userRoles)
    .filter(([, role]) => role.viewer) // Nur Benutzer mit der 'viewer' Rolle
    .map(([id]) => Number(id));

  if (viewers.length === 0) {
    alert("Bitte mindestens einen Viewer auswählen.");
    return;
  }

  // Überprüfe, ob Threads ausgewählt wurden
  if (formData.selectedThreads.length === 0) {
    alert("Bitte mindestens einen Thread auswählen.");
    return;
  }

  // Threads als Liste von IDs verarbeiten
  const threadIds = Object.values(formData.selectedThreads);

  // Überprüfe, ob Threads ausgewählt wurden
  if (formData.selectedThreads.length === 0) {
    alert("Bitte mindestens einen Thread auswählen.");
    return;
  }

  // Datum in ISO-Format umwandeln
  const startDateISO = new Date(formData.startDate).toISOString().substring(0,19);
  const endDateISO = new Date(formData.endDate).toISOString().substring(0,19);

  const payload = {
    scenario_name: formData.scenarioName,
    function_type_id: formData.selectedCategory,
    begin: startDateISO,
    end: endDateISO,
    viewer: viewers,
    rater: raters,
    threads: threadIds
  };

  try {
    const confirmation = confirm("Sind Sie sicher, dass Sie das Szenario speichern möchten?");
    if (!confirmation) return;

    console.log(payload);
    console.log(JSON.stringify(payload))
    // Sende die Anfrage zum Erstellen des Szenarios
    await axios.post("/api/admin/create_scenario", payload, getAuthHeaders());
    alert("Szenario erfolgreich erstellt!");
    closeDialog();
  } catch (error) {
    console.error("Fehler beim Erstellen des Szenarios:", error);
    alert(`Fehler beim Erstellen des Szenarios: ${error.message}`);
    handleApiError(error);
  }
};



    onMounted(async () => {
      await fetchCategories();
      await fetchUsers();
    });

    return {
      dialogState,
      dateMenus,
      state,
      formData,
      threadFilter,
      categoryItems,
      filteredThreads,
      openDialog,
      closeDialog,
      handleCategoryChange,
      handleCheckboxChange,
      submitScenario,
      datePickerProps,
      formatDate,
      isFormValid
    };
  }
};
</script>

<style scoped>
.user-card {
  transition: all 0.3s ease;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.v-row {
  display: flex;
  align-items: center;
}

.v-col {
  display: flex;
  justify-content: center;
}

.d-flex {
  display: flex;
  align-items: center;
}

.d-flex.align-center {
  justify-content: flex-start;
}
</style>
