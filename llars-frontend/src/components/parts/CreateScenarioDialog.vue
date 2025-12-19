<template>
  <div>
    <LBtn
      variant="primary"
      prepend-icon="mdi-plus"
      @click="openDialog"
    >
      Szenario Erstellen
    </LBtn>

    <v-dialog v-model="dialogState.showCreateDialog" max-width="1000px">
      <v-card>
        <v-card-title class="headline">Szenario erstellen</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="formData.scenarioName"
            :error-messages="errors.scenarioName"
            label="Szenario Name"
            outlined
            density="comfortable"
            required
          ></v-text-field>

          <v-select
            v-model="formData.selectedCategory"
            :items="categoryItems"
            :error-messages="errors.selectedCategory"
            label="Kategorie"
            outlined
            density="comfortable"
            required
            @update:model-value="handleCategoryChange"
          ></v-select>

          <v-row>
            <v-col cols="12" md="6">
              <div class="date-field-col">
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
                      :error-messages="errors.startDate"
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
                <div class="quick-date-row">
                  <LBtn size="small" variant="tonal" prepend-icon="mdi-calendar-today" @click="setStartToday">
                    Heute
                  </LBtn>
                </div>
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="date-field-col">
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
                      :error-messages="errors.endDate"
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
                <div class="quick-date-row">
                  <LBtn size="small" variant="tonal" prepend-icon="mdi-calendar-week" @click="setEndInDays(7)">
                    In 1 Woche
                  </LBtn>
                  <LBtn size="small" variant="tonal" prepend-icon="mdi-calendar-month" @click="setEndInMonths(1)">
                    In 1 Monat
                  </LBtn>
                </div>
              </div>
            </v-col>
          </v-row>

          <v-expansion-panels>
            <!-- Nutzer Panel -->
            <v-expansion-panel :class="{ 'error-panel': errors.raters }">
              <v-expansion-panel-title>
                Nutzer
              </v-expansion-panel-title>
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
                        <div class="text-subtitle-1 mb-1">{{user.name}}</div>
                        <div class="text-caption text-grey">ID: {{user.id}}</div>

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

            <v-expansion-panel v-if="formData.selectedCategory === 4">
              <v-expansion-panel-title>
                Modell-Konfiguration
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="formData.llm1Model"
                      :items="modelItems"
                      :loading="state.isLoadingModels"
                      label="Language-Modell 1"
                      outlined
                      density="comfortable"
                      hint="Erstes Modell für die Gegenüberstellung"
                      persistent-hint
                      clearable
                    >
                      <template v-slot:no-data>
                        <v-list-item>
                          <v-list-item-title>
                            {{ state.isLoadingModels ? 'Lade Modelle...' : 'Keine Modelle verfügbar' }}
                          </v-list-item-title>
                        </v-list-item>
                      </template>
                    </v-select>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="formData.llm2Model"
                      :items="modelItems"
                      :loading="state.isLoadingModels"
                      label="Language-Modell 2"
                      outlined
                      density="comfortable"
                      hint="Zweites Modell für die Gegenüberstellung"
                      persistent-hint
                      clearable
                    >
                      <template v-slot:no-data>
                        <v-list-item>
                          <v-list-item-title>
                            {{ state.isLoadingModels ? 'Lade Modelle...' : 'Keine Modelle verfügbar' }}
                          </v-list-item-title>
                        </v-list-item>
                      </template>
                    </v-select>
                  </v-col>
                </v-row>
                <v-alert
                  type="info"
                  variant="tonal"
                  class="mt-3"
                >
                  <template v-if="state.isLoadingModels">
                    <v-progress-circular
                      indeterminate
                      size="16"
                      class="mr-2"
                    ></v-progress-circular>
                    Modelle werden geladen...
                  </template>
                  <template v-else-if="state.availableModels.length > 0">
                    {{ state.availableModels.length }} verfügbare Modelle geladen.
                  </template>
                  <template v-else>
                    Bitte wählen Sie Modelle aus der Liste der verfügbaren Modelle aus.
                  </template>
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <v-expansion-panel v-if="formData.selectedCategory === 5">
              <v-expansion-panel-title>
                Fake/Echt – Import
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  Importiere JSON-Items im v6-Format (ein Item oder Liste). Nach dem Import kannst du die Threads im nächsten Panel auswählen.
                </v-alert>

                <v-file-input
                  v-model="authImport.files"
                  label="JSON-Dateien (optional)"
                  prepend-icon="mdi-file-json"
                  variant="outlined"
                  density="comfortable"
                  multiple
                  show-size
                  accept="application/json,.json"
                />

                <v-textarea
                  v-model="authImport.jsonText"
                  label="Oder JSON einfügen (optional)"
                  placeholder='{"metadata": {...}, "messages": [...]}'
                  variant="outlined"
                  density="comfortable"
                  auto-grow
                  rows="3"
                  class="mt-3"
                />

                <div class="d-flex ga-2 mt-3">
                  <LBtn
                    variant="primary"
                    prepend-icon="mdi-upload"
                    :loading="authImport.isImporting"
                    @click="importAuthenticity"
                  >
                    Importieren
                  </LBtn>
                  <LBtn variant="tonal" prepend-icon="mdi-refresh" @click="handleCategoryChange(formData.selectedCategory)">
                    Threads aktualisieren
                  </LBtn>
                </div>

                <v-alert v-if="authImport.error" type="error" variant="tonal" class="mt-3">
                  {{ authImport.error }}
                </v-alert>

                <v-alert v-if="authImport.result" type="success" variant="tonal" class="mt-3">
                  Import: {{ authImport.result.imported || 0 }} neu, {{ authImport.result.skipped_existing || 0 }} übersprungen,
                  {{ (authImport.result.errors || []).length }} Fehler.
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Threads Panel -->
            <v-expansion-panel :class="{ 'error-panel': errors.selectedThreads }" v-if="formData.selectedCategory !== 4">
              <v-expansion-panel-title>
                Threads
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
                <v-row class="select-all-row">
                  <v-col>
                    <LBtn
                      variant="secondary"
                      prepend-icon="mdi-check-all"
                      @click="selectAllFilteredThreads"
                    >
                      Alle anwählen
                    </LBtn>
                  </v-col>
                  <v-col>
                    <LBtn
                      variant="secondary"
                      prepend-icon="mdi-close-box-outline"
                      @click="deselectAllFilteredThreads"
                    >
                      Alle abwählen
                    </LBtn>
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
                            <div class="text-subtitle-1 text-truncate">{{thread.subject}}</div>
                          </div>
                          <div class="d-flex justify-space-between align-center mb-1">
                            <div class="text-caption text-grey">Thread-ID: {{thread.thread_id}}</div>
                            <div class="text-caption">{{thread.sender}}</div>
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
          <LBtn variant="cancel" @click="closeDialog">Abbrechen</LBtn>
          <LBtn variant="primary" @click="validateAndSubmitScenario">Anlegen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {reactive, onMounted, computed,} from 'vue';
import {
  getFunctionTypes,
  getAllUsers,
  getThreadsOfType,
  createScenario,
  getAvailableModels
} from '@/services/scenarioApi';
import { importAuthenticityDataset } from '@/services/authenticityApi';

export default {
  name: 'ScenarioDialog',

  setup(props, {emit}) {
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
      isLoadingThreads: false,
      availableModels: [],
      isLoadingModels: false
    });

    const formData = reactive({
      scenarioName: '',
      selectedCategory: null,
      startDate: null,
      endDate: null,
      userRoles: {},
      selectedThreads: [],
      llm1Model: '',
      llm2Model: ''
    });

    const errors = reactive({
      scenarioName: '',
      selectedCategory: '',
      startDate: '',
      endDate: '',
      userRoles: '',
      selectedThreads: ''
    });

    const authImport = reactive({
      files: [],
      jsonText: '',
      isImporting: false,
      error: '',
      result: null
    });


    const validateForm = () => {
      errors.scenarioName = formData.scenarioName ? "" : "Bitte geben Sie einen Szenario Namen an.";
      errors.selectedCategory = formData.selectedCategory ? "" : "Bitte wählen Sie eine Kategorie aus.";
      errors.startDate = formData.startDate ? "" : "Bitte wählen Sie ein Startdatum aus.";
      errors.endDate = formData.endDate ? "" : "Bitte wählen Sie ein Enddatum aus.";

      // Überprüfen, ob das Startdatum nach dem Enddatum liegt
      if (formData.startDate && formData.endDate && new Date(formData.startDate) > new Date(formData.endDate)) {
        errors.startDate = "Das Startdatum darf nicht nach dem Enddatum liegen.";
        errors.endDate = "Das Enddatum darf nicht vor dem Startdatum liegen.";
      }

      const raters = Object.entries(formData.userRoles).filter(([, role]) => role.rater).map(([id]) => Number(id));
      errors.raters = raters.length > 0 ? "" : "Bitte wählen Sie mindestens einen Rater aus.";

      if(formData.selectedCategory !== 4) {
        errors.selectedThreads = formData.selectedThreads.length > 0 ? ""
          : "Bitte wählen Sie mindestens einen Thread aus.";
      }

      return !Object.values(errors).some((error) => error);
    };

    const selectAllFilteredThreads = () => {
  // Sicherstellen, dass `filteredThreads` und `formData.selectedThreads` existieren
  if (!Array.isArray(filteredThreads.value) || filteredThreads.value.length === 0) {
    formData.selectedThreads = [];
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
      'mail_rating': 'Verlaufsbewertung',
      'ranking': 'Ranking',
      'comparison': 'Gegenüberstellung',
      'authenticity': 'Fake/Echt'
    };

    const categoryItems = computed(() => {
      return state.categories.map(category => ({
        value: category.function_type_id,
        title: `${category.emoji ? category.emoji + ' ' : ''}${category.display_name || categoryNameMapping[category.name] || category.name}`.trim(),
        raw: category
      }));
    });

    const modelItems = computed(() => {
      return state.availableModels.map(model => ({
        value: model.id,
        title: model.name,
        subtitle: model.owned_by ? `Owned by: ${model.owned_by}` : undefined
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

    const fetchCategories = async () => {
      try {
        state.categories = await getFunctionTypes();
      } catch (error) {
        console.error("Fehler beim Laden der Kategorien:", error);
        handleApiError(error);
      }
    };

    const fetchUsers = async () => {
      try {
        state.users = await getAllUsers();
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

    const fetchAvailableModels = async () => {
      state.isLoadingModels = true;
      try {
        state.availableModels = await getAvailableModels();
      } catch (error) {
        console.error("Fehler beim Laden der verfügbaren Modelle:", error);
        handleApiError(error);
        state.availableModels = [];
      } finally {
        state.isLoadingModels = false;
      }
    };

    const fetchThreads = async (categoryId) => {
      if (!categoryId) {
        state.threads = [];
        return;
      }

      state.isLoadingThreads = true;
      try {
        state.threads = await getThreadsOfType(categoryId);
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
      
      if (newCategoryId === 4) {
        await fetchAvailableModels();
      }
    };

    const _dateToPickerString = (date) => {
      const d = date instanceof Date ? date : new Date(date);
      if (!d || Number.isNaN(d.getTime())) return null;
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      return `${yyyy}-${mm}-${dd}`;
    };

    const _parsePickerValue = (value) => {
      if (!value) return null;
      if (value instanceof Date) return value;
      const s = String(value);
      const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
      if (m) {
        return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
      }
      const d = new Date(s);
      return Number.isNaN(d.getTime()) ? null : d;
    };

    const setStartToday = () => {
      formData.startDate = _dateToPickerString(new Date());
      if (!formData.endDate) {
        formData.endDate = _dateToPickerString(new Date());
      }
    };

    const setEndInDays = (days) => {
      const base = _parsePickerValue(formData.startDate) || new Date();
      const d = new Date(base.getFullYear(), base.getMonth(), base.getDate());
      d.setDate(d.getDate() + Number(days || 0));
      formData.endDate = _dateToPickerString(d);
    };

    const setEndInMonths = (months) => {
      const base = _parsePickerValue(formData.startDate) || new Date();
      const d = new Date(base.getFullYear(), base.getMonth(), base.getDate());
      d.setMonth(d.getMonth() + Number(months || 0));
      formData.endDate = _dateToPickerString(d);
    };

    const importAuthenticity = async () => {
      authImport.error = '';
      authImport.result = null;

      const items = [];

      const text = String(authImport.jsonText || '').trim();
      if (text) {
        try {
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed)) {
            items.push(...parsed);
          } else {
            items.push(parsed);
          }
        } catch (e) {
          authImport.error = 'JSON im Textfeld ist ungültig.';
          return;
        }
      } else if (Array.isArray(authImport.files) && authImport.files.length > 0) {
        try {
          const readFile = (file) => new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(String(reader.result || ''));
            reader.onerror = () => reject(new Error('Datei konnte nicht gelesen werden.'));
            reader.readAsText(file);
          });

          const contents = await Promise.all(authImport.files.map(readFile));
          for (const content of contents) {
            const parsed = JSON.parse(content);
            if (Array.isArray(parsed)) items.push(...parsed);
            else items.push(parsed);
          }
        } catch (e) {
          authImport.error = 'Eine oder mehrere Dateien enthalten ungültiges JSON.';
          return;
        }
      } else {
        authImport.error = 'Bitte JSON einfügen oder eine Datei auswählen.';
        return;
      }

      authImport.isImporting = true;
      try {
        authImport.result = await importAuthenticityDataset(items.length === 1 ? items[0] : items);
        // Refresh threads list after successful import
        await fetchThreads(formData.selectedCategory);
      } catch (e) {
        authImport.error = e?.response?.data?.message || e?.message || 'Import fehlgeschlagen.';
      } finally {
        authImport.isImporting = false;
      }
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
      formData.llm1Model = '';
      formData.llm2Model = '';
      authImport.files = [];
      authImport.jsonText = '';
      authImport.isImporting = false;
      authImport.error = '';
      authImport.result = null;

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

      if (formData.selectedCategory === 4) {
        if (formData.llm1Model.trim()) {
          payload.llm1_model = formData.llm1Model.trim();
        }
        if (formData.llm2Model.trim()) {
          payload.llm2_model = formData.llm2Model.trim();
        }
      }

      try {
        const confirmation = confirm("Sind Sie sicher, dass Sie das Szenario speichern möchten?");
        if (!confirmation) return;

        console.log(payload);
        await createScenario(payload);
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
      authImport,
      threadFilter,
      categoryItems,
      modelItems,
      filteredThreads,
      openDialog,
      closeDialog,
      handleCategoryChange,
      handleCheckboxChange,
      importAuthenticity,
      setStartToday,
      setEndInDays,
      setEndInMonths,
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

.date-field-col {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.date-field-col :deep(.v-field) {
  width: 100%;
}

.quick-date-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  flex-wrap: wrap;
}
</style>
