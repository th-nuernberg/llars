<!-- PromptEngineering/PromptEngineering.vue -->
<template>
  <div class="prompt-home" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <LIcon :size="isMobile ? 22 : 28" color="primary" :class="isMobile ? 'mr-2' : 'mr-3'">mdi-file-document-edit-outline</LIcon>
          <div>
            <h1 class="page-title">{{ isMobile ? 'Prompts' : 'Prompt Engineering' }}</h1>
            <p v-if="!isMobile" class="page-subtitle">Erstellen und verwalten Sie Ihre Prompts</p>
          </div>
        </div>
        <LBtn
          variant="primary"
          :prepend-icon="isMobile ? '' : 'mdi-plus'"
          :size="isMobile ? 'small' : 'default'"
          @click="openCreateDialog"
        >
          <LIcon v-if="isMobile">mdi-plus</LIcon>
          <span v-else>Neues Prompt</span>
        </LBtn>
      </div>
    </div>

    <!-- Main Content -->
    <div class="content-area">
      <!-- Meine Prompts Section -->
      <div class="section">
        <div class="section-header">
          <LIcon size="20" class="mr-2" color="primary">mdi-folder-account</LIcon>
          <span class="section-title">Meine Prompts</span>
          <span v-if="prompts.length" class="section-count">{{ prompts.length }}</span>
          <v-spacer />
          <LIconBtn icon="mdi-refresh" tooltip="Aktualisieren" size="small" @click="fetchPrompts" />
        </div>

        <v-skeleton-loader v-if="isLoading('prompts')" type="card@3" class="mt-4" />

        <transition-group
          v-else-if="prompts.length > 0"
          name="prompt-list"
          tag="div"
          class="prompts-grid"
        >
          <LCard
            v-for="prompt in prompts"
            :key="prompt.id"
            :title="prompt.name"
            icon="mdi-file-document-edit-outline"
            color="#b0ca97"
            outlined
            clickable
            :class="['prompt-card', { 'prompt-card--new': newPromptIds.has(prompt.id) }]"
            @click="navigateToPromptDetail(prompt.id)"
          >
            <template #status>
              <v-chip size="x-small" variant="tonal" color="info">
                #{{ prompt.id }}
              </v-chip>
            </template>

            <div class="prompt-meta">
              <div class="d-flex align-center text-caption text-medium-emphasis">
                <LIcon size="14" class="mr-1">mdi-clock-outline</LIcon>
                {{ formatRelativeDate(prompt.created_at) }}
              </div>
              <div v-if="prompt.shared_with?.length" class="shared-info mt-2">
                <LIcon size="14" color="warning" class="mr-1">mdi-share-variant</LIcon>
                <span class="text-caption">{{ prompt.shared_with.length }} Nutzer</span>
                <div class="shared-avatars ml-2">
                  <img
                    v-for="username in prompt.shared_with.slice(0, 3)"
                    :key="username"
                    :src="getDiceBearUrl(username, 24)"
                    class="shared-avatar"
                    :title="username"
                  />
                  <span v-if="prompt.shared_with.length > 3" class="more-badge">
                    +{{ prompt.shared_with.length - 3 }}
                  </span>
                </div>
              </div>
            </div>

            <template #actions>
              <LActionGroup
                :actions="['edit', 'delete']"
                size="small"
                @action="handlePromptAction($event, prompt)"
              />
            </template>
          </LCard>
        </transition-group>

        <div v-else class="empty-state">
          <LIcon size="48" color="grey-lighten-1">mdi-file-document-plus-outline</LIcon>
          <div class="text-subtitle-1 mt-3">Noch keine Prompts</div>
          <div class="text-body-2 text-medium-emphasis mb-4">
            Erstellen Sie Ihr erstes Prompt, um loszulegen.
          </div>
          <LBtn variant="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
            Prompt erstellen
          </LBtn>
        </div>
      </div>

      <!-- Geteilte Prompts Section -->
      <div class="section mt-8">
        <div class="section-header">
          <LIcon size="20" class="mr-2" color="warning">mdi-account-group</LIcon>
          <span class="section-title">Mit mir geteilt</span>
          <span v-if="sharedPrompts.length" class="section-count">{{ sharedPrompts.length }}</span>
        </div>

        <v-skeleton-loader v-if="isLoading('sharedPrompts')" type="card@3" class="mt-4" />

        <transition-group
          v-else-if="sharedPrompts.length > 0"
          name="prompt-list"
          tag="div"
          class="prompts-grid"
        >
          <LCard
            v-for="prompt in sharedPrompts"
            :key="prompt.id"
            :title="prompt.name"
            icon="mdi-file-document-outline"
            color="#e8c87a"
            outlined
            clickable
            :class="['prompt-card', { 'prompt-card--new': newSharedPromptIds.has(prompt.id) }]"
            @click="navigateToPromptDetail(prompt.id)"
          >
            <template #status>
              <LTag variant="warning" size="small">Geteilt</LTag>
            </template>

            <div class="prompt-meta">
              <div class="d-flex align-center text-caption text-medium-emphasis">
                <LIcon size="14" class="mr-1">mdi-account</LIcon>
                {{ prompt.owner }}
              </div>
              <div class="d-flex align-center text-caption text-medium-emphasis mt-1">
                <LIcon size="14" class="mr-1">mdi-clock-outline</LIcon>
                {{ formatRelativeDate(prompt.shared_at) }}
              </div>
            </div>
          </LCard>
        </transition-group>

        <div v-else class="empty-state-small">
          <LIcon size="32" color="grey-lighten-1">mdi-account-group-outline</LIcon>
          <span class="text-body-2 text-medium-emphasis ml-3">
            Keine geteilten Prompts vorhanden
          </span>
        </div>
      </div>
    </div>

    <!-- Create Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="520">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2" color="primary">mdi-file-document-plus</LIcon>
            <span class="text-h6">Neues Prompt erstellen</span>
            <v-spacer />
            <LIconBtn icon="mdi-close" tooltip="Schließen" size="small" @click="closeCreateDialog" />
          </div>
        </template>

        <v-alert v-if="createError" type="error" variant="tonal" class="mb-4" density="compact">
          {{ createError }}
        </v-alert>

        <v-text-field
          v-model="newPrompt.name"
          label="Name"
          placeholder="z. B. Interview-Leitfaden"
          prepend-inner-icon="mdi-file-document-outline"
          variant="outlined"
          density="comfortable"
          autofocus
          @keyup.enter="savePrompt"
        />

        <!-- User invite section -->
        <div class="section-label mt-4">
          <LIcon size="16" class="mr-1">mdi-account-multiple-plus</LIcon>
          Mit Nutzern teilen (optional)
        </div>
        <div v-if="selectedUsers.length > 0" class="invited-users mb-2">
          <LTag
            v-for="user in selectedUsers"
            :key="user"
            variant="primary"
            closable
            @close="removeUser(user)"
          >
            {{ user }}
          </LTag>
        </div>
        <LUserSearch
          ref="userSearchRef"
          :exclude-usernames="selectedUsers"
          placeholder="Nutzernamen eingeben..."
          @select="handleUserSelect"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeCreateDialog">Abbrechen</LBtn>
          <LBtn
            variant="primary"
            :loading="creating"
            :disabled="!newPrompt.name?.trim()"
            @click="savePrompt"
          >
            Erstellen
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Rename Dialog -->
    <v-dialog v-model="showRenameDialog" max-width="440">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2">mdi-rename-box</LIcon>
            <span class="text-h6">Prompt umbenennen</span>
            <v-spacer />
            <LIconBtn icon="mdi-close" tooltip="Schließen" size="small" @click="closeRenameDialog" />
          </div>
        </template>

        <v-text-field
          v-model="renamePromptName"
          label="Neuer Name"
          variant="outlined"
          density="comfortable"
          autofocus
          @keyup.enter="renamePrompt"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeRenameDialog">Abbrechen</LBtn>
          <LBtn variant="primary" :disabled="!renamePromptName?.trim()" @click="renamePrompt">
            Speichern
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Delete Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2" color="error">mdi-delete-alert</LIcon>
            <span class="text-h6">Prompt löschen</span>
          </div>
        </template>

        <p class="text-body-1">
          Möchten Sie <strong>{{ selectedPrompt?.name }}</strong> wirklich löschen?
        </p>
        <p class="text-body-2 text-medium-emphasis">
          Diese Aktion kann nicht rückgängig gemacht werden.
        </p>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDeleteDialog">Abbrechen</LBtn>
          <LBtn variant="danger" @click="confirmDeletePrompt">Löschen</LBtn>
        </template>
      </LCard>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { getSocket } from '@/services/socketService';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { useMobile } from '@/composables/useMobile';
import { formatRelativeDate, getDiceBearUrl } from '@/utils/userUtils';

const router = useRouter();
const { isLoading, withLoading } = useSkeletonLoading(['prompts', 'sharedPrompts']);
const { isMobile, isTablet } = useMobile();

// State
const prompts = ref([]);
const sharedPrompts = ref([]);
const newPromptIds = ref(new Set());
const newSharedPromptIds = ref(new Set());

// Create dialog
const showCreateDialog = ref(false);
const creating = ref(false);
const createError = ref('');
const newPrompt = ref({ name: '' });
const selectedUsers = ref([]);
const userSearchRef = ref(null);

// Rename dialog
const showRenameDialog = ref(false);
const renamePromptName = ref('');
const selectedPrompt = ref(null);

// Delete dialog
const showDeleteDialog = ref(false);

// WebSocket
let socket = null;
let currentUserId = null;

function formatDate(dateString) {
  if (!dateString) return '—';
  return new Date(dateString).toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

async function fetchPrompts() {
  await withLoading('prompts', async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts`);
      prompts.value = response.data.data || response.data.prompts || [];
    } catch (error) {
      console.error('Fehler beim Abrufen der Prompts:', error);
    }
  });
}

async function fetchSharedPrompts() {
  await withLoading('sharedPrompts', async () => {
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/api/prompts/shared`);
      sharedPrompts.value = response.data.data || response.data.shared_prompts || [];
    } catch (error) {
      console.error('Fehler beim Abrufen der geteilten Prompts:', error);
    }
  });
}

function markSharedPromptNew(id) {
  if (!id) return;
  const next = new Set(newSharedPromptIds.value);
  next.add(id);
  newSharedPromptIds.value = next;
  setTimeout(() => {
    const updated = new Set(newSharedPromptIds.value);
    updated.delete(id);
    newSharedPromptIds.value = updated;
  }, 3600);
}

function openCreateDialog() {
  showCreateDialog.value = true;
  newPrompt.value = { name: '' };
  selectedUsers.value = [];
  createError.value = '';
}

function closeCreateDialog() {
  showCreateDialog.value = false;
  newPrompt.value = { name: '' };
  selectedUsers.value = [];
  createError.value = '';
  userSearchRef.value?.reset?.();
}

async function savePrompt() {
  if (!newPrompt.value.name?.trim()) return;
  creating.value = true;
  createError.value = '';

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts`,
      {
        name: newPrompt.value.name.trim(),
        content: { blocks: {} },
      }
    );

    const promptData = response.data?.data;
    if (!promptData?.id) {
      throw new Error('Ungültige Server-Antwort: Prompt-ID fehlt');
    }

    const promptId = promptData.id;
    const newPromptData = {
      ...promptData,
      shared_with: []
    };

    // Share with selected users
    if (selectedUsers.value.length > 0) {
      for (const user of selectedUsers.value) {
        try {
          await axios.post(
            `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${promptId}/share`,
            { shared_with: user }
          );
          newPromptData.shared_with.push(user);
        } catch (shareError) {
          console.error(`Fehler beim Teilen mit ${user}:`, shareError);
        }
      }
    }

    // Mark as new and add to list
    newPromptIds.value.add(promptId);
    setTimeout(() => {
      newPromptIds.value.delete(promptId);
    }, 3000);

    prompts.value = [newPromptData, ...prompts.value];
    closeCreateDialog();
    navigateToPromptDetail(promptId);

  } catch (error) {
    console.error('Fehler beim Speichern des Prompts:', error);
    if (error.response?.status === 409) {
      createError.value = `Ein Prompt mit dem Namen "${newPrompt.value.name}" existiert bereits.`;
    } else {
      createError.value = error.response?.data?.error || error.message || 'Fehler beim Speichern';
    }
  } finally {
    creating.value = false;
  }
}

function handleUserSelect(user) {
  if (user?.username && !selectedUsers.value.includes(user.username)) {
    selectedUsers.value.push(user.username);
  }
  userSearchRef.value?.reset?.();
}

function removeUser(user) {
  selectedUsers.value = selectedUsers.value.filter(u => u !== user);
}

function handlePromptAction(action, prompt) {
  if (action === 'edit') {
    openRenameDialog(prompt);
  } else if (action === 'delete') {
    openDeleteDialog(prompt);
  }
}

function openRenameDialog(prompt) {
  selectedPrompt.value = prompt;
  renamePromptName.value = prompt.name;
  showRenameDialog.value = true;
}

function closeRenameDialog() {
  showRenameDialog.value = false;
  renamePromptName.value = '';
  selectedPrompt.value = null;
}

async function renamePrompt() {
  if (!selectedPrompt.value || !renamePromptName.value?.trim()) return;

  try {
    await axios.put(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${selectedPrompt.value.id}/rename`,
      { name: renamePromptName.value.trim() }
    );

    const prompt = prompts.value.find(p => p.id === selectedPrompt.value.id);
    if (prompt) {
      prompt.name = renamePromptName.value.trim();
    }

    closeRenameDialog();
  } catch (error) {
    console.error('Fehler beim Umbenennen des Prompts:', error);
  }
}

function openDeleteDialog(prompt) {
  selectedPrompt.value = prompt;
  showDeleteDialog.value = true;
}

function closeDeleteDialog() {
  showDeleteDialog.value = false;
  selectedPrompt.value = null;
}

async function confirmDeletePrompt() {
  if (!selectedPrompt.value) return;

  try {
    await axios.delete(
      `${import.meta.env.VITE_API_BASE_URL}/api/prompts/${selectedPrompt.value.id}`
    );

    prompts.value = prompts.value.filter(p => p.id !== selectedPrompt.value.id);
    closeDeleteDialog();
  } catch (error) {
    console.error('Fehler beim Löschen des Prompts:', error);
  }
}

function navigateToPromptDetail(promptId) {
  router.push(`/promptengineering/${promptId}`);
}

// WebSocket
async function fetchUserId() {
  try {
    const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/auth/authentik/me`);
    return response.data.user_id || response.data.id;
  } catch (error) {
    return null;
  }
}

function handlePromptsUpdate(data) {
  if (data.prompts) {
    prompts.value = data.prompts;
  }
}

function handleSharedPromptsUpdate(data) {
  if (data.shared_prompts) {
    const nextList = data.shared_prompts;
    const existingIds = new Set(sharedPrompts.value.map(prompt => prompt.id));
    nextList.forEach(prompt => {
      if (!existingIds.has(prompt.id)) {
        markSharedPromptNew(prompt.id);
      }
    });
    sharedPrompts.value = nextList;
  }
}

function setupWebSocket(userId) {
  if (!userId) return;

  socket = getSocket();
  if (socket) {
    socket.on('prompts:list', handlePromptsUpdate);
    socket.on('prompts:updated', handlePromptsUpdate);
    socket.on('prompts:shared_updated', handleSharedPromptsUpdate);

    if (socket.connected) {
      socket.emit('prompts:subscribe', { user_id: userId });
    }

    socket.on('connect', () => {
      socket.emit('prompts:subscribe', { user_id: userId });
    });
  }
}

function cleanupWebSocket() {
  if (socket) {
    socket.off('prompts:list', handlePromptsUpdate);
    socket.off('prompts:updated', handlePromptsUpdate);
    socket.off('prompts:shared_updated', handleSharedPromptsUpdate);

    if (currentUserId) {
      socket.emit('prompts:unsubscribe', { user_id: currentUserId });
    }
  }
}

onMounted(async () => {
  currentUserId = await fetchUserId();
  await Promise.all([fetchPrompts(), fetchSharedPrompts()]);

  if (currentUserId) {
    setupWebSocket(currentUserId);
  }
});

onUnmounted(() => {
  cleanupWebSocket();
});
</script>

<style scoped>
.prompt-home {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.page-header {
  flex-shrink: 0;
  padding: 20px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 4px 0 0 0;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.section {
  max-width: 1400px;
  margin: 0 auto;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.section-count {
  margin-left: 8px;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 500;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  border-radius: 10px;
}

.prompts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.prompt-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.prompt-card:hover {
  transform: translateY(-2px);
}

.prompt-card--new {
  animation: promptHighlight 2.5s ease-out;
}

@keyframes promptHighlight {
  0% {
    transform: scale(1.02);
    box-shadow: 0 0 0 3px rgba(var(--v-theme-primary), 0.3);
  }
  100% {
    transform: scale(1);
    box-shadow: none;
  }
}

.prompt-meta {
  margin-top: 8px;
}

.shared-info {
  display: flex;
  align-items: center;
}

.shared-avatars {
  display: flex;
  align-items: center;
}

.shared-avatar {
  width: 22px;
  height: 22px;
  border-radius: 6px 2px 6px 2px;
  border: 2px solid rgb(var(--v-theme-surface));
  margin-left: -6px;
}

.shared-avatar:first-child {
  margin-left: 0;
}

.more-badge {
  margin-left: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.empty-state-small {
  display: flex;
  align-items: center;
  padding: 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
}

.invited-users {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.w-100 {
  width: 100%;
}

/* List transitions */
.prompt-list-enter-active,
.prompt-list-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.prompt-list-enter-from,
.prompt-list-leave-to {
  opacity: 0;
  transform: translateY(12px);
}

.prompt-list-move {
  transition: transform 0.3s ease;
}

/* ============================================
   MOBILE RESPONSIVE STYLES
   ============================================ */
.prompt-home.is-mobile {
  /* 64px AppBar + 24px Footer = 88px */
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  overflow: hidden;
  max-width: 100vw;
}

.prompt-home.is-mobile .page-header {
  padding: 12px 16px;
}

.prompt-home.is-mobile .page-title {
  font-size: 1.1rem;
}

.prompt-home.is-mobile .content-area {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}

.prompt-home.is-mobile .section-header {
  margin-bottom: 12px;
}

.prompt-home.is-mobile .section-title {
  font-size: 0.9rem;
}

.prompt-home.is-mobile .prompts-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}

.prompt-home.is-mobile .section {
  margin-bottom: 24px;
}

.prompt-home.is-mobile .section.mt-8 {
  margin-top: 24px !important;
}

.prompt-home.is-mobile .empty-state {
  padding: 32px 16px;
}

.prompt-home.is-mobile .empty-state-small {
  padding: 16px;
  flex-direction: column;
  text-align: center;
  gap: 8px;
}

.prompt-home.is-mobile .empty-state-small span {
  margin-left: 0 !important;
}

/* Tablet adjustments */
.prompt-home.is-tablet .prompts-grid {
  grid-template-columns: repeat(2, 1fr);
}

.prompt-home.is-tablet .page-header {
  padding: 16px 20px;
}

.prompt-home.is-tablet .content-area {
  padding: 20px;
}
</style>
