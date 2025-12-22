<!-- PromptEngineering/sidebar.vue -->
<template>
  <div class="sidebar">
    <!-- Sidebar Header -->
    <div class="sidebar-header">
      <v-icon size="20" color="primary" class="mr-2">mdi-file-document-edit-outline</v-icon>
      <span class="sidebar-title text-truncate">{{ promptName }}</span>
      <v-spacer />
      <v-btn icon variant="text" size="small" @click="goToOverview">
        <v-icon size="18">mdi-arrow-left</v-icon>
      </v-btn>
    </div>

    <!-- Sidebar Content -->
    <div class="sidebar-content">
      <!-- Online Users -->
      <div class="sidebar-section">
        <div class="section-label">
          <v-icon size="14" class="mr-1">mdi-account-multiple</v-icon>
          Online ({{ Object.keys(users).length }})
        </div>
        <div class="users-list">
          <div v-for="(user, id) in users" :key="id" class="user-item">
            <span class="user-dot" :style="{ backgroundColor: user.color }"></span>
            <span class="user-name text-truncate">{{ user.username }}</span>
          </div>
          <div v-if="Object.keys(users).length === 0" class="empty-users">
            <span class="text-caption text-medium-emphasis">Keine Nutzer online</span>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="sidebar-section">
        <div class="section-label">
          <v-icon size="14" class="mr-1">mdi-lightning-bolt</v-icon>
          Aktionen
        </div>
        <div class="actions-grid">
          <LBtn variant="accent" block prepend-icon="mdi-plus" size="small" @click="$emit('showAddBlockDialog')">
            Neuer Block
          </LBtn>
          <LBtn variant="primary" block prepend-icon="mdi-eye" size="small" @click="showPreview = true">
            Vorschau
          </LBtn>
          <LBtn variant="accent" block prepend-icon="mdi-rocket" size="small" @click="$emit('triggerTestPrompt')">
            Testen
          </LBtn>
        </div>
      </div>

      <!-- Import/Export -->
      <div class="sidebar-section">
        <div class="section-label">
          <v-icon size="14" class="mr-1">mdi-swap-horizontal</v-icon>
          Import / Export
        </div>
        <div class="actions-grid">
          <LBtn variant="secondary" block prepend-icon="mdi-download" size="small" @click="downloadPrompt">
            Download
          </LBtn>
          <LBtn variant="secondary" block prepend-icon="mdi-content-copy" size="small" @click="copyPrompt">
            Kopieren
          </LBtn>
          <LBtn variant="secondary" block prepend-icon="mdi-upload" size="small" @click="triggerJsonUpload">
            Importieren
          </LBtn>
        </div>
        <input ref="jsonFileInput" type="file" accept=".json" style="display: none" @change="handleJsonFileUpload" />
      </div>

      <!-- Options Section -->
      <div class="sidebar-section">
        <div class="section-label">
          <v-icon size="14" class="mr-1">mdi-cog</v-icon>
          Optionen
        </div>
        <div class="option-item" @click="$emit('toggleGitPanel')">
          <v-icon size="16" :color="showGitPanel ? 'primary' : 'grey'" class="mr-2">
            mdi-source-branch
          </v-icon>
          <span class="option-label">Git-Panel</span>
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
          <v-icon size="14" class="mr-1">mdi-share-variant</v-icon>
          Freigaben
        </div>

        <!-- Owner Info (if not owner) -->
        <div v-if="!isOwner && owner" class="owner-card mb-3">
          <img :src="getDiceBearUrl(owner, 32)" class="owner-avatar" alt="" />
          <div class="owner-info">
            <span class="owner-label">Besitzer</span>
            <span class="owner-name">{{ owner }}</span>
          </div>
        </div>

        <!-- Shared Users List -->
        <div v-if="sharedWith.length > 0" class="shared-list mb-3">
          <div v-for="user in sharedWith" :key="user" class="shared-item">
            <img :src="getDiceBearUrl(user, 28)" class="shared-avatar" alt="" />
            <span class="shared-name text-truncate">{{ user }}</span>
            <v-btn
              v-if="isOwner"
              icon
              variant="text"
              size="x-small"
              color="error"
              @click="unsharePromptWithUser(user)"
            >
              <v-icon size="14">mdi-close</v-icon>
            </v-btn>
          </div>
        </div>

        <div v-else-if="isOwner" class="empty-shared">
          <span class="text-caption text-medium-emphasis">Noch mit niemandem geteilt</span>
        </div>

        <!-- Share Input (Owner only) -->
        <div v-if="isOwner" class="share-input-section">
          <LUserSearch
            ref="userSearchRef"
            :exclude-usernames="[...sharedWith, owner]"
            placeholder="Nutzer hinzufügen..."
            density="compact"
            :show-add-button="true"
            add-button-text="Teilen"
            button-size="x-small"
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
              <v-icon class="mr-2" color="primary">mdi-eye</v-icon>
              <span class="text-h6">Vorschau: {{ promptName }}</span>
              <v-spacer />
              <v-btn icon="mdi-close" variant="text" size="small" @click="showPreview = false" />
            </div>
          </template>

          <div class="preview-body">
            <div v-for="block in sortedBlocks" :key="block.id" class="preview-block">
              <div class="preview-block-title">{{ block.title }}</div>
              <div class="preview-block-content">{{ getBlockContent(block) }}</div>
            </div>
            <div v-if="sortedBlocks.length === 0" class="empty-preview">
              <v-icon size="32" color="grey-lighten-1">mdi-file-document-outline</v-icon>
              <span class="text-body-2 text-medium-emphasis mt-2">Keine Blöcke vorhanden</span>
            </div>
          </div>
        </LCard>
      </v-dialog>
    </Teleport>

    <!-- Copy Snackbar -->
    <v-snackbar v-model="showCopySnackbar" :timeout="2000" color="success">
      Prompt in Zwischenablage kopiert!
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getDiceBearUrl } from '@/utils/userUtils';
import axios from 'axios';

const props = defineProps({
  users: { type: Object, required: true },
  blocks: { type: Array, required: true },
  promptId: { type: Number, required: true },
  isOwner: { type: Boolean, default: false },
  sharedWith: { type: Array, default: () => [] },
  owner: { type: String, required: true },
  promptName: { type: String, required: true },
  showGitPanel: { type: Boolean, default: true }
});

const emit = defineEmits(['showAddBlockDialog', 'refreshPromptDetails', 'uploadJsonFileSelected', 'triggerTestPrompt', 'toggleGitPanel']);

const router = useRouter();
const jsonFileInput = ref(null);
const userSearchRef = ref(null);
const showPreview = ref(false);
const showCopySnackbar = ref(false);
const shareError = ref('');

const sortedBlocks = computed(() => {
  return [...props.blocks].sort((a, b) => (a.position || 0) - (b.position || 0));
});

const getBlockContent = (block) => {
  if (block.content && typeof block.content.toString === 'function') {
    return block.content.toString();
  }
  return '';
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
    shareError.value = error.response?.data?.error || 'Fehler beim Teilen';
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
    shareError.value = error.response?.data?.error || 'Fehler beim Entfernen';
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

.preview-block-content {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.5;
  white-space: pre-wrap;
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
}

.w-100 {
  width: 100%;
}
</style>
