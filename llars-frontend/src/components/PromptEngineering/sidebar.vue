<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <!-- Sidebar Header -->
    <div class="sidebar-header">
      <LIcon size="20" color="primary" class="mr-2">mdi-file-document-edit-outline</LIcon>
      <span class="sidebar-title text-truncate">{{ promptName }}</span>
      <v-spacer />
      <v-btn icon variant="text" size="small" @click="goToOverview">
        <LIcon size="18">mdi-arrow-left</LIcon>
      </v-btn>
    </div>

    <!-- Sidebar Content -->
    <div class="sidebar-content">
      <!-- Online Users -->
      <div class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-account-multiple</LIcon>
          {{ $t('promptEngineering.sidebar.onlineUsers', { count: Object.keys(users).length }) }}
        </div>
        <div class="users-list">
          <div v-for="(user, id) in users" :key="id" class="user-item">
            <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
            <span class="user-name text-truncate">{{ user.username }}</span>
          </div>
          <div v-if="Object.keys(users).length === 0" class="empty-users">
            <span class="text-caption text-medium-emphasis">{{ $t('promptEngineering.sidebar.noUsers') }}</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-lightning-bolt</LIcon>
          {{ $t('promptEngineering.sidebar.actions') }}
        </div>
        <div class="actions-grid">
          <LBtn variant="accent" block prepend-icon="mdi-plus" size="small" @click="$emit('showAddBlockDialog')">
            {{ $t('promptEngineering.sidebar.newBlock') }}
          </LBtn>
          <LBtn variant="secondary" block prepend-icon="mdi-code-braces" size="small" @click="$emit('openVariableManager')">
            {{ $t('promptEngineering.variables.manageVariables') }}
          </LBtn>
          <LBtn variant="primary" block prepend-icon="mdi-eye" size="small" @click="showPreview = true">
            {{ $t('promptEngineering.sidebar.preview') }}
          </LBtn>
          <LBtn variant="accent" block prepend-icon="mdi-rocket" size="small" @click="$emit('triggerTestPrompt')">
            {{ $t('promptEngineering.sidebar.test') }}
          </LBtn>
        </div>
      </div>

      <!-- Placeholder Palette for Drag & Drop -->
      <div class="sidebar-section">
        <PlaceholderPalette
          :prompt-id="promptId"
          :extracted-variables="extractedVariables"
          :user-variables="userVariables"
        />
      </div>

      <!-- Import/Export -->
      <div class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-swap-horizontal</LIcon>
          {{ $t('promptEngineering.sidebar.importExport') }}
        </div>
        <div class="actions-grid">
          <LBtn variant="secondary" block prepend-icon="mdi-download" size="small" @click="downloadPrompt">
            {{ $t('promptEngineering.sidebar.download') }}
          </LBtn>
          <LBtn variant="secondary" block prepend-icon="mdi-content-copy" size="small" @click="copyPrompt">
            {{ $t('promptEngineering.sidebar.copy') }}
          </LBtn>
          <LBtn variant="secondary" block prepend-icon="mdi-upload" size="small" @click="triggerJsonUpload">
            {{ $t('promptEngineering.sidebar.import') }}
          </LBtn>
        </div>
        <input ref="jsonFileInput" type="file" accept=".json" style="display: none" @change="handleJsonFileUpload" />
      </div>

      <!-- Version Control: Block Changes -->
      <div v-if="showGitPanel" class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-source-branch</LIcon>
          {{ $t('promptEngineering.sidebar.gitPanel') }}
          <v-spacer />
          <v-btn
            icon
            variant="text"
            size="x-small"
            :title="$t('common.refresh')"
            :loading="refreshingChanges"
            @click="$emit('refreshGitSummary')"
          >
            <LIcon size="14">mdi-refresh</LIcon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="x-small"
            :title="$t('promptEngineering.sidebar.openFloatingPanel')"
            @click="$emit('openFloatingGitPanel')"
          >
            <LIcon size="14">mdi-open-in-new</LIcon>
          </v-btn>
        </div>

        <!-- Block change list -->
        <div class="vc-block-list">
          <template v-if="changedBlocksList.length > 0">
            <div
              v-for="cb in changedBlocksList"
              :key="cb.title"
              class="vc-block-item"
            >
              <LIcon size="14" class="mr-1" :color="cb.isNew ? 'info' : cb.isDeleted ? 'error' : 'grey'">
                {{ cb.isNew ? 'mdi-plus-circle-outline' : cb.isDeleted ? 'mdi-minus-circle-outline' : 'mdi-text-box-outline' }}
              </LIcon>
              <span class="vc-block-name">{{ cb.title }}</span>
              <span v-if="cb.isNew && cb.insertions === 0 && cb.deletions === 0" class="vc-stat vc-new">{{ $t('promptEngineering.gitPanel.new') }}</span>
              <template v-else>
                <span class="vc-stat vc-ins">+{{ cb.insertions }}</span>
                <span class="vc-stat vc-del">-{{ cb.deletions }}</span>
              </template>
            </div>
          </template>
          <div v-else class="vc-synced">
            <LIcon size="14" color="success" class="mr-1">mdi-check-circle</LIcon>
            <span>{{ $t('promptEngineering.gitPanel.synced') }}</span>
          </div>
        </div>

        <!-- Commit section -->
        <div v-if="changedBlocksList.length > 0" class="vc-commit-section">
          <v-text-field
            v-model="commitMessage"
            :placeholder="$t('promptEngineering.floatingGit.commitPlaceholder')"
            variant="outlined"
            density="compact"
            hide-details
            class="vc-commit-input"
            @keyup.enter="handleCommit"
          />
          <LBtn
            variant="primary"
            size="small"
            :disabled="!commitMessage.trim()"
            :loading="committing"
            @click="handleCommit"
          >
            {{ $t('promptEngineering.floatingGit.commit') }}
          </LBtn>
        </div>
      </div>

      <!-- Options Section -->
      <div class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-cog</LIcon>
          {{ $t('promptEngineering.sidebar.options') }}
        </div>
        <div class="option-item" @click="$emit('toggleGitPanel')">
          <LIcon size="16" :color="showGitPanel ? 'primary' : 'grey'" class="mr-2">
            mdi-source-branch
          </LIcon>
          <span class="option-label">{{ $t('promptEngineering.sidebar.gitPanel') }}</span>
          <v-spacer />
          <v-switch
            :model-value="showGitPanel"
            color="primary"
            hide-details
            density="compact"
            @click.stop="$emit('toggleGitPanel')"
          />
        </div>
      </div>

      <!-- Sharing Section -->
      <div class="sidebar-section">
        <div class="section-label">
          <LIcon size="14" class="mr-1">mdi-share-variant</LIcon>
          {{ $t('promptEngineering.sidebar.shares') }}
        </div>

        <!-- Owner Info (if not owner) -->
        <div v-if="!isOwner && owner" class="owner-card mb-3">
          <LAvatar :username="owner" :seed="ownerAvatar?.avatar_seed" :src="ownerAvatar?.avatar_url" size="sm" class="owner-avatar" />
          <div class="owner-info">
            <span class="owner-label">{{ $t('promptEngineering.sidebar.owner') }}</span>
            <span class="owner-name">{{ owner }}</span>
          </div>
        </div>

        <!-- Shared Users List -->
        <div v-if="sharedWith.length > 0" class="shared-list mb-3">
          <div v-for="user in sharedWith" :key="user.username || user" class="shared-item">
            <LAvatar :username="user.username || user" :seed="user.avatar_seed" :src="user.avatar_url" size="sm" class="shared-avatar" />
            <span class="shared-name text-truncate">{{ user.username || user }}</span>
            <v-btn
              v-if="isOwner"
              icon
              variant="text"
              size="x-small"
              color="error"
              @click="unsharePromptWithUser(user.username || user)"
            >
              <LIcon size="14">mdi-close</LIcon>
            </v-btn>
          </div>
        </div>

        <div v-else-if="isOwner" class="empty-shared">
          <span class="text-caption text-medium-emphasis">{{ $t('promptEngineering.sidebar.notSharedYet') }}</span>
        </div>

        <!-- Share Input (Owner only) -->
        <div v-if="isOwner" class="share-input-section">
          <LUserSearch
            ref="userSearchRef"
            :exclude-usernames="[...sharedWith.map(u => u.username || u), owner]"
            :placeholder="$t('promptEngineering.sidebar.addUserPlaceholder')"
            density="compact"
            :show-add-button="true"
            :add-button-text="$t('promptEngineering.sidebar.shareAction')"
            button-size="small"
            @add="shareWithSelectedUser"
          />
          <div v-if="shareError" class="error-message mt-2">
            {{ shareError }}
          </div>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <Teleport to="body">
      <v-dialog v-model="showPreview" max-width="800">
        <LCard>
          <template #header>
            <div class="d-flex align-center w-100">
              <LIcon class="mr-2" color="primary">mdi-eye</LIcon>
              <span class="text-h6">{{ $t('promptEngineering.sidebar.previewTitle', { name: promptName }) }}</span>
              <v-spacer />
              <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" size="small" @click="showPreview = false" />
            </div>
          </template>

          <!-- Toggle between placeholder and resolved view -->
          <div class="preview-toggle">
            <v-btn-toggle v-model="previewMode" mandatory density="compact" color="primary">
              <v-btn value="placeholder" size="small">
                <LIcon start size="16">mdi-code-braces</LIcon>
                {{ $t('promptEngineering.sidebar.previewPlaceholder') }}
              </v-btn>
              <v-btn value="resolved" size="small">
                <LIcon start size="16">mdi-check-circle</LIcon>
                {{ $t('promptEngineering.sidebar.previewResolved') }}
              </v-btn>
            </v-btn-toggle>
          </div>

          <div class="preview-body">
            <div v-for="block in sortedBlocks" :key="block.id" class="preview-block">
              <div class="preview-block-title">{{ block.title }}</div>
              <div
                class="preview-block-content"
                :class="{ 'has-highlights': previewMode === 'resolved' }"
                v-html="getPreviewContent(block)"
              ></div>
            </div>
            <div v-if="sortedBlocks.length === 0" class="empty-preview">
              <LIcon size="32" color="grey-lighten-1">mdi-file-document-outline</LIcon>
              <span class="text-body-2 text-medium-emphasis mt-2">{{ $t('promptEngineering.sidebar.previewEmpty') }}</span>
            </div>
          </div>
        </LCard>
      </v-dialog>
    </Teleport>

    <!-- Copy Snackbar -->
    <v-snackbar v-model="showCopySnackbar" :timeout="2000" color="success">
      {{ $t('promptEngineering.sidebar.copied') }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import PlaceholderPalette from './testing/PlaceholderPalette.vue';
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const props = defineProps({
  users: { type: Object, required: true },
  blocks: { type: Array, required: true },
  promptId: { type: Number, required: true },
  isOwner: { type: Boolean, default: false },
  sharedWith: { type: Array, default: () => [] },
  owner: { type: String, required: true },
  ownerAvatar: { type: Object, default: null },
  promptName: { type: String, required: true },
  showGitPanel: { type: Boolean, default: true },
  extractedVariables: { type: Array, default: () => [] },
  userVariables: { type: Array, default: () => [] },
  gitSummary: { type: Object, default: () => ({ users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }) },
  getContent: { type: Function, default: null },
  blockCharDiffs: { type: Object, default: () => ({}) }
});

const emit = defineEmits(['showAddBlockDialog', 'refreshPromptDetails', 'uploadJsonFileSelected', 'triggerTestPrompt', 'toggleGitPanel', 'openVariableManager', 'gitCommitted', 'openFloatingGitPanel', 'refreshGitSummary']);

const router = useRouter();
const { t } = useI18n();
const jsonFileInput = ref(null);
const userSearchRef = ref(null);
const showPreview = ref(false);
const showCopySnackbar = ref(false);
const shareError = ref('');
const previewMode = ref('placeholder'); // 'placeholder' or 'resolved'

// Version control state
const commitMessage = ref('');
const committing = ref(false);
const refreshingChanges = ref(false);

// Changed blocks derived from blockCharDiffs (includes new/deleted blocks even if empty)
const changedBlocksList = computed(() => {
  const diffs = props.blockCharDiffs || {};
  return Object.entries(diffs)
    .filter(([, d]) => d.insertions > 0 || d.deletions > 0 || d.isNew || d.isDeleted)
    .map(([title, d]) => ({ title, insertions: d.insertions, deletions: d.deletions, isNew: d.isNew, isDeleted: d.isDeleted }));
});

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

const handleCommit = async () => {
  const msg = commitMessage.value.trim();
  if (!msg) return;
  committing.value = true;
  try {
    const contentSnapshot = props.getContent ? props.getContent() : null;
    await axios.post(
      `${API_BASE}/api/prompts/${props.promptId}/commit`,
      {
        message: msg,
        diff_summary: props.gitSummary || null,
        content_snapshot: contentSnapshot
      },
      { headers: authHeaders() }
    );
    commitMessage.value = '';
    emit('gitCommitted');
  } catch (error) {
    console.error('Commit failed:', error);
  } finally {
    committing.value = false;
  }
};

const sortedBlocks = computed(() => {
  return [...props.blocks].sort((a, b) => (a.position || 0) - (b.position || 0));
});

// Konvertiert Y.Text Delta zu Text, inklusive Variable-Embeds
const getBlockContent = (block) => {
  if (!block.content) return '';

  // Versuche toDelta() für präzise Embed-Behandlung
  try {
    if (typeof block.content.toDelta === 'function') {
      const delta = block.content.toDelta();
      let text = '';

      for (const op of delta) {
        if (typeof op.insert === 'string') {
          text += op.insert;
        } else if (typeof op.insert === 'object' && op.insert !== null) {
          // Handle variable embed
          if (op.insert.variable) {
            text += `{{${op.insert.variable}}}`;
          }
        }
      }

      return text;
    }
  } catch (e) {
    // Fallback
  }

  // Fallback zu toString()
  if (typeof block.content.toString === 'function') {
    return block.content.toString();
  }

  return '';
};

// Escape HTML to prevent XSS
const escapeHtml = (text) => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

// Get preview content - either with placeholders or with resolved values
const getPreviewContent = (block) => {
  const content = getBlockContent(block);

  if (previewMode.value === 'placeholder') {
    // Show original content with placeholders highlighted
    let html = escapeHtml(content);
    // Highlight placeholders
    html = html.replace(/\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g, '<span class="placeholder-tag">{{$1}}</span>');
    return html.replace(/\n/g, '<br/>');
  } else {
    // Show resolved content with replaced values highlighted
    let html = escapeHtml(content);

    // Replace variables with their values and highlight them
    for (const userVar of props.userVariables) {
      if (userVar.name && userVar.content) {
        const placeholder = `{{${userVar.name}}}`;
        const escapedPlaceholder = escapeHtml(placeholder);
        const escapedContent = escapeHtml(userVar.content);
        const highlightedValue = `<span class="resolved-value">${escapedContent}</span>`;
        html = html.split(escapedPlaceholder).join(highlightedValue);
      }
    }

    // Highlight remaining unresolved placeholders
    html = html.replace(/\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g, '<span class="unresolved-placeholder">{{$1}}</span>');

    return html.replace(/\n/g, '<br/>');
  }
};

const goToOverview = () => {
  router.push('/promptengineering');
};

// JSON Upload
const triggerJsonUpload = () => {
  jsonFileInput.value?.click();
};

const handleJsonFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const fileContent = await file.text();
    const jsonData = JSON.parse(fileContent);
    emit('uploadJsonFileSelected', jsonData);
    event.target.value = '';
  } catch (error) {
    console.error('Fehler beim JSON-Upload:', error);
  }
};

// Download
const downloadPrompt = () => {
  const promptData = {};
  sortedBlocks.value.forEach(block => {
    promptData[block.title] = getBlockContent(block).trim();
  });

  const jsonStr = JSON.stringify(promptData, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = window.URL.createObjectURL(blob);

  const sanitize = (name) => name.replace(/[^a-z0-9_\-]/gi, '_');
  const filename = `${sanitize(props.promptName || 'prompt')}.json`;

  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

// Copy
const copyPrompt = async () => {
  const promptData = {};
  sortedBlocks.value.forEach(block => {
    promptData[block.title] = getBlockContent(block).trim();
  });

  const jsonStr = JSON.stringify(promptData, null, 2);

  try {
    await navigator.clipboard.writeText(jsonStr);
    showCopySnackbar.value = true;
  } catch (err) {
    console.error('Copy failed:', err);
  }
};

// Share
const shareWithSelectedUser = async (user) => {
  if (!props.isOwner || !user?.username) return;
  shareError.value = '';

  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/share`,
      { shared_with: user.username }
    );
    userSearchRef.value?.reset?.();
    emit('refreshPromptDetails');
  } catch (error) {
    shareError.value = error.response?.data?.error || t('promptEngineering.errors.shareFailed');
    userSearchRef.value?.setAdding?.(false);
  }
};

// Unshare
const unsharePromptWithUser = async (username) => {
  if (!props.isOwner) return;

  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${props.promptId}/unshare`,
      { unshare_with: username }
    );
    emit('refreshPromptDetails');
  } catch (error) {
    shareError.value = error.response?.data?.error || t('promptEngineering.errors.unshareFailed');
    setTimeout(() => { shareError.value = ''; }, 5000);
  }
};
</script>

<style scoped>
.sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  overflow: hidden;
}

.sidebar-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.08), rgba(var(--v-theme-primary), 0.02));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.sidebar-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.sidebar-section {
  margin-bottom: 16px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.users-list {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 8px;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 6px;
  gap: 8px;
}

.user-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.user-name {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

.empty-users {
  padding: 12px;
  text-align: center;
}

.actions-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Option Item */
.option-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.option-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.option-label {
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

/* Owner Card */
.owner-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-primary), 0.12);
}

.owner-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px 3px 8px 3px;
  flex-shrink: 0;
}

.owner-info {
  display: flex;
  flex-direction: column;
}

.owner-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.owner-name {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

/* Shared List */
.shared-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.shared-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
}

.shared-avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px 2px 6px 2px;
  flex-shrink: 0;
}

.shared-name {
  flex: 1;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

.empty-shared {
  padding: 12px;
  text-align: center;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.share-input-section {
  margin-top: 8px;
}

.error-message {
  font-size: 0.8rem;
  color: rgb(var(--v-theme-error));
}

/* Preview */
.preview-body {
  max-height: 60vh;
  overflow-y: auto;
}

.preview-block {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.preview-block:last-child {
  margin-bottom: 0;
}

.preview-block-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
  margin-bottom: 8px;
}

.preview-toggle {
  display: flex;
  justify-content: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.preview-block-content {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Placeholder tag in original view */
:deep(.placeholder-tag) {
  display: inline;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.15);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
}

/* Resolved value in resolved view */
:deep(.resolved-value) {
  display: inline;
  background: rgba(var(--v-theme-success), 0.2);
  border-bottom: 2px solid rgba(var(--v-theme-success), 0.5);
  padding: 0 2px;
  border-radius: 2px;
}

/* Unresolved placeholder in resolved view */
:deep(.unresolved-placeholder) {
  display: inline;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.15);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid rgba(var(--v-theme-warning), 0.3);
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
}

/* Version Control Block List */
.vc-block-list {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 6px;
}

.vc-block-item {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 4px;
  gap: 4px;
}

.vc-block-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.vc-block-name {
  flex: 1;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

.vc-stat {
  font-size: 10px;
  font-family: 'Roboto Mono', monospace;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
}

.vc-stat.vc-ins {
  background: rgba(152, 212, 187, 0.2);
  color: #2e7d32;
}

.vc-stat.vc-del {
  background: rgba(232, 160, 135, 0.2);
  color: #c62828;
}

.vc-stat.vc-new {
  background: rgba(136, 196, 200, 0.2);
  color: #0288d1;
}

.vc-synced {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.vc-commit-section {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 8px;
}

.vc-commit-input {
  flex: 1;
}

.vc-commit-input :deep(.v-field) {
  border-radius: 8px 2px 8px 2px !important;
  font-size: 0.8rem;
}

.w-100 {
  width: 100%;
}
</style>
