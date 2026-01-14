<template>
  <v-dialog
    v-model="dialogVisible"
    :fullscreen="isFullscreen"
    :max-width="isFullscreen ? undefined : '1100'"
    scrollable
  >
    <v-card class="stats-dialog">
      <!-- Header with gradient accent -->
      <div class="dialog-header">
        <div class="header-content">
          <div class="header-icon">
            <LIcon size="28">mdi-chart-box</LIcon>
          </div>
          <div class="header-text">
            <h2 class="header-title">{{ scenario?.name || 'Statistiken' }}</h2>
            <span class="header-subtitle">Fake/Echt Szenario Auswertung</span>
          </div>
        </div>
        <div class="header-actions">
          <LIconBtn
            :icon="isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
            :tooltip="isFullscreen ? 'Vollbild beenden' : 'Vollbild'"
            @click="toggleFullscreen"
          />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="close" />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">
          <v-progress-circular indeterminate color="primary" size="56" width="4" />
        </div>
        <p class="loading-text">Statistiken werden geladen...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <LIcon size="48" color="error">mdi-alert-circle-outline</LIcon>
        </div>
        <p class="error-text">{{ error }}</p>
        <LBtn variant="primary" prepend-icon="mdi-refresh" @click="fetchStats">
          Erneut versuchen
        </LBtn>
      </div>

      <!-- Stats Content -->
      <div v-else class="stats-content" :class="{ 'fullscreen-content': isFullscreen }">
        <!-- Key Metrics Row -->
        <div class="metrics-grid">
          <!-- Krippendorff's Alpha -->
          <div class="metric-card metric-alpha">
            <div class="metric-icon" :class="alphaIconClass">
              <LIcon>mdi-chart-bell-curve-cumulative</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Krippendorff's Alpha</span>
              <div class="metric-value-row">
                <span class="metric-value" :class="alphaColorClass">
                  {{ formatAlpha(stats?.krippendorff_alpha) }}
                </span>
                <LTag :variant="alphaVariant" size="sm">
                  {{ stats?.alpha_interpretation || 'N/A' }}
                </LTag>
              </div>
              <span class="metric-hint">Inter-Rater-Reliabilität</span>
            </div>
          </div>

          <!-- Accuracy -->
          <div class="metric-card metric-accuracy">
            <div class="metric-icon icon-success">
              <LIcon>mdi-bullseye-arrow</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Gesamtgenauigkeit</span>
              <div class="metric-value-row">
                <span class="metric-value text-success">
                  {{ stats?.overall_accuracy != null ? stats.overall_accuracy + '%' : 'N/A' }}
                </span>
              </div>
              <span class="metric-hint">vs. Ground Truth</span>
            </div>
          </div>

          <!-- Progress -->
          <div class="metric-card metric-progress">
            <div class="metric-icon icon-accent">
              <LIcon>mdi-percent-circle</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Fortschritt</span>
              <div class="metric-value-row">
                <span class="metric-value text-accent">{{ overallProgress }}%</span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar-track">
                  <div class="progress-bar-fill" :style="{ width: overallProgress + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Threads -->
          <div class="metric-card metric-threads">
            <div class="metric-icon icon-secondary">
              <LIcon>mdi-message-text-outline</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Konversationen</span>
              <div class="metric-value-row">
                <span class="metric-value">{{ stats?.total_threads || 0 }}</span>
              </div>
              <div class="thread-breakdown">
                <span class="breakdown-item real">
                  <span class="breakdown-dot"></span>
                  {{ stats?.ground_truth_stats?.real_count || 0 }} Echt
                </span>
                <span class="breakdown-item fake">
                  <span class="breakdown-dot"></span>
                  {{ stats?.ground_truth_stats?.fake_count || 0 }} Fake
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Vote Distribution Section -->
        <div class="section-card">
          <div class="section-header">
            <LIcon class="section-icon">mdi-chart-donut</LIcon>
            <h3 class="section-title">Abstimmungsverteilung</h3>
          </div>
          <div class="vote-distribution">
            <div class="vote-bar">
              <div
                class="vote-segment vote-real"
                :style="{ width: votePercentage('real') + '%' }"
                :class="{ 'has-label': votePercentage('real') > 12 }"
              >
                <span class="segment-label" v-if="votePercentage('real') > 12">
                  {{ stats?.vote_distribution?.real || 0 }}
                </span>
              </div>
              <div
                class="vote-segment vote-fake"
                :style="{ width: votePercentage('fake') + '%' }"
                :class="{ 'has-label': votePercentage('fake') > 12 }"
              >
                <span class="segment-label" v-if="votePercentage('fake') > 12">
                  {{ stats?.vote_distribution?.fake || 0 }}
                </span>
              </div>
              <div
                class="vote-segment vote-pending"
                :style="{ width: votePercentage('pending') + '%' }"
                :class="{ 'has-label': votePercentage('pending') > 12 }"
              >
                <span class="segment-label" v-if="votePercentage('pending') > 12">
                  {{ stats?.vote_distribution?.pending || 0 }}
                </span>
              </div>
            </div>
            <div class="vote-legend">
              <div class="legend-item">
                <span class="legend-dot real"></span>
                <span class="legend-text">Echt</span>
                <span class="legend-count">{{ stats?.vote_distribution?.real || 0 }}</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot fake"></span>
                <span class="legend-text">Fake</span>
                <span class="legend-count">{{ stats?.vote_distribution?.fake || 0 }}</span>
              </div>
              <div class="legend-item">
                <span class="legend-dot pending"></span>
                <span class="legend-text">Ausstehend</span>
                <span class="legend-count">{{ stats?.vote_distribution?.pending || 0 }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- User Stats Section -->
        <div class="section-card users-section">
          <div class="section-header">
            <LIcon class="section-icon">mdi-account-group</LIcon>
            <h3 class="section-title">Benutzer-Fortschritt</h3>
            <div class="section-actions">
              <v-text-field
                v-model="userSearch"
                density="compact"
                variant="outlined"
                placeholder="Benutzer suchen..."
                prepend-inner-icon="mdi-magnify"
                hide-details
                class="search-input"
                clearable
              />
            </div>
          </div>

          <div class="users-table-wrapper">
            <table class="users-table">
              <thead>
                <tr>
                  <th class="th-user">Benutzer</th>
                  <th class="th-progress">Fortschritt</th>
                  <th class="th-accuracy">Genauigkeit</th>
                  <th class="th-action"></th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="user in filteredUsers"
                  :key="user.user_id"
                  class="user-row"
                  @click="showUserDetails(user)"
                >
                  <td class="td-user">
                    <div class="user-info">
                      <div class="user-avatar" :style="{ backgroundColor: getAvatarColor(user.username) }">
                        <v-icon v-if="user.is_llm" size="16">mdi-robot-outline</v-icon>
                        <span v-else>{{ user.username.charAt(0).toUpperCase() }}</span>
                      </div>
                      <div class="user-details">
                        <span class="user-name">{{ user.username }}</span>
                        <div class="user-tags">
                          <LTag :variant="user.role === 'rater' ? 'primary' : 'gray'" size="sm">
                            {{ user.role === 'rater' ? 'Viewer' : 'Evaluator' }}
                          </LTag>
                          <LTag v-if="user.is_llm" variant="info" size="sm">LLM</LTag>
                        </div>
                      </div>
                    </div>
                  </td>
                  <td class="td-progress">
                    <div class="progress-cell">
                      <div class="mini-progress-bar">
                        <div
                          class="mini-progress-fill"
                          :style="{ width: user.progress_percent + '%' }"
                          :class="getProgressClass(user.progress_percent)"
                        ></div>
                      </div>
                      <span class="progress-text">
                        {{ user.voted_count }}/{{ user.total_threads }}
                        <span class="progress-percent">({{ user.progress_percent }}%)</span>
                      </span>
                    </div>
                  </td>
                  <td class="td-accuracy">
                    <div v-if="user.accuracy_percent != null" class="accuracy-cell">
                      <LIcon :color="getAccuracyColor(user.accuracy_percent)" size="18">
                        {{ getAccuracyIcon(user.accuracy_percent) }}
                      </LIcon>
                      <span class="accuracy-value" :class="getAccuracyClass(user.accuracy_percent)">
                        {{ user.accuracy_percent }}%
                      </span>
                      <span class="accuracy-detail">
                        ({{ user.correct_count }}/{{ user.correct_count + user.incorrect_count }})
                      </span>
                    </div>
                    <span v-else class="no-data">—</span>
                  </td>
                  <td class="td-action">
                    <LIconBtn
                      icon="mdi-chevron-right"
                      size="small"
                      tooltip="Details"
                    />
                  </td>
                </tr>
                <tr v-if="!filteredUsers.length">
                  <td colspan="4" class="empty-row">
                    <LIcon class="empty-icon">mdi-account-search</LIcon>
                    <span>Keine Benutzer gefunden</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- User Detail Panel (Fullscreen) -->
        <div v-if="isFullscreen && selectedUser" class="section-card user-detail-panel">
          <div class="section-header">
            <div class="user-avatar large" :style="{ backgroundColor: getAvatarColor(selectedUser.username) }">
              <v-icon v-if="selectedUser.is_llm" size="20">mdi-robot-outline</v-icon>
              <span v-else>{{ selectedUser.username.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="detail-user-info">
              <h3 class="section-title">{{ selectedUser.username }}</h3>
              <div class="user-tags">
                <LTag :variant="selectedUser.role === 'rater' ? 'primary' : 'gray'" size="sm">
                  {{ selectedUser.role === 'rater' ? 'Viewer' : 'Evaluator' }}
                </LTag>
                <LTag v-if="selectedUser.is_llm" variant="info" size="sm">LLM</LTag>
              </div>
            </div>
            <div class="section-actions">
              <LIconBtn icon="mdi-close" @click="selectedUser = null" />
            </div>
          </div>

          <div class="detail-stats-row">
            <div class="detail-stat">
              <span class="detail-stat-value">{{ selectedUser.progress_percent }}%</span>
              <span class="detail-stat-label">Fortschritt</span>
            </div>
            <div class="detail-stat">
              <span class="detail-stat-value">{{ selectedUser.accuracy_percent ?? 'N/A' }}%</span>
              <span class="detail-stat-label">Genauigkeit</span>
            </div>
            <div class="detail-stat">
              <span class="detail-stat-value">{{ selectedUser.voted_count }}/{{ selectedUser.total_threads }}</span>
              <span class="detail-stat-label">Bewertet</span>
            </div>
          </div>

          <!-- Fake/Real Breakdown -->
          <div v-if="selectedUser.correct_count > 0 || selectedUser.incorrect_count > 0" class="vote-breakdown-row">
            <div class="breakdown-card fake">
              <div class="breakdown-header">
                <LIcon size="18" color="#c87a6a">mdi-close-circle</LIcon>
                <span class="breakdown-title">Fake erkannt</span>
              </div>
              <div class="breakdown-stats">
                <span class="breakdown-correct">{{ selectedUser.fake_correct || 0 }} richtig</span>
                <span class="breakdown-separator">/</span>
                <span class="breakdown-incorrect">{{ selectedUser.fake_incorrect || 0 }} falsch</span>
              </div>
              <div class="breakdown-bar">
                <div
                  class="breakdown-bar-fill"
                  :style="{ width: getFakeAccuracy(selectedUser) + '%' }"
                ></div>
              </div>
            </div>
            <div class="breakdown-card real">
              <div class="breakdown-header">
                <LIcon size="18" color="#4a9f7e">mdi-check-circle</LIcon>
                <span class="breakdown-title">Echt erkannt</span>
              </div>
              <div class="breakdown-stats">
                <span class="breakdown-correct">{{ selectedUser.real_correct || 0 }} richtig</span>
                <span class="breakdown-separator">/</span>
                <span class="breakdown-incorrect">{{ selectedUser.real_incorrect || 0 }} falsch</span>
              </div>
              <div class="breakdown-bar real">
                <div
                  class="breakdown-bar-fill"
                  :style="{ width: getRealAccuracy(selectedUser) + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <div class="detail-threads-grid">
            <div class="thread-column">
              <div class="thread-column-header voted">
                <LIcon size="18">mdi-check-circle</LIcon>
                <span>Bewertet ({{ selectedUser.voted_threads?.length || 0 }})</span>
              </div>
              <div class="thread-list">
                <div
                  v-for="thread in selectedUser.voted_threads"
                  :key="thread.thread_id"
                  class="thread-item"
                >
                  <LIcon :color="thread.is_correct ? 'success' : 'error'" size="16">
                    {{ thread.is_correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </LIcon>
                  <div class="thread-info">
                    <span class="thread-subject">{{ thread.subject || `Thread #${thread.thread_id}` }}</span>
                    <div class="thread-meta">
                      <LTag :variant="thread.vote === 'fake' ? 'danger' : 'success'" size="sm">
                        {{ thread.vote }}
                      </LTag>
                      <span v-if="thread.confidence" class="confidence">{{ thread.confidence }}%</span>
                    </div>
                  </div>
                </div>
                <div v-if="!selectedUser.voted_threads?.length" class="empty-threads">
                  Keine Bewertungen
                </div>
              </div>
            </div>

            <div class="thread-column">
              <div class="thread-column-header pending">
                <LIcon size="18">mdi-clock-outline</LIcon>
                <span>Ausstehend ({{ selectedUser.pending_threads?.length || 0 }})</span>
              </div>
              <div class="thread-list">
                <div
                  v-for="thread in selectedUser.pending_threads"
                  :key="thread.thread_id"
                  class="thread-item pending"
                >
                  <LIcon color="grey" size="16">mdi-minus-circle-outline</LIcon>
                  <div class="thread-info">
                    <span class="thread-subject">{{ thread.subject || `Thread #${thread.thread_id}` }}</span>
                  </div>
                </div>
                <div v-if="!selectedUser.pending_threads?.length" class="empty-threads success">
                  Alle bewertet!
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dialog-footer">
        <div class="footer-info">
          <LIcon size="14" class="mr-1">mdi-information-outline</LIcon>
          <span>Alpha: ≥0.8 Sehr gut • ≥0.667 Akzeptabel • ≥0.4 Moderat</span>
        </div>
        <LBtn variant="cancel" @click="close">Schließen</LBtn>
      </div>
    </v-card>
  </v-dialog>

  <!-- User Details Dialog (Non-fullscreen) -->
  <v-dialog v-model="userDetailsDialog" max-width="650">
    <v-card v-if="selectedUser" class="user-detail-dialog">
      <div class="detail-dialog-header">
        <div class="user-avatar large" :style="{ backgroundColor: getAvatarColor(selectedUser.username) }">
          <v-icon v-if="selectedUser.is_llm" size="20">mdi-robot-outline</v-icon>
          <span v-else>{{ selectedUser.username.charAt(0).toUpperCase() }}</span>
        </div>
        <div class="detail-user-info">
          <h3>{{ selectedUser.username }}</h3>
          <div class="user-tags">
            <LTag :variant="selectedUser.role === 'rater' ? 'primary' : 'gray'" size="sm">
              {{ selectedUser.role === 'rater' ? 'Viewer' : 'Evaluator' }}
            </LTag>
            <LTag v-if="selectedUser.is_llm" variant="info" size="sm">LLM</LTag>
          </div>
        </div>
        <LIconBtn icon="mdi-close" @click="userDetailsDialog = false" />
      </div>

      <div class="detail-dialog-content">
        <div class="detail-stats-row compact">
          <div class="detail-stat">
            <span class="detail-stat-value">{{ selectedUser.progress_percent }}%</span>
            <span class="detail-stat-label">Fortschritt</span>
          </div>
          <div class="detail-stat">
            <span class="detail-stat-value">{{ selectedUser.accuracy_percent ?? 'N/A' }}%</span>
            <span class="detail-stat-label">Genauigkeit</span>
          </div>
          <div class="detail-stat">
            <span class="detail-stat-value">{{ selectedUser.voted_count }}/{{ selectedUser.total_threads }}</span>
            <span class="detail-stat-label">Bewertet</span>
          </div>
        </div>

        <!-- Fake/Real Breakdown (Non-fullscreen) -->
        <div v-if="selectedUser.correct_count > 0 || selectedUser.incorrect_count > 0" class="vote-breakdown-row compact">
          <div class="breakdown-card fake">
            <div class="breakdown-header">
              <LIcon size="16" color="#c87a6a">mdi-close-circle</LIcon>
              <span class="breakdown-title">Fake erkannt</span>
            </div>
            <div class="breakdown-stats">
              <span class="breakdown-correct">{{ selectedUser.fake_correct || 0 }} richtig</span>
              <span class="breakdown-separator">/</span>
              <span class="breakdown-incorrect">{{ selectedUser.fake_incorrect || 0 }} falsch</span>
            </div>
            <div class="breakdown-bar">
              <div
                class="breakdown-bar-fill"
                :style="{ width: getFakeAccuracy(selectedUser) + '%' }"
              ></div>
            </div>
          </div>
          <div class="breakdown-card real">
            <div class="breakdown-header">
              <LIcon size="16" color="#4a9f7e">mdi-check-circle</LIcon>
              <span class="breakdown-title">Echt erkannt</span>
            </div>
            <div class="breakdown-stats">
              <span class="breakdown-correct">{{ selectedUser.real_correct || 0 }} richtig</span>
              <span class="breakdown-separator">/</span>
              <span class="breakdown-incorrect">{{ selectedUser.real_incorrect || 0 }} falsch</span>
            </div>
            <div class="breakdown-bar real">
              <div
                class="breakdown-bar-fill"
                :style="{ width: getRealAccuracy(selectedUser) + '%' }"
              ></div>
            </div>
          </div>
        </div>

        <LTabs
          v-model="detailTab"
          :tabs="[
            { value: 'voted', label: `Bewertet (${selectedUser.voted_threads?.length || 0})`, icon: 'mdi-check-circle' },
            { value: 'pending', label: `Ausstehend (${selectedUser.pending_threads?.length || 0})`, icon: 'mdi-clock-outline' }
          ]"
          class="detail-tabs"
        />

        <div class="detail-thread-list">
          <template v-if="detailTab === 'voted'">
            <div
              v-for="thread in selectedUser.voted_threads"
              :key="thread.thread_id"
              class="thread-item"
            >
              <LIcon :color="thread.is_correct ? 'success' : 'error'" size="18">
                {{ thread.is_correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
              </LIcon>
              <div class="thread-info">
                <span class="thread-subject">{{ thread.subject || `Thread #${thread.thread_id}` }}</span>
                <div class="thread-meta">
                  <LTag :variant="thread.vote === 'fake' ? 'danger' : 'success'" size="sm">
                    {{ thread.vote }}
                  </LTag>
                  <span v-if="thread.confidence" class="confidence">{{ thread.confidence }}% sicher</span>
                </div>
              </div>
            </div>
            <div v-if="!selectedUser.voted_threads?.length" class="empty-threads">
              Noch keine Bewertungen
            </div>
          </template>
          <template v-else>
            <div
              v-for="thread in selectedUser.pending_threads"
              :key="thread.thread_id"
              class="thread-item pending"
            >
              <LIcon color="grey" size="18">mdi-minus-circle-outline</LIcon>
              <div class="thread-info">
                <span class="thread-subject">{{ thread.subject || `Thread #${thread.thread_id}` }}</span>
              </div>
            </div>
            <div v-if="!selectedUser.pending_threads?.length" class="empty-threads success">
              Alle Threads bewertet!
            </div>
          </template>
        </div>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'
import { logI18n } from '@/utils/logI18n'

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
const subscribedScenarioId = ref(null)

let socket = null
let socketListenersAttached = false

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
  if (alpha == null) return 'text-muted'
  if (alpha >= 0.8) return 'text-success'
  if (alpha >= 0.667) return 'text-accent'
  if (alpha >= 0.4) return 'text-warning'
  return 'text-danger'
})

const alphaIconClass = computed(() => {
  const alpha = stats.value?.krippendorff_alpha
  if (alpha == null) return 'icon-muted'
  if (alpha >= 0.8) return 'icon-success'
  if (alpha >= 0.667) return 'icon-accent'
  if (alpha >= 0.4) return 'icon-warning'
  return 'icon-danger'
})

// Methods
async function fetchStats() {
  if (!props.scenario?.scenario_id) return

  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/admin/scenario/${props.scenario.scenario_id}/user_stats`)
    stats.value = response.data
  } catch (err) {
    logI18n('error', 'logs.admin.stats.fetchStatsFailed', err)
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

function getProgressClass(percent) {
  if (percent >= 80) return 'progress-success'
  if (percent >= 50) return 'progress-accent'
  if (percent >= 25) return 'progress-warning'
  return 'progress-danger'
}

function getAccuracyColor(percent) {
  if (percent >= 70) return 'success'
  if (percent >= 50) return 'warning'
  return 'error'
}

function getAccuracyIcon(percent) {
  if (percent >= 70) return 'mdi-check-circle'
  if (percent >= 50) return 'mdi-minus-circle'
  return 'mdi-close-circle'
}

function getAccuracyClass(percent) {
  if (percent >= 70) return 'accuracy-good'
  if (percent >= 50) return 'accuracy-moderate'
  return 'accuracy-poor'
}

function getAvatarColor(username) {
  const colors = ['#b0ca97', '#D1BC8A', '#88c4c8', '#98d4bb', '#a8c5e2', '#e8c87a']
  const index = username.charCodeAt(0) % colors.length
  return colors[index]
}

function getFakeAccuracy(user) {
  const total = (user.fake_correct || 0) + (user.fake_incorrect || 0)
  if (total === 0) return 0
  return Math.round((user.fake_correct || 0) / total * 100)
}

function getRealAccuracy(user) {
  const total = (user.real_correct || 0) + (user.real_incorrect || 0)
  if (total === 0) return 0
  return Math.round((user.real_correct || 0) / total * 100)
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

function handleSocketStats(payload) {
  if (!payload || payload.kind !== 'authenticity') return
  if (!props.scenario?.scenario_id || payload.scenario_id !== props.scenario.scenario_id) return
  stats.value = payload.stats
  error.value = null
  loading.value = false
}

function subscribeScenario(scenarioId) {
  if (!socket || !scenarioId) return
  if (subscribedScenarioId.value === scenarioId) return

  if (subscribedScenarioId.value) {
    socket.emit('scenario:unsubscribe', { scenario_id: subscribedScenarioId.value })
  }

  subscribedScenarioId.value = scenarioId
  socket.emit('scenario:subscribe', { scenario_id: scenarioId })
}

function setupSocket() {
  socket = getSocket()
  if (!socket) return

  if (socketListenersAttached) {
    if (socket.connected && props.modelValue && props.scenario?.scenario_id) {
      subscribeScenario(props.scenario.scenario_id)
    }
    return
  }

  socket.on('scenario:stats', handleSocketStats)
  socket.on('scenario:stats_updated', handleSocketStats)
  socket.on('connect', handleSocketConnect)
  socketListenersAttached = true

  if (socket.connected && props.modelValue && props.scenario?.scenario_id) {
    subscribeScenario(props.scenario.scenario_id)
  }
}

function cleanupSocket() {
  if (!socket) return
  socket.off('scenario:stats', handleSocketStats)
  socket.off('scenario:stats_updated', handleSocketStats)
  socket.off('connect', handleSocketConnect)
  if (subscribedScenarioId.value) {
    socket.emit('scenario:unsubscribe', { scenario_id: subscribedScenarioId.value })
  }
  subscribedScenarioId.value = null
  socketListenersAttached = false
}

function handleSocketConnect() {
  if (props.modelValue && props.scenario?.scenario_id) {
    subscribeScenario(props.scenario.scenario_id)
  }
}

watch(() => [props.modelValue, props.scenario?.scenario_id], ([isOpen, scenarioId], [wasOpen, prevScenarioId]) => {
  if (!isOpen) {
    cleanupSocket()
    stats.value = null
    error.value = null
    selectedUser.value = null
    return
  }

  setupSocket()

  if (scenarioId) {
    fetchStats()
    subscribeScenario(scenarioId)
  }
})

onUnmounted(() => {
  cleanupSocket()
})
</script>

<style scoped>
/* LLARS Design Variables */
.stats-dialog {
  --llars-primary: #b0ca97;
  --llars-secondary: #D1BC8A;
  --llars-accent: #88c4c8;
  --llars-success: #98d4bb;
  --llars-warning: #e8c87a;
  --llars-danger: #e8a087;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
  border-radius: var(--llars-radius) !important;
}

/* Header */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions :deep(.v-btn) {
  color: white !important;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
}

.loading-text,
.error-text {
  color: rgba(0, 0, 0, 0.6);
  font-size: 1rem;
}

.error-icon {
  width: 80px;
  height: 80px;
  background: rgba(232, 160, 135, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Content */
.stats-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.fullscreen-content {
  padding: 32px;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.metric-card {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--llars-radius-sm);
  padding: 20px;
  display: flex;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon.icon-success { background: rgba(152, 212, 187, 0.2); color: #4a9f7e; }
.metric-icon.icon-accent { background: rgba(136, 196, 200, 0.2); color: #5a9a9e; }
.metric-icon.icon-secondary { background: rgba(209, 188, 138, 0.2); color: #9a8a5a; }
.metric-icon.icon-warning { background: rgba(232, 200, 122, 0.2); color: #9a8a4a; }
.metric-icon.icon-danger { background: rgba(232, 160, 135, 0.2); color: #c87a6a; }
.metric-icon.icon-muted { background: rgba(0, 0, 0, 0.05); color: #999; }

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.metric-label {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
}

.metric-value-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}

.metric-value.text-success { color: #4a9f7e; }
.metric-value.text-accent { color: #5a9a9e; }
.metric-value.text-warning { color: #c9a84a; }
.metric-value.text-danger { color: #c87a6a; }
.metric-value.text-muted { color: #999; }

.metric-hint {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
}

.progress-bar-container {
  margin-top: 4px;
}

.progress-bar-track {
  height: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--llars-accent);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.thread-breakdown {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.6);
}

.breakdown-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.breakdown-item.real .breakdown-dot { background: var(--llars-success); }
.breakdown-item.fake .breakdown-dot { background: var(--llars-danger); }

/* Section Cards */
.section-card {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--llars-radius-sm);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.section-icon {
  color: var(--llars-primary);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.search-input {
  max-width: 200px;
}

.search-input :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

/* Vote Distribution */
.vote-distribution {
  padding: 20px;
}

.vote-bar {
  display: flex;
  height: 40px;
  border-radius: var(--llars-radius-sm);
  overflow: hidden;
  background: rgba(0, 0, 0, 0.04);
}

.vote-segment {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: width 0.5s ease;
  min-width: 0;
}

.vote-segment.vote-real { background: var(--llars-success); }
.vote-segment.vote-fake { background: var(--llars-danger); }
.vote-segment.vote-pending { background: #bbb; }

.segment-label {
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.vote-legend {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  flex-wrap: wrap;
  max-height: 120px;
  overflow-y: auto;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 4px 2px 4px 2px;
}

.legend-dot.real { background: var(--llars-success); }
.legend-dot.fake { background: var(--llars-danger); }
.legend-dot.pending { background: #bbb; }

.legend-text {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.7);
}

.legend-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.9);
}

/* Users Table */
.users-table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 400px;
  position: relative;
  /* Subtle shadow to indicate more content below */
  background:
    linear-gradient(white 30%, transparent),
    linear-gradient(transparent, white 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0,0,0,.12), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0,0,0,.12), transparent) 0 100%;
  background-repeat: no-repeat;
  background-size: 100% 40px, 100% 40px, 100% 12px, 100% 12px;
  background-attachment: local, local, scroll, scroll;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.users-table th {
  text-align: left;
  padding: 12px 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0, 0, 0, 0.5);
  background: #f9f9f9;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.users-table td {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.user-row {
  cursor: pointer;
  transition: background-color 0.15s;
}

.user-row:hover {
  background: rgba(176, 202, 151, 0.08);
}

.user-row:last-child td {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-avatar.large {
  width: 48px;
  height: 48px;
  font-size: 1.125rem;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.user-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 140px;
}

.mini-progress-bar {
  height: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.mini-progress-fill.progress-success { background: var(--llars-success); }
.mini-progress-fill.progress-accent { background: var(--llars-accent); }
.mini-progress-fill.progress-warning { background: var(--llars-warning); }
.mini-progress-fill.progress-danger { background: var(--llars-danger); }

.progress-text {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.7);
}

.progress-percent {
  color: rgba(0, 0, 0, 0.5);
}

.accuracy-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.accuracy-value {
  font-weight: 600;
}

.accuracy-value.accuracy-good { color: #4a9f7e; }
.accuracy-value.accuracy-moderate { color: #c9a84a; }
.accuracy-value.accuracy-poor { color: #c87a6a; }

.accuracy-detail {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.5);
}

.no-data {
  color: rgba(0, 0, 0, 0.3);
}

.empty-row {
  text-align: center;
  padding: 40px 20px !important;
  color: rgba(0, 0, 0, 0.5);
}

.empty-icon {
  margin-right: 8px;
  opacity: 0.5;
}

/* User Detail Panel */
.user-detail-panel {
  margin-top: 24px;
}

.detail-user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.detail-stats-row {
  display: flex;
  gap: 24px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.02);
}

.detail-stats-row.compact {
  padding: 16px 20px;
  margin-bottom: 16px;
  border-radius: var(--llars-radius-sm);
}

.detail-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.87);
}

.detail-stat-label {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-threads-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
}

.thread-column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--llars-radius-sm);
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 12px;
}

.thread-column-header.voted {
  background: rgba(152, 212, 187, 0.15);
  color: #4a9f7e;
}

.thread-column-header.pending {
  background: rgba(232, 200, 122, 0.15);
  color: #9a8a4a;
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 350px;
  overflow-y: auto;
}

.thread-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 6px;
  transition: background 0.15s;
}

.thread-item:hover {
  background: rgba(0, 0, 0, 0.04);
}

.thread-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.thread-subject {
  font-size: 0.875rem;
  color: rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.thread-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
}

.empty-threads {
  padding: 24px;
  text-align: center;
  color: rgba(0, 0, 0, 0.4);
  font-size: 0.875rem;
}

.empty-threads.success {
  color: #4a9f7e;
}

/* Vote Breakdown Row */
.vote-breakdown-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 0 20px 20px;
}

.vote-breakdown-row.compact {
  padding: 0;
  margin-bottom: 16px;
}

.breakdown-card {
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--llars-radius-sm);
  padding: 14px 16px;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.breakdown-card.fake {
  border-left: 3px solid var(--llars-danger);
}

.breakdown-card.real {
  border-left: 3px solid var(--llars-success);
}

.breakdown-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.breakdown-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
}

.breakdown-stats {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.breakdown-correct {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4a9f7e;
}

.breakdown-incorrect {
  font-size: 0.875rem;
  color: #c87a6a;
}

.breakdown-separator {
  color: rgba(0, 0, 0, 0.3);
}

.breakdown-bar {
  height: 6px;
  background: rgba(232, 160, 135, 0.3);
  border-radius: 3px;
  overflow: hidden;
}

.breakdown-bar.real {
  background: rgba(152, 212, 187, 0.3);
}

.breakdown-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.breakdown-card.fake .breakdown-bar-fill {
  background: var(--llars-danger);
}

.breakdown-card.real .breakdown-bar-fill {
  background: var(--llars-success);
}

/* Footer */
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.02);
}

.footer-info {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
}

/* User Detail Dialog */
.user-detail-dialog {
  border-radius: var(--llars-radius) !important;
  overflow: hidden;
}

.detail-dialog-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  color: white;
}

.detail-dialog-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.detail-dialog-header :deep(.v-btn) {
  color: white !important;
}

.detail-dialog-content {
  padding: 20px;
}

.detail-tabs {
  margin-bottom: 16px;
}

.detail-thread-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

/* Responsive */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .detail-threads-grid {
    grid-template-columns: 1fr;
  }

  .vote-legend {
    gap: 16px;
  }

  .detail-stats-row {
    flex-wrap: wrap;
    gap: 16px;
  }
}
</style>
