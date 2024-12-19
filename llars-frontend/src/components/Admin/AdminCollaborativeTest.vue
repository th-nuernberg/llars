<template>
  <div class="container">
    <!-- Neue Collaborators-List oben -->
    <div class="collaborators-container d-flex align-center mb-4" v-if="otherUsers.length > 0">
      <div class="collaborators-list d-flex align-center">
        <span class="mr-2">Aktuell im Raum:</span>
        <v-chip
          v-for="(collaborator, index) in otherUsers"
          :key="collaborator.id"
          small
          class="mr-2"
          :style="{ backgroundColor: getCursorColor(collaborator.id), color: 'white' }"
        >
          {{ collaborator.name }}
        </v-chip>
      </div>
    </div>

    <!-- Blocks Container -->
    <div class="blocks-container">
      <v-btn color="primary" class="mb-2" @click="addBlockPrompt">Neuen Block hinzufügen</v-btn>

      <draggable
        v-model="blocks"
        class="blocks-list"
        item-key="name"
        handle=".drag-handle"
        @change="handleBlockReorder"
      >
        <template #item="{ element, index }">
          <v-card class="mb-4">
            <v-card-title class="d-flex align-center">
              <v-icon class="mr-2 cursor-move drag-handle">
                mdi-drag
              </v-icon>
              {{ element.name }}
              <v-spacer></v-spacer>
              <v-btn icon @click="removeBlock(index)" class="ml-2">
                <v-icon color="error">mdi-delete</v-icon>
              </v-btn>
            </v-card-title>
            <v-card-text>
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

    <!-- Room Info -->
    <v-card class="room-info mt-4" v-if="roomInfo">
      <v-card-title>
        Room Information
      </v-card-title>
      <v-card-text>
        <p>Room ID: {{ roomInfo.room }}</p>
        <p>Connected Users: {{ Object.keys(roomInfo.users || {}).length }}</p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, computed} from 'vue';
import {io} from 'socket.io-client';
import draggable from 'vuedraggable';
import {useRoute} from 'vue-router';

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

function getRandomColor() {
  const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FFEEAD', '#D4A5A5', '#9B59B6', '#3498DB'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

function getCursorColor(user_id) {
  if (!cursorColors.value[user_id]) {
    cursorColors.value[user_id] = getRandomColor();
  }
  return cursorColors.value[user_id];
}

// Computed zum Anzeigen der anderen Nutzer im Raum
const otherUsers = computed(() => {
  if (!roomInfo.value || !roomInfo.value.users) return [];
  return Object.entries(roomInfo.value.users)
    .filter(([id, name]) => name !== username) // optional: den eigenen Nutzer ausblenden
    .map(([id, name]) => ({id, name}));
});

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
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.emit('leave_eng');
    socket.value.disconnect();
  }
});
</script>

<style scoped>
.container {
  padding: 16px;
}

.blocks-container {
  height: calc(100vh - 200px);
  overflow-y: auto;
  padding-right: 16px;
}

.textarea-container {
  position: relative;
}

.prompt-textarea {
  font-family: 'Roboto Mono', monospace;
  width: 100%;
  box-sizing: border-box;
}

.room-info {
  position: fixed;
  bottom: 16px;
  right: 16px;
  width: 300px;
  z-index: 100;
}

.drag-handle {
  cursor: move;
}

/* Neue Collaborators-List Styles */
.collaborators-container {
  display: flex;
  align-items: center;
}

.collaborators-list {
  display: flex;
  align-items: center;
}
</style>
