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
import { ref, onMounted, onUnmounted } from 'vue';
import { io } from 'socket.io-client';

const socket = ref(null);
const inputText = ref('');

const onTextChanged = () => {
  if (socket.value) {
    socket.value.emit('update_text', { newText: inputText.value, room: 'room1' });
  }
};

onMounted(() => {
  socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`);

  socket.value.emit('connect_prompt_eng', () => {
    console.log('Verbindung zu WebSocket erfolgreich');
  });

  socket.value.on('connection_response', (data) => {
    console.log('Serverantwort:', data);
  });

  socket.value.emit('join_eng', { room: 'room1' }, () => {
    console.log('Client hat sich dem Raum angeschlossen');
  });

socket.value.on('text_update', (data) => {
  console.log('Full data received:', data);
  console.log('New text:', data.newText);
  console.log('Current input text before update:', inputText.value);

  if (data.newText !== undefined) {
    inputText.value = data.newText;

    console.log('Input text after update:', inputText.value);
  } else {
    console.warn('No newText found in update');
  }
});
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect();
  }
});
</script>
