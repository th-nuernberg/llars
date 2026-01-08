<template>
  <div
    :class="cardClasses"
    :style="cardStyle"
    @click="clickable ? $emit('click', $event) : null"
  >
    <!-- Color Accent Bar -->
    <div v-if="color" class="l-card__accent" :style="{ backgroundColor: color }" />

    <!-- Header -->
    <div v-if="$slots.header || title" class="l-card__header">
      <slot name="header">
        <!-- Default Header Layout -->
        <div class="l-card__header-content">
          <v-avatar
            v-if="icon || $slots.avatar"
            :color="color || 'primary'"
            :size="avatarSize"
            class="l-card__avatar"
          >
            <slot name="avatar">
              <LIcon :color="iconColor">{{ icon }}</LIcon>
            </slot>
          </v-avatar>

          <div class="l-card__titles">
            <div class="l-card__title">{{ title }}</div>
            <div v-if="subtitle" class="l-card__subtitle">{{ subtitle }}</div>
          </div>
        </div>

        <div v-if="$slots.status || status" class="l-card__status">
          <slot name="status">
            <LTag v-if="status" :variant="statusVariant" size="sm">
              {{ status }}
            </LTag>
          </slot>
        </div>
      </slot>
    </div>

    <!-- Content -->
    <div v-if="$slots.default" class="l-card__content">
      <slot />
    </div>

    <!-- Stats Row -->
    <div v-if="$slots.stats || stats.length > 0" class="l-card__stats">
      <slot name="stats">
        <div
          v-for="(stat, index) in stats"
          :key="index"
          class="l-card__stat"
        >
          <LIcon v-if="stat.icon" size="16" class="mr-1">{{ stat.icon }}</LIcon>
          <span class="l-card__stat-value">{{ stat.value }}</span>
          <span v-if="stat.label" class="l-card__stat-label">{{ stat.label }}</span>
        </div>
      </slot>
    </div>

    <!-- Tags -->
    <div v-if="$slots.tags" class="l-card__tags">
      <slot name="tags" />
    </div>

    <!-- Actions -->
    <div v-if="$slots.actions" class="l-card__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
/**
 * LCard - LLARS Global Card Component
 *
 * A flexible, themeable card component with the signature LLARS styling.
 * Features color accent bar, avatar, stats row, and action slots.
 *
 * Props:
 *   - title: Card title
 *   - subtitle: Secondary text below title
 *   - icon: MDI icon name for avatar
 *   - color: Accent color (border-top and avatar)
 *   - status: Status text (shown as LTag)
 *   - statusVariant: LTag variant for status
 *   - stats: Array of { icon, value, label } for stats row
 *   - clickable: Makes card clickable with hover effect
 *   - flat: Remove elevation/shadow
 *   - outlined: Use outline style instead of elevated
 *
 * Slots:
 *   - default: Main content area
 *   - header: Custom header (replaces default header)
 *   - avatar: Custom avatar content
 *   - status: Custom status badge area
 *   - stats: Custom stats row
 *   - tags: Tags/badges area below stats
 *   - actions: Bottom action buttons
 *
 * Usage:
 *   <LCard
 *     title="My Chatbot"
 *     subtitle="chatbot-id"
 *     icon="mdi-robot"
 *     color="#b0ca97"
 *     status="Aktiv"
 *     status-variant="success"
 *     :stats="[{ icon: 'mdi-folder', value: 3, label: 'Collections' }]"
 *   >
 *     <p>Description here</p>
 *     <template #actions>
 *       <LBtn variant="text">Edit</LBtn>
 *     </template>
 *   </LCard>
 */
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: ''
  },
  iconColor: {
    type: String,
    default: 'white'
  },
  color: {
    type: String,
    default: ''
  },
  status: {
    type: String,
    default: ''
  },
  statusVariant: {
    type: String,
    default: 'gray',
    validator: (v) => ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'danger', 'gray'].includes(v)
  },
  stats: {
    type: Array,
    default: () => []
  },
  avatarSize: {
    type: [Number, String],
    default: 40
  },
  clickable: {
    type: Boolean,
    default: false
  },
  flat: {
    type: Boolean,
    default: false
  },
  outlined: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const cardClasses = computed(() => ({
  'l-card': true,
  'l-card--clickable': props.clickable,
  'l-card--flat': props.flat,
  'l-card--outlined': props.outlined,
  'l-card--has-accent': !!props.color
}))

const cardStyle = computed(() => ({}))
</script>

<style scoped>
/* Base Card Styles */
.l-card {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius, 16px 4px 16px 4px);
  box-shadow: var(--llars-shadow-md, 0 4px 8px rgba(0, 0, 0, 0.08));
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  color: rgb(var(--v-theme-on-surface));
}

.l-card--flat {
  box-shadow: none;
}

.l-card--outlined {
  box-shadow: none;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.l-card--clickable {
  cursor: pointer;
}

.l-card--clickable:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.l-card--outlined.l-card--clickable:hover {
  box-shadow: 0 6px 18px rgba(var(--v-theme-primary), 0.12);
}

/* Accent Bar */
.l-card__accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
}

/* Header */
.l-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 16px 16px 0 16px;
  gap: 12px;
}

.l-card--has-accent .l-card__header {
  padding-top: 20px;
}

.l-card__header-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.l-card__avatar {
  flex-shrink: 0;
}

.l-card__titles {
  flex: 1;
  min-width: 0;
}

.l-card__title {
  font-size: 1.1rem;
  font-weight: 600;
  line-height: 1.3;
  color: rgb(var(--v-theme-on-surface));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.l-card__subtitle {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.l-card__status {
  flex-shrink: 0;
}

/* Content */
.l-card__content {
  flex: 1;
  padding: 12px 16px;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Stats Row */
.l-card__stats {
  display: flex;
  gap: 16px;
  padding: 0 16px 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding-top: 12px;
  margin-top: auto;
}

.l-card__stat {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.l-card__stat-value {
  font-weight: 500;
  margin-right: 4px;
}

.l-card__stat-label {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Tags */
.l-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 12px 16px;
}

/* Actions */
.l-card__actions {
  display: flex;
  align-items: center;
  padding: 8px 16px 12px 16px;
  gap: 8px;
  margin-top: auto;
}
</style>
