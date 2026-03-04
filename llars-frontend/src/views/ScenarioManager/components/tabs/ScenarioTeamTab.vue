<template>
  <div class="team-tab">
    <!-- Header -->
    <div class="tab-header">
      <h3>{{ $t('scenarioManager.team.title') }}</h3>
      <LBtn v-if="canManage" variant="primary" @click="showInviteDialog = true">
        <LIcon start>mdi-account-plus</LIcon>
        {{ $t('scenarioManager.team.invite') }}
      </LBtn>
    </div>

    <!-- Team Stats -->
    <div class="team-stats">
      <div class="stat-card">
        <LIcon size="24" color="primary">mdi-account-check</LIcon>
        <div class="stat-info">
          <span class="stat-value">{{ evaluators.length }}</span>
          <span class="stat-label">{{ $t('scenarioManager.team.evaluators') }}</span>
        </div>
      </div>
      <div class="stat-card">
        <LIcon size="24" color="accent">mdi-robot</LIcon>
        <div class="stat-info">
          <span class="stat-value">{{ llmEvaluators.length }}</span>
          <span class="stat-label">{{ $t('scenarioManager.team.llmModels') }}</span>
        </div>
      </div>
    </div>

    <!-- Team Members List -->
    <div class="section">
      <h4 class="section-title">{{ $t('scenarioManager.team.humanEvaluators') }}</h4>
      <div class="members-list">
        <div
          v-for="member in evaluators"
          :key="member.user_id"
          class="member-card"
          :class="{ 'is-rejected': member.invitation_status === 'rejected' }"
        >
          <div class="member-avatar">
            <LAvatar
              :username="member.username"
              :seed="member.avatar_seed"
              :src="member.avatar_url"
              size="md"
            />
          </div>
          <div class="member-info">
            <span class="member-name">{{ member.display_name || member.username }}</span>
            <div class="member-meta">
              <LTag :variant="getRoleVariant(member.role)" size="sm">
                {{ $t(`scenarioManager.team.roles.${member.role?.toLowerCase() || 'evaluator'}`) }}
              </LTag>
              <!-- Owner indicator -->
              <LTag v-if="isOwner(member)" variant="primary" size="sm">
                {{ $t('scenarioManager.team.roles.owner') }}
              </LTag>
              <!-- Invitation Status Badge -->
              <LTag
                v-if="member.invitation_status && member.invitation_status !== 'accepted' && !isOwner(member)"
                :variant="getInvitationVariant(member.invitation_status)"
                size="sm"
              >
                {{ $t(`scenarioManager.invitation.${member.invitation_status}`) }}
              </LTag>
            </div>
          </div>
          <div class="member-stats">
            <span class="stat">
              <LIcon size="16">mdi-check-circle-outline</LIcon>
              {{ member.completed || 0 }} / {{ member.total || 0 }}
            </span>
          </div>
          <div class="member-actions" v-if="canManage && !isOwner(member)">
            <!-- Re-invite button for rejected members -->
            <LBtn
              v-if="member.invitation_status === 'rejected'"
              variant="primary"
              size="small"
              :loading="reinviting === member.user_id"
              @click="doReinvite(member)"
            >
              <LIcon start size="16">mdi-email-send-outline</LIcon>
              {{ $t('scenarioManager.invitation.reinvite') }}
            </LBtn>
            <v-menu v-else>
              <template #activator="{ props }">
                <v-btn icon size="small" variant="text" v-bind="props">
                  <LIcon size="18">mdi-dots-vertical</LIcon>
                </v-btn>
              </template>
              <v-list density="compact">
                <v-list-item @click="changeRole(member)">
                  <template #prepend>
                    <LIcon size="18" class="mr-2">mdi-account-convert</LIcon>
                  </template>
                  <v-list-item-title>{{ $t('scenarioManager.team.changeRole') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="confirmRemoveMember(member)" class="text-error">
                  <template #prepend>
                    <LIcon size="18" class="mr-2" color="error">mdi-account-remove</LIcon>
                  </template>
                  <v-list-item-title>{{ $t('scenarioManager.team.remove') }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>

        <div v-if="evaluators.length === 0" class="empty-list">
          <p>{{ $t('scenarioManager.team.noEvaluators') }}</p>
        </div>
      </div>
    </div>

    <!-- LLM Evaluators -->
    <div class="section">
      <div class="section-header">
        <h4 class="section-title">{{ $t('scenarioManager.team.llmEvaluators') }}</h4>
        <LBtn v-if="canManage" variant="secondary" size="small" @click="showAddLLMDialog = true">
          <LIcon start size="16">mdi-plus</LIcon>
          {{ $t('scenarioManager.team.addLLM') }}
        </LBtn>
      </div>
      <div class="members-list">
        <div
          v-for="llm in llmEvaluators"
          :key="llm.id"
          class="member-card is-llm"
        >
          <div class="member-avatar llm">
            <LIcon size="20">mdi-robot-outline</LIcon>
          </div>
          <div class="member-info">
            <span class="member-name">{{ llm.model_name }}</span>
            <div class="member-meta">
              <span class="member-detail">{{ llm.provider }}</span>
              <LTag v-if="llm.status === 'failed' || llm.status === 'stopped'" variant="danger" size="sm">
                {{ $t(`scenarioManager.team.llm${llm.status === 'failed' ? 'Failed' : 'Stopped'}`) }}
              </LTag>
              <LTag v-else-if="llm.status === 'completed'" variant="success" size="sm">
                {{ $t('scenarioManager.team.llmCompleted') }}
              </LTag>
              <LTag v-else-if="llm.status === 'running'" variant="info" size="sm">
                {{ $t('scenarioManager.team.llmRunning') }}
              </LTag>
            </div>
          </div>
          <div class="member-stats">
            <span class="stat">
              <LIcon size="16">mdi-check-circle-outline</LIcon>
              {{ llm.completed || 0 }} / {{ llm.total || 0 }}
            </span>
            <span
              v-if="llm.errorCount > 0"
              class="stat error-stat"
              @click="openErrorDialog(llm)"
            >
              <LIcon size="16" color="#e8a087">mdi-alert-circle</LIcon>
              <span class="error-count">{{ llm.errorCount }}</span>
              {{ $t('scenarioManager.overview.failed') }}
            </span>
            <span class="stat" v-if="llm.cost">
              <LIcon size="16">mdi-currency-usd</LIcon>
              {{ llm.cost.toFixed(4) }}
            </span>
          </div>
          <div class="member-actions" v-if="canManage">
            <!-- Start button: model has not started yet -->
            <LBtn
              v-if="llm.completed === 0 && llm.errorCount === 0 && llm.status !== 'running'"
              variant="primary"
              size="small"
              :loading="retryingModel === llm.id"
              @click="retryLLM(llm)"
            >
              <LIcon start size="16">mdi-play</LIcon>
              {{ $t('scenarioManager.team.startLLM') }}
            </LBtn>
            <!-- Retry button: model has errors -->
            <LBtn
              v-else-if="(llm.errorCount > 0 || llm.status === 'stopped' || llm.status === 'failed') && llm.status !== 'running'"
              variant="accent"
              size="small"
              :loading="retryingModel === llm.id"
              @click="retryLLM(llm)"
            >
              <LIcon start size="16">mdi-refresh</LIcon>
              {{ $t('scenarioManager.team.retry') }}
            </LBtn>
            <v-btn icon size="small" variant="text" color="error" @click="confirmRemoveLLM(llm)">
              <LIcon size="18">mdi-delete-outline</LIcon>
            </v-btn>
          </div>
        </div>

        <div v-if="llmEvaluators.length === 0" class="empty-list">
          <p>{{ $t('scenarioManager.team.noLLM') }}</p>
        </div>
      </div>
    </div>

    <!-- Invite Dialog -->
    <v-dialog v-model="showInviteDialog" max-width="500">
      <v-card>
        <v-card-title>
          <LIcon color="primary" class="mr-2">mdi-account-plus</LIcon>
          {{ $t('scenarioManager.team.inviteTitle') }}
        </v-card-title>
        <v-card-text>
          <!-- Selected users as chips -->
          <div v-if="selectedUsers.length > 0" class="selected-users mb-3">
            <LTag
              v-for="user in selectedUsers"
              :key="user.username"
              variant="secondary"
              closable
              class="mr-2 mb-2"
              @close="removeSelectedUser(user)"
            >
              {{ user.display_name || user.username }}
            </LTag>
          </div>

          <!-- User search -->
          <LUserSearch
            ref="userSearchRef"
            :exclude-usernames="excludedUsernames"
            :placeholder="$t('scenarioManager.team.searchUsers')"
            @select="handleUserSelect"
          />

          <v-select
            v-model="inviteRole"
            :items="roleOptions"
            :label="$t('scenarioManager.team.role')"
            variant="outlined"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showInviteDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" :disabled="selectedUsers.length === 0" :loading="inviting" @click="inviteUsers">
            {{ $t('scenarioManager.team.sendInvite') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add LLM Dialog -->
    <v-dialog v-model="showAddLLMDialog" max-width="500">
      <v-card>
        <v-card-title>
          <LIcon color="accent" class="mr-2">mdi-robot-outline</LIcon>
          {{ $t('scenarioManager.team.addLLMTitle') }}
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="selectedLLM"
            :items="availableLLMs"
            :label="$t('scenarioManager.team.selectModel')"
            item-title="name"
            item-value="id"
            variant="outlined"
          />
          <v-select
            v-model="selectedTemplate"
            :items="availableTemplates"
            :label="$t('scenarioManager.team.selectTemplate')"
            item-title="name"
            item-value="id"
            variant="outlined"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showAddLLMDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" :disabled="!selectedLLM" :loading="addingLLM" @click="addLLMEvaluator">
            {{ $t('scenarioManager.team.add') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Remove Confirmation -->
    <v-dialog v-model="showRemoveDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="error" class="mr-2">mdi-alert-circle-outline</LIcon>
          {{ $t('scenarioManager.team.removeTitle') }}
        </v-card-title>
        <v-card-text>
          {{ $t('scenarioManager.team.removeConfirm', { name: memberToRemove?.display_name || memberToRemove?.username }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showRemoveDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" :loading="removing" @click="removeMember">
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error Details Dialog -->
    <v-dialog v-model="showErrorDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="#e8a087" class="mr-2">mdi-alert-circle-outline</LIcon>
          {{ $t('scenarioManager.team.errorDetailsTitle') }}
          <span v-if="errorDialogModel" class="ml-2 text-subtitle-2 text-medium-emphasis">
            — {{ errorDialogModel.model_name }}
          </span>
        </v-card-title>
        <v-card-text>
          <div v-if="errorDetailsLoading" class="text-center py-4">
            <v-progress-circular indeterminate size="32" />
          </div>
          <div v-else-if="errorDetails.length === 0" class="text-center py-4 text-medium-emphasis">
            {{ $t('scenarioManager.team.noErrors') }}
          </div>
          <div v-else class="error-list">
            <div v-for="err in errorDetails" :key="err.id" class="error-item">
              <div class="error-item-header">
                <span class="error-item-label">{{ err.item_label }}</span>
                <span class="error-item-date">{{ formatErrorDate(err.updated_at) }}</span>
              </div>
              <div class="error-item-message">{{ err.error }}</div>
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn
            v-if="canManage && errorDetails.length > 0"
            variant="accent"
            :loading="retryingModel === errorDialogModel?.id"
            @click="retryLLM(errorDialogModel); showErrorDialog = false"
          >
            <LIcon start size="16">mdi-refresh</LIcon>
            {{ $t('scenarioManager.team.retryAll') }}
          </LBtn>
          <LBtn variant="text" @click="showErrorDialog = false">
            {{ $t('common.close') || $t('common.cancel') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Change Role Dialog -->
    <v-dialog v-model="showRoleDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="primary" class="mr-2">mdi-account-convert</LIcon>
          {{ $t('scenarioManager.team.changeRole') }}
        </v-card-title>
        <v-card-text>
          <p class="mb-4">
            {{ $t('scenarioManager.team.changeRoleFor', { name: memberToChangeRole?.display_name || memberToChangeRole?.username }) }}
          </p>
          <v-select
            v-model="newRole"
            :items="roleOptions"
            :label="$t('scenarioManager.team.newRole')"
            variant="outlined"
          />
          <v-alert
            v-if="newRole === 'VIEWER'"
            type="info"
            variant="tonal"
            density="compact"
            class="mt-3"
          >
            {{ $t('scenarioManager.team.viewerHint') }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showRoleDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" :loading="changingRole" @click="confirmRoleChange">
            {{ $t('common.save') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useScenarioManager } from '../../composables/useScenarioManager'
import { useModelRegistry } from '@/composables/useModelRegistry'
import { useAuth } from '@/composables/useAuth'
import { getSocket } from '@/services/socketService'
import LAvatar from '@/components/common/LAvatar.vue'
import LUserSearch from '@/components/common/LUserSearch.vue'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  },
  liveStats: {
    type: Object,
    default: null
  },
  canManage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['team-updated', 'refreshStats'])

const { t } = useI18n()
const {
  inviteUsers: doInvite,
  removeUser,
  reinviteUser,
  updateUserRole,
  getScenarioTeam
} = useScenarioManager()
const { formatModelName: registryFormatModelName } = useModelRegistry()
const { getToken } = useAuth()

// State
const showInviteDialog = ref(false)
const reinviting = ref(null)
const teamData = ref(null)
const showAddLLMDialog = ref(false)
const showRemoveDialog = ref(false)
const selectedUsers = ref([])  // Array of user objects { username, display_name, ... }
const inviteRole = ref('ASSESSOR')
const inviting = ref(false)
const memberToRemove = ref(null)
const removing = ref(false)
const userSearchRef = ref(null)

const selectedLLM = ref(null)
const selectedTemplate = ref(null)
const addingLLM = ref(false)

// Role change dialog
const showRoleDialog = ref(false)
const memberToChangeRole = ref(null)
const newRole = ref('ASSESSOR')
const changingRole = ref(false)

// Error dialog and retry
const showErrorDialog = ref(false)
const errorDialogModel = ref(null)
const errorDetails = ref([])
const errorDetailsLoading = ref(false)
const retryingModel = ref(null)

// Mock data
const availableLLMs = ref([
  { id: 'gpt-4o', name: 'GPT-4o' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet' }
])

const availableTemplates = ref([
  { id: 'default', name: 'Standard' },
  { id: 'detailed', name: 'Detailed' }
])

const roleOptions = computed(() => [
  { title: t('scenarioManager.team.roles.assessor'), value: 'ASSESSOR' },
  { title: t('scenarioManager.team.roles.viewer'), value: 'VIEWER' }
])

// Usernames to exclude from search (already selected + already in team)
const excludedUsernames = computed(() => {
  const selected = selectedUsers.value.map(u => u.username)
  const existing = evaluators.value.map(u => u.username)
  return [...new Set([...selected, ...existing])]
})

// Assessor-type roles (shown in the Assessors tab)
const ASSESSOR_ROLES = ['Assessor', 'Evaluator']

// Computed
const evaluators = computed(() => {
  // Use team data if available (includes invitation_status), otherwise fall back to scenario.users
  let users = []
  if (teamData.value?.team) {
    users = teamData.value.team.filter(u => !u.is_ai)
  } else {
    users = props.scenario?.users?.filter(u => !u.is_llm) || []
  }

  // Filter: show Assessors and Owner. Manager and Viewer (non-owner) belong to Collaboration in Settings.
  users = users.filter(u => ASSESSOR_ROLES.includes(u.role) || isOwner(u))

  // Merge with live stats to get completed/total counts
  // userStatsList contains all human users with their progress
  const userStats = props.liveStats?.userStatsList?.filter(e => !e.isLLM) || []

  return users.map(user => {
    // Find matching stats by user_id, id, or username
    const stats = userStats.find(s =>
      s.id === user.user_id ||
      s.id === user.username ||
      s.name === user.username
    )

    return {
      ...user,
      completed: stats?.completed || 0,
      total: stats?.total || 0
    }
  })
})

const llmEvaluators = computed(() => {
  const evaluators = props.scenario?.llm_evaluators || []
  // Get live stats for LLM evaluators from userStatsList
  const llmLiveStats = props.liveStats?.userStatsList?.filter(e => e.isLLM) || []

  // Transform string model IDs to objects with display info
  return evaluators.map(modelId => {
    // If it's already an object, return as-is
    if (typeof modelId === 'object' && modelId !== null) {
      return modelId
    }

    // Use the central model registry for consistent display names
    const displayName = registryFormatModelName(modelId)

    // Extract model_name and provider from the formatted display name
    let provider = 'Unknown'
    let modelName = displayName
    const parts = displayName.split('/')
    if (parts.length > 1) {
      provider = parts[0]
      modelName = parts.slice(1).join('/')
    }

    // Find matching live stats (name or id contains the model_id for LLMs)
    const liveData = llmLiveStats.find(s =>
      s.name === modelId ||
      s.id === modelId ||
      s.name?.includes(modelName)
    )

    // Determine model status
    const completed = liveData?.completed || 0
    const total = liveData?.total || 0
    const errorCount = liveData?.errorCount || 0
    let status = 'pending'
    if (liveData?.status) {
      status = liveData.status
    } else if (completed >= total && total > 0) {
      status = 'completed'
    } else if (errorCount > 0 && completed + errorCount < total) {
      status = 'stopped'
    } else if (errorCount > 0 && completed + errorCount >= total) {
      status = 'failed'
    } else if (completed > 0) {
      status = 'running'
    }

    return {
      id: modelId,
      model_name: modelName,
      provider: provider,
      completed,
      total,
      errorCount,
      recentErrors: liveData?.recentErrors || [],
      status,
    }
  })
})

// Methods
function isOwner(member) {
  return member.username === props.scenario?.created_by
}

function getRoleVariant(role) {
  const map = {
    'Owner': 'primary',
    'Manager': 'secondary',
    'Assessor': 'info',
    'Evaluator': 'info',
    'Viewer': 'default'
  }
  return map[role] || 'default'
}

function getInvitationVariant(status) {
  const map = {
    'accepted': 'success',
    'rejected': 'danger',
    'pending': 'warning'
  }
  return map[status] || 'default'
}

async function doReinvite(member) {
  reinviting.value = member.user_id
  try {
    await reinviteUser(props.scenario.id, member.user_id)
    // Refresh team data
    await loadTeamData()
    emit('team-updated')
  } finally {
    reinviting.value = null
  }
}

async function loadTeamData() {
  if (props.scenario?.id && props.canManage) {
    try {
      teamData.value = await getScenarioTeam(props.scenario.id)
    } catch (err) {
      console.error('Failed to load team data:', err)
    }
  }
}

function handleUserSelect(user) {
  if (user && !selectedUsers.value.find(u => u.username === user.username)) {
    selectedUsers.value.push(user)
  }
  // Reset the search component
  if (userSearchRef.value) {
    userSearchRef.value.reset()
  }
}

function removeSelectedUser(user) {
  selectedUsers.value = selectedUsers.value.filter(u => u.username !== user.username)
}

async function inviteUsers() {
  inviting.value = true
  try {
    // Extract user IDs from the user objects
    const userIds = selectedUsers.value.map(u => u.id)
    await doInvite(props.scenario.id, userIds, inviteRole.value)
    showInviteDialog.value = false
    selectedUsers.value = []
    // Refresh team data
    await loadTeamData()
    emit('team-updated')
  } finally {
    inviting.value = false
  }
}

function confirmRemoveMember(member) {
  memberToRemove.value = member
  showRemoveDialog.value = true
}

async function removeMember() {
  removing.value = true
  try {
    await removeUser(props.scenario.id, memberToRemove.value.user_id)
    showRemoveDialog.value = false
    memberToRemove.value = null
    // Refresh team data to remove archived user from display
    await loadTeamData()
    emit('team-updated')
  } finally {
    removing.value = false
  }
}

function changeRole(member) {
  memberToChangeRole.value = member
  // Set current role as default, but allow changing to other role
  newRole.value = (member.role === 'Assessor' || member.role === 'Evaluator') ? 'VIEWER' : 'ASSESSOR'
  showRoleDialog.value = true
}

async function confirmRoleChange() {
  if (!memberToChangeRole.value) return

  changingRole.value = true
  try {
    await updateUserRole(props.scenario.id, memberToChangeRole.value.user_id, newRole.value)
    showRoleDialog.value = false
    memberToChangeRole.value = null
    // Refresh team data
    await loadTeamData()
    emit('team-updated')
  } catch (err) {
    console.error('Failed to change role:', err)
  } finally {
    changingRole.value = false
  }
}

async function openErrorDialog(llm) {
  errorDialogModel.value = llm
  errorDetails.value = []
  errorDetailsLoading.value = true
  showErrorDialog.value = true

  try {
    const response = await axios.get(
      `/api/evaluation/llm/${props.scenario.id}/errors`,
      {
        params: { model_id: llm.id },
        headers: { Authorization: `Bearer ${getToken()}` },
      }
    )
    errorDetails.value = response.data.errors || []
  } catch (err) {
    console.error('Failed to load error details:', err)
    errorDetails.value = []
  } finally {
    errorDetailsLoading.value = false
  }
}

async function retryLLM(llm) {
  if (!llm?.id || retryingModel.value) return
  retryingModel.value = llm.id

  try {
    await axios.post(
      `/api/evaluation/llm/${props.scenario.id}/start`,
      { model_id: llm.id },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    )
  } catch (err) {
    console.error('Failed to retry LLM evaluation:', err)
  } finally {
    retryingModel.value = null
  }
}

function formatErrorDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString()
}

function confirmRemoveLLM(llm) {
  // TODO: Implement LLM removal
  console.log('Remove LLM:', llm)
}

async function addLLMEvaluator() {
  addingLLM.value = true
  try {
    // TODO: Implement adding LLM evaluator
    await new Promise(resolve => setTimeout(resolve, 500))
    showAddLLMDialog.value = false
    emit('team-updated')
  } finally {
    addingLLM.value = false
  }
}

// Socket listener for model_aborted events
const onModelAborted = () => {
  emit('refreshStats')
}

onMounted(async () => {
  if (props.scenario?.id) {
    // Load team data with invitation status (only for owners)
    await loadTeamData()

    // Listen for model aborted events to refresh stats
    const socket = getSocket()
    if (socket) {
      socket.on('llm_eval:model_aborted', onModelAborted)
    }
  }
})

onBeforeUnmount(() => {
  const socket = getSocket()
  if (socket) {
    socket.off('llm_eval:model_aborted', onModelAborted)
  }
})
</script>

<style scoped>
.team-tab {
  max-width: 800px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tab-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

/* Team Stats */
.team-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Section */
.section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 16px;
}

.section-header .section-title {
  margin: 0;
}

/* Members List */
.members-list {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.member-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.member-card:last-child {
  border-bottom: none;
}

.member-avatar {
  flex-shrink: 0;
}

.member-avatar.llm {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-accent), 0.1);
  color: rgb(var(--v-theme-accent));
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.member-detail {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.member-stats {
  display: flex;
  gap: 16px;
}

.member-stats .stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.empty-list {
  padding: 32px;
  text-align: center;
}

.empty-list p {
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

/* Rejected member styling */
.member-card.is-rejected {
  background-color: rgba(244, 67, 54, 0.04);
  opacity: 0.8;
}

/* Error styles */
.error-stat {
  cursor: pointer;
  color: #e8a087 !important;
  transition: opacity 0.2s;
}

.error-stat:hover {
  opacity: 0.8;
}

.error-count {
  font-weight: 600;
  color: #e8a087;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.error-item {
  padding: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
}

.error-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.error-item-label {
  font-weight: 500;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

.error-item-date {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.error-item-message {
  font-size: 0.8rem;
  color: #e8a087;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

.member-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
</style>
