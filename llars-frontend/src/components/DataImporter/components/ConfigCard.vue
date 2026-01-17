<template>
  <div class="config-card" :class="{ 'config-card--loading': loading }">
    <div class="config-card-header">
      <LIcon v-if="icon" size="18" class="mr-2" :color="iconColor">{{ icon }}</LIcon>
      <span class="config-card-title">{{ title }}</span>
      <v-progress-circular
        v-if="loading"
        indeterminate
        size="16"
        width="2"
        color="primary"
        class="ml-auto"
      />
      <LIcon
        v-else-if="hasValue"
        size="16"
        color="success"
        class="ml-auto"
      >
        mdi-check-circle
      </LIcon>
    </div>
    <div class="config-card-content">
      <template v-if="loading && !hasValue">
        <div class="loading-placeholder">
          <div class="loading-bar" />
          <div class="loading-bar loading-bar--short" />
        </div>
      </template>
      <template v-else>
        <slot>
          <span v-if="value" class="config-value">{{ value }}</span>
          <span v-else class="config-empty">Nicht konfiguriert</span>
        </slot>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  icon: { type: String, default: null },
  iconColor: { type: String, default: 'primary' },
  loading: { type: Boolean, default: false },
  value: { type: [String, Number, Object, Array], default: null }
})

const hasValue = computed(() => {
  if (props.value === null || props.value === undefined) return false
  if (Array.isArray(props.value)) return props.value.length > 0
  if (typeof props.value === 'object') return Object.keys(props.value).length > 0
  return !!props.value
})
</script>

<style scoped>
.config-card {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 12px 4px 12px 4px;
  border: 1px solid rgba(var(--v-border-color), 0.15);
  overflow: hidden;
  transition: all 0.2s;
}

.config-card--loading {
  border-color: rgba(176, 202, 151, 0.3);
}

.config-card-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
}

.config-card-title {
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.config-card-content {
  padding: 12px 14px;
  min-height: 48px;
}

.config-value {
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
}

.config-empty {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-style: italic;
}

/* Loading animation */
.loading-placeholder {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loading-bar {
  height: 14px;
  background: linear-gradient(
    90deg,
    rgba(176, 202, 151, 0.2) 25%,
    rgba(176, 202, 151, 0.4) 50%,
    rgba(176, 202, 151, 0.2) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.loading-bar--short {
  width: 60%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
