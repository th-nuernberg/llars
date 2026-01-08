<template>
  <div class="zotero-panel">
    <!-- Connection Status -->
    <div class="zotero-section">
      <div class="section-header">
        <LIcon class="mr-2" color="primary">mdi-book-open-page-variant</LIcon>
        <span class="section-title">Zotero Verbindung</span>
      </div>

      <div v-if="loading" class="d-flex justify-center pa-4">
        <v-progress-circular indeterminate size="24" />
      </div>

      <template v-else>
        <!-- Connected State -->
        <div v-if="isConnected" class="connection-info">
          <v-chip color="success" variant="tonal" size="small" class="mb-2">
            <LIcon start size="small">mdi-check-circle</LIcon>
            Verbunden
          </v-chip>
          <div class="text-body-2 mb-2">
            <strong>Account:</strong> {{ connection?.zotero_username }}
          </div>
          <div class="text-caption text-medium-emphasis" v-if="connection?.connected_at">
            Verbunden seit {{ formatDate(connection.connected_at) }}
          </div>
          <LBtn
            variant="outlined"
            size="small"
            class="mt-3"
            @click="handleDisconnect"
          >
            Verbindung trennen
          </LBtn>
        </div>

        <!-- Not Connected State -->
        <div v-else class="connection-prompt">
          <p class="text-body-2 text-medium-emphasis mb-3">
            Verbinde deinen Zotero Account um Literaturverzeichnisse zu synchronisieren.
          </p>

          <div class="connection-methods">
            <!-- OAuth Method (only shown if configured by admin) -->
            <template v-if="oauthAvailable">
              <div class="method-card method-primary">
                <div class="method-title">
                  <LIcon size="small" class="mr-1" color="primary">mdi-login</LIcon>
                  Mit Zotero anmelden
                </div>
                <p class="text-caption text-medium-emphasis mb-3">
                  Empfohlen: Melde dich direkt bei Zotero an und autorisiere LLARS.
                </p>
                <LBtn
                  variant="primary"
                  :loading="connectingOAuth"
                  @click="handleConnectWithOAuth"
                >
                  <LIcon start>mdi-open-in-new</LIcon>
                  Mit Zotero verbinden
                </LBtn>
              </div>

              <div class="method-divider">
                <span>oder</span>
              </div>
            </template>

            <!-- API Key Method -->
            <div class="method-card" :class="{ 'method-primary': !oauthAvailable }">
              <div class="method-title">
                <LIcon size="small" class="mr-1">mdi-key</LIcon>
                API-Key eingeben
              </div>
              <p class="text-caption text-medium-emphasis mb-2">
                {{ oauthAvailable ? 'Alternativ: Erstelle einen API-Key auf zotero.org' : 'Erstelle einen API-Key auf zotero.org und gib ihn hier ein.' }}
              </p>
              <v-text-field
                v-model="apiKeyInput"
                label="Zotero API Key"
                placeholder="Enter your API key"
                variant="outlined"
                density="compact"
                hide-details
                type="password"
                class="mb-2"
              />
              <LBtn
                :variant="oauthAvailable ? 'secondary' : 'primary'"
                :size="oauthAvailable ? 'small' : 'default'"
                :loading="connecting"
                :disabled="!apiKeyInput.trim()"
                @click="handleConnectWithApiKey"
              >
                Verbinden
              </LBtn>
              <div class="text-caption text-medium-emphasis mt-2">
                <a href="https://www.zotero.org/settings/keys" target="_blank" rel="noopener">
                  API-Key erstellen auf zotero.org
                  <LIcon size="x-small">mdi-open-in-new</LIcon>
                </a>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Linked Libraries (only shown when connected) -->
    <div v-if="isConnected" class="zotero-section mt-4">
      <div class="section-header">
        <LIcon class="mr-2" color="secondary">mdi-library</LIcon>
        <span class="section-title">Verknüpfte Bibliotheken</span>
        <v-spacer />
        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-plus"
          @click="showAddLibraryDialog = true"
        >
          Hinzufügen
        </LBtn>
      </div>

      <div v-if="loadingLibraries" class="d-flex justify-center pa-4">
        <v-progress-circular indeterminate size="24" />
      </div>

      <div v-else-if="workspaceLibraries.length === 0" class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-book-off-outline</LIcon>
        <p class="text-body-2 text-medium-emphasis mt-2">
          Keine Bibliotheken verknüpft
        </p>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          class="mt-2"
          @click="showAddLibraryDialog = true"
        >
          Bibliothek hinzufügen
        </LBtn>
      </div>

      <div v-else class="libraries-list">
        <div
          v-for="lib in workspaceLibraries"
          :key="lib.id"
          class="library-card"
        >
          <div class="library-header">
            <LIcon size="small" class="mr-2" :color="lib.library_type === 'group' ? 'info' : 'primary'">
              {{ lib.library_type === 'group' ? 'mdi-account-group' : 'mdi-bookshelf' }}
            </LIcon>
            <div class="library-name">
              {{ lib.library_name }}
              <span v-if="lib.collection_name" class="collection-name">
                / {{ lib.collection_name }}
              </span>
            </div>
          </div>

          <div class="library-meta">
            <v-chip size="x-small" variant="tonal">
              {{ lib.bib_filename }}
            </v-chip>
            <v-chip size="x-small" variant="tonal" color="info">
              {{ lib.item_count }} Einträge
            </v-chip>
            <v-chip v-if="lib.auto_sync_enabled" size="x-small" variant="tonal" color="success">
              Auto-Sync: {{ lib.auto_sync_interval_minutes }}min
            </v-chip>
          </div>

          <div class="library-sync-info text-caption text-medium-emphasis">
            <template v-if="lib.last_synced_at">
              Zuletzt synchronisiert: {{ formatRelativeTime(lib.last_synced_at) }}
            </template>
            <template v-else>
              Noch nicht synchronisiert
            </template>
          </div>

          <div v-if="lib.last_sync_error" class="library-error">
            <LIcon size="small" color="error">mdi-alert-circle</LIcon>
            {{ lib.last_sync_error }}
          </div>

          <div class="library-actions">
            <LBtn
              variant="text"
              size="small"
              prepend-icon="mdi-sync"
              :loading="syncingLibraryId === lib.id"
              @click="handleSync(lib)"
            >
              Sync
            </LBtn>
            <LBtn
              variant="text"
              size="small"
              prepend-icon="mdi-cog"
              @click="openSettings(lib)"
            >
              Einstellungen
            </LBtn>
            <LBtn
              variant="text"
              size="small"
              prepend-icon="mdi-delete"
              color="error"
              @click="confirmRemove(lib)"
            >
              Entfernen
            </LBtn>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Library Dialog -->
    <v-dialog v-model="showAddLibraryDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2" color="primary">mdi-plus-circle</LIcon>
          Bibliothek hinzufügen
        </v-card-title>

        <v-card-text>
          <div v-if="loadingZoteroLibraries" class="d-flex justify-center pa-4">
            <v-progress-circular indeterminate />
          </div>

          <template v-else>
            <!-- Library Selection -->
            <v-select
              v-model="selectedLibrary"
              :items="zoteroLibraries"
              item-title="name"
              item-value="library_id"
              label="Bibliothek auswählen"
              variant="outlined"
              density="compact"
              return-object
              class="mb-3"
            >
              <template #item="{ item, props }">
                <v-list-item v-bind="props">
                  <template #prepend>
                    <LIcon :color="item.raw.library_type === 'group' ? 'info' : 'primary'">
                      {{ item.raw.library_type === 'group' ? 'mdi-account-group' : 'mdi-bookshelf' }}
                    </LIcon>
                  </template>
                </v-list-item>
              </template>
            </v-select>

            <!-- Collection Selection (optional) -->
            <v-select
              v-if="selectedLibrary"
              v-model="selectedCollection"
              :items="[{ key: null, name: 'Gesamte Bibliothek' }, ...collections]"
              item-title="name"
              item-value="key"
              label="Collection (optional)"
              variant="outlined"
              density="compact"
              return-object
              :loading="loadingCollections"
              class="mb-3"
            />

            <!-- Filename -->
            <v-text-field
              v-model="newBibFilename"
              label="Dateiname"
              placeholder="references.bib"
              variant="outlined"
              density="compact"
              suffix=".bib"
              :rules="[v => !!v || 'Dateiname erforderlich']"
              class="mb-3"
            />

            <!-- Auto-Sync Settings -->
            <v-switch
              v-model="newAutoSync"
              label="Auto-Sync aktivieren"
              density="compact"
              hide-details
              color="primary"
            />
            <v-slider
              v-if="newAutoSync"
              v-model="newSyncInterval"
              :min="5"
              :max="120"
              :step="5"
              label="Sync-Intervall (Minuten)"
              thumb-label
              class="mt-2"
            />
          </template>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showAddLibraryDialog = false">
            Abbrechen
          </LBtn>
          <LBtn
            variant="primary"
            :loading="addingLibrary"
            :disabled="!canAddLibrary"
            @click="handleAddLibrary"
          >
            Hinzufügen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Settings Dialog -->
    <v-dialog v-model="showSettingsDialog" max-width="400">
      <v-card v-if="editingLibrary">
        <v-card-title>
          <LIcon class="mr-2">mdi-cog</LIcon>
          Sync-Einstellungen
        </v-card-title>

        <v-card-text>
          <div class="text-body-2 mb-3">
            <strong>{{ editingLibrary.library_name }}</strong>
            <span v-if="editingLibrary.collection_name">
              / {{ editingLibrary.collection_name }}
            </span>
          </div>

          <v-switch
            v-model="editAutoSync"
            label="Auto-Sync aktivieren"
            density="compact"
            hide-details
            color="primary"
          />
          <v-slider
            v-if="editAutoSync"
            v-model="editSyncInterval"
            :min="5"
            :max="120"
            :step="5"
            label="Sync-Intervall (Minuten)"
            thumb-label
            class="mt-3"
          />
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showSettingsDialog = false">
            Abbrechen
          </LBtn>
          <LBtn
            variant="primary"
            :loading="savingSettings"
            @click="handleSaveSettings"
          >
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Remove Confirmation Dialog -->
    <v-dialog v-model="showRemoveDialog" max-width="400">
      <v-card v-if="removingLibrary">
        <v-card-title class="text-error">
          <LIcon class="mr-2" color="error">mdi-alert</LIcon>
          Bibliothek entfernen?
        </v-card-title>

        <v-card-text>
          <p>
            Möchtest du <strong>{{ removingLibrary.library_name }}</strong> wirklich entfernen?
          </p>
          <p class="text-caption text-medium-emphasis">
            Die .bib Datei bleibt erhalten, wird aber nicht mehr synchronisiert.
          </p>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showRemoveDialog = false">
            Abbrechen
          </LBtn>
          <LBtn
            variant="danger"
            :loading="removing"
            @click="handleRemove"
          >
            Entfernen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Error/Success Messages -->
    <v-snackbar v-model="showMessage" :color="messageType" timeout="4000">
      {{ message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import zoteroService from '@/services/zoteroService'

const props = defineProps({
  workspaceId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['library-added', 'library-removed', 'library-synced'])

// Connection state
const loading = ref(true)
const connecting = ref(false)
const connectingOAuth = ref(false)
const oauthAvailable = ref(false)
const isConnected = ref(false)
const connection = ref(null)
const apiKeyInput = ref('')

// Libraries state
const loadingLibraries = ref(false)
const workspaceLibraries = ref([])
const syncingLibraryId = ref(null)

// Add library dialog state
const showAddLibraryDialog = ref(false)
const loadingZoteroLibraries = ref(false)
const zoteroLibraries = ref([])
const selectedLibrary = ref(null)
const collections = ref([])
const loadingCollections = ref(false)
const selectedCollection = ref(null)
const newBibFilename = ref('references')
const newAutoSync = ref(false)
const newSyncInterval = ref(30)
const addingLibrary = ref(false)

// Settings dialog state
const showSettingsDialog = ref(false)
const editingLibrary = ref(null)
const editAutoSync = ref(false)
const editSyncInterval = ref(30)
const savingSettings = ref(false)

// Remove dialog state
const showRemoveDialog = ref(false)
const removingLibrary = ref(null)
const removing = ref(false)

// Messages
const showMessage = ref(false)
const message = ref('')
const messageType = ref('success')

const canAddLibrary = computed(() => {
  return selectedLibrary.value && newBibFilename.value.trim()
})

// Format date
function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

// Format relative time
function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'gerade eben'
  if (diffMins < 60) return `vor ${diffMins} Minuten`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `vor ${diffHours} Stunden`

  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `vor ${diffDays} Tagen`

  return formatDate(dateStr)
}

// Show notification
function notify(msg, type = 'success') {
  message.value = msg
  messageType.value = type
  showMessage.value = true
}

// Load connection status and OAuth availability
async function loadConnectionStatus() {
  try {
    loading.value = true

    // Load both in parallel
    const [statusResult, oauthResult] = await Promise.all([
      zoteroService.getConnectionStatus(),
      zoteroService.checkOAuthAvailable().catch(() => ({ oauth_available: false }))
    ])

    isConnected.value = statusResult.connected
    connection.value = statusResult.connection
    oauthAvailable.value = oauthResult.oauth_available || false
  } catch (err) {
    console.error('Failed to load Zotero connection status:', err)
  } finally {
    loading.value = false
  }
}

// Load workspace libraries
async function loadWorkspaceLibraries() {
  try {
    loadingLibraries.value = true
    const result = await zoteroService.getWorkspaceLibraries(props.workspaceId)
    workspaceLibraries.value = result.libraries || []
  } catch (err) {
    console.error('Failed to load workspace libraries:', err)
  } finally {
    loadingLibraries.value = false
  }
}

// Connect with API key
async function handleConnectWithApiKey() {
  try {
    connecting.value = true
    const result = await zoteroService.connectWithApiKey(apiKeyInput.value.trim())
    connection.value = result.connection
    isConnected.value = true
    apiKeyInput.value = ''
    notify('Zotero Account verbunden!')
  } catch (err) {
    notify(err.response?.data?.error || 'Verbindung fehlgeschlagen', 'error')
  } finally {
    connecting.value = false
  }
}

// Connect with OAuth (redirect to Zotero)
async function handleConnectWithOAuth() {
  try {
    connectingOAuth.value = true
    const result = await zoteroService.startOAuth()

    if (result.authorization_url) {
      // Redirect to Zotero authorization page
      window.location.href = result.authorization_url
    } else {
      notify('OAuth nicht verfügbar. Bitte API-Key verwenden.', 'warning')
    }
  } catch (err) {
    const errorMsg = err.response?.data?.error || 'OAuth-Verbindung fehlgeschlagen'
    // If OAuth not configured, show info message instead of error
    if (errorMsg.includes('not configured')) {
      notify('OAuth ist nicht konfiguriert. Bitte API-Key verwenden.', 'info')
    } else {
      notify(errorMsg, 'error')
    }
  } finally {
    connectingOAuth.value = false
  }
}

// Disconnect
async function handleDisconnect() {
  try {
    await zoteroService.disconnect()
    isConnected.value = false
    connection.value = null
    workspaceLibraries.value = []
    notify('Zotero Account getrennt')
  } catch (err) {
    notify(err.response?.data?.error || 'Trennung fehlgeschlagen', 'error')
  }
}

// Load Zotero libraries when dialog opens
async function loadZoteroLibraries() {
  try {
    loadingZoteroLibraries.value = true
    const result = await zoteroService.getLibraries()
    zoteroLibraries.value = result.libraries || []
  } catch (err) {
    console.error('Failed to load Zotero libraries:', err)
    notify('Fehler beim Laden der Bibliotheken', 'error')
  } finally {
    loadingZoteroLibraries.value = false
  }
}

// Load collections when library is selected
async function loadCollections() {
  if (!selectedLibrary.value) {
    collections.value = []
    return
  }

  try {
    loadingCollections.value = true
    const result = await zoteroService.getCollections(
      selectedLibrary.value.library_type,
      selectedLibrary.value.library_id
    )
    collections.value = result.collections || []
  } catch (err) {
    console.error('Failed to load collections:', err)
  } finally {
    loadingCollections.value = false
  }
}

// Add library
async function handleAddLibrary() {
  try {
    addingLibrary.value = true

    let filename = newBibFilename.value.trim()
    if (!filename.endsWith('.bib')) {
      filename += '.bib'
    }

    const data = {
      library_type: selectedLibrary.value.library_type,
      library_id: selectedLibrary.value.library_id,
      library_name: selectedLibrary.value.name,
      collection_key: selectedCollection.value?.key || null,
      collection_name: selectedCollection.value?.name || null,
      bib_filename: filename,
      auto_sync_enabled: newAutoSync.value,
      auto_sync_interval_minutes: newSyncInterval.value
    }

    const result = await zoteroService.addWorkspaceLibrary(props.workspaceId, data)
    workspaceLibraries.value.push(result.library)

    showAddLibraryDialog.value = false
    resetAddForm()

    notify(result.message || 'Bibliothek hinzugefügt!')
    emit('library-added', result.library)
  } catch (err) {
    notify(err.response?.data?.error || 'Fehler beim Hinzufügen', 'error')
  } finally {
    addingLibrary.value = false
  }
}

// Reset add form
function resetAddForm() {
  selectedLibrary.value = null
  selectedCollection.value = null
  newBibFilename.value = 'references'
  newAutoSync.value = false
  newSyncInterval.value = 30
}

// Sync library
async function handleSync(lib) {
  try {
    syncingLibraryId.value = lib.id
    const result = await zoteroService.syncLibrary(props.workspaceId, lib.id)

    // Update library in list
    const index = workspaceLibraries.value.findIndex(l => l.id === lib.id)
    if (index >= 0) {
      workspaceLibraries.value[index] = result.library
    }

    notify(result.message || 'Synchronisiert!')
    emit('library-synced', result.library)
  } catch (err) {
    notify(err.response?.data?.error || 'Sync fehlgeschlagen', 'error')
  } finally {
    syncingLibraryId.value = null
  }
}

// Open settings dialog
function openSettings(lib) {
  editingLibrary.value = lib
  editAutoSync.value = lib.auto_sync_enabled
  editSyncInterval.value = lib.auto_sync_interval_minutes
  showSettingsDialog.value = true
}

// Save settings
async function handleSaveSettings() {
  try {
    savingSettings.value = true
    const result = await zoteroService.updateLibrarySettings(
      props.workspaceId,
      editingLibrary.value.id,
      {
        auto_sync_enabled: editAutoSync.value,
        auto_sync_interval_minutes: editSyncInterval.value
      }
    )

    // Update library in list
    const index = workspaceLibraries.value.findIndex(l => l.id === editingLibrary.value.id)
    if (index >= 0) {
      workspaceLibraries.value[index] = result.library
    }

    showSettingsDialog.value = false
    notify('Einstellungen gespeichert!')
  } catch (err) {
    notify(err.response?.data?.error || 'Speichern fehlgeschlagen', 'error')
  } finally {
    savingSettings.value = false
  }
}

// Confirm remove
function confirmRemove(lib) {
  removingLibrary.value = lib
  showRemoveDialog.value = true
}

// Remove library
async function handleRemove() {
  try {
    removing.value = true
    await zoteroService.removeWorkspaceLibrary(props.workspaceId, removingLibrary.value.id)

    workspaceLibraries.value = workspaceLibraries.value.filter(l => l.id !== removingLibrary.value.id)

    showRemoveDialog.value = false
    notify('Bibliothek entfernt')
    emit('library-removed', removingLibrary.value)
  } catch (err) {
    notify(err.response?.data?.error || 'Entfernen fehlgeschlagen', 'error')
  } finally {
    removing.value = false
    removingLibrary.value = null
  }
}

// Watch for add dialog open
watch(showAddLibraryDialog, (open) => {
  if (open && zoteroLibraries.value.length === 0) {
    loadZoteroLibraries()
  }
})

// Watch for library selection
watch(selectedLibrary, () => {
  selectedCollection.value = null
  loadCollections()
})

// Initial load
onMounted(async () => {
  await loadConnectionStatus()
  if (isConnected.value) {
    await loadWorkspaceLibraries()
  }
})

// Watch for connection changes
watch(isConnected, async (connected) => {
  if (connected) {
    await loadWorkspaceLibraries()
  }
})
</script>

<style scoped>
.zotero-panel {
  padding: 16px;
}

.zotero-section {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  padding: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-weight: 600;
  font-size: 1rem;
}

.connection-info {
  padding: 8px 0;
}

.connection-prompt {
  padding: 8px 0;
}

.connection-methods {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.method-card {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  padding: 16px;
}

.method-card.method-primary {
  background: rgba(var(--v-theme-primary), 0.08);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.method-title {
  font-weight: 500;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.method-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
}

.method-divider::before,
.method-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.12);
}

.empty-state {
  text-align: center;
  padding: 24px;
}

.libraries-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.library-card {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  padding: 12px;
}

.library-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.library-name {
  font-weight: 500;
}

.collection-name {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.library-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.library-sync-info {
  margin-bottom: 8px;
}

.library-error {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgb(var(--v-theme-error));
  font-size: 0.85rem;
  margin-bottom: 8px;
}

.library-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
