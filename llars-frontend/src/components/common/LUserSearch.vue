<template>
  <div class="l-user-search">
    <v-autocomplete
      v-model="selectedUser"
      v-model:search="searchQuery"
      :items="suggestions"
      :loading="loading"
      item-title="username"
      item-value="username"
      return-object
      :placeholder="placeholder"
      :label="label"
      variant="outlined"
      :density="density"
      hide-details
      clearable
      no-filter
      :disabled="disabled"
    >
      <template #item="{ props, item }">
        <v-list-item v-bind="props" class="user-suggestion">
          <template #prepend>
            <img class="user-avatar user-avatar--list" :src="getAvatarUrl(item.raw)" alt="" />
          </template>
          <v-list-item-title class="user-title">
            {{ formatDisplayName(item.raw.username) }}
          </v-list-item-title>
          <v-list-item-subtitle class="user-subtitle">@{{ item.raw.username }}</v-list-item-subtitle>
        </v-list-item>
      </template>
      <template #selection="{ item }">
        <div class="d-flex align-center ga-2">
          <img class="user-avatar user-avatar--selection small" :src="getAvatarUrl(item.raw)" alt="" />
          <span>{{ formatDisplayName(item.raw.username) }}</span>
        </div>
      </template>
      <template #no-data>
        <v-list-item v-if="searchQuery && searchQuery.length >= 2 && !loading">
          <v-list-item-title class="text-medium-emphasis">
            Keine Nutzer gefunden
          </v-list-item-title>
        </v-list-item>
        <v-list-item v-else-if="!loading">
          <v-list-item-title class="text-medium-emphasis">
            Mindestens 2 Zeichen eingeben
          </v-list-item-title>
        </v-list-item>
      </template>
    </v-autocomplete>

    <LBtn
      v-if="showAddButton"
      variant="primary"
      :size="buttonSize"
      :loading="adding"
      :disabled="!selectedUser || adding || disabled"
      :title="addButtonText"
      class="mt-2"
      @click="handleAdd"
    >
      <v-icon start size="small">mdi-account-plus</v-icon>
      {{ addButtonText }}
    </LBtn>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'
import { getAvatarUrl, formatDisplayName } from '@/utils/userUtils'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const props = defineProps({
  modelValue: { type: Object, default: null },
  placeholder: { type: String, default: 'Nutzernamen eingeben...' },
  label: { type: String, default: null },
  density: { type: String, default: 'compact' },
  disabled: { type: Boolean, default: false },
  showAddButton: { type: Boolean, default: false },
  addButtonText: { type: String, default: 'Hinzufügen' },
  buttonSize: { type: String, default: 'small' },
  excludeUsernames: { type: Array, default: () => [] },
  searchEndpoint: { type: String, default: '/api/users/search' }
})

const emit = defineEmits(['update:modelValue', 'select', 'add'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const selectedUser = ref(props.modelValue)
const searchQuery = ref('')
const suggestions = ref([])
const loading = ref(false)
const adding = ref(false)

let searchTimer = null

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

watch(searchQuery, (query) => {
  if (searchTimer) clearTimeout(searchTimer)
  const q = String(query || '').trim()

  if (q.length < 2) {
    suggestions.value = []
    loading.value = false
    return
  }

  loading.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await axios.get(`${API_BASE}${props.searchEndpoint}`, {
        headers: authHeaders(),
        params: { q, limit: 10 }
      })

      let users = res.data.users || []

      // Filter out excluded usernames
      if (props.excludeUsernames.length > 0) {
        const excluded = new Set(props.excludeUsernames.map(u => u.toLowerCase()))
        users = users.filter(u => !excluded.has(u.username.toLowerCase()))
      }

      suggestions.value = users
    } catch (e) {
      console.error('User search failed:', e)
      suggestions.value = []
    } finally {
      loading.value = false
    }
  }, 250)
})

watch(selectedUser, (user) => {
  emit('update:modelValue', user)
  if (user) {
    emit('select', user)
  }
})

watch(() => props.modelValue, (val) => {
  selectedUser.value = val
})

function handleAdd() {
  if (!selectedUser.value) return
  adding.value = true
  emit('add', selectedUser.value)
}

// Expose method to reset after external add completes
function reset() {
  selectedUser.value = null
  searchQuery.value = ''
  suggestions.value = []
  adding.value = false
}

function setAdding(val) {
  adding.value = val
}

defineExpose({ reset, setAdding })
</script>

<style scoped>
.l-user-search {
  width: 100%;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px 3px 8px 3px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.user-avatar.small {
  width: 24px;
  height: 24px;
  border-radius: 6px 2px 6px 2px;
}

.user-avatar--list {
  margin-left: -4px;
  margin-right: 12px;
}

.user-avatar--selection {
  margin-right: 0;
}

.user-suggestion {
  padding-top: 8px;
  padding-bottom: 8px;
}

.user-title {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.user-subtitle {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
