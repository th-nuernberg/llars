<template>
  <v-dialog v-model="isOpen" max-width="520" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-account-group</v-icon>
        {{ $t('messaging.newGroup') }}
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="groupName"
          :label="$t('messaging.groupName')"
          variant="outlined"
          density="compact"
          class="mb-3"
        />
        <v-textarea
          v-model="groupDescription"
          :label="$t('messaging.groupDescription')"
          variant="outlined"
          density="compact"
          rows="2"
          class="mb-3"
        />
        <LUserSearch
          v-model="selectedUser"
          :label="$t('messaging.addMembers')"
          clearable
          @update:model-value="addMember"
        />
        <div v-if="members.length > 0" class="mt-2 d-flex flex-wrap gap-1">
          <v-chip
            v-for="member in members"
            :key="member"
            closable
            size="small"
            @click:close="removeMember(member)"
          >
            {{ member }}
          </v-chip>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="close">{{ $t('common.cancel') }}</LBtn>
        <LBtn
          variant="primary"
          :disabled="!groupName.trim() || members.length === 0"
          @click="create"
        >
          {{ $t('messaging.createGroup') }}
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

const groupName = ref('')
const groupDescription = ref('')
const members = ref([])
const selectedUser = ref(null)

const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const addMember = (username) => {
  if (username && !members.value.includes(username)) {
    members.value.push(username)
  }
  selectedUser.value = null
}

const removeMember = (username) => {
  members.value = members.value.filter((m) => m !== username)
}

const close = () => {
  groupName.value = ''
  groupDescription.value = ''
  members.value = []
  selectedUser.value = null
  isOpen.value = false
}

const create = () => {
  if (groupName.value.trim() && members.value.length > 0) {
    emit('create', {
      name: groupName.value.trim(),
      description: groupDescription.value.trim() || null,
      members: members.value,
    })
    close()
  }
}
</script>
