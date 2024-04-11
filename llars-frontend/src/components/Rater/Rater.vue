<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1>Rater Dashboard</h1>
        <p>Bewerten Sie die Relevanz und Qualität der generierten Features für E-Mail-Verläufe.</p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="6" v-for="item in items" :key="item.id">
        <v-card>
          <v-card-title>{{ item.emailSubject }}</v-card-title>
          <v-card-text>
            <div>{{ item.emailExcerpt }}</div>
            <div><strong>Feature:</strong> {{ item.generatedFeature }}</div>
            <v-chip class="ma-2" color="blue" outlined>{{ item.featureType }}</v-chip>
          </v-card-text>
          <v-card-actions>
            <v-btn text color="green" @click="rateItem(item, 'positive')">Gut</v-btn>
            <v-btn text color="red" @click="rateItem(item, 'negative')">Schlecht</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';

// Beispiel-Daten, die tatsächlich über eine API abgerufen werden sollten
const items = ref([
  {
    id: 1,
    emailSubject: 'Betreff der E-Mail',
    emailExcerpt: 'Auszug aus dem E-Mail-Verlauf...',
    generatedFeature: 'Automatisch generierte Zusammenfassung des Inhalts',
    featureType: 'Zusammenfassung',
  },
  {
    id: 2,
    emailSubject: 'Betreff der E-Mail 2',
    emailExcerpt: 'Auszug aus einem anderen E-Mail-Verlauf...',
    generatedFeature: 'Automatisch generierter Betreff zum E-Mail-Verlauf',
    featureType: 'Generierter Betreff',
  },
  // Weitere Einträge...
]);

function rateItem(item, rating) {
  console.log(`Item ${item.id} rated as ${rating}`);
  // Hier sollte die Bewertungsinformation an den Server gesendet werden
}
</script>

<style scoped>
</style>
