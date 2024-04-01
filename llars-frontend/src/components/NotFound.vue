<template>
  <div>
    <h1>404 - Seite nicht gefunden</h1>
    <p>Die angeforderte Seite konnte nicht gefunden werden.</p>
    <button @click="goHome">Zur Startseite</button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';

const router = useRouter();

function goHome() {
  router.push('/');
}
</script>

<style>
/* Fügen Sie hier notwendige Stile hinzu */
</style>
