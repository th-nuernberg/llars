<template>
  <v-card variant="outlined" class="quick-stats-bar mb-4">
    <v-card-text class="py-3">
      <v-row align="center" no-gutters>
        <!-- Similarity Score -->
        <v-col cols="6" sm="3" class="stat-item">
          <div class="d-flex align-center">
            <v-progress-circular
              :model-value="similarity * 100"
              :color="getSimilarityColor(similarity)"
              :size="48"
              :width="5"
            >
              <span class="text-caption font-weight-bold">{{ Math.round(similarity * 100) }}%</span>
            </v-progress-circular>
            <div class="ml-3">
              <div class="text-caption text-medium-emphasis">{{ $t('oncoco.quickStats.similarity.label') }}</div>
              <div class="text-body-2 font-weight-medium">{{ getSimilarityText(similarity) }}</div>
            </div>
          </div>
        </v-col>

        <!-- Frobenius Distance -->
        <v-col cols="6" sm="3" class="stat-item">
          <div class="d-flex align-center">
            <v-avatar :color="getFrobeniusColor(frobeniusDistance)" size="48" class="text-white">
              <span class="text-caption font-weight-bold">{{ formatNumber(frobeniusDistance) }}</span>
            </v-avatar>
            <div class="ml-3">
              <div class="text-caption text-medium-emphasis">{{ $t('oncoco.quickStats.frobenius.label') }}</div>
              <div class="text-body-2 font-weight-medium">{{ getFrobeniusText(frobeniusDistance) }}</div>
            </div>
          </div>
        </v-col>

        <!-- Significance (p-value) -->
        <v-col cols="6" sm="3" class="stat-item">
          <div class="d-flex align-center">
            <v-avatar :color="getSignificanceColor(pValue)" size="48" class="text-white">
              <LIcon v-if="pValue < 0.05">mdi-check</LIcon>
              <LIcon v-else>mdi-minus</LIcon>
            </v-avatar>
            <div class="ml-3">
              <div class="text-caption text-medium-emphasis">{{ $t('oncoco.quickStats.significance.label') }}</div>
              <div class="text-body-2 font-weight-medium">
                p={{ formatPValue(pValue) }}
                <v-chip
                  v-if="pValue < 0.05"
                  size="x-small"
                  color="success"
                  class="ml-1"
                >
                  {{ $t('oncoco.quickStats.significance.short') }}
                </v-chip>
              </div>
            </div>
          </div>
        </v-col>

        <!-- Chi-Square Significant States -->
        <v-col cols="6" sm="2" class="stat-item">
          <div class="d-flex align-center">
            <v-avatar :color="getChiSquareColor(chiSquareSignificant, chiSquareTotal)" size="48" class="text-white">
              <span class="text-caption font-weight-bold">{{ chiSquareSignificant }}/{{ chiSquareTotal }}</span>
            </v-avatar>
            <div class="ml-3">
              <div class="text-caption text-medium-emphasis">{{ $t('oncoco.quickStats.chiSquare.label') }}</div>
              <div class="text-body-2 font-weight-medium">{{ getChiSquareText(chiSquareSignificant, chiSquareTotal) }}</div>
            </div>
          </div>
        </v-col>

        <!-- Methodology Button -->
        <v-col cols="12" sm="1" class="d-flex justify-end">
          <v-btn
            icon
            variant="text"
            size="small"
            @click="$emit('show-methodology')"
            :title="$t('oncoco.quickStats.methodology')"
          >
            <LIcon>mdi-information-outline</LIcon>
          </v-btn>
        </v-col>
      </v-row>

      <!-- Loading Overlay -->
      <v-overlay
        :model-value="loading"
        contained
        class="align-center justify-center"
      >
        <v-progress-circular indeterminate size="32"></v-progress-circular>
      </v-overlay>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { useI18n } from 'vue-i18n';

const props = defineProps({
  similarity: {
    type: Number,
    default: 0
  },
  frobeniusDistance: {
    type: Number,
    default: 0
  },
  pValue: {
    type: Number,
    default: 1
  },
  chiSquareSignificant: {
    type: Number,
    default: 0
  },
  chiSquareTotal: {
    type: Number,
    default: 0
  },
  loading: {
    type: Boolean,
    default: false
  }
});

defineEmits(['show-methodology']);

const { t } = useI18n();

// Helper functions
const formatNumber = (value) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return value.toFixed(2);
};

const formatPValue = (value) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  if (value < 0.001) return '<0.001';
  if (value < 0.01) return '<0.01';
  return value.toFixed(2);
};

// Similarity helpers
const getSimilarityColor = (value) => {
  if (value >= 0.8) return 'success';
  if (value >= 0.6) return 'info';
  if (value >= 0.4) return 'warning';
  return 'error';
};

const getSimilarityText = (value) => {
  if (value >= 0.9) return t('oncoco.quickStats.similarity.levels.veryHigh');
  if (value >= 0.7) return t('oncoco.quickStats.similarity.levels.high');
  if (value >= 0.5) return t('oncoco.quickStats.similarity.levels.moderate');
  if (value >= 0.3) return t('oncoco.quickStats.similarity.levels.low');
  return t('oncoco.quickStats.similarity.levels.veryLow');
};

// Frobenius helpers
const getFrobeniusColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.4) return 'info';
  if (value < 0.6) return 'warning';
  return 'error';
};

const getFrobeniusText = (value) => {
  if (value < 0.2) return t('oncoco.quickStats.frobenius.levels.similar');
  if (value < 0.4) return t('oncoco.quickStats.frobenius.levels.moderate');
  if (value < 0.6) return t('oncoco.quickStats.frobenius.levels.distinct');
  return t('oncoco.quickStats.frobenius.levels.strong');
};

// Significance helpers
const getSignificanceColor = (pValue) => {
  if (pValue < 0.01) return 'success';
  if (pValue < 0.05) return 'info';
  return 'grey';
};

// Chi-Square helpers
const getChiSquareColor = (significant, total) => {
  if (total === 0) return 'grey';
  const ratio = significant / total;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};

const getChiSquareText = (significant, total) => {
  if (total === 0) return t('oncoco.quickStats.chiSquare.empty');
  const percent = Math.round((significant / total) * 100);
  return t('oncoco.quickStats.chiSquare.states', { percent });
};
</script>

<style scoped>
.quick-stats-bar {
  position: relative;
  overflow: hidden;
}

.stat-item {
  padding: 8px 12px;
  min-width: 0; /* Allow shrinking */
}

.stat-item .text-body-2 {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 600px) {
  .stat-item {
    padding: 8px 4px;
  }

  .stat-item .ml-3 {
    margin-left: 8px !important;
  }
}
</style>
