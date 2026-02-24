<template>
  <div class="pipeline-hub">
    <!-- Header -->
    <div class="hub-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goHome">
        {{ $t('navigation.home') }}
      </LBtn>
      <div class="header-info">
        <h1 class="header-title">{{ $t('pipeline.title') }}</h1>
        <p class="header-subtitle">{{ $t('pipeline.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <v-menu offset-y>
          <template #activator="{ props }">
            <LBtn variant="tonal" size="small" v-bind="props">
              <v-icon start size="16">mdi-filter-variant</v-icon>
              {{ activeFilter ? getStatusLabel(activeFilter) : $t('pipeline.allStatuses') }}
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="activeFilter = null">
              {{ $t('pipeline.allStatuses') }}
            </v-list-item>
            <v-divider />
            <v-list-item
              v-for="s in STATUS_OPTIONS"
              :key="s.value"
              @click="activeFilter = s.value"
            >
              {{ s.label }}
            </v-list-item>
          </v-list>
        </v-menu>
        <LBtn variant="primary" @click="$router.push({ name: 'PipelineWizard' })">
          <v-icon start size="18">mdi-plus</v-icon>
          {{ $t('pipeline.newRun') }}
        </LBtn>
      </div>
    </div>

    <!-- Content -->
    <div class="hub-content">
      <!-- Active runs section -->
      <div v-if="activeRuns.length > 0" class="runs-section">
        <h3 class="section-title">
          <v-icon color="primary" size="20" class="mr-2">mdi-play-circle-outline</v-icon>
          {{ $t('pipeline.activeRuns') }}
          <LTag variant="info" size="sm">{{ activeRuns.length }}</LTag>
        </h3>
        <div class="runs-grid">
          <PipelineRunCard
            v-for="run in activeRuns"
            :key="run.id"
            :run="run"
            @click="navigateToRun(run)"
          />
        </div>
      </div>

      <!-- All runs -->
      <div class="runs-section">
        <h3 v-if="activeRuns.length > 0" class="section-title">
          {{ $t('pipeline.allRuns') }}
        </h3>

        <!-- Loading -->
        <div v-if="isLoading" class="runs-grid">
          <div v-for="n in 6" :key="'skel-' + n">
            <v-skeleton-loader type="card" height="180" />
          </div>
        </div>

        <!-- Runs grid -->
        <div v-else-if="filteredRuns.length > 0" class="runs-grid">
          <PipelineRunCard
            v-for="run in filteredRuns"
            :key="run.id"
            :run="run"
            @click="navigateToRun(run)"
          />
        </div>

        <!-- Empty state -->
        <div v-else class="empty-state">
          <v-icon size="64" color="grey-lighten-1">mdi-transit-connection-variant</v-icon>
          <h3>{{ $t('pipeline.emptyTitle') }}</h3>
          <p>{{ activeFilter ? $t('pipeline.emptyFilterHint') : $t('pipeline.emptyHint') }}</p>
          <LBtn variant="primary" @click="$router.push({ name: 'PipelineWizard' })">
            {{ $t('pipeline.createFirst') }}
          </LBtn>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePipeline, RUN_STATUS } from './composables/usePipeline'
import PipelineRunCard from './components/PipelineRunCard.vue'
import LBtn from '@/components/common/LBtn.vue'
import LTag from '@/components/common/LTag.vue'

const router = useRouter()
const { t } = useI18n()

const {
  runs,
  activeRuns,
  isLoading,
} = usePipeline({ autoLoadRuns: true })

const activeFilter = ref(null)

const STATUS_OPTIONS = computed(() => [
  { value: RUN_STATUS.RUNNING, label: t('pipeline.status.running') },
  { value: RUN_STATUS.COMPLETED, label: t('pipeline.status.completed') },
  { value: RUN_STATUS.PAUSED, label: t('pipeline.status.paused') },
  { value: RUN_STATUS.WAITING_FOR_REVIEW, label: t('pipeline.status.waitingForReview') },
  { value: RUN_STATUS.FAILED, label: t('pipeline.status.failed') },
])

const filteredRuns = computed(() => {
  if (!activeFilter.value) return runs.value
  return runs.value.filter(r => r.status === activeFilter.value)
})

function getStatusLabel(status) {
  const found = STATUS_OPTIONS.value.find(s => s.value === status)
  return found ? found.label : status
}

function goHome() {
  router.push('/home')
}

function navigateToRun(run) {
  router.push({ name: 'PipelineSession', params: { runId: run.id } })
}
</script>

<style scoped>
.pipeline-hub {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.hub-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.header-subtitle {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.hub-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.runs-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.runs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  gap: 12px;
}

.empty-state h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.empty-state p {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.85rem;
  margin: 0;
}

@media (max-width: 768px) {
  .hub-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .runs-grid {
    grid-template-columns: 1fr;
  }
}
</style>
