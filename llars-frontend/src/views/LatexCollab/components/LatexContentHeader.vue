<!--
  LatexContentHeader.vue

  Header bar for LaTeX workspace content area.
  Shows document info, connection status, and action buttons.
-->
<template>
  <div class="content-header">
    <div class="header-left">
      <!-- Mobile menu button -->
      <v-btn
        v-if="isMobile"
        icon
        variant="text"
        size="small"
        class="mr-2"
        :title="$t('latexCollab.header.menuOpen')"
        @click="$emit('open-mobile-menu')"
      >
        <LIcon>mdi-menu</LIcon>
      </v-btn>
      <v-btn
        variant="text"
        size="small"
        class="header-back-btn"
        :title="$t('latexCollab.header.backToWorkspaces')"
        @click="$emit('navigate-back')"
      >
        <LIcon size="18">mdi-arrow-left</LIcon>
        <span v-if="!isMobile" class="header-back-label">{{ $t('latexCollab.header.workspaces') }}</span>
      </v-btn>
      <LIcon v-if="!isMobile" size="20" color="primary" class="mr-2">mdi-file-code-outline</LIcon>
      <div class="header-info">
        <div class="header-title">{{ documentTitle }}</div>
        <div class="header-subtitle">{{ workspaceName }}</div>
      </div>
    </div>

    <div class="header-actions">
      <v-btn
        v-if="canShare"
        icon
        variant="text"
        size="small"
        :title="$t('latexCollab.share.title')"
        @click="$emit('open-share')"
      >
        <LIcon size="20">mdi-account-multiple-plus</LIcon>
      </v-btn>

      <v-btn
        icon
        variant="text"
        size="small"
        :title="$t('latexCollab.zotero.title')"
        @click="$emit('open-zotero')"
      >
        <LIcon size="20">zotero</LIcon>
      </v-btn>

      <v-btn
        v-if="canSetMain"
        icon
        variant="text"
        size="small"
        :title="$t('latexCollab.header.setMain')"
        @click="$emit('set-main-document')"
      >
        <LIcon size="20">{{ isMainDocument ? 'mdi-star' : 'mdi-star-outline' }}</LIcon>
      </v-btn>

      <v-btn
        icon
        variant="text"
        size="small"
        :color="reviewMode ? 'primary' : undefined"
        :title="$t('latexCollab.header.reviewMode')"
        @click="$emit('toggle-review-mode')"
      >
        <LIcon size="20">mdi-comment-text-outline</LIcon>
      </v-btn>

      <!-- ZIP Import/Export Menu -->
      <v-menu location="bottom end">
        <template #activator="{ props: menuProps }">
          <v-btn
            icon
            variant="text"
            size="small"
            v-bind="menuProps"
            :title="$t('latexCollab.zip.menuTitle')"
          >
            <LIcon size="20">mdi-folder-zip</LIcon>
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item
            prepend-icon="mdi-download"
            :title="$t('latexCollab.zip.downloadTitle')"
            :subtitle="$t('latexCollab.zip.downloadSubtitle')"
            @click="$emit('download-zip')"
          />
          <v-list-item
            v-if="canEdit"
            prepend-icon="mdi-upload"
            :title="$t('latexCollab.zip.importTitle')"
            :subtitle="$t('latexCollab.zip.importSubtitle')"
            @click="$emit('import-zip')"
          />
        </v-list>
      </v-menu>

      <!-- Divider -->
      <div v-if="showConnectionStatus" class="header-divider" />

      <!-- Connection Status -->
      <template v-if="showConnectionStatus">
        <v-chip v-if="isConnected" size="small" color="success" variant="tonal">
          <LIcon start size="small">mdi-cloud-check-outline</LIcon>
          {{ $t('latexCollab.header.liveSync') }}
        </v-chip>
        <v-chip v-else size="small" color="warning" variant="tonal">
          <LIcon start size="small">mdi-cloud-alert-outline</LIcon>
          {{ $t('latexCollab.header.reconnecting') }}
        </v-chip>

        <!-- Ghost Text Toggle (only in AI mode) -->
        <v-tooltip v-if="aiEnabled" location="bottom">
          <template #activator="{ props: tooltipProps }">
            <v-chip
              v-bind="tooltipProps"
              size="small"
              :color="ghostTextEnabled ? 'primary' : 'default'"
              :variant="ghostTextEnabled ? 'flat' : 'outlined'"
              class="ghost-text-chip"
              @click="$emit('toggle-ghost-text')"
            >
              <LIcon start size="small">{{ ghostTextEnabled ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</LIcon>
              {{ $t('latexCollab.header.ghostText') }}
            </v-chip>
          </template>
          <span>
            {{ ghostTextEnabled ? $t('latexCollab.header.ghostTextEnabled') : $t('latexCollab.header.ghostTextDisabled') }}
          </span>
        </v-tooltip>

        <!-- Active Users -->
        <div v-if="activeUsers.length" class="header-users">
          <v-chip
            v-for="u in activeUsers"
            :key="u.userId"
            size="small"
            variant="tonal"
            :style="{ borderColor: u.color }"
            class="user-chip"
          >
            <span class="user-dot" :style="{ backgroundColor: u.color }" />
            {{ u.username }}
          </v-chip>
        </div>
      </template>

      <div v-if="isMobile" class="mode-toggle-group">
        <button
          class="mode-btn"
          :class="{ active: viewMode === 'editor' }"
          :title="$t('latexCollab.header.view.editor')"
          @click="$emit('update:viewMode', 'editor')"
        >
          <LIcon size="18">mdi-pencil</LIcon>
        </button>
        <button
          class="mode-btn"
          :class="{ active: viewMode === 'split' }"
          :title="$t('latexCollab.header.view.split')"
          @click="$emit('update:viewMode', 'split')"
        >
          <LIcon size="18">mdi-view-split-vertical</LIcon>
        </button>
        <button
          class="mode-btn"
          :class="{ active: viewMode === 'preview' }"
          :title="$t('latexCollab.header.view.preview')"
          @click="$emit('update:viewMode', 'preview')"
        >
          <LIcon size="18">mdi-file-pdf-box</LIcon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isMobile: {
    type: Boolean,
    default: false
  },
  documentTitle: {
    type: String,
    default: ''
  },
  workspaceName: {
    type: String,
    default: ''
  },
  canShare: {
    type: Boolean,
    default: false
  },
  canSetMain: {
    type: Boolean,
    default: false
  },
  canEdit: {
    type: Boolean,
    default: false
  },
  isMainDocument: {
    type: Boolean,
    default: false
  },
  reviewMode: {
    type: Boolean,
    default: false
  },
  showConnectionStatus: {
    type: Boolean,
    default: false
  },
  isConnected: {
    type: Boolean,
    default: false
  },
  aiEnabled: {
    type: Boolean,
    default: false
  },
  ghostTextEnabled: {
    type: Boolean,
    default: false
  },
  activeUsers: {
    type: Array,
    default: () => []
  },
  viewMode: {
    type: String,
    default: 'split'
  }
})

defineEmits([
  'open-mobile-menu',
  'navigate-back',
  'open-share',
  'open-zotero',
  'set-main-document',
  'toggle-review-mode',
  'toggle-ghost-text',
  'update:viewMode',
  'download-zip',
  'import-zip'
])
</script>

<style scoped>
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface-variant), 0.15) 100%);
  flex-shrink: 0;
  min-height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.header-back-btn {
  flex-shrink: 0;
}

.header-back-label {
  margin-left: 4px;
  font-size: 13px;
}

.header-info {
  min-width: 0;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-subtitle {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  margin: 0 8px;
}

.header-users {
  display: flex;
  gap: 4px;
  margin-left: 8px;
}

.user-chip {
  border-left: 3px solid;
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}

.ghost-text-chip {
  cursor: pointer;
}

.mode-toggle-group {
  display: flex;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
  padding: 2px;
  margin-left: 8px;
}

.mode-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.mode-btn.active {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-primary));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>
