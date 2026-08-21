<template>
  <v-dialog
    :model-value="modelValue"
    max-width="620"
    persistent
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="reward-card">
      <!-- Header -->
      <div class="reward-header">
        <div class="reward-title celebration-pulse">
          <LIcon size="28" class="mr-2">mdi-trophy-variant</LIcon>
          <span v-if="isFirst">{{ $t('evaluation.comparison.gamification.milestoneFirstTitle') }}</span>
          <span v-else>{{ $t('evaluation.comparison.gamification.milestoneRecurringTitle', { n: milestoneCount }) }}</span>
        </div>
        <LIconBtn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="close"
        />
      </div>

      <!-- Subtitle -->
      <div class="reward-subtitle">
        {{ $t('evaluation.comparison.gamification.subtitle') }}
      </div>

      <!-- Body -->
      <div class="reward-body">
        <div v-if="loading" class="reward-loading">
          <LSkeleton type="card" />
          <LSkeleton type="card" />
        </div>

        <div v-else-if="visiblePreferences.length === 0" class="reward-empty">
          <LIcon size="48" color="grey-lighten-1">mdi-information-outline</LIcon>
          <p>{{ $t('evaluation.comparison.gamification.noSignal') }}</p>
        </div>

        <div v-else class="reward-stats">
          <div
            v-for="pref in visiblePreferences"
            :key="pref.key"
            class="stat-row"
          >
            <LGauge
              :icon="pref.icon"
              :label="pref.label"
              :value="`${pref.chosen}/${pref.applicable}`"
              :percent="pref.percent"
              show-progress
              show-percent
            />
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="reward-footer">
        <LBtn
          variant="text"
          size="small"
          :disabled="loading"
          @click="onViewHistory"
        >
          <LIcon start size="16">mdi-history</LIcon>
          {{ $t('evaluation.comparison.gamification.viewHistory') }}
        </LBtn>
        <LBtn
          variant="primary"
          size="small"
          @click="close"
        >
          {{ $t('evaluation.comparison.gamification.continueButton') }}
        </LBtn>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
/**
 * ComparisonRewardDialog - Gamification reward popup.
 *
 * Triggered after an assessor reaches a milestone in a comparison scenario
 * (first_milestone, then every recurring_milestone). Shows their pairwise
 * preference patterns so far — pure preference reveal, no right/wrong:
 * "you chose Human 7/10", "preferred Trained-SFT 5/8", etc.
 *
 * Data source: GET /api/evaluation/session/:scenarioId/comparison/preferences
 * (see app/services/evaluation/comparison_preference_stats_service.py).
 *
 * Axes with applicable == 0 are hidden so first-time users don't see empty
 * cards — early in a scenario, only some axes have signal yet.
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
  },
  milestoneCount: {
    type: Number,
    default: 0
  },
  isFirst: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'view-history'])
const { t } = useI18n()

const loading = ref(false)
const stats = ref(null)
const error = ref(null)

// Fetch fresh stats every time the dialog opens — the milestone is hit on
// the most recent submit, so we want the count to include it.
watch(() => props.modelValue, async (open) => {
  if (!open) return
  loading.value = true
  error.value = null
  try {
    const res = await axios.get(
      `/api/evaluation/session/${props.scenarioId}/comparison/preferences`
    )
    stats.value = res.data
  } catch (err) {
    console.error('Failed to load preference stats:', err)
    error.value = err.response?.data?.error || 'Failed to load stats'
    stats.value = null
  } finally {
    loading.value = false
  }
})

// Build the visible preference rows from the payload, filtering out axes
// with no signal yet (applicable == 0). Order is fixed — most "Turing-Test"
// relevant axis first.
const visiblePreferences = computed(() => {
  const p = stats.value?.preferences || {}
  const rows = []
  const human = p.human_vs_llm || {}
  if (human.applicable > 0) {
    rows.push({
      key: 'human',
      icon: 'mdi-account-heart-outline',
      label: t('evaluation.comparison.gamification.humanVsLLM', {
        chosen: human.chose_human, total: human.applicable
      }),
      chosen: human.chose_human,
      applicable: human.applicable,
      percent: Math.round((human.chose_human / human.applicable) * 100)
    })
  }
  const trained = p.trained_vs_base || {}
  if (trained.applicable > 0) {
    rows.push({
      key: 'trained',
      icon: 'mdi-school-outline',
      label: t('evaluation.comparison.gamification.trainedVsBase', {
        chosen: trained.chose_trained, total: trained.applicable
      }),
      chosen: trained.chose_trained,
      applicable: trained.applicable,
      percent: Math.round((trained.chose_trained / trained.applicable) * 100)
    })
  }
  const larger = p.larger_vs_smaller || {}
  if (larger.applicable > 0) {
    rows.push({
      key: 'larger',
      icon: 'mdi-arrow-expand-vertical',
      label: t('evaluation.comparison.gamification.largerVsSmaller', {
        chosen: larger.chose_larger, total: larger.applicable
      }),
      chosen: larger.chose_larger,
      applicable: larger.applicable,
      percent: Math.round((larger.chose_larger / larger.applicable) * 100)
    })
  }
  const closed = p.closed_vs_open || {}
  if (closed.applicable > 0) {
    rows.push({
      key: 'closed',
      icon: 'mdi-lock-outline',
      label: t('evaluation.comparison.gamification.closedVsOpen', {
        chosen: closed.chose_closed, total: closed.applicable
      }),
      chosen: closed.chose_closed,
      applicable: closed.applicable,
      percent: Math.round((closed.chose_closed / closed.applicable) * 100)
    })
  }
  return rows
})

function close() {
  emit('update:modelValue', false)
}

function onViewHistory() {
  emit('view-history')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.reward-card {
  border-radius: 16px 4px 16px 4px;
  padding: 0;
  overflow: hidden;
}

.reward-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px 8px;
  background: linear-gradient(135deg,
    rgba(176, 202, 151, 0.18) 0%,
    rgba(136, 196, 200, 0.12) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.reward-title {
  display: flex;
  align-items: center;
  font-size: 1.15rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.reward-subtitle {
  padding: 12px 20px 4px;
  font-size: 0.92rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.reward-body {
  padding: 12px 20px 16px;
  min-height: 120px;
}

.reward-loading,
.reward-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reward-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  color: rgba(var(--v-theme-on-surface), 0.55);
  text-align: center;
}

.stat-row {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 10px 3px 10px 3px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.25);
}

.reward-footer {
  display: flex;
  justify-content: space-between;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  background: rgba(var(--v-theme-surface-variant), 0.18);
}

/* Celebration pulse for the headline. Plays twice on dialog open. */
.celebration-pulse {
  animation: lcelebrate 1.6s ease-out 2;
}

@keyframes lcelebrate {
  0%   { transform: scale(1); }
  50%  { transform: scale(1.06); }
  100% { transform: scale(1); }
}
</style>
