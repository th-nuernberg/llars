<template>
  <div class="research-groups-admin">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-4">
      <h2 class="text-h6">{{ t('researchGroup.admin.title') }}</h2>
      <LBtn variant="primary" @click="showCreateDialog = true">
        <v-icon start>mdi-plus</v-icon>
        {{ t('researchGroup.create') }}
      </LBtn>
    </div>

    <LLoading v-if="loading" />

    <!-- Empty State -->
    <div v-else-if="!groups.length" class="text-center text-medium-emphasis pa-8">
      {{ t('researchGroup.admin.noGroups') }}
    </div>

    <!-- Group Cards -->
    <div v-else class="d-flex flex-column" style="gap: 12px;">
      <v-card
        v-for="group in groups"
        :key="group.id"
        variant="outlined"
        class="group-card"
      >
        <!-- Card Header -->
        <div class="d-flex align-center pa-4" style="gap: 12px;">
          <v-btn
            variant="text"
            density="compact"
            :icon="expandedGroups[group.id] ? 'mdi-chevron-down' : 'mdi-chevron-right'"
            size="small"
            @click="toggleExpand(group)"
          />

          <div class="flex-grow-1">
            <div class="d-flex align-center" style="gap: 8px;">
              <span class="text-subtitle-1 font-weight-medium">{{ group.name }}</span>
              <span class="text-caption text-medium-emphasis">({{ group.slug }})</span>
            </div>
            <div v-if="group.description" class="text-caption text-medium-emphasis">
              {{ group.description }}
            </div>
          </div>

          <!-- Stat Chips -->
          <div class="d-flex align-center" style="gap: 8px;">
            <v-chip size="small" variant="tonal" color="primary">
              <v-icon start size="14">mdi-account-group</v-icon>
              {{ group.stats?.members ?? group.member_count }} {{ t('researchGroup.admin.stats.members') }}
            </v-chip>
            <v-chip size="small" variant="tonal" color="secondary">
              <v-icon start size="14">mdi-calendar-star</v-icon>
              {{ group.stats?.conferences ?? 0 }} {{ t('researchGroup.admin.stats.conferences') }}
            </v-chip>
            <v-chip size="small" variant="tonal" color="accent">
              <v-icon start size="14">mdi-file-document-outline</v-icon>
              {{ group.stats?.papers ?? 0 }} {{ t('researchGroup.admin.stats.papers') }}
            </v-chip>
          </div>

          <!-- Actions -->
          <div class="d-flex" style="gap: 4px;">
            <LIconBtn
              icon="mdi-pencil"
              :tooltip="t('researchGroup.edit')"
              size="small"
              @click="editGroup(group)"
            />
            <LIconBtn
              icon="mdi-delete"
              :tooltip="t('researchGroup.delete')"
              size="small"
              color="error"
              @click="confirmDelete(group)"
            />
          </div>
        </div>

        <!-- Expanded Members Section -->
        <v-expand-transition>
          <div v-if="expandedGroups[group.id]">
            <v-divider />
            <div class="pa-4">
              <!-- Pending Access Requests -->
              <div v-if="groupRequests[group.id]?.length" class="mb-4">
                <div class="text-subtitle-2 mb-2">{{ t('researchGroup.accessRequest.pending') }}</div>
                <div
                  v-for="req in groupRequests[group.id]"
                  :key="req.id"
                  class="d-flex align-center pa-2 mb-1 rounded"
                  style="background: rgba(var(--v-theme-warning), 0.08);"
                >
                  <LAvatar :username="req.username" size="sm" class="mr-2" />
                  <span class="text-body-2 flex-grow-1">
                    {{ req.username }}
                    <span v-if="req.message" class="text-caption text-medium-emphasis ml-1">&mdash; {{ req.message }}</span>
                  </span>
                  <LBtn variant="primary" size="x-small" class="mr-1" @click="handleResolveRequest(req.id, 'approve', group.id)">
                    {{ t('researchGroup.accessRequest.approve') }}
                  </LBtn>
                  <LBtn variant="cancel" size="x-small" @click="handleResolveRequest(req.id, 'reject', group.id)">
                    {{ t('researchGroup.accessRequest.reject') }}
                  </LBtn>
                </div>
              </div>

              <!-- Member List -->
              <div class="text-subtitle-2 mb-2">{{ t('researchGroup.members.title') }}</div>

              <div v-if="!groupMembersMap[group.id]?.length" class="text-body-2 text-medium-emphasis mb-3">
                {{ t('researchGroup.admin.members.noMembers') }}
              </div>

              <v-table v-else density="compact" class="mb-3 members-table">
                <tbody>
                  <tr v-for="member in groupMembersMap[group.id]" :key="member.id">
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
                        @update:model-value="handleRoleChange(group.id, member.id, $event)"
                      />
                    </td>
                    <td style="width: 40px;">
                      <LIconBtn
                        icon="mdi-close"
                        :tooltip="t('researchGroup.admin.members.removeMember')"
                        size="x-small"
                        color="error"
                        @click="handleRemoveMember(group, member)"
                      />
                    </td>
                  </tr>
                </tbody>
              </v-table>

              <!-- Add Member Row -->
              <div class="d-flex align-center" style="gap: 8px;">
                <LUserSearch
                  v-model="newMemberUser[group.id]"
                  :placeholder="t('researchGroup.members.searchUser')"
                  :exclude-usernames="(groupMembersMap[group.id] || []).map(m => m.username)"
                  show-add-button
                  :add-button-text="t('researchGroup.admin.members.add')"
                  style="flex: 1; max-width: 400px;"
                  @add="handleAddMember(group.id, $event)"
                />
                <v-select
                  v-model="newMemberRole[group.id]"
                  :items="roleOptions"
                  item-title="label"
                  item-value="value"
                  variant="outlined"
                  density="compact"
                  hide-details
                  style="max-width: 140px;"
                />
              </div>
            </div>
          </div>
        </v-expand-transition>
      </v-card>
    </div>

    <!-- Create/Edit Dialog -->
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from '@/views/ConferenceManager/composables/useResearchGroups'

const { t } = useI18n()
const {
  fetchAllGroups, allGroups,
  createGroup, updateGroup, deleteGroup,
  fetchMembers, addMember, updateMemberRole, removeMember,
  fetchGroupRequests, resolveAccessRequest,
} = useResearchGroups()

const loading = ref(true)
const groups = ref([])
const showCreateDialog = ref(false)
const editingGroup = ref(null)
const saving = ref(false)
const formData = ref({ name: '', slug: '', description: '' })

// Expand state
const expandedGroups = reactive({})
const groupMembersMap = reactive({})
const groupRequests = reactive({})
const newMemberUser = reactive({})
const newMemberRole = reactive({})

const roleOptions = computed(() => [
  { label: t('researchGroup.members.roles.owner'), value: 'owner' },
  { label: t('researchGroup.members.roles.member'), value: 'member' },
  { label: t('researchGroup.members.roles.viewer'), value: 'viewer' },
])

async function loadGroups() {
  loading.value = true
  try {
    await fetchAllGroups()
    groups.value = allGroups.value
  } finally {
    loading.value = false
  }
}

async function toggleExpand(group) {
  const id = group.id
  if (expandedGroups[id]) {
    expandedGroups[id] = false
    return
  }
  expandedGroups[id] = true
  if (!newMemberRole[id]) newMemberRole[id] = 'member'
  await Promise.all([
    loadMembers(id),
    loadRequests(id),
  ])
}

async function loadMembers(groupId) {
  const members = await fetchMembers(groupId)
  groupMembersMap[groupId] = members
}

async function loadRequests(groupId) {
  const requests = await fetchGroupRequests(groupId)
  groupRequests[groupId] = requests
}

async function handleAddMember(groupId, user) {
  if (!user) return
  try {
    await addMember(groupId, user.id, newMemberRole[groupId] || 'member')
    await loadMembers(groupId)
    newMemberUser[groupId] = null
    await loadGroups()
  } catch (err) {
    console.error('Failed to add member:', err)
  }
}

async function handleRoleChange(groupId, memberId, newRole) {
  try {
    await updateMemberRole(groupId, memberId, newRole)
    await loadMembers(groupId)
  } catch (err) {
    console.error('Failed to update role:', err)
  }
}

async function handleRemoveMember(group, member) {
  if (!confirm(t('researchGroup.members.confirmRemove', { name: member.username }))) return
  try {
    await removeMember(group.id, member.id)
    await loadMembers(group.id)
    await loadGroups()
  } catch (err) {
    console.error('Failed to remove member:', err)
  }
}

async function handleResolveRequest(requestId, action, groupId) {
  try {
    await resolveAccessRequest(requestId, action)
    await Promise.all([
      loadRequests(groupId),
      loadMembers(groupId),
      loadGroups(),
    ])
  } catch (err) {
    console.error('Failed to resolve request:', err)
  }
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

async function confirmDelete(group) {
  if (!confirm(`Delete "${group.name}"? This will not delete conferences/papers, but they will lose their group assignment.`)) return
  try {
    await deleteGroup(group.id)
    await loadGroups()
  } catch (err) {
    console.error('Failed to delete group:', err)
  }
}

onMounted(loadGroups)
</script>

<style scoped>
.group-card, .dialog-card {
  border-radius: 16px 4px 16px 4px;
}

.members-table {
  background: transparent;
}

.members-table :deep(td) {
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
