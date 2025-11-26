<template>
  <v-app>
    <!-- Normale Benutzer AppBar -->
    <v-app-bar v-if="!isAdminUser" app dark color="primary">
      <!--<v-app-bar-nav-icon></v-app-bar-nav-icon>-->
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
      <v-btn icon @click="openSettings" title="Einstellungen">
        <v-icon>mdi-cog</v-icon>
      </v-btn>
      <v-btn icon @click="logout" title="Abmelden">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- Admin Benutzer AppBar -->
    <v-app-bar v-else app dark color="primary"> <!-- Primärfarbe verwendet -->
      <!--<v-app-bar-nav-icon></v-app-bar-nav-icon>-->
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
        color="admin"
        text-color="white"
        prepend-icon="mdi-shield-account"
      >
        Admin: {{ username }}
      </v-chip>
      <v-btn icon @click="openSettings" title="Einstellungen">
        <v-icon>mdi-cog</v-icon>
      </v-btn>
      <v-btn icon @click="logout" title="Abmelden">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view :key="$route.fullPath"></router-view>
    </v-main>

    <!-- Chatbot wird nur angezeigt, wenn Benutzer eingeloggt ist und ENABLE_CHAT true ist -->
    <FloatingChat v-if="username && ENABLE_CHAT" />

    <!-- User Settings Dialog -->
    <UserSettingsDialog v-model="settingsDialogOpen" />

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
import { useAuth } from '@/composables/useAuth';
import { useAppTheme } from '@/composables/useAppTheme';
import FloatingChat from './components/FloatingChat.vue';
import UserSettingsDialog from './components/UserSettingsDialog.vue';

// Globale Konstante für Chat-Aktivierung (kann der Entwickler ändern)
const ENABLE_CHAT = false; // hier auf true/false setzen um Chat global zu aktivieren/deaktivieren

const router = useRouter();
const auth = useAuth();
const { applyTheme } = useAppTheme();

const username = ref('');
const isAdminUser = ref(false);
const links = ref(['Dokumentation', 'Impressum', 'Datenschutz', 'Kontakt']);
const settingsDialogOpen = ref(false);

// Funktion zum Prüfen und Löschen alter Chat-Nachrichten
const cleanupOldChatMessages = () => {
  try {
    const chatData = localStorage.getItem('chat_messages');
    if (chatData) {
      const storedTimestamp = localStorage.getItem('chat_messages_timestamp');
      const currentTime = new Date().getTime();

      if (!storedTimestamp) {
        localStorage.setItem('chat_messages_timestamp', currentTime.toString());
        return;
      }

      const timestampDiff = currentTime - parseInt(storedTimestamp);
      const oneDayInMs = 24 * 60 * 60 * 1000;

      if (timestampDiff > oneDayInMs) {
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
  isAdminUser.value = isAdmin(user); // Prüfen, ob der Benutzer ein Admin ist
}

onMounted(() => {
  updateUsername();
  cleanupOldChatMessages();
  applyTheme(); // Apply theme on app mount
});

watch(() => router.currentRoute.value, () => {
  updateUsername();
}, {immediate: true});

function logout() {
  // Prüfen, ob es unsichere Änderungen gibt
  if (containsLocalStorageItemWithString('hasUnsaved_ratingChanges_')) {
    const confirmLogout = window.confirm(
      'Es gibt ungesicherte Änderungen. Möchten Sie wirklich ausloggen?'
    );

    if (!confirmLogout) {
      // Abbrechen, wenn der Benutzer das Logout ablehnt
      return;
    }
  }

  // Logout via useAuth (löscht sessionStorage: auth_token, auth_refreshToken, auth_idToken)
  auth.logout();

  // Alte localStorage-Items löschen (für Kompatibilität mit altem System)
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('api_key');
  localStorage.removeItem('chat_messages');
  localStorage.removeItem('chat_messages_timestamp');

  Object.keys(localStorage).forEach((key) => {
    if (
      key.startsWith('featureOrder_') ||
      key.startsWith('featureRating_') ||
      key.startsWith('rankerDetail_data_') ||
      key.startsWith('hasUnsaved_ratingChanges_') ||
      key.startsWith('local_rating_changes_') ||
      key.startsWith('local_messageRating_changes')
    ) {
      localStorage.removeItem(key);
    }
  });

  username.value = '';
  router.push('/login');
}

function containsLocalStorageItemWithString(string) {
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i); // Holen des Keys an Index i
        if (key.includes(string)) {
            return true; // Ein Item mit dem String im Namen wurde gefunden
        }
    }
    return false; // Kein Item mit dem String im Namen
}



function goHome() {
  router.push('/home');
}

function navigateTo(link) {
  switch (link) {
    case 'Dokumentation':
      // Navigate to internal documentation page
      router.push('/docs');
      break;
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

function openSettings() {
  settingsDialogOpen.value = true;
}
</script>

<!-- Global styles (not scoped) for Vuetify component overrides -->
<style>
/* Fix Vuetify Tooltip background - should be dark in light mode, light in dark mode */
.v-tooltip > .v-overlay__content {
  background: rgba(33, 33, 33, 0.95) !important;
  color: #ffffff !important;
}

/* Dark mode tooltip - lighter background */
.v-theme--dark .v-tooltip > .v-overlay__content {
  background: rgba(66, 66, 66, 0.95) !important;
  color: #ffffff !important;
}

/* ============================================
   LIGHT MODE TEXT CONTRAST FIXES
   ============================================
   In Light Mode, text must be dark for readability.
   Vuetify's default medium-emphasis opacity (0.6) is too light.
   We increase it to 0.75 for better contrast.
   ============================================ */

/* Light mode: Increase medium-emphasis opacity for better contrast */
.v-theme--light {
  --v-medium-emphasis-opacity: 0.75;
  --v-high-emphasis-opacity: 0.95;
}

/* Light mode: Ensure text-medium-emphasis is readable */
.v-theme--light .text-medium-emphasis {
  color: rgba(0, 0, 0, 0.75) !important;
}

/* Light mode: Ensure text-caption is readable */
.v-theme--light .text-caption {
  color: rgba(0, 0, 0, 0.7);
}

/* Light mode: Ensure v-card-text content is readable */
.v-theme--light .v-card-text {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix expansion panels text */
.v-theme--light .v-expansion-panel-title,
.v-theme--light .v-expansion-panel-text {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix slider tick labels and values */
.v-theme--light .v-slider .v-slider__tick-label {
  color: rgba(0, 0, 0, 0.7);
}

/* Light mode: Fix chip text in outlined variant */
.v-theme--light .v-chip.v-chip--variant-outlined {
  color: rgba(0, 0, 0, 0.87);
}

/* Light mode: Fix radio button and switch labels */
.v-theme--light .v-label {
  color: rgba(0, 0, 0, 0.87);
  opacity: 1;
}

.v-theme--light .v-selection-control .v-label {
  color: rgba(0, 0, 0, 0.87);
  opacity: 1;
}

/* Light mode: Fix text inside radio/switch labels using text-medium-emphasis */
.v-theme--light .v-selection-control .text-medium-emphasis,
.v-theme--light .v-radio .text-medium-emphasis,
.v-theme--light .v-switch .text-medium-emphasis {
  color: rgba(0, 0, 0, 0.7) !important;
}

/* Light mode: Fix text-caption inside form controls */
.v-theme--light .v-selection-control .text-caption,
.v-theme--light .v-radio .text-caption,
.v-theme--light .v-switch .text-caption {
  color: rgba(0, 0, 0, 0.7) !important;
}

/* Light mode: Fix form hint text */
.v-theme--light .v-messages__message {
  color: rgba(0, 0, 0, 0.6);
}

/* Light mode: Fix input labels */
.v-theme--light .v-field__outline,
.v-theme--light .v-field-label {
  color: rgba(0, 0, 0, 0.6);
}
</style>

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
  transform: translateY(0px);
  margin-top: 9px;
  margin-right: 15px;
}

.toolbar-text-wrapper {
  align-self: center;
  margin-top: 2px;
}

.toolbar-text {
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: 0.1px;
  color: rgb(var(--v-theme-on-primary));
}
</style>
