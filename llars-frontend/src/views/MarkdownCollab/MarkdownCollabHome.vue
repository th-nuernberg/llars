<template>
  <v-container class="pa-6" fluid>
    <div class="d-flex align-center mb-6">
      <div>
        <div class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-language-markdown</v-icon>
          <h2 class="text-h5 mb-0">Markdown Collab</h2>
        </div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          Kollaborative Workspaces für Markdown-Dateien mit Live-Preview.
        </div>
      </div>
      <v-spacer />
      <LBtn
        variant="primary"
        prepend-icon="mdi-plus"
        :disabled="!hasPermission('feature:markdown_collab:edit')"
        @click="createDialog = true"
      >
        Workspace erstellen
      </LBtn>
    </div>

    <v-alert
      v-if="!hasPermission('feature:markdown_collab:view')"
      type="warning"
      variant="tonal"
      class="mb-6"
    >
      Dir fehlt die Berechtigung <code>feature:markdown_collab:view</code>.
    </v-alert>

    <v-row v-else>
      <v-col cols="12">
        <v-skeleton-loader v-if="isLoading('workspaces')" type="card@3" />

        <LCard v-else outlined>
          <template #header>
            <div class="d-flex align-center w-100">
              <v-icon class="mr-2">mdi-folder-multiple-outline</v-icon>
              <span class="text-h6">Workspaces</span>
              <v-spacer />
              <v-btn variant="text" icon="mdi-refresh" @click="loadWorkspaces(true)" />
            </div>
          </template>

          <v-row v-if="workspaces.length > 0">
            <v-col
              v-for="ws in workspaces"
              :key="ws.id"
              cols="12"
              md="6"
              lg="4"
            >
              <LCard
                :title="ws.name"
                icon="mdi-folder"
                color="#b0ca97"
                outlined
                clickable
                @click="openWorkspace(ws.id)"
              >
                <template #status>
                  <v-chip size="small" variant="tonal" color="info">
                    #{{ ws.id }}
                  </v-chip>
                </template>

                <div class="text-medium-emphasis mb-2">
                  Besitzer: {{ ws.owner_username }}
                </div>
                <div class="d-flex align-center text-caption">
                  <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                  <span>Zuletzt geändert: {{ formatDate(ws.updated_at) }}</span>
                </div>

                <template #actions>
                  <v-spacer />
                  <LBtn variant="text" size="small" @click.stop="openWorkspace(ws.id)">
                    Öffnen
                  </LBtn>
                </template>
              </LCard>
            </v-col>
          </v-row>

          <div v-else class="empty-state">
            <v-icon size="56" class="mb-3" color="grey">mdi-folder-open-outline</v-icon>
            <div class="text-subtitle-1 mb-1">Noch keine Workspaces</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              Erstelle deinen ersten Markdown Collab Workspace.
            </div>
            <LBtn
              variant="primary"
              prepend-icon="mdi-plus"
              :disabled="!hasPermission('feature:markdown_collab:edit')"
              @click="createDialog = true"
            >
              Workspace erstellen
            </LBtn>
          </div>
        </LCard>
      </v-col>
    </v-row>

    <v-dialog v-model="createDialog" max-width="520">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <v-icon class="mr-2">mdi-plus-circle</v-icon>
            <span class="text-h6">Workspace erstellen</span>
            <v-spacer />
            <v-btn icon="mdi-close" variant="text" @click="createDialog = false" />
          </div>
        </template>

        <v-alert v-if="createError" type="error" variant="tonal" class="mb-4">
          {{ createError }}
        </v-alert>
        <v-text-field
          v-model="newWorkspaceName"
          label="Name"
          placeholder="z. B. Dissertation Notes"
          prepend-inner-icon="mdi-folder"
          variant="outlined"
          density="comfortable"
        />
        <v-select
          v-model="newWorkspaceVisibility"
          :items="visibilityItems"
          label="Sichtbarkeit"
          prepend-inner-icon="mdi-eye-outline"
          variant="outlined"
          density="comfortable"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="createDialog = false">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            :loading="creating"
            :disabled="!canCreate"
            @click="createWorkspace"
          >
            Erstellen
          </LBtn>
        </template>
      </LCard>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const router = useRouter()
const { hasPermission, fetchPermissions } = usePermissions()
const { isLoading, withLoading } = useSkeletonLoading(['workspaces'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'

const workspaces = ref([])

const createDialog = ref(false)
const creating = ref(false)
const createError = ref('')
const newWorkspaceName = ref('')
const newWorkspaceVisibility = ref('private')

const visibilityItems = [
  { title: 'Privat', value: 'private' },
  { title: 'Team', value: 'team' },
  { title: 'Organisation', value: 'org' }
]

const canCreate = computed(() => {
  return hasPermission('feature:markdown_collab:edit') && newWorkspaceName.value.trim().length >= 2
})

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

async function loadWorkspaces(force = false) {
  await withLoading('workspaces', async () => {
    const res = await axios.get(`${API_BASE}/api/markdown-collab/workspaces`, {
      headers: authHeaders(),
      params: force ? { _ts: Date.now() } : undefined
    })
    workspaces.value = res.data.workspaces || []
  })
}

function openWorkspace(id) {
  router.push(`/MarkdownCollab/workspace/${id}`)
}

async function createWorkspace() {
  createError.value = ''
  creating.value = true
  try {
    const res = await axios.post(
      `${API_BASE}/api/markdown-collab/workspaces`,
      {
        name: newWorkspaceName.value.trim(),
        visibility: newWorkspaceVisibility.value
      },
      { headers: authHeaders() }
    )
    const ws = res.data.workspace
    createDialog.value = false
    newWorkspaceName.value = ''
    newWorkspaceVisibility.value = 'private'
    await loadWorkspaces(true)
    if (ws?.id) openWorkspace(ws.id)
  } catch (e) {
    createError.value = e?.response?.data?.error || e?.message || 'Workspace konnte nicht erstellt werden'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await fetchPermissions()
  if (hasPermission('feature:markdown_collab:view')) {
    await loadWorkspaces()
  }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 16px;
  color: rgb(var(--v-theme-on-surface));
}

.w-100 {
  width: 100%;
}
</style>
