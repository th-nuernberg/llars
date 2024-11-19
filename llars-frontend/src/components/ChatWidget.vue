<script setup>
import { ref, onMounted } from 'vue'

const messages = ref([])
const newMessage = ref('')
const chatContainer = ref(null)

// Beispiel-Nachrichten zum Testen
onMounted(() => {
  messages.value = [
    {
      id: 1,
      content: 'Hallo! Wie kann ich dir helfen?',
      sender: 'bot',
      timestamp: new Date().toLocaleTimeString()
    }
  ]
})

const sendMessage = () => {
  if (!newMessage.value.trim()) return

  // Benutzer-Nachricht hinzufügen
  messages.value.push({
    id: messages.value.length + 1,
    content: newMessage.value,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString()
  })

  // Chat-Verlauf nach unten scrollen
  setTimeout(() => {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }, 100)

  // Nachrichtenfeld leeren
  newMessage.value = ''

  // Hier später die LLM-Integration einbauen
  simulateBotResponse()
}

// Simulation einer Bot-Antwort (später durch echte LLM-Integration ersetzen)
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
  <div class="chat-window">
    <!-- Chat Header -->
    <div class="chat-header">
      <h2>Chat Assistant</h2>
    </div>

    <!-- Chat Messages -->
    <div class="chat-messages" ref="chatContainer">
      <div v-for="message in messages"
           :key="message.id"
           :class="['message', message.sender]">
        <div class="message-content">{{ message.content }}</div>
        <div class="message-timestamp">{{ message.timestamp }}</div>
      </div>
    </div>

    <!-- Chat Input -->
    <div class="chat-input">
      <input
        v-model="newMessage"
        @keyup.enter="sendMessage"
        type="text"
        placeholder="Schreibe eine Nachricht..."
      >
      <button @click="sendMessage">Senden</button>
    </div>
  </div>
</template>

<style scoped>
.chat-window {
  width: 100%;
  max-width: 600px;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  margin: 0 auto;
}

.chat-header {
  padding: 1rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
  border-radius: 8px 8px 0 0;
}

.chat-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  max-width: 70%;
  padding: 0.8rem;
  border-radius: 1rem;
  position: relative;
}

.message.user {
  align-self: flex-end;
  background: #007bff;
  color: white;
  border-bottom-right-radius: 0.2rem;
}

.message.bot {
  align-self: flex-start;
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
  padding: 1rem;
  border-top: 1px solid #ddd;
  display: flex;
  gap: 0.5rem;
}

.chat-input input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.chat-input button {
  padding: 0.5rem 1rem;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.chat-input button:hover {
  background: #0056b3;
}
</style>
