<template>
  <div class="llm-providers-section">
    <v-card class="mb-4 transparent-card" variant="outlined">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-connection</LIcon>
        Quick Connect
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col
            v-for="provider in quickProviders"
            :key="provider.type"
            cols="12"
            md="4"
          >
            <v-card variant="outlined" class="quick-card">
              <v-card-title class="text-subtitle-1">
                <LIcon class="mr-2" size="18">{{ provider.icon }}</LIcon>
                {{ provider.title }}
              </v-card-title>
              <v-card-subtitle>{{ provider.subtitle }}</v-card-subtitle>
              <v-card-text class="text-caption text-medium-emphasis">
                <div>Endpoint: {{ provider.base_url }}</div>
                <div v-if="provider.requires_key">API Key erforderlich</div>
                <div v-else>API Key optional</div>
              </v-card-text>
              <v-card-actions>
                <LBtn variant="primary" size="small" @click="openQuickDialog(provider)">
                  Quick Connect
                </LBtn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-database-cog</LIcon>
        Provider Registry
        <v-spacer />
        <LBtn variant="primary" size="small" @click="openCreateDialog">
          Provider hinzufügen
        </LBtn>
      </v-card-title>
      <v-card-text>
        <v-skeleton-loader v-if="loading" type="table"></v-skeleton-loader>

        <v-data-table
          v-else
          :headers="headers"
          :items="providers"
          :items-per-page="10"
        >
          <template v-slot:item.name="{ item }">
            <div class="d-flex flex-column">
              <span class="font-weight-medium">{{ item.name }}</span>
              <span class="text-caption text-medium-emphasis">{{ item.provider_type }}</span>
            </div>
          </template>

          <template v-slot:item.base_url="{ item }">
            <span class="text-caption">{{ item.base_url || '-' }}</span>
          </template>

          <template v-slot:item.is_default="{ item }">
            <v-chip v-if="item.is_default" color="primary" size="small" variant="tonal">
              Default
            </v-chip>
          </template>

          <template v-slot:item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'success' : 'warning'" size="small" variant="tonal">
              {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="d-flex ga-1 justify-end">
              <LBtn size="small" variant="text" @click="testProvider(item)">Test</LBtn>
              <LBtn
                size="small"
                variant="text"
                :disabled="!item.is_openai_compatible"
                @click="syncProvider(item)"
              >
                Sync
              </LBtn>
              <LBtn size="small" variant="text" @click="openEditDialog(item)">Bearbeiten</LBtn>
            </div>
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8 text-medium-emphasis">
              <LIcon size="48" class="mb-2">mdi-database-off</LIcon>
              <div>Keine Provider verbunden</div>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <v-card class="mt-4">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-brain</LIcon>
        LLM Modelle
      </v-card-title>
      <v-card-text>
        <v-skeleton-loader v-if="llmLoading" type="table"></v-skeleton-loader>

        <v-data-table
          v-else
          :headers="llmHeaders"
          :items="llmModelsFiltered"
          :items-per-page="10"
        >
          <template v-slot:item.display_name="{ item }">
            <div class="d-flex flex-column">
              <div class="d-flex align-center flex-wrap ga-2">
                <span class="font-weight-medium">{{ item.display_name }}</span>
                <v-chip
                  v-if="item.is_default"
                  color="primary"
                  size="x-small"
                  variant="tonal"
                >
                  Default
                </v-chip>
              </div>
              <span class="text-caption text-medium-emphasis">{{ item.model_id }}</span>
            </div>
          </template>

          <template v-slot:item.provider_label="{ item }">
            <div class="d-flex flex-column">
              <span class="font-weight-medium">
                {{ item.provider_label || item.provider || 'Unbekannt' }}
              </span>
              <span class="text-caption text-medium-emphasis">
                <span v-if="item.provider_type">{{ item.provider_type }}</span>
                <span v-else>manuell</span>
                <span v-if="item.provider_base_url"> · {{ item.provider_base_url }}</span>
              </span>
            </div>
          </template>

          <template v-slot:item.created_by="{ item }">
            <span class="text-caption text-medium-emphasis">
              {{ item.created_by || 'System' }}
            </span>
          </template>

          <template v-slot:item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'success' : 'warning'" size="small" variant="tonal">
              {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
          </template>

          <template v-slot:item.is_restricted="{ item }">
            <v-chip :color="item.is_restricted ? 'warning' : 'success'" size="small" variant="tonal">
              <LIcon start size="small">
                {{ item.is_restricted ? 'mdi-lock' : 'mdi-earth' }}
              </LIcon>
              {{ item.is_restricted ? 'Eingeschränkt' : 'Public' }}
            </v-chip>
          </template>

          <template v-slot:item.allowed_usernames="{ item }">
            <div class="d-flex flex-wrap gap-1">
              <v-chip
                v-for="r in (item.allowed_roles || []).slice(0, 3)"
                :key="'role-' + r"
                size="x-small"
                variant="tonal"
                color="secondary"
              >
                <LIcon start size="x-small">mdi-account-group</LIcon>
                {{ r }}
              </v-chip>
              <v-chip
                v-if="(item.allowed_roles || []).length > 3"
                size="x-small"
                variant="text"
              >
                +{{ (item.allowed_roles || []).length - 3 }} Rollen
              </v-chip>

              <v-chip
                v-for="u in (item.allowed_usernames || []).slice(0, 3)"
                :key="u"
                size="x-small"
                variant="tonal"
                color="primary"
              >
                {{ u }}
              </v-chip>
              <v-chip
                v-if="(item.allowed_usernames || []).length > 3"
                size="x-small"
                variant="text"
              >
                +{{ (item.allowed_usernames || []).length - 3 }}
              </v-chip>
              <span
                v-if="!item.is_restricted"
                class="text-caption text-medium-emphasis"
              >
                Öffentlich
              </span>
            </div>
          </template>

          <template v-slot:item.actions="{ item }">
            <LBtn size="small" variant="text" @click="openLlmAccessDialog(item)">
              Bearbeiten
            </LBtn>
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8 text-medium-emphasis">
              <LIcon size="48" class="mb-2">mdi-robot-off</LIcon>
              <div>Keine LLM Modelle gefunden</div>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Quick Connect Dialog -->
    <v-dialog v-model="quickDialog" max-width="640">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-connection</LIcon>
          Quick Connect: {{ activeQuick?.title }}
          <v-spacer />
          <LIconBtn icon="mdi-close" @click="quickDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-select
            v-model="providerForm.provider_type"
            :items="providerTypeOptions"
            item-title="title"
            item-value="value"
            label="Provider Typ"
            variant="outlined"
            density="comfortable"
            hide-details
          />
          <v-text-field
            v-model="providerForm.name"
            label="Name"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-text-field
            v-model="providerForm.base_url"
            label="Base URL"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-text-field
            v-if="activeQuick?.requires_key"
            v-model="providerForm.api_key"
            label="API Key"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-text-field
            v-if="activeQuick?.supports_version"
            v-model="providerForm.api_version"
            label="API Version"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-textarea
            v-if="activeQuick?.requires_models"
            v-model="providerForm.model_ids"
            label="Model IDs (kommagetrennt)"
            variant="outlined"
            density="comfortable"
            rows="2"
            auto-grow
            hide-details
            class="mt-3"
          />
          <v-switch
            v-model="providerForm.is_default"
            label="Als Default Provider setzen"
            color="primary"
            hide-details
            class="mt-2"
          />
          <v-switch
            v-if="activeQuick?.supports_sync"
            v-model="providerForm.sync_models"
            label="Modelle automatisch synchronisieren"
            color="primary"
            hide-details
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="quickDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="saving" @click="submitQuickConnect">
            Verbinden
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Provider Dialog -->
    <v-dialog v-model="editDialog" max-width="640">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-pencil</LIcon>
          Provider bearbeiten
          <v-spacer />
          <LIconBtn icon="mdi-close" @click="editDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-text-field
            v-model="providerForm.name"
            label="Name"
            variant="outlined"
            density="comfortable"
            hide-details
          />
          <v-text-field
            v-model="providerForm.base_url"
            label="Base URL"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-text-field
            v-model="providerForm.api_key"
            label="API Key (leer lassen = unverändert)"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-text-field
            v-model="providerForm.api_version"
            label="API Version"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <v-textarea
            v-model="providerForm.model_ids"
            label="Model IDs (kommagetrennt)"
            variant="outlined"
            density="comfortable"
            rows="2"
            auto-grow
            hide-details
            class="mt-3"
          />
          <v-switch
            v-model="providerForm.is_default"
            label="Als Default Provider setzen"
            color="primary"
            hide-details
            class="mt-2"
          />
          <v-switch
            v-model="providerForm.is_active"
            label="Provider aktiv"
            color="primary"
            hide-details
          />
          <v-switch
            v-model="providerForm.is_openai_compatible"
            label="OpenAI-kompatibel"
            color="primary"
            hide-details
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="editDialog = false">Schließen</LBtn>
          <LBtn variant="primary" :loading="saving" @click="saveProvider">
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>

    <v-dialog v-model="llmAccessDialog" max-width="700">
      <v-card v-if="selectedLlmModel">
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-brain</LIcon>
          Zugriff: {{ selectedLlmModel.display_name }}
          <v-spacer />
          <v-chip
            v-if="selectedLlmModel.is_default"
            color="primary"
            size="x-small"
            variant="tonal"
            class="mr-2"
          >
            Default
          </v-chip>
          <LIconBtn icon="mdi-close" @click="llmAccessDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <div class="text-caption text-medium-emphasis mb-3">
            <div>
              Quelle:
              <strong>{{ selectedLlmModel.provider_label || selectedLlmModel.provider || 'Unbekannt' }}</strong>
              <span v-if="selectedLlmModel.provider_type">({{ selectedLlmModel.provider_type }})</span>
            </div>
            <div v-if="selectedLlmModel.provider_base_url">
              Endpoint: {{ selectedLlmModel.provider_base_url }}
            </div>
            <div>
              Erstellt von: {{ selectedLlmModel.created_by || 'System' }}
            </div>
          </div>

          <v-switch
            v-model="llmIsPublic"
            label="Public (für alle sichtbar)"
            color="primary"
            hide-details
            class="mb-3"
          />

          <v-alert
            v-if="llmIsPublic"
            type="info"
            variant="tonal"
            class="mb-4"
          >
            Dieses Modell ist öffentlich sichtbar. Sobald Benutzer/Rollen gesetzt werden,
            ist es eingeschränkt.
          </v-alert>

          <v-autocomplete
            v-model="llmAccessUsernames"
            :items="allUsernames"
            label="Erlaubte Nutzer"
            multiple
            chips
            closable-chips
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
            :disabled="llmIsPublic"
          />
          <v-autocomplete
            v-model="llmAccessRoleNames"
            :items="roles"
            item-title="display_name"
            item-value="role_name"
            label="Erlaubte Rollen (Nutzergruppen)"
            multiple
            chips
            closable-chips
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
            :disabled="llmIsPublic"
          />
          <div class="text-caption text-medium-emphasis mt-2">
            Tipp: Rollen sind Nutzergruppen im LLARS Permission-System.
          </div>
          <v-alert
            v-if="!llmIsPublic && !llmAccessUsernames.length && !llmAccessRoleNames.length"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-2"
          >
            Ohne Auswahl bleibt das Modell faktisch öffentlich sichtbar.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="llmAccessDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="savingLlmAccess" @click="saveLlmAccess">
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import axios from 'axios'

const providers = ref([])
const loading = ref(false)
const saving = ref(false)

const llmModels = ref([])
const llmLoading = ref(false)
const llmAccessDialog = ref(false)
const selectedLlmModel = ref(null)
const llmAccessUsernames = ref([])
const llmAccessRoleNames = ref([])
const savingLlmAccess = ref(false)
const roles = ref([])
const allUsernames = ref([])
const llmIsPublic = ref(true)

const quickDialog = ref(false)
const editDialog = ref(false)
const activeQuick = ref(null)

const providerForm = ref({
  id: null,
  provider_type: '',
  name: '',
  base_url: '',
  api_key: '',
  api_version: '',
  model_ids: '',
  is_default: false,
  is_active: true,
  is_openai_compatible: true,
  sync_models: false
})

const snackbar = ref({ show: false, text: '', color: 'info' })

const headers = [
  { title: 'Provider', key: 'name', sortable: true },
  { title: 'Base URL', key: 'base_url', sortable: false },
  { title: 'Default', key: 'is_default', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: '', key: 'actions', sortable: false, align: 'end' }
]

const llmHeaders = [
  { title: 'Modell', key: 'display_name', sortable: true },
  { title: 'Quelle', key: 'provider_label', sortable: true },
  { title: 'Erstellt von', key: 'created_by', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Sichtbarkeit', key: 'is_restricted', sortable: true },
  { title: 'Zuweisungen', key: 'allowed_usernames', sortable: false },
  { title: '', key: 'actions', sortable: false, align: 'end' }
]

const quickProviders = [
  {
    type: 'openai',
    title: 'OpenAI',
    subtitle: 'ChatGPT, GPT-4o, o3',
    base_url: 'https://api.openai.com/v1',
    icon: 'mdi-openai',
    requires_key: true,
    supports_sync: true
  },
  {
    type: 'ollama',
    title: 'Ollama',
    subtitle: 'Lokale Modelle (OpenAI kompatibel)',
    base_url: 'http://localhost:11434/v1',
    icon: 'mdi-server',
    requires_key: false,
    supports_sync: true
  },
  {
    type: 'vllm',
    title: 'vLLM',
    subtitle: 'Self-hosted OpenAI Endpoint',
    base_url: 'http://localhost:8000/v1',
    icon: 'mdi-server-network',
    requires_key: false,
    supports_sync: true
  },
  {
    type: 'anthropic',
    title: 'Claude (Anthropic)',
    subtitle: 'Claude 3.x API',
    base_url: 'https://api.anthropic.com',
    icon: 'mdi-lightning-bolt',
    requires_key: true,
    requires_models: true,
    supports_version: true,
    supports_sync: false
  },
  {
    type: 'gemini',
    title: 'Google Gemini',
    subtitle: 'Gemini 1.5 / 2.0 API',
    base_url: 'https://generativelanguage.googleapis.com',
    icon: 'mdi-google',
    requires_key: true,
    requires_models: true,
    supports_version: true,
    supports_sync: false
  },
  {
    type: 'litellm',
    title: 'LiteLLM Proxy',
    subtitle: 'OpenAI-kompatibler Gateway',
    base_url: 'https://kiz1.in.ohmportal.de/llmproxy/v1',
    icon: 'mdi-gate',
    requires_key: false,
    supports_sync: true
  }
]

function resetProviderForm() {
  providerForm.value = {
    id: null,
    provider_type: '',
    name: '',
    base_url: '',
    api_key: '',
    api_version: '',
    model_ids: '',
    is_default: false,
    is_active: true,
    is_openai_compatible: true,
    sync_models: false
  }
}

function showMessage(text, color = 'info') {
  snackbar.value = { show: true, text, color }
}

const providerTypeOptions = [
  { title: 'OpenAI', value: 'openai' },
  { title: 'OpenAI kompatibel', value: 'openai_compatible' },
  { title: 'Ollama', value: 'ollama' },
  { title: 'vLLM', value: 'vllm' },
  { title: 'LiteLLM Proxy', value: 'litellm' },
  { title: 'Anthropic (Claude)', value: 'anthropic' },
  { title: 'Google Gemini', value: 'gemini' },
  { title: 'Custom', value: 'custom' }
]

const llmModelsFiltered = computed(() => {
  return (llmModels.value || []).filter(model => model.model_type === 'llm')
})

async function fetchProviders() {
  loading.value = true
  try {
    const response = await axios.get('/api/llm/providers')
    providers.value = response.data.providers || []
  } catch (error) {
    console.error('Error loading providers:', error)
    providers.value = []
  } finally {
    loading.value = false
  }
}

function openQuickDialog(template) {
  resetProviderForm()
  activeQuick.value = template
  providerForm.value.provider_type = template.type
  providerForm.value.name = template.title
  providerForm.value.base_url = template.base_url
  providerForm.value.is_openai_compatible = template.supports_sync === true || template.type === 'openai'
  providerForm.value.is_active = true
  providerForm.value.is_default = false
  providerForm.value.sync_models = Boolean(template.supports_sync)
  if (template.supports_version) {
    providerForm.value.api_version = template.type === 'anthropic' ? '2023-06-01' : 'v1beta'
  }
  quickDialog.value = true
}

function openCreateDialog() {
  resetProviderForm()
  activeQuick.value = null
  editDialog.value = true
}

function openEditDialog(provider) {
  resetProviderForm()
  providerForm.value.id = provider.id
  providerForm.value.provider_type = provider.provider_type
  providerForm.value.name = provider.name
  providerForm.value.base_url = provider.base_url || ''
  providerForm.value.is_default = provider.is_default
  providerForm.value.is_active = provider.is_active
  providerForm.value.is_openai_compatible = provider.is_openai_compatible
  providerForm.value.api_version = provider.config?.api_version || ''
  editDialog.value = true
}

function parseModelIds(input) {
  return (input || '')
    .split(/[,\n]/)
    .map(s => s.trim())
    .filter(Boolean)
}

async function submitQuickConnect() {
  saving.value = true
  try {
    const payload = {
      provider_type: providerForm.value.provider_type,
      name: providerForm.value.name,
      base_url: providerForm.value.base_url,
      is_default: providerForm.value.is_default,
      is_active: providerForm.value.is_active,
      is_openai_compatible: providerForm.value.is_openai_compatible,
      sync_models: providerForm.value.sync_models,
      model_ids: parseModelIds(providerForm.value.model_ids),
      config: providerForm.value.api_version
        ? { api_version: providerForm.value.api_version }
        : {}
    }
    if (providerForm.value.api_key) {
      payload.api_key = providerForm.value.api_key
    }
    await axios.post('/api/llm/providers', payload)
    showMessage('Provider verbunden', 'success')
    quickDialog.value = false
    await fetchProviders()
  } catch (error) {
    console.error('Quick connect failed:', error)
    showMessage('Quick Connect fehlgeschlagen', 'error')
  } finally {
    saving.value = false
  }
}

async function saveProvider() {
  saving.value = true
  try {
    if (!providerForm.value.provider_type) {
      showMessage('Provider Typ erforderlich', 'error')
      saving.value = false
      return
    }
    const payload = {
      provider_type: providerForm.value.provider_type,
      name: providerForm.value.name,
      base_url: providerForm.value.base_url,
      is_default: providerForm.value.is_default,
      is_active: providerForm.value.is_active,
      is_openai_compatible: providerForm.value.is_openai_compatible,
      model_ids: parseModelIds(providerForm.value.model_ids),
      config: providerForm.value.api_version
        ? { api_version: providerForm.value.api_version }
        : {}
    }
    if (providerForm.value.api_key) {
      payload.api_key = providerForm.value.api_key
    }

    if (providerForm.value.id) {
      await axios.put(`/api/llm/providers/${providerForm.value.id}`, payload)
    } else {
      await axios.post('/api/llm/providers', payload)
    }
    showMessage('Provider gespeichert', 'success')
    editDialog.value = false
    await fetchProviders()
  } catch (error) {
    console.error('Save provider failed:', error)
    showMessage('Speichern fehlgeschlagen', 'error')
  } finally {
    saving.value = false
  }
}

async function testProvider(provider) {
  try {
    const response = await axios.post(`/api/llm/providers/${provider.id}/test`)
    showMessage(response.data.message || 'Verbindung OK', 'success')
  } catch (error) {
    console.error('Provider test failed:', error)
    showMessage(error.response?.data?.error || 'Verbindung fehlgeschlagen', 'error')
  }
}

async function syncProvider(provider) {
  try {
    const response = await axios.post(`/api/llm/providers/${provider.id}/sync-models`)
    showMessage(`Sync: ${response.data.inserted || 0} neu`, 'success')
  } catch (error) {
    console.error('Model sync failed:', error)
    showMessage(error.response?.data?.error || 'Sync fehlgeschlagen', 'error')
  }
}

async function fetchLlmAccessOverview() {
  llmLoading.value = true
  try {
    const response = await axios.get('/api/llm/models/access/overview?include_inactive=true')
    llmModels.value = response.data.models || []
  } catch (error) {
    console.error('Error loading LLM models:', error)
    llmModels.value = []
  } finally {
    llmLoading.value = false
  }
}

async function fetchRoles() {
  try {
    const response = await axios.get('/api/permissions/roles')
    roles.value = response.data.roles || []
  } catch (error) {
    console.error('Error loading roles:', error)
    roles.value = []
  }
}

async function fetchUsersForAccess() {
  try {
    const response = await axios.get('/api/permissions/users-with-roles')
    const users = response.data.users || response.data.data || []
    allUsernames.value = users.map(u => u.username).filter(Boolean).sort()
  } catch (error) {
    console.error('Error loading users:', error)
    allUsernames.value = []
  }
}

async function openLlmAccessDialog(model) {
  selectedLlmModel.value = model
  llmAccessUsernames.value = [...(model.allowed_usernames || [])]
  llmAccessRoleNames.value = [...(model.allowed_roles || [])]
  llmIsPublic.value = !llmAccessUsernames.value.length && !llmAccessRoleNames.value.length
  llmAccessDialog.value = true

  if (!allUsernames.value.length) {
    await fetchUsersForAccess()
  }
  if (!roles.value.length) {
    await fetchRoles()
  }
}

watch(llmIsPublic, (value) => {
  if (value) {
    llmAccessUsernames.value = []
    llmAccessRoleNames.value = []
  }
})

async function saveLlmAccess() {
  if (!selectedLlmModel.value) return
  savingLlmAccess.value = true
  try {
    const response = await axios.put(`/api/llm/models/${selectedLlmModel.value.id}/access`, {
      usernames: llmAccessUsernames.value,
      role_names: llmAccessRoleNames.value
    })
    const updatedUsers = response.data.allowed_usernames || []
    const updatedRoles = response.data.allowed_roles || []
    selectedLlmModel.value.allowed_usernames = updatedUsers
    selectedLlmModel.value.allowed_roles = updatedRoles
    selectedLlmModel.value.is_restricted = Boolean(updatedUsers.length || updatedRoles.length)
    llmIsPublic.value = !selectedLlmModel.value.is_restricted
    await fetchLlmAccessOverview()
    llmAccessDialog.value = false
  } catch (error) {
    console.error('Error saving LLM access:', error)
    showMessage('Zugriff speichern fehlgeschlagen', 'error')
  } finally {
    savingLlmAccess.value = false
  }
}

onMounted(() => {
  fetchProviders()
  fetchLlmAccessOverview()
})
</script>

<style scoped>
.quick-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;
}

.transparent-card {
  background-color: transparent;
  box-shadow: none;
}
</style>
