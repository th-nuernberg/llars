<template>
  <div
    class="kanban-card"
    :style="{ borderLeftColor: statusColor }"
    @click="$emit('click')"
  >
    <!-- Drag Handle (hover only) -->
    <div class="drag-handle">
      <v-icon size="14" color="disabled">mdi-drag</v-icon>
    </div>

    <!-- Content -->
    <div class="card-body">
      <div class="card-title">{{ paper.title }}</div>

      <div v-if="paper.conference_acronym" class="card-conference">
        <v-chip size="x-small" variant="tonal" :style="{ borderRadius: '6px 2px 6px 2px' }">
          <span
            class="ranking-dot"
            :style="{ backgroundColor: conferenceRankingColor }"
          />
          {{ paper.conference_acronym }}
        </v-chip>
        <span v-if="paper.submissions?.length > 1" class="resubmit-indicator" :title="`${paper.submissions.length} submissions`">
          &#8617; {{ paper.submissions.length }}
        </span>
      </div>

      <!-- Deadline warning -->
      <div v-if="deadlineSoon" class="deadline-warning">
        <v-icon size="12" color="error">mdi-clock-alert-outline</v-icon>
        <span>{{ formatDeadline }}</span>
      </div>

      <div v-if="paper.authors?.length" class="card-authors">
        <span
          v-for="(author, i) in paper.authors.slice(0, 3)"
          :key="i"
          class="author-circle"
          :title="getAuthorName(author)"
        >
          {{ getInitials(author) }}
        </span>
        <span v-if="paper.authors.length > 3" class="author-overflow">
          +{{ paper.authors.length - 3 }}
        </span>
      </div>

      <div v-if="paper.keywords?.length" class="card-keywords">
        <v-chip
          v-for="kw in paper.keywords.slice(0, 3)"
          :key="kw"
          size="x-small"
          variant="outlined"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
        >
          {{ kw }}
        </v-chip>
        <v-chip
          v-if="paper.keywords.length > 3"
          size="x-small"
          variant="outlined"
          :style="{ borderRadius: '6px 2px 6px 2px' }"
        >
          +{{ paper.keywords.length - 3 }}
        </v-chip>
      </div>
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <div class="footer-links">
        <a
          v-if="paper.overleaf_url"
          :href="paper.overleaf_url"
          target="_blank"
          class="footer-link overleaf"
          @click.stop
        >
          <v-icon size="14">mdi-leaf</v-icon>
        </a>
        <template v-if="paper.latex_workspace_id">
          <a
            v-if="latexAccess.hasAccess"
            class="footer-link llars-latex"
            @click.stop="$emit('open-workspace', paper.latex_workspace_id)"
          >
            <v-icon size="14">mdi-file-document-edit-outline</v-icon>
          </a>
          <span
            v-else-if="latexAccess.requestStatus === 'pending'"
            class="footer-link disabled"
          >
            <v-icon size="14">mdi-clock-outline</v-icon>
          </span>
          <a
            v-else
            class="footer-link lock"
            @click.stop="$emit('request-latex-access', paper.latex_workspace_id)"
          >
            <v-icon size="14">mdi-lock-outline</v-icon>
          </a>
        </template>
      </div>

      <div class="card-menu">
        <v-btn icon size="x-small" variant="text" @click.stop="$emit('click')">
          <v-icon size="14">mdi-pencil-outline</v-icon>
        </v-btn>
        <v-btn icon size="x-small" variant="text" color="error" @click.stop="$emit('delete')">
          <v-icon size="14">mdi-delete-outline</v-icon>
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getStatusConfig, getRankingColor } from '../config/conferenceConfig'

const props = defineProps({
  paper: { type: Object, required: true },
  conferences: { type: Array, default: () => [] },
  latexAccess: { type: Object, default: () => ({ hasAccess: false, requestStatus: null }) },
})

defineEmits(['click', 'delete', 'request-latex-access', 'open-workspace'])

const statusColor = computed(() => getStatusConfig(props.paper.status).color)

const linkedConference = computed(() => {
  if (!props.paper.conference_id) return null
  return props.conferences.find(c => c.id === props.paper.conference_id)
})

const conferenceRankingColor = computed(() => {
  if (!linkedConference.value) return '#808080'
  return getRankingColor(linkedConference.value.core_ranking)
})

const deadlineSoon = computed(() => {
  const conf = linkedConference.value
  if (!conf?.submission_deadline) return false
  const deadline = new Date(conf.submission_deadline)
  const now = new Date()
  const diffDays = (deadline - now) / (1000 * 60 * 60 * 24)
  return diffDays >= 0 && diffDays <= 14
})

const formatDeadline = computed(() => {
  const conf = linkedConference.value
  if (!conf?.submission_deadline) return ''
  const deadline = new Date(conf.submission_deadline)
  const now = new Date()
  const diffDays = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24))
  return `${diffDays}d`
})

function getAuthorName(author) {
  return author.display_name || author.external_name || author.username || 'Unknown'
}

function getInitials(author) {
  const name = getAuthorName(author)
  const parts = name.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
}
</script>

<style scoped>
.kanban-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-left: 4px solid;
  border-radius: 16px 4px 16px 4px;
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
  display: flex;
  flex-direction: column;
  gap: 6px;
  position: relative;
}

.kanban-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

/* Drag handle */
.drag-handle {
  position: absolute;
  left: 8px;
  top: 50%;
  transform: translateY(-50%);
  opacity: 0;
  transition: opacity 0.2s;
}

.kanban-card:hover .drag-handle {
  opacity: 0.5;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title {
  font-weight: 500;
  font-size: 0.85rem;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-conference {
  display: flex;
  align-items: center;
  gap: 4px;
}

.resubmit-indicator {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.45);
  font-weight: 500;
}

.ranking-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 4px;
}

.deadline-warning {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  color: #c4735a;
  font-weight: 600;
}

.card-authors {
  display: flex;
  align-items: center;
  gap: 0;
}

.author-circle {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.55rem;
  font-weight: 600;
  margin-left: -4px;
  border: 2px solid rgb(var(--v-theme-surface));
}

.author-circle:first-child {
  margin-left: 0;
}

.author-overflow {
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-left: 4px;
}

.card-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-link {
  text-decoration: none;
  transition: color 0.2s;
  display: flex;
  align-items: center;
}

.footer-link.overleaf {
  color: #4caf50;
}

.footer-link.llars-latex {
  color: #88c4c8;
  cursor: pointer;
}

.footer-link.llars-latex:hover {
  color: #6bb0b5;
}

.footer-link.lock {
  color: rgba(var(--v-theme-on-surface), 0.4);
  cursor: pointer;
}

.footer-link.lock:hover {
  color: #e8a087;
}

.footer-link.disabled {
  color: rgba(var(--v-theme-on-surface), 0.25);
  cursor: default;
}

.card-menu {
  display: flex;
  gap: 0;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.kanban-card:hover .card-menu {
  opacity: 1;
}
</style>
