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
                <v-chip v-if="message.selected === 'llm1'" color="success" size="small">Gewählt
                </v-chip>
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
                <v-chip v-if="message.selected === 'llm2'" color="success" size="small">Gewählt
                </v-chip>
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
      <div class="input-wrapper">
        <v-textarea
          v-model="newMessage"
          @keyup.enter.exact="sendMessage"
          @keydown.enter.shift.prevent
          placeholder="Schreiben Sie eine Nachricht..."
          variant="outlined"
          :loading="isProcessing"
          :disabled="isProcessing || !canSendMessage"
          hide-details
          rows="2"
          auto-grow
          max-rows="6"
          density="comfortable"
          class="message-input"
          :class="{ 'input-disabled': !canSendMessage, 'input-processing': isProcessing }"
        >
          <template v-slot:prepend-inner>
            <div class="input-status-icon">
              <v-icon
                v-if="!canSendMessage"
                color="error"
                size="small"
                class="status-icon lock-icon"
              >
                mdi-lock
              </v-icon>
              <v-icon
                v-else-if="isProcessing"
                color="primary"
                size="small"
                class="status-icon processing-icon"
              >
                mdi-clock-outline
              </v-icon>
            </div>
          </template>

          <template v-slot:append-inner>
            <v-btn
              @click="sendMessage"
              :disabled="!newMessage.trim() || isProcessing || !canSendMessage"
              color="primary"
              variant="flat"
              size="small"
              class="send-button"
              :loading="isProcessing"
            >
              <v-icon>mdi-send</v-icon>
            </v-btn>
          </template>
        </v-textarea>
      </div>

      <transition name="hint-fade">
        <div v-if="!canSendMessage" class="input-hint error-hint">
          <v-icon size="small" color="error" class="mr-2">mdi-information-outline</v-icon>
          Bitte bewerten Sie zuerst die vorherigen Antworten, bevor Sie eine neue Nachricht senden.
        </div>
        <div v-else-if="isProcessing" class="input-hint processing-hint">
          <v-icon size="small" color="primary" class="mr-2">mdi-clock-outline</v-icon>
          Antworten werden generiert...
        </div>
      </transition>
    </div>

    <!-- Dialog für Bewertungsabweichung -->
    <v-dialog v-model="showJustificationDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="text-h5 bg-warning text-white pa-4">
          <v-icon start class="mr-2">mdi-alert-circle</v-icon>
          Bewertungsabweichung
        </v-card-title>
        <v-card-text class="pa-6">
          <div class="mb-4">
            <v-alert type="info" variant="tonal" class="mb-4">
              Wir führen automatisch auch eine Bewertung der Konversation durch künstliche Intelligenz durch. Diesmal hat diese sich anders entschieden, als Sie es haben. Um das besser zu verstehen, würden wir uns freuen, wenn Sie hierfür eine Begründung angeben könnten. Vielen Dank!
              <br>
              <strong>Ihre Bewertung:</strong> {{ formatSelection(currentJustification?.user_selection) }}
              <br>
              <strong>KI-Bewertung:</strong> {{ formatSelection(currentJustification?.ai_selection) }}
            </v-alert>
          </div>
          
          <div class="mb-4">
            <h4 class="text-subtitle-1 mb-2">Begründung der KI:</h4>
            <v-card variant="outlined" class="pa-3">
              <p class="text-body-2">{{ currentJustification?.ai_reason }}</p>
            </v-card>
          </div>

          <div>
            <h4 class="text-subtitle-1 mb-2">Ihre Begründung (optional):</h4>
            <v-textarea
              v-model="userJustification"
              placeholder="Warum sind Sie anderer Meinung als die KI? (Optional)"
              variant="outlined"
              hide-details
              rows="3"
              auto-grow
              max-rows="6"
            />
          </div>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn
            color="grey"
            variant="text"
            @click="closeJustificationDialog(false)"
          >
            Ohne Begründung fortfahren
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="closeJustificationDialog(true)"
            :disabled="!userJustification.trim()"
          >
            Begründung speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  useComparisonSocket,
  useComparisonHelpers,
  type Message
} from './ComparisonChat/index';

const props = defineProps<{
  sessionId: number;
  persona: any;
}>();

const emit = defineEmits<{
  (e: 'messageUpdate'): void;
  (e: 'suggestionStateChange', generating: boolean): void;
}>();

// Initialize composables
const sessionIdRef = computed(() => props.sessionId);

const {
  messages,
  isProcessing,
  generatingSuggestion,
  showJustificationDialog,
  currentJustification,
  initializeSocket,
  sendMessage: socketSendMessage,
  selectResponse,
  generateSuggestion: socketGenerateSuggestion,
  submitJustification,
  closeJustificationDialog: socketCloseDialog,
  setupSessionWatcher
} = useComparisonSocket({
  sessionId: sessionIdRef,
  onMessageUpdate: () => emit('messageUpdate'),
  onSuggestionStateChange: (generating) => emit('suggestionStateChange', generating)
});

const {
  messagesContainer,
  newMessage,
  userJustification,
  canSendMessage,
  formatTimestamp,
  isStreaming,
  formatSelection,
  getResponseContent,
  scrollToBottom,
  clearNewMessage,
  setSuggestion,
  clearJustification
} = useComparisonHelpers(messages);

// Handle send message
const sendMessage = async () => {
  if (!newMessage.value.trim() || isProcessing.value || !canSendMessage.value) return;

  const messageContent = newMessage.value.trim();
  clearNewMessage();
  socketSendMessage(messageContent);
};

// Handle generate suggestion with callback for setting the value
const generateSuggestion = () => {
  if (generatingSuggestion.value || !canSendMessage.value) return;
  socketGenerateSuggestion();
};

// Handle close justification dialog
const closeJustificationDialog = (saveJustification: boolean) => {
  if (saveJustification && userJustification.value.trim()) {
    submitJustification(userJustification.value);
  }
  socketCloseDialog();
  clearJustification();
};

// Initialize on mount
onMounted(() => {
  initializeSocket(scrollToBottom);
  setupSessionWatcher();
});

defineExpose({
  generateSuggestion
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
  border: 2px solid rgb(var(--v-theme-surface-variant));
  border-radius: 0.5rem;
  padding: 1rem;
  background: rgb(var(--v-theme-surface));
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
  border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
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
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
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
  0%, 60% {
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
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
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
  margin: 0;
  text-align: center;
}

.input-container {
  padding: 1.5rem;
  border-top: 1px solid rgb(var(--v-theme-surface-variant));
  background: rgb(var(--v-theme-surface));
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.04);
}

.input-wrapper {
  max-width: 100%;
  margin: 0 auto;
  position: relative;
}

.message-input {
  transition: all 0.3s ease;
}

.message-input :deep(.v-field) {
  border-radius: 20px !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  background: rgb(var(--v-theme-surface));
  transition: all 0.3s ease;
}

.message-input :deep(.v-field):hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.message-input :deep(.v-field--focused) {
  box-shadow: 0 4px 20px rgba(25, 118, 210, 0.15) !important;
  border-color: #1976d2 !important;
}

.message-input.input-disabled :deep(.v-field) {
  background: rgb(var(--v-theme-surface-variant)) !important;
  border-color: rgb(var(--v-theme-surface-variant)) !important;
  box-shadow: none !important;
}

.message-input.input-processing :deep(.v-field) {
  border-color: #1976d2 !important;
  background: linear-gradient(45deg, #ffffff, #f8fbff) !important;
}

.message-input :deep(.v-field__input) {
  padding: 12px 16px !important;
  min-height: 48px !important;
  font-size: 0.95rem;
  line-height: 1.4;
}

.message-input :deep(.v-field__prepend-inner) {
  padding-top: 12px !important;
  padding-left: 4px !important;
}

.message-input :deep(.v-field__append-inner) {
  padding-top: 8px !important;
  padding-right: 8px !important;
}

.input-status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.status-icon {
  transition: all 0.3s ease;
}

.lock-icon {
  animation: shake 0.5s ease-in-out;
}

.processing-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

.send-button {
  border-radius: 12px !important;
  min-width: 44px !important;
  height: 36px !important;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.3) !important;
  transition: all 0.3s ease !important;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4) !important;
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
}

.send-button:disabled {
  opacity: 0.5 !important;
  box-shadow: none !important;
}

.input-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
  transition: all 0.3s ease;
}

.error-hint {
  background: linear-gradient(135deg, #ffebee, #fce4ec);
  color: #c62828;
  border: 1px solid #ffcdd2;
}

.processing-hint {
  background: linear-gradient(135deg, #e3f2fd, #f3e5f5);
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.hint-fade-enter-active,
.hint-fade-leave-active {
  transition: all 0.3s ease;
}

.hint-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.hint-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-2px);
  }
  75% {
    transform: translateX(2px);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

@media (max-width: 768px) {
  .input-container {
    padding: 1rem;
  }

  .message-input :deep(.v-field__input) {
    font-size: 0.9rem;
  }

  .input-hint {
    font-size: 0.8rem;
    padding: 0.4rem 0.8rem;
  }
}

@media (max-width: 480px) {
  .message-input :deep(.v-field) {
    border-radius: 16px !important;
  }

  .send-button {
    min-width: 40px !important;
    height: 32px !important;
  }
}
</style>
