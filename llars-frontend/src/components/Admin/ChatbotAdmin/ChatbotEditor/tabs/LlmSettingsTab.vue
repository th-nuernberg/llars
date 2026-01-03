<!--
  ChatbotEditor - LLM Settings Tab

  Model selection, temperature, max tokens, prompt templates, system prompt and welcome message.
-->
<template>
  <v-form ref="formLLM" class="llm-tab-form">
    <!-- Top section: Model & Prompt Templates -->
    <div class="llm-top-section">
      <v-row dense>
        <!-- Model Selection -->
        <v-col cols="12" md="6">
          <v-combobox
            v-model="formData.model_name"
            :items="llmModelItems"
            item-title="title"
            item-value="value"
            :return-object="false"
            label="Modell"
            variant="outlined"
            density="compact"
            :loading="llmModelsLoading"
            clearable
            hide-details
          >
            <template #append>
              <v-btn
                icon
                variant="text"
                size="x-small"
                :loading="llmModelsLoading"
                @click="$emit('sync-models')"
              >
                <v-icon size="18">mdi-refresh</v-icon>
              </v-btn>
            </template>
          </v-combobox>
        </v-col>

        <!-- Temperature -->
        <v-col cols="12" md="3">
          <v-text-field
            v-model.number="formData.temperature"
            label="Temperatur"
            type="number"
            :min="0"
            :max="2"
            :step="0.1"
            variant="outlined"
            density="compact"
            hide-details
          />
        </v-col>

        <!-- Max Tokens -->
        <v-col cols="12" md="3">
          <v-text-field
            v-model.number="formData.max_tokens"
            label="Max. Tokens"
            type="number"
            variant="outlined"
            density="compact"
            hide-details
          />
        </v-col>

        <!-- Prompt Templates -->
        <v-col cols="12">
          <div class="d-flex align-center flex-wrap ga-1">
            <span class="text-caption text-medium-emphasis mr-2">Vorlagen:</span>
            <v-chip
              v-for="template in promptTemplates"
              :key="template.name"
              variant="outlined"
              size="small"
              @click="$emit('apply-template', template)"
            >
              <v-icon start size="14">{{ template.icon }}</v-icon>
              {{ template.name }}
            </v-chip>
          </div>
        </v-col>
      </v-row>
    </div>

    <!-- Bottom section: System Prompt + Welcome Message split -->
    <div class="llm-prompts-split">
      <!-- System Prompt -->
      <div class="prompt-panel">
        <div class="prompt-panel-header">
          <v-icon size="18" class="mr-1">mdi-code-braces</v-icon>
          System Prompt
          <span class="text-caption text-medium-emphasis ml-auto">
            {{ formData.system_prompt?.length || 0 }} Zeichen
          </span>
        </div>
        <div class="prompt-panel-content">
          <textarea
            v-model="formData.system_prompt"
            class="prompt-textarea-full"
            placeholder="Definieren Sie die Rolle und das Verhalten des Chatbots..."
            @input="$emit('update-line-count')"
          />
        </div>
      </div>

      <!-- Welcome Message -->
      <div class="prompt-panel">
        <div class="prompt-panel-header">
          <v-icon size="18" class="mr-1">mdi-message-text</v-icon>
          Willkommensnachricht
          <span class="text-caption text-medium-emphasis ml-auto">
            {{ formData.welcome_message?.length || 0 }} Zeichen
          </span>
        </div>
        <div class="prompt-panel-content">
          <textarea
            v-model="formData.welcome_message"
            class="prompt-textarea-full"
            placeholder="Erste Nachricht beim Start eines Gesprächs..."
          />
        </div>
      </div>
    </div>
  </v-form>
</template>

<script setup>
/**
 * @component LlmSettingsTab
 * @description LLM configuration tab with model selection and prompts.
 */

defineProps({
  /** Form data object */
  formData: {
    type: Object,
    required: true
  },
  /** Available LLM models */
  llmModelItems: {
    type: Array,
    default: () => []
  },
  /** LLM models loading state */
  llmModelsLoading: {
    type: Boolean,
    default: false
  },
  /** Available prompt templates */
  promptTemplates: {
    type: Array,
    default: () => []
  }
});

defineEmits(['sync-models', 'apply-template', 'update-line-count']);
</script>

<style scoped>
/* LLM Tab Split Layout */
.llm-tab-form {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 100%;
  overflow: visible;
}

.llm-top-section {
  flex-shrink: 0;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  margin-bottom: 16px;
}

.llm-prompts-split {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

.prompt-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px 2px 8px 2px;
  overflow: hidden;
}

.prompt-panel-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  font-weight: 500;
  font-size: 14px;
  flex-shrink: 0;
}

.prompt-panel-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.prompt-textarea-full {
  flex: 1;
  width: 100%;
  min-height: 0;
  padding: 12px 14px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
  overflow-y: auto;
}

.prompt-textarea-full::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Responsive: Stack on smaller screens */
@media (max-width: 768px) {
  .llm-prompts-split {
    flex-direction: column;
  }

  .prompt-panel {
    flex: none;
    min-height: 200px;
  }
}
</style>
