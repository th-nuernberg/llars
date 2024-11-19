<script setup>
import { ref } from 'vue'

const messages = ref([])
const newMessage = ref('')
const chatContainer = ref(null)
const isChatOpen = ref(false)

// Beispiel-Nachrichten zum Testen
messages.value = [
  {
    id: 1,
    content: 'Hallo! Wie kann ich dir helfen?',
    sender: 'bot',
    timestamp: new Date().toLocaleTimeString()
  }
]

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value
}

const sendMessage = () => {
  if (!newMessage.value.trim()) return

  messages.value.push({
    id: messages.value.length + 1,
    content: newMessage.value,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString()
  })

  setTimeout(() => {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }, 100)

  newMessage.value = ''
  simulateBotResponse()
}

const simulateBotResponse = () => {
  setTimeout(() => {
    messages.value.push({
      id: messages.value.length + 1,
      content: 'Dies ist eine Beispiel-Antwort vom Bot.',
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString()
    })
  }, 1000)
}
</script>

<template>
  <!-- Chat Toggle Button -->
  <div class="chat-toggle" @click="toggleChat">
    <v-btn
      icon
      color="primary"
      size="large"
      elevation="4"
    >
      <v-icon>{{ isChatOpen ? 'mdi-close' : 'mdi-message' }}</v-icon>
    </v-btn>
  </div>

  <!-- Floating Chat Window -->
  <div class="chat-window" :class="{ 'chat-open': isChatOpen }">
    <div class="chat-header">
      <div class="header-content">
        <img
          src="@/assets/llars_the_bear/llars_transparent.png"
          alt="LLars Logo"
          class="chat-logo"
        >
        <h3>LLars</h3>
      </div>
      <v-btn icon size="small" @click="toggleChat">
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </div>

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
          <div class="message-content">{{ message.content }}</div>
          <div class="message-timestamp">{{ message.timestamp }}</div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <v-text-field
        v-model="newMessage"
        @keyup.enter="sendMessage"
        placeholder="Schreibe eine Nachricht..."
        variant="outlined"
        density="compact"
        hide-details
        append-inner-icon="mdi-send"
        @click:append-inner="sendMessage"
      ></v-text-field>
    </div>
  </div>
</template>

<style scoped>
.chat-toggle {
  position: fixed;
  bottom: 40px;
  right: 20px;
  z-index: 999;
}

.chat-window {
  position: fixed;
  bottom: 100px;
  right: 20px;
  width: 350px;
  height: 500px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  transform: translateX(400px);
  transition: transform 0.3s ease;
  z-index: 998;
}

.chat-window.chat-open {
  transform: translateX(0);
}

.chat-header {
  padding: 8px 16px;
  background: #b0ca97;
  color: white;
  border-radius: 12px 12px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-logo {
  height: 40px;
  width: auto;
  object-fit: contain;
  margin-left: -4px;
}

.chat-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 500;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.message-container {
  display: flex;
  align-items: flex-end; /* Changed from flex-start to flex-end */
  gap: 8px;
  max-width: 100%;
}

.message-container.user {
  flex-direction: row-reverse;
}

.avatar-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  width: 36px;
  height: 36px;
  align-self: flex-end; /* Verschiebt nur den Avatar nach unten */
  margin-bottom: -10px; /* Feinjustierung der Position */
}

.message-avatar {
  width: 30px;
  height: 30px;
  object-fit: contain;
  position: absolute;
  z-index: 2;
  margin-top: 2px;
  margin-right: 1px;
}

.message-avatar-background {
  position: absolute;
  width: 36px;
  height: 36px;
  background-color: #ededed;
  border-radius: 50%;
  z-index: 1;
}

.message {
  max-width: 80%;
  padding: 0.8rem;
  border-radius: 1rem;
  position: relative;
}

.message-container.user .message {
  background: #b0ca97;
  color: white;
  border-bottom-right-radius: 0.2rem;
}

.message-container.bot .message {
  background: #f1f1f1;
  color: black;
  border-bottom-left-radius: 0.2rem;
}

.message-timestamp {
  font-size: 0.7rem;
  opacity: 0.7;
  margin-top: 0.3rem;
}

.chat-input {
  padding: 12px;
  border-top: 1px solid #eee;
}
</style>
