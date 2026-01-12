<!--
  ShareDialog.vue

  Workspace sharing/members management dialog.
-->
<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="480">
    <v-card class="share-dialog">
      <v-card-title class="share-header">
        <LIcon class="mr-2" color="primary">mdi-account-multiple-plus</LIcon>
        <div>
          <div>{{ $t('latexCollab.share.title') }}</div>
          <div class="text-caption text-medium-emphasis">{{ workspaceName }}</div>
        </div>
        <v-spacer />
        <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" size="small" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="share-body">
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" density="compact">
          {{ error }}
        </v-alert>

        <!-- Owner Section -->
        <div class="section-label">{{ $t('latexCollab.share.ownerLabel') }}</div>
        <div class="user-card owner-card">
          <img class="user-avatar" :src="getAvatarUrl(ownerInfo)" alt="" />
          <div class="user-info">
            <div class="user-name">{{ formatDisplayName(ownerInfo.username) }}</div>
            <div class="user-meta">@{{ ownerInfo.username }}</div>
          </div>
          <LTag variant="primary" size="small">{{ $t('latexCollab.share.ownerTag') }}</LTag>
        </div>

        <!-- Search Section -->
        <div class="section-label mt-4">{{ $t('latexCollab.share.inviteLabel') }}</div>
        <LUserSearch
          ref="userSearchRef"
          v-model="selectedUser"
          :exclude-usernames="excludedUsernames"
          :show-add-button="true"
          :add-button-text="$t('latexCollab.share.addButton')"
          @add="handleInvite"
        />

        <!-- Members Section -->
        <div class="section-label mt-4">
          {{ $t('latexCollab.share.members') }}
          <span v-if="members.length" class="member-count">{{ members.length }}</span>
        </div>

        <v-skeleton-loader v-if="loading" type="list-item-avatar@3" />

        <div v-else-if="members.length === 0" class="empty-members">
          <LIcon size="28" color="grey-lighten-1">mdi-account-group-outline</LIcon>
          <span>{{ $t('latexCollab.share.emptyMembers') }}</span>
        </div>

        <div v-else class="members-list">
          <div v-for="m in members" :key="m.username" class="user-card">
            <img class="user-avatar" :src="getAvatarUrl(m)" alt="" />
            <div class="user-info">
              <div class="user-name">{{ formatDisplayName(m.username) }}</div>
              <div class="user-meta">{{ formatRelativeDate(m.added_at) }}</div>
            </div>
            <v-btn
              v-if="canRemove"
              icon
              variant="text"
              size="x-small"
              color="error"
              :loading="removingUsername === m.username"
              :title="$t('latexCollab.share.removeMember')"
              @click="$emit('remove', m.username)"
            >
              <LIcon size="18">mdi-close</LIcon>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { getAvatarUrl, formatDisplayName, formatRelativeDate } from '@/utils/userUtils'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  workspaceName: {
    type: String,
    default: ''
  },
  ownerInfo: {
    type: Object,
    default: () => ({ username: '', avatar_url: null, avatar_seed: null, collab_color: null })
  },
  members: {
    type: Array,
    default: () => []
  },
  excludedUsernames: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  removingUsername: {
    type: String,
    default: ''
  },
  canRemove: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'invite', 'remove'])

const selectedUser = ref(null)
const userSearchRef = ref(null)

function handleInvite(user) {
  emit('invite', user)
  selectedUser.value = null
  userSearchRef.value?.reset?.()
}
</script>

<style scoped>
.share-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
}

.share-body {
  padding: 20px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-count {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 10px 4px 10px 4px;
  margin-bottom: 8px;
}

.owner-card {
  background: rgba(var(--v-theme-primary), 0.08);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-meta {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.empty-members {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 13px;
}

.members-list {
  max-height: 240px;
  overflow-y: auto;
}
</style>
