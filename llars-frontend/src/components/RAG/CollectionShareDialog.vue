<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
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
        <!-- Collection Info -->
        <v-alert v-if="collection" type="info" variant="tonal" density="compact" class="mb-4">
          <div class="d-flex align-center">
            <LIcon size="16" class="mr-2">mdi-account</LIcon>
            <span class="text-body-2">
              Erstellt von: <strong>{{ collection.created_by || 'Unbekannt' }}</strong>
            </span>
          </div>
        </v-alert>

        <!-- Existing Users with Permissions -->
        <div v-if="shareUsers.length > 0" class="mb-4">
          <div class="section-label mb-2">
            <LIcon size="16" class="mr-1">mdi-account-check</LIcon>
            Aktuelle Berechtigungen
          </div>
          <v-list density="compact" class="bg-grey-lighten-4 rounded">
            <v-list-item
              v-for="user in shareUsers"
              :key="user.target"
              class="py-1"
            >
              <template #prepend>
                <v-avatar size="32" color="primary" class="mr-3">
                  <span class="text-white text-caption">{{ user.target.substring(0, 2).toUpperCase() }}</span>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2">{{ user.target }}</v-list-item-title>
              <v-list-item-subtitle class="text-caption">
                <span v-if="user.can_edit" class="text-success">Lesen & Schreiben</span>
                <span v-else class="text-info">Nur Lesen</span>
              </v-list-item-subtitle>
              <template #append>
                <v-btn-toggle
                  v-model="user.can_edit"
                  mandatory
                  density="compact"
                  color="primary"
                  class="mr-2"
                >
                  <v-btn :value="false" size="small" variant="tonal">
                    <LIcon size="16" class="mr-1">mdi-eye</LIcon>
                    Lesen
                  </v-btn>
                  <v-btn :value="true" size="small" variant="tonal">
                    <LIcon size="16" class="mr-1">mdi-pencil</LIcon>
                    Schreiben
                  </v-btn>
                </v-btn-toggle>
                <LIconBtn
                  icon="mdi-close"
                  size="small"
                  variant="text"
                  tooltip="Entfernen"
                  @click="removeShareUser(user.target)"
                />
              </template>
            </v-list-item>
          </v-list>
        </div>

        <!-- Add New User -->
        <div class="section-label mt-4 mb-2">
          <LIcon size="16" class="mr-1">mdi-account-plus</LIcon>
          Nutzer hinzufuegen
        </div>

        <!-- Permission level for new users -->
        <v-row class="mb-2" align="center">
          <v-col cols="12" md="8">
            <LUserSearch
              ref="userSearchRef"
              :exclude-usernames="existingUsernames"
              placeholder="Nutzernamen eingeben..."
              @select="addShareUser"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-btn-toggle
              v-model="newUserPermission"
              mandatory
              density="compact"
              color="primary"
              class="w-100"
            >
              <v-btn value="view" size="small" variant="tonal" class="flex-grow-1">
                <LIcon size="16" class="mr-1">mdi-eye</LIcon>
                Lesen
              </v-btn>
              <v-btn value="edit" size="small" variant="tonal" class="flex-grow-1">
                <LIcon size="16" class="mr-1">mdi-pencil</LIcon>
                Schreiben
              </v-btn>
            </v-btn-toggle>
          </v-col>
        </v-row>

        <v-alert v-if="chatbotRequiredUsers.length > 0" type="warning" variant="tonal" density="compact" class="mt-4">
          <div class="text-body-2">
            <strong>Hinweis:</strong> Die folgenden Nutzer haben Zugriff über geteilte Chatbots und können nicht entfernt werden:
          </div>
          <div class="mt-1">
            <v-chip
              v-for="user in chatbotRequiredUsers"
              :key="user"
              size="small"
              color="warning"
              variant="flat"
              class="mr-1 mt-1"
            >
              {{ user }}
            </v-chip>
          </div>
        </v-alert>
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
const shareUsers = ref([])  // Array of { target, can_view, can_edit, can_delete, can_share }
const shareRoleNames = ref([])
const chatbotRequiredUsers = ref([])
const userSearchRef = ref(null)
const newUserPermission = ref('view')  // Default permission for new users

const title = computed(() => 'Collection teilen')
const subtitle = computed(() => {
  if (!props.collection) return ''
  return props.collection.display_name || props.collection.name || ''
})

const existingUsernames = computed(() => shareUsers.value.map(u => u.target))

const closeDialog = () => {
  emit('update:modelValue', false)
}

const loadAccess = async () => {
  if (!props.collection?.id) return
  loading.value = true
  try {
    // Load current permissions
    const [accessResponse, requiredResponse] = await Promise.all([
      axios.get(`/api/rag/collections/${props.collection.id}/access`),
      axios.get(`/api/rag/collections/${props.collection.id}/access/required`).catch(() => ({ data: { users: [] } }))
    ])

    if (accessResponse.data.success) {
      // Transform users to include permission flags
      shareUsers.value = (accessResponse.data.users || []).map(user => ({
        target: user.target,
        can_view: user.can_view !== false,
        can_edit: user.can_edit === true,
        can_delete: user.can_delete === true,
        can_share: user.can_share === true
      }))
      shareRoleNames.value = (accessResponse.data.roles || []).map(role => role.target)
    }

    // Get chatbot-required users
    chatbotRequiredUsers.value = requiredResponse.data.users || []
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
  if (!existingUsernames.value.includes(username)) {
    shareUsers.value.push({
      target: username,
      can_view: true,
      can_edit: newUserPermission.value === 'edit',
      can_delete: false,
      can_share: false
    })
  }
  userSearchRef.value?.reset?.()
}

const removeShareUser = (username) => {
  // Check if user is required by chatbot
  if (chatbotRequiredUsers.value.includes(username)) {
    emit('error', `${username} kann nicht entfernt werden - Chatbot-Zugriff aktiv`)
    return
  }
  shareUsers.value = shareUsers.value.filter(u => u.target !== username)
}

const saveAccess = async () => {
  if (!props.collection?.id) return
  saving.value = true
  try {
    // Use batch API to set individual permissions per user
    const userPermissions = shareUsers.value.map(u => ({
      target: u.target,
      can_view: true,
      can_edit: u.can_edit,
      can_delete: false,
      can_share: false
    }))

    const response = await axios.put(`/api/rag/collections/${props.collection.id}/access`, {
      user_permissions: userPermissions,
      role_names: shareRoleNames.value
    })

    if (response.data.success) {
      emit('saved', { collection_id: props.collection.id, users: shareUsers.value })
      emit('update:modelValue', false)
    }
  } catch (error) {
    const errorMsg = error.response?.data?.error || 'Fehler beim Speichern der Zugriffsrechte'
    emit('error', errorMsg)
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
      shareUsers.value = []
      shareRoleNames.value = []
      chatbotRequiredUsers.value = []
      newUserPermission.value = 'view'
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

<style scoped>
.section-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
}
</style>
