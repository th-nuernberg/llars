<template>
  <div ref="layoutRoot" class="admin-chatbots-container" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <template v-if="wizardOpen">
      <ChatbotBuilderWizard
        :resume-chatbot-id="wizardResumeChatbotId"
        @created="onWizardChatbotCreated"
        @test="openTestDialogById"
        @close="handleWizardClose"
      />
    </template>

    <template v-else>
      <!-- Header Section (fixed) -->
      <div class="chatbots-header">
        <!-- Actions -->
        <div class="d-flex" :class="isMobile ? 'flex-column ga-2' : 'justify-end mb-3'">
          <div class="d-flex" :class="isMobile ? 'justify-space-between w-100' : 'flex-wrap ga-2'">
            <LBtn
              variant="secondary"
              :prepend-icon="isMobile ? undefined : 'mdi-wizard-hat'"
              :size="isMobile ? 'small' : 'default'"
              @click="openWizard()"
            >
              <v-icon v-if="isMobile" size="18" class="mr-1">mdi-wizard-hat</v-icon>
              {{ isMobile ? 'Wizard' : 'Builder Wizard' }}
            </LBtn>
            <LBtn
              variant="primary"
              :prepend-icon="isMobile ? undefined : 'mdi-plus'"
              :size="isMobile ? 'small' : 'default'"
              @click="openCreateDialog"
            >
              <v-icon v-if="isMobile" size="18" class="mr-1">mdi-plus</v-icon>
              {{ isMobile ? 'Neu' : 'Neuer Chatbot' }}
            </LBtn>
          </div>
        </div>

        <!-- Stats Cards -->
        <div class="stats-row" :class="isMobile ? 'mb-2 mt-2' : 'mb-3'">
          <div class="stats-card">
            <v-skeleton-loader v-if="loading.stats" type="card" height="80" />
            <v-card v-else variant="tonal" color="primary">
              <v-card-text class="d-flex align-center py-3">
                <v-icon size="28" class="mr-3">mdi-robot</v-icon>
                <div>
                  <div class="text-h6 font-weight-bold">{{ stats.total_chatbots }}</div>
                  <div class="text-caption">Chatbots</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
          <div class="stats-card">
            <v-skeleton-loader v-if="loading.stats" type="card" height="80" />
            <v-card v-else variant="tonal" color="success">
              <v-card-text class="d-flex align-center py-3">
                <v-icon size="28" class="mr-3">mdi-check-circle</v-icon>
                <div>
                  <div class="text-h6 font-weight-bold">{{ stats.active_chatbots }}</div>
                  <div class="text-caption">Aktiv</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
          <div class="stats-card">
            <v-skeleton-loader v-if="loading.stats" type="card" height="80" />
            <v-card v-else variant="tonal" color="info">
              <v-card-text class="d-flex align-center py-3">
                <v-icon size="28" class="mr-3">mdi-message-text</v-icon>
                <div>
                  <div class="text-h6 font-weight-bold">{{ stats.total_conversations }}</div>
                  <div class="text-caption">Gespräche</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
          <div class="stats-card">
            <v-skeleton-loader v-if="loading.stats" type="card" height="80" />
            <v-card v-else variant="tonal" color="warning">
              <v-card-text class="d-flex align-center py-3">
                <v-icon size="28" class="mr-3">mdi-folder-multiple</v-icon>
                <div>
                  <div class="text-h6 font-weight-bold">{{ collectionsCount }}</div>
                  <div class="text-caption">Collections</div>
                </div>
              </v-card-text>
            </v-card>
          </div>
        </div>
      </div>

      <!-- Tabs (fills remaining space) -->
      <div ref="tabsCard" class="chatbots-tabs-card">
        <LTabs
          v-model="activeTab"
          :tabs="[
            { value: 'chatbots', label: 'Chatbots', icon: 'mdi-robot' },
            { value: 'collections', label: 'Collections', icon: 'mdi-folder-multiple' },
            { value: 'documents', label: 'Dokumente', icon: 'mdi-file-document-multiple' }
          ]"
        />

        <div class="chatbots-tabs-body">
          <v-window v-model="activeTab">
            <!-- Chatbots Tab -->
            <v-window-item value="chatbots">
              <ChatbotList
                :chatbots="chatbots"
                :loading="loading.chatbots"
                :can-share="canShare"
                :current-username="currentUsername"
                :is-admin="isAdmin"
                @edit="openEditDialog"
                @delete="confirmDelete"
                @duplicate="duplicateChatbot"
                @test="openTestDialog"
                @manage-collections="openCollectionManager"
                @resume="resumeChatbotBuild"
                @share="openShareDialog"
              />
            </v-window-item>

            <!-- Collections Tab -->
            <v-window-item value="collections">
              <CollectionManager
                :collections="collections"
                :loading="loading.collections"
                :can-share="canShareCollections"
                @create="openCreateCollectionDialog"
                @edit="openEditCollectionDialog"
                @delete="confirmDeleteCollection"
                @share="openCollectionShareDialog"
                @view-documents="viewCollectionDocuments"
              />
            </v-window-item>

            <!-- Documents Tab -->
            <v-window-item value="documents">
              <DocumentManager
                :documents="documents"
                :collections="collections"
                :loading="loading.documents"
                :initial-collection-filter="documentCollectionFilter"
                @upload="openUploadDialog"
                @view="viewDocument"
                @delete="confirmDeleteDocument"
                @download="downloadDocument"
              />
            </v-window-item>
          </v-window>
        </div>
      </div>
    </template>

    <!-- Chatbot Editor Dialog -->
    <ChatbotEditor
      v-model="dialogs.editor"
      :chatbot="selectedChatbot"
      :collections="collections"
      :is-edit="isEditMode"
      @save="saveChatbot"
      @collection-created="loadCollections"
      @documents-uploaded="onDocumentsUploaded"
    />

    <!-- Collection Editor Dialog -->
    <CollectionEditor
      v-model="dialogs.collectionEditor"
      :collection="selectedCollection"
      :is-edit="isCollectionEditMode"
      @save="saveCollection"
    />

    <!-- Chatbot Test Dialog -->
    <ChatbotTestDialog
      v-model="dialogs.test"
      :chatbot="selectedChatbot"
    />

    <!-- Document Viewer Dialog -->
    <DocumentViewer
      v-model="dialogs.documentViewer"
      :document="selectedDocument"
    />

    <!-- Upload Dialog -->
    <DocumentUploadDialog
      v-model="dialogs.upload"
      :collections="collections"
      @uploaded="onDocumentsUploaded"
    />

    <!-- Collection Assignment Dialog -->
    <CollectionAssignmentDialog
      v-model="dialogs.collectionAssignment"
      :chatbot="selectedChatbot"
      :available-collections="collections"
      @save="saveCollectionAssignment"
    />

    <!-- Delete Confirmation -->
    <v-dialog v-model="dialogs.deleteConfirm" max-width="400">
      <v-card>
    <v-card-title class="text-h6">
      {{ deleteType === 'chatbot' ? 'Chatbot löschen?' : deleteType === 'collection' ? 'Collection löschen?' : 'Dokument löschen?' }}
    </v-card-title>
    <v-card-text>
      {{ deleteMessage }}
      <v-checkbox
        v-if="deleteType === 'chatbot'"
        v-model="deleteChatbotCollections"
        label="Primäre Collection und Dokumente mit löschen"
        density="compact"
        hide-details
        class="mt-3"
      />
    </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="dialogs.deleteConfirm = false">Abbrechen</LBtn>
          <LBtn variant="danger" @click="executeDelete">Löschen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- Share Dialog -->
    <v-dialog v-model="shareDialog" max-width="700">
      <LCard title="Chatbot teilen" subtitle="Zugriff für andere Nutzer verwalten">
        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="shareDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="shareSaving" @click="saveChatbotAccess">Speichern</LBtn>
        </template>

        <v-skeleton-loader v-if="shareLoading" type="paragraph@2, list-item" />
        <div v-else>
          <div class="section-label mt-2">
            <v-icon size="16" class="mr-1">mdi-account-multiple-plus</v-icon>
            Nutzer hinzufügen
          </div>
          <div v-if="shareUsernames.length > 0" class="invited-users mb-2">
            <LTag
              v-for="user in shareUsernames"
              :key="user"
              variant="primary"
              closable
              @close="removeShareUser(user)"
            >
              {{ user }}
            </LTag>
          </div>
          <LUserSearch
            ref="userSearchRef"
            :exclude-usernames="shareUsernames"
            placeholder="Nutzernamen eingeben..."
            @select="addShareUser"
          />
        </div>
      </LCard>
    </v-dialog>

    <CollectionShareDialog
      v-model="collectionShareDialog"
      :collection="shareCollection"
      @saved="handleCollectionShareSaved"
      @error="handleCollectionShareError"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'
import ChatbotList from './ChatbotList.vue'
import ChatbotEditor from './ChatbotEditor.vue'
import ChatbotTestDialog from './ChatbotTestDialog.vue'
import ChatbotBuilderWizard from './ChatbotBuilderWizard.vue'
import CollectionManager from '@/components/RAG/CollectionManager.vue'
import CollectionEditor from '@/components/RAG/CollectionEditor.vue'
import DocumentManager from '@/components/RAG/DocumentManager.vue'
import DocumentViewer from '@/components/RAG/DocumentViewer.vue'
import DocumentUploadDialog from '@/components/RAG/DocumentUploadDialog.vue'
import CollectionShareDialog from '@/components/RAG/CollectionShareDialog.vue'
import CollectionAssignmentDialog from './CollectionAssignmentDialog.vue'

// State
const activeTab = ref('chatbots')
const chatbots = ref([])
const collections = ref([])
const documents = ref([])
const stats = ref({
  total_chatbots: 0,
  active_chatbots: 0,
  total_conversations: 0,
  total_messages: 0
})

const loading = ref({
  chatbots: true,
  collections: true,
  documents: true,
  stats: true
})

const dialogs = ref({
  editor: false,
  collectionEditor: false,
  test: false,
  documentViewer: false,
  upload: false,
  collectionAssignment: false,
  deleteConfirm: false
})
const shareDialog = ref(false)
const shareSaving = ref(false)
const shareLoading = ref(false)
const shareUsernames = ref([])
const shareRoleNames = ref([])
const shareChatbot = ref(null)
const userSearchRef = ref(null)
const collectionShareDialog = ref(false)
const shareCollection = ref(null)

const wizardOpen = ref(false)
const wizardResumeChatbotId = ref(null)

const selectedChatbot = ref(null)
const selectedCollection = ref(null)
const selectedDocument = ref(null)
const isEditMode = ref(false)
const isCollectionEditMode = ref(false)
const deleteType = ref('')
const deleteTarget = ref(null)
const deleteChatbotCollections = ref(false)
const documentCollectionFilter = ref(null)

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

const auth = useAuth()
const { hasPermission, isAdmin } = usePermissions()
const { isMobile, isTablet, isSmallScreen } = useMobile()
const currentUsername = computed(() => auth.tokenParsed.value?.preferred_username || localStorage.getItem('username') || '')
const canShare = computed(() => hasPermission('feature:chatbots:share'))
const canShareCollections = computed(() => hasPermission('feature:rag:share'))

// Layout refs
const layoutRoot = ref(null)
const tabsCard = ref(null)

// Computed
const collectionsCount = computed(() => collections.value.length)

const deleteMessage = computed(() => {
  if (deleteType.value === 'chatbot' && deleteTarget.value) {
    return `Möchten Sie den Chatbot "${deleteTarget.value.display_name}" wirklich löschen? Alle zugehörigen Gespräche werden ebenfalls gelöscht.`
  }
  if (deleteType.value === 'collection' && deleteTarget.value) {
    return `Möchten Sie die Collection "${deleteTarget.value.display_name}" wirklich löschen? Alle enthaltenen Dokumente werden ebenfalls gelöscht.`
  }
  if (deleteType.value === 'document' && deleteTarget.value) {
    return `Möchten Sie das Dokument "${deleteTarget.value.filename}" wirklich löschen?`
  }
  return ''
})

// Methods
async function loadChatbots() {
  loading.value.chatbots = true
  try {
    const response = await axios.get('/api/chatbots?include_inactive=true')
    if (response.data.success) {
      chatbots.value = response.data.chatbots
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Chatbots', 'error')
    console.error('Error loading chatbots:', error)
  } finally {
    loading.value.chatbots = false
  }
}

async function loadCollections() {
  loading.value.collections = true
  try {
    const response = await axios.get('/api/rag/collections')
    if (response.data.success) {
      collections.value = response.data.collections
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Collections', 'error')
    console.error('Error loading collections:', error)
  } finally {
    loading.value.collections = false
  }
}

async function loadDocuments() {
  loading.value.documents = true
  try {
    const response = await axios.get('/api/rag/documents')
    if (response.data.success) {
      documents.value = response.data.documents
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Dokumente', 'error')
    console.error('Error loading documents:', error)
  } finally {
    loading.value.documents = false
  }
}

async function loadStats() {
  loading.value.stats = true
  try {
    const response = await axios.get('/api/chatbots/stats/overview')
    if (response.data.success) {
      stats.value = response.data.stats
    }
  } catch (error) {
    console.error('Error loading stats:', error)
  } finally {
    loading.value.stats = false
  }
}

function openCreateDialog() {
  selectedChatbot.value = null
  isEditMode.value = false
  dialogs.value.editor = true
}

function openWizard() {
  wizardResumeChatbotId.value = null
  wizardOpen.value = true
}

function resumeChatbotBuild(chatbot) {
  if (!chatbot?.id) return
  wizardResumeChatbotId.value = chatbot.id
  wizardOpen.value = true
}

async function handleWizardClose() {
  wizardOpen.value = false
  wizardResumeChatbotId.value = null
  // Reload chatbots to show any newly created or in-progress builds
  await loadChatbots()
}

function openEditDialog(chatbot) {
  selectedChatbot.value = { ...chatbot }
  isEditMode.value = true
  dialogs.value.editor = true
}

function openTestDialog(chatbot) {
  selectedChatbot.value = chatbot
  dialogs.value.test = true
}

function openCollectionManager(chatbot) {
  selectedChatbot.value = chatbot
  dialogs.value.collectionAssignment = true
}

function openCollectionShareDialog(collection) {
  shareCollection.value = collection
  collectionShareDialog.value = true
}

async function openShareDialog(chatbot) {
  if (!chatbot?.id) return
  shareChatbot.value = chatbot
  shareDialog.value = true
  shareLoading.value = true
  try {
    const response = await axios.get(`/api/chatbots/${chatbot.id}/access`)
    if (response.data.success) {
      shareUsernames.value = [...(response.data.allowed_usernames || [])]
      shareRoleNames.value = [...(response.data.allowed_roles || [])]
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Zugriffsrechte', 'error')
    console.error('Error loading chatbot access:', error)
  } finally {
    shareLoading.value = false
  }
}

function addShareUser(user) {
  if (!user?.username) return
  const username = user.username
  if (!shareUsernames.value.includes(username)) {
    shareUsernames.value.push(username)
  }
  userSearchRef.value?.reset?.()
}

function removeShareUser(username) {
  shareUsernames.value = shareUsernames.value.filter(u => u !== username)
}

async function saveChatbotAccess() {
  if (!shareChatbot.value?.id) return
  shareSaving.value = true
  try {
    const response = await axios.put(`/api/chatbots/${shareChatbot.value.id}/access`, {
      usernames: shareUsernames.value,
      role_names: shareRoleNames.value
    })
    if (response.data.success) {
      showSnackbar('Zugriffsrechte gespeichert', 'success')
      shareDialog.value = false
      shareChatbot.value = null
    }
  } catch (error) {
    showSnackbar('Fehler beim Speichern der Zugriffsrechte', 'error')
    console.error('Error saving chatbot access:', error)
  } finally {
    shareSaving.value = false
  }
}

function handleCollectionShareSaved() {
  showSnackbar('Zugriffsrechte gespeichert', 'success')
  collectionShareDialog.value = false
  shareCollection.value = null
}

function handleCollectionShareError(message) {
  showSnackbar(message || 'Fehler beim Speichern der Zugriffsrechte', 'error')
}

watch(collectionShareDialog, (value) => {
  if (!value) {
    shareCollection.value = null
  }
})

async function saveChatbot(chatbotData) {
  try {
    let response
    if (isEditMode.value) {
      response = await axios.put(`/api/chatbots/${chatbotData.id}`, chatbotData)
    } else {
      response = await axios.post('/api/chatbots', chatbotData)
    }

    if (response.data.success) {
      showSnackbar(isEditMode.value ? 'Chatbot aktualisiert' : 'Chatbot erstellt', 'success')
      dialogs.value.editor = false
      await loadChatbots()
      await loadStats()
    }
  } catch (error) {
    showSnackbar(error.response?.data?.error || 'Fehler beim Speichern', 'error')
    console.error('Error saving chatbot:', error)
  }
}

async function duplicateChatbot(chatbot) {
  try {
    const response = await axios.post(`/api/chatbots/${chatbot.id}/duplicate`)
    if (response.data.success) {
      showSnackbar('Chatbot dupliziert', 'success')
      await loadChatbots()
    }
  } catch (error) {
    showSnackbar('Fehler beim Duplizieren', 'error')
    console.error('Error duplicating chatbot:', error)
  }
}

function confirmDelete(chatbot) {
  deleteType.value = 'chatbot'
  deleteTarget.value = chatbot
  deleteChatbotCollections.value = false
  dialogs.value.deleteConfirm = true
}

function confirmDeleteCollection(collection) {
  deleteType.value = 'collection'
  deleteTarget.value = collection
  dialogs.value.deleteConfirm = true
}

function confirmDeleteDocument(document) {
  deleteType.value = 'document'
  deleteTarget.value = document
  dialogs.value.deleteConfirm = true
}

async function executeDelete() {
  try {
    let response
    if (deleteType.value === 'chatbot') {
      const params = deleteChatbotCollections.value ? '?delete_collections=true' : ''
      response = await axios.delete(`/api/chatbots/${deleteTarget.value.id}${params}`)
      if (response.data.success) {
        const extra = deleteChatbotCollections.value ? ' (inkl. Collection)' : ''
        showSnackbar(`Chatbot gelöscht${extra}`, 'success')
        await loadChatbots()
        await loadStats()
        if (deleteChatbotCollections.value) {
          await loadCollections()
          await loadDocuments()
        }
      }
    } else if (deleteType.value === 'collection') {
      response = await axios.delete(`/api/rag/collections/${deleteTarget.value.id}`)
      if (response.data.success) {
        showSnackbar('Collection gelöscht', 'success')
        await loadCollections()
        await loadDocuments()
      }
    } else if (deleteType.value === 'document') {
      response = await axios.delete(`/api/rag/documents/${deleteTarget.value.id}`)
      if (response.data.success) {
        showSnackbar('Dokument gelöscht', 'success')
        await loadDocuments()
        await loadCollections()
      }
    }
  } catch (error) {
    showSnackbar('Fehler beim Löschen', 'error')
    console.error('Error deleting:', error)
  } finally {
    dialogs.value.deleteConfirm = false
    deleteTarget.value = null
    deleteChatbotCollections.value = false
  }
}

// Collection methods
function openCreateCollectionDialog() {
  selectedCollection.value = null
  isCollectionEditMode.value = false
  dialogs.value.collectionEditor = true
}

function openEditCollectionDialog(collection) {
  selectedCollection.value = { ...collection }
  isCollectionEditMode.value = true
  dialogs.value.collectionEditor = true
}

async function saveCollection(collectionData) {
  try {
    let response
    if (isCollectionEditMode.value) {
      response = await axios.put(`/api/rag/collections/${collectionData.id}`, collectionData)
    } else {
      response = await axios.post('/api/rag/collections', collectionData)
    }

    if (response.data.success) {
      showSnackbar(isCollectionEditMode.value ? 'Collection aktualisiert' : 'Collection erstellt', 'success')
      dialogs.value.collectionEditor = false
      await loadCollections()
    }
  } catch (error) {
    showSnackbar(error.response?.data?.error || 'Fehler beim Speichern', 'error')
    console.error('Error saving collection:', error)
  }
}

function viewCollectionDocuments(collection) {
  // Set collection filter and switch to documents tab
  documentCollectionFilter.value = collection.name
  activeTab.value = 'documents'
}

// Document methods
function openUploadDialog() {
  dialogs.value.upload = true
}

async function viewDocument(document) {
  selectedDocument.value = document
  dialogs.value.documentViewer = true
}

async function downloadDocument(document) {
  try {
    const response = await axios.get(`/api/rag/documents/${document.id}/download`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', document.original_filename || document.filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    showSnackbar('Fehler beim Download', 'error')
    console.error('Error downloading document:', error)
  }
}

function onDocumentsUploaded() {
  dialogs.value.upload = false
  loadDocuments()
  loadCollections()
}

async function saveCollectionAssignment(data) {
  try {
    // Remove existing assignments
    for (const coll of selectedChatbot.value.collections || []) {
      await axios.delete(`/api/chatbots/${selectedChatbot.value.id}/collections/${coll.id}`)
    }

    // Add new assignments
    for (const collId of data.collection_ids) {
      await axios.post(`/api/chatbots/${selectedChatbot.value.id}/collections`, {
        collection_id: collId
      })
    }

    showSnackbar('Collections zugewiesen', 'success')
    dialogs.value.collectionAssignment = false
    await loadChatbots()
  } catch (error) {
    showSnackbar('Fehler beim Zuweisen', 'error')
    console.error('Error assigning collections:', error)
  }
}

function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// Wizard methods
async function onWizardChatbotCreated(chatbotId) {
  showSnackbar('Chatbot erfolgreich erstellt', 'success')
  await loadChatbots()
  await loadCollections()
  await loadStats()
}

async function openTestDialogById(chatbotId) {
  try {
    const response = await axios.get(`/api/chatbots/${chatbotId}`)
    if (response.data.success) {
      selectedChatbot.value = response.data.chatbot
      dialogs.value.test = true
    }
  } catch (error) {
    console.error('Error loading chatbot for test:', error)
    showSnackbar('Fehler beim Laden des Chatbots', 'error')
  }
}

// Clear document collection filter when switching tabs
watch(activeTab, (newTab) => {
  if (newTab !== 'documents') {
    documentCollectionFilter.value = null
  }
})

watch(shareDialog, (open) => {
  if (!open) {
    shareUsernames.value = []
    shareRoleNames.value = []
    shareChatbot.value = null
  }
})

// Lifecycle
onMounted(() => {
  loadChatbots()
  loadCollections()
  loadDocuments()
  loadStats()
})

// Expose wizardOpen for parent components
defineExpose({
  wizardOpen
})
</script>

<style scoped>
/* Container fills all available space from parent */
.admin-chatbots-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header section with buttons and stats - fixed height */
.chatbots-header {
  flex-shrink: 0;
}

/* Stats row using CSS Grid for responsive layout */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

@media (max-width: 960px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}

.stats-card {
  min-width: 0;
}

/* Tabs card fills remaining vertical space */
.chatbots-tabs-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Tabs body scrolls internally */
.chatbots-tabs-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

/* ========================================
   MOBILE RESPONSIVE STYLES
   ======================================== */

.admin-chatbots-container.is-mobile {
  padding: 0;
}

.admin-chatbots-container.is-mobile .chatbots-header {
  padding: 0 0 8px 0;
}

.admin-chatbots-container.is-mobile .stats-row {
  display: flex;
  overflow-x: auto;
  gap: 8px;
  padding-bottom: 4px;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.admin-chatbots-container.is-mobile .stats-row::-webkit-scrollbar {
  display: none;
}

.admin-chatbots-container.is-mobile .stats-card {
  flex: 0 0 auto;
  min-width: 120px;
}

.admin-chatbots-container.is-mobile .stats-card .v-card-text {
  padding: 8px 12px !important;
}

.admin-chatbots-container.is-mobile .stats-card .text-h6 {
  font-size: 1rem !important;
}

.admin-chatbots-container.is-mobile .stats-card .text-caption {
  font-size: 0.65rem !important;
}

.admin-chatbots-container.is-mobile .stats-card .v-icon {
  font-size: 20px !important;
}

/* Mobile tabs */
.admin-chatbots-container.is-mobile .chatbots-tabs-card {
  margin-top: 8px;
}

/* Tablet styles */
.admin-chatbots-container.is-tablet .stats-row {
  grid-template-columns: repeat(2, 1fr);
}

/* Full width helper */
.w-100 {
  width: 100%;
}
</style>
