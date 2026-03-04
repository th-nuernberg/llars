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

    <!-- Groups Table -->
    <v-card v-else variant="outlined" class="groups-card">
      <v-table>
        <thead>
          <tr>
            <th>{{ t('researchGroup.name') }}</th>
            <th>{{ t('researchGroup.slug') }}</th>
            <th>{{ t('researchGroup.members.title') }}</th>
            <th>{{ t('researchGroup.createdBy') }}</th>
            <th>{{ t('common.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="group in groups" :key="group.id">
            <td class="font-weight-medium">{{ group.name }}</td>
            <td class="text-medium-emphasis">{{ group.slug }}</td>
            <td>{{ group.member_count }}</td>
            <td>{{ group.created_by }}</td>
            <td>
              <div class="d-flex gap-1">
                <LIconBtn
                  icon="mdi-account-group"
                  tooltip="Members"
                  size="small"
                  @click="router.push({ name: 'ResearchGroupMembers', params: { groupId: group.id } })"
                />
                <LIconBtn
                  icon="mdi-pencil"
                  tooltip="Edit"
                  size="small"
                  @click="editGroup(group)"
                />
                <LIconBtn
                  icon="mdi-delete"
                  tooltip="Delete"
                  size="small"
                  color="error"
                  @click="confirmDelete(group)"
                />
              </div>
            </td>
          </tr>
          <tr v-if="!groups.length">
            <td colspan="5" class="text-center text-medium-emphasis pa-4">
              {{ t('researchGroup.admin.noGroups') }}
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from '@/views/ConferenceManager/composables/useResearchGroups'

const { t } = useI18n()
const router = useRouter()
const { fetchAllGroups, allGroups, createGroup, updateGroup, deleteGroup } = useResearchGroups()

const loading = ref(true)
const groups = ref([])
const showCreateDialog = ref(false)
const editingGroup = ref(null)
const saving = ref(false)
const formData = ref({ name: '', slug: '', description: '' })

async function loadGroups() {
  loading.value = true
  try {
    await fetchAllGroups()
    groups.value = allGroups.value
  } finally {
    loading.value = false
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
.groups-card, .dialog-card {
  border-radius: 16px 4px 16px 4px;
}
</style>
