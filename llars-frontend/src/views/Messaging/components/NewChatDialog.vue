<template>
  <v-dialog v-model="isOpen" max-width="480" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-message-plus</v-icon>
        {{ $t('messaging.newChat') }}
      </v-card-title>
      <v-card-text>
        <LUserSearch
          v-model="selectedUser"
          :label="$t('messaging.selectUser')"
          clearable
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="close">{{ $t('common.cancel') }}</LBtn>
        <LBtn variant="primary" :disabled="!selectedUser" @click="create">
          {{ $t('messaging.startChat') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'create'])

const selectedUser = ref(null)

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const close = () => {
  selectedUser.value = null
  isOpen.value = false
}

const create = () => {
  if (selectedUser.value) {
    emit('create', selectedUser.value)
    close()
  }
}
</script>
