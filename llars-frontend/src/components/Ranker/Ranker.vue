<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1>Ranker Dashboard</h1>
        <p>Klicken Sie auf einen Fall, um ein Ranking durchzuführen.</p>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12" sm="4" v-for="caseItem in cases" :key="caseItem.id">
        <v-card class="mb-4 case-card" @click="navigateToCase(caseItem.id)">
          <v-chip
            class="category-chip"
            :color="getCategoryColor(caseItem.category)"
            small
          >
            {{ caseItem.category }}
          </v-chip>
          <v-card-title>{{ caseItem.title }}</v-card-title>
          <v-card-text>{{ caseItem.description }}</v-card-text>
          <v-card-actions>
            <v-btn text color="primary">Bewerten</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const cases = ref([
  {
    id: 1,
    title: 'Fall 1',
    description: 'Beschreibung von Fall 1...',
    category: 'Jugend'
  },
  {
    id: 2,
    title: 'Fall 2',
    description: 'Beschreibung von Fall 2...',
    category: 'Eltern'
  },
  // Weitere Fälle...
]);

function navigateToCase(caseId) {
  router.push({ name: 'RankerDetail', params: { id: caseId } });
}

function getCategoryColor(category) {
  const colors = {
    Jugend: 'deep-purple lighten-3',
    Eltern: 'light-green lighten-3',
    // Weitere Kategorien und Farben...
  };
  return colors[category] || 'grey';
}
</script>

<style scoped>
.case-card {
  position: relative;
  transition: box-shadow 0.3s ease-in-out, transform 0.1s ease-in-out;
  cursor: pointer;
}

.case-card:hover {
  box-shadow: 0 8px 16px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

.category-chip {
  position: absolute;
  top: 4px;
  right: 4px;
  border-radius: 12px 5px 12px 5px;
}
</style>
