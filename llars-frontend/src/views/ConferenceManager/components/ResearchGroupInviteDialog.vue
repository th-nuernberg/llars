<template>
  <v-dialog v-model="dialogVisible" max-width="500" persistent>
    <v-card class="invite-dialog">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-account-plus</v-icon>
        {{ t('researchGroup.members.invite') }}
      </v-card-title>

      <v-card-text>
        <LUserSearch
          v-model="selectedUser"
          :label="t('researchGroup.members.searchUser')"
          class="mb-4"
        />

        <v-select
          v-model="selectedRole"
          :items="roleOptions"
          :label="t('researchGroup.members.role')"
          variant="outlined"
          density="compact"
        />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="close">{{ t('common.cancel') }}</LBtn>
        <LBtn
          variant="primary"
          :disabled="!selectedUser"
          :loading="inviting"
          @click="invite"
        >
          {{ t('researchGroup.members.invite') }}
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from '../composables/useResearchGroups'

const props = defineProps({
  groupId: { type: [String, Number], required: true },
})

const emit = defineEmits(['invited', 'update:modelValue'])

const dialogVisible = defineModel({ type: Boolean, default: false })

const { t } = useI18n()
const { addMember } = useResearchGroups()

const selectedUser = ref(null)
const selectedRole = ref('member')
const inviting = ref(false)

const roleOptions = computed(() => [
  { title: t('researchGroup.members.roles.member'), value: 'member' },
  { title: t('researchGroup.members.roles.viewer'), value: 'viewer' },
  { title: t('researchGroup.members.roles.owner'), value: 'owner' },
])

function close() {
  dialogVisible.value = false
  selectedUser.value = null
  selectedRole.value = 'member'
}

async function invite() {
  if (!selectedUser.value) return
  inviting.value = true
  try {
    await addMember(props.groupId, selectedUser.value.id, selectedRole.value)
    emit('invited')
    close()
  } catch (err) {
    console.error('Failed to invite:', err)
  } finally {
    inviting.value = false
  }
}
</script>

<style scoped>
.invite-dialog {
  border-radius: 16px 4px 16px 4px;
}
</style>
