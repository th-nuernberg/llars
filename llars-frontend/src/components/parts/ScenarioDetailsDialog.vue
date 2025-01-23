<template>
  <div>
    <!-- Detail/Edit Dialog Trigger Button -->
    <v-btn
      prepend-icon="mdi-eye"
      @click.stop="openDialog"
      class="details-btn"
      density="compact"
      variant="flat"
      size = "small"
    >
    </v-btn>

    <!-- Main Dialog -->
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
            :readonly="!isEditing"
            outlined
            density="comfortable"
          ></v-text-field>

          <v-text-field
            v-model="editedScenario.func_type"
            label="Kategorie"
            readonly
            disabled
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
                    v-model="editedScenario.begin_date"
                    label="Startdatum"
                    :readonly="!isEditing"
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
                    v-model="editedScenario.end_date"
                    label="Enddatum"
                    :readonly="!isEditing"
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
                  <v-col cols="12" class="mb-4">
                    <div class="text-h6 mb-2">Rater</div>
                    <v-row>
                      <v-col
                        v-for="rater in editedScenario.raters"
                        :key="rater.user_id"
                        cols="12" sm="6" md="4"
                      >
                        <v-card outlined class="user-card" density="compact">
                          <v-card-item>
                            <div class="text-subtitle-1 mb-1">{{ rater.username }}</div>
                            <div class="text-caption text-grey">ID: {{ rater.user_id }}</div>
                          </v-card-item>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-col>

                  <!-- Viewers Section -->
                  <v-col cols="12">
                    <div class="d-flex align-center mb-2">
                      <div class="text-h6">Viewer</div>
                      <v-spacer></v-spacer>
                      <v-btn
                        v-if="isEditing"
                        color="primary"
                        prepend-icon="mdi-plus"
                        @click="openViewerSelectionDialog"
                      >
                        Viewer hinzufügen
                      </v-btn>
                    </div>
                    <v-row>
                      <v-col
                        v-for="viewer in editedScenario.viewers"
                        :key="viewer.user_id"
                        cols="12" sm="6" md="4"
                      >
                        <v-card outlined class="user-card" density="compact">
                          <v-card-item>
                            <div class="text-subtitle-1 mb-1">{{ viewer.username }}</div>
                            <div class="text-caption text-grey">ID: {{ viewer.user_id }}</div>
                          </v-card-item>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-col>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Threads Panel -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                Threads
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="d-flex align-center mb-4">
                  <v-spacer></v-spacer>
                  <v-btn
                    v-if="isEditing"
                    color="primary"
                    prepend-icon="mdi-plus"
                    @click="openThreadSelectionDialog"
                  >
                    Threads hinzufügen
                  </v-btn>
                </div>
                <v-row>
                  <v-col
                    v-for="thread in editedScenario.threads"
                    :key="thread.thread_id"
                    cols="12" sm="6" md="4"
                  >
                    <v-card outlined class="thread-card" density="compact">
                      <v-card-item>
                        <div class="d-flex align-center mb-1">
                          <div class="text-subtitle-1 text-truncate">{{ thread.subject }}</div>
                        </div>
                        <div class="d-flex justify-space-between align-center">
                          <div class="text-caption text-grey">Thread-ID: {{ thread.thread_id }}</div>
                          <div class="text-caption">{{ thread.sender }}</div>
                        </div>
                      </v-card-item>
                    </v-card>
                  </v-col>
                </v-row>
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

    <!-- Thread Selection Dialog -->
    <v-dialog v-model="threadSelectionDialog" max-width="800px">
      <v-card>
        <v-card-title>Threads Hinzufügen</v-card-title>
        <v-card-text>
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
          <v-row>
            <v-col
              v-for="thread in filteredAvailableThreads"
              :key="thread.thread_id"
              cols="12" sm="6" md="4"
            >
              <v-card outlined class="thread-card" density="compact">
                <v-card-item>
                  <div class="d-flex align-center mb-1">
                    <div class="text-subtitle-1 text-truncate">{{ thread.subject }}</div>
                  </div>
                  <div class="d-flex justify-space-between align-center mb-1">
                    <div class="text-caption text-grey">Thread-ID: {{ thread.thread_id }}</div>
                    <div class="text-caption">{{ thread.sender }}</div>
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
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="red" @click="threadSelectionDialog = false">Abbrechen</v-btn>
          <v-btn color="green" @click="addThreadsToScenario">Hinzufügen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Viewer Selection Dialog -->
    <v-dialog v-model="viewerSelectionDialog" max-width="800px">
      <v-card>
        <v-card-title>Viewer Hinzufügen</v-card-title>
        <v-card-text>
          <v-row>
            <v-col
              v-for="user in availableUsers"
              :key="user.id"
              cols="12" sm="6" md="4"
            >
              <v-card outlined class="user-card" density="compact">
                <v-card-item>
                  <div class="text-subtitle-1 mb-1">{{ user.name }}</div>
                  <div class="text-caption text-grey">ID: {{ user.id }}</div>
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
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="red" @click="viewerSelectionDialog = false">Abbrechen</v-btn>
          <v-btn color="green" @click="addViewersToScenario">Hinzufügen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {ref, reactive, onMounted, computed,} from 'vue';
import axios from 'axios';

export default {
  name: 'ScenarioDetailDialog',

  props: {
    scenarioId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      dialog: false,
      isEditing: false,
      threadSelectionDialog: false,
      viewerSelectionDialog: false,
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
        begin_date: '',
        end_date: '',
        threads: [],
        raters: [],
        viewers: []
      },
      selectedThreads: [],
      selectedViewers: [],
      availableThreads: [],
      availableUsers: [],
      errors: {}
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
      this.dialog = true
      await this.loadScenarioDetails()
    },

    closeDialog() {
      this.dialog = false
      this.isEditing = false
      this.editedScenario = JSON.parse(JSON.stringify(this.originalScenario))
    },

    startEditing() {
      this.isEditing = true
    },

    selectAllFilteredThreads() {
      this.selectedThreads = this.filteredAvailableThreads.map(thread => thread.thread_id)
    },

    deselectAllFilteredThreads() {
      this.selectedThreads = []
    },

    async loadScenarioDetails() {
      try {
        const response = await axios.get(`/api/admin/scenarios/${this.scenarioId}`, {
      headers: {
        'Authorization': localStorage.getItem('api_key')
      }
    });
        this.originalScenario = response.data
        this.editedScenario = JSON.parse(JSON.stringify(response.data))
      } catch (error) {
        console.error('Error loading scenario details:', error)
        // Handle error appropriately
      }
    },

    async loadAvailableThreads() {
      if (!this.editedScenario.function_type_id) return;

      try {
        const response = await axios.get(`/api/admin/get_threads_from_function_type/${this.editedScenario.function_type_id}`, {
          headers: {
            'Authorization': localStorage.getItem('api_key')
          }
        });
        this.availableThreads =  response.data;
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

    async saveChanges() {
      try {
        // Prepare the update payload
        const updatePayload = {
          id: this.editedScenario.scenario_id,
          new_name: this.editedScenario.scenario_name !== this.originalScenario.scenario_name
            ? this.editedScenario.scenario_name
            : undefined,
          new_begin: this.editedScenario.begin_date !== this.originalScenario.begin_date
            ? this.editedScenario.begin_date
            : undefined,
          new_end: this.editedScenario.end_date !== this.originalScenario.end_date
            ? this.editedScenario.end_date
            : undefined
        }

        // Only include fields that have actually changed
        const finalPayload = Object.fromEntries(
          Object.entries(updatePayload).filter(([_, value]) => value !== undefined)
        )

        if (Object.keys(finalPayload).length > 1) { // > 1 because id is always included
          await axios.post('/api/admin/edit_scenario', {
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(finalPayload)
          })
        }

        this.isEditing = false
        await this.loadScenarioDetails() // Reload the data
      } catch (error) {
        console.error('Error saving changes:', error)
        // Handle error appropriately
      }
    },

    async openThreadSelectionDialog() {
      this.threadSelectionDialog = true;
      await this.loadAvailableThreads();
    },


    async addThreadsToScenario() {
      try {
        const threads = Object.values(this.selectedThreads)
        const payload = {
            scenario_id: this.scenarioId,
            thread_ids: threads
          };
        console.log("Threads: ", payload)
        await axios.post('/api/admin/add_threads_to_scenario',
          payload,
          {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': localStorage.getItem('api_key')
          }
        });

        this.threadSelectionDialog = false
        this.selectedThreads = []
        await this.loadScenarioDetails() // Reload the data
      } catch (error) {
        console.error('Error adding threads:', error)
        // Handle error appropriately
      }
    },

    async openViewerSelectionDialog() {
      this.viewerSelectionDialog = true
      await this.loadAvailableUsers();
    },

    async addViewersToScenario() {
      try {
        const payload = {
            scenario_id: this.scenarioId,
            user_ids: Object.values(this.selectedViewers)
          }
        // This is the suggested API endpoint format for adding viewers

        await axios.post('/api/admin/add_viewers_to_scenario',
          payload,
          {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': localStorage.getItem('api_key')
          }
          })

        this.viewerSelectionDialog = false
        this.selectedViewers = []
        await this.loadScenarioDetails() // Reload the data
      } catch (error) {
        console.error('Error adding viewers:', error)
        // Handle error appropriately
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    }
  }
}
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
