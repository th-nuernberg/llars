<template>
  <div class="field-prompts-section">
    <v-card>
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-auto-fix</LIcon>
        {{ $t('aiAssist.admin.title') }}
        <v-spacer />
        <LBtn
          variant="secondary"
          size="small"
          prepend-icon="mdi-database-import"
          :loading="seeding"
          class="mr-2"
          @click="seedDefaults"
        >
          {{ $t('aiAssist.admin.seedDefaults') }}
        </LBtn>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          {{ $t('aiAssist.admin.create') }}
        </LBtn>
      </v-card-title>
      <v-card-subtitle>
        {{ $t('aiAssist.admin.subtitle') }}
      </v-card-subtitle>

      <v-card-text>
        <v-skeleton-loader v-if="loading" type="table" />

        <template v-else>
          <!-- Empty state -->
          <v-alert v-if="prompts.length === 0" type="info" variant="tonal" class="mb-4">
            {{ $t('aiAssist.admin.noPrompts') }}
          </v-alert>

          <!-- Data table -->
          <v-data-table
            v-else
            :headers="headers"
            :items="prompts"
            :items-per-page="10"
            class="elevation-0"
          >
            <template #item.field_key="{ item }">
              <div class="d-flex align-center">
                <code class="text-caption">{{ item.field_key }}</code>
                <v-tooltip v-if="item.description" location="top" max-width="400">
                  <template #activator="{ props }">
                    <LIcon v-bind="props" size="16" class="ml-1 text-grey cursor-pointer">
                      mdi-information-outline
                    </LIcon>
                  </template>
                  <div class="text-body-2">
                    <strong>{{ item.display_name }}</strong>
                    <br />
                    {{ item.description }}
                    <br /><br />
                    <span class="text-caption">
                      Variablen: {{ (item.context_variables || []).join(', ') || 'keine' }}
                    </span>
                  </div>
                </v-tooltip>
              </div>
            </template>

            <template #item.is_active="{ item }">
              <v-chip
                :color="item.is_active ? 'success' : 'grey'"
                size="small"
                variant="tonal"
              >
                {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
              </v-chip>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex gap-1">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click="openTestDialog(item)"
                >
                  <LIcon size="18">mdi-play-circle-outline</LIcon>
                  <v-tooltip activator="parent" location="top">
                    {{ $t('aiAssist.admin.test') }}
                  </v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  @click="openEditDialog(item)"
                >
                  <LIcon size="18">mdi-pencil-outline</LIcon>
                  <v-tooltip activator="parent" location="top">
                    {{ $t('aiAssist.admin.edit') }}
                  </v-tooltip>
                </v-btn>
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="error"
                  @click="openDeleteDialog(item)"
                >
                  <LIcon size="18">mdi-delete-outline</LIcon>
                  <v-tooltip activator="parent" location="top">
                    {{ $t('aiAssist.admin.delete') }}
                  </v-tooltip>
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </template>
      </v-card-text>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="editDialog" max-width="800" persistent>
      <v-card>
        <v-card-title>
          <LIcon class="mr-2">{{ isEditing ? 'mdi-pencil' : 'mdi-plus' }}</LIcon>
          {{ isEditing ? $t('aiAssist.admin.edit') : $t('aiAssist.admin.create') }}
        </v-card-title>

        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editForm.field_key"
                  :label="$t('aiAssist.admin.fieldKey')"
                  :hint="$t('aiAssist.admin.fieldKeyHint')"
                  :rules="[rules.required]"
                  :disabled="isEditing"
                  variant="outlined"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="editForm.display_name"
                  :label="$t('aiAssist.admin.displayName')"
                  :rules="[rules.required]"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editForm.description"
                  :label="$t('aiAssist.admin.description')"
                  variant="outlined"
                  rows="2"
                  auto-grow
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editForm.system_prompt"
                  :label="$t('aiAssist.admin.systemPrompt')"
                  :rules="[rules.required]"
                  variant="outlined"
                  rows="4"
                  auto-grow
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="editForm.user_prompt_template"
                  :label="$t('aiAssist.admin.userPrompt')"
                  :rules="[rules.required]"
                  variant="outlined"
                  rows="4"
                  auto-grow
                  hint="Verwenden Sie {variable} als Platzhalter"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12">
                <v-combobox
                  v-model="editForm.context_variables"
                  :label="$t('aiAssist.admin.contextVariables')"
                  variant="outlined"
                  chips
                  closable-chips
                  multiple
                  hint="Drücken Sie Enter um Variablen hinzuzufügen"
                  persistent-hint
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="editForm.max_tokens"
                  :label="$t('aiAssist.admin.maxTokens')"
                  type="number"
                  :min="10"
                  :max="4000"
                  variant="outlined"
                />
              </v-col>
              <v-col cols="6">
                <v-slider
                  v-model="editForm.temperature"
                  :label="$t('aiAssist.admin.temperature')"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  thumb-label
                />
              </v-col>
              <v-col cols="12">
                <v-switch
                  v-model="editForm.is_active"
                  :label="$t('aiAssist.admin.isActive')"
                  color="primary"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeEditDialog">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn
            variant="primary"
            :loading="saving"
            :disabled="!formValid"
            @click="savePrompt"
          >
            {{ $t('common.save') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="error" class="mr-2">mdi-alert-circle</LIcon>
          {{ $t('aiAssist.admin.delete') }}
        </v-card-title>
        <v-card-text>
          {{ $t('aiAssist.admin.deleteConfirm', { name: promptToDelete?.display_name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="deleteDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" :loading="deleting" @click="confirmDelete">
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Test Dialog -->
    <v-dialog v-model="testDialog" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="primary" class="mr-2">mdi-play-circle</LIcon>
          {{ $t('aiAssist.admin.testTitle') }}: {{ promptToTest?.display_name }}
        </v-card-title>
        <v-card-text>
          <v-textarea
            v-model="testContext"
            :label="$t('aiAssist.admin.testContext')"
            variant="outlined"
            rows="4"
            hint="JSON-Objekt mit Kontext-Variablen"
            persistent-hint
          />
          <v-alert v-if="testError" type="error" variant="tonal" class="mt-4">
            {{ testError }}
          </v-alert>
          <v-card v-if="testResult" variant="tonal" class="mt-4">
            <v-card-title class="text-subtitle-2">
              {{ $t('aiAssist.admin.testResult') }}
            </v-card-title>
            <v-card-text>
              <pre class="text-body-2">{{ testResult }}</pre>
            </v-card-text>
          </v-card>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="testDialog = false">
            {{ $t('common.close') }}
          </LBtn>
          <LBtn variant="primary" :loading="testing" @click="runTest">
            {{ $t('aiAssist.admin.test') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()

// State
const loading = ref(true)
const prompts = ref([])
const editDialog = ref(false)
const deleteDialog = ref(false)
const testDialog = ref(false)
const saving = ref(false)
const deleting = ref(false)
const seeding = ref(false)
const testing = ref(false)
const formValid = ref(false)
const promptToDelete = ref(null)
const promptToTest = ref(null)
const testContext = ref('{}')
const testResult = ref('')
const testError = ref('')
const isEditing = ref(false)

const editForm = reactive({
  id: null,
  field_key: '',
  display_name: '',
  description: '',
  system_prompt: '',
  user_prompt_template: '',
  context_variables: [],
  max_tokens: 200,
  temperature: 0.7,
  is_active: true
})

const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
})

const rules = {
  required: v => !!v || t('validation.required')
}

const headers = computed(() => [
  { title: t('aiAssist.admin.columns.fieldKey'), key: 'field_key', sortable: true },
  { title: t('aiAssist.admin.columns.displayName'), key: 'display_name', sortable: true },
  { title: 'Max Tokens', key: 'max_tokens', sortable: true, width: '100px' },
  { title: 'Temp.', key: 'temperature', sortable: true, width: '80px' },
  { title: t('aiAssist.admin.columns.isActive'), key: 'is_active', sortable: true, width: '100px' },
  { title: t('aiAssist.admin.columns.actions'), key: 'actions', sortable: false, width: '150px' }
])

// Methods
async function fetchPrompts() {
  loading.value = true
  try {
    const response = await axios.get('/api/admin/field-prompts')
    prompts.value = response.data.prompts || []
  } catch (error) {
    console.error('Failed to fetch prompts:', error)
    showSnackbar('Fehler beim Laden der Prompts', 'error')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  isEditing.value = false
  Object.assign(editForm, {
    id: null,
    field_key: '',
    display_name: '',
    description: '',
    system_prompt: '',
    user_prompt_template: '',
    context_variables: [],
    max_tokens: 200,
    temperature: 0.7,
    is_active: true
  })
  editDialog.value = true
}

function openEditDialog(prompt) {
  isEditing.value = true
  Object.assign(editForm, {
    id: prompt.id,
    field_key: prompt.field_key,
    display_name: prompt.display_name,
    description: prompt.description || '',
    system_prompt: prompt.system_prompt,
    user_prompt_template: prompt.user_prompt_template,
    context_variables: prompt.context_variables || [],
    max_tokens: prompt.max_tokens,
    temperature: prompt.temperature,
    is_active: prompt.is_active
  })
  editDialog.value = true
}

function closeEditDialog() {
  editDialog.value = false
}

async function savePrompt() {
  saving.value = true
  try {
    if (isEditing.value) {
      await axios.put(`/api/admin/field-prompts/${editForm.id}`, editForm)
      showSnackbar('Prompt erfolgreich aktualisiert', 'success')
    } else {
      await axios.post('/api/admin/field-prompts', editForm)
      showSnackbar('Prompt erfolgreich erstellt', 'success')
    }
    closeEditDialog()
    await fetchPrompts()
  } catch (error) {
    console.error('Failed to save prompt:', error)
    const msg = error.response?.data?.error || 'Fehler beim Speichern'
    showSnackbar(msg, 'error')
  } finally {
    saving.value = false
  }
}

function openDeleteDialog(prompt) {
  promptToDelete.value = prompt
  deleteDialog.value = true
}

async function confirmDelete() {
  if (!promptToDelete.value) return

  deleting.value = true
  try {
    await axios.delete(`/api/admin/field-prompts/${promptToDelete.value.id}`)
    showSnackbar('Prompt erfolgreich gelöscht', 'success')
    deleteDialog.value = false
    promptToDelete.value = null
    await fetchPrompts()
  } catch (error) {
    console.error('Failed to delete prompt:', error)
    showSnackbar('Fehler beim Löschen', 'error')
  } finally {
    deleting.value = false
  }
}

function openTestDialog(prompt) {
  promptToTest.value = prompt
  testResult.value = ''
  testError.value = ''
  // Pre-fill context with example values
  const exampleContext = {}
  for (const v of (prompt.context_variables || [])) {
    exampleContext[v] = `[${v}]`
  }
  testContext.value = JSON.stringify(exampleContext, null, 2)
  testDialog.value = true
}

async function runTest() {
  if (!promptToTest.value) return

  testing.value = true
  testResult.value = ''
  testError.value = ''

  try {
    const context = JSON.parse(testContext.value)
    const response = await axios.post(
      `/api/admin/field-prompts/${promptToTest.value.id}/test`,
      { context }
    )
    if (response.data.success) {
      testResult.value = response.data.value
    } else {
      testError.value = response.data.error || 'Test fehlgeschlagen'
    }
  } catch (error) {
    console.error('Test failed:', error)
    if (error instanceof SyntaxError) {
      testError.value = 'Ungültiges JSON im Kontext'
    } else {
      testError.value = error.response?.data?.error || error.message
    }
  } finally {
    testing.value = false
  }
}

async function seedDefaults() {
  seeding.value = true
  try {
    const response = await axios.post('/api/admin/field-prompts/seed-defaults')
    const created = response.data.created || 0
    showSnackbar(t('aiAssist.admin.seeded', { count: created }), 'success')
    await fetchPrompts()
  } catch (error) {
    console.error('Failed to seed defaults:', error)
    showSnackbar('Fehler beim Laden der Standard-Prompts', 'error')
  } finally {
    seeding.value = false
  }
}

function showSnackbar(text, color = 'success') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

onMounted(() => {
  fetchPrompts()
})
</script>

<style scoped>
.field-prompts-section {
  max-width: 1200px;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', monospace;
}

code {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
