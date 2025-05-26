<template>
  <div class="comparison-chat">
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="message.messageId"
        class="message-group"
      >
        <!-- User Message -->
        <div v-if="message.type === 'user'" class="user-message-container">
          <div class="user-message">
            <div class="message-content">{{ message.content }}</div>
            <div class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</div>
          </div>
        </div>

        <!-- Bot Responses (side by side) -->
        <div v-else-if="message.type === 'bot_pair'" class="bot-responses-container">
          <div class="responses-grid">
            <div class="response-card" :class="{ 'selected': message.selected === 'llm1' }">
              <div class="response-header">
                <h4>Modell 1</h4>
                <v-chip v-if="message.selected === 'llm1'" color="success" size="small">Gewählt</v-chip>
              </div>
              <div class="response-content">
                <div v-if="message.streaming?.llm1" class="typing-indicator">
                  Schreibt<span class="typing-dots"></span>
                </div>
                <div v-else>{{ getResponseContent(message, 'llm1') }}</div>
              </div>
            </div>

            <div class="response-card" :class="{ 'selected': message.selected === 'llm2' }">
              <div class="response-header">
                <h4>Modell 2</h4>
                <v-chip v-if="message.selected === 'llm2'" color="success" size="small">Gewählt</v-chip>
              </div>
              <div class="response-content">
                <div v-if="message.streaming?.llm2" class="typing-indicator">
                  Schreibt<span class="typing-dots"></span>
                </div>
                <div v-else>{{ getResponseContent(message, 'llm2') }}</div>
              </div>
            </div>
          </div>

          <!-- Rating Buttons -->
          <div v-if="!message.selected && !isStreaming(message)" class="rating-container">
            <v-btn-group variant="outlined" divided>
              <v-btn @click="selectResponse(message.messageId, 'llm1')" color="primary">
                <v-icon class="mr-1">mdi-thumb-up</v-icon>
                Modell 1 ist besser
              </v-btn>
              <v-btn @click="selectResponse(message.messageId, 'tie')" color="warning">
                <v-icon class="mr-1">mdi-equal</v-icon>
                Beide gleich gut
              </v-btn>
              <v-btn @click="selectResponse(message.messageId, 'llm2')" color="primary">
                <v-icon class="mr-1">mdi-thumb-up</v-icon>
                Modell 2 ist besser
              </v-btn>
            </v-btn-group>
            <p class="rating-hint">Bitte bewerten Sie die Antworten, bevor Sie fortfahren...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="input-container">
      <v-text-field
        v-model="newMessage"
        @keyup.enter="sendMessage"
        placeholder="Schreibe eine Nachricht..."
        variant="outlined"
        :loading="isProcessing"
        :disabled="isProcessing || !canSendMessage"
        hide-details
        density="comfortable"
        append-inner-icon="mdi-send"
        @click:append-inner="sendMessage"
      >
        <template v-slot:prepend-inner>
          <v-icon v-if="!canSendMessage" color="error">mdi-lock</v-icon>
        </template>
      </v-text-field>
      <div v-if="!canSendMessage" class="input-hint">
        Bitte bewerten Sie zuerst die vorherigen Antworten, bevor Sie eine neue Nachricht senden...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import { io } from 'socket.io-client';

interface Message {
  messageId: number;
  idx: number;
  type: 'user' | 'bot_pair';
  content?: string | { llm1: string; llm2: string };
  selected?: string | null;
  streaming?: { llm1: boolean; llm2: boolean };
  timestamp: string;
}

const props = defineProps<{
  sessionId: number;
  persona: any;
}>();

const emit = defineEmits<{
  (e: 'messageUpdate'): void;
}>();

const messages = ref<Message[]>([]);
const newMessage = ref('');
const isProcessing = ref(false);
const messagesContainer = ref<HTMLElement>();
const socket = ref<any>(null);

const canSendMessage = computed(() => {
  const lastMessage = messages.value[messages.value.length - 1];
  return !lastMessage ||
    lastMessage.type === 'user' ||
    (lastMessage.type === 'bot_pair' && lastMessage.selected);
});

const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleTimeString('de-DE', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const isStreaming = (message: Message) => {
  return message.streaming?.llm1 || message.streaming?.llm2;
};

const getResponseContent = (message: Message, llmType: 'llm1' | 'llm2') => {
  if (typeof message.content === 'object' && message.content) {
    return message.content[llmType] || '';
  }
  return '';
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: 'smooth'
      });
    }
  });
};

const sendMessage = async () => {
  if (!newMessage.value.trim() || isProcessing.value || !canSendMessage.value) return;

  const messageContent = newMessage.value.trim();
  newMessage.value = '';
  isProcessing.value = true;

  if (socket.value) {
    socket.value.emit('comparison_message', {
      sessionId: props.sessionId,
      message: messageContent
    });
  }
};

const selectResponse = async (messageId: number, selection: string) => {
  const message = messages.value.find(m => m.messageId === messageId);
  if (message && socket.value) {
    socket.value.emit('rate_response', {
      sessionId: props.sessionId,
      messageId: messageId,
      selection: selection
    });
  }
};

const findMessageById = (messageId: number): Message | undefined => {
  return messages.value.find(m => m.messageId === messageId);
};

const addOrUpdateMessage = (messageData: any) => {
  const existingIndex = messages.value.findIndex(m => m.messageId === messageData.messageId);

  const message: Message = {
    messageId: messageData.messageId,
    idx: messageData.idx,
    type: messageData.type,
    content: messageData.content,
    selected: messageData.selected || null,
    timestamp: messageData.timestamp,
    streaming: messageData.type === 'bot_pair' ? { llm1: false, llm2: false } : undefined
  };

  if (existingIndex >= 0) {
    messages.value[existingIndex] = message;
  } else {
    messages.value.push(message);
    messages.value.sort((a, b) => a.idx - b.idx);
  }

  scrollToBottom();
};

// Socket setup
const initializeSocket = () => {
  const username = localStorage.getItem('username') || 'Gast';
  socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`, {
    path: '/socket.io/',
    transports: ['websocket'],
    query: { username: username },
    headers: {
      'Content-Type': 'application/json; charset=utf-8'
    }
  });

  socket.value.on('connect', () => {
    console.log('Socket connected for comparison');
    socket.value.emit('join_comparison_session', {
      sessionId: props.sessionId
    });
  });

  socket.value.on('messages_loaded', (data: any) => {
    console.log('Messages loaded:', data);
    messages.value = data.messages.map((msg: any) => ({
      messageId: msg.messageId,
      idx: msg.idx,
      type: msg.type,
      content: msg.content,
      selected: msg.selected || null,
      timestamp: msg.timestamp,
      streaming: msg.type === 'bot_pair' ? { llm1: false, llm2: false } : undefined
    }));
    scrollToBottom();
  });

  socket.value.on('message_created', (messageData: any) => {
    console.log('Message created:', messageData);
    addOrUpdateMessage(messageData);
  });

  socket.value.on('message_updated', (messageData: any) => {
    console.log('Message updated:', messageData);
    addOrUpdateMessage(messageData);
    emit('messageUpdate');
  });

  socket.value.on('streaming_started', (data: any) => {
    console.log('Streaming started:', data);
    const message = findMessageById(data.messageId);
    if (message && message.streaming) {
      data.llmTypes.forEach((llmType: string) => {
        if (message.streaming) {
          message.streaming[llmType as keyof typeof message.streaming] = true;
        }
      });
    }
  });

  // Streaming Update
  socket.value.on('streaming_update', (data: any) => {
    const { messageId, llmType, fullContent } = data;
    const message = findMessageById(messageId);

    if (message && message.type === 'bot_pair' && typeof message.content === 'object') {
      message.content[llmType as keyof typeof message.content] = fullContent;
      scrollToBottom();
    }
  });

  socket.value.on('streaming_complete', (data: any) => {
    console.log('Streaming complete:', data);
    const { messageId, llmType, finalContent } = data;
    const message = findMessageById(messageId);

    if (message) {
      if (message.streaming) {
        message.streaming[llmType as keyof typeof message.streaming] = false;
      }

      if (message.type === 'bot_pair' && typeof message.content === 'object') {
        message.content[llmType as keyof typeof message.content] = finalContent;
      }

      if (!message.streaming?.llm1 && !message.streaming?.llm2) {
        isProcessing.value = false;
      }
    }
  });

  socket.value.on('streaming_error', (data: any) => {
    console.error('Streaming error:', data);
    const { messageId, llmType, error } = data;
    const message = findMessageById(messageId);

    if (message) {
      if (message.streaming) {
        message.streaming[llmType as keyof typeof message.streaming] = false;
      }

      if (message.type === 'bot_pair' && typeof message.content === 'object') {
        message.content[llmType as keyof typeof message.content] = error;
      }

      if (!message.streaming?.llm1 && !message.streaming?.llm2) {
        isProcessing.value = false;
      }
    }
  });

  socket.value.on('error', (data: any) => {
    console.error('Socket error:', data);
    isProcessing.value = false;
  });

  socket.value.on('disconnect', () => {
    console.log('Socket disconnected');
    isProcessing.value = false;
  });
};

watch(() => props.sessionId, (newId) => {
  if (newId && socket.value) {
    messages.value = [];
    socket.value.emit('join_comparison_session', {
      sessionId: newId
    });
  }
});

onMounted(() => {
  initializeSocket();
});

// Entferne die loadMessages Methode - wird nicht mehr benötigt
defineExpose({
  // Keine loadMessages Funktion mehr nötig
});
</script>

<style scoped>
.comparison-chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message-group {
  margin-bottom: 1rem;
}

.user-message-container {
  display: flex;
  justify-content: flex-end;
}

.user-message {
  background: #1976d2;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  max-width: 70%;
}

.message-content {
  margin-bottom: 0.25rem;
}

.message-timestamp {
  font-size: 0.75rem;
  opacity: 0.8;
}

.bot-responses-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.responses-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.response-card {
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  background: white;
  transition: all 0.3s ease;
}

.response-card.selected {
  border-color: #4caf50;
  background: #f8fff8;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.response-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.response-content {
  min-height: 3rem;
  line-height: 1.5;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-style: italic;
}

.typing-dots {
  display: inline-flex;
  gap: 2px;
}

.typing-dots::after {
  content: '...';
  animation: typing 1.5s infinite;
}

@keyframes typing {
  0%, 60% { opacity: 0; }
  30% { opacity: 1; }
}

.rating-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem 0;
}

.rating-hint {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
  text-align: center;
}

.input-container {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  background: white;
}

.input-hint {
  font-size: 0.875rem;
  color: #ff5722;
  margin-top: 0.5rem;
  text-align: center;
}
</style>
