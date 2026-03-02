<template>
  <v-dialog v-model="dialogVisible" max-width="560" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start color="accent">mdi-auto-fix</v-icon>
        {{ t('conferenceManager.wizard.title') }}
        <v-spacer />
        <v-btn icon variant="text" @click="close"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>

      <v-card-text>
        <!-- Phase 1: Input -->
        <template v-if="!streaming">
          <p class="text-body-2 mb-4" style="opacity: 0.7">
            {{ t('conferenceManager.wizard.description') }}
          </p>

          <v-text-field
            v-model="query"
            :label="t('conferenceManager.wizard.inputLabel')"
            :placeholder="t('conferenceManager.wizard.inputPlaceholder')"
            :hint="t('conferenceManager.wizard.hint')"
            variant="outlined"
            density="compact"
            persistent-hint
            autofocus
            prepend-inner-icon="mdi-magnify"
            :error-messages="errorMsg"
            @keyup.enter="startSearch"
          />
        </template>

        <!-- Phase 2: Progress -->
        <template v-else>
          <div class="steps-container">
            <div v-for="(step, i) in steps" :key="step.key" class="step-row" :class="{ active: currentStep === step.key, done: isStepDone(step.key) }">
              <div class="step-icon">
                <v-progress-circular v-if="currentStep === step.key && !isDone && !hasError" :size="18" :width="2" indeterminate color="accent" />
                <v-icon v-else-if="isStepDone(step.key)" size="18" color="success">mdi-check-circle</v-icon>
                <v-icon v-else-if="hasError && currentStep === step.key" size="18" color="error">mdi-alert-circle</v-icon>
                <v-icon v-else size="18" style="opacity: 0.25">mdi-circle-outline</v-icon>
              </div>
              <span class="step-label">{{ t(`conferenceManager.wizard.steps.${step.key}`) }}</span>
            </div>
          </div>

          <div v-if="hasError" class="error-box mt-4">
            <v-icon size="16" color="error" class="mr-1">mdi-alert</v-icon>
            <span>{{ errorMsg }}</span>
          </div>

          <div v-if="searchResults.length" class="search-results mt-3">
            <div v-for="(sr, i) in searchResults.slice(0, 3)" :key="i" class="search-result-item">
              <span class="sr-title">{{ sr.title }}</span>
              <span class="sr-url">{{ sr.url }}</span>
            </div>
          </div>
        </template>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">{{ t('conferenceManager.actions.cancel') }}</v-btn>
        <v-btn
          v-if="!streaming"
          color="accent"
          variant="flat"
          :disabled="!query.trim()"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          prepend-icon="mdi-auto-fix"
          @click="startSearch"
        >
          {{ t('conferenceManager.wizard.search') }}
        </v-btn>
        <v-btn
          v-if="hasError"
          color="accent"
          variant="outlined"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          prepend-icon="mdi-refresh"
          @click="retry"
        >
          {{ t('conferenceManager.wizard.retry') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'

const { t } = useI18n()
const auth = useAuth()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'wizard-result'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const query = ref('')
const streaming = ref(false)
const currentStep = ref(null)
const isDone = ref(false)
const hasError = ref(false)
const errorMsg = ref('')
const searchResults = ref([])

const steps = [
  { key: 'searching' },
  { key: 'scraping' },
  { key: 'analyzing' },
  { key: 'done' },
]

const stepOrder = ['searching', 'scraping', 'analyzing', 'done']

function isStepDone(key) {
  if (isDone.value) return true
  const current = stepOrder.indexOf(currentStep.value)
  const target = stepOrder.indexOf(key)
  return current > target
}

function close() {
  dialogVisible.value = false
  reset()
}

function reset() {
  streaming.value = false
  currentStep.value = null
  isDone.value = false
  hasError.value = false
  errorMsg.value = ''
  searchResults.value = []
}

function retry() {
  reset()
}

async function startSearch() {
  if (!query.value.trim()) return

  streaming.value = true
  hasError.value = false
  errorMsg.value = ''
  currentStep.value = 'searching'

  try {
    const headers = { 'Content-Type': 'application/json' }
    const token = auth.getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    const response = await fetch('/api/conference-manager/conferences/wizard/stream', {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({ query: query.value.trim() }),
    })

    if (!response.ok || !response.body) {
      throw new Error(`Request failed: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const lines = part.trim().split('\n')
        let eventName = 'message'
        let eventData = ''

        for (const line of lines) {
          if (line.startsWith('event:')) eventName = line.slice(6).trim()
          else if (line.startsWith('data:')) eventData = line.slice(5).trim()
        }

        if (!eventData) continue

        try {
          const payload = JSON.parse(eventData)
          handleEvent(eventName, payload)
        } catch (e) {
          console.warn('SSE parse error:', e)
        }
      }
    }
  } catch (e) {
    hasError.value = true
    errorMsg.value = t('conferenceManager.wizard.errors.failed')
    console.error('Wizard stream failed:', e)
  }
}

function handleEvent(name, data) {
  switch (name) {
    case 'searching':
      currentStep.value = 'searching'
      break
    case 'search_results':
      searchResults.value = data.results || []
      break
    case 'scraping':
      currentStep.value = 'scraping'
      break
    case 'thinking':
      currentStep.value = 'analyzing'
      break
    case 'chunk':
      // LLM streaming token – keep step on analyzing
      break
    case 'result':
      emit('wizard-result', data)
      break
    case 'done':
      currentStep.value = 'done'
      isDone.value = true
      // Auto-close after short delay to show the done state
      setTimeout(() => close(), 600)
      break
    case 'error':
      hasError.value = true
      if (data.error === 'no_results') {
        errorMsg.value = t('conferenceManager.wizard.errors.noResults')
      } else if (data.error === 'no_llm') {
        errorMsg.value = t('conferenceManager.wizard.errors.noLlm')
      } else {
        errorMsg.value = data.message || t('conferenceManager.wizard.errors.failed')
      }
      break
  }
}
</script>

<style scoped>
.steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.step-row {
  display: flex;
  align-items: center;
  gap: 10px;
  opacity: 0.4;
  transition: opacity 0.3s;
}

.step-row.active,
.step-row.done {
  opacity: 1;
}

.step-icon {
  width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-label {
  font-size: 0.875rem;
}

.error-box {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  background: rgba(232, 160, 135, 0.1);
  color: #c4735a;
  font-size: 0.82rem;
}

.search-results {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  padding-top: 8px;
}

.search-result-item {
  display: flex;
  flex-direction: column;
  padding: 4px 0;
  gap: 1px;
}

.sr-title {
  font-size: 0.78rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sr-url {
  font-size: 0.68rem;
  opacity: 0.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
