<template>
  <v-dialog v-model="dialog" max-width="500px" persistent>
    <v-card>
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-h5">
          <v-icon class="mr-2">mdi-account-cog</v-icon>
          Profil & Einstellungen
        </span>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        ></v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-6">
        <!-- Profile Section -->
        <div class="mb-6">
          <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
            <v-icon class="mr-2">mdi-account</v-icon>
            Mein Profil
          </h3>

          <v-card variant="outlined" class="pa-4">
            <div class="profile-section">
              <LAvatar
                :seed="avatarSeed"
                :username="username"
                size="xl"
                class="mr-4"
              />
              <div class="profile-info">
                <div class="text-h6">{{ username || 'Nicht angemeldet' }}</div>
                <div class="text-body-2 text-medium-emphasis">
                  {{ userEmail || 'Keine E-Mail hinterlegt' }}
                </div>
                <LTag
                  v-if="isAdmin"
                  variant="danger"
                  size="sm"
                  prepend-icon="mdi-shield-account"
                  class="mt-2"
                >
                  Administrator
                </LTag>
                <LTag
                  v-else-if="username"
                  variant="primary"
                  size="sm"
                  class="mt-2"
                >
                  Benutzer
                </LTag>
              </div>
            </div>
          </v-card>
        </div>

        <!-- Theme Settings Section -->
        <div class="mb-6">
          <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
            <v-icon class="mr-2">mdi-palette</v-icon>
            Design & Darstellung
          </h3>

          <v-card variant="outlined" class="pa-4">
            <div class="mb-3">
              <div class="text-body-2 text-medium-emphasis mb-2">Farbmodus</div>
              <v-chip-group
                v-model="selectedTheme"
                column
                mandatory
                selected-class="text-primary"
              >
                <v-chip
                  v-for="option in themeOptions"
                  :key="option.value"
                  :value="option.value"
                  variant="outlined"
                  class="theme-chip"
                  @click="changeTheme(option.value)"
                >
                  <v-icon :icon="option.icon" start></v-icon>
                  {{ option.title }}
                </v-chip>
              </v-chip-group>
            </div>

            <!-- Current Theme Preview -->
            <v-alert
              v-if="currentThemeOption"
              :icon="currentThemeOption.icon"
              variant="tonal"
              color="primary"
              class="mt-3"
            >
              <div class="text-caption">
                Aktuell: <strong>{{ currentThemeOption.title }}</strong>
                <span v-if="themePreference === 'system'">
                  ({{ systemPrefersDark ? 'Dunkel' : 'Hell' }})
                </span>
              </div>
            </v-alert>
          </v-card>
        </div>

        <!-- Additional Settings Section (Placeholder) -->
        <div class="mb-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
            <v-icon class="mr-2">mdi-account-cog</v-icon>
            Weitere Einstellungen
          </h3>

          <v-card variant="outlined" class="pa-4">
            <v-list lines="two" density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon>mdi-bell</v-icon>
                </template>
                <v-list-item-title>Benachrichtigungen</v-list-item-title>
                <v-list-item-subtitle>Systembenachrichtigungen aktivieren</v-list-item-subtitle>
                <template v-slot:append>
                  <v-switch
                    v-model="notificationsEnabled"
                    color="primary"
                    hide-details
                    inset
                  ></v-switch>
                </template>
              </v-list-item>

              <v-divider class="my-2"></v-divider>

              <v-list-item>
                <template v-slot:prepend>
                  <v-icon>mdi-translate</v-icon>
                </template>
                <v-list-item-title>Sprache</v-list-item-title>
                <v-list-item-subtitle>Deutsch (DE)</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card>
        </div>

        <!-- Info Section -->
        <v-alert
          variant="outlined"
          color="info"
          icon="mdi-information"
          class="text-caption"
        >
          Einstellungen werden lokal in Ihrem Browser gespeichert.
        </v-alert>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <LBtn
          variant="primary"
          prepend-icon="mdi-check"
          @click="closeDialog"
        >
          Fertig
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAppTheme } from '@/composables/useAppTheme'
import { useAuth } from '@/composables/useAuth'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue'])

// Use composables
const {
  themePreference,
  themeOptions,
  currentThemeOption,
  systemPrefersDark,
  setThemePreference,
} = useAppTheme()

const auth = useAuth()

// User profile data
const username = computed(() => {
  try {
    return localStorage.getItem('username') || auth.tokenParsed.value?.preferred_username || ''
  } catch {
    return ''
  }
})

const avatarSeed = computed(() => auth.avatarSeed.value)
const userEmail = computed(() => auth.tokenParsed.value?.email || '')
const isAdmin = computed(() => auth.isAdmin.value)

// Dialog state
const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Local state
const selectedTheme = ref(themePreference.value)
const notificationsEnabled = ref(
  localStorage.getItem('llars-notifications-enabled') === 'true'
)

// Watch for theme preference changes from outside
watch(themePreference, (newValue) => {
  selectedTheme.value = newValue
})

// Watch for notifications toggle
watch(notificationsEnabled, (newValue) => {
  localStorage.setItem('llars-notifications-enabled', String(newValue))
  // TODO: Implement actual notification handling
})

// Methods
function changeTheme(theme) {
  setThemePreference(theme)
}

function closeDialog() {
  dialog.value = false
}
</script>

<style scoped>
/* Profile Section */
.profile-section {
  display: flex;
  align-items: center;
}

.profile-info {
  flex: 1;
}

.theme-chip {
  flex: 1;
  justify-content: center;
  min-width: 120px;
  font-weight: 500;
}

.v-chip-group {
  gap: 8px;
}

.text-medium-emphasis {
  opacity: 0.7;
}

/* Animation for dialog */
.v-dialog {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Card styling */
.v-card {
  border-radius: 12px;
}

.v-card-title {
  background-color: rgb(var(--v-theme-surface-light));
  padding: 16px 24px;
}
</style>
