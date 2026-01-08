<template>
  <div class="step-users pa-6">
    <!-- User Selection -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-account-group</LIcon>
        Benutzer einladen
        <v-spacer />
        <v-chip color="primary" variant="tonal" size="small">
          {{ selectedCount }} ausgewählt
        </v-chip>
      </v-card-title>

      <v-card-text>
        <!-- Loading -->
        <div v-if="loadingUsers" class="text-center pa-6">
          <v-progress-circular indeterminate color="primary" />
          <div class="text-caption mt-2">Lade Benutzer...</div>
        </div>

        <template v-else>
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
                <th class="text-center">Evaluator</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>
                  <div class="d-flex align-center">
                    <v-avatar
                      size="32"
                      color="primary"
                      class="mr-2"
                    >
                      <span class="text-caption">{{ getInitials(getDisplayName(user)) }}</span>
                    </v-avatar>
                    <div>
                      <div class="font-weight-medium">{{ getDisplayName(user) }}</div>
                      <div v-if="user.email" class="text-caption text-medium-emphasis">
                        {{ user.email }}
                      </div>
                    </div>
                    <v-chip
                      v-if="user.in_scenario"
                      size="x-small"
                      variant="tonal"
                      color="info"
                      class="ml-2"
                    >
                      {{ user.scenario_role }}
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
                    :model-value="localConfig.evaluators.includes(user.id)"
                    hide-details
                    density="compact"
                    color="secondary"
                    @update:model-value="toggleEvaluator(user.id, $event)"
                  />
                </td>
              </tr>
            </tbody>
          </v-table>

          <div v-if="!users.length" class="text-center text-medium-emphasis pa-6">
            <LIcon size="48" class="mb-2">mdi-account-off</LIcon>
            <div>Keine Benutzer verfügbar</div>
          </div>
        </template>
      </v-card-text>
    </v-card>

    <!-- Distribution Preview -->
    <v-card v-if="localConfig.raters.length && scenarioConfig?.distributionMode !== 'all'" variant="outlined">
      <v-card-title>
        <LIcon class="mr-2">mdi-chart-pie</LIcon>
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

    <!-- Role Explanation -->
    <v-alert
      type="info"
      variant="tonal"
      class="mt-4"
      density="compact"
    >
      <div class="text-body-2">
        <strong>Rater:</strong> Können Items im Szenario bewerten/ranken.<br>
        <strong>Evaluator:</strong> Können an Evaluationen teilnehmen und Ergebnisse sehen.
      </div>
    </v-alert>

    <!-- Selection Summary -->
    <v-alert
      v-if="localConfig.raters.length === 0 && localConfig.evaluators.length === 0"
      type="warning"
      variant="tonal"
      class="mt-4"
    >
      <LIcon class="mr-2">mdi-alert</LIcon>
      Mindestens ein Benutzer sollte ausgewählt werden (optional).
    </v-alert>

    <v-alert
      v-else
      type="success"
      variant="tonal"
      class="mt-4"
    >
      <div>
        <strong>{{ localConfig.raters.length }} Rater</strong> und
        <strong>{{ localConfig.evaluators.length }} Evaluatoren</strong> werden eingeladen.
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
  scenarioId: {
    type: Number,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:userConfig'])

// Local copy - ensure evaluators array exists
const localConfig = ref({
  raters: props.userConfig?.raters || [],
  evaluators: props.userConfig?.evaluators || props.userConfig?.viewers || []
})

// Sync
watch(localConfig, (newVal) => {
  emit('update:userConfig', newVal)
}, { deep: true })

watch(() => props.userConfig, (newVal) => {
  localConfig.value = {
    raters: newVal?.raters || [],
    evaluators: newVal?.evaluators || newVal?.viewers || []
  }
}, { deep: true })

const users = ref([])
const loadingUsers = ref(false)

const selectedCount = computed(() => {
  return localConfig.value.raters.length + localConfig.value.evaluators.length
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

const getDisplayName = (user) => {
  if (!user) return 'Unbekannt'
  return user.username || 'Unbekannt'
}

const getUserName = (userId) => {
  const user = users.value.find(u => u.id === userId)
  return getDisplayName(user)
}

const toggleRater = (userId, isSelected) => {
  if (isSelected) {
    if (!localConfig.value.raters.includes(userId)) {
      localConfig.value.raters.push(userId)
    }
    // Remove from evaluators if added as rater
    const evalIdx = localConfig.value.evaluators.indexOf(userId)
    if (evalIdx > -1) {
      localConfig.value.evaluators.splice(evalIdx, 1)
    }
  } else {
    const idx = localConfig.value.raters.indexOf(userId)
    if (idx > -1) {
      localConfig.value.raters.splice(idx, 1)
    }
  }
}

const toggleEvaluator = (userId, isSelected) => {
  if (isSelected) {
    if (!localConfig.value.evaluators.includes(userId)) {
      localConfig.value.evaluators.push(userId)
    }
    // Remove from raters if added as evaluator
    const raterIdx = localConfig.value.raters.indexOf(userId)
    if (raterIdx > -1) {
      localConfig.value.raters.splice(raterIdx, 1)
    }
  } else {
    const idx = localConfig.value.evaluators.indexOf(userId)
    if (idx > -1) {
      localConfig.value.evaluators.splice(idx, 1)
    }
  }
}

const selectAllAsRaters = () => {
  localConfig.value.raters = users.value.map(u => u.id)
  localConfig.value.evaluators = []
}

const selectResearchersAsRaters = () => {
  // Filter users by system role (researcher or admin should be raters)
  localConfig.value.raters = users.value
    .filter(u => !u.in_scenario)
    .map(u => u.id)
}

const clearSelection = () => {
  localConfig.value.raters = []
  localConfig.value.evaluators = []
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    // Use the new endpoint for available users
    const params = props.scenarioId ? { scenario_id: props.scenarioId } : {}
    const response = await axios.get('/api/admin/available_users_for_scenario', { params })
    users.value = response.data.users || []
  } catch (err) {
    console.error('Failed to load users:', err)
    // Fallback to general users endpoint
    try {
      const response = await axios.get('/api/users')
      users.value = (response.data.users || response.data || []).map(u => ({
        id: u.id,
        username: u.username || u.name,
        email: u.email,
        in_scenario: false
      }))
    } catch (fallbackErr) {
      console.error('Fallback also failed:', fallbackErr)
      users.value = []
    }
  } finally {
    loadingUsers.value = false
  }
}

onMounted(() => {
  loadUsers()
})

// Reload users if scenarioId changes
watch(() => props.scenarioId, () => {
  loadUsers()
})
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
