<template>
  <div class="team-tab">
    <!-- Header -->
    <div class="tab-header">
      <h3>{{ $t('scenarioManager.team.title') }}</h3>
      <LBtn v-if="scenario?.is_owner" variant="primary" @click="showInviteDialog = true">
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
            <LAvatar :user="member" size="40" />
          </div>
          <div class="member-info">
            <span class="member-name">{{ member.display_name || member.username }}</span>
            <div class="member-meta">
              <LTag :variant="getRoleVariant(member.role)" size="sm">
                {{ $t(`scenarioManager.team.roles.${member.role?.toLowerCase() || 'evaluator'}`) }}
              </LTag>
              <!-- Invitation Status Badge -->
              <LTag
                v-if="member.invitation_status && member.invitation_status !== 'accepted' && member.role !== 'OWNER'"
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
          <div class="member-actions" v-if="scenario?.is_owner && member.role !== 'OWNER'">
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
        <LBtn v-if="scenario?.is_owner" variant="secondary" size="small" @click="showAddLLMDialog = true">
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
            <span class="member-detail">{{ llm.provider }}</span>
          </div>
          <div class="member-stats">
            <span class="stat">
              <LIcon size="16">mdi-check-circle-outline</LIcon>
              {{ llm.completed || 0 }} / {{ llm.total || 0 }}
            </span>
            <span class="stat" v-if="llm.cost">
              <LIcon size="16">mdi-currency-usd</LIcon>
              {{ llm.cost.toFixed(4) }}
            </span>
          </div>
          <div class="member-actions" v-if="scenario?.is_owner">
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
          <v-autocomplete
            v-model="selectedUsers"
            :items="availableUsers"
            :loading="loadingUsers"
            :label="$t('scenarioManager.team.selectUsers')"
            item-title="display_name"
            item-value="id"
            multiple
            chips
            closable-chips
            variant="outlined"
            @update:search="searchUsers"
          >
            <template #chip="{ props, item }">
              <v-chip v-bind="props" :text="item.raw.display_name || item.raw.username" />
            </template>
          </v-autocomplete>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScenarioManager } from '../../composables/useScenarioManager'
import LAvatar from '@/components/common/LAvatar.vue'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['team-updated'])

const { t } = useI18n()
const {
  inviteUsers: doInvite,
  removeUser,
  getAvailableUsers,
  reinviteUser,
  getScenarioTeam
} = useScenarioManager()

// State
const showInviteDialog = ref(false)
const reinviting = ref(null)
const teamData = ref(null)
const showAddLLMDialog = ref(false)
const showRemoveDialog = ref(false)
const selectedUsers = ref([])
const inviteRole = ref('EVALUATOR')
const inviting = ref(false)
const loadingUsers = ref(false)
const availableUsers = ref([])
const memberToRemove = ref(null)
const removing = ref(false)

const selectedLLM = ref(null)
const selectedTemplate = ref(null)
const addingLLM = ref(false)

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
  { title: t('scenarioManager.team.roles.evaluator'), value: 'EVALUATOR' },
  { title: t('scenarioManager.team.roles.rater'), value: 'RATER' }
])

// Computed
const evaluators = computed(() => {
  // Use team data if available (includes invitation_status), otherwise fall back to scenario.users
  if (teamData.value?.team) {
    return teamData.value.team.filter(u => !u.is_ai)
  }
  return props.scenario?.users?.filter(u => !u.is_llm) || []
})

const llmEvaluators = computed(() => {
  return props.scenario?.llm_evaluators || []
})

// Methods
function getRoleVariant(role) {
  const map = {
    'OWNER': 'primary',
    'RATER': 'info',
    'EVALUATOR': 'default'
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
  if (props.scenario?.id && props.scenario?.is_owner) {
    try {
      teamData.value = await getScenarioTeam(props.scenario.id)
    } catch (err) {
      console.error('Failed to load team data:', err)
    }
  }
}

async function searchUsers(query) {
  if (!query || query.length < 2) return
  loadingUsers.value = true
  try {
    availableUsers.value = await getAvailableUsers(props.scenario.id)
  } finally {
    loadingUsers.value = false
  }
}

async function inviteUsers() {
  inviting.value = true
  try {
    await doInvite(props.scenario.id, selectedUsers.value, inviteRole.value)
    showInviteDialog.value = false
    selectedUsers.value = []
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
    emit('team-updated')
  } finally {
    removing.value = false
  }
}

function changeRole(member) {
  // TODO: Implement role change
  console.log('Change role:', member)
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

onMounted(async () => {
  if (props.scenario?.id) {
    // Load available users for invite dialog
    availableUsers.value = await getAvailableUsers(props.scenario.id)
    // Load team data with invitation status (only for owners)
    await loadTeamData()
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

.member-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
</style>
