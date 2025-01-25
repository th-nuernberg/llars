<!-- PromptEngineering/PromptEngineering.vue -->
<template>
  <v-container fluid>
    <!-- Header mit Titel und Button -->
    <v-row class="mb-6 align-center">
      <v-col cols="12" sm="8">
        <h1>Prompt Engineering</h1>
        <p>Wählen Sie ein Prompt aus, um es zu bearbeiten oder zu teilen.</p>
      </v-col>
      <v-col cols="12" sm="4" class="d-flex justify-end">
        <v-btn
          color="primary"
          class="prompt-create-button"
          @click="showCreateDialog = true"
          style="border-radius: 16px 4px 16px 4px"
        >
          <v-icon class="mr-2">mdi-plus</v-icon>
          Neues Prompt erstellen
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <!-- Hauptinhalt -->
      <v-col cols="12">
        <!-- Meine Prompts -->
        <h2 class="text-h5 mb-4">Meine Prompts</h2>
        <v-row>
          <template v-if="prompts.length > 0">
            <v-col cols="12" sm="6" md="4" v-for="prompt in prompts" :key="prompt.id">
              <v-card class="mb-4 case-card">
                <div class="card-actions">
                  <button @click.stop="openRenameDialog(prompt)" class="edit-button">
                    <v-icon size="small">mdi-pencil</v-icon>
                  </button>
                  <button @click.stop="deletePrompt(prompt)" class="delete-button">
                    <v-icon size="small">mdi-close</v-icon>
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
              Sie haben noch keine Prompts erstellt. Nutzen Sie den Button oben rechts, um Ihr erstes Prompt anzulegen.
            </div>
          </v-col>
        </v-row>

        <!-- Mit mir geteilte Prompts -->
        <h2 class="text-h5 mb-4 mt-6">Mit mir geteilte Prompts</h2>
        <v-row>
          <template v-if="sharedPrompts.length > 0">
            <v-col cols="12" sm="6" md="4" v-for="prompt in sharedPrompts" :key="prompt.id">
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
    </v-row>

    <!-- Dialog zum Erstellen eines neuen Prompts -->
    <div v-if="showCreateDialog" class="dialog-overlay">
      <div class="dialog-box">
        <h3>Neues Prompt erstellen</h3>
        <form @submit.prevent="savePrompt">
          <input
            v-model="newPrompt.name"
            type="text"
            placeholder="Prompt Name"
            class="block-input"
            required
          />

          <!-- User Input Bereich -->
          <div class="share-section">
            <label class="share-label">Mit Benutzern teilen:</label>
            <div class="selected-users">
              <div v-for="user in selectedUsers" :key="user" class="user-chip">
                {{ user }}
                <button
                  type="button"
                  class="remove-user-btn"
                  @click="removeUser(user)"
                >
                  ×
                </button>
              </div>
            </div>
            <input
              v-model="currentUser"
              @keydown.enter.prevent="addUser"
              type="text"
              placeholder="Benutzername eingeben und Enter drücken"
              class="block-input"
            />
          </div>

          <div class="dialog-buttons">
            <button type="button" class="cancel-button" @click="closeCreateDialog">
              Abbrechen
            </button>
            <button
              type="submit"
              class="success-button"
              :disabled="!newPrompt.name"
            >
              Erstellen
            </button>
          </div>
        </form>
      </div>
    </div>

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
const selectedUsers = ref([]);
const currentUser = ref('');

// Form State
const newPrompt = ref({ name: '' });
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
// Aktualisierte savePrompt Funktion
// Aktualisierte savePrompt Funktion
async function savePrompt() {
  if (!newPrompt.value.name) return;

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

    const promptId = response.data.prompt.id;
    const newPromptData = {
      ...response.data.prompt,
      shared_with: []
    };

    // Mit allen ausgewählten Usern teilen
    if (selectedUsers.value.length > 0) {
      for (const user of selectedUsers.value) {
        try {
          await axios.post(
            `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/share`,
            { shared_with: user },
            {
              headers: {
                'Authorization': api_key,
                'Content-Type': 'application/json',
              },
            }
          );
          newPromptData.shared_with.push(user);
        } catch (shareError) {
          console.error(`Fehler beim Teilen mit ${user}:`, shareError);
          alert(`Fehler beim Teilen mit ${user}: ${shareError.response?.data?.error || 'Unbekannter Fehler'}`);
        }
      }
    }

    // Aktualisiertes Prompt zur Liste hinzufügen
    prompts.value.push(newPromptData);

    // Dialog schließen und Erfolgsmeldung anzeigen
    closeCreateDialog();
    alert('Prompt wurde erfolgreich erstellt' +
      (newPromptData.shared_with.length > 0
        ? ` und mit ${newPromptData.shared_with.join(', ')} geteilt`
        : ''));

  } catch (error) {
    console.error('Fehler beim Speichern des Prompts:', error);
    alert(error.response?.data?.error || 'Fehler beim Speichern des Prompts');
  }
}
function removeUser(user) {
  selectedUsers.value = selectedUsers.value.filter(u => u !== user);
}
// Zuerst fügen wir eine neue Funktion zur Überprüfung des Usernamens hinzu
async function checkUserExists(username) {
  try {
    const api_key = localStorage.getItem('api_key');
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/users/check/${username}`,
      {
        headers: {
          'Authorization': api_key
        }
      }
    );
    return response.status === 200;
  } catch (error) {
    return false;
  }
}

// Dann aktualisieren wir die addUser Funktion
async function addUser() {
  const username = currentUser.value.trim();
  if (username && !selectedUsers.value.includes(username)) {
    try {
      const userExists = await checkUserExists(username);
      if (userExists) {
        selectedUsers.value.push(username);
        currentUser.value = ''; // Input leeren
      } else {
        alert(`Der Benutzer "${username}" existiert nicht.`);
      }
    } catch (error) {
      console.error('Fehler bei der Benutzerüberprüfung:', error);
      alert('Fehler bei der Überprüfung des Benutzers.');
    }
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

// Am Anfang zu den anderen refs hinzufügen:
const showCreateDialog = ref(false);

// Neue Methode zum Schließen des Create-Dialogs
function closeCreateDialog() {
  showCreateDialog.value = false;
  newPrompt.value.name = '';
  selectedUsers.value = [];
  currentUser.value = '';
}

// Modifizieren wir die savePrompt Funktion

</script>

<style scoped>
.case-card {
  cursor: pointer;
  transition: box-shadow 0.3s ease-in-out, transform 0.1s ease-in-out;
  position: relative;
  height: 105px; /* Fixe Höhe für alle Karten */
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-content {
  height: 100%;
  overflow: hidden;
}
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
/* Zum bestehenden <style> hinzufügen */
.prompt-create-button {
  width: 100%;
  margin-bottom: 20px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.dialog-box {
  background: white;
  padding: 24px;
  border-radius: 8px;
  min-width: 320px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.dialog-box h3 {
  margin: 0 0 16px 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
}

.block-input {
  width: 100%;
  margin: 10px 0;
  padding: 8px;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.95rem;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.dialog-buttons button {
  padding: 8px 14px;
  border: none;
  border-radius: 16px 4px 16px 4px;
  cursor: pointer;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog-buttons .cancel-button {
  background-color: #9e9e9e;
  color: #fff;
  transition: background-color 0.2s;
}

.dialog-buttons .cancel-button:hover {
  background-color: #7e7e7e;
}

.dialog-buttons .success-button {
  background-color: #81b68b;
  color: #fff;
  transition: background-color 0.2s;
}

.dialog-buttons .success-button:hover {
  background-color: #6ca077;
}

.dialog-buttons .success-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.share-section {
  margin: 15px 0;
}

.share-label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
  color: #666;
}

.selected-users {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  min-height: 35px;
}

.user-chip {
  display: flex;
  align-items: center;
  background-color: #81b68b;
  color: white;
  padding: 4px 8px;
  border-radius: 16px 4px 16px 4px;
  font-size: 0.9rem;
}

.remove-user-btn {
  background: none;
  border: none;
  color: white;
  margin-left: 8px;
  cursor: pointer;
  padding: 0 4px;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-user-btn:hover {
  color: #e74c3c;
}
</style>
