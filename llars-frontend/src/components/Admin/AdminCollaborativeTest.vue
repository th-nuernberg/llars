<template>
  <div class="container">
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
                  <v-icon class="mr-2 cursor-move drag-handle text-grey-darken-1">
                    mdi-drag
                  </v-icon>
                  {{ element.name }}
                  <v-spacer></v-spacer>
                  <v-btn
                    icon="mdi-delete"
                    variant="text"
                    density="comfortable"
                    color="grey-darken-1"
                    @click="removeBlock(index)"
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
                :style="{ backgroundColor: getCursorColor(collaborator.id), color: 'white' }"
              >
                {{ collaborator.username }}
              </v-chip>
            </div>
          </v-card-text>
        </v-card>

        <!-- Add Block Button -->
        <v-btn
          color="primary"
          block
          class="mb-4"
          @click="addBlockPrompt"
        >
          Neuen Block hinzufügen
        </v-btn>

        <!-- Room Info -->
        <v-card class="room-info" v-if="roomInfo">
          <v-card-title class="text-subtitle-1">
            Room Information
          </v-card-title>
          <v-card-text>
            <p>Room ID: {{ roomInfo.room }}</p>
            <p>Connected Users: {{ Object.keys(roomInfo.users || {}).length }}</p>
          </v-card-text>
        </v-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { io } from 'socket.io-client';
import draggable from 'vuedraggable';
import { useRoute } from 'vue-router';

const socket = ref(null);
const blocks = ref([]);
const roomInfo = ref(null);
const userId = ref(null);
const loadingBlocks = ref(true);

// Beispielsweise könnte promptId über die Route ausgelesen werden.
const route = useRoute();
const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);

const username = localStorage.getItem('username') || 'Unbekannter Benutzer';

// Farbenverwaltung
const cursorColors = ref({});
const usedColors = ref(new Set());

// Erweiterte Farbliste für mehr Variationen
const availableColors = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD',
  '#D4A5A5', '#9B59B6', '#3498DB', '#2ECC71', '#E74C3C',
  '#F1C40F', '#8E44AD', '#16A085', '#E67E22', '#2C3E50',
  '#27AE60', '#D35400', '#7F8C8D', '#C0392B', '#1ABC9C'
];

function getUnusedColor() {
  // Filtere bereits verwendete Farben heraus
  const unusedColors = availableColors.filter(color => !usedColors.value.has(color));

  // Wenn alle Farben verwendet wurden, erstelle neue Farbtöne
  if (unusedColors.length === 0) {
    const baseColor = availableColors[Math.floor(Math.random() * availableColors.length)];
    // Modifiziere den Farbton leicht
    const hslColor = hexToHSL(baseColor);
    hslColor.h = (hslColor.h + 20) % 360; // Verschiebe den Farbton
    return HSLToHex(hslColor.h, hslColor.s, hslColor.l);
  }

  return unusedColors[Math.floor(Math.random() * unusedColors.length)];
}

// Hilfsfunktionen für Farbkonvertierung
function hexToHSL(hex) {
  // Entferne das #
  hex = hex.replace(/#/g, '');

  // Konvertiere zu RGB
  const r = parseInt(hex.substring(0, 2), 16) / 255;
  const g = parseInt(hex.substring(2, 4), 16) / 255;
  const b = parseInt(hex.substring(4, 6), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;

  if (max === min) {
    h = s = 0;
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h *= 60;
  }

  return { h, s: s * 100, l: l * 100 };
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

function getCursorColor(user_id) {
  if (!cursorColors.value[user_id]) {
    const newColor = getUnusedColor();
    cursorColors.value[user_id] = newColor;
    usedColors.value.add(newColor);
  }
  return cursorColors.value[user_id];
}

// Verbesserte otherUsers computed property
const otherUsers = computed(() => {
  if (!roomInfo.value || !roomInfo.value.users) return [];

  return Object.entries(roomInfo.value.users)
    .filter(([id]) => id !== userId.value)
    .map(([id, username]) => ({
      id,
      username: typeof username === 'object' ? username.username : username
    }));
});

// Verbesserte updateUserList Funktion
function updateUserList(users) {
  console.log('Updating user list:', users);
  if (roomInfo.value) {
    roomInfo.value = {
      ...roomInfo.value,
      users: users
    };
  }
}

// Diese Funktion baut das "updates"-Objekt aus dem aktuellen Stand der blocks auf.
// Dabei werden die Positionen 1-basiert oder 0-basiert gezählt. Wir nehmen hier 1-basiert an.
function buildUpdatesObject() {
  const updates = {};
  blocks.value.forEach((block, idx) => {
    // Stelle sicher, dass wir den Inhalt mit übergeben, um konsistente Daten zu halten.
    updates[block.name] = {
      new_position: idx,
      content: block.content
    };
  });
  return updates;
}

const handleTextChange = (blockId, newContent) => {
  // Hier werden Texteingaben verarbeitet.
  // Statt bei jedem Tastendruck zu senden, könntest du auch Debouncing nutzen.
  // Da wir aber die komplette Logik über pe_update_blocks steuern wollen,
  // schicken wir Textupdates separat oder aktualisieren periodisch.
  // Für das Beispiel lassen wir pe_text_update erstmal weiterlaufen.
  if (socket.value) {
    socket.value.emit('pe_text_update', {
      blockId,
      content: newContent,
      room: roomId.value,
      userId: userId.value
    });
  }
};

// Diese Methode wird aufgerufen, wenn die Reihenfolge (oder die Anzahl) der Blöcke sich ändert.
// Wir senden dann über pe_update_blocks den kompletten neuen Stand.
function handleBlockReorder() {
  if (socket.value) {
    const updates = buildUpdatesObject();
    socket.value.emit('pe_update_blocks', {
      room: roomId.value,
      updates
    });
  }
}

// Block hinzufügen
function addBlockPrompt() {
  const blockName = prompt('Name des neuen Blocks?');
  if (!blockName) return;

  // Prüfen ob der Name bereits existiert
  const existing = blocks.value.find(b => b.name === blockName);
  if (existing) {
    alert('Ein Block mit diesem Namen existiert bereits!');
    return;
  }

  blocks.value.push({
    name: blockName,
    content: ''
  });

  // Sobald sich die Blöcke geändert haben, schicken wir ein Update.
  handleBlockReorder();
}

// Block entfernen
function removeBlock(index) {
  blocks.value.splice(index, 1);
  handleBlockReorder();
}

// Inhalt vom Server verarbeiten
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

  // Verbindung herstellen
  socket.value.emit('pe_connect', { username }, () => {
    console.log('WebSocket connection established');
  });

  socket.value.on('pe_connected', (data) => {
    console.log('Connected to server:', data);
    userId.value = data.user_id;
  });

  socket.value.on('connect', () => {
    socket.value.emit('pe_join_room', { room: roomId.value, prompt_id: promptId.value }, () => {
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
      users: data.users || {}
    };
  });

  socket.value.on('pe_text_update', (data) => {
    console.log('Received updated text content:', data);
    // Aktualisiere nur Inhalte, wenn sich was geändert hat.
    // Hier bekommst du das komplette content-Objekt. Aktualisiere die Blöcke:
    processReceivedContent(data);
    // Aktualisiere RoomInfo falls nötig
    if (data.users) {
      roomInfo.value.users = data.users;
    }
  });

  // Neuer Listener für aktualisierte Blocks nach pe_update_blocks
  socket.value.on('pe_blocks_updated', (data) => {
    console.log('Received blocks updated content:', data);
    processReceivedContent(data);
    // Aktualisiere RoomInfo falls nötig
    if (data.users) {
      roomInfo.value.users = data.users;
    }
  });

  socket.value.on('pe_user_left', (data) => {
    console.log('User left room:', data);
    // Entferne die Farbe des Benutzers aus den verwendeten Farben
    if (cursorColors.value[data.user_id]) {
      usedColors.value.delete(cursorColors.value[data.user_id]);
      delete cursorColors.value[data.user_id];
    }
    updateUserList(data.users);
  });
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.emit('pe_leave_room');
    socket.value.disconnect();
  }
});
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
