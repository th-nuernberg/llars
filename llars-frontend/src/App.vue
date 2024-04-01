<template>
  <v-app>
    <v-app-bar app dark color="primary">
      <v-app-bar-nav-icon></v-app-bar-nav-icon>
      <v-toolbar-title>
        <img src="./assets/logo/llars-logo.png" alt="Logo" height="30" class="mr-2">
        LLars Plattform
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>
    <v-main> <!-- v-main hinzugefügt, um den Content zu umschließen -->
      <router-view></router-view>
    </v-main>
  </v-app>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  router.push('/login');
}
</script>
