<template>
  <div>
    <v-card>
      <v-card-title class="headline d-flex justify-space-between align-center">
        <span>Szenario Details</span>
        <v-btn
          v-if="isEditing"
          color="primary"
          @click="saveChanges"
        >
          Änderungen speichern
        </v-btn>
        <v-btn
          v-else
          color="primary"
          @click="startEditing"
        >
          Bearbeiten
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Basic Information Section -->
        <v-text-field
          v-model="editableData.scenarioName"
          :readonly="!isEditing"
          label="Szenario Name"
          :error-messages="errors.scenarioName"
          outlined
          density="comfortable"
        ></v-text-field>

        <v-text-field
          :model-value="categoryNameMapping[scenarioData.func_type] || scenarioData.func_type"
          label="Kategorie"
          readonly
          outlined
          density="comfortable"
        ></v-text-field>

        <v-row>
          <v-col cols="12" md="6">
            <v-menu
              v-model="dateMenus.start"
              :close-on-content-click="false"
              :disabled="!isEditing"
              location="start"
              transition="scale-transition"
              min-width="auto"
            >
              <template v-slot:activator="{ props }">
                <v-text-field
                  :model-value="formatDate(editableData.startDate)"
                  label="Startdatum"
                  :error-messages="errors.startDate"
                  readonly
                  v-bind="props"
                  prepend-icon="mdi-calendar"
                  outlined
                  density="comfortable"
                ></v-text-field>
              </template>
              <v-date-picker
                v-if="isEditing"
                v-model="editableData.startDate"
                v-bind="datePickerProps"
                @click:save="dateMenus.start = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
          <v-col cols="12" md="6">
            <v-menu
              v-model="dateMenus.end"
              :close-on-content-click="false"
              :disabled="!isEditing"
              location="end"
              transition="scale-transition"
              min-width="auto"
            >
              <template v-slot:activator="{ props }">
                <v-text-field
                  :model-value="formatDate(editableData.endDate)"
                  label="Enddatum"
                  :error-messages="errors.endDate"
                  readonly
                  v-bind="props"
                  prepend-icon="mdi-calendar"
                  outlined
                  density="comfortable"
                ></v-text-field>
              </template>
              <v-date-picker
                v-if="isEditing"
                v-model="editableData.endDate"
                v-bind="datePickerProps"
                @click:save="dateMenus.end = false"
              ></v-date-picker>
            </v-menu>
          </v-col>
        </v-row>

        <v-expansion-panels>
          <!-- Users Panel -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              Nutzer
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- Existing Users Section -->
              <div class="mb-4">
                <div class="text-h6 mb-2">Zugewiesene Nutzer</div>
                <v-row>
                  <!-- Raters Section -->
                  <v-col cols="12" md="6">
                    <v-card outlined>
                      <v-card-title>Rater</v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item
                            v-for="rater in scenarioData.raters"
                            :key="rater.user_id"
                          >
                            <v-list-item-title>{{ rater.username }}</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>

                  <!-- Viewers Section -->
                  <v-col cols="12" md="6">
                    <v-card outlined>
                      <v-card-title>Viewer</v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item
                            v-for="viewer in scenarioData.viewers"
                            :key="viewer.user_id"
                          >
                            <v-list-item-title>{{ viewer.username }}</v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </div>

              <!-- Add New Viewers Section -->
              <div v-if="isEditing">
                <div class="text-h6 mb-2">Neue Viewer hinzufügen</div>
                <v-row>
                  <v-col
                    v-for="user in availableViewers"
                    :key="user.id"
                    cols="12"
                    sm="6"
                    md="4"
                  >
                    <v-card outlined class="user-card" density="compact">
                      <v-card-item>
                        <div class="text-subtitle-1 mb-1">{{user.username}}</div>
                        <div class="text-caption text-grey">ID: {{user.id}}</div>
                        <v-checkbox
                          v-model="newViewers"
                          :value="user.id"
                          label="Als Viewer hinzufügen"
                          density="compact"
                          hide-details
                        ></v-checkbox>
                      </v-card-item>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>

          <!-- Threads Panel -->
          <v-expansion-panel>
            <v-expansion-panel-title>
              Threads
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <!-- Existing Threads -->
              <div class="mb-4">
                <div class="text-h6 mb-2">Zugewiesene Threads</div>
                <v-row>
                  <v-col
                    v-for="thread in scenarioData.threads"
                    :key="thread.thread_id"
                    cols="12"
                    sm="6"
                    md="4"
                  >
                    <v-card outlined class="thread-card" density="compact">
                      <v-card-item>
                        <div class="d-flex align-center mb-1">
                          <div class="text-subtitle-1 text-truncate">{{thread.subject}}</div>
                        </div>
                        <div class="d-flex justify-space-between align-center">
                          <div class="text-caption text-grey">Thread-ID: {{thread.thread_id}}</div>
                          <div class="text-caption">{{thread.sender}}</div>
                        </div>
                      </v-card-item>
                    </v-card>
                  </v-col>
                </v-row>
              </div>

              <!-- Add New Threads Section -->
              <div v-if="isEditing">
                <div class="text-h6 mb-2">Neue Threads hinzufügen</div>
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

                <v-row class="select-all-row">
                  <v-col>
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-check"
                      @click="selectAllFilteredThreads"
                    >
                      Alle anwählen
                    </v-btn>
                  </v-col>
                  <v-col>
                    <v-btn
                      color="primary"
                      prepend-icon="mdi-alpha-x-box-outline"
                      @click="deselectAllFilteredThreads"
                    >
                      Alle abwählen
                    </v-btn>
                  </v-col>
                </v-row>

                <v-row>
                  <v-col
                    v-for="thread in availableThreads"
                    :key="thread.thread_id"
                    cols="12"
                    sm="6"
                    md="4"
                  >
                    <v-card outlined class="thread-card" density="compact">
                      <v-card-item>
                        <div class="d-flex align-center mb-1">
                          <div class="text-subtitle-1 text-truncate">{{thread.subject}}</div>
                        </div>
                        <div class="d-flex justify-space-between align-center mb-1">
                          <div class="text-caption text-grey">Thread-ID: {{thread.thread_id}}</div>
                          <div class="text-caption">{{thread.sender}}</div>
                        </div>
                        <v-checkbox
                          v-model="newThreads"
                          :value="thread.thread_id"
                          label="Hinzufügen"
                          density="compact"
                          hide-details
                          class="mt-1"
                        ></v-checkbox>
                      </v-card-item>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
  </div>
</template>


<script>
import { ref, reactive, computed, onMounted } from 'vue';
import axios from 'axios';

export default {
  name: 'ScenarioDetails',

  props: {
    scenarioId: {
      type: Number,
      required: true
    }
  },

  setup(props) {
    const isEditing = ref(false);
    const scenarioData = reactive({
      scenario_name: '',
      func_type: '',
      begin_date: null,
      end_date: null,
      threads: [],
      raters: [],
      viewers: []
    });

    const editableData = reactive({
      scenarioName: '',
      startDate: null,
      endDate: null
    });

    const newThreads = ref([]);
    const newViewers = ref([]);
    const availableThreads = ref([]);
    const allUsers = ref([]);

    const dateMenus = reactive({
      start: false,
      end: false
    });

    const errors = reactive({
      scenarioName: '',
      startDate: '',
      endDate: ''
    });

    const threadFilter = reactive({
      from: null,
      to: null
    });

    const categoryNameMapping = {
      'rating': 'Rating',
      'mail_rating': 'Verlauf Generierung',
      'ranking': 'Ranking'
    };

    const availableViewers = computed(() => {
      const existingUserIds = new Set([
        ...scenarioData.viewers.map(v => v.user_id),
        ...scenarioData.raters.map(r => r.user_id)
      ]);
      return allUsers.value.filter(user => !existingUserIds.has(user.id));
    });

    const datePickerProps = {
      locale: 'de-DE',
      firstDayOfWeek: 1,
      color: 'primary'
    };

    const getAuthHeaders = () => ({
      headers: {
        'Authorization': localStorage.getItem('api_key')
      }
    });

    const fetchScenarioDetails = async () => {
      try {
        const response = await axios.get(`/api/scenarios/${props.scenarioId}`, getAuthHeaders());
        Object.assign(scenarioData, response.data);

        // Initialize editable data
        editableData.scenarioName = response.data.scenario_name;
        editableData.startDate = response.data.begin_date.split('T')[0];
        editableData.endDate = response.data.end_date.split('T')[0];
      } catch (error) {
        console.error("Fehler beim Laden der Szenario-Details:", error);
        handleApiError(error);
      }
    };

    const fetchAvailableThreads = async () => {
      try {
        const response = await axios.get(
          `/api/admin/get_threads_from_function_type/${scenarioData.function_type_id}`,
          getAuthHeaders()
        );
        const existingThreadIds = new Set(scenarioData.threads.map(t => t.thread_id));
        availableThreads.value = response.data.filter(thread => !existingThreadIds.has(thread.thread_id));
      } catch (error) {
        console.error("Fehler beim Laden der verfügbaren Threads:", error);
        handleApiError(error);
      }
    };

    const fetchUsers = async () => {
      try {
        const response = await axios.get("/api/admin/get_users", getAuthHeaders());
        allUsers.value = response.data;
      } catch (error) {
        console.error("Fehler beim Laden der User:", error);
        handleApiError(error);
      }
    };

    const validateForm = () => {
      let isValid = true;
      errors.scenarioName = editableData.scenarioName ? "" : "Bitte geben Sie einen Szenario Namen an.";

      if (editableData.startDate && editableData.endDate &&
          new Date(editableData.startDate) > new Date(editableData.endDate)) {
        errors.startDate = "Das Startdatum darf nicht nach dem Enddatum liegen.";
        errors.endDate = "Das Enddatum darf nicht vor dem Startdatum liegen.";
        isValid = false;
      }

      return isValid && !Object.values(errors).some(error => error);
    };

 //--------------------------------------------------------------------------------------------------------------

    const selectAllFilteredThreads = () => {
  // Sicherstellen, dass `filteredThreads` und `formData.selectedThreads` existieren
  if (!Array.isArray(filteredThreads.value) || filteredThreads.value.length === 0) {
    formData.selectedThreads = []; // Leeren, falls keine gefilterten Threads vorhanden sind
    return;
  }

  // Alle Thread-IDs aus `filteredThreads` in `formData.selectedThreads` hinzufügen
  formData.selectedThreads = filteredThreads.value.map(thread => thread.thread_id);
};

    const deselectAllFilteredThreads = () => {
  // Alle ausgewählten Threads abwählen, indem das Array leer gesetzt wird
  formData.selectedThreads = [];
};

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
      if (role === 'viewer') {
        formData.userRoles[userId].rater = false;
      } else if (role === 'rater') {
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
      formData.selectedThreads = [];

      // Sicherstellen, dass das 'userRoles' Objekt korrekt zurückgesetzt wird
      formData.userRoles = Object.fromEntries(
        state.users.map(user => [user.id, {viewer: false, rater: false}])
      );

      // Leeren des 'threads' Arrays
      state.threads.splice(0, state.threads.length);  // Verwende 'splice', um das Array reaktiv zu leeren

      threadFilter.from = null;
      threadFilter.to = null;

      // Fehler zurücksetzen
      Object.keys(errors).forEach((key) => {
        errors[key] = '';
      });
    };

    const validateAndSubmitScenario = async () => {
      if (!validateForm()) {
        return;
      }

      const raters = Object.entries(formData.userRoles).filter(([, role]) => role.rater).map(([id]) => Number(id));
      const viewers = Object.entries(formData.userRoles).filter(([, role]) => role.viewer).map(([id]) => Number(id));
      const startDateISO = new Date(formData.startDate).toISOString().substring(0, 19);
      const endDateISO = new Date(formData.endDate).toISOString().substring(0, 19);
      const threadIds = Object.values(formData.selectedThreads);

      const payload = {
        scenario_name: formData.scenarioName,
        function_type_id: formData.selectedCategory,
        begin: startDateISO,
        end: endDateISO,
        rater: raters,
        threads: threadIds,
        viewer: viewers
      };

      try {
        const confirmation = confirm("Sind Sie sicher, dass Sie das Szenario speichern möchten?");
        if (!confirmation) return;

        console.log(payload);
        await axios.post("/api/admin/create_scenario", payload, getAuthHeaders());
        alert("Szenario erfolgreich erstellt!");
        emit('scenarioCreated');
        closeDialog();
      } catch (error) {
        console.error("Fehler beim Erstellen des Szenarios:", error);
        alert(`Fehler beim Erstellen des Szenarios: ${error.message}`);
        handleApiError(error);
      }
    };

    onMounted(async () => {
      try {
        await Promise.all([fetchCategories(), fetchUsers()]);
      } catch (error) {
        console.error("Fehler beim Initialisieren der Daten:", error);
      }
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
      validateAndSubmitScenario,
      datePickerProps,
      formatDate,
      errors,
      selectAllFilteredThreads,
      deselectAllFilteredThreads
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

.error-panel {
  border: 1px solid red;
  background-color: #ffe6e6;
}

.v-alert {
  margin-top: 10px;
}


.select-all-row {
  margin-bottom: 2em;
}
</style>
