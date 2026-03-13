<!--
  LShareDialog.vue — Global Share Dialog Component (#36)

  Reusable dialog for sharing resources with other users.
  Shows current members with avatars, allows adding/removing users.

  Pattern extracted from LatexCollab ShareDialog and Generation sharing UIs.
-->
<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :max-width="maxWidth">
    <v-card class="share-dialog">
      <!-- Header -->
      <v-card-title class="share-header">
        <LIcon class="mr-2" color="accent">mdi-share-variant</LIcon>
        <div>
          <div>{{ title }}</div>
          <div v-if="subtitle" class="text-caption text-medium-emphasis">{{ subtitle }}</div>
        </div>
        <v-spacer />
        <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" size="small" @click="$emit('update:modelValue', false)" />
      </v-card-title>

      <v-divider />

      <v-card-text class="share-body">
        <!-- Error Alert -->
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4" density="compact">
          {{ error }}
        </v-alert>

        <!-- Prepend Slot (e.g. Owner section) -->
        <slot name="prepend" />

        <!-- Members Section -->
        <div class="section-label">
          {{ $t('common.shareDialog.members') }}
          <span v-if="sharedUsers.length" class="member-count">{{ sharedUsers.length }}</span>
        </div>

        <v-skeleton-loader v-if="loading" type="list-item-avatar@3" />

        <div v-else-if="sharedUsers.length === 0" class="empty-members">
          <LIcon size="28" color="grey-lighten-1">mdi-account-group-outline</LIcon>
          <span>{{ $t('common.shareDialog.emptyMembers') }}</span>
        </div>

        <div v-else class="members-list">
          <div v-for="user in sharedUsers" :key="user.username" class="user-card">
            <LAvatar :username="user.username" :seed="user.avatar_seed" :src="user.avatar_url" size="sm" />
            <div class="user-info">
              <div class="user-name">{{ formatDisplayName(user.username) }}</div>
              <div v-if="user.created_at || user.added_at" class="user-meta">
                {{ formatRelativeDate(user.created_at || user.added_at) }}
              </div>
            </div>
            <v-btn
              v-if="canRemove"
              icon
              variant="text"
              size="x-small"
              color="error"
              :loading="removingUsername === user.username"
              :title="$t('common.shareDialog.removeMember')"
              @click="$emit('unshare', user.username)"
            >
              <LIcon size="18">mdi-close</LIcon>
            </v-btn>
          </div>
        </div>

        <!-- Add User Section -->
        <div class="section-label mt-4">{{ $t('common.shareDialog.addUser') }}</div>
        <LUserSearch
          ref="userSearchRef"
          v-model="selectedUser"
          :exclude-usernames="allExcludedUsernames"
          :placeholder="$t('common.shareDialog.searchPlaceholder')"
          :show-add-button="true"
          :add-button-text="$t('common.shareDialog.addButton')"
          :disabled="isSharing"
          @add="handleShare"
        />

        <!-- Append Slot (e.g. Pending Requests) -->
        <slot name="append" />
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { formatDisplayName, formatRelativeDate } from '@/utils/userUtils'

const props = defineProps({
  /** v-model for dialog visibility */
  modelValue: {
    type: Boolean,
    default: false
  },
  /** Dialog title */
  title: {
    type: String,
    required: true
  },
  /** Optional subtitle (e.g. resource name) */
  subtitle: {
    type: String,
    default: null
  },
  /** List of shared users: [{ username, avatar_seed?, avatar_url?, created_at? }] */
  sharedUsers: {
    type: Array,
    default: () => []
  },
  /** Loading state for member list */
  loading: {
    type: Boolean,
    default: false
  },
  /** Whether a share operation is in progress */
  isSharing: {
    type: Boolean,
    default: false
  },
  /** Username currently being removed (shows spinner on that row) */
  removingUsername: {
    type: String,
    default: ''
  },
  /** Whether remove buttons are shown */
  canRemove: {
    type: Boolean,
    default: true
  },
  /** Extra usernames to exclude from search (e.g. current user) */
  additionalExcludeUsernames: {
    type: Array,
    default: () => []
  },
  /** Error message to display */
  error: {
    type: String,
    default: ''
  },
  /** Dialog max width */
  maxWidth: {
    type: [Number, String],
    default: 480
  }
})

const emit = defineEmits(['update:modelValue', 'share', 'unshare'])

const selectedUser = ref(null)
const userSearchRef = ref(null)

/** Combine shared usernames + additional excludes for the search component */
const allExcludedUsernames = computed(() => {
  const shared = props.sharedUsers.map(u => u.username).filter(Boolean)
  return [...shared, ...props.additionalExcludeUsernames]
})

function handleShare(user) {
  emit('share', user)
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
