<template>
  <div class="api-keys-settings" role="region" aria-label="API Key Verwaltung">
    <!-- Info Section -->
    <section class="settings-panel info-panel" role="group">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-information-outline</LIcon>
        <h2 class="panel-title">{{ $t('userSettings.apiKeys.infoTitle') }}</h2>
      </header>
      <div class="panel-content">
        <p class="info-text">{{ $t('userSettings.apiKeys.infoText') }}</p>
        <div class="usage-examples">
          <code class="usage-code">X-API-Key: &lt;your-api-key&gt;</code>
          <code class="usage-code">Authorization: Bearer &lt;your-api-key&gt;</code>
        </div>
      </div>
    </section>

    <!-- Create New Key Section -->
    <section class="settings-panel" role="group" aria-labelledby="create-key-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-plus-circle</LIcon>
        <h2 id="create-key-title" class="panel-title">{{ $t('userSettings.apiKeys.createTitle') }}</h2>
      </header>
      <div class="panel-content">
        <div class="create-form">
          <div class="form-field">
            <label for="key-name" class="field-label">{{ $t('userSettings.apiKeys.keyName') }}</label>
            <input
              id="key-name"
              v-model="newKeyName"
              type="text"
              class="text-input"
              :placeholder="$t('userSettings.apiKeys.keyNamePlaceholder')"
              maxlength="100"
              @keyup.enter="createApiKey"
            />
          </div>
          <button
            class="action-btn primary"
            :disabled="!newKeyName.trim() || creating"
            @click="createApiKey"
          >
            <LIcon v-if="creating" size="16" class="spin">mdi-loading</LIcon>
            <LIcon v-else size="16">mdi-key-plus</LIcon>
            <span>{{ $t('userSettings.apiKeys.createButton') }}</span>
          </button>
        </div>

        <!-- New Key Display (only shown once after creation) -->
        <Transition name="slide-fade">
          <div v-if="newlyCreatedKey" class="new-key-display" role="alert">
            <div class="new-key-header">
              <LIcon size="18" color="#4caf50">mdi-check-circle</LIcon>
              <span class="new-key-title">{{ $t('userSettings.apiKeys.keyCreated') }}</span>
            </div>
            <p class="new-key-warning">{{ $t('userSettings.apiKeys.keyWarning') }}</p>
            <div class="new-key-value">
              <code class="key-code">{{ newlyCreatedKey }}</code>
              <button
                class="copy-btn"
                @click="copyToClipboard(newlyCreatedKey)"
                :aria-label="$t('common.copy')"
              >
                <LIcon size="16">{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</LIcon>
              </button>
            </div>
            <button class="dismiss-btn" @click="newlyCreatedKey = null">
              {{ $t('common.dismiss') }}
            </button>
          </div>
        </Transition>
      </div>
    </section>

    <!-- API Keys List -->
    <section class="settings-panel" role="group" aria-labelledby="keys-list-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-key-chain</LIcon>
        <h2 id="keys-list-title" class="panel-title">
          {{ $t('userSettings.apiKeys.listTitle') }}
          <span v-if="apiKeys.length" class="key-count">({{ apiKeys.length }})</span>
        </h2>
      </header>
      <div class="panel-content">
        <!-- Loading State -->
        <div v-if="loading" class="loading-state">
          <LIcon size="24" class="spin">mdi-loading</LIcon>
          <span>{{ $t('common.loading') }}</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="!apiKeys.length" class="empty-state">
          <LIcon size="48" class="empty-icon">mdi-key-outline</LIcon>
          <p class="empty-text">{{ $t('userSettings.apiKeys.noKeys') }}</p>
        </div>

        <!-- Keys Table -->
        <div v-else class="keys-list">
          <div
            v-for="key in apiKeys"
            :key="key.id"
            class="key-item"
            :class="{ inactive: !key.is_active, system: key.is_system_key }"
          >
            <div class="key-info">
              <div class="key-header">
                <span class="key-name">{{ key.name }}</span>
                <div class="key-badges">
                  <span v-if="key.is_system_key" class="badge system">
                    <LIcon size="12">mdi-shield-key</LIcon>
                    {{ $t('userSettings.apiKeys.systemKey') }}
                  </span>
                  <span v-if="!key.is_active" class="badge inactive">
                    {{ $t('userSettings.apiKeys.inactive') }}
                  </span>
                </div>
              </div>
              <div class="key-meta">
                <span class="key-prefix">
                  <LIcon size="12">mdi-key</LIcon>
                  {{ key.key_prefix }}...
                </span>
                <span class="key-date">
                  <LIcon size="12">mdi-calendar</LIcon>
                  {{ formatDate(key.created_at) }}
                </span>
                <span v-if="key.last_used_at" class="key-used">
                  <LIcon size="12">mdi-clock-outline</LIcon>
                  {{ $t('userSettings.apiKeys.lastUsed') }}: {{ formatDate(key.last_used_at) }}
                </span>
              </div>
            </div>
            <div class="key-actions">
              <button
                v-if="!key.is_system_key"
                class="icon-btn"
                :class="{ active: key.is_active }"
                :title="key.is_active ? $t('userSettings.apiKeys.deactivate') : $t('userSettings.apiKeys.activate')"
                @click="toggleKeyStatus(key)"
              >
                <LIcon size="18">{{ key.is_active ? 'mdi-toggle-switch' : 'mdi-toggle-switch-off' }}</LIcon>
              </button>
              <button
                v-if="!key.is_system_key"
                class="icon-btn danger"
                :title="$t('common.delete')"
                @click="confirmDelete(key)"
              >
                <LIcon size="18">mdi-delete-outline</LIcon>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Delete Confirmation Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="deleteDialog" class="dialog-overlay" @click.self="deleteDialog = null">
          <div class="dialog-content" role="dialog" aria-modal="true">
            <div class="dialog-header">
              <LIcon size="24" color="#e8a087">mdi-alert-circle</LIcon>
              <h3 class="dialog-title">{{ $t('userSettings.apiKeys.deleteTitle') }}</h3>
            </div>
            <p class="dialog-text">
              {{ $t('userSettings.apiKeys.deleteConfirm', { name: deleteDialog?.name }) }}
            </p>
            <div class="dialog-actions">
              <button class="action-btn" @click="deleteDialog = null">
                {{ $t('common.cancel') }}
              </button>
              <button class="action-btn danger" @click="deleteApiKey">
                <LIcon size="16">mdi-delete</LIcon>
                {{ $t('common.delete') }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import LIcon from '@/components/common/LIcon.vue'

const { t } = useI18n()

const loading = ref(true)
const creating = ref(false)
const apiKeys = ref([])
const newKeyName = ref('')
const newlyCreatedKey = ref(null)
const copied = ref(false)
const deleteDialog = ref(null)

// Load API keys on mount
onMounted(async () => {
  await loadApiKeys()
})

async function loadApiKeys() {
  loading.value = true
  try {
    const response = await axios.get('/api/auth/api-keys')
    apiKeys.value = response.data.api_keys || []
  } catch (error) {
    console.error('Failed to load API keys:', error)
  } finally {
    loading.value = false
  }
}

async function createApiKey() {
  if (!newKeyName.value.trim() || creating.value) return

  creating.value = true
  try {
    const response = await axios.post('/api/auth/api-keys', {
      name: newKeyName.value.trim()
    })

    if (response.data.success) {
      // Show the newly created key (only shown once!)
      newlyCreatedKey.value = response.data.api_key.key
      newKeyName.value = ''
      // Reload keys to update list
      await loadApiKeys()
    }
  } catch (error) {
    console.error('Failed to create API key:', error)
  } finally {
    creating.value = false
  }
}

async function toggleKeyStatus(key) {
  try {
    const response = await axios.put(`/api/auth/api-keys/${key.id}`, {
      is_active: !key.is_active
    })

    if (response.data.success) {
      key.is_active = response.data.api_key.is_active
    }
  } catch (error) {
    console.error('Failed to toggle key status:', error)
  }
}

function confirmDelete(key) {
  deleteDialog.value = key
}

async function deleteApiKey() {
  if (!deleteDialog.value) return

  try {
    const response = await axios.delete(`/api/auth/api-keys/${deleteDialog.value.id}`)

    if (response.data.success) {
      apiKeys.value = apiKeys.value.filter(k => k.id !== deleteDialog.value.id)
      deleteDialog.value = null
    }
  } catch (error) {
    console.error('Failed to delete API key:', error)
  }
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
/* ============================================
   LLARS API Keys Settings
   ============================================ */

.api-keys-settings {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
  --llars-danger: #e8a087;
  --llars-success: #98d4bb;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Panel Design */
.settings-panel {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.panel-icon {
  color: var(--llars-primary);
  opacity: 0.9;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
  display: flex;
  align-items: center;
  gap: 8px;
}

.key-count {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.panel-content {
  padding: 16px;
}

/* Info Panel */
.info-panel {
  border-left: 3px solid var(--llars-accent);
}

.info-text {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.usage-examples {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.usage-code {
  font-size: 12px;
  padding: 6px 10px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-family: monospace;
}

/* Create Form */
.create-form {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.form-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 12px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.text-input {
  padding: 10px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgb(var(--v-theme-on-surface));
  font-size: 14px;
  transition: all 0.15s ease;
}

.text-input:focus {
  outline: none;
  border-color: var(--llars-primary);
  box-shadow: 0 0 0 3px rgba(176, 202, 151, 0.15);
}

.text-input::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Action Buttons */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: var(--llars-radius-sm);
  background: rgba(var(--v-theme-on-surface), 0.02);
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.action-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.primary {
  background: var(--llars-primary);
  border-color: var(--llars-primary);
  color: white;
}

.action-btn.primary:hover:not(:disabled) {
  filter: brightness(1.05);
}

.action-btn.danger {
  color: var(--llars-danger);
  border-color: rgba(232, 160, 135, 0.3);
}

.action-btn.danger:hover {
  background: rgba(232, 160, 135, 0.1);
  border-color: var(--llars-danger);
}

/* New Key Display */
.new-key-display {
  margin-top: 16px;
  padding: 16px;
  background: rgba(152, 212, 187, 0.1);
  border: 1px solid rgba(152, 212, 187, 0.3);
  border-radius: var(--llars-radius-sm);
}

.new-key-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.new-key-title {
  font-weight: 600;
  color: #4caf50;
}

.new-key-warning {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0 0 12px 0;
}

.new-key-value {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 4px;
  padding: 8px 12px;
}

.key-code {
  flex: 1;
  font-family: monospace;
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface));
  word-break: break-all;
}

.copy-btn {
  padding: 6px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 4px;
  cursor: pointer;
  color: rgba(var(--v-theme-on-surface), 0.7);
  transition: all 0.15s ease;
}

.copy-btn:hover {
  background: var(--llars-primary);
  color: white;
}

.dismiss-btn {
  margin-top: 12px;
  padding: 6px 12px;
  border: none;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 12px;
  cursor: pointer;
}

.dismiss-btn:hover {
  color: rgb(var(--v-theme-on-surface));
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-icon {
  opacity: 0.3;
}

.empty-text {
  margin: 0;
  font-size: 14px;
}

/* Keys List */
.keys-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.key-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: var(--llars-radius-sm);
  transition: all 0.15s ease;
}

.key-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.key-item.inactive {
  opacity: 0.6;
}

.key-item.system {
  border-left: 3px solid var(--llars-accent);
}

.key-info {
  flex: 1;
  min-width: 0;
}

.key-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.key-name {
  font-weight: 600;
  font-size: 14px;
  color: rgb(var(--v-theme-on-surface));
}

.key-badges {
  display: flex;
  gap: 6px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 4px;
  text-transform: uppercase;
}

.badge.system {
  background: rgba(136, 196, 200, 0.15);
  color: var(--llars-accent);
}

.badge.inactive {
  background: rgba(232, 160, 135, 0.15);
  color: var(--llars-danger);
}

.key-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.key-meta > span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.key-actions {
  display: flex;
  gap: 6px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgb(var(--v-theme-on-surface));
}

.icon-btn.active {
  color: var(--llars-success);
}

.icon-btn.danger:hover {
  background: rgba(232, 160, 135, 0.15);
  color: var(--llars-danger);
}

/* Dialog */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-content {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  padding: 24px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.dialog-text {
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Spin Animation */
.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Transitions */
.slide-fade-enter-active {
  transition: all 0.2s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.15s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Mobile */
@media (max-width: 600px) {
  .create-form {
    flex-direction: column;
    align-items: stretch;
  }

  .key-item {
    flex-direction: column;
    align-items: stretch;
  }

  .key-actions {
    justify-content: flex-end;
    padding-top: 12px;
    border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
    margin-top: 12px;
  }
}
</style>
