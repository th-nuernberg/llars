<template>
  <div class="evaluation-status" :class="statusClass">
    <transition name="status-fade" mode="out-in">
      <div :key="displayStatus" class="status-content">
        <v-icon v-if="saving" size="16" class="saving-icon">mdi-loading</v-icon>
        <v-icon v-else-if="displayStatus === 'done'" size="16">mdi-check-circle</v-icon>
        <v-icon v-else-if="displayStatus === 'in_progress'" size="16">mdi-progress-clock</v-icon>
        <v-icon v-else size="16">mdi-circle-outline</v-icon>
        <span class="status-label">{{ statusLabel }}</span>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'pending',
    validator: (v) => ['pending', 'in_progress', 'done', 'not_started', 'progressing', 'completed'].includes(v)
  },
  saving: { type: Boolean, default: false }
})

// Normalize different status formats
const displayStatus = computed(() => {
  if (props.saving) return 'saving'

  const statusMap = {
    'pending': 'pending',
    'not_started': 'pending',
    'in_progress': 'in_progress',
    'progressing': 'in_progress',
    'Progressing': 'in_progress',
    'done': 'done',
    'completed': 'done',
    'Done': 'done'
  }
  return statusMap[props.status] || 'pending'
})

const statusClass = computed(() => {
  if (props.saving) return 'status-saving'
  return `status-${displayStatus.value}`
})

const statusLabel = computed(() => {
  if (props.saving) return 'Speichert...'

  const labels = {
    'pending': 'Ausstehend',
    'in_progress': 'In Bearbeitung',
    'done': 'Abgeschlossen'
  }
  return labels[displayStatus.value] || 'Ausstehend'
})
</script>

<style scoped>
.evaluation-status {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 16px 4px 16px 4px;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.status-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Pending State */
.status-pending {
  background: rgba(158, 158, 158, 0.15);
  color: #757575;
  border: 1px solid rgba(158, 158, 158, 0.3);
}

/* In Progress State */
.status-in_progress {
  background: rgba(232, 200, 122, 0.2);
  color: #b8860b;
  border: 1px solid rgba(232, 200, 122, 0.5);
}

/* Done State */
.status-done {
  background: rgba(76, 175, 80, 0.15);
  color: #2e7d32;
  border: 1px solid rgba(76, 175, 80, 0.4);
  animation: celebrate 0.5s ease-out;
}

/* Saving State */
.status-saving {
  background: rgba(136, 196, 200, 0.2);
  color: #00838f;
  border: 1px solid rgba(136, 196, 200, 0.5);
}

.saving-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes celebrate {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
    box-shadow: 0 0 20px rgba(76, 175, 80, 0.4);
  }
  100% {
    transform: scale(1);
  }
}

/* Transition */
.status-fade-enter-active,
.status-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.status-fade-enter-from {
  opacity: 0;
  transform: translateY(-5px);
}

.status-fade-leave-to {
  opacity: 0;
  transform: translateY(5px);
}
</style>
