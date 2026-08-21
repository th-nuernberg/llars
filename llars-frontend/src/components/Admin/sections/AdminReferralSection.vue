<template>
  <div class="admin-referral-section">
    <!-- Header with Analytics Overview -->
    <LCard :title="$t('admin.referral.title')" icon="mdi-account-group" class="mb-4">
      <template #actions>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          @click="showCreateCampaignDialog = true"
        >
          {{ $t('admin.referral.newCampaign') }}
        </LBtn>
      </template>

      <!-- Analytics Overview -->
      <div v-if="overview" class="analytics-overview mb-4">
        <v-row dense>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ overview.total_campaigns }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.campaigns') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-success">{{ overview.active_campaigns }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.active') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ overview.total_links }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.links') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-info">{{ overview.total_clicks || 0 }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.clicks') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value text-primary">{{ overview.total_registrations }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.registrations') }}</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-card">
              <div class="stat-value">{{ formatConversion(overview.conversion_rate) }}</div>
              <div class="stat-label">{{ $t('admin.referral.stats.conversion') }}</div>
            </div>
          </v-col>
        </v-row>

        <v-row dense class="mt-2">
          <v-col cols="12" sm="6">
            <v-alert
              :type="overview.referral_enabled ? 'success' : 'warning'"
              variant="tonal"
              density="compact"
            >
              <template #prepend>
                <v-icon>{{ overview.referral_enabled ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              </template>
              {{ overview.referral_enabled ? $t('admin.referral.systemStatus.referralEnabled') : $t('admin.referral.systemStatus.referralDisabled') }}
            </v-alert>
          </v-col>
          <v-col cols="12" sm="6">
            <v-alert
              :type="overview.self_registration_enabled ? 'success' : 'warning'"
              variant="tonal"
              density="compact"
            >
              <template #prepend>
                <v-icon>{{ overview.self_registration_enabled ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
              </template>
              {{ overview.self_registration_enabled ? $t('admin.referral.systemStatus.selfRegEnabled') : $t('admin.referral.systemStatus.selfRegDisabled') }}
            </v-alert>
          </v-col>
        </v-row>
      </div>

      <v-skeleton-loader v-else type="article" />
    </LCard>

    <!-- Campaigns List -->
    <LCard :title="$t('admin.referral.campaigns.title')" icon="mdi-bullhorn" class="mb-4">
      <template #actions>
        <v-checkbox
          v-model="showArchived"
          :label="$t('admin.referral.campaigns.showArchived')"
          density="compact"
          hide-details
          class="mr-2"
        />
      </template>

      <v-data-table
        :headers="campaignHeaders"
        :items="campaigns"
        :loading="loading"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Status Column -->
        <template #item.status="{ item }">
          <LTag :variant="getStatusVariant(item.status)" size="sm">
            {{ getStatusLabel(item.status) }}
          </LTag>
        </template>

        <!-- Links Column -->
        <template #item.link_count="{ item }">
          <v-chip size="small" variant="outlined">
            {{ item.link_count }} Links
          </v-chip>
        </template>

        <!-- Dates Column -->
        <template #item.dates="{ item }">
          <span class="text-caption">
            {{ formatDateRange(item.start_date, item.end_date) }}
          </span>
        </template>

        <!-- Actions Column -->
        <template #item.actions="{ item }">
          <LActionGroup
            :actions="getCampaignActions(item)"
            @action="handleCampaignAction($event, item)"
            size="small"
          />
        </template>
      </v-data-table>
    </LCard>

    <!-- Selected Campaign Details -->
    <LCard
      v-if="selectedCampaign"
      :title="`${selectedCampaign.name}`"
      icon="mdi-link-variant"
      class="mb-4"
    >
      <template #actions>
        <LBtn
          variant="primary"
          size="small"
          prepend-icon="mdi-plus"
          @click="showCreateLinkDialog = true"
        >
          {{ $t('admin.referral.campaigns.newLink') }}
        </LBtn>
        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-close"
          @click="selectedCampaign = null"
          class="ml-2"
        >
          {{ $t('admin.referral.campaigns.close') }}
        </LBtn>
      </template>

      <!-- Campaign Info -->
      <v-row dense class="mb-4">
        <v-col cols="12" md="6">
          <div class="text-subtitle-2 mb-1">{{ $t('admin.referral.campaigns.description') }}</div>
          <div class="text-body-2">{{ selectedCampaign.description || $t('admin.referral.campaigns.noDescription') }}</div>
        </v-col>
        <v-col cols="12" md="3">
          <div class="text-subtitle-2 mb-1">{{ $t('admin.referral.campaigns.status') }}</div>
          <v-select
            v-model="selectedCampaign.status"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            @update:model-value="updateCampaignStatus"
          />
        </v-col>
        <v-col cols="12" md="3">
          <div class="text-subtitle-2 mb-1">{{ $t('admin.referral.campaigns.maxRegistrations') }}</div>
          <div class="text-body-2">{{ selectedCampaign.max_registrations || $t('admin.referral.campaigns.unlimited') }}</div>
        </v-col>
      </v-row>

      <!-- Links Table -->
      <v-data-table
        :headers="linkHeaders"
        :items="campaignLinks"
        :loading="linksLoading"
        :items-per-page="5"
        class="elevation-0"
      >
        <!-- Code/Slug Column -->
        <template #item.identifier="{ item }">
          <div class="d-flex align-center">
            <!-- Inline color editor: swatch shows the link's resolved badge
                 color and opens a preset menu (or "Auto" to clear the override). -->
            <v-menu :close-on-content-click="true" location="bottom start">
              <template #activator="{ props }">
                <button
                  v-bind="props"
                  type="button"
                  class="ref-color-swatch mr-2"
                  :style="{ backgroundColor: item.color }"
                  :title="$t('admin.referral.table.color')"
                />
              </template>
              <div class="ref-color-menu">
                <button
                  v-for="c in colorPresets"
                  :key="c"
                  type="button"
                  class="ref-color-swatch ref-color-swatch--option"
                  :class="{ 'is-selected': (item.color_custom || '').toLowerCase() === c.toLowerCase() }"
                  :style="{ backgroundColor: c }"
                  @click="setLinkColor(item, c)"
                />
                <button type="button" class="ref-color-auto" @click="setLinkColor(item, '')">
                  {{ $t('admin.referral.table.colorAuto') }}
                </button>
              </div>
            </v-menu>
            <code class="text-primary">{{ item.slug || item.code }}</code>
            <v-btn
              icon
              size="x-small"
              variant="text"
              @click="copyLink(item)"
              class="ml-1"
            >
              <v-icon size="small">mdi-content-copy</v-icon>
            </v-btn>
          </div>
          <div v-if="item.label" class="text-caption text-medium-emphasis">{{ item.label }}</div>
        </template>

        <!-- Role Column -->
        <template #item.role_name="{ item }">
          <LTag variant="info" size="sm">{{ item.role_name }}</LTag>
        </template>

        <!-- Stats Column: funnel Aufrufe (clicks) -> Registrierungen -->
        <template #item.stats="{ item }">
          <div class="d-flex align-center" style="gap: 6px;">
            <span :title="$t('admin.referral.table.headers.clicks')">
              <v-icon size="x-small" class="mr-1">mdi-eye-outline</v-icon>{{ item.click_count || 0 }}
            </span>
            <v-icon size="x-small" class="text-medium-emphasis">mdi-arrow-right</v-icon>
            <span :title="$t('admin.referral.table.headers.registrations')">
              <v-icon size="x-small" class="mr-1">mdi-account-check-outline</v-icon>{{ item.registrations || 0 }}<span
                v-if="item.max_uses"
                class="text-medium-emphasis"
              > / {{ item.max_uses }}</span>
            </span>
            <span
              v-if="item.click_count"
              class="text-caption text-medium-emphasis"
            >({{ formatConversion(item.conversion_rate) }})</span>
          </div>
        </template>

        <!-- Active Column -->
        <template #item.is_active="{ item }">
          <v-switch
            :model-value="item.is_active"
            @update:model-value="toggleLinkActive(item, $event)"
            color="success"
            density="compact"
            hide-details
          />
        </template>

        <!-- Invitations funnel (invited / accepted / pending) -->
        <template #item.invitations="{ item }">
          <div class="text-caption">
            <span>{{ $t('admin.referral.invitations.invited') }}: {{ linkStats[item.id]?.invited ?? '–' }}</span>
            <span class="ml-2 text-success">{{ $t('admin.referral.invitations.accepted') }}: {{ linkStats[item.id]?.accepted ?? '–' }}</span>
            <span class="ml-2 text-warning">{{ $t('admin.referral.invitations.pending') }}: {{ linkStats[item.id]?.pending ?? '–' }}</span>
          </div>
          <div v-if="linkStats[item.id]?.registered_unmatched" class="text-caption text-medium-emphasis">
            +{{ linkStats[item.id].registered_unmatched }} {{ $t('admin.referral.invitations.unmatched') }}
          </div>
        </template>

        <!-- Actions Column -->
        <template #item.actions="{ item }">
          <LIconBtn
            icon="mdi-qrcode"
            variant="primary"
            size="small"
            class="mr-1"
            :tooltip="$t('admin.referral.qr.showTooltip')"
            @click="openQrDialog(item)"
          />
          <LBtn
            variant="secondary"
            size="x-small"
            prepend-icon="mdi-email-fast-outline"
            class="mr-1"
            @click="openInviteDialog(item)"
          >
            {{ $t('admin.referral.invitations.inviteBtn') }}
          </LBtn>
          <LIconBtn
            icon="mdi-email-edit-outline"
            variant="default"
            size="small"
            class="mr-1"
            :tooltip="$t('admin.referral.welcomeMail.editTooltip')"
            @click="openWelcomeDialog(item)"
          />
          <v-btn
            icon
            size="small"
            variant="text"
            color="error"
            @click="confirmDeleteLink(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </LCard>

    <!-- Invite Dialog (per link) -->
    <v-dialog v-model="showInviteDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-email-fast-outline</v-icon>
          {{ $t('admin.referral.invitations.dialogTitle') }}
        </v-card-title>
        <v-card-text>
          <p class="text-caption text-medium-emphasis mb-3">
            {{ $t('admin.referral.invitations.dialogHelp', { link: inviteLink ? (inviteLink.slug || inviteLink.code) : '' }) }}
          </p>
          <v-textarea
            v-model="inviteRecipients"
            :label="$t('admin.referral.invitations.recipients')"
            :hint="$t('admin.referral.invitations.recipientsHint')"
            variant="outlined"
            density="comfortable"
            rows="3"
            class="mb-3"
          />
          <v-textarea
            v-model="inviteIntro"
            :label="$t('admin.referral.invitations.intro')"
            variant="outlined"
            density="comfortable"
            rows="2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showInviteDialog = false">{{ $t('admin.referral.deleteDialog.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="inviting" :disabled="!inviteRecipients.trim()" @click="sendInvites">
            {{ $t('admin.referral.invitations.sendBtn') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- QR Code Dialog (per link) -->
    <LQrCodeDialog
      v-model="showQrDialog"
      :url="qrUrl"
      :filename-base="qrFilenameBase"
    />

    <!-- Recent Registrations -->
    <LCard :title="$t('admin.referral.recentRegistrations.title')" icon="mdi-account-check" class="mb-4">
      <template #actions>
        <v-btn
          v-if="selectedCampaign"
          variant="text"
          size="small"
          @click="filterRegistrationsByCampaign"
        >
          {{ $t('admin.referral.recentRegistrations.filterOnly', { name: selectedCampaign.name }) }}
        </v-btn>
        <v-btn
          v-if="registrationFilter"
          variant="text"
          size="small"
          color="error"
          @click="clearRegistrationFilter"
        >
          {{ $t('admin.referral.recentRegistrations.clearFilter') }}
        </v-btn>
      </template>

      <v-data-table
        :headers="registrationHeaders"
        :items="registrations"
        :loading="registrationsLoading"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Username Column -->
        <template #item.username="{ item }">
          <div class="d-flex align-center">
            <LAvatar
              :username="item.username"
              :seed="item.avatar_seed"
              :src="item.avatar_url"
              size="sm"
              class="mr-2"
            />
            <span class="font-weight-medium">{{ item.username }}</span>
          </div>
        </template>

        <!-- Source Column (Link/Campaign) -->
        <template #item.source="{ item }">
          <div>
            <code class="text-primary text-caption">{{ item.link_slug || item.link_code }}</code>
            <span v-if="item.link_label" class="text-caption text-medium-emphasis ml-1">
              ({{ item.link_label }})
            </span>
          </div>
          <div class="text-caption text-medium-emphasis">
            {{ item.campaign_name }}
          </div>
        </template>

        <!-- Role Column -->
        <template #item.role_assigned="{ item }">
          <LTag variant="info" size="sm">{{ item.role_assigned }}</LTag>
        </template>

        <!-- Date Column -->
        <template #item.registered_at="{ item }">
          <span class="text-caption">{{ formatDateTime(item.registered_at) }}</span>
        </template>
      </v-data-table>

      <div v-if="registrationTotal > registrations.length" class="text-center mt-2">
        <v-btn variant="text" size="small" @click="loadMoreRegistrations">
          {{ $t('admin.referral.recentRegistrations.loadMore', { count: registrationTotal - registrations.length }) }}
        </v-btn>
      </div>
    </LCard>

    <!-- Create Campaign Dialog -->
    <v-dialog v-model="showCreateCampaignDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-bullhorn-variant</v-icon>
          {{ $t('admin.referral.createCampaignDialog.title') }}
        </v-card-title>
        <v-card-text>
          <v-form ref="campaignForm" v-model="campaignFormValid">
            <v-text-field
              v-model="newCampaign.name"
              :label="$t('admin.referral.createCampaignDialog.name')"
              :rules="[v => !!v || $t('admin.referral.createCampaignDialog.nameRequired')]"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <v-textarea
              v-model="newCampaign.description"
              :label="$t('admin.referral.createCampaignDialog.description')"
              variant="outlined"
              density="comfortable"
              rows="2"
              class="mb-3"
            />
            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model="newCampaign.start_date"
                  :label="$t('admin.referral.createCampaignDialog.startDate')"
                  type="datetime-local"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="newCampaign.end_date"
                  :label="$t('admin.referral.createCampaignDialog.endDate')"
                  type="datetime-local"
                  variant="outlined"
                  density="comfortable"
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model.number="newCampaign.max_registrations"
              :label="$t('admin.referral.createCampaignDialog.maxRegistrations')"
              type="number"
              variant="outlined"
              density="comfortable"
              :hint="$t('admin.referral.createCampaignDialog.unlimitedHint')"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showCreateCampaignDialog = false">{{ $t('admin.referral.createCampaignDialog.cancel') }}</LBtn>
          <LBtn
            variant="primary"
            @click="createCampaign"
            :loading="creating"
            :disabled="!campaignFormValid"
          >
            {{ $t('admin.referral.createCampaignDialog.create') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Create Link Dialog -->
    <v-dialog v-model="showCreateLinkDialog" max-width="500">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-link-plus</v-icon>
          {{ $t('admin.referral.createLinkDialog.title') }}
        </v-card-title>
        <v-card-text>
          <v-form ref="linkForm" v-model="linkFormValid">
            <v-text-field
              v-model="newLink.slug"
              :label="$t('admin.referral.createLinkDialog.customSlug')"
              variant="outlined"
              density="comfortable"
              :hint="$t('admin.referral.createLinkDialog.slugHint')"
              persistent-hint
              class="mb-3"
              :rules="slugRules"
            />
            <v-text-field
              v-model="newLink.label"
              :label="$t('admin.referral.createLinkDialog.label')"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <!-- Badge color for this link (Auto = deterministic backend color) -->
            <div class="mb-3">
              <div class="ref-color-caption">{{ $t('admin.referral.createLinkDialog.color') }}</div>
              <div class="ref-color-row">
                <button
                  v-for="c in colorPresets"
                  :key="c"
                  type="button"
                  class="ref-color-swatch ref-color-swatch--option"
                  :class="{ 'is-selected': (newLink.color || '').toLowerCase() === c.toLowerCase() }"
                  :style="{ backgroundColor: c }"
                  @click="newLink.color = c"
                />
                <button
                  type="button"
                  class="ref-color-auto"
                  :class="{ 'is-selected': !newLink.color }"
                  @click="newLink.color = ''"
                >
                  {{ $t('admin.referral.createLinkDialog.colorAuto') }}
                </button>
              </div>
            </div>
            <v-select
              v-model="newLink.role_name"
              :items="availableRoles"
              :label="$t('admin.referral.createLinkDialog.roleForNewUsers')"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <!-- Welcome mail routing: standard (generic, auto-filled) is the
                 default; 'custom' opens subject/body with {placeholders}. -->
            <v-select
              v-model="newLink.welcome_template"
              :items="welcomeTemplateOptions"
              item-title="title"
              item-value="value"
              :label="$t('admin.referral.welcomeMail.templateLabel')"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <template v-if="newLink.welcome_template === 'custom'">
              <v-text-field
                v-model="newLink.welcome_subject"
                :label="$t('admin.referral.welcomeMail.subject')"
                variant="outlined"
                density="comfortable"
                class="mb-3"
              />
              <v-textarea
                v-model="newLink.welcome_body"
                :label="$t('admin.referral.welcomeMail.body')"
                variant="outlined"
                density="comfortable"
                rows="5"
                auto-grow
                :hint="$t('admin.referral.welcomeMail.placeholdersHint')"
                persistent-hint
                class="mb-3"
              />
            </template>
            <v-text-field
              v-model.number="newLink.max_uses"
              :label="$t('admin.referral.createLinkDialog.maxUses')"
              type="number"
              variant="outlined"
              density="comfortable"
              :hint="$t('admin.referral.createCampaignDialog.unlimitedHint')"
              class="mb-3"
            />
            <v-text-field
              v-model="newLink.expires_at"
              :label="$t('admin.referral.createLinkDialog.expiresAt')"
              type="datetime-local"
              variant="outlined"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showCreateLinkDialog = false">{{ $t('admin.referral.deleteDialog.cancel') }}</LBtn>
          <LBtn
            variant="primary"
            @click="createLink"
            :loading="creatingLink"
            :disabled="!linkFormValid"
          >
            {{ $t('admin.referral.createCampaignDialog.create') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Welcome-Mail Dialog (per link) -->
    <v-dialog v-model="showWelcomeDialog" max-width="560">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-email-edit-outline</v-icon>
          {{ $t('admin.referral.welcomeMail.title') }}
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="welcomeForm.welcome_template"
            :items="welcomeTemplateOptions"
            item-title="title"
            item-value="value"
            :label="$t('admin.referral.welcomeMail.templateLabel')"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />
          <template v-if="welcomeForm.welcome_template === 'custom'">
            <v-text-field
              v-model="welcomeForm.welcome_subject"
              :label="$t('admin.referral.welcomeMail.subject')"
              variant="outlined"
              density="comfortable"
              class="mb-3"
            />
            <v-textarea
              v-model="welcomeForm.welcome_body"
              :label="$t('admin.referral.welcomeMail.body')"
              variant="outlined"
              density="comfortable"
              rows="6"
              auto-grow
              :hint="$t('admin.referral.welcomeMail.placeholdersHint')"
              persistent-hint
            />
          </template>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showWelcomeDialog = false">{{ $t('admin.referral.deleteDialog.cancel') }}</LBtn>
          <LBtn variant="primary" :loading="savingWelcome" @click="saveWelcomeMail">
            {{ $t('common.save') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          {{ deleteDialogTitle }}
        </v-card-title>
        <v-card-text>{{ deleteDialogText }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="showDeleteDialog = false">{{ $t('admin.referral.deleteDialog.cancel') }}</LBtn>
          <LBtn variant="danger" @click="executeDelete" :loading="deleting">{{ $t('admin.referral.deleteDialog.delete') }}</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useReferralSystem } from '@/composables/useReferralSystem'
import { useMailCenter } from '@/composables/useMailCenter'
import { useSnackbar } from '@/composables/useSnackbar'
import LAvatar from '@/components/common/LAvatar.vue'
import LIconBtn from '@/components/common/LIconBtn.vue'
import LQrCodeDialog from '@/components/common/LQrCodeDialog.vue'
import { COLLAB_COLOR_PRESETS } from '@/constants/colors'

// Preset swatches offered for a referral link's badge color (same palette the
// backend auto-assigns from, so manual + auto colors stay visually coherent).
const colorPresets = COLLAB_COLOR_PRESETS

const { t, locale } = useI18n()
const referral = useReferralSystem()
const mail = useMailCenter()
const { showSuccess, showError, showInfo, showWarning, showMessage } = useSnackbar()

function showSnackbar(message, color = 'success') {
  switch (color) {
    case 'success':
      showSuccess(message)
      break
    case 'error':
      showError(message)
      break
    case 'info':
      showInfo(message)
      break
    case 'warning':
      showWarning(message)
      break
    default:
      showMessage(message, { color })
      break
  }
}

// State
const loading = ref(false)
const linksLoading = ref(false)
const creating = ref(false)
const creatingLink = ref(false)
const deleting = ref(false)

const overview = ref(null)
const campaigns = ref([])
const selectedCampaign = ref(null)
const campaignLinks = ref([])
const showArchived = ref(false)

// Dialogs
const showCreateCampaignDialog = ref(false)
const showCreateLinkDialog = ref(false)
const showDeleteDialog = ref(false)

// Invitation funnel stats per link id, and the per-link invite dialog state.
const linkStats = ref({})
const showInviteDialog = ref(false)
const inviteLink = ref(null)
const inviteRecipients = ref('')
const inviteIntro = ref('')
const inviting = ref(false)
// Per-link QR-code dialog state. We derive the public join URL via the
// composable's getLinkUrl() so the QR matches the copy/clipboard URL exactly.
const showQrDialog = ref(false)
const qrUrl = ref('')
const qrFilenameBase = ref('llars-join')

const deleteDialogTitle = ref('')
const deleteDialogText = ref('')
const deleteTarget = ref(null)
const deleteType = ref('') // 'campaign' or 'link'

// Forms
const campaignForm = ref(null)
const linkForm = ref(null)
const campaignFormValid = ref(false)
const linkFormValid = ref(false)

const newCampaign = ref({
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  max_registrations: null
})

const newLink = ref({
  slug: '',
  label: '',
  role_name: 'evaluator',
  max_uses: null,
  expires_at: '',
  color: '',  // '' = let the backend auto-assign a deterministic color
  welcome_template: 'standard',
  welcome_subject: '',
  welcome_body: ''
})

const availableRoles = ['admin', 'researcher', 'evaluator', 'chatbot_manager']

const slugRules = computed(() => [
  v => !v || /^[a-z0-9-]+$/.test(v) || t('admin.referral.validation.slugFormat')
])

const statusOptions = computed(() => [
  { label: t('admin.referral.statusOptions.draft'), value: 'draft' },
  { label: t('admin.referral.statusOptions.active'), value: 'active' },
  { label: t('admin.referral.statusOptions.paused'), value: 'paused' },
  { label: t('admin.referral.statusOptions.expired'), value: 'expired' },
  { label: t('admin.referral.statusOptions.archived'), value: 'archived' }
])

// Table headers
const campaignHeaders = computed(() => [
  { title: t('admin.referral.table.headers.name'), key: 'name', sortable: true },
  { title: t('admin.referral.table.headers.status'), key: 'status', sortable: true },
  { title: t('admin.referral.table.headers.links'), key: 'link_count', sortable: true },
  { title: t('admin.referral.table.headers.period'), key: 'dates', sortable: false },
  { title: t('admin.referral.table.headers.createdBy'), key: 'created_by', sortable: true },
  { title: t('admin.referral.table.headers.actions'), key: 'actions', sortable: false, align: 'end' }
])

const linkHeaders = computed(() => [
  { title: t('admin.referral.table.headers.codeSlug'), key: 'identifier', sortable: false },
  { title: t('admin.referral.table.headers.role'), key: 'role_name', sortable: true },
  { title: t('admin.referral.table.headers.funnel'), key: 'stats', sortable: false },
  { title: t('admin.referral.invitations.column'), key: 'invitations', sortable: false },
  { title: t('admin.referral.table.headers.active'), key: 'is_active', sortable: true },
  { title: '', key: 'actions', sortable: false, align: 'end' }
])

const registrationHeaders = computed(() => [
  { title: t('admin.referral.table.headers.user'), key: 'username', sortable: true },
  { title: t('admin.referral.table.headers.source'), key: 'source', sortable: false },
  { title: t('admin.referral.table.headers.role'), key: 'role_assigned', sortable: true },
  { title: t('admin.referral.table.headers.registeredAt'), key: 'registered_at', sortable: true }
])

// Registrations state
const registrations = ref([])
const registrationsLoading = ref(false)
const registrationTotal = ref(0)
const registrationFilter = ref(null) // { campaign_id: X } or { link_id: Y }

// Load data
onMounted(async () => {
  await loadOverview()
  await loadCampaigns()
  await loadRegistrations()
})

// Watch for archive filter changes
watch(showArchived, () => {
  loadCampaigns()
})

async function loadOverview() {
  try {
    overview.value = await referral.getAnalyticsOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

async function loadCampaigns() {
  loading.value = true
  try {
    campaigns.value = await referral.listCampaigns(showArchived.value)
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function loadCampaignLinks(campaignId) {
  linksLoading.value = true
  try {
    campaignLinks.value = await referral.listCampaignLinks(campaignId)
    // Best-effort: fetch the invited/accepted/pending funnel for each link.
    for (const link of campaignLinks.value) {
      loadLinkStats(link.id)
    }
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    linksLoading.value = false
  }
}

async function loadLinkStats(linkId) {
  try {
    linkStats.value = { ...linkStats.value, [linkId]: await mail.fetchLinkInvitations(linkId) }
  } catch (e) {
    // Non-fatal — the table still renders without the funnel.
  }
}

// Open the QR dialog for a link: build the public /join/<slug|code> URL and a
// matching download filename (llars-join-<slug|code>).
function openQrDialog(link) {
  qrUrl.value = referral.getLinkUrl(link)
  qrFilenameBase.value = `llars-join-${link.slug || link.code}`
  showQrDialog.value = true
}

function openInviteDialog(link) {
  inviteLink.value = link
  inviteRecipients.value = ''
  inviteIntro.value = ''
  showInviteDialog.value = true
}

async function sendInvites() {
  if (!inviteLink.value || !inviteRecipients.value.trim()) return
  inviting.value = true
  try {
    const res = await mail.sendInvite({
      referralLinkId: inviteLink.value.id,
      listText: inviteRecipients.value,
      intro: inviteIntro.value,
    })
    const r = res.result || {}
    showSnackbar(t('admin.referral.invitations.sentResult', {
      sent: r.sent || 0, failed: r.failed || 0, skipped: r.skipped || 0,
    }), 'success')
    showInviteDialog.value = false
    loadLinkStats(inviteLink.value.id)
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    inviting.value = false
  }
}

async function loadRegistrations(append = false) {
  registrationsLoading.value = true
  try {
    const params = {
      limit: 20,
      offset: append ? registrations.value.length : 0,
      ...registrationFilter.value
    }
    const result = await referral.listRegistrations(params)
    if (append) {
      registrations.value = [...registrations.value, ...result.registrations]
    } else {
      registrations.value = result.registrations
    }
    registrationTotal.value = result.total
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    registrationsLoading.value = false
  }
}

function filterRegistrationsByCampaign() {
  if (!selectedCampaign.value) return
  registrationFilter.value = { campaign_id: selectedCampaign.value.id }
  loadRegistrations()
}

function clearRegistrationFilter() {
  registrationFilter.value = null
  loadRegistrations()
}

function loadMoreRegistrations() {
  loadRegistrations(true)
}

// Format a backend conversion_rate (fraction in [0,1], or null when there
// were no clicks yet) as a percentage string for the funnel display.
function formatConversion(rate) {
  if (rate === null || rate === undefined) return '–'
  return `${Math.round(rate * 100)}%`
}

function formatDateTime(isoString) {
  if (!isoString) return '-'
  const date = new Date(isoString)
  const loc = locale.value === 'de' ? 'de-DE' : 'en-US'
  return date.toLocaleString(loc, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Status helpers
function getStatusVariant(status) {
  const variants = {
    draft: 'secondary',
    active: 'success',
    paused: 'warning',
    expired: 'danger',
    archived: 'secondary'
  }
  return variants[status] || 'secondary'
}

function getStatusLabel(status) {
  return referral.getStatusLabel(status)
}

// Date formatting
function formatDateRange(start, end) {
  if (!start && !end) return t('admin.referral.dateRange.noPeriod')
  const loc = locale.value === 'de' ? 'de-DE' : 'en-US'
  const formatDate = (d) => new Date(d).toLocaleDateString(loc, { day: '2-digit', month: '2-digit', year: '2-digit' })
  if (start && end) return `${formatDate(start)} - ${formatDate(end)}`
  if (start) return t('admin.referral.dateRange.from', { date: formatDate(start) })
  return t('admin.referral.dateRange.until', { date: formatDate(end) })
}

// Campaign actions
function getCampaignActions(campaign) {
  return ['view', 'edit', 'delete']
}

async function handleCampaignAction(action, campaign) {
  switch (action) {
    case 'view':
      selectedCampaign.value = campaign
      await loadCampaignLinks(campaign.id)
      break
    case 'edit':
      selectedCampaign.value = campaign
      await loadCampaignLinks(campaign.id)
      break
    case 'delete':
      confirmDeleteCampaign(campaign)
      break
  }
}

// Create campaign
async function createCampaign() {
  if (!campaignFormValid.value) return

  creating.value = true
  try {
    const data = { ...newCampaign.value }
    // Convert empty strings to null
    if (!data.start_date) data.start_date = null
    if (!data.end_date) data.end_date = null
    if (!data.max_registrations) data.max_registrations = null

    await referral.createCampaign(data)
    showSnackbar(t('admin.referral.messages.campaignCreated'), 'success')
    showCreateCampaignDialog.value = false
    resetCampaignForm()
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    creating.value = false
  }
}

function resetCampaignForm() {
  newCampaign.value = {
    name: '',
    description: '',
    start_date: '',
    end_date: '',
    max_registrations: null
  }
}

// Update campaign status
async function updateCampaignStatus() {
  if (!selectedCampaign.value) return

  try {
    await referral.updateCampaignStatus(selectedCampaign.value.id, selectedCampaign.value.status)
    showSnackbar(t('admin.referral.messages.statusUpdated'), 'success')
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

// Create link
async function createLink() {
  if (!linkFormValid.value || !selectedCampaign.value) return

  creatingLink.value = true
  try {
    const data = { ...newLink.value }
    // Convert empty strings to null
    if (!data.slug) data.slug = null
    if (!data.label) data.label = null
    if (!data.max_uses) data.max_uses = null
    if (!data.expires_at) data.expires_at = null
    if (!data.color) data.color = null  // null -> backend auto-color
    if (!data.welcome_subject) data.welcome_subject = null
    if (!data.welcome_body) data.welcome_body = null

    const link = await referral.createLink(selectedCampaign.value.id, data)
    showSnackbar(t('admin.referral.messages.linkCreated', { url: link.url }), 'success')
    showCreateLinkDialog.value = false
    resetLinkForm()
    await loadCampaignLinks(selectedCampaign.value.id)
    await loadCampaigns()
    await loadOverview()
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    creatingLink.value = false
  }
}

// --- Welcome-Mail-Dialog (pro Link) ---
const showWelcomeDialog = ref(false)
const savingWelcome = ref(false)
const welcomeLink = ref(null)
const welcomeForm = ref({ welcome_template: 'standard', welcome_subject: '', welcome_body: '' })

const welcomeTemplateOptions = computed(() => [
  { title: t('admin.referral.welcomeMail.templates.standard'), value: 'standard' },
  { title: t('admin.referral.welcomeMail.templates.kkb'), value: 'kkb' },
  { title: t('admin.referral.welcomeMail.templates.custom'), value: 'custom' }
])

function openWelcomeDialog(link) {
  welcomeLink.value = link
  welcomeForm.value = {
    welcome_template: link.welcome_template || 'standard',
    welcome_subject: link.welcome_subject || '',
    welcome_body: link.welcome_body || ''
  }
  showWelcomeDialog.value = true
}

async function saveWelcomeMail() {
  if (!welcomeLink.value) return
  savingWelcome.value = true
  try {
    const updated = await referral.updateLink(welcomeLink.value.id, { ...welcomeForm.value })
    Object.assign(welcomeLink.value, {
      welcome_template: updated?.welcome_template ?? welcomeForm.value.welcome_template,
      welcome_subject: updated?.welcome_subject ?? welcomeForm.value.welcome_subject,
      welcome_body: updated?.welcome_body ?? welcomeForm.value.welcome_body
    })
    showSnackbar(t('admin.referral.welcomeMail.saved'), 'success')
    showWelcomeDialog.value = false
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    savingWelcome.value = false
  }
}

function resetLinkForm() {
  newLink.value = {
    slug: '',
    label: '',
    role_name: 'evaluator',
    max_uses: null,
    expires_at: '',
    color: '',
    welcome_template: 'standard',
    welcome_subject: '',
    welcome_body: ''
  }
}

// Change a link's badge color inline from the table. Empty string clears the
// override so the link reverts to its deterministic auto-color.
async function setLinkColor(link, color) {
  try {
    const updated = await referral.updateLink(link.id, { color: color || '' })
    link.color = updated?.color ?? color ?? null
    link.color_custom = updated?.color_custom ?? (color || null)
    showSnackbar(t('admin.referral.messages.linkColorUpdated'), 'success')
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

// Toggle link active
async function toggleLinkActive(link, active) {
  try {
    await referral.updateLink(link.id, { is_active: active })
    link.is_active = active
    showSnackbar(active ? t('admin.referral.messages.linkActivated') : t('admin.referral.messages.linkDeactivated'), 'success')
  } catch (e) {
    showSnackbar(e.message, 'error')
  }
}

// Copy link
async function copyLink(link) {
  const success = await referral.copyLinkToClipboard(link)
  if (success) {
    showSnackbar(t('admin.referral.messages.linkCopied'), 'success')
  } else {
    showSnackbar(t('admin.referral.messages.copyFailed'), 'error')
  }
}

// Delete confirmation
function confirmDeleteCampaign(campaign) {
  deleteTarget.value = campaign
  deleteType.value = 'campaign'
  deleteDialogTitle.value = t('admin.referral.deleteDialog.deleteCampaign')
  deleteDialogText.value = t('admin.referral.deleteDialog.deleteCampaignText', { name: campaign.name })
  showDeleteDialog.value = true
}

function confirmDeleteLink(link) {
  deleteTarget.value = link
  deleteType.value = 'link'
  deleteDialogTitle.value = t('admin.referral.deleteDialog.deleteLink')
  deleteDialogText.value = t('admin.referral.deleteDialog.deleteLinkText', { code: link.slug || link.code })
  showDeleteDialog.value = true
}

async function executeDelete() {
  deleting.value = true
  try {
    if (deleteType.value === 'campaign') {
      await referral.deleteCampaign(deleteTarget.value.id)
      showSnackbar(t('admin.referral.messages.campaignDeleted'), 'success')
      if (selectedCampaign.value?.id === deleteTarget.value.id) {
        selectedCampaign.value = null
        campaignLinks.value = []
      }
      await loadCampaigns()
    } else {
      await referral.deleteLink(deleteTarget.value.id)
      showSnackbar(t('admin.referral.messages.linkDeleted'), 'success')
      if (selectedCampaign.value) {
        await loadCampaignLinks(selectedCampaign.value.id)
      }
    }
    await loadOverview()
    showDeleteDialog.value = false
  } catch (e) {
    showSnackbar(e.message, 'error')
  } finally {
    deleting.value = false
  }
}
</script>

<style scoped>
.admin-referral-section {
  padding: 0;
}

.analytics-overview {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: var(--llars-radius-sm);
  padding: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-xs);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Referral-link color editing (table swatch + create-dialog picker) */
.ref-color-swatch {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.18);
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  transition: transform 0.12s ease, border-color 0.12s ease;
}

.ref-color-swatch:hover {
  transform: scale(1.12);
}

.ref-color-swatch--option.is-selected {
  border-color: rgb(var(--v-theme-on-surface));
  box-shadow: 0 0 0 2px rgba(var(--v-theme-on-surface), 0.15);
}

.ref-color-caption {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 6px;
}

.ref-color-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.ref-color-menu {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  max-width: 200px;
  padding: 10px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}

.ref-color-auto {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  background: rgba(var(--v-theme-on-surface), 0.06);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.18);
  border-radius: 6px 2px 6px 2px;
  padding: 3px 9px;
  cursor: pointer;
}

.ref-color-auto.is-selected {
  border-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-primary));
}
</style>
