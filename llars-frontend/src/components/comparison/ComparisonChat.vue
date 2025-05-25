<template>
  <div class="comparison-chat">
    <div class="messages-container" ref="messagesContainer">
      <div
        v-for="(message, index) in messages"
        :key="message.id"
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
                  <span class="typing-dots"></span>
                  Schreibt...
                </div>
                <div v-else>{{ message.content?.llm1 || '' }}</div>
              </div>
            </div>

            <div class="response-card" :class="{ 'selected': message.selected === 'llm2' }">
              <div class="response-header">
                <h4>Modell 2</h4>
                <v-chip v-if="message.selected === 'llm2'" color="success" size="small">Gewählt</v-chip>
              </div>
              <div class="response-content">
                <div v-if="message.streaming?.llm2" class="typing-indicator">
                  <span class="typing-dots"></span>
                  Schreibt...
                </div>
                <div v-else>{{ message.content?.llm2 || '' }}</div>
              </div>
            </div>
          </div>

          <!-- Rating Buttons -->
          <div v-if="!message.selected && !isStreaming(message)" class="rating-container">
            <v-btn-group variant="outlined" divided>
              <v-btn @click="selectResponse(message.id, 'llm1')" color="primary">
                <v-icon>mdi-thumb-up</v-icon>
                 Modell 1 ist besser
              </v-btn>
              <v-btn @click="selectResponse(message.id, 'tie')" color="warning">
                <v-icon>mdi-equal</v-icon>
                Beide gleich gut
              </v-btn>
              <v-btn @click="selectResponse(message.id, 'llm2')" color="primary">
                <v-icon>mdi-thumb-up</v-icon>
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
  id: number;
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

  const userMessage: Message = {
    id: Date.now(),
    idx: messages.value.length,
    type: 'user',
    content: messageContent,
    timestamp: new Date().toISOString()
  };

  messages.value.push(userMessage);
  scrollToBottom();

  const botMessage: Message = {
    id: Date.now() + 1,
    idx: messages.value.length,
    type: 'bot_pair',
    content: { llm1: '', llm2: '' },
    streaming: { llm1: true, llm2: true },
    selected: null,
    timestamp: new Date().toISOString()
  };

  messages.value.push(botMessage);
  scrollToBottom();

  if (socket.value) {
    socket.value.emit('comparison_message', {
      sessionId: props.sessionId,
      message: messageContent,
      messageId: botMessage.id
    });
  }
};

const selectResponse = async (messageId: number, selection: string) => {
  const message = messages.value.find(m => m.id === messageId);
  if (message) {
    message.selected = selection;

    if (socket.value) {
      socket.value.emit('rate_response', {
        sessionId: props.sessionId,
        messageId: messageId,
        selection: selection
      });
    }

    emit('messageUpdate');
  }
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

  socket.value.on('comparison_response', (data: any) => {
    console.log(data)
    const { messageId, llmType, content, complete } = data;
    const message = messages.value.find(m => m.id === messageId);

    if (message && message.type === 'bot_pair') {
      if (!complete) {
        if (typeof message.content === 'object') {
          message.content[llmType as keyof typeof message.content] += content;
        }
      } else {
        if (message.streaming) {
          message.streaming[llmType as keyof typeof message.streaming] = false;
        }

        if (!message.streaming?.llm1 && !message.streaming?.llm2) {
          isProcessing.value = false;
        }
      }
      scrollToBottom();
    }
  });

  socket.value.on('rating_saved', (data: any) => {
    console.log('Rating saved:', data);
  });

  socket.value.on('disconnect', () => {
    console.log('Socket disconnected');
  });
};

const loadMessages = async (sessionMessages: any[]) => {
  messages.value = sessionMessages.map(msg => ({
    id: msg.id,
    idx: msg.idx,
    type: msg.type,
    content: typeof msg.content === 'string' ? msg.content : JSON.parse(msg.content),
    selected: msg.selected || null,
    timestamp: msg.timestamp
  }));

  nextTick(() => {
    scrollToBottom();
  });
};

watch(() => props.sessionId, (newId) => {
  if (newId && socket.value) {
    socket.value.emit('join_comparison_session', {
      sessionId: newId
    });
  }
});

onMounted(() => {
  initializeSocket();
});

defineExpose({
  loadMessages
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
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-message-container {
  display: flex;
  justify-content: flex-end;
}

.user-message {
  background: #1976d2;
  color: white;
  padding: 12px 16px;
  border-radius: 18px;
  border-bottom-right-radius: 6px;
  max-width: 70%;
}

.message-content {
  line-height: 1.4;
}

.message-timestamp {
  font-size: 0.75rem;
  opacity: 0.8;
  margin-top: 4px;
}

.bot-responses-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.responses-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.response-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 16px;
  background: white;
  transition: all 0.3s ease;
}

.response-card.selected {
  border-color: #4caf50;
  background: #f1f8e9;
}

.response-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.response-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #333;
}

.response-content {
  line-height: 1.5;
  min-height: 40px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
  font-style: italic;
}

.typing-dots {
  display: inline-block;
  animation: typing 1.5s infinite;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0; }
  30% { opacity: 1; }
}

.rating-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.rating-hint {
  margin: 0;
  font-size: 0.875rem;
  color: #666;
  text-align: center;
}

.input-container {
  padding: 16px;
  border-top: 1px solid #eee;
  background: white;
}

.input-hint {
  margin-top: 8px;
  font-size: 0.875rem;
  color: #ff1e00;
  text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
  .responses-grid {
    grid-template-columns: 1fr;
  }

  .user-message {
    max-width: 85%;
  }
}
</style>
