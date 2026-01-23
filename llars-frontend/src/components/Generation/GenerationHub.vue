<!--
  GenerationHub.vue - Batch Generation Overview

  Main dashboard for batch generation jobs. Shows all jobs
  with their status, progress, and actions. Entry point for
  creating new jobs and accessing job details.
-->
<template>
  <div class="generation-hub" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="hub-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goHome">
        {{ $t('navigation.home') }}
      </LBtn>
      <div class="header-info">
        <h1>{{ $t('generation.title') }}</h1>
        <p class="text-medium-emphasis">{{ $t('generation.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <!-- Status Filter -->
        <v-menu offset-y>
          <template v-slot:activator="{ props }">
            <LBtn variant="tonal" size="small" v-bind="props">
              <LIcon start size="18">mdi-filter-variant</LIcon>
              {{ activeFilter ? getStatusLabel(activeFilter) : $t('generation.hub.allStatuses') }}
              <LIcon end size="18">mdi-chevron-down</LIcon>
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="activeFilter = null">
              <v-list-item-title>{{ $t('generation.hub.allStatuses') }}</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item
              v-for="status in STATUS_OPTIONS"
              :key="status.value"
              @click="activeFilter = status.value"
            >
              <template v-slot:prepend>
                <LIcon size="18" :color="status.color" class="mr-2">{{ status.icon }}</LIcon>
              </template>
              <v-list-item-title>{{ status.label }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

        <!-- New Job Button -->
        <LBtn variant="primary" @click="showWizard = true">
          <LIcon start>mdi-plus</LIcon>
          {{ $t('generation.hub.newJob') }}
        </LBtn>
      </div>
    </div>

    <!-- Content -->
    <div class="hub-content">
      <!-- Active Jobs Section -->
      <div v-if="activeJobs.length > 0" class="jobs-section">
        <h3 class="section-title">
          <LIcon color="primary" class="mr-2">mdi-play-circle-outline</LIcon>
          {{ $t('generation.hub.activeJobs') }}
          <LTag variant="info" size="small" class="ml-2">{{ activeJobs.length }}</LTag>
        </h3>
        <div class="jobs-grid">
          <GenerationJobCard
            v-for="job in activeJobs"
            :key="job.id"
            :job="job"
            @click="navigateToJob(job)"
            @pause="pauseJob(job.id)"
            @cancel="cancelJob(job.id)"
          />
        </div>
      </div>

      <!-- All Jobs Grid -->
      <div class="jobs-section">
        <h3 class="section-title">
          <LIcon color="secondary" class="mr-2">mdi-format-list-bulleted</LIcon>
          {{ $t('generation.hub.allJobs') }}
        </h3>

        <!-- Loading Skeletons -->
        <div v-if="isLoading" class="jobs-grid">
          <div v-for="n in 6" :key="'skel-' + n" class="job-card-skeleton">
            <v-skeleton-loader type="card" height="180" />
          </div>
        </div>

        <!-- Job Cards -->
        <div v-else-if="filteredJobs.length > 0" class="jobs-grid">
          <GenerationJobCard
            v-for="job in filteredJobs"
            :key="job.id"
            :job="job"
            @click="navigateToJob(job)"
            @start="startJob(job.id)"
            @pause="pauseJob(job.id)"
            @cancel="cancelJob(job.id)"
            @delete="confirmDelete(job)"
          />
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <LIcon size="64" color="grey-lighten-1">mdi-robot-off-outline</LIcon>
          <h3>{{ $t('generation.hub.emptyTitle') }}</h3>
          <p class="text-medium-emphasis">
            {{ activeFilter ? $t('generation.hub.emptyFilterHint') : $t('generation.hub.emptyHint') }}
          </p>
          <div class="empty-actions">
            <LBtn v-if="activeFilter" variant="tonal" @click="activeFilter = null">
              {{ $t('generation.hub.clearFilter') }}
            </LBtn>
            <LBtn variant="primary" @click="showWizard = true">
              <LIcon start>mdi-plus</LIcon>
              {{ $t('generation.hub.createFirst') }}
            </LBtn>
          </div>
        </div>
      </div>
    </div>

    <!-- Generation Wizard Dialog -->
    <v-dialog
      v-model="showWizard"
      max-width="900"
      persistent
      scrollable
    >
      <GenerationWizard
        v-if="showWizard"
        @close="showWizard = false"
        @created="handleJobCreated"
      />
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <LCard>
        <template #title>
          <LIcon color="danger" class="mr-2">mdi-delete-alert</LIcon>
          {{ $t('generation.hub.deleteTitle') }}
        </template>
        <v-card-text>
          {{ $t('generation.hub.deleteConfirm', { name: jobToDelete?.name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showDeleteDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" @click="executeDelete">
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </LCard>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMobile } from '@/composables/useMobile'
import { useGeneration, JOB_STATUS } from '@/composables/useGeneration'
import GenerationJobCard from './GenerationJobCard.vue'
import GenerationWizard from './GenerationWizard.vue'

const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()

// Generation composable
const {
  jobs,
  activeJobs,
  isLoading,
  loadJobs,
  startJob,
  pauseJob,
  cancelJob,
  deleteJob
} = useGeneration({ autoLoadJobs: true })

// Local state
const activeFilter = ref(null)
const showWizard = ref(false)
const showDeleteDialog = ref(false)
const jobToDelete = ref(null)

// Status filter options
const STATUS_OPTIONS = [
  { value: JOB_STATUS.CREATED, label: t('generation.status.created'), icon: 'mdi-clock-outline', color: 'grey' },
  { value: JOB_STATUS.RUNNING, label: t('generation.status.running'), icon: 'mdi-play-circle', color: 'primary' },
  { value: JOB_STATUS.PAUSED, label: t('generation.status.paused'), icon: 'mdi-pause-circle', color: 'warning' },
  { value: JOB_STATUS.COMPLETED, label: t('generation.status.completed'), icon: 'mdi-check-circle', color: 'success' },
  { value: JOB_STATUS.FAILED, label: t('generation.status.failed'), icon: 'mdi-alert-circle', color: 'error' },
  { value: JOB_STATUS.CANCELLED, label: t('generation.status.cancelled'), icon: 'mdi-cancel', color: 'grey' }
]

// Computed
const filteredJobs = computed(() => {
  if (!activeFilter.value) return jobs.value
  return jobs.value.filter(j => j.status === activeFilter.value)
})

// Methods
function getStatusLabel(status) {
  const option = STATUS_OPTIONS.find(o => o.value === status)
  return option?.label || status
}

function navigateToJob(job) {
  router.push({ name: 'GenerationJobDetail', params: { jobId: job.id } })
}

function handleJobCreated(job) {
  showWizard.value = false
  navigateToJob(job)
}

function confirmDelete(job) {
  jobToDelete.value = job
  showDeleteDialog.value = true
}

async function executeDelete() {
  if (jobToDelete.value) {
    await deleteJob(jobToDelete.value.id)
    showDeleteDialog.value = false
    jobToDelete.value = null
  }
}

function goHome() {
  router.push('/Home')
}
</script>

<style scoped>
.generation-hub {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
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

.header-info h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-info p {
  margin: 4px 0 0 0;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Content */
.hub-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Sections */
.jobs-section {
  margin-bottom: 32px;
}

.jobs-section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 16px 0;
}

/* Jobs Grid */
.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px 4px 12px 4px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.1);
}

.empty-state h3 {
  margin: 16px 0 8px 0;
  font-size: 1.1rem;
}

.empty-state p {
  max-width: 400px;
  margin-bottom: 16px;
}

.empty-actions {
  display: flex;
  gap: 12px;
}

/* Skeleton */
.job-card-skeleton {
  min-height: 180px;
}

/* Mobile Styles */
.generation-hub.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
}

.generation-hub.is-mobile .hub-header {
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
}

.generation-hub.is-mobile .header-info h1 {
  font-size: 1.25rem;
}

.generation-hub.is-mobile .header-actions {
  width: 100%;
  justify-content: space-between;
}

.generation-hub.is-mobile .hub-content {
  padding: 16px;
}

.generation-hub.is-mobile .jobs-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}
</style>
