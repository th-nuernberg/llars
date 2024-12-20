<template>
  <div class="container">
    <!-- Notification Snackbar -->
    <v-snackbar
      v-model="showNotification"
      :timeout="notificationTimeout"
      :color="notificationColor"
    >
      {{ notificationMessage }}
    </v-snackbar>

    <div class="main-layout">
      <!-- Main Content Area -->
      <div class="content-area">
        <!-- Blocks Container -->
        <div class="blocks-container">
          <draggable
            v-model="blocks"
            class="blocks-list"
            item-key="name"
            handle=".drag-handle"
            @change="handleBlockReorder"
          >
            <template #item="{ element, index }">
              <v-card class="block-card mb-4">
                <v-card-title class="d-flex align-center pa-4">
                  <v-icon class="mr-2 cursor-move drag-handle text-grey-darken-1" size="small">
                    mdi-drag-horizontal-variant
                  </v-icon>
                  {{ element.name }}
                  <v-spacer></v-spacer>
                  <v-btn
                    icon="mdi-delete"
                    variant="text"
                    density="comfortable"
                    color="grey-darken-1"
                    @click="openDeleteDialog(index)"
                    class="delete-btn"
                  >
                  </v-btn>
                </v-card-title>
                <v-card-text class="pa-4">
                  <div class="textarea-container">
                    <v-textarea
                      v-model="element.content"
                      outlined
                      hide-details
                      rows="4"
                      class="prompt-textarea"
                      :data-block-id="element.name"
                      @update:model-value="value => handleTextChange(element.name, value)"
                      @focus="handleCursorUpdate(element.name)"
                    ></v-textarea>
                  </div>
                </v-card-text>
              </v-card>
            </template>
          </draggable>

          <v-skeleton-loader
            v-if="loadingBlocks && blocks.length === 0"
            type="article"
            class="mb-4"
          ></v-skeleton-loader>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="sidebar">
        <!-- Collaborators List -->
        <v-card class="mb-4 collaborators-card">
          <v-card-title class="text-subtitle-1">
            Aktuell im Raum
          </v-card-title>
          <v-card-text>
            <div class="collaborators-list">
              <v-chip
                v-for="collaborator in otherUsers"
                :key="collaborator.id"
                small
                class="mb-2 mr-2"
                :style="{ backgroundColor: getUsernameColor(collaborator.username), color: 'white' }"
              >
                {{ collaborator.username }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>

        <v-btn
          color="primary"
          block
          class="mb-4"
          @click="addBlockPrompt"
        >
          <v-icon left>mdi-plus</v-icon>
          Neuen Block hinzufügen
        </v-btn>

        <v-btn
          color="success"
          block
          class="mb-4"
          @click="savePrompt"
        >
          <v-icon left>mdi-content-save</v-icon>
          Prompt speichern
        </v-btn>

        <v-btn
          color="info"
          block
          class="mb-4"
          @click="openPreviewModal"
        >
          <v-icon left>mdi-eye</v-icon>
          Vorschau
        </v-btn>

        <v-btn
          color="secondary"
          block
          class="mb-4"
          @click="downloadJSON"
        >
          <v-icon left>mdi-download</v-icon>
          JSON herunterladen
        </v-btn>

        <v-btn
          color="primary"
          block
          class="mb-4"
          @click="$refs.fileInput.click()"
        >
          <v-icon left>mdi-upload</v-icon>
          JSON hochladen
        </v-btn>
        <input
          type="file"
          ref="fileInput"
          accept=".json"
          style="display: none"
          @change="handleFileUpload"
        />

        <v-btn
          block
          color="grey"
          @click="goBack"
        >
          <v-icon left>mdi-arrow-left</v-icon>
          Zurück zur Übersicht
        </v-btn>

        <!-- Share Card für Owner -->
        <v-card class="mt-4" v-if="isOwner">
          <v-card-title class="text-subtitle-1">
            Prompt teilen
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="shareWithUser"
              label="Benutzername"
              density="comfortable"
              class="mb-4"
              placeholder="Mit Benutzer teilen"
              hide-details
            />
            <v-btn
              block
              color="info"
              class="mb-4"
              :disabled="!shareWithUser"
              @click="sharePrompt"
            >
              <v-icon left>mdi-share</v-icon>
              Teilen
            </v-btn>

            <!-- Liste der geteilten Benutzer -->
            <template v-if="sharedUsers.length > 0">
              <v-divider class="my-4"></v-divider>
              <div class="d-flex align-center mb-2">
                <span class="text-subtitle-2">Geteilt mit:</span>
                <v-chip
                  size="small"
                  color="info"
                  class="ml-2"
                >
                  {{ sharedUsers.length }}
                </v-chip>
              </div>
              <v-list density="compact">
                <v-list-item
                  v-for="user in sharedUsers"
                  :key="user"
                  :value="user"
                >
                  <template v-slot:prepend>
                    <v-icon size="small" color="info">mdi-account</v-icon>
                  </template>
                  {{ user }}
                  <template v-slot:append>
                    <v-btn
                      icon="mdi-delete"
                      size="small"
                      color="error"
                      variant="text"
                      @click="unsharePrompt(user)"
                    >
                      <v-icon size="small">mdi-delete</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </template>
          </v-card-text>
        </v-card>

        <!-- Read-only Share Card für geteilte Benutzer -->
        <v-card class="mt-4" v-else-if="sharedUsers.length > 0">
          <v-card-title class="text-subtitle-1">
            Geteilt mit
          </v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item
                v-for="user in sharedUsers"
                :key="user"
                :value="user"
              >
                <template v-slot:prepend>
                  <v-icon size="small" color="info">mdi-account</v-icon>
                </template>
                {{ user }}
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <v-card class="room-info" v-if="roomInfo">
          <v-card-title class="text-subtitle-1">
            Room Information
          </v-card-title>
          <v-card-text>
            <p>Room ID: {{ roomInfo.room }}</p>
            <p>Connected Users: {{ roomInfo.users ? roomInfo.users.length : 0 }}</p>
          </v-card-text>
        </v-card>
      </div>

    </div>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          Block löschen
        </v-card-title>
        <v-card-text class="pa-4">
          Möchten Sie diesen Block wirklich löschen?
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            @click="showDeleteDialog = false"
          >
            Abbrechen
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            @click="confirmDelete"
          >
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
        <v-dialog v-model="showPreviewModal" max-width="800">
      <v-card>
        <v-card-title class="text-h6 pa-4">
          Vorschau
        </v-card-title>
        <v-card-text class="pa-4">
          <div v-html="formattedPreviewText"></div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="showPreviewModal = false"
          >
            Schließen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>


<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import {io} from 'socket.io-client';
import draggable from 'vuedraggable';
import { useRoute, useRouter } from 'vue-router';


const socket = ref(null);
const blocks = ref([]);
const roomInfo = ref(null);
const userId = ref(null);
const loadingBlocks = ref(true);
const showDeleteDialog = ref(false);
const blockToDelete = ref(null);

const showPreviewModal = ref(false);

const route = useRoute();
const router = useRouter();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);

const username = localStorage.getItem('username') || 'Unbekannter Benutzer';

const shareWithUser = ref('');
const sharedUsers = ref([]);
const owner = ref('');
const isSharedPrompt = ref(false);

// Farbmanagement nach Usernames
const cursorColors = ref({});
const usedColors = ref(new Set());

const availableColors = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
  '#D4A5A5', '#9B59B6', '#3498DB', '#2ECC71', '#E74C3C',
  '#F1C40F', '#8E44AD', '#16A085', '#E67E22', '#2C3E50',
  '#27AE60', '#D35400', '#7F8C8D', '#C0392B', '#1ABC9C'
];

function hexToHSL(hex) {
  hex = hex.replace(/#/g, '');
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s;
  let l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h *= 60;
  }

  return {h, s: s * 100, l: l * 100};
}

function HSLToHex(h, s, l) {
  s /= 100;
  l /= 100;
  const k = n => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = n =>
    l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));

  const toHex = n => {
    const hex = Math.round(255 * n).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };

  return `#${toHex(f(0))}${toHex(f(8))}${toHex(f(4))}`;
}

function getUnusedColor() {
  const unusedColors = availableColors.filter(color => !usedColors.value.has(color));
  if (unusedColors.length === 0) {
    const baseColor = availableColors[Math.floor(Math.random() * availableColors.length)];
    const hslColor = hexToHSL(baseColor);
    hslColor.h = (hslColor.h + 20) % 360;
    return HSLToHex(hslColor.h, hslColor.s, hslColor.l);
  }
  return unusedColors[Math.floor(Math.random() * unusedColors.length)];
}

function getUsernameColor(user_name) {
  console.log('Getting color for user:', user_name);
  if (!cursorColors.value[user_name]) {
    const newColor = getUnusedColor();
    cursorColors.value[user_name] = newColor;
    usedColors.value.add(newColor);
  }
  return cursorColors.value[user_name];
}

const showNotification = ref(false);
const notificationMessage = ref('');
const notificationColor = ref('success');
const notificationTimeout = ref(3000);

function showSuccessNotification(message) {
  notificationMessage.value = message;
  notificationColor.value = 'success';
  showNotification.value = true;
}

function showErrorNotification(message) {
  notificationMessage.value = message;
  notificationColor.value = 'error';
  showNotification.value = true;
}

const otherUsers = computed(() => {
  if (!roomInfo.value || !roomInfo.value.users) return [];
  // roomInfo.value.users ist jetzt ein Array von Objekten {id, username}
  // Filtere den eigenen User heraus
  return roomInfo.value.users.filter(u => u.id !== userId.value);
});

function updateUserList(users) {
  console.log('Updating user list:', users);
  if (roomInfo.value) {
    roomInfo.value = {
      ...roomInfo.value,
      users: users
    };
  }
}

function buildUpdatesObject() {
  const updates = {};
  blocks.value.forEach((block, idx) => {
    updates[block.name] = {
      new_position: idx,
      content: block.content
    };
  });
  return updates;
}

const handleTextChange = (blockId, newContent) => {
  if (socket.value) {
    socket.value.emit('pe_text_update', {
      blockId,
      content: newContent,
      room: roomId.value,
      userId: userId.value
    });
  }
};

function handleBlockReorder() {
  if (socket.value) {
    const updates = buildUpdatesObject();
    socket.value.emit('pe_update_blocks', {
      room: roomId.value,
      updates
    });
  }
}

function handleCursorUpdate(blockId) {
  if (socket.value) {
    socket.value.emit('pe_cursor_update', {
      room: roomId.value,
      block_id: blockId,
      position: 0
    });
  }
}

function addBlockPrompt() {
  const blockName = prompt('Name des neuen Blocks?');
  if (!blockName) return;
  const existing = blocks.value.find(b => b.name === blockName);
  if (existing) {
    alert('Ein Block mit diesem Namen existiert bereits!');
    return;
  }
  blocks.value.push({
    name: blockName,
    content: ''
  });
  handleBlockReorder();
}

function openDeleteDialog(index) {
  blockToDelete.value = index;
  showDeleteDialog.value = true;
}

function confirmDelete() {
  if (blockToDelete.value !== null) {
    blocks.value.splice(blockToDelete.value, 1);
    handleBlockReorder();
    showDeleteDialog.value = false;
    blockToDelete.value = null;
  }
}

function processReceivedContent(content) {
  if (!content || !content.blocks) return;
  const blocksObject = content.blocks;
  const blocksArray = Object.entries(blocksObject).map(([name, blockData]) => ({
    name,
    content: blockData.content,
    position: blockData.position
  }));
  blocksArray.sort((a, b) => a.position - b.position);
  blocks.value = blocksArray;
  loadingBlocks.value = false;
}

onMounted(() => {
  socket.value = io(import.meta.env.VITE_API_BASE_URL + '/pe');

  socket.value.emit('pe_connect', {username}, () => {
    console.log('WebSocket connection established');
  });

  socket.value.on('pe_connected', (data) => {
    console.log('Connected to server:', data);
    userId.value = data.user_id;
  });

  socket.value.on('connect', () => {
    socket.value.emit('pe_join_room', {room: roomId.value, prompt_id: promptId.value}, () => {
      console.log('Joined room:', roomId.value);
    });
  });

  socket.value.on('pe_joined_room', (data) => {
    console.log('Received room data:', data);
    if (data.content) {
      processReceivedContent(data.content);
    }
    roomInfo.value = {
      room: data.room,
      users: data.users || []
    };
  });

  socket.value.on('pe_text_update', (data) => {
    console.log('Received updated text content:', data);
    processReceivedContent(data);
    if (data.users) {
      roomInfo.value.users = data.users;
    }
  });

  socket.value.on('pe_blocks_updated', (data) => {
    console.log('Received blocks updated content:', data);
    processReceivedContent(data);
    if (data.users) {
      roomInfo.value.users = data.users;
    }
  });

  socket.value.on('pe_user_left', (data) => {
    console.log('User left room:', data);
    // Finde den Benutzer, der den Raum verlassen hat
    const leavingUser = roomInfo.value.users.find(u => u.id === data.user_id);
    if (leavingUser) {
      const leavingUsername = leavingUser.username;
      if (cursorColors.value[leavingUsername]) {
        usedColors.value.delete(cursorColors.value[leavingUsername]);
        delete cursorColors.value[leavingUsername];
      }
    }
    updateUserList(data.users);
  });

  socket.value.on('pe_cursor_updated', (data) => {
    console.log('Cursor updated:', data);
    // Hier wird aktuell nichts weitergemacht.
  });
  fetchPromptDetails()
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.emit('pe_leave_room');
    socket.value.disconnect();
  }
});

async function savePrompt() {
  try {
    const apiKey = localStorage.getItem('api_key');
    if (!apiKey) {
      console.error('API key not found');
      showErrorNotification('API-Schlüssel nicht gefunden');
      return;
    }

    const response = await fetch(`/api/prompts/${promptId.value}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': apiKey
      },
      body: JSON.stringify({
        content: buildBlocksObject()
      })
    });

    if (response.ok) {
      console.log('Prompt saved successfully');
      showSuccessNotification('Prompt erfolgreich gespeichert');
    } else {
      console.error('Error saving prompt:', response.statusText);
      showErrorNotification('Fehler beim Speichern des Prompts');
    }
  } catch (error) {
    console.error('Error saving prompt:', error);
    showErrorNotification('Fehler beim Speichern des Prompts');
  }
}

function buildBlocksObject() {
  const blocksObject = {};
  blocks.value.forEach((block) => {
    blocksObject[block.name] = {
      content: block.content,
      position: block.position
    };
  });
  return blocksObject;
}


const formattedPreviewText = computed(() => {
  return blocks.value
    .map(block => block.content)
    .join('\n\n')
    .replace(/\n/g, '<br>');
});

function openPreviewModal() {
  showPreviewModal.value = true;
}

function downloadJSON() {
  const jsonData = blocks.value.reduce((data, block) => {
    data[block.name] = block.content;
    return data;
  }, {});

  const jsonString = JSON.stringify(jsonData, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = 'prompt_data.json';
  link.click();

  URL.revokeObjectURL(url);
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const fileContent = await file.text();
    const jsonData = JSON.parse(fileContent);

    // Convert JSON data to blocks format
    const newBlocks = Object.entries(jsonData).map(([name, content], index) => ({
      name,
      content,
      position: index
    }));

    // Update blocks
    blocks.value = newBlocks;

    // Trigger block reorder to sync with other users
    handleBlockReorder();

    showSuccessNotification('JSON erfolgreich importiert');
  } catch (error) {
    console.error('Error parsing JSON file:', error);
    showErrorNotification('Fehler beim Parsen der JSON-Datei');
  }

  // Reset file input
  event.target.value = '';
}

function goBack() {
  router.push('/promptengineering');
}

const isOwner = computed(() => {
  const currentUser = localStorage.getItem('username');
  return owner.value === currentUser;
});

// Neue Funktionen für das Teilen
async function sharePrompt() {
  try {
    const apiKey = localStorage.getItem('api_key');
    const response = await fetch(`/api/prompts/${promptId.value}/share`, {
      method: 'POST',
      headers: {
        'Authorization': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        shared_with: shareWithUser.value
      })
    });

    if (response.ok) {
      await fetchPromptDetails(); // Funktion zum Neuladen der Prompt-Details
      showSuccessNotification(`Prompt wurde erfolgreich mit ${shareWithUser.value} geteilt!`);
      shareWithUser.value = '';
    } else {
      const errorData = await response.json();
      showErrorNotification(errorData.error || 'Fehler beim Teilen des Prompts');
    }
  } catch (error) {
    console.error('Error sharing prompt:', error);
    showErrorNotification('Fehler beim Teilen des Prompts');
  }
}

async function unsharePrompt(username) {
  try {
    const apiKey = localStorage.getItem('api_key');
    const response = await fetch(`/api/prompts/${promptId.value}/unshare`, {
      method: 'POST',
      headers: {
        'Authorization': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        unshare_with: username
      })
    });

    if (response.ok) {
      const index = sharedUsers.value.indexOf(username);
      if (index > -1) {
        sharedUsers.value.splice(index, 1);
      }
      showSuccessNotification(`Freigabe für ${username} wurde aufgehoben`);
    } else {
      const errorData = await response.json();
      showErrorNotification(errorData.error || 'Fehler beim Aufheben der Freigabe');
    }
  } catch (error) {
    console.error('Error unsharing prompt:', error);
    showErrorNotification('Fehler beim Aufheben der Freigabe');
  }
}

async function fetchPromptDetails() {
  console.log('Fetching prompt details...');
  try {
    const apiKey = localStorage.getItem('api_key');
    const response = await fetch(`/api/prompts/${promptId.value}`, {
      headers: {
        'Authorization': apiKey
      }
    });

    if (response.ok) {
      const data = await response.json();
      owner.value = data.owner || '';
      isSharedPrompt.value = data.is_shared || false;
      sharedUsers.value = data.shared_with || [];
    }
  } catch (error) {
    console.error('Error fetching prompt details:', error);
    showErrorNotification('Fehler beim Laden der Prompt-Details');
  }
}

</script>

<style scoped>
.container {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.main-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 24px;
  height: calc(100vh - 48px);
}

.content-area {
  overflow-y: auto;
  padding-right: 16px;
}

.sidebar {
  height: 100%;
  overflow-y: auto;
}

.block-card {
  border-radius: 8px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.block-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.textarea-container {
  position: relative;
}

.prompt-textarea {
  font-family: 'Roboto Mono', monospace;
  width: 100%;
  box-sizing: border-box;
  border-radius: 4px;
}

.collaborators-card {
  border-radius: 8px;
}

.collaborators-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.delete-btn {
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.delete-btn:hover {
  opacity: 1;
}

.drag-handle {
  cursor: move;
}
</style>
