<!-- Ranker/Ranker.vue -->
<template>
  <div class="overview-page" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="overview-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goToHub">
        {{ $t('evaluation.backToEvaluations') }}
      </LBtn>
      <div class="header-info">
        <h1>{{ $t('evaluation.ranking.pageTitle') }}</h1>
        <p class="text-medium-emphasis">{{ $t('evaluation.ranking.pageSubtitle') }}</p>
      </div>
      <div class="header-stats">
        <LTag variant="success" size="small">
          {{ $t('evaluation.progress', { done: doneCount, total: emailThreads.length }) }}
        </LTag>
      </div>
    </div>

    <!-- Content -->
    <div class="overview-content">
      <div class="threads-grid">
        <template v-if="isLoading('threads')">
          <div v-for="n in 6" :key="'skel-' + n" class="thread-card-skeleton">
            <v-skeleton-loader type="card" height="180" />
          </div>
        </template>

        <template v-else>
          <div
            v-for="thread in emailThreads"
            :key="thread.thread_id"
            class="thread-card"
            :class="{ 'is-done': thread.ranked }"
            @click="navigateToCase(thread.thread_id)"
          >
            <LEvaluationStatus
              class="card-status"
              :status="thread.ranked ? 'done' : 'pending'"
            />
            <div class="card-body">
              <h3 class="card-title">{{ thread.subject }}</h3>
              <p class="card-subtitle">{{ thread.sender }}</p>
            </div>
            <div class="card-footer">
              <LTag variant="gray" size="small">Chat #{{ thread.chat_id }}</LTag>
              <span class="card-id">Thread #{{ thread.thread_id }}</span>
            </div>
          </div>

          <div v-if="emailThreads.length === 0" class="empty-state">
            <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
            <h3>{{ $t('evaluation.ranking.emptyTitle') }}</h3>
            <p class="text-medium-emphasis">
              {{ $t('evaluation.emptyHint') }}
            </p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useMobile } from '@/composables/useMobile'

const { isMobile } = useMobile()

const router = useRouter()
const emailThreads = ref([])
const { isLoading, withLoading } = useSkeletonLoading(['threads'])

const doneCount = computed(() => emailThreads.value.filter(t => t.ranked).length)

onMounted(async () => {
  await withLoading('threads', async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/email_threads/rankings`)
      emailThreads.value = response.data
    } catch (error) {
      console.error('Error fetching email threads:', error)
      emailThreads.value = []
    }
  })
})

function goToHub() {
  router.push({ name: 'EvaluationHub' })
}

function navigateToCase(threadId) {
  router.push({ name: 'RankerDetail', params: { id: threadId } })
}
</script>

<style scoped>
.overview-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.overview-header {
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

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.threads-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.thread-card {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  min-height: 160px;
}

.thread-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.thread-card.is-done {
  border-left: 3px solid rgb(var(--v-theme-success));
}

.card-status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.card-body {
  flex: 1;
  padding-right: 100px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-subtitle {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.card-id {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state h3 {
  margin: 16px 0 8px 0;
  font-size: 1.1rem;
}

.empty-state p {
  max-width: 400px;
}

/* Mobile Styles */
.overview-page.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
}

.overview-page.is-mobile .overview-header {
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
}

.overview-page.is-mobile .header-info h1 {
  font-size: 1.25rem;
}

.overview-page.is-mobile .header-info p {
  font-size: 0.8rem;
}

.overview-page.is-mobile .overview-content {
  padding: 16px;
}

.overview-page.is-mobile .threads-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}

.overview-page.is-mobile .thread-card {
  min-height: 140px;
  padding: 12px;
}

.overview-page.is-mobile .card-body {
  padding-right: 80px;
}

.overview-page.is-mobile .card-title {
  font-size: 0.9rem;
}
</style>
