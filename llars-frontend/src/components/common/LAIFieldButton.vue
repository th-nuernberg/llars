<template>
  <LBtn
    :variant="variant"
    :size="size"
    :loading="generating"
    :disabled="disabled || !fieldKey"
    :tooltip="tooltip || $t('aiAssist.generate')"
    :tooltip-location="tooltipLocation"
    :prepend-icon="icon"
    class="l-ai-field-button"
    @click="handleGenerate"
  >
    <slot>{{ $t('aiAssist.generateShort') }}</slot>
  </LBtn>
</template>

<script setup>
/**
 * LAIFieldButton - AI-Assist Field Generation Button
 *
 * A button that triggers AI generation for a form field.
 * Uses the useAIAssist composable to call the generation API.
 *
 * @example
 * <v-text-field v-model="scenarioName">
 *   <template #append>
 *     <LAIFieldButton
 *       field-key="scenario.settings.name"
 *       :context="{ scenario_type: 'rating', existing_description }"
 *       @generated="scenarioName = $event"
 *     />
 *   </template>
 * </v-text-field>
 *
 * @example Icon-only button
 * <LAIFieldButton
 *   field-key="scenario.settings.name"
 *   :context="context"
 *   icon-only
 *   @generated="handleValue"
 * />
 */
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAIAssist } from '@/composables/useAIAssist'

const props = defineProps({
  /**
   * The field key for the prompt template (e.g., 'scenario.settings.name')
   */
  fieldKey: {
    type: String,
    required: true
  },
  /**
   * Context variables to pass to the prompt
   */
  context: {
    type: Object,
    default: () => ({})
  },
  /**
   * Whether to stream the response
   */
  stream: {
    type: Boolean,
    default: false
  },
  /**
   * Custom tooltip text
   */
  tooltip: {
    type: String,
    default: null
  },
  /**
   * Tooltip location
   */
  tooltipLocation: {
    type: String,
    default: 'top'
  },
  /**
   * Button variant (uses LLARS design system)
   */
  variant: {
    type: String,
    default: 'tonal'
  },
  /**
   * Button size
   */
  size: {
    type: String,
    default: 'small',
    validator: (v) => ['small', 'default', 'large'].includes(v)
  },
  /**
   * Whether the button is disabled
   */
  disabled: {
    type: Boolean,
    default: false
  },
  /**
   * Icon to show (defaults to sparkles)
   */
  icon: {
    type: String,
    default: 'mdi-auto-fix'
  }
})

const emit = defineEmits([
  /**
   * Emitted when generation completes successfully
   * @param {string} value - The generated value
   */
  'generated',
  /**
   * Emitted when generation starts/ends
   * @param {boolean} isGenerating - Whether generation is in progress
   */
  'generating',
  /**
   * Emitted when an error occurs
   * @param {Error} error - The error object
   */
  'error'
])

const { t } = useI18n()
const { generate, generating: aiGenerating, error: aiError } = useAIAssist()

const generating = computed(() => aiGenerating.value)

async function handleGenerate() {
  emit('generating', true)
  try {
    const value = await generate(props.fieldKey, props.context, props.stream)
    if (value) {
      emit('generated', value)
    }
  } catch (error) {
    console.error('AI generation failed:', error)
    emit('error', error)
  } finally {
    emit('generating', false)
  }
}
</script>

<style scoped>
.l-ai-field-button {
  /* Ensure button fits well in input append slots */
  flex-shrink: 0;
}

/* Add subtle glow effect when generating */
.l-ai-field-button:deep(.l-btn--loading) {
  box-shadow: 0 0 8px rgba(176, 202, 151, 0.4);
}
</style>
