<template>
  <div
    :class="cardClasses"
    :style="cardStyle"
    @click="clickable ? $emit('click', $event) : null"
  >
    <!-- Content -->
    <div class="l-stat-card__content">
      <!-- Icon -->
      <div class="l-stat-card__icon-wrapper" :style="iconWrapperStyle">
        <LIcon :size="iconSize" color="white">{{ icon }}</LIcon>
      </div>

      <!-- Value -->
      <div class="l-stat-card__value">{{ value }}</div>

      <!-- Label -->
      <div class="l-stat-card__label">{{ label }}</div>

      <!-- Trend (optional) -->
      <div v-if="trend" class="l-stat-card__trend" :class="trendClass">
        <LIcon size="14">{{ trendIcon }}</LIcon>
        <span>{{ trend }}</span>
      </div>
    </div>

    <!-- Accent Bar -->
    <div class="l-stat-card__accent" :style="{ backgroundColor: color }" />
  </div>
</template>

<script setup>
/**
 * LStatCard - LLARS Statistics Card Component
 *
 * A modern, centered statistics card for dashboards.
 * Features a prominent value, icon, and optional trend indicator.
 *
 * Props:
 *   - value: The main statistic value (e.g., "623", "42%")
 *   - label: Description text below the value
 *   - icon: MDI icon name
 *   - color: Accent color for icon background and bottom bar
 *   - trend: Optional trend text (e.g., "+12%")
 *   - trendUp: Boolean indicating positive trend (green) vs negative (red)
 *   - clickable: Makes card clickable with hover effect
 *   - size: Card size variant ('sm', 'md', 'lg')
 *
 * Usage:
 *   <LStatCard
 *     value="623"
 *     label="RAG Dokumente"
 *     icon="mdi-file-document-multiple"
 *     color="#a8c5e2"
 *     trend="+15%"
 *     :trend-up="true"
 *   />
 */
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: [String, Number],
    required: true
  },
  label: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: 'mdi-chart-box'
  },
  color: {
    type: String,
    default: '#b0ca97'
  },
  trend: {
    type: String,
    default: ''
  },
  trendUp: {
    type: Boolean,
    default: true
  },
  clickable: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

defineEmits(['click'])

const cardClasses = computed(() => ({
  'l-stat-card': true,
  'l-stat-card--clickable': props.clickable,
  [`l-stat-card--${props.size}`]: true
}))

const cardStyle = computed(() => ({}))

const iconWrapperStyle = computed(() => ({
  backgroundColor: props.color
}))

const iconSize = computed(() => {
  const sizes = { sm: 16, md: 20, lg: 24 }
  return sizes[props.size]
})

const trendClass = computed(() => ({
  'l-stat-card__trend--up': props.trendUp,
  'l-stat-card__trend--down': !props.trendUp
}))

const trendIcon = computed(() =>
  props.trendUp ? 'mdi-trending-up' : 'mdi-trending-down'
)
</script>

<style scoped>
/* Base Card Styles */
.l-stat-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.l-stat-card--clickable {
  cursor: pointer;
}

.l-stat-card--clickable:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

/* Content */
.l-stat-card__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 12px 16px;
  text-align: center;
  gap: 4px;
}

/* Icon Wrapper */
.l-stat-card__icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  margin-bottom: 2px;
}

/* Value */
.l-stat-card__value {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.1;
  color: rgb(var(--v-theme-on-surface));
  letter-spacing: -0.02em;
}

/* Label */
.l-stat-card__label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Trend */
.l-stat-card__trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
  margin-top: 4px;
}

.l-stat-card__trend--up {
  color: #2e7d32;
  background: rgba(46, 125, 50, 0.1);
}

.l-stat-card__trend--down {
  color: #c62828;
  background: rgba(198, 40, 40, 0.1);
}

/* Accent Bar */
.l-stat-card__accent {
  height: 4px;
  width: 100%;
  margin-top: auto;
}

/* Size Variants */
.l-stat-card--sm .l-stat-card__content {
  padding: 8px 8px 12px;
  gap: 2px;
}

.l-stat-card--sm .l-stat-card__icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 6px;
}

.l-stat-card--sm .l-stat-card__value {
  font-size: 1.25rem;
}

.l-stat-card--sm .l-stat-card__label {
  font-size: 0.65rem;
}

.l-stat-card--lg .l-stat-card__content {
  padding: 16px 16px 20px;
  gap: 6px;
}

.l-stat-card--lg .l-stat-card__icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 10px;
}

.l-stat-card--lg .l-stat-card__value {
  font-size: 1.75rem;
}

.l-stat-card--lg .l-stat-card__label {
  font-size: 0.85rem;
}
</style>
