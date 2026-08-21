<template>
  <v-menu
    v-model="isVisible"
    :style="{ position: 'fixed', left: position.x + 'px', top: position.y + 'px' }"
    location="bottom start"
    :close-on-content-click="true"
  >
    <v-list density="compact" class="py-1">
      <v-list-item @click="$emit('reply', message)" prepend-icon="mdi-reply">
        <v-list-item-title>{{ $t('messaging.reply') }}</v-list-item-title>
      </v-list-item>
      <v-list-item @click="$emit('copy', message)" prepend-icon="mdi-content-copy">
        <v-list-item-title>{{ $t('messaging.copy') }}</v-list-item-title>
      </v-list-item>
      <v-list-item
        v-if="canEdit"
        @click="$emit('edit', message)"
        prepend-icon="mdi-pencil"
      >
        <v-list-item-title>{{ $t('messaging.edit') }}</v-list-item-title>
      </v-list-item>
      <v-divider v-if="canDelete" class="my-1" />
      <v-list-item
        v-if="canDelete"
        @click="$emit('delete', message)"
        prepend-icon="mdi-delete"
        class="text-error"
      >
        <v-list-item-title>{{ $t('messaging.delete') }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  position: { type: Object, default: () => ({ x: 0, y: 0 }) },
  message: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue', 'reply', 'copy', 'edit', 'delete'])

const { tokenParsed } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || '')

const isVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const canEdit = computed(() => {
  return props.message?.sender_username === username.value && !props.message?.is_deleted
})

const canDelete = computed(() => {
  return props.message?.sender_username === username.value && !props.message?.is_deleted
})
</script>
