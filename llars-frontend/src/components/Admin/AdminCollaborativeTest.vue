<template>
  <div>
    <p>Aktueller Text: {{ inputText }}</p>
    <v-text-field
      v-model="inputText"
      @input="onTextChanged"
      label="Text"
      outlined
    ></v-text-field>

    <!-- Raum-Informationen -->
    <div v-if="roomInfo">
      <p>Raum: {{ roomInfo.room }}</p>
      <p>Benutzer im Raum: {{ roomInfo.users.length }}</p>
    </div>
  </div>
</template>

<script setup>
import {ref, onMounted, onUnmounted, reactive} from 'vue';
import {io} from 'socket.io-client';
import axios from "axios";
const socket = ref(null);
const inputText = ref('');
const roomInfo = ref(null);
const user_id = ref(null);
const s_id = ref(null);

const username = localStorage.getItem('username');
const prompt_id = 1 //route.params.id;
const room_id = prompt_id

const onTextChanged = () => {
  if (socket.value) {
    socket.value.emit('update_text', {
      newText: inputText.value,
      room: room_id.value,
      user_id: user_id.value
    });
  }
};

onMounted(() => {
  // Initialisiere Socket-Verbindung
  socket.value = io(`${import.meta.env.VITE_API_BASE_URL}`);

  // Verbindung herstellen
  const user = localStorage.getItem('username');
  socket.value.emit('pe_connect', { user_id: user }, () => {
  console.log('Verbindung zu WebSocket erfolgreich');
});

  // Verbindungsantwort empfangen
  socket.value.on('pe_connected', (data) => {
    console.log('Connected to Server:', data);
    // Speichere die Benutzer-ID
    user_id.value = data.user_id;
    s_id.value = data.s_id;
  });

  // Raum beitreten
  socket.value.emit('pe_join_room', {room: room_id, prompt_id: prompt_id}, () => {
    console.log('Client hat sich dem Raum angeschlossen');
  });

  socket.value.on('pe_joined_room', (data) => {
    console.log('Raum beigetreten:', data);
  });

  // Raum-Zustandsinformationen empfangen
  socket.value.on('room_state', (data) => {
    console.log('Raum-Zustand erhalten:', data);

    // Aktualisiere Raum-Informationen
    roomInfo.value = {
      room: data.room,
      users: data.users
    };

    // Setze initialen Prompt, wenn vorhanden
    if (data.prompt !== undefined) {
      inputText.value = data.prompt;
    }
  });

  // Text-Update-Event
  socket.value.on('text_update', (data) => {
    console.log('Vollständige Daten erhalten:', data);
    console.log('Neuer Text:', data.newText);
    console.log('Aktueller Text vor Update:', inputText.value);

    if (data.newText !== undefined) {
      // Verhindere Schleife, wenn der Text von diesem Benutzer stammt
      if (data.userId !== userId.value) {
        inputText.value = data.newText;
        console.log('Text nach Update:', inputText.value);
      }
    } else {
      console.warn('Kein neuer Text gefunden');
    }
  });
});


// Aufräumen bei Komponentenabbau
onUnmounted(() => {
  if (socket.value) {
    // Raum verlassen
    socket.value.emit('leave_eng');

    // Verbindung trennen
    socket.value.disconnect();
  }
});
</script>
