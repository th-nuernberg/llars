<template>
  <div class="conference-entry">
    <LLoading v-if="loading" :text="t('researchGroup.loading')" />
    <div v-else-if="error" class="text-center pa-8">
      <v-icon size="48" color="error" class="mb-4">mdi-alert-circle-outline</v-icon>
      <p>{{ error }}</p>
      <LBtn variant="primary" @click="loadGroups">{{ t('common.retry') }}</LBtn>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from './composables/useResearchGroups'

const { t } = useI18n()
const router = useRouter()
const { fetchMyGroups } = useResearchGroups()

const loading = ref(true)
const error = ref(null)

async function loadGroups() {
  loading.value = true
  error.value = null
  try {
    const groups = await fetchMyGroups()

    if (groups.length === 0) {
      // No groups - show selection page (they can request access)
      router.replace({ name: 'ResearchGroupSelection' })
    } else if (groups.length === 1) {
      // Single group - go directly to conference manager
      router.replace({ name: 'ConferenceManager', params: { groupId: groups[0].id } })
    } else {
      // Multiple groups - show selection
      router.replace({ name: 'ResearchGroupSelection' })
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to load groups'
  } finally {
    loading.value = false
  }
}

onMounted(loadGroups)
</script>

<style scoped>
.conference-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}
</style>
