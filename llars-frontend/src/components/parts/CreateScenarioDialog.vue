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
                <v-icon size="20" class="mr-2">mdi-database-import</v-icon>
                Daten-Import
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-alert type="info" variant="tonal" class="mb-4">
                  <div class="d-flex align-center">
                    <v-icon size="20" class="mr-2">mdi-information</v-icon>
                    <span>Importiere JSON-Daten im v6-Format. Du kannst <strong>einzelne Dateien</strong>, <strong>mehrere Dateien</strong>, oder einen <strong>ganzen Ordner</strong> hochladen.</span>
                  </div>
                </v-alert>

                <!-- Import Mode Toggle -->
                <v-btn-toggle
                  v-model="authImport.mode"
                  mandatory
                  density="compact"
                  class="mb-4"
                  color="primary"
                >
                  <v-btn value="files" prepend-icon="mdi-file-multiple">
                    Dateien
                  </v-btn>
                  <v-btn value="folder" prepend-icon="mdi-folder">
                    Ordner
                  </v-btn>
                  <v-btn value="text" prepend-icon="mdi-code-json">
                    JSON Text
                  </v-btn>
                </v-btn-toggle>

                <!-- Files Mode -->
                <div v-if="authImport.mode === 'files'" class="import-section">
                  <v-file-input
                    v-model="authImport.files"
                    label="JSON-Dateien auswählen"
                    prepend-icon="mdi-file-json"
                    variant="outlined"
                    density="comfortable"
                    multiple
                    show-size
                    accept="application/json,.json"
                    :hint="authImport.files?.length ? `${authImport.files.length} Datei(en) ausgewählt` : 'Eine oder mehrere .json Dateien'"
                    persistent-hint
                  />
                </div>

                <!-- Folder Mode -->
                <div v-if="authImport.mode === 'folder'" class="import-section">
                  <div class="folder-upload-container">
                    <input
                      ref="folderInputRef"
                      type="file"
                      webkitdirectory
                      directory
                      multiple
                      accept=".json,application/json"
                      class="folder-input-hidden"
                      @change="handleFolderSelect"
                    />
                    <v-card
                      variant="outlined"
                      class="folder-dropzone"
                      :class="{ 'has-files': authImport.folderFiles?.length }"
                      @click="triggerFolderSelect"
                    >
                      <div class="folder-dropzone-content">
                        <v-icon size="48" :color="authImport.folderFiles?.length ? 'success' : 'grey'">
                          {{ authImport.folderFiles?.length ? 'mdi-folder-check' : 'mdi-folder-open' }}
                        </v-icon>
                        <div v-if="authImport.folderFiles?.length" class="mt-2">
                          <strong>{{ authImport.folderFiles.length }} JSON-Datei(en)</strong>
                          <div class="text-caption text-grey">aus Ordner geladen</div>
                        </div>
                        <div v-else class="mt-2">
                          <strong>Ordner auswählen</strong>
                          <div class="text-caption text-grey">Klicken um einen Ordner mit JSON-Dateien zu wählen</div>
                        </div>
                      </div>
                    </v-card>
                    <LBtn
                      v-if="authImport.folderFiles?.length"
                      variant="text"
                      size="small"
                      prepend-icon="mdi-close"
                      class="mt-2"
                      @click="clearFolderFiles"
                    >
                      Auswahl löschen
                    </LBtn>
                  </div>
                </div>

                <!-- Text Mode -->
                <div v-if="authImport.mode === 'text'" class="import-section">
                  <v-textarea
                    v-model="authImport.jsonText"
                    label="JSON einfügen"
                    placeholder='{"metadata": {...}, "messages": [...]}

oder als Array:
[{"metadata": {...}, "messages": [...]}, ...]'
                    variant="outlined"
                    density="comfortable"
                    auto-grow
                    rows="5"
                    hint="Ein einzelnes JSON-Objekt oder ein Array von Objekten"
                    persistent-hint
                  />
                </div>

                <!-- Action Buttons -->
                <div class="d-flex ga-2 mt-4">
                  <LBtn
                    variant="primary"
                    prepend-icon="mdi-upload"
                    :loading="authImport.isImporting"
                    :disabled="!canImport"
                    @click="importAuthenticity"
                  >
                    {{ importButtonLabel }}
                  </LBtn>
                  <LBtn variant="tonal" prepend-icon="mdi-refresh" @click="handleCategoryChange(formData.selectedCategory)">
                    Threads aktualisieren
                  </LBtn>
                </div>

                <!-- Progress -->
                <v-progress-linear
                  v-if="authImport.isImporting"
                  indeterminate
                  color="primary"
                  class="mt-3"
                />

                <!-- Error Alert -->
                <v-alert v-if="authImport.error" type="error" variant="tonal" class="mt-3" closable @click:close="authImport.error = ''">
                  <div class="d-flex align-center">
                    <v-icon size="20" class="mr-2">mdi-alert-circle</v-icon>
                    {{ authImport.error }}
                  </div>
                </v-alert>

                <!-- Success Alert -->
                <v-alert v-if="authImport.result" type="success" variant="tonal" class="mt-3" closable @click:close="authImport.result = null">
                  <div class="font-weight-medium mb-1">Import erfolgreich!</div>
                  <div class="d-flex ga-4 flex-wrap">
                    <span><v-icon size="16" class="mr-1">mdi-plus-circle</v-icon>{{ authImport.result.imported || 0 }} neu importiert</span>
                    <span><v-icon size="16" class="mr-1">mdi-skip-next</v-icon>{{ authImport.result.skipped_existing || 0 }} übersprungen</span>
                    <span v-if="(authImport.result.errors || []).length > 0" class="text-error">
                      <v-icon size="16" class="mr-1">mdi-alert</v-icon>{{ (authImport.result.errors || []).length }} Fehler
                    </span>
                  </div>
                  <div v-if="authImport.result.thread_ids?.length > 0" class="mt-2 text-caption">
                    <v-icon size="14" class="mr-1">mdi-check-circle</v-icon>
                    {{ authImport.result.thread_ids.length }} Threads automatisch ausgewählt
                  </div>
                </v-alert>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Threads Panel -->
            <v-expansion-panel :class="{ 'error-panel': errors.selectedThreads }" v-if="formData.selectedCategory !== 4">
              <v-expansion-panel-title>
                <div class="d-flex align-center ga-2">
                  <span>Threads</span>
                  <LTag v-if="formData.selectedThreads.length > 0" variant="success" size="sm">
                    {{ formData.selectedThreads.length }} ausgewählt
                  </LTag>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <!-- Auto-selection info -->
                <v-alert v-if="formData.selectedThreads.length > 0 && authImport.result?.thread_ids?.length > 0" type="info" variant="tonal" class="mb-4" density="compact">
                  <v-icon size="16" class="mr-1">mdi-check-circle</v-icon>
                  {{ formData.selectedThreads.length }} Threads wurden automatisch aus dem Import ausgewählt.
                </v-alert>
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
import {reactive, onMounted, computed, ref} from 'vue';
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
    const folderInputRef = ref(null);
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
      mode: 'files',
      files: [],
      folderFiles: [],
      jsonText: '',
      isImporting: false,
      error: '',
      result: null
    });

    // Computed: Can import (has data to import)
    const canImport = computed(() => {
      if (authImport.mode === 'files') {
        return authImport.files && authImport.files.length > 0;
      }
      if (authImport.mode === 'folder') {
        return authImport.folderFiles && authImport.folderFiles.length > 0;
      }
      if (authImport.mode === 'text') {
        return authImport.jsonText && authImport.jsonText.trim().length > 0;
      }
      return false;
    });

    // Computed: Import button label
    const importButtonLabel = computed(() => {
      if (authImport.mode === 'files' && authImport.files?.length) {
        return `${authImport.files.length} Datei(en) importieren`;
      }
      if (authImport.mode === 'folder' && authImport.folderFiles?.length) {
        return `${authImport.folderFiles.length} Datei(en) importieren`;
      }
      return 'Importieren';
    });

    // Folder upload handlers
    const triggerFolderSelect = () => {
      if (folderInputRef.value) {
        folderInputRef.value.click();
      }
    };

    const handleFolderSelect = (event) => {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      // Filter only .json files
      const jsonFiles = Array.from(files).filter(file =>
        file.name.toLowerCase().endsWith('.json')
      );

      authImport.folderFiles = jsonFiles;
      authImport.error = '';
      authImport.result = null;

      if (jsonFiles.length === 0) {
        authImport.error = 'Keine JSON-Dateien im Ordner gefunden.';
      }
    };

    const clearFolderFiles = () => {
      authImport.folderFiles = [];
      if (folderInputRef.value) {
        folderInputRef.value.value = '';
      }
    };


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

      const readFile = (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve({ name: file.name, content: String(reader.result || '') });
        reader.onerror = () => reject(new Error(`Datei "${file.name}" konnte nicht gelesen werden.`));
        reader.readAsText(file);
      });

      try {
        // Mode: Text
        if (authImport.mode === 'text') {
          const text = String(authImport.jsonText || '').trim();
          if (!text) {
            authImport.error = 'Bitte JSON einfügen.';
            return;
          }
          const parsed = JSON.parse(text);
          if (Array.isArray(parsed)) {
            items.push(...parsed);
          } else {
            items.push(parsed);
          }
        }
        // Mode: Files
        else if (authImport.mode === 'files') {
          if (!authImport.files || authImport.files.length === 0) {
            authImport.error = 'Bitte eine oder mehrere JSON-Dateien auswählen.';
            return;
          }
          const fileResults = await Promise.all(authImport.files.map(readFile));
          for (const { name, content } of fileResults) {
            try {
              const parsed = JSON.parse(content);
              if (Array.isArray(parsed)) items.push(...parsed);
              else items.push(parsed);
            } catch (e) {
              authImport.error = `Datei "${name}" enthält ungültiges JSON.`;
              return;
            }
          }
        }
        // Mode: Folder
        else if (authImport.mode === 'folder') {
          if (!authImport.folderFiles || authImport.folderFiles.length === 0) {
            authImport.error = 'Bitte einen Ordner mit JSON-Dateien auswählen.';
            return;
          }
          const fileResults = await Promise.all(authImport.folderFiles.map(readFile));
          for (const { name, content } of fileResults) {
            try {
              const parsed = JSON.parse(content);
              if (Array.isArray(parsed)) items.push(...parsed);
              else items.push(parsed);
            } catch (e) {
              authImport.error = `Datei "${name}" enthält ungültiges JSON.`;
              return;
            }
          }
        }
      } catch (e) {
        authImport.error = e?.message || 'Fehler beim Lesen der Daten.';
        return;
      }

      if (items.length === 0) {
        authImport.error = 'Keine gültigen Items zum Importieren gefunden.';
        return;
      }

      authImport.isImporting = true;
      try {
        authImport.result = await importAuthenticityDataset(items.length === 1 ? items[0] : items);
        // Refresh threads list after successful import
        await fetchThreads(formData.selectedCategory);

        // Auto-select all imported threads
        if (authImport.result?.thread_ids?.length > 0) {
          const importedIds = authImport.result.thread_ids;
          // Add imported thread IDs to selection (avoid duplicates)
          const currentSelection = new Set(formData.selectedThreads);
          importedIds.forEach(id => currentSelection.add(id));
          formData.selectedThreads = Array.from(currentSelection);
        }
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
      authImport.mode = 'files';
      authImport.files = [];
      authImport.folderFiles = [];
      authImport.jsonText = '';
      authImport.isImporting = false;
      authImport.error = '';
      authImport.result = null;
      if (folderInputRef.value) {
        folderInputRef.value.value = '';
      }

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
      canImport,
      importButtonLabel,
      folderInputRef,
      openDialog,
      closeDialog,
      handleCategoryChange,
      handleCheckboxChange,
      importAuthenticity,
      triggerFolderSelect,
      handleFolderSelect,
      clearFolderFiles,
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

/* Import Section */
.import-section {
  min-height: 100px;
}

/* Folder Upload */
.folder-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.folder-input-hidden {
  display: none;
}

.folder-dropzone {
  width: 100%;
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.2);
  background: rgba(var(--v-theme-surface-variant), 0.1);
  transition: all 0.2s ease;
}

.folder-dropzone:hover {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}

.folder-dropzone.has-files {
  border-color: rgb(var(--v-theme-success));
  background: rgba(var(--v-theme-success), 0.05);
  border-style: solid;
}

.folder-dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px;
}
</style>
