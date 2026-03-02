<template>
  <div class="admin-communication-section">
    <!-- Card 1: Global Settings -->
    <LCard :title="$t('admin.communication.globalSettings')" icon="mdi-message-cog" class="mb-4">
      <div class="d-flex align-center mb-3">
        <v-switch
          v-model="globalEnabled"
          :label="$t('admin.communication.masterToggle')"
          color="primary"
          hide-details
          :loading="savingToggle"
          @update:model-value="toggleGlobal"
        />
      </div>
      <v-alert
        :type="globalEnabled ? 'success' : 'warning'"
        variant="tonal"
        density="compact"
      >
        <template #prepend>
          <v-icon>{{ globalEnabled ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
        </template>
        {{ globalEnabled ? $t('admin.communication.statusEnabled') : $t('admin.communication.statusDisabled') }}
      </v-alert>
    </LCard>

    <!-- Card 2: User Access Management -->
    <LCard :title="$t('admin.communication.userAccess')" icon="mdi-account-key" class="mb-4">
      <template #actions>
        <LBtn variant="primary" size="small" prepend-icon="mdi-check-all" @click="enableAll" :loading="bulkLoading">
          {{ $t('admin.communication.enableAll') }}
        </LBtn>
        <LBtn variant="cancel" size="small" prepend-icon="mdi-close-circle" class="ml-2" @click="disableAll" :loading="bulkLoading">
          {{ $t('admin.communication.disableAll') }}
        </LBtn>
      </template>

      <v-text-field
        v-model="userSearch"
        :placeholder="$t('admin.communication.searchUser')"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="mb-3"
      />

      <v-data-table
        :headers="tableHeaders"
        :items="filteredUsers"
        :loading="usersLoading"
        density="compact"
        :items-per-page="15"
        class="comm-users-table"
      >
        <template #item.username="{ item }">
          <div class="d-flex align-center gap-3">
            <LAvatar :username="item.username" :seed="item.avatar_seed" :src="item.avatar_url" size="xs" />
            <span>{{ item.username }}</span>
          </div>
        </template>
        <template #item.all="{ item }">
          <v-switch
            :model-value="allEnabled(item)"
            color="primary"
            density="compact"
            hide-details
            @update:model-value="toggleAll(item, $event)"
          />
        </template>
        <template #item.access="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:access']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:access', $event)"
          />
        </template>
        <template #item.chat="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:chat']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:chat', $event)"
          />
        </template>
        <template #item.voice="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:voice']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:voice', $event)"
          />
        </template>
        <template #item.video="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:video']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:video', $event)"
          />
        </template>
        <template #item.transcription="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:transcription']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:transcription', $event)"
          />
        </template>
        <template #item.ai="{ item }">
          <v-checkbox-btn
            :model-value="item.permissions['feature:communication:ai']"
            color="primary"
            density="compact"
            @update:model-value="togglePerm(item, 'feature:communication:ai', $event)"
          />
        </template>
      </v-data-table>
    </LCard>

    <!-- Card 3: Communication Statistics -->
    <LCard :title="$t('admin.communication.statistics')" icon="mdi-chart-line" class="mb-4">
      <template v-if="stats">
        <v-row dense class="mb-4">
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_conversations }}</div>
              <div class="stat-label">{{ $t('admin.communication.stats.conversations') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_messages }}</div>
              <div class="stat-label">{{ $t('admin.communication.stats.messages') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_calls }}</div>
              <div class="stat-label">{{ $t('admin.communication.stats.calls') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-primary">{{ stats.active_users }}</div>
              <div class="stat-label">{{ $t('admin.communication.stats.activeUsers') }}</div>
            </div>
          </v-col>
        </v-row>

        <!-- Per-User Stats Table -->
        <div v-if="userStats.length > 0" class="mb-3">
          <div class="text-subtitle-2 font-weight-bold mb-2">{{ $t('admin.communication.stats.perUser') }}</div>
          <v-data-table
            :headers="statsHeaders"
            :items="userStats"
            density="compact"
            :items-per-page="10"
          >
            <template #item.username="{ item }">
              <div class="d-flex align-center gap-2">
                <LAvatar :username="item.username" :seed="item.avatar_seed" :src="item.avatar_url" size="xs" />
                <span>{{ item.username }}</span>
              </div>
            </template>
            <template #item.last_active="{ item }">
              {{ item.last_active ? new Date(item.last_active).toLocaleString() : '–' }}
            </template>
          </v-data-table>
        </div>

        <v-alert type="info" variant="tonal" density="compact" class="mt-2">
          <template #prepend><v-icon>mdi-shield-lock</v-icon></template>
          {{ $t('admin.communication.stats.privacyNote') }}
        </v-alert>
      </template>
      <v-skeleton-loader v-else type="article" />
    </LCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbar } from '@/composables/useSnackbar'
import { usePermissions } from '@/composables/usePermissions'
import { useCommunicationAdmin } from '@/composables/useCommunicationAdmin'
import axios from 'axios'

const { t } = useI18n()
const { showSuccess, showError } = useSnackbar()
const { fetchPermissions } = usePermissions()
const {
  communicationEnabled,
  refreshCommunicationStatus,
  fetchUsers,
  setUserPermissions,
  bulkSetPermissions,
  fetchStats,
} = useCommunicationAdmin()

/** After any permission change, re-fetch own permissions so App bar reacts immediately. */
async function syncPermissions() {
  try { await fetchPermissions() } catch { /* ignore */ }
}

const COMM_PERMS = [
  'feature:communication:access',
  'feature:communication:chat',
  'feature:communication:voice',
  'feature:communication:video',
  'feature:communication:transcription',
  'feature:communication:ai',
]

// Global toggle
const globalEnabled = ref(false)
const savingToggle = ref(false)

async function toggleGlobal(value) {
  savingToggle.value = true
  try {
    await axios.patch('/api/admin/system/settings', { communication_enabled: value })
    await refreshCommunicationStatus()
    showSuccess(t('admin.communication.toggleSaved'))
  } catch {
    globalEnabled.value = !value
    showError(t('admin.communication.toggleError'))
  } finally {
    savingToggle.value = false
  }
}

// User Access Table
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const bulkLoading = ref(false)

const tableHeaders = computed(() => [
  { title: t('admin.communication.table.user'), key: 'username', sortable: true },
  { title: t('admin.communication.table.all'), key: 'all', sortable: false, width: 70 },
  { title: t('admin.communication.table.access'), key: 'access', sortable: false, width: 70 },
  { title: 'Chat', key: 'chat', sortable: false, width: 70 },
  { title: 'Voice', key: 'voice', sortable: false, width: 70 },
  { title: 'Video', key: 'video', sortable: false, width: 70 },
  { title: t('admin.communication.table.transcription'), key: 'transcription', sortable: false, width: 70 },
  { title: 'KI', key: 'ai', sortable: false, width: 70 },
])

const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value
  const q = userSearch.value.toLowerCase()
  return users.value.filter(u => u.username.toLowerCase().includes(q))
})

function allEnabled(item) {
  return COMM_PERMS.every(k => item.permissions[k] === true)
}

async function togglePerm(item, key, value) {
  item.permissions[key] = value
  try {
    await setUserPermissions(item.username, { [key]: value })
    await syncPermissions()
  } catch {
    item.permissions[key] = !value
    showError(t('admin.communication.permError'))
  }
}

async function toggleAll(item, value) {
  const perms = {}
  COMM_PERMS.forEach(k => { perms[k] = value })
  const prev = { ...item.permissions }
  COMM_PERMS.forEach(k => { item.permissions[k] = value })
  try {
    await setUserPermissions(item.username, perms)
    await syncPermissions()
  } catch {
    Object.assign(item.permissions, prev)
    showError(t('admin.communication.permError'))
  }
}

async function enableAll() {
  bulkLoading.value = true
  const perms = {}
  COMM_PERMS.forEach(k => { perms[k] = true })
  try {
    const usernames = users.value.map(u => u.username)
    await bulkSetPermissions(usernames, perms)
    await loadUsers()
    await syncPermissions()
    showSuccess(t('admin.communication.bulkEnabled'))
  } catch {
    showError(t('admin.communication.permError'))
  } finally {
    bulkLoading.value = false
  }
}

async function disableAll() {
  bulkLoading.value = true
  const perms = {}
  COMM_PERMS.forEach(k => { perms[k] = false })
  try {
    const usernames = users.value.map(u => u.username)
    await bulkSetPermissions(usernames, perms)
    await loadUsers()
    await syncPermissions()
    showSuccess(t('admin.communication.bulkDisabled'))
  } catch {
    showError(t('admin.communication.permError'))
  } finally {
    bulkLoading.value = false
  }
}

async function loadUsers() {
  usersLoading.value = true
  try {
    users.value = await fetchUsers()
  } catch { /* ignore */ } finally {
    usersLoading.value = false
  }
}

// Statistics
const stats = ref(null)
const userStats = ref([])

const statsHeaders = computed(() => [
  { title: t('admin.communication.table.user'), key: 'username', sortable: true },
  { title: t('admin.communication.stats.conversations'), key: 'conversation_count', sortable: true },
  { title: t('admin.communication.stats.messagesSent'), key: 'message_count', sortable: true },
  { title: t('admin.communication.stats.lastActive'), key: 'last_active', sortable: true },
  { title: t('admin.communication.stats.unread'), key: 'unread_count', sortable: true },
])

async function loadStats() {
  try {
    const data = await fetchStats()
    stats.value = data.stats || {}
    userStats.value = data.user_stats || []
  } catch { /* ignore */ }
}

onMounted(async () => {
  globalEnabled.value = communicationEnabled.value
  await Promise.all([loadUsers(), loadStats()])
})
</script>

<style scoped>
.stat-card {
  text-align: center;
  padding: 12px 8px;
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 2px;
}
.comm-users-table :deep(th),
.comm-users-table :deep(td) {
  padding: 4px 8px !important;
}
</style>
