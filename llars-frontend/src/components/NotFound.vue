<template>
  <div class="not-found-container">
    <h1 class="not-found-title">Oops! 404</h1>
    <p class="not-found-message">Entschuldigung, aber wir können die gesuchte Seite nicht finden.</p>
    <img src="/api/placeholder/400/300" alt="404 Illustration" class="not-found-image" />
    <p class="not-found-suggestion">Vielleicht möchten Sie zur Startseite zurückkehren?</p>
    <button @click="goHome" class="home-button">Zur Startseite</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function goHome() {
  router.push('/');
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  font-family: Arial, sans-serif;
  background-color: #f8f9fa;
}

.not-found-title {
  font-size: 4rem;
  color: #343a40;
  margin-bottom: 0.5rem;
}

.not-found-message {
  font-size: 1.25rem;
  color: #6c757d;
  margin-bottom: 2rem;
}

.not-found-image {
  max-width: 100%;
  height: auto;
  margin-bottom: 2rem;
}

.not-found-suggestion {
  font-size: 1.1rem;
  color: #495057;
  margin-bottom: 1rem;
}

.home-button {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  color: #fff;
  background-color: #007bff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.home-button:hover {
  background-color: #0056b3;
}
</style>
