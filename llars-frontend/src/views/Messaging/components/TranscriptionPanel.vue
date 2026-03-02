<template>
  <div v-if="hasPermission('feature:communication:transcription')" class="transcription-panel">
    <div class="transcription-header">
      <div class="d-flex align-center gap-2">
        <v-icon size="18" color="accent">mdi-microphone-message</v-icon>
        <span class="text-subtitle-2 font-weight-bold">{{ $t('messaging.call.transcription') }}</span>
      </div>
      <LIconBtn
        icon="mdi-close"
        size="x-small"
        :tooltip="$t('messaging.close')"
        @click="$emit('close')"
      />
    </div>

    <div ref="transcriptContainer" class="transcription-body">
      <div v-if="chunks.length === 0" class="transcription-empty">
        <v-icon size="32" class="mb-2" style="opacity: 0.4">mdi-text-box-outline</v-icon>
        <span class="text-body-2" style="opacity: 0.5">{{ $t('messaging.call.noTranscript') }}</span>
      </div>

      <div
        v-for="(chunk, idx) in chunks"
        :key="idx"
        class="transcript-chunk"
      >
        <span class="transcript-speaker">{{ chunk.speaker }}</span>
        <span class="transcript-text">{{ chunk.text }}</span>
      </div>
    </div>

    <div v-if="isTranscribing" class="transcription-status">
      <v-icon size="12" color="error" class="transcription-pulse">mdi-circle</v-icon>
      <span class="text-caption">{{ $t('messaging.call.liveTranscription') }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { usePermissions } from '@/composables/usePermissions'

const { hasPermission } = usePermissions()

const props = defineProps({
  chunks: { type: Array, default: () => [] },
  isTranscribing: { type: Boolean, default: false },
})

defineEmits(['close'])

const transcriptContainer = ref(null)

// Auto-scroll to bottom when new chunks arrive
watch(() => props.chunks.length, async () => {
  await nextTick()
  if (transcriptContainer.value) {
    transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.transcription-panel {
  width: 300px;
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.transcription-header {
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.transcription-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.transcription-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.transcript-chunk {
  font-size: 0.85rem;
  line-height: 1.4;
}

.transcript-speaker {
  font-weight: 600;
  font-size: 0.78rem;
  margin-right: 6px;
  opacity: 0.75;
}

.transcript-text {
  color: inherit;
}

.transcription-status {
  padding: 6px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  font-size: 0.78rem;
  opacity: 0.7;
}

.transcription-pulse {
  animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@media (max-width: 768px) {
  .transcription-panel {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    z-index: 11;
    background: rgb(var(--v-theme-surface));
  }
}
</style>
