<template>
  <v-container class="fill-height">
    <v-row justify="center" class="mb-5">
      <v-col cols="12" class="text-center">
        <img src="@/assets/logo/llars-logo.png" alt="LLars Logo" height="100" class="mb-2">
        <h1>Welcome to LLars</h1>
        <div class="subtitle-1 mb-4">Your Rank, Label, Rate and FeatureGenerate Software!</div>
      </v-col>
    </v-row>
    <v-row justify="center" align="stretch" class="cards-container mt-3">
      <v-col cols="12" sm="6" md="4" lg="3" v-for="item in items" :key="item.title" class="card-column d-flex">
        <v-card
          class="card-hover custom-card d-flex flex-column align-center justify-center"
          color="teal-lighten-4"
          :elevation="item.elevation"
          @click="item.disabled ? null : navigateTo(item.route)"
          @mouseover="() => item.elevation = item.disabled ? 2 : 5"
          @mouseleave="() => item.elevation = 1"
          :class="{ 'disabled-card': item.disabled }"
        >
          <div class="d-flex align-center card-content">
            <v-icon large class="mx-2" style="font-size: 50px;">{{ item.icon }}</v-icon>
            <div class="text-content">
              <v-card-title class="text-h5 font-weight-bold">{{ item.title }}</v-card-title>
              <v-card-text>{{ item.description }}</v-card-text>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const items = ref([
  { title: 'Ranker', description: 'Detailierte Analyse und Ranking', route: '/ranker', icon: 'mdi-chart-line', elevation: 1, disabled: false },
  { title: 'Rater', description: 'Bewerten Sie Ihre Daten', route: '/rater', icon: 'mdi-star', elevation: 1, disabled: false },
  { title: 'Labler', description: 'Beschriften Sie Ihre Datenpunkte', route: '/labler', icon: 'mdi-tag-text-outline', elevation: 1, disabled: true },
  { title: 'FeatureGenerator', description: 'Erzeugen Sie dynamisch Features', route: '/feature-generator', icon: 'mdi-cogs', elevation: 1, disabled: true }
]);

function navigateTo(route) {
  router.push(route);
}
</script>

<style>
.fill-height {
  min-height: 100vh;
}

.card-hover {
  transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
}

.card-hover:hover {
  transform: scale(1.05);
}

.mb-5 {
  margin-bottom: 5rem;
}

.mt-3 {
  margin-top: 3rem;
}

.cards-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
}

.card-column {
  display: flex;
  padding: 10px;
}

.custom-card {
  width: 100%;
  max-width: 300px;
  padding: 20px;
  flex-grow: 1;
}

.card-content {
  width: 100%;
  justify-content: center;
}

.text-content {
  text-align: left;
  flex-grow: 1;
}

/* Style für deaktivierte Kacheln */
.disabled-card {
  opacity: 0.6; /* Macht die Karte leicht transparent */
}

.disabled-card:hover {
  transform: scale(1.01); /* Leichter Hover-Effekt */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* Schwächerer Schatten */
}
</style>
