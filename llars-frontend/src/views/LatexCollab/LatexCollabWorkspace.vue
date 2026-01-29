<template>
  <div class="workspace-root" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <input
      ref="assetInputRef"
      type="file"
      class="asset-input"
      multiple
      @change="handleAssetFiles"
    />
    <input
      ref="zipInputRef"
      type="file"
      class="asset-input"
      accept=".zip"
      @change="handleZipImport"
    />
    <!-- Tree Panel (Mobile Drawer + Desktop Sidebar) -->
    <LatexTreePanel
      ref="treePanelRef"
      :is-mobile="isMobile"
      v-model:mobile-open="mobileSidebarOpen"
      v-model:tree-collapsed="treeCollapsed"
      v-model:files-collapsed="filesCollapsed"
      v-model:git-collapsed="gitCollapsed"
      v-model:outline-collapsed="outlineCollapsed"
      :workspace-id="workspaceId"
      :nodes="treeNodes"
      :selected-id="selectedNodeId"
      :loading="isLoading('tree')"
      :can-edit="hasPermission('feature:latex_collab:edit')"
      :can-commit="hasPermission('feature:latex_collab:edit')"
      :recently-added-ids="recentlyAddedNodeIds"
      :tree-panel-width="treePanelWidth"
      :resizing-tree="resizingTree"
      :outline-flat-items="outlineFlatItems"
      :outline-empty-label="outlineEmptyLabel"
      :is-outline-item-collapsed="isOutlineItemCollapsed"
      @select="handleSelectNode"
      @create="handleCreateNode"
      @rename="handleRenameNode"
      @remove="handleDeleteNode"
      @move="handleMoveNode"
      @open-asset-picker="openAssetPicker"
      @start-tree-resize="startTreeResize"
      @navigate-home="router.push('/Home')"
      @navigate-workspaces="router.push(routeBase)"
      @toggle-outline-item="toggleOutlineItem"
      @jump-to-outline-item="jumpToOutlineItem"
      @open-git-detail="gitDetailDialog = true"
      @committed="refreshCommits"
    />

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Content Header -->
      <LatexContentHeader
        :is-mobile="isMobile"
        :document-title="selectedNode?.title || $t('latexCollab.workspace.empty.noDocument')"
        :workspace-name="workspace?.name || $t('latexCollab.workspace.fallbackName', { id: workspaceId })"
        :can-share="canShareWorkspace"
        :can-set-main="canSetMainDocument"
        :can-edit="hasPermission('feature:latex_collab:edit')"
        :is-main-document="selectedNode?.id === workspace?.main_document_id"
        :review-mode="reviewMode"
        :show-connection-status="selectedNode?.type === 'file' && !selectedNode?.asset_id"
        :is-connected="editorRef?.isConnected"
        :ai-enabled="props.aiEnabled"
        :ghost-text-enabled="props.ghostTextEnabled"
        :active-users="editorRef?.activeUsers || []"
        v-model:view-mode="viewMode"
        @open-mobile-menu="mobileSidebarOpen = true"
        @navigate-back="router.push(routeBase)"
        @open-share="openShareDialog"
        @open-zotero="zoteroDialog = true"
        @set-main-document="setMainDocument"
        @toggle-review-mode="reviewMode = !reviewMode"
        @toggle-ghost-text="editorRef?.toggleGhostText?.()"
        @download-zip="downloadWorkspaceZip"
        @import-zip="openZipImportDialog"
      />

      <!-- Content Body -->
      <div class="content-body">
        <div v-if="isLoading('document')" class="document-loading-overlay">
          <v-skeleton-loader
            type="card"
            class="document-loading-skeleton"
            height="320"
          />
        </div>

        <v-alert
          v-if="!hasPermission('feature:latex_collab:view')"
          type="warning"
        variant="tonal"
        class="ma-4"
      >
        <i18n-t keypath="latexCollab.permissions.missing" tag="span">
          <template #permission>
            <code>feature:latex_collab:view</code>
          </template>
        </i18n-t>
      </v-alert>

        <v-alert
          v-else-if="selectedNode && selectedNode.asset_id"
          type="info"
        variant="tonal"
        class="ma-4"
      >
        {{ $t('latexCollab.workspace.assetWarning') }}
      </v-alert>

        <v-alert
          v-else-if="!selectedNode || selectedNode.type !== 'file'"
          type="info"
        variant="tonal"
        class="ma-4"
      >
        {{ $t('latexCollab.workspace.empty.selectFile') }}
      </v-alert>

        <template v-else>
          <div class="editor-layout">
            <!-- Editor/Preview Panes -->
            <div ref="panesContainerRef" class="panes-container" :class="`mode-${viewMode}`">
              <!-- Editor Pane -->
              <div
                class="pane editor-pane"
                :style="editorPaneStyle"
              >
                <!-- Zotero read-only notice -->
                <v-alert
                  v-if="selectedNode?.is_zotero_managed"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="zotero-readonly-notice"
                >
                  <template #prepend>
                  <LIcon color="teal">mdi-bookshelf</LIcon>
                </template>
                <span class="text-body-2">
                  <i18n-t keypath="latexCollab.workspace.zoteroReadonly" tag="span">
                    <template #brand>
                      <strong>Zotero</strong>
                    </template>
                  </i18n-t>
                </span>
                </v-alert>
                <LatexEditorPane
                  ref="editorRef"
                  :document="selectedNode"
                  :readonly="editorReadonly"
                  :comments="comments"
                  :active-comment-id="activeCommentId"
                  :ai-enabled="props.aiEnabled"
                  :ghost-text-enabled="props.ghostTextEnabled"
                  :ghost-text-delay="props.ghostTextDelay"
                  @content-change="onEditorContentChange"
                  @git-summary="(s) => (gitSummary = s)"
                  @sync-request="handleEditorSyncRequest"
                  @ai-command="(cmd) => emit('ai-command', cmd)"
                  @ai-action="(e) => emit('ai-action', e)"
                  @request-completion="(req) => emit('request-completion', req)"
                  @update:ghost-text-enabled="(val) => emit('update:ghostTextEnabled', val)"
                  @document-saved="handleDocumentSaved"
                  @document-updated="handleDocumentUpdated"
                  @diff-calculated="handleDiffCalculated"
                  @request-comment="openCommentDialog"
                />
              </div>

              <!-- Resize Divider: Editor | Preview -->
              <div
                v-if="viewMode === 'split'"
                class="resize-divider vertical"
                :class="{ resizing: resizingPanes }"
                @mousedown="startPanesResize"
              >
                <div class="resize-handle" />
              </div>

              <!-- Preview Pane -->
              <div class="pane preview-pane" :style="previewPaneStyle">
                <div class="preview-toolbar">
                  <div class="compile-actions">
                    <LBtn
                      variant="primary"
                      size="small"
                      :loading="isCompiling"
                      :disabled="!canCompile"
                      prepend-icon="mdi-rocket-launch-outline"
                      :title="$t('latexCollab.compile.actions.compile')"
                      @click="triggerCompile"
                    >
                      {{ $t('latexCollab.compile.actions.compile') }}
                    </LBtn>
                    <v-select
                      v-model="compileCommitId"
                      :items="compileCommitOptions"
                      :label="$t('latexCollab.compile.versionLabel')"
                      density="compact"
                      variant="outlined"
                      hide-details
                      class="compile-select"
                    />
                  </div>
                  <div class="compile-status">
                    <v-chip size="x-small" variant="tonal" :color="compileStatusColor">
                      {{ compileStatusLabel }}
                    </v-chip>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      :title="$t('latexCollab.compile.actions.showLogs')"
                      @click="compileLogDialog = true"
                    >
                      <LIcon size="16">mdi-text-box-outline</LIcon>
                    </v-btn>
                    <v-menu>
                      <template #activator="{ props: menuProps }">
                        <v-btn icon variant="text" size="x-small" v-bind="menuProps" :title="$t('latexCollab.compile.auto.title')">
                          <LIcon size="16">mdi-tune-variant</LIcon>
                        </v-btn>
                      </template>
                      <v-card class="compile-settings">
                        <v-card-title class="text-subtitle-2">{{ $t('latexCollab.compile.auto.title') }}</v-card-title>
                        <v-card-text>
                      <v-switch
                        v-model="autoCompileEnabled"
                        :label="$t('latexCollab.compile.auto.enable')"
                        density="compact"
                        hide-details
                      />
                      <v-text-field
                        v-model.number="autoCompileDelay"
                        :label="$t('latexCollab.compile.auto.delayLabel')"
                        type="number"
                        min="500"
                        step="250"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                      <v-switch
                        v-model="syncEnabled"
                        :label="$t('latexCollab.compile.auto.syncLabel')"
                        density="compact"
                        hide-details
                        :disabled="!canSync"
                      />
                    </v-card-text>
                  </v-card>
                </v-menu>
              </div>
            </div>

                <!-- PDF + Comments resizable container -->
                <div ref="previewContentRef" class="preview-content">
                  <LatexPdfViewer
                    ref="pdfViewerRef"
                    class="pdf-section"
                    :workspace-id="workspaceId"
                    :job-id="pdfJobId"
                    :refresh-key="pdfRefreshKey"
                    :is-compiling="isCompiling"
                    @pdf-click="handlePdfClick"
                    @no-pdf="handleNoPdf"
                  />

                  <!-- Resize divider between PDF and Comments -->
                  <div
                    class="preview-resize-divider"
                    :class="{ resizing: resizingComments }"
                    @mousedown="startCommentsResize"
                  >
                    <div class="preview-resize-handle">
                      <span /><span /><span />
                    </div>
                  </div>

                  <div class="comments-panel" :style="commentsPanelStyle">
                  <div class="comments-header">
                    <div class="d-flex align-center ga-2">
                      <LIcon size="18">mdi-comment-multiple-outline</LIcon>
                      <span class="text-body-2">{{ $t('latexCollab.comments.title') }}</span>
                    </div>
                    <v-spacer />
                    <LBtn
                      variant="text"
                      size="small"
                      prepend-icon="mdi-comment-plus-outline"
                      :disabled="!canComment"
                      :title="$t('latexCollab.comments.add')"
                      @click="openCommentDialog"
                    >
                      {{ $t('latexCollab.comments.addLabel') }}
                    </LBtn>
                  </div>

                  <v-alert v-if="commentError" type="error" variant="tonal" density="compact" class="mb-2">
                    {{ commentError }}
                  </v-alert>

                  <div v-if="comments.length === 0" class="comments-empty">
                    {{ $t('latexCollab.comments.empty') }}
                  </div>

                  <div v-else class="comment-list">
                    <div
                      v-for="c in comments"
                      :key="c.id"
                      class="comment-thread"
                      :class="{
                        active: c.id === activeCommentId,
                        'other-document': isCommentInOtherDocument(c)
                      }"
                      :style="c.author_color ? { borderColor: c.author_color } : {}"
                      :data-comment-id="c.id"
                    >
                      <!-- Document indicator (for workspace-wide comments) -->
                      <div
                        v-if="c.document"
                        class="comment-document"
                        :class="{ clickable: isCommentInOtherDocument(c) }"
                        @click="navigateToComment(c)"
                      >
                        <LIcon size="14" class="mr-1">mdi-file-document-outline</LIcon>
                        <span class="document-title">{{ c.document.title }}</span>
                        <LIcon
                          v-if="isCommentInOtherDocument(c)"
                          size="12"
                          class="ml-1 jump-icon"
                        >mdi-arrow-right</LIcon>
                      </div>

                      <!-- Top-level comment -->
                      <div class="comment-item" @click="navigateToComment(c)">
                        <div class="comment-meta">
                          <span class="comment-author">
                            <span
                              v-if="c.author_color"
                              class="author-color-dot"
                              :style="{ backgroundColor: c.author_color }"
                            />
                            {{ c.author_username }}
                          </span>
                          <span class="comment-date">{{ formatDate(c.created_at) }}</span>
                        </div>
                        <div class="comment-body">{{ c.body }}</div>
                        <div class="comment-actions">
                          <LTag v-if="c.resolved_at" variant="success" size="x-small">{{ $t('latexCollab.comments.resolved') }}</LTag>
                          <!-- AI Resolve Button -->
                          <v-btn
                            v-if="!c.resolved_at && aiAssistantEnabled"
                            icon
                            variant="text"
                            size="x-small"
                            color="purple"
                            :title="aiResolvingCommentId === c.id ? $t('latexCollab.comments.aiStreamToggle') : $t('latexCollab.comments.aiResolveTitle')"
                            :loading="aiResolvingCommentId === c.id && !aiStreamWindowOpen"
                            :disabled="aiResolvingCommentId !== null && aiResolvingCommentId !== c.id"
                            @click.stop="handleAiButtonClick(c)"
                          >
                            <LIcon size="16">mdi-robot</LIcon>
                          </v-btn>
                          <v-btn
                            icon
                            variant="text"
                            size="x-small"
                            :title="$t('latexCollab.comments.reply')"
                            @click.stop="startReply(c.id)"
                          >
                            <LIcon size="16">mdi-reply</LIcon>
                          </v-btn>
                          <v-btn
                            icon
                            variant="text"
                            size="x-small"
                            :title="c.resolved_at ? $t('latexCollab.comments.reopen') : $t('latexCollab.comments.resolve')"
                            @click.stop="toggleCommentResolved(c)"
                          >
                            <LIcon size="16">mdi-check</LIcon>
                          </v-btn>
                          <v-btn
                            icon
                            variant="text"
                            size="x-small"
                            :title="$t('common.delete')"
                            @click.stop="deleteComment(c)"
                          >
                            <LIcon size="16">mdi-delete-outline</LIcon>
                          </v-btn>
                        </div>
                      </div>

                      <!-- Replies -->
                      <div v-if="c.replies && c.replies.length > 0" class="comment-replies">
                        <div
                          v-for="reply in c.replies"
                          :key="reply.id"
                          class="comment-reply"
                        >
                          <div class="comment-meta">
                            <span class="comment-author">
                              <span
                                v-if="reply.author_color"
                                class="author-color-dot"
                                :style="{ backgroundColor: reply.author_color }"
                              />
                              {{ reply.author_username }}
                            </span>
                            <span class="comment-date">{{ formatDate(reply.created_at) }}</span>
                          </div>
                          <div class="comment-body">{{ reply.body }}</div>
                          <div class="comment-actions">
                            <v-btn
                              icon
                              variant="text"
                              size="x-small"
                              :title="$t('common.delete')"
                              @click.stop="deleteComment(reply)"
                            >
                              <LIcon size="14">mdi-delete-outline</LIcon>
                            </v-btn>
                          </div>
                        </div>
                      </div>

                      <!-- Reply input -->
                      <div v-if="replyingToId === c.id" class="reply-input">
                        <v-textarea
                          v-model="replyDraft"
                          :placeholder="$t('latexCollab.comments.replyPlaceholder')"
                          variant="outlined"
                          density="compact"
                          rows="2"
                          auto-grow
                          hide-details
                          class="reply-textarea"
                          @click.stop
                        />
                        <div class="reply-actions">
                          <v-btn
                            variant="text"
                            size="x-small"
                            @click.stop="cancelReply"
                          >
                            {{ $t('common.cancel') }}
                          </v-btn>
                          <v-btn
                            color="primary"
                            size="x-small"
                            :disabled="!canSubmitReply"
                            @click.stop="submitReply(collabColor)"
                          >
                            {{ $t('latexCollab.comments.reply') }}
                          </v-btn>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>  <!-- Close preview-content -->
            </div>  <!-- Close preview-pane -->
          </div>  <!-- Close panes-container -->

          </div>
        </template>
      </div>
    </div>

    <!-- Share / Members Dialog -->
    <ShareDialog
      v-model="shareDialog"
      :workspace-name="workspace?.name"
      :owner-info="ownerInfo"
      :members="members"
      :excluded-usernames="excludedUsernames"
      :loading="membersLoading"
      :error="shareError"
      :removing-username="removingUsername"
      :can-remove="canShareWorkspace"
      @invite="inviteMember"
      @remove="removeMember"
    />

    <!-- Git Detail Dialog -->
    <GitDetailDialog
      v-model="gitDetailDialog"
      :workspace-id="workspaceId"
      :selected-document-id="selectedNodeId"
      :can-commit="hasPermission('feature:latex_collab:edit')"
      :get-content="getEditorContent"
      :before-commit="handleBeforeCommit"
      :before-rollback="handleBeforeRollback"
      @committed="refreshCommits"
      @rollback="handleRollback"
      @restored="handleRestored"
    />

    <!-- Floating Comment Card (no overlay, draggable, beside text) -->
    <Teleport to="body">
      <div
        v-if="commentDialog"
        ref="floatingCommentCardRef"
        class="floating-comment-card"
        :style="floatingCommentCardStyle"
        @keydown.esc="commentDialog = false"
        @keydown.ctrl.enter="canSubmitComment && submitComment(collabColor)"
      >
        <!-- Draggable Header -->
        <div
          class="floating-comment-header"
          @mousedown="startDragCommentCard"
        >
          <LIcon size="16" class="mr-1">mdi-comment-plus-outline</LIcon>
          <span class="floating-comment-title">{{ $t('latexCollab.comments.dialog.title') }}</span>
          <v-spacer />
          <LIconBtn
            icon="mdi-close"
            size="x-small"
            :tooltip="$t('common.close')"
            @click="commentDialog = false"
          />
        </div>
        <!-- Content -->
        <div class="floating-comment-body">
          <v-alert v-if="commentError" type="error" variant="tonal" class="mb-2" density="compact">
            {{ commentError }}
          </v-alert>
          <v-textarea
            ref="commentTextareaRef"
            v-model="commentDraft"
            :placeholder="$t('latexCollab.comments.dialog.placeholder')"
            variant="outlined"
            density="compact"
            rows="3"
            auto-grow
            hide-details
            autofocus
            @keydown.esc.stop="commentDialog = false"
            @keydown.ctrl.enter="canSubmitComment && submitComment(collabColor)"
          />
        </div>
        <!-- Actions -->
        <div class="floating-comment-actions">
          <v-btn
            variant="text"
            size="small"
            :title="$t('latexCollab.comments.dialog.cancelTitle')"
            @click="commentDialog = false"
          >
            {{ $t('common.cancel') }}
          </v-btn>
          <v-btn
            color="primary"
            size="small"
            :title="$t('latexCollab.comments.dialog.saveTitle')"
            :disabled="!canSubmitComment"
            @click="submitComment(collabColor)"
          >
            {{ $t('common.save') }}
          </v-btn>
        </div>
      </div>
    </Teleport>

    <!-- Floating AI Stream Window (shows streaming tokens) -->
    <Teleport to="body">
      <div
        v-if="aiStreamWindowOpen && aiResolvingCommentId !== null"
        ref="floatingAiStreamRef"
        class="floating-ai-stream-card"
        :style="floatingAiStreamStyle"
      >
        <!-- Draggable Header -->
        <div
          class="floating-ai-stream-header"
          @mousedown="startDragAiStream"
        >
          <div class="ai-stream-header-left">
            <div class="ai-pulse-indicator" />
            <LIcon size="16" class="mr-1" color="purple">mdi-robot</LIcon>
            <span class="floating-ai-stream-title">{{ $t('latexCollab.comments.aiStreaming') }}</span>
          </div>
          <v-spacer />
          <LIconBtn
            icon="mdi-close"
            size="x-small"
            :tooltip="$t('common.close')"
            @click="aiStreamWindowOpen = false"
          />
        </div>
        <!-- Stream Content -->
        <div ref="aiStreamContentRef" class="floating-ai-stream-body">
          <div v-if="!aiStreamContent" class="ai-stream-waiting">
            <v-progress-circular indeterminate size="20" width="2" color="purple" class="mr-2" />
            {{ $t('latexCollab.comments.aiWaiting') }}
          </div>
          <pre v-else class="ai-stream-content">{{ aiStreamContent }}<span class="ai-cursor" v-if="aiStreamStatus === 'streaming'">|</span></pre>
        </div>
        <!-- Status Footer -->
        <div class="floating-ai-stream-footer">
          <LTag
            :variant="aiStreamStatus === 'completed' ? 'success' : aiStreamStatus === 'error' ? 'danger' : 'info'"
            size="x-small"
          >
            {{ aiStreamStatus === 'completed' ? $t('latexCollab.comments.aiCompleted') :
               aiStreamStatus === 'error' ? $t('latexCollab.comments.aiError', { error: '' }) :
               $t('latexCollab.comments.aiProcessing') }}
          </LTag>
          <span v-if="aiStreamContent" class="ai-stream-chars">
            {{ aiStreamContent.length }} {{ $t('latexCollab.comments.aiChars') }}
          </span>
        </div>
      </div>
    </Teleport>

    <!-- Compile Log Dialog -->
    <CompileLogDialog
      v-model="compileLogDialog"
      :error="compileError"
      :issues="compileIssues"
      :log="compileLog"
      @jump-to-issue="jumpToIssue"
    />

    <!-- Zotero Dialog -->
    <v-dialog v-model="zoteroDialog" max-width="600">
      <v-card class="zotero-dialog">
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2">zotero</LIcon>
          <div>
            <div>{{ $t('latexCollab.zotero.title') }}</div>
            <div class="text-caption text-medium-emphasis">{{ workspace?.name }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" :tooltip="$t('common.close')" size="small" @click="zoteroDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0">
          <ZoteroPanel
            v-if="zoteroDialog && workspaceId"
            :workspace-id="workspaceId"
            @library-added="handleZoteroLibraryAdded"
            @library-synced="handleZoteroLibrarySynced"
            @library-removed="handleZoteroLibraryRemoved"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Notification Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      location="bottom right"
    >
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import { useAuth } from '@/composables/useAuth'
import { useMobile } from '@/composables/useMobile'
import { useSplitPaneResize } from '@/composables/useSplitPaneResize'
import { useWorkspaceSocket } from '@/components/MarkdownCollab/composables/useWorkspaceSocket'
import { useActiveDuration, useVisibilityTracker, useScrollDepth } from '@/composables/useAnalyticsMetrics'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import LatexEditorPane from '@/components/LatexCollab/LatexEditorPane.vue'
import LatexPdfViewer from '@/components/LatexCollab/LatexPdfViewer.vue'
import { GitDetailDialog } from '@/components/common/Git'
import ZoteroPanel from '@/components/LatexCollab/Zotero/ZoteroPanel.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getAvatarUrl, formatDisplayName, formatRelativeDate } from '@/utils/userUtils'
import { getSocket } from '@/services/socketService'

// Local composables - now actually used!
import {
  useLatexCompile,
  useLatexComments,
  useLatexOutline,
  useLatexSync,
  useLatexMembers
} from './composables'

// Local components
import {
  LatexTreePanel,
  LatexContentHeader,
  ShareDialog,
  CompileLogDialog
} from './components'

// Props for customizable base path (used by AI wrapper)
const props = defineProps({
  basePath: {
    type: String,
    default: '/LatexCollab'
  },
  aiEnabled: {
    type: Boolean,
    default: false
  },
  ghostTextEnabled: {
    type: Boolean,
    default: false
  },
  ghostTextDelay: {
    type: Number,
    default: 800
  }
})

// Emits for parent communication (used by AI wrapper)
const emit = defineEmits(['document-change', 'ai-command', 'ai-action', 'request-completion', 'update:ghostTextEnabled'])

const route = useRoute()
const router = useRouter()
const { locale, t } = useI18n()

// Simple snackbar for notifications
const snackbar = ref({ show: false, text: '', color: 'info' })
function showSnackbar(text, color = 'info') {
  snackbar.value = { show: true, text, color }
  setTimeout(() => { snackbar.value.show = false }, 4000)
}

// Computed route base for navigation
const routeBase = computed(() => props.basePath)

const { hasPermission, fetchPermissions, username: currentUsername, isAdmin } = usePermissions()
const { collabColor } = useAuth()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['tree', 'document'])
const { isMobile, isTablet } = useMobile()

// Mobile sidebar state
const mobileSidebarOpen = ref(false)

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const VIEWMODE_KEY = 'latex-collab-view-mode'
const TREE_COLLAPSED_KEY = 'latex-collab-tree-collapsed'
const TREE_WIDTH_KEY = 'latex-collab-tree-width'
const PANES_WIDTH_KEY = 'latex-collab-panes-width'
const OUTLINE_COLLAPSED_KEY = 'latex-outline-collapsed'
const AUTO_COMPILE_KEY = 'latex-collab-auto-compile'
const COMMENTS_HEIGHT_KEY = 'latex-collab-comments-height'
const AUTO_COMPILE_DELAY_KEY = 'latex-collab-auto-compile-delay'
const SYNC_KEY = 'latex-collab-sync-enabled'
const AI_CONTEXT_MAX_CHARS = 3800
const AI_CONTEXT_MAX_FILES = 6
const AI_CONTEXT_ALLOWED_EXTS = ['.tex', '.bib']

const workspace = ref(null)
const nodesFlat = ref([])

const currentText = ref('')
const gitSummary = ref({ users: [], totalChangedLines: 0 })
const treePanelRef = ref(null)
const editorRef = ref(null)
const pdfViewerRef = ref(null)
const pendingDocId = ref(null)
const pendingJump = ref(null)

// Panel states
const treeCollapsed = ref(localStorage.getItem(TREE_COLLAPSED_KEY) === 'true')
const treePanelWidth = ref(parseInt(localStorage.getItem(TREE_WIDTH_KEY)) || 280)
const viewMode = ref(localStorage.getItem(VIEWMODE_KEY) || 'split')
const resizingTree = ref(false)

// Comments panel resize state
const commentsPanelHeight = ref(parseInt(localStorage.getItem(COMMENTS_HEIGHT_KEY)) || 200)
const resizingComments = ref(false)
const previewContentRef = ref(null)

// Panel collapse states (for unified tree stack panels)
const FILES_COLLAPSED_KEY = 'latex-collab-files-collapsed'
const GIT_COLLAPSED_KEY = 'latex-collab-git-collapsed'
const filesCollapsed = ref(localStorage.getItem(FILES_COLLAPSED_KEY) === 'true')
const gitCollapsed = ref(localStorage.getItem(GIT_COLLAPSED_KEY) === 'true')
const gitDetailDialog = ref(false)
// Outline state - initialized later via useLatexOutline composable after selectedNode is available
const {
  panesContainerRef,
  editorPaneStyle,
  previewPaneStyle,
  resizingPanes,
  startResize: startPanesResize
} = useSplitPaneResize({
  storageKey: PANES_WIDTH_KEY,
  viewMode
})

// Sharing / members - using composable
// Note: We'll initialize useLatexMembers after workspaceId, workspace, hasPermission are available

const reviewMode = ref(false)

// Compile and sync state - initialized later via composables after selectedNode is available

// Comments state - initialized later via useLatexComments composable after selectedNode is available

// Zotero dialog
const zoteroDialog = ref(false)

const assetInputRef = ref(null)
const zipInputRef = ref(null)
const zipImporting = ref(false)

// Analytics: entity dimension for this workspace/document
const workspaceEntity = computed(() => `ws:${workspaceId.value}`)
const documentEntity = computed(() => selectedNodeId.value ? `doc:${selectedNodeId.value}` : '')

// Session active time tracking
useActiveDuration({
  category: 'latex',
  action: 'session_active_ms',
  name: () => workspaceEntity.value,
  dimensions: () => ({ entity: workspaceEntity.value, view: viewMode.value })
})

// Pane visibility tracking (editor, preview)
const paneVisibility = useVisibilityTracker({
  category: 'latex',
  action: 'pane_visible_ms',
  nameBuilder: (id) => `pane:${id}`,
  dimensions: () => ({ entity: documentEntity.value })
})

// Scroll depth for panes container
useScrollDepth(panesContainerRef, {
  category: 'latex',
  action: 'scroll_depth',
  name: () => `${documentEntity.value}|${viewMode.value}`,
  dimensions: () => ({ entity: documentEntity.value, view: viewMode.value })
})

// Register panes for visibility tracking
watch(panesContainerRef, (el) => {
  if (el) {
    paneVisibility.register('panes', el, { view: viewMode.value })
  }
})

watch(viewMode, (val) => {
  localStorage.setItem(VIEWMODE_KEY, val)
  // Pane width is handled by CSS (flex: 1 1 50%) by default
  // or by saved localStorage value when user has manually resized
})

watch(viewMode, async () => {
  await nextTick()
  editorRef.value?.refresh?.()
})

watch(treeCollapsed, (val) => {
  localStorage.setItem(TREE_COLLAPSED_KEY, val.toString())
})

watch(filesCollapsed, (val) => {
  localStorage.setItem(FILES_COLLAPSED_KEY, val.toString())
})

watch(gitCollapsed, (val) => {
  localStorage.setItem(GIT_COLLAPSED_KEY, val.toString())
})

// outlineCollapsed watcher is now handled by useLatexOutline composable
// autoCompileEnabled, autoCompileDelay watchers are now handled by useLatexCompile composable
// syncEnabled watcher is now handled by useLatexSync composable

watch(isMobile, (val) => {
  if (!val) {
    viewMode.value = 'split'
  }
})

watch(
  () => workspace.value?.latest_compile_job_id,
  (jobId) => {
    if (jobId) {
      loadCompileStatus(jobId)
    }
  }
)

const workspaceId = computed(() => Number(route.params.workspaceId))
const routeDocId = computed(() => (route.params.documentId ? Number(route.params.documentId) : null))

// Workspace socket for real-time tree updates
const {
  isConnected: wsConnected,
  recentlyAddedNodeIds,
  connect: wsConnect,
  emitNodeCreated,
  emitNodeRenamed,
  emitNodeDeleted,
  emitNodeMoved
} = useWorkspaceSocket(workspaceId, {
  onNodeCreated: (data) => {
    // Add the new node to the tree
    const newNode = { ...data.node, type: data.node.type }
    nodesFlat.value = [...nodesFlat.value, newNode]
    // Git panel updates are now handled by useGitStatus composable via socket events
  },
  onNodeRenamed: (data) => {
    // Update the node title in the tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.title = data.newTitle
      nodesFlat.value = [...nodesFlat.value]
    }
    // Git panel updates are now handled by useGitStatus composable via socket events
  },
  onNodeDeleted: (data) => {
    // Remove the node from the tree (and children recursively)
    const removeRecursive = (nodeId) => {
      const children = nodesFlat.value.filter(n => n.parent_id === nodeId)
      children.forEach(c => removeRecursive(c.id))
      nodesFlat.value = nodesFlat.value.filter(n => n.id !== nodeId)
    }
    removeRecursive(data.nodeId)

    // If we're viewing the deleted document, navigate away
    if (routeDocId.value === data.nodeId) {
      router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
    }
    // Git panel updates are now handled by useGitStatus composable via socket events
  },
  onNodeMoved: (data) => {
    // Update node position in tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.parent_id = data.newParentId
      node.order_index = data.newOrderIndex
      nodesFlat.value = [...nodesFlat.value]
    }
  }
})

// Compile status socket for real-time compile updates
let compileSocket = null
let compileSocketConnectHandler = null

function setupCompileSocket() {
  compileSocket = getSocket()
  if (!compileSocket) return

  // Handler for compile status updates
  const onCompileStatus = (data) => {
    if (data?.workspace_id !== workspaceId.value) return
    handleCompileStatusUpdate(data)
  }

  compileSocket.on('latex_collab:compile_status', onCompileStatus)

  // AI streaming event handlers
  compileSocket.on('latex_collab:ai_resolve:token', handleAiStreamToken)
  compileSocket.on('latex_collab:ai_resolve:completed', handleAiStreamCompleted)
  compileSocket.on('latex_collab:ai_resolve:error', handleAiStreamError)

  // Subscribe to workspace updates when connected
  compileSocketConnectHandler = () => {
    compileSocket.emit('latex_collab:subscribe_workspace', { workspace_id: workspaceId.value })
  }

  if (compileSocket.connected) {
    compileSocketConnectHandler()
  }
  compileSocket.on('connect', compileSocketConnectHandler)
}

function cleanupCompileSocket() {
  if (!compileSocket) return
  compileSocket.off('latex_collab:compile_status')
  compileSocket.off('latex_collab:ai_resolve:token', handleAiStreamToken)
  compileSocket.off('latex_collab:ai_resolve:completed', handleAiStreamCompleted)
  compileSocket.off('latex_collab:ai_resolve:error', handleAiStreamError)
  if (compileSocketConnectHandler) {
    compileSocket.off('connect', compileSocketConnectHandler)
  }
  if (workspaceId.value) {
    compileSocket.emit('latex_collab:unsubscribe_workspace', { workspace_id: workspaceId.value })
  }
  compileSocket = null
  compileSocketConnectHandler = null
}

const selectedNodeId = computed(() => routeDocId.value)
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodesFlat.value.find(n => n.id === selectedNodeId.value) || null
})

// ============================================================
// COMPOSABLES INTEGRATION
// ============================================================

// Members management composable
const {
  shareDialog,
  members,
  membersLoading,
  shareError,
  removingUsername,
  ownerInfo,
  canShareWorkspace,
  excludedUsernames,
  loadMembers,
  openShareDialog,
  inviteMember,
  removeMember
} = useLatexMembers({
  workspaceId,
  workspace,
  hasPermission,
  currentUsername,
  isAdmin
})

// Outline management composable
const {
  outlineCollapsed,
  outlineItems,
  outlineCollapsedIds,
  outlineFlatItems,
  outlineEmptyLabel,
  toggleOutlineCollapsed,
  isOutlineItemCollapsed,
  toggleOutlineItem,
  scheduleOutlineUpdate,
  jumpToOutlineItem,
  resetOutline
} = useLatexOutline({
  selectedNode,
  editorRef
})

// Comments socket for real-time comment sync
const commentsSocket = ref(null)

// Initialize comments socket
function initCommentsSocket() {
  commentsSocket.value = getSocket()
}

// Comments management composable
const {
  comments,
  activeCommentId,
  commentDialog,
  commentDraft,
  commentError,
  pendingCommentRange,
  commentCardPosition,
  commentTextareaRef,
  replyingToId,
  replyDraft,
  canComment,
  canSubmitComment,
  canSubmitReply,
  loadComments,
  openCommentDialog,
  submitComment,
  toggleCommentResolved,
  deleteComment,
  selectComment,
  resetComments,
  startReply,
  cancelReply,
  submitReply,
  navigateToComment,
  highlightCommentRange
} = useLatexComments({
  workspaceId,
  selectedNode,
  editorRef,
  hasPermission,
  onNavigateToDocument: handleNavigateToDocument,
  socket: commentsSocket
})

/**
 * Check if a comment belongs to a different document than currently selected.
 * Uses number comparison to avoid string/number type mismatch.
 * @param {Object} comment - The comment to check
 * @returns {boolean} True if comment is in a different document
 */
function isCommentInOtherDocument(comment) {
  if (!comment?.document_id) return false
  const currentDocId = selectedNode.value?.id
  if (currentDocId == null) return true
  return Number(comment.document_id) !== Number(currentDocId)
}

/**
 * Handle navigation to a document from a comment click.
 * Opens the document and then highlights the comment range.
 */
function handleNavigateToDocument(documentId, comment) {
  // Convert to number for consistent comparison with nodeById keys
  const docIdNum = Number(documentId)
  const node = nodeById.value.get(docIdNum)

  if (!node) {
    console.warn('[handleNavigateToDocument] Node not found for documentId:', documentId)
    return
  }

  // Select the document node - use the router to navigate
  router.push(`${routeBase.value}/workspace/${workspaceId.value}/document/${docIdNum}`)

  // After document loads, highlight the comment range
  if (comment && comment.range_start != null && comment.range_end != null) {
    // Wait for editor to be ready then highlight
    nextTick(() => {
      setTimeout(() => {
        highlightCommentRange(comment)
      }, 400) // Delay to ensure editor has loaded the new document
    })
  }
}

// ============================================================
// AI Assistant for Comment Resolution
// ============================================================
const aiAssistantEnabled = ref(false)
const aiAssistantColor = ref('#9B59B6')  // LLARS KI purple
const aiAssistantUsername = ref('LLARS KI')
const aiResolvingCommentId = ref(null)

// AI Streaming Window State
const aiStreamWindowOpen = ref(false)
const aiStreamContent = ref('')
const aiStreamStatus = ref('idle') // 'idle' | 'streaming' | 'completed' | 'error'
const aiStreamResult = ref(null)
const floatingAiStreamRef = ref(null)
const aiStreamDragOffset = ref({ x: 0, y: 0 })
const isDraggingAiStream = ref(false)
const aiStreamPosition = ref({ x: 100, y: 100 })
const aiStreamContentRef = ref(null)

const floatingAiStreamStyle = computed(() => ({
  left: `${Math.max(10, aiStreamPosition.value.x)}px`,
  top: `${Math.max(10, aiStreamPosition.value.y)}px`
}))

/**
 * Fetch AI assistant settings from the server
 */
async function loadAiAssistantSettings() {
  try {
    const res = await axios.get(`${API_BASE}/api/system/ai-assistant`, {
      headers: authHeaders()
    })
    if (res.data?.success && res.data?.ai_assistant) {
      aiAssistantEnabled.value = res.data.ai_assistant.enabled
      aiAssistantColor.value = res.data.ai_assistant.color
      aiAssistantUsername.value = res.data.ai_assistant.username
    }
  } catch (e) {
    console.warn('Could not load AI assistant settings:', e)
    aiAssistantEnabled.value = false
  }
}

/**
 * Handle click on AI button - either start resolve or toggle stream window
 * @param {Object} comment - The comment
 */
function handleAiButtonClick(comment) {
  if (aiResolvingCommentId.value === comment.id) {
    // Already processing this comment - toggle the stream window
    aiStreamWindowOpen.value = !aiStreamWindowOpen.value
  } else {
    // Start new AI resolve
    aiResolveComment(comment)
  }
}

/**
 * Use AI to resolve a comment with streaming support.
 * @param {Object} comment - The comment to resolve
 */
async function aiResolveComment(comment) {
  if (!comment || aiResolvingCommentId.value !== null) return

  // Navigate to the comment's document first if needed
  const currentDocId = selectedNode.value?.id
  const commentDocId = comment.document_id
  const isSameDoc = currentDocId != null && Number(currentDocId) === Number(commentDocId)

  if (!isSameDoc) {
    handleNavigateToDocument(commentDocId, comment)
    await new Promise(resolve => setTimeout(resolve, 600))
  }

  // Reset stream state
  aiResolvingCommentId.value = comment.id
  aiStreamContent.value = ''
  aiStreamStatus.value = 'streaming'
  aiStreamResult.value = null
  aiStreamWindowOpen.value = true  // Open stream window automatically

  // Position the stream window near the comment
  const commentEl = document.querySelector(`.comment-thread[data-comment-id="${comment.id}"]`)
  if (commentEl) {
    const rect = commentEl.getBoundingClientRect()
    aiStreamPosition.value = { x: rect.right + 20, y: rect.top }
  } else {
    aiStreamPosition.value = { x: window.innerWidth / 2 - 180, y: window.innerHeight / 3 }
  }

  try {
    // Check if there's an existing stream we can reconnect to
    const statusRes = await axios.get(
      `${API_BASE}/api/latex-collab/comments/${comment.id}/ai-resolve/status`,
      { headers: authHeaders() }
    )

    if (statusRes.data?.active) {
      // Reconnect to existing stream
      aiStreamContent.value = statusRes.data.content || ''
      aiStreamStatus.value = statusRes.data.status || 'streaming'
      if (statusRes.data.result) {
        aiStreamResult.value = statusRes.data.result
      }
      return
    }

    // Start new streaming request
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/comments/${comment.id}/ai-resolve`,
      { auto_resolve: true, streaming: true },
      { headers: authHeaders() }
    )

    if (!res.data?.success) {
      throw new Error(res.data?.error || 'Failed to start AI streaming')
    }

    // Streaming started - tokens will arrive via Socket.IO
    // The REST response just confirms streaming has started
  } catch (e) {
    const errorMsg = e?.response?.data?.error || e?.message || 'Unknown error'
    showSnackbar(t('latexCollab.comments.aiError', { error: errorMsg }), 'error')
    console.error('AI resolve failed:', e)
    aiResolvingCommentId.value = null
    aiStreamStatus.value = 'error'
  }
}

/**
 * Handle incoming AI stream token
 */
function handleAiStreamToken(data) {
  if (data.comment_id !== aiResolvingCommentId.value) return

  aiStreamContent.value += data.token

  // Auto-scroll stream content
  nextTick(() => {
    if (aiStreamContentRef.value) {
      aiStreamContentRef.value.scrollTop = aiStreamContentRef.value.scrollHeight
    }
  })
}

/**
 * Handle AI stream completion
 */
function handleAiStreamCompleted(data) {
  if (data.comment_id !== aiResolvingCommentId.value) return

  aiStreamStatus.value = 'completed'
  aiStreamResult.value = data

  // Apply the text change to the editor
  const { changes } = data
  if (changes?.old_text && changes?.new_text && changes.range_start != null && changes.range_end != null) {
    if (editorRef.value?.replaceRange) {
      editorRef.value.replaceRange(
        changes.range_start,
        changes.range_end,
        changes.new_text,
        {
          collabColor: aiAssistantColor.value,
          collabUser: aiAssistantUsername.value
        }
      )
      // Refresh Git panel after AI changes
      setTimeout(() => {
        treePanelRef.value?.refreshGit?.()
      }, 500)
    }
  }

  showSnackbar(t('latexCollab.comments.aiSuccess'), 'success')

  // Reset after a delay to allow user to see the result
  setTimeout(() => {
    if (aiStreamStatus.value === 'completed') {
      aiResolvingCommentId.value = null
      // Keep window open so user can see final result
    }
  }, 2000)
}

/**
 * Handle AI stream error
 */
function handleAiStreamError(data) {
  if (data.comment_id !== aiResolvingCommentId.value) return

  aiStreamStatus.value = 'error'
  showSnackbar(t('latexCollab.comments.aiError', { error: data.error }), 'error')

  setTimeout(() => {
    aiResolvingCommentId.value = null
  }, 3000)
}

// AI Stream Window Drag Functions
function startDragAiStream(e) {
  if (e.button !== 0) return
  isDraggingAiStream.value = true
  const card = floatingAiStreamRef.value
  if (!card) return
  const rect = card.getBoundingClientRect()
  aiStreamDragOffset.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  document.addEventListener('mousemove', dragAiStream)
  document.addEventListener('mouseup', stopDragAiStream)
  e.preventDefault()
}

function dragAiStream(e) {
  if (!isDraggingAiStream.value) return
  aiStreamPosition.value = {
    x: Math.max(0, e.clientX - aiStreamDragOffset.value.x),
    y: Math.max(0, e.clientY - aiStreamDragOffset.value.y)
  }
}

function stopDragAiStream() {
  isDraggingAiStream.value = false
  document.removeEventListener('mousemove', dragAiStream)
  document.removeEventListener('mouseup', stopDragAiStream)
}

// Compile management composable
const {
  compileJobId,
  compileStatus,
  compileError,
  compileLog,
  compileHasPdf,
  compileHasSynctex,
  compileLogDialog,
  pdfRefreshKey,
  compileCommitId,
  compileCommitOptions,
  compileIssues,
  autoCompileEnabled,
  autoCompileDelay,
  canCompile,
  isCompiling,
  compileStatusLabel,
  compileStatusColor,
  canSync,
  pdfJobId,
  loadCompileStatus,
  loadCommitOptions,
  scheduleAutoCompile,
  triggerCompile,
  handleCompileStatusUpdate
} = useLatexCompile({
  workspaceId,
  selectedNode,
  editorRef,
  resolveDocumentIdFromPath,
  normalizePath,
  reviewMode,
  hasPermission
})

// Sync management composable
const {
  syncEnabled,
  handleEditorSyncRequest,
  handlePdfClick
} = useLatexSync({
  selectedNode,
  pdfViewerRef,
  compileJobId,
  canSync,
  jumpToDocument
})

const editorReadonly = computed(() => {
  // Read-only if user lacks edit permission, in review mode, or document is Zotero-managed
  if (!hasPermission('feature:latex_collab:edit')) return true
  if (reviewMode.value) return true
  if (selectedNode.value?.is_zotero_managed) return true
  return false
})

const canSetMainDocument = computed(() => {
  return !!(selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id && hasPermission('feature:latex_collab:edit'))
})

// canCompile, canSync, pdfJobId, isCompiling, compileStatusLabel, compileStatusColor
// now provided by useLatexCompile composable

// canComment and canSubmitComment now provided by useLatexComments composable

// Tree panel resize
function startTreeResize(event) {
  event.preventDefault()
  resizingTree.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onTreeMouseMove)
  document.addEventListener('mouseup', stopTreeResize)
}

function onTreeMouseMove(event) {
  if (!resizingTree.value) return
  // Allow very small widths (min 48px for icon-only mode), max 600px
  const newWidth = Math.max(48, Math.min(600, event.clientX))
  treePanelWidth.value = newWidth
}

function stopTreeResize() {
  resizingTree.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
  localStorage.setItem(TREE_WIDTH_KEY, treePanelWidth.value.toString())
}

// Comments panel resize (vertical)
function startCommentsResize(event) {
  event.preventDefault()
  resizingComments.value = true
  document.body.style.cursor = 'row-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onCommentsMouseMove)
  document.addEventListener('mouseup', stopCommentsResize)
}

function onCommentsMouseMove(event) {
  if (!resizingComments.value || !previewContentRef.value) return
  const containerRect = previewContentRef.value.getBoundingClientRect()
  const mouseY = event.clientY
  const containerBottom = containerRect.bottom
  // Height is from mouse position to bottom of container
  const newHeight = containerBottom - mouseY
  // Min 100px, max 400px
  commentsPanelHeight.value = Math.max(100, Math.min(400, newHeight))
}

function stopCommentsResize() {
  resizingComments.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  document.removeEventListener('mousemove', onCommentsMouseMove)
  document.removeEventListener('mouseup', stopCommentsResize)
  localStorage.setItem(COMMENTS_HEIGHT_KEY, commentsPanelHeight.value.toString())
}

// Computed style for comments panel
const commentsPanelStyle = computed(() => ({
  height: `${commentsPanelHeight.value}px`,
  minHeight: `${commentsPanelHeight.value}px`,
  maxHeight: `${commentsPanelHeight.value}px`
}))

// Floating comment card (inline beside text, no overlay)
const floatingCommentCardRef = ref(null)
const floatingCommentDragOffset = ref({ x: 0, y: 0 })
const isDraggingCommentCard = ref(false)

const floatingCommentCardStyle = computed(() => {
  const pos = commentCardPosition.value
  return {
    left: `${Math.max(10, pos.x)}px`,
    top: `${Math.max(10, pos.y)}px`
  }
})

function startDragCommentCard(e) {
  if (e.button !== 0) return // Only left mouse button
  isDraggingCommentCard.value = true
  const card = floatingCommentCardRef.value
  if (!card) return
  const rect = card.getBoundingClientRect()
  floatingCommentDragOffset.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
  document.addEventListener('mousemove', dragCommentCard)
  document.addEventListener('mouseup', stopDragCommentCard)
  e.preventDefault()
}

function dragCommentCard(e) {
  if (!isDraggingCommentCard.value) return
  const newX = e.clientX - floatingCommentDragOffset.value.x
  const newY = e.clientY - floatingCommentDragOffset.value.y
  commentCardPosition.value = {
    x: Math.max(0, newX),
    y: Math.max(0, newY)
  }
}

function stopDragCommentCard() {
  isDraggingCommentCard.value = false
  document.removeEventListener('mousemove', dragCommentCard)
  document.removeEventListener('mouseup', stopDragCommentCard)
}

// Outline functions now provided by useLatexOutline composable

// Auto-compile when no PDF exists
let autoCompileTriggered = false
function handleNoPdf() {
  // Prevent multiple auto-compile attempts per session
  if (autoCompileTriggered) return
  // Only auto-compile if not already compiling and user has permission
  if (!isCompiling.value && canCompile.value) {
    autoCompileTriggered = true
    triggerCompile()
  } else if (!isCompiling.value && hasPermission('feature:latex_collab:edit')) {
    // If no document selected yet, schedule retry after short delay
    setTimeout(() => {
      if (!autoCompileTriggered && !isCompiling.value && canCompile.value) {
        autoCompileTriggered = true
        triggerCompile()
      }
    }, 500)
  }
}

// Initialize pane width on mount
onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Load AI assistant settings
  loadAiAssistantSettings()

  // Connect to workspace socket for real-time tree updates
  wsConnect()

  // Connect to compile status socket for real-time compile updates
  setupCompileSocket()

  // Connect to comments socket for real-time comment sync
  initCommentsSocket()

  // Auto-select first file if none selected
  if (!routeDocId.value) {
    const preferred = nodesFlat.value.find(n => n.id === workspace.value?.main_document_id && n.type === 'file' && !n.asset_id)
      || nodesFlat.value.find(n => n.type === 'file' && !n.asset_id)
    if (preferred) router.replace(`${routeBase.value}/workspace/${workspaceId.value}/document/${preferred.id}`)
  }

  if (!isMobile.value) {
    viewMode.value = 'split'
  }

  if (workspace.value?.latest_compile_job_id) {
    await loadCompileStatus(workspace.value.latest_compile_job_id)
  }

  // Editor pane width is now handled by CSS (flex: 1 1 50%) by default
  // Only apply saved width from localStorage when user has manually resized
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onTreeMouseMove)
  document.removeEventListener('mouseup', stopTreeResize)
  document.removeEventListener('mousemove', onCommentsMouseMove)
  document.removeEventListener('mouseup', stopCommentsResize)
  // Cleanup compile status socket
  cleanupCompileSocket()
  // Timer cleanups are now handled by composables:
  // - autoCompileTimer, compilePollTimer by useLatexCompile
  // - syncTimer by useLatexSync
  // - outlineUpdateTimer by useLatexOutline
  // - Git panel refresh is now handled by useGitStatus composable in GitStatusWidget
})

function onEditorContentChange(text) {
  currentText.value = text
  if (pendingDocId.value && pendingDocId.value === selectedNodeId.value) {
    setLoading('document', false)
    pendingDocId.value = null
  }
  scheduleOutlineUpdate(text)
  scheduleAutoCompile()
  // Git panel is updated via WebSocket 'document_saved' events (see handleDocumentSaved)
  // No need for polling-based refresh here
  // Emit for AI wrapper component
  emit('document-change', text)
}

/**
 * Handle document_saved events from YJS server for real-time Git panel updates.
 *
 * This function is the final step in the real-time update chain:
 *   1. User types in editor → Yjs local update
 *   2. Yjs syncs to server → 2s debounce timer starts
 *   3. After 2s inactivity → YJS server saves to DB
 *   4. Server broadcasts `document_saved` to workspace room
 *   5. useYjsCollaboration receives event → calls onDocumentSaved callback
 *   6. EditorPane emits 'document-saved' event to parent
 *   7. This function receives the event and refreshes Git panel
 *
 * The workspace-level check ensures we only refresh for documents in THIS
 * workspace, not unrelated workspaces the user might have open in other tabs.
 *
 * @param {Object} data - Event payload from YJS server
 * @param {number} data.documentId - The document that was saved
 * @param {number} data.workspaceId - Workspace containing the document
 * @param {string} data.kind - Document type ('latex')
 * @param {number} data.contentLength - Length of saved content
 * @param {string} data.savedAt - ISO timestamp of save
 */
function handleDocumentSaved(data) {
  console.log('[LatexCollabWorkspace] document_saved empfangen:', data)
  // Git panel updates are now handled by useGitStatus composable via socket events
  // The composable automatically listens for 'latex_collab:commit_created' events
}

/**
 * Handle document_updated events from YJS server.
 * Note: Server no longer sends diff data - clients calculate diff locally.
 *
 * @param {Object} data - Event payload from YJS server
 * @param {number} data.documentId - Updated document ID
 * @param {number} data.workspaceId - Workspace containing the document
 * @param {string} data.kind - Document type ('latex')
 * @param {number} data.timestamp - Event timestamp
 */
function handleDocumentUpdated(data) {
  // Server event is now lightweight - local diff is handled by handleDiffCalculated
  // This event can be used for other purposes like activity indicators
}

/**
 * Handle local diff calculation from LatexEditorPane for INSTANT Git panel updates.
 *
 * This is called on every YJS update with diff calculated locally against
 * the baseline stored in the YJS document. No server roundtrip required.
 *
 * @param {Object} data - Diff data from local calculation
 * @param {number} data.documentId - Document ID
 * @param {number} data.insertions - Characters inserted since baseline
 * @param {number} data.deletions - Characters deleted since baseline
 * @param {boolean} data.hasChanges - Whether document differs from baseline
 */
function handleDiffCalculated(data) {
  // Real-time diff updates are now handled by the GitStatusWidget's useGitStatus composable
  // which listens to socket events directly. This function is kept for potential future use.
  if (!data.documentId) return
  console.log('[LatexCollabWorkspace] Diff calculated:', data.documentId, data.insertions, data.deletions)
}

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString(locale.value || undefined)
  } catch {
    return iso
  }
}

// parseLatexLog and decorateIssues now in useLatexCompile composable

// Members functions now provided by useLatexMembers composable

// Zotero library event handlers
async function handleZoteroLibraryAdded(library) {
  // Refresh the file tree to show the new .bib file
  await loadTree()
}

async function handleZoteroLibrarySynced(library) {
  // Refresh the file tree to reflect updated .bib content
  await loadTree()
}

async function handleZoteroLibraryRemoved(library) {
  // The .bib file is kept but no longer synced - no tree refresh needed
  console.log('Zotero-Bibliothek entfernt:', library.library_name)
}

function buildTree(flat) {
  const byId = new Map(flat.map(n => [n.id, { ...n, children: [] }]))
  const roots = []
  for (const node of byId.values()) {
    if (node.parent_id == null) {
      roots.push(node)
      continue
    }
    const parent = byId.get(node.parent_id)
    if (parent) parent.children.push(node)
    else roots.push(node)
  }
  const sortRec = (arr) => {
    arr.sort((a, b) => (a.order_index ?? 0) - (b.order_index ?? 0) || a.id - b.id)
    arr.forEach(n => sortRec(n.children))
  }
  sortRec(roots)
  return roots
}

const treeNodes = computed(() => buildTree(nodesFlat.value))

function normalizePath(path) {
  if (!path) return ''
  let normalized = String(path).replace(/\\/g, '/').trim()
  if (normalized.startsWith('./')) normalized = normalized.slice(2)
  return normalized.replace(/^\/+/, '')
}

const nodeById = computed(() => {
  const map = new Map()
  nodesFlat.value.forEach((n) => map.set(n.id, n))
  return map
})

function buildNodePath(nodeId, cache) {
  if (cache.has(nodeId)) return cache.get(nodeId)
  const node = nodeById.value.get(nodeId)
  if (!node) return ''
  const parentPath = node.parent_id ? buildNodePath(node.parent_id, cache) : ''
  const full = parentPath ? `${parentPath}/${node.title}` : node.title
  cache.set(nodeId, full)
  return full
}

const nodePathById = computed(() => {
  const cache = new Map()
  const map = new Map()
  nodesFlat.value.forEach((n) => {
    map.set(n.id, buildNodePath(n.id, cache))
  })
  return map
})

const nodeIdByPath = computed(() => {
  const map = new Map()
  nodePathById.value.forEach((path, id) => {
    map.set(normalizePath(path), id)
  })
  return map
})

const nodeIdByFilename = computed(() => {
  const map = new Map()
  nodePathById.value.forEach((path, id) => {
    const name = normalizePath(path).split('/').pop()
    if (name && !map.has(name)) map.set(name, id)
  })
  return map
})

function resolveDocumentIdFromPath(path) {
  const normalized = normalizePath(path)
  if (!normalized) return null
  if (nodeIdByPath.value.has(normalized)) return nodeIdByPath.value.get(normalized)
  const filename = normalized.split('/').pop()
  if (filename && nodeIdByFilename.value.has(filename)) return nodeIdByFilename.value.get(filename)
  return null
}

function isAiContextNode(node) {
  if (!node || node.type !== 'file' || node.asset_id) return false
  const title = String(node.title || '').toLowerCase()
  return AI_CONTEXT_ALLOWED_EXTS.some(ext => title.endsWith(ext))
}

function getNodePathForAi(node) {
  if (!node?.id) return node?.title || ''
  return nodePathById.value.get(node.id) || node.title || ''
}

async function fetchAiContextDocuments(documentIds) {
  if (!Array.isArray(documentIds) || documentIds.length === 0) return new Map()

  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/documents/content`,
      { document_ids: documentIds },
      { headers: authHeaders() }
    )
    const docs = res.data?.documents || []
    const map = new Map()
    docs.forEach((doc) => {
      map.set(doc.id, doc.content_text || '')
    })
    return map
  } catch (e) {
    console.warn('[LatexCollabWorkspace] Konnte AI-Kontext nicht laden:', e)
    return new Map()
  }
}

async function getAiChatContext() {
  const currentNode = selectedNode.value
  const currentId = currentNode?.id || null
  const currentContent = editorRef.value?.getCurrentContent?.() || currentText.value || ''

  const mainId = workspace.value?.main_document_id || null

  const candidates = []
  if (currentNode && currentNode.type === 'file' && !currentNode.asset_id) {
    candidates.push(currentNode)
  }

  if (mainId && mainId !== currentId) {
    const mainNode = nodesFlat.value.find(n => n.id === mainId)
    if (isAiContextNode(mainNode)) {
      candidates.push(mainNode)
    }
  }

  if (candidates.length < AI_CONTEXT_MAX_FILES) {
    const additional = nodesFlat.value.filter((node) => {
      if (!isAiContextNode(node)) return false
      if (node.id === currentId) return false
      if (node.id === mainId) return false
      return true
    })
    candidates.push(...additional)
  }

  const limited = candidates.slice(0, AI_CONTEXT_MAX_FILES)
  const otherIds = limited
    .map(node => node.id)
    .filter(id => id && id !== currentId)

  const otherContentMap = await fetchAiContextDocuments(otherIds)

  let remaining = AI_CONTEXT_MAX_CHARS
  let context = ''
  const sources = []

  for (const node of limited) {
    const path = getNodePathForAi(node)
    const header = `${context ? '\n\n' : ''}[FILE: ${path}]\n`
    if (remaining <= header.length + 1) break

    const rawContent = node.id === currentId ? currentContent : (otherContentMap.get(node.id) || '')
    if (!rawContent) continue

    const available = remaining - header.length
    const truncated = rawContent.length > available
    const contentSlice = truncated ? rawContent.slice(0, available) : rawContent

    context += header + contentSlice
    remaining -= header.length + contentSlice.length

    sources.push({
      id: node.id,
      title: node.title || '',
      path,
      chars: contentSlice.length,
      truncated
    })

    if (remaining <= 0) break
  }

  if (!context && currentContent) {
    context = currentContent.slice(0, AI_CONTEXT_MAX_CHARS)
    sources.push({
      id: currentId,
      title: currentNode?.title || '',
      path: getNodePathForAi(currentNode),
      chars: context.length,
      truncated: currentContent.length > context.length
    })
  }

  return { content: context, sources }
}

async function loadTree() {
  await withLoading('tree', async () => {
    const res = await axios.get(`${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/tree`, {
      headers: authHeaders()
    })
    workspace.value = res.data.workspace
    nodesFlat.value = (res.data.nodes || []).map(n => ({ ...n, type: n.type }))
  })
}

// Debounce to prevent double-click issues
let lastSelectTime = 0
let lastSelectNodeId = null

function handleSelectNode(nodeId) {
  // Prevent duplicate clicks within 100ms on the same node
  const now = Date.now()
  if (nodeId === lastSelectNodeId && now - lastSelectTime < 100) {
    console.log('[handleSelectNode] Doppelten Klick auf nodeId ignoriert:', nodeId)
    return
  }
  lastSelectTime = now
  lastSelectNodeId = nodeId

  const node = nodesFlat.value.find(n => n.id === nodeId)
  if (!node) return

  if (node.type === 'file') {
    router.push(`${routeBase.value}/workspace/${workspaceId.value}/document/${node.id}`)
    return
  }

  // Folder: keep workspace route, but don't force a document selection
  router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
}

function openAssetPicker() {
  if (!hasPermission('feature:latex_collab:edit')) return
  assetInputRef.value?.click()
}

// ============================================================
// ZIP Import/Export Functions
// ============================================================

/**
 * Download the workspace as a ZIP file
 */
async function downloadWorkspaceZip() {
  if (!workspaceId.value) return

  try {
    const response = await axios.get(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/export`,
      {
        headers: authHeaders(),
        responseType: 'blob'
      }
    )

    // Extract filename from Content-Disposition header or generate one
    const contentDisposition = response.headers['content-disposition']
    let filename = `workspace_${workspaceId.value}.zip`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
      }
    }

    // Create download link
    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    showSnackbar(t('latexCollab.zip.downloadSuccess'), 'success')
  } catch (e) {
    console.error('ZIP download failed:', e)
    showSnackbar(t('latexCollab.zip.downloadError'), 'error')
  }
}

/**
 * Open the ZIP file picker for import
 */
function openZipImportDialog() {
  if (!hasPermission('feature:latex_collab:edit')) return
  zipInputRef.value?.click()
}

/**
 * Handle ZIP file import
 */
async function handleZipImport(event) {
  const file = event?.target?.files?.[0]
  if (!file) return

  if (!file.name.toLowerCase().endsWith('.zip')) {
    showSnackbar(t('latexCollab.zip.invalidFile'), 'error')
    return
  }

  if (zipImporting.value) return
  zipImporting.value = true

  try {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/import`,
      formData,
      { headers: authHeaders() }
    )

    if (response.data?.success) {
      const { imported_count, skipped_count } = response.data
      showSnackbar(
        t('latexCollab.zip.importSuccess', { imported: imported_count, skipped: skipped_count }),
        'success'
      )
      // Refresh the tree to show imported files
      await loadTree()
    }
  } catch (e) {
    console.error('ZIP import failed:', e)
    const errorMsg = e?.response?.data?.error || e?.message || 'Unknown error'
    showSnackbar(t('latexCollab.zip.importError', { error: errorMsg }), 'error')
  } finally {
    zipImporting.value = false
    // Reset the input so the same file can be selected again
    if (event?.target) {
      event.target.value = ''
    }
  }
}

async function handleAssetFiles(event) {
  const files = Array.from(event?.target?.files || [])
  if (!files.length) return

  for (const file of files) {
    await uploadAsset(file)
  }

  if (event?.target) {
    event.target.value = ''
  }
}

async function uploadAsset(file) {
  if (!workspaceId.value || !file) return
  if (!hasPermission('feature:latex_collab:edit')) return

  const parentId = selectedNode.value?.type === 'folder'
    ? selectedNode.value.id
    : (selectedNode.value?.parent_id ?? null)

  const form = new FormData()
  form.append('file', file)
  if (parentId) form.append('parent_id', String(parentId))

  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/assets`,
      form,
      { headers: authHeaders() }
    )
    const newNode = res.data.node
    if (newNode) {
      nodesFlat.value = [...nodesFlat.value, { ...newNode, type: newNode.type }]
      emitNodeCreated(newNode)
    }
  } catch (e) {
    console.error('Asset-Upload fehlgeschlagen:', e)
    await loadTree()
  }
}

async function handleCreateNode({ parentId, type, title }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/documents`,
      {
        workspace_id: workspaceId.value,
        parent_id: parentId ?? null,
        type,
        title
      },
      { headers: authHeaders() }
    )

    // Add node to local tree immediately
    const newNode = res.data.node
    if (newNode) {
      nodesFlat.value = [...nodesFlat.value, { ...newNode, type: newNode.type }]
      // Broadcast to other users
      emitNodeCreated(newNode)
    }
  } catch (e) {
    console.error('Konnte Knoten nicht erstellen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleRenameNode({ id, parentId, title }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/latex-collab/documents/${id}`,
      { parent_id: parentId ?? null, title },
      { headers: authHeaders() }
    )

    // Update local tree immediately
    const node = nodesFlat.value.find(n => n.id === id)
    if (node) {
      node.title = title
      nodesFlat.value = [...nodesFlat.value]
      // Broadcast to other users
      emitNodeRenamed(id, title)
    }
  } catch (e) {
    console.error('Konnte Knoten nicht umbenennen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleDeleteNode({ id }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.delete(`${API_BASE}/api/latex-collab/documents/${id}`, {
      headers: authHeaders()
    })

    // Remove from local tree immediately (including children)
    const removeRecursive = (nodeId) => {
      const children = nodesFlat.value.filter(n => n.parent_id === nodeId)
      children.forEach(c => removeRecursive(c.id))
      nodesFlat.value = nodesFlat.value.filter(n => n.id !== nodeId)
    }
    removeRecursive(id)

    // Broadcast to other users
    emitNodeDeleted(id)
    // Git panel updates are now handled by useGitStatus composable via socket events

    // Navigate away if viewing deleted document
    if (routeDocId.value === id) {
      router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
    }
  } catch (e) {
    console.error('Konnte Knoten nicht loeschen:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function handleMoveNode({ id, parentId, orderIndex }) {
  if (!hasPermission('feature:latex_collab:edit')) return
  try {
    await axios.patch(
      `${API_BASE}/api/latex-collab/documents/${id}`,
      { parent_id: parentId ?? null, order_index: orderIndex },
      { headers: authHeaders() }
    )

    // Update local tree immediately
    const node = nodesFlat.value.find(n => n.id === id)
    if (node) {
      node.parent_id = parentId ?? null
      node.order_index = orderIndex
      nodesFlat.value = [...nodesFlat.value]
      // Broadcast to other users
      emitNodeMoved(id, parentId ?? null, orderIndex)
    }
  } catch (e) {
    console.error('Konnte Knoten nicht verschieben:', e)
    await loadTree() // Fallback: reload tree
  }
}

async function setMainDocument() {
  if (!canSetMainDocument.value || !selectedNode.value) return
  try {
    const res = await axios.patch(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/main`,
      { document_id: selectedNode.value.id },
      { headers: authHeaders() }
    )
    workspace.value = res.data.workspace || workspace.value
  } catch (e) {
    console.error('Konnte Hauptdokument nicht festlegen:', e)
  }
}

// Compile and sync functions now provided by useLatexCompile and useLatexSync composables

// Comments functions now provided by useLatexComments composable

function jumpToIssue(issue) {
  if (!issue || !issue.document_id) return
  const node = nodeById.value.get(issue.document_id)
  if (!node || node.asset_id) return
  jumpToDocument(issue.document_id, issue.line || 1, 1)
}

function jumpToDocument(documentId, line = 1, column = 1) {
  if (!documentId) return
  const node = nodeById.value.get(documentId)
  if (!node || node.asset_id) return
  if (selectedNodeId.value === documentId) {
    nextTick(() => {
      editorRef.value?.jumpToLine?.(line, column)
    })
    return
  }
  pendingJump.value = { documentId, line, column }
  router.push(`${routeBase.value}/workspace/${workspaceId.value}/document/${documentId}`)
}

// Get current content from editor for diff viewer in Git Panel
function getEditorContent() {
  return editorRef.value?.getCurrentContent?.() || ''
}

async function refreshCommits() {
  // Refresh the git baseline after commit to update diff decorations
  await editorRef.value?.refreshBaseline?.()
  editorRef.value?.clearHighlights?.()
  await loadCommitOptions()
  // Git panel updates are now handled by useGitStatus composable via socket events
}

async function handleRollback(payload) {
  const documentId = typeof payload === 'object' && payload !== null ? payload.documentId : payload
  const baseline = typeof payload === 'object' && payload !== null ? payload.baseline : null
  console.log('[handleRollback] Aufgerufen mit documentId:', documentId, 'selectedNodeId:', selectedNodeId.value)

  // Build the room name for this document
  const roomName = `latex_${documentId}`

  // If the rolled back document is currently open, use reloadRoom which:
  // 1. Destroys the local ydoc (clearing all local state/history)
  // 2. Creates a fresh ydoc
  // 3. Sends reload_room to server which clears cache and reloads from DB
  // 4. Server broadcasts snapshot_document to all clients
  // This ensures a clean slate without Yjs merge conflicts
  if (selectedNodeId.value === documentId) {
    console.log('[handleRollback] Dokument ist derzeit geoeffnet, verwende reloadRoom fuer sauberen Reset')
    const result = await editorRef.value?.reloadRoom?.()
    console.log('[handleRollback] reloadRoom Ergebnis:', result)
    // Refresh the baseline to update diff decorations
    await editorRef.value?.refreshBaseline?.()
    editorRef.value?.clearHighlights?.()
  } else {
    // If the document is NOT currently open, only invalidate the YJS server cache
    // This is necessary because the YJS server caches room state and would serve
    // stale content when the user later opens this document
    console.log('[handleRollback] Dokument ist NICHT geoeffnet, invalidiere YJS-Cache fuer Raum:', roomName)
    const cacheResult = await editorRef.value?.reloadAnyRoom?.(roomName)
    console.log('[handleRollback] reloadAnyRoom Ergebnis:', cacheResult)
  }
}

async function handleRestored(documentId) {
  console.log('[handleRestored] Datei wiederhergestellt:', documentId)
  // Refresh the tree to show the restored file
  await loadTree()
}

async function handleBeforeRollback(documentId) {
  if (documentId && selectedNodeId.value === documentId) {
    await editorRef.value?.flushDocumentState?.()
  }
}

async function handleBeforeCommit(documentIds = []) {
  if (!Array.isArray(documentIds) || documentIds.length === 0) return
  if (selectedNodeId.value && documentIds.includes(selectedNodeId.value)) {
    await editorRef.value?.flushDocumentState?.()
  }
}

// Track if this is the initial mount vs subsequent document switches
let isInitialDocumentLoad = true
watch(
  selectedNodeId,
  (docId) => {
    currentText.value = ''
    gitSummary.value = { users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }
    resetOutline() // Using composable function
    if (docId) {
      // Only show loading skeleton on initial mount, not on document switches
      // Document switches are handled smoothly by the editor's YJS room switch
      if (isInitialDocumentLoad) {
        pendingDocId.value = docId
        setLoading('document', true)
        isInitialDocumentLoad = false
      }
      const node = nodesFlat.value.find(n => n.id === docId)
      if (node?.asset_id) {
        pendingDocId.value = null
        setLoading('document', false)
      }
      activeCommentId.value = null
      commentError.value = ''
      commentDraft.value = ''
      // Comments are loaded at workspace level now, no need to reload on document change
      loadCommitOptions()
      if (pendingJump.value && pendingJump.value.documentId === docId) {
        const { line, column } = pendingJump.value
        pendingJump.value = null
        nextTick(() => {
          editorRef.value?.jumpToLine?.(line, column)
        })
      }
    } else {
      pendingDocId.value = null
      setLoading('document', false)
      comments.value = []
      activeCommentId.value = null
      pendingCommentRange.value = null
      commentError.value = ''
      commentDraft.value = ''
      compileCommitId.value = null
      compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
    }
  },
  { immediate: true }
)

watch(
  selectedNode,
  (node) => {
    if (node && node.type === 'file' && !node.asset_id) {
      // Comments are loaded at workspace level now
      loadCommitOptions()
    }
  }
)

defineExpose({
  getAiChatContext
})
</script>

<style scoped>
/* Import extracted styles */
@import './styles/LatexCollabWorkspace.css';
</style>
