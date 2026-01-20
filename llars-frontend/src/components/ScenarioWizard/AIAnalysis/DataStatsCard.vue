<template>
  <div class="data-stats-card">
    <!-- Header -->
    <div class="card-header">
      <v-icon size="18" class="mr-2">mdi-folder-open</v-icon>
      <span>{{ $t('scenarioWizard.analysis.data') }}</span>
    </div>

    <!-- Content -->
    <div class="card-content">
      <!-- Main Stat -->
      <div class="main-stat">
        <div class="stat-value">{{ itemCount }}</div>
        <div class="stat-label">Items</div>
      </div>

      <!-- Secondary Stats -->
      <div class="secondary-stats">
        <div class="stat-row">
          <v-icon size="16" class="mr-2 stat-icon">mdi-format-list-bulleted</v-icon>
          <span>{{ fieldCount }} {{ $t('scenarioWizard.analysis.fields') }}</span>
        </div>
        <div class="stat-row">
          <v-icon size="16" class="mr-2 stat-icon">mdi-file-multiple</v-icon>
          <span>{{ fileCount }} {{ $t('scenarioWizard.analysis.files') }}</span>
        </div>
      </div>

      <!-- Fields Overview (expandable) -->
      <div v-if="fields && fields.length > 0" class="fields-section">
        <div class="fields-header" @click="showFields = !showFields">
          <v-icon size="16" :class="{ rotated: showFields }">mdi-chevron-down</v-icon>
          <span>{{ $t('scenarioWizard.analysis.fieldOverview') }}</span>
        </div>

        <v-expand-transition>
          <div v-show="showFields" class="fields-list">
            <div v-for="field in fields" :key="field.name" class="field-item">
              <span class="field-name">{{ field.name }}</span>
              <span class="field-type">{{ field.type }}</span>
              <div v-if="field.completeness !== undefined" class="field-completeness">
                <div
                  class="completeness-bar"
                  :style="{ width: `${field.completeness * 100}%` }"
                ></div>
              </div>
            </div>
          </div>
        </v-expand-transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  itemCount: {
    type: Number,
    default: 0
  },
  fieldCount: {
    type: Number,
    default: 0
  },
  fileCount: {
    type: Number,
    default: 1
  },
  fields: {
    type: Array,
    default: () => []
  }
})

const showFields = ref(false)
</script>

<style scoped>
.data-stats-card {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(136, 196, 200, 0.3);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  height: 200px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: rgba(136, 196, 200, 0.1);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #88c4c8;
}

.card-content {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  overflow-y: auto;
}

/* Main Stat */
.main-stat {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

/* Secondary Stats */
.secondary-stats {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-row {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.stat-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Fields Section */
.fields-section {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  padding-top: 12px;
}

.fields-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  user-select: none;
}

.fields-header:hover {
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.fields-header .v-icon {
  transition: transform 0.3s ease;
}

.fields-header .v-icon.rotated {
  transform: rotate(180deg);
}

.fields-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding: 4px 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px;
}

.field-name {
  color: rgba(var(--v-theme-on-surface), 0.9);
  font-family: monospace;
  flex: 1;
}

.field-type {
  color: #88c4c8;
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(136, 196, 200, 0.15);
  border-radius: 4px;
}

.field-completeness {
  width: 40px;
  height: 4px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.completeness-bar {
  height: 100%;
  background: #98d4bb;
  border-radius: 2px;
  transition: width 0.3s ease;
}
</style>
