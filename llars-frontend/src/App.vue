<template>
  <v-app>
    <v-app-bar app dark color="teal-lighten-4">
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <v-toolbar-title @click="goHome" style="cursor: pointer;">
        <img src="./assets/logo/llars-logo.png" alt="Logo" height="30" class="mr-2">
        LLars Plattform
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-chip v-if="username" class="mr-2">
        {{ username }}
      </v-chip>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>
    <v-main>
      <router-view :key="$route.fullPath"></router-view>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const username = ref('');

function updateUsername() {
  username.value = localStorage.getItem('username') || '';
}

onMounted(() => {
  updateUsername();
});

watch(() => router.currentRoute.value, () => {
  updateUsername();
}, { immediate: true });

function logout() {
  // Entferne allgemeine Auth-Daten
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  localStorage.removeItem('api_key');

  // Entferne alle gespeicherten Ranked-Feature-Daten
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('featureOrder_') || key.startsWith('featureRating_')) {
      localStorage.removeItem(key);
    }
  });

  username.value = ''; // Setze den Benutzernamen zurück
  router.push('/login');
}

function goHome() {
  router.push('/home');
}
</script>
