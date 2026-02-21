<template>
  <LCard :title="$t('evaluationAssistant.controls.title')" icon="mdi-cog">
    <!-- Model Selection -->
    <v-select
      v-model="selectedModel"
      :items="availableModels"
      :label="$t('evaluationAssistant.controls.model')"
      item-title="display_name"
      item-value="id"
      variant="outlined"
      density="compact"
      :disabled="isRunning"
      class="mb-3"
    >
      <template #item="{ item, props }">
        <v-list-item v-bind="props">
          <template #prepend>
            <LIcon size="20" class="mr-2">mdi-robot</LIcon>
          </template>
          <v-list-item-subtitle>{{ item.raw.provider }}</v-list-item-subtitle>
        </v-list-item>
      </template>
    </v-select>

    <!-- Template Selection -->
    <v-select
      v-model="selectedTemplate"
      :items="templateOptions"
      :label="$t('evaluationAssistant.controls.template')"
      item-title="name"
      item-value="id"
      variant="outlined"
      density="compact"
      :disabled="isRunning"
      class="mb-4"
    >
      <template #item="{ item, props }">
        <v-list-item v-bind="props">
          <template #append>
            <LTag v-if="item.raw.is_default" variant="success" size="xs">
              {{ $t('evaluationAssistant.controls.default') }}
            </LTag>
          </template>
        </v-list-item>
      </template>
    </v-select>

    <!-- Action Buttons -->
    <div class="action-buttons">
      <LBtn
        v-if="!isRunning"
        variant="primary"
        prepend-icon="mdi-play"
        :disabled="!canStart"
        @click="handleStart"
        block
      >
        {{ $t('evaluationAssistant.controls.start') }}
      </LBtn>
      <LBtn
        v-else
        variant="danger"
        prepend-icon="mdi-stop"
        @click="handleStop"
        block
      >
        {{ $t('evaluationAssistant.controls.stop') }}
      </LBtn>
    </div>

    <!-- Warning for missing configuration -->
    <v-alert
      v-if="!canStart && !isRunning"
      type="warning"
      variant="tonal"
      density="compact"
      class="mt-3"
    >
      {{ missingConfigMessage }}
    </v-alert>
  </LCard>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EVAL_STATUS } from '@/composables/useLLMEvaluation'

const { t } = useI18n()

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  scenarioId: {
    type: [String, Number],
    required: true
  },
  availableModels: {
    type: Array,
    default: () => []
  },
  availableTemplates: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['start', 'stop'])

// State
const selectedModel = ref(null)
const selectedTemplate = ref(null)

// Computed
const isRunning = computed(() => props.status === EVAL_STATUS.RUNNING)

const templateOptions = computed(() => {
  return [
    { id: null, name: t('evaluationAssistant.controls.defaultTemplate'), is_default: true },
    ...props.availableTemplates
  ]
})

const canStart = computed(() => {
  return selectedModel.value && props.availableModels.length > 0
})

const missingConfigMessage = computed(() => {
  if (props.availableModels.length === 0) {
    return t('evaluationAssistant.controls.noModels')
  }
  if (!selectedModel.value) {
    return t('evaluationAssistant.controls.selectModel')
  }
  return ''
})

// Auto-select first model
watch(() => props.availableModels, (models) => {
  if (models.length > 0 && !selectedModel.value) {
    selectedModel.value = models[0].id
  }
}, { immediate: true })

// Methods
function handleStart() {
  emit('start', {
    modelId: selectedModel.value,
    promptTemplateId: selectedTemplate.value
  })
}

function handleStop() {
  emit('stop')
}
</script>

<style scoped>
.action-buttons {
  display: flex;
  gap: 8px;
}
</style>
