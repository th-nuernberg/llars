<template>
  <v-container fluid class="judge-session">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.push({ name: 'JudgeOverview' })"
          ></v-btn>
          <div class="ml-2">
            <h1 class="text-h4 font-weight-bold">{{ session?.session_name || 'Judge Session' }}</h1>
            <div class="d-flex align-center mt-1">
              <v-chip
                :color="getStatusColor(session?.status)"
                :prepend-icon="getStatusIcon(session?.status)"
                size="small"
                class="mr-2"
              >
                {{ getStatusText(session?.status) }}
              </v-chip>
              <span class="text-caption text-medium-emphasis">
                Session ID: {{ sessionId }}
              </span>
            </div>
          </div>
          <v-spacer></v-spacer>

          <!-- Action Buttons -->
          <div class="d-flex gap-2">
            <v-btn
              v-if="session?.status === 'created' || session?.status === 'queued' || session?.status === 'paused'"
              color="success"
              prepend-icon="mdi-play"
              @click="startSession"
              :loading="actionLoading"
            >
              Start
            </v-btn>
            <v-btn
              v-if="session?.status === 'running'"
              color="warning"
              prepend-icon="mdi-pause"
              @click="pauseSession"
              :loading="actionLoading"
            >
              Pause
            </v-btn>
            <v-btn
              v-if="session?.status === 'completed'"
              color="primary"
              prepend-icon="mdi-chart-box"
              @click="navigateToResults"
            >
              Ergebnisse
            </v-btn>
            <v-btn
              icon="mdi-refresh"
              variant="text"
              @click="loadSession"
              :loading="loading"
            ></v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Progress Bar -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <div class="d-flex justify-space-between mb-2">
              <span class="text-subtitle-2">Fortschritt</span>
              <span class="text-subtitle-2 font-weight-bold">
                {{ session?.completed_comparisons || 0 }} / {{ session?.total_comparisons || 0 }} Vergleiche
              </span>
            </div>
            <v-progress-linear
              :model-value="progress"
              height="25"
              rounded
              :color="progress === 100 ? 'success' : 'primary'"
              striped
            >
              <template v-slot:default="{ value }">
                <strong>{{ Math.round(value) }}%</strong>
              </template>
            </v-progress-linear>

            <!-- Session Info -->
            <div class="d-flex justify-space-between mt-4 text-caption text-medium-emphasis">
              <span>Säulen: {{ session?.pillar_count }}</span>
              <span>Samples: {{ session?.samples_per_pillar }}</span>
              <span>Position-Swap: {{ session?.position_swap ? 'Ja' : 'Nein' }}</span>
              <span v-if="session?.created_at">Erstellt: {{ formatDate(session.created_at) }}</span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Queue Display - Shows ALL pending comparisons -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-playlist-play</v-icon>
            Vergleichs-Warteschlange
            <v-spacer></v-spacer>
            <v-chip size="small" color="info" class="mr-2">
              {{ queue.stats?.pending || 0 }} ausstehend
            </v-chip>
            <v-chip size="small" color="warning" class="mr-2" v-if="queue.stats?.running > 0">
              {{ queue.stats?.running || 0 }} läuft
            </v-chip>
            <v-chip size="small" color="success" class="mr-2" v-if="queue.stats?.completed > 0">
              {{ queue.stats?.completed || 0 }} fertig
            </v-chip>
            <v-btn
              icon="mdi-refresh"
              variant="text"
              size="small"
              @click="loadQueue"
              :loading="queueLoading"
            ></v-btn>
          </v-card-title>
          <v-divider></v-divider>

          <!-- Queue Table -->
          <v-data-table
            v-if="queue.pending?.length > 0 || queue.current"
            :headers="queueHeaders"
            :items="allQueueItems"
            :items-per-page="20"
            class="queue-table"
            density="compact"
          >
            <!-- Position -->
            <template v-slot:item.queue_position="{ item }">
              <span class="font-weight-bold">#{{ item.queue_position + 1 }}</span>
            </template>

            <!-- Status -->
            <template v-slot:item.status="{ item }">
              <v-chip
                size="x-small"
                :color="getQueueStatusColor(item.status)"
                variant="flat"
              >
                <v-icon start size="x-small" :class="{ 'mdi-spin': item.status === 'running' }">
                  {{ getQueueStatusIcon(item.status) }}
                </v-icon>
                {{ getQueueStatusText(item.status) }}
              </v-chip>
            </template>

            <!-- Pillar A -->
            <template v-slot:item.pillar_a="{ item }">
              <v-chip size="small" color="blue" variant="outlined">
                {{ item.pillar_a_name }}
              </v-chip>
            </template>

            <!-- VS -->
            <template v-slot:item.vs="{ item }">
              <v-icon size="small">mdi-arrow-left-right</v-icon>
            </template>

            <!-- Pillar B -->
            <template v-slot:item.pillar_b="{ item }">
              <v-chip size="small" color="green" variant="outlined">
                {{ item.pillar_b_name }}
              </v-chip>
            </template>

            <!-- Result (if completed) -->
            <template v-slot:item.result="{ item }">
              <template v-if="item.winner">
                <v-chip size="x-small" :color="item.winner === 'A' ? 'blue' : 'green'" variant="flat">
                  <v-icon start size="x-small">mdi-trophy</v-icon>
                  {{ item.winner }}
                </v-chip>
              </template>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
          </v-data-table>

          <!-- Empty State -->
          <v-card-text v-else class="text-center py-8 text-medium-emphasis">
            <v-icon size="48" class="mb-2">mdi-playlist-remove</v-icon>
            <div>Keine Vergleiche in der Warteschlange</div>
            <div class="text-caption mt-1">
              Konfigurieren Sie die Session um Vergleiche zu erstellen
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Current Comparison View -->
    <v-row v-if="currentComparison">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-eye</v-icon>
            Aktueller Vergleich
            <v-spacer></v-spacer>
            <!-- Live Stream Button -->
            <v-btn
              v-if="session?.status === 'running'"
              color="error"
              variant="tonal"
              size="small"
              class="mr-2"
              :loading="reconnecting"
              @click="reconnectToStream"
            >
              <v-icon start :class="{ 'pulse-icon': isStreaming }">mdi-broadcast</v-icon>
              {{ isStreaming ? 'Live' : 'Verbinden' }}
            </v-btn>
            <!-- Fullscreen Button -->
            <v-btn
              color="primary"
              variant="tonal"
              size="small"
              class="mr-2"
              @click="openFullscreen"
            >
              <v-icon start>mdi-fullscreen</v-icon>
              Vollbild
            </v-btn>
            <v-chip size="small" variant="outlined">
              Vergleich {{ (currentComparison.comparison_index || 0) + 1 }} von {{ session?.total_comparisons }}
            </v-chip>
          </v-card-title>
          <v-divider></v-divider>

          <v-card-text>
            <v-row>
              <!-- Thread A -->
              <v-col cols="12" md="5">
                <div class="thread-container">
                  <div class="thread-header">
                    <v-chip color="blue" variant="flat" prepend-icon="mdi-alpha-a-circle">
                      Thread A - {{ currentComparison.pillar_a_name }}
                    </v-chip>
                  </div>
                  <v-card variant="outlined" class="mt-2 thread-card">
                    <v-card-text class="pa-3">
                      <div v-for="(msg, idx) in currentComparison.thread_a_messages" :key="idx" class="message-item mb-3">
                        <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                          <v-icon size="small" class="mr-1">
                            {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                          </v-icon>
                          {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                        </div>
                        <div class="message-content">{{ msg.content }}</div>
                      </div>
                    </v-card-text>
                  </v-card>
                </div>
              </v-col>

              <!-- Center: LLM Evaluation -->
              <v-col cols="12" md="2">
                <div class="evaluation-center">
                  <!-- LLM Status -->
                  <v-card variant="outlined" class="text-center mb-3">
                    <v-card-text class="pa-2">
                      <v-icon
                        :color="currentComparison.llm_status === 'completed' ? 'success' : 'info'"
                        size="32"
                        :class="{ 'rotating': currentComparison.llm_status === 'running' }"
                      >
                        {{ currentComparison.llm_status === 'completed' ? 'mdi-check-circle' : 'mdi-loading' }}
                      </v-icon>
                      <div class="text-caption mt-1">
                        {{ currentComparison.llm_status === 'completed' ? 'Bewertet' : 'Bewertet...' }}
                      </div>
                    </v-card-text>
                  </v-card>

                  <!-- Winner Display -->
                  <v-card
                    v-if="currentComparison.winner"
                    variant="outlined"
                    :color="currentComparison.winner === 'A' ? 'blue' : 'green'"
                    class="text-center winner-card"
                  >
                    <v-card-text class="pa-3">
                      <v-icon size="48" color="warning">mdi-trophy</v-icon>
                      <div class="text-h5 font-weight-bold mt-2">
                        {{ currentComparison.winner }}
                      </div>
                      <div class="text-caption">Gewinner</div>
                    </v-card-text>
                  </v-card>

                  <!-- Confidence Score -->
                  <v-card v-if="currentComparison.confidence_score" variant="outlined" class="text-center mt-3">
                    <v-card-text class="pa-2">
                      <div class="text-caption text-medium-emphasis">Konfidenz</div>
                      <div class="text-h6 font-weight-bold">
                        {{ Math.round(currentComparison.confidence_score * 100) }}%
                      </div>
                    </v-card-text>
                  </v-card>
                </div>
              </v-col>

              <!-- Thread B -->
              <v-col cols="12" md="5">
                <div class="thread-container">
                  <div class="thread-header">
                    <v-chip color="green" variant="flat" prepend-icon="mdi-alpha-b-circle">
                      Thread B - {{ currentComparison.pillar_b_name }}
                    </v-chip>
                  </div>
                  <v-card variant="outlined" class="mt-2 thread-card">
                    <v-card-text class="pa-3">
                      <div v-for="(msg, idx) in currentComparison.thread_b_messages" :key="idx" class="message-item mb-3">
                        <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                          <v-icon size="small" class="mr-1">
                            {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                          </v-icon>
                          {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                        </div>
                        <div class="message-content">{{ msg.content }}</div>
                      </div>
                    </v-card-text>
                  </v-card>
                </div>
              </v-col>
            </v-row>

            <!-- LLM Prompt Display -->
            <v-expansion-panels class="mt-4" v-model="expandedPanels">
              <v-expansion-panel value="prompt">
                <v-expansion-panel-title>
                  <v-icon class="mr-2">mdi-message-text</v-icon>
                  LLM Prompt (an das Modell gesendet)
                  <v-chip size="x-small" class="ml-2" color="info">{{ currentComparison.llm_prompt?.length || 0 }} Zeichen</v-chip>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                    <strong>System Prompt:</strong> {{ currentComparison.llm_system_prompt }}
                  </v-alert>
                  <pre class="prompt-preview">{{ currentComparison.llm_prompt }}</pre>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- LLM Stream Output - Live Formatted -->
              <v-expansion-panel value="stream">
                <v-expansion-panel-title>
                  <v-icon class="mr-2" :class="{ 'rotating': isStreaming }">
                    {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
                  </v-icon>
                  LLM Ausgabe (Live Stream)
                  <v-chip size="x-small" class="ml-2" :color="isStreaming ? 'warning' : (llmStreamContent ? 'success' : 'grey')">
                    {{ isStreaming ? 'Streamt...' : (llmStreamContent ? 'Fertig' : 'Warte...') }}
                  </v-chip>
                  <v-chip size="x-small" class="ml-1" color="info" v-if="llmStreamContent">
                    {{ llmStreamContent.length }} Zeichen
                  </v-chip>
                </v-expansion-panel-title>
                <v-expansion-panel-text class="stream-panel-content">
                  <!-- Stream Status Header -->
                  <v-alert
                    :type="isStreaming ? 'warning' : 'info'"
                    variant="tonal"
                    density="compact"
                    class="mb-3"
                  >
                    <div class="d-flex align-center justify-space-between">
                      <span>
                        <strong>Vergleich #{{ currentComparison.comparison_index + 1 }}:</strong>
                        {{ currentComparison.pillar_a_name }} vs {{ currentComparison.pillar_b_name }}
                      </span>
                      <v-chip
                        size="x-small"
                        :color="isStreaming ? 'warning' : 'success'"
                        class="ml-2"
                      >
                        <v-icon start size="x-small" :class="{ 'rotating': isStreaming }">
                          {{ isStreaming ? 'mdi-loading' : 'mdi-check' }}
                        </v-icon>
                        {{ isStreaming ? 'LLM generiert...' : 'Abgeschlossen' }}
                      </v-chip>
                    </div>
                  </v-alert>

                  <!-- Formatted JSON Output (when valid JSON detected) -->
                  <div v-if="parsedStreamJson" class="formatted-json-output mb-3">
                    <v-card variant="outlined" class="pa-3">
                      <div class="text-subtitle-2 font-weight-bold mb-2 d-flex align-center">
                        <v-icon class="mr-1" size="small" color="success">mdi-check-circle</v-icon>
                        Strukturierte Bewertung
                      </div>

                      <!-- Winner Display -->
                      <v-row class="mb-3">
                        <v-col cols="4">
                          <v-card
                            :color="parsedStreamJson.winner === 'A' ? 'success' : 'grey-lighten-3'"
                            variant="tonal"
                            class="text-center pa-2"
                          >
                            <div class="text-h5 font-weight-bold">A</div>
                            <div class="text-caption">{{ currentComparison.pillar_a_name }}</div>
                          </v-card>
                        </v-col>
                        <v-col cols="4" class="d-flex align-center justify-center">
                          <v-chip
                            :color="parsedStreamJson.winner === 'TIE' ? 'warning' : 'primary'"
                            size="large"
                          >
                            <v-icon start>mdi-trophy</v-icon>
                            {{ parsedStreamJson.winner || '?' }}
                          </v-chip>
                        </v-col>
                        <v-col cols="4">
                          <v-card
                            :color="parsedStreamJson.winner === 'B' ? 'success' : 'grey-lighten-3'"
                            variant="tonal"
                            class="text-center pa-2"
                          >
                            <div class="text-h5 font-weight-bold">B</div>
                            <div class="text-caption">{{ currentComparison.pillar_b_name }}</div>
                          </v-card>
                        </v-col>
                      </v-row>

                      <!-- Confidence -->
                      <div v-if="parsedStreamJson.confidence" class="mb-3">
                        <div class="text-caption text-medium-emphasis">Konfidenz</div>
                        <v-progress-linear
                          :model-value="parsedStreamJson.confidence * 100"
                          :color="parsedStreamJson.confidence >= 0.8 ? 'success' : parsedStreamJson.confidence >= 0.6 ? 'info' : 'warning'"
                          height="20"
                          rounded
                        >
                          <template v-slot:default="{ value }">
                            <strong>{{ Math.round(value) }}%</strong>
                          </template>
                        </v-progress-linear>
                      </div>

                      <!-- Criteria Scores -->
                      <div v-if="parsedStreamJson.criteria_scores" class="criteria-scores">
                        <div class="text-subtitle-2 font-weight-bold mb-2">Kriterien-Bewertungen</div>
                        <v-table density="compact">
                          <thead>
                            <tr>
                              <th>Kriterium</th>
                              <th class="text-center">A</th>
                              <th class="text-center">B</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(scores, criterion) in parsedStreamJson.criteria_scores" :key="criterion">
                              <td>{{ formatCriterionName(criterion) }}</td>
                              <td class="text-center">
                                <v-chip size="x-small" :color="getScoreColor(scores.score_a)">
                                  {{ scores.score_a }}/5
                                </v-chip>
                              </td>
                              <td class="text-center">
                                <v-chip size="x-small" :color="getScoreColor(scores.score_b)">
                                  {{ scores.score_b }}/5
                                </v-chip>
                              </td>
                            </tr>
                          </tbody>
                        </v-table>
                      </div>

                      <!-- Final Justification -->
                      <div v-if="parsedStreamJson.final_justification" class="mt-3">
                        <div class="text-subtitle-2 font-weight-bold mb-1">Begründung</div>
                        <div class="text-body-2 justification-text">{{ parsedStreamJson.final_justification }}</div>
                      </div>
                    </v-card>
                  </div>

                  <!-- Raw Stream Output -->
                  <div class="stream-output-container">
                    <div class="d-flex align-center justify-space-between mb-2">
                      <span class="text-subtitle-2">Raw Stream Output</span>
                      <v-btn
                        size="x-small"
                        variant="text"
                        @click="copyStreamToClipboard"
                        :disabled="!llmStreamContent"
                      >
                        <v-icon start size="small">mdi-content-copy</v-icon>
                        Kopieren
                      </v-btn>
                    </div>
                    <div class="stream-output" ref="streamOutput" @scroll="handleStreamScroll">
                      <pre v-if="llmStreamContent" class="stream-pre">{{ llmStreamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
                      <div v-else class="text-center text-medium-emphasis py-4">
                        <v-progress-circular v-if="isStreaming" indeterminate color="primary" class="mb-2"></v-progress-circular>
                        <v-icon v-else size="32" class="mb-2">mdi-text-box-outline</v-icon>
                        <div>{{ isStreaming ? 'Warte auf LLM-Ausgabe...' : 'Stream startet wenn der Vergleich beginnt' }}</div>
                      </div>
                      <!-- Follow Button (appears when user scrolls up) -->
                      <v-btn
                        v-if="!autoScrollEnabled && isStreaming"
                        class="follow-btn"
                        color="primary"
                        size="small"
                        rounded
                        @click="enableAutoScroll"
                      >
                        <v-icon start>mdi-arrow-down</v-icon>
                        Folgen
                      </v-btn>
                    </div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Chain of Thought -->
              <v-expansion-panel v-if="currentComparison.chain_of_thought" value="cot">
                <v-expansion-panel-title>
                  <v-icon class="mr-2">mdi-brain</v-icon>
                  Chain-of-Thought Reasoning
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <div v-for="(step, idx) in currentComparison.chain_of_thought" :key="idx" class="cot-step mb-3">
                    <div class="text-subtitle-2 font-weight-bold">{{ step.step_name }}</div>
                    <div class="text-body-2 mt-1">{{ step.reasoning }}</div>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- JSON Preview -->
              <v-expansion-panel value="json">
                <v-expansion-panel-title>
                  <v-icon class="mr-2">mdi-code-json</v-icon>
                  JSON Rohdaten
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <pre class="json-preview">{{ JSON.stringify(currentComparison, null, 2) }}</pre>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Comparison History -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-history</v-icon>
            Verlauf ({{ completedComparisons.length }} abgeschlossene Vergleiche)
          </v-card-title>
          <v-divider></v-divider>

          <v-data-table
            :headers="historyHeaders"
            :items="completedComparisons"
            :items-per-page="10"
            class="history-table"
          >
            <!-- Index -->
            <template v-slot:item.comparison_index="{ item }">
              <span class="font-weight-bold">#{{ item.comparison_index + 1 }}</span>
            </template>

            <!-- Pillars -->
            <template v-slot:item.pillars="{ item }">
              <div class="d-flex gap-1">
                <v-chip size="small" color="blue" variant="outlined">{{ item.pillar_a_name }}</v-chip>
                <v-icon size="small">mdi-arrow-left-right</v-icon>
                <v-chip size="small" color="green" variant="outlined">{{ item.pillar_b_name }}</v-chip>
              </div>
            </template>

            <!-- Winner -->
            <template v-slot:item.winner="{ item }">
              <v-chip
                size="small"
                :color="item.winner === 'A' ? 'blue' : item.winner === 'B' ? 'green' : 'grey'"
                variant="flat"
              >
                <v-icon start size="small">mdi-trophy</v-icon>
                {{ item.winner || 'TBD' }}
              </v-chip>
            </template>

            <!-- Confidence -->
            <template v-slot:item.confidence_score="{ item }">
              <v-chip
                v-if="item.confidence_score"
                size="small"
                :color="getConfidenceColor(item.confidence_score)"
                variant="outlined"
              >
                {{ Math.round(item.confidence_score * 100) }}%
              </v-chip>
              <span v-else>-</span>
            </template>

            <!-- Timestamp -->
            <template v-slot:item.evaluated_at="{ item }">
              {{ formatDate(item.evaluated_at) }}
            </template>

            <!-- Actions -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                icon="mdi-eye"
                size="small"
                variant="text"
                @click="viewComparison(item)"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>

  <!-- Fullscreen Dialog -->
  <v-dialog
    v-model="fullscreenMode"
    fullscreen
    transition="dialog-bottom-transition"
    class="fullscreen-dialog"
  >
    <v-card class="fullscreen-card d-flex flex-column">
      <!-- Header -->
      <v-toolbar color="primary" density="compact">
        <v-btn icon @click="closeFullscreen">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>
          <v-icon class="mr-2" :class="{ 'pulse-icon': isStreaming }">mdi-broadcast</v-icon>
          Live Vergleich #{{ (currentComparison?.comparison_index || 0) + 1 }}
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-chip
          :color="isStreaming ? 'error' : 'success'"
          class="mr-2"
          variant="flat"
        >
          <v-icon start size="small" :class="{ 'rotating': isStreaming }">
            {{ isStreaming ? 'mdi-loading' : 'mdi-check-circle' }}
          </v-icon>
          {{ isStreaming ? 'Streamt...' : 'Abgeschlossen' }}
        </v-chip>
        <v-chip color="white" variant="outlined" class="mr-2">
          {{ currentComparison?.pillar_a_name }} vs {{ currentComparison?.pillar_b_name }}
        </v-chip>
      </v-toolbar>

      <!-- Main Content -->
      <v-container fluid class="flex-grow-1 pa-4 fullscreen-content">
        <v-row class="h-100">
          <!-- Left: Thread A -->
          <v-col cols="12" md="3" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-blue py-2">
                <v-icon class="mr-2">mdi-alpha-a-circle</v-icon>
                Thread A - {{ currentComparison?.pillar_a_name }}
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="flex-grow-1 overflow-y-auto thread-scroll">
                <div v-for="(msg, idx) in currentComparison?.thread_a_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content text-body-2">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Center: Live Stream -->
          <v-col cols="12" md="6" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-primary py-2 d-flex align-center">
                <v-icon class="mr-2" :class="{ 'rotating': isStreaming }">
                  {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
                </v-icon>
                LLM Live Output
                <v-spacer></v-spacer>
                <!-- Display Mode Toggle -->
                <v-btn-toggle
                  v-model="streamDisplayMode"
                  density="compact"
                  mandatory
                  class="mr-2"
                  color="white"
                  variant="outlined"
                >
                  <v-btn value="raw" size="small">
                    <v-icon start size="small">mdi-code-braces</v-icon>
                    Raw
                  </v-btn>
                  <v-btn value="formatted" size="small">
                    <v-icon start size="small">mdi-format-list-bulleted</v-icon>
                    Formatiert
                  </v-btn>
                </v-btn-toggle>
                <v-chip size="small" color="white" variant="outlined" class="mr-2">
                  {{ llmStreamContent.length }} Zeichen
                </v-chip>
                <v-btn
                  icon="mdi-content-copy"
                  size="small"
                  variant="text"
                  @click="copyStreamToClipboard"
                  :disabled="!llmStreamContent"
                ></v-btn>
              </v-card-title>
              <v-divider></v-divider>

              <!-- Result Display - ALWAYS VISIBLE with Likert Scales -->
              <div class="pa-3 result-display-header">
                <v-row dense>
                  <!-- Side A with Name -->
                  <v-col cols="4" class="text-center">
                    <v-card
                      :color="parsedStreamJson?.winner === 'A' ? 'success' : (isStreaming ? 'grey-darken-1' : 'grey-lighten-2')"
                      variant="tonal"
                      class="pa-3 winner-card-fullscreen"
                      :class="{ 'winner-highlight': parsedStreamJson?.winner === 'A' }"
                    >
                      <div class="text-h4 font-weight-bold">A</div>
                      <div class="text-caption">{{ currentComparison?.pillar_a_name }}</div>
                    </v-card>
                  </v-col>

                  <!-- Center: Winner + Confidence -->
                  <v-col cols="4" class="d-flex flex-column align-center justify-center">
                    <v-chip
                      :color="parsedStreamJson?.winner ? 'primary' : 'grey'"
                      size="x-large"
                      class="mb-2"
                      :class="{ 'pulse-chip': isStreaming && !parsedStreamJson?.winner }"
                    >
                      <v-icon start :class="{ 'rotating': isStreaming && !parsedStreamJson?.winner }">
                        {{ isStreaming && !parsedStreamJson?.winner ? 'mdi-loading' : 'mdi-trophy' }}
                      </v-icon>
                      {{ parsedStreamJson?.winner || (isStreaming ? '...' : '?') }}
                    </v-chip>
                    <div class="text-center">
                      <div class="text-caption text-medium-emphasis">Konfidenz</div>
                      <div class="text-h6 font-weight-bold">
                        {{ parsedStreamJson?.confidence ? Math.round(parsedStreamJson.confidence * 100) + '%' : (isStreaming ? '...' : '-') }}
                      </div>
                    </div>
                  </v-col>

                  <!-- Side B with Name -->
                  <v-col cols="4" class="text-center">
                    <v-card
                      :color="parsedStreamJson?.winner === 'B' ? 'success' : (isStreaming ? 'grey-darken-1' : 'grey-lighten-2')"
                      variant="tonal"
                      class="pa-3 winner-card-fullscreen"
                      :class="{ 'winner-highlight': parsedStreamJson?.winner === 'B' }"
                    >
                      <div class="text-h4 font-weight-bold">B</div>
                      <div class="text-caption">{{ currentComparison?.pillar_b_name }}</div>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- Likert Scales for all criteria - ALWAYS visible with placeholders -->
                <v-row dense class="mt-3">
                  <v-col cols="12">
                    <div class="likert-scales-container">
                      <div
                        v-for="criterion in SCORE_CRITERIA"
                        :key="criterion.key"
                        class="likert-row"
                      >
                        <!-- Criterion Label -->
                        <div class="likert-label text-caption">{{ criterion.label }}</div>

                        <!-- A Score Likert -->
                        <div class="likert-scale likert-a">
                          <div
                            v-for="n in 5"
                            :key="`a-${n}`"
                            class="likert-dot"
                            :class="{
                              'likert-active': parsedStreamJson?.scores?.A?.[criterion.key] >= n,
                              'likert-pending': !parsedStreamJson?.scores?.A?.[criterion.key] && isStreaming,
                              'likert-a-color': parsedStreamJson?.scores?.A?.[criterion.key] >= n
                            }"
                          >
                            <span v-if="n === parsedStreamJson?.scores?.A?.[criterion.key]" class="likert-value">{{ n }}</span>
                          </div>
                        </div>

                        <!-- VS Divider -->
                        <div class="likert-vs text-caption text-medium-emphasis">vs</div>

                        <!-- B Score Likert -->
                        <div class="likert-scale likert-b">
                          <div
                            v-for="n in 5"
                            :key="`b-${n}`"
                            class="likert-dot"
                            :class="{
                              'likert-active': parsedStreamJson?.scores?.B?.[criterion.key] >= n,
                              'likert-pending': !parsedStreamJson?.scores?.B?.[criterion.key] && isStreaming,
                              'likert-b-color': parsedStreamJson?.scores?.B?.[criterion.key] >= n
                            }"
                          >
                            <span v-if="n === parsedStreamJson?.scores?.B?.[criterion.key]" class="likert-value">{{ n }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </v-col>
                </v-row>
              </div>

              <v-divider></v-divider>

              <!-- Stream Output - Raw or Formatted -->
              <v-card-text
                class="flex-grow-1 overflow-y-auto stream-scroll position-relative"
                ref="fullscreenStreamOutput"
                @scroll="handleStreamScroll"
              >
                <!-- Empty State -->
                <div v-if="!llmStreamContent" class="d-flex flex-column align-center justify-center h-100 text-medium-emphasis">
                  <v-progress-circular v-if="isStreaming" indeterminate size="64" color="primary" class="mb-4"></v-progress-circular>
                  <v-icon v-else size="64" class="mb-4">mdi-text-box-outline</v-icon>
                  <div class="text-h6">{{ isStreaming ? 'Warte auf LLM-Ausgabe...' : 'Stream startet wenn der Vergleich beginnt' }}</div>
                </div>

                <!-- RAW Mode -->
                <pre v-else-if="streamDisplayMode === 'raw'" class="stream-pre-fullscreen">{{ llmStreamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>

                <!-- FORMATTED Mode -->
                <div v-else class="formatted-stream-view">
                  <!-- Pre-structured Step Areas - ALL 6 steps always visible -->
                  <div class="structured-steps-container">
                    <div
                      v-for="(stepDef, stepKey) in STEP_DEFINITIONS"
                      :key="stepKey"
                      class="structured-step"
                      :class="{
                        'step-active': getStepByKey(stepKey),
                        'step-streaming': getStepByKey(stepKey)?.isStreaming,
                        'step-pending': !getStepByKey(stepKey) && isStreaming
                      }"
                    >
                      <!-- Step Header - Always visible -->
                      <div class="step-header d-flex align-center">
                        <v-avatar
                          size="28"
                          :color="getStepByKey(stepKey) ? 'primary' : 'grey'"
                          class="mr-2"
                        >
                          <v-icon size="16" :class="{ 'rotating': getStepByKey(stepKey)?.isStreaming }">
                            {{ getStepByKey(stepKey)?.isStreaming ? 'mdi-loading' : stepDef.icon }}
                          </v-icon>
                        </v-avatar>
                        <span class="step-title" :class="{ 'text-medium-emphasis': !getStepByKey(stepKey) }">
                          {{ stepDef.title }}
                        </span>
                        <v-spacer></v-spacer>
                        <v-icon
                          v-if="getStepByKey(stepKey) && !getStepByKey(stepKey)?.isStreaming"
                          size="small"
                          color="success"
                        >
                          mdi-check-circle
                        </v-icon>
                        <v-progress-circular
                          v-else-if="getStepByKey(stepKey)?.isStreaming"
                          indeterminate
                          size="16"
                          width="2"
                          color="warning"
                        ></v-progress-circular>
                      </div>

                      <!-- Step Content - Shows when step is active -->
                      <div class="step-content" v-if="getStepByKey(stepKey)">
                        <div class="step-text">
                          {{ getStepByKey(stepKey).content }}<span v-if="getStepByKey(stepKey)?.isStreaming" class="cursor-blink">|</span>
                        </div>
                      </div>

                      <!-- Placeholder when waiting -->
                      <div class="step-placeholder" v-else-if="isStreaming">
                        <span class="text-caption text-medium-emphasis">Warte auf Analyse...</span>
                      </div>
                    </div>
                  </div>

                  <!-- Final Justification - at the bottom -->
                  <div v-if="parsedStreamJson?.final_justification" class="justification-section mt-4">
                    <div class="d-flex align-center mb-2">
                      <v-icon size="small" color="primary" class="mr-2">mdi-text-box-check</v-icon>
                      <span class="text-subtitle-2 font-weight-bold">Abschließende Begründung</span>
                    </div>
                    <v-card variant="tonal" color="primary" class="pa-3">
                      <div class="text-body-2">{{ parsedStreamJson.final_justification }}</div>
                    </v-card>
                  </div>

                  <!-- Raw JSON Preview (collapsed) -->
                  <v-expansion-panels class="mt-4" variant="accordion">
                    <v-expansion-panel>
                      <v-expansion-panel-title class="py-2">
                        <v-icon size="small" class="mr-2">mdi-code-json</v-icon>
                        <span class="text-caption">Raw JSON anzeigen</span>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <pre class="stream-pre-fullscreen text-caption">{{ llmStreamContent }}</pre>
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>
                </div>

                <!-- Follow Button - shows when auto-scroll is disabled -->
                <v-btn
                  v-if="!autoScrollEnabled && isStreaming"
                  class="follow-btn"
                  color="primary"
                  size="small"
                  rounded
                  @click="enableAutoScroll"
                >
                  <v-icon start>mdi-arrow-down</v-icon>
                  Folgen
                </v-btn>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Right: Thread B -->
          <v-col cols="12" md="3" class="d-flex flex-column">
            <v-card class="flex-grow-1 d-flex flex-column" variant="outlined">
              <v-card-title class="bg-green py-2">
                <v-icon class="mr-2">mdi-alpha-b-circle</v-icon>
                Thread B - {{ currentComparison?.pillar_b_name }}
              </v-card-title>
              <v-divider></v-divider>
              <v-card-text class="flex-grow-1 overflow-y-auto thread-scroll">
                <div v-for="(msg, idx) in currentComparison?.thread_b_messages" :key="idx" class="message-item mb-3">
                  <div class="message-role text-caption font-weight-bold mb-1" :class="msg.role === 'assistant' ? 'text-primary' : 'text-secondary'">
                    <v-icon size="small" class="mr-1">
                      {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
                    </v-icon>
                    {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                  </div>
                  <div class="message-content text-body-2">{{ msg.content }}</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>

      <!-- Footer with Progress -->
      <v-footer class="bg-surface-variant pa-2">
        <v-container fluid>
          <v-row align="center">
            <v-col cols="12" md="8">
              <v-progress-linear
                :model-value="progress"
                height="20"
                rounded
                :color="progress === 100 ? 'success' : 'primary'"
                striped
              >
                <template v-slot:default="{ value }">
                  <strong>{{ session?.completed_comparisons || 0 }} / {{ session?.total_comparisons || 0 }} ({{ Math.round(value) }}%)</strong>
                </template>
              </v-progress-linear>
            </v-col>
            <v-col cols="12" md="4" class="text-right">
              <v-chip size="small" :color="getStatusColor(session?.status)" class="mr-2">
                <v-icon start size="small">{{ getStatusIcon(session?.status) }}</v-icon>
                {{ getStatusText(session?.status) }}
              </v-chip>
              <span class="text-caption">Session: {{ session?.session_name }}</span>
            </v-col>
          </v-row>
        </v-container>
      </v-footer>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { getSocket, useSocketState } from '@/services/socketService';

const route = useRoute();
const router = useRouter();
const sessionId = route.params.id;

// State
const session = ref(null);
const currentComparison = ref(null);
const completedComparisons = ref([]);
const queue = ref({ pending: [], current: null, stats: {} });
const loading = ref(false);
const actionLoading = ref(false);
const queueLoading = ref(false);
const reconnecting = ref(false);
const fullscreenMode = ref(false);
const socket = ref(null);
const expandedPanels = ref([]);
const llmStreamContent = ref('');
const streamOutput = ref(null);
const fullscreenStreamOutput = ref(null);
const autoScrollEnabled = ref(true);
const streamDisplayMode = ref('formatted'); // 'raw' or 'formatted' - default to formatted for better UX

// Queue Table Headers
const queueHeaders = [
  { title: '#', key: 'queue_position', sortable: true, width: '60px' },
  { title: 'Status', key: 'status', sortable: true, width: '120px' },
  { title: 'Säule A', key: 'pillar_a', sortable: false },
  { title: '', key: 'vs', sortable: false, width: '50px' },
  { title: 'Säule B', key: 'pillar_b', sortable: false },
  { title: 'Ergebnis', key: 'result', sortable: false, width: '100px' }
];

// History Table Headers
const historyHeaders = [
  { title: '#', key: 'comparison_index', sortable: true },
  { title: 'Säulen', key: 'pillars', sortable: false },
  { title: 'Gewinner', key: 'winner', sortable: true },
  { title: 'Konfidenz', key: 'confidence_score', sortable: true },
  { title: 'Zeitpunkt', key: 'evaluated_at', sortable: true },
  { title: 'Aktionen', key: 'actions', sortable: false }
];

// Computed
const progress = computed(() => {
  if (!session.value || !session.value.total_comparisons) return 0;
  return (session.value.completed_comparisons / session.value.total_comparisons) * 100;
});

// Check if LLM is currently streaming
const isStreaming = computed(() => {
  return currentComparison.value?.llm_status === 'running';
});

// Step definitions with German titles
const STEP_DEFINITIONS = {
  'step_1': { title: 'Analyse Berater-Kohärenz', icon: 'mdi-account-tie' },
  'step_2': { title: 'Analyse Klienten-Kohärenz', icon: 'mdi-account' },
  'step_3': { title: 'Analyse Beratungsqualität', icon: 'mdi-star' },
  'step_4': { title: 'Analyse Empathie', icon: 'mdi-heart' },
  'step_5': { title: 'Analyse Authentizität', icon: 'mdi-check-decagram' },
  'step_6': { title: 'Analyse Lösungsorientierung', icon: 'mdi-lightbulb' }
};

// Score criteria mapping
const SCORE_CRITERIA = [
  { key: 'counsellor_coherence', label: 'Berater-Kohärenz' },
  { key: 'client_coherence', label: 'Klienten-Kohärenz' },
  { key: 'quality', label: 'Qualität' },
  { key: 'empathy', label: 'Empathie' },
  { key: 'authenticity', label: 'Authentizität' },
  { key: 'solution_orientation', label: 'Lösungsorientierung' }
];

// Parse stream content incrementally - extracts partial data while streaming
const parsedStreamJson = computed(() => {
  if (!llmStreamContent.value) return null;

  const content = llmStreamContent.value.trim();
  const result = {
    winner: null,
    confidence: null,
    scores: { A: {}, B: {} },
    final_justification: null,
    criteria_scores: null
  };

  // Try to parse complete JSON first
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.winner || parsed.criteria_scores || parsed.confidence || parsed.scores) {
        // Convert scores format if needed
        if (parsed.scores) {
          result.scores = parsed.scores;
          // Also build criteria_scores for compatibility
          result.criteria_scores = {};
          for (const criterion of SCORE_CRITERIA) {
            if (parsed.scores.A?.[criterion.key] !== undefined || parsed.scores.B?.[criterion.key] !== undefined) {
              result.criteria_scores[criterion.key] = {
                score_a: parsed.scores.A?.[criterion.key] || 0,
                score_b: parsed.scores.B?.[criterion.key] || 0
              };
            }
          }
        }
        if (parsed.criteria_scores) {
          result.criteria_scores = parsed.criteria_scores;
        }
        result.winner = parsed.winner || null;
        result.confidence = parsed.confidence || null;
        result.final_justification = parsed.final_justification || null;
        return result;
      }
    }
  } catch (e) {
    // JSON not complete - try incremental parsing
  }

  // Incremental parsing for partial JSON
  // Extract winner
  const winnerMatch = content.match(/"winner"\s*:\s*"([AB])"/);
  if (winnerMatch) result.winner = winnerMatch[1];

  // Extract confidence
  const confMatch = content.match(/"confidence"\s*:\s*([\d.]+)/);
  if (confMatch) result.confidence = parseFloat(confMatch[1]);

  // Extract individual scores from "scores": { "A": { ... }, "B": { ... } }
  for (const criterion of SCORE_CRITERIA) {
    // Try to find score for A
    const scoreAPattern = new RegExp(`"A"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
    const scoreAMatch = content.match(scoreAPattern);
    if (scoreAMatch) {
      result.scores.A[criterion.key] = parseInt(scoreAMatch[1]);
    }

    // Try to find score for B
    const scoreBPattern = new RegExp(`"B"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
    const scoreBMatch = content.match(scoreBPattern);
    if (scoreBMatch) {
      result.scores.B[criterion.key] = parseInt(scoreBMatch[1]);
    }
  }

  // Build criteria_scores from parsed scores
  if (Object.keys(result.scores.A).length > 0 || Object.keys(result.scores.B).length > 0) {
    result.criteria_scores = {};
    for (const criterion of SCORE_CRITERIA) {
      if (result.scores.A[criterion.key] !== undefined || result.scores.B[criterion.key] !== undefined) {
        result.criteria_scores[criterion.key] = {
          score_a: result.scores.A[criterion.key] || 0,
          score_b: result.scores.B[criterion.key] || 0
        };
      }
    }
  }

  // Extract final_justification
  const justMatch = content.match(/"final_justification"\s*:\s*"([^"]+)"/);
  if (justMatch) result.final_justification = justMatch[1];

  // Only return if we found something
  if (result.winner || result.confidence || Object.keys(result.scores.A).length > 0) {
    return result;
  }

  return null;
});

// Parse stream content for Chain of Thought steps incrementally
const parsedStreamSteps = computed(() => {
  if (!llmStreamContent.value) return [];

  const content = llmStreamContent.value;
  const steps = [];

  // Extract each step incrementally using regex
  for (const [stepKey, stepDef] of Object.entries(STEP_DEFINITIONS)) {
    // Pattern to match "step_X": "content..." (handles incomplete strings too)
    const stepPattern = new RegExp(`"${stepKey}"\\s*:\\s*"`, 'm');
    const stepMatch = content.match(stepPattern);

    if (stepMatch) {
      // Found the step, now extract its content
      const startIdx = content.indexOf(stepMatch[0]) + stepMatch[0].length;
      let endIdx = startIdx;
      let escaped = false;
      let stepContent = '';

      // Parse string content, handling escapes
      for (let i = startIdx; i < content.length; i++) {
        const char = content[i];
        if (escaped) {
          // Handle escape sequences
          if (char === 'n') stepContent += '\n';
          else if (char === '"') stepContent += '"';
          else if (char === '\\') stepContent += '\\';
          else stepContent += char;
          escaped = false;
        } else if (char === '\\') {
          escaped = true;
        } else if (char === '"') {
          // End of string
          endIdx = i;
          break;
        } else {
          stepContent += char;
        }
        endIdx = i;
      }

      // Check if this step is still being written (no closing quote found)
      const isStreaming = endIdx === content.length - 1 && content[endIdx] !== '"';

      steps.push({
        key: stepKey,
        title: stepDef.title,
        icon: stepDef.icon,
        content: stepContent,
        isStreaming: isStreaming
      });
    }
  }

  return steps;
});

// Combine current and pending items for queue display
const allQueueItems = computed(() => {
  const items = [];

  // Add current comparison first if running
  if (queue.value.current) {
    items.push({
      ...queue.value.current,
      status: 'running'
    });
  }

  // Add all pending items
  if (queue.value.pending) {
    items.push(...queue.value.pending);
  }

  return items.sort((a, b) => a.queue_position - b.queue_position);
});

// Load Session
const loadSession = async () => {
  loading.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}`
    );
    session.value = response.data;

    // Load current comparison - check both formats (id or object)
    if (session.value.current_comparison_id || session.value.current_comparison) {
      await loadCurrentComparison();
    }

    // Load completed comparisons and queue
    await loadCompletedComparisons();
    await loadQueue();
  } catch (error) {
    console.error('Error loading session:', error);
  } finally {
    loading.value = false;
  }
};

const loadCurrentComparison = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/current`
    );
    currentComparison.value = response.data;
  } catch (error) {
    console.error('Error loading current comparison:', error);
  }
};

const loadCompletedComparisons = async () => {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/comparisons`
    );
    completedComparisons.value = response.data;
  } catch (error) {
    console.error('Error loading comparisons:', error);
  }
};

const loadQueue = async () => {
  queueLoading.value = true;
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/queue`
    );
    queue.value = response.data;
  } catch (error) {
    console.error('Error loading queue:', error);
  } finally {
    queueLoading.value = false;
  }
};

// Session Control
const startSession = async () => {
  actionLoading.value = true;
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/start`
    );
    await loadSession();
    startPolling(); // Start polling when session starts
  } catch (error) {
    console.error('Error starting session:', error);
  } finally {
    actionLoading.value = false;
  }
};

const pauseSession = async () => {
  actionLoading.value = true;
  try {
    await axios.post(
      `${import.meta.env.VITE_API_BASE_URL}/api/judge/sessions/${sessionId}/pause`
    );
    stopPolling(); // Stop polling when paused
    await loadSession();
  } catch (error) {
    console.error('Error pausing session:', error);
  } finally {
    actionLoading.value = false;
  }
};

const navigateToResults = () => {
  router.push({ name: 'JudgeResults', params: { id: sessionId } });
};

const viewComparison = (comparison) => {
  currentComparison.value = comparison;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// Socket.IO for Live Updates (using centralized service with suspension handling)
const setupSocket = () => {
  socket.value = getSocket();

  // Remove existing listeners to prevent duplicates on reconnect
  socket.value.off('judge:joined');
  socket.value.off('judge:error');
  socket.value.off('judge:progress');
  socket.value.off('judge:comparison_start');
  socket.value.off('judge:llm_stream');
  socket.value.off('judge:comparison_complete');
  socket.value.off('judge:session_complete');

  // Re-join room when socket reconnects (handles browser suspension)
  socket.value.on('connect', () => {
    console.log('[Judge Socket] Connected/Reconnected');
    // Use correct event name with judge: prefix
    socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });
  });

  // Join immediately if already connected
  if (socket.value.connected) {
    socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });
  }

  // Handle join confirmation
  socket.value.on('judge:joined', (data) => {
    console.log('[Judge Socket] Joined session room:', data);
  });

  // Handle errors
  socket.value.on('judge:error', (data) => {
    console.error('[Judge Socket] Error:', data.message);
  });

  // Progress updates from worker
  socket.value.on('judge:progress', (data) => {
    console.log('[Judge Socket] Progress:', data);
    if (data.session_id == sessionId) {
      session.value = {
        ...session.value,
        status: data.status,
        completed_comparisons: data.completed,
        total_comparisons: data.total
      };
    }
  });

  // Comparison started
  socket.value.on('judge:comparison_start', (data) => {
    console.log('[Judge Socket] Comparison started:', data);
    // Check session_id if provided, otherwise accept all (room-based filtering)
    if (!data.session_id || data.session_id == sessionId) {
      // Reset stream content for new comparison - IMPORTANT for clean display
      llmStreamContent.value = '';
      console.log('[Judge Socket] Stream content cleared for new comparison');

      // Re-enable auto-scroll for new comparison
      autoScrollEnabled.value = true;

      // Update comparison status
      if (currentComparison.value) {
        currentComparison.value = {
          ...currentComparison.value,
          llm_status: 'running',
          winner: null,
          confidence_score: null
        };
      }

      // Expand the stream panel automatically
      expandedPanels.value = ['stream', 'prompt'];

      // Reload current comparison to get full data
      loadCurrentComparison();
    }
  });

  // LLM streaming tokens (show live generation)
  socket.value.on('judge:llm_stream', (data) => {
    if (data.session_id == sessionId) {
      // Append streamed content
      llmStreamContent.value += data.token || data.content || '';

      // Update llm_status to show evaluation in progress
      if (currentComparison.value) {
        currentComparison.value = {
          ...currentComparison.value,
          llm_status: 'running'
        };
      }

      // Auto-scroll to bottom (only if auto-scroll is enabled)
      if (autoScrollEnabled.value) {
        if (streamOutput.value) {
          streamOutput.value.scrollTop = streamOutput.value.scrollHeight;
        }
        if (fullscreenStreamOutput.value) {
          fullscreenStreamOutput.value.scrollTop = fullscreenStreamOutput.value.scrollHeight;
        }
      }
    }
  });

  // Comparison completed
  socket.value.on('judge:comparison_complete', async (data) => {
    console.log('[Judge Socket] Comparison complete:', data);
    if (data.session_id == sessionId) {
      // Update current comparison with result
      if (currentComparison.value) {
        currentComparison.value = {
          ...currentComparison.value,
          llm_status: 'completed',
          winner: data.winner,
          confidence_score: data.confidence
        };
      }
      // Reload completed comparisons list and queue
      await loadCompletedComparisons();
      await loadQueue();
    }
  });

  // Session completed
  socket.value.on('judge:session_complete', async (data) => {
    console.log('[Judge Socket] Session complete:', data);
    if (data.session_id == sessionId) {
      await loadSession();
    }
  });

  // Status response (from get_status request)
  socket.value.on('judge:status', (data) => {
    console.log('[Judge Socket] Status:', data);
    if (data.session_id == sessionId) {
      session.value = {
        ...session.value,
        status: data.status,
        completed_comparisons: data.completed,
        total_comparisons: data.total,
        current_comparison_id: data.current_comparison_id
      };
    }
  });
};

// Utility Functions
const getStatusColor = (status) => {
  const colors = {
    created: 'grey',
    queued: 'warning',
    running: 'info',
    paused: 'orange',
    completed: 'success',
    failed: 'error'
  };
  return colors[status] || 'grey';
};

const getStatusIcon = (status) => {
  const icons = {
    created: 'mdi-file-document',
    queued: 'mdi-clock-outline',
    running: 'mdi-play-circle',
    paused: 'mdi-pause-circle',
    completed: 'mdi-check-circle',
    failed: 'mdi-alert-circle'
  };
  return icons[status] || 'mdi-help-circle';
};

const getStatusText = (status) => {
  const texts = {
    created: 'Erstellt',
    queued: 'In Warteschlange',
    running: 'Läuft',
    paused: 'Pausiert',
    completed: 'Abgeschlossen',
    failed: 'Fehlgeschlagen'
  };
  return texts[status] || status;
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'info';
  if (confidence >= 0.4) return 'warning';
  return 'error';
};

// Queue status helpers
const getQueueStatusColor = (status) => {
  const colors = {
    'pending': 'grey',
    'running': 'warning',
    'completed': 'success',
    'failed': 'error',
    'PENDING': 'grey',
    'RUNNING': 'warning',
    'COMPLETED': 'success',
    'FAILED': 'error'
  };
  return colors[status] || 'grey';
};

const getQueueStatusIcon = (status) => {
  const icons = {
    'pending': 'mdi-clock-outline',
    'running': 'mdi-loading',
    'completed': 'mdi-check',
    'failed': 'mdi-alert',
    'PENDING': 'mdi-clock-outline',
    'RUNNING': 'mdi-loading',
    'COMPLETED': 'mdi-check',
    'FAILED': 'mdi-alert'
  };
  return icons[status] || 'mdi-help';
};

const getQueueStatusText = (status) => {
  const texts = {
    'pending': 'Ausstehend',
    'running': 'Läuft',
    'completed': 'Fertig',
    'failed': 'Fehler',
    'PENDING': 'Ausstehend',
    'RUNNING': 'Läuft',
    'COMPLETED': 'Fertig',
    'FAILED': 'Fehler'
  };
  return texts[status] || status;
};

const formatDate = (dateString) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// Get step by key from parsed steps
const getStepByKey = (stepKey) => {
  return parsedStreamSteps.value.find(s => s.key === stepKey) || null;
};

// Format criterion name for display (snake_case to readable)
const formatCriterionName = (criterion) => {
  const nameMap = {
    'counsellor_coherence': 'Berater-Kohärenz',
    'client_coherence': 'Klienten-Kohärenz',
    'quality': 'Qualität',
    'empathy': 'Empathie',
    'authenticity': 'Authentizität',
    'solution_orientation': 'Lösungsorientierung'
  };
  return nameMap[criterion] || criterion.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

// Get color based on score (1-5)
const getScoreColor = (score) => {
  if (score >= 4.5) return 'success';
  if (score >= 3.5) return 'info';
  if (score >= 2.5) return 'warning';
  return 'error';
};

// Copy stream content to clipboard
const copyStreamToClipboard = async () => {
  if (!llmStreamContent.value) return;

  try {
    await navigator.clipboard.writeText(llmStreamContent.value);
    // Could add a snackbar notification here
    console.log('Stream content copied to clipboard');
  } catch (err) {
    console.error('Failed to copy stream content:', err);
  }
};

// Open fullscreen mode
const openFullscreen = () => {
  fullscreenMode.value = true;
  autoScrollEnabled.value = true; // Reset auto-scroll when opening fullscreen
  // Auto-reconnect to stream when opening fullscreen
  if (session.value?.status === 'running' && !isStreaming.value) {
    reconnectToStream();
  }
};

// Close fullscreen mode
const closeFullscreen = () => {
  fullscreenMode.value = false;
};

// Handle user scroll - disable auto-scroll if user scrolls up
const handleStreamScroll = (event) => {
  const el = event.target;
  // Check if user is near the bottom (within 50px)
  const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;

  if (!isNearBottom && autoScrollEnabled.value) {
    // User scrolled up - disable auto-scroll
    autoScrollEnabled.value = false;
    console.log('[Stream] Auto-scroll disabled - user scrolled');
  }
};

// Re-enable auto-scroll and scroll to bottom
const enableAutoScroll = () => {
  autoScrollEnabled.value = true;
  // Immediately scroll to bottom
  if (fullscreenStreamOutput.value) {
    fullscreenStreamOutput.value.scrollTop = fullscreenStreamOutput.value.scrollHeight;
  }
  if (streamOutput.value) {
    streamOutput.value.scrollTop = streamOutput.value.scrollHeight;
  }
  console.log('[Stream] Auto-scroll re-enabled');
};

// Reconnect to live stream
const reconnectToStream = async () => {
  reconnecting.value = true;

  try {
    // Reset stream content
    llmStreamContent.value = '';

    // Get socket (will reconnect if needed via centralized service)
    socket.value = getSocket();

    // Re-join the session room
    socket.value.emit('judge:join_session', { session_id: parseInt(sessionId) });

    // Reload current comparison data
    await loadCurrentComparison();

    // Expand stream panel to show live output
    if (!expandedPanels.value.includes('stream')) {
      expandedPanels.value = ['stream', 'prompt'];
    }

    // Update comparison status to show we're listening
    if (currentComparison.value) {
      currentComparison.value = {
        ...currentComparison.value,
        llm_status: 'running'
      };
    }

    console.log('[Judge] Reconnected to live stream');
  } catch (err) {
    console.error('Failed to reconnect to stream:', err);
  } finally {
    reconnecting.value = false;
  }
};

// Polling interval for running sessions
let pollInterval = null;

const startPolling = () => {
  if (pollInterval) return;
  pollInterval = setInterval(async () => {
    if (session.value?.status === 'running') {
      await loadCurrentComparison();
      await loadQueue();
    } else {
      stopPolling();
    }
  }, 5000); // Poll every 5 seconds
};

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
};

// Lifecycle
onMounted(async () => {
  await loadSession();
  setupSocket();
  // Start polling if session is running
  if (session.value?.status === 'running') {
    startPolling();
  }
});

onUnmounted(() => {
  stopPolling();
  if (socket.value) {
    // Leave the session room (but don't disconnect - shared socket)
    socket.value.emit('judge:leave_session', { session_id: parseInt(sessionId) });
    // Remove our specific listeners
    socket.value.off('judge:joined');
    socket.value.off('judge:error');
    socket.value.off('judge:progress');
    socket.value.off('judge:comparison_start');
    socket.value.off('judge:llm_stream');
    socket.value.off('judge:comparison_complete');
    socket.value.off('judge:session_complete');
  }
});
</script>

<style scoped>
.judge-session {
  max-width: 1600px;
  margin: 0 auto;
}

.thread-container {
  height: 100%;
}

.thread-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.message-item {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.message-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.message-role {
  color: rgb(var(--v-theme-primary));
  text-transform: uppercase;
}

.message-content {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.evaluation-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
}

.winner-card {
  animation: winnerPulse 1s ease-in-out;
}

@keyframes winnerPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.cot-step {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface), 0.5);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 4px;
}

.json-preview {
  background-color: rgba(var(--v-theme-surface), 0.5);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.prompt-preview {
  background-color: rgba(var(--v-theme-info), 0.08);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.stream-output {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.stream-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.thread-card {
  max-height: 500px;
  overflow-y: auto;
}

.history-table :deep(tbody tr) {
  cursor: pointer;
}

.history-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

/* Stream panel content - limit height to prevent overflow */
.stream-panel-content :deep(.v-expansion-panel-text__wrapper) {
  max-height: 500px;
  overflow-y: auto;
}

/* Stream output styles */
.stream-output-container {
  margin-top: 16px;
  position: relative;
}

.stream-pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

/* Formatted JSON output */
.formatted-json-output {
  border: 1px solid rgba(var(--v-theme-success), 0.3);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--v-theme-success), 0.05) 0%, rgba(var(--v-theme-success), 0.02) 100%);
  max-height: 350px;
  overflow-y: auto;
}

.justification-text {
  background-color: rgba(var(--v-theme-surface), 0.8);
  padding: 12px;
  border-radius: 6px;
  font-style: italic;
  line-height: 1.6;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.criteria-scores :deep(.v-table) {
  background: transparent;
}

.criteria-scores :deep(th) {
  background-color: rgba(var(--v-theme-surface-variant), 0.5) !important;
  font-weight: bold;
}

.criteria-scores :deep(td),
.criteria-scores :deep(th) {
  padding: 8px 12px !important;
}

/* Pulsing live icon */
.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

/* Fullscreen styles */
.fullscreen-card {
  height: 100vh;
  overflow: hidden;
}

.fullscreen-content {
  overflow: hidden;
}

.fullscreen-content .h-100 {
  height: 100%;
}

.thread-scroll {
  max-height: calc(100vh - 250px);
}

.stream-scroll {
  max-height: calc(100vh - 400px);
}

.stream-pre-fullscreen {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
}

.criteria-table-fullscreen {
  background: transparent !important;
}

.criteria-table-fullscreen th {
  background-color: rgba(var(--v-theme-surface-variant), 0.3) !important;
}

.bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.08) !important;
}

/* Fullscreen dialog transitions */
.fullscreen-dialog .v-card {
  border-radius: 0 !important;
}

/* Result display header - always visible */
.result-display-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.8) 0%, rgba(var(--v-theme-surface-variant), 0.4) 100%);
  min-height: 120px;
}

.winner-card-fullscreen {
  transition: all 0.3s ease;
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

/* Follow button - fixed at bottom right of stream container */
.follow-btn {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: bounce-in 0.3s ease-out;
}

@keyframes bounce-in {
  0% {
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
  }
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

.position-relative {
  position: relative;
}

/* Formatted stream view styles */
.formatted-stream-view {
  padding: 8px;
}

.cot-steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cot-step-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.6) 0%, rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid rgb(var(--v-theme-primary));
  transition: all 0.3s ease;
}

.cot-step-card.current-step {
  border-left-color: rgb(var(--v-theme-warning));
  background: linear-gradient(135deg, rgba(var(--v-theme-warning), 0.15) 0%, rgba(var(--v-theme-warning), 0.05) 100%);
  box-shadow: 0 2px 8px rgba(var(--v-theme-warning), 0.2);
}

.cot-step-header {
  font-size: 14px;
  color: rgb(var(--v-theme-on-surface));
}

.cot-step-content {
  color: rgba(var(--v-theme-on-surface), 0.85);
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.scores-section {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  padding: 16px;
}

.justification-section {
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
  padding: 16px;
}

.raw-fallback {
  padding: 8px;
}

/* Display mode toggle button styles */
.v-btn-toggle .v-btn {
  text-transform: none;
}

/* ============================================
   LIKERT SCALE STYLES
   ============================================ */
.likert-scales-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
}

.likert-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.likert-label {
  width: 140px;
  flex-shrink: 0;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.likert-scale {
  display: flex;
  gap: 4px;
  align-items: center;
}

.likert-vs {
  width: 30px;
  text-align: center;
  flex-shrink: 0;
}

.likert-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border: 2px solid rgba(var(--v-theme-on-surface), 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.likert-dot.likert-pending {
  animation: likert-pulse 1.5s ease-in-out infinite;
}

.likert-dot.likert-active {
  transform: scale(1.1);
}

.likert-dot.likert-a-color {
  background: rgba(33, 150, 243, 0.8);
  border-color: rgb(33, 150, 243);
}

.likert-dot.likert-b-color {
  background: rgba(76, 175, 80, 0.8);
  border-color: rgb(76, 175, 80);
}

.likert-value {
  color: white;
  font-size: 10px;
  font-weight: bold;
}

@keyframes likert-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.05);
  }
}

/* Winner highlight animation */
.winner-highlight {
  animation: winner-glow 2s ease-in-out infinite;
}

@keyframes winner-glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(var(--v-theme-success), 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(var(--v-theme-success), 0.6);
  }
}

/* ============================================
   STRUCTURED STEPS STYLES
   ============================================ */
.structured-steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.structured-step {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  border-left: 4px solid rgba(var(--v-theme-on-surface), 0.2);
  overflow: hidden;
  transition: all 0.3s ease;
}

.structured-step.step-active {
  border-left-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}

.structured-step.step-streaming {
  border-left-color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.1);
  box-shadow: 0 2px 8px rgba(var(--v-theme-warning), 0.2);
}

.structured-step.step-pending {
  opacity: 0.6;
}

.step-header {
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
}

.step-content {
  padding: 0 16px 16px 16px;
}

.step-text {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.9);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.step-placeholder {
  padding: 8px 16px 12px 16px;
  min-height: 32px;
}
</style>
