<template>
  <div v-if="typingUsersList.length > 0" class="typing-indicator">
    {{ typingText }}
    <span class="typing-dots">
      <span></span>
      <span></span>
      <span></span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  typingUsers: { type: Set, default: () => new Set() },
})

const { t } = useI18n()

const typingUsersList = computed(() => Array.from(props.typingUsers))

const typingText = computed(() => {
  const users = typingUsersList.value
  if (users.length === 0) return ''
  if (users.length === 1) return `${users[0]} ${t('messaging.isTyping')}`
  if (users.length === 2) return `${users[0]} & ${users[1]} ${t('messaging.areTyping')}`
  return t('messaging.severalTyping')
})
</script>
