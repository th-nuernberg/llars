<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
  >
    <LCard
      :title="title"
      :subtitle="subtitle"
    >
      <template #actions>
        <v-spacer />
        <LBtn variant="cancel" @click="closeDialog">Abbrechen</LBtn>
        <LBtn variant="primary" :loading="saving" @click="saveAccess">Speichern</LBtn>
      </template>

      <v-skeleton-loader v-if="loading" type="paragraph@2, list-item" />
      <div v-else>
        <div class="section-label mt-2">
          <LIcon size="16" class="mr-1">mdi-account-multiple-plus</LIcon>
          Nutzer hinzufuegen
        </div>
        <div v-if="shareUsernames.length > 0" class="invited-users mb-2">
          <LTag
            v-for="user in shareUsernames"
            :key="user"
            variant="primary"
            closable
            @close="removeShareUser(user)"
          >
            {{ user }}
          </LTag>
        </div>
        <LUserSearch
          ref="userSearchRef"
          :exclude-usernames="shareUsernames"
          placeholder="Nutzernamen eingeben..."
          @select="addShareUser"
        />
      </div>
    </LCard>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  collection: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'saved', 'error'])

const loading = ref(false)
const saving = ref(false)
const shareUsernames = ref([])
const shareRoleNames = ref([])
const userSearchRef = ref(null)

const title = computed(() => 'Collection teilen')
const subtitle = computed(() => {
  if (!props.collection) return ''
  return props.collection.display_name || props.collection.name || ''
})

const closeDialog = () => {
  emit('update:modelValue', false)
}

const loadAccess = async () => {
  if (!props.collection?.id) return
  loading.value = true
  try {
    const response = await axios.get(`/api/rag/collections/${props.collection.id}/access`)
    if (response.data.success) {
      shareUsernames.value = (response.data.users || []).map(user => user.target)
      shareRoleNames.value = (response.data.roles || []).map(role => role.target)
    }
  } catch (error) {
    emit('error', 'Fehler beim Laden der Zugriffsrechte')
    console.error('Error loading collection access:', error)
  } finally {
    loading.value = false
  }
}

const addShareUser = (user) => {
  if (!user?.username) return
  const username = user.username
  if (!shareUsernames.value.includes(username)) {
    shareUsernames.value.push(username)
  }
  userSearchRef.value?.reset?.()
}

const removeShareUser = (username) => {
  shareUsernames.value = shareUsernames.value.filter(u => u !== username)
}

const saveAccess = async () => {
  if (!props.collection?.id) return
  saving.value = true
  try {
    const response = await axios.put(`/api/rag/collections/${props.collection.id}/access`, {
      usernames: shareUsernames.value,
      role_names: shareRoleNames.value
    })
    if (response.data.success) {
      emit('saved', response.data)
      emit('update:modelValue', false)
    }
  } catch (error) {
    emit('error', 'Fehler beim Speichern der Zugriffsrechte')
    console.error('Error saving collection access:', error)
  } finally {
    saving.value = false
  }
}

watch(
  () => props.modelValue,
  (value) => {
    if (value) {
      loadAccess()
    } else {
      shareUsernames.value = []
      shareRoleNames.value = []
    }
  }
)

watch(
  () => props.collection?.id,
  () => {
    if (props.modelValue) {
      loadAccess()
    }
  }
)
</script>
