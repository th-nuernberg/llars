<template>
  <div class="queue-panel">
    <!-- Header -->
    <div class="queue-header">
      <div class="d-flex align-center gap-1">
        <LIcon size="16">mdi-playlist-play</LIcon>
        <span class="queue-title">Warteschlange</span>
      </div>
      <div class="d-flex align-center gap-1">
        <v-chip size="x-small" color="info" v-if="queue.stats?.pending > 0">
          {{ queue.stats?.pending }} offen
        </v-chip>
        <v-chip size="x-small" color="warning" v-if="queue.stats?.running > 0">
          {{ queue.stats?.running }} läuft
        </v-chip>
        <v-chip size="x-small" color="success" v-if="queue.stats?.completed > 0">
          {{ queue.stats?.completed }} fertig
        </v-chip>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          size="x-small"
          density="compact"
          @click="$emit('refresh')"
          :loading="loading"
        ></v-btn>
      </div>
    </div>

    <!-- Queue Content -->
    <div class="queue-content">
      <template v-if="allQueueItems.length > 0">
        <div
          v-for="item in displayedItems"
          :key="item.queue_position"
          class="queue-item"
          :class="{ 'queue-item-running': item.status === 'running' }"
        >
          <div class="queue-position">#{{ item.queue_position + 1 }}</div>
          <div class="queue-pillars">
            <span class="pillar-badge pillar-a">{{ truncatePillar(item.pillar_a_name) }}</span>
            <LIcon size="10" color="grey">mdi-arrow-left-right</LIcon>
            <span class="pillar-badge pillar-b">{{ truncatePillar(item.pillar_b_name) }}</span>
          </div>
          <div class="queue-status">
            <v-chip
              size="x-small"
              :color="getQueueStatusColor(item.status)"
              variant="flat"
            >
              <LIcon start size="10" :class="{ 'rotating': item.status === 'running' }">
                {{ getQueueStatusIcon(item.status) }}
              </LIcon>
              {{ getQueueStatusText(item.status) }}
            </v-chip>
          </div>
        </div>

        <!-- Show more indicator -->
        <div v-if="allQueueItems.length > maxDisplayItems" class="queue-more">
          <span class="text-caption text-medium-emphasis">
            + {{ allQueueItems.length - maxDisplayItems }} weitere
          </span>
        </div>
      </template>

      <!-- Empty State -->
      <div v-else class="queue-empty">
        <LIcon size="24" color="grey">mdi-playlist-remove</LIcon>
        <span class="text-caption text-medium-emphasis">Keine Vergleiche in Warteschlange</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  queue: {
    type: Object,
    required: true
  },
  allQueueItems: {
    type: Array,
    default: () => []
  },
  headers: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  getQueueStatusColor: {
    type: Function,
    required: true
  },
  getQueueStatusIcon: {
    type: Function,
    required: true
  },
  getQueueStatusText: {
    type: Function,
    required: true
  }
});

defineEmits(['refresh']);

const maxDisplayItems = 10;

const displayedItems = computed(() => {
  return props.allQueueItems.slice(0, maxDisplayItems);
});

const truncatePillar = (name) => {
  if (!name) return '?';
  return name.length > 10 ? name.substring(0, 10) + '...' : name;
};
</script>

<style scoped>
.queue-panel {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden;
  height: 100%;
}

.queue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
}

.queue-title {
  font-size: 12px;
  font-weight: 600;
}

.queue-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.queue-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  margin-bottom: 4px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  transition: background 0.2s ease;
}

.queue-item:hover {
  background: rgba(var(--v-theme-surface-variant), 0.4);
}

.queue-item-running {
  background: rgba(var(--v-theme-warning), 0.1);
  border: 1px solid rgba(var(--v-theme-warning), 0.3);
}

.queue-position {
  font-size: 10px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  min-width: 28px;
}

.queue-pillars {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.pillar-badge {
  font-size: 9px;
  font-weight: 600;
  padding: 2px 5px;
  border-radius: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pillar-a {
  background: rgba(33, 150, 243, 0.15);
  color: rgb(33, 150, 243);
}

.pillar-b {
  background: rgba(76, 175, 80, 0.15);
  color: rgb(76, 175, 80);
}

.queue-status {
  flex-shrink: 0;
}

.queue-more {
  text-align: center;
  padding: 8px;
}

.queue-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* Animations */
.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
