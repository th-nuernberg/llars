<template>
  <div class="evaluation-tab">
    <!-- Summary Cards -->
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(176, 202, 151, 0.15);">
          <LIcon color="#b0ca97" size="24">mdi-check-circle-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.totalEvaluations }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.totalEvaluations') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(136, 196, 200, 0.15);">
          <LIcon color="#88c4c8" size="24">mdi-account-multiple-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.humanEvaluators }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.humanEvaluators') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(196, 160, 212, 0.15);">
          <LIcon color="#c4a0d4" size="24">mdi-robot-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.llmEvaluators }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.llmEvaluators') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(209, 188, 138, 0.15);">
          <LIcon color="#D1BC8A" size="24">mdi-percent</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.agreementRate }}%</span>
          <span class="summary-label">{{ $t('scenarioManager.results.agreementRate') }}</span>
        </div>
      </div>
    </div>

    <!-- Metrics & Results Section -->
    <div class="section-card metrics-results-section">
      <div class="section-header">
        <div class="section-title">
          <LIcon color="success" class="mr-2">mdi-chart-bar</LIcon>
          <h3>{{ $t('scenarioManager.evaluation.metricsResults') }}</h3>
        </div>
        <div class="header-actions">
          <!-- Evaluator Type Filter Toggle -->
          <v-btn-toggle
            v-model="evaluatorTypeFilter"
            mandatory
            density="compact"
            class="evaluator-filter-toggle"
          >
            <v-btn value="all" size="small">
              <LIcon start size="16">mdi-account-group</LIcon>
              {{ $t('scenarioManager.evaluation.filter.all') }}
            </v-btn>
            <v-btn value="human" size="small">
              <LIcon start size="16">mdi-account</LIcon>
              {{ $t('scenarioManager.evaluation.filter.human') }}
            </v-btn>
            <v-btn value="llm" size="small">
              <LIcon start size="16">mdi-robot</LIcon>
              {{ $t('scenarioManager.evaluation.filter.llm') }}
            </v-btn>
          </v-btn-toggle>

          <v-menu>
            <template #activator="{ props }">
              <LBtn variant="secondary" size="small" v-bind="props">
                <LIcon start size="16">mdi-download</LIcon>
                {{ $t('scenarioManager.results.export') }}
              </LBtn>
            </template>
            <v-list density="compact">
              <v-list-item @click="exportResults('json')">
                <template #prepend>
                  <LIcon size="18" class="mr-2">mdi-code-json</LIcon>
                </template>
                <v-list-item-title>JSON</v-list-item-title>
              </v-list-item>
              <v-list-item @click="exportResults('csv')">
                <template #prepend>
                  <LIcon size="18" class="mr-2">mdi-file-delimited</LIcon>
                </template>
                <v-list-item-title>CSV</v-list-item-title>
              </v-list-item>
              <v-list-item @click="exportResults('xlsx')">
                <template #prepend>
                  <LIcon size="18" class="mr-2">mdi-file-excel</LIcon>
                </template>
                <v-list-item-title>Excel</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>
      </div>

      <!-- Agreement Metrics -->
      <div class="metrics-section" v-if="hasMetrics">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.agreementMetrics') }}
          <LTooltip :text="$t('scenarioManager.tooltips.agreementMetrics')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>
        <div class="metrics-grid">
          <!-- Cohen's Kappa (Rating, Classification) -->
          <div class="metric-item" v-if="showKappa && liveAgreementMetrics?.kappa !== null && liveAgreementMetrics?.kappa !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>Cohen's Kappa (κ)</strong>
                  <p>{{ $t('scenarioManager.tooltips.cohensKappa') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0: {{ $t('scenarioManager.tooltips.interpretation.worseThanChance') }}</div>
                    <div>0.00-0.20: {{ $t('scenarioManager.tooltips.interpretation.slight') }}</div>
                    <div>0.21-0.40: {{ $t('scenarioManager.tooltips.interpretation.fair') }}</div>
                    <div>0.41-0.60: {{ $t('scenarioManager.tooltips.interpretation.moderate') }}</div>
                    <div>0.61-0.80: {{ $t('scenarioManager.tooltips.interpretation.substantial') }}</div>
                    <div>0.81-1.00: {{ $t('scenarioManager.tooltips.interpretation.almostPerfect') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getMetricClass(liveAgreementMetrics.kappa)">
                  {{ liveAgreementMetrics.kappa?.toFixed(3) }}
                </span>
                <span class="metric-label">Cohen's κ <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
                <span class="metric-interpretation">{{ getKappaInterpretation(liveAgreementMetrics.kappa) }}</span>
              </div>
            </LTooltip>
          </div>

          <!-- Krippendorff's Alpha (Ranking, Rating, Classification) -->
          <div class="metric-item" v-if="showAlpha && liveAgreementMetrics?.alpha !== null && liveAgreementMetrics?.alpha !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>Krippendorff's Alpha (α)</strong>
                  <p>{{ $t('scenarioManager.tooltips.krippendorffAlpha') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0: {{ $t('scenarioManager.tooltips.interpretation.worseThanChance') }}</div>
                    <div>0.00-0.40: {{ $t('scenarioManager.tooltips.interpretation.poor') }}</div>
                    <div>0.40-0.67: {{ $t('scenarioManager.tooltips.interpretation.tentative') }}</div>
                    <div>0.67-0.80: {{ $t('scenarioManager.tooltips.interpretation.acceptable') }}</div>
                    <div>≥ 0.80: {{ $t('scenarioManager.tooltips.interpretation.reliable') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getMetricClass(liveAgreementMetrics.alpha)">
                  {{ liveAgreementMetrics.alpha?.toFixed(3) }}
                </span>
                <span class="metric-label">Krippendorff's α <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
                <span class="metric-interpretation">{{ liveAgreementMetrics.interpretation || '' }}</span>
              </div>
            </LTooltip>
          </div>

          <!-- Fleiss' Kappa (Ranking, Rating) -->
          <div class="metric-item" v-if="showFleiss && liveAgreementMetrics?.fleiss !== null && liveAgreementMetrics?.fleiss !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>Fleiss' Kappa (κ)</strong>
                  <p>{{ $t('scenarioManager.tooltips.fleissKappa') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0: {{ $t('scenarioManager.tooltips.interpretation.worseThanChance') }}</div>
                    <div>0.00-0.20: {{ $t('scenarioManager.tooltips.interpretation.slight') }}</div>
                    <div>0.21-0.40: {{ $t('scenarioManager.tooltips.interpretation.fair') }}</div>
                    <div>0.41-0.60: {{ $t('scenarioManager.tooltips.interpretation.moderate') }}</div>
                    <div>0.61-0.80: {{ $t('scenarioManager.tooltips.interpretation.substantial') }}</div>
                    <div>0.81-1.00: {{ $t('scenarioManager.tooltips.interpretation.almostPerfect') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getMetricClass(liveAgreementMetrics.fleiss)">
                  {{ liveAgreementMetrics.fleiss?.toFixed(3) }}
                </span>
                <span class="metric-label">Fleiss' κ <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
                <span class="metric-interpretation">{{ getKappaInterpretation(liveAgreementMetrics.fleiss) }}</span>
              </div>
            </LTooltip>
          </div>

          <!-- Accuracy (Classification, Comparison only) -->
          <div class="metric-item" v-if="showAccuracy && liveAgreementMetrics?.accuracy !== null && liveAgreementMetrics?.accuracy !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.results.accuracy') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.percentAgreement') }}</p>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getAccuracyClass(liveAgreementMetrics.accuracy)">
                  {{ liveAgreementMetrics.accuracy }}%
                </span>
                <span class="metric-label">{{ $t('scenarioManager.results.accuracy') }} <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>

          <!-- ICC (Intraclass Correlation Coefficient) - Rating only -->
          <div class="metric-item" v-if="showICC && liveAgreementMetrics?.icc !== null && liveAgreementMetrics?.icc !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.icc.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.icc.description') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0.50: {{ $t('scenarioManager.tooltips.icc.poor') }}</div>
                    <div>0.50-0.75: {{ $t('scenarioManager.tooltips.icc.moderate') }}</div>
                    <div>0.75-0.90: {{ $t('scenarioManager.tooltips.icc.good') }}</div>
                    <div>≥ 0.90: {{ $t('scenarioManager.tooltips.icc.excellent') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getICCClass(liveAgreementMetrics.icc)">
                  {{ liveAgreementMetrics.icc?.toFixed(3) }}
                </span>
                <span class="metric-label">ICC <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
                <span class="metric-interpretation">{{ liveAgreementMetrics.iccInterpretation || '' }}</span>
              </div>
            </LTooltip>
          </div>

          <!-- Kendall's W (Coefficient of Concordance) - Ranking only -->
          <div class="metric-item" v-if="showKendallW && liveAgreementMetrics?.kendallW !== null && liveAgreementMetrics?.kendallW !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.kendallW.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.kendallW.description') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0.30: {{ $t('scenarioManager.tooltips.kendallW.weak') }}</div>
                    <div>0.30-0.50: {{ $t('scenarioManager.tooltips.kendallW.moderate') }}</div>
                    <div>0.50-0.70: {{ $t('scenarioManager.tooltips.kendallW.substantial') }}</div>
                    <div>0.70-0.90: {{ $t('scenarioManager.tooltips.kendallW.high') }}</div>
                    <div>≥ 0.90: {{ $t('scenarioManager.tooltips.kendallW.veryHigh') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getKendallWClass(liveAgreementMetrics.kendallW)">
                  {{ liveAgreementMetrics.kendallW?.toFixed(3) }}
                </span>
                <span class="metric-label">Kendall's W <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
                <span class="metric-interpretation">{{ liveAgreementMetrics.kendallWInterpretation || '' }}</span>
              </div>
            </LTooltip>
          </div>

          <!-- Kendall's Tau - Ranking only -->
          <div class="metric-item" v-if="showKendallTau && liveAgreementMetrics?.kendall !== null && liveAgreementMetrics?.kendall !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>Kendall's Tau (τ)</strong>
                  <p>{{ $t('scenarioManager.tooltips.kendallTau.description') }}</p>
                  <div class="tooltip-scale">
                    <div>-1.0: {{ $t('scenarioManager.tooltips.interpretation.perfectNegative') }}</div>
                    <div>0: {{ $t('scenarioManager.tooltips.interpretation.noCorrelation') }}</div>
                    <div>+1.0: {{ $t('scenarioManager.tooltips.interpretation.perfectPositive') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getCorrelationClass(liveAgreementMetrics.kendall)">
                  {{ liveAgreementMetrics.kendall?.toFixed(3) }}
                </span>
                <span class="metric-label">Kendall's τ <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>

          <!-- MAE (Mean Absolute Error) - Rating only -->
          <div class="metric-item" v-if="showMAE && liveAgreementMetrics?.mae !== null && liveAgreementMetrics?.mae !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.mae.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.mae.description') }}</p>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value error-metric">
                  {{ liveAgreementMetrics.mae?.toFixed(3) }}
                </span>
                <span class="metric-label">MAE <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>

          <!-- RMSE (Root Mean Squared Error) - Rating only -->
          <div class="metric-item" v-if="showRMSE && liveAgreementMetrics?.rmse !== null && liveAgreementMetrics?.rmse !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.rmse.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.rmse.description') }}</p>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value error-metric">
                  {{ liveAgreementMetrics.rmse?.toFixed(3) }}
                </span>
                <span class="metric-label">RMSE <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>

          <!-- Macro F1 Score - Classification only -->
          <div class="metric-item" v-if="showF1Scores && liveAgreementMetrics?.macroF1 !== null && liveAgreementMetrics?.macroF1 !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.macroF1.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.macroF1.description') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0.50: {{ $t('scenarioManager.tooltips.f1.poor') }}</div>
                    <div>0.50-0.70: {{ $t('scenarioManager.tooltips.f1.moderate') }}</div>
                    <div>0.70-0.85: {{ $t('scenarioManager.tooltips.f1.good') }}</div>
                    <div>≥ 0.85: {{ $t('scenarioManager.tooltips.f1.excellent') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getF1Class(liveAgreementMetrics.macroF1)">
                  {{ liveAgreementMetrics.macroF1?.toFixed(3) }}
                </span>
                <span class="metric-label">Macro F1 <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>

          <!-- Micro F1 Score - Classification only -->
          <div class="metric-item" v-if="showF1Scores && liveAgreementMetrics?.microF1 !== null && liveAgreementMetrics?.microF1 !== undefined">
            <LTooltip location="top">
              <template #content>
                <div class="tooltip-content">
                  <strong>{{ $t('scenarioManager.tooltips.microF1.title') }}</strong>
                  <p>{{ $t('scenarioManager.tooltips.microF1.description') }}</p>
                  <div class="tooltip-scale">
                    <div>&lt; 0.50: {{ $t('scenarioManager.tooltips.f1.poor') }}</div>
                    <div>0.50-0.70: {{ $t('scenarioManager.tooltips.f1.moderate') }}</div>
                    <div>0.70-0.85: {{ $t('scenarioManager.tooltips.f1.good') }}</div>
                    <div>≥ 0.85: {{ $t('scenarioManager.tooltips.f1.excellent') }}</div>
                  </div>
                </div>
              </template>
              <div class="metric-content">
                <span class="metric-value" :class="getF1Class(liveAgreementMetrics.microF1)">
                  {{ liveAgreementMetrics.microF1?.toFixed(3) }}
                </span>
                <span class="metric-label">Micro F1 <v-icon size="12" class="info-icon">mdi-information-outline</v-icon></span>
              </div>
            </LTooltip>
          </div>
        </div>
      </div>

      <!-- Confusion Matrix -->
      <div class="confusion-matrix-section" v-if="isAuthenticityScenario && hasConfusionMatrixData">
        <div class="subsection-header">
          <h4 class="subsection-title">{{ $t('scenarioManager.results.confusionMatrix.title') }}</h4>
          <v-select
            v-model="selectedMatrixEvaluator"
            :items="matrixEvaluatorOptions"
            item-title="name"
            item-value="id"
            density="compact"
            variant="outlined"
            hide-details
            class="evaluator-select"
          />
        </div>
        <ConfusionMatrix
          v-if="currentConfusionMatrix"
          :matrix="currentConfusionMatrix"
          :title="selectedMatrixEvaluator === 'all'
            ? $t('scenarioManager.results.confusionMatrix.aggregated')
            : selectedEvaluatorName"
          :show-controls="true"
          :show-metrics="true"
          :show-legend="false"
          :use-heatmap="true"
        />
      </div>

      <!-- Distribution Chart -->
      <div class="distribution-section" v-if="filteredDistributionData.length > 0">
        <h4 class="subsection-title">{{ $t('scenarioManager.results.distribution') }}</h4>
        <div class="chart-bars">
          <div
            v-for="(item, index) in filteredDistributionData"
            :key="item.label"
            class="bar-container"
          >
            <div class="bar-label">{{ item.label }}</div>
            <div class="bar-wrapper">
              <div
                class="bar-fill"
                :style="{
                  width: item.percentage + '%',
                  backgroundColor: getBarColor(index)
                }"
              >
                <span class="bar-value" v-if="item.percentage > 15">{{ item.count }}</span>
              </div>
              <span class="bar-value outside" v-if="item.percentage <= 15">{{ item.count }}</span>
            </div>
            <div class="bar-percentage">{{ item.percentage }}%</div>
          </div>
        </div>
      </div>

      <!-- DEBUG PANEL - Remove after fixing -->
      <div class="debug-panel">
        <div><strong>DEBUG Dimensions:</strong></div>
        <div>dimensions.length: {{ dimensions.length }}</div>
        <div>dimensions IDs: {{ dimensions.map(d => d.id) }}</div>
        <div>hasDimensionDistribution: {{ hasDimensionDistribution }}</div>
        <div>hasDimensionAverages: {{ hasDimensionAverages }}</div>
        <div style="margin-top: 8px;"><strong>Selection:</strong></div>
        <div>selectedDimension: "{{ selectedDimension }}"</div>
        <div>currentDimensionScale: {{ JSON.stringify(currentDimensionScale) }}</div>
        <div style="margin-top: 8px;"><strong>Data:</strong></div>
        <div>dimensionDistributionMap keys: {{ Object.keys(dimensionDistributionMap) }}</div>
        <div>currentDimensionDistribution: {{ currentDimensionDistribution ? 'HAS DATA (' + currentDimensionDistribution.length + ' items)' : 'NULL' }}</div>
        <div style="margin-top: 8px;"><strong>Raw liveStats:</strong></div>
        <div>ratingDistribution: {{ ratingDistributionDebug }}</div>
        <div>by_dimension count: {{ byDimensionDebugCount }}</div>
        <div>by_dimension IDs: {{ byDimensionDebugIds }}</div>
      </div>

      <!-- Dimension Visualizations Grid (Heatmap + Spider Chart side by side) -->
      <div class="dimension-visualizations-grid" v-if="hasDimensionDistribution || hasDimensionAverages">
        <!-- Per-Dimension Distribution (Heatmap) -->
        <div class="visualization-panel" v-if="hasDimensionDistribution">
          <h4 class="subsection-title">
            {{ $t('scenarioManager.results.dimensionDistribution') }}
            <LTooltip :text="$t('scenarioManager.tooltips.dimensionDistribution')" location="top">
              <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
            </LTooltip>
          </h4>

          <!-- Dimension Selector -->
          <div class="dimension-selector" v-if="dimensionOptions.length > 1">
            <v-select
              v-model="selectedDimension"
              :items="dimensionOptions"
              item-title="name"
              item-value="id"
              density="compact"
              variant="outlined"
              hide-details
              class="dimension-select"
            />
          </div>

          <!-- Dimension Heatmap -->
          <div class="heatmap-container" v-if="currentDimensionDistribution && currentDimensionDistribution.length > 0">
            <div class="heatmap-header">
              <span class="heatmap-label">{{ selectedDimensionName }}</span>
              <span class="heatmap-scale" v-if="currentDimensionScale">
                {{ $t('scenarioManager.results.scale') }}: {{ currentDimensionScale.min }} - {{ currentDimensionScale.max }}
              </span>
            </div>
            <div class="heatmap-grid">
              <div
                v-for="(item, index) in currentDimensionDistribution"
                :key="item.value"
                class="heatmap-cell"
                :style="{ backgroundColor: getHeatmapColor(item.percentage) }"
              >
                <span class="heatmap-value">{{ item.value }}</span>
                <span class="heatmap-count">{{ item.count }}</span>
                <span class="heatmap-percent">{{ item.percentage }}%</span>
              </div>
            </div>
          </div>

          <!-- Empty State Heatmap -->
          <div class="heatmap-container empty-heatmap" v-else-if="selectedDimension && currentDimensionScale">
            <div class="heatmap-header">
              <span class="heatmap-label">{{ selectedDimensionName }}</span>
              <span class="heatmap-scale">
                {{ $t('scenarioManager.results.scale') }}: {{ currentDimensionScale.min }} - {{ currentDimensionScale.max }}
              </span>
            </div>
            <div class="heatmap-grid">
              <div
                v-for="value in getScaleValues(currentDimensionScale)"
                :key="value"
                class="heatmap-cell empty-cell"
              >
                <span class="heatmap-value">{{ value }}</span>
                <span class="heatmap-count">0</span>
                <span class="heatmap-percent">-</span>
              </div>
            </div>
            <p class="no-data-hint">{{ $t('scenarioManager.evaluation.noRatingsYet') }}</p>
          </div>

          <!-- Debug: No dimension selected -->
          <div v-else class="no-data-panel">
            <p class="text-medium-emphasis">
              No dimension data available.
              Selected: {{ selectedDimension || 'none' }},
              Scale: {{ currentDimensionScale ? 'OK' : 'missing' }},
              MapKeys: {{ Object.keys(dimensionDistributionMap).join(', ') || 'empty' }}
            </p>
          </div>
        </div>

        <!-- Dimension Comparison (Spider/Bar Chart) -->
        <div class="visualization-panel" v-if="hasDimensionAverages && dimensions.length >= 1">
          <h4 class="subsection-title">
            {{ $t('scenarioManager.results.dimensionComparison') }}
            <LTooltip :text="$t('scenarioManager.tooltips.spiderChart')" location="top">
              <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
            </LTooltip>
          </h4>

          <!-- Bar Chart for 1-2 dimensions -->
          <div v-if="dimensions.length <= 2" class="dimension-bar-chart">
            <div
              v-for="dim in dimensions"
              :key="dim.id"
              class="dimension-bar-row"
            >
              <div class="dimension-bar-label">{{ dim.name || dim.id }}</div>
              <div class="dimension-bar-container">
                <div
                  v-if="evaluatorTypeFilter !== 'llm'"
                  class="dimension-bar human-bar"
                  :style="{ width: getDimensionBarWidth('human', dim.id) + '%' }"
                >
                  <span class="bar-value-label">{{ getDimensionAverage('human', dim.id)?.toFixed(2) || '-' }}</span>
                </div>
                <div
                  v-if="evaluatorTypeFilter !== 'human'"
                  class="dimension-bar llm-bar"
                  :style="{ width: getDimensionBarWidth('llm', dim.id) + '%' }"
                >
                  <span class="bar-value-label">{{ getDimensionAverage('llm', dim.id)?.toFixed(2) || '-' }}</span>
                </div>
              </div>
              <div class="dimension-bar-scale">
                {{ getDimensionScaleLabel(dim.id) }}
              </div>
            </div>
            <div class="bar-chart-legend">
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'llm'">
                <span class="legend-color" style="background-color: #88c4c8;"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'human'">
                <span class="legend-color" style="background-color: #c4a0d4;"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
              </div>
            </div>
          </div>

          <!-- Spider Chart for 3+ dimensions -->
          <div v-else class="spider-chart-container">
            <svg :viewBox="`0 0 ${spiderSize} ${spiderSize}`" class="spider-chart">
              <circle
                v-for="level in 5"
                :key="'bg-' + level"
                :cx="spiderCenter"
                :cy="spiderCenter"
                :r="(spiderRadius / 5) * level"
                fill="none"
                stroke="rgba(var(--v-theme-on-surface), 0.1)"
                stroke-width="1"
              />
              <line
                v-for="(dim, i) in dimensions"
                :key="'axis-' + i"
                :x1="spiderCenter"
                :y1="spiderCenter"
                :x2="getSpiderPoint(i, 1).x"
                :y2="getSpiderPoint(i, 1).y"
                stroke="rgba(var(--v-theme-on-surface), 0.2)"
                stroke-width="1"
              />
              <polygon
                v-if="evaluatorTypeFilter !== 'llm' && humanSpiderPoints.length > 0"
                :points="humanSpiderPoints.map(p => `${p.x},${p.y}`).join(' ')"
                fill="rgba(136, 196, 200, 0.3)"
                stroke="#88c4c8"
                stroke-width="2"
              />
              <polygon
                v-if="evaluatorTypeFilter !== 'human' && llmSpiderPoints.length > 0"
                :points="llmSpiderPoints.map(p => `${p.x},${p.y}`).join(' ')"
                fill="rgba(196, 160, 212, 0.3)"
                stroke="#c4a0d4"
                stroke-width="2"
              />
              <g v-if="evaluatorTypeFilter !== 'llm'">
                <circle
                  v-for="(point, i) in humanSpiderPoints"
                  :key="'human-point-' + i"
                  :cx="point.x"
                  :cy="point.y"
                  r="4"
                  fill="#88c4c8"
                />
              </g>
              <g v-if="evaluatorTypeFilter !== 'human'">
                <circle
                  v-for="(point, i) in llmSpiderPoints"
                  :key="'llm-point-' + i"
                  :cx="point.x"
                  :cy="point.y"
                  r="4"
                  fill="#c4a0d4"
                />
              </g>
              <text
                v-for="(dim, i) in dimensions"
                :key="'label-' + i"
                :x="getSpiderLabelPoint(i).x"
                :y="getSpiderLabelPoint(i).y"
                class="spider-label"
                text-anchor="middle"
                dominant-baseline="middle"
              >
                {{ dim.name || dim.id }}
              </text>
            </svg>

            <div class="spider-legend">
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'llm'">
                <span class="legend-color" style="background-color: #88c4c8;"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'human'">
                <span class="legend-color" style="background-color: #c4a0d4;"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Dimension Averages Table (full width below) -->
      <div class="dimension-averages-section" v-if="hasDimensionAverages && dimensions.length >= 1">
        <div class="dimension-averages-table">
          <table>
            <thead>
              <tr>
                <th>{{ $t('scenarioManager.results.dimension') }}</th>
                <th v-if="evaluatorTypeFilter !== 'llm'">{{ $t('scenarioManager.evaluation.filter.human') }}</th>
                <th v-if="evaluatorTypeFilter !== 'human'">{{ $t('scenarioManager.evaluation.filter.llm') }}</th>
                <th v-if="evaluatorTypeFilter === 'all'">{{ $t('scenarioManager.results.difference') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="dim in dimensions" :key="dim.id">
                <td>{{ dim.name || dim.id }}</td>
                <td v-if="evaluatorTypeFilter !== 'llm'">
                  {{ getDimensionAverage('human', dim.id)?.toFixed(2) || '-' }}
                </td>
                <td v-if="evaluatorTypeFilter !== 'human'">
                  {{ getDimensionAverage('llm', dim.id)?.toFixed(2) || '-' }}
                </td>
                <td v-if="evaluatorTypeFilter === 'all'" :class="getDifferenceClass(dim.id)">
                  {{ getDimensionDifference(dim.id) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Inter-Rater Agreement Heatmap -->
      <div class="agreement-heatmap-section" v-if="hasPairwiseAgreement">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.interRaterAgreement') }}
          <LTooltip :text="$t('scenarioManager.tooltips.interRaterAgreement')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>

        <div class="agreement-heatmap-container">
          <!-- Heatmap Matrix -->
          <div class="heatmap-matrix">
            <!-- Header row -->
            <div class="heatmap-row header-row">
              <div class="heatmap-cell corner-cell"></div>
              <div
                v-for="evaluator in pairwiseEvaluators"
                :key="'header-' + evaluator.id"
                class="heatmap-cell header-cell"
                :class="{ 'is-llm': evaluator.isLLM }"
              >
                <span class="evaluator-name-short" :title="evaluator.name">
                  {{ getShortName(evaluator.name) }}
                </span>
                <LIcon v-if="evaluator.isLLM" size="12" class="llm-icon">mdi-robot</LIcon>
              </div>
            </div>

            <!-- Data rows -->
            <div
              v-for="(rowEval, rowIndex) in pairwiseEvaluators"
              :key="'row-' + rowEval.id"
              class="heatmap-row"
            >
              <div class="heatmap-cell row-label" :class="{ 'is-llm': rowEval.isLLM }">
                <span class="evaluator-name-short" :title="rowEval.name">
                  {{ getShortName(rowEval.name) }}
                </span>
                <LIcon v-if="rowEval.isLLM" size="12" class="llm-icon">mdi-robot</LIcon>
              </div>
              <div
                v-for="(colEval, colIndex) in pairwiseEvaluators"
                :key="'cell-' + rowEval.id + '-' + colEval.id"
                class="heatmap-cell data-cell"
                :style="{ backgroundColor: getAgreementColor(rowEval.id, colEval.id, rowIndex, colIndex) }"
                :title="getAgreementTooltip(rowEval, colEval, rowIndex, colIndex)"
              >
                <span v-if="rowIndex !== colIndex" class="agreement-value">
                  {{ getAgreementValue(rowEval.id, colEval.id) }}
                </span>
                <span v-else class="diagonal-indicator">-</span>
              </div>
            </div>
          </div>

          <!-- Legend -->
          <div class="heatmap-legend">
            <span class="legend-label">{{ $t('scenarioManager.results.lowAgreement') }}</span>
            <div class="legend-gradient"></div>
            <span class="legend-label">{{ $t('scenarioManager.results.highAgreement') }}</span>
          </div>

          <!-- Legend for evaluator types -->
          <div class="evaluator-type-legend">
            <div class="legend-item">
              <LIcon size="14">mdi-account</LIcon>
              <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
            </div>
            <div class="legend-item">
              <LIcon size="14">mdi-robot</LIcon>
              <span>{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- No Results Yet -->
      <div v-if="!hasMetrics && filteredDistributionData.length === 0" class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-chart-box-outline</LIcon>
        <p>{{ $t('scenarioManager.evaluation.noResultsYet') }}</p>
      </div>
    </div>

    <!-- Remove Evaluator Confirmation -->
    <v-dialog v-model="showRemoveDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="error" class="mr-2">mdi-alert-circle-outline</LIcon>
          {{ $t('scenarioManager.evaluation.removeEvaluator') }}
        </v-card-title>
        <v-card-text>
          {{ $t('scenarioManager.evaluation.removeEvaluatorConfirm', { name: evaluatorToRemove?.model_name || evaluatorToRemove?.model_id }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showRemoveDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" :loading="removingEvaluator" @click="removeEvaluator">
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useLLMEvaluation } from '@/composables/useLLMEvaluation'
import { useLLMModels } from '@/composables/useLLMModels'
import { useScenarioManager } from '../../composables/useScenarioManager'
import LAvatar from '@/components/common/LAvatar.vue'
import ConfusionMatrix from '../ConfusionMatrix.vue'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  },
  liveStats: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['evaluation-complete', 'refresh'])

const { t } = useI18n()
const router = useRouter()
const { exportResults: doExport } = useScenarioManager()

// LLM Models
const {
  selectItems: modelSelectItems,
  loading: modelsLoading,
  fetchModels
} = useLLMModels()

// LLM Evaluation
const {
  results,
  agreementMetrics,
  connectToScenario,
  disconnect,
  startEvaluation: doStartEvaluation,
  stopEvaluation: doStopEvaluation,
  fetchAgreementMetrics
} = useLLMEvaluation()

// State
const selectedModel = ref(null)
const selectedTemplate = ref('default')
const addingEvaluator = ref(false)
const showRemoveDialog = ref(false)
const evaluatorToRemove = ref(null)
const removingEvaluator = ref(false)
const selectedMatrixEvaluator = ref('all')
const evaluatorTypeFilter = ref('all')
const selectedDimension = ref(null)

// Spider chart constants
const spiderSize = 300
const spiderCenter = 150
const spiderRadius = 120

// Prompt templates
const promptTemplates = ref([
  { id: 'default', name: t('scenarioManager.evaluation.templates.standard') },
  { id: 'detailed', name: t('scenarioManager.evaluation.templates.detailed') },
  { id: 'quick', name: t('scenarioManager.evaluation.templates.quick') }
])

// ===== Computed: Evaluators =====

const evaluatorStatsList = computed(() => {
  return props.liveStats?.userStatsList || []
})

const humanEvaluators = computed(() => {
  return evaluatorStatsList.value.filter(u => !u.isLLM)
})

const llmEvaluators = computed(() => {
  const liveList = evaluatorStatsList.value.filter(u => u.isLLM)

  if (liveList.length > 0) {
    return liveList
  }

  // Fallback: Build from scenario's llm_evaluators config
  const configList = props.scenario?.llm_evaluators || []
  if (configList.length === 0) {
    return []
  }

  return configList.map(item => {
    const modelId = typeof item === 'string' ? item : (item.model_id || item.modelId || item.id)
    return {
      id: modelId,
      modelId: modelId,
      name: modelId,
      isLLM: true,
      completed: 0,
      total: props.scenario?.thread_count || 0,
      status: 'idle'
    }
  })
})

// ===== Computed: Summary Stats =====

const summaryStats = computed(() => {
  const users = evaluatorStatsList.value
  const humanCount = users.filter(u => !u.isLLM).length
  const llmCount = users.filter(u => u.isLLM).length
  const totalCompleted = users.reduce((sum, u) => sum + (u.completed || 0), 0)

  const usersWithAccuracy = users.filter(u => u.accuracy !== null && u.accuracy !== undefined)
  const avgAccuracy = usersWithAccuracy.length > 0
    ? Math.round(usersWithAccuracy.reduce((sum, u) => sum + u.accuracy, 0) / usersWithAccuracy.length)
    : 0

  return {
    totalEvaluations: totalCompleted,
    humanEvaluators: humanCount || props.scenario?.user_count || 0,
    llmEvaluators: llmCount || props.scenario?.llm_evaluator_count || 0,
    agreementRate: liveAgreementMetrics.value?.accuracy || avgAccuracy || 0
  }
})

// ===== Computed: Agreement Metrics =====

const liveAgreementMetrics = computed(() => {
  // Merge metrics from both sources:
  // - agreementMetrics: from useLLMEvaluation (full AgreementMetricsService)
  // - liveStats.agreementMetrics: from useScenarioStats (partial, only alpha)
  const fromService = agreementMetrics.value
  const fromStats = props.liveStats?.agreementMetrics

  if (!fromService && !fromStats) return null

  // Prefer full metrics from AgreementMetricsService, fallback to stats
  return {
    // Core agreement metrics
    alpha: fromService?.alpha ?? fromStats?.alpha ?? null,
    kappa: fromService?.kappa ?? fromStats?.kappa ?? null,
    fleiss: fromService?.fleiss ?? fromStats?.fleiss ?? null,
    accuracy: fromService?.accuracy ?? fromStats?.accuracy ?? null,
    interpretation: fromService?.interpretation ?? fromStats?.interpretation ?? null,
    kendall: fromService?.kendall ?? null,
    spearman: fromService?.spearman ?? null,
    // New metrics
    icc: fromService?.icc ?? null,
    iccInterpretation: fromService?.iccInterpretation ?? null,
    kendallW: fromService?.kendallW ?? null,
    kendallWInterpretation: fromService?.kendallWInterpretation ?? null,
    mae: fromService?.mae ?? null,
    rmse: fromService?.rmse ?? null,
    macroF1: fromService?.macroF1 ?? null,
    microF1: fromService?.microF1 ?? null,
    // Metadata
    raterCount: fromService?.raterCount ?? 0,
    itemCount: fromService?.itemCount ?? 0,
    taskType: fromService?.taskType ?? null
  }
})

const hasMetrics = computed(() => {
  const m = liveAgreementMetrics.value
  return m && (
    m.alpha !== null ||
    m.kappa !== null ||
    m.fleiss !== null ||
    m.accuracy !== null ||
    m.icc !== null ||
    m.kendallW !== null ||
    m.kendall !== null ||  // Kendall's Tau
    m.mae !== null ||
    m.rmse !== null ||
    m.macroF1 !== null ||
    m.microF1 !== null
  )
})

// ===== Task-Type Specific Metric Visibility =====
const currentTaskType = computed(() => {
  return liveAgreementMetrics.value?.taskType ||
         props.liveStats?.functionType ||
         props.scenario?.function_type ||
         null
})

// Ranking: Krippendorff's α, Kendall's W, Kendall's τ, Fleiss' κ
const isRankingScenario = computed(() => currentTaskType.value === 'ranking')

// Rating: ICC, Krippendorff's α, MAE, RMSE, Cohen's/Fleiss' κ
const isRatingScenario = computed(() =>
  currentTaskType.value === 'rating' || currentTaskType.value === 'mail_rating'
)

// Classification/Authenticity: Accuracy, F1, Confusion Matrix, Cohen's κ
const isClassificationScenario = computed(() =>
  currentTaskType.value === 'authenticity' ||
  currentTaskType.value === 'text_classification' ||
  currentTaskType.value === 'labeling'
)

// Comparison: Bradley-Terry, Percent Agreement
const isComparisonScenario = computed(() => currentTaskType.value === 'comparison')

// If task type is unknown, show all metrics that have values (fallback mode)
const hasKnownTaskType = computed(() => currentTaskType.value !== null)

// Metric visibility helpers - show if type matches OR if type unknown (fallback)
const showKappa = computed(() =>
  !hasKnownTaskType.value || isClassificationScenario.value || isRatingScenario.value
)
const showAlpha = computed(() =>
  !hasKnownTaskType.value || isRankingScenario.value || isRatingScenario.value || isClassificationScenario.value
)
const showFleiss = computed(() =>
  !hasKnownTaskType.value || isRankingScenario.value || isRatingScenario.value
)
const showAccuracy = computed(() =>
  isClassificationScenario.value || isComparisonScenario.value
)
const showICC = computed(() =>
  !hasKnownTaskType.value || isRatingScenario.value
)
const showKendallW = computed(() =>
  !hasKnownTaskType.value || isRankingScenario.value
)
const showKendallTau = computed(() =>
  !hasKnownTaskType.value || isRankingScenario.value
)
const showMAE = computed(() =>
  !hasKnownTaskType.value || isRatingScenario.value
)
const showRMSE = computed(() =>
  !hasKnownTaskType.value || isRatingScenario.value
)
const showF1Scores = computed(() =>
  !hasKnownTaskType.value || isClassificationScenario.value
)

// ===== Computed: LLM Controls =====

const canAddEvaluator = computed(() => {
  return selectedModel.value && props.scenario?.thread_count > 0
})

const selectedModelCost = computed(() => {
  if (!selectedModel.value) return null
  const model = modelSelectItems.value.find(m => m.id === selectedModel.value)
  return model?.costPer1k || null
})

const costEstimate = computed(() => {
  if (!selectedModelCost.value || !props.scenario?.thread_count) return null
  return (props.scenario.thread_count * 0.5) * selectedModelCost.value
})

// ===== Computed: Confusion Matrix =====

const isAuthenticityScenario = computed(() => {
  const functionType = props.liveStats?.functionType || props.scenario?.function_type
  return functionType === 'authenticity' || functionType === 'classification' || functionType === 'labeling'
})

const hasConfusionMatrixData = computed(() => {
  return evaluatorStatsList.value.some(e =>
    (e.fake_correct !== undefined && e.fake_correct !== null) ||
    (e.real_correct !== undefined && e.real_correct !== null)
  )
})

const aggregatedConfusionMatrix = computed(() => {
  let tp = 0, fp = 0, tn = 0, fn = 0

  evaluatorStatsList.value.forEach(evaluator => {
    tp += evaluator.fake_correct || 0
    fp += evaluator.fake_incorrect || 0
    tn += evaluator.real_correct || 0
    fn += evaluator.real_incorrect || 0
  })

  if (tp + fp + tn + fn === 0) return null

  return { truePositive: tp, falsePositive: fp, trueNegative: tn, falseNegative: fn }
})

function getEvaluatorConfusionMatrix(evaluatorId) {
  const evaluator = evaluatorStatsList.value.find(e => e.id === evaluatorId)
  if (!evaluator) return null

  const tp = evaluator.fake_correct || 0
  const fp = evaluator.fake_incorrect || 0
  const tn = evaluator.real_correct || 0
  const fn = evaluator.real_incorrect || 0

  if (tp + fp + tn + fn === 0) return null

  return { truePositive: tp, falsePositive: fp, trueNegative: tn, falseNegative: fn }
}

const matrixEvaluatorOptions = computed(() => {
  const options = [
    { id: 'all', name: t('scenarioManager.results.confusionMatrix.aggregated') }
  ]

  evaluatorStatsList.value.forEach(evaluator => {
    const hasData = (evaluator.fake_correct || 0) + (evaluator.fake_incorrect || 0) +
                    (evaluator.real_correct || 0) + (evaluator.real_incorrect || 0) > 0

    if (hasData) {
      options.push({
        id: evaluator.id,
        name: evaluator.name || evaluator.username || evaluator.id,
        isLLM: evaluator.isLLM
      })
    }
  })

  return options
})

const currentConfusionMatrix = computed(() => {
  if (selectedMatrixEvaluator.value === 'all') {
    return aggregatedConfusionMatrix.value
  }
  return getEvaluatorConfusionMatrix(selectedMatrixEvaluator.value)
})

const selectedEvaluatorName = computed(() => {
  if (selectedMatrixEvaluator.value === 'all') {
    return t('scenarioManager.results.confusionMatrix.aggregated')
  }
  const evaluator = evaluatorStatsList.value.find(e => e.id === selectedMatrixEvaluator.value)
  return evaluator?.name || evaluator?.username || selectedMatrixEvaluator.value
})

// ===== Computed: Distribution =====

const distributionData = computed(() => {
  // Check for rating distribution (for rating type scenarios)
  const ratingDist = props.liveStats?.ratingDistribution
  if (ratingDist?.all) {
    return ratingDist.all
  }
  // Fall back to general distribution
  if (props.liveStats?.distribution) {
    return props.liveStats.distribution
  }

  const voteCounts = {}
  evaluatorStatsList.value.forEach(evaluator => {
    if (evaluator.votedThreads) {
      evaluator.votedThreads.forEach(thread => {
        const vote = thread.vote || thread.rating || thread.label || 'unknown'
        voteCounts[vote] = (voteCounts[vote] || 0) + 1
      })
    }
  })

  const total = Object.values(voteCounts).reduce((sum, count) => sum + count, 0)
  if (total === 0) return []

  return Object.entries(voteCounts)
    .map(([label, count]) => ({
      label: formatLabel(label),
      count,
      percentage: Math.round((count / total) * 100)
    }))
    .sort((a, b) => b.count - a.count)
})

const barColors = ['#b0ca97', '#88c4c8', '#D1BC8A', '#c4a0d4', '#e8a087', '#98d4bb']

function getBarColor(index) {
  return barColors[index % barColors.length]
}

// ===== Computed: Filtered Distribution Data =====

const filteredDistributionData = computed(() => {
  const ratingDist = props.liveStats?.ratingDistribution

  // Use filtered data based on evaluator type
  if (ratingDist) {
    if (evaluatorTypeFilter.value === 'human' && ratingDist.humans) {
      return ratingDist.humans
    }
    if (evaluatorTypeFilter.value === 'llm' && ratingDist.llms) {
      return ratingDist.llms
    }
    if (ratingDist.all) {
      return ratingDist.all
    }
  }

  // Fallback to distributionData
  return distributionData.value
})

// ===== Computed: Dimensions =====

const dimensions = computed(() => {
  // Get dimensions from scenario config
  const config = props.scenario?.config_json || props.scenario?.config
  const evalConfig = config?.eval_config || {}

  // Dimensions can be at root level or in eval_config
  const configDimensions = config?.dimensions || evalConfig?.dimensions || []

  if (configDimensions.length > 0) {
    return configDimensions.map(d => ({
      id: d.id,
      name: d.name?.de || d.name?.en || d.name || d.id,
      scale: d.scale
    }))
  }

  // Fallback: Get dimensions from rating distribution data
  const byDim = props.liveStats?.ratingDistribution?.by_dimension
  if (byDim && Array.isArray(byDim) && byDim.length > 0) {
    return byDim.map(d => ({
      id: d.dimension_id,
      name: d.dimension_name || d.dimension_id,
      scale: d.scale_min !== undefined ? { min: d.scale_min, max: d.scale_max } : null
    }))
  }

  return []
})

const dimensionOptions = computed(() => {
  return dimensions.value.map(d => ({
    id: d.id,
    name: d.name
  }))
})

const selectedDimensionName = computed(() => {
  const dim = dimensions.value.find(d => d.id === selectedDimension.value)
  return dim?.name || selectedDimension.value || ''
})

// ===== Computed: Per-Dimension Distribution =====

const hasDimensionDistribution = computed(() => {
  // Show if we have rating data OR if dimensions are configured
  const byDim = props.liveStats?.ratingDistribution?.by_dimension
  const hasRatingData = byDim && Array.isArray(byDim) && byDim.length > 0
  const hasConfigDimensions = dimensions.value.length > 0
  return hasRatingData || hasConfigDimensions
})

// Convert by_dimension array to object keyed by dimension_id for easier access
const dimensionDistributionMap = computed(() => {
  const byDim = props.liveStats?.ratingDistribution?.by_dimension
  if (!byDim || !Array.isArray(byDim)) return {}

  const map = {}
  for (const dim of byDim) {
    if (dim.dimension_id) {
      map[dim.dimension_id] = dim
    }
  }
  return map
})

const currentDimensionDistribution = computed(() => {
  if (!selectedDimension.value) return null

  const dimData = dimensionDistributionMap.value[selectedDimension.value]
  if (!dimData) return null

  // Get the right data based on filter
  let data = null
  if (evaluatorTypeFilter.value === 'human') {
    data = dimData.humans || dimData.all
  } else if (evaluatorTypeFilter.value === 'llm') {
    data = dimData.llms || dimData.all
  } else {
    data = dimData.all
  }

  return data
})

const currentDimensionScale = computed(() => {
  // First try from dimension config
  const dim = dimensions.value.find(d => d.id === selectedDimension.value)
  if (dim?.scale) return dim.scale

  // Fallback to distribution data which includes scale_min/scale_max
  const dimData = dimensionDistributionMap.value[selectedDimension.value]
  if (dimData) {
    return {
      min: dimData.scale_min ?? 1,
      max: dimData.scale_max ?? 5
    }
  }

  return { min: 1, max: 5 }
})

// ===== Computed: Dimension Averages =====

const hasDimensionAverages = computed(() => {
  // Show dimension comparison if dimensions are configured (even without data yet)
  return dimensions.value.length > 0
})

function getDimensionAverage(type, dimensionId) {
  const dimData = dimensionDistributionMap.value[dimensionId]
  if (!dimData) return null

  let data = null

  if (type === 'human') {
    data = dimData.humans || []
  } else if (type === 'llm') {
    data = dimData.llms || []
  } else {
    data = dimData.all || []
  }

  if (!data || data.length === 0) return null

  // Calculate weighted average
  let totalWeight = 0
  let weightedSum = 0

  data.forEach(item => {
    const value = parseFloat(item.value)
    const count = item.count || 0
    if (!isNaN(value) && count > 0) {
      weightedSum += value * count
      totalWeight += count
    }
  })

  return totalWeight > 0 ? weightedSum / totalWeight : null
}

function getDimensionDifference(dimensionId) {
  const humanAvg = getDimensionAverage('human', dimensionId)
  const llmAvg = getDimensionAverage('llm', dimensionId)

  if (humanAvg === null || llmAvg === null) return '-'

  const diff = llmAvg - humanAvg
  const sign = diff >= 0 ? '+' : ''
  return `${sign}${diff.toFixed(2)}`
}

function getDifferenceClass(dimensionId) {
  const humanAvg = getDimensionAverage('human', dimensionId)
  const llmAvg = getDimensionAverage('llm', dimensionId)

  if (humanAvg === null || llmAvg === null) return ''

  const diff = Math.abs(llmAvg - humanAvg)
  if (diff < 0.3) return 'diff-small'
  if (diff < 0.7) return 'diff-medium'
  return 'diff-large'
}

// ===== Bar Chart Helpers =====

function getDimensionBarWidth(type, dimensionId) {
  const avg = getDimensionAverage(type, dimensionId)
  if (avg === null) return 0

  // Get scale for this dimension
  const dim = dimensions.value.find(d => d.id === dimensionId)
  const dimData = dimensionDistributionMap.value[dimensionId]

  const min = dim?.scale?.min ?? dimData?.scale_min ?? 1
  const max = dim?.scale?.max ?? dimData?.scale_max ?? 5

  // Calculate percentage of scale
  if (max === min) return 50
  return Math.round(((avg - min) / (max - min)) * 100)
}

function getDimensionScaleLabel(dimensionId) {
  const dim = dimensions.value.find(d => d.id === dimensionId)
  const dimData = dimensionDistributionMap.value[dimensionId]

  const min = dim?.scale?.min ?? dimData?.scale_min ?? 1
  const max = dim?.scale?.max ?? dimData?.scale_max ?? 5

  return `${min}-${max}`
}

function getScaleValues(scale) {
  if (!scale) return [1, 2, 3, 4, 5]
  const min = scale.min ?? 1
  const max = scale.max ?? 5
  const step = scale.step ?? 1
  const values = []
  for (let v = min; v <= max; v += step) {
    values.push(v)
  }
  return values
}

// ===== Spider Chart Helpers =====

function getSpiderPoint(index, value) {
  const count = dimensions.value.length
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2
  const r = spiderRadius * value
  return {
    x: spiderCenter + r * Math.cos(angle),
    y: spiderCenter + r * Math.sin(angle)
  }
}

function getSpiderLabelPoint(index) {
  const count = dimensions.value.length
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2
  const r = spiderRadius + 25
  return {
    x: spiderCenter + r * Math.cos(angle),
    y: spiderCenter + r * Math.sin(angle)
  }
}

function getNormalizedValue(type, dimensionId) {
  const avg = getDimensionAverage(type, dimensionId)
  if (avg === null) return 0

  // Get scale from dimension config or distribution data
  const dim = dimensions.value.find(d => d.id === dimensionId)
  const dimData = dimensionDistributionMap.value[dimensionId]

  const min = dim?.scale?.min ?? dimData?.scale_min ?? 1
  const max = dim?.scale?.max ?? dimData?.scale_max ?? 5

  // Normalize to 0-1 range
  if (max === min) return 0.5  // Avoid division by zero
  return (avg - min) / (max - min)
}

const humanSpiderPoints = computed(() => {
  return dimensions.value.map((dim, i) => {
    const normalizedValue = getNormalizedValue('human', dim.id)
    return getSpiderPoint(i, normalizedValue)
  })
})

const llmSpiderPoints = computed(() => {
  return dimensions.value.map((dim, i) => {
    const normalizedValue = getNormalizedValue('llm', dim.id)
    return getSpiderPoint(i, normalizedValue)
  })
})

// ===== Heatmap Helpers =====

function getHeatmapColor(percentage) {
  // Gradient from light to primary color
  const intensity = percentage / 100
  const r = Math.round(255 - (255 - 176) * intensity)
  const g = Math.round(255 - (255 - 202) * intensity)
  const b = Math.round(255 - (255 - 151) * intensity)
  return `rgb(${r}, ${g}, ${b})`
}

// ===== Pairwise Agreement Heatmap =====

const hasPairwiseAgreement = computed(() => {
  const pairwise = props.liveStats?.pairwiseAgreement
  return pairwise && pairwise.evaluators && pairwise.evaluators.length >= 2
})

const pairwiseEvaluators = computed(() => {
  const pairwise = props.liveStats?.pairwiseAgreement
  if (!pairwise?.evaluators) return []
  // Sort: humans first, then LLMs
  return [...pairwise.evaluators].sort((a, b) => {
    if (a.isLLM === b.isLLM) return a.name.localeCompare(b.name)
    return a.isLLM ? 1 : -1
  })
})

const pairwiseAgreements = computed(() => {
  const pairwise = props.liveStats?.pairwiseAgreement
  return pairwise?.agreements || {}
})

function getAgreementKey(id1, id2) {
  // Keys are stored as "min-max" for consistency
  const str1 = String(id1)
  const str2 = String(id2)
  return str1 < str2 ? `${str1}-${str2}` : `${str2}-${str1}`
}

function getAgreementValue(id1, id2) {
  if (id1 === id2) return '-'
  const key = getAgreementKey(id1, id2)
  const value = pairwiseAgreements.value[key]
  if (value === undefined || value === null) return '-'
  return Math.round(value * 100) + '%'
}

function getAgreementColor(id1, id2, rowIndex, colIndex) {
  if (rowIndex === colIndex) return 'rgba(var(--v-theme-surface-variant), 0.3)'

  const key = getAgreementKey(id1, id2)
  const value = pairwiseAgreements.value[key]

  if (value === undefined || value === null) {
    return 'rgba(var(--v-theme-surface-variant), 0.1)'
  }

  // Gradient: red (low) -> yellow (medium) -> green (high)
  if (value < 0.4) {
    // Red to yellow
    const t = value / 0.4
    const r = 232
    const g = Math.round(160 + (200 - 160) * t)
    const b = Math.round(135 + (100 - 135) * t)
    return `rgba(${r}, ${g}, ${b}, 0.7)`
  } else if (value < 0.7) {
    // Yellow to light green
    const t = (value - 0.4) / 0.3
    const r = Math.round(232 - (232 - 152) * t)
    const g = Math.round(200 - (200 - 212) * t)
    const b = Math.round(100 + (187 - 100) * t)
    return `rgba(${r}, ${g}, ${b}, 0.7)`
  } else {
    // Light green to green
    const t = (value - 0.7) / 0.3
    const r = Math.round(152 - (152 - 98) * t)
    const g = Math.round(212 - (212 - 200) * t)
    const b = Math.round(187 - (187 - 140) * t)
    return `rgba(${r}, ${g}, ${b}, 0.8)`
  }
}

function getAgreementTooltip(eval1, eval2, rowIndex, colIndex) {
  if (rowIndex === colIndex) return eval1.name

  const key = getAgreementKey(eval1.id, eval2.id)
  const value = pairwiseAgreements.value[key]

  if (value === undefined || value === null) {
    return `${eval1.name} / ${eval2.name}: ${t('scenarioManager.results.noOverlap')}`
  }

  const percentage = Math.round(value * 100)
  return `${eval1.name} / ${eval2.name}: ${percentage}% ${t('scenarioManager.results.agreement')}`
}

function getShortName(name) {
  if (!name) return '?'
  // For LLM model names, extract the model part
  if (name.includes('/')) {
    name = name.split('/').pop()
  }
  // Truncate long names
  if (name.length > 8) {
    return name.substring(0, 7) + '...'
  }
  return name
}

function formatLabel(label) {
  const labelMap = {
    'fake': t('scenarioManager.results.labels.fake') || 'Fake',
    'real': t('scenarioManager.results.labels.real') || 'Real',
    'authentic': t('scenarioManager.results.labels.authentic') || 'Authentic',
    'phishing': t('scenarioManager.results.labels.phishing') || 'Phishing',
    'spam': t('scenarioManager.results.labels.spam') || 'Spam',
    'legitimate': t('scenarioManager.results.labels.legitimate') || 'Legitimate'
  }
  return labelMap[label?.toLowerCase()] || String(label).charAt(0).toUpperCase() + String(label).slice(1)
}

// ===== Methods: UI Helpers =====

function getEvaluatorName(evaluator) {
  const modelId = evaluator.modelId || evaluator.model_id || evaluator.id || evaluator.user_id
  const name = evaluator.name || evaluator.model_name || evaluator.username || evaluator.display_name

  const searchId = modelId || name
  if (searchId) {
    const cleanId = String(searchId).replace(/^llm:/, '')
    const model = modelSelectItems.value.find(m =>
      m.id === cleanId || m.id === searchId || m.id?.toLowerCase() === cleanId?.toLowerCase()
    )
    if (model?.name) return model.name
  }

  if (name && name !== modelId) return name
  if (modelId) return formatModelId(String(modelId).replace(/^llm:/, ''))
  if (name) return formatModelId(name)
  return 'Unknown Model'
}

function formatModelId(modelId) {
  if (!modelId) return 'Unknown'
  return modelId.split('/').pop().split(':')[0]
}

function getProviderFromModelId(evaluator) {
  const modelId = evaluator.modelId || evaluator.model_id || evaluator.id
  if (!modelId) return 'Unknown'

  if (modelId.includes('/')) {
    const provider = modelId.split('/')[0]
    return provider.charAt(0).toUpperCase() + provider.slice(1)
  }

  const id = modelId.toLowerCase()
  if (id.includes('gpt') || id.includes('openai')) return 'OpenAI'
  if (id.includes('claude') || id.includes('anthropic')) return 'Anthropic'
  if (id.includes('mistral')) return 'Mistral'
  if (id.includes('llama')) return 'Meta'
  if (id.includes('gemini') || id.includes('google')) return 'Google'

  return 'LLM'
}

function getProgressPercent(evaluator) {
  if (!evaluator.total || evaluator.total === 0) return 0
  return Math.round((evaluator.completed || 0) / evaluator.total * 100)
}

function getProgressClass(evaluator) {
  const percent = getProgressPercent(evaluator)
  if (percent >= 100) return 'completed'
  if (evaluator.status === 'running') return 'running'
  return 'paused'
}

function getStatusVariant(evaluator) {
  if (evaluator.completed >= evaluator.total) return 'success'
  if (evaluator.status === 'running') return 'info'
  if (evaluator.status === 'error') return 'danger'
  return 'warning'
}

function getStatusLabel(evaluator) {
  if (evaluator.completed >= evaluator.total) return t('scenarioManager.evaluation.status.completed')
  if (evaluator.status === 'running') return t('scenarioManager.evaluation.status.running')
  if (evaluator.status === 'error') return t('scenarioManager.evaluation.status.error')
  return t('scenarioManager.evaluation.status.idle')
}

function getMetricClass(value) {
  if (value >= 0.8) return 'excellent'
  if (value >= 0.6) return 'good'
  if (value >= 0.4) return 'moderate'
  return 'poor'
}

function getAccuracyClass(value) {
  if (value >= 80) return 'excellent'
  if (value >= 60) return 'good'
  if (value >= 40) return 'moderate'
  return 'poor'
}

function getKappaInterpretation(kappa) {
  if (kappa === null || kappa === undefined) return '-'
  if (kappa >= 0.8) return t('scenarioManager.results.kappa.excellent')
  if (kappa >= 0.6) return t('scenarioManager.results.kappa.good')
  if (kappa >= 0.4) return t('scenarioManager.results.kappa.moderate')
  if (kappa >= 0.2) return t('scenarioManager.results.kappa.fair')
  return t('scenarioManager.results.kappa.poor')
}

function getICCClass(value) {
  if (value >= 0.9) return 'excellent'
  if (value >= 0.75) return 'good'
  if (value >= 0.5) return 'moderate'
  return 'poor'
}

function getKendallWClass(value) {
  if (value >= 0.9) return 'excellent'
  if (value >= 0.7) return 'good'
  if (value >= 0.5) return 'moderate'
  if (value >= 0.3) return 'fair'
  return 'poor'
}

function getCorrelationClass(value) {
  const absValue = Math.abs(value)
  if (absValue >= 0.8) return 'excellent'
  if (absValue >= 0.6) return 'good'
  if (absValue >= 0.4) return 'moderate'
  return 'poor'
}

function getF1Class(value) {
  if (value >= 0.85) return 'excellent'
  if (value >= 0.7) return 'good'
  if (value >= 0.5) return 'moderate'
  return 'poor'
}

// ===== Methods: Actions =====

function startHumanEvaluation() {
  const functionType = props.scenario?.function_type_name || 'rating'
  const routeMap = {
    'ranking': 'RankingSession',
    'rating': 'RatingSession',
    'mail_rating': 'RatingSession',  // mail_rating uses the same rating interface
    'authenticity': 'AuthenticitySession',
    'comparison': 'ComparisonSession',
    'labeling': 'RatingSession'  // labeling uses rating interface
  }
  const routeName = routeMap[functionType] || 'RatingSession'

  router.push({
    name: routeName,
    params: { scenarioId: props.scenario.id }
  })
}

async function addLLMEvaluator() {
  if (!selectedModel.value) return

  addingEvaluator.value = true
  try {
    await doStartEvaluation({
      scenario_id: props.scenario.id,
      model_id: selectedModel.value,
      template_id: selectedTemplate.value
    })
    emit('refresh')
  } catch (err) {
    console.error('Failed to add evaluator:', err)
  } finally {
    addingEvaluator.value = false
  }
}

function confirmRemoveEvaluator(evaluator) {
  evaluatorToRemove.value = evaluator
  showRemoveDialog.value = true
}

async function removeEvaluator() {
  if (!evaluatorToRemove.value) return

  removingEvaluator.value = true
  try {
    showRemoveDialog.value = false
    evaluatorToRemove.value = null
    emit('refresh')
  } catch (err) {
    console.error('Failed to remove evaluator:', err)
  } finally {
    removingEvaluator.value = false
  }
}

async function pauseEvaluator(evaluator) {
  try {
    await doStopEvaluation()
    emit('refresh')
  } catch (err) {
    console.error('Failed to pause evaluator:', err)
  }
}

async function resumeEvaluator(evaluator) {
  try {
    await doStartEvaluation({
      scenario_id: props.scenario.id,
      model_id: evaluator.model_id
    })
    emit('refresh')
  } catch (err) {
    console.error('Failed to resume evaluator:', err)
  }
}

async function exportResults(format) {
  try {
    const data = await doExport(props.scenario.id, format)
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      downloadBlob(blob, `scenario-${props.scenario.id}-results.json`)
    } else {
      downloadBlob(data, `scenario-${props.scenario.id}-results.${format}`)
    }
  } catch (error) {
    console.error('Export failed:', error)
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// ===== Lifecycle =====

onMounted(async () => {
  await fetchModels()

  if (modelSelectItems.value.length > 0 && !selectedModel.value) {
    const defaultModel = modelSelectItems.value.find(m => m.isDefault)
    selectedModel.value = defaultModel?.id || modelSelectItems.value[0].id
  }

  if (props.scenario?.id) {
    connectToScenario(props.scenario.id)
  }
})

onUnmounted(() => {
  disconnect()
})

watch(() => props.scenario?.id, (newId) => {
  if (newId) {
    // connectToScenario also fetches agreement metrics
    connectToScenario(newId)
  }
}, { immediate: true })

// Initialize selected dimension when dimensions change
watch(dimensions, (newDimensions) => {
  console.log('[EvaluationTab] dimensions watcher fired:', {
    dimensionsCount: newDimensions.length,
    dimensionIds: newDimensions.map(d => d.id),
    currentSelectedDimension: selectedDimension.value
  })
  if (newDimensions.length > 0 && !selectedDimension.value) {
    console.log('[EvaluationTab] Setting selectedDimension to:', newDimensions[0].id)
    selectedDimension.value = newDimensions[0].id
  }
}, { immediate: true })

// Fix dimension selection if current selection doesn't exist in distribution map
watch(
  () => ({ map: dimensionDistributionMap.value, selected: selectedDimension.value }),
  ({ map, selected }) => {
    const mapKeys = Object.keys(map)
    // If we have data in the map but selected dimension is not in it, auto-select first available
    if (mapKeys.length > 0 && selected && !mapKeys.includes(selected)) {
      console.log('[EvaluationTab] Dimension ID mismatch detected, auto-selecting:', mapKeys[0])
      selectedDimension.value = mapKeys[0]
    }
  },
  { immediate: true }
)

// Debug computed properties - remove after fixing
const ratingDistributionDebug = computed(() => {
  return props.liveStats?.ratingDistribution ? 'EXISTS' : 'NULL'
})
const byDimensionDebugCount = computed(() => {
  return props.liveStats?.ratingDistribution?.by_dimension?.length || 0
})
const byDimensionDebugIds = computed(() => {
  return (props.liveStats?.ratingDistribution?.by_dimension || []).map(d => d.dimension_id)
})

// Debug watcher - remove after fixing
watch(
  () => ({
    scenario: props.scenario?.id,
    liveStats: props.liveStats,
    dims: dimensions.value,
    hasDimDist: hasDimensionDistribution.value,
    hasDimAvg: hasDimensionAverages.value,
    selectedDim: selectedDimension.value,
    currentScale: currentDimensionScale.value,
    currentDist: currentDimensionDistribution.value,
    dimMapKeys: Object.keys(dimensionDistributionMap.value)
  }),
  (val) => {
    const byDim = val.liveStats?.ratingDistribution?.by_dimension
    console.log('[EvaluationTab DEBUG]', {
      scenarioId: val.scenario,
      hasLiveStats: !!val.liveStats,
      ratingDistributionExists: !!val.liveStats?.ratingDistribution,
      byDimensionCount: byDim?.length || 0,
      byDimensionIds: byDim?.map(d => d.dimension_id) || [],
      configDimensionIds: val.dims?.map(d => d.id) || [],
      dimensionDistributionMapKeys: val.dimMapKeys,
      selectedDimension: val.selectedDim,
      selectedDimensionInMap: val.dimMapKeys?.includes(val.selectedDim),
      currentDimensionScale: val.currentScale,
      currentDimensionDistribution: val.currentDist,
      currentDimensionDistributionLength: val.currentDist?.length
    })
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
/* DEBUG - Remove after fixing */
.debug-panel {
  background-color: rgba(var(--v-theme-error), 0.1);
  border: 2px solid rgb(var(--v-theme-error));
  padding: 12px;
  margin: 12px 0;
  border-radius: 8px;
  font-size: 12px;
  font-family: monospace;
  max-height: 400px;
  overflow-y: auto;
  color: rgb(var(--v-theme-on-surface));
}

.no-data-panel {
  padding: 16px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 0.85rem;
}

.evaluation-tab {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1200px;
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

.summary-content {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.summary-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Section Card */
.section-card {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.section-title {
  display: flex;
  align-items: center;
}

.section-title h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* Human Evaluators Grid */
.evaluator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 16px 20px;
}

.evaluator-card {
  padding: 12px 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.evaluator-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.evaluator-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.evaluator-name {
  font-weight: 500;
  font-size: 0.9rem;
}

.evaluator-progress {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-progress-bar {
  flex: 1;
  height: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 35px;
  text-align: right;
}

/* Add Evaluator Form */
.add-evaluator-form {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.form-row {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  min-width: 150px;
}

.form-group.flex-1 { flex: 1; }
.form-group.flex-2 { flex: 2; }

.form-group label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 6px;
}

.form-actions {
  flex-shrink: 0;
}

.model-cost {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.cost-estimate {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  background-color: rgba(var(--v-theme-warning), 0.08);
  border-radius: 6px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* LLM Evaluators List */
.llm-evaluators-list {
  padding: 16px 20px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 12px;
}

.list-header .count {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.llm-evaluator-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.llm-evaluator-card:last-child {
  margin-bottom: 0;
}

.llm-evaluator-card.is-running {
  border-color: rgba(var(--v-theme-info), 0.3);
  background-color: rgba(var(--v-theme-info), 0.03);
}

.evaluator-main {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 180px;
}

.evaluator-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-accent), 0.1);
  color: rgb(var(--v-theme-accent));
}

.evaluator-main .evaluator-info {
  flex: 1;
}

.model-name {
  font-weight: 500;
  font-size: 0.9rem;
  display: block;
}

.model-provider {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.evaluator-progress-section {
  flex: 1;
  min-width: 200px;
}

.progress-bar-container {
  width: 100%;
}

.progress-bar {
  height: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-fill.completed { background-color: rgb(var(--v-theme-success)); }
.progress-fill.running {
  background-color: rgb(var(--v-theme-info));
  animation: progress-pulse 1.5s ease-in-out infinite;
}
.progress-fill.paused { background-color: rgb(var(--v-theme-warning)); }

@keyframes progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.progress-stats .percent {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.evaluator-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 100px;
}

.evaluator-meta .cost {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.evaluator-actions {
  display: flex;
  gap: 4px;
}

/* Metrics & Results Section */
.metrics-results-section {
  padding-bottom: 0;
}

.metrics-section,
.confusion-matrix-section,
.distribution-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.metrics-section:last-child,
.confusion-matrix-section:last-child,
.distribution-section:last-child {
  border-bottom: none;
}

.subsection-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin: 0 0 16px 0;
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.subsection-header .subsection-title {
  margin-bottom: 0;
}

.evaluator-select {
  min-width: 180px;
  max-width: 250px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  cursor: help;
  transition: background-color 0.2s;
}

.metric-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
}

.metric-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
}

.metric-value.excellent { color: rgb(var(--v-theme-success)); }
.metric-value.good { color: #b0ca97; }
.metric-value.moderate { color: rgb(var(--v-theme-warning)); }
.metric-value.fair { color: #d4a574; }
.metric-value.poor { color: rgb(var(--v-theme-error)); }
.metric-value.error-metric { color: #88c4c8; } /* Neutral für Fehlermetriken (niedriger = besser) */

.metric-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  opacity: 0.5;
}

.metric-item:hover .info-icon {
  opacity: 1;
}

.metric-interpretation {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-top: 2px;
}

/* Tooltip Styles */
.help-icon {
  margin-left: 6px;
  opacity: 0.5;
  cursor: help;
  vertical-align: middle;
}

.help-icon:hover {
  opacity: 1;
}

.tooltip-content {
  max-width: 300px;
  padding: 4px;
}

.tooltip-content strong {
  display: block;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.tooltip-content p {
  margin: 0 0 8px 0;
  font-size: 0.8rem;
  line-height: 1.4;
  opacity: 0.9;
}

.tooltip-scale {
  font-size: 0.75rem;
  opacity: 0.8;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 8px;
  margin-top: 4px;
}

.tooltip-scale div {
  padding: 2px 0;
}

/* Distribution Chart */
.chart-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bar-container {
  display: grid;
  grid-template-columns: 100px 1fr 50px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-wrapper {
  display: flex;
  align-items: center;
  height: 28px;
  background-color: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 6px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  border-radius: 6px;
  transition: width 0.5s ease;
  min-width: fit-content;
}

.bar-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.bar-value.outside {
  color: rgb(var(--v-theme-on-surface));
  text-shadow: none;
  padding-left: 8px;
}

.bar-percentage {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: right;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-state.small {
  padding: 24px 20px;
}

.empty-state p {
  margin: 12px 0 0;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-state .hint {
  margin-top: 4px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Evaluator Filter Toggle */
.evaluator-filter-toggle {
  margin-right: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.evaluator-filter-toggle .v-btn {
  font-size: 0.75rem;
  text-transform: none;
  min-width: 80px;
}

/* Per-Dimension Section */
.per-dimension-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

/* Dimension Visualizations Grid (Heatmap + Spider side by side) */
.dimension-visualizations-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.visualization-panel {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.visualization-panel .subsection-title {
  margin-bottom: 12px;
}

.visualization-panel .heatmap-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.visualization-panel .spider-chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.visualization-panel .dimension-bar-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.dimension-selector {
  margin-bottom: 16px;
}

.dimension-select {
  max-width: 300px;
}

/* Heatmap */
.heatmap-container {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 16px;
}

.heatmap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.heatmap-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.heatmap-scale {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.heatmap-grid {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.heatmap-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  padding: 12px 16px;
  border-radius: 8px;
  text-align: center;
  transition: transform 0.2s;
}

.heatmap-cell:hover {
  transform: scale(1.05);
}

.heatmap-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.7);
}

.heatmap-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
  margin-top: 2px;
}

.heatmap-percent {
  font-size: 0.7rem;
  color: rgba(0, 0, 0, 0.5);
}

/* Empty State Heatmap */
.empty-heatmap .empty-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.15);
}

.empty-heatmap .empty-cell .heatmap-value {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-heatmap .empty-cell .heatmap-count,
.empty-heatmap .empty-cell .heatmap-percent {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.no-data-hint {
  margin-top: 12px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: center;
  font-style: italic;
}

/* Dimension Comparison Section */
.dimension-comparison-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

/* Dimension Bar Chart (for 1-2 dimensions) */
.dimension-bar-chart {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.dimension-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dimension-bar-label {
  min-width: 120px;
  font-weight: 500;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.dimension-bar-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
  padding: 8px;
}

.dimension-bar {
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
  min-width: 50px;
  transition: width 0.3s ease;
}

.dimension-bar.human-bar {
  background: linear-gradient(90deg, rgba(136, 196, 200, 0.3) 0%, #88c4c8 100%);
}

.dimension-bar.llm-bar {
  background: linear-gradient(90deg, rgba(196, 160, 212, 0.3) 0%, #c4a0d4 100%);
}

.dimension-bar .bar-value-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
  text-shadow: 0 0 4px rgba(255, 255, 255, 0.8);
}

.dimension-bar-scale {
  min-width: 50px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: right;
}

.bar-chart-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 8px;
}

/* Spider Chart Section */
.spider-chart-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.spider-chart-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.spider-chart {
  width: 100%;
  max-width: 350px;
  height: auto;
}

.spider-label {
  font-size: 10px;
  fill: rgb(var(--v-theme-on-surface));
  font-weight: 500;
}

.spider-legend {
  display: flex;
  gap: 24px;
  justify-content: center;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

/* Dimension Averages Table */
.dimension-averages-table {
  margin-top: 16px;
  overflow-x: auto;
}

.dimension-averages-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.dimension-averages-table th,
.dimension-averages-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.dimension-averages-table th {
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.dimension-averages-table td {
  color: rgb(var(--v-theme-on-surface));
}

.dimension-averages-table tr:last-child td {
  border-bottom: none;
}

.dimension-averages-table .diff-small {
  color: rgb(var(--v-theme-success));
}

.dimension-averages-table .diff-medium {
  color: rgb(var(--v-theme-warning));
}

.dimension-averages-table .diff-large {
  color: rgb(var(--v-theme-error));
}

/* Inter-Rater Agreement Heatmap */
.agreement-heatmap-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.agreement-heatmap-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.heatmap-matrix {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.heatmap-row {
  display: flex;
  gap: 2px;
}

.heatmap-row.header-row .heatmap-cell {
  font-weight: 600;
  font-size: 0.7rem;
}

.heatmap-matrix .heatmap-cell {
  min-width: 56px;
  max-width: 56px;
  height: 44px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 0.75rem;
  transition: transform 0.15s, box-shadow 0.15s;
  padding: 4px;
}

.heatmap-matrix .heatmap-cell:not(.corner-cell):not(.row-label):not(.header-cell):hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 10;
}

.heatmap-matrix .corner-cell {
  background: transparent;
}

.heatmap-matrix .header-cell,
.heatmap-matrix .row-label {
  background-color: rgba(var(--v-theme-surface-variant), 0.3);
  font-weight: 500;
}

.heatmap-matrix .header-cell.is-llm,
.heatmap-matrix .row-label.is-llm {
  background-color: rgba(196, 160, 212, 0.2);
}

.heatmap-matrix .data-cell {
  cursor: default;
}

.heatmap-matrix .agreement-value {
  font-weight: 600;
  font-size: 0.8rem;
  color: rgba(0, 0, 0, 0.75);
}

.heatmap-matrix .diagonal-indicator {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-size: 1rem;
}

.evaluator-name-short {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 48px;
  font-size: 0.65rem;
  line-height: 1.2;
}

.heatmap-matrix .llm-icon {
  color: #c4a0d4;
  margin-top: 2px;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.heatmap-legend .legend-gradient {
  width: 120px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(to right,
    rgba(232, 160, 135, 0.7) 0%,
    rgba(232, 200, 100, 0.7) 40%,
    rgba(152, 212, 187, 0.7) 70%,
    rgba(98, 200, 140, 0.8) 100%
  );
}

.heatmap-legend .legend-label {
  font-size: 0.7rem;
}

.evaluator-type-legend {
  display: flex;
  gap: 20px;
  justify-content: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.evaluator-type-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Responsive */
@media (max-width: 768px) {
  .dimension-visualizations-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }

  .visualization-panel {
    min-height: 280px;
  }

  .form-row {
    flex-direction: column;
    align-items: stretch;
  }

  .form-group.flex-1,
  .form-group.flex-2 {
    flex: none;
  }

  .llm-evaluator-card {
    flex-direction: column;
    align-items: stretch;
  }

  .evaluator-main,
  .evaluator-progress-section,
  .evaluator-meta {
    min-width: 100%;
  }

  .evaluator-actions {
    justify-content: flex-end;
    margin-top: 8px;
  }

  .bar-container {
    grid-template-columns: 80px 1fr 40px;
  }

  .evaluator-filter-toggle {
    margin-right: 0;
    margin-bottom: 8px;
    width: 100%;
  }

  .header-actions {
    flex-direction: column;
    width: 100%;
  }

  .heatmap-grid {
    justify-content: center;
  }

  .spider-chart {
    max-width: 280px;
  }

  .dimension-averages-table {
    font-size: 0.8rem;
  }

  .dimension-averages-table th,
  .dimension-averages-table td {
    padding: 8px;
  }

  .dimension-bar-row {
    flex-direction: column;
    align-items: stretch;
  }

  .dimension-bar-label {
    min-width: auto;
    margin-bottom: 4px;
  }

  .dimension-bar-scale {
    text-align: left;
    margin-top: 4px;
  }
}
</style>
