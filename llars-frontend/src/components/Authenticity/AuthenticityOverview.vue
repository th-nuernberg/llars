<template>
  <div class="overview-page">
    <!-- Header -->
    <div class="overview-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goToHub">
        Evaluierungen
      </LBtn>
      <div class="header-info">
        <h1>Fake/Echt</h1>
        <p class="text-medium-emphasis">Öffne einen Verlauf und stimme ab, ob er echt oder fake ist.</p>
      </div>
      <div class="header-stats">
        <LTag variant="success" size="small">
          {{ doneCount }} / {{ threads.length }} abgeschlossen
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
            v-for="thread in threads"
            :key="thread.thread_id"
            class="thread-card"
            :class="{ 'is-done': thread.vote }"
            @click="openThread(thread.thread_id)"
          >
            <LEvaluationStatus
              class="card-status"
              :status="thread.vote ? 'done' : 'pending'"
            />
            <div class="card-body">
              <h3 class="card-title">{{ thread.subject }}</h3>
              <p class="card-subtitle">{{ thread.sender }}</p>
            </div>
            <div class="card-footer">
              <LTag v-if="thread.vote" :variant="thread.vote === 'real' ? 'success' : 'danger'" size="small">
                {{ thread.vote === 'real' ? 'Echt' : 'Fake' }}
              </LTag>
              <span class="card-id">Thread #{{ thread.thread_id }}</span>
            </div>
          </div>

          <div v-if="threads.length === 0" class="empty-state">
            <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
            <h3>Keine Threads verfügbar</h3>
            <p class="text-medium-emphasis">
              Stelle sicher, dass ein aktives Szenario existiert und Threads zugewiesen sind.
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
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { listAuthenticityThreads } from '@/services/authenticityApi'

const router = useRouter()
const { isLoading, withLoading } = useSkeletonLoading(['threads'])

const threads = ref([])

const doneCount = computed(() => threads.value.filter(t => t.vote).length)

onMounted(async () => {
  await withLoading('threads', async () => {
    threads.value = await listAuthenticityThreads()
  })
})

function goToHub() {
  router.push({ name: 'EvaluationHub' })
}

function openThread(threadId) {
  router.push({ name: 'AuthenticityDetail', params: { id: threadId } })
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
</style>
