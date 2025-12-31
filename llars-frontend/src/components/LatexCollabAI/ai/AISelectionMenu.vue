<template>
  <Teleport to="body">
    <transition name="menu-fade">
      <div
        v-if="visible && position"
        class="ai-selection-menu"
        :style="menuStyle"
        @mousedown.stop
      >
        <v-tooltip v-for="action in actions" :key="action.key" :text="action.tooltip" location="top">
          <template #activator="{ props }">
            <button
              v-bind="props"
              class="menu-action"
              :class="{ loading: loadingAction === action.key }"
              :disabled="loadingAction !== null"
              @click="handleAction(action)"
            >
              <v-icon v-if="loadingAction !== action.key" size="18">{{ action.icon }}</v-icon>
              <v-progress-circular
                v-else
                indeterminate
                size="16"
                width="2"
              />
            </button>
          </template>
        </v-tooltip>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import aiWritingService from '@/services/aiWritingService'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object, // { x, y }
    default: null
  },
  selectedText: {
    type: String,
    default: ''
  },
  documentContent: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'close',
  'rewrite',
  'expand',
  'summarize',
  'find-citation',
  'ask-chat',
  'fix-latex'
])

const loadingAction = ref(null)

const actions = [
  {
    key: 'rewrite',
    icon: 'mdi-refresh',
    tooltip: 'Umformulieren (Ctrl+Shift+R)',
    handler: 'rewrite'
  },
  {
    key: 'expand',
    icon: 'mdi-arrow-expand',
    tooltip: 'Erweitern (Ctrl+Shift+E)',
    handler: 'expand'
  },
  {
    key: 'summarize',
    icon: 'mdi-text-short',
    tooltip: 'Kürzen (Ctrl+Shift+K)',
    handler: 'summarize'
  },
  {
    key: 'cite',
    icon: 'mdi-book-search',
    tooltip: 'Zitat finden (Ctrl+Shift+C)',
    handler: 'find-citation'
  },
  {
    key: 'chat',
    icon: 'mdi-chat-question',
    tooltip: 'In Chat fragen (Ctrl+Shift+?)',
    handler: 'ask-chat'
  },
  {
    key: 'fix',
    icon: 'mdi-wrench',
    tooltip: 'LaTeX prüfen (Ctrl+Shift+L)',
    handler: 'fix-latex'
  }
]

const menuStyle = computed(() => {
  if (!props.position) return {}

  // Position above selection with some offset
  return {
    left: `${props.position.x}px`,
    top: `${props.position.y - 50}px`,
    transform: 'translateX(-50%)'
  }
})

async function handleAction(action) {
  loadingAction.value = action.key

  try {
    switch (action.handler) {
      case 'rewrite': {
        const result = await aiWritingService.rewrite({
          text: props.selectedText,
          style: 'academic',
          context: props.documentContent.substring(0, 500)
        })
        emit('rewrite', result.result)
        break
      }

      case 'expand': {
        const result = await aiWritingService.expand({
          text: props.selectedText,
          context: props.documentContent.substring(0, 500)
        })
        emit('expand', result.result)
        break
      }

      case 'summarize': {
        const result = await aiWritingService.summarize({
          text: props.selectedText
        })
        emit('summarize', result.result)
        break
      }

      case 'find-citation':
        emit('find-citation', props.selectedText)
        break

      case 'ask-chat':
        emit('ask-chat', props.selectedText)
        break

      case 'fix-latex': {
        const result = await aiWritingService.fixLatex(props.selectedText)
        emit('fix-latex', result)
        break
      }
    }
  } catch (e) {
    console.error('Selection action error:', e)
  } finally {
    loadingAction.value = null
    emit('close')
  }
}
</script>

<style scoped>
.ai-selection-menu {
  position: fixed;
  z-index: 9999;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px 2px 8px 2px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  padding: 4px;
  display: flex;
  gap: 2px;
}

.menu-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.menu-action:hover:not(:disabled) {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.menu-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-action.loading {
  background: rgba(var(--v-theme-primary), 0.1);
}

/* Animation */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: all 0.15s ease;
}

.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) scale(0.95);
}
</style>
