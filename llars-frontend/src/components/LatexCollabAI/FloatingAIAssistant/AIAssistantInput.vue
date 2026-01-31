<template>
  <div class="assistant-input">
    <!-- Quick Actions -->
    <div class="quick-actions">
      <LBtn
        v-for="action in quickActions"
        :key="action.id"
        :variant="action.requiresSelection && !hasSelection ? 'outlined' : 'secondary'"
        size="x-small"
        :disabled="action.requiresSelection && !hasSelection"
        :title="action.requiresSelection && !hasSelection ? $t('floatingAi.quickActions.selectFirst') : ''"
        @click="$emit('quick-action', action.id)"
      >
        <LIcon size="14" class="mr-1">{{ action.icon }}</LIcon>
        {{ action.label }}
      </LBtn>
      <v-menu v-if="moreActions.length">
        <template #activator="{ props }">
          <LBtn variant="text" size="x-small" v-bind="props">
            <LIcon size="14">mdi-dots-horizontal</LIcon>
          </LBtn>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="action in moreActions"
            :key="action.id"
            :disabled="action.requiresSelection && !hasSelection"
            @click="$emit('quick-action', action.id)"
          >
            <template #prepend>
              <LIcon size="16">{{ action.icon }}</LIcon>
            </template>
            <v-list-item-title>{{ action.label }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </div>

    <!-- Input Area -->
    <div class="input-area">
      <v-textarea
        :model-value="modelValue"
        @update:model-value="$emit('update:modelValue', $event)"
        :placeholder="inputPlaceholder"
        rows="2"
        max-rows="4"
        auto-grow
        hide-details
        density="compact"
        variant="outlined"
        @keydown.ctrl.enter="$emit('send')"
        @keydown.meta.enter="$emit('send')"
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <LBtn
        variant="primary"
        size="small"
        :loading="isLoading"
        :disabled="!modelValue?.trim()"
        @click="$emit('send')"
      >
        <LIcon>mdi-send</LIcon>
      </LBtn>
    </div>

    <!-- Context Hint -->
    <div class="context-hint" v-if="contextHint">
      <LIcon size="12" class="mr-1">mdi-information-outline</LIcon>
      <span>{{ contextHint }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  context: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['update:modelValue', 'send', 'quick-action'])

const { t } = useI18n()

const hasSelection = computed(() => {
  return props.context.selection?.hasSelection
})

const allActions = computed(() => [
  {
    id: 'title',
    label: t('floatingAi.quickActions.title'),
    icon: 'mdi-format-title',
    requiresSelection: false
  },
  {
    id: 'abstract',
    label: t('floatingAi.quickActions.abstract'),
    icon: 'mdi-text-box-outline',
    requiresSelection: false
  },
  {
    id: 'rewrite',
    label: t('floatingAi.quickActions.rewrite'),
    icon: 'mdi-pencil-outline',
    requiresSelection: true
  },
  {
    id: 'expand',
    label: t('floatingAi.quickActions.expand'),
    icon: 'mdi-arrow-expand-horizontal',
    requiresSelection: true
  },
  {
    id: 'fix',
    label: t('floatingAi.quickActions.fix'),
    icon: 'mdi-wrench-outline',
    requiresSelection: false
  }
])

const quickActions = computed(() => allActions.value.slice(0, 4))
const moreActions = computed(() => allActions.value.slice(4))

const inputPlaceholder = computed(() => {
  if (hasSelection.value) {
    return t('floatingAi.input.placeholderSelection')
  }
  return t('floatingAi.input.placeholder')
})

const contextHint = computed(() => {
  if (props.context.currentSection) {
    return t('floatingAi.input.contextHint', { section: props.context.currentSection.title })
  }
  return null
})
</script>

<style scoped>
.assistant-input {
  flex-shrink: 0;
  padding: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.input-area {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-area :deep(.v-input) {
  flex: 1;
}

.input-area :deep(.v-field) {
  border-radius: 12px 4px 12px 4px;
}

.context-hint {
  display: flex;
  align-items: center;
  margin-top: 6px;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
