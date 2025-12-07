<template>
  <v-row class="mb-4">
    <v-col cols="12" sm="6" lg="3">
      <v-skeleton-loader v-if="loading" type="card" height="90" />
      <v-card v-else class="stat-card">
        <v-card-text class="d-flex align-center">
          <v-avatar color="primary" size="56" class="mr-4">
            <v-icon icon="mdi-compare" color="white" size="28"></v-icon>
          </v-avatar>
          <div>
            <div class="text-h4 font-weight-bold">{{ totalComparisons }}</div>
            <div class="text-subtitle-2 text-medium-emphasis">Gesamt Vergleiche</div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col cols="12" sm="6" lg="3">
      <v-skeleton-loader v-if="loading" type="card" height="90" />
      <v-card v-else class="stat-card">
        <v-card-text class="d-flex align-center">
          <v-avatar color="success" size="56" class="mr-4">
            <v-icon icon="mdi-trophy" color="white" size="28"></v-icon>
          </v-avatar>
          <div>
            <div class="text-h4 font-weight-bold">{{ topPillar?.name || '-' }}</div>
            <div class="text-subtitle-2 text-medium-emphasis">Beste Säule</div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col cols="12" sm="6" lg="3">
      <v-skeleton-loader v-if="loading" type="card" height="90" />
      <v-card v-else class="stat-card">
        <v-card-text class="d-flex align-center">
          <v-avatar color="info" size="56" class="mr-4">
            <v-icon icon="mdi-percent" color="white" size="28"></v-icon>
          </v-avatar>
          <div>
            <div class="text-h4 font-weight-bold">{{ averageConfidence }}%</div>
            <div class="text-subtitle-2 text-medium-emphasis">Ø Konfidenz</div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
    <v-col cols="12" sm="6" lg="3">
      <v-skeleton-loader v-if="loading" type="card" height="90" />
      <v-card v-else class="stat-card">
        <v-card-text class="d-flex align-center">
          <v-avatar color="warning" size="56" class="mr-4">
            <v-icon icon="mdi-clock-outline" color="white" size="28"></v-icon>
          </v-avatar>
          <div>
            <div class="text-h4 font-weight-bold">{{ duration }}</div>
            <div class="text-subtitle-2 text-medium-emphasis">Laufzeit</div>
          </div>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
const props = defineProps({
  loading: { type: Boolean, default: false },
  totalComparisons: { type: Number, default: 0 },
  topPillar: { type: Object, default: null },
  averageConfidence: { type: Number, default: 0 },
  duration: { type: String, default: '-' }
});
</script>

<style scoped>
.stat-card {
  height: 100%;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}
</style>
