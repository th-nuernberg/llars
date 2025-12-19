<template>
  <v-dialog
    v-model="dialogVisible"
    :fullscreen="isFullscreen"
    :max-width="isFullscreen ? undefined : '1000'"
    scrollable
    persistent
  >
    <v-card class="stats-dialog">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4">
        <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
        <div>
          <span class="text-h6">{{ scenario?.name || 'Statistiken' }}</span>
          <div class="text-caption text-medium-emphasis">Fake/Echt Szenario Statistiken</div>
        </div>
        <v-spacer />
        <LIconBtn
          :icon="isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
          :tooltip="isFullscreen ? 'Vollbild beenden' : 'Vollbild'"
          @click="toggleFullscreen"
        />
        <LIconBtn icon="mdi-close" tooltip="Schließen" @click="close" />
      </v-card-title>

      <v-divider />

      <!-- Loading State -->
      <v-card-text v-if="loading" class="pa-8 text-center">
        <v-progress-circular indeterminate color="primary" size="48" />
        <div class="text-body-1 mt-4 text-medium-emphasis">Statistiken werden geladen...</div>
      </v-card-text>

      <!-- Error State -->
      <v-card-text v-else-if="error" class="pa-8">
        <v-alert type="error" variant="tonal">
          {{ error }}
        </v-alert>
      </v-card-text>

      <!-- Stats Content -->
      <v-card-text v-else class="stats-content" :class="{ 'fullscreen-content': isFullscreen }">
        <!-- Overview Cards -->
        <div class="overview-grid mb-6">
          <!-- Krippendorff's Alpha Card -->
          <v-card variant="outlined" class="stat-card">
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="primary" class="mr-2">mdi-chart-bell-curve</v-icon>
                <span class="text-body-2 text-medium-emphasis">Krippendorff's Alpha</span>
              </div>
              <div class="d-flex align-center">
                <span class="text-h4 font-weight-bold" :class="alphaColorClass">
                  {{ formatAlpha(stats?.krippendorff_alpha) }}
                </span>
                <LTag :variant="alphaVariant" size="sm" class="ml-3">
                  {{ stats?.alpha_interpretation || 'N/A' }}
                </LTag>
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                Inter-Rater-Reliabilität
              </div>
            </v-card-text>
          </v-card>

          <!-- Accuracy Card -->
          <v-card variant="outlined" class="stat-card">
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="success" class="mr-2">mdi-target</v-icon>
                <span class="text-body-2 text-medium-emphasis">Gesamtgenauigkeit</span>
              </div>
              <div class="d-flex align-center">
                <span class="text-h4 font-weight-bold text-success">
                  {{ stats?.overall_accuracy != null ? stats.overall_accuracy + '%' : 'N/A' }}
                </span>
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                Korrekte Einschätzungen vs. Ground Truth
              </div>
            </v-card-text>
          </v-card>

          <!-- Progress Card -->
          <v-card variant="outlined" class="stat-card">
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="info" class="mr-2">mdi-progress-check</v-icon>
                <span class="text-body-2 text-medium-emphasis">Gesamtfortschritt</span>
              </div>
              <div class="d-flex align-center">
                <span class="text-h4 font-weight-bold text-info">
                  {{ overallProgress }}%
                </span>
              </div>
              <v-progress-linear
                :model-value="overallProgress"
                color="info"
                height="6"
                rounded
                class="mt-2"
              />
            </v-card-text>
          </v-card>

          <!-- Threads Card -->
          <v-card variant="outlined" class="stat-card">
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon color="secondary" class="mr-2">mdi-forum</v-icon>
                <span class="text-body-2 text-medium-emphasis">Konversationen</span>
              </div>
              <div class="text-h4 font-weight-bold">
                {{ stats?.total_threads || 0 }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                <span class="text-success">{{ stats?.ground_truth_stats?.real_count || 0 }} Echt</span>
                <span class="mx-1">•</span>
                <span class="text-error">{{ stats?.ground_truth_stats?.fake_count || 0 }} Fake</span>
              </div>
            </v-card-text>
          </v-card>
        </div>

        <!-- Vote Distribution -->
        <v-card variant="outlined" class="mb-6">
          <v-card-title class="text-subtitle-1 pa-4 pb-2">
            <v-icon class="mr-2" size="small">mdi-chart-pie</v-icon>
            Abstimmungsverteilung
          </v-card-title>
          <v-card-text class="pa-4 pt-0">
            <div class="vote-distribution">
              <div class="vote-bar">
                <div
                  class="vote-segment vote-real"
                  :style="{ width: votePercentage('real') + '%' }"
                >
                  <span v-if="votePercentage('real') > 10">{{ stats?.vote_distribution?.real || 0 }}</span>
                </div>
                <div
                  class="vote-segment vote-fake"
                  :style="{ width: votePercentage('fake') + '%' }"
                >
                  <span v-if="votePercentage('fake') > 10">{{ stats?.vote_distribution?.fake || 0 }}</span>
                </div>
                <div
                  class="vote-segment vote-pending"
                  :style="{ width: votePercentage('pending') + '%' }"
                >
                  <span v-if="votePercentage('pending') > 10">{{ stats?.vote_distribution?.pending || 0 }}</span>
                </div>
              </div>
              <div class="vote-legend mt-3">
                <div class="legend-item">
                  <span class="legend-dot bg-success"></span>
                  <span>Echt ({{ stats?.vote_distribution?.real || 0 }})</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot bg-error"></span>
                  <span>Fake ({{ stats?.vote_distribution?.fake || 0 }})</span>
                </div>
                <div class="legend-item">
                  <span class="legend-dot bg-grey"></span>
                  <span>Ausstehend ({{ stats?.vote_distribution?.pending || 0 }})</span>
                </div>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- User Stats Table -->
        <v-card variant="outlined">
          <v-card-title class="text-subtitle-1 pa-4 pb-2 d-flex align-center">
            <v-icon class="mr-2" size="small">mdi-account-group</v-icon>
            Benutzer-Fortschritt
            <v-spacer />
            <v-text-field
              v-model="userSearch"
              density="compact"
              variant="outlined"
              placeholder="Suchen..."
              prepend-inner-icon="mdi-magnify"
              hide-details
              class="search-field"
              clearable
            />
          </v-card-title>
          <v-card-text class="pa-0">
            <v-data-table
              :headers="userHeaders"
              :items="filteredUsers"
              :items-per-page="isFullscreen ? 15 : 5"
              class="user-stats-table"
              density="comfortable"
            >
              <!-- Username Column -->
              <template v-slot:item.username="{ item }">
                <div class="d-flex align-center">
                  <v-avatar size="32" :color="getAvatarColor(item.username)" class="mr-2">
                    <span class="text-caption text-white">{{ item.username.charAt(0).toUpperCase() }}</span>
                  </v-avatar>
                  <div>
                    <div class="font-weight-medium">{{ item.username }}</div>
                    <LTag :variant="item.role === 'rater' ? 'primary' : 'gray'" size="sm">
                      {{ item.role === 'rater' ? 'Bewerter' : 'Betrachter' }}
                    </LTag>
                  </div>
                </div>
              </template>

              <!-- Progress Column -->
              <template v-slot:item.progress="{ item }">
                <div class="progress-cell">
                  <v-progress-linear
                    :model-value="item.progress_percent"
                    :color="getProgressColor(item.progress_percent)"
                    height="8"
                    rounded
                    class="mb-1"
                  />
                  <div class="text-caption">
                    {{ item.voted_count }} / {{ item.total_threads }}
                    <span class="text-medium-emphasis">({{ item.progress_percent }}%)</span>
                  </div>
                </div>
              </template>

              <!-- Accuracy Column -->
              <template v-slot:item.accuracy="{ item }">
                <div v-if="item.accuracy_percent != null" class="d-flex align-center">
                  <v-icon
                    :color="item.accuracy_percent >= 70 ? 'success' : item.accuracy_percent >= 50 ? 'warning' : 'error'"
                    size="small"
                    class="mr-1"
                  >
                    {{ item.accuracy_percent >= 70 ? 'mdi-check-circle' : item.accuracy_percent >= 50 ? 'mdi-minus-circle' : 'mdi-close-circle' }}
                  </v-icon>
                  <span :class="getAccuracyClass(item.accuracy_percent)">
                    {{ item.accuracy_percent }}%
                  </span>
                  <span class="text-caption text-medium-emphasis ml-2">
                    ({{ item.correct_count }}/{{ item.correct_count + item.incorrect_count }})
                  </span>
                </div>
                <span v-else class="text-medium-emphasis">—</span>
              </template>

              <!-- Details Column -->
              <template v-slot:item.details="{ item }">
                <LIconBtn
                  icon="mdi-chevron-right"
                  size="small"
                  tooltip="Details anzeigen"
                  @click="showUserDetails(item)"
                />
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>

        <!-- User Detail Panel (Fullscreen only) -->
        <v-card v-if="isFullscreen && selectedUser" variant="outlined" class="mt-6">
          <v-card-title class="text-subtitle-1 pa-4 pb-2 d-flex align-center">
            <v-icon class="mr-2" size="small">mdi-account-details</v-icon>
            Details: {{ selectedUser.username }}
            <v-spacer />
            <LIconBtn icon="mdi-close" size="small" @click="selectedUser = null" />
          </v-card-title>
          <v-card-text class="pa-4">
            <v-row>
              <!-- Voted Threads -->
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon color="success" size="small" class="mr-1">mdi-check</v-icon>
                  Bewertet ({{ selectedUser.voted_threads?.length || 0 }})
                </div>
                <v-list density="compact" class="thread-list">
                  <v-list-item
                    v-for="thread in selectedUser.voted_threads"
                    :key="thread.thread_id"
                    class="thread-item"
                  >
                    <template v-slot:prepend>
                      <v-icon
                        :color="thread.is_correct ? 'success' : 'error'"
                        size="small"
                      >
                        {{ thread.is_correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
                      </v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ thread.subject || `Thread #${thread.thread_id}` }}
                    </v-list-item-title>
                    <v-list-item-subtitle>
                      Stimme: {{ thread.vote }}
                      <span v-if="thread.confidence"> ({{ thread.confidence }}% sicher)</span>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="!selectedUser.voted_threads?.length">
                    <v-list-item-title class="text-medium-emphasis">Keine Bewertungen</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-col>

              <!-- Pending Threads -->
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon color="warning" size="small" class="mr-1">mdi-clock-outline</v-icon>
                  Ausstehend ({{ selectedUser.pending_threads?.length || 0 }})
                </div>
                <v-list density="compact" class="thread-list">
                  <v-list-item
                    v-for="thread in selectedUser.pending_threads"
                    :key="thread.thread_id"
                    class="thread-item"
                  >
                    <template v-slot:prepend>
                      <v-icon color="grey" size="small">mdi-minus-circle-outline</v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ thread.subject || `Thread #${thread.thread_id}` }}
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item v-if="!selectedUser.pending_threads?.length">
                    <v-list-item-title class="text-medium-emphasis">Alle bewertet!</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>

      <!-- Footer -->
      <v-divider />
      <v-card-actions class="pa-4">
        <div class="text-caption text-medium-emphasis">
          <v-icon size="x-small" class="mr-1">mdi-information-outline</v-icon>
          Krippendorff's Alpha: ≥0.8 = Sehr gut, ≥0.667 = Akzeptabel, ≥0.4 = Moderat
        </div>
        <v-spacer />
        <LBtn variant="cancel" @click="close">Schließen</LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- User Details Dialog (Non-fullscreen) -->
  <v-dialog v-model="userDetailsDialog" max-width="600">
    <v-card v-if="selectedUser">
      <v-card-title class="d-flex align-center pa-4">
        <v-avatar size="40" :color="getAvatarColor(selectedUser.username)" class="mr-3">
          <span class="text-white">{{ selectedUser.username.charAt(0).toUpperCase() }}</span>
        </v-avatar>
        <div>
          <div class="text-h6">{{ selectedUser.username }}</div>
          <div class="text-caption text-medium-emphasis">
            {{ selectedUser.role === 'rater' ? 'Bewerter' : 'Betrachter' }}
          </div>
        </div>
        <v-spacer />
        <LIconBtn icon="mdi-close" @click="userDetailsDialog = false" />
      </v-card-title>
      <v-divider />
      <v-card-text class="pa-4">
        <!-- Stats Row -->
        <div class="d-flex gap-4 mb-4">
          <v-card variant="tonal" class="flex-1 pa-3">
            <div class="text-caption text-medium-emphasis">Fortschritt</div>
            <div class="text-h5 font-weight-bold">{{ selectedUser.progress_percent }}%</div>
          </v-card>
          <v-card variant="tonal" class="flex-1 pa-3">
            <div class="text-caption text-medium-emphasis">Genauigkeit</div>
            <div class="text-h5 font-weight-bold">{{ selectedUser.accuracy_percent ?? 'N/A' }}%</div>
          </v-card>
          <v-card variant="tonal" class="flex-1 pa-3">
            <div class="text-caption text-medium-emphasis">Bewertet</div>
            <div class="text-h5 font-weight-bold">{{ selectedUser.voted_count }}/{{ selectedUser.total_threads }}</div>
          </v-card>
        </div>

        <!-- Thread Lists -->
        <v-tabs v-model="detailTab" density="compact" class="mb-4">
          <v-tab value="voted">
            <v-icon size="small" class="mr-1">mdi-check</v-icon>
            Bewertet ({{ selectedUser.voted_threads?.length || 0 }})
          </v-tab>
          <v-tab value="pending">
            <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
            Ausstehend ({{ selectedUser.pending_threads?.length || 0 }})
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="detailTab">
          <v-tabs-window-item value="voted">
            <v-list density="compact" class="thread-list">
              <v-list-item
                v-for="thread in selectedUser.voted_threads"
                :key="thread.thread_id"
              >
                <template v-slot:prepend>
                  <v-icon
                    :color="thread.is_correct ? 'success' : 'error'"
                    size="small"
                  >
                    {{ thread.is_correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </v-icon>
                </template>
                <v-list-item-title>{{ thread.subject || `Thread #${thread.thread_id}` }}</v-list-item-title>
                <v-list-item-subtitle>
                  <LTag :variant="thread.vote === 'fake' ? 'danger' : 'success'" size="sm">
                    {{ thread.vote }}
                  </LTag>
                  <span v-if="thread.confidence" class="ml-2 text-medium-emphasis">
                    {{ thread.confidence }}% sicher
                  </span>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="!selectedUser.voted_threads?.length">
                <v-list-item-title class="text-medium-emphasis text-center">
                  Noch keine Bewertungen
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-tabs-window-item>

          <v-tabs-window-item value="pending">
            <v-list density="compact" class="thread-list">
              <v-list-item
                v-for="thread in selectedUser.pending_threads"
                :key="thread.thread_id"
              >
                <template v-slot:prepend>
                  <v-icon color="grey" size="small">mdi-minus-circle-outline</v-icon>
                </template>
                <v-list-item-title>{{ thread.subject || `Thread #${thread.thread_id}` }}</v-list-item-title>
              </v-list-item>
              <v-list-item v-if="!selectedUser.pending_threads?.length">
                <v-list-item-title class="text-medium-emphasis text-center">
                  Alle Threads bewertet!
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  scenario: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// State
const isFullscreen = ref(false)
const loading = ref(false)
const error = ref(null)
const stats = ref(null)
const userSearch = ref('')
const selectedUser = ref(null)
const userDetailsDialog = ref(false)
const detailTab = ref('voted')

// Computed
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const filteredUsers = computed(() => {
  if (!stats.value?.user_stats) return []
  if (!userSearch.value) return stats.value.user_stats
  const search = userSearch.value.toLowerCase()
  return stats.value.user_stats.filter(u =>
    u.username.toLowerCase().includes(search)
  )
})

const overallProgress = computed(() => {
  if (!stats.value?.user_stats?.length) return 0
  const total = stats.value.user_stats.reduce((sum, u) => sum + u.progress_percent, 0)
  return Math.round(total / stats.value.user_stats.length)
})

const alphaVariant = computed(() => {
  const alpha = stats.value?.krippendorff_alpha
  if (alpha == null) return 'gray'
  if (alpha >= 0.8) return 'success'
  if (alpha >= 0.667) return 'info'
  if (alpha >= 0.4) return 'warning'
  return 'danger'
})

const alphaColorClass = computed(() => {
  const alpha = stats.value?.krippendorff_alpha
  if (alpha == null) return 'text-medium-emphasis'
  if (alpha >= 0.8) return 'text-success'
  if (alpha >= 0.667) return 'text-info'
  if (alpha >= 0.4) return 'text-warning'
  return 'text-error'
})

const userHeaders = [
  { title: 'Benutzer', key: 'username', sortable: true },
  { title: 'Fortschritt', key: 'progress', sortable: false, width: '200px' },
  { title: 'Genauigkeit', key: 'accuracy', sortable: true },
  { title: '', key: 'details', sortable: false, width: '60px', align: 'end' }
]

// Methods
async function fetchStats() {
  if (!props.scenario?.scenario_id) return

  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/admin/scenario/${props.scenario.scenario_id}/user_stats`)
    stats.value = response.data
  } catch (err) {
    console.error('Error fetching stats:', err)
    error.value = err.response?.data?.message || 'Fehler beim Laden der Statistiken'
  } finally {
    loading.value = false
  }
}

function formatAlpha(alpha) {
  if (alpha == null) return 'N/A'
  return alpha.toFixed(3)
}

function votePercentage(type) {
  const dist = stats.value?.vote_distribution
  if (!dist) return 0
  const total = (dist.real || 0) + (dist.fake || 0) + (dist.pending || 0)
  if (total === 0) return 0
  return Math.round((dist[type] || 0) / total * 100)
}

function getProgressColor(percent) {
  if (percent >= 80) return 'success'
  if (percent >= 50) return 'info'
  if (percent >= 25) return 'warning'
  return 'error'
}

function getAccuracyClass(percent) {
  if (percent >= 70) return 'text-success font-weight-bold'
  if (percent >= 50) return 'text-warning font-weight-bold'
  return 'text-error font-weight-bold'
}

function getAvatarColor(username) {
  const colors = ['primary', 'secondary', 'info', 'success', 'warning', 'error']
  const index = username.charCodeAt(0) % colors.length
  return colors[index]
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function showUserDetails(user) {
  selectedUser.value = user
  if (!isFullscreen.value) {
    userDetailsDialog.value = true
  }
}

function close() {
  dialogVisible.value = false
  isFullscreen.value = false
  selectedUser.value = null
}

// Watch for dialog open
watch(() => props.modelValue, (newVal) => {
  if (newVal && props.scenario) {
    fetchStats()
  } else {
    stats.value = null
    error.value = null
    selectedUser.value = null
  }
})
</script>

<style scoped>
.stats-dialog {
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.stats-content {
  overflow-y: auto;
  padding: 24px;
}

.fullscreen-content {
  max-height: none;
  padding: 32px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card {
  border-radius: var(--llars-radius-sm, 8px 2px 8px 2px);
}

.vote-distribution {
  padding: 8px 0;
}

.vote-bar {
  display: flex;
  height: 32px;
  border-radius: 6px;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.vote-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  transition: width 0.3s ease;
  min-width: 0;
}

.vote-real {
  background-color: rgb(var(--v-theme-success));
}

.vote-fake {
  background-color: rgb(var(--v-theme-error));
}

.vote-pending {
  background-color: rgb(var(--v-theme-grey));
}

.vote-legend {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.search-field {
  max-width: 200px;
}

.progress-cell {
  min-width: 150px;
}

.thread-list {
  max-height: 300px;
  overflow-y: auto;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.thread-item {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.thread-item:last-child {
  border-bottom: none;
}

:deep(.user-stats-table) {
  background: transparent;
}

:deep(.user-stats-table tbody tr) {
  cursor: pointer;
  transition: background-color 0.2s;
}

:deep(.user-stats-table tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

.gap-4 {
  gap: 16px;
}

.flex-1 {
  flex: 1;
}
</style>
