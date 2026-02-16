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

      <div class="summary-card" v-if="hasHumans">
        <div class="summary-icon" style="background-color: rgba(136, 196, 200, 0.15);">
          <LIcon color="#88c4c8" size="24">mdi-account-multiple-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.humanEvaluators }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.humanEvaluators') }}</span>
        </div>
      </div>

      <div class="summary-card" v-if="hasLLMs">
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
            v-if="hasHumans && hasLLMs"
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

      <!-- Total Progress Section -->
      <div class="total-progress-section">
        <div class="progress-header">
          <h4 class="subsection-title">
            <LIcon size="18" class="mr-2">mdi-progress-check</LIcon>
            {{ $t('scenarioManager.evaluation.totalProgress') }}
          </h4>
          <div class="progress-stats">
            <span class="progress-count">{{ filteredProgress.completed }} / {{ filteredProgress.total }}</span>
            <span class="progress-percent">{{ filteredProgress.percent }}%</span>
          </div>
        </div>

        <!-- Main Progress Bar -->
        <div class="progress-bar-container">
          <div class="progress-bar-track">
            <div
              class="progress-bar-fill"
              :style="{ width: filteredProgress.percent + '%' }"
              :class="getProgressColorClass(filteredProgress.percent)"
            ></div>
          </div>
        </div>

        <!-- Progress Legend (when filter is "all") -->
        <div class="progress-legend" v-if="evaluatorTypeFilter === 'all' && hasHumans && hasLLMs">
          <div class="legend-item human">
            <LIcon size="14">mdi-account</LIcon>
            <span class="legend-label">{{ $t('scenarioManager.evaluation.filter.human') }}</span>
            <span class="legend-value">{{ filteredProgress.human.completed }}/{{ filteredProgress.human.total }}</span>
            <span class="legend-percent">({{ filteredProgress.human.percent }}%)</span>
          </div>
          <div class="legend-item llm">
            <LIcon size="14">mdi-robot</LIcon>
            <span class="legend-label">{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
            <span class="legend-value">{{ filteredProgress.llm.completed }}/{{ filteredProgress.llm.total }}</span>
            <span class="legend-percent">({{ filteredProgress.llm.percent }}%)</span>
          </div>
        </div>

        <!-- Evaluator count info -->
        <div class="evaluator-count-info">
          <span v-if="evaluatorTypeFilter === 'all'">
            {{ filteredProgress.human.count + filteredProgress.llm.count }} {{ $t('scenarioManager.evaluation.evaluators') }}
            ({{ filteredProgress.human.count }} {{ $t('scenarioManager.evaluation.filter.human') }}, {{ filteredProgress.llm.count }} LLM)
          </span>
          <span v-else-if="evaluatorTypeFilter === 'human'">
            {{ filteredProgress.human.count }} {{ $t('scenarioManager.evaluation.humanEvaluators') }}
          </span>
          <span v-else>
            {{ filteredProgress.llm.count }} {{ $t('scenarioManager.evaluation.llmEvaluators') }}
          </span>
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
        <p v-if="isRankingScenario" class="subsection-description text-medium-emphasis text-caption mb-2">
          {{ $t('scenarioManager.results.rankingMetricsDescription') }}
        </p>
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
        <LConfusionMatrix
          v-if="currentConfusionMatrix"
          :matrix="currentConfusionMatrix"
          :title="selectedMatrixEvaluator === 'all'
            ? $t('scenarioManager.results.confusionMatrix.aggregated')
            : selectedEvaluatorName"
          :show-controls="true"
          :show-metrics="true"
          :show-legend="false"
          :use-heatmap="true"
          size="default"
        />
      </div>

      <!-- Ranking Bucket Distribution Chart -->
      <div class="bucket-distribution-section" v-if="hasBucketDistribution">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.bucketDistribution') }}
          <LTooltip :text="$t('scenarioManager.tooltips.bucketDistribution')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>
        <div class="bucket-chart">
          <div
            v-for="bucket in bucketDistribution"
            :key="bucket.bucket"
            class="bucket-bar-container"
          >
            <div class="bucket-label">{{ bucket.label }}</div>
            <div class="bucket-bar-wrapper">
              <div
                class="bucket-bar-fill"
                :style="{
                  width: bucket.percentage + '%',
                  backgroundColor: bucket.color
                }"
              >
                <span class="bucket-bar-value" v-if="bucket.percentage > 15">{{ bucket.count }}</span>
              </div>
              <span class="bucket-bar-value outside" v-if="bucket.percentage <= 15">{{ bucket.count }}</span>
            </div>
            <div class="bucket-percentage">{{ bucket.percentage }}%</div>
          </div>
        </div>
      </div>

      <!-- Provenance Analysis (Ranking) -->
      <div class="provenance-section" v-if="hasProvenanceAnalysis">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.provenanceAnalysis') }}
          <LTooltip :text="$t('scenarioManager.tooltips.provenanceAnalysis')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>
        <p class="subsection-description text-medium-emphasis text-caption mb-3">
          {{ $t('scenarioManager.results.provenanceDescription', { bucket: provenanceTopBucketLabel }) }}
        </p>

        <div class="provenance-best-grid">
          <div class="provenance-best-card">
            <span class="provenance-best-label">{{ $t('scenarioManager.results.bestLLM') }}</span>
            <strong class="provenance-best-name">{{ bestProvenanceLLM?.label || '-' }}</strong>
            <span v-if="bestProvenanceLLM" class="provenance-best-meta">
              {{ formatProvenanceRate(bestProvenanceLLM.top_bucket_rate) }}% | {{ bestProvenanceLLM.top_bucket_count }}/{{ bestProvenanceLLM.total }}
            </span>
          </div>
          <div class="provenance-best-card">
            <span class="provenance-best-label">{{ $t('scenarioManager.results.bestPrompt') }}</span>
            <strong class="provenance-best-name">{{ bestProvenancePrompt?.label || '-' }}</strong>
            <span v-if="bestProvenancePrompt" class="provenance-best-meta">
              {{ formatProvenanceRate(bestProvenancePrompt.top_bucket_rate) }}% | {{ bestProvenancePrompt.top_bucket_count }}/{{ bestProvenancePrompt.total }}
            </span>
          </div>
        </div>

        <div class="provenance-lists-grid">
          <div class="provenance-list-card">
            <div class="provenance-list-header">
              <span>{{ $t('scenarioManager.results.modelRanking') }}</span>
              <span>{{ $t('scenarioManager.results.assignments') }}: {{ currentProvenanceSegment?.total_assignments || 0 }}</span>
            </div>
            <div v-if="currentProvenanceSegment?.by_llm?.length" class="provenance-list">
              <div
                v-for="(entry, index) in currentProvenanceSegment.by_llm.slice(0, 8)"
                :key="`prov-llm-${entry.id}`"
                class="provenance-row"
              >
                <div class="provenance-row-main">
                  <span class="provenance-rank">#{{ index + 1 }}</span>
                  <span class="provenance-label">{{ entry.label }}</span>
                </div>
                <div class="provenance-row-stats">
                  <span class="provenance-rate">{{ formatProvenanceRate(entry.top_bucket_rate) }}%</span>
                  <span class="provenance-count">{{ entry.top_bucket_count }}/{{ entry.total }}</span>
                </div>
              </div>
            </div>
            <div v-else class="provenance-empty">
              {{ $t('scenarioManager.results.noProvenanceData') }}
            </div>
          </div>

          <div class="provenance-list-card">
            <div class="provenance-list-header">
              <span>{{ $t('scenarioManager.results.promptRanking') }}</span>
              <span>{{ $t('scenarioManager.results.topBucketShare') }}</span>
            </div>
            <div v-if="currentProvenanceSegment?.by_prompt?.length" class="provenance-list">
              <div
                v-for="(entry, index) in currentProvenanceSegment.by_prompt.slice(0, 8)"
                :key="`prov-prompt-${entry.id}`"
                class="provenance-row"
              >
                <div class="provenance-row-main">
                  <span class="provenance-rank">#{{ index + 1 }}</span>
                  <span class="provenance-label">{{ entry.label }}</span>
                </div>
                <div class="provenance-row-stats">
                  <span class="provenance-rate">{{ formatProvenanceRate(entry.top_bucket_rate) }}%</span>
                  <span class="provenance-count">{{ entry.top_bucket_count }}/{{ entry.total }}</span>
                </div>
              </div>
            </div>
            <div v-else class="provenance-empty">
              {{ $t('scenarioManager.results.noProvenanceData') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Ranking Agreement Heatmap (reuses LAgreementHeatmap) -->
      <div class="agreement-heatmap-section" v-if="hasRankingAgreement">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.rankingAgreement') }}
          <LTooltip :text="$t('scenarioManager.tooltips.rankingAgreement')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>
        <div class="heatmap-container">
          <LAgreementHeatmap
            :evaluators="pairwiseEvaluators"
            :agreements="pairwiseAgreements"
            :show-values="true"
            :show-hover-info="true"
            :show-legend="true"
            :show-evaluator-type-legend="true"
            :low-label="$t('scenarioManager.results.lowAgreement')"
            :high-label="$t('scenarioManager.results.highAgreement')"
            @cell-click="openAgreementDetail"
          />
        </div>
      </div>

      <!-- Distribution Chart (not for ranking - ranking uses bucket distribution) -->
      <div class="distribution-section" v-if="filteredDistributionData.length > 0 && !isRankingScenario">
        <h4 class="subsection-title">{{ $t('scenarioManager.results.distribution') }}</h4>
        <div class="chart-bars">
          <div
            v-for="(item, index) in filteredDistributionData"
            :key="item.value || item.label"
            class="bar-container"
          >
            <div class="bar-label">{{ getLocalizedLabel(item) }}</div>
            <div class="bar-wrapper">
              <div
                class="bar-fill"
                :style="{
                  width: item.percentage + '%',
                  backgroundColor: getLikertColor(item.value, index)
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

      <!-- Inter-Rater Agreement Heatmap (standalone section - only for scenarios WITHOUT dimensions like labeling) -->
      <div class="agreement-heatmap-section" v-if="hasPairwiseAgreement && !isRankingScenario && !hasDimensionAverages">
        <h4 class="subsection-title">
          {{ $t('scenarioManager.results.interRaterAgreement') }}
          <LTooltip :text="$t('scenarioManager.tooltips.interRaterAgreement')" location="top">
            <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
          </LTooltip>
        </h4>
        <div class="heatmap-container">
          <LAgreementHeatmap
            :evaluators="pairwiseEvaluators"
            :agreements="pairwiseAgreements"
            :show-values="true"
            :show-hover-info="true"
            :show-legend="true"
            :show-evaluator-type-legend="true"
            :low-label="$t('scenarioManager.results.lowAgreement')"
            :high-label="$t('scenarioManager.results.highAgreement')"
            @cell-click="openAgreementDetail"
          />
        </div>
      </div>

      <!-- ROW 1: Spider Chart + Heatmap (for scenarios WITH dimensions like rating, mail_rating) -->
      <div class="dimension-visualizations-grid" v-if="hasDimensionDistribution || hasDimensionAverages">
        <!-- Spider Chart (Left) -->
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
                <!-- All combined bar (shown when filter is 'all') -->
                <div
                  v-if="evaluatorTypeFilter === 'all'"
                  class="dimension-bar all-bar"
                  :style="{ width: getDimensionBarWidth('all', dim.id) + '%' }"
                >
                  <span class="bar-value-label">{{ getDimensionAverage('all', dim.id)?.toFixed(2) || '-' }}</span>
                </div>
                <!-- Human bar -->
                <div
                  v-if="evaluatorTypeFilter !== 'llm'"
                  class="dimension-bar human-bar"
                  :style="{ width: getDimensionBarWidth('human', dim.id) + '%' }"
                >
                  <span class="bar-value-label">{{ getDimensionAverage('human', dim.id)?.toFixed(2) || '-' }}</span>
                </div>
                <!-- LLM bar -->
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
              <div class="legend-item" v-if="evaluatorTypeFilter === 'all'">
                <span class="legend-color all-color"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.all') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'llm'">
                <span class="legend-color human-color"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'human'">
                <span class="legend-color llm-color"></span>
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
              <!-- All combined polygon (shown when filter is 'all') -->
              <polygon
                v-if="evaluatorTypeFilter === 'all' && allSpiderPoints.length > 0"
                :points="allSpiderPoints.map(p => `${p.x},${p.y}`).join(' ')"
                fill="rgba(176, 202, 151, 0.3)"
                stroke="#b0ca97"
                stroke-width="2"
              />
              <!-- Human polygon -->
              <polygon
                v-if="evaluatorTypeFilter !== 'llm' && humanSpiderPoints.length > 0"
                :points="humanSpiderPoints.map(p => `${p.x},${p.y}`).join(' ')"
                fill="rgba(136, 196, 200, 0.3)"
                stroke="#88c4c8"
                stroke-width="2"
              />
              <!-- LLM polygon -->
              <polygon
                v-if="evaluatorTypeFilter !== 'human' && llmSpiderPoints.length > 0"
                :points="llmSpiderPoints.map(p => `${p.x},${p.y}`).join(' ')"
                fill="rgba(196, 160, 212, 0.3)"
                stroke="#c4a0d4"
                stroke-width="2"
              />
              <!-- All combined points (shown when filter is 'all') -->
              <g v-if="evaluatorTypeFilter === 'all'">
                <circle
                  v-for="(point, i) in allSpiderPoints"
                  :key="'all-point-' + i"
                  :cx="point.x"
                  :cy="point.y"
                  :r="hoveredPoint?.type === 'all' && hoveredPoint?.index === i ? 7 : 5"
                  fill="#b0ca97"
                  class="spider-point"
                  @mouseenter="showSpiderTooltip($event, 'all', i)"
                  @mouseleave="hideSpiderTooltip"
                />
              </g>
              <!-- Human points -->
              <g v-if="evaluatorTypeFilter !== 'llm'">
                <circle
                  v-for="(point, i) in humanSpiderPoints"
                  :key="'human-point-' + i"
                  :cx="point.x"
                  :cy="point.y"
                  :r="hoveredPoint?.type === 'human' && hoveredPoint?.index === i ? 7 : 5"
                  fill="#88c4c8"
                  class="spider-point"
                  @mouseenter="showSpiderTooltip($event, 'human', i)"
                  @mouseleave="hideSpiderTooltip"
                />
              </g>
              <!-- LLM points -->
              <g v-if="evaluatorTypeFilter !== 'human'">
                <circle
                  v-for="(point, i) in llmSpiderPoints"
                  :key="'llm-point-' + i"
                  :cx="point.x"
                  :cy="point.y"
                  :r="hoveredPoint?.type === 'llm' && hoveredPoint?.index === i ? 7 : 5"
                  fill="#c4a0d4"
                  class="spider-point"
                  @mouseenter="showSpiderTooltip($event, 'llm', i)"
                  @mouseleave="hideSpiderTooltip"
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

            <!-- Spider Tooltip -->
            <div
              v-if="spiderTooltip.visible"
              class="spider-tooltip"
              :style="{ left: spiderTooltip.x + 'px', top: spiderTooltip.y + 'px' }"
            >
              <div class="tooltip-header">
                <span class="tooltip-dimension">{{ spiderTooltip.dimension }}</span>
                <span class="tooltip-type" :class="spiderTooltip.type">
                  {{ spiderTooltip.type === 'human' ? $t('scenarioManager.evaluation.filter.human') : spiderTooltip.type === 'llm' ? $t('scenarioManager.evaluation.filter.llm') : $t('scenarioManager.evaluation.filter.all') }}
                </span>
              </div>
              <div class="tooltip-value">
                <span class="value-label">{{ $t('scenarioManager.results.average') }}:</span>
                <span class="value-number">{{ spiderTooltip.value }}</span>
              </div>
              <div class="tooltip-scale">
                {{ $t('scenarioManager.results.scale') }}: {{ spiderTooltip.scaleMin }} - {{ spiderTooltip.scaleMax }}
              </div>
            </div>

            <div class="spider-legend">
              <div class="legend-item" v-if="evaluatorTypeFilter === 'all'">
                <span class="legend-color all-color"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.all') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'llm'">
                <span class="legend-color human-color"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.human') }}</span>
              </div>
              <div class="legend-item" v-if="evaluatorTypeFilter !== 'human'">
                <span class="legend-color llm-color"></span>
                <span>{{ $t('scenarioManager.evaluation.filter.llm') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Inter-Rater Agreement Heatmap (Right, next to Spider Chart) -->
        <div class="visualization-panel heatmap-panel" v-if="hasPairwiseAgreement">
          <h4 class="subsection-title">
            {{ $t('scenarioManager.results.interRaterAgreement') }}
            <LTooltip :text="$t('scenarioManager.tooltips.interRaterAgreement')" location="top">
              <v-icon size="16" class="help-icon">mdi-help-circle-outline</v-icon>
            </LTooltip>
          </h4>

          <LAgreementHeatmap
            :evaluators="pairwiseEvaluators"
            :agreements="pairwiseAgreements"
            :show-values="true"
            :show-hover-info="true"
            :show-legend="true"
            :show-evaluator-type-legend="true"
            :low-label="$t('scenarioManager.results.lowAgreement')"
            :high-label="$t('scenarioManager.results.highAgreement')"
            @cell-click="openAgreementDetail"
          />
        </div>

        <!-- Empty placeholder if no agreement data yet -->
        <div class="visualization-panel heatmap-panel empty-panel" v-else>
          <h4 class="subsection-title">
            {{ $t('scenarioManager.results.interRaterAgreement') }}
          </h4>
          <div class="no-data-panel">
            <LIcon size="32" color="grey-lighten-1">mdi-chart-box-outline</LIcon>
            <p class="text-medium-emphasis">{{ $t('scenarioManager.evaluation.noResultsYet') }}</p>
          </div>
        </div>
      </div>

      <!-- ROW 2: Distribution + Differences Table -->
      <div class="dimension-details-grid" v-if="hasDimensionDistribution || (hasDimensionAverages && dimensions.length >= 1)">
        <!-- Per-Dimension Distribution (Left) -->
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
          <div class="heatmap-wrapper">
            <LRatingDistribution
              :items="currentDimensionDistribution || []"
              :label="selectedDimensionName"
              :scale-min="currentDimensionScale?.min"
              :scale-max="currentDimensionScale?.max"
              :scale-step="currentDimensionScale?.step || 1"
              size="default"
            />
          </div>
        </div>

        <!-- Differences Table (Right) -->
        <div class="visualization-panel" v-if="hasDimensionAverages && dimensions.length >= 1">
          <h4 class="subsection-title">
            {{ $t('scenarioManager.results.dimension') }} {{ $t('scenarioManager.results.difference') }}
          </h4>
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

    <!-- Agreement Detail Dialog -->
    <v-dialog v-model="showAgreementDialog" max-width="1380" scrollable class="agreement-detail-dialog">
      <v-card class="agreement-detail-card">
        <v-card-title class="d-flex align-center justify-space-between">
          <div class="d-flex align-center">
            <LIcon color="primary" class="mr-2">mdi-handshake</LIcon>
            {{ $t('scenarioManager.results.agreementDetail') }}
          </div>
          <v-btn icon variant="text" size="small" @click="showAgreementDialog = false">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </v-card-title>

        <v-card-text v-if="selectedAgreement" class="agreement-detail-body">
          <!-- Evaluator Comparison Header -->
          <div class="agreement-comparison">
            <!-- Evaluator 1 -->
            <div class="agreement-evaluator" :class="{ 'is-llm': selectedAgreement.eval1?.isLLM }">
              <div class="agreement-evaluator-avatar">
                <LIcon :color="selectedAgreement.eval1?.isLLM ? '#c4a0d4' : '#88c4c8'" size="24">
                  {{ selectedAgreement.eval1?.isLLM ? 'mdi-robot' : 'mdi-account' }}
                </LIcon>
              </div>
              <div class="agreement-evaluator-details">
                <span class="agreement-evaluator-name">{{ formatAgreementEvaluatorName(selectedAgreement.eval1) }}</span>
                <span class="agreement-evaluator-type">
                  {{ selectedAgreement.eval1?.isLLM ? $t('scenarioManager.evaluation.filter.llm') : $t('scenarioManager.evaluation.filter.human') }}
                </span>
                <span v-if="getAgreementEvaluatorMeta(selectedAgreement.eval1)" class="agreement-evaluator-meta">
                  {{ getAgreementEvaluatorMeta(selectedAgreement.eval1) }}
                </span>
              </div>
            </div>

            <!-- VS Indicator -->
            <div class="vs-indicator">
              <span>vs</span>
            </div>

            <!-- Evaluator 2 -->
            <div class="agreement-evaluator" :class="{ 'is-llm': selectedAgreement.eval2?.isLLM }">
              <div class="agreement-evaluator-avatar">
                <LIcon :color="selectedAgreement.eval2?.isLLM ? '#c4a0d4' : '#88c4c8'" size="24">
                  {{ selectedAgreement.eval2?.isLLM ? 'mdi-robot' : 'mdi-account' }}
                </LIcon>
              </div>
              <div class="agreement-evaluator-details">
                <span class="agreement-evaluator-name">{{ formatAgreementEvaluatorName(selectedAgreement.eval2) }}</span>
                <span class="agreement-evaluator-type">
                  {{ selectedAgreement.eval2?.isLLM ? $t('scenarioManager.evaluation.filter.llm') : $t('scenarioManager.evaluation.filter.human') }}
                </span>
                <span v-if="getAgreementEvaluatorMeta(selectedAgreement.eval2)" class="agreement-evaluator-meta">
                  {{ getAgreementEvaluatorMeta(selectedAgreement.eval2) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Agreement Score -->
          <div class="agreement-score-section">
            <div class="score-circle" :style="{ borderColor: getAgreementScoreColor(selectedAgreement.value) }">
              <span class="score-value">{{ selectedAgreement.percentage }}%</span>
              <span class="score-label">{{ $t('scenarioManager.results.agreement') }}</span>
            </div>
          </div>

          <!-- Agreement Interpretation -->
          <div class="agreement-interpretation">
            <div class="interpretation-badge" :class="getAgreementLevelClass(selectedAgreement.value)">
              <LIcon size="16">{{ getAgreementLevelIcon(selectedAgreement.value) }}</LIcon>
              <span>{{ getAgreementLevelText(selectedAgreement.value) }}</span>
            </div>
          </div>

          <!-- Details Grid -->
          <div class="agreement-details-grid">
            <div class="detail-item">
              <span class="detail-label">{{ $t('scenarioManager.results.comparisonType') }}</span>
              <span class="detail-value">
                <template v-if="selectedAgreement.eval1?.isLLM && selectedAgreement.eval2?.isLLM">
                  <LIcon size="14" class="mr-1">mdi-robot</LIcon>
                  LLM vs LLM
                </template>
                <template v-else-if="!selectedAgreement.eval1?.isLLM && !selectedAgreement.eval2?.isLLM">
                  <LIcon size="14" class="mr-1">mdi-account-multiple</LIcon>
                  {{ $t('scenarioManager.evaluation.filter.human') }} vs {{ $t('scenarioManager.evaluation.filter.human') }}
                </template>
                <template v-else>
                  <LIcon size="14" class="mr-1">mdi-account-supervisor</LIcon>
                  {{ $t('scenarioManager.evaluation.filter.human') }} vs LLM
                </template>
              </span>
            </div>

            <div class="detail-item">
              <span class="detail-label">{{ $t('scenarioManager.results.rawScore') }}</span>
              <span class="detail-value">{{ selectedAgreement.value?.toFixed(4) || '-' }}</span>
            </div>

            <div class="detail-item" v-if="selectedAgreementDetail">
              <span class="detail-label">{{ $t('scenarioManager.results.comparedDataPoints') }}</span>
              <span class="detail-value">{{ comparedItemsCount }}</span>
            </div>
          </div>

          <!-- Explanation -->
          <div class="agreement-explanation">
            <LIcon size="16" class="mr-2">mdi-information-outline</LIcon>
            <span>{{ getAgreementExplanation(selectedAgreement.value) }}</span>
          </div>

          <!-- Item-Level Breakdown -->
          <div v-if="selectedAgreementDetail" class="agreement-breakdown">
            <div class="breakdown-header">
              <h5 class="breakdown-title">{{ $t('scenarioManager.results.itemBreakdown') }}</h5>
              <span v-if="isAgreementDetailTruncated" class="breakdown-note">
                {{ $t('scenarioManager.results.itemBreakdownTruncated') }}
              </span>
            </div>

            <v-expansion-panels v-model="expandedAgreementPanels" multiple variant="accordion" class="breakdown-panels">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="panel-title-row">
                    <span>{{ $t('scenarioManager.results.disagreedDataPoints') }}</span>
                    <span class="panel-count panel-count-disagreed">{{ disagreedItems.length }}</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div v-if="disagreedItems.length === 0" class="panel-empty">
                    {{ $t('scenarioManager.results.noDisagreedDataPoints') }}
                  </div>
                  <div v-else class="agreement-point-list">
                    <details
                      v-for="item in disagreedItems"
                      :key="getAgreementItemKey(item, 'disagreed')"
                      class="agreement-point-item disagreement"
                    >
                      <summary class="agreement-point-summary">
                        <span class="point-label">{{ getAgreementItemLabel(item) }}</span>
                        <span class="point-value-preview">
                          {{ formatAgreementEvaluatorName(selectedAgreement.eval1) }}:
                          {{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval1?.id)) }}
                          ·
                          {{ formatAgreementEvaluatorName(selectedAgreement.eval2) }}:
                          {{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval2?.id)) }}
                        </span>
                      </summary>
                      <div class="agreement-point-body">
                        <div class="agreement-point-row">
                          <span class="point-rater">{{ formatAgreementEvaluatorName(selectedAgreement.eval1) }}</span>
                          <strong>{{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval1?.id)) }}</strong>
                        </div>
                        <div class="agreement-point-row">
                          <span class="point-rater">{{ formatAgreementEvaluatorName(selectedAgreement.eval2) }}</span>
                          <strong>{{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval2?.id)) }}</strong>
                        </div>
                        <p v-if="item.preview" class="point-preview">{{ item.preview }}</p>
                      </div>
                    </details>
                  </div>
                  <div v-if="selectedAgreementDetail.disagreed_omitted_count > 0" class="panel-omitted">
                    {{ $t('scenarioManager.results.omittedDataPoints', { count: selectedAgreementDetail.disagreed_omitted_count }) }}
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="panel-title-row">
                    <span>{{ $t('scenarioManager.results.agreedDataPoints') }}</span>
                    <span class="panel-count panel-count-agreed">{{ agreedItems.length }}</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div v-if="agreedItems.length === 0" class="panel-empty">
                    {{ $t('scenarioManager.results.noAgreedDataPoints') }}
                  </div>
                  <div v-else class="agreement-point-list">
                    <details
                      v-for="item in agreedItems"
                      :key="getAgreementItemKey(item, 'agreed')"
                      class="agreement-point-item agreement"
                    >
                      <summary class="agreement-point-summary">
                        <span class="point-label">{{ getAgreementItemLabel(item) }}</span>
                        <span class="point-value-preview">
                          {{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval1?.id)) }}
                        </span>
                      </summary>
                      <div class="agreement-point-body">
                        <div class="agreement-point-row">
                          <span class="point-rater">{{ formatAgreementEvaluatorName(selectedAgreement.eval1) }}</span>
                          <strong>{{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval1?.id)) }}</strong>
                        </div>
                        <div class="agreement-point-row">
                          <span class="point-rater">{{ formatAgreementEvaluatorName(selectedAgreement.eval2) }}</span>
                          <strong>{{ formatAgreementItemValue(getAgreementItemValue(item, selectedAgreement.eval2?.id)) }}</strong>
                        </div>
                        <p v-if="item.preview" class="point-preview">{{ item.preview }}</p>
                      </div>
                    </details>
                  </div>
                  <div v-if="selectedAgreementDetail.agreed_omitted_count > 0" class="panel-omitted">
                    {{ $t('scenarioManager.results.omittedDataPoints', { count: selectedAgreementDetail.agreed_omitted_count }) }}
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
          <div v-else class="agreement-breakdown-unavailable">
            <LIcon size="16" class="mr-2">mdi-information-outline</LIcon>
            <span>{{ $t('scenarioManager.results.itemBreakdownUnavailable') }}</span>
          </div>
        </v-card-text>
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
import { parseUserProviderModelId } from '@/utils/formatters'
import { useScenarioManager } from '../../composables/useScenarioManager'
import LAvatar from '@/components/common/LAvatar.vue'

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

const { t, locale } = useI18n()
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

// Agreement detail dialog state
const showAgreementDialog = ref(false)
const selectedAgreement = ref(null)
const expandedAgreementPanels = ref([0])

// Spider chart constants - increased size for longer labels
const spiderSize = 360
const spiderCenter = 180
const spiderRadius = 110

// Spider tooltip state
const hoveredPoint = ref(null)
const spiderTooltip = ref({
  visible: false,
  x: 0,
  y: 0,
  dimension: '',
  type: '',
  value: '-',
  scaleMin: 1,
  scaleMax: 5
})

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

// ===== Computed: Evaluator Type Flags =====

const hasHumans = computed(() => {
  return evaluatorStatsList.value.some(u => !u.isLLM)
})

const hasLLMs = computed(() => {
  return evaluatorStatsList.value.some(u => u.isLLM)
})

// Auto-set filter when only one type exists
watch([hasHumans, hasLLMs], ([h, l]) => {
  if (h && !l) evaluatorTypeFilter.value = 'human'
  else if (!h && l) evaluatorTypeFilter.value = 'llm'
  else evaluatorTypeFilter.value = 'all'
}, { immediate: true })

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
    const parsed = parseUserProviderModelId(modelId)
    let displayName = parsed ? parsed.displayName : modelId
    return {
      id: modelId,
      modelId: modelId,
      name: displayName,
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

// ===== Computed: Filtered Progress =====

const filteredProgress = computed(() => {
  const users = evaluatorStatsList.value

  // Filter users based on evaluatorTypeFilter
  let filteredUsers = users
  if (evaluatorTypeFilter.value === 'human') {
    filteredUsers = users.filter(u => !u.isLLM)
  } else if (evaluatorTypeFilter.value === 'llm') {
    filteredUsers = users.filter(u => u.isLLM)
  }

  // Calculate totals
  const completed = filteredUsers.reduce((sum, u) => sum + (u.completed || 0), 0)
  const total = filteredUsers.reduce((sum, u) => sum + (u.total || 0), 0)
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0

  // Calculate per-type progress for the legend
  const humanUsers = users.filter(u => !u.isLLM)
  const llmUsers = users.filter(u => u.isLLM)

  const humanCompleted = humanUsers.reduce((sum, u) => sum + (u.completed || 0), 0)
  const humanTotal = humanUsers.reduce((sum, u) => sum + (u.total || 0), 0)
  const llmCompleted = llmUsers.reduce((sum, u) => sum + (u.completed || 0), 0)
  const llmTotal = llmUsers.reduce((sum, u) => sum + (u.total || 0), 0)

  return {
    completed,
    total,
    percent,
    evaluatorCount: filteredUsers.length,
    human: {
      completed: humanCompleted,
      total: humanTotal,
      percent: humanTotal > 0 ? Math.round((humanCompleted / humanTotal) * 100) : 0,
      count: humanUsers.length
    },
    llm: {
      completed: llmCompleted,
      total: llmTotal,
      percent: llmTotal > 0 ? Math.round((llmCompleted / llmTotal) * 100) : 0,
      count: llmUsers.length
    }
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

// Likert scale colors: red (bad) -> yellow (neutral) -> green (good)
const likertColors = {
  1: '#e57373',  // Red - Very poor
  2: '#ffb74d',  // Orange - Poor
  3: '#fff176',  // Yellow - Acceptable
  4: '#aed581',  // Light green - Good
  5: '#81c784'   // Green - Excellent
}

function getBarColor(index) {
  return barColors[index % barColors.length]
}

/**
 * Get color for Likert scale items based on value.
 * Uses a red-yellow-green gradient for semantic meaning.
 */
function getLikertColor(value, index) {
  // If value is in Likert scale range (1-5), use semantic colors
  if (value >= 1 && value <= 5 && likertColors[value]) {
    return likertColors[value]
  }
  // Fallback to index-based colors for non-Likert scales
  return barColors[index % barColors.length]
}

/**
 * Get localized label for distribution item.
 * Uses label_de/label_en from backend, falls back to label.
 */
function getLocalizedLabel(item) {
  if (!item) return ''

  const lang = locale.value || 'en'

  // Use localized label if available
  if (lang === 'de' && item.label_de) {
    return item.value ? `${item.value} - ${item.label_de}` : item.label_de
  }
  if (item.label_en) {
    return item.value ? `${item.value} - ${item.label_en}` : item.label_en
  }

  // Fallback to default label
  return item.label || String(item.value || '')
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

// ===== Computed: Ranking Bucket Distribution =====

const bucketDistribution = computed(() => {
  return props.liveStats?.bucket_distribution || []
})

const hasBucketDistribution = computed(() => {
  return isRankingScenario.value && bucketDistribution.value.length > 0
})

// ===== Computed: Ranking Provenance Analysis =====

const provenanceAnalysis = computed(() => {
  return props.liveStats?.provenanceAnalysis || props.liveStats?.provenance_analysis || null
})

const currentProvenanceSegmentKey = computed(() => {
  if (evaluatorTypeFilter.value === 'human') return 'human'
  if (evaluatorTypeFilter.value === 'llm') return 'llm'
  return 'all'
})

const currentProvenanceSegment = computed(() => {
  const segments = provenanceAnalysis.value?.segments
  if (!segments) return null
  return segments[currentProvenanceSegmentKey.value] || segments.all || null
})

const provenanceTopBucketLabel = computed(() => {
  return provenanceAnalysis.value?.top_bucket?.label || 'Top Bucket'
})

const bestProvenanceLLM = computed(() => {
  return currentProvenanceSegment.value?.best_llm || null
})

const bestProvenancePrompt = computed(() => {
  return currentProvenanceSegment.value?.best_prompt || null
})

const hasProvenanceAnalysis = computed(() => {
  if (!isRankingScenario.value) return false
  const segment = currentProvenanceSegment.value
  if (!segment) return false
  return (segment.by_llm?.length || 0) > 0 || (segment.by_prompt?.length || 0) > 0
})

// ===== Computed: Ranking Agreement Matrix =====

const rankingAgreement = computed(() => {
  return props.liveStats?.ranking_agreement || { evaluators: [], agreements: {} }
})

const hasRankingAgreement = computed(() => {
  return isRankingScenario.value &&
    rankingAgreement.value.evaluators?.length >= 2 &&
    Object.keys(rankingAgreement.value.agreements || {}).length > 0
})

// ===== Computed: Dimensions =====

const dimensions = computed(() => {
  // Get dimensions from scenario config
  const config = props.scenario?.config_json || props.scenario?.config
  const evalConfig = config?.eval_config || {}

  // Dimensions can be at multiple locations:
  // 1. config.dimensions (direct)
  // 2. config.eval_config.dimensions (nested in eval_config)
  // 3. config.eval_config.config.dimensions (nested in eval_config.config - from wizard)
  const configDimensions = config?.dimensions || evalConfig?.dimensions || evalConfig?.config?.dimensions || []

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

// ===== Ranking Agreement Helpers =====

function getShortEvaluatorName(evaluator) {
  const name = evaluator.name || evaluator.id
  if (evaluator.isLLM) {
    // For LLM models, show last part of model ID (e.g., "Mistral-Small-24B")
    const parts = String(name).split('/')
    const modelName = parts[parts.length - 1]
    // Remove common suffixes to shorten
    return modelName
      .replace(/-Instruct.*$/, '')
      .replace(/-\d{4}$/, '')
      .substring(0, 18)
  }
  // For humans, show full name (tooltip shows full anyway)
  return String(name).substring(0, 15)
}

function getRankingAgreementValue(id1, id2) {
  const agreements = rankingAgreement.value.agreements || {}
  // Keys are formatted as "min-max"
  const key1 = `${id1}-${id2}`
  const key2 = `${id2}-${id1}`
  const value = agreements[key1] ?? agreements[key2]
  if (value === null || value === undefined) return '-'
  return Math.round(value * 100) + '%'
}

function getCellStyle(id1, id2, rowIndex, colIndex) {
  if (rowIndex === colIndex) {
    return { backgroundColor: 'rgba(var(--v-theme-surface), 0.5)' }
  }
  const agreements = rankingAgreement.value.agreements || {}
  const key1 = `${id1}-${id2}`
  const key2 = `${id2}-${id1}`
  const value = agreements[key1] ?? agreements[key2]
  if (value === null || value === undefined) {
    return { backgroundColor: 'rgba(var(--v-theme-on-surface), 0.05)' }
  }
  // Color from red (0%) to green (100%)
  const hue = value * 120 // 0 = red, 120 = green
  return {
    backgroundColor: `hsla(${hue}, 70%, 85%, 0.6)`
  }
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
  const r = spiderRadius + 35  // More space for labels
  return {
    x: spiderCenter + r * Math.cos(angle),
    y: spiderCenter + r * Math.sin(angle)
  }
}

function showSpiderTooltip(event, type, index) {
  const dim = dimensions.value[index]
  if (!dim) return

  const avg = getDimensionAverage(type, dim.id)
  const dimData = dimensionDistributionMap.value[dim.id]

  const scaleMin = dim?.scale?.min ?? dimData?.scale_min ?? 1
  const scaleMax = dim?.scale?.max ?? dimData?.scale_max ?? 5

  // Get position relative to the spider chart container
  const container = event.target.closest('.spider-chart-container')
  const rect = container?.getBoundingClientRect()
  const svgRect = event.target.closest('svg')?.getBoundingClientRect()

  hoveredPoint.value = { type, index }
  spiderTooltip.value = {
    visible: true,
    x: svgRect ? event.clientX - rect.left + 10 : event.offsetX + 10,
    y: svgRect ? event.clientY - rect.top - 40 : event.offsetY - 40,
    dimension: dim.name || dim.id,
    type: type,
    value: avg !== null ? avg.toFixed(2) : '-',
    scaleMin,
    scaleMax
  }
}

function hideSpiderTooltip() {
  hoveredPoint.value = null
  spiderTooltip.value.visible = false
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

const allSpiderPoints = computed(() => {
  return dimensions.value.map((dim, i) => {
    const normalizedValue = getNormalizedValue('all', dim.id)
    return getSpiderPoint(i, normalizedValue)
  })
})

// ===== Pairwise Agreement Heatmap =====

// Get pairwise data from either source (unified or legacy ranking_agreement)
const pairwiseData = computed(() => {
  // Prefer pairwiseAgreement (unified), fallback to ranking_agreement (deprecated)
  return props.liveStats?.pairwiseAgreement || props.liveStats?.ranking_agreement || null
})

const hasPairwiseAgreement = computed(() => {
  const pairwise = pairwiseData.value
  return pairwise && pairwise.evaluators && pairwise.evaluators.length >= 2
})

const pairwiseEvaluators = computed(() => {
  const pairwise = pairwiseData.value
  if (!pairwise?.evaluators) return []
  // Sort: humans first, then LLMs
  return [...pairwise.evaluators].sort((a, b) => {
    if (a.isLLM === b.isLLM) return a.name.localeCompare(b.name)
    return a.isLLM ? 1 : -1
  })
})

const pairwiseAgreements = computed(() => {
  const pairwise = pairwiseData.value
  return pairwise?.agreements || {}
})

const selectedAgreementDetail = computed(() => {
  if (!selectedAgreement.value) return null
  const pairwise = pairwiseData.value
  if (!pairwise) return null

  const eval1Id = selectedAgreement.value.eval1?.id
  const eval2Id = selectedAgreement.value.eval2?.id
  if (eval1Id === undefined || eval2Id === undefined) return null

  const key = getAgreementKey(eval1Id, eval2Id)
  return pairwise?.pair_details?.[key] || pairwise?.pairDetails?.[key] || null
})

const agreedItems = computed(() => {
  const rawItems = selectedAgreementDetail.value?.agreed_items || selectedAgreementDetail.value?.agreedItems || []
  return [...rawItems].sort((a, b) => {
    const aId = Number(a?.item_id ?? a?.feature_id ?? 0)
    const bId = Number(b?.item_id ?? b?.feature_id ?? 0)
    return aId - bId
  })
})

const disagreedItems = computed(() => {
  const rawItems = selectedAgreementDetail.value?.disagreed_items || selectedAgreementDetail.value?.disagreedItems || []
  return [...rawItems].sort((a, b) => {
    const aId = Number(a?.item_id ?? a?.feature_id ?? 0)
    const bId = Number(b?.item_id ?? b?.feature_id ?? 0)
    return aId - bId
  })
})

const comparedItemsCount = computed(() => {
  const detail = selectedAgreementDetail.value
  if (!detail) return 0
  return detail.shared_count ?? detail.sharedCount ?? (agreedItems.value.length + disagreedItems.value.length)
})

const isAgreementDetailTruncated = computed(() => {
  const detail = selectedAgreementDetail.value
  if (!detail) return false
  const omittedAgreed = detail.agreed_omitted_count || 0
  const omittedDisagreed = detail.disagreed_omitted_count || 0
  return Boolean(detail.truncated) || (omittedAgreed + omittedDisagreed > 0)
})

function getAgreementKey(id1, id2) {
  // Keys are stored as "min-max" for consistency
  const str1 = String(id1)
  const str2 = String(id2)
  return str1 < str2 ? `${str1}-${str2}` : `${str2}-${str1}`
}

// ===== Agreement Detail Dialog =====

function openAgreementDetail(eventData) {
  // Support both old (eval1, eval2) and new ({ evaluator1, evaluator2, value }) formats
  const eval1 = eventData.evaluator1 || eventData
  const eval2 = eventData.evaluator2 || arguments[1]
  const value = eventData.value !== undefined ? eventData.value : pairwiseAgreements.value[getAgreementKey(eval1.id, eval2.id)]

  selectedAgreement.value = {
    eval1: eval1,
    eval2: eval2,
    value: value,
    percentage: value !== undefined && value !== null ? Math.round(value * 100) : null
  }
  const key = getAgreementKey(eval1.id, eval2.id)
  const detail = pairwiseData.value?.pair_details?.[key] || pairwiseData.value?.pairDetails?.[key]
  const hasDisagreedItems = (detail?.disagreed_items?.length || detail?.disagreedItems?.length || 0) > 0
  expandedAgreementPanels.value = hasDisagreedItems ? [0] : [1]
  showAgreementDialog.value = true
}

function getAgreementItemKey(item, prefix = 'item') {
  const primaryId = item?.item_id ?? item?.feature_id ?? item?.id ?? item?.label ?? 'unknown'
  return `${prefix}-${String(primaryId)}`
}

function getAgreementItemLabel(item) {
  if (!item) return '-'
  if (item.label) return item.label
  const itemId = item.item_id ?? item.feature_id
  if (itemId !== undefined && itemId !== null) {
    return `${t('scenarioManager.results.dataPoint')} #${itemId}`
  }
  return t('scenarioManager.results.dataPoint')
}

function getAgreementItemValue(item, evaluatorId) {
  if (!item || evaluatorId === undefined || evaluatorId === null) return null
  return item.values?.[String(evaluatorId)] ?? null
}

function formatAgreementItemValue(value) {
  if (value === undefined || value === null || value === '') return '-'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2)
  }
  const text = String(value).trim()
  if (!text) return '-'
  return text.charAt(0).toUpperCase() + text.slice(1)
}

function formatAgreementEvaluatorName(evaluator) {
  if (!evaluator) return '-'
  const rawId = String(evaluator.id || evaluator.model_id || '').replace(/^llm:/, '')
  const rawName = String(evaluator.name || evaluator.username || evaluator.model_name || '').trim()

  // Keep human names as provided; fallback to id only if missing.
  if (!evaluator.isLLM) {
    return rawName || rawId || '-'
  }

  // For LLMs prefer full model id when available to avoid truncated labels like "...".
  if (rawName && !rawName.includes('...')) {
    // If backend sends only model short name but id has provider/model, show full id.
    if (rawId && rawId.includes('/') && !rawName.includes('/')) {
      const shortFromId = rawId.split('/').pop()
      if (shortFromId && shortFromId.toLowerCase() === rawName.toLowerCase()) {
        return rawId
      }
    }
    return rawName
  }

  return rawId || rawName || '-'
}

function getAgreementEvaluatorMeta(evaluator) {
  if (!evaluator || !evaluator.isLLM) return ''
  const rawId = String(evaluator.id || evaluator.model_id || evaluator.name || '').replace(/^llm:/, '')
  if (!rawId) return ''
  const displayName = formatAgreementEvaluatorName(evaluator)
  // Show raw id only if it differs from displayed name.
  if (rawId !== displayName) return rawId
  return ''
}

function getAgreementScoreColor(value) {
  if (value === undefined || value === null) return 'rgba(var(--v-theme-on-surface), 0.3)'
  if (value >= 0.8) return '#62c88c'  // High - green
  if (value >= 0.6) return '#98d4bb'  // Good - light green
  if (value >= 0.4) return '#e8c864'  // Moderate - yellow
  return '#e8a087'  // Low - red/orange
}

function getAgreementLevelClass(value) {
  if (value === undefined || value === null) return 'level-unknown'
  if (value >= 0.8) return 'level-excellent'
  if (value >= 0.6) return 'level-good'
  if (value >= 0.4) return 'level-moderate'
  return 'level-low'
}

function getAgreementLevelIcon(value) {
  if (value === undefined || value === null) return 'mdi-help-circle'
  if (value >= 0.8) return 'mdi-check-circle'
  if (value >= 0.6) return 'mdi-check'
  if (value >= 0.4) return 'mdi-alert-circle'
  return 'mdi-close-circle'
}

function getAgreementLevelText(value) {
  if (value === undefined || value === null) return t('scenarioManager.results.agreementLevels.unknown')
  if (value >= 0.8) return t('scenarioManager.results.agreementLevels.excellent')
  if (value >= 0.6) return t('scenarioManager.results.agreementLevels.good')
  if (value >= 0.4) return t('scenarioManager.results.agreementLevels.moderate')
  return t('scenarioManager.results.agreementLevels.low')
}

function getProgressColorClass(percent) {
  if (percent >= 100) return 'progress-complete'
  if (percent >= 75) return 'progress-high'
  if (percent >= 50) return 'progress-medium'
  if (percent >= 25) return 'progress-low'
  return 'progress-start'
}

function getAgreementExplanation(value) {
  if (value === undefined || value === null) {
    return t('scenarioManager.results.agreementExplanation.noData')
  }
  if (value >= 0.8) {
    return t('scenarioManager.results.agreementExplanation.excellent')
  }
  if (value >= 0.6) {
    return t('scenarioManager.results.agreementExplanation.good')
  }
  if (value >= 0.4) {
    return t('scenarioManager.results.agreementExplanation.moderate')
  }
  return t('scenarioManager.results.agreementExplanation.low')
}

function formatProvenanceRate(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '0.0'
  return numeric.toFixed(1)
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
  // Use unified EvaluationSession for all evaluation types
  // EvaluationSession auto-detects the interface based on scenario function_type_id
  router.push({
    name: 'EvaluationSession',
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
  if (newDimensions.length > 0 && !selectedDimension.value) {
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
      selectedDimension.value = mapKeys[0]
    }
  },
  { immediate: true }
)

</script>

<style scoped>
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

/* Total Progress Section */
.total-progress-section {
  padding: 16px 20px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-header .subsection-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.progress-stats {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-count {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.progress-percent {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.progress-bar-container {
  margin-bottom: 10px;
}

.progress-bar-track {
  height: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.progress-bar-fill.progress-low {
  background-color: rgba(232, 160, 135, 0.8);
}

.progress-bar-fill.progress-medium {
  background-color: rgba(209, 188, 138, 0.8);
}

.progress-bar-fill.progress-high {
  background-color: rgba(136, 196, 200, 0.8);
}

.progress-bar-fill.progress-complete {
  background-color: rgba(152, 212, 187, 0.9);
}

.progress-legend {
  display: flex;
  gap: 24px;
  margin-bottom: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.legend-item.human .v-icon {
  color: #88c4c8;
}

.legend-item.llm .v-icon {
  color: #c4a0d4;
}

.legend-label {
  font-weight: 500;
}

.legend-value {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.legend-percent {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 0.75rem;
}

.evaluator-count-info {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
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
.distribution-section,
.bucket-distribution-section,
.provenance-section,
.ranking-agreement-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}


.metrics-section:last-child,
.confusion-matrix-section:last-child,
.distribution-section:last-child,
.bucket-distribution-section:last-child,
.provenance-section:last-child,
.ranking-agreement-section:last-child {
  border-bottom: none;
}

/* Bucket Distribution Styles */
.bucket-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bucket-bar-container {
  display: grid;
  grid-template-columns: 100px 1fr 60px;
  gap: 12px;
  align-items: center;
}

.bucket-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
  text-align: right;
}

.bucket-bar-wrapper {
  position: relative;
  height: 28px;
  background-color: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.bucket-bar-fill {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 8px;
  transition: width 0.3s ease-out;
  border-radius: 4px;
}

.bucket-bar-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.7);
}

.bucket-bar-value.outside {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.bucket-percentage {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-align: left;
}

/* Provenance Analysis */
.provenance-best-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.provenance-best-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
}

.provenance-best-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.provenance-best-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  line-height: 1.3;
}

.provenance-best-meta {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

.provenance-lists-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.provenance-list-card {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  padding: 10px;
}

.provenance-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

.provenance-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.provenance-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
}

.provenance-row-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.provenance-rank {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
  min-width: 18px;
}

.provenance-label {
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provenance-row-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provenance-rate {
  font-size: 0.82rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.provenance-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.provenance-empty {
  padding: 12px 4px 6px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Ranking Agreement Matrix Styles */
.ranking-agreement-matrix {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-x: auto;
  margin: 0 auto;
}

.matrix-row {
  display: flex;
  gap: 2px;
}

.matrix-cell {
  min-width: 100px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 500;
  border-radius: 4px;
  flex-shrink: 0;
}

.matrix-cell.corner-cell {
  background: transparent;
}

.matrix-cell.header-cell,
.matrix-cell.row-header-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex-direction: column;
  gap: 2px;
}

.matrix-cell.data-cell {
  color: rgba(0, 0, 0, 0.7);
}

.matrix-cell.diagonal-cell {
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.matrix-cell .evaluator-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 90px;
  font-size: 0.75rem;
}

.llm-badge {
  margin-top: 2px;
}

.mirror-value {
  opacity: 0.6;
  font-size: 0.75rem;
}

.agreement-legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
  padding: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
}

.legend-gradient {
  display: flex;
  align-items: center;
  gap: 8px;
}

.gradient-bar {
  width: 120px;
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(to right, hsla(0, 70%, 85%, 0.6), hsla(60, 70%, 85%, 0.6), hsla(120, 70%, 85%, 0.6));
}

.legend-min,
.legend-max {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.legend-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
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

/* Agreement Heatmap Section (independent, shows for all scenario types) */
.agreement-heatmap-section {
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.agreement-heatmap-section .heatmap-container {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  justify-content: center;
}

/* Dimension Visualizations Grid (Spider only, no longer includes heatmap) */
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
  overflow: visible;  /* Allow spider chart labels to extend outside */
}

.visualization-panel .subsection-title {
  margin-bottom: 12px;
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

/* Dimension Details Grid (ROW 2: Distribution + Table) */
.dimension-details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

@media (max-width: 900px) {
  .provenance-lists-grid {
    grid-template-columns: 1fr;
  }
}

/* Heatmap Panel - Centered Content */
.heatmap-panel {
  display: flex;
  flex-direction: column;
}

/* Empty Panel */
.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.no-data-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  gap: 12px;
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

.dimension-bar.all-bar {
  background: linear-gradient(90deg, rgba(176, 202, 151, 0.3) 0%, #b0ca97 100%);
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
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
  overflow: visible;  /* Ensure labels aren't clipped */
}

.spider-chart {
  width: 100%;
  max-width: 400px;
  height: auto;
  overflow: visible;  /* Ensure labels aren't clipped */
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

.legend-color.human-color {
  background-color: #88c4c8;
}

.legend-color.llm-color {
  background-color: #c4a0d4;
}

.legend-color.all-color {
  background-color: #b0ca97;
}

/* Spider Point Interaction */
.spider-point {
  cursor: pointer;
  transition: r 0.15s ease, filter 0.15s ease;
}

.spider-point:hover {
  filter: brightness(1.2);
}

/* Spider Tooltip */
.spider-tooltip {
  position: absolute;
  z-index: 100;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  min-width: 140px;
}

.spider-tooltip .tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.spider-tooltip .tooltip-dimension {
  font-weight: 600;
  font-size: 0.9rem;
  color: rgb(var(--v-theme-on-surface));
}

.spider-tooltip .tooltip-type {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.spider-tooltip .tooltip-type.human {
  background-color: rgba(136, 196, 200, 0.2);
  color: #88c4c8;
}

.spider-tooltip .tooltip-type.llm {
  background-color: rgba(196, 160, 212, 0.2);
  color: #c4a0d4;
}

.spider-tooltip .tooltip-type.all {
  background-color: rgba(176, 202, 151, 0.2);
  color: #b0ca97;
}

.spider-tooltip .tooltip-value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 4px;
}

.spider-tooltip .value-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.spider-tooltip .value-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-primary));
}

.spider-tooltip .tooltip-scale {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
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

/* Agreement Detail Dialog */
.agreement-detail-dialog :deep(.v-overlay__content) {
  width: min(1380px, 97vw);
}

.agreement-detail-card {
  border-radius: 16px 4px 16px 4px;
}

.agreement-detail-body {
  max-height: min(84vh, 980px);
  overflow-y: auto;
  padding-right: 12px;
}

.agreement-comparison {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 12px;
  margin-bottom: 20px;
}

.agreement-evaluator {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.agreement-evaluator-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px 4px 12px 4px;
  background-color: rgba(136, 196, 200, 0.15);
}

.agreement-evaluator.is-llm .agreement-evaluator-avatar {
  background-color: rgba(196, 160, 212, 0.15);
}

.agreement-evaluator-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.agreement-evaluator-name {
  font-weight: 600;
  font-size: 1.02rem;
  line-height: 1.25;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.agreement-evaluator-type {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.agreement-evaluator-meta {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  word-break: break-all;
}

.vs-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  flex-shrink: 0;
}

.agreement-score-section {
  display: flex;
  justify-content: center;
  padding: 28px 0;
}

.score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  border: 5px solid #b0ca97;
  background-color: rgba(var(--v-theme-surface), 1);
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.score-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.agreement-interpretation {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.interpretation-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.interpretation-badge.level-excellent {
  background-color: rgba(98, 200, 140, 0.15);
  color: #3d9a5c;
}

.interpretation-badge.level-good {
  background-color: rgba(152, 212, 187, 0.2);
  color: #4a9a7a;
}

.interpretation-badge.level-moderate {
  background-color: rgba(232, 200, 100, 0.2);
  color: #9a8030;
}

.interpretation-badge.level-low {
  background-color: rgba(232, 160, 135, 0.2);
  color: #b05a40;
}

.interpretation-badge.level-unknown {
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.agreement-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
}

.detail-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.agreement-explanation {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-radius: 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.5;
}

.agreement-explanation .v-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: rgb(var(--v-theme-primary));
}

.agreement-breakdown {
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.breakdown-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.breakdown-title {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.88);
}

.breakdown-note {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.panel-title-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 0.9rem;
  font-weight: 600;
}

.panel-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.panel-count-disagreed {
  background-color: rgba(232, 160, 135, 0.22);
  color: #aa4f33;
}

.panel-count-agreed {
  background-color: rgba(152, 212, 187, 0.28);
  color: #3d8c6b;
}

.panel-empty {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.agreement-point-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agreement-point-item {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  background-color: rgba(var(--v-theme-surface), 1);
  overflow: hidden;
}

.agreement-point-item.agreement {
  border-left: 4px solid rgba(152, 212, 187, 0.9);
}

.agreement-point-item.disagreement {
  border-left: 4px solid rgba(232, 160, 135, 0.95);
}

.agreement-point-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
  list-style: none;
}

.agreement-point-item summary::-webkit-details-marker {
  display: none;
}

.agreement-point-item summary::marker {
  content: '';
}

.agreement-point-item[open] .agreement-point-summary {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.point-label {
  flex: 1;
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.35;
  color: rgba(var(--v-theme-on-surface), 0.88);
  word-break: break-word;
}

.point-value-preview {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.62);
  text-align: right;
  max-width: 45%;
  word-break: break-word;
}

.agreement-point-body {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agreement-point-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.point-rater {
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  word-break: break-word;
}

.point-preview {
  margin: 2px 0 0;
  padding: 8px 10px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.04);
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.72);
  line-height: 1.35;
}

.panel-omitted {
  margin-top: 8px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.agreement-breakdown-unavailable {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  border-radius: 8px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  font-size: 0.83rem;
  color: rgba(var(--v-theme-on-surface), 0.68);
}

/* Responsive */
@media (max-width: 768px) {
  .dimension-visualizations-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }

  .dimension-details-grid {
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

  .agreement-detail-dialog :deep(.v-overlay__content) {
    width: min(1380px, 99vw);
  }

  .agreement-comparison {
    grid-template-columns: 1fr;
  }

  .vs-indicator {
    justify-self: center;
  }

  .point-value-preview {
    max-width: 100%;
    text-align: left;
  }

  .agreement-point-summary {
    flex-direction: column;
  }
}
</style>
