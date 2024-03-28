<!-- Login.vue -->
<script setup>
// import { eventBus } from '../eventBus.js';
import axios from 'axios';
// import { useRouter } from 'vue-router';
import { ref } from 'vue'
import { makePostRequestAsync } from '../services/rest_functions.js';
// Reactive state
const username = ref('');
const password = ref('');
const errorMessage = ref('');
// const router = useRouter();
function handleLogin() {
  console.log("handleLogin");
  login();
}
async function login() {
  try {
    console.log("username", username.value, "password", password.value);
    const response = await makePostRequestAsync('/login', {
      username: username.value,
      password: password.value
    });
    console.log(`Response: ${response}`);
    console.log(response.data.access_token);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('username', response.data.username);
      // Emit an event if necessary
      // eventBus.emit('auth-change', true, response.data.username)
      // eventBus.emit('login-success', );
      // router.push({ path: '/0' });
    }
  } catch (error) {
    // Handle error
    errorMessage.value = error.message || 'An error occurred during login';
  }
}

</script>

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

  <style scoped>
  .login-container {
    padding: 20px;
    border: 1px solid #ddd;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  }
  </style>