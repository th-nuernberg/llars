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
            <div class="section-toggle" @click="toggleSection('basicInfo')">
              <h4 class="section-title">{{ $t('scenarioManager.settings.basicInfo') }}</h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.basicInfo }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.basicInfo" class="section-body">
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
          </div>

          <!-- Aufgabe (Task description + Evaluation criteria) -->
          <div class="settings-section">
            <div class="section-toggle" @click="toggleSection('task')">
              <h4 class="section-title">{{ $t('evaluation.briefing.title') }}</h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.task }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.task" class="section-body">
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

              <!-- Per-Item-Header (comparison scenarios only) -->
              <div v-if="isComparisonScenario" class="markdown-field mt-4">
                <div class="markdown-field__header">
                  <div class="markdown-field__label">{{ $t('scenarioManager.evalConfig.comparison.itemHeaderTemplate', 'Per-Item-Header') }}</div>
                </div>
                <p class="markdown-field__hint">{{ itemHeaderTemplateHint }}</p>
                <LMarkdownEditor
                  ref="itemHeaderEditorRef"
                  :model-value="briefingItemHeaderTemplate"
                  :placeholder="itemHeaderPlaceholder"
                  :rows="4"
                  @update:modelValue="updateBriefingItemHeaderTemplate"
                />
              </div>
            </div>
          </div>

          <!-- Time Period -->
          <div class="settings-section">
            <div class="section-toggle" @click="toggleSection('timePeriod')">
              <h4 class="section-title">{{ $t('scenarioManager.settings.timePeriod') }}</h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.timePeriod }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.timePeriod" class="section-body">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="formData.begin"
                    :label="$t('scenarioManager.settings.startDate')"
                    type="date"
                    variant="outlined"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="formData.end"
                    :label="$t('scenarioManager.settings.endDate')"
                    type="date"
                    variant="outlined"
                  />
                </v-col>
              </v-row>
            </div>
          </div>

          <!-- Distribution Settings -->
          <div class="settings-section">
            <div class="section-toggle" @click="toggleSection('distribution')">
              <h4 class="section-title">
                {{ $t('scenarioManager.settings.distribution') }}
                <LTooltip :text="$t('scenarioManager.settings.distributionTooltip')" location="right">
                  <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
                </LTooltip>
              </h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.distribution }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.distribution" class="section-body">
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
          </div>

          <!-- Order Settings -->
          <div class="settings-section">
            <div class="section-toggle" @click="toggleSection('order')">
              <h4 class="section-title">
                {{ $t('scenarioManager.settings.order') }}
                <LTooltip :text="$t('scenarioManager.settings.orderTooltip')" location="right">
                  <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
                </LTooltip>
              </h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.order }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.order" class="section-body">
              <LRadioGroup
                v-model="formData.config.order_mode"
                :options="orderOptions"
              />
            </div>
          </div>

          <!-- Co-Pilot (labeling only): owner can toggle/edit AFTER creation.
               Prompt/codebook edits bump the prompt version server-side on
               save; regeneration is an explicit button (cost control). -->
          <div v-if="isLabelingScenario" class="settings-section">
            <div class="section-toggle" @click="toggleSection('copilot')">
              <h4 class="section-title">
                {{ $t('scenarioManager.evalConfig.labeling.copilot.title') }}
              </h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.copilot }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.copilot" class="section-body">
              <LSwitch
                v-model="copilotForm.enabled"
                :label="$t('scenarioManager.evalConfig.labeling.copilot.enable')"
                @update:modelValue="syncCopilotIntoConfig"
              />
              <template v-if="copilotForm.enabled">
                <LlmModelSelect
                  v-model="copilotForm.model_id"
                  :label="$t('scenarioManager.evalConfig.labeling.copilot.model')"
                  class="mt-3"
                  @update:modelValue="syncCopilotIntoConfig"
                />
                <v-select
                  v-model="copilotForm.top_k"
                  :items="copilotTopKOptions"
                  :label="$t('scenarioManager.evalConfig.labeling.copilot.topK')"
                  variant="outlined"
                  density="compact"
                  class="mt-2"
                  @update:modelValue="syncCopilotIntoConfig"
                />
                <v-textarea
                  v-model="copilotForm.prompt"
                  :label="$t('scenarioManager.evalConfig.labeling.copilot.prompt')"
                  variant="outlined"
                  density="compact"
                  rows="6"
                  auto-grow
                  class="mt-2 copilot-prompt-textarea"
                  @update:modelValue="syncCopilotIntoConfig"
                />
                <v-textarea
                  v-model="copilotForm.codebook"
                  :label="$t('scenarioManager.evalConfig.labeling.copilot.codebook')"
                  variant="outlined"
                  density="compact"
                  rows="3"
                  auto-grow
                  class="mt-2"
                  @update:modelValue="syncCopilotIntoConfig"
                />
                <div class="mt-1">
                  <span class="copilot-field-label">
                    {{ $t('scenarioManager.evalConfig.labeling.copilot.hiddenControl') }}:
                    {{ Math.round((copilotForm.hidden_control_ratio || 0) * 100) }}%
                  </span>
                  <v-slider
                    v-model="copilotForm.hidden_control_ratio"
                    :min="0"
                    :max="0.3"
                    :step="0.05"
                    density="compact"
                    hide-details
                    color="primary"
                    @update:modelValue="syncCopilotIntoConfig"
                  />
                </div>
                <p class="copilot-hint">{{ $t('scenarioManager.evalConfig.labeling.copilot.promptHint') }}</p>

                <div class="copilot-status-row">
                  <LTag v-if="copilotStatus?.running" variant="info" size="small">
                    {{ $t('scenarioManager.settings.copilotRunning') }}
                  </LTag>
                  <LTag v-else-if="copilotStatus?.enabled" variant="default" size="small">
                    {{ $t('scenarioManager.settings.copilotStatusText', {
                      completed: copilotStatus.completed,
                      total: copilotStatus.total_items,
                      stale: copilotStatus.stale,
                      errors: copilotStatus.errors,
                      version: copilotStatus.prompt_version
                    }) }}
                  </LTag>
                  <v-spacer />
                  <LBtn
                    size="small"
                    variant="secondary"
                    :loading="copilotStarting"
                    :disabled="hasChanges"
                    @click="startCopilotGeneration"
                  >
                    {{ $t('scenarioManager.settings.copilotRegenerate') }}
                  </LBtn>
                </div>
                <p v-if="hasChanges" class="copilot-hint">
                  {{ $t('scenarioManager.settings.copilotSaveFirst') }}
                </p>
              </template>
            </div>
          </div>

          <!-- Parts / Phases (labeling only, owner view): per-part progress,
               lock/unlock (the study gate between calibration phases) and
               per-part co-pilot toggle. Assessors never see this structure. -->
          <div v-if="isLabelingScenario && partsStatus?.enabled" class="settings-section">
            <div class="section-toggle" @click="toggleSection('parts')">
              <h4 class="section-title">
                {{ $t('scenarioManager.evalConfig.labeling.parts.title') }}
                <LTooltip :text="$t('scenarioManager.evalConfig.labeling.parts.settingsTooltip')" location="right">
                  <LIcon size="16" class="section-help-icon">mdi-help-circle-outline</LIcon>
                </LTooltip>
              </h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.parts }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.parts" class="section-body">
              <div
                v-for="part in partsStatus.parts"
                :key="part.id"
                class="part-card"
              >
                <div class="part-card-head">
                  <span class="part-card-name">{{ part.name }}</span>
                  <LTag size="small" variant="default">
                    {{ part.item_count }} {{ $t('scenarioManager.evalConfig.labeling.parts.items') }}
                  </LTag>
                  <LTag v-if="part.order === 'random'" size="small" variant="info">
                    {{ $t('scenarioManager.evalConfig.labeling.parts.orderRandom') }}
                  </LTag>
                  <LTag v-if="part.copilot" size="small" variant="info">
                    <LIcon size="12" class="mr-1">mdi-robot-outline</LIcon>
                    {{ $t('scenarioManager.evalConfig.labeling.copilot.title') }}
                  </LTag>
                  <LTag :variant="part.locked ? 'warning' : 'success'" size="small">
                    <LIcon size="12" class="mr-1">
                      {{ part.locked ? 'mdi-lock-outline' : 'mdi-lock-open-variant-outline' }}
                    </LIcon>
                    {{ part.locked
                      ? $t('scenarioManager.evalConfig.labeling.parts.locked')
                      : $t('scenarioManager.evalConfig.labeling.parts.open') }}
                  </LTag>
                </div>

                <div v-if="part.assessors?.length" class="part-card-progress">
                  <div
                    v-for="assessor in part.assessors"
                    :key="assessor.user_id"
                    class="part-progress-row"
                  >
                    <span class="part-progress-name">{{ assessor.username }}</span>
                    <span class="part-progress-count">{{ assessor.labeled }}/{{ assessor.total }}</span>
                    <v-progress-linear
                      :model-value="assessor.total ? (assessor.labeled / assessor.total) * 100 : 0"
                      color="primary"
                      height="6"
                      rounded
                    />
                  </div>
                </div>

                <div class="part-card-actions">
                  <LSwitch
                    v-if="copilotForm.enabled"
                    :model-value="part.copilot"
                    :label="$t('scenarioManager.evalConfig.labeling.parts.copilotSwitch')"
                    :disabled="partsUpdating === part.id"
                    @update:modelValue="value => updatePartField(part, 'copilot', value)"
                  />
                  <v-spacer />
                  <LBtn
                    size="small"
                    :variant="part.locked ? 'primary' : 'secondary'"
                    :loading="partsUpdating === part.id"
                    @click="updatePartField(part, 'locked', !part.locked)"
                  >
                    <LIcon size="16" class="mr-1">
                      {{ part.locked ? 'mdi-lock-open-variant-outline' : 'mdi-lock-outline' }}
                    </LIcon>
                    {{ part.locked
                      ? $t('scenarioManager.evalConfig.labeling.parts.unlock')
                      : $t('scenarioManager.evalConfig.labeling.parts.lock') }}
                  </LBtn>
                </div>
              </div>
            </div>
          </div>

          <!-- Status -->
          <div class="settings-section">
            <div class="section-toggle" @click="toggleSection('status')">
              <h4 class="section-title">{{ $t('scenarioManager.settings.status') }}</h4>
              <LIcon class="section-chevron" :class="{ 'is-open': sectionsOpen.status }" size="18">mdi-chevron-down</LIcon>
            </div>

            <div v-show="sectionsOpen.status" class="section-body">
              <v-select
                v-model="formData.status"
                :items="statusOptions"
                item-title="label"
                item-value="value"
                variant="outlined"
              />
            </div>
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

        <!-- Origin legend: associate each referral-link color with its source. -->
        <LOriginLegend :origins="teamOrigins" style="margin-bottom: 12px;" />

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
                <!-- Origin pill: where this member came from -->
                <LUserOrigin :origin="member.origin" size="sm" />
              </div>
            </div>

            <!-- Flag Toggles. Reads is_viewer/is_assessor (derived from
                 manager_role/evaluation_role on backend). For the scenario
                 owner: viewer is locked on (owners always have view access)
                 and only the assessor switch is editable. -->
            <div v-if="canManage" class="member-flags">
              <LSwitch
                :model-value="isMemberOwner(member)
                  ? true
                  : (member.is_viewer ?? (member.manager_role && member.manager_role !== 'none'))"
                :label="$t('scenarioManager.settingsTab.toggleViewer')"
                :disabled="isMemberOwner(member) || updatingFlags === member.user_id"
                @change="(val) => toggleFlag(member, 'is_viewer', val)"
              />
              <LSwitch
                :model-value="member.is_assessor ?? (member.evaluation_role === 'assessor')"
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
 * 2. Team: Member list with capability toggles (is_viewer/is_assessor synced to
 *    manager_role/evaluation_role on the backend)
 *
 * Uses the PUT /api/scenarios/:id/users/:userId/flags endpoint for toggling capabilities.
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
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'
import axios from 'axios'

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

// Collapsible section state — Basic Info and Task open by default
const sectionsOpen = ref({
  basicInfo: true,
  task: true,
  timePeriod: false,
  distribution: false,
  order: false,
  copilot: false,
  parts: false,
  status: false
})

function toggleSection(key) {
  sectionsOpen.value[key] = !sectionsOpen.value[key]
}

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
  { title: t('scenarioManager.settings.roleEditor'), value: 'MANAGER' },
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

// Origin objects for the legend (referral-link color -> source label).
const teamOrigins = computed(() => teamMembers.value.map(m => m.origin).filter(Boolean))

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

const isLabelingScenario = computed(() => {
  const typeId = Number(props.scenario?.function_type_id)
  const typeName = String(
    props.scenario?.function_type_name ||
    props.scenario?.function_type ||
    ''
  ).toLowerCase()
  return typeId === 7 || typeName === 'labeling'
})

// --- Co-Pilot (labeling): owner-facing post-creation editing ---
// The form mirrors config_json.eval_config.config.copilot; syncCopilotIntoConfig
// writes edits back into formData.config so the regular saveSettings PUT
// persists them. Prompt versioning + salt handling happen SERVER-side
// (LabelingCopilotService.normalize_config_on_write) on save.
const copilotForm = ref({
  enabled: false,
  model_id: null,
  prompt: '',
  codebook: '',
  top_k: 1,
  hidden_control_ratio: 0.15
})
const copilotStatus = ref(null)
const copilotStarting = ref(false)

const copilotTopKOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.labeling.copilot.topKOptions.one'), value: 1 },
  { title: t('scenarioManager.evalConfig.labeling.copilot.topKOptions.two'), value: 2 }
])

function locateCopilotConfig(config) {
  if (!config || typeof config !== 'object') return null
  return (
    config.eval_config?.config?.copilot ||
    config.config?.copilot ||
    config.copilot ||
    null
  )
}

function initCopilotForm(config) {
  const copilot = locateCopilotConfig(config)
  copilotForm.value = {
    enabled: Boolean(copilot?.enabled),
    model_id: copilot?.model_id || null,
    prompt: copilot?.prompt || '',
    codebook: copilot?.codebook || '',
    top_k: copilot?.top_k === 2 ? 2 : 1,
    hidden_control_ratio: typeof copilot?.hidden_control_ratio === 'number'
      ? copilot.hidden_control_ratio
      : 0.15
  }
}

function syncCopilotIntoConfig() {
  const config = formData.value.config
  if (!config || typeof config !== 'object') return
  if (!config.eval_config || typeof config.eval_config !== 'object') {
    config.eval_config = { config: {} }
  }
  if (!config.eval_config.config || typeof config.eval_config.config !== 'object') {
    config.eval_config.config = {}
  }
  // Preserve server-managed fields (prompt_version, history, salt) — the
  // form only owns the user-editable subset.
  const existing = locateCopilotConfig(config) || {}
  const merged = { ...existing, ...copilotForm.value }
  config.eval_config.config.copilot = merged
  // v1-created scenarios duplicate the inner config at config.config —
  // mirror so the two copies can't drift apart.
  if (config.config && typeof config.config === 'object') {
    config.config.copilot = merged
  }
}

async function loadCopilotStatus() {
  if (!isLabelingScenario.value || !props.scenario?.id) return
  try {
    const response = await axios.get(`/api/evaluation/llm/${props.scenario.id}/copilot/status`)
    copilotStatus.value = response.data
  } catch (err) {
    console.error('Failed to load copilot status:', err)
  }
}

async function startCopilotGeneration() {
  copilotStarting.value = true
  try {
    await axios.post(`/api/evaluation/llm/${props.scenario.id}/copilot/start`)
    showSuccess(t('scenarioManager.settings.copilotQueued'))
    await loadCopilotStatus()
  } catch (err) {
    showError(err.response?.data?.error || t('common.error'))
  } finally {
    copilotStarting.value = false
  }
}

// --- Parts / Phases (labeling): owner-facing phase management ---
// Status comes from the owner-only endpoint (per-part progress); lock/unlock
// and per-part copilot go through the dedicated PUT (server validates the
// editable field set) instead of the generic config save — the partition
// itself (item_ids) is server-authoritative and never editable here.
const partsStatus = ref(null)
const partsUpdating = ref(null)

async function loadPartsStatus() {
  if (!isLabelingScenario.value || !props.scenario?.id || !props.canManage) return
  try {
    const response = await axios.get(`/api/scenarios/${props.scenario.id}/parts`)
    partsStatus.value = response.data
  } catch (err) {
    console.error('Failed to load parts status:', err)
  }
}

async function updatePartField(part, field, value) {
  partsUpdating.value = part.id
  try {
    const response = await axios.put(
      `/api/scenarios/${props.scenario.id}/parts/${part.id}`,
      { [field]: value }
    )
    partsStatus.value = response.data
    showSuccess(t('scenarioManager.evalConfig.labeling.parts.updated'))
    if (field === 'copilot' && value) {
      // Newly copilot-enabled part: suggestions for its items may be missing —
      // remind via status refresh; generation stays an explicit button.
      await loadCopilotStatus()
    }
  } catch (err) {
    showError(err.response?.data?.error || t('common.error'))
  } finally {
    partsUpdating.value = null
  }
}

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

const itemHeaderEditorRef = ref(null)

const briefingItemHeaderTemplate = computed(() =>
  getLocalizedText(briefingEvalConfig.value?.itemHeaderTemplate, locale.value) || ''
)

// Defined in script to avoid Vue template compiler mis-parsing {{variable}} as interpolation.
const itemHeaderTemplateHint = computed(() =>
  t(
    'scenarioManager.evalConfig.comparison.itemHeaderTemplateHint',
    'Wird pro Item über dem Gesprächsverlauf angezeigt. Platzhalter {{variable}} werden durch Item-Metadaten ersetzt.'
  )
)

const itemHeaderPlaceholder = computed(() =>
  locale.value === 'en'
    ? '**{{persona_name}}** — Target style: {{target_style}} (Axis: {{axis}})\n\nCase: {{hauptanliegen}}'
    : '**{{persona_name}}** — Zielstil: {{target_style}} (Achse: {{axis}})\n\nHauptanliegen: {{hauptanliegen}}'
)

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
  const map = {
    OWNER: 'primary',
    MANAGER: 'secondary',
    EDITOR: 'secondary',
    MEMBER: 'default'
  }
  return map[level] || 'default'
}

function getAccessLevelLabel(level) {
  const map = {
    OWNER: t('scenarioManager.settingsTab.tags.owner'),
    MANAGER: t('scenarioManager.settingsTab.tags.editor'),
    EDITOR: t('scenarioManager.settingsTab.tags.editor'),
    MEMBER: t('scenarioManager.settingsTab.tags.member')
  }
  return map[level] || level
}

function getCapabilityTagVariant(tag) {
  const map = {
    Owner: 'primary',
    Editor: 'secondary',
    Viewer: 'info',
    Assessor: 'success',
    'Eval. Viewer': 'info'
  }
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

function updateBriefingItemHeaderTemplate(value) {
  ensureBriefingFields()
  if (!briefingEvalConfig.value) return

  if (!briefingEvalConfig.value.itemHeaderTemplate) {
    briefingEvalConfig.value.itemHeaderTemplate = { de: '', en: '' }
  }
  briefingEvalConfig.value.itemHeaderTemplate = setLocalizedText(
    briefingEvalConfig.value.itemHeaderTemplate,
    value,
    locale.value
  )
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
    // Build the effective flag state after the toggle
    const effectiveViewer = flag === 'is_viewer' ? value : member.is_viewer
    const effectiveAssessor = flag === 'is_assessor' ? value : member.is_assessor

    // For the owner row we MUST NOT send is_viewer/manager_role — the backend
    // would otherwise overwrite manager_role='owner' with 'viewer' or 'none',
    // demoting the owner. Only the assessor flag is editable for owners.
    const flags = isMemberOwner(member)
      ? {
          is_assessor: effectiveAssessor,
          evaluation_role: effectiveAssessor ? 'assessor' : 'none'
        }
      : {
          is_viewer: effectiveViewer,
          is_assessor: effectiveAssessor,
          // Also send 2-axis role fields so backend stays in sync
          manager_role: effectiveViewer ? 'viewer' : 'none',
          evaluation_role: effectiveAssessor ? 'assessor' : 'none'
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
  initCopilotForm(formData.value.config)
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
  await loadCopilotStatus()
  await loadPartsStatus()
})
</script>

<style scoped>
.settings-tab {
  width: 100%;
}

/* Co-Pilot section */
.copilot-field-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.copilot-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
  margin: 4px 0 0;
}

.copilot-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.copilot-prompt-textarea :deep(textarea) {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.82rem;
}

/* Parts / Phases section */
.part-card {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}

.part-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.part-card-name {
  font-weight: 600;
  font-size: 0.9rem;
}

.part-card-progress {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.part-progress-row {
  display: grid;
  grid-template-columns: minmax(100px, 160px) 60px 1fr;
  align-items: center;
  gap: 10px;
  font-size: 0.8rem;
}

.part-progress-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.part-progress-count {
  text-align: right;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-variant-numeric: tabular-nums;
}

.part-card-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
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
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.settings-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  /* min-height 44px keeps the tap target finger-friendly on touch devices
     (was ~20px = just the title line). Padding adds the same vertical room. */
  min-height: 44px;
  background: none;
  border: none;
  padding: 12px 8px;
  cursor: pointer;
  text-align: left;
  gap: 8px;
}

.section-toggle:focus-visible {
  outline: 2px solid rgb(var(--v-theme-primary));
  outline-offset: 2px;
  border-radius: 4px;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.section-chevron {
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.section-chevron.is-open {
  transform: rotate(180deg);
}

.section-body {
  padding-top: 16px;
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

.markdown-field__hint {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 4px 0 8px;
  line-height: 1.4;
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
  /* flex-wrap lets fields drop to the next line instead of cramping when
     horizontal space runs out (tablet/narrow desktop). */
  flex-wrap: wrap;
}

.collab-search {
  flex: 1;
  /* Ensure the search field can still shrink/grow correctly when wrapped. */
  min-width: 0;
}

.collab-role-select {
  width: 140px;
  flex-shrink: 0;
}

/* Mobile: stack the add-collaborator controls vertically so the search field
   and role select are usable full-width instead of squeezed into one row. */
@media (max-width: 600px) {
  .collab-add-row {
    flex-direction: column;
  }

  .collab-search,
  .collab-role-select {
    width: 100%;
  }
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
