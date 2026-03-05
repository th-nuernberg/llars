<template>
  <v-dialog v-model="dialogVisible" max-width="700" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-file-document-outline</v-icon>
        {{ isEdit ? t('conferenceManager.paper.edit') : t('conferenceManager.paper.create') }}
        <v-spacer />
        <v-btn icon variant="text" @click="close"><v-icon>mdi-close</v-icon></v-btn>
      </v-card-title>

      <v-card-text>
        <v-form ref="formRef" @submit.prevent="save">
          <v-text-field
            v-model="form.title"
            :label="t('conferenceManager.paper.title') + ' *'"
            :rules="[v => !!v || t('conferenceManager.validation.required')]"
            variant="outlined"
            density="compact"
          />

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.status"
                :items="PAPER_STATUSES"
                :item-title="s => t(s.labelKey)"
                item-value="value"
                :label="t('conferenceManager.paper.status')"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.conference_id"
                :items="conferenceOptions"
                item-title="label"
                item-value="value"
                :label="t('conferenceManager.paper.conference')"
                variant="outlined"
                density="compact"
                clearable
              />
            </v-col>
          </v-row>

          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.overleaf_url"
                :label="t('conferenceManager.paper.overleafUrl')"
                variant="outlined"
                density="compact"
                prepend-inner-icon="overleaf"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.external_url"
                :label="t('conferenceManager.paper.externalUrl')"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-link"
              />
            </v-col>
          </v-row>

          <v-select
            v-model="form.latex_workspace_id"
            :items="latexWorkspaces"
            :label="t('conferenceManager.paper.latexWorkspace')"
            variant="outlined"
            density="compact"
            clearable
            prepend-inner-icon="llars-latex"
          />

          <v-combobox
            v-model="form.keywords"
            :label="t('conferenceManager.paper.keywords')"
            variant="outlined"
            density="compact"
            multiple
            chips
            closable-chips
          />

          <v-textarea
            v-model="form.description"
            :label="t('conferenceManager.paper.description')"
            variant="outlined"
            density="compact"
            rows="3"
            auto-grow
          />

          <v-divider class="my-3" />

          <PaperAuthorEditor v-model="form.authors" />

          <v-divider class="my-3" />

          <!-- Submission History -->
          <div v-if="isEdit" class="submission-history mb-3">
            <div class="d-flex align-center mb-2">
              <v-icon size="18" class="mr-2">mdi-history</v-icon>
              <span class="text-subtitle-2">{{ t('conferenceManager.paper.submissions') }}</span>
              <v-spacer />
              <v-btn
                size="x-small"
                variant="tonal"
                color="primary"
                :style="{ borderRadius: '6px 2px 6px 2px' }"
                prepend-icon="mdi-plus"
                @click="showAddSubmission = !showAddSubmission"
              >
                {{ t('conferenceManager.paper.addSubmission') }}
              </v-btn>
            </div>

            <!-- Add submission inline form -->
            <v-expand-transition>
              <div v-if="showAddSubmission" class="submission-add-form mb-3">
                <v-row dense>
                  <v-col cols="12" sm="5">
                    <v-select
                      v-model="newSubmission.conference_id"
                      :items="conferenceOptions"
                      item-title="label"
                      item-value="value"
                      :label="t('conferenceManager.paper.conference')"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" sm="3">
                    <v-select
                      v-model="newSubmission.status"
                      :items="SUBMISSION_STATUSES"
                      :item-title="s => t(s.labelKey)"
                      item-value="value"
                      :label="t('conferenceManager.paper.status')"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="newSubmission.submitted_at"
                      :label="t('conferenceManager.paper.submittedAt')"
                      type="date"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                </v-row>
                <v-row dense class="mt-1">
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="newSubmission.decided_at"
                      :label="t('conferenceManager.paper.decidedAt')"
                      type="date"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" sm="5">
                    <v-text-field
                      v-model="newSubmission.notes"
                      :label="t('conferenceManager.paper.notes')"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="12" sm="3" class="d-flex align-center">
                    <v-btn
                      size="small"
                      color="primary"
                      variant="flat"
                      :style="{ borderRadius: '6px 2px 6px 2px' }"
                      :loading="submissionSaving"
                      @click="saveNewSubmission"
                    >
                      {{ t('conferenceManager.actions.save') }}
                    </v-btn>
                    <v-btn
                      size="small"
                      variant="text"
                      class="ml-1"
                      @click="showAddSubmission = false"
                    >
                      {{ t('conferenceManager.actions.cancel') }}
                    </v-btn>
                  </v-col>
                </v-row>
              </div>
            </v-expand-transition>

            <!-- Timeline -->
            <div v-if="form.submissions?.length" class="submission-timeline">
              <div
                v-for="(sub, idx) in form.submissions"
                :key="sub.id"
                class="submission-entry"
                :class="{ 'is-current': idx === 0 }"
              >
                <div class="submission-dot" :style="{ backgroundColor: getSubmissionStatusConfig(sub.status).color }" />
                <div class="submission-content">
                  <div class="d-flex align-center flex-wrap ga-1">
                    <v-chip
                      v-if="sub.conference"
                      size="x-small"
                      variant="tonal"
                      color="primary"
                      :style="{ borderRadius: '6px 2px 6px 2px' }"
                    >
                      {{ sub.conference.acronym }} {{ sub.conference.year }}
                    </v-chip>
                    <v-chip
                      size="x-small"
                      :color="getSubmissionStatusConfig(sub.status).color"
                      variant="flat"
                      :style="{ borderRadius: '6px 2px 6px 2px' }"
                    >
                      <v-icon start size="10">{{ getSubmissionStatusConfig(sub.status).icon }}</v-icon>
                      {{ t(getSubmissionStatusConfig(sub.status).labelKey) }}
                    </v-chip>
                    <v-chip
                      v-if="idx === 0"
                      size="x-small"
                      variant="outlined"
                      color="primary"
                      :style="{ borderRadius: '6px 2px 6px 2px' }"
                    >
                      {{ t('conferenceManager.paper.currentSubmission') }}
                    </v-chip>
                    <v-spacer />
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      color="error"
                      @click="removeSubmission(sub)"
                    >
                      <v-icon size="14">mdi-delete-outline</v-icon>
                    </v-btn>
                  </div>
                  <div class="submission-meta">
                    <span v-if="sub.submitted_at">{{ t('conferenceManager.paper.submittedAt') }}: {{ formatDate(sub.submitted_at) }}</span>
                    <span v-if="sub.decided_at"> · {{ t('conferenceManager.paper.decidedAt') }}: {{ formatDate(sub.decided_at) }}</span>
                  </div>
                  <div v-if="sub.notes" class="submission-notes">{{ sub.notes }}</div>
                </div>
              </div>
            </div>
            <div v-else class="text-body-2 text-disabled pa-2">
              {{ t('conferenceManager.paper.noSubmissions') }}
            </div>
          </div>

          <v-divider v-if="isEdit" class="my-3" />

          <v-textarea
            v-model="form.notes"
            :label="t('conferenceManager.paper.notes')"
            variant="outlined"
            density="compact"
            rows="2"
            auto-grow
          />
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="close">{{ t('conferenceManager.actions.cancel') }}</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="saving"
          :style="{ borderRadius: '16px 4px 16px 4px' }"
          @click="save"
        >
          {{ isEdit ? t('conferenceManager.actions.save') : t('conferenceManager.actions.create') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { PAPER_STATUSES, SUBMISSION_STATUSES, getSubmissionStatusConfig } from '../config/conferenceConfig'
import { useConferenceManager } from '../composables/useConferenceManager'
import PaperAuthorEditor from './PaperAuthorEditor.vue'

const { t } = useI18n()
const { getToken } = useAuth()
const { conferences, createPaper, updatePaper, addSubmission, deleteSubmission } = useConferenceManager()

const latexWorkspaces = ref([])

async function loadLatexWorkspaces() {
  try {
    const response = await axios.get('/api/latex-collab/workspaces', {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    latexWorkspaces.value = (response.data.workspaces || []).map(ws => ({
      title: ws.name,
      value: ws.id,
    }))
  } catch (err) {
    console.error('Failed to load workspaces:', err)
  }
}

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  paper: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.paper?.id)
const saving = ref(false)
const formRef = ref(null)

const conferenceOptions = computed(() =>
  conferences.value.map(c => ({
    label: `${c.acronym} ${c.year}`,
    value: c.id,
  }))
)

const showAddSubmission = ref(false)
const submissionSaving = ref(false)
const defaultSubmission = () => ({
  conference_id: null,
  status: 'submitted',
  submitted_at: '',
  decided_at: '',
  notes: '',
})
const newSubmission = ref(defaultSubmission())

const defaultForm = () => ({
  title: '',
  status: 'planning',
  conference_id: null,
  latex_workspace_id: null,
  overleaf_url: '',
  external_url: '',
  keywords: [],
  description: '',
  notes: '',
  authors: [],
  submissions: [],
})

const form = ref(defaultForm())

watch(() => props.modelValue, (visible) => {
  if (visible) loadLatexWorkspaces()
})

watch(() => props.paper, (val) => {
  if (val) {
    form.value = {
      ...defaultForm(),
      ...val,
      keywords: val.keywords || [],
      authors: val.authors || [],
      submissions: val.submissions || [],
    }
  } else {
    form.value = defaultForm()
  }
  showAddSubmission.value = false
  newSubmission.value = defaultSubmission()
}, { immediate: true })

function close() {
  dialogVisible.value = false
  form.value = defaultForm()
  showAddSubmission.value = false
}

async function saveNewSubmission() {
  if (!newSubmission.value.conference_id) return
  submissionSaving.value = true
  try {
    const paper = await addSubmission(props.paper.id, newSubmission.value)
    form.value.submissions = paper.submissions || []
    form.value.conference_id = paper.conference_id
    form.value.status = paper.status
    newSubmission.value = defaultSubmission()
    showAddSubmission.value = false
    emit('saved')
  } catch (err) {
    console.error('Add submission failed:', err)
  } finally {
    submissionSaving.value = false
  }
}

async function removeSubmission(sub) {
  try {
    const paper = await deleteSubmission(props.paper.id, sub.id)
    form.value.submissions = paper.submissions || []
    form.value.conference_id = paper.conference_id
    form.value.status = paper.status
    emit('saved')
  } catch (err) {
    console.error('Delete submission failed:', err)
  }
}

function formatDate(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

async function save() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value) {
      await updatePaper(props.paper.id, form.value)
    } else {
      await createPaper(form.value)
    }
    emit('saved')
    close()
  } catch (err) {
    console.error('Save paper failed:', err)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.submission-add-form {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 12px;
}

.submission-timeline {
  position: relative;
  padding-left: 16px;
}

.submission-timeline::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.submission-entry {
  position: relative;
  padding: 6px 0 10px 12px;
}

.submission-dot {
  position: absolute;
  left: -12px;
  top: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid rgb(var(--v-theme-surface));
  z-index: 1;
}

.submission-entry.is-current .submission-dot {
  width: 12px;
  height: 12px;
  left: -13px;
  top: 9px;
}

.submission-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.submission-meta {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 2px;
}

.submission-notes {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-style: italic;
}
</style>
