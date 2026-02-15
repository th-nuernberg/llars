<template>
  <div class="llm-providers">
    <!-- Info Banner -->
    <v-alert type="info" variant="tonal" class="mb-4" density="compact">
      <template #prepend>
        <v-icon>mdi-information</v-icon>
      </template>
      {{ $t('userSettings.providers.info') }}
    </v-alert>

    <!-- Provider List -->
    <LCard :title="$t('userSettings.providers.myProviders')" icon="mdi-key-chain" class="mb-4">
      <template #actions>
        <LBtn variant="primary" size="small" @click="openCreateDialog">
          <v-icon start>mdi-plus</v-icon>
          {{ $t('userSettings.providers.addProvider') }}
        </LBtn>
      </template>

      <div v-if="loading" class="loading-state">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-else-if="providers.length === 0" class="empty-state">
        <v-icon size="48" color="grey">mdi-api-off</v-icon>
        <p>{{ $t('userSettings.providers.noProviders') }}</p>
        <LBtn variant="secondary" @click="openCreateDialog">
          {{ $t('userSettings.providers.addFirstProvider') }}
        </LBtn>
      </div>

      <div v-else class="providers-list">
        <div
          v-for="provider in providers"
          :key="provider.id"
          class="provider-card"
          :class="{ inactive: !provider.is_active, default: provider.is_default }"
        >
          <div class="provider-icon">
            <v-icon :color="getProviderColor(provider.provider_type)">
              {{ getProviderIcon(provider.provider_type) }}
            </v-icon>
          </div>

          <div class="provider-info">
            <div class="provider-name">
              {{ provider.name }}
              <LTag v-if="provider.is_default" variant="success" size="sm">Default</LTag>
              <LTag v-if="provider.is_shared" variant="info" size="sm">
                <v-icon size="x-small">mdi-share-variant</v-icon>
                {{ provider.share_count || 0 }}
              </LTag>
            </div>
            <div class="provider-meta">
              <span class="provider-type">{{ getProviderTypeName(provider.provider_type) }}</span>
              <span v-if="provider.base_url" class="provider-url">{{ truncateUrl(provider.base_url) }}</span>
              <span v-if="provider.config?.selected_models?.length" class="provider-model">
                {{ provider.config.selected_models.join(', ') }}
              </span>
              <span v-else-if="provider.config?.model_id" class="provider-model">{{ provider.config.model_id }}</span>
            </div>
            <div class="provider-stats">
              <span v-if="provider.total_requests > 0">
                {{ provider.total_requests }} {{ $t('userSettings.providers.requests') }}
              </span>
              <span v-if="provider.last_used_at" class="last-used">
                {{ $t('userSettings.providers.lastUsed') }}: {{ formatDate(provider.last_used_at) }}
              </span>
            </div>
          </div>

          <div class="provider-status">
            <v-icon v-if="provider.api_key_set" color="success" size="small">mdi-check-circle</v-icon>
            <v-icon v-else color="warning" size="small">mdi-alert-circle</v-icon>
          </div>

          <div class="provider-actions">
            <v-menu>
              <template #activator="{ props }">
                <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props" />
              </template>
              <v-list density="compact">
                <v-list-item @click="testProvider(provider)">
                  <template #prepend><v-icon size="small">mdi-connection</v-icon></template>
                  <v-list-item-title>{{ $t('userSettings.providers.test') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="editProvider(provider)">
                  <template #prepend><v-icon size="small">mdi-pencil</v-icon></template>
                  <v-list-item-title>{{ $t('common.edit') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="openShareDialog(provider)">
                  <template #prepend><v-icon size="small">mdi-share-variant</v-icon></template>
                  <v-list-item-title>{{ $t('userSettings.providers.share') }}</v-list-item-title>
                </v-list-item>
                <v-list-item v-if="!provider.is_default" @click="setDefault(provider)">
                  <template #prepend><v-icon size="small">mdi-star</v-icon></template>
                  <v-list-item-title>{{ $t('userSettings.providers.setDefault') }}</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="deleteProvider(provider)" class="text-error">
                  <template #prepend><v-icon size="small" color="error">mdi-delete</v-icon></template>
                  <v-list-item-title>{{ $t('common.delete') }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </div>
    </LCard>

    <!-- Shared With Me -->
    <LCard v-if="sharedProviders.length > 0" :title="$t('userSettings.providers.sharedWithMe')" icon="mdi-account-group">
      <div class="providers-list">
        <div
          v-for="provider in sharedProviders"
          :key="'shared-' + provider.id"
          class="provider-card shared"
        >
          <div class="provider-icon">
            <v-icon :color="getProviderColor(provider.provider_type)">
              {{ getProviderIcon(provider.provider_type) }}
            </v-icon>
          </div>

          <div class="provider-info">
            <div class="provider-name">
              {{ provider.name }}
              <LTag variant="gray" size="sm">
                von {{ provider.shared_by }}
              </LTag>
            </div>
            <div class="provider-meta">
              <span class="provider-type">{{ getProviderTypeName(provider.provider_type) }}</span>
              <span v-if="provider.config?.selected_models?.length" class="provider-model">
                {{ provider.config.selected_models.join(', ') }}
              </span>
              <span v-else-if="provider.config?.model_id" class="provider-model">{{ provider.config.model_id }}</span>
            </div>
          </div>
        </div>
      </div>
    </LCard>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon start>{{ editingProvider ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          {{ editingProvider ? $t('userSettings.providers.editProvider') : $t('userSettings.providers.addProvider') }}
        </v-card-title>

        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <v-select
              v-model="form.provider_type"
              :items="providerTypes"
              item-title="name"
              item-value="id"
              :label="$t('userSettings.providers.form.type')"
              :rules="[v => !!v || $t('userSettings.providers.form.typeRequired')]"
              variant="outlined"
              density="comfortable"
              :disabled="!!editingProvider"
            >
              <template #item="{ item, props }">
                <v-list-item v-bind="props">
                  <template #prepend>
                    <v-icon :color="getProviderColor(item.value)">{{ getProviderIcon(item.value) }}</v-icon>
                  </template>
                  <v-list-item-subtitle>{{ item.raw.description }}</v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-select>

            <!-- Name field: hidden for OpenAI (auto-generated) -->
            <v-text-field
              v-if="form.provider_type !== 'openai'"
              v-model="form.name"
              :label="$t('userSettings.providers.form.name')"
              :rules="[v => !!v || $t('userSettings.providers.form.nameRequired')]"
              variant="outlined"
              density="comfortable"
              :placeholder="$t('userSettings.providers.form.namePlaceholder')"
            />

            <v-text-field
              v-model="form.api_key"
              :label="$t('userSettings.providers.form.apiKey')"
              :type="showApiKey ? 'text' : 'password'"
              variant="outlined"
              density="comfortable"
              :placeholder="editingProvider ? $t('userSettings.providers.form.apiKeyUnchanged') : 'sk-...'"
              :append-inner-icon="showApiKey ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showApiKey = !showApiKey"
            />

            <!-- OpenAI: Multi-select dropdown with predefined models -->
            <v-select
              v-if="form.provider_type === 'openai'"
              v-model="form.selected_models"
              :items="openaiModelCatalog"
              item-title="title"
              item-value="id"
              label="OpenAI Modelle"
              variant="outlined"
              density="comfortable"
              multiple
              chips
              closable-chips
              hint="Modelle auswählen die verfügbar sein sollen"
              persistent-hint
            >
              <template #item="{ item, props }">
                <v-list-item v-bind="props">
                  <template #append>
                    <span class="text-caption text-medium-emphasis">{{ item.raw.meta }}</span>
                  </template>
                </v-list-item>
              </template>
            </v-select>

            <v-text-field
              v-if="selectedProviderType?.supports_base_url && form.provider_type !== 'openai'"
              v-model="form.base_url"
              :label="$t('userSettings.providers.form.baseUrl')"
              variant="outlined"
              density="comfortable"
              :placeholder="selectedProviderType?.default_base_url"
            />

            <v-switch
              v-model="form.is_default"
              :label="$t('userSettings.providers.form.setAsDefault')"
              color="primary"
              density="compact"
              hide-details
            />
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="saving" :disabled="!formValid" @click="saveProvider">
            {{ editingProvider ? $t('common.save') : $t('common.create') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Share Dialog -->
    <v-dialog v-model="showShareDialog" max-width="500">
      <v-card v-if="sharingProvider">
        <v-card-title>
          <v-icon start>mdi-share-variant</v-icon>
          {{ $t('userSettings.providers.shareTitle', { name: sharingProvider.name }) }}
        </v-card-title>

        <v-card-text>
          <!-- Existing Shares -->
          <div v-if="sharingProvider.shares?.length > 0" class="mb-4">
            <div class="text-subtitle-2 mb-2">{{ $t('userSettings.providers.currentShares') }}</div>
            <v-chip
              v-for="share in sharingProvider.shares"
              :key="share.id"
              class="mr-2 mb-2"
              closable
              @click:close="removeShare(share)"
            >
              <v-icon start size="small">
                {{ share.share_type === 'user' ? 'mdi-account' : 'mdi-account-group' }}
              </v-icon>
              {{ share.target_identifier }}
            </v-chip>
          </div>

          <!-- Share with All Toggle -->
          <v-switch
            v-model="sharingProvider.share_with_all"
            :label="$t('userSettings.providers.shareWithAll')"
            color="primary"
            @change="toggleShareAll"
          />

          <v-divider class="my-4" />

          <!-- Add Share -->
          <div class="text-subtitle-2 mb-2">{{ $t('userSettings.providers.addShare') }}</div>
          <v-btn-toggle v-model="newShare.type" mandatory density="compact" class="mb-3" color="primary">
            <v-btn value="user" size="small">
              <v-icon start size="small">mdi-account</v-icon>
              {{ $t('userSettings.providers.shareTypeUser') }}
            </v-btn>
            <v-btn value="role" size="small">
              <v-icon start size="small">mdi-account-group</v-icon>
              {{ $t('userSettings.providers.shareTypeRole') }}
            </v-btn>
          </v-btn-toggle>

          <!-- User search (with autocomplete) -->
          <LUserSearch
            v-if="newShare.type === 'user'"
            ref="userSearchRef"
            :exclude-usernames="existingShareUsernames"
            :placeholder="$t('userSettings.providers.username')"
            density="compact"
            :show-add-button="true"
            :add-button-text="$t('userSettings.providers.share')"
            button-size="small"
            @add="addUserShare"
          />

          <!-- Role input (free text) -->
          <div v-else class="d-flex gap-2">
            <v-text-field
              v-model="newShare.target"
              :label="$t('userSettings.providers.roleName')"
              variant="outlined"
              density="compact"
              hide-details
              class="flex-grow-1"
            />
            <LBtn variant="primary" :disabled="!newShare.target" @click="addShare">
              <v-icon>mdi-plus</v-icon>
            </LBtn>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showShareDialog = false">{{ $t('common.close') }}</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import LCard from '@/components/common/LCard.vue'
import LBtn from '@/components/common/LBtn.vue'
import LTag from '@/components/common/LTag.vue'
import LUserSearch from '@/components/common/LUserSearch.vue'
import axios from 'axios'

const { t } = useI18n()

const loading = ref(true)
const saving = ref(false)
const providers = ref([])
const sharedProviders = ref([])
const providerTypes = ref([])

const showDialog = ref(false)
const editingProvider = ref(null)
const formRef = ref(null)
const formValid = ref(false)
const showApiKey = ref(false)

const form = ref({
  provider_type: '',
  name: '',
  api_key: '',
  base_url: '',
  is_default: false,
  selected_models: []
})

const openaiModelCatalog = [
  { id: 'gpt-5.2', title: 'GPT-5.2', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5.1', title: 'GPT-5.1', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5', title: 'GPT-5', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5-mini', title: 'GPT-5 Mini', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-5-nano', title: 'GPT-5 Nano', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: false, supports_reasoning: false },
  { id: 'gpt-4.1', title: 'GPT-4.1', meta: '1M ctx · 32K out', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4.1-mini', title: 'GPT-4.1 Mini', meta: '1M ctx · 32K out', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4.1-nano', title: 'GPT-4.1 Nano', meta: '1M ctx · 32K out', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4o', title: 'GPT-4o', meta: '128K ctx · 16K out', context_window: 128000, max_output_tokens: 16384, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4o-mini', title: 'GPT-4o Mini', meta: '128K ctx · 16K out', context_window: 128000, max_output_tokens: 16384, supports_vision: true, supports_reasoning: false },
  { id: 'o3', title: 'o3', meta: '200K ctx · 100K out', context_window: 200000, max_output_tokens: 100000, supports_vision: true, supports_reasoning: true },
  { id: 'o3-mini', title: 'o3 Mini', meta: '200K ctx · 100K out', context_window: 200000, max_output_tokens: 100000, supports_vision: false, supports_reasoning: true },
  { id: 'o4-mini', title: 'o4 Mini', meta: '200K ctx · 100K out', context_window: 200000, max_output_tokens: 100000, supports_vision: true, supports_reasoning: true },
]

const showShareDialog = ref(false)
const sharingProvider = ref(null)
const newShare = ref({ type: 'user', target: '' })
const userSearchRef = ref(null)

const existingShareUsernames = computed(() => {
  const shares = sharingProvider.value?.shares || []
  return shares
    .filter(s => s.share_type === 'user')
    .map(s => s.target_identifier)
})

const selectedProviderType = computed(() => {
  return providerTypes.value.find(t => t.id === form.value.provider_type)
})

onMounted(async () => {
  await Promise.all([loadProviders(), loadProviderTypes()])
})

async function loadProviders() {
  loading.value = true
  try {
    const [ownResponse, availableResponse] = await Promise.all([
      axios.get('/api/user/providers'),
      axios.get('/api/user/providers/available')
    ])

    providers.value = ownResponse.data.providers
    sharedProviders.value = availableResponse.data.providers.filter(p => p.source !== 'own')
  } catch (error) {
    console.error('Failed to load providers:', error)
  } finally {
    loading.value = false
  }
}

async function loadProviderTypes() {
  try {
    const response = await axios.get('/api/user/providers/types')
    providerTypes.value = response.data.types
  } catch (error) {
    console.error('Failed to load provider types:', error)
  }
}


function openCreateDialog() {
  editingProvider.value = null
  form.value = {
    provider_type: '',
    name: '',
    api_key: '',
    base_url: '',
    is_default: false,
    selected_models: []
  }
  showApiKey.value = false
  showDialog.value = true
}

function editProvider(provider) {
  editingProvider.value = provider
  form.value = {
    provider_type: provider.provider_type,
    name: provider.name,
    api_key: '',
    base_url: provider.base_url || '',
    is_default: provider.is_default,
    selected_models: provider.config?.selected_models || []
  }
  showApiKey.value = false
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  editingProvider.value = null
}

async function saveProvider() {
  if (!formRef.value?.validate()) return

  saving.value = true
  try {
    const isOpenai = form.value.provider_type === 'openai'

    const payload = {
      provider_type: form.value.provider_type,
      name: isOpenai ? 'OpenAI' : form.value.name,
      base_url: isOpenai ? null : (form.value.base_url || null),
      is_default: form.value.is_default
    }

    if (form.value.api_key) {
      payload.api_key = form.value.api_key
    }

    if (isOpenai) {
      payload.config = { selected_models: form.value.selected_models || [] }
    }

    if (editingProvider.value) {
      await axios.put(`/api/user/providers/${editingProvider.value.id}`, payload)
    } else {
      await axios.post('/api/user/providers', payload)
    }

    await loadProviders()
    closeDialog()
  } catch (error) {
    console.error('Failed to save provider:', error)
  } finally {
    saving.value = false
  }
}

async function deleteProvider(provider) {
  if (!confirm(t('userSettings.providers.deleteConfirm', { name: provider.name }))) return

  try {
    await axios.delete(`/api/user/providers/${provider.id}`)
    await loadProviders()
  } catch (error) {
    console.error('Failed to delete provider:', error)
  }
}

async function setDefault(provider) {
  try {
    await axios.put(`/api/user/providers/${provider.id}`, { is_default: true })
    await loadProviders()
  } catch (error) {
    console.error('Failed to set default:', error)
  }
}

async function testProvider(provider) {
  try {
    const response = await axios.post(`/api/user/providers/${provider.id}/test`)
    alert(response.data.success
      ? t('userSettings.providers.testSuccess')
      : t('userSettings.providers.testFailed', { error: response.data.message }))
  } catch (error) {
    alert(t('userSettings.providers.testFailed', { error: error.response?.data?.message || error.message }))
  }
}

function openShareDialog(provider) {
  sharingProvider.value = { ...provider }
  newShare.value = { type: 'user', target: '' }
  showShareDialog.value = true
}

async function addShare() {
  if (!newShare.value.target) return

  try {
    await axios.post(`/api/user/providers/${sharingProvider.value.id}/shares`, {
      share_type: newShare.value.type,
      target_identifier: newShare.value.target
    })

    newShare.value.target = ''
    await loadProviders()

    // Refresh sharing provider data
    const updated = providers.value.find(p => p.id === sharingProvider.value.id)
    if (updated) sharingProvider.value = { ...updated }
  } catch (error) {
    console.error('Failed to add share:', error)
    alert(error.response?.data?.message || t('common.error'))
  }
}

async function addUserShare(user) {
  if (!user?.username) return

  try {
    await axios.post(`/api/user/providers/${sharingProvider.value.id}/shares`, {
      share_type: 'user',
      target_identifier: user.username
    })

    userSearchRef.value?.reset()
    await loadProviders()

    const updated = providers.value.find(p => p.id === sharingProvider.value.id)
    if (updated) sharingProvider.value = { ...updated }
  } catch (error) {
    console.error('Failed to add user share:', error)
    userSearchRef.value?.setAdding(false)
    alert(error.response?.data?.message || t('common.error'))
  }
}

async function removeShare(share) {
  try {
    await axios.delete(`/api/user/providers/${sharingProvider.value.id}/shares/${share.id}`)
    await loadProviders()

    const updated = providers.value.find(p => p.id === sharingProvider.value.id)
    if (updated) sharingProvider.value = { ...updated }
  } catch (error) {
    console.error('Failed to remove share:', error)
  }
}

async function toggleShareAll() {
  try {
    await axios.post(`/api/user/providers/${sharingProvider.value.id}/share-all`, {
      share_with_all: sharingProvider.value.share_with_all
    })
    await loadProviders()
  } catch (error) {
    console.error('Failed to toggle share all:', error)
  }
}

function getProviderIcon(type) {
  const icons = {
    openai: 'mdi-robot',
    anthropic: 'mdi-head-cog',
    gemini: 'mdi-google',
    azure: 'mdi-microsoft-azure',
    ollama: 'mdi-server',
    litellm: 'mdi-lightning-bolt',
    custom: 'mdi-api'
  }
  return icons[type] || 'mdi-api'
}

function getProviderColor(type) {
  const colors = {
    openai: '#00A67E',
    anthropic: '#D4A574',
    gemini: '#4285F4',
    azure: '#0078D4',
    ollama: '#6B7280',
    litellm: '#F59E0B',
    custom: '#8B5CF6'
  }
  return colors[type] || '#6B7280'
}

function getProviderTypeName(type) {
  const names = {
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gemini: 'Google Gemini',
    azure: 'Azure OpenAI',
    ollama: 'Ollama',
    litellm: 'LiteLLM',
    custom: 'Custom'
  }
  return names[type] || type
}

function truncateUrl(url) {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    return parsed.hostname
  } catch {
    return url.substring(0, 30) + '...'
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}
</script>

<style scoped>
.llm-providers {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 16px;
  text-align: center;
}

.empty-state p {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.providers-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: all 0.2s;
}

.provider-card:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.provider-card.default {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background: rgba(var(--v-theme-primary), 0.05);
}

.provider-card.inactive {
  opacity: 0.6;
}

.provider-card.shared {
  background: rgba(var(--v-theme-info), 0.05);
  border-color: rgba(var(--v-theme-info), 0.2);
}

.provider-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-name {
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.provider-meta {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  gap: 12px;
  margin-top: 2px;
}

.provider-stats {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
  display: flex;
  gap: 12px;
}
</style>
