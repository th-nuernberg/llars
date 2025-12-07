<template>
  <div class="admin-users">
    <!-- Search and Filter Row -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="searchQuery"
          label="Benutzer suchen"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
          @keyup.enter="searchUser"
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="roleFilter"
          :items="roleFilterOptions"
          label="Nach Rolle filtern"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <LBtn variant="primary" @click="searchUser" :loading="loadingSearch" block prepend-icon="mdi-magnify">
          Suchen
        </LBtn>
      </v-col>
    </v-row>

    <!-- User Details Card (when user is selected) -->
    <v-expand-transition>
      <v-card v-if="selectedUser" class="mb-4" elevation="3">
        <v-card-title class="d-flex align-center">
          <v-avatar color="primary" class="mr-3">
            <v-icon>mdi-account</v-icon>
          </v-avatar>
          <div>
            <div class="text-h6">{{ selectedUser.username }}</div>
            <div class="text-caption text-medium-emphasis">Benutzerdetails</div>
          </div>
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="selectedUser = null" />
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text>
          <v-row>
            <!-- Roles Section -->
            <v-col cols="12" md="6">
              <h4 class="text-subtitle-1 font-weight-bold mb-3">
                <v-icon class="mr-1">mdi-shield-account</v-icon>
                Zugewiesene Rollen
              </h4>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <v-chip
                  v-for="role in selectedUser.roles"
                  :key="role.id"
                  color="primary"
                  variant="flat"
                  closable
                  @click:close="unassignRole(role.role_name)"
                >
                  {{ role.display_name }}
                </v-chip>
                <v-chip v-if="selectedUser.roles.length === 0" variant="outlined">
                  Keine Rollen zugewiesen
                </v-chip>
              </div>

              <!-- Add Role -->
              <div class="d-flex align-center gap-2">
                <v-select
                  v-model="roleToAssign"
                  :items="availableRoles"
                  item-title="display_name"
                  item-value="role_name"
                  label="Rolle hinzufügen"
                  variant="outlined"
                  density="compact"
                  hide-details
                  style="max-width: 250px;"
                ></v-select>
                <LIconBtn
                  icon="mdi-plus"
                  variant="success"
                  :disabled="!roleToAssign"
                  @click="assignRole"
                  :loading="assigningRole"
                  size="default"
                />
              </div>
            </v-col>

            <!-- Permissions Section -->
            <v-col cols="12" md="6">
              <h4 class="text-subtitle-1 font-weight-bold mb-3">
                <v-icon class="mr-1">mdi-key</v-icon>
                Effektive Berechtigungen ({{ selectedUser.permissions.length }})
              </h4>
              <div class="permissions-list">
                <v-chip
                  v-for="perm in selectedUser.permissions.slice(0, showAllPermissions ? undefined : 8)"
                  :key="perm"
                  size="small"
                  variant="tonal"
                  class="ma-1"
                >
                  {{ perm }}
                </v-chip>
                <LBtn
                  v-if="selectedUser.permissions.length > 8"
                  variant="text"
                  size="small"
                  @click="showAllPermissions = !showAllPermissions"
                >
                  {{ showAllPermissions ? 'Weniger anzeigen' : `+${selectedUser.permissions.length - 8} mehr` }}
                </LBtn>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </v-expand-transition>

    <!-- Users Table -->
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-account-group</v-icon>
        Benutzer mit Rollen
        <v-spacer></v-spacer>
        <LBtn variant="text" @click="loadAllUsersWithRoles" :loading="loadingUsers" prepend-icon="mdi-refresh">
          Aktualisieren
        </LBtn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="filteredUsers"
          :loading="loadingUsers"
          :items-per-page="10"
          class="elevation-0"
        >
          <template v-slot:item.username="{ item }">
            <div class="d-flex align-center">
              <v-avatar size="32" color="primary" class="mr-2">
                <span class="text-caption">{{ item.username.charAt(0).toUpperCase() }}</span>
              </v-avatar>
              <span class="font-weight-medium">{{ item.username }}</span>
            </div>
          </template>

          <template v-slot:item.roles="{ item }">
            <v-chip
              v-for="role in item.roles"
              :key="role.id"
              size="small"
              :color="getRoleColor(role.role_name)"
              class="ma-1"
            >
              {{ role.display_name }}
            </v-chip>
            <span v-if="item.roles.length === 0" class="text-medium-emphasis">-</span>
          </template>

          <template v-slot:item.actions="{ item }">
            <LIconBtn
              icon="mdi-pencil"
              tooltip="Bearbeiten"
              @click="selectUser(item.username)"
              :loading="loadingUser === item.username"
            />
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8">
              <v-icon size="48" class="mb-2 text-medium-emphasis">mdi-account-search</v-icon>
              <div class="text-medium-emphasis">
                {{ searchQuery ? 'Keine Benutzer gefunden' : 'Suchen Sie nach einem Benutzer oder laden Sie alle Benutzer mit Rollen' }}
              </div>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// State
const searchQuery = ref('');
const roleFilter = ref(null);
const selectedUser = ref(null);
const roleToAssign = ref(null);
const showAllPermissions = ref(false);
const users = ref([]);
const allRoles = ref([]);

// Loading states
const loadingSearch = ref(false);
const loadingUsers = ref(false);
const loadingUser = ref(null);
const assigningRole = ref(false);

// Table headers
const headers = [
  { title: 'Benutzer', key: 'username', sortable: true },
  { title: 'Rollen', key: 'roles', sortable: false },
  { title: 'Aktionen', key: 'actions', sortable: false, align: 'end' },
];

// Role filter options
const roleFilterOptions = computed(() => {
  return ['Alle', ...allRoles.value.map(r => r.display_name)];
});

// Available roles for assignment (exclude already assigned)
const availableRoles = computed(() => {
  if (!selectedUser.value) return allRoles.value;
  const assignedRoleNames = selectedUser.value.roles.map(r => r.role_name);
  return allRoles.value.filter(r => !assignedRoleNames.includes(r.role_name));
});

// Filtered users based on role filter
const filteredUsers = computed(() => {
  if (!roleFilter.value || roleFilter.value === 'Alle') return users.value;
  return users.value.filter(u =>
    u.roles.some(r => r.display_name === roleFilter.value)
  );
});

// Get role color
const getRoleColor = (roleName) => {
  const colors = {
    'admin': 'error',
    'researcher': 'primary',
    'viewer': 'info'
  };
  return colors[roleName] || 'grey';
};

// Load all roles
const loadRoles = async () => {
  try {
    const response = await axios.get('/api/permissions/roles');
    allRoles.value = response.data.roles || [];
  } catch (error) {
    console.error('Error loading roles:', error);
  }
};

// Load all users with roles
const loadAllUsersWithRoles = async () => {
  loadingUsers.value = true;
  try {
    const response = await axios.get('/api/permissions/users-with-roles');
    users.value = response.data.users || [];
  } catch (error) {
    console.error('Error loading users:', error);
    // Fallback: Try to get from user_roles table
    users.value = [];
  }
  loadingUsers.value = false;
};

// Search for a specific user
const searchUser = async () => {
  if (!searchQuery.value) return;

  loadingSearch.value = true;
  try {
    const response = await axios.get(`/api/permissions/user/${searchQuery.value}`);
    selectedUser.value = response.data;
    showAllPermissions.value = false;

    // Add to users list if not already there
    const existingIndex = users.value.findIndex(u => u.username === response.data.username);
    if (existingIndex === -1) {
      users.value.unshift({
        username: response.data.username,
        roles: response.data.roles
      });
    }
  } catch (error) {
    console.error('Error searching user:', error);
    selectedUser.value = null;
  }
  loadingSearch.value = false;
};

// Select user for editing
const selectUser = async (username) => {
  loadingUser.value = username;
  try {
    const response = await axios.get(`/api/permissions/user/${username}`);
    selectedUser.value = response.data;
    showAllPermissions.value = false;
    roleToAssign.value = null;
  } catch (error) {
    console.error('Error loading user:', error);
  }
  loadingUser.value = null;
};

// Assign role to user
const assignRole = async () => {
  if (!selectedUser.value || !roleToAssign.value) return;

  assigningRole.value = true;
  try {
    await axios.post('/api/permissions/assign-role', {
      username: selectedUser.value.username,
      role_name: roleToAssign.value
    });

    // Reload user data
    await selectUser(selectedUser.value.username);
    await loadAllUsersWithRoles();
    roleToAssign.value = null;
  } catch (error) {
    console.error('Error assigning role:', error);
  }
  assigningRole.value = false;
};

// Unassign role from user
const unassignRole = async (roleName) => {
  if (!selectedUser.value) return;

  try {
    await axios.post('/api/permissions/unassign-role', {
      username: selectedUser.value.username,
      role_name: roleName
    });

    // Reload user data
    await selectUser(selectedUser.value.username);
    await loadAllUsersWithRoles();
  } catch (error) {
    console.error('Error unassigning role:', error);
  }
};

onMounted(() => {
  loadRoles();
  loadAllUsersWithRoles();
});
</script>

<style scoped>
.permissions-list {
  max-height: 200px;
  overflow-y: auto;
}

.gap-2 {
  gap: 8px;
}
</style>
