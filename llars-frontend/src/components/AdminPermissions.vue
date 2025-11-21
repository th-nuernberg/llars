<template>
  <v-container fluid class="admin-permissions">
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Berechtigungsverwaltung</h1>
      </v-col>
    </v-row>

    <!-- Permission denied message -->
    <v-row v-if="!hasPermission('admin:permissions:manage')">
      <v-col cols="12">
        <v-alert type="error" prominent>
          <v-icon large>mdi-lock</v-icon>
          Sie haben keine Berechtigung, diese Seite zu sehen. Erforderlich: admin:permissions:manage
        </v-alert>
      </v-col>
    </v-row>

    <!-- Admin content -->
    <div v-else>
      <!-- Tabs for different sections -->
      <v-tabs v-model="activeTab" bg-color="primary">
        <v-tab value="users">Benutzer</v-tab>
        <v-tab value="roles">Rollen</v-tab>
        <v-tab value="permissions">Berechtigungen</v-tab>
      </v-tabs>

      <v-card class="mt-4">
        <v-window v-model="activeTab">
          <!-- Users Tab -->
          <v-window-item value="users">
            <v-card-text>
              <h2 class="text-h5 mb-4">Benutzer & Rollen</h2>

              <!-- User search -->
              <v-text-field
                v-model="searchUsername"
                label="Benutzername suchen"
                prepend-icon="mdi-magnify"
                clearable
                @keyup.enter="loadUserPermissions"
              ></v-text-field>

              <v-btn color="primary" @click="loadUserPermissions" :loading="loadingUser">
                Benutzer laden
              </v-btn>

              <!-- User info card -->
              <v-card v-if="selectedUser" class="mt-4" elevation="2">
                <v-card-title>
                  <v-icon left>mdi-account</v-icon>
                  {{ selectedUser.username }}
                </v-card-title>

                <v-divider></v-divider>

                <!-- User roles -->
                <v-card-subtitle class="mt-4">
                  <strong>Zugewiesene Rollen:</strong>
                </v-card-subtitle>
                <v-card-text>
                  <v-chip
                    v-for="role in selectedUser.roles"
                    :key="role.id"
                    class="ma-1"
                    color="primary"
                    closable
                    @click:close="unassignRole(selectedUser.username, role.role_name)"
                  >
                    {{ role.display_name }}
                  </v-chip>

                  <div class="mt-2">
                    <v-select
                      v-model="selectedRoleToAssign"
                      :items="availableRolesToAssign"
                      item-title="display_name"
                      item-value="role_name"
                      label="Rolle zuweisen"
                      density="compact"
                      style="max-width: 300px"
                    ></v-select>
                    <v-btn
                      size="small"
                      color="success"
                      @click="assignRole(selectedUser.username, selectedRoleToAssign)"
                      :disabled="!selectedRoleToAssign"
                    >
                      Rolle zuweisen
                    </v-btn>
                  </div>
                </v-card-text>

                <v-divider></v-divider>

                <!-- User permissions -->
                <v-card-subtitle class="mt-4">
                  <strong>Berechtigungen ({{ selectedUser.permissions.length }}):</strong>
                </v-card-subtitle>
                <v-card-text>
                  <v-chip
                    v-for="permission in selectedUser.permissions"
                    :key="permission"
                    class="ma-1"
                    size="small"
                  >
                    {{ permission }}
                  </v-chip>
                </v-card-text>
              </v-card>
            </v-card-text>
          </v-window-item>

          <!-- Roles Tab -->
          <v-window-item value="roles">
            <v-card-text>
              <h2 class="text-h5 mb-4">Verfügbare Rollen</h2>

              <v-list>
                <v-list-item
                  v-for="role in allRoles"
                  :key="role.id"
                  :title="role.display_name"
                  :subtitle="role.description"
                >
                  <template v-slot:prepend>
                    <v-icon>mdi-shield-account</v-icon>
                  </template>

                  <template v-slot:append>
                    <v-chip size="small">{{ role.role_name }}</v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-window-item>

          <!-- Permissions Tab -->
          <v-window-item value="permissions">
            <v-card-text>
              <h2 class="text-h5 mb-4">Alle Berechtigungen</h2>

              <!-- Group permissions by category -->
              <div v-for="(perms, category) in permissionsByCategory" :key="category" class="mb-4">
                <h3 class="text-h6 mb-2">
                  <v-chip color="secondary" class="mr-2">{{ category }}</v-chip>
                </h3>

                <v-table density="compact">
                  <thead>
                    <tr>
                      <th>Permission Key</th>
                      <th>Anzeigename</th>
                      <th>Beschreibung</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="perm in perms" :key="perm.id">
                      <td><code>{{ perm.permission_key }}</code></td>
                      <td>{{ perm.display_name }}</td>
                      <td>{{ perm.description }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </v-card-text>
          </v-window-item>
        </v-window>
      </v-card>
    </div>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePermissions } from '@/composables/usePermissions'
import axios from 'axios'

const { hasPermission } = usePermissions()

// State
const activeTab = ref('users')
const searchUsername = ref('')
const selectedUser = ref(null)
const loadingUser = ref(false)
const allRoles = ref([])
const allPermissions = ref([])
const selectedRoleToAssign = ref(null)

const snackbar = ref({
  show: false,
  message: '',
  color: 'success'
})

// Computed
const permissionsByCategory = computed(() => {
  const grouped = {}
  allPermissions.value.forEach(perm => {
    const category = perm.category || 'other'
    if (!grouped[category]) {
      grouped[category] = []
    }
    grouped[category].push(perm)
  })
  return grouped
})

const availableRolesToAssign = computed(() => {
  if (!selectedUser.value) return allRoles.value

  const assignedRoleNames = selectedUser.value.roles.map(r => r.role_name)
  return allRoles.value.filter(role => !assignedRoleNames.includes(role.role_name))
})

// Methods
async function loadAllRoles() {
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
    const token = sessionStorage.getItem('keycloak_token')

    const response = await axios.get(`${baseUrl}/api/permissions/roles`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.data.success) {
      allRoles.value = response.data.roles
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Rollen', 'error')
    console.error('Failed to load roles:', error)
  }
}

async function loadAllPermissions() {
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
    const token = sessionStorage.getItem('keycloak_token')

    const response = await axios.get(`${baseUrl}/api/permissions`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    if (response.data.success) {
      allPermissions.value = response.data.permissions
    }
  } catch (error) {
    showSnackbar('Fehler beim Laden der Berechtigungen', 'error')
    console.error('Failed to load permissions:', error)
  }
}

async function loadUserPermissions() {
  if (!searchUsername.value) {
    showSnackbar('Bitte Benutzername eingeben', 'warning')
    return
  }

  loadingUser.value = true

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
    const token = sessionStorage.getItem('keycloak_token')

    const response = await axios.get(
      `${baseUrl}/api/permissions/user/${searchUsername.value}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    )

    if (response.data.success) {
      selectedUser.value = {
        username: response.data.username,
        permissions: response.data.permissions,
        roles: response.data.roles
      }
      showSnackbar(`Benutzer ${searchUsername.value} geladen`, 'success')
    }
  } catch (error) {
    if (error.response?.status === 404) {
      showSnackbar('Benutzer nicht gefunden', 'warning')
    } else {
      showSnackbar('Fehler beim Laden der Benutzerdaten', 'error')
    }
    console.error('Failed to load user permissions:', error)
    selectedUser.value = null
  } finally {
    loadingUser.value = false
  }
}

async function assignRole(username, roleName) {
  if (!roleName) return

  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
    const token = sessionStorage.getItem('keycloak_token')

    await axios.post(
      `${baseUrl}/api/permissions/assign-role`,
      { username, role_name: roleName },
      { headers: { 'Authorization': `Bearer ${token}` } }
    )

    showSnackbar(`Rolle erfolgreich zugewiesen`, 'success')
    selectedRoleToAssign.value = null
    await loadUserPermissions()
  } catch (error) {
    showSnackbar('Fehler beim Zuweisen der Rolle', 'error')
    console.error('Failed to assign role:', error)
  }
}

async function unassignRole(username, roleName) {
  try {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:80'
    const token = sessionStorage.getItem('keycloak_token')

    await axios.post(
      `${baseUrl}/api/permissions/unassign-role`,
      { username, role_name: roleName },
      { headers: { 'Authorization': `Bearer ${token}` } }
    )

    showSnackbar(`Rolle erfolgreich entfernt`, 'success')
    await loadUserPermissions()
  } catch (error) {
    showSnackbar('Fehler beim Entfernen der Rolle', 'error')
    console.error('Failed to unassign role:', error)
  }
}

function showSnackbar(message, color = 'success') {
  snackbar.value = {
    show: true,
    message,
    color
  }
}

// Lifecycle
onMounted(async () => {
  if (hasPermission('admin:permissions:manage')) {
    await Promise.all([
      loadAllRoles(),
      loadAllPermissions()
    ])
  }
})
</script>

<style scoped>
.admin-permissions {
  max-width: 1400px;
  margin: 0 auto;
}

code {
  background-color: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}
</style>
