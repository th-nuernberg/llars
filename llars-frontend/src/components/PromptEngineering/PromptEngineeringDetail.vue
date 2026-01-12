<!-- PromptEngineering/PromptEngineeringDetail.vue -->
<template>
  <div
    ref="containerRef"
    class="prompt-workspace"
    :class="{
      'prompt-workspace--git-hidden': !showGitPanel,
      'is-mobile': isMobile,
      'is-tablet': isTablet
    }"
  >
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
      temporary
      width="300"
      class="mobile-sidebar-drawer"
    >
      <sidebar
        :users="users"
        :blocks="blocks"
        :prompt-id="Number(promptId)"
        :is-owner="promptOwner === username"
        :shared-with="sharedWithUsers"
        :owner="promptOwner"
        :promptName="promptName"
        :show-git-panel="showGitPanel"
        :extracted-variables="extractedVariables"
        :user-variables="userVariables"
        @showAddBlockDialog="showAddBlockDialog = true; mobileSidebarOpen = false"
        @refreshPromptDetails="fetchPromptDetails()"
        @uploadJsonFileSelected="onJsonFileSelected"
        @triggerTestPrompt="openTestPromptDialog(); mobileSidebarOpen = false"
        @openVariableManager="openVariableManager(); mobileSidebarOpen = false"
        @toggleGitPanel="toggleGitPanel"
      />
      <template #append>
        <v-divider />
        <v-list density="compact" class="pa-2">
          <v-list-item
            prepend-icon="mdi-arrow-left"
            :title="$t('promptEngineering.editor.backToOverview')"
            @click="router.push('/promptengineering'); mobileSidebarOpen = false"
          />
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Left Panel: Sidebar (Desktop only) -->
    <div v-if="!isMobile" class="left-panel" :style="leftPanelStyle()">
      <sidebar
        :users="users"
        :blocks="blocks"
        :prompt-id="Number(promptId)"
        :is-owner="promptOwner === username"
        :shared-with="sharedWithUsers"
        :owner="promptOwner"
        :promptName="promptName"
        :show-git-panel="showGitPanel"
        :extracted-variables="extractedVariables"
        :user-variables="userVariables"
        @showAddBlockDialog="showAddBlockDialog = true"
        @refreshPromptDetails="fetchPromptDetails()"
        @uploadJsonFileSelected="onJsonFileSelected"
        @triggerTestPrompt="openTestPromptDialog"
        @openVariableManager="openVariableManager"
        @toggleGitPanel="toggleGitPanel"
      />
    </div>

    <!-- Resize Divider (Desktop only) -->
    <div
      v-if="!isMobile"
      class="resize-divider"
      :class="{ resizing: isResizing }"
      @mousedown="startResize"
    >
      <div class="resize-handle"></div>
    </div>

    <!-- Right Panel: Editor -->
    <div class="right-panel" :style="isMobile ? {} : rightPanelStyle()">
      <!-- Loading State -->
      <div v-if="isLoading('prompt')" class="loading-state">
        <v-skeleton-loader type="heading" class="mb-4" />
        <v-skeleton-loader type="card" class="mb-4" />
        <v-skeleton-loader type="card" class="mb-4" />
        <v-skeleton-loader type="card" />
      </div>

      <template v-else>
        <!-- Prompt Header -->
        <div class="prompt-header">
          <div class="prompt-header-left">
            <!-- Mobile menu button -->
            <v-btn
              v-if="isMobile"
              icon
              variant="text"
              size="small"
              class="mr-2"
              @click="mobileSidebarOpen = true"
            >
              <LIcon>mdi-menu</LIcon>
            </v-btn>
            <h1 class="prompt-title">{{ promptName }}</h1>
          </div>
          <div class="prompt-meta">
            <LTag variant="primary" size="small">
              {{ blocks.length }} {{ blocks.length === 1 ? $t('promptEngineering.editor.block') : $t('promptEngineering.editor.blocks') }}
            </LTag>
            <span v-if="sharedWithUsers.length && !isMobile" class="text-caption text-medium-emphasis ml-2">
              <LIcon size="14" class="mr-1">mdi-share-variant</LIcon>
              {{ $t('promptEngineering.editor.usersCount', { count: sharedWithUsers.length }) }}
            </span>
          </div>
        </div>

        <!-- Blocks Container -->
        <div ref="blocksContainerRef" class="blocks-container">
          <draggable
            v-if="blocks.length > 0"
            v-model="sortedBlocks"
            item-key="id"
            handle=".drag-handle"
            @end="onDragEnd"
            class="draggable-container"
          >
            <template #item="{ element: block }">
              <div class="editor-block">
                <div class="editor-header">
                  <div class="drag-handle" :title="$t('promptEngineering.editor.dragToSort')">
                    <LIcon size="18">mdi-drag</LIcon>
                  </div>

                  <!-- Block Title -->
                  <template v-if="editingBlockId === block.id">
                    <input
                      class="block-title-input"
                      type="text"
                      v-model="editingBlockTitle"
                      @keyup.enter="handleSaveBlockTitle(block)"
                      @blur="handleSaveBlockTitle(block)"
                      @keyup.escape="resetBlockTitleEdit"
                      :placeholder="$t('promptEngineering.editor.blockTitlePlaceholder')"
                      autofocus
                    />
                  </template>
                  <template v-else>
                    <h3 class="block-title" @dblclick="startEditBlockTitle(block)">
                      {{ block.title }}
                    </h3>
                  </template>

                  <v-spacer />

                  <div class="header-actions">
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      @click="startEditBlockTitle(block)"
                      :title="$t('promptEngineering.editor.rename')"
                    >
                      <LIcon size="16">mdi-pencil</LIcon>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      color="error"
                      @click="openDeleteBlockDialog(block)"
                      :title="$t('promptEngineering.editor.delete')"
                    >
                      <LIcon size="16">mdi-delete</LIcon>
                    </v-btn>
                  </div>
                </div>

                <!-- Quill Editor -->
                <div :ref="el => setEditorRef(el, block)" class="editor-content"></div>
              </div>
            </template>
          </draggable>

          <!-- Empty State -->
          <div v-else class="empty-blocks">
            <LIcon size="48" color="grey-lighten-1">mdi-file-document-plus-outline</LIcon>
            <div class="text-subtitle-1 mt-3">{{ $t('promptEngineering.editor.emptyTitle') }}</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              {{ $t('promptEngineering.editor.emptyDescription') }}
            </div>
            <LBtn variant="accent" prepend-icon="mdi-plus" @click="showAddBlockDialog = true">
              {{ $t('promptEngineering.editor.newBlock') }}
            </LBtn>
          </div>
        </div>

        <!-- Git Panel -->
        <div v-if="showGitPanel" ref="gitPanelRef" class="mt-4">
          <PromptGitPanel
            :prompt-id="Number(promptId)"
            :summary="gitSummary"
            :can-commit="true"
            :get-content="getContentSnapshot"
            @committed="onGitCommitted"
          />
        </div>

        <!-- Debug Info (Development only) -->
        <div v-if="isDevelopment" class="debug-info">
          <div class="debug-header" @click="debugExpanded = !debugExpanded">
            <LIcon size="18" class="debug-chevron" :class="{ 'rotated': debugExpanded }">mdi-chevron-right</LIcon>
            <h4>{{ $t('promptEngineering.editor.debugTitle') }}</h4>
            <LTag variant="gray" size="sm" class="ml-2">{{ blocks.length }} Blocks, {{ userVariables.length }} Variables</LTag>
          </div>
          <v-expand-transition>
            <div v-show="debugExpanded" class="debug-content">
              <div class="debug-section">
                <h5>Blocks & Variable Usage</h5>
                <div v-for="(block, idx) in blocks" :key="block.id" class="debug-block">
                  <div class="debug-block-header">
                    <span class="debug-block-index">#{{ idx + 1 }}</span>
                    <span class="debug-block-type">{{ block.type }}</span>
                    <LTag v-if="getVariablesInBlock(block).length > 0" variant="info" size="sm">
                      {{ getVariablesInBlock(block).length }} var(s)
                    </LTag>
                  </div>
                  <pre class="debug-block-content" v-html="highlightVariablesInContent(block.content || '')"></pre>
                  <div v-if="getVariablesInBlock(block).length > 0" class="debug-block-vars">
                    <LTag v-for="v in getVariablesInBlock(block)" :key="v" variant="accent" size="sm" class="mr-1">
                      {{ formatVarTag(v) }}
                    </LTag>
                  </div>
                </div>
              </div>
              <div class="debug-section">
                <h5>Variables ({{ userVariables.length }})</h5>
                <pre>{{ JSON.stringify(userVariables, null, 2) }}</pre>
              </div>
            </div>
          </v-expand-transition>
        </div>
      </template>
    </div>

    <!-- Add Block Dialog -->
    <v-dialog v-model="showAddBlockDialog" max-width="440">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2" color="accent">mdi-plus-circle</LIcon>
            <span class="text-h6">{{ $t('promptEngineering.dialogs.blockCreateTitle') }}</span>
          </div>
        </template>

        <v-text-field
          v-model="newBlockName"
          :label="$t('promptEngineering.dialogs.blockNameLabel')"
          :placeholder="$t('promptEngineering.dialogs.blockNamePlaceholder')"
          variant="outlined"
          density="comfortable"
          autofocus
          @keyup.enter="handleCreateBlock"
        />

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeAddBlockDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="accent" :disabled="!newBlockName?.trim()" @click="handleCreateBlock">
            {{ $t('promptEngineering.actions.create') }}
          </LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Delete Block Dialog -->
    <v-dialog v-model="showDeleteBlockDialog" max-width="400">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2" color="error">mdi-delete-alert</LIcon>
            <span class="text-h6">{{ $t('promptEngineering.dialogs.blockDeleteTitle') }}</span>
          </div>
        </template>

        <i18n-t keypath="promptEngineering.dialogs.blockDeleteConfirm" tag="p" class="text-body-1">
          <template #name>
            <strong>{{ blockToDelete?.title }}</strong>
          </template>
        </i18n-t>
        <p class="text-body-2 text-medium-emphasis">
          {{ $t('promptEngineering.dialogs.blockDeleteHint') }}
        </p>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeDeleteBlockDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="danger" @click="handleConfirmDeleteBlock">{{ $t('common.delete') }}</LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Upload Choice Dialog -->
    <v-dialog v-model="showUploadChoiceDialog" max-width="440">
      <LCard>
        <template #header>
          <div class="d-flex align-center w-100">
            <LIcon class="mr-2" color="secondary">mdi-upload</LIcon>
            <span class="text-h6">{{ $t('promptEngineering.dialogs.importTitle') }}</span>
          </div>
        </template>

        <p class="text-body-1">
          {{ $t('promptEngineering.dialogs.importQuestion') }}
        </p>

        <template #actions>
          <v-spacer />
          <LBtn variant="cancel" @click="closeUploadChoiceDialog">{{ $t('common.cancel') }}</LBtn>
          <LBtn variant="danger" @click="handleOverrideJsonBlocks">{{ $t('promptEngineering.dialogs.importOverride') }}</LBtn>
          <LBtn variant="primary" @click="handleAppendJsonBlocks">{{ $t('promptEngineering.dialogs.importAppend') }}</LBtn>
        </template>
      </LCard>
    </v-dialog>

    <!-- Test Prompt Dialog -->
    <TestPromptDialog
      v-model="showTestPromptDialog"
      :prompt="assemblePrompt()"
      :prompt-id="promptId"
      :variables="userVariables"
    />

    <!-- Variable Manager Dialog -->
    <VariableManagerDialog
      v-model="showVariableManager"
      :prompt-id="promptId"
      :variables="userVariables"
      :create-variable="createVariable"
      :update-variable="updateVariable"
      :delete-variable="deleteVariable"
      :is-valid-name="isValidVariableName"
      :variable-exists="variableExists"
    />

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :timeout="3000" color="success">
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script>
// Module script: Register Quill extensions once
import Quill from 'quill';
import QuillCursors from 'quill-cursors';
import Inline from 'quill/blots/inline';
import Embed from 'quill/blots/embed';

Quill.register('modules/cursors', QuillCursors);

// Global state to track dragged variable for move operations
window.__llarsVariableDrag = null;

// Variable Embed Blot - atomic element for {{variables}}
// This creates a single, draggable tag element instead of plain text
class VariableBlot extends Embed {
  static create(value) {
    const node = super.create();
    node.setAttribute('data-variable', value);
    node.setAttribute('contenteditable', 'false');
    node.setAttribute('draggable', 'true');

    // Create inner structure for the tag
    const tagContent = document.createElement('span');
    tagContent.className = 'variable-tag-content';
    tagContent.textContent = `{{${value}}}`;
    node.appendChild(tagContent);

    // Prevent Quill from handling mousedown on the variable tag
    // This allows native drag to work
    node.addEventListener('mousedown', (e) => {
      // Allow drag to start but prevent Quill selection
      e.stopPropagation();
    });

    // Add drag handlers
    node.addEventListener('dragstart', (e) => {
      e.stopPropagation(); // Prevent Quill from interfering
      e.dataTransfer.setData('text/variable-move', value);
      e.dataTransfer.setData('text/plain', `{{${value}}}`);
      e.dataTransfer.effectAllowed = 'move';
      node.classList.add('dragging');

      // Store reference to the dragged node for later removal
      window.__llarsVariableDrag = {
        node: node,
        value: value
      };
    });

    node.addEventListener('dragend', (e) => {
      e.stopPropagation();
      node.classList.remove('dragging');
      // Clear the drag reference after a short delay to allow drop to process
      setTimeout(() => {
        window.__llarsVariableDrag = null;
      }, 100);
    });

    return node;
  }

  static value(node) {
    return node.getAttribute('data-variable');
  }

  // Return the text representation for copy/paste and serialization
  static formats(node) {
    return node.getAttribute('data-variable');
  }

  // Length of 1 means it acts as a single character
  length() {
    return 1;
  }
}
VariableBlot.blotName = 'variable';
VariableBlot.tagName = 'span';
VariableBlot.className = 'ql-variable';
Quill.register(VariableBlot);

// Placeholder highlight blot - styled as a tag/chip (legacy, for backwards compatibility)
class HighlightBlot extends Inline {}
HighlightBlot.blotName = 'highlight';
HighlightBlot.tagName = 'span';
HighlightBlot.className = 'placeholder-highlight';
Quill.register(HighlightBlot);

// User highlight blot for collaboration
class UserHighlightBlot extends Inline {
  static create(value) {
    const node = super.create();
    if (value) {
      node.style.setProperty('--llars-collab-bg', value);
    }
    return node;
  }

  static formats(node) {
    return node.style.getPropertyValue('--llars-collab-bg') || null;
  }
}
UserHighlightBlot.blotName = 'llars-user-highlight';
UserHighlightBlot.tagName = 'span';
UserHighlightBlot.className = 'llars-user-highlight';
Quill.register(UserHighlightBlot);
</script>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import TestPromptDialog from './TestPromptDialog.vue';
import VariableManagerDialog from './VariableManagerDialog.vue';
import PromptGitPanel from './PromptGitPanel.vue';
import { useRoute, useRouter } from 'vue-router';
import 'quill/dist/quill.snow.css';
import draggable from 'vuedraggable';
import sidebar from "@/components/PromptEngineering/sidebar.vue";
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import { usePanelResize } from '@/composables/usePanelResize';
import { useMobile } from '@/composables/useMobile';
import { useI18n } from 'vue-i18n';

// Composables
import { useSnackbar } from './composables/useSnackbar';
import { useDialogs } from './composables/useDialogs';
import { usePromptDetails } from './composables/usePromptDetails';
import { useYjsCollaboration } from './composables/useYjsCollaboration';
import { usePromptBlocks } from './composables/usePromptBlocks';
import { useQuillEditor } from './composables/useQuillEditor';
import { usePromptGitDiff } from './composables/usePromptGitDiff';
import { usePromptVariables } from './composables/usePromptVariables';
import { useCollaborativeVariables } from './composables/useCollaborativeVariables';
import { useAuth } from '@/composables/useAuth';
import { useActiveDuration, useScrollDepth, useTypingMetrics, useVisibilityTracker } from '@/composables/useAnalyticsMetrics';

const isDevelopment = import.meta.env.VITE_PROJECT_STATE === 'development';
const debugExpanded = ref(false);

// Debug helper functions
const VARIABLE_REGEX = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g;

const getVariablesInBlock = (block) => {
  const raw = block.content || '';
  // Ensure content is a string
  const content = typeof raw === 'string' ? raw : String(raw);
  const found = new Set();
  let match;
  const regex = new RegExp(VARIABLE_REGEX.source, 'g');
  while ((match = regex.exec(content)) !== null) {
    found.add(match[1]);
  }
  return Array.from(found);
};

const highlightVariablesInContent = (content) => {
  if (!content) return '';
  // Ensure content is a string
  const str = typeof content === 'string' ? content : String(content);
  const escaped = str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  return escaped.replace(/\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g,
    '<span class="debug-var-highlight">{{$1}}</span>');
};

const formatVarTag = (name) => `{{${name}}}`;

const route = useRoute();
const router = useRouter();
const { isMobile, isTablet } = useMobile();
const { t } = useI18n();
const mobileSidebarOpen = ref(false);

const promptId = computed(() => route.params.id || 1);
const roomId = computed(() => `room_${promptId.value}`);
const username = localStorage.getItem('username') || t('promptEngineering.user.unknown');
const blocksContainerRef = ref(null);
const gitPanelRef = ref(null);
const promptEntity = computed(() => `prompt:${promptId.value}`);

// Skeleton Loading
const { isLoading, setLoading, withLoading } = useSkeletonLoading(['prompt']);

// Resizable Panel
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 22,
  minLeftPercent: 15,
  maxLeftPercent: 40,
  storageKey: 'prompt-engineering-sidebar-width'
});

// Composables initialization
const { showSnackbar, snackbarMessage, showMessage } = useSnackbar();

const {
  showAddBlockDialog,
  newBlockName,
  closeAddBlockDialog,
  showDeleteBlockDialog,
  blockToDelete,
  openDeleteBlockDialog,
  closeDeleteBlockDialog,
  showUploadChoiceDialog,
  pendingJsonData,
  openUploadChoiceDialog,
  closeUploadChoiceDialog,
  editingBlockId,
  editingBlockTitle,
  startEditBlockTitle,
  resetBlockTitleEdit,
  showTestPromptDialog,
  openTestPromptDialog,
  showVariableManager,
  openVariableManager
} = useDialogs();

const { promptName, promptOwner, sharedWithUsers, fetchPromptDetails } = usePromptDetails(promptId);
const auth = useAuth();
const typingMetrics = useTypingMetrics({
  category: 'prompt',
  name: 'editor',
  dimensions: () => ({ entity: promptEntity.value, view: 'editor' })
});

useActiveDuration({
  category: 'prompt',
  action: 'session_active_ms',
  name: () => `prompt:${promptId.value}`,
  dimensions: () => ({ entity: promptEntity.value })
});

const paneVisibility = useVisibilityTracker({
  category: 'prompt',
  action: 'pane_visible_ms',
  nameBuilder: (id) => `pane:${id}`,
  dimensions: () => ({ entity: promptEntity.value })
});

useScrollDepth(blocksContainerRef, {
  category: 'prompt',
  action: 'scroll_depth',
  name: () => `prompt:${promptId.value}|editor`,
  dimensions: () => ({ entity: promptEntity.value, view: 'editor' })
});

const countDeltaChars = (delta) => {
  if (!delta?.ops) return 0;
  return delta.ops.reduce((total, op) => {
    if (typeof op.insert === 'string') return total + op.insert.length;
    if (op.insert) return total + 1;
    return total;
  }, 0);
};

// YJS and Socket.IO setup
const collaboration = useYjsCollaboration(
  roomId,
  username,
  () => processYDoc(),
  (userId, cursor) => updateCursor(userId, cursor),
  { autoSync: true }  // Enable automatic Yjs sync (sends incremental updates only)
);

const { ydoc, socket, users, updateColor } = collaboration;

// Blocks management
const blocksManager = usePromptBlocks(ydoc, roomId, socket, showMessage, t);
const { blocks, sortedBlocks, processYDoc, createBlock, deleteBlock, saveBlockTitle, handleJsonUpload, assemblePrompt } = blocksManager;

// Extract variables from the assembled prompt for PlaceholderPalette
const assembledPromptText = computed(() => assemblePrompt())
const promptVariablesExtractor = usePromptVariables(assembledPromptText, { promptId })
const extractedVariables = computed(() => promptVariablesExtractor.validVariables.value || [])

// Collaborative variables management (synced via Yjs)
const collaborativeVariables = useCollaborativeVariables(ydoc, showMessage, t)
const {
  variables: userVariables,
  createVariable,
  updateVariable,
  deleteVariable,
  isValidName: isValidVariableName,
  variableExists
} = collaborativeVariables

// Git versioning - declare early so editors can reference showGitPanel
const showGitPanel = ref(true); // Stored in localStorage
const gitDiff = usePromptGitDiff(promptId, users);

const getCurrentUserColor = () => {
  const authColor = auth.collabColor?.value || null;
  if (authColor) return authColor;

  const socketId = socket.value?.id || null;
  if (socketId && users.value?.[socketId]?.color) {
    return users.value[socketId].color;
  }

  const targetName = auth.username?.value || username;
  const userEntry = Object.values(users.value || {}).find((user) => user?.username === targetName);
  return userEntry?.color || null;
};

// Quill editor management with user highlighting support
const editorManager = useQuillEditor(ydoc, socket, roomId, {
  getUserColor: () => getCurrentUserColor(),
  getUsername: () => auth.username?.value || username,
  showUserHighlighting: () => showGitPanel.value,
  onUserTextChange: ({ delta }) => {
    const chars = countDeltaChars(delta);
    if (chars > 0) {
      typingMetrics.recordInput(chars);
    }
  }
});
const {
  editorCount,
  setEditorRef,
  updateCursor,
  cleanupEditor,
  cleanupAll,
  applyHighlightingToAll,
  removeCursorForUser,
  clearUserHighlights,
  flushPendingHighlights,
  editors
} = editorManager;
const gitSummary = ref({ users: [], insertions: 0, deletions: 0, hasChanges: false, totalChangedLines: 0 });

// Load git panel visibility from localStorage
const loadGitPanelVisibility = () => {
  try {
    const stored = localStorage.getItem('prompt-git-panel-visible');
    showGitPanel.value = stored !== 'false';
  } catch {
    showGitPanel.value = true;
  }
};

// Save git panel visibility to localStorage
const saveGitPanelVisibility = (visible) => {
  try {
    localStorage.setItem('prompt-git-panel-visible', String(visible));
  } catch {
    // Ignore
  }
};

// Toggle git panel visibility
const toggleGitPanel = () => {
  showGitPanel.value = !showGitPanel.value;
  saveGitPanelVisibility(showGitPanel.value);
};

// Get current content as snapshot string (for commits)
const getContentSnapshot = () => {
  const result = {};
  for (const block of sortedBlocks.value) {
    const editor = editors.get(block.id);
    if (editor) {
      result[block.title] = editor.getText().trim();
    } else if (block.content) {
      result[block.title] = typeof block.content === 'string' ? block.content : block.content.toString?.() || '';
    }
  }
  return JSON.stringify(result, null, 2);
};

// Update git summary when content changes
const updateGitSummary = () => {
  const currentContent = getContentSnapshot();
  const summary = gitDiff.getChangeSummary(currentContent);

  // Add current user if they made changes
  if (summary.hasChanges && auth.username?.value) {
    const existingUser = summary.users.find(u => u.username === auth.username.value);
    if (!existingUser) {
      summary.users.push({
        username: auth.username.value,
        color: auth.collabColor?.value || '#9e9e9e',
        changedLines: summary.totalChangedLines
      });
    }
  }

  gitSummary.value = summary;
};

// Handle commit completed
const onGitCommitted = () => {
  gitDiff.updateBaseline(getContentSnapshot());
  clearUserHighlights(); // Clear text highlighting after commit
  updateGitSummary();
};

// Event handlers
const handleCreateBlock = () => {
  if (createBlock(newBlockName.value)) {
    closeAddBlockDialog();
  }
};

const handleConfirmDeleteBlock = () => {
  if (deleteBlock(blockToDelete.value)) {
    closeDeleteBlockDialog();
  }
};

const handleSaveBlockTitle = (block) => {
  if (saveBlockTitle(block, editingBlockTitle.value)) {
    resetBlockTitleEdit();
  } else {
    resetBlockTitleEdit();
  }
};

const onJsonFileSelected = (jsonData) => {
  openUploadChoiceDialog(jsonData);
};

const handleOverrideJsonBlocks = () => {
  if (handleJsonUpload(pendingJsonData.value, true)) {
    closeUploadChoiceDialog();
  }
};

const handleAppendJsonBlocks = () => {
  if (handleJsonUpload(pendingJsonData.value, false)) {
    closeUploadChoiceDialog();
  }
};

const onDragEnd = () => {
  showMessage(t('promptEngineering.messages.blockOrderUpdated'));
};

watch(blocksContainerRef, (el) => {
  paneVisibility.register('editor', el, { view: 'editor' });
});

watch(gitPanelRef, (el) => {
  paneVisibility.register('git', el, { view: 'git' });
});

// Watch for new/deleted blocks
watch(
  () => blocks.value,
  (newBlocks, oldBlocks) => {
    if (oldBlocks) {
      const deletedBlocks = oldBlocks.filter(
        oldBlock => !newBlocks.find(newBlock => newBlock.id === oldBlock.id)
      );
      deletedBlocks.forEach(block => {
        cleanupEditor(block.id);
      });
    }

    // Update git summary when blocks change
    updateGitSummary();
  },
  { deep: true }
);

// Debounced git summary update for text changes
let gitUpdateTimeout = null;
const debouncedGitUpdate = () => {
  if (gitUpdateTimeout) clearTimeout(gitUpdateTimeout);
  gitUpdateTimeout = setTimeout(() => {
    updateGitSummary();
  }, 500);
};

// Watch editors map for content changes
watch(
  () => editorCount.value,
  () => {
    // Re-attach text-change listeners when editors change
    for (const [blockId, editor] of editors) {
      if (!editor._gitListenerAttached) {
        editor.on('text-change', debouncedGitUpdate);
        editor._gitListenerAttached = true;
      }
    }
  }
);

// Lifecycle hooks
onMounted(async () => {
  // Load git panel visibility preference
  loadGitPanelVisibility();

  await withLoading('prompt', async () => {
    await fetchPromptDetails();
    collaboration.initialize();

    // Load git baseline for diff tracking
    await gitDiff.loadBaseline();
    updateGitSummary();

    watch(
      () => blocks.value.length,
      () => {
        applyHighlightingToAll();
      }
    );
  });
});

watch(
  () => auth.collabColor.value,
  (newColor) => {
    if (newColor && socket.value?.connected) {
      updateColor(newColor);
    }
  }
);

watch(
  [
    () => auth.collabColor.value,
    () => users.value,
    () => socket.value?.id
  ],
  () => {
    flushPendingHighlights();
  },
  { deep: true }
);

onUnmounted(() => {
  cleanupAll();
  collaboration.cleanup();
});

// User left handler
watch(users, (newUsers, oldUsers) => {
  if (oldUsers) {
    Object.keys(oldUsers).forEach(userId => {
      if (!newUsers[userId]) {
        removeCursorForUser(userId);
      }
    });
  }
});
</script>

<style scoped>
.prompt-workspace {
  height: calc(100vh - 94px);
  display: flex;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.left-panel {
  flex-shrink: 0;
  height: 100%;
  overflow: hidden;
}

.resize-divider {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.15s ease;
  z-index: 10;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.2);
}

.resize-handle {
  width: 2px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
  transition: all 0.15s ease;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
  height: 60px;
}

.right-panel {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-state {
  padding: 24px;
}

.prompt-header {
  flex-shrink: 0;
  padding: 20px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.prompt-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

.prompt-meta {
  display: flex;
  align-items: center;
}

.blocks-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.draggable-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.editor-block {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.drag-handle {
  cursor: grab;
  color: rgba(var(--v-theme-on-surface), 0.4);
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.drag-handle:hover {
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-on-surface), 0.08);
}

.block-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  cursor: pointer;
}

.block-title:hover {
  color: rgb(var(--v-theme-primary));
}

.block-title-input {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
  padding: 6px 10px;
  border: 1px solid rgb(var(--v-theme-primary));
  border-radius: 6px;
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-on-surface));
  outline: none;
}

.header-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.editor-block:hover .header-actions {
  opacity: 1;
}

.editor-content {
  min-height: 180px;
  background: rgb(var(--v-theme-surface));
}

:deep(.ql-container) {
  font-size: 15px;
  border: none !important;
}

:deep(.ql-editor) {
  min-height: 150px;
  padding: 16px;
  line-height: 1.6;
}

/* Placeholder drop target visual feedback */
:deep(.ql-editor.placeholder-drop-target) {
  background: rgba(var(--v-theme-primary), 0.08) !important;
  outline: 2px dashed rgb(var(--v-theme-primary));
  outline-offset: -2px;
}

:deep(.ql-toolbar) {
  border: none !important;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08) !important;
  background: rgba(var(--v-theme-on-surface), 0.02);
}

/* Placeholder Tag Styling - looks like a draggable chip/tag */
:deep(.placeholder-highlight) {
  display: inline-flex;
  align-items: center;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.2), rgba(var(--v-theme-primary), 0.1));
  padding: 2px 8px;
  border-radius: 4px 2px 4px 2px;
  border: 1px solid rgba(var(--v-theme-primary), 0.4);
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85em;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  cursor: grab;
  user-select: none;
  transition: all 0.15s ease;
  vertical-align: baseline;
  margin: 0 2px;
}

:deep(.placeholder-highlight:hover) {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.3), rgba(var(--v-theme-primary), 0.2));
  border-color: rgba(var(--v-theme-primary), 0.6);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(var(--v-theme-primary), 0.25);
}

:deep(.placeholder-highlight:active),
:deep(.placeholder-highlight.dragging) {
  cursor: grabbing;
  opacity: 0.7;
  transform: scale(0.95);
}

:deep(.llars-user-highlight) {
  background-color: var(--llars-collab-bg);
  border-radius: 2px;
}

/* Variable Embed Blot - atomic draggable tag element */
:deep(.ql-variable) {
  display: inline-flex;
  align-items: center;
  vertical-align: baseline;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.2), rgba(var(--v-theme-primary), 0.1));
  padding: 2px 8px;
  margin: 0 2px;
  border-radius: 6px 2px 6px 2px;
  border: 1px solid rgba(var(--v-theme-primary), 0.4);
  cursor: grab;
  user-select: none;
  transition: all 0.15s ease;
}

:deep(.ql-variable .variable-tag-content) {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85em;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  white-space: nowrap;
}

:deep(.ql-variable:hover) {
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.3), rgba(var(--v-theme-primary), 0.2));
  border-color: rgba(var(--v-theme-primary), 0.6);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.3);
}

:deep(.ql-variable:active),
:deep(.ql-variable.dragging) {
  cursor: grabbing;
  opacity: 0.6;
  transform: scale(0.95);
  box-shadow: 0 1px 4px rgba(var(--v-theme-primary), 0.2);
}

/* Drop indicator when dragging over editor */
:deep(.editor-content.drag-over),
:deep(.ql-editor.placeholder-drop-target) {
  background: rgba(var(--v-theme-primary), 0.05) !important;
  outline: 2px dashed rgba(var(--v-theme-primary), 0.4);
  outline-offset: -2px;
}

/* Show insertion cursor during drag */
:deep(.ql-editor.placeholder-drop-target)::after {
  content: '';
  position: absolute;
  width: 2px;
  height: 1.2em;
  background: rgb(var(--v-theme-primary));
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Drop cursor animation for drag and drop */
@keyframes dropCursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

:deep(.ql-drop-cursor) {
  box-shadow: 0 0 4px rgba(136, 196, 200, 0.8);
  border-radius: 1px;
}

.prompt-workspace--git-hidden :deep(.llars-user-highlight) {
  background-color: transparent !important;
}

:deep(.ql-cursor-flag) {
  display: inline-flex;
  align-items: center;
  position: absolute;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  color: white;
  white-space: nowrap;
  transform: translate(-50%, -100%);
  z-index: 100;
}

:deep(.ql-cursor-caret) {
  position: absolute;
  margin-top: -1px;
  width: 2px;
}

.empty-blocks {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.12);
}

.debug-info {
  margin-top: 24px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.debug-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.debug-header:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.debug-header h4 {
  margin: 0;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.debug-chevron {
  margin-right: 8px;
  transition: transform 0.2s ease;
}

.debug-chevron.rotated {
  transform: rotate(90deg);
}

.debug-content {
  padding: 0 16px 16px 16px;
}

.debug-info pre {
  font-size: 0.75rem;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  font-family: 'Roboto Mono', monospace;
}

.debug-section {
  margin-bottom: 16px;
}

.debug-section:last-child {
  margin-bottom: 0;
}

.debug-section h5 {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-weight: 600;
}

.debug-block {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 8px;
}

.debug-block:last-child {
  margin-bottom: 0;
}

.debug-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.debug-block-index {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.debug-block-type {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.debug-block-content {
  background: rgba(var(--v-theme-on-surface), 0.04);
  padding: 8px;
  border-radius: 4px;
  max-height: 120px;
  overflow-y: auto;
}

.debug-block-vars {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.debug-var-highlight) {
  background: rgba(var(--v-theme-accent), 0.25);
  color: rgb(var(--v-theme-accent));
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: 600;
}

.w-100 {
  width: 100%;
}

/* ============================================
   MOBILE RESPONSIVE STYLES
   ============================================ */
.prompt-workspace.is-mobile {
  /* 64px AppBar + 24px Footer = 88px */
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  overflow: hidden;
  max-width: 100vw;
}

.mobile-sidebar-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-sidebar-drawer :deep(.sidebar) {
  height: 100%;
}

/* Mobile: right panel takes full width */
.prompt-workspace.is-mobile .right-panel {
  width: 100% !important;
  flex: 1;
}

.prompt-workspace.is-mobile .prompt-header {
  padding: 12px 16px;
}

.prompt-workspace.is-mobile .prompt-header-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.prompt-workspace.is-mobile .prompt-title {
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.prompt-workspace.is-mobile .blocks-container {
  padding: 12px;
}

.prompt-workspace.is-mobile .draggable-container {
  gap: 12px;
}

.prompt-workspace.is-mobile .editor-block {
  border-radius: 8px;
}

.prompt-workspace.is-mobile .editor-header {
  padding: 10px 12px;
  gap: 6px;
}

.prompt-workspace.is-mobile .block-title {
  font-size: 0.9rem;
}

.prompt-workspace.is-mobile .editor-content {
  min-height: 120px;
}

.prompt-workspace.is-mobile :deep(.ql-editor) {
  min-height: 100px;
  padding: 12px;
  font-size: 14px;
}

.prompt-workspace.is-mobile :deep(.ql-toolbar) {
  padding: 6px 8px;
}

.prompt-workspace.is-mobile :deep(.ql-toolbar button) {
  width: 24px;
  height: 24px;
}

.prompt-workspace.is-mobile .empty-blocks {
  padding: 32px 16px;
}

/* Mobile: Always show header actions (no hover on touch) */
.prompt-workspace.is-mobile .header-actions {
  opacity: 1;
}

/* Tablet adjustments */
.prompt-workspace.is-tablet .left-panel {
  max-width: 260px;
}

.prompt-workspace.is-tablet .prompt-header {
  padding: 16px 20px;
}

.prompt-workspace.is-tablet .blocks-container {
  padding: 16px;
}

/* Desktop header-left for consistency */
.prompt-header-left {
  display: flex;
  align-items: center;
}
</style>
