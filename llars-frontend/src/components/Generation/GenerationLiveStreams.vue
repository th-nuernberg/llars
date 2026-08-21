<!--
  GenerationLiveStreams.vue - Multi-Stream Live Preview

  Shows up to N parallel live-streaming outputs during batch generation.
  Responsive grid: 1 col (1 stream), 2 cols (2-3), 3 cols (4+).
-->
<template>
  <div v-if="isJobRunning || streams.length > 0" class="live-streams">
    <!-- Header -->
    <div class="streams-header">
      <div class="streams-title">
        <v-progress-circular
          v-if="parsedStreams.length > 0"
          indeterminate
          size="14"
          width="2"
          color="primary"
          class="mr-2"
        />
        <LIcon v-else size="16" color="grey" class="mr-2">mdi-access-point</LIcon>
        <span>{{ $t('generation.detail.liveStreams') }}</span>
      </div>
      <span class="streams-count">
        {{ parsedStreams.length }}/{{ maxParallel }} {{ $t('generation.detail.active') }}
      </span>
    </div>

    <!-- Stream Grid -->
    <div class="streams-grid" :class="gridClass">
      <!-- Active Streams -->
      <div
        v-for="stream in parsedStreams"
        :key="stream.outputId"
        class="stream-card"
        :class="{
          'stream-completed': stream.justCompleted,
          'stream-failed': stream.justFailed
        }"
      >
        <div class="stream-card-header">
          <LTag
            variant="default"
            size="small"
            :style="getModelTagStyle(stream.modelColor, stream.model)"
          >
            {{ formatModelName(stream.model) }}
          </LTag>
          <span v-if="stream.tokenCount" class="stream-tokens">
            {{ stream.tokenCount }} tok
          </span>
        </div>
        <div class="stream-item-name">{{ stream.itemName }}</div>
        <div class="stream-content" :ref="el => setStreamRef(stream.outputId, el)">
          <template v-if="stream.visibleContent">{{ stream.visibleContent }}<span class="cursor">|</span></template>
          <span v-else-if="stream.thoughtsContent" class="stream-waiting">{{ $t('generation.detail.thinkingHidden') }}</span>
          <span v-else class="stream-waiting">{{ $t('generation.detail.waitingForResponse') }}</span>
        </div>
        <details v-if="stream.thoughtsContent" class="stream-thoughts">
          <summary>{{ $t('generation.detail.showThoughts') }}</summary>
          <pre class="stream-thoughts-pre">{{ stream.thoughtsContent }}</pre>
        </details>
      </div>

      <!-- Idle Slots -->
      <div
        v-for="n in idleSlotCount"
        :key="'idle-' + n"
        class="stream-card stream-idle"
      >
        <div class="idle-content">
          <LIcon size="20" color="grey">mdi-dots-horizontal</LIcon>
          <span>{{ $t('generation.detail.waitingForBatch') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, watch } from 'vue'
import { parseUserProviderModelId } from '@/utils/formatters'
import { parseGenerationOutput } from '@/utils/generationOutputParser'

const props = defineProps({
  streams: {
    type: Array,
    default: () => []
  },
  maxParallel: {
    type: Number,
    default: 1
  },
  isJobRunning: {
    type: Boolean,
    default: false
  },
  userProviderNames: {
    type: Object,
    default: () => ({})
  }
})

const parsedStreams = computed(() => props.streams.map((stream) => {
  const parsed = parseGenerationOutput(stream.content || '')
  return {
    ...stream,
    visibleContent: parsed.visibleContent,
    thoughtsContent: parsed.thoughtsContent
  }
}))

// Stream content refs for auto-scroll
const streamRefs = new Map()

function setStreamRef(outputId, el) {
  if (el) {
    streamRefs.set(outputId, el)
  } else {
    streamRefs.delete(outputId)
  }
}

// Auto-scroll each stream card when content changes
watch(() => props.streams.map(s => s.content), () => {
  nextTick(() => {
    for (const stream of props.streams) {
      const el = streamRefs.get(stream.outputId)
      if (el) {
        el.scrollTop = el.scrollHeight
      }
    }
  })
}, { deep: true })

const gridClass = computed(() => {
  const total = parsedStreams.value.length + idleSlotCount.value
  if (total <= 1) return 'grid-1'
  if (total <= 3) return 'grid-2'
  return 'grid-3'
})

const idleSlotCount = computed(() => {
  if (!props.isJobRunning) return 0
  return Math.max(0, props.maxParallel - parsedStreams.value.length)
})

function formatModelName(modelId) {
  const providerName = props.userProviderNames[modelId] || null
  const parsed = parseUserProviderModelId(modelId, providerName)
  if (parsed) return parsed.displayName
  return modelId
}

// Model color helpers — colors come from DB (single source of truth)
const normalizeHex = (value) => {
  if (!value || typeof value !== 'string') return null
  const v = value.trim()
  if (!/^#?[0-9A-Fa-f]{6}$/.test(v)) return null
  return v.startsWith('#') ? v : `#${v}`
}

const DEFAULT_MODEL_COLOR = '#6B7280'

const hexToRgb = (hex) => {
  const normalized = normalizeHex(hex)
  if (!normalized) return null
  const value = normalized.replace('#', '')
  return {
    r: parseInt(value.substring(0, 2), 16),
    g: parseInt(value.substring(2, 4), 16),
    b: parseInt(value.substring(4, 6), 16)
  }
}

const resolveColor = (modelName, explicitColor) => {
  const normalized = normalizeHex(explicitColor)
  if (normalized) return normalized
  return DEFAULT_MODEL_COLOR
}

function getModelTagStyle(color, modelName) {
  const resolved = resolveColor(modelName, color)
  const rgb = hexToRgb(resolved)
  if (!rgb) return {}
  return {
    background: `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.1)`,
    borderBottom: `2px solid rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.6)`,
    color: resolved
  }
}
</script>

<style scoped>
.live-streams {
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 8px 2px 8px 2px;
  padding: 12px;
  margin-bottom: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.04);
}

.streams-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.streams-title {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  font-weight: 600;
}

.streams-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Grid Layout */
.streams-grid {
  display: grid;
  gap: 8px;
}

.grid-1 { grid-template-columns: 1fr; }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }

@media (max-width: 900px) {
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .grid-2, .grid-3 { grid-template-columns: 1fr; }
}

/* Stream Card */
.stream-card {
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 6px 2px 6px 2px;
  padding: 8px 10px;
  background: rgba(var(--v-theme-surface), 1);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  min-height: 80px;
  display: flex;
  flex-direction: column;
}

.stream-card.stream-completed {
  border-color: #98d4bb;
  box-shadow: 0 0 8px rgba(152, 212, 187, 0.4);
  animation: flash-green 0.6s ease-out;
}

.stream-card.stream-failed {
  border-color: #e8a087;
  box-shadow: 0 0 8px rgba(232, 160, 135, 0.4);
  animation: flash-red 0.6s ease-out;
}

@keyframes flash-green {
  0% { background: rgba(152, 212, 187, 0.2); }
  100% { background: rgba(var(--v-theme-surface), 1); }
}

@keyframes flash-red {
  0% { background: rgba(232, 160, 135, 0.2); }
  100% { background: rgba(var(--v-theme-surface), 1); }
}

.stream-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.stream-tokens {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.stream-item-name {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stream-content {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.72rem;
  line-height: 1.4;
  color: rgba(var(--v-theme-on-surface), 0.8);
  max-height: 120px;
  overflow-y: auto;
  flex: 1;
  word-break: break-word;
  white-space: pre-wrap;
}

.stream-thoughts {
  margin-top: 8px;
  border-top: 1px dashed rgba(var(--v-theme-on-surface), 0.2);
  padding-top: 6px;
}

.stream-thoughts summary {
  cursor: pointer;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
  user-select: none;
}

.stream-thoughts-pre {
  margin: 6px 0 0 0;
  padding: 8px;
  border-radius: 6px 2px 6px 2px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  font-size: 0.7rem;
  line-height: 1.35;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 110px;
  overflow-y: auto;
}

.stream-waiting {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-style: italic;
}

.cursor {
  animation: blink 0.8s step-end infinite;
  color: #b0ca97;
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Idle Slot */
.stream-idle {
  border-style: dashed;
  display: flex;
  align-items: center;
  justify-content: center;
}

.idle-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
