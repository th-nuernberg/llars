<template>
  <v-card class="git-root" variant="outlined">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2" color="primary">mdi-source-branch</v-icon>
      Git Panel
      <v-spacer />
      <v-chip size="small" variant="tonal" :color="summary?.hasChanges ? 'warning' : 'info'">
        <template v-if="summary?.insertions !== undefined">
          +{{ summary?.insertions || 0 }} / -{{ summary?.deletions || 0 }}
        </template>
        <template v-else>
          {{ summary?.totalChangedLines || 0 }} Änderungen
        </template>
      </v-chip>
      <v-btn icon="mdi-refresh" variant="text" class="ml-1" title="History neu laden" @click="loadCommits(true)" />
      <v-btn
        icon
        variant="text"
        class="ml-1"
        :title="expanded ? 'Einklappen' : 'Ausklappen'"
        @click="expanded = !expanded"
      >
        <v-icon>{{ expanded ? 'mdi-chevron-down' : 'mdi-chevron-up' }}</v-icon>
      </v-btn>
    </v-card-title>

    <v-divider />

    <v-expand-transition>
      <div v-show="expanded">
        <v-card-text>
          <v-alert v-if="loadError" type="error" variant="tonal" class="mb-4">
            {{ loadError }}
          </v-alert>
          <v-row>
            <v-col cols="12" md="5">
              <div class="text-subtitle-2 mb-2">Uncommitted Changes</div>
              <div v-if="!summary?.hasChanges && (summary?.users || []).length === 0" class="text-body-2 text-medium-emphasis">
                Keine uncommitted Änderungen.
              </div>
              <div v-else class="mb-3">
                <div v-if="summary?.insertions !== undefined" class="text-body-2 mb-2">
                  <span class="text-success">+{{ summary?.insertions || 0 }} Zeichen eingefügt</span>
                  <span class="mx-2">|</span>
                  <span class="text-error">-{{ summary?.deletions || 0 }} Zeichen gelöscht</span>
                </div>
                <v-list v-if="(summary?.users || []).length > 0" density="compact" class="pa-0">
                  <v-list-item
                    v-for="u in summary.users"
                    :key="u.username"
                    class="px-0"
                  >
                    <template #prepend>
                      <span class="user-dot" :style="{ backgroundColor: u.color }" />
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ u.username }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ u.changedLines }} Zeilen
                    </v-list-item-subtitle>
                  </v-list-item>
                </v-list>
              </div>

              <v-divider class="my-4" />

              <div class="text-subtitle-2 mb-2">Commit</div>
              <v-alert v-if="commitError" type="error" variant="tonal" class="mb-3">
                {{ commitError }}
              </v-alert>
              <v-text-field
                v-model="commitMessage"
                label="Commit Message"
                variant="outlined"
                density="comfortable"
                :disabled="!canCommit"
                :hint="canCommit ? 'Pflichtfeld' : 'Du hast keine Edit-Rechte'"
                persistent-hint
              />
              <div class="d-flex justify-end">
                <v-btn
                  color="primary"
                  :loading="committing"
                  :disabled="!canSubmitCommit"
                  @click="submitCommit"
                >
                  Commit
                </v-btn>
              </div>
            </v-col>

            <v-col cols="12" md="7">
              <div class="text-subtitle-2 mb-2">History</div>
              <v-skeleton-loader v-if="isLoading('commits')" type="list-item@6" />
              <v-alert
                v-else-if="commits.length === 0"
                type="info"
                variant="tonal"
              >
                Noch keine Commits.
              </v-alert>
              <v-list v-else density="compact" class="history-list">
                <v-list-item v-for="c in commits" :key="c.id">
                  <v-list-item-title class="text-body-2">
                    {{ c.message }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-caption">
                    {{ c.author_username }} · {{ formatDate(c.created_at) }}
                  </v-list-item-subtitle>
                  <template #append>
                    <v-chip size="x-small" variant="tonal">#{{ c.id }}</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-card-text>
      </div>
    </v-expand-transition>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const props = defineProps({
  documentId: { type: Number, required: true },
  summary: { type: Object, default: () => ({ users: [], totalChangedLines: 0, hasChanges: false }) },
  canCommit: { type: Boolean, default: false },
  // Function to get current content from editor for commit snapshot
  getContent: { type: Function, default: null }
})

const emit = defineEmits(['committed'])

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const { isLoading, withLoading } = useSkeletonLoading(['commits'])

const expanded = ref(true)
const commits = ref([])

const commitMessage = ref('')
const committing = ref(false)
const commitError = ref('')
const loadError = ref('')

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

async function loadCommits(force = false) {
  await withLoading('commits', async () => {
    loadError.value = ''
    try {
      const res = await axios.get(`${API_BASE}/api/markdown-collab/documents/${props.documentId}/commits`, {
        headers: authHeaders(),
        params: force ? { _ts: Date.now() } : undefined
      })
      commits.value = res.data.commits || []
    } catch (e) {
      commits.value = []
      loadError.value = e?.response?.data?.error || e?.message || 'History konnte nicht geladen werden'
    }
  })
}

const canSubmitCommit = computed(() => {
  const msgOk = commitMessage.value.trim().length > 0
  // Use hasChanges from summary (based on actual diff comparison with baseline)
  const hasChanges = props.summary?.hasChanges === true || (props.summary?.totalChangedLines || 0) > 0
  return props.canCommit && msgOk && hasChanges
})

async function submitCommit() {
  if (!canSubmitCommit.value) return
  committing.value = true
  commitError.value = ''
  try {
    // Get current content for snapshot (required for character-level diff)
    const contentSnapshot = props.getContent ? props.getContent() : null

    await axios.post(
      `${API_BASE}/api/markdown-collab/documents/${props.documentId}/commit`,
      {
        message: commitMessage.value.trim(),
        diff_summary: props.summary || null,
        content_snapshot: contentSnapshot
      },
      { headers: authHeaders() }
    )
    commitMessage.value = ''
    await loadCommits(true)
    emit('committed')
  } catch (e) {
    commitError.value = e?.response?.data?.error || e?.message || 'Commit fehlgeschlagen'
  } finally {
    committing.value = false
  }
}

watch(
  () => props.documentId,
  async () => {
    commitMessage.value = ''
    commits.value = []
    await loadCommits(true)
  }
)

onMounted(async () => {
  await loadCommits()
})
</script>

<style scoped>
.git-root {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.user-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
  margin-right: 10px;
}

.history-list {
  max-height: 220px;
  overflow: auto;
}
</style>
