<template>
  <v-container fluid class="chat-page pa-0">
    <v-row no-gutters class="chat-container">
      <v-col cols="12" class="chat-main">

        <!-- Chat Messages -->
        <div class="chat-messages" ref="chatContainer">
          <div v-for="message in messages"
               :key="message.id"
               :class="['message-container', message.sender]">
            <template v-if="message.sender === 'bot'">
              <div class="avatar-wrapper">
                <div class="message-avatar-background"></div>
                <img
                  src="@/assets/llars_the_bear/llars_transparent.png"
                  alt="LLars Logo"
                  class="message-avatar"
                >
              </div>
            </template>
            <div class="message">
              <div class="message-content">
                <template v-if="enableTypewriterAnimation">
                  <transition-group
                    :name="`fade-letter-${animationSpeed}`"
                    tag="span"
                    appear
                  >
                    <span
                      v-for="(char, index) in message.content.split('')"
                      :key="`${message.id}-${index}`"
                      class="letter"
                    >
                      {{ char }}
                    </span>
                  </transition-group>
                </template>
                <template v-else>
                  <span>{{ message.content }}</span>
                </template>
              </div>
              <div v-if="message.streaming" class="stream-indicator">▪▪▪</div>
              <div class="message-timestamp">{{ message.timestamp }}</div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div class="chat-input">
          <v-text-field
            v-model="newMessage"
            @keyup.enter="sendMessage"
            placeholder="Schreibe eine Nachricht..."
            variant="outlined"
            :loading="isProcessing"
            :disabled="isProcessing"
            hide-details
            density="comfortable"
            class="chat-input-field"
            append-inner-icon="mdi-send"
            @click:append-inner="sendMessage"
          ></v-text-field>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { io } from 'socket.io-client';

const STORAGE_KEY = 'chat_messages';
const messages = ref([]);
const newMessage = ref('');
const chatContainer = ref(null);
const socket = ref(null);
const isProcessing = ref(false);
const enableTypewriterAnimation = ref(true);
const animationSpeed = ref('medium');

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  });
};

// Funktion zum Laden der Nachrichten aus dem localStorage
// Funktion zum Laden der Nachrichten aus dem localStorage
const loadMessages = () => {
  try {
    const savedMessages = localStorage.getItem(STORAGE_KEY);
    const username = localStorage.getItem('username') || 'Gast';

    if (savedMessages) {
      messages.value = JSON.parse(savedMessages);
    } else {
      // Personalisierte Begrüßungsnachricht
      messages.value = [
        {
          id: 1,
          content: `Hallo ${username}! Wie kann ich dir helfen?`,
          sender: 'bot',
          timestamp: new Date().toLocaleTimeString(),
          streaming: false
        }
      ];
      // Speichere die initiale Nachricht
      saveMessages();
    }
  } catch (error) {
    console.error('Error loading messages from localStorage:', error);
    const username = localStorage.getItem('username') || 'Gast';
    messages.value = [
      {
        id: 1,
        content: `Hallo ${username}! Wie kann ich dir helfen?`,
        sender: 'bot',
        timestamp: new Date().toLocaleTimeString(),
        streaming: false
      }
    ];
  }
};

// Funktion zum Speichern der Nachrichten im localStorage
const saveMessages = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value));
  } catch (error) {
    console.error('Error saving messages to localStorage:', error);
  }
};

const sendMessage = () => {
  if (!newMessage.value.trim() || isProcessing.value) return;

  const messageObj = {
    id: messages.value.length + 1,
    content: newMessage.value,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString(),
    streaming: false
  };

  messages.value.push(messageObj);
  saveMessages();
  scrollToBottom();

  const userMessage = newMessage.value.trim();
  newMessage.value = '';
  isProcessing.value = true;

  socket.value.emit('chat_stream', {message: userMessage});
};

const addMessage = (content, sender, streaming = false) => {
  const messageObj = {
    id: messages.value.length + 1,
    content,
    sender,
    timestamp: new Date().toLocaleTimeString(),
    streaming
  };

  messages.value.push(messageObj);
  saveMessages();

  if (enableTypewriterAnimation.value) {
    adjustAnimationSpeed(content.length);
  }
  scrollToBottom();
};

const adjustAnimationSpeed = (length) => {
  if (length > 50) {
    animationSpeed.value = 'fast';
  } else if (length > 20) {
    animationSpeed.value = 'medium';
  } else {
    animationSpeed.value = 'slow';
  }
};

onMounted(() => {
  loadMessages();

  // Verbesserte Socket.io Initialisierung mit Umgebungsvariable
  socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`, {
    path: '/socket.io/',
    transports: ['websocket'],
    headers: {
      'Content-Type': 'application/json; charset=utf-8'
    }
  });

  socket.value.on('connect', () => console.log('Socket connected'));
  socket.value.on('disconnect', () => console.log('Socket disconnected'));

  socket.value.on('chat_response', (data) => {
    const lastMessage = messages.value[messages.value.length - 1];

    if (!data.complete) {
      if (lastMessage && lastMessage.streaming) {
        lastMessage.content += data.content;
        saveMessages();
        if (enableTypewriterAnimation.value) {
          adjustAnimationSpeed(data.content.length);
        }
      } else {
        addMessage(data.content, 'bot', true);
      }
    } else {
      if (lastMessage && lastMessage.streaming) {
        lastMessage.streaming = false;
        saveMessages();
      }
      isProcessing.value = false;
      scrollToBottom();
    }
  });
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect();
  }
});
</script>

<style scoped>
.chat-page {
  height: 100%;
  background-color: #f5f5f5;
}

.chat-container {
  height: calc(100vh - 9vh - 10px); /* Abzüglich der AppBar-Höhe */
}

.chat-main {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
}

.chat-header {
  padding: 16px 24px;
  background: #b0ca97;
  color: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.chat-logo {
  height: 40px;
  width: auto;
  object-fit: contain;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scroll-behavior: smooth;
}

.message-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 80%;
}

.message-container.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.avatar-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.message-avatar {
  width: 34px;
  height: 34px;
  object-fit: contain;
  position: absolute;
  z-index: 2;
}

.message-avatar-background {
  position: absolute;
  width: 40px;
  height: 40px;
  background-color: #ededed;
  border-radius: 50%;
  z-index: 1;
}

.message {
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
  min-width: 100px;
}

.message-container.user .message {
  background: #b0ca97;
  color: white;
  border-bottom-right-radius: 4px;
}

.message-container.bot .message {
  background: #f1f1f1;
  color: black;
  border-bottom-left-radius: 4px;
}

.message-content {
  line-height: 1.5;
  font-size: 1rem;
  word-wrap: break-word;
}

.letter {
  display: inline;
}

.fade-letter-slow-enter-active {
  animation: fade-in 0.5s ease-out;
}

.fade-letter-medium-enter-active {
  animation: fade-in 0.3s ease-out;
}

.fade-letter-fast-enter-active {
  animation: fade-in 0.15s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0.6;
    transform: translateY(-1px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-timestamp {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 4px;
}

.stream-indicator {
  margin-top: 4px;
  font-size: 0.8rem;
  opacity: 0.6;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

.chat-input {
  padding: 16px 24px;
  background: white;
  border-top: 1px solid #eee;
}

.chat-input-field {
  max-width: 1200px;
  margin: 0 auto;
}

/* Responsive Design */
@media (min-width: 960px) {
  .message-container {
    max-width: 60%;
  }
}

@media (max-width: 600px) {
  .chat-messages {
    padding: 16px;
  }

  .message-container {
    max-width: 90%;
  }

  .chat-input {
    padding: 12px 16px;
  }
}
</style>
