<!-- SourcePanel.vue - Source details side panel -->
<template>
  <div class="sources-panel" :style="panelStyle">
    <div class="sources-panel-card">
      <!-- Panel Header -->
      <div class="sources-panel-header">
        <div class="header-title-area">
          <div class="source-icon">
            <v-icon size="20">mdi-bookmark-multiple</v-icon>
          </div>
          <div class="source-title-info">
            <span class="source-title">
              {{ source?.title || source?.filename || 'Quelle' }}
            </span>
            <span v-if="source?.collection_name" class="source-collection">
              {{ source.collection_name }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <LTooltip :text="pinned ? 'Lösen' : 'Anheften'">
            <button
              class="panel-action"
              :class="{ active: pinned }"
              @click="$emit('update:pinned', !pinned)"
            >
              <v-icon size="18">{{ pinned ? 'mdi-pin' : 'mdi-pin-outline' }}</v-icon>
            </button>
          </LTooltip>
          <LTooltip text="Schließen">
            <button class="panel-action close" @click="$emit('close')">
              <v-icon size="18">mdi-close</v-icon>
            </button>
          </LTooltip>
        </div>
      </div>

      <!-- Custom Tabs -->
      <div class="source-tabs">
        <button
          class="source-tab"
          :class="{ active: activeTab === 'excerpt' }"
          @click="$emit('update:activeTab', 'excerpt')"
        >
          <v-icon size="16">mdi-text-box</v-icon>
          <span>Ausschnitt</span>
        </button>
        <button
          class="source-tab"
          :class="{ active: activeTab === 'screenshot', disabled: !hasScreenshot }"
          :disabled="!hasScreenshot"
          @click="$emit('update:activeTab', 'screenshot')"
        >
          <v-icon size="16">mdi-image</v-icon>
          <span>Screenshot</span>
        </button>
        <button
          class="source-tab"
          :class="{ active: activeTab === 'document', disabled: !hasDocument }"
          :disabled="!hasDocument"
          @click="$emit('update:activeTab', 'document')"
        >
          <v-icon size="16">mdi-file-document</v-icon>
          <span>Dokument</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="sources-panel-body">
        <!-- Excerpt Tab -->
        <div v-if="activeTab === 'excerpt'" class="tab-content">
          <div v-if="!source" class="empty-source">
            <v-icon size="48" class="mb-2">mdi-bookmark-outline</v-icon>
            <div>Quelle auswählen</div>
          </div>
          <template v-else>
            <!-- Metadata Tags -->
            <div class="source-metadata">
              <LTag v-if="source.collection_name" variant="primary" size="sm" prepend-icon="mdi-folder">
                {{ source.collection_name }}
              </LTag>
              <LTag v-if="source.page_number" variant="gray" size="sm" prepend-icon="mdi-book-open-page-variant">
                Seite {{ source.page_number }}
              </LTag>
              <LTag v-if="source.chunk_index !== null && source.chunk_index !== undefined" variant="gray" size="sm" prepend-icon="mdi-text">
                Chunk {{ source.chunk_index }}
              </LTag>
              <LTag v-if="source.relevance !== null && source.relevance !== undefined" variant="success" size="sm" prepend-icon="mdi-check-circle">
                {{ ((source.relevance || 0) * 100).toFixed(0) }}% relevant
              </LTag>
            </div>

            <!-- Excerpt Text -->
            <div class="excerpt-box">
              <div class="excerpt-label">
                <v-icon size="14">mdi-format-quote-open</v-icon>
                Textausschnitt
              </div>
              <div class="excerpt-text">
                {{ source.excerpt }}
              </div>
            </div>

            <!-- Actions -->
            <div class="source-actions">
              <LBtn
                v-if="source.download_url"
                :href="source.download_url"
                target="_blank"
                rel="noopener"
                variant="primary"
                size="small"
                prepend-icon="mdi-download"
              >
                Download
              </LBtn>
              <LBtn
                variant="text"
                size="small"
                prepend-icon="mdi-file-search"
                :disabled="!hasDocument"
                @click="$emit('update:activeTab', 'document')"
              >
                Volltext anzeigen
              </LBtn>
            </div>
          </template>
        </div>

        <!-- Screenshot Tab -->
        <div v-else-if="activeTab === 'screenshot'" class="tab-content">
          <v-skeleton-loader v-if="loadingScreenshot" type="image" height="320" class="skeleton-llars" />
          <div v-else-if="screenshotError" class="error-box">
            <v-icon size="24" color="error">mdi-alert-circle</v-icon>
            <span>{{ screenshotError }}</span>
          </div>
          <div v-else class="screenshot-container">
            <div v-if="!screenshotUrl" class="empty-source">
              <v-icon size="48" class="mb-2">mdi-image-off</v-icon>
              <div>Kein Screenshot verfügbar</div>
            </div>
            <template v-else>
              <div class="screenshot-actions">
                <LBtn
                  size="small"
                  variant="secondary"
                  prepend-icon="mdi-fullscreen"
                  @click="$emit('fullscreen', 'screenshot')"
                >
                  Vergrößern
                </LBtn>
              </div>
              <div class="screenshot-frame" @click="$emit('fullscreen', 'screenshot')">
                <v-img :src="screenshotUrl" contain max-height="420">
                  <template #placeholder>
                    <div class="d-flex align-center justify-center fill-height">
                      <v-progress-circular indeterminate color="primary" size="24" />
                    </div>
                  </template>
                </v-img>
              </div>
            </template>
          </div>
        </div>

        <!-- Document Tab -->
        <div v-else-if="activeTab === 'document'" class="tab-content">
          <v-skeleton-loader v-if="loadingContent" type="article" class="skeleton-llars" />
          <div v-else-if="contentError" class="error-box">
            <v-icon size="24" color="error">mdi-alert-circle</v-icon>
            <span>{{ contentError }}</span>
          </div>
          <div v-else class="document-container">
            <div v-if="!documentContent" class="empty-source">
              <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
              <div>Kein Inhalt verfügbar</div>
            </div>
            <template v-else>
              <div class="document-actions">
                <LBtn
                  size="small"
                  variant="secondary"
                  prepend-icon="mdi-fullscreen"
                  @click="$emit('fullscreen', 'document')"
                >
                  Vergrößern
                </LBtn>
              </div>
              <div class="document-text">
                {{ documentContent }}
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  source: {
    type: Object,
    default: null
  },
  activeTab: {
    type: String,
    default: 'excerpt'
  },
  pinned: {
    type: Boolean,
    default: false
  },
  panelStyle: {
    type: Object,
    default: () => ({})
  },
  // Content state
  documentContent: {
    type: String,
    default: ''
  },
  screenshotUrl: {
    type: String,
    default: null
  },
  // Loading states
  loadingScreenshot: {
    type: Boolean,
    default: false
  },
  loadingContent: {
    type: Boolean,
    default: false
  },
  // Error states
  screenshotError: {
    type: String,
    default: null
  },
  contentError: {
    type: String,
    default: null
  }
})

defineEmits([
  'close',
  'update:pinned',
  'update:activeTab',
  'fullscreen'
])

const hasScreenshot = computed(() => {
  return !!(props.source?.screenshot_url || props.source?.document_id)
})

const hasDocument = computed(() => {
  return !!props.source?.content_url
})
</script>

<style scoped>
.sources-panel {
  height: 100%;
  background: rgb(var(--v-theme-surface));
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sources-panel-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Panel Header */
.sources-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.header-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.source-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px 3px 10px 3px;
  background: var(--llars-primary, #b0ca97);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.source-title-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.source-title {
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-collection {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.header-actions {
  display: flex;
  gap: 4px;
}

.panel-action {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.panel-action:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgb(var(--v-theme-on-surface));
}

.panel-action.active {
  color: var(--llars-primary, #b0ca97);
}

.panel-action.close:hover {
  background: rgba(232, 160, 135, 0.15);
  color: #e8a087;
}

/* Tabs */
.source-tabs {
  display: flex;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 0 8px;
}

.source-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 8px;
  border: none;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.source-tab:hover:not(.disabled) {
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.source-tab.active {
  color: var(--llars-primary, #b0ca97);
  border-bottom-color: var(--llars-primary, #b0ca97);
  font-weight: 500;
}

.source-tab.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Panel Body */
.sources-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.tab-content {
  height: 100%;
}

.empty-source {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-align: center;
}

/* Metadata */
.source-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
}

/* Excerpt Box */
.excerpt-box {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  margin-bottom: 16px;
}

.excerpt-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
}

.excerpt-text {
  font-size: 14px;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
  white-space: pre-wrap;
}

/* Source Actions */
.source-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Screenshot */
.screenshot-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screenshot-actions {
  display: flex;
  justify-content: flex-end;
}

.screenshot-frame {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.screenshot-frame:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

/* Document */
.document-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-actions {
  display: flex;
  justify-content: flex-end;
}

.document-text {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

/* Error Box */
.error-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(232, 160, 135, 0.1);
  border-radius: 8px;
  color: #e8a087;
}
</style>
