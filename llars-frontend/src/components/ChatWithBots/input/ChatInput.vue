<!-- ChatInput.vue - Chat message input with file upload -->
<template>
  <div class="chat-input">
    <!-- File Preview -->
    <div v-if="selectedFiles.length > 0" class="file-preview mb-2">
      <v-chip
        v-for="(file, idx) in selectedFiles"
        :key="idx"
        closable
        size="small"
        class="mr-1"
        @click:close="removeFile(idx)"
      >
        <LIcon start size="14">{{ getFileIcon(file.type) }}</LIcon>
        {{ file.name }}
        <span class="text-caption ml-1">({{ formatFileSize(file.size) }})</span>
      </v-chip>
    </div>

    <div class="d-flex align-center gap-2">
      <!-- File Upload Button -->
      <v-btn
        icon
        variant="text"
        :disabled="disabled"
        @click="triggerFileInput"
        :title="fileUploadTooltip"
      >
        <LIcon>mdi-paperclip</LIcon>
      </v-btn>
      <input
        ref="fileInput"
        type="file"
        multiple
        :accept="acceptedFileTypes"
        style="display: none"
        @change="handleFileSelect"
      />

      <!-- Message Input -->
      <v-textarea
        v-model="message"
        @keydown="handleKeyDown"
        :placeholder="$t('chat.messagePlaceholder')"
        variant="outlined"
        :loading="loading"
        :disabled="disabled"
        hide-details
        density="comfortable"
        rows="1"
        auto-grow
        max-rows="6"
        class="flex-grow-1 chat-textarea"
      />

      <!-- Send Button -->
      <v-btn
        icon
        color="primary"
        :disabled="(!message.trim() && selectedFiles.length === 0) || disabled"
        :loading="loading"
        @click="handleSend"
      >
        <LIcon>mdi-send</LIcon>
      </v-btn>
    </div>

    <!-- Supported file types info -->
    <div class="text-caption text-medium-emphasis mt-1 supported-types-hint">
      <template v-if="supportsVision">
        {{ $t('chat.supportedTypesWithImages') }}
      </template>
      <template v-else>
        {{ $t('chat.supportedTypesNoImages') }}
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  supportsVision: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'send'])

const message = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const selectedFiles = ref([])
const fileInput = ref(null)

const acceptedFileTypes = computed(() => {
  const types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
  if (props.supportsVision) {
    types.push('.png', '.jpg', '.jpeg', '.gif', '.webp')
  }
  return types.join(',')
})

const fileUploadTooltip = computed(() => {
  if (props.supportsVision) {
    return t('chat.uploadFilesWithImages')
  }
  return t('chat.uploadFilesTooltip')
})

/**
 * Trigger file input dialog
 */
function triggerFileInput() {
  fileInput.value?.click()
}

/**
 * Handle file selection from input
 */
function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      // Emit error for parent to handle
      emit('file-error', { file, error: 'File too large (max 10MB)' })
      continue
    }
    selectedFiles.value.push(file)
  }
  event.target.value = ''
}

/**
 * Remove file from selection
 */
function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

/**
 * Get icon for file type
 */
function getFileIcon(type) {
  const ext = type.split('.').pop()?.toLowerCase() || type
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes(ext)) return 'mdi-image'
  if (ext === 'pdf' || type === 'pdf') return 'mdi-file-pdf-box'
  if (['doc', 'docx'].includes(ext) || type === 'word') return 'mdi-file-word'
  if (['xls', 'xlsx'].includes(ext) || type === 'excel') return 'mdi-file-excel'
  if (['ppt', 'pptx'].includes(ext) || type === 'powerpoint') return 'mdi-file-powerpoint'
  return 'mdi-file'
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

/**
 * Handle keyboard events for textarea
 * - Enter (without modifiers): Send message
 * - Shift+Enter or Ctrl+J: Insert line break
 */
function handleKeyDown(event) {
  // Shift+Enter or Ctrl+J: Allow line break (default behavior)
  if ((event.key === 'Enter' && event.shiftKey) || (event.key === 'j' && event.ctrlKey)) {
    // For Ctrl+J, manually insert newline since it's not default behavior
    if (event.key === 'j' && event.ctrlKey) {
      event.preventDefault()
      const textarea = event.target
      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const value = message.value
      message.value = value.substring(0, start) + '\n' + value.substring(end)
      // Set cursor position after the newline
      nextTick(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 1
      })
    }
    // Shift+Enter is handled automatically by textarea
    return
  }

  // Enter (without Shift): Send message
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}

/**
 * Handle send action
 */
function handleSend() {
  if ((!message.value.trim() && selectedFiles.value.length === 0) || props.disabled) return

  emit('send', {
    message: message.value.trim(),
    files: [...selectedFiles.value]
  })

  // Clear local state
  selectedFiles.value = []
}

/**
 * Get selected files (for parent access)
 */
function getSelectedFiles() {
  return [...selectedFiles.value]
}

/**
 * Clear selected files
 */
function clearFiles() {
  selectedFiles.value = []
}

defineExpose({
  getSelectedFiles,
  clearFiles
})
</script>

<style scoped>
.chat-input {
  padding: 16px 24px;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.file-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chat-input :deep(.v-field) {
  border-radius: 16px 4px 16px 4px !important;
}

.chat-textarea :deep(textarea) {
  min-height: 24px !important;
  max-height: 150px;
  line-height: 1.5;
  resize: none;
}

/* ==================== Mobile ==================== */
@media (max-width: 600px) {
  /* Bottom-pinned composer: tighter horizontal padding + safe-area bottom inset
     so the bar clears the iOS home indicator and stays above the soft keyboard
     (the parent shell uses 100dvh, so the bar tracks the visible viewport). A
     subtle top divider/shadow separates it from the streaming messages. */
  .chat-input {
    padding: 8px 10px;
    padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px));
    flex-shrink: 0;
    box-shadow: 0 -1px 0 rgba(var(--v-theme-on-surface), 0.06);
  }

  /* Align attach + textarea + send along the bottom so a multi-row textarea
     grows upward while the buttons stay at the composer baseline. */
  .chat-input .d-flex {
    align-items: flex-end !important;
    gap: 6px !important;
  }

  /* Pill-shaped, auto-growing textarea (max ~5 rows) with comfortable padding. */
  .chat-input :deep(.v-field) {
    border-radius: 22px !important;
  }

  .chat-textarea :deep(textarea) {
    max-height: 132px; /* ~5 rows */
    font-size: 16px;   /* >=16px prevents iOS zoom-on-focus */
  }

  /* Attach button: 44px touch target, muted so the send button stands out. */
  .chat-input .v-btn.v-btn--icon {
    width: 44px;
    height: 44px;
  }

  /* Large, thumb-friendly, high-contrast send button with the LLARS asymmetric
     radius signature. */
  .chat-input .v-btn.v-btn--icon:last-child {
    width: 48px;
    height: 48px;
    border-radius: 16px 4px 16px 4px;
  }

  /* Hide the verbose "supported file types" hint to save vertical space */
  .chat-input .supported-types-hint {
    display: none;
  }
}
</style>
