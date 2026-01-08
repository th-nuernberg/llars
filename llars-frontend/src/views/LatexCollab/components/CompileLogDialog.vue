<!--
  CompileLogDialog.vue

  Dialog for viewing LaTeX compile logs and issues.
-->
<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="760">
    <v-card class="compile-log-dialog">
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2">mdi-text-box-outline</LIcon>
        Compile Log
        <v-spacer />
        <LIconBtn icon="mdi-close" tooltip="Schließen" @click="$emit('update:modelValue', false)" />
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-3" density="compact">
          {{ error }}
        </v-alert>
        <div v-if="issues.length" class="compile-issues">
          <div class="text-subtitle-2 mb-2">Fehler &amp; Warnungen</div>
          <div class="issue-list">
            <div
              v-for="issue in issues"
              :key="issue.id"
              class="issue-row"
              :class="{ clickable: !!issue.document_id }"
              @click="handleIssueClick(issue)"
            >
              <v-chip size="x-small" variant="tonal" :color="issue.color">
                {{ issue.label }}
              </v-chip>
              <span class="issue-message">{{ issue.message }}</span>
              <span class="issue-location">{{ issue.location }}</span>
            </div>
          </div>
        </div>
        <pre class="compile-log">{{ log || 'Noch kein Log vorhanden.' }}</pre>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  issues: {
    type: Array,
    default: () => []
  },
  log: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'jump-to-issue'])

function handleIssueClick(issue) {
  if (issue.document_id) {
    emit('jump-to-issue', issue)
  }
}
</script>

<style scoped>
.compile-issues {
  margin-bottom: 16px;
}

.issue-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
}

.issue-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  font-size: 13px;
}

.issue-row:last-child {
  border-bottom: none;
}

.issue-row.clickable {
  cursor: pointer;
}

.issue-row.clickable:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.issue-message {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.issue-location {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 12px;
  flex-shrink: 0;
}

.compile-log {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 16px;
  font-size: 12px;
  font-family: 'Fira Code', 'Consolas', monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}
</style>
