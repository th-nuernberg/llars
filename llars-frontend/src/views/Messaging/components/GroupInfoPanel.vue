<template>
  <div class="group-info-panel">
    <div class="group-info-header">
      <LAvatar
        :seed="conversation?.avatar_seed || conversation?.name"
        :username="conversation?.name"
        size="lg"
        class="mb-2"
      />
      <h3>{{ conversation?.name }}</h3>
      <p v-if="conversation?.description" class="text-body-2 mt-1" style="opacity: 0.7">
        {{ conversation.description }}
      </p>
    </div>

    <v-divider class="mb-3" />

    <div class="d-flex align-center justify-space-between mb-2">
      <span class="text-subtitle-2">{{ $t('messaging.members') }} ({{ activeMembers.length }})</span>
      <LIconBtn
        v-if="isAdmin"
        icon="mdi-account-plus"
        size="x-small"
        :tooltip="$t('messaging.addMember')"
        @click="showAddMember = true"
      />
    </div>

    <div class="group-members-list">
      <div
        v-for="member in activeMembers"
        :key="member.username"
        class="group-member-item"
      >
        <div class="d-flex align-center gap-2">
          <LAvatar :username="member.username" :seed="member.username" size="xs" />
          <span class="text-body-2">{{ member.username }}</span>
          <LTag v-if="member.role === 'owner'" variant="info" size="sm">Owner</LTag>
          <LTag v-else-if="member.role === 'admin'" variant="secondary" size="sm">Admin</LTag>
        </div>
        <LIconBtn
          v-if="isAdmin && member.role !== 'owner' && member.username !== currentUsername"
          icon="mdi-close"
          size="x-small"
          @click="$emit('removeMember', member.username)"
        />
      </div>
    </div>

    <!-- Add Member Dialog -->
    <v-dialog v-model="showAddMember" max-width="400">
      <v-card>
        <v-card-title>{{ $t('messaging.addMember') }}</v-card-title>
        <v-card-text>
          <LUserSearch v-model="newMember" clearable />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showAddMember = false">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="primary" :disabled="!newMember" @click="addMember">
            {{ $t('messaging.add') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-divider class="my-3" />

    <LBtn
      variant="danger"
      size="small"
      prepend-icon="mdi-exit-run"
      block
      @click="$emit('leaveGroup')"
    >
      {{ $t('messaging.leaveGroup') }}
    </LBtn>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

const props = defineProps({
  conversation: { type: Object, default: null },
})

const emit = defineEmits(['addMember', 'removeMember', 'leaveGroup'])

const { username: currentUsername } = useAuth()

const showAddMember = ref(false)
const newMember = ref(null)

const activeMembers = computed(() => {
  return (props.conversation?.participants || []).filter((p) => p.is_active)
})

const isAdmin = computed(() => {
  const me = activeMembers.value.find((p) => p.username === currentUsername.value)
  return me?.role === 'owner' || me?.role === 'admin'
})

const addMember = () => {
  if (newMember.value) {
    emit('addMember', newMember.value)
    newMember.value = null
    showAddMember.value = false
  }
}
</script>
