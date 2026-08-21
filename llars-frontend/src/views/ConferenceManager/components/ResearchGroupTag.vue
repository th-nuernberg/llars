<template>
  <div class="research-group-tag d-flex align-center gap-2">
    <LTag variant="info" @click="router.push({ name: 'ResearchGroupSelection' })">
      <v-icon start size="14">mdi-account-group</v-icon>
      {{ group.name }}
    </LTag>
    <LIconBtn
      v-if="canManageMembers"
      icon="mdi-account-plus-outline"
      :tooltip="t('researchGroup.members.invite')"
      size="small"
      @click="router.push({ name: 'ResearchGroupMembers', params: { groupId: group.id } })"
    />
    <v-badge
      v-if="pendingCount > 0"
      :content="pendingCount"
      color="warning"
      inline
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useResearchGroups } from '../composables/useResearchGroups'

const props = defineProps({
  group: { type: Object, required: true },
})

const { t } = useI18n()
const router = useRouter()
const { fetchPendingRequests, pendingRequests } = useResearchGroups()

const canManageMembers = computed(() => {
  const role = props.group.user_role
  return role === 'owner' || role === 'member'
})

const pendingCount = computed(() => {
  return pendingRequests.value.filter(r => r.group_id === props.group.id).length
})

onMounted(() => {
  if (canManageMembers.value) {
    fetchPendingRequests()
  }
})
</script>

<style scoped>
.research-group-tag {
  cursor: default;
}
</style>
