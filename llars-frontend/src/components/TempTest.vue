<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { io } from 'socket.io-client'

const messages = ref([])
const newMessage = ref('')
const chatContainer = ref(null)
const isChatOpen = ref(false)
const socket = ref(null)
const isProcessing = ref(false)

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

messages.value = [
  {
    id: 1,
    content: 'Hallo! Wie kann ich dir helfen?',
    sender: 'bot',
    timestamp: new Date().toLocaleTimeString(),
    streaming: false
  }
];

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value;
  if (isChatOpen.value) {
    nextTick(() => scrollToBottom());
  }
};

const sendMessage = () => {
  if (!newMessage.value.trim() || isProcessing.value) return;

  // Benutzer-Nachricht hinzufügen
  messages.value.push({
    id: messages.value.length + 1,
    content: newMessage.value,
    sender: 'user',
    timestamp: new Date().toLocaleTimeString(),
    streaming: false
  });
  scrollToBottom();

  const userMessage = newMessage.value.trim();
  newMessage.value = '';
  isProcessing.value = true;

  // Nachricht an den Flask-Server senden
  socket.value.emit('chat_stream', { message: userMessage });
};

const addMessage = (content, sender, streaming = false) => {
  messages.value.push({
    id: messages.value.length + 1,
    content,
    sender,
    timestamp: new Date().toLocaleTimeString(),
    streaming
  });
  scrollToBottom();
};

// Verbindung zu Socket.IO herstellen
onMounted(() => {
  socket.value = io('http://localhost:80', {
    path: '/socket.io/',
    transports: ['websocket']
  });

  socket.value.on('connect', () => console.log('Socket connected'));
  socket.value.on('disconnect', () => console.log('Socket disconnected'));

  // Gestreamte Antworten empfangen
  socket.value.on('chat_response', (data) => {
    const lastMessage = messages.value[messages.value.length - 1];

    if (!data.complete) {
      if (lastMessage && lastMessage.streaming) {
        lastMessage.content += data.content; // Stream hinzufügen
        scrollToBottom();
      } else {
        addMessage(data.content, 'bot', true); // Neue Nachricht starten
      }
    } else {
      if (lastMessage && lastMessage.streaming) {
        lastMessage.streaming = false;
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
