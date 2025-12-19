<template>
  <LTag :variant="variant" :size="size" :prepend-icon="showIcon ? icon : null">
    {{ label }}
  </LTag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: [String, Boolean, null],
    default: null
  },
  size: {
    type: String,
    default: 'small'
  },
  showIcon: {
    type: Boolean,
    default: true
  }
})

const normalizedStatus = computed(() => {
  if (typeof props.status === 'boolean') {
    return props.status ? 'completed' : 'not_started'
  }

  const raw = String(props.status ?? '').trim().toLowerCase()
  if (!raw) return 'not_started'

  if (['done', 'completed', 'abgeschlossen', 'bewertet', 'ranked', 'rated', 'voted'].includes(raw)) {
    return 'completed'
  }

  if (['progressing', 'in bearbeitung', 'in_progress', 'in progress'].includes(raw)) {
    return 'progressing'
  }

  if (['not started', 'not_started', 'nicht begonnen', 'nicht bewertet', 'not ranked', 'not rated', 'not voted'].includes(raw)) {
    return 'not_started'
  }

  return 'not_started'
})

const label = computed(() => {
  if (normalizedStatus.value === 'completed') return 'Abgeschlossen'
  if (normalizedStatus.value === 'progressing') return 'In Bearbeitung'
  return 'Nicht begonnen'
})

const variant = computed(() => {
  if (normalizedStatus.value === 'completed') return 'success'
  if (normalizedStatus.value === 'progressing') return 'warning'
  return 'gray'
})

const icon = computed(() => {
  if (normalizedStatus.value === 'completed') return 'mdi-check-circle'
  if (normalizedStatus.value === 'progressing') return 'mdi-progress-clock'
  return 'mdi-play-circle-outline'
})
</script>

