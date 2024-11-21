<template>
  <v-app>
    <!-- Normale Benutzer AppBar -->
    <v-app-bar v-if="!isAdminUser" app dark color="primary"> <!-- Primärfarbe verwendet -->
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
        <v-toolbar-title  @click="goHome" style="display: flex; align-items: center; cursor: pointer;">
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
    <v-app-bar v-else app dark color="primary"> <!-- Primärfarbe verwendet -->
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

    <v-footer app dark color="primary" height="30" class="px-4 footer"> <!-- Primärfarbe verwendet -->
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

const router = useRouter();
const username = ref('');
const isAdminUser = ref(false); // Neu hinzugefügt, um den Admin-Status zu speichern
const links = ref(['Impressum', 'Datenschutz', 'Kontakt']); // Footer Links

function updateUsername() {
  const user = localStorage.getItem('username') || '';
  username.value = user;
  isAdminUser.value = isAdmin(user); // Prüfen, ob der Benutzer ein Admin ist
}

onMounted(() => {
  updateUsername();
});

watch(() => router.currentRoute.value, () => {
  updateUsername();
}, { immediate: true });

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

  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('api_key');

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
