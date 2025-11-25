<template>
  <div v-if="!isConnected" class="error-view">
    <div class="paint-strokes">
      <div v-for="n in 8" :key="n"></div>
    </div>

    <div class="error-container">
      <h1 class="title">Service Temporarily Unavailable</h1>
      <div v-if="isRetrying" class="loader">
        <div class="spinner"></div>
      </div>
      <p v-else class="retry-text">
        Connection failed after multiple attempts.
        <span class="retry-link" @click="startRetrying">Try again</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';

// Zeitintervalle
const PHASE_1_DURATION = 2 * 60 * 1000; // 2 Minuten
const PHASE_2_DURATION = 5 * 60 * 1000; // 5 Minuten
const PHASE_3_DURATION = 10 * 60 * 1000; // 10 Minuten

const PHASE_1_INTERVAL = 5000;
const PHASE_2_INTERVAL = 10000;
const PHASE_3_INTERVAL = 30000;

const isConnected = ref(false);
const isRetrying = ref(false);
let startTime = 0;
let retryTimeout = null;

const getCurrentInterval = () => {
  const elapsedTime = Date.now() - startTime;

  if (elapsedTime <= PHASE_1_DURATION) return PHASE_1_INTERVAL;
  if (elapsedTime <= PHASE_2_DURATION) return PHASE_2_INTERVAL;
  if (elapsedTime <= PHASE_3_DURATION) return PHASE_3_INTERVAL;
  return null;
};

const checkConnection = async () => {
  try {
    // Versuche einfach die Root-URL zu fetchen
    const response = await fetch('/', { method: 'HEAD', cache: 'no-cache' });
    if (response.ok) {
      isConnected.value = true;
      isRetrying.value = false;
      // Sobald wieder connected, Seite neu laden
      window.location.reload();
      return;
    }
    retryConnection();
  } catch {
    retryConnection();
  }
};

const retryConnection = () => {
  const interval = getCurrentInterval();
  if (interval === null) {
    isRetrying.value = false;
    return;
  }

  isRetrying.value = true;
  retryTimeout = setTimeout(checkConnection, interval);
};

const startRetrying = () => {
  startTime = Date.now();
  isRetrying.value = true;
  checkConnection();
};

// Fehler-Events werden hier nicht noch mal registriert, da diese bereits in App.vue gehandhabt werden.
// Diese Komponente zeigt nur an, dass kein Connect da ist und versucht neu zu verbinden.

onMounted(() => {
  // Wenn diese Komponente gemountet ist, gehen wir davon aus, dass keine Verbindung vorhanden ist
  isConnected.value = false;
  startRetrying();
});

onBeforeUnmount(() => {
  if (retryTimeout) clearTimeout(retryTimeout);
});
</script>

<style scoped>
.error-view {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgb(var(--v-theme-background));
  z-index: 9999;
}

.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  padding: 20px;
}

.title {
  font-size: 2.5rem;
  color: rgb(var(--v-theme-on-background));
  margin-bottom: 2rem;
}

.retry-text {
  color: rgb(var(--v-theme-on-background));
  font-size: 1.1rem;
}

.retry-link {
  color: rgb(var(--v-theme-primary));
  cursor: pointer;
  text-decoration: underline;
}

.loader {
  margin-top: 2rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgb(var(--v-theme-surface-variant));
  border-top: 5px solid rgb(var(--v-theme-primary));
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.paint-strokes {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.paint-strokes div {
  position: absolute;
  width: 100%;
  height: 100%;
  filter: blur(20px);
  mix-blend-mode: multiply;
}
</style>
