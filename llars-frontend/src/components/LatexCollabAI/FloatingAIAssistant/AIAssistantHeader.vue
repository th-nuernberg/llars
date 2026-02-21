<template>
  <div
    class="assistant-header"
    @mousedown="$emit('mousedown', $event)"
  >
    <div class="header-main">
      <div class="header-title">
        <LIcon class="mr-2" color="white">mdi-robot-happy</LIcon>
        <span>{{ $t('floatingAi.title') }}</span>
      </div>
      <div class="header-actions">
        <v-btn
          icon
          variant="text"
          size="x-small"
          color="white"
          :title="$t('floatingAi.minimize')"
          @click.stop="$emit('minimize')"
        >
          <LIcon size="18">mdi-minus</LIcon>
        </v-btn>
        <v-btn
          icon
          variant="text"
          size="x-small"
          color="white"
          :title="$t('floatingAi.close')"
          @click.stop="$emit('close')"
        >
          <LIcon size="18">mdi-close</LIcon>
        </v-btn>
      </div>
    </div>

    <!-- Context Info Bar -->
    <div class="header-context" v-if="hasContext">
      <div class="context-item" v-if="context.fileName">
        <LIcon size="14" class="mr-1">mdi-file-document</LIcon>
        <span class="context-text">{{ context.fileName }}</span>
      </div>
      <div class="context-item" v-if="context.currentSection">
        <LIcon size="14" class="mr-1">mdi-map-marker</LIcon>
        <span class="context-text">{{ context.currentSection.title }}</span>
      </div>
      <div class="context-item selection" v-if="context.selection?.hasSelection">
        <LIcon size="14" class="mr-1">mdi-selection</LIcon>
        <span class="context-text">{{ truncatedSelection }}</span>
        <span class="context-count">({{ selectionWordCount }}w)</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  context: {
    type: Object,
    default: () => ({})
  },
  isDragging: {
    type: Boolean,
    default: false
  }
})

defineEmits(['mousedown', 'minimize', 'close'])

const hasContext = computed(() => {
  return props.context.fileName ||
         props.context.currentSection ||
         props.context.selection?.hasSelection
})

const truncatedSelection = computed(() => {
  const text = props.context.selection?.text || ''
  if (text.length > 30) {
    return text.substring(0, 30) + '...'
  }
  return text
})

const selectionWordCount = computed(() => {
  const text = props.context.selection?.text || ''
  return text.split(/\s+/).filter(w => w.length > 0).length
})
</script>

<style scoped>
.assistant-header {
  flex-shrink: 0;
  background: linear-gradient(135deg, #88c4c8 0%, #b0ca97 100%);
  cursor: grab;
  user-select: none;
}

.assistant-header:active {
  cursor: grabbing;
}

.header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
}

.header-title {
  display: flex;
  align-items: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.header-context {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.15);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.context-item {
  display: flex;
  align-items: center;
  color: white;
  font-size: 11px;
  opacity: 0.9;
}

.context-item.selection {
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
}

.context-text {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-count {
  margin-left: 4px;
  opacity: 0.7;
  font-size: 10px;
}
</style>
