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
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        :disabled="!hasPermission('feature:markdown_collab:edit')"
        @click="createDialog = true"
      >
        Workspace erstellen
      </v-btn>
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

        <v-card v-else variant="outlined">
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-folder-multiple-outline</v-icon>
            Workspaces
            <v-spacer />
            <v-btn variant="text" icon="mdi-refresh" @click="loadWorkspaces(true)" />
          </v-card-title>
          <v-divider />

          <v-card-text>
            <v-row v-if="workspaces.length > 0">
              <v-col
                v-for="ws in workspaces"
                :key="ws.id"
                cols="12"
                md="6"
                lg="4"
              >
                <v-card class="workspace-card" variant="tonal" @click="openWorkspace(ws.id)">
                  <v-card-title class="d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-folder</v-icon>
                    <span class="text-truncate">{{ ws.name }}</span>
                    <v-spacer />
                    <v-chip size="small" variant="tonal" color="info">
                      #{{ ws.id }}
                    </v-chip>
                  </v-card-title>
                  <v-card-subtitle class="text-medium-emphasis">
                    Besitzer: {{ ws.owner_username }}
                  </v-card-subtitle>
                  <v-card-text class="text-body-2">
                    <div class="d-flex align-center">
                      <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                      <span>Zuletzt geändert: {{ formatDate(ws.updated_at) }}</span>
                    </div>
                  </v-card-text>
                  <v-card-actions class="justify-end">
                    <v-btn variant="text" color="primary" @click.stop="openWorkspace(ws.id)">
                      Öffnen
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>

            <div v-else class="empty-state">
              <v-icon size="56" class="mb-3" color="grey">mdi-folder-open-outline</v-icon>
              <div class="text-subtitle-1 mb-1">Noch keine Workspaces</div>
              <div class="text-body-2 text-medium-emphasis mb-4">
                Erstelle deinen ersten Markdown Collab Workspace.
              </div>
              <v-btn
                color="primary"
                prepend-icon="mdi-plus"
                :disabled="!hasPermission('feature:markdown_collab:edit')"
                @click="createDialog = true"
              >
                Workspace erstellen
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="createDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-plus-circle</v-icon>
          Workspace erstellen
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" @click="createDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
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
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" @click="createDialog = false">Abbrechen</v-btn>
          <v-btn
            color="primary"
            :loading="creating"
            :disabled="!canCreate"
            @click="createWorkspace"
          >
            Erstellen
          </v-btn>
        </v-card-actions>
      </v-card>
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
.workspace-card {
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.workspace-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(var(--v-theme-primary), 0.12);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 16px;
  color: rgb(var(--v-theme-on-surface));
}
</style>
