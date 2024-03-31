<template>
  <div class="container d-flex justify-content-center align-items-center" style="min-height: 100vh;">
    <div class="login-container w-100" style="max-width: 400px;">
      <h2 class="text-center mb-4">LLars Plattform</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group mb-3">
          <label for="username">Username:</label>
          <input type="text" class="form-control" id="username" v-model="username" required>
        </div>
        <div class="form-group mb-3">
          <label for="password">Passwort:</label>
          <input type="password" class="form-control" id="password" v-model="password" required>
        </div>
        <button class="btn btn-primary w-100" type="submit">Login</button>
      </form>
      <p v-if="errorMessage" class="text-danger mt-3">{{ errorMessage }}</p>
    </div>
  </div>
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
      router.push('/animals'); // oder eine andere Route, die der Benutzer nach dem Login sehen sollte
    }
  } catch (error) {
    errorMessage.value = error.message || 'An error occurred during login';
  }
}
</script>

<style scoped>
.login-container {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
</style>
