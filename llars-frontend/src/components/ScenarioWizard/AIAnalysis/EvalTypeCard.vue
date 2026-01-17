<template>
  <div class="eval-type-card" :class="{ 'is-loading': loading, 'is-complete': !loading && !streaming }">
    <!-- Header -->
    <div class="card-header">
      <v-icon size="18" class="mr-2">mdi-chart-box</v-icon>
      <span>{{ $t('scenarioWizard.analysis.evalType') }}</span>
    </div>

    <!-- Content -->
    <div class="card-content">
      <!-- Loading State -->
      <template v-if="loading">
        <div class="skeleton-icon"></div>
        <div class="skeleton-text skeleton-text--large"></div>
        <div class="skeleton-text skeleton-text--small"></div>
      </template>

      <!-- Content State -->
      <template v-else>
        <!-- Icon + Type Name -->
        <div class="eval-type-display">
          <v-icon :color="typeConfig.color" size="48" class="type-icon">
            {{ typeConfig.icon }}
          </v-icon>
          <div class="type-name">{{ typeConfig.label }}</div>
        </div>

        <!-- Confidence -->
        <div v-if="confidence !== null" class="confidence-section">
          <div class="confidence-label">
            {{ $t('scenarioWizard.analysis.confidence') }}: {{ confidencePercent }}%
          </div>
          <div class="confidence-dots">
            <span
              v-for="i in 10"
              :key="i"
              class="confidence-dot"
              :class="{ filled: i <= Math.round(confidence * 10) }"
              :style="{ backgroundColor: i <= Math.round(confidence * 10) ? confidenceColor : undefined }"
            ></span>
          </div>
        </div>

        <!-- Change Type Dropdown (when editable) -->
        <div v-if="editable" class="type-selector">
          <v-select
            v-model="localEvalType"
            :items="evalTypeOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            :label="$t('scenarioWizard.analysis.changeType')"
            @update:model-value="$emit('update:evalType', $event)"
          >
            <template #item="{ item, props }">
              <v-list-item v-bind="props">
                <template #prepend>
                  <v-icon :color="item.raw.color" size="20">{{ item.raw.icon }}</v-icon>
                </template>
              </v-list-item>
            </template>
          </v-select>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  evalType: {
    type: String,
    default: null
  },
  confidence: {
    type: Number,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  streaming: {
    type: Boolean,
    default: false
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:evalType'])

// Local state for v-model binding
const localEvalType = ref(props.evalType)
watch(() => props.evalType, (v) => { localEvalType.value = v })

// Eval type configuration
const EVAL_TYPE_CONFIG = {
  rating: {
    icon: 'mdi-star',
    color: '#D1BC8A',
    label: 'Rating'
  },
  ranking: {
    icon: 'mdi-sort-ascending',
    color: '#88c4c8',
    label: 'Ranking'
  },
  labeling: {
    icon: 'mdi-tag-multiple',
    color: '#b0ca97',
    label: 'Labeling'
  },
  comparison: {
    icon: 'mdi-compare',
    color: '#e8a087',
    label: 'Vergleich'
  },
  authenticity: {
    icon: 'mdi-shield-check',
    color: '#98d4bb',
    label: 'Authentizität'
  },
  text_classification: {
    icon: 'mdi-format-list-checks',
    color: '#b0ca97',
    label: 'Klassifikation'
  },
  mail_rating: {
    icon: 'mdi-email-check',
    color: '#D1BC8A',
    label: 'E-Mail Rating'
  },
  text_rating: {
    icon: 'mdi-text-box-check',
    color: '#D1BC8A',
    label: 'Text Rating'
  }
}

// Computed
const typeConfig = computed(() => {
  return EVAL_TYPE_CONFIG[props.evalType] || {
    icon: 'mdi-help-circle',
    color: '#888',
    label: props.evalType || '...'
  }
})

const confidencePercent = computed(() => {
  if (props.confidence === null) return 0
  return Math.round(props.confidence * 100)
})

const confidenceColor = computed(() => {
  if (props.confidence >= 0.7) return '#98d4bb' // Success green
  if (props.confidence >= 0.4) return '#D1BC8A' // Warning yellow
  return '#e8a087' // Danger red
})

const evalTypeOptions = computed(() => {
  return Object.entries(EVAL_TYPE_CONFIG).map(([value, config]) => ({
    value,
    label: config.label,
    icon: config.icon,
    color: config.color
  }))
})
</script>

<style scoped>
.eval-type-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(176, 202, 151, 0.3);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.eval-type-card.is-complete {
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
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

/* Loading Skeleton */
.skeleton-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #3a3a3a;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-text {
  background: #3a3a3a;
  border-radius: 4px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}

.skeleton-text--large {
  width: 80px;
  height: 24px;
}

.skeleton-text--small {
  width: 120px;
  height: 16px;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

/* Eval Type Display */
.eval-type-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.type-icon {
  animation: icon-appear 0.3s ease-out;
}

@keyframes icon-appear {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.type-name {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

/* Confidence */
.confidence-section {
  text-align: center;
  width: 100%;
}

.confidence-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.confidence-dots {
  display: flex;
  justify-content: center;
  gap: 4px;
}

.confidence-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #3a3a3a;
  transition: background-color 0.3s ease;
}

.confidence-dot.filled {
  background: #98d4bb;
}

/* Type Selector */
.type-selector {
  width: 100%;
  margin-top: 8px;
}

.type-selector :deep(.v-field) {
  border-radius: 8px 2px 8px 2px;
}
</style>
