<template>
  <div class="access-request-page">
    <div class="page-header">
      <div class="header-left">
        <LIconBtn
          icon="mdi-arrow-left"
          :tooltip="t('common.back')"
          @click="router.push({ name: 'ResearchGroupSelection' })"
        />
        <v-icon size="28" color="primary">mdi-lock-open-variant-outline</v-icon>
        <h1 class="title">{{ t('researchGroup.accessRequest.title') }}</h1>
      </div>
    </div>

    <LLoading v-if="loading" />

    <v-card v-else variant="outlined" class="request-card" max-width="600">
      <v-card-text class="pa-6">
        <div class="text-center mb-6">
          <v-icon size="64" color="primary" class="mb-3">mdi-account-group-outline</v-icon>
          <h2 class="text-h6 mb-1">{{ groupInfo?.name }}</h2>
          <p v-if="groupInfo?.description" class="text-body-2 text-medium-emphasis">
            {{ groupInfo.description }}
          </p>
        </div>

        <!-- Already sent -->
        <div v-if="requestSent" class="text-center">
          <v-icon size="48" color="success" class="mb-3">mdi-check-circle-outline</v-icon>
          <p class="text-body-1">{{ t('researchGroup.accessRequest.sent') }}</p>
        </div>

        <!-- Request form -->
        <template v-else>
          <v-textarea
            v-model="message"
            :label="t('researchGroup.accessRequest.message')"
            variant="outlined"
            rows="3"
            class="mb-4"
          />
          <div class="text-center">
            <LBtn variant="primary" :loading="submitting" @click="submitRequest">
              {{ t('researchGroup.accessRequest.submit') }}
            </LBtn>
          </div>
        </template>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from './composables/useResearchGroups'

const props = defineProps({
  groupId: { type: [String, Number], required: true },
})

const { t } = useI18n()
const router = useRouter()
const { createAccessRequest } = useResearchGroups()

const loading = ref(true)
const groupInfo = ref(null)
const message = ref('')
const submitting = ref(false)
const requestSent = ref(false)

async function loadGroup() {
  try {
    // Try to fetch group info (might fail if not a member, use allGroups fallback)
    const { fetchAllGroups, allGroups } = useResearchGroups()
    await fetchAllGroups()
    groupInfo.value = allGroups.value.find(g => g.id === Number(props.groupId))
  } catch {
    // Ignore
  } finally {
    loading.value = false
  }
}

async function submitRequest() {
  submitting.value = true
  try {
    const result = await createAccessRequest(props.groupId, message.value)
    if (result.status === 'already_pending') {
      requestSent.value = true
    } else {
      requestSent.value = true
    }
  } catch (err) {
    console.error('Failed to submit request:', err)
  } finally {
    submitting.value = false
  }
}

onMounted(loadGroup)
</script>

<style scoped>
.access-request-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left .title {
  font-size: 1.3rem;
  font-weight: 500;
  margin: 0;
}

.request-card {
  margin: 0 auto;
  border-radius: 16px 4px 16px 4px;
}
</style>
