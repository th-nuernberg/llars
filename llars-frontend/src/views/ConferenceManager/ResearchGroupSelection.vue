<template>
  <div class="group-selection">
    <div class="page-header">
      <div class="header-left">
        <v-icon size="28" color="primary">mdi-account-group-outline</v-icon>
        <h1 class="title">{{ t('researchGroup.selection.title') }}</h1>
      </div>
    </div>

    <LLoading v-if="groupLoading" />

    <template v-else>
      <!-- My Groups -->
      <div v-if="myGroups.length" class="mb-6">
        <h3 class="text-subtitle-1 font-weight-medium mb-3">{{ t('researchGroup.myGroups') }}</h3>
        <div class="groups-grid">
          <v-card
            v-for="group in myGroups"
            :key="group.id"
            class="group-card"
            variant="outlined"
            @click="router.push({ name: 'ConferenceManager', params: { groupId: group.id } })"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon size="20" color="primary" class="mr-2">mdi-account-group</v-icon>
                <span class="text-subtitle-1 font-weight-medium">{{ group.name }}</span>
              </div>
              <p v-if="group.description" class="text-body-2 text-medium-emphasis mb-2">
                {{ group.description }}
              </p>
              <div class="d-flex align-center gap-2">
                <LTag variant="info" size="small">
                  {{ t(`researchGroup.members.roles.${group.user_role}`) }}
                </LTag>
                <span class="text-caption text-medium-emphasis">
                  {{ group.member_count }} {{ t('researchGroup.members.title') }}
                </span>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </div>

      <!-- No Groups Message -->
      <div v-else class="text-center pa-8">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-account-group-outline</v-icon>
        <p class="text-body-1 text-medium-emphasis mb-4">{{ t('researchGroup.selection.noGroups') }}</p>
      </div>

      <!-- All Groups (for requesting access) -->
      <div v-if="otherGroups.length">
        <h3 class="text-subtitle-1 font-weight-medium mb-3">{{ t('researchGroup.selection.otherGroups') }}</h3>
        <div class="groups-grid">
          <v-card
            v-for="group in otherGroups"
            :key="group.id"
            class="group-card"
            variant="outlined"
            @click="router.push({ name: 'ResearchGroupAccessRequest', params: { groupId: group.id } })"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-icon size="20" color="grey" class="mr-2">mdi-account-group-outline</v-icon>
                <span class="text-subtitle-1 font-weight-medium">{{ group.name }}</span>
              </div>
              <p v-if="group.description" class="text-body-2 text-medium-emphasis mb-2">
                {{ group.description }}
              </p>
              <div class="d-flex align-center">
                <span class="text-caption text-medium-emphasis">
                  {{ group.member_count }} {{ t('researchGroup.members.title') }}
                </span>
                <v-spacer />
                <LBtn variant="text" size="small">
                  {{ t('researchGroup.accessRequest.title') }}
                  <v-icon end size="14">mdi-arrow-right</v-icon>
                </LBtn>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from './composables/useResearchGroups'

const { t } = useI18n()
const router = useRouter()
const { myGroups, allGroups, groupLoading, fetchMyGroups, fetchAllGroups } = useResearchGroups()

const myGroupIds = computed(() => new Set(myGroups.value.map(g => g.id)))
const otherGroups = computed(() => allGroups.value.filter(g => !myGroupIds.value.has(g.id)))

onMounted(async () => {
  await Promise.all([fetchMyGroups(), fetchAllGroups()])
})
</script>

<style scoped>
.group-selection {
  max-width: 1000px;
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
  font-size: 1.5rem;
  font-weight: 500;
  margin: 0;
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.group-card {
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s;
  border-radius: 16px 4px 16px 4px;
}

.group-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
