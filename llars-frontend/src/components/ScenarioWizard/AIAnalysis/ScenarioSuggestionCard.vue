<template>
  <div class="scenario-card" :class="{ 'is-loading': loading, 'is-complete': !loading && !streaming }">
    <!-- Header -->
    <div class="card-header">
      <v-icon size="18" class="mr-2">mdi-file-document-edit</v-icon>
      <span>{{ $t('scenarioWizard.analysis.scenarioSuggestion') }}</span>
    </div>

    <!-- Content -->
    <div class="card-content">
      <!-- Loading State -->
      <template v-if="loading">
        <div class="skeleton-field">
          <div class="skeleton-label"></div>
          <div class="skeleton-input"></div>
        </div>
        <div class="skeleton-field">
          <div class="skeleton-label"></div>
          <div class="skeleton-textarea"></div>
        </div>
      </template>

      <!-- Content State -->
      <template v-else>
        <!-- Scenario Name -->
        <div class="field-group">
          <label class="field-label">{{ $t('scenarioWizard.analysis.scenarioName') }}</label>
          <div class="streaming-field" :class="{ streaming: nameStreaming }">
            <v-text-field
              v-model="localName"
              variant="outlined"
              density="compact"
              hide-details
              :readonly="nameStreaming"
              @update:model-value="$emit('update:name', $event)"
            >
              <template #append-inner>
                <span v-if="nameStreaming" class="streaming-cursor">|</span>
                <v-icon v-else-if="editable" size="18" color="rgba(255,255,255,0.5)">mdi-pencil</v-icon>
              </template>
            </v-text-field>
          </div>
        </div>

        <!-- Scenario Description -->
        <div class="field-group">
          <label class="field-label">{{ $t('scenarioWizard.analysis.scenarioDescription') }}</label>
          <div class="streaming-field" :class="{ streaming: descriptionStreaming }">
            <v-textarea
              v-model="localDescription"
              variant="outlined"
              density="compact"
              hide-details
              rows="3"
              auto-grow
              :readonly="descriptionStreaming"
              @update:model-value="$emit('update:description', $event)"
            >
              <template #append-inner>
                <span v-if="descriptionStreaming" class="streaming-cursor">|</span>
                <v-icon v-else-if="editable" size="18" color="rgba(255,255,255,0.5)">mdi-pencil</v-icon>
              </template>
            </v-textarea>
          </div>
        </div>

        <!-- Regenerate Button -->
        <div v-if="editable && !streaming" class="regenerate-section">
          <v-btn
            variant="text"
            size="small"
            color="primary"
            prepend-icon="mdi-refresh"
            @click="$emit('regenerate')"
          >
            {{ $t('scenarioWizard.analysis.regenerate') }}
          </v-btn>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    default: ''
  },
  description: {
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
  nameStreaming: {
    type: Boolean,
    default: false
  },
  descriptionStreaming: {
    type: Boolean,
    default: false
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:name', 'update:description', 'regenerate'])

// Local state for v-model binding
const localName = ref(props.name)
const localDescription = ref(props.description)

watch(() => props.name, (v) => { localName.value = v })
watch(() => props.description, (v) => { localDescription.value = v })
</script>

<style scoped>
.scenario-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(176, 202, 151, 0.3);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.scenario-card.is-complete {
  border-color: rgba(176, 202, 151, 0.6);
}

.card-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(176, 202, 151, 0.1);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #b0ca97;
}

.card-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Loading Skeleton */
.skeleton-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-label {
  width: 80px;
  height: 12px;
  background: #3a3a3a;
  border-radius: 4px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-input {
  width: 100%;
  height: 40px;
  background: #3a3a3a;
  border-radius: 8px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-textarea {
  width: 100%;
  height: 80px;
  background: #3a3a3a;
  border-radius: 8px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

/* Field Groups */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Streaming Field */
.streaming-field :deep(.v-field) {
  border-radius: 8px 2px 8px 2px;
  transition: border-color 0.3s ease;
}

.streaming-field.streaming :deep(.v-field) {
  border-color: rgba(176, 202, 151, 0.5);
}

/* Streaming Cursor */
.streaming-cursor {
  color: #b0ca97;
  font-weight: bold;
  animation: cursor-blink 1s infinite;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Regenerate */
.regenerate-section {
  display: flex;
  justify-content: flex-end;
}

.regenerate-section :deep(.v-btn) {
  text-transform: none;
  font-size: 13px;
}
</style>
