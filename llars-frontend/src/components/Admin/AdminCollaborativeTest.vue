<template>
  <div class="container">
    <!-- Blocks Container -->
    <div class="blocks-container">
      <template v-if="blocks.length > 0">
        <v-card
          v-for="block in blocks"
          :key="block.name"
          class="mb-4"
        >
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-text</v-icon>
            {{ block.name }}
          </v-card-title>
          <v-card-text>
            <div class="textarea-container">
              <v-textarea
                v-model="block.content"
                outlined
                hide-details
                rows="4"
                class="prompt-textarea"
                :data-block-id="block.name"
                @update:model-value="value => handleTextChange(block.name, value)"
              ></v-textarea>
            </div>
          </v-card-text>
        </v-card>
      </template>
      <v-skeleton-loader
        v-else
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
        <p>Connected Users: {{ roomInfo.users?.length || 0 }}</p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted} from 'vue';
import {io} from 'socket.io-client';

const socket = ref(null);
const blocks = ref([]);
const roomInfo = ref(null);
const userId = ref(null);

const username = localStorage.getItem('username');
const promptId = 1; // Würde normalerweise aus den route params stammen
const roomId = `room_${promptId}`;

const handleTextChange = (blockId, newContent) => {
  console.log('blockid:', blockId);
  console.log('newContent:', newContent); // Jetzt wird der komplette Text übermittelt
  if (socket.value) {
    socket.value.emit('pe_text_update', {
      blockId,
      content: newContent,
      room: roomId,
      userId: userId.value
    });
  }
};

const processReceivedContent = (content) => {
  if (!content || !content.blocks) return;

  console.log('Processing received content:', content);

  const blocksObject = content.blocks;
  const blocksArray = Object.entries(blocksObject).map(([name, blockData]) => ({
    name,
    content: blockData.content,
    position: blockData.position
  }));

  blocksArray.sort((a, b) => a.position - b.position);
  blocks.value = blocksArray;
};

onMounted(() => {
  socket.value = io(import.meta.env.VITE_API_BASE_URL);

  socket.value.emit('pe_connect', {username}, () => {
    console.log('WebSocket connection established');
  });

  socket.value.on('pe_connected', (data) => {
    console.log('Connected to server:', data);
    userId.value = data.user_id;
  });

  socket.value.on('connect', () => {
    socket.value.emit('pe_join_room', {room: roomId, prompt_id: promptId}, () => {
      console.log('Joined room:', roomId);
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
    console.log('Received updated content:', data);
    processReceivedContent(data);
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
</style>
