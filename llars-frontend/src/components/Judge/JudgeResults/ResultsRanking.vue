<template>
  <div class="ranking-grid">
    <!-- Pillar Ranking Card -->
    <div class="results-card">
      <div class="card-header">
        <LIcon class="header-icon">mdi-podium</LIcon>
        <span class="header-title">Säulen-Ranking</span>
      </div>
      <div class="card-content">
        <v-skeleton-loader v-if="loading" type="list-item-avatar@5" />
        <template v-else>
          <div class="ranking-list">
            <div
              v-for="(pillar, index) in pillarRanking"
              :key="pillar.pillar_id"
              class="ranking-item"
            >
              <div
                class="rank-badge"
                :style="{ backgroundColor: getRankColor(index) }"
              >
                {{ index + 1 }}
              </div>

              <div class="pillar-info">
                <div class="pillar-name">{{ pillar.name }}</div>
                <div class="pillar-stats">
                  <LTag variant="success" size="small">{{ pillar.wins }} Siege</LTag>
                  <LTag variant="danger" size="small">{{ pillar.losses }} Niederlagen</LTag>
                  <LTag variant="gray" size="small">{{ Math.round(pillar.win_rate * 100) }}%</LTag>
                </div>
              </div>

              <div class="pillar-score">
                <div class="score-value">{{ pillar.score.toFixed(2) }}</div>
                <div class="score-label">Score</div>
              </div>
            </div>
          </div>

          <div v-if="pillarRanking.length === 0" class="empty-state">
            <LIcon size="48" color="grey-lighten-1">mdi-chart-line</LIcon>
            <div class="empty-text">Keine Daten verfügbar</div>
          </div>
        </template>
      </div>
    </div>

    <!-- Win Matrix Heatmap -->
    <div class="results-card">
      <div class="card-header">
        <LIcon class="header-icon">mdi-grid</LIcon>
        <span class="header-title">Vergleichs-Matrix</span>
      </div>
      <div class="card-content">
        <v-skeleton-loader v-if="loading" type="table" />
        <template v-else>
          <div class="matrix-container">
            <table class="win-matrix">
              <thead>
                <tr>
                  <th class="corner-cell"></th>
                  <th
                    v-for="pillar in pillarList"
                    :key="'header-' + pillar.pillar_id"
                    class="header-cell"
                  >
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
          <div class="matrix-legend">
            Zeile = Angreifer, Spalte = Verteidiger. Werte = Anzahl Siege.
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
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
.ranking-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: var(--llars-spacing-lg);
  margin-bottom: var(--llars-spacing-lg);
}

/* Card Styles */
.results-card {
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius);
  box-shadow: var(--llars-shadow-sm);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-sm);
  padding: var(--llars-spacing-md) var(--llars-spacing-lg);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.header-icon {
  color: var(--llars-primary);
}

.header-title {
  font-weight: 600;
  font-size: 1rem;
}

.card-content {
  padding: var(--llars-spacing-md);
}

/* Ranking List */
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: var(--llars-spacing-sm);
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: var(--llars-spacing-md);
  padding: var(--llars-spacing-md);
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: var(--llars-radius-sm);
  transition: all 0.2s ease;
}

.ranking-item:hover {
  background: rgba(var(--v-theme-primary), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.2);
}

.rank-badge {
  width: 40px;
  height: 40px;
  border-radius: var(--llars-radius-xs);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.pillar-info {
  flex: 1;
  min-width: 0;
}

.pillar-name {
  font-weight: 600;
  font-size: 1rem;
  margin-bottom: 4px;
}

.pillar-stats {
  display: flex;
  gap: var(--llars-spacing-xs);
  flex-wrap: wrap;
}

.pillar-score {
  text-align: right;
  flex-shrink: 0;
}

.score-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--llars-primary);
}

.score-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Matrix Styles */
.matrix-container {
  overflow-x: auto;
}

.win-matrix {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.win-matrix th,
.win-matrix td {
  padding: 10px 12px;
  text-align: center;
  border: 1px solid rgba(var(--v-border-color), 0.12);
}

.win-matrix .corner-cell {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-radius: var(--llars-radius-xs) 0 0 0;
}

.win-matrix .header-cell,
.win-matrix .row-header {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  font-weight: 600;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.win-matrix .matrix-cell {
  transition: all 0.2s ease;
  font-weight: 500;
}

.win-matrix .matrix-cell:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
  position: relative;
}

.win-matrix .diagonal-cell {
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.matrix-legend {
  text-align: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: var(--llars-spacing-sm);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--llars-spacing-xl);
  gap: var(--llars-spacing-md);
}

.empty-text {
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
