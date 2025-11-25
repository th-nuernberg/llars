<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="sidebar-content">
      <v-spacer></v-spacer>
      <!-- Zurück-Button -->
      <button
        @click="goToOverview"
        class="action-button back-button">
        <v-icon class="button-icon">mdi-arrow-left</v-icon>
        Zur Übersicht
      </button>

      <!-- Online Users Liste -->
      <div class="users-list">
        <h3>Online Users:</h3>
        <div v-for="(user, id) in users" :key="id" class="user-item">
          <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
          {{ user.username }}
        </div>
      </div>

      <!-- Buttons für Aktionen -->
      <!-- Vorschau anzeigen -->
      <button @click="showPreview = true" class="action-button preview-button">
        <v-icon class="button-icon"> mdi-eye</v-icon>
        Vorschau anzeigen
      </button>

      <!-- Neuen Block hinzufügen -->
      <button @click="$emit('showAddBlockDialog')" class="action-button add-block-button">
        <v-icon class="button-icon"> mdi-plus</v-icon>
        Neuer Block
      </button>

      <!-- Download Prompt Button -->
      <button @click="downloadPrompt" class="action-button download-button">
        <v-icon class="button-icon">mdi-download</v-icon>
        Download Prompt
      </button>
      <!-- Copy Prompt Button -->
      <button @click="copyPrompt" class="action-button copy-button">
        <v-icon class="button-icon">mdi-content-copy</v-icon>
        Copy Prompt
      </button>

      <button @click="triggerJsonUpload" class="action-button upload-button">
        <v-icon class="button-icon">mdi-upload</v-icon>
        Upload Prompt
      </button>
      <!-- Prompt testen Button -->
      <button @click="$emit('triggerTestPrompt')" class="action-button test-prompt-button">
        <v-icon class="button-icon">mdi-rocket</v-icon>
        Prompt testen
      </button>

      <input
        type="file"
        ref="jsonFileInput"
        style="display: none"
        accept=".json"
        @change="handleJsonFileUpload"
      />
    </div>

    <!-- Besitzer anzeigen, falls nicht der Owner -->
    <div v-if="!isOwner && owner" class="owner-info">
      <h3>Besitzer:</h3>
      <p class="owner-name">{{ owner }}</p>
    </div>

    <!-- Prompt-Sharing -->
    <div class="sharing-section">
      <h3>Geteilt mit:</h3>
      <ul class="shared-users-list">
        <!-- Auflistung der User, mit denen geteilt ist -->
        <li v-for="user in sharedWith" :key="user" class="shared-user-item">
          {{ user }}
          <!-- Nur zeigen, wenn Owner -->
          <button
            v-if="isOwner"
            @click="unsharePromptWithUser(user)"
            class="unshare-button"
          >
            ✕
          </button>
        </li>
      </ul>

      <!-- Nur zeigen, wenn Owner -->
      <div v-if="isOwner" class="share-form">
        <input
          v-model="userToShare"
          type="text"
          placeholder="Username eingeben..."
          class="share-input"
        />
        <button @click="sharePromptWithUser" class="share-button">
          Teilen
        </button>
      </div>
      <!-- Anzeige von Fehlern -->
      <p v-if="shareError" class="error-message">{{ shareError }}</p>
    </div>

    <!-- Preview Modal mit Teleport -->
    <Teleport to="body">
      <div v-if="showPreview" class="preview-modal">
        <div class="preview-content">
          <div class="preview-header">
            <h3>Vorschau</h3>
            <button @click="showPreview = false" class="close-button">
              <v-icon>mdi-close</v-icon>
            </button>
          </div>
          <div class="preview-body">
            <div v-for="block in sortedBlocks" :key="block.id" class="preview-block">
              <h4>{{ block.title }}</h4>
              <p>{{ getBlockContent(block) }}</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
    <!-- Snackbar für kopiertes Prompt -->
    <Teleport to="body">
      <v-snackbar v-model="showCopySnackbar" :timeout="2000" color="success">
        Prompt kopiert!
      </v-snackbar>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'; // computed hinzufügen
import { useRouter } from 'vue-router';

const jsonFileInput = ref(null); // Referenz auf den unsichtbaren <input type="file">

const props = defineProps({
  users: {
    type: Object,
    required: true,
  },
  blocks: {
    type: Array,
    required: true,
  },
  promptId: {
    type: Number,
    required: true,
  },
  isOwner: {
    type: Boolean,
    default: false,
  },
  sharedWith: {
    type: Array,
    default: () => [],
  },
  owner: {
    type: String, // Neuer Prop-Typ
    required: true,
  },
  promptName: { // Neu hinzugefügt
    type: String,
    required: true,
  },
});



const router = useRouter();

// Ganz oben im <script setup>:
const emit = defineEmits(['showAddBlockDialog', 'refreshPromptDetails', 'triggerTestPrompt']);

// Im sidebar.vue
// wenn share/unshare erfolgreich war:
emit('refreshPromptDetails');

// Eingabefeld für Username:
const userToShare = ref('');
const shareError = ref('');

//UPLOAD
const triggerJsonUpload = () => {
  if (jsonFileInput.value) {
    jsonFileInput.value.click();
  }
};

// sidebar.vue <script setup>:
const handleJsonFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const fileContent = await file.text();
    const jsonData = JSON.parse(fileContent);

    // Stopp! Nicht direkt handleJsonUpload aufrufen,
    // sondern dem Parent nur "wir haben JSON data!" signalisieren:
    emit('uploadJsonFileSelected', jsonData);

    // Input zurücksetzen:
    event.target.value = '';
  } catch (error) {
    console.error('Fehler beim JSON-Upload:', error);
    // evtl. Snackbar anzeigen
  }
};

// SHARE
const sharePromptWithUser = async () => {
  if (!props.isOwner) return; // Sicherheitshalber
  // if (!userToShare.value.trim()) return;

  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/share`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          shared_with: userToShare.value.trim()
        })
      }
    );

    const data = await response.json();
    if (!response.ok) {
      // z.B. 404, 409, etc.
      shareError.value = data.error || 'Fehler beim Teilen';
    } else {
      // Erfolg => Liste aktualisieren
      userToShare.value = '';
      shareError.value = '';

      // Option 1: Prompt-Details neu laden
      // emit('refreshPromptDetails');
      // Option 2: sharedWith lokal updaten
      // props.sharedWith.push(shared_with_username);

      // Besser: Hol die aktuellen Prompt-Daten neu
      emit('refreshPromptDetails');
    }
  } catch (error) {
    shareError.value = error.message;
  }
};

const clearShareError = () => {
  setTimeout(() => {
    shareError.value = '';
  }, 15000); // 15 Sekunden
};

// UNSHARE
const unsharePromptWithUser = async (usernameToRemove) => {
  if (!props.isOwner) return; // Sicherheitshalber
  try {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/unshare`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          unshare_with: usernameToRemove, // Sende den Benutzer, der entfernt werden soll
        }),
      }
    );

    const data = await response.json();
    if (!response.ok) {
      shareError.value = data.error || 'Fehler beim Entfernen der Freigabe';
      clearShareError();
    } else {
      shareError.value = '';
      emit('refreshPromptDetails'); // Prompt-Details neu laden
    }
  } catch (error) {
    shareError.value = error.message;
  }
};




const showPreview = ref(false);
const showCopySnackbar = ref(false);

// Neue computed property für sortierte Blöcke
const sortedBlocks = computed(() => {
  return [...props.blocks].sort((a, b) => a.position - b.position);
});

const getBlockContent = (block) => {
  if (block.content && typeof block.content.toString === 'function') {
    return block.content.toString();
  }
  return '';
};

// Füge diese Funktion im script setup-Bereich hinzu
const downloadPrompt = () => {
  // Erstelle ein Objekt aus den sortierten Blöcken
  const promptData = {};

  sortedBlocks.value.forEach(block => {
    // Hole den Inhalt des Blocks und entferne zusätzliche Leerzeichen/Zeilenumbrüche am Anfang und Ende
    const content = getBlockContent(block).trim();

    // Füge den Block zum promptData Objekt hinzu
    promptData[block.title] = content;
  });

  // Konvertiere das Objekt zu einem formatierten JSON-String
  const jsonStr = JSON.stringify(promptData, null, 2);

  // Erstelle einen Blob mit dem JSON-Inhalt
  const blob = new Blob([jsonStr], { type: 'application/json' });

  // Erstelle eine URL für den Blob
  const url = window.URL.createObjectURL(blob);

  // Dynamischer Dateiname basierend auf dem `promptName`
  const sanitizeFilename = (name) => name.replace(/[^a-z0-9_\-]/gi, '_');
  const filename = `${sanitizeFilename(props.promptName || 'prompt')}.json`;


  // Erstelle ein unsichtbares <a> Element für den Download
  const a = document.createElement('a');
  a.href = url;
  a.download = filename; // Dynamischer Dateiname

  // Füge das Element zum DOM hinzu und klicke es programmatisch
  document.body.appendChild(a);
  a.click();

  // Cleanup: Entferne das Element und die URL
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

// Copy Prompt to Clipboard as JSON file
const copyPrompt = async () => {
  const promptData = {};
  sortedBlocks.value.forEach(block => {
    const content = getBlockContent(block).trim();
    promptData[block.title] = content;
  });
  const jsonStr = JSON.stringify(promptData, null, 2);
  const sanitizeFilename = (name) => name.replace(/[^a-z0-9_\-]/gi, '_');
  const file = new File([jsonStr], `${sanitizeFilename(props.promptName || 'prompt')}.json`, { type: 'application/json' });
  try {
    await navigator.clipboard.write([new ClipboardItem({ 'application/json': file })]);
  } catch (err) {
    await navigator.clipboard.writeText(jsonStr);
  }
  showCopySnackbar.value = true;
};


const goToOverview = () => {
  router.push('/promptengineering');
};
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: rgb(var(--v-theme-surface));
  border-right: 1px solid rgb(var(--v-theme-surface-variant));
  height: calc(100vh - 64px);
  position: fixed;
  top: 64px;
  left: 0;
  overflow-y: auto;
  padding: 20px;
}

.sidebar-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.preview-icon {
  font-size: 1.2em;
}

.preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  width: 100vw;
  height: 100vh;
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-content {
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin: 20px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 8px 8px 0 0;
}

.preview-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.close-button {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 8px;
  color: rgb(var(--v-theme-on-surface));
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.close-button:hover {
  color: rgb(var(--v-theme-error));
}

.preview-block {
  margin-bottom: 30px;
  padding: 15px;
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 6px;
}

.preview-block:last-child {
  margin-bottom: 0;
}

.preview-block h4 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  color: rgb(var(--v-theme-on-surface));
  border-bottom: 2px solid rgb(var(--v-theme-surface-variant));
  padding-bottom: 8px;
}

.preview-block p {
  margin: 0;
  font-size: 1rem;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.5;
  white-space: pre-wrap;
}

.action-button {
  width: 100%;
  padding: 8px 12px;
  color: white;
  border: none;
  border-radius: 16px 4px 16px 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  min-height: 40px; /* Einheitliche Höhe für alle Buttons */
}

.button-icon {
  font-size: 1.2em;
  line-height: 1;
  margin-right: 8px;
  display: flex;
  align-items: center;
}

.back-button {
  background-color: #b0ca97;  /* Heller Beige-Ton passend zum Schema */
}

.back-button:hover {
  background-color: #9bb582;  /* slightly darker */
}

.preview-button {
  background-color: #b0ca97;  /* primary color */
}

.preview-button:hover {
  background-color: #9bb582;  /* slightly darker */
}

.add-block-button {
  background-color: #81b68b;  /* secondary color */
}

.add-block-button:hover {
  background-color: #6ca077;  /* slightly darker */
}

.download-button {
  background-color: #D1BC8A;  /* Mix zwischen primary und secondary */
}

.download-button:hover {
  background-color: #aa9768;  /* slightly darker */
}

.upload-button {
  background-color: #D1BC8A; /* oder eine andere Farbe */
}

.upload-button:hover {
  background-color: #aa9768;
}

.copy-button {
  background-color: #D1BC8A;
}
.copy-button:hover {
  background-color: #aa9768;
}


.users-list {
  background-color: rgb(var(--v-theme-surface));
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.users-list h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: rgb(var(--v-theme-on-surface));
}

.user-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  font-size: 0.9rem;
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

/* Styling für Sharing Section */
.sharing-section {
  background-color: rgb(var(--v-theme-surface));
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin-top: 20px;
}

.sharing-section h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: rgb(var(--v-theme-on-surface));
}

.shared-users-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.shared-user-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 0.9rem;
}

.unshare-button {
  background: none;
  border: none;
  color: rgb(var(--v-theme-on-surface));
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.unshare-button:hover {
  background-color: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-error));
}

.share-form {
  margin-top: 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.share-input {
  width: 100%;
  padding: 8px;
  border: 1px solid rgb(var(--v-theme-surface-variant));
  border-radius: 4px;
  font-size: 0.9rem;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
}

.share-button {
  background-color: #81b68b;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 100%;
}

.share-button:hover {
  background-color: #6ca077;
}

.error-message {
  color: #e74c3c;
  font-size: 0.85rem;
  margin-top: 8px;
}

.test-prompt-button{
  background-color: #81b68b;
  color: white;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 100%;
}

.test-prompt-button:hover {
  background-color: #6ca077;
}

/* Neue computed property für sortierte Blöcke */

.owner-info {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  margin-top: 20px;
}

.owner-info h3 {
  margin: 0 0 10px;
  font-size: 1rem;
  color: #333;
}

.owner-name {
  font-size: 0.9rem;
  color: #666;
}

</style>
