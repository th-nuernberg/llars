<template>
  <div class="referral-links">
    <!-- Info Banner -->
    <v-alert type="info" variant="tonal" class="mb-4" density="compact">
      <template #prepend>
        <v-icon>mdi-information</v-icon>
      </template>
      {{ $t('userSettings.referrals.info') }}
    </v-alert>

    <!-- Stats Overview -->
    <div v-if="stats" class="stats-grid mb-4">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_links || 0 }}</div>
        <div class="stat-label">{{ $t('userSettings.referrals.stats.totalLinks') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_registrations || 0 }}</div>
        <div class="stat-label">{{ $t('userSettings.referrals.stats.totalRegistrations') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.active_links || 0 }}</div>
        <div class="stat-label">{{ $t('userSettings.referrals.stats.activeLinks') }}</div>
      </div>
    </div>

    <!-- Links List -->
    <LCard :title="$t('userSettings.referrals.myLinks')" icon="mdi-link-variant" class="mb-4">
      <template #actions>
        <LBtn variant="primary" size="small" @click="openCreateDialog">
          <v-icon start>mdi-plus</v-icon>
          {{ $t('userSettings.referrals.createLink') }}
        </LBtn>
      </template>

      <div v-if="loading" class="loading-state">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-else-if="links.length === 0" class="empty-state">
        <v-icon size="48" color="grey">mdi-link-off</v-icon>
        <p>{{ $t('userSettings.referrals.noLinks') }}</p>
        <LBtn variant="secondary" @click="openCreateDialog">
          {{ $t('userSettings.referrals.createFirstLink') }}
        </LBtn>
      </div>

      <div v-else class="links-list">
        <div
          v-for="link in links"
          :key="link.id"
          class="link-card"
          :class="{ inactive: !link.is_active }"
        >
          <div class="link-main">
            <div class="link-header">
              <span class="link-label">{{ link.label || $t('userSettings.referrals.defaultLabel') }}</span>
              <LTag v-if="!link.is_active" variant="gray">{{ $t('userSettings.referrals.inactive') }}</LTag>
              <LTag v-else-if="isExpired(link)" variant="warning">{{ $t('userSettings.referrals.expired') }}</LTag>
              <LTag v-else variant="success">{{ $t('userSettings.referrals.active') }}</LTag>
            </div>

            <div class="link-url">
              <code>{{ getFullUrl(link) }}</code>
              <v-btn icon="mdi-content-copy" variant="text" size="x-small" @click="copyLink(link)" />
            </div>

            <div class="link-meta">
              <span v-if="link.registrations !== undefined">
                <v-icon size="small">mdi-account-plus</v-icon>
                {{ link.registrations }} {{ $t('userSettings.referrals.registrations') }}
              </span>
              <span v-if="link.max_uses">
                <v-icon size="small">mdi-counter</v-icon>
                {{ link.remaining_uses || 0 }} / {{ link.max_uses }} {{ $t('userSettings.referrals.remaining') }}
              </span>
              <span v-if="link.expires_at">
                <v-icon size="small">mdi-clock-outline</v-icon>
                {{ formatDate(link.expires_at) }}
              </span>
            </div>

            <p v-if="link.description" class="link-description">{{ link.description }}</p>
          </div>

          <div class="link-actions">
            <v-menu>
              <template #activator="{ props }">
                <v-btn icon="mdi-dots-vertical" variant="text" size="small" v-bind="props" />
              </template>
              <v-list density="compact">
                <v-list-item @click="copyLink(link)">
                  <template #prepend><v-icon size="small">mdi-content-copy</v-icon></template>
                  <v-list-item-title>{{ $t('userSettings.referrals.copyLink') }}</v-list-item-title>
                </v-list-item>
                <v-list-item @click="editLink(link)">
                  <template #prepend><v-icon size="small">mdi-pencil</v-icon></template>
                  <v-list-item-title>{{ $t('common.edit') }}</v-list-item-title>
                </v-list-item>
                <v-list-item v-if="link.is_active" @click="deactivateLink(link)">
                  <template #prepend><v-icon size="small">mdi-close-circle</v-icon></template>
                  <v-list-item-title>{{ $t('userSettings.referrals.deactivate') }}</v-list-item-title>
                </v-list-item>
                <v-divider />
                <v-list-item @click="deleteLink(link)" class="text-error">
                  <template #prepend><v-icon size="small" color="error">mdi-delete</v-icon></template>
                  <v-list-item-title>{{ $t('common.delete') }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </div>
        </div>
      </div>
    </LCard>

    <!-- Recent Registrations -->
    <LCard v-if="registrations.length > 0" :title="$t('userSettings.referrals.recentRegistrations')" icon="mdi-account-multiple-plus">
      <v-table density="compact">
        <thead>
          <tr>
            <th>{{ $t('userSettings.referrals.table.user') }}</th>
            <th>{{ $t('userSettings.referrals.table.link') }}</th>
            <th>{{ $t('userSettings.referrals.table.date') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="reg in registrations" :key="reg.id">
            <td>{{ reg.username }}</td>
            <td>{{ reg.link_label || reg.link_code }}</td>
            <td>{{ formatDate(reg.registered_at) }}</td>
          </tr>
        </tbody>
      </v-table>
    </LCard>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon start>{{ editingLink ? 'mdi-pencil' : 'mdi-link-plus' }}</v-icon>
          {{ editingLink ? $t('userSettings.referrals.editLink') : $t('userSettings.referrals.createLink') }}
        </v-card-title>

        <v-card-text>
          <v-form ref="formRef" v-model="formValid">
            <!-- Label -->
            <v-text-field
              v-model="form.label"
              :label="$t('userSettings.referrals.form.label')"
              variant="outlined"
              density="comfortable"
              :placeholder="$t('userSettings.referrals.form.labelPlaceholder')"
              @update:model-value="onLabelInput"
            />

            <!-- Slug with URL preview -->
            <v-text-field
              v-model="form.slug"
              :label="$t('userSettings.referrals.form.slug')"
              variant="outlined"
              density="comfortable"
              :placeholder="$t('userSettings.referrals.form.slugPlaceholder')"
              :disabled="!!editingLink"
              :error-messages="slugError"
              :loading="slugChecking"
              :color="slugAvailable === true ? 'success' : undefined"
              @update:model-value="onSlugInput"
              @focus="slugManuallyEdited = true"
            >
              <template #prepend-inner>
                <span class="text-medium-emphasis text-body-2">/join/</span>
              </template>
              <template v-if="slugAvailable === true && form.slug.length >= 3" #append-inner>
                <v-icon color="success" size="small">mdi-check-circle</v-icon>
              </template>
              <template v-else-if="slugAvailable === false" #append-inner>
                <v-icon color="error" size="small">mdi-close-circle</v-icon>
              </template>
            </v-text-field>

            <!-- URL Preview -->
            <div v-if="form.slug && form.slug.length >= 3 && !slugError" class="url-preview mb-4">
              <v-icon size="small" class="mr-1">mdi-link-variant</v-icon>
              <code>{{ urlPreview }}</code>
            </div>

            <!-- Optional settings in expandable section -->
            <v-expansion-panels variant="accordion" flat class="mb-2 optional-settings">
              <v-expansion-panel>
                <v-expansion-panel-title class="text-body-2 px-0">
                  <v-icon size="small" class="mr-2">mdi-cog-outline</v-icon>
                  {{ $t('userSettings.referrals.form.optionalSettings') }}
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-textarea
                    v-model="form.description"
                    :label="$t('userSettings.referrals.form.description')"
                    variant="outlined"
                    density="comfortable"
                    rows="2"
                    :placeholder="$t('userSettings.referrals.form.descriptionPlaceholder')"
                  />

                  <div class="d-flex gap-3">
                    <v-text-field
                      v-model.number="form.max_uses"
                      :label="$t('userSettings.referrals.form.maxUses')"
                      type="number"
                      variant="outlined"
                      density="comfortable"
                      min="1"
                      :placeholder="$t('userSettings.referrals.form.maxUsesPlaceholder')"
                      class="flex-1"
                    />

                    <v-text-field
                      v-model="form.expires_at"
                      :label="$t('userSettings.referrals.form.expiresAt')"
                      type="date"
                      variant="outlined"
                      density="comfortable"
                      class="flex-1"
                    />
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="saving" :disabled="slugAvailable === false || slugChecking" @click="saveLink">
            {{ editingLink ? $t('common.save') : $t('common.create') }}
          </LBtn>
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
import axios from 'axios'

const { t, locale } = useI18n()

const loading = ref(true)
const saving = ref(false)
const links = ref([])
const registrations = ref([])
const stats = ref(null)

const showDialog = ref(false)
const editingLink = ref(null)
const formRef = ref(null)
const formValid = ref(false)

const form = ref({
  label: '',
  slug: '',
  description: '',
  max_uses: null,
  expires_at: ''
})

const slugChecking = ref(false)
const slugAvailable = ref(null) // null = not checked, true = available, false = taken
const slugError = ref('')
const slugManuallyEdited = ref(false)
let slugCheckTimer = null

function slugify(text) {
  return (text || '')
    .trim()
    .toLowerCase()
    .replace(/[äÄ]/g, 'ae')
    .replace(/[öÖ]/g, 'oe')
    .replace(/[üÜ]/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const urlPreview = computed(() => {
  const base = window.location.origin
  return `${base}/join/${form.value.slug}`
})

function onLabelInput(value) {
  if (!slugManuallyEdited.value && !editingLink.value) {
    const slug = slugify(value)
    form.value.slug = slug
    if (slug) {
      onSlugInput(slug)
    } else {
      slugAvailable.value = null
      slugError.value = ''
    }
  }
}

function onSlugInput(value) {
  const slug = (value || '').trim().toLowerCase().replace(/\s+/g, '-')
  slugAvailable.value = null
  slugError.value = ''

  if (slugCheckTimer) clearTimeout(slugCheckTimer)

  if (!slug) return
  if (slug.length < 3) {
    slugError.value = t('userSettings.referrals.form.slugTooShort')
    return
  }

  slugChecking.value = true
  slugCheckTimer = setTimeout(async () => {
    try {
      const { data } = await axios.get('/api/user/referrals/check-slug', { params: { slug } })
      if (data.available) {
        slugAvailable.value = true
        slugError.value = ''
      } else {
        slugAvailable.value = false
        slugError.value = t('userSettings.referrals.form.slugTaken')
      }
    } catch {
      slugAvailable.value = null
      slugError.value = ''
    } finally {
      slugChecking.value = false
    }
  }, 400)
}

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    const [linksRes, statsRes, regsRes] = await Promise.all([
      axios.get('/api/user/referrals'),
      axios.get('/api/user/referrals/stats'),
      axios.get('/api/user/referrals/registrations?limit=10')
    ])

    links.value = linksRes.data.links
    stats.value = statsRes.data.stats
    registrations.value = regsRes.data.registrations
  } catch (error) {
    console.error('Failed to load referral data:', error)
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingLink.value = null
  form.value = {
    label: '',
    slug: '',
    description: '',
    max_uses: null,
    expires_at: ''
  }
  slugAvailable.value = null
  slugError.value = ''
  slugChecking.value = false
  slugManuallyEdited.value = false
  showDialog.value = true
}

function editLink(link) {
  editingLink.value = link
  form.value = {
    label: link.label || '',
    slug: link.slug || '',
    description: link.description || '',
    max_uses: link.max_uses || null,
    expires_at: link.expires_at ? link.expires_at.split('T')[0] : ''
  }
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
  editingLink.value = null
}

async function saveLink() {
  saving.value = true
  try {
    const payload = {
      label: form.value.label || null,
      description: form.value.description || null,
      max_uses: form.value.max_uses || null,
      expires_at: form.value.expires_at ? new Date(form.value.expires_at).toISOString() : null
    }

    if (!editingLink.value && form.value.slug) {
      payload.slug = form.value.slug.toLowerCase().replace(/\s+/g, '-')
    }

    if (editingLink.value) {
      await axios.put(`/api/user/referrals/${editingLink.value.id}`, payload)
    } else {
      await axios.post('/api/user/referrals', payload)
    }

    await loadData()
    closeDialog()
  } catch (error) {
    console.error('Failed to save link:', error)
    alert(error.response?.data?.message || t('common.error'))
  } finally {
    saving.value = false
  }
}

async function deleteLink(link) {
  if (!confirm(t('userSettings.referrals.deleteConfirm'))) return

  try {
    await axios.delete(`/api/user/referrals/${link.id}`)
    await loadData()
  } catch (error) {
    console.error('Failed to delete link:', error)
  }
}

async function deactivateLink(link) {
  try {
    await axios.post(`/api/user/referrals/${link.id}/deactivate`)
    await loadData()
  } catch (error) {
    console.error('Failed to deactivate link:', error)
  }
}

function copyLink(link) {
  const url = getFullUrl(link)
  navigator.clipboard.writeText(url)
    .then(() => {
      // Could show a toast notification here
    })
    .catch(err => console.error('Failed to copy:', err))
}

function getFullUrl(link) {
  const base = window.location.origin
  return `${base}/join/${link.slug || link.code}`
}

function isExpired(link) {
  if (!link.expires_at) return false
  return new Date(link.expires_at) < new Date()
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString(locale.value === 'de' ? 'de-DE' : 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped>
.referral-links {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-card {
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.stat-label {
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-top: 4px;
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

.links-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.link-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: all 0.2s;
}

.link-card:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.link-card.inactive {
  opacity: 0.6;
}

.link-main {
  flex: 1;
  min-width: 0;
}

.link-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.link-label {
  font-weight: 600;
  font-size: 1rem;
}

.link-url {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.link-url code {
  background: rgba(var(--v-theme-on-surface), 0.06);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8125rem;
  color: rgb(var(--v-theme-primary));
  word-break: break-all;
}

.link-meta {
  display: flex;
  gap: 16px;
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.link-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.link-description {
  margin-top: 8px;
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.url-preview {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 6px;
  font-size: 0.8125rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.url-preview code {
  color: rgb(var(--v-theme-primary));
  word-break: break-all;
}

.optional-settings :deep(.v-expansion-panel) {
  background: transparent !important;
}

.optional-settings :deep(.v-expansion-panel-title) {
  min-height: 36px;
  padding: 4px 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.optional-settings :deep(.v-expansion-panel-text__wrapper) {
  padding: 8px 0 0;
}
</style>
