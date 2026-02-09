<template>
  <v-autocomplete
    v-model="modelValueProxy"
    :items="modelItems"
    item-title="title"
    item-value="value"
    :return-object="false"
    :label="label"
    :prepend-inner-icon="prependIcon"
    :variant="variant"
    :density="density"
    :rules="resolvedRules"
    :loading="loading"
    :clearable="clearable"
    :disabled="disabled"
    :hide-details="hideDetails"
    :multiple="multiple"
    :chips="multiple"
    :closable-chips="multiple"
  >
    <template v-if="showSync" #append>
      <v-btn
        icon
        variant="text"
        size="small"
        :loading="syncLoading"
        @click="syncModels"
      >
        <LIcon>mdi-refresh</LIcon>
        <v-tooltip activator="parent" location="top">
          Modelle synchronisieren
        </v-tooltip>
      </v-btn>
    </template>

    <template #item="{ props: itemProps, item }">
      <v-list-item v-bind="itemProps">
        <template #prepend>
          <LIcon :color="item.raw.supports_vision ? 'success' : 'grey'">
            {{ item.raw.supports_vision ? 'mdi-eye' : 'mdi-text' }}
          </LIcon>
        </template>
        <v-list-item-title>{{ item.raw.display_name || item.raw.model_id }}</v-list-item-title>
        <v-list-item-subtitle class="text-caption">
          {{ item.raw.provider }} · {{ item.raw.model_id }}
        </v-list-item-subtitle>
      </v-list-item>
    </template>

    <template #selection="{ item }">
      <div class="d-flex align-center">
        <LIcon class="mr-2" size="18" :color="item.raw.supports_vision ? 'success' : 'grey'">
          {{ item.raw.supports_vision ? 'mdi-eye' : 'mdi-text' }}
        </LIcon>
        <span class="text-truncate">{{ item.raw.display_name || item.raw.model_id }}</span>
      </div>
    </template>

    <template #no-data>
      <div class="px-4 py-3 text-caption text-medium-emphasis">
        Keine LLM-Modelle verfügbar.
      </div>
    </template>
  </v-autocomplete>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'

const props = defineProps({
  modelValue: {
    type: [String, Array],
    default: null
  },
  multiple: {
    type: Boolean,
    default: false
  },
  modelType: {
    type: String,
    default: 'llm'
  },
  label: {
    type: String,
    default: 'LLM Modell'
  },
  prependIcon: {
    type: String,
    default: 'mdi-brain'
  },
  variant: {
    type: String,
    default: 'outlined'
  },
  density: {
    type: String,
    default: 'comfortable'
  },
  rules: {
    type: Array,
    default: () => []
  },
  required: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  hideDetails: {
    type: Boolean,
    default: false
  },
  activeOnly: {
    type: Boolean,
    default: true
  },
  visionOnly: {
    type: Boolean,
    default: false
  },
  reasoningOnly: {
    type: Boolean,
    default: false
  },
  autoSelectDefault: {
    type: Boolean,
    default: true
  },
  allowSync: {
    type: Boolean,
    default: false
  },
  includeUserProviders: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'models-loaded'])

const models = ref([])
const loading = ref(false)
const syncLoading = ref(false)

const { hasPermission, fetchPermissions } = usePermissions()

const modelValueProxy = computed({
  get: () => {
    if (props.multiple) {
      return Array.isArray(props.modelValue) ? props.modelValue : []
    }
    return props.modelValue
  },
  set: (value) => emit('update:modelValue', value)
})

const resolvedRules = computed(() => {
  if (props.rules?.length) return props.rules
  if (!props.required) return []
  return [value => (Array.isArray(value) ? value.length > 0 : !!value) || 'Pflichtfeld']
})

const showSync = computed(() => props.allowSync && hasPermission('admin:system:configure'))

const modelItems = computed(() => {
  const items = Array.isArray(models.value) ? [...models.value] : []
  const currentValues = props.multiple
    ? (Array.isArray(props.modelValue) ? props.modelValue : [])
    : (typeof props.modelValue === 'string' ? [props.modelValue] : [])

  currentValues
    .map(value => (typeof value === 'string' ? value.trim() : ''))
    .filter(Boolean)
    .forEach((current) => {
      if (!items.some(m => m.model_id === current)) {
        items.unshift({
          model_id: current,
          display_name: current,
          provider: 'custom',
          supports_vision: false,
          supports_reasoning: false,
          context_window: 0,
          max_output_tokens: 0
        })
      }
    })

  return items.map(m => ({
    title: m.display_name || m.model_id,
    value: m.model_id,
    ...m
  }))
})

const applyDefaultSelection = () => {
  if (props.multiple) return
  if (!props.autoSelectDefault) return
  const current = typeof props.modelValue === 'string' ? props.modelValue.trim() : ''
  if (current) return
  if (!models.value.length) return
  const def = models.value.find(m => m.is_default) || models.value[0]
  if (def?.model_id) {
    emit('update:modelValue', def.model_id)
  }
}

const loadModels = async () => {
  loading.value = true
  try {
    const requests = [
      axios.get('/api/llm/models/available', {
        params: {
          active_only: props.activeOnly,
          model_type: props.modelType,
          vision_only: props.visionOnly,
          reasoning_only: props.reasoningOnly
        }
      })
    ]
    if (props.includeUserProviders) {
      requests.push(axios.get('/api/user/providers/available'))
    }

    const results = await Promise.allSettled(requests)
    const modelsResult = results[0]
    const providersResult = results[1]

    const baseModels = modelsResult?.status === 'fulfilled'
      ? (modelsResult.value.data.models || [])
      : []

    let providerModels = []
    if (props.includeUserProviders && providersResult?.status === 'fulfilled') {
      const providers = providersResult.value.data?.providers || []
      providerModels = providers
        .map((provider) => {
          const config = provider?.config || {}
          const modelId = (config.model_id || '').trim()
          if (!modelId || !provider.api_key_set || provider.is_active === false) return null
          return {
            model_id: `user-provider:${provider.id}:${modelId}`,
            display_name: `${provider.name || 'Provider'} • ${modelId}`,
            provider: provider.name || provider.provider_type || 'User Provider',
            supports_vision: false,
            supports_reasoning: false,
            context_window: 0,
            max_output_tokens: 0,
            is_user_provider: true
          }
        })
        .filter(Boolean)
    }

    models.value = [...baseModels, ...providerModels]
  } catch (error) {
    console.error('[LlmModelSelect] Error loading models:', error)
    models.value = []
  } finally {
    loading.value = false
    applyDefaultSelection()
    emit('models-loaded', models.value)
  }
}

const syncModels = async () => {
  syncLoading.value = true
  try {
    await axios.post('/api/llm/models/sync')
  } catch (error) {
    console.warn('[LlmModelSelect] Model sync failed:', error)
  } finally {
    syncLoading.value = false
  }
  await loadModels()
}

watch(
  () => [props.modelType, props.activeOnly, props.visionOnly, props.reasoningOnly, props.includeUserProviders],
  () => loadModels()
)

watch(
  () => props.modelValue,
  () => applyDefaultSelection()
)

onMounted(async () => {
  if (props.allowSync) {
    await fetchPermissions()
  }
  await loadModels()
})
</script>
