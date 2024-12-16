<template>
  <div>
    <p>Aktueller Text: {{ inputText }}</p>
    <v-text-field
      v-model="inputText"
      @input="onTextChanged"
      label="Text"
      outlined
    ></v-text-field>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { io } from 'socket.io-client';

const socket = io(`${import.meta.env.VITE_API_BASE_URL}`);
const inputText = ref('');

// Funktion, um den Text zu ändern
const onTextChanged = () => {
  // Sende den neuen Text an den Server
  console.log('Text wird an Server gesendet:', inputText.value);
  console.log('Raum:', 'room1');
  console.log('inputText:', inputText);
  socket.emit('update_text', { newText: inputText.value, room: 'room1' });
};

// Socket.IO-Event-Listener
onMounted(() => {
  // Verbindungsereignis senden, um den Client zu verbinden
  socket.emit('connect_prompt_eng', () => {
    console.log('Verbindung zu WebSocket erfolgreich');
  });

  // Event, das auf die Antwort des Servers wartet
  socket.on('connection_response', (data) => {
    console.log('Serverantwort:', data);
    // Optional: Text aus der Serverantwort setzen
  });


  // Senden des Payloads beim Joinen des Raums
  socket.emit('join_eng', { room: 'room1' }, () => {
  console.log('Client hat sich dem Raum angeschlossen');
  });

  // Event, das Textaktualisierungen vom Server empfängt
  socket.on('text_update', (data) => {
    console.log('Text vom Server erhalten:', data);
    if (data.newText) {
      inputText.value = data.newText;
      console.log('Text wurde aktualisiert:', inputText.value);
    }
  });
});

// Aufräumarbeiten, wenn die Komponente unmontiert wird
onUnmounted(() => {
  socket.off('connection_response');
});

</script>

<style scoped>
/* Hier kannst du Stil hinzufügen */
</style>
