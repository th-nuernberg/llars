<template>
  <div class="voice-call-panel d-flex flex-column align-center justify-center pa-6" style="min-height: 300px;">
    <v-icon size="64" color="primary" class="mb-4">mdi-phone-in-talk</v-icon>
    <h3 class="mb-2">{{ $t('messaging.call.voice') }}</h3>
    <p class="text-body-2 mb-4">{{ formattedDuration }}</p>

    <div class="d-flex gap-3">
      <v-btn
        icon
        :color="isMuted ? 'error' : 'default'"
        @click="$emit('toggleMute')"
      >
        <v-icon>{{ isMuted ? 'mdi-microphone-off' : 'mdi-microphone' }}</v-icon>
      </v-btn>
      <v-btn
        icon
        color="error"
        size="large"
        @click="$emit('endCall')"
      >
        <v-icon>mdi-phone-hangup</v-icon>
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  duration: { type: Number, default: 0 },
  isMuted: { type: Boolean, default: false },
})

defineEmits(['toggleMute', 'endCall'])

const formattedDuration = computed(() => {
  const m = Math.floor(props.duration / 60)
  const s = props.duration % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})
</script>
