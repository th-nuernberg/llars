<template>
  <div class="reasoning-card" :class="{ 'is-loading': loading, 'is-collapsed': isCollapsed }">
    <!-- Header (clickable to toggle) -->
    <div class="card-header" @click="toggle">
      <div class="header-left">
        <v-icon size="18" class="mr-2">mdi-comment-text</v-icon>
        <span>{{ $t('scenarioWizard.analysis.reasoning') }}</span>
      </div>
      <v-icon size="20" class="toggle-icon" :class="{ rotated: !isCollapsed }">
        mdi-chevron-down
      </v-icon>
    </div>

    <!-- Content (collapsible) -->
    <v-expand-transition>
      <div v-show="!isCollapsed" class="card-content">
        <!-- Loading State -->
        <template v-if="loading">
          <div class="skeleton-line" style="width: 100%"></div>
          <div class="skeleton-line" style="width: 90%"></div>
          <div class="skeleton-line" style="width: 95%"></div>
        </template>

        <!-- Content State -->
        <template v-else>
          <div class="reasoning-text" :class="{ streaming: streaming }">
            <span v-if="reasoning">{{ reasoning }}</span>
            <span v-else class="no-content">{{ $t('scenarioWizard.analysis.noReasoning') }}</span>
            <span v-if="streaming" class="streaming-cursor">|</span>
          </div>
        </template>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  reasoning: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  streaming: {
    type: Boolean,
    default: false
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:collapsed'])

// Local state
const isCollapsed = ref(props.collapsed)

watch(() => props.collapsed, (v) => { isCollapsed.value = v })

// Auto-expand when streaming starts
watch(() => props.streaming, (streaming) => {
  if (streaming) {
    isCollapsed.value = false
  }
})

// Auto-collapse when streaming ends (after a delay)
watch([() => props.streaming, () => props.loading], ([streaming, loading]) => {
  if (!streaming && !loading && props.reasoning) {
    // Keep expanded for a moment after streaming ends
    setTimeout(() => {
      // Only collapse if user hasn't interacted
      // (could add a "userInteracted" flag if needed)
    }, 2000)
  }
})

function toggle() {
  isCollapsed.value = !isCollapsed.value
  emit('update:collapsed', isCollapsed.value)
}
</script>

<style scoped>
.reasoning-card {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(176, 202, 151, 0.2);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.reasoning-card:not(.is-collapsed) {
  border-color: rgba(176, 202, 151, 0.4);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(176, 202, 151, 0.05);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.card-header:hover {
  background: rgba(176, 202, 151, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #b0ca97;
}

.toggle-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: transform 0.3s ease;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.card-content {
  padding: 16px;
  max-height: 120px;
  overflow-y: auto;
}

/* Loading Skeleton */
.skeleton-line {
  height: 14px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
  margin-bottom: 8px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-line:last-child {
  margin-bottom: 0;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* Reasoning Text */
.reasoning-text {
  font-size: 14px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.85);
  font-style: italic;
}

.reasoning-text::before {
  content: '"';
  color: #b0ca97;
  font-size: 20px;
  margin-right: 4px;
}

.reasoning-text::after {
  content: '"';
  color: #b0ca97;
  font-size: 20px;
  margin-left: 4px;
}

.reasoning-text.streaming::after {
  content: none;
}

.no-content {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-style: normal;
}

/* Streaming Cursor */
.streaming-cursor {
  color: #b0ca97;
  font-weight: bold;
  font-style: normal;
  animation: cursor-blink 1s infinite;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
