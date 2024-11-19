<!-- SocketDemo.vue -->
<template>
  <div class="container mx-auto p-4">
    <div class="mb-4">
      <h2 class="text-xl font-bold">Socket.IO Connection Status:</h2>
      <p :class="connectionStatusClass">{{ connectionStatus }}</p>
    </div>

    <div class="space-y-4">
      <div class="flex gap-2">
        <input
          v-model="message"
          type="text"
          class="border rounded p-2 flex-grow"
          placeholder="Enter message"
          @keyup.enter="sendMessage"
        />
        <button
          @click="sendMessage"
          class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Send
        </button>
      </div>

      <div class="border rounded p-4 max-h-96 overflow-y-auto">
        <h3 class="font-bold mb-2">Message History:</h3>
        <ul class="space-y-2">
          <li
            v-for="(msg, index) in messages"
            :key="index"
            class="p-2 rounded"
            :class="msg.type === 'sent' ? 'bg-blue-100' : 'bg-gray-100'"
          >
            <span class="font-bold">{{ msg.type === 'sent' ? 'You' : 'Server' }}:</span>
            {{ msg.content }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { io } from 'socket.io-client'

export default {
  setup() {
    const socket = ref(null)
    const connected = ref(false)
    const message = ref('')
    const messages = ref([])

    const connectionStatus = computed(() =>
      connected.value ? 'Connected' : 'Disconnected'
    )

    const connectionStatusClass = computed(() => ({
      'text-green-500': connected.value,
      'text-red-500': !connected.value
    }))

    const initializeSocket = () => {
      socket.value = io('http://localhost:80', {
        path: '/socket.io/',
        transports: ['websocket']
      })

      socket.value.on('connect', () => {
        connected.value = true
        addMessage('Connected to server', 'received')
      })

      socket.value.on('disconnect', () => {
        connected.value = false
        addMessage('Disconnected from server', 'received')
      })

      socket.value.on('message', (msg) => {
        addMessage(msg, 'received')
      })
    }

    const sendMessage = () => {
      if (!message.value.trim() || !socket.value?.connected) return

      socket.value.emit('message', message.value)
      addMessage(message.value, 'sent')
      message.value = ''
    }

    const addMessage = (content, type) => {
      messages.value.push({ content, type })
    }

    onMounted(() => {
      initializeSocket()
    })

    onUnmounted(() => {
      if (socket.value) {
        socket.value.disconnect()
      }
    })

    return {
      connected,
      connectionStatus,
      connectionStatusClass,
      message,
      messages,
      sendMessage
    }
  }
}
</script>
