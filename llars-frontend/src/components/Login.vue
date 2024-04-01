<template>
  <v-container class="fill-height" fluid>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark>
            <v-toolbar-title>LLars Plattform Login</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                label="Username"
                prepend-icon="mdi-account"
                v-model="username"
                required
              ></v-text-field>
              <v-text-field
                label="Passwort"
                prepend-icon="mdi-lock"
                v-model="password"
                type="password"
                required
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="handleLogin">Login</v-btn>
          </v-card-actions>
          <v-alert v-if="errorMessage" type="error" class="ma-4">
            {{ errorMessage }}
          </v-alert>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { makePostRequestAsync } from '../services/rest_functions.js';

const username = ref('');
const password = ref('');
const errorMessage = ref('');
const router = useRouter();

async function handleLogin() {
  try {
    const response = await makePostRequestAsync('/login', {
      username: username.value,
      password: password.value
    });
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('username', response.data.username);
      router.push('/Home'); // oder eine andere Route, die der Benutzer nach dem Login sehen sollte
    }
  } catch (error) {
    errorMessage.value = error.message || 'An error occurred during login';
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
}
</style>
