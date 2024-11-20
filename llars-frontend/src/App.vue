<template>
  <v-app>
    <!-- Normale Benutzer AppBar -->
    <v-app-bar v-if="!isAdminUser" app dark color="primary">
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <v-toolbar-title @click="goHome" style="display: flex; align-items: center; cursor: pointer;">
        <v-row no-gutters align="center">
          <v-col cols="auto">
            <img src="./assets/logo/llars-logo.png" alt="Logo" height="26" class="logo-image">
          </v-col>
          <v-col cols="auto" class="toolbar-text-wrapper">
            <span class="toolbar-text">LLars Plattform</span>
          </v-col>
        </v-row>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-chip
        v-if="username"
        class="mr-2 user-chip"
        color="secondary"
        text-color="white"
        prepend-icon="mdi-account"
      >
        {{ username }}
      </v-chip>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- Admin Benutzer AppBar -->
    <v-app-bar v-else app dark color="primary">
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <v-toolbar-title @click="goAdminHome" style="display: flex; align-items: center; cursor: pointer;">
        <v-row no-gutters align="center">
          <v-col cols="auto">
            <img src="./assets/logo/llars-logo.png" alt="Logo" height="26" class="logo-image">
          </v-col>
          <v-col cols="auto" class="toolbar-text-wrapper">
            <span class="toolbar-text">Admin Dashboard</span>
          </v-col>
        </v-row>
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-chip
        v-if="username"
        class="mr-2 user-chip"
        color="admin"
        text-color="white"
        prepend-icon="mdi-shield-account"
      >
        Admin: {{ username }}
      </v-chip>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view :key="$route.fullPath"></router-view>
    </v-main>

    <!-- Chatbot wird nur angezeigt, wenn Benutzer eingeloggt ist -->
    <FloatingChat v-if="username" />

    <v-footer app dark color="primary" height="30" class="px-4 footer">
      <v-row no-gutters align="center" justify="space-between">
        <v-col cols="auto">
          <span class="copyright">
            © {{ new Date().getFullYear() }} LLars Plattform
          </span>
        </v-col>

        <v-col cols="auto">
          <span
            v-for="(link, index) in links"
            :key="link"
            class="footer-link"
            @click="navigateTo(link)"
          >
            {{ link }}
          </span>
        </v-col>
      </v-row>
    </v-footer>
  </v-app>
</template>


<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { isAdmin } from '@/services/admins';
import FloatingChat from './components/FloatingChat.vue';

const router = useRouter();
const username = ref('');
const isAdminUser = ref(false);
const links = ref(['Impressum', 'Datenschutz', 'Kontakt']);

// Funktion zum Prüfen und Löschen alter Chat-Nachrichten
const cleanupOldChatMessages = () => {
  try {
    const chatData = localStorage.getItem('chat_messages');
    if (chatData) {
      // Prüfen ob es einen Zeitstempel gibt
      const storedTimestamp = localStorage.getItem('chat_messages_timestamp');
      const currentTime = new Date().getTime();

      if (!storedTimestamp) {
        // Wenn kein Zeitstempel existiert, aktuellen setzen
        localStorage.setItem('chat_messages_timestamp', currentTime.toString());
        return;
      }

      // Prüfen ob die Nachrichten älter als 24 Stunden sind
      const timestampDiff = currentTime - parseInt(storedTimestamp);
      const oneDayInMs = 24 * 60 * 60 * 1000;

      if (timestampDiff > oneDayInMs) {
        // Chat-Nachrichten und Zeitstempel löschen wenn älter als 24 Stunden
        localStorage.removeItem('chat_messages');
        localStorage.removeItem('chat_messages_timestamp');
      }
    }
  } catch (error) {
    console.error('Error cleaning up chat messages:', error);
  }
};

function updateUsername() {
  const user = localStorage.getItem('username') || '';
  username.value = user;
  isAdminUser.value = isAdmin(user);
}

onMounted(() => {
  updateUsername();
  // Beim Mounten alte Nachrichten prüfen
  cleanupOldChatMessages();
});

watch(() => router.currentRoute.value, () => {
  updateUsername();
}, { immediate: true });

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('api_key');

  // Chat-bezogene Daten löschen
  localStorage.removeItem('chat_messages');
  localStorage.removeItem('chat_messages_timestamp');

  // Andere Feature-bezogene Daten löschen
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('featureOrder_') ||
        key.startsWith('featureRating_') ||
        key.startsWith('rankerDetail_data_')) {
      localStorage.removeItem(key);
    }
  });

  username.value = '';
  router.push('/login');
}

function goHome() {
  router.push('/home');
}

function goAdminHome() {
  router.push('/AdminDashboard');
}

function navigateTo(link) {
  switch (link) {
    case 'Impressum':
      router.push('/impressum');
      break;
    case 'Datenschutz':
      router.push('/datenschutz');
      break;
    case 'Kontakt':
      router.push('/kontakt');
      break;
  }
}
</script>

<style scoped>
.user-chip {
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: capitalize;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.user-chip:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.footer {
  font-size: 0.75rem;
}

.copyright {
  color: white;
}

.footer-link {
  color: white;
  cursor: pointer;
  margin-left: 1rem;
}

.footer-link:hover {
  text-decoration: underline;
}


.logo-image {
  /* Hier können Sie das Bild anpassen */
  transform: translateY(0px);  /* Vertikale Position */
  margin-top: 9px;            /* Zusätzlicher Abstand von oben */
  margin-right: 15px;
  /* height: 20px; */         /* Falls Sie die Höhe per CSS steuern möchten */
}

.toolbar-text-wrapper {
  align-self: center; /* Passt die vertikale Ausrichtung unabhängig an */
  margin-top: 2px; /* Verschiebung nach Bedarf anpassen */
}

.toolbar-text {
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: 0.1px;
  color: #f8f8f8;
}

</style>
