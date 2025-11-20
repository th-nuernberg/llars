<template>
  <div>
    <v-btn
      prepend-icon="mdi-eye"
      @click.stop="openDialog"
      class="details-btn"
      density="compact"
      variant="flat"
      size="small"
    >
    </v-btn>

    <v-dialog v-model="dialog" max-width="1000px">
      <v-card>
        <v-card-title class="headline">
          Szenario Details
          <v-spacer></v-spacer>
          <v-btn
            v-if="!isEditing"
            icon="mdi-pencil"
            @click="startEditing"
          ></v-btn>
        </v-card-title>

        <v-card-text>
          <v-text-field
            v-model="editedScenario.scenario_name"
            label="Szenario Name"
            :error-messages="errors.scenarioName"
            :readonly="!isEditing"
            outlined
            density="comfortable"
          ></v-text-field>

          <v-text-field
            v-model="categoryNameMapping"
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
                location="start"
                transition="scale-transition"
                min-width="auto"
              >
                <template v-slot:activator="{ props }">
                  <v-text-field
                    :model-value="formatDateForDisplay(editedScenario.begin_date)"
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
                  v-model="editedScenario.begin_date"
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
                    :model-value="formatDateForDisplay(editedScenario.end_date)"
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
                  v-model="editedScenario.end_date"
                  locale="de-DE"
                  :first-day-of-week="1"
                  color="primary"
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
                <v-row>
                  <!-- Raters Section -->
                  <v-col cols="12">
                    <div class="text-h6 mb-4">Rater</div>
                  </v-col>
                  <v-col cols="12" class="mb-4">
                    <v-row>
                      <v-col
                        v-for="rater in editedScenario.raters"
                        :key="rater.user_id"
                        cols="12" sm="6" md="4"
                      >
                        <v-card outlined class="user-card" density="compact">
                          <v-card-item>
                            <div class="d-flex align-center mb-1">
                              <div class="text-subtitle-1 text-truncate">{{rater.username}}</div>
                            </div>
                            <div class="d-flex justify-space-between align-center">
                              <div class="text-caption text-grey">ID: {{rater.user_id}}</div>
                            </div>
                          </v-card-item>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-col>

                  <!-- Viewers Section -->
                  <v-col cols="12">
                    <div class="text-h6 mb-4">Viewer</div>
                  </v-col>
                  <v-col cols="12" class="mb-4">
                    <v-row>
                      <v-col
                        v-for="viewer in editedScenario.viewers"
                        :key="viewer.user_id"
                        cols="12" sm="6" md="4"
                      >
                        <v-card outlined class="user-card" density="compact">
                          <v-card-item>
                            <div class="d-flex align-center mb-1">
                              <div class="text-subtitle-1 text-truncate">{{viewer.username}}</div>
                            </div>
                            <div class="d-flex justify-space-between align-center">
                              <div class="text-caption text-grey">ID: {{viewer.user_id}}</div>
                            </div>
                          </v-card-item>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-col>
                </v-row>

                <!-- Available Viewers for Editing Mode -->
                <div v-if="isEditing" class="mt-4">
                  <div class="text-subtitle-1 mb-2">Verfügbare Viewer</div>
                  <v-row>
                    <v-col
                      v-for="user in filteredAvailableUsers"
                      :key="user.id"
                      cols="12" sm="6" md="4"
                    >
                      <v-card outlined class="user-card" density="compact">
                        <v-card-item>
                          <div class="d-flex align-center mb-1">
                            <div class="text-subtitle-1 text-truncate">{{user.name}}</div>
                          </div>
                          <div class="d-flex justify-space-between align-center">
                            <div class="text-caption text-grey">ID: {{user.id}}</div>
                          </div>
                          <v-checkbox
                            v-model="selectedViewers"
                            :value="user.id"
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
              </v-expansion-panel-text>
            </v-expansion-panel>


            <!-- Threads Panel -->
            <v-expansion-panel v-if="this.editedScenario.func_type !== 'comparison'">
              <v-expansion-panel-title>
                Threads
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <!-- Thread Filter -->
                <v-row v-if="isEditing">
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
                <v-row v-if="isEditing" class="select-all-row">
                  <v-col>
                    <v-btn
                      class="select-all-btn"
                      color="primary"
                      prepend-icon="mdi-check"
                      @click="selectAllFilteredThreads"
                    >
                      Alle anwählen
                    </v-btn>
                  </v-col>
                  <v-col>
                    <v-btn
                      class="select-all-btn"
                      color="primary"
                      prepend-icon="mdi-alpha-x-box-outline"
                      @click="deselectAllFilteredThreads"
                    >
                      Alle abwählen
                    </v-btn>
                  </v-col>
                </v-row>

                <!-- Existing Threads -->
                <v-row>
                  <v-col
                    v-for="thread in editedScenario.threads"
                    :key="thread.thread_id"
                    cols="12" sm="6" md="4"
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

                <!-- Available Threads -->
                <div v-if="isEditing" class="mt-4">
                  <div class="text-subtitle-1 mb-2">Verfügbare Threads</div>
                  <v-row>
                    <v-col
                      v-for="thread in filteredAvailableThreads"
                      :key="thread.thread_id"
                      cols="12" sm="6" md="4"
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
                            v-model="selectedThreads"
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
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel v-if="this.editedScenario.function_type_id === 4">
              <v-expansion-panel-title>
                Modell-Konfiguration
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="editedScenario.llm1_model"
                      label="Language-Modell 1"
                      hint="Z.B. mistralai/Mistral-Small-3.1-24B-Instruct-2503"
                      :readonly="!isEditing"
                      outlined
                      density="comfortable"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="editedScenario.llm2_model"
                      label="Language-Modell 2"
                      hint="Z.B. mistralai/Mistral-Small-3.1-24B-Instruct-2503"
                      :readonly="!isEditing"
                      outlined
                      density="comfortable"
                    ></v-text-field>
                  </v-col>
                </v-row>
                <v-alert
                  v-if="!isEditing && (!editedScenario.llm1_model || !editedScenario.llm2_model)"
                  type="info"
                  class="mt-2"
                  density="compact"
                >
                  Keine Modelle konfiguriert
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="red" @click="closeDialog">Abbrechen</v-btn>
          <v-btn
            v-if="isEditing"
            color="green"
            @click="saveChanges"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>


<script>
import {ref, reactive, onMounted, computed} from 'vue';
import axios from 'axios';

export default {
  name: 'ScenarioDetailDialog',

  props: {
    scenarioId: {
      type: Number,
      required: true
    }
  },
  emits: ["scenarioEdited"],

  data() {
    return {
      dialog: false,
      isEditing: false,
      dateMenus: {
        start: false,
        end: false,
      },
      threadFilter: {
        from: null,
        to: null
      },
      originalScenario: null,
      editedScenario: {
        scenario_id: null,
        scenario_name: '',
        func_type: '',
        function_type_id: null,
        begin_date: null,
        end_date: null,
        threads: [],
        raters: [],
        viewers: [],
        llm1_model: '',
        llm2_model: ''
      },
      selectedThreads: [],
      selectedViewers: [],
      availableThreads: [],
      availableUsers: [],
      errors: {
        scenarioName: '',
        startDate: '',
        endDate: '',
      },
    }
  },

  computed: {
    filteredAvailableThreads() {
      // Filter threads excluding already added threads
      const existingThreadIds = this.editedScenario.threads.map(t => t.thread_id);
      let filtered = this.availableThreads.filter(thread =>
        !existingThreadIds.includes(thread.thread_id)
      );

      // Apply additional thread ID filtering
      if (this.threadFilter.from || this.threadFilter.to) {
        filtered = filtered.filter(thread => {
          const id = thread.thread_id;
          const fromOk = !this.threadFilter.from || id >= this.threadFilter.from;
          const toOk = !this.threadFilter.to || id <= this.threadFilter.to;
          return fromOk && toOk;
        });
      }

      return filtered;
    },

    categoryNameMapping() {
      const categoryLabels = {
        'rating': 'Rating',
        'mail_rating': 'Verlauf Generierung',
        'ranking': 'Ranking',
        'comparison': 'Gegenüberstellung'
      };
      return categoryLabels[this.editedScenario.func_type] || this.editedScenario.func_type;
    },

    filteredAvailableUsers() {
      // Filter users excluding already added viewers and raters
      const existingUserIds = [
        ...this.editedScenario.viewers.map(v => v.user_id),
        ...this.editedScenario.raters.map(r => r.user_id)
      ];

      return this.availableUsers.filter(user =>
        !existingUserIds.includes(user.id)
      );
    }
  },

  methods: {
    async openDialog() {
      this.dialog = true;
      await this.loadScenarioDetails();
      if (this.isEditing) {
        await Promise.all([
          this.loadAvailableThreads(),
          this.loadAvailableUsers()
        ]);
      }
    },


    selectAllFilteredThreads() {
      this.selectedThreads = this.filteredAvailableThreads.map(thread => thread.thread_id);
    },

    deselectAllFilteredThreads() {
      this.selectedThreads = [];
    },

    closeDialog() {
      this.dialog = false;
      this.isEditing = false;
      this.editedScenario = JSON.parse(JSON.stringify(this.originalScenario));
      this.selectedThreads = [];
      this.selectedViewers = [];
    },

    async startEditing() {
      this.isEditing = true;
      await Promise.all([
        this.loadAvailableThreads(),
        this.loadAvailableUsers()
      ]);
    },


    formatDateForDisplay(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    },

    formatDateForBackend(date) {
      if (!date) return '';
      return date.toISOString().substring(0, 19);
    },


    async loadScenarioDetails() {
      try {
        const response = await axios.get(`/api/admin/scenarios/${this.scenarioId}`, {
          headers: {
            'Authorization': localStorage.getItem('api_key')
          }
        });
        const data = response.data;


        data.begin_date = data.begin_date ? new Date(data.begin_date) : null;
        data.end_date = data.end_date ? new Date(data.end_date) : null;

        this.originalScenario = data;
        this.editedScenario = JSON.parse(JSON.stringify(data));

        // The deepcopy through Json-function above changes the type of the date fields this line fixes ist
        this.editedScenario.begin_date = this.editedScenario.begin_date ? new Date(data.begin_date) : null;
        this.editedScenario.end_date = this.editedScenario.end_date ? new Date(data.end_date) : null;


      } catch (error) {
        console.error('Error loading scenario details:', error);
      }
    },

    async loadAvailableThreads() {
      if (!this.editedScenario.function_type_id) return;

      try {
        const response = await axios.get(
          `/api/admin/get_threads_from_function_type/${this.editedScenario.function_type_id}`,
          {
            headers: {
              'Authorization': localStorage.getItem('api_key')
            }
          }
        );
        this.availableThreads = response.data;
      } catch (error) {
        console.error('Error loading available threads:', error);
      }
    },

    async loadAvailableUsers() {
      try {
        const response = await axios.get('/api/admin/get_users', {
          headers: {
            'Authorization': localStorage.getItem('api_key')
          }
        });
        this.availableUsers = response.data;
      } catch (error) {
        console.error('Error loading available users:', error);
      }
    },

    validateForm() {
      let isValid = true;

      // Szenarioname prüfen
      if (!this.editedScenario.scenario_name.trim()) {
        this.errors.scenarioName = 'Der Szenarioname darf nicht leer sein.';
        isValid = false;
      } else {
        this.errors.scenarioName = null;
      }

      // Datum prüfen
      const beginDate = this.editedScenario.begin_date;
      const endDate = this.editedScenario.end_date;

      if (!beginDate)
        this.errors.startDate = "Kein Startdatum vorhanden"
      if (!endDate)
        this.errors.startDate = "Kein Enddatum vorhanden"

      if (beginDate && endDate && beginDate > endDate) {
        this.errors.startDate = 'Das Startdatum darf nicht hinter dem Enddatum liegen.';
        this.errors.endDate = 'Das Enddatum darf nicht vor dem Startdatum liegen.';
        isValid = false;
      } else {
        this.errors.startDate = "";
        this.errors.endDate = "";
      }

      return isValid;
    },


    async saveChanges() {
      if (!this.validateForm()) {
        console.warn('Validierungsfehler, Änderungen werden nicht gespeichert.');
        return;
      }
      try {
        const updates = [];

        const basicChanges = {
          id: this.editedScenario.scenario_id,
          new_name: this.editedScenario.scenario_name !== this.originalScenario.scenario_name
            ? this.editedScenario.scenario_name
            : undefined,
          new_begin: this.editedScenario.begin_date !== this.originalScenario.begin_date
            ? this.formatDateForBackend(this.editedScenario.begin_date)
            : undefined,
          new_end: this.editedScenario.end_date !== this.originalScenario.end_date
            ? this.formatDateForBackend(this.editedScenario.end_date)
            : undefined,
          llm1_model: this.editedScenario.function_type_id === 4 &&
                     this.editedScenario.llm1_model !== this.originalScenario.llm1_model
            ? this.editedScenario.llm1_model
            : undefined,
          llm2_model: this.editedScenario.function_type_id === 4 &&
                     this.editedScenario.llm2_model !== this.originalScenario.llm2_model
            ? this.editedScenario.llm2_model
            : undefined
        };

        // Only include fields that have actually changed
        const finalBasicChanges = Object.fromEntries(
          Object.entries(basicChanges).filter(([_, value]) => value !== undefined)
        );

        const confirmation = confirm("Sind Sie sicher, dass Sie die Änderungen speichern möchten?");
        if (!confirmation) return;

        // Add basic changes if any exist
        if (Object.keys(finalBasicChanges).length > 1) { // > 1 because id is always included
          updates.push(
            axios.post('/api/admin/edit_scenario',
              finalBasicChanges,
              {
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': localStorage.getItem('api_key')
                }
              })
          );
        }

        // Add new threads if any are selected
        if (this.selectedThreads.length > 0) {
          updates.push(
            axios.post('/api/admin/add_threads_to_scenario',
              {
                scenario_id: this.scenarioId,
                thread_ids: this.selectedThreads
              },
              {
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': localStorage.getItem('api_key')
                }
              }
            )
          );
        }

        // Add new viewers if any are selected
        if (this.selectedViewers.length > 0) {
          updates.push(
            axios.post('/api/admin/add_viewers_to_scenario',
              {
                scenario_id: this.scenarioId,
                user_ids: this.selectedViewers
              },
              {
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': localStorage.getItem('api_key')
                }
              }
            )
          );
        }

        // Wait for all updates to complete
        await Promise.all(updates);


        this.isEditing = false;
        await this.loadScenarioDetails(); // Reload the data

        // Reset selections
        this.selectedThreads = [];
        this.selectedViewers = [];
        this.errors.scenarioName = "";
        this.errors.startDate = "";
        this.errors.endDate = "";

        alert("Szenario erfolgreich geändert!");
        this.$emit("scenarioEdited")
      } catch (error) {
        console.error('Fehler beim Änderen aufgetreten:', error);
        // Handle error appropriately
      }
    }
  }
}
</script>


<style scoped>
.user-card {
  transition: all 0.3s ease;
  width: 100%; /* Ensure cards take full width of their column */
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.v-row {
  display: flex;
  flex-wrap: wrap; /* Ensure proper wrapping */
  margin: 0 -12px; /* Compensate for column padding */
}

.v-col {
  display: flex;
  padding: 12px; /* Add consistent padding */
}

/* Rest of your existing styles remain the same */
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

.details-btn {
  padding: 0;
  min-width: 36px;
  width: 36px;
  height: 36px;
}

.details-btn:hover {
  color: #9db888 !important;
  box-shadow: 0 2px 8px rgba(176, 202, 151, 0.4);
}

.select-all-row {
  margin-bottom: 2em;
}
</style>
