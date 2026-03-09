<template>
  <div class="emoji-picker-wrapper" ref="wrapperRef">
    <LIconBtn
      icon="mdi-emoticon-plus-outline"
      size="x-small"
      :tooltip="$t('messaging.moreReactions')"
      @click.stop="open = !open"
    />
    <Transition name="fade">
      <div v-if="open" class="emoji-picker-popover" :class="popoverClass">
        <div class="emoji-picker-grid">
          <span
            v-for="emoji in allEmojis"
            :key="emoji"
            class="emoji-picker-item"
            @click.stop="selectEmoji(emoji)"
          >
            {{ emoji }}
          </span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  popoverClass: { type: String, default: '' },
})

const emit = defineEmits(['select'])

const open = ref(false)
const wrapperRef = ref(null)

const allEmojis = [
  '👍', '👎', '❤️', '😄', '😂', '😮', '😢', '😡',
  '🎉', '🙏', '🤔', '👀', '🔥', '💯', '✅', '❌',
  '⭐', '💪', '🤝', '👏', '🚀', '💡', '📌', '🎯',
]

const selectEmoji = (emoji) => {
  emit('select', emoji)
  open.value = false
}

const onClickOutside = (e) => {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>
