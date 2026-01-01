<template>
  <div class="workspace-root" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <input
      ref="assetInputRef"
      type="file"
      class="asset-input"
      multiple
      @change="handleAssetFiles"
    />
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
      temporary
      width="300"
      class="mobile-tree-drawer"
    >
      <div class="mobile-tree-content">
        <div class="tree-main">
          <MarkdownTreePanel
            :workspace-id="workspaceId"
            :nodes="treeNodes"
            :selected-id="selectedNodeId"
            :loading="isLoading('tree')"
            :can-edit="hasPermission('feature:latex_collab:edit')"
            :recently-added-ids="recentlyAddedNodeIds"
            file-placeholder="z. B. main.tex"
            file-icon="mdi-file-code-outline"
            file-icon-color="primary"
            @select="(id) => { handleSelectNode(id); mobileSidebarOpen = false; }"
            @create="handleCreateNode"
            @rename="handleRenameNode"
            @remove="handleDeleteNode"
            @move="handleMoveNode"
          />
        </div>
        <div class="tree-outline-panel" :class="{ collapsed: outlineCollapsed }">
          <div class="tree-outline-header">
            <div class="tree-outline-title">
              <v-icon size="14">mdi-format-list-bulleted</v-icon>
              Verzeichnis
            </div>
            <v-btn
              icon
              variant="text"
              size="x-small"
              :title="outlineCollapsed ? 'Verzeichnis anzeigen' : 'Verzeichnis ausblenden'"
              @click="toggleOutlineCollapsed"
            >
              <v-icon size="16">{{ outlineCollapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
            </v-btn>
          </div>
          <div v-if="!outlineCollapsed" class="tree-outline-list">
            <div v-if="outlineFlatItems.length === 0" class="tree-outline-empty">
              {{ outlineEmptyLabel }}
            </div>
            <div
              v-for="item in outlineFlatItems"
              :key="item.id"
              class="tree-outline-item"
              :style="{ paddingLeft: `${8 + item.depth * 12}px` }"
            >
              <button
                v-if="item.hasChildren"
                class="tree-outline-toggle"
                type="button"
                :title="isOutlineItemCollapsed(item.id) ? 'Aufklappen' : 'Einklappen'"
                @click.stop="toggleOutlineItem(item.id)"
              >
                <v-icon size="14">
                  {{ isOutlineItemCollapsed(item.id) ? 'mdi-chevron-right' : 'mdi-chevron-down' }}
                </v-icon>
              </button>
              <span v-else class="tree-outline-spacer"></span>
              <button
                class="tree-outline-link"
                type="button"
                :title="item.title"
                @click="jumpToOutlineItem(item)"
              >
                {{ item.title }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <template #append>
        <v-divider />
        <v-list density="compact" class="pa-2">
          <v-list-item
            prepend-icon="mdi-home"
            title="Startseite"
            @click="router.push('/Home')"
          />
          <v-list-item
            prepend-icon="mdi-folder-multiple"
            title="Alle Workspaces"
            @click="router.push(routeBase.value)"
          />
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Desktop: Collapsible File Tree -->
    <div
      v-if="!isMobile"
      class="tree-panel"
      :class="{ collapsed: treeCollapsed }"
      :style="!treeCollapsed ? { width: treePanelWidth + 'px' } : {}"
    >
      <!-- Collapsed State -->
      <div v-if="treeCollapsed" class="tree-collapsed" @click="treeCollapsed = false">
        <div class="collapsed-bar">
          <div class="collapsed-icon-box">
            <v-icon size="18">mdi-file-tree</v-icon>
          </div>
          <span class="collapsed-label">Dateien</span>
          <v-spacer />
          <v-icon size="18" class="expand-icon">mdi-chevron-right</v-icon>
        </div>
      </div>

      <!-- Expanded State -->
      <div v-else class="tree-expanded">
        <div class="tree-stack">
          <div class="tree-main">
            <MarkdownTreePanel
              :workspace-id="workspaceId"
              :nodes="treeNodes"
              :selected-id="selectedNodeId"
              :loading="isLoading('tree')"
              :can-edit="hasPermission('feature:latex_collab:edit')"
              :recently-added-ids="recentlyAddedNodeIds"
              file-placeholder="z. B. main.tex"
              file-icon="mdi-file-code-outline"
              file-icon-color="primary"
              @select="handleSelectNode"
              @create="handleCreateNode"
              @rename="handleRenameNode"
              @remove="handleDeleteNode"
              @move="handleMoveNode"
            >
              <template #header-append>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  title="Asset hochladen"
                  @click.stop="openAssetPicker"
                >
                  <v-icon size="18">mdi-paperclip</v-icon>
                </v-btn>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  title="Einklappen"
                  @click.stop="treeCollapsed = true"
                >
                  <v-icon size="18">mdi-chevron-left</v-icon>
                </v-btn>
              </template>
            </MarkdownTreePanel>
          </div>
          <div class="tree-outline-panel" :class="{ collapsed: outlineCollapsed }">
            <div class="tree-outline-header">
              <div class="tree-outline-title">
                <v-icon size="14">mdi-format-list-bulleted</v-icon>
                Verzeichnis
              </div>
              <v-btn
                icon
                variant="text"
                size="x-small"
                :title="outlineCollapsed ? 'Verzeichnis anzeigen' : 'Verzeichnis ausblenden'"
                @click="toggleOutlineCollapsed"
              >
                <v-icon size="16">{{ outlineCollapsed ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
              </v-btn>
            </div>
            <div v-if="!outlineCollapsed" class="tree-outline-list">
              <div v-if="outlineFlatItems.length === 0" class="tree-outline-empty">
                {{ outlineEmptyLabel }}
              </div>
              <div
                v-for="item in outlineFlatItems"
                :key="item.id"
                class="tree-outline-item"
                :style="{ paddingLeft: `${8 + item.depth * 12}px` }"
              >
                <button
                  v-if="item.hasChildren"
                  class="tree-outline-toggle"
                  type="button"
                  :title="isOutlineItemCollapsed(item.id) ? 'Aufklappen' : 'Einklappen'"
                  @click.stop="toggleOutlineItem(item.id)"
                >
                  <v-icon size="14">
                    {{ isOutlineItemCollapsed(item.id) ? 'mdi-chevron-right' : 'mdi-chevron-down' }}
                  </v-icon>
                </button>
                <span v-else class="tree-outline-spacer"></span>
                <button
                  class="tree-outline-link"
                  type="button"
                  :title="item.title"
                  @click="jumpToOutlineItem(item)"
                >
                  {{ item.title }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Resize Divider: Tree | Content (Desktop only) -->
    <div
      v-if="!isMobile && !treeCollapsed"
      class="resize-divider vertical"
      :class="{ resizing: resizingTree }"
      @mousedown="startTreeResize"
    >
      <div class="resize-handle" />
    </div>

    <!-- Main Content Area -->
    <div class="content-area">
      <!-- Content Header - Subtle LLARS Design -->
      <div class="content-header">
        <div class="header-left">
          <!-- Mobile menu button -->
          <v-btn
            v-if="isMobile"
            icon
            variant="text"
            size="small"
            class="mr-2"
            title="Menü öffnen"
            @click="mobileSidebarOpen = true"
          >
            <v-icon>mdi-menu</v-icon>
          </v-btn>
          <v-btn
            variant="text"
            size="small"
            class="header-back-btn"
            title="Zurück zu den Workspaces"
            @click="router.push(routeBase.value)"
          >
            <v-icon size="18">mdi-arrow-left</v-icon>
            <span v-if="!isMobile" class="header-back-label">Workspaces</span>
          </v-btn>
          <v-icon v-if="!isMobile" size="20" color="primary" class="mr-2">mdi-file-code-outline</v-icon>
          <div class="header-info">
            <div class="header-title">{{ selectedNode?.title || 'Kein Dokument' }}</div>
            <div class="header-subtitle">{{ workspace?.name || `Workspace #${workspaceId}` }}</div>
          </div>
        </div>

        <div class="header-actions">
          <v-btn
            v-if="canShareWorkspace"
            icon
            variant="text"
            size="small"
            title="Workspace teilen"
            @click="openShareDialog"
          >
            <v-icon size="20">mdi-account-multiple-plus</v-icon>
          </v-btn>

          <v-btn
            icon
            variant="text"
            size="small"
            title="Zotero Bibliotheken"
            @click="zoteroDialog = true"
          >
            <v-icon size="20">mdi-book-open-page-variant</v-icon>
          </v-btn>

          <v-btn
            v-if="canSetMainDocument"
            icon
            variant="text"
            size="small"
            title="Als main.tex setzen"
            @click="setMainDocument"
          >
            <v-icon size="20">
              {{ selectedNode?.id === workspace?.main_document_id ? 'mdi-star' : 'mdi-star-outline' }}
            </v-icon>
          </v-btn>

          <v-btn
            icon
            variant="text"
            size="small"
            :color="reviewMode ? 'primary' : undefined"
            title="Review Mode"
            @click="reviewMode = !reviewMode"
          >
            <v-icon size="20">mdi-comment-text-outline</v-icon>
          </v-btn>

          <!-- Divider -->
          <div v-if="selectedNode?.type === 'file' && !selectedNode?.asset_id" class="header-divider" />

          <!-- Connection Status -->
          <template v-if="selectedNode?.type === 'file' && !selectedNode?.asset_id">
            <v-chip v-if="editorRef?.isConnected" size="small" color="success" variant="tonal">
              <v-icon start size="small">mdi-cloud-check-outline</v-icon>
              Live Sync
            </v-chip>
            <v-chip v-else size="small" color="warning" variant="tonal">
              <v-icon start size="small">mdi-cloud-alert-outline</v-icon>
              Reconnecting…
            </v-chip>

            <!-- Ghost Text Toggle (only in AI mode) -->
            <v-tooltip v-if="props.aiEnabled" location="bottom">
              <template #activator="{ props: tooltipProps }">
                <v-chip
                  v-bind="tooltipProps"
                  size="small"
                  :color="props.ghostTextEnabled ? 'primary' : 'default'"
                  :variant="props.ghostTextEnabled ? 'flat' : 'outlined'"
                  class="ghost-text-chip"
                  @click="editorRef?.toggleGhostText?.()"
                >
                  <v-icon start size="small">{{ props.ghostTextEnabled ? 'mdi-lightning-bolt' : 'mdi-lightning-bolt-outline' }}</v-icon>
                  Ghost Text
                </v-chip>
              </template>
              <span>{{ props.ghostTextEnabled ? 'KI-Autovervollständigung aktiv (Tab = Annehmen, Esc = Ablehnen)' : 'KI-Autovervollständigung deaktiviert' }}</span>
            </v-tooltip>

            <!-- Active Users -->
            <div v-if="editorRef?.activeUsers?.length" class="header-users">
              <v-chip
                v-for="u in editorRef.activeUsers"
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
              title="Editor"
              @click="viewMode = 'editor'"
            >
              <v-icon size="18">mdi-pencil</v-icon>
            </button>
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'split' }"
              title="Split"
              @click="viewMode = 'split'"
            >
              <v-icon size="18">mdi-view-split-vertical</v-icon>
            </button>
            <button
              class="mode-btn"
              :class="{ active: viewMode === 'preview' }"
              title="PDF"
              @click="viewMode = 'preview'"
            >
              <v-icon size="18">mdi-file-pdf-box</v-icon>
            </button>
          </div>
        </div>
      </div>

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
          Dir fehlt die Berechtigung <code>feature:latex_collab:view</code>.
        </v-alert>

        <v-alert
          v-else-if="selectedNode && selectedNode.asset_id"
          type="info"
          variant="tonal"
          class="ma-4"
        >
          Dieses Asset ist eine Binärdatei und kann nicht direkt im Editor bearbeitet werden.
        </v-alert>

        <v-alert
          v-else-if="!selectedNode || selectedNode.type !== 'file'"
          type="info"
          variant="tonal"
          class="ma-4"
        >
          Wähle links eine LaTeX-Datei aus, um sie zu bearbeiten.
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
                    <v-icon color="teal">mdi-bookshelf</v-icon>
                  </template>
                  <span class="text-body-2">
                    Diese Datei wird von <strong>Zotero</strong> verwaltet und ist schreibgeschützt.
                    Änderungen werden bei der nächsten Synchronisation überschrieben.
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
                  @request-completion="(req) => emit('request-completion', req)"
                  @update:ghost-text-enabled="(val) => emit('update:ghostTextEnabled', val)"
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
                      title="LaTeX kompilieren"
                      @click="triggerCompile"
                    >
                      Kompilieren
                    </LBtn>
                    <v-select
                      v-model="compileCommitId"
                      :items="compileCommitOptions"
                      label="Version"
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
                      title="Logs anzeigen"
                      @click="compileLogDialog = true"
                    >
                      <v-icon size="16">mdi-text-box-outline</v-icon>
                    </v-btn>
                    <v-menu>
                      <template #activator="{ props: menuProps }">
                        <v-btn icon variant="text" size="x-small" v-bind="menuProps" title="Auto-Compile">
                          <v-icon size="16">mdi-tune-variant</v-icon>
                        </v-btn>
                      </template>
                      <v-card class="compile-settings">
                        <v-card-title class="text-subtitle-2">Auto-Compile</v-card-title>
                        <v-card-text>
                      <v-switch
                        v-model="autoCompileEnabled"
                        label="Automatisch kompilieren"
                        density="compact"
                        hide-details
                      />
                      <v-text-field
                        v-model.number="autoCompileDelay"
                        label="Latenz (ms)"
                        type="number"
                        min="500"
                        step="250"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                      <v-switch
                        v-model="syncEnabled"
                        label="PDF Sync (SyncTeX)"
                        density="compact"
                        hide-details
                        :disabled="!canSync"
                      />
                    </v-card-text>
                  </v-card>
                </v-menu>
              </div>
            </div>

                <LatexPdfViewer
                  ref="pdfViewerRef"
                  :workspace-id="workspaceId"
                  :job-id="pdfJobId"
                  :refresh-key="pdfRefreshKey"
                  :is-compiling="isCompiling"
                  @pdf-click="handlePdfClick"
                />

                <div class="comments-panel">
                  <div class="comments-header">
                    <div class="d-flex align-center ga-2">
                      <v-icon size="18">mdi-comment-multiple-outline</v-icon>
                      <span class="text-body-2">Kommentare</span>
                    </div>
                    <v-spacer />
                    <LBtn
                      variant="text"
                      size="small"
                      prepend-icon="mdi-comment-plus-outline"
                      :disabled="!canComment"
                      title="Kommentar hinzufügen"
                      @click="openCommentDialog"
                    >
                      Kommentar
                    </LBtn>
                  </div>

                  <v-alert v-if="commentError" type="error" variant="tonal" density="compact" class="mb-2">
                    {{ commentError }}
                  </v-alert>

                  <div v-if="comments.length === 0" class="comments-empty">
                    Keine Kommentare vorhanden.
                  </div>

                  <div v-else class="comment-list">
                    <div
                      v-for="c in comments"
                      :key="c.id"
                      class="comment-item"
                      :class="{ active: c.id === activeCommentId }"
                      @click="selectComment(c)"
                    >
                      <div class="comment-meta">
                        <span class="comment-author">{{ c.author_username }}</span>
                        <span class="comment-date">{{ formatDate(c.created_at) }}</span>
                      </div>
                      <div class="comment-body">{{ c.body }}</div>
                      <div class="comment-actions">
                        <LTag v-if="c.resolved_at" variant="success" size="x-small">Resolved</LTag>
                        <v-btn
                          icon
                          variant="text"
                          size="x-small"
                          :title="c.resolved_at ? 'Reopen' : 'Resolve'"
                          @click.stop="toggleCommentResolved(c)"
                        >
                          <v-icon size="16">mdi-check</v-icon>
                        </v-btn>
                        <v-btn
                          icon
                          variant="text"
                          size="x-small"
                          title="Löschen"
                          @click.stop="deleteComment(c)"
                        >
                          <v-icon size="16">mdi-delete-outline</v-icon>
                        </v-btn>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Git Panel - Workspace-Level Multi-File Commits -->
            <LatexWorkspaceGitPanel
              ref="gitPanelRef"
              :workspace-id="workspaceId"
              :can-commit="hasPermission('feature:latex_collab:edit')"
              @committed="refreshCommits"
              @rollback="handleRollback"
            />
          </div>
        </template>
      </div>
    </div>

    <!-- Share / Members Dialog - Subtle Design -->
    <v-dialog v-model="shareDialog" max-width="480">
      <v-card class="share-dialog">
        <v-card-title class="share-header">
          <v-icon class="mr-2" color="primary">mdi-account-multiple-plus</v-icon>
          <div>
            <div>Workspace teilen</div>
            <div class="text-caption text-medium-emphasis">{{ workspace?.name }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" size="small" @click="shareDialog = false" />
        </v-card-title>

        <v-divider />

        <v-card-text class="share-body">
          <v-alert v-if="shareError" type="error" variant="tonal" class="mb-4" density="compact">
            {{ shareError }}
          </v-alert>

          <!-- Owner Section -->
          <div class="section-label">Owner</div>
          <div class="user-card owner-card">
            <img class="user-avatar" :src="getAvatarUrl(ownerInfo)" alt="" />
            <div class="user-info">
              <div class="user-name">{{ formatDisplayName(ownerInfo.username) }}</div>
              <div class="user-meta">@{{ ownerInfo.username }}</div>
            </div>
            <LTag variant="primary" size="small">Owner</LTag>
          </div>

          <!-- Search Section -->
          <div class="section-label mt-4">Nutzer einladen</div>
          <LUserSearch
            ref="userSearchRef"
            v-model="selectedUser"
            :exclude-usernames="excludedUsernames"
            :show-add-button="true"
            add-button-text="Hinzufügen"
            @add="inviteMember"
          />

          <!-- Members Section -->
          <div class="section-label mt-4">
            Mitglieder
            <span v-if="members.length" class="member-count">{{ members.length }}</span>
          </div>

          <v-skeleton-loader v-if="membersLoading" type="list-item-avatar@3" />

          <div v-else-if="members.length === 0" class="empty-members">
            <v-icon size="28" color="grey-lighten-1">mdi-account-group-outline</v-icon>
            <span>Noch keine Mitglieder</span>
          </div>

          <div v-else class="members-list">
            <div v-for="m in members" :key="m.username" class="user-card">
              <img class="user-avatar" :src="getAvatarUrl(m)" alt="" />
              <div class="user-info">
                <div class="user-name">{{ formatDisplayName(m.username) }}</div>
                <div class="user-meta">{{ formatRelativeDate(m.added_at) }}</div>
              </div>
              <v-btn
                v-if="canShareWorkspace"
                icon
                variant="text"
                size="x-small"
                color="error"
                :loading="removingUsername === m.username"
                title="Mitglied entfernen"
                @click="removeMember(m.username)"
              >
                <v-icon size="18">mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="commentDialog" max-width="520">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-comment-plus-outline</v-icon>
          Kommentar hinzufügen
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="commentDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="commentError" type="error" variant="tonal" class="mb-3" density="compact">
            {{ commentError }}
          </v-alert>
          <v-textarea
            v-model="commentDraft"
            label="Kommentar"
            variant="outlined"
            density="comfortable"
            auto-grow
            hide-details
          />
        </v-card-text>
        <v-card-actions class="justify-end">
          <v-btn variant="text" title="Kommentar abbrechen" @click="commentDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" title="Kommentar speichern" :disabled="!canSubmitComment" @click="submitComment">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="compileLogDialog" max-width="760">
      <v-card class="compile-log-dialog">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-text-box-outline</v-icon>
          Compile Log
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="compileLogDialog = false" />
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-alert v-if="compileError" type="error" variant="tonal" class="mb-3" density="compact">
            {{ compileError }}
          </v-alert>
          <div v-if="compileIssues.length" class="compile-issues">
            <div class="text-subtitle-2 mb-2">Fehler &amp; Warnungen</div>
            <div class="issue-list">
              <div
                v-for="issue in compileIssues"
                :key="issue.id"
                class="issue-row"
                :class="{ clickable: !!issue.document_id }"
                @click="jumpToIssue(issue)"
              >
                <v-chip size="x-small" variant="tonal" :color="issue.color">
                  {{ issue.label }}
                </v-chip>
                <span class="issue-message">{{ issue.message }}</span>
                <span class="issue-location">{{ issue.location }}</span>
              </div>
            </div>
          </div>
          <pre class="compile-log">{{ compileLog || 'Noch kein Log vorhanden.' }}</pre>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Zotero Dialog -->
    <v-dialog v-model="zoteroDialog" max-width="600">
      <v-card class="zotero-dialog">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-book-open-page-variant</v-icon>
          <div>
            <div>Zotero Bibliotheken</div>
            <div class="text-caption text-medium-emphasis">{{ workspace?.name }}</div>
          </div>
          <v-spacer />
          <LIconBtn icon="mdi-close" tooltip="Schließen" size="small" @click="zoteroDialog = false" />
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
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'
import { useSplitPaneResize } from '@/composables/useSplitPaneResize'
import { useWorkspaceSocket } from '@/components/MarkdownCollab/composables/useWorkspaceSocket'
import { useActiveDuration, useVisibilityTracker, useScrollDepth } from '@/composables/useAnalyticsMetrics'
import MarkdownTreePanel from '@/components/MarkdownCollab/MarkdownTreePanel.vue'
import LatexEditorPane from '@/components/LatexCollab/LatexEditorPane.vue'
import LatexPdfViewer from '@/components/LatexCollab/LatexPdfViewer.vue'
import LatexWorkspaceGitPanel from '@/components/LatexCollab/LatexWorkspaceGitPanel.vue'
import ZoteroPanel from '@/components/LatexCollab/Zotero/ZoteroPanel.vue'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { getAvatarUrl, formatDisplayName, formatRelativeDate } from '@/utils/userUtils'

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
const emit = defineEmits(['document-change', 'ai-command', 'request-completion', 'update:ghostTextEnabled'])

const route = useRoute()
const router = useRouter()

// Computed route base for navigation
const routeBase = computed(() => props.basePath)

const { hasPermission, fetchPermissions, username: currentUsername, isAdmin } = usePermissions()
const { isLoading, withLoading, setLoading } = useSkeletonLoading(['tree', 'document'])
const { isMobile, isTablet } = useMobile()

// Mobile sidebar state
const mobileSidebarOpen = ref(false)

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:55080'
const VIEWMODE_KEY = 'latex-collab-view-mode'
const TREE_COLLAPSED_KEY = 'latex-collab-tree-collapsed'
const TREE_WIDTH_KEY = 'latex-collab-tree-width'
const PANES_WIDTH_KEY = 'latex-collab-panes-width'
const OUTLINE_COLLAPSED_KEY = 'latex-outline-collapsed'
const AUTO_COMPILE_KEY = 'latex-collab-auto-compile'
const AUTO_COMPILE_DELAY_KEY = 'latex-collab-auto-compile-delay'
const SYNC_KEY = 'latex-collab-sync-enabled'

const workspace = ref(null)
const nodesFlat = ref([])

const currentText = ref('')
const gitSummary = ref({ users: [], totalChangedLines: 0 })
const editorRef = ref(null)
const pdfViewerRef = ref(null)
const gitPanelRef = ref(null)
const pendingDocId = ref(null)
const pendingJump = ref(null)

// Panel states
const treeCollapsed = ref(localStorage.getItem(TREE_COLLAPSED_KEY) === 'true')
const treePanelWidth = ref(parseInt(localStorage.getItem(TREE_WIDTH_KEY)) || 280)
const viewMode = ref(localStorage.getItem(VIEWMODE_KEY) || 'split')
const resizingTree = ref(false)
const outlineCollapsed = ref(localStorage.getItem(OUTLINE_COLLAPSED_KEY) === 'true')
const outlineItems = ref([])
const outlineCollapsedIds = ref(new Set())
const outlineFlatItems = computed(() => {
  const items = []
  const collapsed = outlineCollapsedIds.value
  const walk = (nodes, depth) => {
    for (const node of nodes) {
      const hasChildren = Array.isArray(node.children) && node.children.length > 0
      items.push({ ...node, depth, hasChildren })
      if (hasChildren && !collapsed.has(node.id)) {
        walk(node.children, depth + 1)
      }
    }
  }
  walk(outlineItems.value || [], 0)
  return items
})
const outlineEmptyLabel = computed(() => {
  if (selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id) {
    return 'Keine Kapitel gefunden'
  }
  return 'Kein Dokument'
})
let outlineUpdateTimer = null
let lastOutlineText = ''
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

// Sharing / members
const shareDialog = ref(false)
const members = ref([])
const membersLoading = ref(false)
const shareError = ref('')
const removingUsername = ref('')
const selectedUser = ref(null)
const userSearchRef = ref(null)
const ownerInfo = ref({ username: '', avatar_url: null, avatar_seed: null, collab_color: null })

const reviewMode = ref(false)

const autoCompileEnabled = ref(localStorage.getItem(AUTO_COMPILE_KEY) === 'true')
const autoCompileDelay = ref(parseInt(localStorage.getItem(AUTO_COMPILE_DELAY_KEY)) || 2000)
let autoCompileTimer = null
const syncEnabled = ref(localStorage.getItem(SYNC_KEY) !== 'false')
let syncTimer = null

const compileJobId = ref(null)
const compileStatus = ref('idle')
const compileError = ref('')
const compileLog = ref('')
const compileHasPdf = ref(false)
const compileHasSynctex = ref(false)
const compileLogDialog = ref(false)
const pdfRefreshKey = ref(0)
const pdfRefreshJobId = ref(null)
const compileCommitId = ref(null)
const compileCommitOptions = ref([{ title: 'Aktuell', value: null }])
let compilePollTimer = null

const comments = ref([])
const activeCommentId = ref(null)
const commentDialog = ref(false)
const commentDraft = ref('')
const commentError = ref('')
const pendingCommentRange = ref(null)

// Zotero dialog
const zoteroDialog = ref(false)

const assetInputRef = ref(null)

const compileIssues = ref([])

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

watch(outlineCollapsed, (val) => {
  localStorage.setItem(OUTLINE_COLLAPSED_KEY, val ? 'true' : 'false')
})

watch(autoCompileEnabled, (val) => {
  localStorage.setItem(AUTO_COMPILE_KEY, val ? 'true' : 'false')
})

watch(autoCompileDelay, (val) => {
  const normalized = Number.isFinite(Number(val)) ? Math.max(250, Number(val)) : 2000
  if (normalized !== Number(val)) {
    autoCompileDelay.value = normalized
    return
  }
  localStorage.setItem(AUTO_COMPILE_DELAY_KEY, normalized.toString())
})

watch(syncEnabled, (val) => {
  localStorage.setItem(SYNC_KEY, val ? 'true' : 'false')
  if (!val && syncTimer) {
    clearTimeout(syncTimer)
    syncTimer = null
  }
})

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
  },
  onNodeRenamed: (data) => {
    // Update the node title in the tree
    const node = nodesFlat.value.find(n => n.id === data.nodeId)
    if (node) {
      node.title = data.newTitle
      nodesFlat.value = [...nodesFlat.value]
    }
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

const selectedNodeId = computed(() => routeDocId.value)
const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodesFlat.value.find(n => n.id === selectedNodeId.value) || null
})

const canShareWorkspace = computed(() => {
  if (!workspace.value) return false
  if (!hasPermission('feature:latex_collab:share')) return false
  return isAdmin.value || (currentUsername.value && currentUsername.value === workspace.value.owner_username)
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

const canCompile = computed(() => {
  return !!(selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id && hasPermission('feature:latex_collab:edit'))
})

const canSync = computed(() => (
  compileStatus.value === 'success'
  && !!compileJobId.value
  && compileHasSynctex.value
))
const pdfJobId = computed(() => (
  compileStatus.value === 'success' && compileJobId.value ? compileJobId.value : null
))

const isCompiling = computed(() => ['queued', 'running'].includes(compileStatus.value))

const compileStatusLabel = computed(() => {
  if (compileStatus.value === 'queued') return 'Queued'
  if (compileStatus.value === 'running') return 'Kompiliert'
  if (compileStatus.value === 'success') return 'Fertig'
  if (compileStatus.value === 'failed') return 'Fehler'
  return 'Idle'
})

const compileStatusColor = computed(() => {
  if (compileStatus.value === 'success') return 'success'
  if (compileStatus.value === 'failed') return 'error'
  if (compileStatus.value === 'running') return 'info'
  if (compileStatus.value === 'queued') return 'warning'
  return undefined
})

const canComment = computed(() => {
  return !!(selectedNode.value && selectedNode.value.type === 'file' && !selectedNode.value.asset_id && hasPermission('feature:latex_collab:edit'))
})

const canSubmitComment = computed(() => commentDraft.value.trim().length > 0 && !!pendingCommentRange.value)

// Usernames to exclude from search (owner + existing members)
const excludedUsernames = computed(() => {
  const excluded = []
  if (workspace.value?.owner_username) excluded.push(workspace.value.owner_username)
  members.value.forEach(m => excluded.push(m.username))
  return excluded
})

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

const outlineCommandLevels = {
  part: { level: 0, label: 'Teil' },
  chapter: { level: 1, label: 'Kapitel' },
  section: { level: 2, label: 'Abschnitt' },
  subsection: { level: 3, label: 'Unterabschnitt' },
  subsubsection: { level: 4, label: 'Unter-Unterabschnitt' },
  paragraph: { level: 5, label: 'Paragraph' }
}

const outlinePattern = /\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*(?:\[[^\]]*])?\s*\{([^}]*)\}/g

function toggleOutlineCollapsed() {
  outlineCollapsed.value = !outlineCollapsed.value
}

function isOutlineItemCollapsed(id) {
  return outlineCollapsedIds.value.has(id)
}

function toggleOutlineItem(id) {
  const next = new Set(outlineCollapsedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  outlineCollapsedIds.value = next
}

function buildOutline(text) {
  if (!text) return []
  const items = []
  const stack = []
  const lines = text.split('\n')
  const lineStarts = []
  let offset = 0
  for (const line of lines) {
    lineStarts.push(offset)
    offset += line.length + 1
  }

  outlinePattern.lastIndex = 0
  let match = outlinePattern.exec(text)
  let lineIndex = 0
  while (match) {
    const matchIndex = match.index
    while (lineIndex + 1 < lineStarts.length && lineStarts[lineIndex + 1] <= matchIndex) {
      lineIndex += 1
    }
    const line = lines[lineIndex] || ''
    const trimmed = line.trim()
    if (trimmed && !trimmed.startsWith('%')) {
      const colIndex = matchIndex - lineStarts[lineIndex]
      const leading = line.slice(0, Math.max(0, colIndex))
      if (!leading.includes('%')) {
        const cmd = match[1]
        const meta = outlineCommandLevels[cmd] || { level: 9, label: cmd }
        const title = (match[2] || '').trim() || meta.label
        const item = {
          id: `${cmd}:${lineIndex + 1}:${title}`,
          title,
          line: lineIndex + 1,
          level: meta.level,
          children: []
        }

        while (stack.length && stack[stack.length - 1].level >= item.level) {
          stack.pop()
        }
        if (stack.length) {
          stack[stack.length - 1].children.push(item)
        } else {
          items.push(item)
        }
        stack.push(item)
      }
    }
    match = outlinePattern.exec(text)
  }

  return items
}

function updateOutline(text) {
  if (text === lastOutlineText) return
  lastOutlineText = text
  const nextItems = buildOutline(text)
  outlineItems.value = nextItems

  const validIds = new Set()
  const collect = (nodes) => {
    for (const node of nodes) {
      validIds.add(node.id)
      if (node.children?.length) collect(node.children)
    }
  }
  collect(nextItems)

  if (outlineCollapsedIds.value.size) {
    const next = new Set()
    outlineCollapsedIds.value.forEach((id) => {
      if (validIds.has(id)) next.add(id)
    })
    outlineCollapsedIds.value = next
  }
}

function scheduleOutlineUpdate(text) {
  if (outlineUpdateTimer) clearTimeout(outlineUpdateTimer)
  outlineUpdateTimer = setTimeout(() => {
    updateOutline(text)
  }, 200)
}

function jumpToOutlineItem(item) {
  if (!item?.line) return
  editorRef.value?.jumpToLine?.(item.line, 1)
}

// Initialize pane width on mount
onMounted(async () => {
  await fetchPermissions()
  await loadTree()

  // Connect to workspace socket for real-time tree updates
  wsConnect()

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
  if (autoCompileTimer) clearTimeout(autoCompileTimer)
  if (compilePollTimer) clearTimeout(compilePollTimer)
  if (syncTimer) clearTimeout(syncTimer)
  if (outlineUpdateTimer) clearTimeout(outlineUpdateTimer)
})

function onEditorContentChange(text) {
  currentText.value = text
  if (pendingDocId.value && pendingDocId.value === selectedNodeId.value) {
    setLoading('document', false)
    pendingDocId.value = null
  }
  scheduleOutlineUpdate(text)
  scheduleAutoCompile()
  // Emit for AI wrapper component
  emit('document-change', text)
}

function authHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatDate(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function parseLatexLog(logText) {
  const issues = []
  const lines = String(logText || '').split(/\r?\n/)
  const fileStack = []

  const pushFile = (file) => {
    if (!file) return
    const cleaned = file.replace(/[()]/g, '').trim()
    if (!cleaned) return
    fileStack.push(cleaned)
  }

  const currentFile = () => fileStack[fileStack.length - 1] || null

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i] || ''

    const fileMatches = Array.from(line.matchAll(/\(([^()\s]+?\.(?:tex|bib|sty|cls|ltx|bst))\b/g))
    fileMatches.forEach((match) => pushFile(match[1]))

    const closeCount = (line.match(/\)/g) || []).length
    for (let c = 0; c < closeCount && fileStack.length > 0; c += 1) {
      fileStack.pop()
    }

    if (line.startsWith('! ')) {
      let lineNo = null
      for (let j = i + 1; j < Math.min(i + 6, lines.length); j += 1) {
        const ln = lines[j]
        const match = ln.match(/^l\.(\d+)/) || ln.match(/line\s+(\d+)/i)
        if (match) {
          lineNo = Number(match[1])
          break
        }
      }
      issues.push({
        type: 'error',
        message: line.replace(/^!\s*/, '').trim(),
        file: currentFile(),
        line: lineNo
      })
      continue
    }

    if (/warning/i.test(line)) {
      const match = line.match(/line\s+(\d+)/i)
      issues.push({
        type: 'warning',
        message: line.trim(),
        file: currentFile(),
        line: match ? Number(match[1]) : null
      })
      continue
    }

    if (line.includes('Overfull \\hbox')) {
      const match = line.match(/lines?\s+(\d+)/i)
      issues.push({
        type: 'overfull',
        message: line.trim(),
        file: currentFile(),
        line: match ? Number(match[1]) : null
      })
    }
  }

  return issues
}

function decorateIssues(issues) {
  return issues.map((issue, index) => {
    const filePath = issue.file ? normalizePath(issue.file) : ''
    const fileName = filePath ? filePath.split('/').pop() : ''
    const documentId = filePath ? resolveDocumentIdFromPath(filePath) : null
    const location = fileName
      ? `${fileName}${issue.line ? `:${issue.line}` : ''}`
      : (issue.line ? `Zeile ${issue.line}` : '—')
    const type = issue.type || 'warning'
    const color = type === 'error' ? 'error' : (type === 'overfull' ? 'info' : 'warning')
    const label = type === 'error' ? 'Error' : (type === 'overfull' ? 'Overfull' : 'Warning')
    return {
      ...issue,
      id: `${type}-${index}-${issue.line || 0}`,
      document_id: documentId,
      location,
      color,
      label
    }
  })
}

async function loadMembers() {
  if (!workspaceId.value) return
  membersLoading.value = true
  shareError.value = ''
  try {
    const res = await axios.get(`${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members`, {
      headers: authHeaders()
    })
    members.value = res.data.members || []
    // Store owner info
    ownerInfo.value = {
      username: res.data.owner?.username || '',
      avatar_url: res.data.owner?.avatar_url || null,
      avatar_seed: res.data.owner?.avatar_seed || null,
      collab_color: res.data.owner?.collab_color || null
    }
  } catch (e) {
    members.value = []
    shareError.value = e?.response?.data?.error || e?.message || 'Mitglieder konnten nicht geladen werden'
  } finally {
    membersLoading.value = false
  }
}

// Helper functions for user display imported from @/utils/userUtils

function openShareDialog() {
  shareDialog.value = true
  selectedUser.value = null
  loadMembers()
}

async function inviteMember(user) {
  const username = user?.username || selectedUser.value?.username
  if (!username) return
  shareError.value = ''
  try {
    await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members`,
      { username: username.trim() },
      { headers: authHeaders() }
    )
    selectedUser.value = null
    userSearchRef.value?.reset?.()
    await loadMembers()
  } catch (e) {
    shareError.value = e?.response?.data?.error || e?.message || 'Einladung fehlgeschlagen'
    userSearchRef.value?.setAdding?.(false)
  }
}

async function removeMember(username) {
  if (!username) return
  removingUsername.value = username
  shareError.value = ''
  try {
    await axios.delete(`${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/members/${encodeURIComponent(username)}`, {
      headers: authHeaders()
    })
    await loadMembers()
  } catch (e) {
    shareError.value = e?.response?.data?.error || e?.message || 'Entfernen fehlgeschlagen'
  } finally {
    removingUsername.value = ''
  }
}

// Zotero library event handlers
async function handleZoteroLibraryAdded(library) {
  // Refresh the file tree to show the new .bib file
  await loadDocuments()
}

async function handleZoteroLibrarySynced(library) {
  // Refresh the file tree to reflect updated .bib content
  await loadDocuments()
}

async function handleZoteroLibraryRemoved(library) {
  // The .bib file is kept but no longer synced - no tree refresh needed
  console.log('Zotero library removed:', library.library_name)
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

async function loadTree() {
  await withLoading('tree', async () => {
    const res = await axios.get(`${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/tree`, {
      headers: authHeaders()
    })
    workspace.value = res.data.workspace
    nodesFlat.value = (res.data.nodes || []).map(n => ({ ...n, type: n.type }))
  })
}

function handleSelectNode(nodeId) {
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
    console.error('Asset upload failed:', e)
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
    console.error('Failed to create node:', e)
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
    console.error('Failed to rename node:', e)
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

    // Navigate away if viewing deleted document
    if (routeDocId.value === id) {
      router.push(`${routeBase.value}/workspace/${workspaceId.value}`)
    }
  } catch (e) {
    console.error('Failed to delete node:', e)
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
    console.error('Failed to move node:', e)
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
    console.error('Failed to set main document:', e)
  }
}

async function loadCommitOptions() {
  if (!selectedNode.value || selectedNode.value.asset_id) {
    compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
    compileCommitId.value = null
    return
  }
  try {
    const res = await axios.get(
      `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/commits`,
      { headers: authHeaders() }
    )
    const items = (res.data?.commits || []).map((c) => ({
      title: `#${c.id} · ${c.message}`,
      value: c.id
    }))
    const options = [{ title: 'Aktuell', value: null }, ...items]
    compileCommitOptions.value = options
    const optionValues = new Set(options.map((opt) => opt.value))
    if (!optionValues.has(compileCommitId.value)) {
      compileCommitId.value = null
    }
  } catch (e) {
    compileCommitOptions.value = [{ title: 'Aktuell', value: null }]
    compileCommitId.value = null
  }
}

async function loadCompileStatus(jobId) {
  if (!jobId) {
    compileStatus.value = 'idle'
    compileJobId.value = null
    compileError.value = ''
    compileLog.value = ''
    compileHasPdf.value = false
    compileHasSynctex.value = false
    return
  }
  try {
    const res = await axios.get(`${API_BASE}/api/latex-collab/compile/${jobId}`, {
      headers: authHeaders()
    })
    const job = res.data?.job
    if (job) {
      compileJobId.value = job.id
      compileStatus.value = job.status || 'idle'
      compileError.value = job.error_message || ''
      compileLog.value = job.log_text || ''
      compileHasPdf.value = !!job.has_pdf
      compileHasSynctex.value = !!job.has_synctex
      if (['queued', 'running'].includes(job.status)) {
        pollCompileJob(job.id)
      }
    }
  } catch (e) {
    console.error('Failed to load compile status:', e)
  }
}

watch([compileLog, nodesFlat], () => {
  compileIssues.value = decorateIssues(parseLatexLog(compileLog.value))
}, { immediate: true })

function scheduleAutoCompile() {
  if (!autoCompileEnabled.value || !canCompile.value || reviewMode.value || isCompiling.value) return
  if (autoCompileTimer) clearTimeout(autoCompileTimer)
  autoCompileTimer = setTimeout(() => {
    triggerCompile()
  }, autoCompileDelay.value)
}

async function triggerCompile() {
  if (!canCompile.value) return
  compileError.value = ''
  compileLog.value = ''
  compileHasPdf.value = false
  compileHasSynctex.value = false
  pdfRefreshJobId.value = null
  if (autoCompileTimer) clearTimeout(autoCompileTimer)
  try {
    if (!compileCommitId.value) {
      await editorRef.value?.flushDocumentState?.()
    }
    const payload = {}
    if (compileCommitId.value) payload.commit_id = compileCommitId.value
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/workspaces/${workspaceId.value}/compile`,
      payload,
      { headers: authHeaders() }
    )
    const job = res.data?.job
    if (job) {
      compileJobId.value = job.id
      compileStatus.value = job.status || 'queued'
      compileHasPdf.value = !!job.has_pdf
      compileHasSynctex.value = !!job.has_synctex
      pollCompileJob(job.id)
    }
  } catch (e) {
    compileStatus.value = 'failed'
    compileError.value = e?.response?.data?.error || e?.message || 'Kompilierung fehlgeschlagen'
    compileHasPdf.value = false
    compileHasSynctex.value = false
  }
}

async function pollCompileJob(jobId) {
  if (!jobId) return
  if (compilePollTimer) clearTimeout(compilePollTimer)
  let pdfWaitAttempts = 0
  const maxPdfWaitAttempts = 12
  let rateLimitedCount = 0

  const poll = async () => {
    let nextDelay = 1500
    try {
      const res = await axios.get(`${API_BASE}/api/latex-collab/compile/${jobId}`, {
        headers: authHeaders()
      })
      const job = res.data?.job
      if (job) {
        compileJobId.value = job.id
        compileStatus.value = job.status || compileStatus.value
        compileError.value = job.error_message || ''
        compileLog.value = job.log_text || ''
        compileHasPdf.value = !!job.has_pdf
        compileHasSynctex.value = !!job.has_synctex
        rateLimitedCount = 0
        if (job.status === 'success') {
          compileError.value = ''
          if (pdfRefreshJobId.value !== job.id) {
            pdfRefreshJobId.value = job.id
            pdfRefreshKey.value += 1
          }
          if (job.has_pdf && job.has_synctex) {
            compilePollTimer = null
            return
          }
          pdfWaitAttempts += 1
          nextDelay = 800
          if (pdfWaitAttempts > maxPdfWaitAttempts) {
            compilePollTimer = null
            return
          }
        }
        if (job.status === 'failed') {
          compilePollTimer = null
          return
        }
      }
    } catch (e) {
      const status = e?.response?.status
      if (status === 429) {
        rateLimitedCount += 1
        nextDelay = Math.min(12000, 1200 * Math.pow(1.7, rateLimitedCount))
      } else {
        console.error('Compile polling failed:', e)
      }
    }
    compilePollTimer = setTimeout(poll, nextDelay)
  }

  compilePollTimer = setTimeout(poll, 800)
}

function handleEditorSyncRequest(payload) {
  if (!syncEnabled.value || !canSync.value) return
  if (!payload || !payload.line) return
  if (!selectedNode.value || selectedNode.value.asset_id) return
  scheduleSyncToPdf(payload.line, payload.column)
}

function scheduleSyncToPdf(line, column = 1) {
  if (!syncEnabled.value || !canSync.value) return
  if (syncTimer) clearTimeout(syncTimer)
  syncTimer = setTimeout(() => {
    syncSourceToPdf(line, column)
  }, 350)
}

async function syncSourceToPdf(line, column = 1) {
  if (!compileJobId.value || !selectedNode.value) return
  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/compile/${compileJobId.value}/synctex/forward`,
      {
        document_id: selectedNode.value.id,
        line,
        column
      },
      { headers: authHeaders() }
    )
    if (res.data?.success === false) return
    const location = res.data?.location
    if (location) {
      pdfViewerRef.value?.scrollToLocation?.(location)
    }
  } catch (e) {
    // Ignore sync errors to avoid blocking editor usage
  }
}

async function handlePdfClick(payload) {
  if (!syncEnabled.value || !canSync.value) return
  if (!payload || !payload.page) return
  if (!compileJobId.value) return

  try {
    const res = await axios.post(
      `${API_BASE}/api/latex-collab/compile/${compileJobId.value}/synctex/inverse`,
      {
        page: payload.page,
        x: payload.x,
        y: payload.y
      },
      { headers: authHeaders() }
    )
    if (res.data?.success === false) return
    const location = res.data?.location
    if (!location) return
    if (!location.document_id) return
    jumpToDocument(location.document_id, location.line || 1, location.column || 1)
  } catch (e) {
    // Ignore sync errors to avoid interrupting normal PDF usage
  }
}

async function loadComments() {
  if (!selectedNode.value || selectedNode.value.asset_id) {
    comments.value = []
    activeCommentId.value = null
    return
  }
  try {
    const res = await axios.get(
      `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/comments`,
      { headers: authHeaders() }
    )
    comments.value = res.data?.comments || []
  } catch (e) {
    console.error('Failed to load comments:', e)
    comments.value = []
  }
}

function openCommentDialog() {
  commentError.value = ''
  const range = editorRef.value?.getSelectionRange?.()
  if (!range || range.from === range.to) {
    commentError.value = 'Bitte markiere zuerst den Text für den Kommentar.'
    return
  }
  pendingCommentRange.value = range
  commentDraft.value = ''
  commentDialog.value = true
}

async function submitComment() {
  if (!pendingCommentRange.value || !selectedNode.value) return
  commentError.value = ''
  try {
    await axios.post(
      `${API_BASE}/api/latex-collab/documents/${selectedNode.value.id}/comments`,
      {
        range_start: pendingCommentRange.value.from,
        range_end: pendingCommentRange.value.to,
        body: commentDraft.value.trim()
      },
      { headers: authHeaders() }
    )
    commentDialog.value = false
    commentDraft.value = ''
    pendingCommentRange.value = null
    await loadComments()
  } catch (e) {
    commentError.value = e?.response?.data?.error || e?.message || 'Kommentar konnte nicht gespeichert werden'
  }
}

async function toggleCommentResolved(comment) {
  if (!comment) return
  try {
    await axios.patch(
      `${API_BASE}/api/latex-collab/comments/${comment.id}`,
      { resolved: !comment.resolved_at },
      { headers: authHeaders() }
    )
    await loadComments()
  } catch (e) {
    console.error('Failed to update comment:', e)
  }
}

async function deleteComment(comment) {
  if (!comment) return
  try {
    await axios.delete(`${API_BASE}/api/latex-collab/comments/${comment.id}`, {
      headers: authHeaders()
    })
    await loadComments()
  } catch (e) {
    console.error('Failed to delete comment:', e)
  }
}

function selectComment(comment) {
  activeCommentId.value = comment?.id || null
}

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

async function refreshCommits() {
  // Refresh the git baseline after commit to update diff decorations
  await editorRef.value?.refreshBaseline?.()
  editorRef.value?.clearHighlights?.()
  await loadCommitOptions()
  // Also refresh the workspace git panel
  gitPanelRef.value?.checkForChanges?.()
}

async function handleRollback(documentId) {
  // If the rolled back document is currently open, reload it
  if (selectedNodeId.value === documentId) {
    // Reload the document content from the server
    await loadDocumentContent(documentId)
    // Refresh the baseline to update diff decorations
    await editorRef.value?.refreshBaseline?.()
    editorRef.value?.clearHighlights?.()
  }
}

watch(
  selectedNodeId,
  (docId) => {
    currentText.value = ''
    gitSummary.value = { users: [], totalChangedLines: 0, hasChanges: false, insertions: 0, deletions: 0 }
    outlineItems.value = []
    outlineCollapsedIds.value = new Set()
    lastOutlineText = ''
    if (docId) {
      pendingDocId.value = docId
      setLoading('document', true)
      const node = nodesFlat.value.find(n => n.id === docId)
      if (node?.asset_id) {
        pendingDocId.value = null
        setLoading('document', false)
      }
      activeCommentId.value = null
      commentError.value = ''
      commentDraft.value = ''
      loadComments()
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
      loadComments()
      loadCommitOptions()
    }
  }
)
</script>

<style scoped>
/* LLARS Design Variables */
.workspace-root {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  height: calc(100vh - 94px);
  display: flex;
  background-color: rgb(var(--v-theme-background));
  overflow: hidden;
}

/* ============================================
   TREE PANEL
   ============================================ */
.tree-panel {
  flex-shrink: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-width: 0;
  overflow: hidden;
}

.tree-panel.collapsed {
  width: 48px !important;
}

.tree-expanded {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.tree-stack {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.tree-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.tree-outline-panel {
  flex-shrink: 0;
  margin: 0 8px 8px;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  background: rgba(var(--v-theme-surface-variant), 0.18);
  overflow: hidden;
  max-height: 240px;
}

.tree-outline-panel.collapsed {
  height: 32px;
  max-height: 32px;
}

.tree-outline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.tree-outline-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.tree-outline-panel.collapsed .tree-outline-list {
  display: none;
}

.tree-outline-list {
  overflow: auto;
  padding: 6px 4px 8px;
  max-height: 200px;
}

.tree-outline-empty {
  padding: 6px 8px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.tree-outline-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 6px;
  color: rgba(var(--v-theme-on-surface), 0.78);
}

.tree-outline-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.tree-outline-toggle,
.tree-outline-link {
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
  cursor: pointer;
  color: inherit;
  display: flex;
  align-items: center;
}

.tree-outline-link {
  font-size: 12px;
  line-height: 1.3;
  text-align: left;
}

.tree-outline-spacer {
  width: 16px;
  height: 16px;
  display: inline-block;
}

/* Collapsed Tree */
.tree-collapsed {
  height: 100%;
  cursor: pointer;
}

.collapsed-bar {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  gap: 12px;
  background: linear-gradient(180deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
}

.collapsed-icon-box {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.collapsed-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  font-size: 13px;
  color: white;
  letter-spacing: 1px;
}

.expand-icon {
  color: white;
  opacity: 0.8;
  margin-top: auto;
}

/* ============================================
   RESIZE DIVIDER
   ============================================ */
.resize-divider {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.resize-divider.vertical {
  width: 6px;
  cursor: col-resize;
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.resize-divider.vertical:hover,
.resize-divider.vertical.resizing {
  background: rgba(var(--v-theme-primary), 0.15);
}

.resize-handle {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
  transition: background 0.15s, height 0.15s;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
  height: 60px;
}

/* ============================================
   CONTENT AREA
   ============================================ */
.content-area {
  flex: 1;
  min-width: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ============================================
   CONTENT HEADER - Subtle Design
   ============================================ */
.content-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.header-info {
  min-width: 0;
  flex: 1;
}

.header-back-btn {
  margin-right: 6px;
}

.header-back-label {
  margin-left: 4px;
  font-size: 12px;
  text-transform: none;
}

.header-title {
  font-weight: 500;
  font-size: 14px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgb(var(--v-theme-on-surface));
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
  height: 20px;
  background: rgba(var(--v-theme-on-surface), 0.15);
  margin: 0 4px;
}

.header-users {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
  max-width: 200px;
  overflow: hidden;
}

.user-chip {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.user-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.ghost-text-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

.ghost-text-chip:hover {
  transform: scale(1.02);
}

.mode-toggle-group {
  display: flex;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px;
  padding: 2px;
}

.mode-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: rgba(var(--v-theme-on-surface), 0.8);
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.mode-btn.active {
  background: var(--llars-primary);
  color: white;
}

.content-body {
  flex: 1;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.document-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  display: flex;
  justify-content: center;
  padding: 16px;
  background: rgba(var(--v-theme-background), 0.55);
}

.document-loading-skeleton {
  width: 100%;
  max-width: 980px;
}

/* ============================================
   EDITOR LAYOUT
   ============================================ */
.editor-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px;
  gap: 8px;
  overflow: hidden;
}

.panes-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.pane {
  min-height: 0;
  overflow: hidden;
}

.preview-pane {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-pane :deep(.pdf-viewer) {
  flex: 1;
  min-height: 0;
}

.preview-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.compile-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.compile-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.compile-select {
  min-width: 180px;
  max-width: 260px;
}

.compile-settings {
  min-width: 260px;
}

.comments-panel {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px;
  background: rgba(var(--v-theme-surface), 0.7);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 160px;
  max-height: 260px;
  overflow: hidden;
}

.comments-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comments-empty {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  padding: 8px;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
}

.comment-item {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.comment-item.active {
  border-color: rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.08);
}

.comment-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
}

.comment-author {
  font-weight: 600;
}

.comment-body {
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.comment-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}

.asset-input {
  display: none;
}

/* Split mode */
.panes-container.mode-split .editor-pane {
  flex-shrink: 0;
}

.panes-container.mode-split .preview-pane {
  flex: 1;
  min-width: 0;
}

/* Editor only mode */
.panes-container.mode-editor {
  flex-direction: column;
}

.panes-container.mode-editor .editor-pane {
  flex: 1;
  width: 100% !important;
}

.panes-container.mode-editor .preview-pane {
  display: none;
}

/* Preview only mode */
.panes-container.mode-preview {
  flex-direction: column;
}

.panes-container.mode-preview .editor-pane {
  display: none;
}

.panes-container.mode-preview .preview-pane {
  flex: 1;
}

/* Zotero read-only notice */
.zotero-readonly-notice {
  margin: 8px 8px 0 8px;
  flex-shrink: 0;
  border-left: 3px solid #009688 !important;
}

.zotero-readonly-notice :deep(.v-alert__content) {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ============================================
   SHARE DIALOG - Subtle Design
   ============================================ */
.share-dialog {
  border-radius: 12px !important;
}

.share-header {
  display: flex;
  align-items: center;
}

.share-body {
  max-height: 50vh;
  overflow-y: auto;
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
  gap: 6px;
}

.member-count {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 8px;
  font-weight: 500;
}

.compile-log-dialog {
  border-radius: 12px !important;
}

.zotero-dialog {
  border-radius: 12px !important;
}

.zotero-dialog :deep(.v-card-text) {
  max-height: 70vh;
  overflow-y: auto;
}

.compile-issues {
  margin-bottom: 12px;
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.issue-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 8px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-on-surface), 0.02);
  font-size: 12px;
}

.issue-row.clickable {
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
}

.issue-row.clickable:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.issue-message {
  color: rgb(var(--v-theme-on-surface));
}

.issue-location {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.compile-log {
  max-height: 50vh;
  overflow: auto;
  padding: 12px;
  font-size: 11px;
  line-height: 1.4;
  background: rgba(var(--v-theme-surface-variant), 0.25);
  color: rgb(var(--v-theme-on-surface));
  border-radius: 8px;
  white-space: pre-wrap;
}

/* User Avatar */
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  flex-shrink: 0;
  object-fit: cover;
}

.user-avatar.small {
  width: 28px;
  height: 28px;
  border-radius: 6px;
}

.user-avatar.x-small {
  width: 22px;
  height: 22px;
  border-radius: 5px;
}

/* User Card */
.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.user-card.owner-card {
  background: rgba(var(--v-theme-primary), 0.04);
  border-color: rgba(var(--v-theme-primary), 0.12);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  font-size: 13px;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.2;
}

.user-meta {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Members Section */
.empty-members {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 12px;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* ============================================
   MOBILE RESPONSIVE STYLES
   ============================================ */
.workspace-root.is-mobile {
  /* 64px AppBar + 24px Footer = 88px */
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
  overflow: hidden;
  max-width: 100vw;
}

.mobile-tree-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-tree-drawer :deep(.tree-panel) {
  height: 100%;
}

.mobile-tree-content {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.mobile-tree-content .tree-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.mobile-tree-content .tree-outline-panel {
  margin: 0 12px 12px;
}

/* Mobile content area takes full width */
.workspace-root.is-mobile .content-area {
  width: 100%;
}

/* Mobile header adjustments */
.workspace-root.is-mobile .content-header {
  padding: 6px 8px;
}

.workspace-root.is-mobile .header-title {
  font-size: 13px;
}

.workspace-root.is-mobile .header-subtitle {
  font-size: 10px;
}

.workspace-root.is-mobile .mode-toggle-group {
  padding: 1px;
}

.workspace-root.is-mobile .mode-btn {
  width: 28px;
  height: 28px;
}

/* Mobile editor layout */
.workspace-root.is-mobile .editor-layout {
  padding: 4px;
  gap: 4px;
}

/* Mobile: On split mode, stack vertically instead of horizontal */
.workspace-root.is-mobile .panes-container.mode-split {
  flex-direction: column;
}

.workspace-root.is-mobile .panes-container.mode-split .editor-pane {
  width: 100% !important;
  flex: 1;
}

.workspace-root.is-mobile .panes-container.mode-split .preview-pane {
  flex: 1;
}

.workspace-root.is-mobile .panes-container.mode-split .resize-divider {
  display: none;
}

/* Hide Git panel on mobile in compact mode */
.workspace-root.is-mobile .git-panel {
  max-height: 120px;
}

/* Tablet adjustments */
.workspace-root.is-tablet .tree-panel {
  max-width: 240px;
}

/* Default 50/50 split - ensure panes container uses flexbox properly */
.panes-container.mode-split .editor-pane,
.panes-container.mode-split .preview-pane {
  flex: 1 1 50%;
  min-width: 0;
}
</style>
