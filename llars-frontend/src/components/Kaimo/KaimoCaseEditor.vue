<template>
  <v-container class="kaimo-case-editor">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('header')"
          type="heading, text"
          class="mb-4"
        />
        <div v-else class="d-flex align-center mb-4">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="goBack"
            class="mr-3"
          />
          <div>
            <div class="text-h5 font-weight-bold">
              Fall bearbeiten: {{ formData.display_name || 'Unbenannt' }}
            </div>
            <div class="text-subtitle-2 text-medium-emphasis">
              {{ formData.name || 'Keine Beschreibung' }}
            </div>
          </div>
          <v-spacer />
          <v-chip
            :color="formData.status === 'published' ? 'success' : formData.status === 'archived' ? 'error' : 'warning'"
            variant="flat"
            size="small"
          >
            {{ formData.status || 'draft' }}
          </v-chip>
        </div>
      </v-col>
    </v-row>

    <!-- Main Content -->
    <v-row>
      <v-col cols="12">
        <v-skeleton-loader
          v-if="isLoading('content')"
          type="card"
          height="600"
        />
        <v-card v-else elevation="2">
          <!-- Tabs -->
          <v-tabs v-model="activeTab" bg-color="surface">
            <v-tab value="general">
              <v-icon start>mdi-information</v-icon>
              Grunddaten
            </v-tab>
            <v-tab value="documents">
              <v-icon start>mdi-file-document-multiple</v-icon>
              Dokumente
              <v-chip
                v-if="documents.length > 0"
                size="x-small"
                class="ml-2"
                variant="flat"
                color="primary"
              >
                {{ documents.length }}
              </v-chip>
            </v-tab>
            <v-tab value="hints">
              <v-icon start>mdi-lightbulb-on</v-icon>
              Hinweise
              <v-chip
                v-if="hints.length > 0"
                size="x-small"
                class="ml-2"
                variant="flat"
                color="primary"
              >
                {{ hints.length }}
              </v-chip>
            </v-tab>
            <v-tab value="preview">
              <v-icon start>mdi-eye</v-icon>
              Vorschau
            </v-tab>
          </v-tabs>

          <v-divider />

          <!-- Tab Content -->
          <v-card-text style="min-height: 500px;">
            <v-window v-model="activeTab">
              <!-- ============ TAB 1: Grunddaten ============ -->
              <v-window-item value="general" eager>
                <v-form ref="formGeneral">
                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="formData.name"
                        label="Technischer Name"
                        hint="Eindeutiger Bezeichner (z.B. fall-001)"
                        persistent-hint
                        :rules="[rules.required]"
                        variant="outlined"
                        density="comfortable"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="formData.display_name"
                        label="Anzeigename"
                        hint="Name wie er Benutzern angezeigt wird"
                        persistent-hint
                        :rules="[rules.required]"
                        variant="outlined"
                        density="comfortable"
                      />
                    </v-col>
                    <v-col cols="12">
                      <v-textarea
                        v-model="formData.description"
                        label="Beschreibung"
                        hint="Kurze Beschreibung des Falls"
                        persistent-hint
                        rows="3"
                        variant="outlined"
                        density="comfortable"
                      />
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="formData.icon"
                        label="Icon (Emoji)"
                        hint="z.B. 📁"
                        persistent-hint
                        variant="outlined"
                        density="comfortable"
                      >
                        <template #prepend-inner>
                          <span class="text-h6">{{ formData.icon || '📁' }}</span>
                        </template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-text-field
                        v-model="formData.color"
                        label="Farbe (Hex)"
                        hint="z.B. #1976D2"
                        persistent-hint
                        variant="outlined"
                        density="comfortable"
                      >
                        <template #prepend-inner>
                          <input
                            v-model="formData.color"
                            type="color"
                            style="width: 32px; height: 32px; border: none; cursor: pointer"
                          >
                        </template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="12" md="4">
                      <v-select
                        v-model="formData.status"
                        label="Status"
                        :items="statusOptions"
                        variant="outlined"
                        density="comfortable"
                      />
                    </v-col>
                  </v-row>
                </v-form>
              </v-window-item>

              <!-- ============ TAB 2: Dokumente ============ -->
              <v-window-item value="documents" eager>
                <div class="d-flex align-center mb-4">
                  <div class="text-h6">Dokumente</div>
                  <v-spacer />
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-plus"
                    variant="outlined"
                    @click="openDocumentDialog(null)"
                  >
                    Dokument hinzufügen
                  </v-btn>
                </div>

                <v-data-table
                  :headers="documentHeaders"
                  :items="documents"
                  :items-per-page="10"
                  class="elevation-1"
                  density="comfortable"
                >
                  <template #item.title="{ item }">
                    <div class="font-weight-medium">{{ item.title }}</div>
                  </template>
                  <template #item.type="{ item }">
                    <v-chip size="small" variant="outlined">
                      {{ item.type }}
                    </v-chip>
                  </template>
                  <template #item.date="{ item }">
                    {{ formatDate(item.date) }}
                  </template>
                  <template #item.actions="{ item }">
                    <v-btn
                      icon="mdi-pencil"
                      size="small"
                      variant="text"
                      @click="openDocumentDialog(item)"
                    />
                    <v-btn
                      icon="mdi-delete"
                      size="small"
                      variant="text"
                      color="error"
                      @click="deleteDocument(item)"
                    />
                  </template>
                  <template #no-data>
                    <div class="text-center pa-8 text-medium-emphasis">
                      <v-icon size="48" color="grey-lighten-1" class="mb-2">
                        mdi-file-document-outline
                      </v-icon>
                      <div>Noch keine Dokumente vorhanden</div>
                    </div>
                  </template>
                </v-data-table>
              </v-window-item>

              <!-- ============ TAB 3: Hinweise ============ -->
              <v-window-item value="hints" eager>
                <div class="d-flex align-center mb-4">
                  <div class="text-h6">Hinweise</div>
                  <v-spacer />
                  <v-btn
                    color="primary"
                    prepend-icon="mdi-plus"
                    variant="outlined"
                    @click="openHintDialog(null)"
                  >
                    Hinweis hinzufügen
                  </v-btn>
                </div>

                <v-data-table
                  :headers="hintHeaders"
                  :items="hints"
                  :items-per-page="10"
                  class="elevation-1"
                  density="comfortable"
                >
                  <template #item.content="{ item }">
                    <div class="text-truncate" style="max-width: 300px;">
                      {{ item.content }}
                    </div>
                  </template>
                  <template #item.source_document_id="{ item }">
                    <v-chip size="small" variant="outlined">
                      {{ getDocumentTitle(item.source_document_id) }}
                    </v-chip>
                  </template>
                  <template #item.expected_category_id="{ item }">
                    <v-chip size="small" color="primary" variant="flat">
                      {{ getCategoryName(item.expected_category_id) }}
                    </v-chip>
                  </template>
                  <template #item.expected_rating="{ item }">
                    <v-chip
                      size="small"
                      :color="getRatingColor(item.expected_rating)"
                      variant="flat"
                    >
                      {{ item.expected_rating }}
                    </v-chip>
                  </template>
                  <template #item.actions="{ item }">
                    <v-btn
                      icon="mdi-pencil"
                      size="small"
                      variant="text"
                      @click="openHintDialog(item)"
                    />
                    <v-btn
                      icon="mdi-delete"
                      size="small"
                      variant="text"
                      color="error"
                      @click="deleteHint(item)"
                    />
                  </template>
                  <template #no-data>
                    <div class="text-center pa-8 text-medium-emphasis">
                      <v-icon size="48" color="grey-lighten-1" class="mb-2">
                        mdi-lightbulb-outline
                      </v-icon>
                      <div>Noch keine Hinweise vorhanden</div>
                    </div>
                  </template>
                </v-data-table>
              </v-window-item>

              <!-- ============ TAB 4: Vorschau ============ -->
              <v-window-item value="preview" eager>
                <v-alert
                  type="info"
                  variant="tonal"
                  class="mb-4"
                  icon="mdi-eye"
                >
                  <div class="text-subtitle-2">User-Ansicht Vorschau</div>
                  <div class="text-body-2">
                    So sehen Benutzer diesen Fall im KAIMO Panel.
                  </div>
                </v-alert>

                <!-- Case Header Preview -->
                <v-card class="mb-4" variant="outlined">
                  <v-card-title class="d-flex align-center">
                    <v-avatar :color="formData.color || 'primary'" size="48" class="mr-3">
                      <span class="text-h5">{{ formData.icon || '📁' }}</span>
                    </v-avatar>
                    <div>
                      <div class="text-h6">{{ formData.display_name || 'Unbenannt' }}</div>
                      <div class="text-caption text-medium-emphasis">
                        {{ formData.description || 'Keine Beschreibung' }}
                      </div>
                    </div>
                  </v-card-title>
                </v-card>

                <!-- Documents Preview -->
                <div class="mb-4">
                  <div class="text-subtitle-1 font-weight-bold mb-2">
                    Dokumente ({{ documents.length }})
                  </div>
                  <v-row>
                    <v-col
                      v-for="doc in documents"
                      :key="doc.id"
                      cols="12"
                      md="6"
                    >
                      <v-card variant="outlined" class="pa-3">
                        <div class="d-flex align-center mb-2">
                          <v-icon class="mr-2" color="primary">mdi-file-document</v-icon>
                          <div class="font-weight-medium">{{ doc.title }}</div>
                          <v-spacer />
                          <v-chip size="x-small" variant="outlined">
                            {{ doc.type }}
                          </v-chip>
                        </div>
                        <div class="text-caption text-medium-emphasis">
                          {{ formatDate(doc.date) }}
                        </div>
                        <div class="text-body-2 mt-2 text-truncate-3-lines">
                          {{ doc.content }}
                        </div>
                      </v-card>
                    </v-col>
                    <v-col v-if="documents.length === 0" cols="12">
                      <div class="text-center text-medium-emphasis pa-4">
                        Keine Dokumente verfügbar
                      </div>
                    </v-col>
                  </v-row>
                </div>

                <!-- Hints Preview -->
                <div>
                  <div class="text-subtitle-1 font-weight-bold mb-2">
                    Hinweise ({{ hints.length }})
                  </div>
                  <div class="d-flex flex-wrap gap-2">
                    <v-chip
                      v-for="hint in hints"
                      :key="hint.id"
                      :color="getCategoryColor(hint.expected_category_id)"
                      variant="flat"
                      size="small"
                    >
                      <v-icon start size="small">mdi-lightbulb-on</v-icon>
                      {{ getCategoryName(hint.expected_category_id) }}
                      <v-tooltip activator="parent" location="bottom">
                        {{ hint.content }}
                      </v-tooltip>
                    </v-chip>
                    <div v-if="hints.length === 0" class="text-medium-emphasis">
                      Keine Hinweise verfügbar
                    </div>
                  </div>
                </div>
              </v-window-item>
            </v-window>
          </v-card-text>

          <!-- Actions -->
          <v-divider />
          <v-card-actions>
            <v-btn
              variant="text"
              @click="goBack"
            >
              Abbrechen
            </v-btn>
            <v-spacer />
            <v-btn
              color="primary"
              variant="outlined"
              :loading="saving"
              @click="saveChanges"
            >
              Speichern
            </v-btn>
            <v-btn
              v-if="formData.status !== 'published'"
              color="success"
              variant="flat"
              :loading="publishing"
              @click="publishCase"
            >
              Veröffentlichen
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- ============ DIALOGS ============ -->

    <!-- Document Dialog -->
    <v-dialog
      v-model="documentDialog"
      max-width="800"
      persistent
      scrollable
    >
      <v-card>
        <v-card-title class="bg-primary">
          <v-icon class="mr-2">{{ editingDocument?.id ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          {{ editingDocument?.id ? 'Dokument bearbeiten' : 'Neues Dokument' }}
        </v-card-title>
        <v-card-text class="pt-4">
          <v-form ref="formDocument">
            <v-text-field
              v-model="editingDocument.title"
              label="Titel"
              :rules="[rules.required]"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-select
              v-model="editingDocument.type"
              label="Typ"
              :items="documentTypes"
              :rules="[rules.required]"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-text-field
              v-model="editingDocument.date"
              label="Datum"
              type="date"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-textarea
              v-model="editingDocument.content"
              label="Inhalt"
              hint="Markdown wird unterstützt"
              persistent-hint
              rows="8"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-text-field
              v-model.number="editingDocument.sort_order"
              label="Sortierung"
              type="number"
              variant="outlined"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDocumentDialog">
            Abbrechen
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="savingDocument"
            @click="saveDocument"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Hint Dialog -->
    <v-dialog
      v-model="hintDialog"
      max-width="800"
      persistent
      scrollable
    >
      <v-card>
        <v-card-title class="bg-primary">
          <v-icon class="mr-2">{{ editingHint?.id ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          {{ editingHint?.id ? 'Hinweis bearbeiten' : 'Neuer Hinweis' }}
        </v-card-title>
        <v-card-text class="pt-4">
          <v-form ref="formHint">
            <v-textarea
              v-model="editingHint.content"
              label="Inhalt"
              :rules="[rules.required]"
              rows="4"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-select
              v-model="editingHint.source_document_id"
              label="Quell-Dokument"
              :items="documentItems"
              item-title="title"
              item-value="id"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-select
              v-model="editingHint.expected_category_id"
              label="Erwartete Kategorie"
              :items="categoryItems"
              item-title="name"
              item-value="id"
              :rules="[rules.required]"
              variant="outlined"
              density="comfortable"
              class="mb-2"
              @update:model-value="onCategoryChange"
            />
            <v-select
              v-model="editingHint.expected_subcategory_id"
              label="Erwartete Unterkategorie"
              :items="filteredSubcategories"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="comfortable"
              class="mb-2"
              :disabled="!editingHint.expected_category_id"
            />
            <v-select
              v-model="editingHint.expected_rating"
              label="Erwartetes Rating"
              :items="ratingOptions"
              :rules="[rules.required]"
              variant="outlined"
              density="comfortable"
              class="mb-2"
            />
            <v-text-field
              v-model.number="editingHint.sort_order"
              label="Sortierung"
              type="number"
              variant="outlined"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-divider />
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeHintDialog">
            Abbrechen
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="savingHint"
            @click="saveHint"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-error">
          <v-icon class="mr-2">mdi-alert</v-icon>
          Löschen bestätigen
        </v-card-title>
        <v-card-text class="pt-4">
          <p>Möchten Sie dieses Element wirklich löschen?</p>
          <p class="text-medium-emphasis">Diese Aktion kann nicht rückgängig gemacht werden.</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">
            Abbrechen
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="deleting"
            @click="confirmDelete"
          >
            Löschen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarMessage }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import {
  getKaimoCaseAdmin,
  updateKaimoCase,
  createKaimoDocument,
  updateKaimoDocument,
  deleteKaimoDocument,
  createKaimoHint,
  updateKaimoHint,
  deleteKaimoHint,
  getKaimoCategories,
  publishKaimoCase
} from '@/services/kaimoApi'

const route = useRoute()
const router = useRouter()
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['header', 'content'])
const { hasPermission, isResearcher } = usePermissions()

// Check permissions
const canEditKaimo = computed(() => {
  return hasPermission('admin:kaimo:manage') || isResearcher.value
})

// Form Data
const formData = ref({
  name: '',
  display_name: '',
  description: '',
  icon: '📁',
  color: '#1976D2',
  status: 'draft'
})

// Lists
const documents = ref([])
const hints = ref([])
const categories = ref([])
const subcategories = ref([])

// Dialogs
const activeTab = ref('general')
const documentDialog = ref(false)
const hintDialog = ref(false)
const deleteDialog = ref(false)
const editingDocument = ref({})
const editingHint = ref({})
const deleteTarget = ref(null)

// Loading states
const saving = ref(false)
const publishing = ref(false)
const savingDocument = ref(false)
const savingHint = ref(false)
const deleting = ref(false)

// Snackbar
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Options
const statusOptions = [
  { title: 'Entwurf', value: 'draft' },
  { title: 'Veröffentlicht', value: 'published' },
  { title: 'Archiviert', value: 'archived' }
]

const documentTypes = [
  { title: 'Aktenvermerk', value: 'aktenvermerk' },
  { title: 'Bericht', value: 'bericht' },
  { title: 'Protokoll', value: 'protokoll' },
  { title: 'Sonstiges', value: 'sonstiges' }
]

const ratingOptions = [
  { title: 'Risk', value: 'risk' },
  { title: 'Resource', value: 'resource' },
  { title: 'Unclear', value: 'unclear' }
]

// Validation rules
const rules = {
  required: v => !!v || 'Dieses Feld ist erforderlich'
}

// Table Headers
const documentHeaders = [
  { title: 'Titel', key: 'title', sortable: true },
  { title: 'Typ', key: 'type', sortable: true },
  { title: 'Datum', key: 'date', sortable: true },
  { title: 'Sortierung', key: 'sort_order', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
]

const hintHeaders = [
  { title: 'Inhalt', key: 'content', sortable: false },
  { title: 'Quelle', key: 'source_document_id', sortable: false },
  { title: 'Kategorie', key: 'expected_category_id', sortable: false },
  { title: 'Rating', key: 'expected_rating', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
]

// Computed
const documentItems = computed(() => {
  return documents.value.map(d => ({ id: d.id, title: d.title }))
})

const categoryItems = computed(() => {
  return categories.value.filter(c => !c.parent_id)
})

const filteredSubcategories = computed(() => {
  if (!editingHint.value.expected_category_id) return []
  return subcategories.value.filter(s => s.parent_id === editingHint.value.expected_category_id)
})

// Helper Functions
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE')
}

function getDocumentTitle(docId) {
  const doc = documents.value.find(d => d.id === docId)
  return doc?.title || '-'
}

function getCategoryName(catId) {
  const cat = [...categories.value, ...subcategories.value].find(c => c.id === catId)
  return cat?.name || '-'
}

function getCategoryColor(catId) {
  const cat = categories.value.find(c => c.id === catId)
  return cat?.color || 'primary'
}

function getRatingColor(rating) {
  switch (rating) {
    case 'risk': return 'error'
    case 'resource': return 'success'
    case 'unclear': return 'warning'
    default: return 'grey'
  }
}

function showSnackbar(message, color = 'success') {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}

// Navigation
function goBack() {
  router.back()
}

// Load Data
async function loadCase() {
  try {
    const caseId = route.params.id
    const data = await getKaimoCaseAdmin(caseId)

    formData.value = {
      name: data.case.name,
      display_name: data.case.display_name,
      description: data.case.description,
      icon: data.case.icon || '📁',
      color: data.case.color || '#1976D2',
      status: data.case.status
    }

    documents.value = data.documents || []
    hints.value = data.hints || []
  } catch (err) {
    console.error('Failed to load case:', err)
    showSnackbar('Fall konnte nicht geladen werden', 'error')
  }
}

async function loadCategories() {
  try {
    const data = await getKaimoCategories()
    categories.value = data.categories.filter(c => !c.parent_id) || []
    subcategories.value = data.categories.filter(c => c.parent_id) || []
  } catch (err) {
    console.error('Failed to load categories:', err)
  }
}

// Save Functions
async function saveChanges() {
  saving.value = true
  try {
    const caseId = route.params.id
    await updateKaimoCase(caseId, formData.value)
    showSnackbar('Änderungen gespeichert')
  } catch (err) {
    console.error('Failed to save case:', err)
    showSnackbar('Speichern fehlgeschlagen', 'error')
  } finally {
    saving.value = false
  }
}

async function publishCase() {
  publishing.value = true
  try {
    const caseId = route.params.id
    await publishKaimoCase(caseId)
    formData.value.status = 'published'
    showSnackbar('Fall veröffentlicht')
  } catch (err) {
    console.error('Failed to publish case:', err)
    showSnackbar('Veröffentlichung fehlgeschlagen', 'error')
  } finally {
    publishing.value = false
  }
}

// Document Functions
function openDocumentDialog(doc) {
  if (doc) {
    editingDocument.value = { ...doc }
  } else {
    editingDocument.value = {
      title: '',
      type: 'aktenvermerk',
      date: new Date().toISOString().split('T')[0],
      content: '',
      sort_order: documents.value.length + 1
    }
  }
  documentDialog.value = true
}

function closeDocumentDialog() {
  documentDialog.value = false
  editingDocument.value = {}
}

async function saveDocument() {
  savingDocument.value = true
  try {
    const caseId = route.params.id
    if (editingDocument.value.id) {
      const updated = await updateKaimoDocument(caseId, editingDocument.value.id, editingDocument.value)
      const index = documents.value.findIndex(d => d.id === editingDocument.value.id)
      if (index !== -1) {
        documents.value[index] = updated.document
      }
      showSnackbar('Dokument aktualisiert')
    } else {
      const created = await createKaimoDocument(caseId, editingDocument.value)
      documents.value.push(created.document)
      showSnackbar('Dokument erstellt')
    }
    closeDocumentDialog()
  } catch (err) {
    console.error('Failed to save document:', err)
    showSnackbar('Speichern fehlgeschlagen', 'error')
  } finally {
    savingDocument.value = false
  }
}

function deleteDocument(doc) {
  deleteTarget.value = { type: 'document', item: doc }
  deleteDialog.value = true
}

// Hint Functions
function openHintDialog(hint) {
  if (hint) {
    editingHint.value = { ...hint }
  } else {
    editingHint.value = {
      content: '',
      source_document_id: null,
      expected_category_id: null,
      expected_subcategory_id: null,
      expected_rating: 'risk',
      sort_order: hints.value.length + 1
    }
  }
  hintDialog.value = true
}

function closeHintDialog() {
  hintDialog.value = false
  editingHint.value = {}
}

function onCategoryChange() {
  // Reset subcategory when category changes
  editingHint.value.expected_subcategory_id = null
}

async function saveHint() {
  savingHint.value = true
  try {
    const caseId = route.params.id
    if (editingHint.value.id) {
      const updated = await updateKaimoHint(caseId, editingHint.value.id, editingHint.value)
      const index = hints.value.findIndex(h => h.id === editingHint.value.id)
      if (index !== -1) {
        hints.value[index] = updated.hint
      }
      showSnackbar('Hinweis aktualisiert')
    } else {
      const created = await createKaimoHint(caseId, editingHint.value)
      hints.value.push(created.hint)
      showSnackbar('Hinweis erstellt')
    }
    closeHintDialog()
  } catch (err) {
    console.error('Failed to save hint:', err)
    showSnackbar('Speichern fehlgeschlagen', 'error')
  } finally {
    savingHint.value = false
  }
}

function deleteHint(hint) {
  deleteTarget.value = { type: 'hint', item: hint }
  deleteDialog.value = true
}

// Delete Confirmation
async function confirmDelete() {
  deleting.value = true
  try {
    const caseId = route.params.id
    if (deleteTarget.value.type === 'document') {
      await deleteKaimoDocument(caseId, deleteTarget.value.item.id)
      documents.value = documents.value.filter(d => d.id !== deleteTarget.value.item.id)
      showSnackbar('Dokument gelöscht')
    } else if (deleteTarget.value.type === 'hint') {
      await deleteKaimoHint(caseId, deleteTarget.value.item.id)
      hints.value = hints.value.filter(h => h.id !== deleteTarget.value.item.id)
      showSnackbar('Hinweis gelöscht')
    }
    deleteDialog.value = false
    deleteTarget.value = null
  } catch (err) {
    console.error('Failed to delete:', err)
    showSnackbar('Löschen fehlgeschlagen', 'error')
  } finally {
    deleting.value = false
  }
}

// Lifecycle
onMounted(async () => {
  if (!canEditKaimo.value) {
    showSnackbar('Keine Berechtigung zum Bearbeiten', 'error')
    router.push({ name: 'KaimoHub' })
    return
  }

  await withLoading('header', async () => {
    await loadCategories()
  })

  await withLoading('content', async () => {
    await loadCase()
  })
})
</script>

<style scoped>
.kaimo-case-editor {
  max-width: 1200px;
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.gap-2 {
  gap: 8px;
}

.text-truncate-3-lines {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
