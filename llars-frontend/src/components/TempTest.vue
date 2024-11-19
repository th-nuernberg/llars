<template>
  <div class="container mx-auto p-4">
    <div class="mb-4">
      <h2 class="text-xl font-bold">Chat with AI Assistant</h2>
      <p :class="connectionStatusClass">{{ connectionStatus }}</p>
    </div>

    <div class="space-y-4">
      <div class="flex gap-2">
        <input
          v-model="message"
          type="text"
          class="border rounded p-2 flex-grow"
          placeholder="Ask me anything..."
          @keyup.enter="sendChatMessage"
          :disabled="isProcessing"
        />
        <button
          @click="sendChatMessage"
          class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          :disabled="isProcessing"
        >
          {{ isProcessing ? 'Processing...' : 'Send' }}
        </button>
      </div>

      <div class="border rounded p-4 max-h-96 overflow-y-auto" ref="chatContainer">
        <ul class="space-y-4">
          <li
            v-for="(msg, index) in messages"
            :key="index"
            class="p-3 rounded"
            :class="getMessageClass(msg)"
          >
            <div class="flex items-start gap-2">
              <span class="font-bold min-w-[50px]">
                {{ msg.type === 'sent' ? 'You:' : 'AI:' }}
              </span>
              <div class="flex-grow">
                <p class="whitespace-pre-wrap">{{ msg.content }}</p>
                <div v-if="msg.streaming" class="mt-1">
                  <span class="animate-pulse">▪▪▪</span>
                </div>
              </div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { io } from 'socket.io-client'

export default {
  setup() {
    const socket = ref(null)
    const connected = ref(false)
    const message = ref('')
    const messages = ref([])
    const isProcessing = ref(false)
    const chatContainer = ref(null)

    const connectionStatus = computed(() =>
      connected.value ? 'Connected' : 'Disconnected'
    )

    const connectionStatusClass = computed(() => ({
      'text-green-500': connected.value,
      'text-red-500': !connected.value
    }))

    const getMessageClass = (msg) => ({
      'bg-blue-100': msg.type === 'sent',
      'bg-gray-100': msg.type === 'received',
      'opacity-70': msg.streaming
    })

    const scrollToBottom = async () => {
      await nextTick()
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }

    watch(messages, () => {
      scrollToBottom()
    }, { deep: true })

    const initializeSocket = () => {
      socket.value = io('http://localhost:80', {
        path: '/socket.io/',
        transports: ['websocket']
      })

      socket.value.on('connect', () => {
        connected.value = true
      })

      socket.value.on('disconnect', () => {
        connected.value = false
      })

      socket.value.on('welcome', (msg) => {
        addMessage(msg.message, 'received')
      })

      socket.value.on('chat_response', (data) => {
        if (!data.complete) {
          if (messages.value.length > 0 && messages.value[messages.value.length - 1].streaming) {
            messages.value[messages.value.length - 1].content += data.content
          } else {
            addMessage(data.content, 'received', true)
          }
        } else {
          const lastMessage = messages.value[messages.value.length - 1]
          if (lastMessage && lastMessage.streaming) {
            lastMessage.streaming = false
          }
          isProcessing.value = false
        }
      })
    }

  const sendChatMessage = () => {
    if (!message.value.trim() || !socket.value?.connected || isProcessing.value) return

    if (message.value.toLowerCase().includes('mock chat')) {
      socket.value.emit('mock_chat', { message: message.value })
    } else {
      socket.value.emit('chat_message', { message: message.value })
    }

    addMessage(message.value, 'sent')
    isProcessing.value = true
    message.value = ''
  }

    const addMessage = (content, type, streaming = false) => {
      messages.value.push({ content, type, streaming })
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
      isProcessing,
      chatContainer,
      sendChatMessage,
      getMessageClass
    }
  }
}
</script>
