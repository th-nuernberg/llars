<template>
  <v-container class="oncoco-results">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-btn
          variant="text"
          prepend-icon="mdi-arrow-left"
          @click="router.push({ name: 'OnCoCoOverview' })"
        >
          {{ $t('oncoco.results.back') }}
        </v-btn>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-skeleton-loader v-if="isLoading('data')" type="card" height="200" class="mb-4" />

    <template v-else-if="analysis">
      <!-- Analysis Info Header -->
      <v-row class="mb-4">
        <v-col cols="12">
          <v-card>
            <v-card-title class="d-flex align-center">
              <LIcon class="mr-2" color="primary">mdi-chart-bar</LIcon>
              {{ analysis.name }}
              <v-spacer></v-spacer>
              <v-chip
                :color="getStatusColor(analysis.status)"
                :prepend-icon="getStatusIcon(analysis.status)"
              >
                {{ getStatusText(analysis.status) }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">{{ $t('oncoco.results.metrics.progress') }}</div>
                  <v-progress-linear
                    :model-value="analysis.progress || 0"
                    height="24"
                    rounded
                    :color="analysis.status === 'completed' ? 'success' : 'primary'"
                    class="mt-1"
                  >
                    <template v-slot:default="{ value }">
                      <strong>{{ Math.round(value) }}%</strong>
                    </template>
                  </v-progress-linear>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">{{ $t('oncoco.results.metrics.threads') }}</div>
                  <div class="text-h6">{{ analysis.processed_threads }} / {{ analysis.total_threads }}</div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">{{ $t('oncoco.results.metrics.sentencesAnalyzed') }}</div>
                  <div class="text-h6">{{ analysis.total_sentences?.toLocaleString() || 0 }}</div>
                </v-col>
                <v-col cols="6" sm="3">
                  <div class="text-caption text-medium-emphasis">{{ $t('oncoco.results.metrics.createdAt') }}</div>
                  <div class="text-body-1">{{ formatDate(analysis.created_at) }}</div>
                </v-col>
              </v-row>

              <!-- Start Button if pending -->
              <v-btn
                v-if="analysis.status === 'pending'"
                color="primary"
                variant="flat"
                prepend-icon="mdi-play"
                @click="startAnalysis"
                :loading="starting"
                class="mt-4"
              >
                {{ $t('oncoco.results.actions.start') }}
              </v-btn>

              <!-- Resume Button if stuck in running status (no Socket.IO updates) -->
              <div v-if="analysis.status === 'running' && isStuck" class="mt-4">
                <v-alert type="warning" density="compact" class="mb-3">
                  {{ $t('oncoco.results.stuckWarning', { seconds: stuckDuration }) }}
                </v-alert>
                <v-btn
                  color="warning"
                  variant="flat"
                  prepend-icon="mdi-refresh"
                  @click="resumeAnalysis"
                  :loading="resuming"
                >
                  {{ $t('oncoco.results.actions.resume') }}
                </v-btn>
              </div>

              <!-- Retry Button if failed -->
              <div v-if="analysis.status === 'failed'" class="mt-4">
                <v-alert type="error" density="compact" class="mb-3">
                  {{ analysis.error_message || $t('oncoco.results.failedFallback') }}
                </v-alert>
                <v-btn
                  color="warning"
                  variant="flat"
                  prepend-icon="mdi-refresh"
                  @click="startAnalysis"
                  :loading="starting"
                >
                  {{ $t('oncoco.results.actions.retry') }}
                </v-btn>
              </div>

            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Live Status Panel (only show when running) -->
      <v-row v-if="analysis.status === 'running'" class="mb-4">
        <v-col cols="12">
          <v-card color="primary" variant="tonal">
            <v-card-title class="d-flex align-center">
              <v-progress-circular indeterminate size="24" class="mr-3"></v-progress-circular>
              <span>{{ $t('oncoco.results.running.title') }}</span>
              <v-spacer></v-spacer>
              <v-chip color="success" size="small" v-if="liveData.timing">
                {{ $t('oncoco.results.running.elapsed', { duration: formatDuration(liveData.timing.elapsed_seconds) }) }}
              </v-chip>
            </v-card-title>

            <v-card-text>
              <v-row>
                <!-- Hardware Info -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <LIcon class="mr-2">mdi-chip</LIcon>
                      {{ $t('oncoco.results.live.hardware') }}
                    </v-card-title>
                    <v-card-text v-if="liveData.hardware">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.deviceType') }}</span>
                        <span class="font-weight-bold">{{ liveData.hardware.device_type }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.deviceName') }}</span>
                        <span class="font-weight-bold text-truncate" style="max-width: 150px;">{{ liveData.hardware.device_name }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.cpuCores') }}</span>
                        <span class="font-weight-bold">{{ liveData.hardware.cpu_count }} / {{ liveData.hardware.cpu_count_logical }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.cpuUsage') }}</span>
                        <v-progress-linear
                          :model-value="liveData.hardware.cpu_percent"
                          height="16"
                          rounded
                          color="primary"
                          style="max-width: 100px;"
                        >
                          <small>{{ liveData.hardware.cpu_percent }}%</small>
                        </v-progress-linear>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.memory') }}</span>
                        <span class="font-weight-bold">{{ liveData.hardware.memory_used_gb }} / {{ liveData.hardware.memory_total_gb }} GB</span>
                      </div>
                      <div class="d-flex justify-space-between" v-if="liveData.hardware.model_size_mb">
                        <span class="text-caption">{{ $t('oncoco.results.live.modelSize') }}</span>
                        <span class="font-weight-bold">{{ liveData.hardware.model_size_mb }} MB</span>
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      {{ $t('oncoco.results.live.waiting') }}
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Current Processing -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <LIcon class="mr-2">mdi-file-document-outline</LIcon>
                      {{ $t('oncoco.results.live.currentThread') }}
                    </v-card-title>
                    <v-card-text v-if="liveData.current_thread">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.pillar') }}</span>
                        <v-chip size="x-small" color="primary">{{ liveData.current_thread.pillar_name }}</v-chip>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.threadId') }}</span>
                        <span class="font-weight-bold">{{ liveData.current_thread.thread_id }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.messages') }}</span>
                        <span class="font-weight-bold">{{ liveData.current_thread.message_count }}</span>
                      </div>
                      <v-divider class="my-2"></v-divider>
                      <div v-if="liveData.current_message">
                        <div class="d-flex justify-space-between mb-2">
                          <span class="text-caption">{{ $t('oncoco.results.live.message') }}</span>
                          <span class="font-weight-bold">{{ liveData.current_message.message_index }} / {{ liveData.current_message.total_messages }}</span>
                        </div>
                        <div class="d-flex justify-space-between mb-2">
                          <span class="text-caption">{{ $t('oncoco.results.live.sender') }}</span>
                          <span class="font-weight-bold text-truncate" style="max-width: 120px;">{{ liveData.current_message.sender }}</span>
                        </div>
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      {{ $t('oncoco.results.live.waiting') }}
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- Performance -->
                <v-col cols="12" md="4">
                  <v-card variant="outlined" class="h-100">
                    <v-card-title class="text-subtitle-1">
                      <LIcon class="mr-2">mdi-speedometer</LIcon>
                      {{ $t('oncoco.results.live.performance') }}
                    </v-card-title>
                    <v-card-text v-if="liveData.timing">
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.threadsPerSecond') }}</span>
                        <span class="font-weight-bold">{{ liveData.timing.threads_per_second?.toFixed(3) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.sentencesPerSecond') }}</span>
                        <span class="font-weight-bold">{{ liveData.timing.sentences_per_second?.toFixed(1) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.elapsed') }}</span>
                        <span class="font-weight-bold">{{ formatDuration(liveData.timing.elapsed_seconds) }}</span>
                      </div>
                      <div class="d-flex justify-space-between mb-2">
                        <span class="text-caption">{{ $t('oncoco.results.live.eta') }}</span>
                        <span class="font-weight-bold text-warning">{{ formatDuration(liveData.timing.eta_seconds) }}</span>
                      </div>
                      <v-divider class="my-2"></v-divider>
                      <div class="text-caption text-medium-emphasis">
                        {{ $t('oncoco.results.live.workerSingle') }}
                      </div>
                    </v-card-text>
                    <v-card-text v-else class="text-center text-medium-emphasis">
                      {{ $t('oncoco.results.live.waiting') }}
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>

              <!-- Last Classified Sentence -->
              <v-row class="mt-3" v-if="liveData.timing?.last_sentence">
                <v-col cols="12">
                  <v-card variant="outlined">
                    <v-card-title class="text-subtitle-1 py-2">
                      <LIcon class="mr-2">mdi-message-text</LIcon>
                      {{ $t('oncoco.results.live.lastClassified') }}
                    </v-card-title>
                    <v-card-text class="py-2">
                      <div class="d-flex align-center">
                        <v-chip
                          :color="liveData.timing.last_sentence.role === 'counselor' ? 'primary' : 'secondary'"
                          size="small"
                          class="mr-3"
                        >
                          {{ liveData.timing.last_sentence.role === 'counselor' ? $t('oncoco.results.roles.counselor') : $t('oncoco.results.roles.client') }}
                        </v-chip>
                        <span class="text-body-2 mr-3" style="flex: 1;">
                          "{{ liveData.timing.last_sentence.text }}"
                        </span>
                        <v-chip color="info" size="small" class="mr-2">
                          {{ liveData.timing.last_sentence.label_display }}
                        </v-chip>
                        <v-chip
                          :color="liveData.timing.last_sentence.confidence > 80 ? 'success' : liveData.timing.last_sentence.confidence > 50 ? 'warning' : 'error'"
                          size="small"
                        >
                          {{ liveData.timing.last_sentence.confidence }}%
                        </v-chip>
                      </div>
                    </v-card-text>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Info when not completed -->
      <v-row v-if="analysis.status === 'pending'">
        <v-col cols="12">
          <v-alert type="info" prominent>
            <v-alert-title>{{ $t('oncoco.results.pending.title') }}</v-alert-title>
            {{ $t('oncoco.results.pending.subtitle') }}
          </v-alert>
        </v-col>
      </v-row>

      <v-row v-if="analysis.status === 'failed'">
        <v-col cols="12">
          <v-alert type="error" prominent>
            <v-alert-title>{{ $t('oncoco.results.failed.title') }}</v-alert-title>
            {{ analysis.error_message || $t('oncoco.results.failed.subtitle') }}
          </v-alert>
        </v-col>
      </v-row>

      <!-- Results Tabs (only show when completed) -->
      <template v-if="analysis.status === 'completed'">
        <v-row>
          <v-col cols="12">
            <v-skeleton-loader v-if="isLoading('tabs')" type="card" height="400" />
            <v-card v-else>
              <v-tabs v-model="activeTab" color="primary">
                <v-tab value="overview">{{ $t('oncoco.results.tabs.overview') }}</v-tab>
                <v-tab value="distribution">{{ $t('oncoco.results.tabs.distribution') }}</v-tab>
                <v-tab value="transitions">{{ $t('oncoco.results.tabs.transitions') }}</v-tab>
                <v-tab value="sentences">{{ $t('oncoco.results.tabs.sentences') }}</v-tab>
              </v-tabs>

              <v-card-text>
                <v-window v-model="activeTab">
                  <!-- Overview Tab -->
                  <v-window-item value="overview">
                    <v-row>
                      <v-col
                        v-for="(stats, pillarNum) in analysis.pillar_statistics"
                        :key="pillarNum"
                        cols="12"
                        md="4"
                      >
                        <v-card variant="outlined">
                          <v-card-title class="text-subtitle-1">
                            {{ $t('oncoco.results.pillarLabel', { id: pillarNum }) }}
                          </v-card-title>
                          <v-card-text>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">{{ $t('oncoco.results.overview.sentences') }}</span>
                              <span class="font-weight-bold">{{ stats.total_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">{{ $t('oncoco.results.overview.counselorSentences') }}</span>
                              <span class="font-weight-bold text-primary">{{ stats.counselor_sentences?.toLocaleString() }}</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">{{ $t('oncoco.results.overview.clientSentences') }}</span>
                              <span class="font-weight-bold text-secondary">{{ stats.client_sentences?.toLocaleString() }}</span>
                            </div>
                            <v-divider class="my-2"></v-divider>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">{{ $t('oncoco.results.overview.impactFactorRatio') }}</span>
                              <span class="font-weight-bold">{{ (stats.impact_factor_ratio * 100).toFixed(1) }}%</span>
                            </div>
                            <div class="d-flex justify-space-between mb-2">
                              <span class="text-caption">{{ $t('oncoco.results.overview.resourceActivation') }}</span>
                              <span class="font-weight-bold">{{ (stats.resource_activation_score * 100).toFixed(1) }}%</span>
                            </div>
                            <div class="d-flex justify-space-between">
                              <span class="text-caption">{{ $t('oncoco.results.overview.mutualInformation') }}</span>
                              <span class="font-weight-bold">{{ stats.mi_score?.toFixed(3) }}</span>
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>
                  </v-window-item>

                  <!-- Distribution Tab -->
                  <v-window-item value="distribution">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionPillar"
                          :items="pillarOptions"
                          :label="$t('oncoco.results.filters.pillar')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionLevel"
                          :items="levelOptions"
                          :label="$t('oncoco.results.filters.detailLevel')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="distributionRole"
                          :items="roleFilterOptions"
                          :label="$t('oncoco.results.filters.role')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                    </v-row>

                    <v-progress-linear v-if="loadingDistribution" indeterminate></v-progress-linear>

                    <!-- Distribution Table -->
                    <v-data-table
                      :headers="distributionHeaders"
                      :items="distributionData"
                      :loading="loadingDistribution"
                      :items-per-page="20"
                      density="compact"
                    >
                      <template v-slot:item.label="{ item }">
                        <div>
                          <span class="font-weight-medium">{{ item.display_name }}</span>
                          <div class="text-caption text-medium-emphasis">{{ item.label }}</div>
                        </div>
                      </template>
                      <template v-slot:item.role="{ item }">
                        <v-chip
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                          size="x-small"
                        >
                          {{ item.role === 'counselor' ? $t('oncoco.results.roles.counselor') : $t('oncoco.results.roles.client') }}
                        </v-chip>
                      </template>
                      <template v-slot:item.count="{ item }">
                        <v-progress-linear
                          :model-value="(item.count / maxDistributionCount) * 100"
                          height="20"
                          rounded
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                        >
                          <template v-slot:default>
                            <strong>{{ item.count.toLocaleString() }}</strong>
                          </template>
                        </v-progress-linear>
                      </template>
                    </v-data-table>
                  </v-window-item>

                  <!-- Transitions & Comparison Tab -->
                  <v-window-item value="transitions">
                    <!-- Controls -->
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionPillar"
                          :items="pillarOptions"
                          :label="$t('oncoco.results.filters.pillar')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionLevel"
                          :items="levelOptions"
                          :label="$t('oncoco.results.filters.detailLevel')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="transitionRole"
                          :items="roleFilterOptions"
                          :label="$t('oncoco.results.filters.role')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2">
                        <v-select
                          v-model="heatmapColorMode"
                          :items="heatmapModeOptions"
                          :label="$t('oncoco.results.filters.heatmapMode')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="2" class="d-flex align-center">
                        <v-switch
                          v-model="showHeatmapValues"
                          :label="$t('oncoco.results.filters.showValues')"
                          density="compact"
                          hide-details
                          color="primary"
                        ></v-switch>
                      </v-col>
                    </v-row>

                    <v-progress-linear v-if="loadingTransitions || loadingHeatmaps || loadingMatrixComparison" indeterminate></v-progress-linear>

                    <!-- Quick Stats Bar -->
                    <QuickStatsBar
                      v-if="matrixComparisonData"
                      :similarity="quickStatsSimilarity"
                      :frobenius-distance="quickStatsFrobenius"
                      :p-value="quickStatsPValue"
                      :chi-square-significant="quickStatsChiSignificant"
                      :chi-square-total="quickStatsChiTotal"
                      :loading="loadingMatrixComparison"
                      @show-methodology="showMethodologyDialog = true"
                    />

                    <!-- Transition Heatmaps per Pillar -->
                    <div class="text-h6 font-weight-bold mb-3">
                      <LIcon start>mdi-grid</LIcon>
                      {{ $t('oncoco.results.transitions.heatmapsTitle') }}
                    </div>

                    <v-row v-if="Object.keys(heatmapData).length > 0" class="heatmap-row">
                      <v-col
                        v-for="(data, pillarNum) in heatmapData"
                        :key="'heatmap-' + pillarNum"
                        cols="12"
                        lg="4"
                        md="6"
                        class="heatmap-col"
                      >
                        <v-card variant="outlined" class="h-100 heatmap-card">
                          <v-card-title class="text-subtitle-1 py-2">
                            <LIcon start size="small" color="primary">mdi-chart-box</LIcon>
                            {{ getPillarName(pillarNum) }}
                            <v-chip size="x-small" class="ml-2" variant="tonal">
                              {{ $t('oncoco.results.transitions.totalTransitions', { count: data.totalTransitions }) }}
                            </v-chip>
                          </v-card-title>
                          <v-card-text class="pt-0 heatmap-content">
                            <TransitionHeatmap
                              :counts="data.counts"
                              :probabilities="data.probabilities"
                              :labels="data.labels"
                              :label-displays="data.labelDisplays"
                              :show-values="showHeatmapValues"
                              :color-mode="heatmapColorMode"
                              :pillar-name="getPillarName(pillarNum)"
                              :pillar-number="pillarNum"
                              :external-highlight="hoveredTransition"
                              @cell-hover="onHeatmapCellHover"
                              @cell-leave="onHeatmapCellLeave"
                            />
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>

                    <!-- Synchronized Comparison Panel -->
                    <v-expand-transition>
                      <v-card v-if="hoveredTransition" variant="tonal" color="primary" class="mt-3">
                        <v-card-title class="text-subtitle-1 py-2">
                          <LIcon start size="small">mdi-compare</LIcon>
                          {{ $t('oncoco.results.transitions.comparisonTitle', { from: hoveredTransition.fromDisplay }) }}
                          <LIcon size="x-small" class="mx-1">mdi-arrow-right</LIcon>
                          {{ hoveredTransition.toDisplay }}
                        </v-card-title>
                        <v-card-text class="py-2">
                          <v-row dense>
                            <v-col
                              v-for="(data, pillarNum) in heatmapData"
                              :key="'compare-' + pillarNum"
                              cols="12"
                              :sm="12 / Object.keys(heatmapData).length"
                            >
                              <div class="text-center">
                                <div class="text-caption text-medium-emphasis">{{ getPillarName(pillarNum) }}</div>
                                <div class="text-h5 font-weight-bold">
                                  {{ getTransitionCount(pillarNum, hoveredTransition.from, hoveredTransition.to) }}
                                </div>
                                <div class="text-caption">
                                  {{ (getTransitionProbability(pillarNum, hoveredTransition.from, hoveredTransition.to) * 100).toFixed(1) }}%
                                </div>
                              </div>
                            </v-col>
                          </v-row>
                        </v-card-text>
                      </v-card>
                    </v-expand-transition>

                    <v-alert v-if="!loadingHeatmaps && Object.keys(heatmapData).length === 0" type="info" variant="tonal" class="mb-4">
                      {{ $t('oncoco.results.transitions.noHeatmapData') }}
                    </v-alert>

                    <v-divider class="my-4"></v-divider>

                    <!-- Pillar Comparison Panel (NEW - replaces old Statistics tab) -->
                    <PillarComparisonPanel
                      v-if="matrixComparisonData?.pairwise_comparisons?.length > 0"
                      :comparisons="matrixComparisonData.pairwise_comparisons"
                      :loading="loadingMatrixComparison"
                      @highlight-transition="onHighlightTransition"
                    />

                    <v-divider class="my-4"></v-divider>

                    <!-- Top Transitions List (Collapsible) -->
                    <v-expansion-panels variant="accordion">
                      <v-expansion-panel>
                        <v-expansion-panel-title>
                          <LIcon start>mdi-format-list-numbered</LIcon>
                          {{ $t('oncoco.results.transitions.topTitle') }}
                          <span v-if="transitionPillar" class="text-caption ml-2">({{ $t('oncoco.results.transitions.topPillar', { id: transitionPillar }) }})</span>
                          <span v-else class="text-caption ml-2">({{ $t('oncoco.results.transitions.topAll') }})</span>
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <v-list density="compact" v-if="topTransitions.length > 0">
                            <v-list-item
                              v-for="(link, idx) in topTransitions"
                              :key="idx"
                            >
                              <template v-slot:prepend>
                                <span class="text-caption text-medium-emphasis mr-3" style="width: 20px;">{{ idx + 1 }}.</span>
                                <v-chip
                                  size="small"
                                  :color="link.source.startsWith('CO-') ? 'primary' : 'secondary'"
                                  class="mr-2"
                                >
                                  {{ link.source_display }}
                                </v-chip>
                              </template>
                              <v-list-item-title class="d-flex align-center">
                                <LIcon size="small" class="mx-2">mdi-arrow-right</LIcon>
                                <v-chip
                                  size="small"
                                  :color="link.target.startsWith('CO-') ? 'primary' : 'secondary'"
                                >
                                  {{ link.target_display }}
                                </v-chip>
                              </v-list-item-title>
                              <template v-slot:append>
                                <div class="text-right">
                                  <div class="font-weight-bold">{{ link.value }}</div>
                                  <div class="text-caption">{{ (link.probability * 100).toFixed(1) }}%</div>
                                </div>
                              </template>
                            </v-list-item>
                          </v-list>
                          <v-alert v-else-if="!loadingTransitions" type="info" variant="tonal">
                            {{ $t('oncoco.results.transitions.noTransitionData') }}
                          </v-alert>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-window-item>

                  <!-- Methodology Dialog -->
                  <v-dialog v-model="showMethodologyDialog" max-width="900" scrollable>
                    <v-card class="methodology-dialog-card" rounded="lg">
                      <!-- Dialog Header with Close Button -->
                      <v-toolbar color="primary" density="compact">
                        <LIcon class="ml-2">mdi-chart-scatter-plot</LIcon>
                        <v-toolbar-title class="text-body-1 font-weight-medium">
                          {{ $t('oncoco.results.methodology.title') }}
                        </v-toolbar-title>
                        <v-spacer></v-spacer>
                        <v-btn
                          icon="mdi-close"
                          variant="text"
                          @click="showMethodologyDialog = false"
                        ></v-btn>
                      </v-toolbar>

                      <!-- Content with padding -->
                      <v-card-text class="pa-6">
                        <MatrixComparisonMetrics :analysis-id="route.params.id" hide-header />
                      </v-card-text>
                    </v-card>
                  </v-dialog>

                  <!-- Sentences Tab -->
                  <v-window-item value="sentences">
                    <v-row class="mb-4">
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="sentencePillar"
                          :items="pillarOptions"
                          :label="$t('oncoco.results.filters.pillar')"
                          variant="outlined"
                          density="compact"
                          clearable
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-select
                          v-model="sentenceRole"
                          :items="sentenceRoleOptions"
                          :label="$t('oncoco.results.filters.role')"
                          variant="outlined"
                          density="compact"
                        ></v-select>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-text-field
                          v-model="sentenceLabel"
                          :label="$t('oncoco.results.filters.label')"
                          :placeholder="$t('oncoco.results.filters.labelPlaceholder')"
                          variant="outlined"
                          density="compact"
                          clearable
                        ></v-text-field>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <v-btn
                          color="primary"
                          variant="flat"
                          @click="loadSentences"
                          :loading="loadingSentences"
                          block
                        >
                          {{ $t('oncoco.results.actions.load') }}
                        </v-btn>
                      </v-col>
                    </v-row>

                    <v-data-table
                      :headers="sentenceHeaders"
                      :items="sentences"
                      :loading="loadingSentences"
                      :items-per-page="20"
                      density="compact"
                    >
                      <template v-slot:item.sentence_text="{ item }">
                        <div class="sentence-text">{{ item.sentence_text }}</div>
                      </template>
                      <template v-slot:item.role="{ item }">
                        <v-chip
                          :color="item.role === 'counselor' ? 'primary' : 'secondary'"
                          size="x-small"
                        >
                          {{ item.role === 'counselor' ? $t('oncoco.results.roles.counselor') : $t('oncoco.results.roles.client') }}
                        </v-chip>
                      </template>
                      <template v-slot:item.label="{ item }">
                        <div>
                          <div class="font-weight-medium">{{ item.label_display }}</div>
                          <div class="text-caption text-medium-emphasis">{{ item.label }}</div>
                        </div>
                      </template>
                      <template v-slot:item.confidence="{ item }">
                        <v-progress-linear
                          :model-value="item.confidence * 100"
                          height="16"
                          rounded
                          :color="item.confidence > 0.8 ? 'success' : item.confidence > 0.5 ? 'warning' : 'error'"
                        >
                          <template v-slot:default>
                            <small>{{ (item.confidence * 100).toFixed(0) }}%</small>
                          </template>
                        </v-progress-linear>
                      </template>
                    </v-data-table>

                    <div class="text-center mt-4" v-if="sentencesTotal > sentences.length">
                      <v-btn
                        variant="outlined"
                        @click="loadMoreSentences"
                        :loading="loadingSentences"
                      >
                        {{ $t('oncoco.results.actions.loadMore', { loaded: sentences.length, total: sentencesTotal }) }}
                      </v-btn>
                    </div>
                  </v-window-item>
                </v-window>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </template>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';
import TransitionHeatmap from './TransitionHeatmap.vue';
import MatrixComparisonMetrics from './MatrixComparisonMetrics.vue';
import QuickStatsBar from './QuickStatsBar.vue';
import PillarComparisonPanel from './PillarComparisonPanel.vue';
import {
  useOnCoCoAnalysis,
  useOnCoCoSocket,
  useOnCoCoHelpers
} from './OnCoCoResults/composables';

const router = useRouter();
const route = useRoute();
const { t } = useI18n();

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['data', 'tabs']);

// Local UI State
const activeTab = ref('overview');
const showMethodologyDialog = ref(false);
const levelOptions = computed(() => [
  { title: t('oncoco.results.levelOptions.level2'), value: 'level2' },
  { title: t('oncoco.results.levelOptions.full'), value: 'full' }
]);
const heatmapModeOptions = computed(() => [
  { title: t('oncoco.results.heatmapModes.count'), value: 'count' },
  { title: t('oncoco.results.heatmapModes.probability'), value: 'probability' }
]);
const sentenceRoleOptions = computed(() => [
  { title: t('oncoco.results.roles.all'), value: '' },
  { title: t('oncoco.results.roles.counselor'), value: 'counselor' },
  { title: t('oncoco.results.roles.client'), value: 'client' }
]);

// Initialize composables
const analysisId = route.params.id;

const {
  // State
  analysis,
  loading,
  starting,
  resuming,
  liveData,
  // Stuck detection
  stuckDuration,
  isStuck,
  // Distribution
  distributionPillar,
  distributionLevel,
  distributionRole,
  distributionData,
  loadingDistribution,
  maxDistributionCount,
  // Transitions
  transitionPillar,
  transitionLevel,
  transitionRole,
  loadingTransitions,
  topTransitions,
  // Heatmaps
  heatmapData,
  loadingHeatmaps,
  showHeatmapValues,
  heatmapColorMode,
  hoveredTransition,
  // Matrix Comparison
  matrixComparisonData,
  loadingMatrixComparison,
  quickStatsSimilarity,
  quickStatsFrobenius,
  quickStatsPValue,
  quickStatsChiSignificant,
  quickStatsChiTotal,
  // Sentences
  sentencePillar,
  sentenceRole,
  sentenceLabel,
  sentences,
  sentencesTotal,
  loadingSentences,
  // Computed
  pillarOptions,
  roleFilterOptions,
  // Functions
  loadAnalysis,
  startAnalysis,
  resumeAnalysis,
  loadDistribution,
  loadTransitions,
  loadHeatmaps,
  loadMatrixComparison,
  loadSentences,
  loadMoreSentences,
  updateLiveData,
  clearLiveData,
  getTransitionCount,
  getTransitionProbability
} = useOnCoCoAnalysis(analysisId);

const {
  getStatusColor,
  getStatusIcon,
  getStatusText,
  getPillarName,
  formatDate,
  formatDuration,
  distributionHeaders,
  comparisonHeaders,
  sentenceHeaders
} = useOnCoCoHelpers();

// Socket.IO setup with callbacks
const analysisIdRef = ref(analysisId);
const { setupSocket, cleanupSocket } = useOnCoCoSocket(analysisIdRef, {
  onProgress: (data) => {
    updateLiveData(data);
  },
  onComplete: async (data) => {
    clearLiveData();
    await loadAnalysis();
  },
  onError: (data) => {
    console.error('[OnCoCo] Socket-Fehler:', data);
  }
});

// Heatmap Cell Hover Handlers
const onHeatmapCellHover = (data) => {
  const fromDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.from] || data.from;
  const toDisplay = heatmapData.value[data.pillar]?.labelDisplays?.[data.to] || data.to;
  hoveredTransition.value = {
    from: data.from,
    to: data.to,
    fromDisplay,
    toDisplay,
    pillar: data.pillar
  };
};

const onHeatmapCellLeave = () => {
  hoveredTransition.value = null;
};

// Handle highlight from PillarComparisonPanel
const onHighlightTransition = (transition) => {
  if (transition) {
    hoveredTransition.value = {
      from: transition.from_label,
      to: transition.to_label,
      fromDisplay: transition.from_display || transition.from_label,
      toDisplay: transition.to_display || transition.to_label,
      pillar: null
    };
  } else {
    hoveredTransition.value = null;
  }
};

// Watchers for filter changes
watch([distributionPillar, distributionLevel, distributionRole], () => {
  if (analysis.value?.status === 'completed') {
    loadDistribution();
  }
});

watch([transitionPillar, transitionLevel, transitionRole], () => {
  if (analysis.value?.status === 'completed') {
    loadTransitions();
    loadHeatmaps();
    loadMatrixComparison();
  }
});

// Lifecycle
onMounted(async () => {
  await withLoading('data', async () => {
    await loadAnalysis();
  });

  // Load tabs data after analysis is loaded
  if (analysis.value?.status === 'completed') {
    await withLoading('tabs', async () => {
      await Promise.all([
        loadDistribution(),
        loadTransitions(),
        loadHeatmaps(),
        loadMatrixComparison()
      ]);
    });
  }

  setupSocket();
});

onUnmounted(() => {
  cleanupSocket();
});
</script>

<style scoped>
.oncoco-results {
  max-width: 1600px;
  margin: 0 auto;
}

.sentence-text {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Heatmap Layout Fixes */
.heatmap-row {
  flex-wrap: wrap;
}

.heatmap-col {
  min-width: 0; /* Allow flex shrinking */
}

.heatmap-card {
  overflow: hidden;
}

.heatmap-content {
  overflow-x: auto;
  overflow-y: visible;
  padding-bottom: 12px;
}

/* Ensure cards don't overlap */
.heatmap-card :deep(.v-card-text) {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Better spacing for tabs on mobile */
@media (max-width: 960px) {
  .heatmap-col {
    margin-bottom: 16px;
  }
}

/* Methodology Dialog Styles */
.methodology-dialog-card {
  background-color: rgb(var(--v-theme-surface)) !important;
  overflow: hidden;
}

.methodology-dialog-card .v-toolbar {
  flex-shrink: 0;
}

.methodology-dialog-card .v-card-text {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
