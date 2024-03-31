<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <!--<img alt="Vue logo" class="logo" src="./assets/logo.svg" width="125" height="125" />-->
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img src="./assets/llars-logo.png" alt="Logo" style="height: 30px; margin-right: 10px;">
          LLars Plattform
        </a>
        <div class="d-flex justify-content-end">
          <button class="btn btn-outline-danger" @click="logout">Logout</button>
        </div>
      </div>
    </nav>
    <v-app>

    </v-app>
    <router-view></router-view>
  </div>
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

<style>
.navbar {
  margin-bottom: 20px;
}
</style>
