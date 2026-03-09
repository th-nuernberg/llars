<template>
  <div class="research-groups-admin">
    <!-- Header -->
    <div class="rg-header">
      <h2 class="text-h6">{{ t('researchGroup.admin.title') }}</h2>
      <LBtn variant="primary" @click="openCreateDialog">
        <v-icon start>mdi-plus</v-icon>
        {{ t('researchGroup.create') }}
      </LBtn>
    </div>

    <LLoading v-if="loading" />

    <!-- Empty State (no groups at all) -->
    <div v-else-if="!groups.length" class="text-center text-medium-emphasis pa-8">
      {{ t('researchGroup.admin.noGroups') }}
    </div>

    <!-- Master-Detail Layout -->
    <div v-else class="rg-layout" :class="{ 'rg-layout--mobile': isMobile }">

      <!-- Left Panel: Group List (hidden on mobile when detail is shown) -->
      <div v-if="!isMobile || !selectedGroupId" class="rg-list-panel">
        <v-text-field
          v-model="searchQuery"
          :placeholder="t('researchGroup.admin.search')"
          variant="outlined"
          density="compact"
          hide-details
          prepend-inner-icon="mdi-magnify"
          clearable
          class="rg-search"
        />

        <div class="rg-group-list">
          <div
            v-for="group in filteredGroups"
            :key="group.id"
            class="rg-group-item"
            :class="{ 'rg-group-item--active': selectedGroupId === group.id }"
            @click="selectGroup(group)"
          >
            <div class="rg-group-item__content">
              <div class="rg-group-item__name">{{ group.name }}</div>
              <div class="rg-group-item__slug text-caption text-medium-emphasis">{{ group.slug }}</div>
            </div>
            <v-badge
              v-if="group.stats?.pending_requests > 0"
              :content="group.stats.pending_requests"
              color="warning"
              inline
            />
          </div>
        </div>
      </div>

      <!-- Right Panel: Detail View -->
      <div v-if="!isMobile || selectedGroupId" class="rg-detail-panel">

        <!-- Mobile Back Button -->
        <LBtn v-if="isMobile && selectedGroupId" variant="text" class="mb-2" @click="selectedGroupId = null">
          <v-icon start>mdi-arrow-left</v-icon>
          {{ t('common.back') }}
        </LBtn>

        <!-- Empty state when no group selected -->
        <div v-if="!selectedGroup" class="rg-empty-state">
          <v-icon size="64" color="grey-lighten-1">mdi-account-group-outline</v-icon>
          <div class="text-body-1 text-medium-emphasis mt-3">
            {{ t('researchGroup.admin.selectGroup') }}
          </div>
        </div>

        <!-- Group Detail -->
        <template v-else>
          <!-- Detail Header -->
          <div class="rg-detail-header">
            <div class="rg-detail-header__info">
              <h3 class="text-h5 mb-1">{{ selectedGroup.name }}</h3>
              <div class="rg-detail-header__meta">
                <LTag variant="info">{{ selectedGroup.slug }}</LTag>
                <span v-if="selectedGroup.description" class="text-body-2 text-medium-emphasis">
                  {{ selectedGroup.description }}
                </span>
              </div>
            </div>
            <div class="rg-detail-header__actions">
              <LIconBtn
                icon="mdi-pencil"
                :tooltip="t('researchGroup.edit')"
                @click="editGroup(selectedGroup)"
              />
              <LIconBtn
                icon="mdi-delete"
                :tooltip="t('researchGroup.delete')"
                color="error"
                @click="openDeleteDialog(selectedGroup)"
              />
            </div>
          </div>

          <!-- Stats Row -->
          <div class="rg-stats-row">
            <LStatCard
              :value="selectedGroup.stats?.members ?? 0"
              :label="t('researchGroup.admin.stats.members')"
              icon="mdi-account-group"
              color="#b0ca97"
              size="sm"
            />
            <LStatCard
              :value="selectedGroup.stats?.conferences ?? 0"
              :label="t('researchGroup.admin.stats.conferences')"
              icon="mdi-calendar-star"
              color="#D1BC8A"
              size="sm"
            />
            <LStatCard
              :value="selectedGroup.stats?.papers ?? 0"
              :label="t('researchGroup.admin.stats.papers')"
              icon="mdi-file-document-outline"
              color="#88c4c8"
              size="sm"
            />
          </div>

          <!-- Tabs -->
          <LTabs v-model="activeTab" :tabs="detailTabs" variant="pill" class="rg-tabs" />

          <!-- Tab Content -->
          <div class="rg-tab-content">

            <!-- Members Tab -->
            <div v-if="activeTab === 'members'">
              <LLoading v-if="detailLoading" />
              <template v-else>
                <div v-if="!groupMembers.length" class="text-body-2 text-medium-emphasis pa-4">
                  {{ t('researchGroup.admin.members.noMembers') }}
                </div>

                <v-table v-else density="compact" class="members-table">
                  <tbody>
                    <tr v-for="member in groupMembers" :key="member.id">
                      <td style="width: 44px;">
                        <LAvatar
                          :username="member.username"
                          :seed="member.avatar_seed"
                          :src="member.avatar_url"
                          size="sm"
                        />
                      </td>
                      <td class="text-body-2 font-weight-medium">{{ member.username }}</td>
                      <td style="width: 160px;">
                        <v-select
                          :model-value="member.role"
                          :items="roleOptions"
                          item-title="label"
                          item-value="value"
                          variant="outlined"
                          density="compact"
                          hide-details
                          @update:model-value="handleRoleChange(member.id, $event)"
                        />
                      </td>
                      <td style="width: 40px;">
                        <LIconBtn
                          icon="mdi-close"
                          :tooltip="t('researchGroup.admin.members.removeMember')"
                          size="x-small"
                          color="error"
                          @click="openRemoveMemberDialog(member)"
                        />
                      </td>
                    </tr>
                  </tbody>
                </v-table>

                <!-- Add Member Row -->
                <div class="rg-add-member">
                  <LUserSearch
                    v-model="newMemberUser"
                    :placeholder="t('researchGroup.members.searchUser')"
                    :exclude-usernames="groupMembers.map(m => m.username)"
                    show-add-button
                    :add-button-text="t('researchGroup.admin.members.add')"
                    style="flex: 1; max-width: 400px;"
                    @add="handleAddMember"
                  />
                  <v-select
                    v-model="newMemberRole"
                    :items="roleOptions"
                    item-title="label"
                    item-value="value"
                    variant="outlined"
                    density="compact"
                    hide-details
                    style="max-width: 140px;"
                  />
                </div>
              </template>
            </div>

            <!-- Requests Tab -->
            <div v-if="activeTab === 'requests'">
              <LLoading v-if="detailLoading" />
              <template v-else>
                <div v-if="!pendingRequests.length" class="rg-empty-tab">
                  <v-icon size="48" color="grey-lighten-1">mdi-check-circle-outline</v-icon>
                  <div class="text-body-2 text-medium-emphasis mt-2">
                    {{ t('researchGroup.admin.requests.noRequests') }}
                  </div>
                </div>

                <div v-else class="rg-requests-list">
                  <div
                    v-for="req in pendingRequests"
                    :key="req.id"
                    class="rg-request-card"
                  >
                    <div class="rg-request-card__info">
                      <LAvatar :username="req.requester_username" size="sm" />
                      <div>
                        <div class="text-body-2 font-weight-medium">{{ req.requester_username }}</div>
                        <div v-if="req.message" class="text-caption text-medium-emphasis">{{ req.message }}</div>
                        <div v-if="req.created_at" class="text-caption text-medium-emphasis">
                          {{ formatDate(req.created_at) }}
                        </div>
                      </div>
                    </div>
                    <div class="rg-request-card__actions">
                      <LBtn variant="primary" size="small" @click="handleResolveRequest(req.id, 'approve')">
                        {{ t('researchGroup.accessRequest.approve') }}
                      </LBtn>
                      <LBtn variant="cancel" size="small" @click="handleResolveRequest(req.id, 'reject')">
                        {{ t('researchGroup.accessRequest.reject') }}
                      </LBtn>
                    </div>
                  </div>
                </div>
              </template>
            </div>

            <!-- Content Tab -->
            <div v-if="activeTab === 'content'">
              <LLoading v-if="detailLoading" />
              <template v-else>
                <!-- Conferences Section -->
                <div class="rg-content-section">
                  <div class="rg-content-section__header">
                    <h4 class="text-subtitle-1 font-weight-medium">
                      {{ t('researchGroup.admin.content.conferences') }}
                      <span class="text-caption text-medium-emphasis">({{ groupConferences.length }})</span>
                    </h4>
                  </div>

                  <div v-if="!groupConferences.length" class="text-body-2 text-medium-emphasis pa-3">
                    {{ t('researchGroup.admin.content.noConferences') }}
                  </div>

                  <LListTable
                    v-else
                    :columns="conferenceColumns"
                    :items="groupConferences"
                    item-key="id"
                    striped
                    :clickable="false"
                  >
                    <template #row="{ item: conf }">
                      <div class="l-col col-acronym">
                        <span class="font-weight-medium">{{ conf.acronym }} {{ conf.year }}</span>
                      </div>
                      <div class="l-col col-name">
                        <span>{{ conf.name }}</span>
                      </div>
                      <div class="l-col col-ranking">
                        <LTag v-if="conf.core_ranking" variant="info">{{ conf.core_ranking }}</LTag>
                      </div>
                      <div class="l-col col-location">
                        <span class="text-caption">{{ conf.location || '—' }}</span>
                      </div>
                      <div class="l-col col-deadline">
                        <span class="text-caption">{{ conf.submission_deadline ? formatDate(conf.submission_deadline) : '—' }}</span>
                      </div>
                    </template>
                  </LListTable>
                </div>

                <!-- Papers Section -->
                <div class="rg-content-section">
                  <div class="rg-content-section__header">
                    <h4 class="text-subtitle-1 font-weight-medium">
                      {{ t('researchGroup.admin.content.papers') }}
                      <span class="text-caption text-medium-emphasis">({{ groupPapers.length }})</span>
                    </h4>
                  </div>

                  <div v-if="!groupPapers.length" class="text-body-2 text-medium-emphasis pa-3">
                    {{ t('researchGroup.admin.content.noPapers') }}
                  </div>

                  <LListTable
                    v-else
                    :columns="paperColumns"
                    :items="groupPapers"
                    item-key="id"
                    striped
                    :clickable="false"
                  >
                    <template #row="{ item: paper }">
                      <div class="l-col col-title">
                        <span>{{ paper.title }}</span>
                      </div>
                      <div class="l-col col-status">
                        <LTag :variant="paperStatusVariant(paper.status)">{{ paper.status || '—' }}</LTag>
                      </div>
                      <div class="l-col col-conference">
                        <span class="text-caption">{{ paper.conference_acronym || '—' }}</span>
                      </div>
                      <div class="l-col col-authors">
                        <span class="text-caption">{{ (paper.authors || []).join(', ') || '—' }}</span>
                      </div>
                    </template>
                  </LListTable>
                </div>
              </template>
            </div>

          </div>
        </template>
      </div>
    </div>

    <!-- Create/Edit Group Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="500" persistent>
      <v-card class="dialog-card">
        <v-card-title>
          {{ editingGroup ? t('researchGroup.edit') : t('researchGroup.create') }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="formData.name"
            :label="t('researchGroup.name')"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-text-field
            v-model="formData.slug"
            :label="t('researchGroup.slug')"
            variant="outlined"
            density="compact"
            hint="URL-safe identifier"
            persistent-hint
            class="mb-3"
          />
          <v-textarea
            v-model="formData.description"
            :label="t('researchGroup.description')"
            variant="outlined"
            density="compact"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDialog">{{ t('common.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="saving" @click="saveGroup">
            {{ editingGroup ? t('common.save') : t('researchGroup.create') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Group Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="520">
      <v-card class="dialog-card">
        <v-card-title class="d-flex align-center" style="gap: 8px;">
          <v-icon color="error">mdi-alert-circle-outline</v-icon>
          {{ t('researchGroup.admin.deleteDialog.title') }}
        </v-card-title>
        <v-card-text>
          <p class="text-body-1 mb-2">
            {{ t('researchGroup.admin.deleteDialog.confirm', { name: groupToDelete?.name }) }}
          </p>
          <p class="text-body-2 text-medium-emphasis">
            {{ t('researchGroup.admin.deleteDialog.info') }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showDeleteDialog = false">{{ t('common.cancel') }}</LBtn>
          <LBtn variant="danger" :loading="saving" @click="confirmDelete">
            {{ t('researchGroup.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Remove Member Dialog -->
    <v-dialog v-model="showRemoveMemberDialog" max-width="480">
      <v-card class="dialog-card">
        <v-card-title class="d-flex align-center" style="gap: 8px;">
          <v-icon color="warning">mdi-account-remove-outline</v-icon>
          {{ t('researchGroup.admin.removeMemberDialog.title') }}
        </v-card-title>
        <v-card-text>
          <p class="text-body-1">
            {{ t('researchGroup.admin.removeMemberDialog.confirm', { name: memberToRemove?.username }) }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showRemoveMemberDialog = false">{{ t('common.cancel') }}</LBtn>
          <LBtn variant="danger" :loading="saving" @click="confirmRemoveMember">
            {{ t('researchGroup.admin.members.removeMember') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from '@/views/ConferenceManager/composables/useResearchGroups'
import { useMobile } from '@/composables/useMobile'

const { t } = useI18n()
const { isMobile } = useMobile()
const {
  fetchAllGroups, allGroups,
  createGroup, updateGroup, deleteGroup,
  fetchMembers, addMember, updateMemberRole, removeMember,
  fetchGroupRequests, resolveAccessRequest,
  fetchGroupConferences, fetchGroupPapers,
} = useResearchGroups()

// ── List State ──────────────────────────────────────────
const loading = ref(true)
const groups = ref([])
const searchQuery = ref('')
const selectedGroupId = ref(null)

// ── Detail State ────────────────────────────────────────
const activeTab = ref('members')
const detailLoading = ref(false)
const groupMembers = ref([])
const pendingRequests = ref([])
const groupConferences = ref([])
const groupPapers = ref([])

// ── Dialog State ────────────────────────────────────────
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const showRemoveMemberDialog = ref(false)
const editingGroup = ref(null)
const groupToDelete = ref(null)
const memberToRemove = ref(null)
const saving = ref(false)
const formData = ref({ name: '', slug: '', description: '' })
const newMemberUser = ref(null)
const newMemberRole = ref('member')

// ── Computed ────────────────────────────────────────────
const filteredGroups = computed(() => {
  if (!searchQuery.value) return groups.value
  const q = searchQuery.value.toLowerCase()
  return groups.value.filter(g =>
    g.name.toLowerCase().includes(q) || g.slug.toLowerCase().includes(q)
  )
})

const selectedGroup = computed(() =>
  groups.value.find(g => g.id === selectedGroupId.value) || null
)

const detailTabs = computed(() => [
  { value: 'members', label: t('researchGroup.admin.tabs.members') },
  {
    value: 'requests',
    label: t('researchGroup.admin.tabs.requests'),
    badge: pendingRequests.value.length || undefined,
  },
  { value: 'content', label: t('researchGroup.admin.tabs.content') },
])

const roleOptions = computed(() => [
  { label: t('researchGroup.members.roles.owner'), value: 'owner' },
  { label: t('researchGroup.members.roles.member'), value: 'member' },
  { label: t('researchGroup.members.roles.viewer'), value: 'viewer' },
])

const conferenceColumns = computed(() => [
  { key: 'acronym', label: 'Conference', width: '120px' },
  { key: 'name', label: t('researchGroup.name'), flex: 1 },
  { key: 'ranking', label: 'Ranking', width: '100px' },
  { key: 'location', label: t('researchGroup.admin.content.location'), width: '140px' },
  { key: 'deadline', label: t('researchGroup.admin.content.deadline'), width: '120px' },
])

const paperColumns = computed(() => [
  { key: 'title', label: 'Title', flex: 1 },
  { key: 'status', label: 'Status', width: '120px' },
  { key: 'conference', label: 'Conference', width: '120px' },
  { key: 'authors', label: 'Authors', width: '200px' },
])

// ── Data Loading ────────────────────────────────────────
async function loadGroups() {
  loading.value = true
  try {
    await fetchAllGroups()
    groups.value = allGroups.value
  } finally {
    loading.value = false
  }
}

async function selectGroup(group) {
  selectedGroupId.value = group.id
  activeTab.value = 'members'
  await loadGroupDetail(group.id)
}

async function loadGroupDetail(groupId) {
  detailLoading.value = true
  try {
    const [members, requests, conferences, papers] = await Promise.all([
      fetchMembers(groupId),
      fetchGroupRequests(groupId),
      fetchGroupConferences(groupId),
      fetchGroupPapers(groupId),
    ])
    groupMembers.value = members
    pendingRequests.value = requests.filter(r => r.status === 'pending')
    groupConferences.value = conferences
    groupPapers.value = papers
  } finally {
    detailLoading.value = false
  }
}

// ── Member Actions ──────────────────────────────────────
async function handleAddMember(user) {
  if (!user || !selectedGroupId.value) return
  try {
    await addMember(selectedGroupId.value, user.id, newMemberRole.value)
    newMemberUser.value = null
    await refreshDetail()
  } catch (err) {
    console.error('Failed to add member:', err)
  }
}

async function handleRoleChange(memberId, newRole) {
  try {
    await updateMemberRole(selectedGroupId.value, memberId, newRole)
    groupMembers.value = await fetchMembers(selectedGroupId.value)
  } catch (err) {
    console.error('Failed to update role:', err)
  }
}

function openRemoveMemberDialog(member) {
  memberToRemove.value = member
  showRemoveMemberDialog.value = true
}

async function confirmRemoveMember() {
  if (!memberToRemove.value) return
  saving.value = true
  try {
    await removeMember(selectedGroupId.value, memberToRemove.value.id)
    showRemoveMemberDialog.value = false
    memberToRemove.value = null
    await refreshDetail()
  } catch (err) {
    console.error('Failed to remove member:', err)
  } finally {
    saving.value = false
  }
}

// ── Request Actions ─────────────────────────────────────
async function handleResolveRequest(requestId, action) {
  try {
    await resolveAccessRequest(requestId, action)
    await refreshDetail()
  } catch (err) {
    console.error('Failed to resolve request:', err)
  }
}

// ── Group CRUD ──────────────────────────────────────────
function openCreateDialog() {
  editingGroup.value = null
  formData.value = { name: '', slug: '', description: '' }
  showCreateDialog.value = true
}

function editGroup(group) {
  editingGroup.value = group
  formData.value = {
    name: group.name,
    slug: group.slug,
    description: group.description || '',
  }
  showCreateDialog.value = true
}

function closeDialog() {
  showCreateDialog.value = false
  editingGroup.value = null
  formData.value = { name: '', slug: '', description: '' }
}

async function saveGroup() {
  saving.value = true
  try {
    if (editingGroup.value) {
      await updateGroup(editingGroup.value.id, formData.value)
    } else {
      await createGroup(formData.value)
    }
    closeDialog()
    await loadGroups()
  } catch (err) {
    console.error('Failed to save group:', err)
  } finally {
    saving.value = false
  }
}

function openDeleteDialog(group) {
  groupToDelete.value = group
  showDeleteDialog.value = true
}

async function confirmDelete() {
  if (!groupToDelete.value) return
  saving.value = true
  try {
    const deletedId = groupToDelete.value.id
    await deleteGroup(deletedId)
    showDeleteDialog.value = false
    groupToDelete.value = null
    if (selectedGroupId.value === deletedId) {
      selectedGroupId.value = null
    }
    await loadGroups()
  } catch (err) {
    console.error('Failed to delete group:', err)
  } finally {
    saving.value = false
  }
}

// ── Helpers ─────────────────────────────────────────────
async function refreshDetail() {
  await Promise.all([
    loadGroupDetail(selectedGroupId.value),
    loadGroups(),
  ])
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  try {
    return new Date(dateStr).toLocaleDateString()
  } catch {
    return dateStr
  }
}

function paperStatusVariant(status) {
  const map = { draft: 'warning', submitted: 'info', accepted: 'success', rejected: 'danger', published: 'success' }
  return map[status?.toLowerCase()] || 'info'
}

// ── Init ────────────────────────────────────────────────
onMounted(loadGroups)
</script>

<style scoped>
.rg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

/* Master-Detail Layout */
.rg-layout {
  display: flex;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  min-height: 500px;
}

.rg-layout--mobile {
  flex-direction: column;
  border: none;
  border-radius: 0;
}

/* Left Panel */
.rg-list-panel {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.rg-layout--mobile .rg-list-panel {
  width: 100%;
  min-width: unset;
  border-right: none;
}

.rg-search {
  margin: 12px;
}

.rg-group-list {
  flex: 1;
  overflow-y: auto;
}

.rg-group-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.15s;
  border-left: 3px solid transparent;
}

.rg-group-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.04);
}

.rg-group-item--active {
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-left-color: rgb(var(--v-theme-primary));
}

.rg-group-item__content {
  min-width: 0;
  flex: 1;
}

.rg-group-item__name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rg-group-item__slug {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Right Panel */
.rg-detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-width: 0;
}

.rg-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}

/* Detail Header */
.rg-detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.rg-detail-header__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.rg-detail-header__actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* Stats Row */
.rg-stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.rg-stats-row > * {
  flex: 1;
}

/* Tabs */
.rg-tabs {
  margin-bottom: 16px;
}

.rg-tab-content {
  min-height: 200px;
}

/* Members Table */
.members-table {
  background: transparent;
}

.members-table :deep(td) {
  padding-top: 4px;
  padding-bottom: 4px;
}

.rg-add-member {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Requests */
.rg-empty-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
}

.rg-requests-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rg-request-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(var(--v-theme-warning), 0.06);
  border-radius: 16px 4px 16px 4px;
  gap: 12px;
}

.rg-request-card__info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.rg-request-card__actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

/* Content Sections */
.rg-content-section {
  margin-bottom: 24px;
}

.rg-content-section:last-child {
  margin-bottom: 0;
}

.rg-content-section__header {
  margin-bottom: 8px;
}

/* Dialogs */
.dialog-card {
  border-radius: 16px 4px 16px 4px;
}

/* Responsive */
@media (max-width: 960px) {
  .rg-stats-row {
    flex-wrap: wrap;
  }

  .rg-stats-row > * {
    flex: 1 1 calc(50% - 6px);
    min-width: 120px;
  }
}
</style>
