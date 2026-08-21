<template>
  <!--
    LUserOrigin — compact "where did this user come from" pill.

    Renders the ACCOUNT dimension of a member's origin as a colored pill:
      - referral  → filled pill in the referral link's color (color == identity
                    of that link, consistent LLARS-wide)
      - existing  → neutral outlined pill ("Bestandsnutzer")
    The SCENARIO dimension (owner / auto-enroll / invited-by / self) lives in the
    hover tooltip so the pill stays glanceable. In `dense` mode (tight layouts
    like the evaluation voter chips) it collapses to just the color dot + tooltip.

    Data shape comes from GET /api/scenarios/<id>/team → member.origin.
  -->
  <v-tooltip
    v-if="origin"
    location="top"
    :open-delay="120"
    max-width="320"
    content-class="l-user-origin__tip"
  >
    <template #activator="{ props: tip }">
      <span
        v-bind="tip"
        class="l-user-origin"
        :class="[
          `l-user-origin--${account}`,
          `l-user-origin--${size}`,
          { 'l-user-origin--dense': dense }
        ]"
        :style="pillStyle"
      >
        <span v-if="dense" class="l-user-origin__dot" :style="dotStyle" />
        <template v-else>
          <LIcon :size="iconSize" class="l-user-origin__icon">{{ icon }}</LIcon>
          <span class="l-user-origin__label">{{ label }}</span>
        </template>
      </span>
    </template>

    <!-- Two-dimensional tooltip: account origin + how they joined this scenario -->
    <div class="l-user-origin__tooltip">
      <div class="ttl-row ttl-head">
        <LIcon size="14" class="ttl-icon">{{ icon }}</LIcon>
        <span>{{ accountLine }}</span>
      </div>
      <div v-if="campaignLine" class="ttl-row ttl-sub">{{ campaignLine }}</div>
      <div v-if="registeredLine" class="ttl-row ttl-sub">{{ registeredLine }}</div>
      <div class="ttl-divider" />
      <div class="ttl-row ttl-sub">
        <LIcon size="13" class="ttl-icon">{{ joinIcon }}</LIcon>
        <span>{{ joinLine }}</span>
      </div>
    </div>
  </v-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getReadableTextColor } from '@/utils/colorHelpers'

const props = defineProps({
  /** member.origin object from the scenario team API ({account, referral, scenario}) */
  origin: {
    type: Object,
    default: null
  },
  /** Collapse to a color dot only (for tight layouts like the evaluation tab) */
  dense: {
    type: Boolean,
    default: false
  },
  size: {
    type: String,
    default: 'sm',
    validator: (v) => ['sm', 'md'].includes(v)
  }
})

const { t, locale } = useI18n()

// Neutral color for "existing account" pills (no specific referral source).
const NEUTRAL = '#9e9e9e'

const JOIN_ICONS = {
  owner: 'mdi-crown-outline',
  referral_autoenroll: 'mdi-link-plus',
  invited: 'mdi-email-outline',
  self: 'mdi-account-arrow-right-outline'
}

const account = computed(() => props.origin?.account || 'existing')
const isReferral = computed(() => account.value === 'referral')
const referral = computed(() => props.origin?.referral || null)

const color = computed(() => (isReferral.value ? (referral.value?.color || NEUTRAL) : NEUTRAL))
const textColor = computed(() => getReadableTextColor(color.value))

const icon = computed(() => (isReferral.value ? 'mdi-link-variant' : 'mdi-account-check-outline'))
const iconSize = computed(() => (props.size === 'md' ? 14 : 12))

const label = computed(() => {
  if (isReferral.value) {
    const r = referral.value || {}
    return r.label || r.slug || r.campaign || t('scenarioManager.origin.viaLink')
  }
  return t('scenarioManager.origin.existing')
})

// Filled colored pill for referral; neutral outlined pill for existing accounts.
const pillStyle = computed(() => {
  if (props.dense) return {}
  if (isReferral.value) {
    return { backgroundColor: color.value, color: textColor.value, borderColor: color.value }
  }
  return {}
})

const dotStyle = computed(() => {
  if (isReferral.value) return { backgroundColor: color.value }
  // Hollow dot for existing accounts so "no source" reads differently.
  return { backgroundColor: 'transparent', borderColor: NEUTRAL }
})

const accountLine = computed(() => (isReferral.value
  ? t('scenarioManager.origin.tooltip.referral')
  : t('scenarioManager.origin.tooltip.existing')))

const campaignLine = computed(() => {
  if (!isReferral.value) return ''
  const r = referral.value || {}
  const parts = []
  if (r.campaign) parts.push(t('scenarioManager.origin.tooltip.campaign', { campaign: r.campaign }))
  if (r.slug) parts.push(t('scenarioManager.origin.tooltip.link', { slug: r.slug }))
  return parts.join(' · ')
})

function fmtDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString(locale.value || undefined, {
      year: 'numeric', month: '2-digit', day: '2-digit'
    })
  } catch {
    return ''
  }
}

const registeredLine = computed(() => {
  if (!isReferral.value) return ''
  const d = fmtDate(referral.value?.registered_at)
  return d ? t('scenarioManager.origin.tooltip.registeredAt', { date: d }) : ''
})

const joinedVia = computed(() => props.origin?.scenario?.joined_via || 'self')
const joinIcon = computed(() => JOIN_ICONS[joinedVia.value] || JOIN_ICONS.self)

const joinLine = computed(() => {
  const s = props.origin?.scenario || {}
  switch (joinedVia.value) {
    case 'owner': return t('scenarioManager.origin.join.owner')
    case 'referral_autoenroll': return t('scenarioManager.origin.join.autoenroll')
    case 'invited': return t('scenarioManager.origin.join.invited', { by: s.invited_by || '—' })
    default: return t('scenarioManager.origin.join.self')
  }
})
</script>

<style scoped>
.l-user-origin {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  /* LLARS signature asymmetric tag radius */
  border-radius: 6px 2px 6px 2px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  max-width: 100%;
  border: 1px solid transparent;
}

.l-user-origin--sm {
  font-size: 0.7rem;
  padding: 3px 7px;
}

.l-user-origin--md {
  font-size: 0.78rem;
  padding: 4px 9px;
}

/* Existing account = neutral, outlined (no brand color to associate). */
.l-user-origin--existing {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border-color: rgba(var(--v-theme-on-surface), 0.18);
  color: rgba(var(--v-theme-on-surface), 0.65);
}

.l-user-origin__icon {
  flex-shrink: 0;
}

.l-user-origin__label {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 14ch;
}

.l-user-origin--md .l-user-origin__label {
  max-width: 22ch;
}

/* Dense = just a dot (tight layouts). */
.l-user-origin--dense {
  padding: 0;
  border: none;
  background: transparent !important;
}

.l-user-origin__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 1.5px solid transparent;
  flex-shrink: 0;
}

/* Tooltip body */
.l-user-origin__tooltip {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 2px 0;
}

.ttl-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
}

.ttl-head {
  font-weight: 600;
}

.ttl-sub {
  opacity: 0.82;
  font-size: 0.74rem;
}

.ttl-icon {
  flex-shrink: 0;
  opacity: 0.9;
}

.ttl-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.18);
  margin: 3px 0;
}
</style>
