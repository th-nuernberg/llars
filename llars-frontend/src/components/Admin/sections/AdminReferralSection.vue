<template>
  <div class="admin-referral-section">
    <!-- Header with Analytics Overview -->
    <LCard title="Referral-System" icon="mdi-account-group" class="mb-4">
      <template #actions>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          @click="showCreateCampaignDialog = true"
        >
          Neue Kampagne
        </LBtn>
      </template>

      <!-- Analytics Overview -->
      <div v-if="overview" class="analytics-overview mb-4">
        <v-row dense>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ overview.total_campaigns }}</div>
              <div class="stat-label">Kampagnen</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-success">{{ overview.active_campaigns }}</div>
              <div class="stat-label">Aktiv</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ overview.total_links }}</div>
              <div class="stat-label">Links</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-primary">{{ overview.total_registrations }}</div>
              <div class="stat-label">Registrierungen</div>
            </div>
          </v-col>
        </v-row>

        <v-row dense class="mt-2">
          <v-col cols="12" sm="6">
            <v-alert
              :type="overview.referral_enabled ? 'success' : 'warning'"
              variant="tonal"
              density="compact"
            >
              <template #prepend>
                <v-icon>{{ overview.referral_enabled ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              </template>
              Referral-System: {{ overview.referral_enabled ? 'Aktiviert' : 'Deaktiviert' }}
            </v-alert>
          </v-col>
          <v-col cols="12" sm="6">
            <v-alert
              :type="overview.self_registration_enabled ? 'success' : 'warning'"
              variant="tonal"
              density="compact"
            >
              <template #prepend>
                <v-icon>{{ overview.self_registration_enabled ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              </template>
              Selbst-Registrierung: {{ overview.self_registration_enabled ? 'Aktiviert' : 'Deaktiviert' }}
            </v-alert>
          </v-col>
        </v-row>
      </div>

      <v-skeleton-loader v-else type="article" />
    </LCard>

    <!-- Campaigns List -->
    <LCard title="Kampagnen" icon="mdi-bullhorn" class="mb-4">
      <template #actions>
        <v-checkbox
          v-model="showArchived"
          label="Archivierte anzeigen"
          density="compact"
          hide-details
          class="mr-2"
        />
      </template>

      <v-data-table
        :headers="campaignHeaders"
        :items="campaigns"
        :loading="loading"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Status Column -->
        <template #item.status="{ item }">
          <LTag :variant="getStatusVariant(item.status)" size="sm">
            {{ getStatusLabel(item.status) }}
          </LTag>
        </template>

        <!-- Links Column -->
        <template #item.link_count="{ item }">
          <v-chip size="small" variant="outlined">
            {{ item.link_count }} Links
          </v-chip>
        </template>

        <!-- Dates Column -->
        <template #item.dates="{ item }">
          <span class="text-caption">
            {{ formatDateRange(item.start_date, item.end_date) }}
          </span>
        </template>

        <!-- Actions Column -->
        <template #item.actions="{ item }">
          <LActionGroup
            :actions="getCampaignActions(item)"
            @action="handleCampaignAction($event, item)"
            size="small"
          />
        </template>
      </v-data-table>
    </LCard>

    <!-- Selected Campaign Details -->
    <LCard
      v-if="selectedCampaign"
      :title="`Kampagne: ${selectedCampaign.name}`"
      icon="mdi-link-variant"
      class="mb-4"
    >
      <template #actions>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          @click="showCreateLinkDialog = true"
        >
          Neuer Link
        </LBtn>
        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-close"
          @click="selectedCampaign = null"
          class="ml-2"
        >
          Schließen
        </LBtn>
      </template>

      <!-- Campaign Info -->
      <v-row dense class="mb-4">
        <v-col cols="12" md="6">
          <div class="text-subtitle-2 mb-1">Beschreibung</div>
          <div class="text-body-2">{{ selectedCampaign.description || 'Keine Beschreibung' }}</div>
        </v-col>
        <v-col cols="12" md="3">
          <div class="text-subtitle-2 mb-1">Status</div>
          <v-select
            v-model="selectedCampaign.status"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            @update:model-value="updateCampaignStatus"
          />
        </v-col>
        <v-col cols="12" md="3">
          <div class="text-subtitle-2 mb-1">Max. Registrierungen</div>
          <div class="text-body-2">{{ selectedCampaign.max_registrations || 'Unbegrenzt' }}</div>
        </v-col>
      </v-row>

      <!-- Links Table -->
      <v-data-table
        :headers="linkHeaders"
        :items="campaignLinks"
        :loading="linksLoading"
        :items-per-page="5"
        class="elevation-0"
      >
        <!-- Code/Slug Column -->
        <template #item.identifier="{ item }">
          <div>
            <code class="text-primary">{{ item.slug || item.code }}</code>
            <v-btn
              icon
              size="x-small"
              variant="text"
              @click="copyLink(item)"
              class="ml-1"
            >
              <v-icon size="small">mdi-content-copy</v-icon>
            </v-btn>
          </div>
          <div v-if="item.label" class="text-caption text-medium-emphasis">{{ item.label }}</div>
        </template>

        <!-- Role Column -->
        <template #item.role_name="{ item }">
          <LTag variant="info" size="sm">{{ item.role_name }}</LTag>
        </template>

        <!-- Stats Column -->
        <template #item.stats="{ item }">
          <span>{{ item.registrations || 0 }}</span>
          <span v-if="item.max_uses" class="text-medium-emphasis">
            / {{ item.max_uses }}
          </span>
        </template>

        <!-- Active Column -->
        <template #item.is_active="{ item }">
          <v-switch
            :model-value="item.is_active"
            @update:model-value="toggleLinkActive(item, $event)"
            color="success"
            density="compact"
            hide-details
          />
        </template>

        <!-- Actions Column -->
        <template #item.actions="{ item }">
          <v-btn
            icon
            size="small"
            variant="text"
            color="error"
            @click="confirmDeleteLink(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </LCard>

    <!-- Recent Registrations -->
    <LCard title="Letzte Registrierungen" icon="mdi-account-check" class="mb-4">
      <template #actions>
        <v-btn
          v-if="selectedCampaign"
          variant="text"
          size="small"
          @click="filterRegistrationsByCampaign"
        >
          Nur {{ selectedCampaign.name }}
        </v-btn>
        <v-btn
          v-if="registrationFilter"
          variant="text"
          size="small"
          color="error"
          @click="clearRegistrationFilter"
        >
          Filter zurücksetzen
        </v-btn>
      </template>

      <v-data-table
        :headers="registrationHeaders"
        :items="registrations"
        :loading="registrationsLoading"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Username Column -->
        <template #item.username="{ item }">
          <div class="d-flex align-center">
            <v-avatar size="28" color="primary" class="mr-2">
              <span class="text-caption text-uppercase">{{ item.username?.charAt(0) }}</span>
            </v-avatar>
            <span class="font-weight-medium">{{ item.username }}</span>
          </div>
        </template>

        <!-- Source Column (Link/Campaign) -->
        <template #item.source="{ item }">
          <div>
            <code class="text-primary text-caption">{{ item.link_slug || item.link_code }}</code>
            <span v-if="item.link_label" class="text-caption text-medium-emphasis ml-1">
              ({{ item.link_label }})
            </span>
          </div>
          <div class="text-caption text-medium-emphasis">
            {{ item.campaign_name }}
          </div>
        </template>

        <!-- Role Column -->
        <template #item.role_assigned="{ item }">
          <LTag variant="info" size="sm">{{ item.role_assigned }}</LTag>
        </template>

        <!-- Date Column -->
        <template #item.registered_at="{ item }">
          <span class="text-caption">{{ formatDateTime(item.registered_at) }}</span>
        </template>
      </v-data-table>

      <div v-if="registrationTotal > registrations.length" class="text-center mt-2">
        <v-btn variant="text" size="small" @click="loadMoreRegistrations">
          Mehr laden ({{ registrationTotal - registrations.length }} weitere)
        </v-btn>
      </div>
    </LCard>

    <!-- Create Campaign Dialog -->
    <v-dialog v-model="showCreateCampaignDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-bullhorn-variant</v-icon>
          Neue Kampagne erstellen
        </v-card-title>
        <v-card-text>
          <v-form ref="campaignForm" v-model="campaignFormValid">
            <v-text-field
              v-model="newCampaign.name"
              label="Name"
              :rules="[v => !!v || 'Name ist erforderlich']"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <v-textarea
              v-model="newCampaign.description"
              label="Beschreibung (optional)"
              variant="outlined"
              density="comfortable"
              rows="2"
              class="mb-3"
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="newCampaign.start_date"
                  label="Startdatum (optional)"
                  type="datetime-local"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="newCampaign.end_date"
                  label="Enddatum (optional)"
                  type="datetime-local"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model.number="newCampaign.max_registrations"
              label="Max. Registrierungen (optional)"
              type="number"
              variant="outlined"
              density="comfortable"
              hint="Leer lassen für unbegrenzt"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showCreateCampaignDialog = false">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            @click="createCampaign"
            :loading="creating"
            :disabled="!campaignFormValid"
          >
            Erstellen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Link Dialog -->
    <v-dialog v-model="showCreateLinkDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-link-plus</v-icon>
          Neuen Link erstellen
        </v-card-title>
        <v-card-text>
          <v-form ref="linkForm" v-model="linkFormValid">
            <v-text-field
              v-model="newLink.slug"
              label="Custom Slug (optional)"
              variant="outlined"
              density="comfortable"
              hint="z.B. ki-konferenz-2026 (nur Kleinbuchstaben, Zahlen, -)"
              persistent-hint
              class="mb-3"
              :rules="slugRules"
            />
            <v-text-field
              v-model="newLink.label"
              label="Label/Beschreibung (optional)"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <v-select
              v-model="newLink.role_name"
              :items="availableRoles"
              label="Rolle für neue User"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <v-text-field
              v-model.number="newLink.max_uses"
              label="Max. Verwendungen (optional)"
              type="number"
              variant="outlined"
              density="comfortable"
              hint="Leer lassen für unbegrenzt"
              class="mb-3"
            />
            <v-text-field
              v-model="newLink.expires_at"
              label="Ablaufdatum (optional)"
              type="datetime-local"
              variant="outlined"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showCreateLinkDialog = false">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            @click="createLink"
            :loading="creatingLink"
            :disabled="!linkFormValid"
          >
            Erstellen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          {{ deleteDialogTitle }}
        </v-card-title>
        <v-card-text>{{ deleteDialogText }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showDeleteDialog = false">Abbrechen</LBtn>
          <LBtn variant="danger" @click="executeDelete" :loading="deleting">Löschen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useReferralSystem } from '@/composables/useReferralSystem'
import { useSnackbar } from '@/composables/useSnackbar'

const referral = useReferralSystem()
const { showSnackbar } = useSnackbar()

// State
const loading = ref(false)
const linksLoading = ref(false)
const creating = ref(false)
const creatingLink = ref(false)
const deleting = ref(false)

const overview = ref(null)
const campaigns = ref([])
const selectedCampaign = ref(null)
const campaignLinks = ref([])
const showArchived = ref(false)

// Dialogs
const showCreateCampaignDialog = ref(false)
const showCreateLinkDialog = ref(false)
const showDeleteDialog = ref(false)
const deleteDialogTitle = ref('')
const deleteDialogText = ref('')
const deleteTarget = ref(null)
const deleteType = ref('') // 'campaign' or 'link'

// Forms
const campaignForm = ref(null)
const linkForm = ref(null)
const campaignFormValid = ref(false)
const linkFormValid = ref(false)

const newCampaign = ref({
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  max_registrations: null
})

const newLink = ref({
  slug: '',
  label: '',
  role_name: 'evaluator',
  max_uses: null,
  expires_at: ''
})

const availableRoles = ['admin', 'researcher', 'evaluator', 'chatbot_manager']

const slugRules = [
  v => !v || /^[a-z0-9-]+$/.test(v) || 'Nur Kleinbuchstaben, Zahlen und Bindestriche erlaubt'
]

const statusOptions = [
  { label: 'Entwurf', value: 'draft' },
  { label: 'Aktiv', value: 'active' },
  { label: 'Pausiert', value: 'paused' },
  { label: 'Abgelaufen', value: 'expired' },
  { label: 'Archiviert', value: 'archived' }
]

// Table headers
const campaignHeaders = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Links', key: 'link_count', sortable: true },
  { title: 'Zeitraum', key: 'dates', sortable: false },
  { title: 'Erstellt von', key: 'created_by', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' }
]

const linkHeaders = [
  { title: 'Code/Slug', key: 'identifier', sortable: false },
  { title: 'Rolle', key: 'role_name', sortable: true },
  { title: 'Registrierungen', key: 'stats', sortable: false },
  { title: 'Aktiv', key: 'is_active', sortable: true },
  { title: '', key: 'actions', sortable: false, align: 'end' }
]

const registrationHeaders = [
  { title: 'Benutzer', key: 'username', sortable: true },
  { title: 'Quelle', key: 'source', sortable: false },
  { title: 'Rolle', key: 'role_assigned', sortable: true },
  { title: 'Registriert am', key: 'registered_at', sortable: true }
]

// Registrations state
const registrations = ref([])
const registrationsLoading = ref(false)
const registrationTotal = ref(0)
const registrationFilter = ref(null) // { campaign_id: X } or { link_id: Y }

// Load data
onMounted(async () => {
  await loadOverview()
  await loadCampaigns()
  await loadRegistrations()
})

// Watch for archive filter changes
watch(showArchived, () => {
  loadCampaigns()
})

async function loadOverview() {
  try {
    overview.value = await referral.getAnalyticsOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

async function loadCampaigns() {
  loading.value = true
  try {
    campaigns.value = await referral.listCampaigns(showArchived.value)
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function loadCampaignLinks(campaignId) {
  linksLoading.value = true
  try {
    campaignLinks.value = await referral.listCampaignLinks(campaignId)
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    linksLoading.value = false
  }
}

async function loadRegistrations(append = false) {
  registrationsLoading.value = true
  try {
    const params = {
      limit: 20,
      offset: append ? registrations.value.length : 0,
      ...registrationFilter.value
    }
    const result = await referral.listRegistrations(params)
    if (append) {
      registrations.value = [...registrations.value, ...result.registrations]
    } else {
      registrations.value = result.registrations
    }
    registrationTotal.value = result.total
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    registrationsLoading.value = false
  }
}

function filterRegistrationsByCampaign() {
  if (!selectedCampaign.value) return
  registrationFilter.value = { campaign_id: selectedCampaign.value.id }
  loadRegistrations()
}

function clearRegistrationFilter() {
  registrationFilter.value = null
  loadRegistrations()
}

function loadMoreRegistrations() {
  loadRegistrations(true)
}

function formatDateTime(isoString) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Status helpers
function getStatusVariant(status) {
  const variants = {
    draft: 'secondary',
    active: 'success',
    paused: 'warning',
    expired: 'danger',
    archived: 'secondary'
  }
  return variants[status] || 'secondary'
}

function getStatusLabel(status) {
  return referral.getStatusLabel(status)
}

// Date formatting
function formatDateRange(start, end) {
  if (!start && !end) return 'Kein Zeitraum'
  const formatDate = (d) => new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' })
  if (start && end) return `${formatDate(start)} - ${formatDate(end)}`
  if (start) return `Ab ${formatDate(start)}`
  return `Bis ${formatDate(end)}`
}

// Campaign actions
function getCampaignActions(campaign) {
  return ['view', 'edit', 'delete']
}

async function handleCampaignAction(action, campaign) {
  switch (action) {
    case 'view':
      selectedCampaign.value = campaign
      await loadCampaignLinks(campaign.id)
      break
    case 'edit':
      selectedCampaign.value = campaign
      await loadCampaignLinks(campaign.id)
      break
    case 'delete':
      confirmDeleteCampaign(campaign)
      break
  }
}

// Create campaign
async function createCampaign() {
  if (!campaignFormValid.value) return

  creating.value = true
  try {
    const data = { ...newCampaign.value }
    // Convert empty strings to null
    if (!data.start_date) data.start_date = null
    if (!data.end_date) data.end_date = null
    if (!data.max_registrations) data.max_registrations = null

    await referral.createCampaign(data)
    showSnackbar('Kampagne erstellt', 'success')
    showCreateCampaignDialog.value = false
    resetCampaignForm()
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    creating.value = false
  }
}

function resetCampaignForm() {
  newCampaign.value = {
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    max_registrations: null
  }
}

// Update campaign status
async function updateCampaignStatus() {
  if (!selectedCampaign.value) return

  try {
    await referral.updateCampaignStatus(selectedCampaign.value.id, selectedCampaign.value.status)
    showSnackbar('Status aktualisiert', 'success')
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

// Create link
async function createLink() {
  if (!linkFormValid.value || !selectedCampaign.value) return

  creatingLink.value = true
  try {
    const data = { ...newLink.value }
    // Convert empty strings to null
    if (!data.slug) data.slug = null
    if (!data.label) data.label = null
    if (!data.max_uses) data.max_uses = null
    if (!data.expires_at) data.expires_at = null

    const link = await referral.createLink(selectedCampaign.value.id, data)
    showSnackbar(`Link erstellt: ${link.url}`, 'success')
    showCreateLinkDialog.value = false
    resetLinkForm()
    await loadCampaignLinks(selectedCampaign.value.id)
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    creatingLink.value = false
  }
}

function resetLinkForm() {
  newLink.value = {
    slug: '',
    label: '',
    role_name: 'evaluator',
    max_uses: null,
    expires_at: ''
  }
}

// Toggle link active
async function toggleLinkActive(link, active) {
  try {
    await referral.updateLink(link.id, { is_active: active })
    link.is_active = active
    showSnackbar(active ? 'Link aktiviert' : 'Link deaktiviert', 'success')
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

// Copy link
async function copyLink(link) {
  const success = await referral.copyLinkToClipboard(link)
  if (success) {
    showSnackbar('Link kopiert', 'success')
  } else {
    showSnackbar('Kopieren fehlgeschlagen', 'error')
  }
}

// Delete confirmation
function confirmDeleteCampaign(campaign) {
  deleteTarget.value = campaign
  deleteType.value = 'campaign'
  deleteDialogTitle.value = 'Kampagne löschen?'
  deleteDialogText.value = `Die Kampagne "${campaign.name}" und alle zugehörigen Links werden unwiderruflich gelöscht.`
  showDeleteDialog.value = true
}

function confirmDeleteLink(link) {
  deleteTarget.value = link
  deleteType.value = 'link'
  deleteDialogTitle.value = 'Link löschen?'
  deleteDialogText.value = `Der Link "${link.slug || link.code}" wird unwiderruflich gelöscht.`
  showDeleteDialog.value = true
}

async function executeDelete() {
  deleting.value = true
  try {
    if (deleteType.value === 'campaign') {
      await referral.deleteCampaign(deleteTarget.value.id)
      showSnackbar('Kampagne gelöscht', 'success')
      if (selectedCampaign.value?.id === deleteTarget.value.id) {
        selectedCampaign.value = null
        campaignLinks.value = []
      }
      await loadCampaigns()
    } else {
      await referral.deleteLink(deleteTarget.value.id)
      showSnackbar('Link gelöscht', 'success')
      if (selectedCampaign.value) {
        await loadCampaignLinks(selectedCampaign.value.id)
      }
    }
    await loadOverview()
    showDeleteDialog.value = false
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.admin-referral-section {
  padding: 0;
}

.analytics-overview {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: var(--llars-radius-sm);
  padding: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-xs);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>
