<template>
  <div class="kaimo-panel">
    <!-- Hero Section -->
    <div class="panel-header">
      <v-skeleton-loader
        v-if="isLoading('hero')"
        type="heading, text"
        class="mb-4"
      />
      <template v-else>
        <div class="header-content">
          <div class="header-left">
            <div class="header-title-row">
              <div class="header-icon">
                <LIcon size="24" color="white">mdi-human-child</LIcon>
              </div>
              <div>
                <h1 class="panel-title">{{ $t('kaimo.panel.title') }}</h1>
                <p class="panel-subtitle">{{ $t('kaimo.panel.subtitle') }}</p>
              </div>
            </div>
            <p class="role-hint">
              {{ canManageKaimo ? $t('kaimo.panel.roleHint.researcher') : $t('kaimo.panel.roleHint.evaluator') }}
            </p>
          </div>

          <div class="header-right">
            <LTag v-if="canManageKaimo" variant="secondary">
              <LIcon size="14" class="mr-1">mdi-shield-account</LIcon>
              {{ $t('kaimo.panel.roles.researcher') }}
            </LTag>
            <LTag v-else variant="primary">
              <LIcon size="14" class="mr-1">mdi-account</LIcon>
              {{ $t('kaimo.panel.roles.evaluator') }}
            </LTag>

            <div class="header-actions">
              <LBtn
                v-if="canManageKaimo"
                variant="primary"
                @click="router.push({ name: 'KaimoNewCase' })"
              >
                <LIcon size="18" class="mr-1">mdi-plus</LIcon>
                {{ $t('kaimo.panel.actions.newCase') }}
              </LBtn>
              <LBtn
                v-if="canManageKaimo"
                variant="outlined"
                @click="openImportDialog"
              >
                <LIcon size="18" class="mr-1">mdi-import</LIcon>
                {{ $t('kaimo.import.button') }}
              </LBtn>
              <LBtn
                variant="text"
                @click="router.push({ name: 'KaimoHub' })"
              >
                <LIcon size="18" class="mr-1">mdi-arrow-left</LIcon>
                {{ $t('common.back') }}
              </LBtn>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Alerts -->
    <v-alert
      v-if="!isLoading('content') && !canViewKaimo"
      type="warning"
      variant="tonal"
      icon="mdi-lock"
      class="mb-4"
    >
      {{ $t('kaimo.panel.alerts.noAccess', { permission: 'feature:kaimo:view' }) }}
    </v-alert>
    <v-alert
      v-else-if="!isLoading('content') && loadError"
      type="error"
      variant="tonal"
      icon="mdi-alert"
      class="mb-4"
    >
      {{ loadError }}
    </v-alert>

    <!-- Main Content -->
    <div v-if="!isLoading('content') && canViewKaimo" class="panel-content">
      <!-- My Cases Section -->
      <LCard class="cases-card" :class="{ 'full-width': canManageKaimo }">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <LIcon size="20" color="primary" class="mr-2">mdi-folder-account</LIcon>
              <span class="card-title">{{ $t('kaimo.panel.sections.myCases') }}</span>
              <LTag variant="primary" size="small" class="ml-2">{{ ownedCases.length }}</LTag>
            </div>
            <LIconBtn
              icon="mdi-refresh"
              :tooltip="$t('common.refresh')"
              :loading="isLoading('content')"
              @click="refresh"
            />
          </div>
        </template>

        <v-skeleton-loader
          v-if="isLoading('content')"
          type="table-heading, table-tbody"
        />
        <div v-else class="table-wrapper">
          <table class="cases-table">
            <thead>
              <tr>
                <th class="text-left">{{ $t('kaimo.panel.table.headers.case') }}</th>
                <th class="text-left">{{ $t('kaimo.panel.table.headers.status') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.docs') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.hints') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.shared') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in ownedCases" :key="c.id" class="case-row clickable" @click="openCase(c)">
                <td>
                  <div class="case-info">
                    <span v-if="c.icon" class="case-icon">{{ c.icon }}</span>
                    <div>
                      <div class="case-name">{{ c.display_name }}</div>
                      <div class="case-description">
                        {{ c.description || $t('kaimo.panel.table.noDescription') }}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <LTag :variant="getStatusVariant(c.status)" size="small">
                    {{ getStatusLabel(c.status) }}
                  </LTag>
                </td>
                <td class="text-right">{{ c.document_count || 0 }}</td>
                <td class="text-right">{{ c.hint_count || 0 }}</td>
                <td class="text-right">
                  <LTag v-if="c.share_count > 0" variant="info" size="small">
                    <LIcon size="12" class="mr-1">mdi-share-variant</LIcon>
                    {{ c.share_count }}
                  </LTag>
                  <span v-else class="text-muted">-</span>
                </td>
                <td class="text-right">
                  <div class="action-buttons" @click.stop>
                    <LIconBtn
                      icon="mdi-eye"
                      :tooltip="$t('kaimo.panel.tooltips.openCase')"
                      size="small"
                      @click="openCase(c)"
                    />
                    <LIconBtn
                      icon="mdi-share-variant"
                      :tooltip="$t('kaimo.panel.tooltips.shareCase')"
                      size="small"
                      color="info"
                      @click="openShareDialog(c)"
                    />
                    <LIconBtn
                      icon="mdi-pencil"
                      :tooltip="$t('kaimo.panel.tooltips.editCase')"
                      size="small"
                      @click="editCase(c)"
                    />
                    <LIconBtn
                      v-if="c.status === 'draft'"
                      icon="mdi-publish"
                      :tooltip="$t('kaimo.panel.tooltips.publish')"
                      size="small"
                      color="success"
                      @click="confirmPublish(c)"
                    />
                    <LIconBtn
                      icon="mdi-delete"
                      :tooltip="$t('common.delete')"
                      size="small"
                      color="danger"
                      @click="confirmDelete(c)"
                    />
                  </div>
                </td>
              </tr>
              <tr v-if="ownedCases.length === 0">
                <td colspan="6" class="empty-state">
                  <LIcon size="24" class="mr-2">mdi-folder-open-outline</LIcon>
                  <span>{{ $t('kaimo.panel.table.emptyOwned') }}</span>
                  <LBtn
                    variant="text"
                    size="small"
                    class="ml-2"
                    @click="router.push({ name: 'KaimoNewCase' })"
                  >
                    {{ $t('kaimo.panel.table.emptyCta') }}
                  </LBtn>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </LCard>

      <!-- Shared With Me Section -->
      <LCard v-if="sharedCases.length > 0 || !canManageKaimo" class="cases-card shared-cases-card">
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <LIcon size="20" color="accent" class="mr-2">mdi-account-group</LIcon>
              <span class="card-title">{{ $t('kaimo.panel.sections.sharedWithMe') }}</span>
              <LTag variant="accent" size="small" class="ml-2">{{ sharedCases.length }}</LTag>
            </div>
          </div>
        </template>

        <div class="table-wrapper">
          <table class="cases-table">
            <thead>
              <tr>
                <th class="text-left">{{ $t('kaimo.panel.table.headers.case') }}</th>
                <th class="text-left">{{ $t('kaimo.panel.table.headers.owner') }}</th>
                <th class="text-left">{{ $t('kaimo.panel.table.headers.status') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.docs') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.hints') }}</th>
                <th class="text-right">{{ $t('kaimo.panel.table.headers.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in sharedCases" :key="c.id" class="case-row clickable" @click="openCase(c)">
                <td>
                  <div class="case-info">
                    <span v-if="c.icon" class="case-icon">{{ c.icon }}</span>
                    <div>
                      <div class="case-name">{{ c.display_name }}</div>
                      <div class="case-description">
                        {{ c.description || $t('kaimo.panel.table.noDescription') }}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <div class="owner-info">
                    <LAvatar
                      :username="c.owner"
                      :seed="c.owner_avatar_seed"
                      :src="c.owner_avatar_url"
                      size="xs"
                      class="mr-1"
                    />
                    <span class="owner-name">{{ c.owner }}</span>
                  </div>
                </td>
                <td>
                  <LTag :variant="getStatusVariant(c.status)" size="small">
                    {{ getStatusLabel(c.status) }}
                  </LTag>
                </td>
                <td class="text-right">{{ c.document_count || 0 }}</td>
                <td class="text-right">{{ c.hint_count || 0 }}</td>
                <td class="text-right">
                  <div class="action-buttons" @click.stop>
                    <LIconBtn
                      icon="mdi-eye"
                      :tooltip="$t('kaimo.panel.tooltips.openCase')"
                      size="small"
                      @click="openCase(c)"
                    />
                  </div>
                </td>
              </tr>
              <tr v-if="sharedCases.length === 0">
                <td colspan="6" class="empty-state">
                  <LIcon size="24" class="mr-2">mdi-share-variant-outline</LIcon>
                  <span>{{ $t('kaimo.panel.table.emptyShared') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </LCard>

      <!-- Info Sidebar (for Evaluators only) -->
      <LCard v-if="!canManageKaimo" class="info-card" color="primary">
        <div class="info-header">
          <div class="info-icon">
            <LIcon size="20" color="white">mdi-information-outline</LIcon>
          </div>
          <div>
            <div class="info-title">{{ $t('kaimo.panel.sidebar.title') }}</div>
            <div class="info-subtitle">{{ $t('kaimo.panel.sidebar.subtitle') }}</div>
          </div>
        </div>
        <div class="info-stats">
          <LTag variant="success" size="small">
            <LIcon size="14" class="mr-1">mdi-check</LIcon>
            {{ $t('kaimo.panel.sidebar.publishedCount', { count: cases.filter(c => c.status === 'published').length }) }}
          </LTag>
          <LTag variant="warning" size="small">
            <LIcon size="14" class="mr-1">mdi-pencil</LIcon>
            {{ $t('kaimo.panel.sidebar.draftCount', { count: cases.filter(c => c.status === 'draft').length }) }}
          </LTag>
        </div>
      </LCard>
    </div>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="450">
      <LCard>
        <template #header>
          <div class="dialog-header">
            <LIcon size="20" color="danger" class="mr-2">mdi-delete-alert</LIcon>
            <span>{{ $t('kaimo.panel.deleteDialog.title') }}</span>
          </div>
        </template>
        <div class="dialog-body">
          <p>{{ $t('kaimo.panel.deleteDialog.body', { name: caseToDelete?.display_name }) }}</p>
          <v-alert v-if="caseToDelete?.assessment_count > 0" type="warning" variant="tonal" class="mt-3">
            <strong>{{ $t('kaimo.panel.deleteDialog.warningTitle') }}</strong>
            {{ $t('kaimo.panel.deleteDialog.warningBody', { count: caseToDelete?.assessment_count }) }}
          </v-alert>
        </div>
        <div class="dialog-actions">
          <LBtn variant="cancel" @click="deleteDialog = false">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="danger" :loading="deleting" @click="executeDelete">
            {{ $t('common.delete') }}
          </LBtn>
        </div>
      </LCard>
    </v-dialog>

    <!-- Publish Confirmation Dialog -->
    <v-dialog v-model="publishDialog" max-width="450">
      <LCard>
        <template #header>
          <div class="dialog-header">
            <LIcon size="20" color="success" class="mr-2">mdi-publish</LIcon>
            <span>{{ $t('kaimo.panel.publishDialog.title') }}</span>
          </div>
        </template>
        <div class="dialog-body">
          <p>{{ $t('kaimo.panel.publishDialog.body', { name: caseToPublish?.display_name }) }}</p>
          <p class="text-muted">{{ $t('kaimo.panel.publishDialog.note') }}</p>
        </div>
        <div class="dialog-actions">
          <LBtn variant="cancel" @click="publishDialog = false">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="publishing" @click="executePublish">
            {{ $t('kaimo.panel.publishDialog.confirm') }}
          </LBtn>
        </div>
      </LCard>
    </v-dialog>

    <!-- Import Dialog -->
    <v-dialog v-model="importDialog" max-width="550">
      <LCard>
        <template #header>
          <div class="dialog-header">
            <LIcon size="20" color="secondary" class="mr-2">mdi-import</LIcon>
            <span>{{ $t('kaimo.import.title') }}</span>
          </div>
        </template>
        <div class="dialog-body">
          <p class="text-muted mb-4">{{ $t('kaimo.import.description') }}</p>

          <v-file-input
            v-model="importFile"
            :label="$t('kaimo.import.fileLabel')"
            accept=".json"
            prepend-icon="mdi-file-document"
            variant="outlined"
            density="comfortable"
            :error-messages="importError"
            @update:model-value="validateImportFile"
          />

          <v-text-field
            v-model="importNameOverride"
            :label="$t('kaimo.import.nameOverride')"
            :hint="$t('kaimo.import.nameOverrideHint')"
            persistent-hint
            variant="outlined"
            density="comfortable"
            class="mt-3"
          />

          <v-checkbox
            v-model="importPublish"
            :label="$t('kaimo.import.publishImmediately')"
            color="success"
            hide-details
            class="mt-2"
          />

          <div v-if="importPreview" class="import-preview">
            <div class="preview-title">{{ importPreview.case?.display_name || importPreview.case?.name }}</div>
            <div class="preview-meta">
              {{ $t('kaimo.import.preview', {
                docs: importPreview.documents?.length || 0,
                hints: importPreview.hints?.length || 0
              }) }}
            </div>
          </div>
        </div>
        <div class="dialog-actions">
          <LBtn variant="cancel" @click="closeImportDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="secondary"
            :loading="importing"
            :disabled="!importFile || !!importError"
            @click="executeImport"
          >
            {{ $t('kaimo.import.button') }}
          </LBtn>
        </div>
      </LCard>
    </v-dialog>

    <!-- Share Dialog -->
    <v-dialog v-model="shareDialog" max-width="500">
      <LCard>
        <template #header>
          <div class="dialog-header">
            <LIcon size="20" color="info" class="mr-2">mdi-share-variant</LIcon>
            <span>{{ $t('kaimo.share.title') }}</span>
          </div>
        </template>
        <div class="dialog-body">
          <p class="text-muted mb-4">
            {{ $t('kaimo.share.description', { name: caseToShare?.display_name }) }}
          </p>

          <!-- Share input -->
          <div class="share-input-row">
            <v-text-field
              v-model="shareUsername"
              :label="$t('kaimo.share.usernameLabel')"
              :placeholder="$t('kaimo.share.usernamePlaceholder')"
              :error-messages="shareError"
              variant="outlined"
              density="comfortable"
              hide-details="auto"
              class="flex-grow-1"
              @keyup.enter="executeShare"
            />
            <LBtn
              variant="primary"
              :loading="sharing"
              :disabled="!shareUsername.trim()"
              @click="executeShare"
            >
              <LIcon size="18">mdi-plus</LIcon>
            </LBtn>
          </div>

          <!-- Shared users list -->
          <div v-if="sharedWithUsers.length > 0" class="shared-users-list mt-4">
            <div class="shared-users-header">
              <LIcon size="16" class="mr-1">mdi-account-group</LIcon>
              {{ $t('kaimo.share.sharedWith') }}
            </div>
            <div
              v-for="user in sharedWithUsers"
              :key="sharedUserName(user)"
              class="shared-user-item"
            >
              <LAvatar
                :username="sharedUserName(user)"
                :seed="user?.avatar_seed || null"
                :src="user?.avatar_url || null"
                size="sm"
                class="mr-2"
              />
              <span class="shared-user-name">{{ sharedUserName(user) }}</span>
              <v-spacer />
              <LIconBtn
                icon="mdi-close"
                size="x-small"
                :tooltip="$t('kaimo.share.remove')"
                color="danger"
                @click="executeUnshare(sharedUserName(user))"
              />
            </div>
          </div>

          <div v-else class="no-shares-hint mt-4">
            <LIcon size="16" class="mr-1 text-muted">mdi-information-outline</LIcon>
            <span class="text-muted">{{ $t('kaimo.share.noShares') }}</span>
          </div>
        </div>
        <div class="dialog-actions">
          <LBtn variant="cancel" @click="closeShareDialog">{{ $t('common.close') }}</LBtn>
        </div>
      </LCard>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { getKaimoCases, getKaimoAdminCases, deleteKaimoCase, publishKaimoCase, importKaimoCase, shareKaimoCase, unshareKaimoCase, getKaimoCaseShares } from '@/services/kaimoApi'

const router = useRouter()
const { t, locale } = useI18n()
const { hasPermission, isResearcher, fetchPermissions } = usePermissions()
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['hero', 'content'])

const canViewKaimo = computed(() => {
  return hasPermission('feature:kaimo:view') || isResearcher.value || hasPermission('admin:kaimo:manage')
})

const canManageKaimo = computed(() => {
  return isResearcher.value || hasPermission('admin:kaimo:manage')
})

const isKaimoAdmin = computed(() => {
  return hasPermission('admin:kaimo:manage')
})

const ownedCases = ref([])
const sharedCases = ref([])
const loadError = ref(null)

// Computed for combined cases (for compatibility)
const cases = computed(() => [...ownedCases.value, ...sharedCases.value])

// Delete dialog
const deleteDialog = ref(false)
const caseToDelete = ref(null)
const deleting = ref(false)

// Publish dialog
const publishDialog = ref(false)
const caseToPublish = ref(null)
const publishing = ref(false)

// Import dialog
const importDialog = ref(false)
const importFile = ref(null)
const importNameOverride = ref('')
const importPublish = ref(false)
const importPreview = ref(null)
const importError = ref('')
const importing = ref(false)

// Share dialog
const shareDialog = ref(false)
const caseToShare = ref(null)
const sharedWithUsers = ref([])
const shareUsername = ref('')
const sharing = ref(false)
const shareError = ref('')

// Snackbar
const snackbar = ref({ show: false, text: '', color: 'success' })

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

const sharedUserName = (entry) => {
  if (!entry) return ''
  if (typeof entry === 'string') return entry
  return entry.username || ''
}

const normalizeSharedUsers = (entries) => {
  if (!Array.isArray(entries)) return []
  return entries
    .map((entry) => {
      if (typeof entry === 'string') {
        return { username: entry, avatar_seed: null, avatar_url: null }
      }
      if (entry && typeof entry === 'object' && entry.username) {
        return {
          username: entry.username,
          avatar_seed: entry.avatar_seed || null,
          avatar_url: entry.avatar_url || null,
        }
      }
      return null
    })
    .filter(Boolean)
}

const getStatusVariant = (status) => {
  switch (status) {
    case 'published': return 'success'
    case 'draft': return 'warning'
    case 'archived': return 'info'
    default: return 'primary'
  }
}

const getStatusLabel = (status) => {
  locale.value
  switch (status) {
    case 'published': return t('kaimo.status.published')
    case 'draft': return t('kaimo.status.draft')
    case 'archived': return t('kaimo.status.archived')
    default: return status
  }
}

const loadCases = async () => {
  loadError.value = null
  if (isKaimoAdmin.value) {
    // Admin API returns flat list (all cases)
    const data = await getKaimoAdminCases()
    ownedCases.value = data?.cases || []
    sharedCases.value = []
  } else {
    // User API returns owned and shared separately
    const data = await getKaimoCases()
    ownedCases.value = data?.owned_cases || []
    sharedCases.value = data?.shared_cases || []
  }
}

const refresh = async () => {
  await withLoading('content', async () => {
    await fetchPermissions(true)
    if (canViewKaimo.value) {
      await loadCases()
    }
  })
  setLoading('hero', false)
}

const openCase = (c) => {
  router.push({ name: 'KaimoCase', params: { id: c.id } })
}

const editCase = (c) => {
  router.push({ name: 'KaimoCaseEditor', params: { id: c.id } })
}

const confirmDelete = (c) => {
  caseToDelete.value = c
  deleteDialog.value = true
}

const executeDelete = async () => {
  if (!caseToDelete.value) return
  deleting.value = true
  try {
    const force = (caseToDelete.value.assessment_count || 0) > 0
    await deleteKaimoCase(caseToDelete.value.id, force)
    showSnackbar(t('kaimo.panel.snackbar.deleteSuccess', { name: caseToDelete.value.display_name }), 'success')
    deleteDialog.value = false
    await loadCases()
  } catch (err) {
    console.error('Fehler beim Loeschen:', err)
    showSnackbar(t('kaimo.panel.snackbar.deleteError'), 'error')
  } finally {
    deleting.value = false
  }
}

const confirmPublish = (c) => {
  caseToPublish.value = c
  publishDialog.value = true
}

const executePublish = async () => {
  if (!caseToPublish.value) return
  publishing.value = true
  try {
    await publishKaimoCase(caseToPublish.value.id)
    showSnackbar(t('kaimo.panel.snackbar.publishSuccess', { name: caseToPublish.value.display_name }), 'success')
    publishDialog.value = false
    await loadCases()
  } catch (err) {
    console.error('Fehler beim Veroeffentlichen:', err)
    showSnackbar(t('kaimo.panel.snackbar.publishError'), 'error')
  } finally {
    publishing.value = false
  }
}

// Share functions
const openShareDialog = async (c) => {
  caseToShare.value = c
  shareUsername.value = ''
  shareError.value = ''
  sharing.value = false

  // Load current shares
  try {
    const data = await getKaimoCaseShares(c.id)
    sharedWithUsers.value = normalizeSharedUsers(data?.shared_with_users || data?.shared_with || [])
  } catch (err) {
    console.error('Error loading shares:', err)
    sharedWithUsers.value = []
  }

  shareDialog.value = true
}

const executeShare = async () => {
  if (!caseToShare.value || !shareUsername.value.trim()) return
  sharing.value = true
  shareError.value = ''

  try {
    const username = shareUsername.value.trim()
    await shareKaimoCase(caseToShare.value.id, username)
    sharedWithUsers.value.push({ username, avatar_seed: null, avatar_url: null })
    shareUsername.value = ''
    showSnackbar(t('kaimo.panel.snackbar.shareSuccess'), 'success')
    await loadCases()
  } catch (err) {
    console.error('Error sharing case:', err)
    shareError.value = err.response?.data?.error || t('kaimo.panel.snackbar.shareError')
  } finally {
    sharing.value = false
  }
}

const executeUnshare = async (username) => {
  if (!caseToShare.value) return

  try {
    await unshareKaimoCase(caseToShare.value.id, username)
    sharedWithUsers.value = sharedWithUsers.value.filter(u => sharedUserName(u) !== username)
    showSnackbar(t('kaimo.panel.snackbar.unshareSuccess'), 'success')
    await loadCases()
  } catch (err) {
    console.error('Error unsharing case:', err)
    showSnackbar(t('kaimo.panel.snackbar.unshareError'), 'error')
  }
}

const closeShareDialog = () => {
  shareDialog.value = false
  caseToShare.value = null
  sharedWithUsers.value = []
  shareUsername.value = ''
  shareError.value = ''
}

// Import functions
const openImportDialog = () => {
  importFile.value = null
  importNameOverride.value = ''
  importPublish.value = false
  importPreview.value = null
  importError.value = ''
  importDialog.value = true
}

const closeImportDialog = () => {
  importDialog.value = false
  importFile.value = null
  importPreview.value = null
  importError.value = ''
}

const validateImportFile = async (files) => {
  importError.value = ''
  importPreview.value = null

  if (!files || files.length === 0) return

  const file = Array.isArray(files) ? files[0] : files
  if (!file) return

  try {
    const text = await file.text()
    const data = JSON.parse(text)

    if (!data.export_version || !data.case) {
      importError.value = t('kaimo.import.invalidFormat')
      return
    }

    importPreview.value = data
  } catch (err) {
    console.error('Import-Validierung fehlgeschlagen:', err)
    importError.value = t('kaimo.import.parseError')
  }
}

const executeImport = async () => {
  if (!importPreview.value) return

  importing.value = true
  try {
    const result = await importKaimoCase(importPreview.value, {
      nameOverride: importNameOverride.value || null,
      publish: importPublish.value
    })

    showSnackbar(t('kaimo.import.success', { name: result.case?.display_name || result.case?.name }), 'success')
    closeImportDialog()
    await loadCases()
  } catch (err) {
    console.error('Import fehlgeschlagen:', err)
    const errorMsg = err.response?.data?.error || t('kaimo.import.error')
    showSnackbar(errorMsg, 'error')
  } finally {
    importing.value = false
  }
}

onMounted(async () => {
  try {
    await refresh()
  } catch (err) {
    loadError.value = t('kaimo.errors.loadCases')
    console.error('KAIMO-Ladefehler', err)
    setLoading('hero', false)
  }
})
</script>

<style scoped>
.kaimo-panel {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

/* Header Section */
.panel-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 20px;
}

.header-left {
  flex: 1;
  min-width: 280px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.header-icon {
  width: 42px;
  height: 42px;
  background-color: #b0ca97; /* LLARS Primary */
  border-radius: 16px 4px 16px 4px; /* LLARS signature */
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.panel-subtitle {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.role-hint {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.header-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Main Content */
.panel-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 900px) {
  .panel-content {
    grid-template-columns: 1fr 320px;
  }

  .panel-content .cases-card.full-width {
    grid-column: 1 / -1;
  }
}

/* Cases Card */
.cases-card {
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.card-header-left {
  display: flex;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

/* Table Styles */
.table-wrapper {
  overflow-x: auto;
}

.cases-table {
  width: 100%;
  border-collapse: collapse;
}

.cases-table th {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
  background-color: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.cases-table td {
  padding: 16px;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: middle;
}

.case-row.clickable {
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.case-row:hover {
  background-color: #f8fafc;
}

.case-row.clickable:active {
  background-color: #f1f5f9;
}

.case-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.case-icon {
  font-size: 24px;
}

.case-name {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 2px;
}

.case-description {
  font-size: 12px;
  color: #94a3b8;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.empty-state {
  text-align: center;
  padding: 32px 16px !important;
  color: #94a3b8;
}

/* Info Card */
.info-card {
  height: fit-content;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.info-icon {
  width: 40px;
  height: 40px;
  background-color: #b0ca97;
  border-radius: 16px 4px 16px 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.info-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.info-subtitle {
  font-size: 13px;
  color: #64748b;
}

.info-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Dialogs */
.dialog-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.dialog-body {
  padding: 0 20px 20px;
}

.dialog-body p {
  margin: 0 0 12px;
  color: #475569;
}

.dialog-body .text-muted {
  color: #94a3b8;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
}

/* Import Preview */
.import-preview {
  margin-top: 16px;
  padding: 12px 16px;
  background-color: rgba(136, 196, 200, 0.1); /* LLARS Accent */
  border-radius: 6px 2px 6px 2px;
  border-left: 3px solid #88c4c8;
}

.preview-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 4px;
}

.preview-meta {
  font-size: 12px;
  color: #64748b;
}

/* Utilities */
.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.mr-1 {
  margin-right: 4px;
}

.mr-2 {
  margin-right: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-3 {
  margin-top: 12px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-4 {
  margin-top: 16px;
}

.flex-grow-1 {
  flex-grow: 1;
}

.text-muted {
  color: #94a3b8;
}

/* Shared Cases Card */
.shared-cases-card {
  margin-top: 24px;
}

/* Owner Info */
.owner-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.owner-name {
  font-size: 13px;
  color: #475569;
}

/* Share Dialog */
.share-input-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.shared-users-list {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.shared-users-header {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background-color: #f8fafc;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shared-user-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-top: 1px solid #f1f5f9;
}

.shared-user-item:hover {
  background-color: #f8fafc;
}

.shared-user-name {
  font-size: 14px;
  color: #1e293b;
}

.no-shares-hint {
  display: flex;
  align-items: center;
  padding: 16px;
  background-color: #f8fafc;
  border-radius: 8px;
  font-size: 13px;
}
</style>
