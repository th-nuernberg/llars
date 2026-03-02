/**
 * Live transcription composable.
 * Listens for transcript_update events and accumulates the full transcript.
 */
import { ref, readonly, onUnmounted } from 'vue'
import socketService from '@/services/socketService'

export function useTranscription() {
  const chunks = ref([])
  const isTranscribing = ref(false)

  const setupListeners = () => {
    const socket = socketService.getSocket()
    if (!socket) return

    socket.on('messaging:transcript_update', (data) => {
      isTranscribing.value = true
      chunks.value.push({
        speaker: data.speaker,
        text: data.text,
        timestamp: data.timestamp,
        callId: data.call_id,
      })
    })
  }

  const cleanupListeners = () => {
    const socket = socketService.getSocket()
    if (socket) {
      socket.off('messaging:transcript_update')
    }
  }

  const clearTranscript = () => {
    chunks.value = []
    isTranscribing.value = false
  }

  onUnmounted(() => {
    cleanupListeners()
  })

  return {
    chunks: readonly(chunks),
    isTranscribing: readonly(isTranscribing),
    setupListeners,
    cleanupListeners,
    clearTranscript,
  }
}
