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
                @input="value => handleTextChange(block.name, value)"
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
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

const socket = ref(null);
const blocks = ref([]);
const roomInfo = ref(null);
const userId = ref(null);

const username = localStorage.getItem('username');
const promptId = 1; // Would typically come from route.params.id
const roomId = `room_${promptId}`;

const handleTextChange = (blockId, newContent) => {
  if (socket.value) {
    socket.value.emit('text_update', {
      blockId,
      content: newContent,
      room: roomId,
      userId: userId.value
    });
  }
};

const processReceivedContent = (content) => {
  if (!content?.blocks) return;

  // Convert blocks object to array and sort by position
  const blocksArray = Object.entries(content.blocks).map(([name, data]) => ({
    name,
    content: data.content,
    position: data.position
  })).sort((a, b) => a.position - b.position);

  blocks.value = blocksArray;
};

onMounted(() => {
  // Initialize socket connection
  socket.value = io(import.meta.env.VITE_API_BASE_URL);

  // Connect to server
  socket.value.emit('pe_connect', { username }, () => {
    console.log('WebSocket connection established');
  });

  // Handle connection response
  socket.value.on('pe_connected', (data) => {
    console.log('Connected to server:', data);
    userId.value = data.user_id;
  });

  // Join room
  socket.value.on('connect', () => {
    socket.value.emit('pe_join_room', { room: roomId, prompt_id: promptId }, () => {
      console.log('Joined room:', roomId);
    });
  });

  // Handle room join confirmation and initial data
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

  // Handle text updates åΩfrom other users
  socket.value.on('pe_text_update', (data) => {
    if (data.userId !== userId.value) {
      const block = blocks.value.find(b => b.name === data.blockId);
      if (block) {
        block.content = data.content;
      }
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
</style>
