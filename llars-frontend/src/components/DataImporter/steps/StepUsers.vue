<template>
  <div class="step-users pa-6">
    <!-- User Selection -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-account-group</v-icon>
        Benutzer zuweisen
        <v-spacer />
        <v-chip color="primary" variant="tonal" size="small">
          {{ selectedCount }} ausgewählt
        </v-chip>
      </v-card-title>

      <v-card-text>
        <!-- Quick Actions -->
        <div class="d-flex flex-wrap gap-2 mb-4">
          <LBtn variant="text" size="small" @click="selectAllAsRaters">
            Alle als Rater
          </LBtn>
          <LBtn variant="text" size="small" @click="selectResearchersAsRaters">
            Researcher als Rater
          </LBtn>
          <LBtn variant="text" size="small" @click="clearSelection">
            Auswahl löschen
          </LBtn>
        </div>

        <!-- User List -->
        <v-table density="comfortable" hover>
          <thead>
            <tr>
              <th style="width: 50%">Benutzer</th>
              <th class="text-center">Rater</th>
              <th class="text-center">Viewer</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <div class="d-flex align-center">
                  <v-avatar size="32" color="primary" class="mr-2">
                    <span class="text-caption">{{ getInitials(user.name) }}</span>
                  </v-avatar>
                  <div>
                    <div class="font-weight-medium">{{ user.name }}</div>
                    <div class="text-caption text-medium-emphasis">{{ user.email }}</div>
                  </div>
                  <v-chip
                    v-if="user.role"
                    size="x-small"
                    variant="tonal"
                    class="ml-2"
                  >
                    {{ user.role }}
                  </v-chip>
                </div>
              </td>
              <td class="text-center">
                <v-checkbox
                  :model-value="localConfig.raters.includes(user.id)"
                  hide-details
                  density="compact"
                  color="primary"
                  @update:model-value="toggleRater(user.id, $event)"
                />
              </td>
              <td class="text-center">
                <v-checkbox
                  :model-value="localConfig.viewers.includes(user.id)"
                  hide-details
                  density="compact"
                  color="secondary"
                  @update:model-value="toggleViewer(user.id, $event)"
                />
              </td>
            </tr>
          </tbody>
        </v-table>

        <div v-if="!users.length" class="text-center text-medium-emphasis pa-6">
          <v-icon size="48" class="mb-2">mdi-account-off</v-icon>
          <div>Keine Benutzer verfügbar</div>
        </div>
      </v-card-text>
    </v-card>

    <!-- Distribution Preview -->
    <v-card v-if="localConfig.raters.length && scenarioConfig?.distributionMode !== 'all'" variant="outlined">
      <v-card-title>
        <v-icon class="mr-2">mdi-chart-pie</v-icon>
        Verteilungs-Vorschau
      </v-card-title>

      <v-card-text>
        <v-row>
          <v-col v-for="raterId in localConfig.raters" :key="raterId" cols="6" sm="4" md="3">
            <v-card variant="tonal" class="pa-3 text-center">
              <v-avatar size="40" color="primary" class="mb-2">
                <span>{{ getInitials(getUserName(raterId)) }}</span>
              </v-avatar>
              <div class="text-body-2 font-weight-medium text-truncate">
                {{ getUserName(raterId) }}
              </div>
              <div class="text-caption text-medium-emphasis">
                ~{{ threadsPerRater }} Threads
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Info Alert -->
    <v-alert
      v-if="localConfig.raters.length === 0"
      type="warning"
      variant="tonal"
      class="mt-4"
    >
      <v-icon class="mr-2">mdi-alert</v-icon>
      Mindestens ein Rater muss ausgewählt werden.
    </v-alert>

    <v-alert
      v-else
      type="info"
      variant="tonal"
      class="mt-4"
    >
      <div>
        <strong>{{ localConfig.raters.length }} Rater</strong> und
        <strong>{{ localConfig.viewers.length }} Viewer</strong> werden dem Szenario zugewiesen.
      </div>
    </v-alert>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  userConfig: {
    type: Object,
    required: true
  },
  session: {
    type: Object,
    default: null
  },
  scenarioConfig: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:userConfig'])

// Local copy
const localConfig = ref({ ...props.userConfig })

// Sync
watch(localConfig, (newVal) => {
  emit('update:userConfig', newVal)
}, { deep: true })

watch(() => props.userConfig, (newVal) => {
  localConfig.value = { ...newVal }
}, { deep: true })

const users = ref([])

const selectedCount = computed(() => {
  return localConfig.value.raters.length + localConfig.value.viewers.length
})

const itemCount = computed(() => {
  return props.session?.item_count ||
         props.session?.validation?.stats?.total_items ||
         0
})

const threadsPerRater = computed(() => {
  if (!localConfig.value.raters.length) return 0
  return Math.ceil(itemCount.value / localConfig.value.raters.length)
})

const getInitials = (name) => {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

const getUserName = (userId) => {
  const user = users.value.find(u => u.id === userId)
  return user?.name || 'Unbekannt'
}

const toggleRater = (userId, isSelected) => {
  if (isSelected) {
    if (!localConfig.value.raters.includes(userId)) {
      localConfig.value.raters.push(userId)
    }
    // Remove from viewers if added as rater
    const viewerIdx = localConfig.value.viewers.indexOf(userId)
    if (viewerIdx > -1) {
      localConfig.value.viewers.splice(viewerIdx, 1)
    }
  } else {
    const idx = localConfig.value.raters.indexOf(userId)
    if (idx > -1) {
      localConfig.value.raters.splice(idx, 1)
    }
  }
}

const toggleViewer = (userId, isSelected) => {
  if (isSelected) {
    if (!localConfig.value.viewers.includes(userId)) {
      localConfig.value.viewers.push(userId)
    }
    // Remove from raters if added as viewer
    const raterIdx = localConfig.value.raters.indexOf(userId)
    if (raterIdx > -1) {
      localConfig.value.raters.splice(raterIdx, 1)
    }
  } else {
    const idx = localConfig.value.viewers.indexOf(userId)
    if (idx > -1) {
      localConfig.value.viewers.splice(idx, 1)
    }
  }
}

const selectAllAsRaters = () => {
  localConfig.value.raters = users.value.map(u => u.id)
  localConfig.value.viewers = []
}

const selectResearchersAsRaters = () => {
  localConfig.value.raters = users.value
    .filter(u => u.role === 'researcher' || u.role === 'admin')
    .map(u => u.id)
}

const clearSelection = () => {
  localConfig.value.raters = []
  localConfig.value.viewers = []
}

onMounted(async () => {
  try {
    const response = await axios.get('/api/users')
    users.value = response.data.users || response.data || []
  } catch (err) {
    console.error('Failed to load users:', err)
  }
})
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
