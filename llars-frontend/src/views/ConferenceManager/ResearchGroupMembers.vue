<template>
  <div class="group-members-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <LIconBtn
          icon="mdi-arrow-left"
          :tooltip="t('common.back')"
          @click="router.push({ name: 'ConferenceManager', params: { groupId } })"
        />
        <v-icon size="28" color="primary">mdi-account-group</v-icon>
        <h1 class="title">{{ currentGroup?.name }} - {{ t('researchGroup.members.title') }}</h1>
      </div>
      <div class="header-right">
        <LBtn v-if="canInvite" variant="primary" @click="showInviteDialog = true">
          <v-icon start>mdi-account-plus</v-icon>
          {{ t('researchGroup.members.invite') }}
        </LBtn>
      </div>
    </div>

    <LLoading v-if="loading" />

    <template v-else>
      <!-- Members List -->
      <v-card variant="outlined" class="mb-4 members-card">
        <v-list>
          <v-list-item
            v-for="member in groupMembers"
            :key="member.id"
            class="member-item"
          >
            <template #prepend>
              <LAvatar :username="member.username" :seed="member.avatar_seed" :src="member.avatar_url" size="md" />
            </template>
            <v-list-item-title>{{ member.username }}</v-list-item-title>
            <v-list-item-subtitle>
              <LTag
                :variant="roleVariant(member.role)"
                size="small"
              >
                {{ t(`researchGroup.members.roles.${member.role}`) }}
              </LTag>
            </v-list-item-subtitle>
            <template #append>
              <div v-if="canManage && member.username !== currentUsername" class="d-flex align-center gap-1">
                <v-menu>
                  <template #activator="{ props: menuProps }">
                    <LIconBtn
                      v-bind="menuProps"
                      icon="mdi-swap-horizontal"
                      tooltip="Change role"
                      size="small"
                    />
                  </template>
                  <v-list density="compact">
                    <v-list-item
                      v-for="role in availableRoles"
                      :key="role"
                      :disabled="member.role === role"
                      @click="handleRoleChange(member.id, role)"
                    >
                      <v-list-item-title>{{ t(`researchGroup.members.roles.${role}`) }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
                <LIconBtn
                  icon="mdi-account-remove"
                  tooltip="Remove"
                  size="small"
                  color="error"
                  @click="handleRemove(member)"
                />
              </div>
              <!-- Self-leave -->
              <LBtn
                v-else-if="member.username === currentUsername && member.role !== 'owner'"
                variant="text"
                size="small"
                color="error"
                @click="handleRemove(member)"
              >
                {{ t('common.leave') }}
              </LBtn>
            </template>
          </v-list-item>
        </v-list>
      </v-card>

      <!-- Pending Access Requests -->
      <div v-if="canInvite && groupRequests.length" class="mb-4">
        <h3 class="text-subtitle-1 font-weight-medium mb-2">
          {{ t('researchGroup.accessRequest.pending') }} ({{ groupRequests.length }})
        </h3>
        <v-card variant="outlined" class="members-card">
          <v-list>
            <v-list-item
              v-for="req in groupRequests"
              :key="req.id"
              class="member-item"
            >
              <v-list-item-title>{{ req.requester_username }}</v-list-item-title>
              <v-list-item-subtitle v-if="req.message">{{ req.message }}</v-list-item-subtitle>
              <template #append>
                <div class="d-flex gap-2">
                  <LBtn variant="primary" size="small" @click="handleResolve(req.id, 'approve')">
                    {{ t('researchGroup.accessRequest.approve') }}
                  </LBtn>
                  <LBtn variant="danger" size="small" @click="handleResolve(req.id, 'reject')">
                    {{ t('researchGroup.accessRequest.reject') }}
                  </LBtn>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </div>
    </template>

    <!-- Invite Dialog -->
    <ResearchGroupInviteDialog
      v-model="showInviteDialog"
      :group-id="groupId"
      @invited="onMemberInvited"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { useResearchGroups } from './composables/useResearchGroups'
import ResearchGroupInviteDialog from './components/ResearchGroupInviteDialog.vue'

const props = defineProps({
  groupId: { type: [String, Number], required: true },
})

const { t } = useI18n()
const router = useRouter()
const { tokenParsed } = useAuth()
const {
  currentGroup, groupMembers, fetchGroup, fetchMembers,
  updateMemberRole, removeMember, fetchGroupRequests, resolveAccessRequest,
} = useResearchGroups()

const loading = ref(true)
const showInviteDialog = ref(false)
const groupRequests = ref([])

const currentUsername = computed(() => tokenParsed.value?.preferred_username)
const userRole = computed(() => currentGroup.value?.user_role)
const canManage = computed(() => userRole.value === 'owner')
const canInvite = computed(() => userRole.value === 'owner' || userRole.value === 'member')
const availableRoles = ['owner', 'member', 'viewer']

function roleVariant(role) {
  if (role === 'owner') return 'warning'
  if (role === 'member') return 'success'
  return 'info'
}

async function handleRoleChange(memberId, newRole) {
  await updateMemberRole(props.groupId, memberId, newRole)
}

async function handleRemove(member) {
  if (!confirm(t('researchGroup.members.confirmRemove', { name: member.username }))) return
  await removeMember(props.groupId, member.id)
}

async function handleResolve(requestId, action) {
  await resolveAccessRequest(requestId, action)
  groupRequests.value = await fetchGroupRequests(props.groupId)
  await fetchMembers(props.groupId)
}

function onMemberInvited() {
  fetchMembers(props.groupId)
}

onMounted(async () => {
  loading.value = true
  try {
    await fetchGroup(props.groupId)
    await fetchMembers(props.groupId)
    if (canInvite.value) {
      groupRequests.value = await fetchGroupRequests(props.groupId)
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.group-members-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.members-card {
  border-radius: 16px 4px 16px 4px;
}

.member-item {
  min-height: 56px;
}
</style>
