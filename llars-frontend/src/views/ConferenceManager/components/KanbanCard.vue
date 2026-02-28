<template>
  <div class="kanban-card" @click="$emit('click')">
    <div class="card-title">{{ paper.title }}</div>

    <div v-if="paper.conference_acronym" class="card-conference">
      <v-chip size="x-small" variant="tonal" color="primary">
        {{ paper.conference_acronym }}
      </v-chip>
    </div>

    <div v-if="paper.authors?.length" class="card-authors">
      <v-icon size="12" class="mr-1">mdi-account-outline</v-icon>
      <span>{{ authorNames }}</span>
    </div>

    <div v-if="paper.keywords?.length" class="card-keywords">
      <v-chip
        v-for="kw in paper.keywords.slice(0, 3)"
        :key="kw"
        size="x-small"
        variant="outlined"
        class="mr-1 mb-1"
      >
        {{ kw }}
      </v-chip>
      <v-chip
        v-if="paper.keywords.length > 3"
        size="x-small"
        variant="outlined"
        class="mb-1"
      >
        +{{ paper.keywords.length - 3 }}
      </v-chip>
    </div>

    <div class="card-footer">
      <a
        v-if="paper.overleaf_url"
        :href="paper.overleaf_url"
        target="_blank"
        class="overleaf-link"
        @click.stop
      >
        <v-icon size="14">mdi-leaf</v-icon>
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  paper: { type: Object, required: true },
})

defineEmits(['click'])

const authorNames = computed(() => {
  if (!props.paper.authors?.length) return ''
  return props.paper.authors
    .map(a => a.external_name || a.username || 'Unknown')
    .join(', ')
})
</script>

<style scoped>
.kanban-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px 4px 16px 4px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
}

.kanban-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.card-title {
  font-weight: 500;
  font-size: 0.875rem;
  line-height: 1.3;
  margin-bottom: 6px;
}

.card-conference {
  margin-bottom: 6px;
}

.card-authors {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 6px;
}

.card-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 4px;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}

.overleaf-link {
  color: #4caf50;
  text-decoration: none;
}
</style>
