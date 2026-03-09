/**
 * Call manager composable.
 * Handles LiveKit room connection, track management, and call lifecycle.
 */
import { ref, readonly, computed, onUnmounted } from 'vue'
import socketService from '@/services/socketService'
import { useAuth } from '@/composables/useAuth'

export function useCallManager() {
  const { tokenParsed } = useAuth()
  const username = computed(() => tokenParsed.value?.preferred_username || '')

  const isInCall = ref(false)
  const callId = ref(null)
  const callType = ref(null)
  const callDuration = ref(0)
  const incomingCall = ref(null)
  const livekitRoom = ref(null)
  const localTracks = ref([])
  const remoteTracks = ref([])
  const isMuted = ref(false)
  const isCameraOff = ref(false)

  let durationTimer = null

  // ── Initiate Call ───────────────────────────────────────────────
  const initiateCall = (conversationId, type = 'voice') => {
    const socket = socketService.getSocket()
    if (!socket?.connected) return

    socket.emit('messaging:call_initiate', {
      conversation_id: conversationId,
      call_type: type,
      username: username.value,
    })
  }

  // ── Join LiveKit Room ───────────────────────────────────────────
  const joinRoom = async (token, livekitUrl, roomName) => {
    try {
      // Dynamic import — uses variable to bypass Vite static analysis
      // livekit-client is optional; calls work end-to-end once the package is installed
      const pkg = 'livekit-client'
      const { Room, RoomEvent, Track } = await import(/* @vite-ignore */ pkg)

      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      })

      room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
        remoteTracks.value = [...remoteTracks.value, {
          track,
          participant: participant.identity,
          kind: track.kind,
        }]
      })

      room.on(RoomEvent.TrackUnsubscribed, (track) => {
        remoteTracks.value = remoteTracks.value.filter((t) => t.track !== track)
      })

      room.on(RoomEvent.Disconnected, () => {
        cleanup()
      })

      await room.connect(livekitUrl, token)

      // Publish local tracks
      const tracks = await room.localParticipant.enableCameraAndMicrophone()
      localTracks.value = tracks || []

      livekitRoom.value = room
      isInCall.value = true
      startDurationTimer()

    } catch (err) {
      console.error('[Call] Failed to join LiveKit room:', err)
      cleanup()
    }
  }

  // ── Accept Incoming Call ────────────────────────────────────────
  const acceptCall = async () => {
    if (!incomingCall.value) return

    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:call_accept', {
        call_id: incomingCall.value.call_id,
        username: username.value,
      })
    }

    callId.value = incomingCall.value.call_id
    callType.value = incomingCall.value.call_type

    if (incomingCall.value.token && incomingCall.value.livekit_url) {
      await joinRoom(
        incomingCall.value.token,
        incomingCall.value.livekit_url,
        incomingCall.value.room_name
      )
    }

    incomingCall.value = null
  }

  // ── Decline Incoming Call ───────────────────────────────────────
  const declineCall = () => {
    if (!incomingCall.value) return

    const socket = socketService.getSocket()
    if (socket?.connected) {
      socket.emit('messaging:call_decline', {
        call_id: incomingCall.value.call_id,
        username: username.value,
      })
    }

    incomingCall.value = null
  }

  // ── End Call ────────────────────────────────────────────────────
  const endCall = (conversationId) => {
    const socket = socketService.getSocket()
    if (socket?.connected && callId.value) {
      socket.emit('messaging:call_end', {
        call_id: callId.value,
        username: username.value,
        conversation_id: conversationId,
      })
    }
    cleanup()
  }

  // ── Toggle Mute ─────────────────────────────────────────────────
  const toggleMute = () => {
    if (!livekitRoom.value) return
    const enabled = livekitRoom.value.localParticipant.isMicrophoneEnabled
    livekitRoom.value.localParticipant.setMicrophoneEnabled(!enabled)
    isMuted.value = !isMuted.value
  }

  // ── Toggle Camera ───────────────────────────────────────────────
  const toggleCamera = () => {
    if (!livekitRoom.value) return
    const enabled = livekitRoom.value.localParticipant.isCameraEnabled
    livekitRoom.value.localParticipant.setCameraEnabled(!enabled)
    isCameraOff.value = !isCameraOff.value
  }

  // ── Duration Timer ──────────────────────────────────────────────
  const startDurationTimer = () => {
    callDuration.value = 0
    durationTimer = setInterval(() => {
      callDuration.value++
    }, 1000)
  }

  // ── Cleanup ─────────────────────────────────────────────────────
  const cleanup = () => {
    if (livekitRoom.value) {
      livekitRoom.value.disconnect()
      livekitRoom.value = null
    }
    localTracks.value = []
    remoteTracks.value = []
    isInCall.value = false
    callId.value = null
    callType.value = null
    isMuted.value = false
    isCameraOff.value = false
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }
  }

  // ── Socket Listeners ────────────────────────────────────────────
  const setupCallListeners = () => {
    const socket = socketService.getSocket()
    if (!socket) return

    socket.on('messaging:call_token', async (data) => {
      callId.value = data.call_id
      if (data.token && data.livekit_url) {
        await joinRoom(data.token, data.livekit_url, data.room_name)
      }
    })

    socket.on('messaging:call_incoming', (data) => {
      incomingCall.value = data
    })

    socket.on('messaging:call_accepted', (data) => {
      // Another participant accepted
    })

    socket.on('messaging:call_ended', () => {
      cleanup()
    })
  }

  const cleanupCallListeners = () => {
    const socket = socketService.getSocket()
    if (socket) {
      socket.off('messaging:call_token')
      socket.off('messaging:call_incoming')
      socket.off('messaging:call_accepted')
      socket.off('messaging:call_ended')
    }
  }

  onUnmounted(() => {
    cleanup()
    cleanupCallListeners()
  })

  return {
    isInCall: readonly(isInCall),
    callId: readonly(callId),
    callType: readonly(callType),
    callDuration: readonly(callDuration),
    incomingCall: readonly(incomingCall),
    localTracks: readonly(localTracks),
    remoteTracks: readonly(remoteTracks),
    isMuted: readonly(isMuted),
    isCameraOff: readonly(isCameraOff),
    initiateCall,
    acceptCall,
    declineCall,
    endCall,
    toggleMute,
    toggleCamera,
    setupCallListeners,
    cleanupCallListeners,
  }
}
