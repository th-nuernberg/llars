<template>
  <div class="evaluation-layout" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="evaluation-header">
      <div class="header-left">
        <LBtn
          variant="tonal"
          prepend-icon="mdi-arrow-left"
          size="small"
          @click="$emit('back')"
        >
          {{ backLabel }}
        </LBtn>
        <div v-if="title" class="header-title">
          <h2>{{ title }}</h2>
          <span v-if="subtitle" class="text-caption text-medium-emphasis">{{ subtitle }}</span>
        </div>
      </div>
      <div class="header-center">
        <slot name="header-center" />
      </div>
      <div class="header-right">
        <slot name="header-right" />
      </div>
    </div>

    <!-- Error Bar -->
    <div v-if="error" class="error-bar">
      <v-alert type="error" variant="tonal" density="compact" closable @click:close="$emit('clear-error')">
        {{ error }}
      </v-alert>
    </div>

    <!-- Main Content -->
    <div class="evaluation-content">
      <slot />
    </div>

    <!-- Action Bar -->
    <div class="evaluation-action-bar">
      <div class="action-bar-left">
        <LBtn
          variant="tonal"
          prepend-icon="mdi-chevron-left"
          size="small"
          :disabled="!canGoPrev"
          @click="$emit('prev')"
        >
          Vorheriger
        </LBtn>
        <LBtn
          variant="tonal"
          append-icon="mdi-chevron-right"
          size="small"
          :disabled="!canGoNext"
          @click="$emit('next')"
        >
          Nächster
        </LBtn>
      </div>

      <div class="action-bar-center">
        <LEvaluationStatus
          :status="status"
          :saving="saving"
        />
        <span v-if="totalItems > 0" class="progress-indicator">
          {{ currentIndex + 1 }} / {{ totalItems }}
        </span>
      </div>

      <div class="action-bar-right">
        <slot name="action-bar-right" />
      </div>
    </div>
  </div>
</template>

<script setup>
import LEvaluationStatus from './LEvaluationStatus.vue'
import { useMobile } from '@/composables/useMobile'

const { isMobile } = useMobile()

defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  backLabel: { type: String, default: 'Übersicht' },
  error: { type: String, default: '' },
  status: { type: String, default: 'pending' }, // 'pending' | 'in_progress' | 'done'
  saving: { type: Boolean, default: false },
  canGoPrev: { type: Boolean, default: false },
  canGoNext: { type: Boolean, default: false },
  currentIndex: { type: Number, default: 0 },
  totalItems: { type: Number, default: 0 }
})

defineEmits(['back', 'prev', 'next', 'clear-error'])
</script>

<style scoped>
.evaluation-layout {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.evaluation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.header-title h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.3;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

/* Error Bar */
.error-bar {
  padding: 8px 16px;
  flex-shrink: 0;
}

/* Main Content */
.evaluation-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Action Bar */
.evaluation-action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  gap: 16px;
}

.action-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.action-bar-center {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
}

.progress-indicator {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  min-width: 50px;
  text-align: center;
}

.action-bar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: flex-end;
}

/* Mobile Styles */
.evaluation-layout.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
}

.evaluation-layout.is-mobile .evaluation-header {
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px;
}

.evaluation-layout.is-mobile .header-left {
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.evaluation-layout.is-mobile .header-title h2 {
  font-size: 1rem;
}

.evaluation-layout.is-mobile .header-center,
.evaluation-layout.is-mobile .header-right {
  display: none;
}

.evaluation-layout.is-mobile .evaluation-content {
  flex-direction: column;
}

.evaluation-layout.is-mobile .evaluation-action-bar {
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
}

.evaluation-layout.is-mobile .action-bar-left {
  order: 2;
  width: 100%;
  justify-content: space-between;
}

.evaluation-layout.is-mobile .action-bar-center {
  order: 1;
  width: 100%;
  justify-content: center;
}

.evaluation-layout.is-mobile .action-bar-right {
  display: none;
}
</style>
