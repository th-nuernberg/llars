<template>
  <!--
    LOriginLegend — maps referral-link colors to their labels so a color becomes
    associatable with a source. Derives the distinct sources from a list of
    member `origin` objects (same shape as GET /api/scenarios/<id>/team →
    member.origin). Renders nothing when there is no referral source to explain.

    Two layouts:
      - default (overview / settings): always-visible wrapping row.
      - collapsible (evaluation, tight space): a "Herkunft ▾" toggle; collapsed
        by default on small screens via the `defaultOpen` prop.
  -->
  <div
    v-if="referralSources.length"
    class="l-origin-legend"
    :class="{ 'is-collapsible': collapsible }"
  >
    <button
      v-if="collapsible"
      type="button"
      class="legend-toggle"
      :aria-expanded="open ? 'true' : 'false'"
      @click="open = !open"
    >
      <LIcon size="14">{{ open ? 'mdi-chevron-down' : 'mdi-chevron-right' }}</LIcon>
      <LIcon size="13" class="legend-toggle-icon">mdi-map-marker-outline</LIcon>
      <span>{{ $t('scenarioManager.origin.legend.title') }}</span>
      <span class="legend-count">{{ totalSources }}</span>
    </button>
    <span v-else class="legend-label">
      <LIcon size="13" class="legend-toggle-icon">mdi-map-marker-outline</LIcon>
      {{ $t('scenarioManager.origin.legend.title') }}
    </span>

    <div v-show="!collapsible || open" class="legend-items">
      <span
        v-for="s in referralSources"
        :key="s.key"
        class="legend-item"
      >
        <span class="legend-dot" :style="{ backgroundColor: s.color }" />
        <span class="legend-item-label">{{ s.label }}</span>
        <span class="legend-item-count">{{ s.count }}</span>
      </span>
      <span v-if="existingCount" class="legend-item legend-item--existing">
        <span class="legend-dot legend-dot--hollow" />
        <span class="legend-item-label">{{ $t('scenarioManager.origin.existing') }}</span>
        <span class="legend-item-count">{{ existingCount }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  /** Array of member.origin objects ({account, referral, scenario}) */
  origins: {
    type: Array,
    default: () => []
  },
  /** Render as a collapsible "Herkunft ▾" toggle (for tight layouts) */
  collapsible: {
    type: Boolean,
    default: false
  },
  /** Initial open state when collapsible (parents pass false on mobile) */
  defaultOpen: {
    type: Boolean,
    default: true
  }
})

const { t } = useI18n()
const open = ref(props.defaultOpen)

const NEUTRAL = '#9e9e9e'

// Distinct referral sources + a tally of plain "existing" accounts.
const derived = computed(() => {
  const map = new Map()
  let existing = 0
  for (const o of (props.origins || [])) {
    if (!o) continue
    if (o.account === 'referral' && o.referral) {
      const r = o.referral
      const key = r.slug || r.label || r.color
      if (!key) { existing++; continue }
      const label = r.label || r.slug || r.campaign || t('scenarioManager.origin.viaLink')
      const cur = map.get(key) || { key, color: r.color || NEUTRAL, label, count: 0 }
      cur.count += 1
      map.set(key, cur)
    } else {
      existing += 1
    }
  }
  const list = Array.from(map.values()).sort(
    (a, b) => b.count - a.count || a.label.localeCompare(b.label)
  )
  return { list, existing }
})

const referralSources = computed(() => derived.value.list)
const existingCount = computed(() => derived.value.existing)
// Count shown in the collapsed toggle: distinct sources incl. the existing bucket.
const totalSources = computed(() => referralSources.value.length + (existingCount.value ? 1 : 0))
</script>

<style scoped>
.l-origin-legend {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
}

.l-origin-legend.is-collapsible {
  gap: 4px 8px;
}

.legend-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.legend-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.74rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 6px 2px 6px 2px;
  padding: 3px 8px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.legend-toggle:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
}

.legend-toggle-icon {
  opacity: 0.7;
}

.legend-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 8px;
  font-size: 0.65rem;
  background: rgba(var(--v-theme-on-surface), 0.12);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.legend-items {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
}

/* When collapsible, the expanded items sit on their own line below the toggle. */
.is-collapsible .legend-items {
  flex-basis: 100%;
  padding: 6px 2px 2px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.74rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  max-width: 100%;
}

.legend-dot {
  width: 11px;
  height: 11px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-dot--hollow {
  background: transparent;
  border: 1.5px solid rgba(var(--v-theme-on-surface), 0.4);
}

.legend-item-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 18ch;
}

.legend-item-count {
  font-size: 0.66rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 6px;
  padding: 0 5px;
}

.legend-item--existing {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

@media (max-width: 600px) {
  .legend-item-label {
    max-width: 12ch;
  }
}
</style>
