<template>
  <div class="scale-preview">
    <div class="scale-header">
      <span class="scale-name">{{ scale.name }}</span>
      <span class="scale-range">{{ scale.min || 1 }} - {{ scale.max || 5 }}</span>
    </div>
    <div class="scale-points">
      <div
        v-for="point in points"
        :key="point.value"
        class="scale-point"
        :class="{ 'scale-point--labeled': point.label }"
      >
        <div class="point-value">{{ point.value }}</div>
        <div v-if="point.label" class="point-label">{{ point.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  scale: {
    type: Object,
    required: true,
    validator: s => s && typeof s.name === 'string'
  }
})

const points = computed(() => {
  const min = props.scale.min || 1
  const max = props.scale.max || 5
  const labels = props.scale.labels || []

  const result = []
  for (let i = min; i <= max; i++) {
    result.push({
      value: i,
      label: labels[i - min] || null
    })
  }
  return result
})
</script>

<style scoped>
.scale-preview {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 8px 2px 8px 2px;
  padding: 10px 12px;
}

.scale-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scale-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.scale-range {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-family: 'Fira Code', monospace;
}

.scale-points {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.scale-point {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.point-value {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(176, 202, 151, 0.2);
  border: 1px solid rgba(176, 202, 151, 0.4);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6a8a52;
}

.scale-point--labeled .point-value {
  background: rgba(176, 202, 151, 0.3);
  border-color: #b0ca97;
}

.point-label {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: center;
  max-width: 50px;
  line-height: 1.2;
}
</style>
