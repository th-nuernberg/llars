# PromptEngineering.vue
# PromptEngineering.vue
<template>
  <v-container fluid>
    <v-row>
      <!-- Linke Seite: Kacheln für bestehende Prompts -->
      <v-col cols="12" md="8">
        <h1>Prompt Engineering</h1>
        <p>Wählen Sie ein Prompt aus, um es zu bearbeiten oder zu teilen.</p>

        <!-- Meine Prompts -->
        <h2 class="text-h5 mb-4">Meine Prompts</h2>
        <v-row>
          <template v-if="prompts.length > 0">
            <v-col cols="12" sm="6" v-for="prompt in prompts" :key="prompt.id">
              <v-card class="mb-4 case-card">
                <div class="card-actions">
                  <button @click.stop="deletePrompt(prompt)" class="delete-button">
                    <v-icon size="small">mdi-close</v-icon>
                  </button>
                  <button @click.stop="openRenameDialog(prompt)" class="edit-button">
                    <v-icon size="small">mdi-pencil</v-icon>
                  </button>
                </div>
                <div class="d-flex flex-column card-content" @click="navigateToPromptDetail(prompt.id)">
                  <v-card-title class="text-truncate">{{ prompt.name }}</v-card-title>
                  <v-card-subtitle>
                    <div class="mb-2">Erstellt: {{ formatDate(prompt.created_at) }}</div>
                    <template v-if="prompt.shared_with && prompt.shared_with.length > 0">
                      <v-divider></v-divider>
                      <div class="d-flex align-center mt-2">
                        <v-icon size="small" color="#dac081" class="mr-1">mdi-share-variant</v-icon>
                        <span class="text-truncate">
                          Geteilt mit: {{ prompt.shared_with.join(', ') }}
                        </span>
                      </div>
                    </template>
                  </v-card-subtitle>
                </div>
              </v-card>
            </v-col>
          </template>
          <v-col v-else cols="12">
            <div class="text-center text-grey my-4">
              Sie haben noch keine Prompts erstellt. Nutzen Sie das Formular rechts, um Ihr erstes Prompt anzulegen.
            </div>
          </v-col>
        </v-row>

        <!-- Mit mir geteilte Prompts -->
        <h2 class="text-h5 mb-4 mt-6">Mit mir geteilte Prompts</h2>
        <v-row>
          <template v-if="sharedPrompts.length > 0">
            <v-col cols="12" sm="6" v-for="prompt in sharedPrompts" :key="prompt.id">
              <v-card class="mb-4 case-card" @click="navigateToPromptDetail(prompt.id)">
                <div class="d-flex flex-column card-content">
                  <v-card-title class="text-truncate">{{ prompt.name }}</v-card-title>
                  <v-card-subtitle>
                    <div class="mb-2">Geteilt am: {{ formatDate(prompt.shared_at) }}</div>
                    <v-divider></v-divider>
                    <div class="d-flex align-center mt-2">
                      <v-icon size="small" color="#dac081" class="mr-1">mdi-account</v-icon>
                      <span class="text-truncate">
                        Geteilt von: {{ prompt.owner }}
                      </span>
                    </div>
                  </v-card-subtitle>
                </div>
              </v-card>
            </v-col>
          </template>
          <v-col v-else cols="12">
            <div class="text-center text-grey my-4">
              Bisher wurden keine Prompts mit Ihnen geteilt.
            </div>
          </v-col>
        </v-row>
      </v-col>

      <!-- Rechte Seite: Menü zum Anlegen eines neuen Prompts -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>Neues Prompt anlegen</v-card-title>
          <v-card-text>
            <v-form ref="newPromptForm" v-model="isFormValid">
              <v-text-field
                v-model="newPrompt.name"
                label="Prompt Name"
                :rules="[rules.required]"
                required
              ></v-text-field>

              <v-text-field
                v-model="sharedWith"
                label="Mit Benutzer teilen (Optional)"
                hint="Benutzername eingeben"
              ></v-text-field>

              <v-btn
                :disabled="!isFormValid"
                color="primary"
                @click="savePrompt"
                class="mt-4"
                block
              >
                Prompt anlegen
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Dialog zum Umbenennen eines Prompts -->
    <v-dialog v-model="showRenameDialog" max-width="500px">
      <v-card>
        <v-card-title>Prompt umbenennen</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="renamePromptName"
            label="Neuer Name"
            :rules="[rules.required]"
            required
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="closeRenameDialog">Abbrechen</v-btn>
          <v-btn color="primary" @click="renamePrompt">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog zum Löschen bestätigen -->
    <v-dialog v-model="showDeleteDialog" max-width="500px">
      <v-card>
        <v-card-title>Prompt löschen</v-card-title>
        <v-card-text>
          Möchten Sie dieses Prompt wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" text @click="closeDeleteDialog">Abbrechen</v-btn>
          <v-btn color="error" @click="confirmDeletePrompt">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

// Router
const router = useRouter();

// Prompts State
const prompts = ref([]);
const sharedPrompts = ref([]);

// Form State
const newPrompt = ref({ name: '' });
const sharedWith = ref('');
const isFormValid = ref(false);
const rules = {
  required: (value) => !!value || 'Pflichtfeld',
};

// Dialog States
const showRenameDialog = ref(false);
const showDeleteDialog = ref(false);
const renamePromptName = ref('');
const selectedPrompt = ref(null);

// API Call zum Speichern eines neuen Prompts
const newPromptForm = ref(null);

// Formatiert das Datum für die Anzeige
function formatDate(dateString) {
  return new Date(dateString).toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// API Call zum Abrufen aller eigenen Prompts
async function fetchPrompts() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts`, {
      headers: {
        'Authorization': api_key,
      },
    });
    prompts.value = response.data.prompts || [];
  } catch (error) {
    console.error('Fehler beim Abrufen der Prompts:', error);
  }
}

// API Call zum Abrufen aller geteilten Prompts
async function fetchSharedPrompts() {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts/shared`, {
      headers: {
        'Authorization': api_key,
      },
    });
    sharedPrompts.value = response.data.shared_prompts || [];
  } catch (error) {
    console.error('Fehler beim Abrufen der geteilten Prompts:', error);
  }
}

// Öffnet den Dialog zum Umbenennen
function openRenameDialog(prompt) {
  selectedPrompt.value = prompt;
  renamePromptName.value = prompt.name;
  showRenameDialog.value = true;
}

// Schließt den Dialog zum Umbenennen
function closeRenameDialog() {
  showRenameDialog.value = false;
  renamePromptName.value = '';
  selectedPrompt.value = null;
}

// API Call zum Umbenennen eines Prompts
async function renamePrompt() {
  if (!selectedPrompt.value || !renamePromptName.value) return;

  try {
    const api_key = localStorage.getItem('api_key');
    await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${selectedPrompt.value.id}/rename`,
      { name: renamePromptName.value },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    // Aktualisiere den Prompt in der Liste
    const prompt = prompts.value.find(p => p.id === selectedPrompt.value.id);
    if (prompt) {
      prompt.name = renamePromptName.value;
    }

    closeRenameDialog();
  } catch (error) {
    console.error('Fehler beim Umbenennen des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Umbenennen des Prompts');
  }
}

// Öffnet den Dialog zum Löschen
function deletePrompt(prompt) {
  selectedPrompt.value = prompt;
  showDeleteDialog.value = true;
}

// Schließt den Dialog zum Löschen
function closeDeleteDialog() {
  showDeleteDialog.value = false;
  selectedPrompt.value = null;
}

// API Call zum Löschen eines Prompts
async function confirmDeletePrompt() {
  if (!selectedPrompt.value) return;

  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${selectedPrompt.value.id}`,
      {
        headers: {
          'Authorization': api_key,
        },
      }
    );

    if (response.status === 200 || response.status === 204) {
      // Entferne den Prompt aus der Liste
      prompts.value = prompts.value.filter(p => p.id !== selectedPrompt.value.id);
      closeDeleteDialog();
      // Optional: Erfolgsbenachrichtigung anzeigen
      alert('Prompt wurde erfolgreich gelöscht');
    }
  } catch (error) {
    console.error('Fehler beim Löschen des Prompts:', error);
    // Zeige spezifische Fehlermeldung vom Server oder generische Meldung
    const errorMessage = error.response?.data?.error || 'Fehler beim Löschen des Prompts';
    alert(errorMessage);
  } finally {
    selectedPrompt.value = null;
  }
}

// Aktualisierte savePrompt Funktion
async function savePrompt() {
  try {
    const api_key = localStorage.getItem('api_key');

    // Neues Prompt speichern
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts`,
      {
        name: newPrompt.value.name,
        content: { blocks: {} },
      },
      {
        headers: {
          'Authorization': api_key,
          'Content-Type': 'application/json',
        },
      }
    );

    // Prompt-Objekt mit leerer shared_with Liste erstellen
    const newPromptData = {
      ...response.data.prompt,
      shared_with: []
    };

    // Falls "Mit Benutzer teilen" ausgefüllt wurde
    if (sharedWith.value) {
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${response.data.prompt.id}/share`,
        {
          shared_with: sharedWith.value,
        },
        {
          headers: {
            'Authorization': api_key,
            'Content-Type': 'application/json',
          },
        }
      );
      newPromptData.shared_with.push(sharedWith.value);
      alert(`Prompt wurde erfolgreich mit ${sharedWith.value} geteilt.`);
    }

    // Aktualisiertes Prompt zur Liste hinzufügen
    prompts.value.push(newPromptData);

    // Felder zurücksetzen und Formular zurücksetzen
    newPrompt.value.name = '';
    sharedWith.value = '';
    newPromptForm.value?.reset();
  } catch (error) {
    console.error('Fehler beim Speichern des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Speichern des Prompts');
  }
}

// Navigation zu Prompt-Detail
function navigateToPromptDetail(promptId) {
  router.push(`/promptengineering/${promptId}`);
}

// Prompts laden, wenn die Komponente gemountet wird
onMounted(async () => {
  await Promise.all([fetchPrompts(), fetchSharedPrompts()]);
});
</script>

<style scoped>
/* NEU */
.delete-button,
.edit-button {
  padding: 4px;
  color: grey;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  width: 24px;
  height: 24px;
}

.delete-button:hover {
  background: rgba(255, 255, 255, 1);
  color: #e74c3c;
}

.edit-button:hover {
  background: rgba(255, 255, 255, 1);
  color: #6ca077;
}

/* Zusätzlich für bessere Positionierung */
.card-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  z-index: 1;
  background: rgba(255, 255, 255, 0.5);
  padding: 2px;
  border-radius: 4px;
}

/* Sicherstellen, dass der Titel nur eine Zeile einnimmt */
.v-card-title {
  line-height: 1.2;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Sicherstellen, dass die Sharing-Information bei Überlauf abgeschnitten wird */
.v-card-subtitle {
  overflow: hidden;
}

/* Text-Overflow für geteilte Benutzer */
.text-truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
