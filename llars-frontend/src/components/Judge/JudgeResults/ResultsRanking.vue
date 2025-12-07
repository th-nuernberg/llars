<template>
  <v-row class="mb-4">
    <v-col cols="12" lg="6">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-podium</v-icon>
          Säulen-Ranking
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="list-item-avatar@5" />
          <template v-else>
            <v-list>
              <v-list-item
                v-for="(pillar, index) in pillarRanking"
                :key="pillar.pillar_id"
                class="ranking-item mb-2"
              >
                <template v-slot:prepend>
                  <v-avatar
                    :color="getRankColor(index)"
                    size="48"
                    class="mr-3"
                  >
                    <span class="text-h6 font-weight-bold">{{ index + 1 }}</span>
                  </v-avatar>
                </template>

                <v-list-item-title class="text-h6 font-weight-bold">
                  {{ pillar.name }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  <div class="d-flex align-center mt-2">
                    <v-chip size="small" color="success" variant="outlined" class="mr-2">
                      {{ pillar.wins }} Siege
                    </v-chip>
                    <v-chip size="small" color="error" variant="outlined" class="mr-2">
                      {{ pillar.losses }} Niederlagen
                    </v-chip>
                    <v-chip size="small" color="grey" variant="outlined">
                      {{ Math.round(pillar.win_rate * 100) }}% Siegrate
                    </v-chip>
                  </div>
                </v-list-item-subtitle>

                <template v-slot:append>
                  <div class="text-right">
                    <div class="text-h5 font-weight-bold text-primary">
                      {{ pillar.score.toFixed(2) }}
                    </div>
                    <div class="text-caption text-medium-emphasis">Score</div>
                  </div>
                </template>
              </v-list-item>
            </v-list>

            <div v-if="pillarRanking.length === 0" class="text-center py-8">
              <v-icon size="64" color="grey-lighten-1">mdi-chart-line</v-icon>
              <div class="text-h6 mt-4 text-medium-emphasis">Keine Daten verfügbar</div>
            </div>
          </template>
        </v-card-text>
      </v-card>
    </v-col>

    <!-- Win Matrix Heatmap -->
    <v-col cols="12" lg="6">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-grid</v-icon>
          Vergleichs-Matrix
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-skeleton-loader v-if="loading" type="table" />
          <template v-else>
            <div class="matrix-container">
              <table class="win-matrix">
                <thead>
                  <tr>
                    <th class="corner-cell"></th>
                    <th v-for="pillar in pillarList" :key="'header-' + pillar.pillar_id" class="header-cell">
                      {{ pillar.name }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="pillarA in pillarList" :key="'row-' + pillarA.pillar_id">
                    <th class="row-header">{{ pillarA.name }}</th>
                    <td
                      v-for="pillarB in pillarList"
                      :key="'cell-' + pillarA.pillar_id + '-' + pillarB.pillar_id"
                      class="matrix-cell"
                      :class="getMatrixCellClass(pillarA.pillar_id, pillarB.pillar_id)"
                      :style="getMatrixCellStyle(pillarA.pillar_id, pillarB.pillar_id)"
                    >
                      {{ getMatrixValue(pillarA.pillar_id, pillarB.pillar_id) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="text-caption text-medium-emphasis mt-2 text-center">
              Zeile = Angreifer, Spalte = Verteidiger. Werte = Anzahl Siege.
            </div>
          </template>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>

<script setup>
const props = defineProps({
  loading: { type: Boolean, default: false },
  pillarRanking: { type: Array, default: () => [] },
  pillarList: { type: Array, default: () => [] },
  getRankColor: { type: Function, required: true },
  getMatrixValue: { type: Function, required: true },
  getMatrixCellClass: { type: Function, required: true },
  getMatrixCellStyle: { type: Function, required: true }
});
</script>

<style scoped>
.ranking-item {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px;
  transition: background-color 0.2s ease;
}

.ranking-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.matrix-container {
  overflow-x: auto;
}

.win-matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.win-matrix th,
.win-matrix td {
  padding: 12px;
  text-align: center;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.win-matrix .corner-cell {
  background-color: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface));
}

.win-matrix .header-cell,
.win-matrix .row-header {
  background-color: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface));
  font-weight: bold;
  font-size: 12px;
}

.win-matrix .matrix-cell {
  transition: all 0.2s ease;
  font-weight: 500;
}

.win-matrix .matrix-cell:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.win-matrix .diagonal-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.38);
}
</style>
