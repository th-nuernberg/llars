<template>
  <div class="admin-permissions">
    <!-- Tabs -->
    <v-card>
      <v-tabs v-model="activeTab" bg-color="primary">
        <v-tab value="roles">
          <LIcon start>mdi-shield-account</LIcon>
          Rollen
        </v-tab>
        <v-tab value="permissions">
          <LIcon start>mdi-key</LIcon>
          Berechtigungen
        </v-tab>
        <v-tab value="chatbots">
          <LIcon start>mdi-robot</LIcon>
          Chatbots
        </v-tab>
        <v-tab value="llm">
          <LIcon start>mdi-brain</LIcon>
          LLM Modelle
        </v-tab>
        <v-tab value="audit">
          <LIcon start>mdi-history</LIcon>
          Audit Log
        </v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
	        <!-- Roles Tab -->
	        <v-window-item value="roles">
	          <v-card-text>
	            <div class="d-flex align-center justify-space-between mb-3">
	              <div class="text-subtitle-2 font-weight-medium">Rollen</div>
	              <LBtn
	                variant="primary"
	                size="small"
	                @click="openCreateRoleDialog"
	              >
	                Neue Rolle
	              </LBtn>
	            </div>
	            <v-skeleton-loader v-if="isLoading('roles')" type="card@3"></v-skeleton-loader>
	            <v-row v-else>
	              <v-col
	                cols="12"
                md="4"
                v-for="role in roles"
                :key="role.id"
              >
                <v-card variant="outlined" class="role-card">
                  <v-card-title class="d-flex align-center">
                    <LIcon :color="getRoleColor(role.role_name)" class="mr-2">
                      {{ getRoleIcon(role.role_name) }}
                    </LIcon>
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
                    <LBtn variant="text" size="small" @click="viewRoleDetails(role)">
                      Details
                    </LBtn>
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

            <!-- Skeleton Loading -->
            <v-skeleton-loader v-if="isLoading('permissions')" type="paragraph@3"></v-skeleton-loader>

            <!-- Grouped Permissions -->
            <div v-else v-for="(group, category) in groupedPermissions" :key="category" class="mb-4">
              <h3 class="text-subtitle-1 font-weight-bold mb-2">
                <LIcon class="mr-1">{{ getCategoryIcon(category) }}</LIcon>
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

        <!-- Chatbots Tab -->
        <v-window-item value="chatbots">
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('chatbots')" type="table"></v-skeleton-loader>

            <v-data-table
              v-else
              :headers="chatbotHeaders"
              :items="chatbots"
              :items-per-page="10"
            >
              <template v-slot:item.is_public="{ item }">
                <v-chip :color="item.is_public ? 'success' : 'warning'" size="small" variant="tonal">
                  <LIcon start size="small">{{ item.is_public ? 'mdi-earth' : 'mdi-lock' }}</LIcon>
                  {{ item.is_public ? 'Public' : 'Private' }}
                </v-chip>
              </template>

	              <template v-slot:item.allowed_usernames="{ item }">
	                <div class="d-flex flex-wrap gap-1">
	                  <v-chip
	                    v-for="r in (item.allowed_roles || []).slice(0, 3)"
	                    :key="'role-' + r"
	                    size="x-small"
	                    variant="tonal"
	                    color="secondary"
	                  >
	                    <LIcon start size="x-small">mdi-account-group</LIcon>
	                    {{ r }}
	                  </v-chip>
	                  <v-chip
	                    v-if="(item.allowed_roles || []).length > 3"
	                    size="x-small"
	                    variant="text"
	                  >
	                    +{{ (item.allowed_roles || []).length - 3 }} Rollen
	                  </v-chip>

	                  <v-chip
	                    v-for="(u, idx) in (item.allowed_usernames || []).slice(0, 3)"
	                    :key="u"
	                    size="x-small"
                    variant="tonal"
                    color="primary"
                  >
                    {{ u }}
                  </v-chip>
	                  <v-chip
	                    v-if="(item.allowed_usernames || []).length > 3"
	                    size="x-small"
	                    variant="text"
	                  >
	                    +{{ (item.allowed_usernames || []).length - 3 }}
	                  </v-chip>
	                  <span
	                    v-if="!item.is_public && (!item.allowed_usernames || item.allowed_usernames.length === 0) && (!item.allowed_roles || item.allowed_roles.length === 0)"
	                    class="text-caption text-medium-emphasis"
	                  >
	                    Keine Zuweisung
	                  </span>
	                </div>
	              </template>

              <template v-slot:item.actions="{ item }">
                <LBtn size="small" variant="text" @click="openAccessDialog(item)">
                  Bearbeiten
                </LBtn>
              </template>

              <template v-slot:no-data>
                <div class="text-center py-8 text-medium-emphasis">
                  <LIcon size="48" class="mb-2">mdi-robot-off</LIcon>
                  <div>Keine Chatbots gefunden</div>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- LLM Models Tab -->
        <v-window-item value="llm">
          <v-card-text>
            <!-- Sync indicator and button -->
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="d-flex align-center">
                <span class="text-subtitle-2 font-weight-medium">LLM Modelle</span>
                <v-chip v-if="syncingLlmModels" size="small" color="info" variant="tonal" class="ml-2">
                  <v-progress-circular indeterminate size="14" width="2" class="mr-2" />
                  Synchronisiere...
                </v-chip>
              </div>
              <LBtn
                variant="text"
                size="small"
                :loading="syncingLlmModels"
                @click="syncAllLlmModels"
              >
                <LIcon start size="16">mdi-sync</LIcon>
                Modelle synchronisieren
              </LBtn>
            </div>

            <!-- Color Legend -->
            <div class="d-flex flex-wrap align-center ga-2 mb-4 pa-2 rounded" style="background: rgba(var(--v-theme-on-surface), 0.05);">
              <span class="text-caption text-medium-emphasis mr-2">Kategorie:</span>
              <v-chip
                v-for="(config, key) in modelTypeConfig"
                :key="key"
                v-show="key !== 'default'"
                size="x-small"
                :color="config.color"
                variant="tonal"
              >
                <LIcon start size="12">{{ config.icon }}</LIcon>
                {{ config.label }}
              </v-chip>
              <v-divider vertical class="mx-2" />
              <span class="text-caption text-medium-emphasis mr-2">Fähigkeiten:</span>
              <v-chip size="x-small" color="orange" variant="tonal">
                <LIcon start size="12">mdi-eye</LIcon>
                Vision
              </v-chip>
              <v-chip size="x-small" color="teal" variant="tonal">
                <LIcon start size="12">mdi-head-cog</LIcon>
                Reasoning
              </v-chip>
            </div>

            <v-skeleton-loader v-if="isLoading('llm') || syncingLlmModels" type="table"></v-skeleton-loader>

            <v-data-table
              v-else
              :headers="llmHeaders"
              :items="llmModels"
              :items-per-page="10"
            >
              <template v-slot:item.display_name="{ item }">
                <div class="d-flex flex-column">
                  <span class="font-weight-medium">{{ item.display_name }}</span>
                  <span class="text-caption text-medium-emphasis">{{ item.model_id }}</span>
                </div>
              </template>

              <template v-slot:item.model_type="{ item }">
                <v-chip
                  :color="getModelTypeConfig(item.model_type).color"
                  size="small"
                  variant="tonal"
                >
                  <LIcon start size="14">{{ getModelTypeConfig(item.model_type).icon }}</LIcon>
                  {{ getModelTypeConfig(item.model_type).label }}
                </v-chip>
              </template>

              <template v-slot:item.capabilities="{ item }">
                <div class="d-flex flex-wrap ga-1">
                  <v-chip
                    v-if="item.supports_vision"
                    color="orange"
                    size="small"
                    variant="tonal"
                  >
                    <LIcon start size="14">mdi-eye</LIcon>
                    Vision
                  </v-chip>
                  <v-chip
                    v-if="item.supports_reasoning"
                    color="teal"
                    size="small"
                    variant="tonal"
                  >
                    <LIcon start size="14">mdi-head-cog</LIcon>
                    Reasoning
                  </v-chip>
                  <span
                    v-if="!item.supports_vision && !item.supports_reasoning"
                    class="text-caption text-medium-emphasis"
                  >
                    —
                  </span>
                </div>
              </template>

              <template v-slot:item.is_restricted="{ item }">
                <v-chip :color="item.is_restricted ? 'warning' : 'success'" size="small" variant="tonal">
                  <LIcon start size="small">
                    {{ item.is_restricted ? 'mdi-lock' : 'mdi-earth' }}
                  </LIcon>
                  {{ item.is_restricted ? 'Eingeschränkt' : 'Public' }}
                </v-chip>
              </template>

              <template v-slot:item.allowed_usernames="{ item }">
                <div class="d-flex flex-wrap gap-1">
                  <v-chip
                    v-for="r in (item.allowed_roles || []).slice(0, 3)"
                    :key="'role-' + r"
                    size="x-small"
                    variant="tonal"
                    color="secondary"
                  >
                    <LIcon start size="x-small">mdi-account-group</LIcon>
                    {{ r }}
                  </v-chip>
                  <v-chip
                    v-if="(item.allowed_roles || []).length > 3"
                    size="x-small"
                    variant="text"
                  >
                    +{{ (item.allowed_roles || []).length - 3 }} Rollen
                  </v-chip>

                  <v-chip
                    v-for="u in (item.allowed_usernames || []).slice(0, 3)"
                    :key="u"
                    size="x-small"
                    variant="tonal"
                    color="primary"
                  >
                    {{ u }}
                  </v-chip>
                  <v-chip
                    v-if="(item.allowed_usernames || []).length > 3"
                    size="x-small"
                    variant="text"
                  >
                    +{{ (item.allowed_usernames || []).length - 3 }}
                  </v-chip>
                  <span
                    v-if="!item.is_restricted"
                    class="text-caption text-medium-emphasis"
                  >
                    Öffentlich
                  </span>
                </div>
              </template>

              <template v-slot:item.actions="{ item }">
                <LBtn size="small" variant="text" @click="openLlmAccessDialog(item)">
                  Bearbeiten
                </LBtn>
              </template>

              <template v-slot:no-data>
                <div class="text-center py-8 text-medium-emphasis">
                  <LIcon size="48" class="mb-2">mdi-robot-off</LIcon>
                  <div>Keine LLM Modelle gefunden</div>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>

        <!-- Audit Log Tab -->
        <v-window-item value="audit">
          <v-card-text>
            <v-skeleton-loader v-if="isLoading('audit')" type="table"></v-skeleton-loader>
            <v-data-table
              v-else
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
                  <LIcon size="48" class="mb-2">mdi-history</LIcon>
                  <div>Keine Audit-Einträge vorhanden</div>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>

    <!-- Chatbot Access Dialog -->
    <v-dialog v-model="accessDialog" max-width="700">
      <v-card v-if="selectedChatbot">
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-robot</LIcon>
          Zugriff: {{ selectedChatbot.display_name }}
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="accessDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
	        <v-card-text>
	          <v-alert
	            v-if="selectedChatbot.is_public"
	            type="info"
	            variant="tonal"
	            class="mb-4"
	          >
	            Dieser Chatbot ist public und für alle Nutzer mit Chatbot-Recht sichtbar.
	            Zuweisungen werden nur bei privaten Chatbots berücksichtigt.
	          </v-alert>

	          <v-autocomplete
	            v-model="accessUsernames"
	            :items="allUsernames"
	            label="Erlaubte Nutzer"
	            multiple
	            chips
	            closable-chips
	            clearable
	            variant="outlined"
	            density="comfortable"
	            hide-details
	          />
	          <v-autocomplete
	            v-model="accessRoleNames"
	            :items="roles"
	            item-title="display_name"
	            item-value="role_name"
	            label="Erlaubte Rollen (Nutzergruppen)"
	            multiple
	            chips
	            closable-chips
	            clearable
	            variant="outlined"
	            density="comfortable"
	            hide-details
	            class="mt-3"
	          />
	          <div class="text-caption text-medium-emphasis mt-2">
	            Tipp: Rollen sind Nutzergruppen im LLARS Permission-System.
	          </div>
	        </v-card-text>
		          <v-card-actions>
		            <v-spacer />
		            <LBtn variant="text" @click="accessDialog = false">Abbrechen</LBtn>
	          <LBtn variant="primary" :loading="savingAccess" @click="saveAccess">
	            Speichern
	          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- LLM Access Dialog -->
    <v-dialog v-model="llmAccessDialog" max-width="700">
      <v-card v-if="selectedLlmModel">
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">mdi-brain</LIcon>
          Zugriff: {{ selectedLlmModel.display_name }}
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="llmAccessDialog = false" />
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text>
          <v-alert
            v-if="!selectedLlmModel.is_restricted"
            type="info"
            variant="tonal"
            class="mb-4"
          >
            Ohne Zuweisung ist dieses Modell für alle Nutzer sichtbar. Sobald Benutzer/Rollen
            gesetzt werden, ist es eingeschränkt.
          </v-alert>

          <v-autocomplete
            v-model="llmAccessUsernames"
            :items="allUsernames"
            label="Erlaubte Nutzer"
            multiple
            chips
            closable-chips
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
          />
          <v-autocomplete
            v-model="llmAccessRoleNames"
            :items="roles"
            item-title="display_name"
            item-value="role_name"
            label="Erlaubte Rollen (Nutzergruppen)"
            multiple
            chips
            closable-chips
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
            class="mt-3"
          />
          <div class="text-caption text-medium-emphasis mt-2">
            Tipp: Rollen sind Nutzergruppen im LLARS Permission-System.
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="llmAccessDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="savingLlmAccess" @click="saveLlmAccess">
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Role Details Dialog -->
    <v-dialog v-model="roleDialog" max-width="600">
      <v-card v-if="selectedRole">
        <v-card-title class="d-flex align-center">
          <LIcon :color="getRoleColor(selectedRole.role_name)" class="mr-2">
            {{ getRoleIcon(selectedRole.role_name) }}
          </LIcon>
          {{ selectedRole.display_name }}
          <v-spacer></v-spacer>
          <LIconBtn icon="mdi-close" @click="roleDialog = false" />
        </v-card-title>
	        <v-divider></v-divider>
	        <v-card-text>
	          <div class="d-flex flex-wrap align-center ga-2 mb-3">
	            <v-chip size="small" variant="tonal">
	              {{ selectedRole.role_name }}
	            </v-chip>
	            <v-chip size="small" variant="tonal">
	              {{ selectedRole.permissions?.length || 0 }} Berechtigungen
	            </v-chip>
	          </div>

	          <p class="text-body-1 mb-4">{{ selectedRole.description || 'Keine Beschreibung' }}</p>

	          <h4 class="text-subtitle-1 font-weight-bold mb-2">Rollenrechte bearbeiten</h4>

	          <v-autocomplete
	            v-model="rolePermissionKeys"
	            :items="permissions"
	            item-title="permission_key"
	            item-value="permission_key"
	            label="Berechtigungen"
	            multiple
	            chips
	            closable-chips
	            clearable
	            variant="outlined"
	            density="comfortable"
	            hide-details
	          >
	            <template #item="{ props, item }">
	              <v-list-item
	                v-bind="props"
	                :title="item.raw.permission_key"
	                :subtitle="item.raw.description || item.raw.display_name || ''"
	              />
	            </template>
	          </v-autocomplete>
	          <div class="text-caption text-medium-emphasis mt-2">
	            Änderungen werden sofort in der Permission-Logik wirksam (nach Reload/Neu-Login).
	          </div>
	        </v-card-text>
		        <v-card-actions class="justify-end">
		          <LBtn variant="text" @click="roleDialog = false">Schließen</LBtn>
		          <LBtn
		            variant="primary"
		            :loading="savingRolePermissions"
		            @click="saveRolePermissions"
		          >
		            Speichern
		          </LBtn>
	        </v-card-actions>
	      </v-card>
	    </v-dialog>

	    <!-- Create Role Dialog -->
	    <v-dialog v-model="createRoleDialog" max-width="700">
	      <v-card>
	        <v-card-title class="d-flex align-center">
	          <LIcon class="mr-2">mdi-plus-circle</LIcon>
	          Neue Rolle erstellen
	          <v-spacer></v-spacer>
	          <LIconBtn icon="mdi-close" @click="createRoleDialog = false" />
	        </v-card-title>
	        <v-divider></v-divider>
	        <v-card-text>
	          <v-row>
	            <v-col cols="12" md="6">
	              <v-text-field
	                v-model="newRoleName"
	                label="Role Name (technisch, z.B. 'team_alpha')"
	                variant="outlined"
	                density="comfortable"
	                hide-details
	              />
	            </v-col>
	            <v-col cols="12" md="6">
	              <v-text-field
	                v-model="newRoleDisplayName"
	                label="Anzeigename"
	                variant="outlined"
	                density="comfortable"
	                hide-details
	              />
	            </v-col>
	          </v-row>

	          <v-textarea
	            v-model="newRoleDescription"
	            label="Beschreibung (optional)"
	            variant="outlined"
	            density="comfortable"
	            rows="2"
	            auto-grow
	            hide-details
	            class="mt-2"
	          />

	          <v-autocomplete
	            v-model="newRolePermissionKeys"
	            :items="permissions"
	            item-title="permission_key"
	            item-value="permission_key"
	            label="Initiale Berechtigungen"
	            multiple
	            chips
	            closable-chips
	            clearable
	            variant="outlined"
	            density="comfortable"
	            hide-details
	            class="mt-3"
	          >
	            <template #item="{ props, item }">
	              <v-list-item
	                v-bind="props"
	                :title="item.raw.permission_key"
	                :subtitle="item.raw.description || item.raw.display_name || ''"
	              />
	            </template>
	          </v-autocomplete>
	        </v-card-text>
		        <v-card-actions class="justify-end">
		          <LBtn variant="text" @click="createRoleDialog = false">Abbrechen</LBtn>
		          <LBtn variant="primary" :loading="creatingRole" @click="createRole">
		            Erstellen
		          </LBtn>
		        </v-card-actions>
		      </v-card>
		    </v-dialog>
	  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';

// State
const activeTab = ref('roles');
const syncingLlmModels = ref(false);
const llmSyncedOnce = ref(false);
const roles = ref([]);
const permissions = ref([]);
const auditLog = ref([]);
const chatbots = ref([]);
const llmModels = ref([]);
const permissionSearch = ref('');

// Loading states
const loadingRoles = ref(false);
const loadingPermissions = ref(false);
const loadingAudit = ref(false);
const loadingChatbots = ref(false);
const loadingLlmModels = ref(false);
const { isLoading, withLoading } = useSkeletonLoading(['roles', 'permissions', 'chatbots', 'llm', 'audit']);

// Dialog
const roleDialog = ref(false);
const selectedRole = ref(null);
const rolePermissionKeys = ref([]);
const savingRolePermissions = ref(false);

// Create role dialog
const createRoleDialog = ref(false);
const newRoleName = ref('');
const newRoleDisplayName = ref('');
const newRoleDescription = ref('');
const newRolePermissionKeys = ref([]);
const creatingRole = ref(false);

// Chatbot access dialog
const accessDialog = ref(false);
const selectedChatbot = ref(null);
const accessUsernames = ref([]);
const accessRoleNames = ref([]);
const allUsernames = ref([]);
const savingAccess = ref(false);

// LLM access dialog
const llmAccessDialog = ref(false);
const selectedLlmModel = ref(null);
const llmAccessUsernames = ref([]);
const llmAccessRoleNames = ref([]);
const savingLlmAccess = ref(false);

// Audit headers
const auditHeaders = [
  { title: 'Aktion', key: 'action', sortable: true },
  { title: 'Benutzer', key: 'performed_by', sortable: true },
  { title: 'Ziel', key: 'target_username', sortable: true },
  { title: 'Details', key: 'details', sortable: false },
  { title: 'Zeitpunkt', key: 'timestamp', sortable: true }
];

const chatbotHeaders = [
  { title: 'Chatbot', key: 'display_name', sortable: true },
  { title: 'Sichtbarkeit', key: 'is_public', sortable: true },
  { title: 'Zuweisungen', key: 'allowed_usernames', sortable: false },
  { title: '', key: 'actions', sortable: false, align: 'end' }
];

const llmHeaders = [
  { title: 'Modell', key: 'display_name', sortable: true },
  { title: 'Kategorie', key: 'model_type', sortable: true },
  { title: 'Fähigkeiten', key: 'capabilities', sortable: false },
  { title: 'Provider', key: 'provider', sortable: true },
  { title: 'Sichtbarkeit', key: 'is_restricted', sortable: true },
  { title: 'Zuweisungen', key: 'allowed_usernames', sortable: false },
  { title: '', key: 'actions', sortable: false, align: 'end' }
];

// Model type colors and labels (must match backend: llm, embedding, reranker)
const modelTypeConfig = {
  llm: { color: 'primary', icon: 'mdi-chat', label: 'LLM' },
  embedding: { color: 'info', icon: 'mdi-vector-line', label: 'Embedding' },
  reranker: { color: 'purple', icon: 'mdi-sort-variant', label: 'Reranker' },
  default: { color: 'grey', icon: 'mdi-robot', label: 'Unbekannt' }
};

const getModelTypeConfig = (modelType) => {
  return modelTypeConfig[modelType?.toLowerCase()] || modelTypeConfig.default;
};

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
    'evaluator': 'info',
    'viewer': 'info'
  };
  return colors[roleName] || 'grey';
};

const getRoleIcon = (roleName) => {
  const icons = {
    'admin': 'mdi-shield-crown',
    'researcher': 'mdi-flask',
    'evaluator': 'mdi-eye',
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
  const a = (action || '').toLowerCase();
  if (a.includes('grant') || a.includes('assign')) return 'success';
  if (a.includes('revoke') || a.includes('unassign')) return 'error';
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
  rolePermissionKeys.value = [...(role?.permissions || [])];
  roleDialog.value = true;
};

const openCreateRoleDialog = () => {
  newRoleName.value = '';
  newRoleDisplayName.value = '';
  newRoleDescription.value = '';
  newRolePermissionKeys.value = [];
  createRoleDialog.value = true;
};

const upsertRole = (updatedRole) => {
  if (!updatedRole) return;
  const idx = roles.value.findIndex(r => r.role_name === updatedRole.role_name);
  if (idx >= 0) {
    roles.value[idx] = { ...roles.value[idx], ...updatedRole };
  } else {
    roles.value.unshift(updatedRole);
  }
  if (selectedRole.value?.role_name === updatedRole.role_name) {
    selectedRole.value = { ...selectedRole.value, ...updatedRole };
  }
};

const createRole = async () => {
  const roleName = newRoleName.value.trim();
  const displayName = newRoleDisplayName.value.trim();
  if (!roleName || !displayName) return;

  creatingRole.value = true;
  try {
    const response = await axios.post('/api/permissions/roles', {
      role_name: roleName,
      display_name: displayName,
      description: newRoleDescription.value,
      permission_keys: newRolePermissionKeys.value
    });
    const created = response.data.role || response.data.data;
    upsertRole(created);
    createRoleDialog.value = false;
    await fetchRoles();
  } catch (error) {
    console.error('Error creating role:', error);
  } finally {
    creatingRole.value = false;
  }
};

const saveRolePermissions = async () => {
  if (!selectedRole.value) return;
  savingRolePermissions.value = true;
  try {
    const response = await axios.put(`/api/permissions/roles/${selectedRole.value.role_name}/permissions`, {
      permission_keys: rolePermissionKeys.value
    });
    const updated = response.data.role || response.data.data;
    upsertRole(updated);
    await fetchRoles();
  } catch (error) {
    console.error('Error saving role permissions:', error);
  } finally {
    savingRolePermissions.value = false;
  }
};

// API calls
const fetchRoles = async () => {
  loadingRoles.value = true;
  await withLoading('roles', async () => {
    try {
      const response = await axios.get('/api/permissions/roles');
      roles.value = response.data.roles || [];
    } catch (error) {
      console.error('Error fetching roles:', error);
    }
  });
  loadingRoles.value = false;
};

const fetchPermissions = async () => {
  loadingPermissions.value = true;
  await withLoading('permissions', async () => {
    try {
      const response = await axios.get('/api/permissions');
      permissions.value = response.data.permissions || [];
    } catch (error) {
      console.error('Error fetching permissions:', error);
    }
  });
  loadingPermissions.value = false;
};

const fetchAuditLog = async () => {
  loadingAudit.value = true;
  await withLoading('audit', async () => {
    try {
      const response = await axios.get('/api/permissions/audit-log');
      auditLog.value = response.data.entries || [];
    } catch (error) {
      console.error('Error fetching audit log:', error);
      auditLog.value = [];
    }
  });
  loadingAudit.value = false;
};

const fetchUsersForAccess = async () => {
  try {
    const response = await axios.get('/api/permissions/users-with-roles');
    const users = response.data.users || response.data.data || [];
    allUsernames.value = users.map(u => u.username).filter(Boolean).sort();
  } catch (error) {
    console.error('Error fetching users for access:', error);
    allUsernames.value = [];
  }
};

const fetchChatbotAccessOverview = async () => {
  loadingChatbots.value = true;
  await withLoading('chatbots', async () => {
    try {
      const response = await axios.get('/api/chatbots/access/overview?include_inactive=true');
      chatbots.value = response.data.chatbots || [];
    } catch (error) {
      console.error('Error fetching chatbot access overview:', error);
      chatbots.value = [];
    }
  });
  loadingChatbots.value = false;
};

const fetchLlmAccessOverview = async () => {
  loadingLlmModels.value = true;
  await withLoading('llm', async () => {
    try {
      const response = await axios.get('/api/llm/models/access/overview?include_inactive=true');
      llmModels.value = response.data.models || [];
    } catch (error) {
      console.error('Error fetching LLM access overview:', error);
      llmModels.value = [];
    }
  });
  loadingLlmModels.value = false;
};

const openAccessDialog = async (chatbot) => {
  selectedChatbot.value = chatbot;
  accessUsernames.value = [...(chatbot.allowed_usernames || [])];
  accessRoleNames.value = [...(chatbot.allowed_roles || [])];
  accessDialog.value = true;

  if (!allUsernames.value.length) {
    await fetchUsersForAccess();
  }
};

const openLlmAccessDialog = async (model) => {
  selectedLlmModel.value = model;
  llmAccessUsernames.value = [...(model.allowed_usernames || [])];
  llmAccessRoleNames.value = [...(model.allowed_roles || [])];
  llmAccessDialog.value = true;

  if (!allUsernames.value.length) {
    await fetchUsersForAccess();
  }
};

const saveAccess = async () => {
  if (!selectedChatbot.value) return;
  savingAccess.value = true;
  try {
    const response = await axios.put(`/api/chatbots/${selectedChatbot.value.id}/access`, {
      usernames: accessUsernames.value,
      role_names: accessRoleNames.value
    });
    const updated = response.data.allowed_usernames || [];
    const updatedRoles = response.data.allowed_roles || [];
    selectedChatbot.value.allowed_usernames = updated;
    selectedChatbot.value.allowed_roles = updatedRoles;
    await fetchChatbotAccessOverview();
    accessDialog.value = false;
  } catch (error) {
    console.error('Error saving chatbot access:', error);
  } finally {
    savingAccess.value = false;
  }
};

const saveLlmAccess = async () => {
  if (!selectedLlmModel.value) return;
  savingLlmAccess.value = true;
  try {
    const response = await axios.put(`/api/llm/models/${selectedLlmModel.value.id}/access`, {
      usernames: llmAccessUsernames.value,
      role_names: llmAccessRoleNames.value
    });
    const updatedUsers = response.data.allowed_usernames || [];
    const updatedRoles = response.data.allowed_roles || [];
    selectedLlmModel.value.allowed_usernames = updatedUsers;
    selectedLlmModel.value.allowed_roles = updatedRoles;
    selectedLlmModel.value.is_restricted = Boolean(updatedUsers.length || updatedRoles.length);
    await fetchLlmAccessOverview();
    llmAccessDialog.value = false;
  } catch (error) {
    console.error('Error saving LLM access:', error);
  } finally {
    savingLlmAccess.value = false;
  }
};

/**
 * Sync LLM models from all active providers
 */
const syncAllLlmModels = async () => {
  if (syncingLlmModels.value) return;
  syncingLlmModels.value = true;

  try {
    // Fetch all providers
    const providersResponse = await axios.get('/api/llm/providers');
    const providers = providersResponse.data.providers || [];

    // Sync each active provider that supports sync (is_openai_compatible)
    const syncPromises = providers
      .filter(p => p.is_active && p.is_openai_compatible)
      .map(provider =>
        axios.post(`/api/llm/providers/${provider.id}/sync-models`, {}).catch(err => {
          console.warn(`Failed to sync provider ${provider.name}:`, err);
          return null;
        })
      );

    await Promise.all(syncPromises);

    // Refresh the LLM models list
    await fetchLlmAccessOverview();
  } catch (error) {
    console.error('Error syncing LLM models:', error);
  } finally {
    syncingLlmModels.value = false;
    llmSyncedOnce.value = true;
  }
};

// Watch for tab changes - auto-sync LLM models when LLM tab is opened
watch(activeTab, async (newTab) => {
  if (newTab === 'llm' && !llmSyncedOnce.value) {
    await syncAllLlmModels();
  }
});

onMounted(() => {
  fetchRoles();
  fetchPermissions();
  fetchChatbotAccessOverview();
  fetchLlmAccessOverview();
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
