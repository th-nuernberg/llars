<template>
  <div class="settings-tab">
    <div class="settings-layout">
      <!-- Settings Section (left/top) -->
      <div class="settings-panel">
        <h3 class="panel-title">
          <LIcon color="primary" class="mr-2" size="20">mdi-cog-outline</LIcon>
          {{ $t('scenarioManager.settings.title') }}
        </h3>

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

            <div class="markdown-field">
              <div class="markdown-field__header">
                <span class="markdown-field__label">{{ $t('scenarioManager.settings.description') }}</span>
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
              </div>
              <LMarkdownEditor
                v-model="formData.description"
                :placeholder="$t('scenarioManager.settings.description')"
                :rows="8"
              />
            </div>
          </div>

          <!-- Briefing -->
          <div class="settings-section">
            <h4 class="section-title">{{ $t('evaluation.briefing.title') }}</h4>

            <div class="markdown-field mb-4">
              <div class="markdown-field__header">
                <div class="markdown-field__label">{{ $t('evaluation.briefing.taskDescription') }}</div>
                <LAIFieldButton
                  field-key="scenario.settings.task_description"
                  :context="buildScenarioAiContext()"
                  icon-only
                  size="small"
                  @generated="updateBriefingTaskDescription($event)"
                />
              </div>
              <LMarkdownEditor
                :model-value="briefingTaskDescription"
                :placeholder="$t('evaluation.briefing.taskDescriptionPlaceholder')"
                :rows="6"
                @update:modelValue="updateBriefingTaskDescription"
              />
            </div>

            <div class="markdown-field">
              <div class="markdown-field__header">
                <div class="markdown-field__label">{{ $t('evaluation.briefing.criteria') }}</div>
                <LAIFieldButton
                  field-key="scenario.settings.evaluation_criteria"
                  :context="buildScenarioAiContext()"
                  icon-only
                  size="small"
                  @generated="updateBriefingCriteria($event)"
                />
              </div>
              <LMarkdownEditor
                :model-value="briefingCriteria"
                :placeholder="briefingCriteriaPlaceholder"
                :rows="8"
                @update:modelValue="updateBriefingCriteria"
              />
            </div>
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

          <!-- Save / Delete actions -->
          <div class="settings-actions">
            <LBtn v-if="isOwner" variant="danger" prepend-icon="mdi-delete-outline" @click="confirmDelete">
              {{ $t('scenarioManager.settings.delete') }}
            </LBtn>
            <v-spacer />
            <LBtn variant="primary" :loading="saving" :disabled="!formValid || !hasChanges" @click="saveSettings">
              {{ $t('common.save') }}
            </LBtn>
          </div>
        </v-form>
      </div>

      <!-- Team Section (right/bottom) -->
      <div class="team-panel">
        <h3 class="panel-title">
          <LIcon color="secondary" class="mr-2" size="20">mdi-account-group-outline</LIcon>
          {{ $t('scenarioManager.settingsTab.teamSection') }}
        </h3>

        <!-- Add collaborator (only for owners) -->
        <div v-if="isOwner" class="team-add-section">
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
              {{ $t('common.add') }}
            </LBtn>
          </div>
        </div>

        <!-- Team Members List -->
        <div class="team-members-list">
          <div
            v-for="member in teamMembers"
            :key="member.user_id"
            class="team-member-card"
          >
            <LAvatar
              :username="member.username"
              :seed="member.avatar_seed"
              :src="member.avatar_url"
              size="sm"
            />
            <div class="member-info">
              <span class="member-name">{{ member.display_name || member.username }}</span>
              <div class="member-tags">
                <!-- Access Level Tag -->
                <LTag
                  :variant="getAccessLevelVariant(member.access_level || member.accessLevel)"
                  size="sm"
                >
                  {{ getAccessLevelLabel(member.access_level || member.accessLevel) }}
                </LTag>
                <!-- Capability Tags from API -->
                <LTag
                  v-for="tag in (member.tags || [])"
                  :key="tag"
                  :variant="getCapabilityTagVariant(tag)"
                  size="sm"
                >
                  {{ $t(`scenarioManager.settingsTab.tags.${tag.toLowerCase()}`) }}
                </LTag>
              </div>
            </div>

            <!-- Flag Toggles (only for non-owner members, only if canManage) -->
            <div v-if="canManage && !isMemberOwner(member)" class="member-flags">
              <LSwitch
                :model-value="member.is_viewer"
                :label="$t('scenarioManager.settingsTab.toggleViewer')"
                :disabled="updatingFlags === member.user_id"
                @change="(val) => toggleFlag(member, 'is_viewer', val)"
              />
              <LSwitch
                :model-value="member.is_assessor"
                :label="$t('scenarioManager.settingsTab.toggleAssessor')"
                :disabled="updatingFlags === member.user_id"
                @change="(val) => toggleFlag(member, 'is_assessor', val)"
              />
            </div>

            <!-- Remove button (only for owners, not on self) -->
            <LIconBtn
              v-if="isOwner && !isMemberOwner(member)"
              icon="mdi-close"
              size="small"
              :tooltip="$t('scenarioManager.settings.removeCollaborator')"
              @click="removeCollaborator(member)"
            />
          </div>

          <div v-if="teamMembers.length === 0" class="team-empty">
            <span>{{ $t('scenarioManager.settings.noCollaborators') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ScenarioSettingsTab - Full settings tab replacing the old settings dialog.
 *
 * Contains two panels:
 * 1. Settings: Name, Description, Briefing, Time Period, Distribution, Order, Status
 * 2. Team: Member list with access-level tags, capability tags, and is_viewer/is_assessor toggles
 *
 * Uses the new PUT /api/scenarios/:id/users/:userId/flags endpoint for toggling capabilities.
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  criteriaListToMarkdown,
  getLocalizedText,
  setLocalizedText
} from '@/utils/scenarioBriefing'
import { useScenarioManager } from '../../composables/useScenarioManager'
import { useSnackbar } from '@/composables/useSnackbar'
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
  },
  canManage: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['saved', 'team-updated'])

const { t, locale } = useI18n()
const {
  updateScenario,
  inviteUsers,
  removeUser,
  getScenarioTeam,
  updateUserFlags
} = useScenarioManager()
const { showSuccess, showError } = useSnackbar()

// Settings form state
const form = ref(null)
const formValid = ref(true)
const saving = ref(false)
const initialFormSnapshot = ref(null)

const formData = ref({
  scenario_name: '',
  description: '',
  ai_generation_prompt: '',
  task_description: '',
  evaluation_criteria: [],
  begin: null,
  end: null,
  status: 'draft',
  config: {
    distribution_mode: 'all',
    order_mode: 'random'
  }
})

// Team state
const collabSearchRef = ref(null)
const collabRole = ref('MANAGER')
const pendingCollabUser = ref(null)
const addingCollab = ref(false)
const teamData = ref(null)
const updatingFlags = ref(null)

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

// Team members: all non-AI users from team data
const teamMembers = computed(() => {
  if (!teamData.value?.team) return []
  return teamData.value.team.filter(u => !u.is_ai)
})

// Exclude existing team members from user search
const excludedCollabUsernames = computed(() => {
  const existing = teamData.value?.team?.map(u => u.username) || []
  const owner = props.scenario?.owner_name ? [props.scenario.owner_name] : []
  return [...new Set([...existing, ...owner])]
})

const isComparisonScenario = computed(() => {
  const typeId = Number(props.scenario?.function_type_id)
  const typeName = String(
    props.scenario?.function_type_name ||
    props.scenario?.function_type ||
    ''
  ).toLowerCase()
  return typeId === 4 || typeName === 'comparison'
})

const briefingEvalConfig = computed(() => {
  const evalConfig = formData.value.config?.eval_config
  if (!evalConfig || typeof evalConfig !== 'object') return null
  return evalConfig.config && typeof evalConfig.config === 'object' ? evalConfig.config : null
})

const briefingTaskDescription = computed(() => {
  return (
    getLocalizedText(briefingEvalConfig.value?.taskDescriptionMarkdown, locale.value) ||
    getLocalizedText(briefingEvalConfig.value?.question, locale.value) ||
    formData.value.task_description
  )
})

const briefingCriteria = computed(() => {
  return (
    getLocalizedText(briefingEvalConfig.value?.criteriaMarkdown, locale.value) ||
    criteriaListToMarkdown(formData.value.evaluation_criteria, locale.value)
  )
})

const briefingCriteriaPlaceholder = computed(() => [
  locale.value === 'en' ? '## What should be evaluated?' : '## Worauf sollte geachtet werden?',
  locale.value === 'en' ? '- Argumentation and traceability' : '- Argumentation und Nachvollziehbarkeit',
  locale.value === 'en' ? '- Factual accuracy' : '- Fachliche Genauigkeit',
  locale.value === 'en' ? '- Style and clarity' : '- Stil und Klarheit'
].join('\n'))

// Track whether form has unsaved changes
const hasChanges = computed(() => {
  if (!initialFormSnapshot.value) return false
  return JSON.stringify(formData.value) !== initialFormSnapshot.value
})

// Validation rules
const rules = {
  required: v => !!v || t('validation.required')
}

// --- Helper functions ---

function getAccessLevelVariant(level) {
  const map = { OWNER: 'primary', MANAGER: 'secondary', MEMBER: 'default' }
  return map[level] || 'default'
}

function getAccessLevelLabel(level) {
  const map = {
    OWNER: t('scenarioManager.settingsTab.tags.owner'),
    MANAGER: t('scenarioManager.settingsTab.tags.manager'),
    MEMBER: t('scenarioManager.settingsTab.tags.member')
  }
  return map[level] || level
}

function getCapabilityTagVariant(tag) {
  const map = { Viewer: 'info', Assessor: 'success' }
  return map[tag] || 'default'
}

function isMemberOwner(member) {
  return member.username === props.scenario?.owner_name ||
         member.access_level === 'OWNER' ||
         member.accessLevel === 'OWNER'
}

// --- Briefing logic (reused from ScenarioSettingsDialog) ---

function normalizeCriteriaList(value) {
  const raw = Array.isArray(value)
    ? value
    : typeof value === 'string'
      ? value.split(/[,\n;]/)
      : []

  const unique = []
  const seen = new Set()

  raw.forEach(entry => {
    const normalized = (typeof entry === 'string' ? entry : String(entry || '')).trim()
    if (!normalized) return
    if (seen.has(normalized)) return
    seen.add(normalized)
    unique.push(normalized)
  })

  return unique
}

function buildScenarioAiContext() {
  const taskDescription = briefingTaskDescription.value || formData.value.task_description || ''
  const criteriaList = criteriaMarkdownToList(briefingCriteria.value)

  return {
    scenario_type: props.scenario?.function_type || '',
    scenario_name: formData.value.scenario_name || '',
    existing_description: formData.value.description || '',
    existing_task_description: taskDescription,
    existing_evaluation_criteria: criteriaList.join(', '),
    generation_prompt: formData.value.ai_generation_prompt || ''
  }
}

function normalizeMarkdownLine(value) {
  return String(value || '')
    .replace(/^#{1,6}\s+/, '')
    .replace(/^[-*+]\s+/, '')
    .replace(/^\d+\.\s+/, '')
    .replace(/[*_~`]/g, '')
    .trim()
}

function criteriaMarkdownToList(markdown) {
  if (!markdown) return []
  return markdown
    .split('\n')
    .map(normalizeMarkdownLine)
    .filter(Boolean)
    .filter((value, index, array) => array.indexOf(value) === index)
}

function parseScenarioConfig(rawConfig) {
  if (!rawConfig) return {}
  if (typeof rawConfig === 'string') {
    try {
      const parsed = JSON.parse(rawConfig)
      return parsed && typeof parsed === 'object' ? parsed : {}
    } catch {
      return {}
    }
  }
  return typeof rawConfig === 'object' ? rawConfig : {}
}

function ensureBriefingFields() {
  if (!formData.value.config || typeof formData.value.config !== 'object') {
    formData.value.config = {}
  }

  if (!formData.value.config.eval_config || typeof formData.value.config.eval_config !== 'object') {
    formData.value.config.eval_config = { config: {} }
  }
  if (!formData.value.config.eval_config.config || typeof formData.value.config.eval_config.config !== 'object') {
    formData.value.config.eval_config.config = {}
  }

  const config = formData.value.config.eval_config.config
  const rootTaskDescription = formData.value.task_description || ''
  const rootCriteria = normalizeCriteriaList(formData.value.evaluation_criteria)

  if (!config.taskDescriptionMarkdown) {
    const fallbackTaskDescription =
      getLocalizedText(config.question, 'de') ||
      getLocalizedText(config.question, 'en') ||
      rootTaskDescription

    config.taskDescriptionMarkdown = {
      de: getLocalizedText(config.taskDescriptionMarkdown, 'de') || fallbackTaskDescription || '',
      en: getLocalizedText(config.taskDescriptionMarkdown, 'en') || fallbackTaskDescription || ''
    }
  }

  if (!config.question && formData.value.config.question) {
    config.question = JSON.parse(JSON.stringify(formData.value.config.question))
  }

  if (isComparisonScenario.value && !config.question) {
    config.question = {
      de: 'Welche Option ist besser?',
      en: 'Which option is better?'
    }
  }

  if (!config.criteriaMarkdown) {
    config.criteriaMarkdown = {
      de:
        getLocalizedText(formData.value.config.criteriaMarkdown, 'de') ||
        getLocalizedText(formData.value.config.evaluation_criteria_markdown, 'de') ||
        criteriaListToMarkdown(rootCriteria, 'de') ||
        criteriaListToMarkdown(config.criteria, 'de'),
      en:
        getLocalizedText(formData.value.config.criteriaMarkdown, 'en') ||
        getLocalizedText(formData.value.config.evaluation_criteria_markdown, 'en') ||
        criteriaListToMarkdown(rootCriteria, 'en') ||
        criteriaListToMarkdown(config.criteria, 'en')
    }
  }
}

function updateBriefingTaskDescription(value) {
  ensureBriefingFields()
  if (!briefingEvalConfig.value) return

  briefingEvalConfig.value.taskDescriptionMarkdown = setLocalizedText(
    briefingEvalConfig.value.taskDescriptionMarkdown,
    value,
    locale.value
  )

  if (isComparisonScenario.value) {
    briefingEvalConfig.value.question = setLocalizedText(
      briefingEvalConfig.value.question,
      value,
      locale.value
    )
  }

  formData.value.task_description = value || ''
}

function updateBriefingCriteria(value) {
  ensureBriefingFields()
  if (!briefingEvalConfig.value) return

  briefingEvalConfig.value.criteriaMarkdown = setLocalizedText(
    briefingEvalConfig.value.criteriaMarkdown,
    value,
    locale.value
  )

  formData.value.evaluation_criteria = criteriaMarkdownToList(value)
}

// --- Team methods ---

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
    emit('team-updated')
  } finally {
    addingCollab.value = false
  }
}

async function removeCollaborator(collab) {
  try {
    await removeUser(props.scenario.id, collab.user_id)
    await loadTeamData()
    emit('team-updated')
  } catch (err) {
    console.error('Failed to remove collaborator:', err)
  }
}

async function toggleFlag(member, flag, value) {
  updatingFlags.value = member.user_id
  try {
    const flags = {
      is_viewer: member.is_viewer,
      is_assessor: member.is_assessor,
      [flag]: value
    }
    await updateUserFlags(props.scenario.id, member.user_id, flags)
    // Refresh team data to get updated tags
    await loadTeamData()
    emit('team-updated')
  } catch (err) {
    console.error('Failed to update user flags:', err)
    showError(t('common.error'))
  } finally {
    updatingFlags.value = null
  }
}

async function loadTeamData() {
  if (props.scenario?.id) {
    try {
      teamData.value = await getScenarioTeam(props.scenario.id)
    } catch (err) {
      console.error('Failed to load team data:', err)
    }
  }
}

// --- Save logic ---

async function saveSettings() {
  if (!form.value?.validate()) return

  saving.value = true
  try {
    const nextTaskDescription = briefingTaskDescription.value || formData.value.task_description || ''
    const nextCriteria = criteriaMarkdownToList(briefingCriteria.value)

    formData.value.task_description = nextTaskDescription
    formData.value.evaluation_criteria = nextCriteria

    const nextConfig = {
      ...(formData.value.config || {}),
      description: formData.value.description,
      distribution_mode: formData.value.config?.distribution_mode || 'all',
      order_mode: formData.value.config?.order_mode || 'random',
      ai_generation_prompt: formData.value.ai_generation_prompt || '',
      task_description: nextTaskDescription,
      evaluation_criteria: nextCriteria
    }

    await updateScenario(props.scenario.id, {
      scenario_name: formData.value.scenario_name,
      description: formData.value.description,
      begin: formData.value.begin,
      end: formData.value.end,
      status: formData.value.status,
      visibility: formData.value.visibility,
      task_description: nextTaskDescription,
      evaluation_criteria: nextCriteria,
      config_json: nextConfig
    })

    // Update snapshot so hasChanges resets
    initialFormSnapshot.value = JSON.stringify(formData.value)
    showSuccess(t('common.success'))
    emit('saved')
  } catch (err) {
    showError(err.response?.data?.error || t('common.error'))
  } finally {
    saving.value = false
  }
}

function confirmDelete() {
  // TODO: Show delete confirmation dialog
  console.log('Delete scenario')
}

// --- Initialize ---

function initializeForm() {
  if (!props.scenario) return

  const config = parseScenarioConfig(props.scenario.config_json)

  if (!config.description && props.scenario.description) {
    config.description = props.scenario.description
  }

  formData.value = {
    scenario_name: props.scenario.scenario_name || '',
    description: props.scenario.description || config.description || '',
    ai_generation_prompt: config.ai_generation_prompt || '',
    task_description: config.task_description || '',
    evaluation_criteria: normalizeCriteriaList(config.evaluation_criteria),
    begin: props.scenario.begin?.split('T')[0] || null,
    end: props.scenario.end?.split('T')[0] || null,
    status: props.scenario.status || 'draft',
    visibility: props.scenario.visibility || 'private',
    config: {
      ...config,
      distribution_mode: config.distribution_mode || 'all',
      order_mode: config.order_mode || 'random'
    }
  }

  ensureBriefingFields()
  // Snapshot for change detection
  initialFormSnapshot.value = JSON.stringify(formData.value)
}

// Re-initialize if scenario changes (e.g. after external save)
watch(() => props.scenario, () => {
  initializeForm()
}, { deep: true })

onMounted(async () => {
  initializeForm()
  await loadTeamData()
})
</script>

<style scoped>
.settings-tab {
  max-width: 1200px;
}

.settings-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
  align-items: start;
}

@media (max-width: 960px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
}

.panel-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 20px;
}

/* Settings Sections */
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

.markdown-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.markdown-field__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.markdown-field__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
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

.settings-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Team Section */
.team-add-section {
  margin-bottom: 16px;
}

.collab-add-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.collab-search {
  flex: 1;
}

.collab-role-select {
  width: 140px;
  flex-shrink: 0;
}

.team-members-list {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.team-member-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.team-member-card:last-child {
  border-bottom: none;
}

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.member-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.member-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.member-flags {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.team-empty {
  text-align: center;
  padding: 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}
</style>
