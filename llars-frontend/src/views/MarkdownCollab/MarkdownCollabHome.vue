<template>
  <v-container class="pa-6" fluid>
    <div class="d-flex align-center mb-6">
      <div>
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-language-markdown</v-icon>
          <h2 class="text-h5 mb-0">Markdown Collab</h2>
        </div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          Kollaborative Workspaces für Markdown-Dateien mit Live-Preview.
        </div>
      </div>
      <v-spacer />
      <LBtn
        variant="primary"
        prepend-icon="mdi-plus"
        :disabled="!hasPermission('feature:markdown_collab:edit')"
        @click="createDialog = true"
      >
        Workspace erstellen
      </LBtn>
    </div>

    <v-alert
      v-if="!hasPermission('feature:markdown_collab:view')"
      type="warning"
      variant="tonal"
      class="mb-6"
    >
      Dir fehlt die Berechtigung <code>feature:markdown_collab:view</code>.
    </v-alert>

    <v-row v-else>
      <v-col cols="12">
        <v-skeleton-loader v-if="isLoading('workspaces')" type="card@3" />

        <LCard v-else outlined>
          <template #header>
            <div class="d-flex align-center w-100">
              <v-icon class="mr-2">mdi-folder-multiple-outline</v-icon>
              <span class="text-h6">Workspaces</span>
              <v-spacer />
              <v-btn variant="text" icon="mdi-refresh" @click="loadWorkspaces(true)" />
            </div>
          </template>

          <transition-group
            v-if="workspaces.length > 0"
            name="workspace-list"
            tag="div"
            class="v-row workspace-grid"
          >
            <v-col
              v-for="ws in workspaces"
              :key="ws.id"
              cols="12"
              md="6"
              lg="4"
            >
              <LCard
                :title="ws.name"
                icon="mdi-folder"
                color="#b0ca97"
                outlined
                clickable
                :class="['workspace-card', { 'workspace-card--new': newWorkspaceIds.has(ws.id) }]"
                @click="openWorkspace(ws.id)"
              >
                <template #status>
                  <v-chip size="small" variant="tonal" color="info">
                    #{{ ws.id }}
                  </v-chip>
                </template>

                <div class="text-medium-emphasis mb-2">
                  Besitzer: {{ ws.owner_username }}
                </div>
                <div class="d-flex align-center text-caption">
                  <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                  <span>Zuletzt geändert: {{ formatDate(ws.updated_at) }}</span>
                </div>

                <template #actions>
                  <v-spacer />
                  <LBtn variant="text" size="small" @click.stop="openWorkspace(ws.id)">
                    Öffnen
                  </LBtn>
                </template>
              </LCard>
            </v-col>
          </transition-group>

          <div v-else class="empty-state">
            <v-icon size="56" class="mb-3" color="grey">mdi-folder-open-outline</v-icon>
            <div class="text-subtitle-1 mb-1">Noch keine Workspaces</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              Erstelle deinen ersten Markdown Collab Workspace.
            </div>
            <LBtn
              variant="primary"
              prepend-icon="mdi-plus"
              :disabled="!hasPermission('feature:markdown_collab:edit')"
              @click="createDialog = true"
            >
              Workspace erstellen
            </LBtn>
          </div>
        </LCard>
      </v-col>
    </v-row>

    <v-dialog v-model="createDialog" max-width="520">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <v-icon class="mr-2">mdi-plus-circle</v-icon>
            <span class="text-h6">Workspace erstellen</span>
            <v-spacer />
            <v-btn icon="mdi-close" variant="text" @click="createDialog = false; resetCreateDialog()" />
          </div>
        </template>

        <v-alert v-if="createError" type="error" variant="tonal" class="mb-4">
          {{ createError }}
        </v-alert>
        <v-text-field
          v-model="newWorkspaceName"
          label="Name"
          placeholder="z. B. Dissertation Notes"
          prepend-inner-icon="mdi-folder"
          variant="outlined"
          density="comfortable"
        />
        <v-select
          v-model="newWorkspaceVisibility"
          :items="visibilityItems"
          label="Sichtbarkeit"
          prepend-inner-icon="mdi-eye-outline"
          variant="outlined"
          density="comfortable"
        />

        <!-- User invite section -->
        <div class="section-label mt-4">
          <v-icon size="16" class="mr-1">mdi-account-multiple-plus</v-icon>
          Mitglieder einladen (optional)
        </div>
        <div v-if="invitedUsers.length > 0" class="invited-users mb-2">
          <LTag
            v-for="user in invitedUsers"
            :key="user"
            variant="primary"
            closable
            @close="removeInvitedUser(user)"
          >
            {{ user }}
          </LTag>
        </div>
        <LUserSearch
          ref="userSearchRef"
          :exclude-usernames="invitedUsers"
          placeholder="Nutzernamen eingeben..."
          @select="handleInviteUserSelect"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="createDialog = false; resetCreateDialog()">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            :loading="creating"
            :disabled="!canCreate"
            @click="createWorkspace"
          >
            Erstellen
          </LBtn>
        </template>
      </LCard>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const router = useRouter()
const { hasPermission, fetchPermissions } = usePermissions()
const { isLoading, withLoading } = useSkeletonLoading(['workspaces'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const workspaces = ref([])
const newWorkspaceIds = ref(new Set())

const createDialog = ref(false)
const creating = ref(false)
const createError = ref('')
const newWorkspaceName = ref('')
const newWorkspaceVisibility = ref('private')
const invitedUsers = ref([])
const userSearchRef = ref(null)

const visibilityItems = [
  { title: 'Privat', value: 'private' },
  { title: 'Team', value: 'team' },
  { title: 'Organisation', value: 'org' }
]

const canCreate = computed(() => {
  return hasPermission('feature:markdown_collab:edit') && newWorkspaceName.value.trim().length >= 2
})

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function sortWorkspaces(list) {
  return [...(list || [])].sort((a, b) => {
    const aTime = a?.updated_at ? new Date(a.updated_at).getTime() : 0
    const bTime = b?.updated_at ? new Date(b.updated_at).getTime() : 0
    return bTime - aTime
  })
}

function markWorkspaceNew(id) {
  if (!id) return
  const next = new Set(newWorkspaceIds.value)
  next.add(id)
  newWorkspaceIds.value = next
  setTimeout(() => {
    const updated = new Set(newWorkspaceIds.value)
    updated.delete(id)
    newWorkspaceIds.value = updated
  }, 3600)
}

async function fetchUserId() {
  try {
    const res = await axios.get(`${API_BASE}/auth/authentik/me`, {
      headers: authHeaders()
    })
    return res.data.user_id || res.data.id || null
  } catch (e) {
    return null
  }
}

async function loadWorkspaces(force = false) {
  await withLoading('workspaces', async () => {
    const res = await axios.get(`${API_BASE}/api/markdown-collab/workspaces`, {
      headers: authHeaders(),
      params: force ? { _ts: Date.now() } : undefined
    })
    workspaces.value = sortWorkspaces(res.data.workspaces || [])
  })
}

function openWorkspace(id) {
  router.push(`/MarkdownCollab/workspace/${id}`)
}

function handleInviteUserSelect(user) {
  if (user?.username && !invitedUsers.value.includes(user.username)) {
    invitedUsers.value.push(user.username)
  }
  userSearchRef.value?.reset?.()
}

function removeInvitedUser(username) {
  invitedUsers.value = invitedUsers.value.filter(u => u !== username)
}

function resetCreateDialog() {
  newWorkspaceName.value = ''
  newWorkspaceVisibility.value = 'private'
  invitedUsers.value = []
  userSearchRef.value?.reset?.()
  createError.value = ''
}

async function createWorkspace() {
  createError.value = ''
  creating.value = true
  try {
    const res = await axios.post(
      `${API_BASE}/api/markdown-collab/workspaces`,
      {
        name: newWorkspaceName.value.trim(),
        visibility: newWorkspaceVisibility.value
      },
      { headers: authHeaders() }
    )
    const ws = res.data.workspace

    // Invite users if any were selected
    if (ws?.id && invitedUsers.value.length > 0) {
      for (const username of invitedUsers.value) {
        try {
          await axios.post(
            `${API_BASE}/api/markdown-collab/workspaces/${ws.id}/members`,
            { username },
            { headers: authHeaders() }
          )
        } catch (inviteErr) {
          console.error(`Failed to invite ${username}:`, inviteErr)
          // Continue with other invites even if one fails
        }
      }
    }

    createDialog.value = false
    resetCreateDialog()
    await loadWorkspaces(true)
    if (ws?.id) openWorkspace(ws.id)
  } catch (e) {
    createError.value = e?.response?.data?.error || e?.message || 'Workspace konnte nicht erstellt werden'
  } finally {
    creating.value = false
  }
}

let socket = null
let socketUserId = null
let onSocketConnect = null

function handleWorkspaceShared(payload) {
  const workspace = payload?.workspace
  if (!workspace?.id) return

  const existingIndex = workspaces.value.findIndex(w => w.id === workspace.id)
  if (existingIndex >= 0) {
    const next = [...workspaces.value]
    next[existingIndex] = { ...next[existingIndex], ...workspace }
    workspaces.value = sortWorkspaces(next)
  } else {
    workspaces.value = sortWorkspaces([workspace, ...workspaces.value])
  }
  markWorkspaceNew(workspace.id)
}

function setupWorkspaceSocket(userId) {
  if (!userId) return
  socket = getSocket()
  if (!socket) return

  socket.on('markdown_collab:workspace_shared', handleWorkspaceShared)

  onSocketConnect = () => {
    socket.emit('markdown_collab:subscribe', { user_id: userId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
  socketUserId = userId
}

function cleanupWorkspaceSocket() {
  if (!socket) return
  socket.off('markdown_collab:workspace_shared', handleWorkspaceShared)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (socketUserId) {
    socket.emit('markdown_collab:unsubscribe', { user_id: socketUserId })
  }
  socketUserId = null
  onSocketConnect = null
}

onMounted(async () => {
  await fetchPermissions()
  if (hasPermission('feature:markdown_collab:view')) {
    await loadWorkspaces()
    const userId = await fetchUserId()
    if (userId) setupWorkspaceSocket(userId)
  }
})

onUnmounted(() => {
  cleanupWorkspaceSocket()
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 16px;
  color: rgb(var(--v-theme-on-surface));
}

.w-100 {
  width: 100%;
}

.workspace-list-enter-active,
.workspace-list-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.workspace-list-enter-from,
.workspace-list-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.workspace-list-move {
  transition: transform 0.35s ease;
}

.workspace-card--new {
  border: 1px solid rgba(var(--v-theme-primary), 0.45);
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.18), 0 14px 26px rgba(0, 0, 0, 0.08);
  background: linear-gradient(120deg, rgba(var(--v-theme-primary), 0.12), rgba(var(--v-theme-surface), 0.96));
  color: rgb(var(--v-theme-on-surface));
  animation: workspace-highlight 2.6s ease-out;
}

@keyframes workspace-highlight {
  0% {
    transform: translateY(8px) scale(1.02);
    box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.28), 0 18px 32px rgba(0, 0, 0, 0.12);
  }
  100% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.18), 0 14px 26px rgba(0, 0, 0, 0.08);
  }
}

/* Create Dialog - Invite Section */
.section-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.invited-users {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
