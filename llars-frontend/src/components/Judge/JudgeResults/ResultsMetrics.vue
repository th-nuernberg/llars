<template>
  <div class="results-card metrics-card">
    <div class="card-header">
      <LIcon class="header-icon">mdi-chart-bar</LIcon>
      <span class="header-title">Detaillierte Metriken</span>
    </div>

    <div class="card-content">
      <v-skeleton-loader v-if="loading" type="table-thead, table-tbody" />
      <div v-else class="metrics-table-wrapper">
        <table class="metrics-table">
          <thead>
            <tr>
              <th class="col-name">Säule</th>
              <th class="col-wins">Siege</th>
              <th class="col-losses">Niederlagen</th>
              <th class="col-winrate">Siegrate</th>
              <th class="col-confidence">Ø Konfidenz</th>
              <th class="col-score">Score</th>
              <th class="col-total">Vergleiche</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in metrics" :key="item.pillar_id" class="metrics-row">
              <td class="col-name">
                <span class="pillar-name">{{ item.name }}</span>
              </td>
              <td class="col-wins">
                <LTag variant="success" size="small">{{ item.wins }}</LTag>
              </td>
              <td class="col-losses">
                <LTag variant="danger" size="small">{{ item.losses }}</LTag>
              </td>
              <td class="col-winrate">
                <div class="winrate-bar">
                  <div
                    class="winrate-fill"
                    :style="{
                      width: (item.win_rate * 100) + '%',
                      backgroundColor: getWinRateColor(item.win_rate)
                    }"
                  ></div>
                  <span class="winrate-label">{{ Math.round(item.win_rate * 100) }}%</span>
                </div>
              </td>
              <td class="col-confidence">
                {{ Math.round(item.avg_confidence * 100) }}%
              </td>
              <td class="col-score">
                <span class="score-value">{{ item.score.toFixed(2) }}</span>
              </td>
              <td class="col-total">
                {{ item.total_comparisons }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  metrics: { type: Array, default: () => [] },
  getWinRateColor: { type: Function, required: true }
});
</script>

<style scoped>
.metrics-card {
  margin-bottom: var(--llars-spacing-lg);
}

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
  padding: 0;
}

/* Table Styles */
.metrics-table-wrapper {
  overflow-x: auto;
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
}

.metrics-table th,
.metrics-table td {
  padding: var(--llars-spacing-md);
  text-align: left;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}

.metrics-table th {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  font-weight: 600;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.metrics-row {
  transition: background-color 0.2s ease;
}

.metrics-row:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

.metrics-row:last-child td {
  border-bottom: none;
}

/* Column Styles */
.col-name {
  min-width: 120px;
}

.pillar-name {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.col-wins,
.col-losses {
  width: 100px;
  text-align: center;
}

.col-winrate {
  min-width: 180px;
}

.winrate-bar {
  position: relative;
  height: 24px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: var(--llars-radius-xs);
  overflow: hidden;
}

.winrate-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: var(--llars-radius-xs);
  transition: width 0.3s ease;
}

.winrate-label {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-weight: 600;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.col-confidence,
.col-total {
  width: 100px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.col-score {
  width: 100px;
  text-align: center;
}

.score-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--llars-primary);
}
</style>
