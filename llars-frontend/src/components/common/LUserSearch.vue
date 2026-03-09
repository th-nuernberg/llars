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
      <template #item="{ props: itemProps, item }">
        <v-list-item v-bind="itemProps" class="user-suggestion">
          <template #prepend>
            <LAvatar :username="item.raw.username" :seed="item.raw.avatar_seed" :src="item.raw.avatar_url" size="sm" class="user-avatar-prepend" />
          </template>
          <v-list-item-title class="user-title">
            {{ getUserDisplayName(item.raw) }}
          </v-list-item-title>
          <v-list-item-subtitle class="user-subtitle">@{{ item.raw.username }}</v-list-item-subtitle>
        </v-list-item>
      </template>
      <template #selection="{ item }">
        <div class="d-flex align-center ga-2">
          <LAvatar :username="item.raw.username" :seed="item.raw.avatar_seed" :src="item.raw.avatar_url" size="xs" />
          <span>{{ getUserDisplayName(item.raw) }}</span>
        </div>
      </template>
      <template #no-data>
        <v-list-item v-if="!loading">
          <v-list-item-title class="text-medium-emphasis">
            {{ noResultsText }}
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
      <LIcon start size="small">mdi-account-plus</LIcon>
      {{ addButtonText }}
    </LBtn>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { getUserDisplayName } from '@/utils/userUtils'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const { t } = useI18n()

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
  searchEndpoint: { type: String, default: '/api/users/search' },
  noResultsText: { type: String, default: null },
})

const emit = defineEmits(['update:modelValue', 'select', 'add'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

const selectedUser = ref(props.modelValue)
const searchQuery = ref('')
const rawSuggestions = ref([])
const loading = ref(false)
const adding = ref(false)

const noResultsText = computed(() =>
  props.noResultsText || t('common.noUsersFound', 'Keine Nutzer gefunden')
)

// Reactive filtering: re-filters whenever excludeUsernames changes
const suggestions = computed(() => {
  if (props.excludeUsernames.length === 0) return rawSuggestions.value
  const excluded = new Set(props.excludeUsernames.map(u => u.toLowerCase()))
  return rawSuggestions.value.filter(u => !excluded.has(u.username.toLowerCase()))
})

let searchTimer = null

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function fetchUsers(query = '') {
  loading.value = true
  try {
    const params = { limit: 15 }
    if (query) params.q = query
    const res = await axios.get(`${API_BASE}${props.searchEndpoint}`, {
      headers: authHeaders(),
      params,
    })

    rawSuggestions.value = res.data.users || []
  } catch (e) {
    console.error('User search failed:', e)
    rawSuggestions.value = []
  } finally {
    loading.value = false
  }
}

// Load all users on mount
onMounted(() => fetchUsers())

watch(searchQuery, (query) => {
  if (searchTimer) clearTimeout(searchTimer)
  const q = String(query || '').trim()

  loading.value = true
  searchTimer = setTimeout(() => fetchUsers(q), 200)
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

function reset() {
  selectedUser.value = null
  searchQuery.value = ''
  rawSuggestions.value = []
  adding.value = false
  // Reload all users
  fetchUsers()
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

.user-suggestion {
  padding-top: 6px;
  padding-bottom: 6px;
}

.user-suggestion :deep(.v-list-item__prepend) {
  margin-right: 12px;
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
