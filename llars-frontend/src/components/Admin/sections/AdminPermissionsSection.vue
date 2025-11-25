<template>
  <div class="admin-permissions">
    <!-- Tabs -->
    <v-card>
      <v-tabs v-model="activeTab" bg-color="primary">
        <v-tab value="roles">
          <v-icon start>mdi-shield-account</v-icon>
          Rollen
        </v-tab>
        <v-tab value="permissions">
          <v-icon start>mdi-key</v-icon>
          Berechtigungen
        </v-tab>
        <v-tab value="audit">
          <v-icon start>mdi-history</v-icon>
          Audit Log
        </v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- Roles Tab -->
        <v-window-item value="roles">
          <v-card-text>
            <v-row>
              <v-col
                cols="12"
                md="4"
                v-for="role in roles"
                :key="role.id"
              >
                <v-card variant="outlined" class="role-card">
                  <v-card-title class="d-flex align-center">
                    <v-icon :color="getRoleColor(role.role_name)" class="mr-2">
                      {{ getRoleIcon(role.role_name) }}
                    </v-icon>
                    {{ role.display_name }}
                  </v-card-title>
                  <v-card-subtitle>{{ role.description || 'Keine Beschreibung' }}</v-card-subtitle>
                  <v-card-text>
                    <div class="text-subtitle-2 mb-2">Berechtigungen:</div>
                    <v-chip
                      v-for="perm in role.permissions?.slice(0, 5)"
                      :key="perm"
                      size="x-small"
                      variant="tonal"
                      class="ma-1"
                    >
                      {{ perm }}
                    </v-chip>
                    <v-chip
                      v-if="role.permissions?.length > 5"
                      size="x-small"
                      variant="text"
                    >
                      +{{ role.permissions.length - 5 }} mehr
                    </v-chip>
                  </v-card-text>
                  <v-card-actions>
                    <v-btn variant="text" size="small" @click="viewRoleDetails(role)">
                      Details
                    </v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-window-item>

        <!-- Permissions Tab -->
        <v-window-item value="permissions">
          <v-card-text>
            <v-text-field
              v-model="permissionSearch"
              label="Berechtigung suchen"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              class="mb-4"
            ></v-text-field>

            <!-- Grouped Permissions -->
            <div v-for="(group, category) in groupedPermissions" :key="category" class="mb-4">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <v-icon class="mr-1">{{ getCategoryIcon(category) }}</v-icon>
                {{ getCategoryName(category) }}
              </h3>
              <v-chip
                v-for="perm in group"
                :key="perm.id"
                :color="getCategoryColor(category)"
                variant="tonal"
                class="ma-1"
              >
                {{ perm.permission_key }}
                <v-tooltip activator="parent" location="top">
                  {{ perm.description || 'Keine Beschreibung' }}
                </v-tooltip>
              </v-chip>
            </div>
          </v-card-text>
        </v-window-item>

        <!-- Audit Log Tab -->
        <v-window-item value="audit">
          <v-card-text>
            <v-data-table
              :headers="auditHeaders"
              :items="auditLog"
              :loading="loadingAudit"
              :items-per-page="10"
            >
              <template v-slot:item.action="{ item }">
                <v-chip :color="getActionColor(item.action)" size="small">
                  {{ item.action }}
                </v-chip>
              </template>

              <template v-slot:item.timestamp="{ item }">
                {{ formatDate(item.timestamp) }}
              </template>

              <template v-slot:no-data>
                <div class="text-center py-8 text-medium-emphasis">
                  <v-icon size="48" class="mb-2">mdi-history</v-icon>
                  <div>Keine Audit-Einträge vorhanden</div>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Role Details Dialog -->
    <v-dialog v-model="roleDialog" max-width="600">
      <v-card v-if="selectedRole">
        <v-card-title class="d-flex align-center">
          <v-icon :color="getRoleColor(selectedRole.role_name)" class="mr-2">
            {{ getRoleIcon(selectedRole.role_name) }}
          </v-icon>
          {{ selectedRole.display_name }}
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="roleDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <p class="text-body-1 mb-4">{{ selectedRole.description || 'Keine Beschreibung' }}</p>

          <h4 class="text-subtitle-1 font-weight-bold mb-2">Alle Berechtigungen ({{ selectedRole.permissions?.length || 0 }}):</h4>
          <v-chip
            v-for="perm in selectedRole.permissions"
            :key="perm"
            size="small"
            variant="tonal"
            class="ma-1"
          >
            {{ perm }}
          </v-chip>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// State
const activeTab = ref('roles');
const roles = ref([]);
const permissions = ref([]);
const auditLog = ref([]);
const permissionSearch = ref('');

// Loading states
const loadingRoles = ref(false);
const loadingPermissions = ref(false);
const loadingAudit = ref(false);

// Dialog
const roleDialog = ref(false);
const selectedRole = ref(null);

// Audit headers
const auditHeaders = [
  { title: 'Aktion', key: 'action', sortable: true },
  { title: 'Benutzer', key: 'performed_by', sortable: true },
  { title: 'Ziel', key: 'target_username', sortable: true },
  { title: 'Details', key: 'details', sortable: false },
  { title: 'Zeitpunkt', key: 'timestamp', sortable: true }
];

// Computed
const groupedPermissions = computed(() => {
  const filtered = permissions.value.filter(p =>
    p.permission_key.toLowerCase().includes(permissionSearch.value.toLowerCase())
  );

  return filtered.reduce((groups, perm) => {
    const category = perm.category || 'other';
    if (!groups[category]) groups[category] = [];
    groups[category].push(perm);
    return groups;
  }, {});
});

// Helper functions
const getRoleColor = (roleName) => {
  const colors = {
    'admin': 'error',
    'researcher': 'primary',
    'viewer': 'info'
  };
  return colors[roleName] || 'grey';
};

const getRoleIcon = (roleName) => {
  const icons = {
    'admin': 'mdi-shield-crown',
    'researcher': 'mdi-flask',
    'viewer': 'mdi-eye'
  };
  return icons[roleName] || 'mdi-account';
};

const getCategoryIcon = (category) => {
  const icons = {
    'feature': 'mdi-puzzle',
    'admin': 'mdi-cog',
    'data': 'mdi-database'
  };
  return icons[category] || 'mdi-key';
};

const getCategoryName = (category) => {
  const names = {
    'feature': 'Feature-Berechtigungen',
    'admin': 'Admin-Berechtigungen',
    'data': 'Daten-Berechtigungen'
  };
  return names[category] || category;
};

const getCategoryColor = (category) => {
  const colors = {
    'feature': 'primary',
    'admin': 'error',
    'data': 'warning'
  };
  return colors[category] || 'grey';
};

const getActionColor = (action) => {
  if (action.includes('grant') || action.includes('assign')) return 'success';
  if (action.includes('revoke') || action.includes('unassign')) return 'error';
  return 'info';
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const viewRoleDetails = (role) => {
  selectedRole.value = role;
  roleDialog.value = true;
};

// API calls
const fetchRoles = async () => {
  loadingRoles.value = true;
  try {
    const response = await axios.get('/api/permissions/roles');
    roles.value = response.data.roles || [];
  } catch (error) {
    console.error('Error fetching roles:', error);
  }
  loadingRoles.value = false;
};

const fetchPermissions = async () => {
  loadingPermissions.value = true;
  try {
    const response = await axios.get('/api/permissions');
    permissions.value = response.data.permissions || [];
  } catch (error) {
    console.error('Error fetching permissions:', error);
  }
  loadingPermissions.value = false;
};

const fetchAuditLog = async () => {
  loadingAudit.value = true;
  try {
    const response = await axios.get('/api/permissions/audit-log');
    auditLog.value = response.data.entries || [];
  } catch (error) {
    console.error('Error fetching audit log:', error);
    auditLog.value = [];
  }
  loadingAudit.value = false;
};

onMounted(() => {
  fetchRoles();
  fetchPermissions();
  fetchAuditLog();
});
</script>

<style scoped>
.role-card {
  height: 100%;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.role-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
