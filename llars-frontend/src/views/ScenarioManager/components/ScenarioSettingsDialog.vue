<template>
  <v-card class="settings-dialog">
    <v-card-title class="d-flex align-center">
      <LIcon color="primary" class="mr-2">mdi-cog-outline</LIcon>
      {{ $t('scenarioManager.settings.title') }}
      <v-spacer />
      <LIconBtn icon="mdi-close" @click="$emit('close')" />
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-model="formValid">
        <!-- Basic Info -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.basicInfo') }}</h4>

          <v-text-field
            v-model="formData.scenario_name"
            :label="$t('scenarioManager.settings.name')"
            :rules="[rules.required]"
            variant="outlined"
            class="mb-4"
          >
            <template #append-inner>
              <LAIFieldButton
                field-key="scenario.settings.name"
                :context="{
                  scenario_type: scenario.function_type,
                  existing_description: formData.description,
                  existing_name: formData.scenario_name
                }"
                icon-only
                size="small"
                @generated="formData.scenario_name = $event"
              />
            </template>
          </v-text-field>

          <v-textarea
            v-model="formData.description"
            :label="$t('scenarioManager.settings.description')"
            variant="outlined"
            rows="3"
            class="mb-4"
          >
            <template #append-inner>
              <LAIFieldButton
                field-key="scenario.settings.description"
                :context="{
                  scenario_type: scenario.function_type,
                  scenario_name: formData.scenario_name,
                  existing_description: formData.description
                }"
                icon-only
                size="small"
                @generated="formData.description = $event"
              />
            </template>
          </v-textarea>
        </div>

        <!-- Time Period -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.timePeriod') }}</h4>

          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="formData.begin"
                :label="$t('scenarioManager.settings.startDate')"
                type="date"
                variant="outlined"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="formData.end"
                :label="$t('scenarioManager.settings.endDate')"
                type="date"
                variant="outlined"
              />
            </v-col>
          </v-row>
        </div>

        <!-- Distribution Settings -->
        <div class="settings-section">
          <h4 class="section-title">
            {{ $t('scenarioManager.settings.distribution') }}
            <LTooltip :text="$t('scenarioManager.settings.distributionTooltip')" location="right">
              <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
            </LTooltip>
          </h4>

          <div class="l-radio-list">
            <LRadio
              v-model="formData.config.distribution_mode"
              value="all"
              name="distribution"
            >
              <div class="radio-label">
                <span class="radio-title">{{ $t('scenarioManager.settings.distributionAll') }}</span>
                <span class="radio-desc">{{ $t('scenarioManager.settings.distributionAllDesc') }}</span>
              </div>
            </LRadio>
            <LRadio
              v-model="formData.config.distribution_mode"
              value="random"
              name="distribution"
            >
              <div class="radio-label">
                <span class="radio-title">{{ $t('scenarioManager.settings.distributionRandom') }}</span>
                <span class="radio-desc">{{ $t('scenarioManager.settings.distributionRandomDesc') }}</span>
              </div>
            </LRadio>
            <LRadio
              v-model="formData.config.distribution_mode"
              value="sequential"
              name="distribution"
            >
              <div class="radio-label">
                <span class="radio-title">{{ $t('scenarioManager.settings.distributionSequential') }}</span>
                <span class="radio-desc">{{ $t('scenarioManager.settings.distributionSequentialDesc') }}</span>
              </div>
            </LRadio>
          </div>
        </div>

        <!-- Order Settings -->
        <div class="settings-section">
          <h4 class="section-title">
            {{ $t('scenarioManager.settings.order') }}
            <LTooltip :text="$t('scenarioManager.settings.orderTooltip')" location="right">
              <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
            </LTooltip>
          </h4>

          <LRadioGroup
            v-model="formData.config.order_mode"
            :options="orderOptions"
          />
        </div>

        <!-- Collaboration (replaces Visibility) -->
        <div class="settings-section" v-if="isOwner">
          <h4 class="section-title">
            {{ $t('scenarioManager.settings.collaboration') }}
            <LTooltip :text="$t('scenarioManager.settings.collaborationTooltip')" location="right">
              <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
            </LTooltip>
          </h4>

          <!-- Add collaborator -->
          <div class="collab-add-row">
            <div class="collab-search">
              <LUserSearch
                ref="collabSearchRef"
                :exclude-usernames="excludedCollabUsernames"
                :placeholder="$t('scenarioManager.settings.addCollaborator')"
                @select="handleCollabUserSelect"
              />
            </div>
            <v-select
              v-model="collabRole"
              :items="collabRoleOptions"
              variant="outlined"
              density="compact"
              hide-details
              class="collab-role-select"
            />
            <LBtn
              variant="primary"
              size="small"
              :disabled="!pendingCollabUser"
              :loading="addingCollab"
              @click="addCollaborator"
            >
              <LIcon start size="16">mdi-plus</LIcon>
              {{ $t('scenarioManager.settings.addCollaborator') }}
            </LBtn>
          </div>

          <!-- Collaborators list -->
          <div class="collab-list" v-if="collaborators.length > 0">
            <div
              v-for="collab in collaborators"
              :key="collab.user_id"
              class="collab-item"
            >
              <LAvatar
                :username="collab.username"
                :seed="collab.avatar_seed"
                :src="collab.avatar_url"
                size="sm"
              />
              <div class="collab-info">
                <span class="collab-name">{{ collab.display_name || collab.username }}</span>
                <LTag :variant="collab.role === 'Manager' ? 'secondary' : 'default'" size="sm">
                  {{ $t(`scenarioManager.team.roles.${collab.role.toLowerCase()}`) }}
                </LTag>
              </div>
              <LIconBtn
                icon="mdi-close"
                size="small"
                :tooltip="$t('scenarioManager.settings.removeCollaborator')"
                @click="removeCollaborator(collab)"
              />
            </div>
          </div>
          <div v-else class="collab-empty">
            <span>{{ $t('scenarioManager.settings.noCollaborators') }}</span>
          </div>
        </div>

        <!-- Status -->
        <div class="settings-section">
          <h4 class="section-title">{{ $t('scenarioManager.settings.status') }}</h4>

          <v-select
            v-model="formData.status"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            variant="outlined"
          />
        </div>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <LBtn v-if="isOwner" variant="danger" prepend-icon="mdi-delete-outline" @click="confirmDelete">
        {{ $t('scenarioManager.settings.delete') }}
      </LBtn>
      <v-spacer />
      <LBtn variant="cancel" @click="$emit('close')">
        {{ $t('common.cancel') }}
      </LBtn>
      <LBtn variant="primary" :loading="saving" :disabled="!formValid" @click="saveSettings">
        {{ $t('common.save') }}
      </LBtn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScenarioManager } from '../composables/useScenarioManager'
import LAvatar from '@/components/common/LAvatar.vue'
import LUserSearch from '@/components/common/LUserSearch.vue'

const props = defineProps({
  scenario: {
    type: Object,
    required: true
  },
  isOwner: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'saved'])

const { t } = useI18n()
const { updateScenario, inviteUsers, removeUser, getScenarioTeam } = useScenarioManager()

// State
const form = ref(null)
const formValid = ref(true)
const saving = ref(false)

const formData = ref({
  scenario_name: '',
  description: '',
  begin: null,
  end: null,
  status: 'draft',
  config: {
    distribution_mode: 'all',
    order_mode: 'random'
  }
})

// Collaboration state
const collabSearchRef = ref(null)
const collabRole = ref('MANAGER')
const pendingCollabUser = ref(null)
const addingCollab = ref(false)
const teamData = ref(null)

// Options
const orderOptions = computed(() => [
  { value: 'fixed', label: t('scenarioManager.settings.orderFixed') },
  { value: 'random', label: t('scenarioManager.settings.orderRandom') }
])

const collabRoleOptions = computed(() => [
  { title: t('scenarioManager.settings.roleManager'), value: 'MANAGER' },
  { title: t('scenarioManager.settings.roleViewer'), value: 'VIEWER' }
])

const statusOptions = computed(() => [
  { value: 'draft', label: t('scenarioManager.status.draft') },
  { value: 'data_collection', label: t('scenarioManager.status.dataCollection') },
  { value: 'evaluating', label: t('scenarioManager.status.evaluating') },
  { value: 'completed', label: t('scenarioManager.status.completed') },
  { value: 'archived', label: t('scenarioManager.status.archived') }
])

// Collaborators: Manager + Viewer users from team data
const collaborators = computed(() => {
  if (!teamData.value?.team) return []
  return teamData.value.team.filter(u =>
    (u.role === 'Manager' || u.role === 'Viewer') && u.username !== props.scenario?.created_by
  )
})

// Exclude existing collaborators + assessors from the search
const excludedCollabUsernames = computed(() => {
  const existing = teamData.value?.team?.map(u => u.username) || []
  const owner = props.scenario?.owner_name ? [props.scenario.owner_name] : []
  return [...new Set([...existing, ...owner])]
})

// Validation rules
const rules = {
  required: v => !!v || t('validation.required')
}

// Methods
function handleCollabUserSelect(user) {
  pendingCollabUser.value = user
}

async function addCollaborator() {
  if (!pendingCollabUser.value) return
  addingCollab.value = true
  try {
    await inviteUsers(props.scenario.id, [pendingCollabUser.value.id], collabRole.value)
    pendingCollabUser.value = null
    if (collabSearchRef.value) collabSearchRef.value.reset()
    await loadTeamData()
  } finally {
    addingCollab.value = false
  }
}

async function removeCollaborator(collab) {
  try {
    await removeUser(props.scenario.id, collab.user_id)
    await loadTeamData()
  } catch (err) {
    console.error('Failed to remove collaborator:', err)
  }
}

async function loadTeamData() {
  if (props.scenario?.id && props.isOwner) {
    try {
      teamData.value = await getScenarioTeam(props.scenario.id)
    } catch (err) {
      console.error('Failed to load team data:', err)
    }
  }
}

async function saveSettings() {
  if (!form.value?.validate()) return

  saving.value = true
  try {
    await updateScenario(props.scenario.id, {
      scenario_name: formData.value.scenario_name,
      description: formData.value.description,
      begin: formData.value.begin,
      end: formData.value.end,
      status: formData.value.status,
      config_json: formData.value.config
    })
    emit('saved')
  } finally {
    saving.value = false
  }
}

function confirmDelete() {
  // TODO: Show delete confirmation dialog
  console.log('Delete scenario')
}

onMounted(async () => {
  // Initialize form with scenario data
  if (props.scenario) {
    formData.value = {
      scenario_name: props.scenario.scenario_name || '',
      description: props.scenario.description || '',
      begin: props.scenario.begin?.split('T')[0] || null,
      end: props.scenario.end?.split('T')[0] || null,
      status: props.scenario.status || 'draft',
      config: {
        distribution_mode: props.scenario.config_json?.distribution_mode || 'all',
        order_mode: props.scenario.config_json?.order_mode || 'random'
      }
    }
  }
  // Load team data for collaboration section
  await loadTeamData()
})
</script>

<style scoped>
.settings-dialog {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.settings-dialog .v-card-text {
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-help-icon {
  opacity: 0.45;
  cursor: help;
  transition: opacity 0.2s ease;
}

.section-help-icon:hover {
  opacity: 0.8;
}

.l-radio-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-label {
  display: flex;
  flex-direction: column;
}

.radio-title {
  font-weight: 500;
}

.radio-desc {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Collaboration section */
.collab-add-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.collab-search {
  flex: 1;
}

.collab-role-select {
  width: 140px;
  flex-shrink: 0;
}

.collab-list {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.collab-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.collab-item:last-child {
  border-bottom: none;
}

.collab-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.collab-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.collab-empty {
  text-align: center;
  padding: 16px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}
</style>
