<template>
  <v-card>
    <v-card-title class="headline">Szenario erstellen</v-card-title>
    <v-card-text>
      <!-- Szenario Name -->
      <v-text-field
        v-model="scenarioName"
        label="Szenario Name"
        outlined
        density="comfortable"
        required
      ></v-text-field>

      <!-- Kategorie Auswahl -->
      <v-select
        v-model="selectedCategory"
        :items="categories"
        item-text="name"
        item-value="function_type_id"
        label="Kategorie"
        outlined
        density="comfortable"
        required
      ></v-select>

      <!-- Datum Auswahl -->
      <v-row>
        <v-col cols="12" md="6">
          <v-date-picker
            v-model="startDate"
            label="Startdatum"
            locale="de"
            required
          ></v-date-picker>
        </v-col>
        <v-col cols="12" md="6">
          <v-date-picker
            v-model="endDate"
            label="Enddatum"
            locale="de"
            required
          ></v-date-picker>
        </v-col>
      </v-row>

      <!-- Nutzer Container -->
      <v-expansion-panels>
        <v-expansion-panel>
          <v-expansion-panel-title>Nutzer</v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <v-col
                v-for="user in users"
                :key="user.id"
                cols="12"
                md="6"
              >
                <v-card outlined>
                  <v-card-title>{{ user.name }} (ID: {{ user.id }})</v-card-title>
                  <v-card-text>
                    <v-radio-group
                      v-model="userRoles[user.id]"
                      :mandatory="false"
                    >
                      <v-radio label="Viewer" value="viewer"></v-radio>
                      <v-radio label="Rater" value="rater"></v-radio>
                    </v-radio-group>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Threads Container -->
        <v-expansion-panel>
          <v-expansion-panel-title>Threads</v-expansion-panel-title>
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
            <v-row>
              <v-col
                v-for="thread in filteredThreads"
                :key="thread.thread_id"
                cols="12"
                md="6"
              >
                <v-card outlined>
                  <v-card-title>
                    {{ thread.subject }} (ID: {{ thread.thread_id }})
                  </v-card-title>
                  <v-card-text>{{ thread.sender }}</v-card-text>
                  <v-checkbox
                    v-model="selectedThreads"
                    :value="thread.thread_id"
                    label="Auswählen"
                  ></v-checkbox>
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
    </v-card-text>
    <v-card-actions>
      <v-spacer></v-spacer>
      <v-btn @click="$emit('close')" color="red">Abbrechen</v-btn>
      <v-btn @click="submitScenario" color="green">Anlegen</v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import axios from "axios";

export default {
  props: {
    dialog: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      scenarioName: "",
      selectedCategory: null,
      startDate: null,
      endDate: null,
      categories: [],
      users: [],
      threads: [],
      userRoles: {},
      selectedThreads: [],
      threadFilter: { from: null, to: null },
    };
  },
  computed: {
    filteredThreads() {
      return this.threads
        .filter(thread => {
          const withinRange =
            (!this.threadFilter.from || thread.thread_id >= this.threadFilter.from) &&
            (!this.threadFilter.to || thread.thread_id <= this.threadFilter.to);
          return withinRange;
        })
        .sort((a, b) => b.thread_id - a.thread_id);
    },
  },
  methods: {
    async fetchCategories() {
      try {
        const response = await axios.get("/api/admin/get_function_types",
          {
            headers: {
            'Authorization': localStorage.getItem("api_key"),
          },
        });
        this.categories = response.data;
      } catch (error) {
        console.error("Error fetching categories:", error);
      }
    },
    async fetchUsers() {
      try {
        const response = await axios.get("/api/admin/get_users",
        {
            headers: {
            'Authorization': localStorage.getItem("api_key"),
          },
        });

        this.users = response.data;
      } catch (error) {
        console.error("Error fetching users:", error);
      }
    },
    async fetchThreads() {
      if (!this.selectedCategory) return;
      try {
        const response = await axios.get(
          `/api/admin/get_threads_from_function_type/${this.selectedCategory}`,
          {
            headers: {
            'Authorization': localStorage.getItem("api_key"),
          },
        });

        this.threads = response.data;
      } catch (error) {
        console.error("Error fetching threads:", error);
      }
    },
    async submitScenario() {
      const viewers = Object.keys(this.userRoles).filter(
        userId => this.userRoles[userId] === "viewer"
      );
      const raters = Object.keys(this.userRoles).filter(
        userId => this.userRoles[userId] === "rater"
      );

      const payload = {
        scenario_name: this.scenarioName,
        function_type_id: this.selectedCategory,
        begin: this.startDate,
        end: this.endDate,
        viewer: viewers.map(Number),
        rater: raters.map(Number),
        threads: this.selectedThreads,
      };

      try {
        const confirmation = confirm(
          "Sind Sie sicher, dass Sie das Szenario speichern möchten?"
        );
        if (!confirmation) return;

        await axios.post("/api/admin/create_scenario", payload,
          {
          headers: {
            'Authorization': localStorage.getItem("api_key"),
            'Content-Type': 'application/json',
          }
        });
        this.$emit('close');
        alert("Szenario erfolgreich erstellt!");
      } catch (error) {
        alert(`Fehler beim Erstellen des Szenarios: ${error.message}`);
      }
    },
  },
  watch: {
    selectedCategory() {
      this.fetchThreads();
    },
  },
  mounted() {
    this.fetchCategories();
    this.fetchUsers();
  },
};
</script>

<style scoped>
.v-card {
  margin-bottom: 16px;
}
</style>
