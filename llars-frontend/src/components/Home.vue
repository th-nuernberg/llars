<template>
  <v-container class="fill-height">
    <v-row justify="center">
      <v-col cols="12" class="text-center">
        <img src="@/assets/logo/llars-logo.png" alt="LLars Logo" height="100" class="mb-2">
        <h1>Welcome to LLars</h1>
        <div class="subtitle-1 mb-4">Your Rank, Label, Rate and FeatureGenerate Software!</div>
      </v-col>
    </v-row>
    <v-row justify="center" align="center">
      <v-col cols="12" sm="6" md="3" v-for="item in items" :key="item.title">
        <v-card
          class="d-flex flex-column align-center py-4 card-hover"
          color="light-blue lighten-2"
          @click="navigateTo(item.route)"
          :elevation="item.elevation"
          @mouseover="() => item.elevation = 5"
          @mouseleave="() => item.elevation = 1"
        >
          <v-icon large class="mx-2">{{ item.icon }}</v-icon>
          <v-card-title class="text-h5 font-weight-bold">{{ item.title }}</v-card-title>
          <v-card-text>{{ item.description }}</v-card-text>
          <v-spacer></v-spacer>
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
  { title: 'Ranker', description: 'Detailierte Analyse und Ranking', route: '/ranker', icon: 'mdi-chart-line', elevation: 1 },
  { title: 'Rater', description: 'Bewerten Sie Ihre Daten', route: '/rater', icon: 'mdi-star', elevation: 1 },
  { title: 'Labler', description: 'Beschriften Sie Ihre Datenpunkte', route: '/labler', icon: 'mdi-tag-text-outline', elevation: 1 },
  { title: 'FeatureGenerator', description: 'Erzeugen Sie dynamisch Features', route: '/feature-generator', icon: 'mdi-cogs', elevation: 1 }
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
  height: 100%; /* Gleichmäßige Höhe für alle Karten */
}

.card-hover:hover {
  transform: scale(1.05);
}
</style>
