<template>
  <div class="admin-users" :class="{ 'is-mobile': isMobile }">
    <!-- Search and Filter Row -->
    <v-row class="mb-4">
      <v-col cols="12" md="4">
        <v-text-field
          v-model="searchQuery"
          :label="$t('admin.users.searchPlaceholder')"
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
          :label="$t('admin.users.filterByRole')"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <LBtn variant="primary" @click="searchUser" :loading="loadingSearch" block prepend-icon="mdi-magnify">
          {{ $t('common.search') }}
        </LBtn>
      </v-col>
      <v-col cols="12" md="3">
        <LBtn variant="primary" @click="openCreateDialog" block prepend-icon="mdi-account-plus">
          {{ $t('admin.users.newUser') }}
        </LBtn>
      </v-col>
    </v-row>

    <!-- User Details Card (when user is selected) -->
    <v-expand-transition>
      <v-card v-if="selectedUser" class="mb-4" elevation="3">
        <v-card-title class="d-flex align-center">
          <LAvatar
            :seed="selectedUser.avatar_seed"
            :src="selectedUser.avatar_url"
            :username="selectedUser.username"
            size="lg"
            class="mr-3"
          />
          <div>
            <div class="text-h6">{{ selectedUser.username }}</div>
            <div class="text-caption text-medium-emphasis">{{ $t('admin.users.userDetails') }}</div>
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
            :icon="selectedUser.is_active ? 'mdi-lock-open-variant' : 'mdi-lock'"
            :tooltip="selectedUser.is_active ? $t('admin.users.actions.lock') : $t('admin.users.actions.unlock')"
            :loading="togglingUser === selectedUser.username"
            :disabled="selectedUser.username === 'admin' || selectedUser.deleted_at"
            @click="toggleUserLock(selectedUser)"
          />
          <LIconBtn
            v-if="selectedUser.db_record_exists"
            icon="mdi-delete"
            :tooltip="$t('admin.users.actions.delete')"
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
            {{ $t('admin.users.notInDbWarning') }}
            <div class="mt-3">
              <LBtn
                variant="primary"
                size="small"
                prepend-icon="mdi-account-plus"
                @click="openCreateDialog(selectedUser.username)"
              >
                {{ $t('admin.users.createInDb') }}
              </LBtn>
            </div>
          </v-alert>

          <v-row>
            <!-- Roles Section -->
            <v-col cols="12" md="6">
              <h4 class="text-subtitle-1 font-weight-bold mb-3">
                <LIcon class="mr-1">mdi-shield-account</LIcon>
                {{ $t('admin.users.assignedRoles') }}
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
                  {{ $t('admin.users.noRolesAssigned') }}
                </LTag>
              </div>

              <!-- Add Role -->
              <div class="d-flex align-center gap-2">
                <v-select
                  v-model="roleToAssign"
                  :items="availableRoles"
                  item-title="display_name"
                  item-value="role_name"
                  :label="$t('admin.users.addRole')"
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
                <LIcon class="mr-1">mdi-key</LIcon>
                {{ $t('admin.users.effectivePermissions', { count: selectedUser.permissions.length }) }}
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
                  {{ showAllPermissions ? $t('admin.users.showLess') : $t('admin.users.showMore', { count: selectedUser.permissions.length - 8 }) }}
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
        <LIcon class="mr-2">mdi-account-group</LIcon>
        {{ $t('admin.users.title') }}
        <v-spacer></v-spacer>
        <LBtn variant="text" @click="loadUsers" :loading="loadingUsers" prepend-icon="mdi-refresh">
          {{ $t('common.refresh') }}
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
                :src="item.avatar_url"
                :username="item.username"
                size="sm"
                class="mr-2"
              />
              <div>
                <span class="font-weight-medium">{{ item.username }}</span>
                <!-- Show status on mobile since column is hidden -->
                <div v-if="isMobile" class="d-flex align-center gap-1 mt-1">
                  <LTag :variant="getStatusVariant(item)" size="sm">
                    {{ getStatusLabel(item) }}
                  </LTag>
                  <LTag
                    v-for="role in item.roles.slice(0, 1)"
                    :key="role.id"
                    size="sm"
                    :variant="getRoleVariant(role.role_name)"
                  >
                    {{ role.display_name }}
                  </LTag>
                  <span v-if="item.roles.length > 1" class="text-caption text-medium-emphasis">
                    +{{ item.roles.length - 1 }}
                  </span>
                </div>
              </div>
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
              <LIcon size="48" class="mb-2 text-medium-emphasis">mdi-account-search</LIcon>
              <div class="text-medium-emphasis">
                {{ searchQuery ? $t('admin.users.empty.noResults') : $t('admin.users.empty.searchHint') }}
              </div>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Create User Dialog -->
    <v-dialog v-model="createDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-account-plus</LIcon>
          {{ $t('admin.users.createDialog.title') }}
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="createDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-alert
            v-if="createWarning"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-4"
            closable
            @click:close="createWarning = ''; createDialog = false"
          >
            <div class="font-weight-bold mb-1">{{ $t('admin.users.createDialog.partialWarningTitle') }}</div>
            {{ createWarning }}
            <div class="mt-2">
              <LBtn variant="secondary" size="small" @click="createWarning = ''; createDialog = false">
                {{ $t('common.close') }}
              </LBtn>
            </div>
          </v-alert>

          <v-alert
            v-else
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            {{ $t('admin.users.createDialog.info') }}
          </v-alert>

          <v-text-field
            v-model="newUserUsername"
            :label="$t('admin.users.createDialog.username') + ' *'"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-account"
            :disabled="creatingUser"
            :hint="$t('admin.users.createDialog.usernameHint')"
            persistent-hint
            class="mb-2"
          />

          <v-text-field
            v-model="newUserEmail"
            :label="$t('admin.users.createDialog.email') + ' *'"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-email"
            type="email"
            :disabled="creatingUser"
            :hint="$t('admin.users.createDialog.emailHint')"
            persistent-hint
            class="mb-2"
          />

          <v-text-field
            v-model="newUserPassword"
            :label="$t('admin.users.createDialog.password') + ' *'"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-lock"
            :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
            :type="showPassword ? 'text' : 'password'"
            @click:append-inner="showPassword = !showPassword"
            :disabled="creatingUser"
            :hint="$t('admin.users.createDialog.passwordHint')"
            persistent-hint
            class="mb-2"
          />

          <v-text-field
            v-model="newUserDisplayName"
            :label="$t('admin.users.createDialog.displayName')"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-card-account-details"
            :disabled="creatingUser"
            :hint="$t('admin.users.createDialog.displayNameHint')"
            persistent-hint
            class="mb-2"
          />

          <div class="mb-2">
            <div class="text-body-2 text-medium-emphasis mb-2">{{ $t('admin.users.createDialog.collabColor') }}</div>
            <div class="d-flex align-center gap-2 mb-2">
              <div
                class="collab-color-preview"
                :style="{ backgroundColor: newUserCollabColor || '#9e9e9e' }"
              ></div>
              <span class="text-caption">{{ newUserCollabColor || $t('admin.users.createDialog.collabColorAuto') }}</span>
              <LBtn
                variant="text"
                size="x-small"
                class="ml-auto"
                :disabled="creatingUser"
                @click="newUserCollabColor = null"
              >
                Auto
              </LBtn>
            </div>
            <div class="collab-color-presets">
              <div
                v-for="color in collabColorPresets"
                :key="color"
                class="collab-color-preset"
                :class="{ selected: newUserCollabColor === color }"
                :style="{ backgroundColor: color }"
                @click="newUserCollabColor = color"
              ></div>
            </div>
          </div>

          <v-text-field
            v-model="newUserAvatarSeed"
            :label="$t('admin.users.createDialog.avatarSeed')"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-image-filter-vintage"
            :disabled="creatingUser"
            :hint="$t('admin.users.createDialog.avatarSeedHint')"
            persistent-hint
            class="mb-2"
          />

          <v-select
            v-model="newUserRoles"
            :items="allRoles"
            item-title="display_name"
            item-value="role_name"
            :label="$t('admin.users.createDialog.initialRoles')"
            variant="outlined"
            density="comfortable"
            multiple
            chips
            clearable
            :disabled="creatingUser"
            class="mb-2"
          />

          <v-switch
            v-model="newUserActive"
            color="success"
            inset
            :label="$t('admin.users.createDialog.accountActive')"
            :disabled="creatingUser"
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="createDialog = false" :disabled="creatingUser">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="primary"
            prepend-icon="mdi-check"
            @click="createUser"
            :loading="creatingUser"
            :disabled="!newUserUsername || !newUserEmail || !newUserPassword || newUserPassword.length < 8"
          >
            {{ $t('admin.users.createDialog.create') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirm Dialog -->
    <v-dialog v-model="deleteDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2" color="error">mdi-alert</LIcon>
          {{ $t('admin.users.deleteDialog.title') }}
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="deleteDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <span v-html="$t('admin.users.deleteDialog.confirm', { username: userToDelete?.username })"></span>
          <div class="text-caption text-medium-emphasis mt-2">
            {{ $t('admin.users.deleteDialog.info') }}
          </div>
        </v-card-text>
        <v-card-actions class="justify-end">
          <LBtn variant="text" @click="deleteDialog = false" :disabled="deletingUser">{{ $t('common.cancel') }}</LBtn>
          <LBtn
            variant="error"
            prepend-icon="mdi-delete"
            @click="deleteUser"
            :loading="deletingUser"
            :disabled="!userToDelete"
          >
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { useMobile } from '@/composables/useMobile';
import { logI18n } from '@/utils/logI18n';
import { COLLAB_COLOR_PRESETS, isColorInAiReservedRange } from '@/constants/colors';

const { t } = useI18n();
const { isMobile } = useMobile();

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
const newUserEmail = ref('');
const newUserPassword = ref('');
const newUserDisplayName = ref('');
const newUserRoles = ref([]);
const newUserCollabColor = ref(null);
const newUserAvatarSeed = ref('');
const newUserActive = ref(true);
const showPassword = ref(false);

// Loading states
const loadingSearch = ref(false);
const loadingUsers = ref(false);
const loadingUser = ref(null);
const assigningRole = ref(false);
const creatingUser = ref(false);
const createWarning = ref('');
const deletingUser = ref(false);
const togglingUser = ref(null);
const { isLoading, withLoading } = useSkeletonLoading(['table']);

// Table headers - responsive for mobile
const headers = computed(() => {
  if (isMobile.value) {
    return [
      { title: t('admin.users.table.user'), key: 'username', sortable: true },
      { title: '', key: 'actions', sortable: false, align: 'end', width: '80px' },
    ];
  }
  return [
    { title: t('admin.users.table.user'), key: 'username', sortable: true },
    { title: t('admin.users.table.status'), key: 'status', sortable: false },
    { title: t('admin.users.table.roles'), key: 'roles', sortable: false },
    { title: t('admin.users.table.actions'), key: 'actions', sortable: false, align: 'end' },
  ];
});

// Use global LLARS color presets (filtered to exclude AI reserved purple/violet range)
const collabColorPresets = COLLAB_COLOR_PRESETS.filter(c => !isColorInAiReservedRange(c));

// Role filter options
const roleFilterOptions = computed(() => {
  return [t('common.all'), ...allRoles.value.map(r => r.display_name)];
});

// Available roles for assignment (exclude already assigned)
const availableRoles = computed(() => {
  if (!selectedUser.value) return allRoles.value;
  const assignedRoleNames = selectedUser.value.roles.map(r => r.role_name);
  return allRoles.value.filter(r => !assignedRoleNames.includes(r.role_name));
});

// Filtered users based on role filter
const filteredUsers = computed(() => {
  if (!roleFilter.value || roleFilter.value === t('common.all')) return users.value;
  return users.value.filter(u =>
    u.roles.some(r => r.display_name === roleFilter.value)
  );
});

// Get role color
const getRoleColor = (roleName) => {
  const colors = {
    'admin': 'error',
    'researcher': 'primary',
    'evaluator': 'info',
    'viewer': 'info'
  };
  return colors[roleName] || 'grey';
};

const getRoleVariant = (roleName) => {
  const variants = {
    'admin': 'danger',
    'researcher': 'primary',
    'evaluator': 'info',
    'viewer': 'info'
  };
  return variants[roleName] || 'gray';
};

const getStatusLabel = (user) => {
  if (user.deleted_at) return t('admin.users.status.deleted');
  return user.is_active ? t('admin.users.status.active') : t('admin.users.status.locked');
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
  if (!selectedUser.value.db_record_exists) return { label: t('admin.users.notInDb'), variant: 'warning' };
  return {
    label: getStatusLabel(selectedUser.value),
    variant: getStatusVariant(selectedUser.value),
  };
});

// Get actions for user row - simplified on mobile
const getUserActions = (user) => {
  // On mobile, only show edit button to open details panel
  if (isMobile.value) {
    return [
      {
        key: 'edit',
        icon: 'mdi-chevron-right',
        tooltip: t('admin.users.actions.details'),
        loading: loadingUser.value === user.username
      }
    ];
  }
  return [
    {
      key: 'edit',
      icon: 'mdi-pencil',
      tooltip: t('admin.users.actions.edit'),
      loading: loadingUser.value === user.username
    },
    {
      key: 'toggle-lock',
      icon: user.is_active ? 'mdi-lock-open-variant' : 'mdi-lock',
      tooltip: user.is_active ? t('admin.users.actions.lock') : t('admin.users.actions.unlock'),
      variant: user.is_active ? 'success' : 'warning',
      loading: togglingUser.value === user.username,
      disabled: user.username === 'admin' || user.deleted_at
    },
    {
      key: 'delete',
      icon: 'mdi-delete',
      tooltip: t('admin.users.actions.delete'),
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
    logI18n('error', 'logs.admin.users.loadRolesFailed', error);
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
      logI18n('error', 'logs.admin.users.loadUsersFailed', error);
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
    logI18n('error', 'logs.admin.users.searchUserFailed', error);
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
    logI18n('error', 'logs.admin.users.loadUserFailed', error);
  }
  loadingUser.value = null;
};

const openCreateDialog = (prefillUsername = '') => {
  // Guard against PointerEvent being passed when called from @click without parentheses
  const username = typeof prefillUsername === 'string' ? prefillUsername : '';
  newUserUsername.value = username;
  newUserEmail.value = '';
  newUserPassword.value = '';
  newUserDisplayName.value = '';
  newUserActive.value = true;
  newUserRoles.value = [];
  newUserCollabColor.value = null;
  newUserAvatarSeed.value = '';
  showPassword.value = false;
  createWarning.value = '';

  if (username && selectedUser.value?.roles?.length) {
    newUserRoles.value = selectedUser.value.roles.map(r => r.role_name);
  }

  createDialog.value = true;
};

const createUser = async () => {
  if (!newUserUsername.value || !newUserEmail.value || !newUserPassword.value) return;
  creatingUser.value = true;
  createWarning.value = '';
  try {
    const response = await axios.post('/api/admin/users', {
      username: newUserUsername.value,
      email: newUserEmail.value,
      password: newUserPassword.value,
      display_name: newUserDisplayName.value || newUserUsername.value,
      is_active: newUserActive.value,
      role_names: newUserRoles.value,
      collab_color: newUserCollabColor.value,
      avatar_seed: newUserAvatarSeed.value || null,
      create_in_authentik: true,
    });

    // Check for warnings (e.g., Authentik creation failed)
    if (response.data.warning) {
      createWarning.value = response.data.warning;
      // Keep dialog open to show warning
      await loadUsers();
      return;
    }

    // Full success
    createDialog.value = false;
    await loadUsers();
    if (selectedUser.value?.username === newUserUsername.value) {
      await selectUser(newUserUsername.value);
    }
  } catch (error) {
    logI18n('error', 'logs.admin.users.createUserFailed', error);
    // Show error to user
    if (error.response?.data?.error) {
      alert(`Fehler: ${error.response.data.error}`);
    }
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
    logI18n('error', 'logs.admin.users.toggleUserLockFailed', error);
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
    logI18n('error', 'logs.admin.users.deleteUserFailed', error);
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
    logI18n('error', 'logs.admin.users.assignRoleFailed', error);
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
    logI18n('error', 'logs.admin.users.unassignRoleFailed', error);
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

.gap-1 {
  gap: 4px;
}

.gap-2 {
  gap: 8px;
}

.collab-color-preview {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.2);
}

.collab-color-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.collab-color-preset {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
}

.collab-color-preset.selected {
  border-color: rgb(var(--v-theme-on-surface));
}

/* Mobile Styles */
.admin-users.is-mobile {
  overflow: hidden;
  max-width: 100vw;
  overflow-x: hidden;
}

.admin-users.is-mobile :deep(.v-data-table) {
  max-width: 100%;
  overflow-x: hidden;
}

.admin-users.is-mobile :deep(.v-data-table__wrapper) {
  overflow-x: hidden;
}

.admin-users.is-mobile :deep(.v-data-table-header th) {
  white-space: nowrap;
}

.admin-users.is-mobile :deep(.v-card) {
  max-width: 100%;
  overflow: hidden;
}

.admin-users.is-mobile :deep(.v-card-title) {
  flex-wrap: wrap;
  gap: 8px;
}

.admin-users.is-mobile :deep(.v-card-title .text-h6) {
  font-size: 1rem !important;
}

/* Compact search row on mobile */
.admin-users.is-mobile :deep(.v-row.mb-4) {
  margin-bottom: 8px !important;
}

.admin-users.is-mobile :deep(.v-row.mb-4 .v-col) {
  padding-top: 4px;
  padding-bottom: 4px;
}
</style>
