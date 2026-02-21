<template>
  <div class="matrix-comparison-metrics">
    <!-- Header with Help Button (hidden when used in dialog) -->
    <div v-if="!hideHeader" class="d-flex align-center mb-3">
      <div class="text-h6 font-weight-bold">
        <LIcon start>mdi-chart-scatter-plot</LIcon>
        {{ $t('oncoco.matrixComparison.title') }}
      </div>
      <v-spacer></v-spacer>
      <v-btn
        variant="outlined"
        size="small"
        prepend-icon="mdi-help-circle"
        @click="showMethodologyDialog = true"
      >
        {{ $t('oncoco.matrixComparison.actions.methodologySources') }}
      </v-btn>
    </div>

    <!-- Loading State -->
    <v-progress-linear v-if="loading" indeterminate class="mb-4"></v-progress-linear>

    <!-- Error Alert -->
    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>

    <!-- Controls -->
    <v-row class="mb-4">
      <v-col cols="12" sm="4" md="3">
        <v-select
          v-model="level"
          :items="levelOptions"
          :label="$t('oncoco.matrixComparison.controls.detailLevel')"
          variant="outlined"
          density="compact"
          @update:model-value="loadMetrics"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="4" md="3">
        <v-text-field
          v-model.number="smoothing"
          type="number"
          min="0"
          step="0.1"
          :label="$t('oncoco.matrixComparison.controls.smoothingLabel')"
          variant="outlined"
          density="compact"
          @update:model-value="debouncedLoadMetrics"
        >
          <template v-slot:append>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <LIcon v-bind="props" size="small">mdi-information</LIcon>
              </template>
              <span>{{ $t('oncoco.matrixComparison.controls.smoothingHint') }}</span>
            </v-tooltip>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="3">
        <v-text-field
          v-model.number="permutations"
          type="number"
          min="100"
          max="10000"
          step="100"
          :label="$t('oncoco.matrixComparison.controls.permutationsLabel')"
          variant="outlined"
          density="compact"
          @update:model-value="debouncedLoadMetrics"
        >
          <template v-slot:append>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <LIcon v-bind="props" size="small">mdi-information</LIcon>
              </template>
              <span>{{ $t('oncoco.matrixComparison.controls.permutationsHint') }}</span>
            </v-tooltip>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="12" md="3" class="d-flex align-center">
        <v-btn
          color="primary"
          variant="flat"
          @click="loadMetrics"
          :loading="loading"
          block
        >
          <LIcon start>mdi-refresh</LIcon>
          {{ $t('oncoco.matrixComparison.actions.calculate') }}
        </v-btn>
      </v-col>
    </v-row>

    <!-- Results -->
    <template v-if="metricsData && !loading">
      <!-- Pairwise Comparisons -->
      <v-row>
        <v-col
          v-for="(comparison, idx) in metricsData.pairwise_comparisons"
          :key="idx"
          cols="12"
          :md="metricsData.pairwise_comparisons.length === 1 ? 12 : 6"
        >
          <v-card variant="outlined" class="h-100">
            <v-card-title class="text-subtitle-1 py-2 d-flex align-center">
              <v-chip size="small" color="primary" class="mr-2">{{ comparison.pillar_a?.name || $t('oncoco.matrixComparison.fallbacks.pillarA') }}</v-chip>
              <LIcon size="small">mdi-swap-horizontal</LIcon>
              <v-chip size="small" color="secondary" class="ml-2">{{ comparison.pillar_b?.name || $t('oncoco.matrixComparison.fallbacks.pillarB') }}</v-chip>
            </v-card-title>

            <v-card-text>
              <!-- Frobenius Distance -->
              <div class="metric-row mb-3">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    {{ $t('oncoco.matrixComparison.metrics.frobenius.label') }}
                    <sup class="footnote-ref" @click="showFootnote('frobenius')">[1]</sup>
                  </span>
                  <span class="font-weight-bold text-h6">{{ formatNum(comparison.metrics?.frobenius_distance) }}</span>
                </div>
                <v-progress-linear
                  :model-value="Math.min((comparison.metrics?.frobenius_distance || 0) * 100, 100)"
                  height="8"
                  rounded
                  :color="getFrobeniusColor(comparison.metrics?.frobenius_distance || 0)"
                ></v-progress-linear>
                  <div class="text-caption text-medium-emphasis mt-1">
                    {{ getFrobeniusInterpretation(comparison.metrics?.frobenius_distance || 0) }}
                  </div>
                </div>

              <!-- Jensen-Shannon Divergence -->
              <div class="metric-row mb-3" v-if="comparison.metrics">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    {{ $t('oncoco.matrixComparison.metrics.jsd.label') }}
                    <sup class="footnote-ref" @click="showFootnote('jsd')">[2]</sup>
                  </span>
                  <span class="font-weight-bold text-h6">{{ formatNum(comparison.metrics?.mean_jsd) }}</span>
                </div>
                <v-progress-linear
                  :model-value="(comparison.metrics?.mean_jsd || 0) * 100"
                  height="8"
                  rounded
                  :color="getJSDColor(comparison.metrics?.mean_jsd || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ $t('oncoco.matrixComparison.metrics.jsd.max', { value: formatNum(comparison.metrics?.max_jsd) }) }} |
                  {{ getJSDInterpretation(comparison.metrics?.mean_jsd || 0) }}
                </div>
              </div>

              <!-- Permutation Test -->
              <div class="metric-row mb-3" v-if="comparison.statistical_tests?.permutation_test">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    {{ $t('oncoco.matrixComparison.metrics.permutation.label') }}
                    <sup class="footnote-ref" @click="showFootnote('permutation')">[3]</sup>
                  </span>
                  <v-chip
                    :color="getSignificanceColor(comparison.statistical_tests?.permutation_test?.p_value || 1)"
                    size="small"
                  >
                    p = {{ formatNum(comparison.statistical_tests?.permutation_test?.p_value) }}
                  </v-chip>
                </div>
                <div class="text-caption mt-1">
                  <LIcon
                    :color="(comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05 ? 'success' : 'warning'"
                    size="small"
                    class="mr-1"
                  >
                    {{ (comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05 ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </LIcon>
                  {{ (comparison.statistical_tests?.permutation_test?.p_value || 1) < 0.05
                    ? $t('oncoco.matrixComparison.metrics.permutation.significant')
                    : $t('oncoco.matrixComparison.metrics.permutation.notSignificant') }}
                </div>
              </div>

              <!-- Effect Size -->
              <div class="metric-row mb-3" v-if="comparison.effect_size">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    {{ $t('oncoco.matrixComparison.metrics.effect.label') }}
                    <sup class="footnote-ref" @click="showFootnote('effect_size')">[4]</sup>
                  </span>
                  <div class="text-right">
                    <div class="font-weight-bold">{{ formatNum(comparison.effect_size?.normalized_frobenius) }}</div>
                    <div class="text-caption text-medium-emphasis">{{ $t('oncoco.matrixComparison.metrics.effect.normalized') }}</div>
                  </div>
                </div>
                <v-progress-linear
                  :model-value="Math.min((comparison.effect_size?.normalized_frobenius || 0) * 200, 100)"
                  height="8"
                  rounded
                  :color="getEffectSizeColor(comparison.effect_size?.normalized_frobenius || 0)"
                ></v-progress-linear>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ getEffectSizeInterpretation(comparison.effect_size?.normalized_frobenius || 0) }}
                </div>
              </div>

              <!-- Chi-Square Summary -->
              <div class="metric-row mb-3" v-if="comparison.statistical_tests?.chi_square">
                <div class="d-flex align-center justify-space-between">
                  <span class="text-body-2">
                    {{ $t('oncoco.matrixComparison.metrics.chiSquare.label') }}
                    <sup class="footnote-ref" @click="showFootnote('chi_square')">[5]</sup>
                  </span>
                  <v-chip
                    :color="getChiSquareSummaryColorFromStats(comparison.statistical_tests?.chi_square)"
                    size="small"
                  >
                    {{ $t('oncoco.matrixComparison.metrics.chiSquare.summary', {
                      significant: comparison.statistical_tests?.chi_square?.significant_rows || 0,
                      total: comparison.statistical_tests?.chi_square?.total_rows || 0
                    }) }}
                  </v-chip>
                </div>
                <div class="text-caption text-medium-emphasis mt-1">
                  {{ $t('oncoco.matrixComparison.metrics.chiSquare.subtitle') }}
                </div>
              </div>

              <v-divider class="my-3"></v-divider>

              <!-- Outlier Transitions -->
              <div class="metric-row mb-3" v-if="comparison.outlier_transitions">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-body-2 font-weight-bold">
                    <LIcon start size="small">mdi-alert-outline</LIcon>
                    {{ $t('oncoco.matrixComparison.outliers.title') }}
                  </span>
                  <v-chip size="x-small" color="warning" variant="tonal">
                    {{ comparison.outlier_transitions?.length || 0 }}
                  </v-chip>
                </div>
                <v-expansion-panels v-if="comparison.outlier_transitions?.length > 0" variant="accordion" density="compact">
                  <v-expansion-panel>
                  <v-expansion-panel-title class="text-caption py-1">
                      {{ $t('oncoco.matrixComparison.outliers.show') }}
                  </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-list density="compact" class="py-0">
                        <v-list-item
                          v-for="(outlier, oIdx) in comparison.outlier_transitions.slice(0, 10)"
                          :key="oIdx"
                          class="px-0"
                        >
                          <template v-slot:prepend>
                            <LIcon
                              :color="outlier.difference > 0 ? 'success' : 'error'"
                              size="small"
                            >
                              {{ outlier.difference > 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                            </LIcon>
                          </template>
                          <v-list-item-title class="text-caption">
                            {{ outlier.from_label }} -> {{ outlier.to_label }}
                          </v-list-item-title>
                          <template v-slot:append>
                            <span class="text-caption font-weight-bold">
                              z={{ formatNum(outlier.z_score, 2) }}
                            </span>
                          </template>
                        </v-list-item>
                      </v-list>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
                <div v-else class="text-caption text-medium-emphasis">
                  {{ $t('oncoco.matrixComparison.outliers.empty') }}
                </div>
              </div>

              <!-- Missing Transitions -->
              <div class="metric-row" v-if="comparison.missing_transitions">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-body-2 font-weight-bold">
                    <LIcon start size="small">mdi-help-circle-outline</LIcon>
                    {{ $t('oncoco.matrixComparison.missing.title') }}
                  </span>
                  <div>
                    <v-chip size="x-small" color="primary" variant="tonal" class="mr-1">
                      {{ $t('oncoco.matrixComparison.missing.onlyInA', { count: comparison.missing_transitions?.missing_in_A?.length || 0 }) }}
                    </v-chip>
                    <v-chip size="x-small" color="secondary" variant="tonal">
                      {{ $t('oncoco.matrixComparison.missing.onlyInB', { count: comparison.missing_transitions?.missing_in_B?.length || 0 }) }}
                    </v-chip>
                  </div>
                </div>
                <v-expansion-panels v-if="(comparison.missing_transitions?.missing_in_A?.length || 0) > 0 || (comparison.missing_transitions?.missing_in_B?.length || 0) > 0" variant="accordion" density="compact">
                  <v-expansion-panel>
                    <v-expansion-panel-title class="text-caption py-1">
                      {{ $t('oncoco.matrixComparison.missing.show') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-if="comparison.missing_transitions?.missing_in_A?.length > 0" class="mb-2">
                        <div class="text-caption font-weight-bold text-primary">{{ $t('oncoco.matrixComparison.missing.onlyIn', { name: comparison.pillar_b?.name || 'B' }) }}</div>
                        <v-chip
                          v-for="(trans, tIdx) in comparison.missing_transitions.missing_in_A.slice(0, 5)"
                          :key="'a-' + tIdx"
                          size="x-small"
                          class="ma-1"
                          variant="outlined"
                        >
                          {{ trans.from_label }} -> {{ trans.to_label }}
                        </v-chip>
                        <span v-if="comparison.missing_transitions.missing_in_A.length > 5" class="text-caption">
                          {{ $t('oncoco.matrixComparison.missing.more', { count: comparison.missing_transitions.missing_in_A.length - 5 }) }}
                        </span>
                      </div>
                      <div v-if="comparison.missing_transitions?.missing_in_B?.length > 0">
                        <div class="text-caption font-weight-bold text-secondary">{{ $t('oncoco.matrixComparison.missing.onlyIn', { name: comparison.pillar_a?.name || 'A' }) }}</div>
                        <v-chip
                          v-for="(trans, tIdx) in comparison.missing_transitions.missing_in_B.slice(0, 5)"
                          :key="'b-' + tIdx"
                          size="x-small"
                          class="ma-1"
                          variant="outlined"
                        >
                          {{ trans.from_label }} -> {{ trans.to_label }}
                        </v-chip>
                        <span v-if="comparison.missing_transitions.missing_in_B.length > 5" class="text-caption">
                          {{ $t('oncoco.matrixComparison.missing.more', { count: comparison.missing_transitions.missing_in_B.length - 5 }) }}
                        </span>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
                <div v-else class="text-caption text-medium-emphasis">
                  {{ $t('oncoco.matrixComparison.missing.none') }}
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Footnotes -->
      <v-card variant="tonal" class="mt-4" color="surface-variant">
        <v-card-text class="text-caption">
          <div class="font-weight-bold mb-2">{{ $t('oncoco.matrixComparison.footnotes.title') }}</div>
          <div>{{ $t('oncoco.matrixComparison.footnotes.items.frobenius') }}</div>
          <div>{{ $t('oncoco.matrixComparison.footnotes.items.jsd') }}</div>
          <div>{{ $t('oncoco.matrixComparison.footnotes.items.permutation') }}</div>
          <div>{{ $t('oncoco.matrixComparison.footnotes.items.effectSize') }}</div>
          <div>{{ $t('oncoco.matrixComparison.footnotes.items.chiSquare') }}</div>
        </v-card-text>
      </v-card>
    </template>

    <!-- Empty State -->
    <v-alert v-if="!metricsData && !loading && !error" type="info" variant="tonal">
      {{ $t('oncoco.matrixComparison.empty') }}
    </v-alert>

    <!-- Methodology Dialog -->
    <v-dialog v-model="showMethodologyDialog" max-width="900" scrollable>
      <v-card class="methodology-dialog-card">
        <v-card-title class="d-flex align-center">
          <LIcon start>mdi-book-open-variant</LIcon>
          {{ $t('oncoco.matrixComparison.methodology.title') }}
          <v-spacer></v-spacer>
          <v-btn icon variant="text" @click="showMethodologyDialog = false">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </v-card-title>

        <v-card-text>
          <v-expansion-panels variant="accordion">
            <!-- Frobenius Distance -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="primary">mdi-matrix</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.frobenius.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.frobenius.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.formula') }}</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\|A - B\|_F = \sqrt{\sum_{i,j} (A_{ij} - B_{ij})^2}" :display-mode="true" />
                  </div>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.frobenius.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.frobenius.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.frobenius.examples.item2') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.frobenius.examples.item3') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.interpretation') }}</h4>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.frobenius.interpretation.verySimilar') }}</v-chip>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.frobenius.interpretation.moderate') }}</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.frobenius.interpretation.distinct') }}</v-chip>
                  <v-chip color="error" size="small">{{ $t('oncoco.matrixComparison.methodology.frobenius.interpretation.strong') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.frobenius.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Jensen-Shannon Divergence -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="secondary">mdi-chart-bell-curve</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.jsd.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.jsd.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.formula') }}</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\text{JSD}(P \| Q) = \frac{1}{2} \text{KL}(P \| M) + \frac{1}{2} \text{KL}(Q \| M)" :display-mode="true" />
                    <div class="formula-note">{{ $t('oncoco.matrixComparison.methodology.jsd.formulaNote') }} <KatexFormula formula="M = \frac{1}{2}(P + Q)" /></div>
                    <KatexFormula formula="\text{KL}(P \| Q) = \sum_i P_i \cdot \log_2 \left( \frac{P_i}{Q_i} \right)" :display-mode="true" />
                  </div>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.jsd.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.jsd.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.jsd.examples.item2') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.jsd.examples.item3') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.interpretation') }}</h4>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.jsd.interpretation.verySimilar') }}</v-chip>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.jsd.interpretation.moderate') }}</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.jsd.interpretation.distinct') }}</v-chip>
                  <v-chip color="error" size="small">{{ $t('oncoco.matrixComparison.methodology.jsd.interpretation.strong') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.jsd.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Permutation Test -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="info">mdi-shuffle-variant</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.permutation.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.permutation.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.permutation.method') }}</h4>
                  <ol>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.steps.step1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.steps.step2') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.steps.step3') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.steps.step4') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.steps.step5') }}</li>
                  </ol>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.permutation.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.permutation.examples.item2') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.interpretation') }}</h4>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.permutation.interpretation.high') }}</v-chip>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.permutation.interpretation.significant') }}</v-chip>
                  <v-chip color="warning" size="small">{{ $t('oncoco.matrixComparison.methodology.permutation.interpretation.notSignificant') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.permutation.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Effect Size -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="warning">mdi-arrow-expand-horizontal</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.effect.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.effect.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.effect.normalizedTitle') }}</h4>
                  <div class="formula-box">
                    <KatexFormula formula="d_{\text{norm}} = \frac{\|A - B\|_F}{\sqrt{n \cdot m}}" :display-mode="true" />
                    <div class="formula-note">{{ $t('oncoco.matrixComparison.methodology.effect.normalizedNote') }}</div>
                  </div>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.effect.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.effect.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.effect.examples.item2') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.effect.examples.item3') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.effect.interpretationTitle') }}</h4>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.effect.interpretation.small') }}</v-chip>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.effect.interpretation.medium') }}</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.effect.interpretation.large') }}</v-chip>
                  <v-chip color="error" size="small">{{ $t('oncoco.matrixComparison.methodology.effect.interpretation.veryLarge') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.effect.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Chi-Square Test -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="error">mdi-chart-bar</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.chiSquare.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.chiSquare.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.formula') }}</h4>
                  <div class="formula-box">
                    <KatexFormula formula="\chi^2 = \sum_j \frac{(O_j - E_j)^2}{E_j}" :display-mode="true" />
                    <div class="formula-note">{{ $t('oncoco.matrixComparison.methodology.chiSquare.formulaNote') }}</div>
                  </div>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.chiSquare.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.chiSquare.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.chiSquare.examples.item2') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.interpretation') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.chiSquare.interpretationIntro') }}</p>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.chiSquare.interpretation.few') }}</v-chip>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.chiSquare.interpretation.moderate') }}</v-chip>
                  <v-chip color="warning" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.chiSquare.interpretation.many') }}</v-chip>
                  <v-chip color="error" size="small">{{ $t('oncoco.matrixComparison.methodology.chiSquare.interpretation.veryMany') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.chiSquare.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>

            <!-- Laplace Smoothing -->
            <v-expansion-panel>
              <v-expansion-panel-title>
                <LIcon start color="purple">mdi-tune</LIcon>
                {{ $t('oncoco.matrixComparison.methodology.laplace.title') }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="methodology-content">
                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.whatIs') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.laplace.whatIs') }}</p>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.formula') }}</h4>
                  <div class="formula-box">
                    <KatexFormula formula="P(y|x) = \frac{\text{count}(x,y) + \alpha}{\sum_z \text{count}(x,z) + \alpha \cdot |Z|}" :display-mode="true" />
                    <div class="formula-note">{{ $t('oncoco.matrixComparison.methodology.laplace.formulaNote') }} <KatexFormula formula="\alpha" /></div>
                  </div>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.example') }}</h4>
                  <p>{{ $t('oncoco.matrixComparison.methodology.laplace.exampleIntro') }}</p>
                  <ul>
                    <li>{{ $t('oncoco.matrixComparison.methodology.laplace.examples.item1') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.laplace.examples.item2') }}</li>
                    <li>{{ $t('oncoco.matrixComparison.methodology.laplace.examples.item3') }}</li>
                  </ul>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.laplace.recommended.title') }}</h4>
                  <v-chip color="info" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.laplace.recommended.alphaZero') }}</v-chip>
                  <v-chip color="success" size="small" class="mr-2">{{ $t('oncoco.matrixComparison.methodology.laplace.recommended.alphaOne') }}</v-chip>
                  <v-chip color="warning" size="small">{{ $t('oncoco.matrixComparison.methodology.laplace.recommended.alphaHigh') }}</v-chip>

                  <h4>{{ $t('oncoco.matrixComparison.methodology.common.source') }}</h4>
                  <p class="text-caption">{{ $t('oncoco.matrixComparison.methodology.laplace.source') }}</p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showMethodologyDialog = false">{{ $t('common.close') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Footnote Snackbar -->
    <v-snackbar v-model="showFootnoteSnackbar" :timeout="5000" location="bottom">
      {{ footnoteText }}
      <template v-slot:actions>
        <v-btn variant="text" @click="showFootnoteSnackbar = false">{{ $t('common.close') }}</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import KatexFormula from '@/components/common/KatexFormula.vue';

const props = defineProps({
  analysisId: {
    type: [Number, String],
    required: true
  },
  hideHeader: {
    type: Boolean,
    default: false
  }
});

const { t } = useI18n();

// State
const loading = ref(false);
const error = ref(null);
const metricsData = ref(null);
const level = ref('level2');
const smoothing = ref(1.0);
const permutations = ref(1000);
const levelOptions = computed(() => [
  { title: t('oncoco.results.levelOptions.level2'), value: 'level2' },
  { title: t('oncoco.results.levelOptions.full'), value: 'full' }
]);

// Dialog States
const showMethodologyDialog = ref(false);
const showFootnoteSnackbar = ref(false);
const footnoteText = ref('');

// Debounce timer
let debounceTimer = null;

// Footnote references
const footnotes = computed(() => ({
  frobenius: t('oncoco.matrixComparison.footnotes.items.frobenius'),
  jsd: t('oncoco.matrixComparison.footnotes.items.jsd'),
  permutation: t('oncoco.matrixComparison.footnotes.items.permutation'),
  effect_size: t('oncoco.matrixComparison.footnotes.items.effectSize'),
  chi_square: t('oncoco.matrixComparison.footnotes.items.chiSquare')
}));

// Safe number formatting helper
const formatNum = (value, decimals = 4) => {
  if (value === undefined || value === null || isNaN(value)) return '-';
  return Number(value).toFixed(decimals);
};

// Load Metrics
const loadMetrics = async () => {
  loading.value = true;
  error.value = null;

  try {
    const params = new URLSearchParams();
    params.append('level', level.value);
    params.append('smoothing', smoothing.value);
    params.append('n_permutations', permutations.value);

    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/oncoco/analyses/${props.analysisId}/matrix-comparison?${params}`
    );
    metricsData.value = response.data;
  } catch (err) {
    console.error('Fehler beim Laden der Metriken:', err);
    error.value = err.response?.data?.error || t('oncoco.matrixComparison.errors.loadFailed');
  } finally {
    loading.value = false;
  }
};

// Debounced load
const debouncedLoadMetrics = () => {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    loadMetrics();
  }, 500);
};

// Show footnote
const showFootnote = (key) => {
  footnoteText.value = footnotes.value[key] || '';
  showFootnoteSnackbar.value = true;
};

// Color helpers
const getFrobeniusColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.4) return 'info';
  if (value < 0.6) return 'warning';
  return 'error';
};

const getFrobeniusInterpretation = (value) => {
  if (value < 0.2) return t('oncoco.matrixComparison.interpretation.frobenius.verySimilar');
  if (value < 0.4) return t('oncoco.matrixComparison.interpretation.frobenius.moderate');
  if (value < 0.6) return t('oncoco.matrixComparison.interpretation.frobenius.distinct');
  return t('oncoco.matrixComparison.interpretation.frobenius.strong');
};

const getJSDColor = (value) => {
  if (value < 0.1) return 'success';
  if (value < 0.3) return 'info';
  if (value < 0.5) return 'warning';
  return 'error';
};

const getJSDInterpretation = (value) => {
  if (value < 0.1) return t('oncoco.matrixComparison.interpretation.jsd.verySimilar');
  if (value < 0.3) return t('oncoco.matrixComparison.interpretation.jsd.moderate');
  if (value < 0.5) return t('oncoco.matrixComparison.interpretation.jsd.distinct');
  return t('oncoco.matrixComparison.interpretation.jsd.strong');
};

const getSignificanceColor = (pValue) => {
  if (pValue < 0.01) return 'error';
  if (pValue < 0.05) return 'warning';
  return 'success';
};

const getEffectSizeColor = (value) => {
  if (value < 0.2) return 'success';
  if (value < 0.5) return 'info';
  if (value < 0.8) return 'warning';
  return 'error';
};

const getEffectSizeInterpretation = (value) => {
  if (value < 0.2) return t('oncoco.matrixComparison.interpretation.effect.small');
  if (value < 0.5) return t('oncoco.matrixComparison.interpretation.effect.medium');
  if (value < 0.8) return t('oncoco.matrixComparison.interpretation.effect.large');
  return t('oncoco.matrixComparison.interpretation.effect.veryLarge');
};

const getChiSquareSignificantCount = (chiSquare) => {
  if (!chiSquare) return 0;
  return Object.values(chiSquare).filter(v => v?.p_value < 0.05).length;
};

const getChiSquareSummaryColor = (chiSquare) => {
  if (!chiSquare) return 'grey';
  const total = Object.keys(chiSquare).length;
  if (total === 0) return 'grey';
  const significant = getChiSquareSignificantCount(chiSquare);
  const ratio = significant / total;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};

// New version that takes the chi_square object from statistical_tests
const getChiSquareSummaryColorFromStats = (chiSquareStats) => {
  if (!chiSquareStats) return 'grey';
  const { significant_rows, total_rows } = chiSquareStats;
  if (!total_rows || total_rows === 0) return 'grey';
  const ratio = significant_rows / total_rows;
  if (ratio < 0.2) return 'success';
  if (ratio < 0.4) return 'info';
  if (ratio < 0.6) return 'warning';
  return 'error';
};

// Load on mount
onMounted(() => {
  loadMetrics();
});
</script>

<style scoped>
.matrix-comparison-metrics {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}

/* Methodology Dialog - ensure solid background */
.methodology-dialog-card {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.metric-row {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
  padding-bottom: 8px;
}

.metric-row:last-child {
  border-bottom: none;
}

/* Fix card overlap in grid */
:deep(.v-row) {
  margin: -8px;
}

:deep(.v-col) {
  padding: 8px;
  min-width: 0; /* Allow shrinking */
}

/* Ensure cards don't overflow */
:deep(.v-card) {
  overflow: hidden;
  word-wrap: break-word;
}

.footnote-ref {
  cursor: pointer;
  color: rgb(var(--v-theme-primary));
  font-size: 0.7em;
  vertical-align: super;
}

.footnote-ref:hover {
  text-decoration: underline;
}

.methodology-content h4 {
  margin-top: 16px;
  margin-bottom: 8px;
  color: rgb(var(--v-theme-primary));
}

.methodology-content h4:first-child {
  margin-top: 0;
}

.methodology-content p {
  margin-bottom: 8px;
}

.methodology-content ul,
.methodology-content ol {
  margin-bottom: 12px;
  padding-left: 20px;
}

.methodology-content li {
  margin-bottom: 4px;
}

.formula-box {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  padding: 16px 20px;
  border-radius: 8px;
  margin: 12px 0;
  overflow-x: auto;
  border-left: 3px solid rgb(var(--v-theme-primary));
  text-align: center;
}

/* KaTeX specific styling */
.formula-box :deep(.katex) {
  font-size: 1.2em;
  color: rgba(var(--v-theme-on-surface), 0.95);
}

.formula-note {
  font-size: 0.9em;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-top: 8px;
  text-align: center;
}

.formula-note :deep(.katex) {
  font-size: 1em;
}
</style>
