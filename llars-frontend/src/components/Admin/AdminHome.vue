<template>
  <v-container class="admin-home">
    <!-- Titel und Einleitung -->
    <v-row>
      <v-col cols="12">
        <v-card class="title-card">
          <v-card-title class="headline">Admin Dashboard</v-card-title>
          <v-card-subtitle>Wählen Sie ein Feature aus, um fortzufahren.</v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <!-- Feature Cards -->
    <v-row>
      <v-col cols="12" sm="6" md="4" lg="3" v-for="item in features" :key="item.title">
        <v-card
          class="mb-4 feature-card"
          @click="navigateToFeature(item.route)"
        >
          <v-card-title class="text-h5">{{ item.title }}</v-card-title>
          <v-card-text>{{ item.description }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

// Liste der Features
const features = ref([
  {
    title: 'Ranker',
    description: 'Verwalten und Analysieren von Ranking-Daten',
    route: '/AdminRanker'
  },
  {
    title: 'Verlauf Generierung',
    description: 'Bewertung von erzeugten Mail Verläufen',
    route: '/AdminHistoryGenerator'
  },
  {
    title: 'Rater',
    description: 'Bewertung von Benutzerinhalten und E-Mail-Threads',
    route: '/admin/rater'
  },
  {
    title: 'Test Site',
    description: 'Test Seite',
    route: '/AdminTester'
  }
]);

// Navigationsfunktion
function navigateToFeature(route) {
  router.push(route);
}
</script>

<style scoped>
.admin-home {
  margin-top: 20px;
  padding: 16px;
  border-radius: 8px;
}

.title-card {
  background-color: #b0ca97;
  color: #fff;
}

.title-card .v-card-title {
  color: #ffffff;
}

.title-card .v-card-subtitle {
  color: #e6f2d5;
}

.feature-card {
  background-color: #ffffff;
  border: 1px solid #b0ca97;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
}

.feature-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  background-color: #e8f5e9;
}

.feature-card .v-card-title {
  color: #2f4f4f;
}

.feature-card .v-card-text {
  color: #556b2f;
}
</style>
