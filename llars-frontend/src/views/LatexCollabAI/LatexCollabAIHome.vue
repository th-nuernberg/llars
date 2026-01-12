<template>
  <v-container :class="['latex-home', { 'pa-4': isMobile, 'pa-6': !isMobile, 'is-mobile': isMobile, 'is-tablet': isTablet }]" fluid>
    <div class="page-header" :class="{ 'flex-column align-start': isMobile }">
      <div>
        <div class="d-flex align-center">
          <LIcon :class="isMobile ? 'mr-1' : 'mr-2'" :size="isMobile ? 20 : 24" color="primary">llars:latex-collab-ai</LIcon>
          <h2 :class="isMobile ? 'text-h6' : 'text-h5'" class="mb-0">
            {{ isMobile ? $t('latexCollabAi.home.titleShort') : $t('latexCollabAi.home.title') }}
          </h2>
          <LTag variant="warning" size="small" class="ml-2">{{ $t('home.badges.test') }}</LTag>
        </div>
        <div v-if="!isMobile" class="text-body-2 text-medium-emphasis mt-1">
          {{ $t('latexCollabAi.home.subtitle') }}
        </div>
      </div>
      <v-spacer v-if="!isMobile" />
      <LBtn
        variant="primary"
        :prepend-icon="isMobile ? '' : 'mdi-plus'"
        :size="isMobile ? 'small' : 'default'"
        :class="{ 'mt-3': isMobile, 'align-self-end': isMobile }"
        :disabled="!hasPermission('feature:latex_collab:edit')"
        @click="createDialog = true"
      >
        <LIcon v-if="isMobile" class="mr-1">mdi-plus</LIcon>
        {{ isMobile ? $t('latexCollabAi.home.actions.newShort') : $t('latexCollabAi.home.actions.create') }}
      </LBtn>
    </div>

    <!-- AI Features Info Banner -->
    <v-alert type="info" variant="tonal" class="mb-4" closable>
      <div class="d-flex align-center">
        <LIcon class="mr-2">mdi-robot-happy</LIcon>
        <div>
          <strong>{{ $t('latexCollabAi.home.banner.title') }}</strong>
          <div class="text-body-2 mt-1">
            {{ $t('latexCollabAi.home.banner.body') }}
          </div>
        </div>
      </div>
    </v-alert>

    <v-alert
      v-if="!hasPermission('feature:latex_collab:view')"
      type="warning"
      variant="tonal"
      class="mb-6"
    >
      <i18n-t keypath="latexCollab.permissions.missing" tag="span">
        <template #permission>
          <code>feature:latex_collab:view</code>
        </template>
      </i18n-t>
    </v-alert>

    <v-row v-else>
      <v-col cols="12">
        <v-skeleton-loader v-if="isLoading('workspaces')" type="card@3" />

        <LCard v-else outlined>
          <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2">mdi-folder-multiple-outline</LIcon>
              <span class="text-h6">{{ $t('latexCollabAi.home.workspaces.title') }}</span>
              <v-spacer />
              <LIconBtn icon="mdi-refresh" :tooltip="$t('common.refresh')" @click="loadWorkspaces(true)" />
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
                color="#88c4c8"
                outlined
                clickable
                :class="['workspace-card', { 'workspace-card--new': newWorkspaceIds.has(ws.id) }]"
                @click="openWorkspace(ws.id)"
              >
                <template #status>
                  <LTag
                    v-if="isOwner(ws)"
                    variant="accent"
                    size="small"
                    prepend-icon="mdi-crown"
                  >
                    {{ $t('latexCollabAi.home.status.owner') }}
                  </LTag>
                  <LTag
                    v-else
                    variant="info"
                    size="small"
                    prepend-icon="mdi-account-multiple"
                  >
                    {{ $t('latexCollabAi.home.status.guest') }}
                  </LTag>
                </template>

                <div class="text-medium-emphasis mb-2">
                  <LIcon size="14" class="mr-1">mdi-account</LIcon>
                  {{ ws.owner_username }}
                </div>
                <div class="d-flex align-center text-caption">
                  <LIcon size="16" class="mr-1">mdi-clock-outline</LIcon>
                  <span>{{ $t('latexCollabAi.home.lastUpdated', { date: formatDate(ws.updated_at) }) }}</span>
                </div>

                <template #actions>
                  <v-spacer />
                  <!-- Leave button for members (non-owners) -->
                  <LBtn
                    v-if="!isOwner(ws)"
                    variant="text"
                    size="small"
                    prepend-icon="mdi-exit-run"
                    @click.stop="confirmLeave(ws)"
                  >
                    {{ $t('latexCollabAi.home.actions.leave') }}
                  </LBtn>
                  <!-- Delete button for owners -->
                  <LBtn
                    v-if="canDeleteWorkspace(ws)"
                    variant="text"
                    size="small"
                    color="error"
                    prepend-icon="mdi-delete"
                    @click.stop="confirmDelete(ws)"
                  >
                    {{ $t('common.delete') }}
                  </LBtn>
                  <LBtn variant="text" size="small" @click.stop="openWorkspace(ws.id)">
                    {{ $t('latexCollabAi.home.actions.open') }}
                  </LBtn>
                </template>
              </LCard>
            </v-col>
          </transition-group>

          <div v-else class="empty-state">
            <LIcon size="56" class="mb-3" color="grey">mdi-folder-open-outline</LIcon>
            <div class="text-subtitle-1 mb-1">{{ $t('latexCollabAi.home.empty.title') }}</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              {{ $t('latexCollabAi.home.empty.subtitle') }}
            </div>
            <LBtn
              variant="primary"
              prepend-icon="mdi-plus"
              :disabled="!hasPermission('feature:latex_collab:edit')"
              @click="createDialog = true"
            >
              {{ $t('latexCollabAi.home.actions.create') }}
            </LBtn>
          </div>
        </LCard>
      </v-col>
    </v-row>

    <v-dialog v-model="createDialog" max-width="520">
      <LCard>
        <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2">mdi-plus-circle</LIcon>
            <span class="text-h6">{{ $t('latexCollabAi.home.dialogs.createTitle') }}</span>
            <v-spacer />
            <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="createDialog = false; resetCreateDialog()" />
          </div>
        </template>

        <v-alert v-if="createError" type="error" variant="tonal" class="mb-4">
          {{ createError }}
        </v-alert>
        <v-text-field
          v-model="newWorkspaceName"
          :label="$t('latexCollabAi.home.form.nameLabel')"
          :placeholder="$t('latexCollabAi.home.form.namePlaceholder')"
          prepend-inner-icon="mdi-folder"
          variant="outlined"
          density="comfortable"
        />
        <v-select
          v-model="newWorkspaceVisibility"
          :items="visibilityItems"
          :label="$t('latexCollabAi.home.form.visibilityLabel')"
          prepend-inner-icon="mdi-eye-outline"
          variant="outlined"
          density="comfortable"
        />

        <!-- User invite section -->
        <div class="section-label mt-4">
          <LIcon size="16" class="mr-1">mdi-account-multiple-plus</LIcon>
          {{ $t('latexCollabAi.home.form.inviteLabel') }}
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
          :placeholder="$t('latexCollabAi.home.form.userPlaceholder')"
          @select="handleInviteUserSelect"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="createDialog = false; resetCreateDialog()">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="primary"
            :loading="creating"
            :disabled="!canCreate"
            @click="createWorkspace"
          >
            {{ $t('latexCollabAi.home.actions.createConfirm') }}
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="420">
      <LCard>
        <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2" color="error">mdi-delete-alert</LIcon>
            <span class="text-h6">{{ $t('latexCollabAi.home.dialogs.deleteTitle') }}</span>
            <v-spacer />
            <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="deleteDialog = false" />
          </div>
        </template>

        <i18n-t keypath="latexCollabAi.home.dialogs.deleteConfirm" tag="p" class="mb-4">
          <template #name>
            <strong>{{ workspaceToDelete?.name }}</strong>
          </template>
        </i18n-t>
        <v-alert type="warning" variant="tonal" density="compact" class="mb-0">
          {{ $t('latexCollabAi.home.dialogs.deleteHint') }}
        </v-alert>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="deleteDialog = false">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="danger"
            :loading="deleting"
            prepend-icon="mdi-delete"
            @click="deleteWorkspace"
          >
            {{ $t('common.delete') }}
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Leave Confirmation Dialog -->
    <v-dialog v-model="leaveDialog" max-width="420">
      <LCard>
        <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2" color="warning">mdi-exit-run</LIcon>
            <span class="text-h6">{{ $t('latexCollabAi.home.dialogs.leaveTitle') }}</span>
            <v-spacer />
            <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" @click="leaveDialog = false" />
          </div>
        </template>

        <i18n-t keypath="latexCollabAi.home.dialogs.leaveConfirm" tag="p" class="mb-4">
          <template #name>
            <strong>{{ workspaceToLeave?.name }}</strong>
          </template>
        </i18n-t>
        <v-alert type="info" variant="tonal" density="compact" class="mb-0">
          {{ $t('latexCollabAi.home.dialogs.leaveHint') }}
        </v-alert>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="leaveDialog = false">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="secondary"
            :loading="leaving"
            prepend-icon="mdi-exit-run"
            @click="leaveWorkspace"
          >
            {{ $t('latexCollabAi.home.actions.leave') }}
          </LBtn>
        </template>
      </LCard>
    </v-dialog>
  </v-container>
</template>

<script setup>
/**
 * LatexCollabAIHome.vue
 *
 * TEST-VERSION: LaTeX Collab mit KI-Schreibassistent
 *
 * Diese Komponente nutzt die gleichen Backend-Endpoints wie LatexCollab,
 * aber die Workspace-Ansicht enthält zusätzliche KI-Features:
 * - Ghost Text Completion
 * - @-Commands
 * - AI Sidebar
 * - RAG-basierte Literatursuche
 *
 * Siehe: /app/data/rag/standard/llars/llars_latex_collab_ai_konzept.md
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useMobile } from '@/composables/useMobile'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getSocket } from '@/services/socketService'

const router = useRouter()
const { t, locale } = useI18n()
const { hasPermission, fetchPermissions, isAdmin, username: permissionsUsername } = usePermissions()
const { isLoading, withLoading } = useSkeletonLoading(['workspaces'])
const { isMobile, isTablet } = useMobile()

// Uses the same API as LatexCollab (shares workspaces)
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const workspaces = ref([])
const newWorkspaceIds = ref(new Set())
const userInfoUsername = ref('')
const currentUsername = computed(() => userInfoUsername.value || permissionsUsername.value || '')

const createDialog = ref(false)
const deleteDialog = ref(false)
const leaveDialog = ref(false)
const workspaceToDelete = ref(null)
const workspaceToLeave = ref(null)
const deleting = ref(false)
const leaving = ref(false)
const creating = ref(false)
const createError = ref('')
const newWorkspaceName = ref('')
const newWorkspaceVisibility = ref('private')
const invitedUsers = ref([])
const userSearchRef = ref(null)

const visibilityItems = computed(() => ([
  { title: t('latexCollabAi.visibility.private'), value: 'private' },
  { title: t('latexCollabAi.visibility.team'), value: 'team' },
  { title: t('latexCollabAi.visibility.org'), value: 'org' }
]))

const canCreate = computed(() => {
  return hasPermission('feature:latex_collab:edit') && newWorkspaceName.value.trim().length >= 2
})

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(locale.value || undefined)
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

async function fetchUserInfo() {
  try {
    const res = await axios.get(`${API_BASE}/auth/authentik/me`, {
      headers: authHeaders()
    })
    userInfoUsername.value = res.data.username || ''
    return res.data.user_id || res.data.id || null
  } catch (e) {
    return null
  }
}

function isOwner(ws) {
  return ws?.owner_username === currentUsername.value
}

function canDeleteWorkspace(ws) {
  return isOwner(ws) || isAdmin.value
}

function confirmDelete(ws) {
  workspaceToDelete.value = ws
  deleteDialog.value = true
}

function confirmLeave(ws) {
  workspaceToLeave.value = ws
  leaveDialog.value = true
}

async function deleteWorkspace() {
  if (!workspaceToDelete.value) return
  deleting.value = true
  try {
    await axios.delete(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceToDelete.value.id}`,
      { headers: authHeaders() }
    )
    workspaces.value = workspaces.value.filter(w => w.id !== workspaceToDelete.value.id)
    deleteDialog.value = false
    workspaceToDelete.value = null
  } catch (e) {
    console.error('Failed to delete workspace:', e)
    alert(e?.response?.data?.error || t('latexCollabAi.errors.deleteFailed'))
  } finally {
    deleting.value = false
  }
}

async function leaveWorkspace() {
  if (!workspaceToLeave.value) return
  leaving.value = true
  try {
    await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceToLeave.value.id}/leave`,
      {},
      { headers: authHeaders() }
    )
    workspaces.value = workspaces.value.filter(w => w.id !== workspaceToLeave.value.id)
    leaveDialog.value = false
    workspaceToLeave.value = null
  } catch (e) {
    console.error('Failed to leave workspace:', e)
    alert(e?.response?.data?.error || t('latexCollabAi.errors.leaveFailed'))
  } finally {
    leaving.value = false
  }
}

async function loadWorkspaces(force = false) {
  await withLoading('workspaces', async () => {
    const res = await axios.get(`${API_BASE}/api/latex-collab/workspaces`, {
      headers: authHeaders(),
      params: force ? { _ts: Date.now() } : undefined
    })
    workspaces.value = sortWorkspaces(res.data.workspaces || [])
  })
}

function openWorkspace(id) {
  // Navigate to AI version of workspace
  router.push(`/LatexCollabAI/workspace/${id}`)
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
      `${API_BASE}/api/latex-collab/workspaces`,
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
            `${API_BASE}/api/latex-collab/workspaces/${ws.id}/members`,
            { username },
            { headers: authHeaders() }
          )
        } catch (inviteErr) {
          console.error(`Failed to invite ${username}:`, inviteErr)
        }
      }
    }

    createDialog.value = false
    resetCreateDialog()
    await loadWorkspaces(true)
    if (ws?.id) openWorkspace(ws.id)
  } catch (e) {
    createError.value = e?.response?.data?.error || e?.message || t('latexCollabAi.errors.createFailed')
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

  socket.on('latex_collab:workspace_shared', handleWorkspaceShared)

  onSocketConnect = () => {
    socket.emit('latex_collab:subscribe', { user_id: userId })
  }

  if (socket.connected) {
    onSocketConnect()
  }
  socket.on('connect', onSocketConnect)
  socketUserId = userId
}

function cleanupWorkspaceSocket() {
  if (!socket) return
  socket.off('latex_collab:workspace_shared', handleWorkspaceShared)
  if (onSocketConnect) socket.off('connect', onSocketConnect)
  if (socketUserId) {
    socket.emit('latex_collab:unsubscribe', { user_id: socketUserId })
  }
  socketUserId = null
  onSocketConnect = null
}

onMounted(async () => {
  await fetchPermissions()
  if (hasPermission('feature:latex_collab:view')) {
    await loadWorkspaces()
    const userId = await fetchUserInfo()
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
  border: 1px solid rgba(136, 196, 200, 0.45);
  box-shadow: 0 0 0 2px rgba(136, 196, 200, 0.18), 0 14px 26px rgba(0, 0, 0, 0.08);
  background: linear-gradient(120deg, rgba(136, 196, 200, 0.12), rgba(var(--v-theme-surface), 0.96));
  color: rgb(var(--v-theme-on-surface));
  animation: workspace-highlight 2.6s ease-out;
}

@keyframes workspace-highlight {
  0% {
    transform: translateY(8px) scale(1.02);
    box-shadow: 0 0 0 3px rgba(136, 196, 200, 0.28), 0 18px 32px rgba(0, 0, 0, 0.12);
  }
  100% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 2px rgba(136, 196, 200, 0.18), 0 14px 26px rgba(0, 0, 0, 0.08);
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

/* Page header */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

/* Mobile Responsive */
.latex-home.is-mobile {
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  overflow-y: auto;
  overflow-x: hidden;
  max-width: 100vw;
  -webkit-overflow-scrolling: touch;
}

.latex-home.is-mobile .page-header {
  margin-bottom: 16px;
}

.latex-home.is-mobile .workspace-grid {
  margin: 0 -8px;
}

.latex-home.is-mobile .workspace-grid > .v-col {
  padding: 8px;
}

.latex-home.is-mobile .empty-state {
  padding: 24px 12px;
}

.latex-home.is-tablet .page-header {
  margin-bottom: 20px;
}
</style>
