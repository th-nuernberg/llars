<template>
  <v-navigation-drawer
    :model-value="modelValue"
    location="right"
    temporary
    width="440"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="drawer-root">
      <!-- Header -->
      <div class="drawer-header">
        <LIcon size="20" class="mr-2">mdi-history</LIcon>
        <span class="drawer-title">
          {{ $t('evaluation.comparison.gamification.historyDrawerTitle') }}
        </span>
        <v-spacer />
        <LIconBtn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="$emit('update:modelValue', false)"
        />
      </div>

      <!-- Aggregate Summary (same payload as the popup, kept compact) -->
      <!--
        PRIVACY: this drawer used to render a per-item history list below
        the aggregate (one row per A/B/tie choice + the categories of the
        two options + a timestamp). For studies where multiple counsellors
        from the same institute participate, that view trivially leaks
        right/wrong patterns: a screenshot tells the next person what the
        prior assessor picked on each item. We now show ONLY the aggregate
        preference axes (with totals), plus the count of completed
        comparisons as a single number — no per-item rows.
      -->
      <div v-if="!loading && summaryRows.length" class="summary-block">
        <div class="summary-title">
          {{ $t('evaluation.comparison.gamification.subtitle') }}
        </div>
        <div
          v-for="row in summaryRows"
          :key="row.key"
          class="summary-line"
        >
          <LIcon size="16" class="mr-1">{{ row.icon }}</LIcon>
          <span class="summary-label">{{ row.label }}</span>
        </div>
      </div>

      <div class="history-list">
        <div v-if="loading" class="history-loading">
          <LSkeleton type="list" />
        </div>

        <div v-else-if="totalCompleted === 0" class="history-empty">
          <LIcon size="40" color="grey-lighten-1">mdi-information-outline</LIcon>
          <p>{{ $t('evaluation.comparison.gamification.historyEmpty') }}</p>
        </div>

        <div v-else class="history-total-card">
          <LIcon size="32" color="primary">mdi-counter</LIcon>
          <div class="history-total-text">
            <div class="history-total-num">{{ totalCompleted }}</div>
            <div class="history-total-label">
              {{ $t('evaluation.comparison.gamification.totalCompleted') }}
            </div>
          </div>
        </div>

        <p v-if="totalCompleted > 0" class="privacy-note">
          <LIcon size="14" class="mr-1">mdi-shield-lock-outline</LIcon>
          {{ $t('evaluation.comparison.gamification.privacyNote') }}
        </p>
      </div>
    </div>
  </v-navigation-drawer>
</template>

<script setup>
/**
 * ComparisonHistoryDrawer - right-side drawer summarising the assessor's
 * past comparisons in the current scenario.
 *
 * Re-fetches the same `/comparison/preferences` payload every time the
 * drawer opens so the history reflects the most recent submit. Categories
 * are mapped to localized labels via `categoryLabel()` — the raw category
 * keys come straight from the backend parser
 * (`comparison_preference_stats_service._categorize`).
 */
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

defineEmits(['update:modelValue'])
const { t } = useI18n()

const loading = ref(false)
const stats = ref(null)

watch(() => props.modelValue, async (open) => {
  if (!open) return
  loading.value = true
  try {
    const res = await axios.get(
      `/api/evaluation/session/${props.scenarioId}/comparison/preferences`
    )
    stats.value = res.data
  } catch (err) {
    console.error('Failed to load comparison history:', err)
    stats.value = null
  } finally {
    loading.value = false
  }
})

// We deliberately do NOT expose individual history entries on this surface
// any more (privacy: prevents per-item leak between assessors in the same
// scenario). The stats payload still carries `history`, but we only count
// it instead of rendering it.
const totalCompleted = computed(() => (stats.value?.history || []).length)

const summaryRows = computed(() => {
  const p = stats.value?.preferences || {}
  const out = []
  if (p.human_vs_llm?.applicable > 0) {
    out.push({
      key: 'human',
      icon: 'mdi-account-heart-outline',
      label: t('evaluation.comparison.gamification.humanVsLLM', {
        chosen: p.human_vs_llm.chose_human,
        total: p.human_vs_llm.applicable
      })
    })
  }
  if (p.trained_vs_base?.applicable > 0) {
    out.push({
      key: 'trained',
      icon: 'mdi-school-outline',
      label: t('evaluation.comparison.gamification.trainedVsBase', {
        chosen: p.trained_vs_base.chose_trained,
        total: p.trained_vs_base.applicable
      })
    })
  }
  if (p.larger_vs_smaller?.applicable > 0) {
    out.push({
      key: 'larger',
      icon: 'mdi-arrow-expand-vertical',
      label: t('evaluation.comparison.gamification.largerVsSmaller', {
        chosen: p.larger_vs_smaller.chose_larger,
        total: p.larger_vs_smaller.applicable
      })
    })
  }
  if (p.closed_vs_open?.applicable > 0) {
    out.push({
      key: 'closed',
      icon: 'mdi-lock-outline',
      label: t('evaluation.comparison.gamification.closedVsOpen', {
        chosen: p.closed_vs_open.chose_closed,
        total: p.closed_vs_open.applicable
      })
    })
  }
  return out
})

// categoryLabel + formatTime are unused since the per-item rows were
// removed (privacy fix). Left out intentionally — restoring requires
// re-thinking how to avoid leaking individual choices between assessors.
</script>

<style scoped>
.drawer-root {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.drawer-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.summary-block {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  background: linear-gradient(135deg,
    rgba(176, 202, 151, 0.08) 0%,
    rgba(136, 196, 200, 0.04) 100%);
}

.summary-title {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-bottom: 6px;
}

.summary-line {
  display: flex;
  align-items: center;
  font-size: 0.88rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  padding: 2px 0;
}

.summary-label {
  flex: 1;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.history-loading,
.history-empty {
  padding: 24px 8px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.history-total-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(176, 202, 151, 0.08);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 12px 3px 12px 3px;
}

.history-total-num {
  font-size: 1.4rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.history-total-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.privacy-note {
  margin: 12px 0 0;
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  display: flex;
  align-items: flex-start;
  line-height: 1.4;
}
</style>
