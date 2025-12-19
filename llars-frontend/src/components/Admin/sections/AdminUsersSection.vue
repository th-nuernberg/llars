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
      <v-col cols="12" md="3">
        <LBtn variant="primary" @click="openCreateDialog" block prepend-icon="mdi-account-plus">
          Neuer Benutzer
        </LBtn>
      </v-col>
    </v-row>

    <!-- User Details Card (when user is selected) -->
    <v-expand-transition>
      <v-card v-if="selectedUser" class="mb-4" elevation="3">
        <v-card-title class="d-flex align-center">
          <LAvatar
            :seed="selectedUser.avatar_seed"
            :username="selectedUser.username"
            size="lg"
            class="mr-3"
          />
          <div>
            <div class="text-h6">{{ selectedUser.username }}</div>
            <div class="text-caption text-medium-emphasis">Benutzerdetails</div>
          </div>
          <v-spacer></v-spacer>
          <LTag
            v-if="selectedUserStatus"
            :variant="selectedUserStatus.variant"
            size="sm"
            class="mr-2"
          >
            {{ selectedUserStatus.label }}
          </LTag>
          <LIconBtn
            v-if="selectedUser.db_record_exists"
            :icon="selectedUser.is_active ? 'mdi-lock' : 'mdi-lock-open-variant'"
            :tooltip="selectedUser.is_active ? 'Sperren' : 'Entsperren'"
            :loading="togglingUser === selectedUser.username"
            :disabled="selectedUser.username === 'admin' || selectedUser.deleted_at"
            @click="toggleUserLock(selectedUser)"
          />
          <LIconBtn
            v-if="selectedUser.db_record_exists"
            icon="mdi-delete"
            tooltip="Löschen"
            variant="error"
            :disabled="selectedUser.username === 'admin'"
            @click="confirmDelete(selectedUser)"
          />
          <LIconBtn icon="mdi-close" @click="selectedUser = null" />
        </v-card-title>

        <v-divider></v-divider>

        <v-card-text>
          <v-alert
            v-if="selectedUser && !selectedUser.db_record_exists"
            type="warning"
            variant="tonal"
            class="mb-4"
          >
            Dieser Benutzer ist noch nicht in der LLARS-Datenbank angelegt. Rollen können bereits verwaltet werden,
            aber Sperren/Löschen ist erst nach dem Anlegen möglich.
            <div class="mt-3">
              <LBtn
                variant="primary"
                size="small"
                prepend-icon="mdi-account-plus"
                @click="openCreateDialog(selectedUser.username)"
              >
                In DB anlegen
              </LBtn>
            </div>
          </v-alert>

          <v-row>
            <!-- Roles Section -->
            <v-col cols="12" md="6">
              <h4 class="text-subtitle-1 font-weight-bold mb-3">
                <v-icon class="mr-1">mdi-shield-account</v-icon>
                Zugewiesene Rollen
              </h4>
              <div class="d-flex flex-wrap gap-2 mb-3">
                <LTag
                  v-for="role in selectedUser.roles"
                  :key="role.id"
                  variant="primary"
                  size="sm"
                  closable
                  @close="unassignRole(role.role_name)"
                >
                  {{ role.display_name }}
                </LTag>
                <LTag v-if="selectedUser.roles.length === 0" variant="gray" size="sm">
                  Keine Rollen zugewiesen
                </LTag>
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
                <LTag
                  v-for="perm in selectedUser.permissions.slice(0, showAllPermissions ? undefined : 8)"
                  :key="perm"
                  variant="info"
                  size="sm"
                  class="ma-1"
                >
                  {{ perm }}
                </LTag>
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
        Benutzer
        <v-spacer></v-spacer>
        <LBtn variant="text" @click="loadUsers" :loading="loadingUsers" prepend-icon="mdi-refresh">
          Aktualisieren
        </LBtn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text>
        <v-skeleton-loader v-if="isLoading('table')" type="table"></v-skeleton-loader>
        <v-data-table
          v-else
          :headers="headers"
          :items="filteredUsers"
          :loading="loadingUsers"
          :items-per-page="10"
          class="elevation-0"
        >
          <template v-slot:item.username="{ item }">
            <div class="d-flex align-center">
              <LAvatar
                :seed="item.avatar_seed"
                :username="item.username"
                size="sm"
                class="mr-2"
              />
              <span class="font-weight-medium">{{ item.username }}</span>
            </div>
          </template>

          <template v-slot:item.status="{ item }">
            <LTag :variant="getStatusVariant(item)" size="sm">
              {{ getStatusLabel(item) }}
            </LTag>
          </template>

          <template v-slot:item.roles="{ item }">
            <LTag
              v-for="role in item.roles"
              :key="role.id"
              size="sm"
              :variant="getRoleVariant(role.role_name)"
              class="ma-1"
            >
              {{ role.display_name }}
            </LTag>
            <span v-if="item.roles.length === 0" class="text-medium-emphasis">-</span>
          </template>

          <template v-slot:item.actions="{ item }">
            <LActionGroup
              :actions="getUserActions(item)"
              @action="(key) => handleUserAction(key, item)"
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

    <!-- Create User Dialog -->
    <v-dialog v-model="createDialog" max-width="560">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Benutzer anlegen
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="createDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-text-field
            v-model="newUserUsername"
            label="Username"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-account"
            :disabled="creatingUser"
          />
          <v-select
            v-model="newUserRoles"
            :items="allRoles"
            item-title="display_name"
            item-value="role_name"
            label="Initiale Rollen"
            variant="outlined"
            density="comfortable"
            multiple
            chips
            clearable
            :disabled="creatingUser"
          />
          <v-switch
            v-model="newUserActive"
            color="success"
            inset
            label="Account aktiv"
            :disabled="creatingUser"
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="createDialog = false" :disabled="creatingUser">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            prepend-icon="mdi-check"
            @click="createUser"
            :loading="creatingUser"
            :disabled="!newUserUsername"
          >
            Anlegen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirm Dialog -->
    <v-dialog v-model="deleteDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          Benutzer löschen
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="deleteDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          Möchtest du den Benutzer <strong>{{ userToDelete?.username }}</strong> wirklich löschen?
          <div class="text-caption text-medium-emphasis mt-2">
            Der Account wird in LLARS deaktiviert und aus Rollen/Berechtigungen entfernt.
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="deleteDialog = false" :disabled="deletingUser">Abbrechen</LBtn>
          <LBtn
            variant="error"
            prepend-icon="mdi-delete"
            @click="deleteUser"
            :loading="deletingUser"
            :disabled="!userToDelete"
          >
            Löschen
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';

// State
const searchQuery = ref('');
const roleFilter = ref(null);
const selectedUser = ref(null);
const roleToAssign = ref(null);
const showAllPermissions = ref(false);
const users = ref([]);
const allRoles = ref([]);
const createDialog = ref(false);
const deleteDialog = ref(false);
const userToDelete = ref(null);
const newUserUsername = ref('');
const newUserRoles = ref([]);
const newUserActive = ref(true);

// Loading states
const loadingSearch = ref(false);
const loadingUsers = ref(false);
const loadingUser = ref(null);
const assigningRole = ref(false);
const creatingUser = ref(false);
const deletingUser = ref(false);
const togglingUser = ref(null);
const { isLoading, withLoading } = useSkeletonLoading(['table']);

// Table headers
const headers = [
  { title: 'Benutzer', key: 'username', sortable: true },
  { title: 'Status', key: 'status', sortable: false },
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

const getRoleVariant = (roleName) => {
  const variants = {
    'admin': 'danger',
    'researcher': 'primary',
    'viewer': 'info'
  };
  return variants[roleName] || 'gray';
};

const getStatusLabel = (user) => {
  if (user.deleted_at) return 'Gelöscht';
  return user.is_active ? 'Aktiv' : 'Gesperrt';
};

const getStatusColor = (user) => {
  if (user.deleted_at) return 'grey';
  return user.is_active ? 'success' : 'warning';
};

const getStatusVariant = (user) => {
  if (user.deleted_at) return 'gray';
  return user.is_active ? 'success' : 'warning';
};

const selectedUserStatus = computed(() => {
  if (!selectedUser.value) return null;
  if (!selectedUser.value.db_record_exists) return { label: 'Nicht angelegt', variant: 'warning' };
  return {
    label: getStatusLabel(selectedUser.value),
    variant: getStatusVariant(selectedUser.value),
  };
});

// Get actions for user row
const getUserActions = (user) => {
  return [
    {
      key: 'edit',
      icon: 'mdi-pencil',
      tooltip: 'Bearbeiten',
      loading: loadingUser.value === user.username
    },
    {
      key: 'toggle-lock',
      icon: user.is_active ? 'mdi-lock' : 'mdi-lock-open-variant',
      tooltip: user.is_active ? 'Sperren' : 'Entsperren',
      variant: user.is_active ? 'warning' : 'success',
      loading: togglingUser.value === user.username,
      disabled: user.username === 'admin' || user.deleted_at
    },
    {
      key: 'delete',
      icon: 'mdi-delete',
      tooltip: 'Löschen',
      variant: 'danger',
      disabled: user.username === 'admin'
    }
  ];
};

// Handle action group clicks
const handleUserAction = (actionKey, user) => {
  switch (actionKey) {
    case 'edit':
      selectUser(user.username);
      break;
    case 'toggle-lock':
      toggleUserLock(user);
      break;
    case 'delete':
      confirmDelete(user);
      break;
  }
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

// Load all users
const loadUsers = async () => {
  loadingUsers.value = true;
  await withLoading('table', async () => {
    try {
      const response = await axios.get('/api/admin/users');
      users.value = response.data.users || [];
    } catch (error) {
      console.error('Error loading users:', error);
      users.value = [];
    }
  });
  loadingUsers.value = false;
};

// Search for a specific user
const searchUser = async () => {
  try {
    if (!searchQuery.value) return;
    loadingSearch.value = true;
    await selectUser(searchQuery.value);
  } catch (error) {
    console.error('Error searching user:', error);
    selectedUser.value = null;
  } finally {
    loadingSearch.value = false;
  }
};

// Select user for editing
const selectUser = async (username) => {
  loadingUser.value = username;
  try {
    const [permResponse, metaResponse] = await Promise.all([
      axios.get(`/api/permissions/user/${encodeURIComponent(username)}`),
      axios.get(`/api/admin/users?q=${encodeURIComponent(username)}&include_deleted=true`),
    ]);

    const metaUsers = metaResponse.data.users || [];
    const meta = metaUsers.find(u => u.username === username) || null;
    selectedUser.value = {
      ...permResponse.data,
      ...(meta || {}),
      db_record_exists: Boolean(meta && meta.id),
    };
    showAllPermissions.value = false;
    roleToAssign.value = null;

    // Ensure user appears in table (if present in DB)
    if (meta && meta.id) {
      const existingIndex = users.value.findIndex(u => u.username === username);
      if (existingIndex === -1) {
        users.value.unshift(meta);
      } else {
        users.value[existingIndex] = { ...users.value[existingIndex], ...meta };
      }
    }
  } catch (error) {
    console.error('Error loading user:', error);
  }
  loadingUser.value = null;
};

const openCreateDialog = (prefillUsername = '') => {
  newUserUsername.value = prefillUsername || '';
  newUserActive.value = true;
  newUserRoles.value = [];

  if (prefillUsername && selectedUser.value?.roles?.length) {
    newUserRoles.value = selectedUser.value.roles.map(r => r.role_name);
  }

  createDialog.value = true;
};

const createUser = async () => {
  if (!newUserUsername.value) return;
  creatingUser.value = true;
  try {
    await axios.post('/api/admin/users', {
      username: newUserUsername.value,
      is_active: newUserActive.value,
      role_names: newUserRoles.value,
    });
    createDialog.value = false;
    await loadUsers();
    if (selectedUser.value?.username === newUserUsername.value) {
      await selectUser(newUserUsername.value);
    }
  } catch (error) {
    console.error('Error creating user:', error);
  } finally {
    creatingUser.value = false;
  }
};

const toggleUserLock = async (user) => {
  if (!user?.username || user.username === 'admin') return;
  togglingUser.value = user.username;
  try {
    const desiredActive = !user.is_active;
    const response = await axios.patch(`/api/admin/users/${encodeURIComponent(user.username)}`, {
      is_active: desiredActive,
    });

    const updated = response.data.user;
    const idx = users.value.findIndex(u => u.username === user.username);
    if (idx !== -1) users.value[idx] = { ...users.value[idx], ...updated };
    if (selectedUser.value?.username === user.username) {
      selectedUser.value = { ...selectedUser.value, ...updated };
    }
  } catch (error) {
    console.error('Error toggling user lock:', error);
  } finally {
    togglingUser.value = null;
  }
};

const confirmDelete = (user) => {
  if (!user?.username || user.username === 'admin') return;
  userToDelete.value = user;
  deleteDialog.value = true;
};

const deleteUser = async () => {
  if (!userToDelete.value?.username) return;
  deletingUser.value = true;
  try {
    await axios.delete(`/api/admin/users/${encodeURIComponent(userToDelete.value.username)}`);
    users.value = users.value.filter(u => u.username !== userToDelete.value.username);
    if (selectedUser.value?.username === userToDelete.value.username) {
      selectedUser.value = null;
    }
    deleteDialog.value = false;
    userToDelete.value = null;
  } catch (error) {
    console.error('Error deleting user:', error);
  } finally {
    deletingUser.value = false;
  }
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
    await loadUsers();
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
    await loadUsers();
  } catch (error) {
    console.error('Error unassigning role:', error);
  }
};

onMounted(() => {
  loadRoles();
  loadUsers();
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
