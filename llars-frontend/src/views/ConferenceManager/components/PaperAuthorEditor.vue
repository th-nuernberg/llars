<template>
  <div>
    <div class="d-flex align-center mb-2">
      <span class="text-subtitle-2">{{ t('conferenceManager.paper.authors') }}</span>
      <v-spacer />
      <v-btn size="small" variant="text" @click="showExternal = true" prepend-icon="mdi-account-plus-outline">
        {{ t('conferenceManager.paper.addExternal') }}
      </v-btn>
    </div>

    <!-- User Search to add LLARS users -->
    <div class="author-search mb-3">
      <LUserSearch
        ref="userSearchRef"
        :placeholder="t('conferenceManager.paper.searchUser')"
        density="compact"
        :exclude-usernames="existingUsernames"
        @select="addUserAuthor"
      />
    </div>

    <!-- External author input (toggled) -->
    <div v-if="showExternal" class="external-input mb-3">
      <div class="d-flex align-center ga-2">
        <v-text-field
          v-model="externalName"
          :label="t('conferenceManager.paper.externalAuthor')"
          density="compact"
          variant="outlined"
          hide-details
          style="flex: 1"
          @keydown.enter.prevent="addExternalAuthor"
        />
        <v-btn
          icon
          size="small"
          variant="tonal"
          color="primary"
          :disabled="!externalName.trim()"
          @click="addExternalAuthor"
        >
          <v-icon size="18">mdi-plus</v-icon>
        </v-btn>
        <v-btn icon size="small" variant="text" @click="showExternal = false; externalName = ''">
          <v-icon size="18">mdi-close</v-icon>
        </v-btn>
      </div>
    </div>

    <!-- Author list -->
    <div v-if="localAuthors.length" class="author-list">
      <div
        v-for="(author, index) in localAuthors"
        :key="author._key"
        class="author-row"
      >
        <div class="author-info">
          <!-- LLARS user -->
          <template v-if="author.user_id">
            <LAvatar
              :username="author.username"
              :seed="author.avatar_seed"
              :src="author.avatar_url"
              size="xs"
            />
            <span class="author-name">{{ formatDisplayName(author.username) }}</span>
            <span class="author-username">@{{ author.username }}</span>
          </template>
          <!-- External author -->
          <template v-else>
            <span class="author-circle-ext">
              {{ getInitials(author.external_name) }}
            </span>
            <span class="author-name">{{ author.external_name }}</span>
            <v-chip size="x-small" variant="outlined" :style="{ borderRadius: '6px 2px 6px 2px' }">
              {{ t('conferenceManager.paper.externalAuthor') }}
            </v-chip>
          </template>
        </div>

        <div class="author-actions">
          <v-checkbox
            v-model="author.is_corresponding"
            :label="t('conferenceManager.paper.corresponding')"
            density="compact"
            hide-details
            class="corresponding-check"
          />
          <v-btn icon size="small" variant="text" color="error" @click="removeAuthor(index)">
            <v-icon size="18">mdi-close</v-icon>
          </v-btn>
        </div>
      </div>
    </div>

    <div v-else class="text-body-2 text-medium-emphasis pa-2">
      {{ t('conferenceManager.paper.noAuthors') }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import LUserSearch from '@/components/common/LUserSearch.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import { formatDisplayName } from '@/utils/userUtils'

const { t } = useI18n()

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

let keyCounter = 0
const userSearchRef = ref(null)
const showExternal = ref(false)
const externalName = ref('')

function makeKey() {
  return ++keyCounter
}

function toLocal(authors) {
  return authors.map(a => ({ ...a, _key: makeKey() }))
}

const localAuthors = ref(toLocal(props.modelValue))

watch(() => props.modelValue, (val) => {
  // Only sync if structurally different (avoid loops)
  if (JSON.stringify(val.map(a => ({ ...a, _key: undefined }))) !==
      JSON.stringify(localAuthors.value.map(a => ({ ...a, _key: undefined })))) {
    localAuthors.value = toLocal(val)
  }
}, { deep: true })

watch(localAuthors, (val) => {
  emit('update:modelValue', val.map((a, i) => {
    const { _key, ...rest } = a
    return { ...rest, author_order: i }
  }))
}, { deep: true })

const existingUsernames = computed(() =>
  localAuthors.value
    .filter(a => a.username)
    .map(a => a.username)
)

function addUserAuthor(user) {
  localAuthors.value.push({
    _key: makeKey(),
    user_id: user.id,
    username: user.username,
    avatar_seed: user.avatar_seed,
    avatar_url: user.avatar_url,
    external_name: null,
    author_order: localAuthors.value.length,
    is_corresponding: false,
  })
  // Reset search
  if (userSearchRef.value) {
    userSearchRef.value.reset()
  }
}

function addExternalAuthor() {
  const name = externalName.value.trim()
  if (!name) return
  localAuthors.value.push({
    _key: makeKey(),
    user_id: null,
    username: null,
    external_name: name,
    author_order: localAuthors.value.length,
    is_corresponding: false,
  })
  externalName.value = ''
}

function removeAuthor(index) {
  localAuthors.value.splice(index, 1)
}

function getInitials(name) {
  if (!name) return '?'
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}
</script>

<style scoped>
.author-search {
  max-width: 400px;
}

.external-input {
  max-width: 400px;
}

.author-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 10px;
  border-radius: 8px;
  transition: background 0.15s;
}

.author-row:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.author-name {
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.author-username {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  white-space: nowrap;
}

.author-circle-ext {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6rem;
  font-weight: 600;
  flex-shrink: 0;
}

.author-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.corresponding-check {
  flex-shrink: 0;
}

.corresponding-check :deep(.v-label) {
  font-size: 0.75rem;
  opacity: 0.7;
}
</style>
