<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <div class="sidebar-content">
      <v-spacer></v-spacer>

      <!-- Online Users Liste -->
      <div class="users-list">
        <h3>Online Users:</h3>
        <div v-for="(user, id) in users" :key="id" class="user-item">
          <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
          {{ user.username }}
        </div>
      </div>

      <!-- Buttons für Aktionen -->

      <!-- Zurück-Button -->
      <button
        @click="goToOverview"
        class="action-button back-button">
        <v-icon class="button-icon">mdi-arrow-left</v-icon>
        Zur Übersicht
      </button>

      <!-- Neuen Block hinzufügen -->
      <button @click="$emit('showAddBlockDialog')" class="action-button add-block-button">
        <v-icon class="button-icon"> mdi-plus</v-icon>
        Neuer Block
      </button>

      <!-- Vorschau anzeigen -->
      <button @click="showPreview = true" class="action-button preview-button">
        <v-icon class="button-icon"> mdi-eye</v-icon>
        Vorschau anzeigen
      </button>

      <!-- Download Prompt Button -->
      <button @click="downloadPrompt" class="action-button download-button">
        <v-icon class="button-icon">mdi-download</v-icon>
        Download Prompt
      </button>

      <button @click="triggerJsonUpload" class="action-button upload-button">
        <v-icon class="button-icon">mdi-upload</v-icon>
        Prompt hochladen
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
});



const router = useRouter();

// Ganz oben im <script setup>:
const emit = defineEmits(['showAddBlockDialog', 'refreshPromptDetails']);

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

const handleJsonFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const fileContent = await file.text(); // Dateiinhalt als String
    const jsonData = JSON.parse(fileContent); // als Objekt parsen

    // JSON-Keys = Blocknamen, Values = Blockinhalte
    // -> an Parent-Komponente weitergeben (oder hier direkt verarbeiten)
    emit('uploadBlocksFromJson', jsonData);
    // Nach dem Upload den file-input zurücksetzen, damit man jederzeit neu hochladen kann
    event.target.value = '';
  } catch (error) {
    console.error('Fehler beim JSON-Upload:', error);
    // ggf. shareError.value o.Ä. befüllen oder Snackbar anzeigen
  }
};
// SHARE
const sharePromptWithUser = async () => {
  if (!props.isOwner) return; // Sicherheitshalber
  // if (!userToShare.value.trim()) return;

  try {
    const apiKey = localStorage.getItem('api_key');
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/share`,
      {
        method: 'POST',
        headers: {
          'Authorization': apiKey,
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
    const apiKey = localStorage.getItem('api_key');
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/unshare`,
      {
        method: 'POST',
        headers: {
          'Authorization': apiKey,
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

  // Erstelle ein unsichtbares <a> Element für den Download
  const a = document.createElement('a');
  a.href = url;
  a.download = 'prompt.json'; // Name der Datei, die heruntergeladen wird

  // Füge das Element zum DOM hinzu und klicke es programmatisch
  document.body.appendChild(a);
  a.click();

  // Cleanup: Entferne das Element und die URL
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};


const goToOverview = () => {
  router.push('/promptengineering');
};
</script>

<style scoped>
.sidebar {
  width: 250px;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
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
  background: white;
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
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
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
  color: #666;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.close-button:hover {
  color: #e74c3c;
}

.preview-block {
  margin-bottom: 30px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
}

.preview-block:last-child {
  margin-bottom: 0;
}

.preview-block h4 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  color: #2c3e50;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 8px;
}

.preview-block p {
  margin: 0;
  font-size: 1rem;
  color: #333;
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

.add-block-button {
  background-color: #81b68b;  /* secondary color */
}

.add-block-button:hover {
  background-color: #6ca077;  /* slightly darker */
}

.preview-button {
  background-color: #b0ca97;  /* primary color */
}

.preview-button:hover {
  background-color: #9bb582;  /* slightly darker */
}

.download-button {
  background-color: #92b199;  /* Mix zwischen primary und secondary */
}

.download-button:hover {
  background-color: #7d9c84;  /* slightly darker */
}

.upload-button {
  background-color: #D1BC8A; /* oder eine andere Farbe */
}

.upload-button:hover {
  background-color: #aa9768;
}


.users-list {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.users-list h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
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
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  margin-top: 20px;
}

.sharing-section h3 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #333;
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
  color: #666;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.unshare-button:hover {
  background-color: #f0f0f0;
  color: #e74c3c;
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
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-size: 0.9rem;
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
