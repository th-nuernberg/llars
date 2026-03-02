<template>
  <div class="video-call-panel" style="position: relative; min-height: 400px; background: #111;">
    <!-- Remote video tracks -->
    <div
      v-for="(track, idx) in remoteTracks"
      :key="idx"
      class="remote-video-container"
      :style="{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }"
    >
      <video
        v-if="track.kind === 'video'"
        :ref="(el) => attachTrack(el, track.track)"
        autoplay
        playsinline
        style="width: 100%; height: 100%; object-fit: cover;"
      />
      <audio
        v-else
        :ref="(el) => attachTrack(el, track.track)"
        autoplay
      />
      <div class="remote-label pa-1 px-2" style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.6); color: white; border-radius: 4px; font-size: 0.8rem;">
        {{ track.participant }}
      </div>
    </div>

    <!-- Local video (picture-in-picture) -->
    <div
      v-if="localVideoTrack"
      style="position: absolute; bottom: 80px; right: 16px; width: 160px; height: 120px; border-radius: 8px; overflow: hidden; border: 2px solid rgba(255,255,255,0.3);"
    >
      <video
        :ref="(el) => attachTrack(el, localVideoTrack)"
        autoplay
        playsinline
        muted
        style="width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1);"
      />
    </div>

    <!-- Controls -->
    <div class="d-flex justify-center gap-3" style="position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);">
      <v-btn
        icon
        :color="isMuted ? 'error' : 'default'"
        @click="$emit('toggleMute')"
      >
        <v-icon color="white">{{ isMuted ? 'mdi-microphone-off' : 'mdi-microphone' }}</v-icon>
      </v-btn>
      <v-btn
        icon
        :color="isCameraOff ? 'error' : 'default'"
        @click="$emit('toggleCamera')"
      >
        <v-icon color="white">{{ isCameraOff ? 'mdi-video-off' : 'mdi-video' }}</v-icon>
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

    <!-- Duration -->
    <div style="position: absolute; top: 12px; left: 50%; transform: translateX(-50%); color: white; font-size: 0.9rem; background: rgba(0,0,0,0.5); padding: 2px 12px; border-radius: 12px;">
      {{ formattedDuration }}
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick } from 'vue'

const props = defineProps({
  localTracks: { type: Array, default: () => [] },
  remoteTracks: { type: Array, default: () => [] },
  duration: { type: Number, default: 0 },
  isMuted: { type: Boolean, default: false },
  isCameraOff: { type: Boolean, default: false },
})

defineEmits(['toggleMute', 'toggleCamera', 'endCall'])

const localVideoTrack = computed(() => {
  const videoTrack = props.localTracks.find((t) => t.kind === 'video')
  return videoTrack || null
})

const formattedDuration = computed(() => {
  const m = Math.floor(props.duration / 60)
  const s = props.duration % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const attachTrack = (el, track) => {
  if (el && track?.attach) {
    nextTick(() => track.attach(el))
  }
}
</script>
