<template>
  <v-container class="home-container">
    <!-- Logo und Titelbereich -->
    <v-row justify="center" class="header mb-5">
      <v-col cols="12" class="text-center">
        <img src="@/assets/logo/llars-logo.png" alt="LLars Logo" height="120" class="mb-2">
        <h1 class="header-title">Willkommen bei LLars</h1>
        <div class="subtitle-text mb-4">Ihre Plattform für Ranking, Labeling, Rating und Mail-Generierung!</div>
      </v-col>
    </v-row>
    <!-- Feature Cards -->
    <v-row class="equal-size-cards">
      <v-col
        v-for="item in items.filter(item => !item.hide)"
        :key="item.title"
        cols="12" sm="6"
        class="d-flex card-col"
      >
        <v-card
          class="mb-4 feature-card d-flex flex-column"
          :color="item.disabled ? 'grey lighten-2' : 'primary'"
          dark
          @click="item.disabled ? null : navigateTo(item.route)"
          :elevation="item.elevation"
          @mouseover="() => item.elevation = item.disabled ? 2 : 5"
          @mouseleave="() => item.elevation = 1"
          :class="{ 'disabled-card': item.disabled }"
        >
          <div class="icon-container flex-grow-0">
            <v-icon large class="icon-center" color="white">{{ item.icon }}</v-icon>
          </div>
          <v-card-title class="text-h5 flex-grow-0">{{ item.title }}</v-card-title>
          <v-card-text class="flex-grow-1">{{ item.description }}</v-card-text>
          <div v-if="item.disabled" class="lock-overlay">
            <v-icon class="lock-icon" color="grey darken-3">mdi-lock</v-icon>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const items = ref([
  { title: 'Ranking', description: 'Ranken Sie Ihre Daten', route: '/ranker', icon: 'mdi-chart-bar-stacked', elevation: 1, disabled: true, hide: false },
  { title: 'Verlaufserstellung', description: 'Erzeugung von Mail-Verläufen (Säule 4)', route: '/HistoryGeneration', icon: 'mdi-timeline-text-outline', elevation: 1, disabled: false, hide: false },
  { title: 'Rating', description: 'Raten Sie Ihre Daten', route: '/rater', icon: 'mdi-star-outline', elevation: 1, disabled: true, hide: true },
      { title: 'Chatbot', description: "Chaten mit LLars", route: '/chat', icon: 'mdi-laptop-account', elevation: 1, disabled: false, hide: false},
  { title: 'Labeling', description: 'Beschriften Sie Ihre Datenpunkte', route: '/labler', icon: 'mdi-label-outline', elevation: 1, disabled: true, hide: true },
  { title: 'Prompt Engineering', description: "Entwerfen von Prompts", route: '/promptengineering', icon: 'mdi-text-search', elevation: 1, disabled: false, hide: false},
]);

function navigateTo(route) {
  router.push(route);
}

onMounted(() => {
  equalizeCardSizes();
  window.addEventListener('resize', equalizeCardSizes);
});

function equalizeCardSizes() {
  const cardCols = document.querySelectorAll('.card-col');
  let maxWidth = 0;
  let maxHeight = 0;

  // Reset sizes and find the maximum natural width and height
  cardCols.forEach(col => {
    col.style.width = '';
    col.style.height = '';
    const width = col.offsetWidth;
    const height = col.offsetHeight;
    if (width > maxWidth) maxWidth = width;
    if (height > maxHeight) maxHeight = height;
  });

  // Set all cards to the maximum width and height
  cardCols.forEach(col => {
    col.style.width = `${maxWidth}px`;
    col.style.height = `${maxHeight}px`;
  });
}
</script>


<style scoped>
.home-container {
  padding: 16px;
  border-radius: 8px;
  max-width: 1200px; /* Adjust this value as needed */
}

.header {
  position: relative;
  z-index: 1;
  padding-top: 64px;
}

.equal-size-cards {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.card-col {
  display: flex;
  justify-content: center;
  padding: 10px;
}

.feature-card {
  background-color: #ffffff;
  border: 1px solid var(--v-primary-base);
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
  text-align: center;
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.feature-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  background-color: var(--v-secondary-lighten-4);
}

.icon-container {
  margin-bottom: 16px;
}

.feature-card .v-card-title {
  color: white;
  margin-top: 10px;
  font-family: Arial, sans-serif; /* Gleiche Schriftart wie die Überschrift */
  font-weight: bold; /* Optional: Bold für Titel in Cards */
  color: #f8f8f8;
}

.feature-card .v-card-text {
  color: white;
  flex-grow: 1;
  font-family: Arial, sans-serif; /* Gleiche Schriftart wie die Überschrift */
  font-size: 0.9rem; /* Optional: Anpassen der Schriftgröße */
    color: #f8f8f8;
}


.disabled-card {
  opacity: 0.8;
  background-color: grey lighten-2;
}

.disabled-card:hover {
  transform: scale(1.01);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.disabled-card:hover .lock-overlay {
  opacity: 1;
}

.lock-icon {
  font-size: 48px;
  animation: lockBounce 1s ease-in-out infinite;
}

@keyframes lockBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@media (max-width: 600px) {
  .header {
    padding-top: 80px;
  }

  .card-col {
    flex-basis: 100%;
  }
}

.header-title {
  color: #333333; /* Dunkles Grau */
  font-family: Arial, sans-serif; /* Beispiel-Schriftart */
  font-weight: bold;
}

.subtitle-text {
  color: #555555; /* Ein etwas helleres Grau als das Header */
  font-family: 'Verdana', sans-serif; /* Beispiel-Schriftart */
  font-size: 1.1rem;
}

</style>
