<template>
  <div class="llm-providers-section">
    <!-- Quick Connect Section (Fixed at top) -->
    <div class="quick-connect-section">
      <div class="quick-connect-header mb-3">
        <h3 class="text-h6 d-flex align-center">
          <LIcon class="mr-2" size="24">mdi-lightning-bolt</LIcon>
          Quick Connect
        </h3>
        <p class="text-body-2 text-medium-emphasis mt-1">
          Verbinde schnell mit populären LLM-Anbietern
        </p>
      </div>

      <div class="llars-quick-grid">
      <div
        v-for="provider in quickProviders"
        :key="provider.type"
        class="llars-quick-card"
        :class="{ 'llars-quick-card--connected': isProviderConnected(provider.type) }"
        :style="{ '--quick-card-color': `var(--llars-provider-${provider.colorVar})`, '--quick-card-bg': `var(--llars-provider-${provider.colorVar}-light)` }"
        @click="openQuickDialog(provider)"
      >
        <div class="llars-quick-card__icon-wrapper">
          <LIcon :name="provider.icon" size="26" class="llars-quick-card__icon" />
        </div>
        <div class="llars-quick-card__content">
          <h4 class="llars-quick-card__title">{{ provider.title }}</h4>
          <p class="llars-quick-card__subtitle">{{ provider.subtitle }}</p>
        </div>
        <div class="llars-quick-card__meta">
          <!-- Connected status -->
          <span v-if="isProviderConnected(provider.type)" class="llars-quick-card__badge llars-quick-card__badge--connected">
            <LIcon size="12">mdi-check-circle</LIcon>
            Verbunden
          </span>
          <!-- Not connected - show lock for all -->
          <span v-else class="llars-quick-card__badge llars-quick-card__badge--locked">
            <LIcon size="12">mdi-lock</LIcon>
            {{ provider.requires_key ? 'API Key' : 'Nicht verbunden' }}
          </span>
        </div>
        <div class="llars-quick-card__arrow">
          <LIcon size="18">mdi-chevron-right</LIcon>
        </div>
      </div>
      </div>
    </div>

    <!-- Scrollable Content Area -->
    <div class="providers-content">
      <!-- Provider Registry -->
    <v-card class="llars-card mb-4">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-database-cog</LIcon>
        Provider Registry
        <v-spacer />
        <LBtn variant="primary" size="small" @click="openCreateDialog">
          <LIcon start size="16">mdi-plus</LIcon>
          Provider hinzufügen
        </LBtn>
      </v-card-title>
      <v-card-text>
        <v-skeleton-loader v-if="loading" type="table" />

        <v-data-table
          v-else
          :headers="headers"
          :items="providers"
          :items-per-page="10"
          class="llars-table"
        >
          <template v-slot:item.name="{ item }">
            <div class="d-flex align-center">
              <div
                class="provider-icon-badge mr-3"
                :style="{ backgroundColor: getProviderColorLight(item.provider_type) }"
              >
                <LIcon
                  :name="getProviderIcon(item.provider_type)"
                  size="20"
                  :style="{ color: getProviderColor(item.provider_type) }"
                />
              </div>
              <div class="d-flex flex-column">
                <span class="font-weight-medium">{{ item.name }}</span>
                <span class="text-caption text-medium-emphasis">{{ item.provider_type }}</span>
              </div>
            </div>
          </template>

          <template v-slot:item.base_url="{ item }">
            <code class="text-caption pa-1 rounded" style="background: rgba(0,0,0,0.05)">
              {{ item.base_url || '-' }}
            </code>
          </template>

          <template v-slot:item.is_default="{ item }">
            <v-chip v-if="item.is_default" color="primary" size="small" variant="tonal" class="llars-chip">
              <LIcon start size="14">mdi-star</LIcon>
              Default
            </v-chip>
          </template>

          <template v-slot:item.is_active="{ item }">
            <v-chip
              :color="item.is_active ? 'success' : 'warning'"
              size="small"
              variant="tonal"
              class="llars-chip"
            >
              <LIcon start size="14">{{ item.is_active ? 'mdi-check-circle' : 'mdi-pause-circle' }}</LIcon>
              {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
          </template>

          <template v-slot:item.actions="{ item }">
            <div class="d-flex ga-1 justify-end">
              <LBtn size="small" variant="text" @click="testProvider(item)">
                <LIcon start size="14">mdi-connection</LIcon>
                Test
              </LBtn>
              <LBtn
                size="small"
                variant="text"
                :disabled="!item.is_openai_compatible"
                @click="syncProvider(item)"
              >
                <LIcon start size="14">mdi-sync</LIcon>
                Sync
              </LBtn>
              <LBtn size="small" variant="text" @click="openEditDialog(item)">
                <LIcon start size="14">mdi-pencil</LIcon>
                Bearbeiten
              </LBtn>
            </div>
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8 text-medium-emphasis">
              <LIcon size="48" class="mb-2" style="opacity: 0.5">mdi-database-off</LIcon>
              <div>Keine Provider verbunden</div>
              <LBtn variant="primary" size="small" class="mt-3" @click="openCreateDialog">
                Ersten Provider hinzufügen
              </LBtn>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- LLM Models -->
    <v-card class="llars-card">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-brain</LIcon>
        LLM Modelle
        <v-chip size="small" variant="tonal" class="ml-2">
          {{ llmModelsFiltered.length }}
        </v-chip>
        <v-spacer />
        <v-chip-group v-model="modelTypeFilter" selected-class="text-primary" mandatory density="compact">
          <v-chip size="small" value="llm" variant="outlined" class="llars-chip">Chat</v-chip>
          <v-chip size="small" value="embedding" variant="outlined" class="llars-chip">Embedding</v-chip>
          <v-chip size="small" value="all" variant="outlined" class="llars-chip">Alle</v-chip>
        </v-chip-group>
      </v-card-title>
      <v-card-text>
        <v-skeleton-loader v-if="llmLoading" type="table" />

        <v-data-table
          v-else
          :headers="llmHeaders"
          :items="llmModelsFiltered"
          :items-per-page="10"
          class="llars-table"
        >
          <template v-slot:item.display_name="{ item }">
            <div class="d-flex flex-column">
              <div class="d-flex align-center flex-wrap ga-2">
                <span class="font-weight-medium">{{ item.display_name }}</span>
                <v-chip
                  v-if="item.is_default"
                  color="primary"
                  size="x-small"
                  variant="tonal"
                  class="llars-chip"
                >
                  Default
                </v-chip>
              </div>
              <span class="text-caption text-medium-emphasis">{{ item.model_id }}</span>
            </div>
          </template>

          <template v-slot:item.provider_label="{ item }">
            <div class="d-flex align-center">
              <div
                class="provider-icon-badge provider-icon-badge--small mr-2"
                :style="{ backgroundColor: getProviderColorLight(item.provider_type) }"
              >
                <LIcon
                  :name="getProviderIcon(item.provider_type)"
                  size="14"
                  :style="{ color: getProviderColor(item.provider_type) }"
                />
              </div>
              <div class="d-flex flex-column">
                <span class="font-weight-medium text-body-2">
                  {{ item.provider_label || item.provider || 'Unbekannt' }}
                </span>
                <span class="text-caption text-medium-emphasis">
                  {{ item.provider_type || 'manuell' }}
                </span>
              </div>
            </div>
          </template>

          <template v-slot:item.created_by="{ item }">
            <span class="text-caption text-medium-emphasis">
              {{ item.created_by || 'System' }}
            </span>
          </template>

          <template v-slot:item.is_active="{ item }">
            <v-chip
              :color="item.is_active ? 'success' : 'warning'"
              size="small"
              variant="tonal"
              class="llars-chip"
            >
              {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
          </template>

          <template v-slot:item.is_restricted="{ item }">
            <v-chip
              :color="item.is_restricted ? 'warning' : 'success'"
              size="small"
              variant="tonal"
              class="llars-chip"
            >
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
                class="llars-chip"
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
                class="llars-chip"
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
                Alle Nutzer
              </span>
            </div>
          </template>

          <template v-slot:item.actions="{ item }">
            <LBtn size="small" variant="text" @click="openLlmAccessDialog(item)">
              <LIcon start size="14">mdi-shield-account</LIcon>
              Zugriff
            </LBtn>
          </template>

          <template v-slot:no-data>
            <div class="text-center py-8 text-medium-emphasis">
              <LIcon size="48" class="mb-2" style="opacity: 0.5">mdi-robot-off</LIcon>
              <div>Keine LLM Modelle gefunden</div>
              <p class="text-caption mt-1">Verbinde einen Provider und synchronisiere Modelle</p>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
    </div>

    <!-- Quick Connect Dialog -->
    <v-dialog v-model="quickDialog" max-width="560">
      <v-card class="llars-dialog">
        <v-card-title class="d-flex align-center pa-4">
          <div
            class="provider-icon-badge mr-3"
            :style="{ backgroundColor: activeQuick?.colorVar ? `var(--llars-provider-${activeQuick.colorVar}-light)` : 'var(--llars-provider-custom-light)' }"
          >
            <LIcon
              :name="activeQuick?.icon"
              size="24"
              :style="{ color: activeQuick?.colorVar ? `var(--llars-provider-${activeQuick.colorVar})` : 'var(--llars-provider-custom)' }"
            />
          </div>
          <div>
            <div class="text-h6">{{ activeQuick?.title }}</div>
            <div class="text-caption text-medium-emphasis">{{ activeQuick?.subtitle }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" @click="quickDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <!-- OpenAI: Model selection list -->
          <template v-if="activeQuick?.type === 'openai'">
            <v-text-field
              v-model="providerForm.api_key"
              label="API Key"
              type="password"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-4"
              placeholder="sk-..."
            />

            <div class="text-subtitle-2 mb-2">Modelle auswählen</div>

            <div v-for="group in openaiModelGroups" :key="group.label" class="mb-3">
              <div class="d-flex align-center mb-1">
                <span class="text-caption font-weight-bold text-medium-emphasis text-uppercase" style="letter-spacing: 0.5px">
                  {{ group.label }}
                </span>
                <v-divider class="ml-2" />
              </div>
              <div class="openai-model-grid">
                <div
                  v-for="model in group.models"
                  :key="model.id"
                  class="openai-model-chip"
                  :class="{ 'openai-model-chip--selected': isOpenaiModelSelected(model.id) }"
                  @click="toggleOpenaiModel(model.id)"
                >
                  <LIcon size="16" class="mr-1">{{ isOpenaiModelSelected(model.id) ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline' }}</LIcon>
                  <div class="d-flex flex-column">
                    <span class="openai-model-chip__name">{{ model.name }}</span>
                    <span class="openai-model-chip__meta">{{ model.meta }}</span>
                  </div>
                </div>
              </div>
            </div>

            <v-alert v-if="selectedOpenaiModels.length === 0" type="info" variant="tonal" density="compact" class="mt-2">
              Bitte mindestens ein Modell auswählen.
            </v-alert>

            <v-switch
              v-model="providerForm.is_default"
              label="Als Default Provider setzen"
              color="primary"
              hide-details
              density="compact"
              class="mt-2"
            />
          </template>

          <!-- Other providers: Standard form -->
          <template v-else>
            <v-text-field
              v-model="providerForm.name"
              label="Name"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-3"
            />
            <v-text-field
              v-model="providerForm.base_url"
              label="Base URL"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-3"
            />
            <v-text-field
              v-if="activeQuick?.requires_key"
              v-model="providerForm.api_key"
              label="API Key"
              type="password"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-3"
            />
            <v-text-field
              v-if="activeQuick?.supports_version"
              v-model="providerForm.api_version"
              label="API Version"
              variant="outlined"
              density="comfortable"
              hide-details
              class="mb-3"
            />
            <v-textarea
              v-if="activeQuick?.requires_models"
              v-model="providerForm.model_ids"
              label="Model IDs (kommagetrennt)"
              variant="outlined"
              density="comfortable"
              rows="2"
              auto-grow
              hide-details
              class="mb-3"
              placeholder="z.B. claude-3-opus-20240229, claude-3-sonnet-20240229"
            />
            <div class="d-flex flex-column ga-1">
              <v-switch
                v-model="providerForm.is_default"
                label="Als Default Provider setzen"
                color="primary"
                hide-details
                density="compact"
              />
              <v-switch
                v-if="activeQuick?.supports_sync"
                v-model="providerForm.sync_models"
                label="Modelle automatisch synchronisieren"
                color="primary"
                hide-details
                density="compact"
              />
            </div>
          </template>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <span v-if="activeQuick?.type === 'openai' && selectedOpenaiModels.length > 0" class="text-caption text-medium-emphasis">
            {{ selectedOpenaiModels.length }} Modell{{ selectedOpenaiModels.length !== 1 ? 'e' : '' }}
          </span>
          <v-spacer />
          <LBtn variant="text" @click="quickDialog = false">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            :loading="saving"
            :disabled="activeQuick?.type === 'openai' && (selectedOpenaiModels.length === 0 || !providerForm.api_key)"
            @click="submitQuickConnect"
            :style="{ backgroundColor: activeQuick?.colorVar ? `var(--llars-provider-${activeQuick.colorVar})` : undefined }"
          >
            <LIcon start size="16">mdi-connection</LIcon>
            Verbinden
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Provider Dialog -->
    <v-dialog v-model="editDialog" max-width="560">
      <v-card class="llars-dialog">
        <v-card-title class="d-flex align-center pa-4">
          <LIcon class="mr-2">mdi-pencil</LIcon>
          Provider bearbeiten
          <v-spacer />
          <LIconBtn icon="mdi-close" @click="editDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <v-select
            v-model="providerForm.provider_type"
            :items="providerTypeOptions"
            item-title="title"
            item-value="value"
            label="Provider Typ"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          />
          <v-text-field
            v-model="providerForm.name"
            label="Name"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          />
          <v-text-field
            v-model="providerForm.base_url"
            label="Base URL"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          />
          <v-text-field
            v-model="providerForm.api_key"
            label="API Key (leer lassen = unverändert)"
            type="password"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          />
          <v-text-field
            v-model="providerForm.api_version"
            label="API Version"
            variant="outlined"
            density="comfortable"
            hide-details
            class="mb-3"
          />
          <v-textarea
            v-model="providerForm.model_ids"
            label="Model IDs (kommagetrennt)"
            variant="outlined"
            density="comfortable"
            rows="2"
            auto-grow
            hide-details
            class="mb-3"
          />
          <div class="d-flex flex-column ga-1">
            <v-switch
              v-model="providerForm.is_default"
              label="Als Default Provider setzen"
              color="primary"
              hide-details
              density="compact"
            />
            <v-switch
              v-model="providerForm.is_active"
              label="Provider aktiv"
              color="primary"
              hide-details
              density="compact"
            />
            <v-switch
              v-model="providerForm.is_openai_compatible"
              label="OpenAI-kompatibel (Sync möglich)"
              color="primary"
              hide-details
              density="compact"
            />
          </div>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <LBtn variant="text" @click="editDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="saving" @click="saveProvider">
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- LLM Access Dialog -->
    <v-dialog v-model="llmAccessDialog" max-width="640">
      <v-card v-if="selectedLlmModel" class="llars-dialog">
        <v-card-title class="d-flex align-center pa-4">
          <LIcon class="mr-2">mdi-shield-account</LIcon>
          <div>
            <div>Zugriff: {{ selectedLlmModel.display_name }}</div>
            <div class="text-caption text-medium-emphasis font-weight-regular">
              {{ selectedLlmModel.model_id }}
            </div>
          </div>
          <v-spacer />
          <v-chip
            v-if="selectedLlmModel.is_default"
            color="primary"
            size="x-small"
            variant="tonal"
            class="mr-2"
          >
            Default
          </v-chip>
          <LIconBtn icon="mdi-close" @click="llmAccessDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4">
          <div class="d-flex align-center mb-4 pa-3 rounded" style="background: rgba(0,0,0,0.03)">
            <div
              class="provider-icon-badge mr-3"
              :style="{ backgroundColor: getProviderColorLight(selectedLlmModel.provider_type) }"
            >
              <LIcon
                :name="getProviderIcon(selectedLlmModel.provider_type)"
                size="20"
                :style="{ color: getProviderColor(selectedLlmModel.provider_type) }"
              />
            </div>
            <div class="text-body-2">
              <strong>{{ selectedLlmModel.provider_label || selectedLlmModel.provider || 'Unbekannt' }}</strong>
              <span v-if="selectedLlmModel.provider_type" class="text-medium-emphasis">
                ({{ selectedLlmModel.provider_type }})
              </span>
            </div>
          </div>

          <v-switch
            v-model="llmIsPublic"
            label="Public (für alle sichtbar)"
            color="primary"
            hide-details
            class="mb-4"
          />

          <v-alert
            v-if="llmIsPublic"
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            Dieses Modell ist für alle Nutzer sichtbar.
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
            :disabled="llmIsPublic"
            class="mb-3"
          />
          <v-autocomplete
            v-model="llmAccessRoleNames"
            :items="roles"
            item-title="display_name"
            item-value="role_name"
            label="Erlaubte Rollen"
            multiple
            chips
            closable-chips
            clearable
            variant="outlined"
            density="comfortable"
            hide-details
            :disabled="llmIsPublic"
          />

          <v-alert
            v-if="!llmIsPublic && !llmAccessUsernames.length && !llmAccessRoleNames.length"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-3"
          >
            Ohne Auswahl bleibt das Modell faktisch öffentlich sichtbar.
          </v-alert>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <LBtn variant="text" @click="llmAccessDialog = false">Abbrechen</LBtn>
          <LBtn variant="primary" :loading="savingLlmAccess" @click="saveLlmAccess">
            Speichern
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { logI18n } from '@/utils/logI18n'

const providers = ref([])
const loading = ref(false)
const saving = ref(false)

const llmModels = ref([])
const llmLoading = ref(false)
const llmAccessDialog = ref(false)
const selectedLlmModel = ref(null)
const llmAccessUsernames = ref([])
const llmAccessRoleNames = ref([])
const savingLlmAccess = ref(false)
const roles = ref([])
const allUsernames = ref([])
const llmIsPublic = ref(true)
const modelTypeFilter = ref('llm')

const quickDialog = ref(false)
const editDialog = ref(false)
const activeQuick = ref(null)

const providerForm = ref({
  id: null,
  provider_type: '',
  name: '',
  base_url: '',
  api_key: '',
  api_version: '',
  model_ids: '',
  is_default: false,
  is_active: true,
  is_openai_compatible: true,
  sync_models: false
})

const snackbar = ref({ show: false, text: '', color: 'info' })

const headers = [
  { title: 'Provider', key: 'name', sortable: true },
  { title: 'Base URL', key: 'base_url', sortable: false },
  { title: 'Default', key: 'is_default', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: '', key: 'actions', sortable: false, align: 'end' }
]

const llmHeaders = [
  { title: 'Modell', key: 'display_name', sortable: true },
  { title: 'Provider', key: 'provider_label', sortable: true },
  { title: 'Erstellt von', key: 'created_by', sortable: true },
  { title: 'Status', key: 'is_active', sortable: true },
  { title: 'Sichtbarkeit', key: 'is_restricted', sortable: true },
  { title: 'Zuweisungen', key: 'allowed_usernames', sortable: false },
  { title: '', key: 'actions', sortable: false, align: 'end' }
]

// Provider configurations - colors reference global CSS variables
const quickProviders = [
  {
    type: 'openai',
    title: 'OpenAI',
    subtitle: 'GPT-5, GPT-4, o3, o4',
    base_url: 'https://api.openai.com/v1',
    icon: 'openai',
    colorVar: 'openai',
    requires_key: true,
    supports_sync: false
  },
  {
    type: 'anthropic',
    title: 'Anthropic',
    subtitle: 'Claude 3.5, Claude 4',
    base_url: 'https://api.anthropic.com',
    icon: 'claude',
    colorVar: 'anthropic',
    requires_key: true,
    requires_models: true,
    supports_version: true,
    supports_sync: false
  },
  {
    type: 'gemini',
    title: 'Google Gemini',
    subtitle: 'Gemini 2.0, 1.5 Pro',
    base_url: 'https://generativelanguage.googleapis.com',
    icon: 'gemini',
    colorVar: 'gemini',
    requires_key: true,
    requires_models: true,
    supports_version: true,
    supports_sync: false
  },
  {
    type: 'ollama',
    title: 'Ollama',
    subtitle: 'Lokale Modelle',
    base_url: 'http://host.docker.internal:11434/v1',
    icon: 'ollama',
    colorVar: 'ollama',
    requires_key: false,
    supports_sync: true
  },
  {
    type: 'vllm',
    title: 'vLLM',
    subtitle: 'Self-hosted Inference',
    base_url: 'http://host.docker.internal:8000/v1',
    icon: 'vllm',
    colorVar: 'vllm',
    requires_key: false,
    supports_sync: true
  },
  {
    type: 'litellm',
    title: 'LiteLLM',
    subtitle: 'Universal Proxy',
    base_url: 'https://kiz1.in.ohmportal.de/llmproxy/v1',
    icon: 'litellm',
    colorVar: 'litellm',
    requires_key: false,
    supports_sync: true
  }
]

// Provider icon mapping - colors use global CSS variables
const providerMeta = {
  openai: { icon: 'openai', colorVar: 'openai' },
  anthropic: { icon: 'claude', colorVar: 'anthropic' },
  gemini: { icon: 'gemini', colorVar: 'gemini' },
  ollama: { icon: 'ollama', colorVar: 'ollama' },
  vllm: { icon: 'vllm', colorVar: 'vllm' },
  litellm: { icon: 'litellm', colorVar: 'litellm' },
  openai_compatible: { icon: 'openai', colorVar: 'openai' },
  custom: { icon: 'database', colorVar: 'custom' },
}

// Helper to get provider color as CSS variable reference
function getProviderColor(providerType) {
  const colorVar = providerMeta[providerType]?.colorVar || 'custom'
  return `var(--llars-provider-${colorVar})`
}

// Helper to get provider light color as CSS variable reference
function getProviderColorLight(providerType) {
  const colorVar = providerMeta[providerType]?.colorVar || 'custom'
  return `var(--llars-provider-${colorVar}-light)`
}

// Helper to get provider icon
function getProviderIcon(providerType) {
  return providerMeta[providerType]?.icon || 'database'
}

// Check if a provider type is already connected
function isProviderConnected(providerType) {
  return providers.value.some(p => p.provider_type === providerType && p.is_active)
}

function resetProviderForm() {
  providerForm.value = {
    id: null,
    provider_type: '',
    name: '',
    base_url: '',
    api_key: '',
    api_version: '',
    model_ids: '',
    is_default: false,
    is_active: true,
    is_openai_compatible: true,
    sync_models: false
  }
}

function showMessage(text, color = 'info') {
  snackbar.value = { show: true, text, color }
}

const providerTypeOptions = [
  { title: 'OpenAI', value: 'openai' },
  { title: 'OpenAI kompatibel', value: 'openai_compatible' },
  { title: 'Ollama', value: 'ollama' },
  { title: 'vLLM', value: 'vllm' },
  { title: 'LiteLLM Proxy', value: 'litellm' },
  { title: 'Anthropic (Claude)', value: 'anthropic' },
  { title: 'Google Gemini', value: 'gemini' },
  { title: 'Custom', value: 'custom' }
]

// ── OpenAI Model Catalog ────────────────────────────────────────────────
const OPENAI_MODELS = [
  // GPT-5 Series
  { id: 'gpt-5.2', name: 'GPT-5.2', group: 'GPT-5', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5.1', name: 'GPT-5.1', group: 'GPT-5', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5', name: 'GPT-5', group: 'GPT-5', meta: '400K ctx · 128K out', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: true },
  { id: 'gpt-5-mini', name: 'GPT-5 Mini', group: 'GPT-5', meta: '400K ctx · 128K out · schnell', context_window: 400000, max_output_tokens: 128000, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-5-nano', name: 'GPT-5 Nano', group: 'GPT-5', meta: '400K ctx · 16K out · ultra-schnell', context_window: 400000, max_output_tokens: 16384, supports_vision: false, supports_reasoning: false },
  // GPT-4 Series
  { id: 'gpt-4.1', name: 'GPT-4.1', group: 'GPT-4', meta: '1M ctx · 32K out', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', group: 'GPT-4', meta: '1M ctx · 32K out · schnell', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4.1-nano', name: 'GPT-4.1 Nano', group: 'GPT-4', meta: '1M ctx · 32K out · ultra-schnell', context_window: 1047576, max_output_tokens: 32768, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4o', name: 'GPT-4o', group: 'GPT-4', meta: '128K ctx · 16K out', context_window: 128000, max_output_tokens: 16384, supports_vision: true, supports_reasoning: false },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', group: 'GPT-4', meta: '128K ctx · 16K out · schnell', context_window: 128000, max_output_tokens: 16384, supports_vision: true, supports_reasoning: false },
  // Reasoning (o-Series)
  { id: 'o3', name: 'o3', group: 'Reasoning', meta: '200K ctx · 100K out', context_window: 200000, max_output_tokens: 100000, supports_vision: true, supports_reasoning: true },
  { id: 'o3-mini', name: 'o3 Mini', group: 'Reasoning', meta: '200K ctx · 100K out · schnell', context_window: 200000, max_output_tokens: 100000, supports_vision: false, supports_reasoning: true },
  { id: 'o4-mini', name: 'o4 Mini', group: 'Reasoning', meta: '200K ctx · 100K out · schnell', context_window: 200000, max_output_tokens: 100000, supports_vision: true, supports_reasoning: true },
]

const selectedOpenaiModels = ref([])

const openaiModelGroups = computed(() => {
  const groups = {}
  for (const m of OPENAI_MODELS) {
    if (!groups[m.group]) groups[m.group] = { label: m.group, models: [] }
    groups[m.group].models.push(m)
  }
  return Object.values(groups)
})

function isOpenaiModelSelected(modelId) {
  return selectedOpenaiModels.value.includes(modelId)
}

function toggleOpenaiModel(modelId) {
  const idx = selectedOpenaiModels.value.indexOf(modelId)
  if (idx >= 0) {
    selectedOpenaiModels.value.splice(idx, 1)
  } else {
    selectedOpenaiModels.value.push(modelId)
  }
}

const llmModelsFiltered = computed(() => {
  if (modelTypeFilter.value === 'all') {
    return llmModels.value || []
  }
  return (llmModels.value || []).filter(model => model.model_type === modelTypeFilter.value)
})

async function fetchProviders() {
  loading.value = true
  try {
    const response = await axios.get('/api/llm/providers')
    providers.value = response.data.providers || []
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.loadProvidersFailed', error)
    providers.value = []
  } finally {
    loading.value = false
  }
}

function openQuickDialog(template) {
  resetProviderForm()
  activeQuick.value = template
  providerForm.value.provider_type = template.type
  providerForm.value.name = template.title
  providerForm.value.base_url = template.base_url
  providerForm.value.is_openai_compatible = template.supports_sync === true || template.type === 'openai'
  providerForm.value.is_active = true
  providerForm.value.is_default = false
  providerForm.value.sync_models = Boolean(template.supports_sync)
  if (template.supports_version) {
    providerForm.value.api_version = template.type === 'anthropic' ? '2023-06-01' : 'v1beta'
  }
  // Reset OpenAI model selection
  selectedOpenaiModels.value = []
  quickDialog.value = true
}

function openCreateDialog() {
  resetProviderForm()
  activeQuick.value = null
  editDialog.value = true
}

function openEditDialog(provider) {
  resetProviderForm()
  providerForm.value.id = provider.id
  providerForm.value.provider_type = provider.provider_type
  providerForm.value.name = provider.name
  providerForm.value.base_url = provider.base_url || ''
  providerForm.value.is_default = provider.is_default
  providerForm.value.is_active = provider.is_active
  providerForm.value.is_openai_compatible = provider.is_openai_compatible
  providerForm.value.api_version = provider.config?.api_version || ''
  editDialog.value = true
}

function parseModelIds(input) {
  return (input || '')
    .split(/[,\n]/)
    .map(s => s.trim())
    .filter(Boolean)
}

async function submitQuickConnect() {
  saving.value = true
  try {
    const isOpenai = activeQuick.value?.type === 'openai'

    // For OpenAI: auto-generate name and use selected models
    const modelIds = isOpenai
      ? selectedOpenaiModels.value
      : parseModelIds(providerForm.value.model_ids)

    const providerName = isOpenai
      ? 'OpenAI'
      : providerForm.value.name

    const payload = {
      provider_type: providerForm.value.provider_type,
      name: providerName,
      base_url: providerForm.value.base_url,
      is_default: providerForm.value.is_default,
      is_active: providerForm.value.is_active,
      is_openai_compatible: providerForm.value.is_openai_compatible,
      sync_models: false,
      model_ids: modelIds,
      config: providerForm.value.api_version
        ? { api_version: providerForm.value.api_version }
        : {},
      // Pass OpenAI model metadata for proper registration
      model_metadata: isOpenai
        ? buildOpenaiModelMetadata()
        : undefined
    }
    if (providerForm.value.api_key) {
      payload.api_key = providerForm.value.api_key
    }

    // Test connection first before saving
    showMessage('Teste Verbindung...', 'info')
    const testResponse = await axios.post('/api/llm/providers/test-connection', {
      base_url: payload.base_url,
      api_key: payload.api_key,
      provider_type: payload.provider_type,
      config: payload.config
    })

    if (!testResponse.data.success) {
      showMessage(testResponse.data.error || 'Verbindung fehlgeschlagen', 'error')
      return
    }

    // Connection successful, now save
    await axios.post('/api/llm/providers', payload)
    const modelCount = modelIds.length
    showMessage(`OpenAI verbunden · ${modelCount} Modell${modelCount !== 1 ? 'e' : ''} hinzugefügt`, 'success')
    quickDialog.value = false
    await fetchProviders()
    await fetchLlmAccessOverview()
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.quickConnectFailed', error)
    const errorMsg = error.response?.data?.error || error.response?.data?.message || 'Verbindung fehlgeschlagen'
    showMessage(errorMsg, 'error')
  } finally {
    saving.value = false
  }
}

function buildOpenaiModelMetadata() {
  const meta = {}
  for (const modelId of selectedOpenaiModels.value) {
    const model = OPENAI_MODELS.find(m => m.id === modelId)
    if (model) {
      meta[modelId] = {
        display_name: model.name,
        context_window: model.context_window,
        max_output_tokens: model.max_output_tokens,
        supports_vision: model.supports_vision,
        supports_reasoning: model.supports_reasoning,
      }
    }
  }
  return meta
}

async function saveProvider() {
  saving.value = true
  try {
    if (!providerForm.value.provider_type) {
      showMessage('Provider Typ erforderlich', 'error')
      saving.value = false
      return
    }
    const payload = {
      provider_type: providerForm.value.provider_type,
      name: providerForm.value.name,
      base_url: providerForm.value.base_url,
      is_default: providerForm.value.is_default,
      is_active: providerForm.value.is_active,
      is_openai_compatible: providerForm.value.is_openai_compatible,
      model_ids: parseModelIds(providerForm.value.model_ids),
      config: providerForm.value.api_version
        ? { api_version: providerForm.value.api_version }
        : {}
    }
    if (providerForm.value.api_key) {
      payload.api_key = providerForm.value.api_key
    }

    if (providerForm.value.id) {
      await axios.put(`/api/llm/providers/${providerForm.value.id}`, payload)
    } else {
      await axios.post('/api/llm/providers', payload)
    }
    showMessage('Provider gespeichert', 'success')
    editDialog.value = false
    await fetchProviders()
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.saveProviderFailed', error)
    showMessage('Speichern fehlgeschlagen', 'error')
  } finally {
    saving.value = false
  }
}

async function testProvider(provider) {
  try {
    const response = await axios.post(`/api/llm/providers/${provider.id}/test`)
    showMessage(response.data.message || 'Verbindung OK', 'success')
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.providerTestFailed', error)
    showMessage(error.response?.data?.error || 'Verbindung fehlgeschlagen', 'error')
  }
}

async function syncProvider(provider) {
  try {
    const response = await axios.post(`/api/llm/providers/${provider.id}/sync-models`)
    showMessage(`Sync: ${response.data.inserted || 0} neu, ${response.data.updated || 0} aktualisiert`, 'success')
    await fetchLlmAccessOverview()
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.modelSyncFailed', error)
    showMessage(error.response?.data?.error || 'Sync fehlgeschlagen', 'error')
  }
}

async function fetchLlmAccessOverview() {
  llmLoading.value = true
  try {
    const response = await axios.get('/api/llm/models/access/overview?include_inactive=true')
    llmModels.value = response.data.models || []
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.loadModelsFailed', error)
    llmModels.value = []
  } finally {
    llmLoading.value = false
  }
}

async function fetchRoles() {
  try {
    const response = await axios.get('/api/permissions/roles')
    roles.value = response.data.roles || []
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.loadRolesFailed', error)
    roles.value = []
  }
}

async function fetchUsersForAccess() {
  try {
    const response = await axios.get('/api/permissions/users-with-roles')
    const users = response.data.users || response.data.data || []
    allUsernames.value = users.map(u => u.username).filter(Boolean).sort()
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.loadUsersFailed', error)
    allUsernames.value = []
  }
}

async function openLlmAccessDialog(model) {
  selectedLlmModel.value = model
  llmAccessUsernames.value = [...(model.allowed_usernames || [])]
  llmAccessRoleNames.value = [...(model.allowed_roles || [])]
  llmIsPublic.value = !llmAccessUsernames.value.length && !llmAccessRoleNames.value.length
  llmAccessDialog.value = true

  if (!allUsernames.value.length) {
    await fetchUsersForAccess()
  }
  if (!roles.value.length) {
    await fetchRoles()
  }
}

watch(llmIsPublic, (value) => {
  if (value) {
    llmAccessUsernames.value = []
    llmAccessRoleNames.value = []
  }
})

async function saveLlmAccess() {
  if (!selectedLlmModel.value) return
  savingLlmAccess.value = true
  try {
    const response = await axios.put(`/api/llm/models/${selectedLlmModel.value.id}/access`, {
      usernames: llmAccessUsernames.value,
      role_names: llmAccessRoleNames.value
    })
    const updatedUsers = response.data.allowed_usernames || []
    const updatedRoles = response.data.allowed_roles || []
    selectedLlmModel.value.allowed_usernames = updatedUsers
    selectedLlmModel.value.allowed_roles = updatedRoles
    selectedLlmModel.value.is_restricted = Boolean(updatedUsers.length || updatedRoles.length)
    llmIsPublic.value = !selectedLlmModel.value.is_restricted
    await fetchLlmAccessOverview()
    llmAccessDialog.value = false
    showMessage('Zugriff gespeichert', 'success')
  } catch (error) {
    logI18n('error', 'logs.admin.llmProviders.saveAccessFailed', error)
    showMessage('Zugriff speichern fehlgeschlagen', 'error')
  } finally {
    savingLlmAccess.value = false
  }
}

onMounted(() => {
  fetchProviders()
  fetchLlmAccessOverview()
})
</script>

<style scoped>
/* Full viewport layout */
.llm-providers-section {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

/* Fixed top section for Quick Connect */
.quick-connect-section {
  flex-shrink: 0;
  padding-bottom: 16px;
}

.quick-connect-header {
  padding: 0 4px;
}

/* Scrollable content area */
.providers-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px; /* Space for scrollbar */
}

/* Provider icon badge */
.provider-icon-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--llars-radius-sm);
  flex-shrink: 0;
}

.provider-icon-badge--small {
  width: 28px;
  height: 28px;
  border-radius: var(--llars-radius-xs);
}

/* LLARS Card styling */
.llars-card {
  border-radius: var(--llars-radius) !important;
  overflow: hidden;
}

.llars-dialog {
  border-radius: var(--llars-radius) !important;
}

.llars-chip {
  border-radius: var(--llars-radius-xs) !important;
}

.llars-table :deep(th) {
  font-weight: 600 !important;
  text-transform: uppercase;
  font-size: 11px !important;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6) !important;
}

/* OpenAI Model Selection */
.openai-model-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.openai-model-chip {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  border-radius: var(--llars-radius-xs);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}

.openai-model-chip:hover {
  border-color: var(--llars-provider-openai);
  background: rgba(0, 0, 0, 0.02);
}

.openai-model-chip--selected {
  border-color: var(--llars-provider-openai);
  background: var(--llars-provider-openai-light);
}

.openai-model-chip__name {
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
}

.openai-model-chip__meta {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  line-height: 1.2;
}
</style>
