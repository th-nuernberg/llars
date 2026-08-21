<template>
  <div
    class="comparison-interface"
    :class="{ 'communication-mode': isCommunicationMode, 'is-sending': isSending }"
    ref="containerRef"
  >
    <!-- Header with Info (hidden when embedded in EvaluationSession) -->
    <div v-if="!hideNavigation" class="comparison-header">
      <div class="header-info">
        <LIcon size="20" class="mr-2">mdi-compare-horizontal</LIcon>
        <h3>{{ $t('evaluation.comparison.title') }}</h3>
        <v-spacer />
        <!-- Gamification: motivation counter + history button. Only shown
             when the scenario has the reward system enabled. -->
        <span
          v-if="gamification.enabled && itemsUntilNextMilestone !== null"
          class="milestone-countdown"
          :class="{ 'milestone-countdown-imminent': itemsUntilNextMilestone <= 1 }"
          :title="$t('evaluation.comparison.gamification.countdownTooltip', { n: itemsUntilNextMilestone })"
        >
          <LIcon size="14" class="mr-1">mdi-trophy-outline</LIcon>
          <span>{{ $t('evaluation.comparison.gamification.countdown', { n: itemsUntilNextMilestone }) }}</span>
        </span>
        <LIconBtn
          v-if="gamification.enabled"
          icon="mdi-history"
          variant="text"
          size="small"
          :tooltip="$t('evaluation.comparison.gamification.viewHistory')"
          @click="historyOpen = true"
        />
        <LEvaluationStatus
          :status="currentItemStatus"
          :saving="saving"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loadingItem" class="loading-state">
      <v-progress-circular indeterminate color="primary" size="48" />
      <p>{{ $t('common.loading') }}</p>
    </div>

    <!-- Item loaded: comparison panels -->
    <template v-else-if="currentItem">

    <!-- NOTE: the task ("Aufgabe") is shown ONLY via the collapsible Aufgabe
         panel/pop-up in the EvaluationSession shell. We deliberately do NOT
         render any extra in-interface briefing banner here (removed on request:
         no green "Worum geht's?" box, no blue response-prompt box). -->

    <!-- Comparison Content -->
    <div
      ref="stackedContainerRef"
      class="comparison-content"
      :class="{
        'layout-stacked': effectiveLayout === 'stacked',
        'layout-side-by-side': effectiveLayout === 'side-by-side',
        'milestone-frame': isMilestoneCard,
        'panels-swapped': swapPanels && effectiveLayout === 'side-by-side'
      }"
    >
      <!-- Conversation Context (only when present) -->
      <div
        v-if="contextMessages?.length"
        class="context-panel"
        :style="effectiveLayout === 'side-by-side'
          ? (swapPanels ? rightPanelStyle() : leftPanelStyle())
          : topPanelStyle()"
      >
        <div class="context-header">
          <LIcon size="18" class="mr-2">mdi-message-text-outline</LIcon>
          <span class="context-title">{{ $t('evaluation.comparison.contextTitle', 'Verlauf bisher') }}</span>
          <v-spacer />
          <!-- Mobile: read the full conversation in the fullscreen overlay too
               (same affordance as the A/B options). Hidden on desktop. -->
          <LIconBtn
            v-if="isMobile"
            class="option-fullscreen-btn"
            icon="mdi-fullscreen"
            variant="text"
            size="x-small"
            :tooltip="$t('evaluation.comparison.readFullscreen', 'Vollbild lesen')"
            @click.stop="openFullscreen('context')"
          />
          <!-- Optional rater note — icon-only, next to the fullscreen button;
               opens the note pop-up. Coloured when a note exists. -->
          <LIconBtn
            v-if="raterNoteEnabled"
            class="notes-icon-btn"
            :class="{ 'has-note': !!notes }"
            :icon="notes ? 'mdi-note-edit' : 'mdi-note-plus-outline'"
            variant="text"
            size="x-small"
            :tooltip="$t('evaluation.comparison.notesLabel')"
            @click.stop="notesDialogOpen = true"
          />
          <!-- Layout toggle (always visible when context is present, even in embedded mode).
               Uses the shared mode-toggle-group pattern. -->
          <div class="mode-toggle-group">
            <button
              class="mode-btn"
              :class="{ active: layoutMode === 'stacked' }"
              :title="$t('evaluation.comparison.layoutStacked', 'Verlauf oben, Optionen unten')"
              @click="setLayout('stacked')"
            >
              <LIcon size="18">mdi-view-stream-outline</LIcon>
            </button>
            <button
              class="mode-btn"
              :class="{ active: layoutMode === 'side-by-side' }"
              :title="$t('evaluation.comparison.layoutSideBySide', 'Verlauf links, Optionen rechts')"
              @click="setLayout('side-by-side')"
            >
              <LIcon size="18">mdi-view-split-vertical</LIcon>
            </button>
            <!-- Swap button: only meaningful in side-by-side; flips context to the right.
                 Hidden on mobile (see <=600px media query) — there side-by-side
                 collapses to a vertical stack, so "swap left/right" is a no-op. -->
            <button
              v-if="layoutMode === 'side-by-side'"
              class="mode-btn mode-btn--swap"
              :class="{ active: swapPanels }"
              :title="swapPanels
                ? $t('evaluation.comparison.swapPanelsOn', 'Verlauf rechts (klicken zum Zurücksetzen)')
                : $t('evaluation.comparison.swapPanelsOff', 'Verlauf rechts anzeigen')"
              @click="swapPanels = !swapPanels"
            >
              <LIcon size="18">mdi-swap-horizontal</LIcon>
            </button>
          </div>
          <!-- First-session attention pill — points at the auto-advance
               switch right after the user lands on the page, then fades
               after ~10s. Suppressed forever via localStorage once seen
               OR once the user toggles autoAdvance. -->
          <span v-if="autoAdvanceHintVisible" class="hint-pill hint-pill--auto-advance">
            <LIcon size="14" class="hint-pill__arrow">mdi-arrow-right-bold</LIcon>
            {{ $t('evaluation.comparison.autoAdvanceHint') }}
          </span>
          <!-- Auto-advance switch: when on, picking A/B (or tie) jumps
               directly to the next item — no manual "Next" click needed.
               Persisted across sessions in localStorage; default OFF
               (v2 key bumped from the legacy default-ON behaviour).
               Skipped automatically on milestone items so the reward
               popup gets the user's attention before nav happens.
               Custom llars:auto-advance icon (tap → arrow → skip-bar). -->
          <LSwitch
            v-model="autoAdvance"
            class="auto-advance-switch"
            :title="autoAdvance
              ? $t('evaluation.comparison.autoAdvanceOn')
              : $t('evaluation.comparison.autoAdvanceOff')"
          >
            <LIcon size="16" class="auto-advance-icon">llars:auto-advance</LIcon>
            <span class="auto-advance-text">{{ $t('evaluation.comparison.autoAdvanceShort') }}</span>
          </LSwitch>
        </div>
        <!-- Per-item header: full Markdown rendering between the header bar
             and the conversation body. Uses resolvedItemHeader (variable-
             substituted template) via LMarkdownContent so bold, line-breaks
             and other formatting are preserved. Replaces the old truncated
             plain-text pill (.context-channel-tag) in the header. -->
        <div v-if="resolvedItemHeader" class="item-header-block">
          <LMarkdownContent :markdown="resolvedItemHeader" compact />
        </div>
        <div ref="contextBodyRef" class="context-body" :class="{ 'has-sent-ghost': !!sentMessage }">
          <LMessageList :messages="displayedMessages" />
        </div>
      </div>

      <!-- Resize Handle — horizontal in side-by-side, vertical in stacked.
           In both modes it sits between the conversation context (above /
           left) and the A/B options (below / right) so the rater can give
           more space to whichever side they need. -->
      <div
        v-if="contextMessages?.length"
        class="resize-handle"
        :class="{
          'resize-handle--horizontal': effectiveLayout === 'side-by-side',
          'resize-handle--vertical': effectiveLayout === 'stacked',
        }"
        @mousedown="effectiveLayout === 'side-by-side' ? startResize($event) : startStackedResize($event)"
      >
        <div class="handle-line" />
      </div>

      <!-- Options + Decision Section -->
      <div
        class="decision-panel"
        :style="contextMessages?.length
          ? (effectiveLayout === 'side-by-side'
              ? (swapPanels ? leftPanelStyle() : rightPanelStyle())
              : bottomPanelStyle())
          : null"
      >

        <!-- (Removed on request: no in-interface response-prompt banner; the
             task is shown only via the collapsible Aufgabe in the shell.) -->

        <!-- Two Options: row in stacked layout, column in side-by-side layout -->
        <div class="options-container">
          <!-- Comm-mode: paper-plane "send" overlay. Rendered as a sibling
               of the panels so it can fly across the container without
               being clipped by .option-panel's overflow. Anchored above
               the picked panel (A → left half / top half, B → right half
               / bottom half depending on layout). Pure visual — no
               interactivity, no a11y role. -->
          <div
            v-if="isSending"
            class="send-flying-icon"
            :class="{
              'send-flying-icon--a': isSending === 'A',
              'send-flying-icon--b': isSending === 'B',
              'send-flying-icon--stacked': effectiveLayout === 'stacked',
              'send-flying-icon--side': effectiveLayout === 'side-by-side',
            }"
            aria-hidden="true"
          >
            <LIcon size="56">mdi-send</LIcon>
          </div>

          <!-- Option A -->
          <div
            class="option-panel option-a"
            :class="{
              selected: selectedOption === 'A',
              'is-flying': isSending === 'A',
              'is-fading': isSending && isSending !== 'A',
            }"
            @click="selectOption('A')"
          >
            <div class="option-header">
              <span class="option-label option-label--a">Option A</span>
              <!-- Dev-only source reveal: shows which model_id / "human"
                   produced the option so devs can sanity-check pairings
                   during local development. Gated on Vite's DEV flag,
                   so production builds NEVER render this — assessors
                   stay blinded to the source as intended. -->
              <span v-if="isDevBuild && optionA?.model" class="dev-source-tag" :title="optionA.model">
                DEV · {{ optionA.model }}
              </span>
              <!-- Mobile-only fullscreen read button: opens this option's
                   full answer in a fullscreen overlay for comfortable reading
                   on a phone. Hidden on desktop (side-by-side panels are big
                   enough). @click.stop so tapping it doesn't also select A. -->
              <LIconBtn
                v-if="isMobile"
                class="option-fullscreen-btn"
                icon="mdi-fullscreen"
                variant="text"
                size="x-small"
                :tooltip="$t('evaluation.comparison.readFullscreen', 'Vollbild lesen')"
                @click.stop="openFullscreen('A')"
              />
            </div>
            <div class="option-content">
              <LMessageList v-if="optionA.messages?.length > 0" :messages="optionA.messages" />
              <div v-else-if="optionA.content" class="content-text">{{ optionA.content }}</div>
              <div v-else class="empty-content">{{ $t('evaluation.comparison.noContent') }}</div>
            </div>
            <div class="option-footer">
              <button
                class="select-btn"
                :class="{ selected: selectedOption === 'A' }"
                :disabled="saving"
                @click.stop="selectOption('A')"
              >
                <LIcon size="20">
                  {{ selectedOption === 'A' ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                </LIcon>
                <span>{{ $t('evaluation.comparison.selectA') }}</span>
              </button>
            </div>
          </div>

          <!-- VS Divider (visible only when options are next to each other) -->
          <div v-if="effectiveLayout === 'stacked'" class="vs-divider">
            <span class="vs-text">VS</span>
          </div>

          <!-- Option B -->
          <div
            class="option-panel option-b"
            :class="{
              selected: selectedOption === 'B',
              'is-flying': isSending === 'B',
              'is-fading': isSending && isSending !== 'B',
            }"
            @click="selectOption('B')"
          >
            <div class="option-header">
              <span class="option-label option-label--b">Option B</span>
              <!-- See Option A above — dev-only source reveal. -->
              <span v-if="isDevBuild && optionB?.model" class="dev-source-tag" :title="optionB.model">
                DEV · {{ optionB.model }}
              </span>
              <!-- Mobile-only fullscreen read button — see Option A. -->
              <LIconBtn
                v-if="isMobile"
                class="option-fullscreen-btn"
                icon="mdi-fullscreen"
                variant="text"
                size="x-small"
                :tooltip="$t('evaluation.comparison.readFullscreen', 'Vollbild lesen')"
                @click.stop="openFullscreen('B')"
              />
            </div>
            <div class="option-content">
              <LMessageList v-if="optionB.messages?.length > 0" :messages="optionB.messages" />
              <div v-else-if="optionB.content" class="content-text">{{ optionB.content }}</div>
              <div v-else class="empty-content">{{ $t('evaluation.comparison.noContent') }}</div>
            </div>
            <div class="option-footer">
              <button
                class="select-btn"
                :class="{ selected: selectedOption === 'B' }"
                :disabled="saving"
                @click.stop="selectOption('B')"
              >
                <LIcon size="20">
                  {{ selectedOption === 'B' ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                </LIcon>
                <span>{{ $t('evaluation.comparison.selectB') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Tie Option (off by default; only shown when scenario config explicitly allows it) -->
        <div v-if="tieAllowed" class="tie-section">
          <button
            class="tie-btn"
            :class="{ selected: selectedOption === 'tie' }"
            :disabled="saving"
            @click="selectOption('tie')"
          >
            <LIcon size="20">mdi-equal</LIcon>
            <span>{{ $t('evaluation.comparison.tie') }}</span>
          </button>
        </div>

        <!-- (Rater note moved to an icon button in the "Verlauf bisher" header,
             next to the fullscreen button — opens the note pop-up.) -->
      </div>
    </div>

    </template><!-- /v-else-if="currentItem" -->

    <!-- Empty State -->
    <div v-else class="empty-state">
      <LIcon size="64" color="grey-lighten-1">mdi-compare-horizontal-off</LIcon>
      <h3>{{ $t('evaluation.comparison.emptyTitle') }}</h3>
    </div>

    <!-- Navigation Footer (only shown if hideNavigation is false) -->
    <div class="nav-footer" v-if="items.length > 0 && !hideNavigation">
      <LBtn
        variant="tonal"
        size="small"
        :disabled="!hasPrev"
        @click="goPrev"
      >
        <LIcon start>mdi-chevron-left</LIcon>
        {{ $t('common.previous') }}
      </LBtn>
      <span class="nav-position">
        {{ currentItemIndex + 1 }} / {{ items.length }}
      </span>
      <LBtn
        variant="primary"
        size="small"
        :disabled="!hasNext"
        @click="goNext"
      >
        {{ $t('common.next') }}
        <LIcon end>mdi-chevron-right</LIcon>
      </LBtn>
    </div>

    <!-- Gamification: reward popup + history drawer. Both lazy-load their
         data on open and re-fetch each time so the count is fresh. -->
    <ComparisonRewardDialog
      v-if="gamification.enabled"
      v-model="rewardOpen"
      :scenario-id="scenarioId"
      :milestone-count="milestoneEvent?.count || 0"
      :is-first="!!milestoneEvent?.isFirst"
      @view-history="onViewHistoryFromReward"
    />
    <ComparisonHistoryDrawer
      v-if="gamification.enabled"
      v-model="historyOpen"
      :scenario-id="scenarioId"
    />

    <!-- (The one-time "thank you" confirmation previously rendered here was
         moved to EvaluationSession.vue, which now owns a universal
         first-evaluation notice for ALL scenario types — see that file's
         maybeShowFirstEvaluationNotice. Removed here to avoid double-firing.) -->

    <!-- Mobile-only fullscreen read overlay for a single option (A or B).
         Mirrors the AdminMailCenterSection fullscreen pattern (v-dialog
         fullscreen + top bar + close button) but renders the option's
         CONTENT directly instead of an iframe. The picked option is still
         reachable from inside the overlay via the footer select button, so
         the rater can read the long answer fullscreen and decide without
         closing first. Selecting auto-closes the overlay. -->
    <v-dialog
      v-model="fullscreenOpen"
      fullscreen
      :scrim="false"
      transition="dialog-bottom-transition"
    >
      <div class="option-fullscreen" :class="{ 'communication-mode': isCommunicationMode }">
        <div class="option-fullscreen-bar">
          <span
            class="option-label"
            :class="fullscreenOption === 'A' ? 'option-label--a' : fullscreenOption === 'B' ? 'option-label--b' : ''"
          >
            {{ fullscreenOption === 'context'
              ? $t('evaluation.comparison.contextTitle', 'Verlauf bisher')
              : fullscreenOption === 'A' ? 'Option A' : 'Option B' }}
          </span>
          <v-spacer />
          <LBtn variant="text" size="small" prepend-icon="mdi-close" @click="fullscreenOpen = false">
            {{ $t('common.close') }}
          </LBtn>
        </div>
        <div class="option-fullscreen-content">
          <template v-if="fullscreenData">
            <LMessageList v-if="fullscreenData.messages?.length > 0" :messages="fullscreenData.messages" />
            <div v-else-if="fullscreenData.content" class="content-text">{{ fullscreenData.content }}</div>
            <div v-else class="empty-content">{{ $t('evaluation.comparison.noContent') }}</div>
          </template>
        </div>
        <!-- Wrapper carries .option-a / .option-b so the existing
             `.option-a .select-btn.selected` (and comm-mode) descendant
             selectors style the fullscreen button identically to the panel
             footer button. -->
        <div
          v-if="fullscreenOption !== 'context'"
          class="option-fullscreen-footer"
          :class="fullscreenOption === 'A' ? 'option-a' : 'option-b'"
        >
          <button
            class="select-btn"
            :class="{ selected: selectedOption === fullscreenOption }"
            :disabled="saving"
            @click="selectFromFullscreen"
          >
            <LIcon size="20">
              {{ selectedOption === fullscreenOption ? 'mdi-check-circle' : 'mdi-circle-outline' }}
            </LIcon>
            <span>{{ fullscreenOption === 'A' ? $t('evaluation.comparison.selectA') : $t('evaluation.comparison.selectB') }}</span>
          </button>
        </div>
      </div>
    </v-dialog>

    <!-- Optional rater-note pop-up (opened by the small "Notiz" button). -->
    <v-dialog v-model="notesDialogOpen" max-width="480">
      <div class="notes-dialog-card">
        <div class="notes-dialog-header">
          <LIcon size="18" class="mr-2">mdi-note-edit-outline</LIcon>
          <span>{{ $t('evaluation.comparison.notesLabel') }}</span>
        </div>
        <v-textarea
          v-model="notes"
          variant="outlined"
          auto-grow
          rows="4"
          hide-details
          autofocus
          :placeholder="$t('evaluation.comparison.notesPlaceholder')"
        />
        <div class="notes-dialog-actions">
          <LBtn variant="primary" size="small" @click="closeNotesDialog">
            {{ $t('common.done') }}
          </LBtn>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
/**
 * ComparisonInterface.vue - A/B Comparison Interface
 *
 * Provides the UI for comparison evaluation where users choose
 * between two options (A vs B) or declare a tie.
 *
 * Two layouts (toggleable via header buttons, persisted in localStorage):
 *  - "stacked"      → Verlauf (conversation context) above the A/B options.
 *  - "side-by-side" → Verlauf left, A/B options + decision controls right
 *                     (mirrors mail-rating / authenticity layout pattern).
 *
 * Side-by-side is only meaningful when there is a conversation context to
 * place next to the candidates; otherwise the toggle is hidden and the
 * stacked layout is used implicitly.
 */
import { ref, computed, watch, onMounted, nextTick, toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { usePanelResize } from '@/composables/usePanelResize'
import { useComparisonEvaluation } from '@/composables/useComparisonEvaluation'
import { useMobile } from '@/composables/useMobile'
import ComparisonRewardDialog from '@/views/Evaluation/interfaces/ComparisonRewardDialog.vue'
import ComparisonHistoryDrawer from '@/views/Evaluation/interfaces/ComparisonHistoryDrawer.vue'
import LMarkdownContent from '@/components/common/LMarkdownContent.vue'

// Vite injects DEV=true only on `vite dev`; production bundles emit
// DEV=false and dead-code-eliminate the v-if branch entirely. That's
// the contract: source reveal is a local-dev convenience, never
// shipped to assessors — see the comment above the .dev-source-tag
// span in the template.
const isDevBuild = import.meta.env.DEV

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  },
  scenario: {
    type: Object,
    default: null
  },
  config: {
    type: Object,
    default: () => ({})
  },
  initialItemId: {
    type: [Number, String],
    default: null
  },
  hideNavigation: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['item-completed', 'all-completed', 'status-change', 'saving-change'])

// Computed prop for hideNavigation to use in template
const hideNavigation = computed(() => props.hideNavigation)
const canEvaluate = computed(() => props.scenario?.can_evaluate !== false)

// Tracks which option is currently mid-send-animation ('A' | 'B' | null).
// Drives the .is-sending modifier on the root + the per-option
// `.option-panel.is-flying` class. Communication-mode only — see
// resolvedCommunication* + isCommunicationMode further below for the
// per-template lookups that depend on the composable + i18n bindings.
const isSending = ref(null)

// Tie option is OFF by default — only enabled when the scenario config
// explicitly enables it.
//
// The flag arrives under BOTH spellings depending on who wrote the scenario:
//   - Scenario Wizard  -> `allowTie`  (camelCase, frontend-authored config)
//   - v1 REST API      -> `allow_tie` (snake_case, Pydantic ComparisonConfig)
// Reading only camelCase silently dropped the tie button for every
// API-created scenario even though `allow_tie: true` is the schema DEFAULT —
// the KIESA Sprachvereinfachung studies collected 359 A/B votes with no tie
// option available. Same dual-key strategy as useComparisonEvaluation's
// readCfgField() for the gamification flags.
//
// Nesting is also ambiguous: the wizard stores it under
// `config_json.eval_config.config.*`, older paths at the top level.
const tieAllowed = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const ec = cfg?.eval_config?.config || {}
  for (const key of ['allowTie', 'allow_tie']) {
    if (ec[key] !== undefined) return ec[key] === true
    if (cfg[key] !== undefined) return cfg[key] === true
  }
  return false
})

// Resolved task question: reads the configurable `question` field from the scenario
// config and substitutes {{variable}} placeholders with per-item metadata_json values.
// Falls back to the i18n default when no custom question is configured.
function _resolveVariables(template, meta) {
  if (!template || !meta) return template
  return String(template).replace(/\{\{(\w+)\}\}/g, (_, key) => {
    const v = meta[key]
    if (v === undefined || v === null) return `{{${key}}}`
    // LocalizedString shape: prefer current locale, fall back to DE
    // (LLARS default), then EN. Without this, items whose metadata
    // includes a {de, en} dict (e.g. channel_label) would render as
    // "[object Object]".
    if (typeof v === 'object' && !Array.isArray(v)) {
      const lang = (locale?.value || 'de')
      return String(v[lang] ?? v.de ?? v.en ?? JSON.stringify(v))
    }
    return String(v)
  })
}

// Pick the current-locale string from a LocalizedString ({de, en}) with a
// stable fallback chain (current locale → DE (LLARS default) → EN). Returns
// '' for an empty/missing value so callers can treat it as falsy. `locale`
// is bound via useI18n below; these readers are only invoked from computeds
// at render time, by which point it is resolved.
function _pickLocalized(v) {
  if (v == null) return ''
  if (typeof v !== 'object') return String(v)
  const lang = locale.value || 'de'
  return v?.[lang] ?? v?.de ?? v?.en ?? ''
}

function _readQuestion(cfg) {
  // Check wizard path (eval_config.config.question) and legacy top-level
  const ec = cfg?.eval_config?.config || {}
  const q = ec.question ?? cfg?.question
  if (!q) return null
  return _pickLocalized(q) || null
}

// Read itemHeaderTemplate from config — same multi-location lookup as _readQuestion.
function _readItemHeaderTemplate(cfg) {
  const ec = cfg?.eval_config?.config || {}
  const t = ec.itemHeaderTemplate ?? ec.item_header_template ?? cfg?.itemHeaderTemplate ?? cfg?.item_header_template
  if (!t) return null
  return _pickLocalized(t) || null
}

// Read the long-form task-briefing markdown from config. Same
// multi-location / multi-key lookup as the other readers. Falls
// back to the short i18n string so a scenario without a configured
// briefing still surfaces a clear prompt to the rater.
function _readTaskDescriptionMarkdown(cfg) {
  const ec = cfg?.eval_config?.config || {}
  const t = ec.taskDescriptionMarkdown
    ?? ec.task_description_markdown
    ?? cfg?.taskDescriptionMarkdown
    ?? cfg?.task_description_markdown
  if (!t) return null
  return _pickLocalized(t) || null
}

// Read the response prompt (communication_comparison only) — the question
// posed to the rater above the A/B options, e.g. "Wie würdest *du* hier
// antworten?". Same multi-location / multi-key lookup as the other readers.
function _readResponsePrompt(cfg) {
  const ec = cfg?.eval_config?.config || {}
  const p = ec.responsePrompt
    ?? ec.response_prompt
    ?? cfg?.responsePrompt
    ?? cfg?.response_prompt
  if (!p) return null
  return _pickLocalized(p) || null
}

// Comparison evaluation composable
const scenarioIdRef = toRef(props, 'scenarioId')
const {
  items,
  currentItem,
  currentItemIndex,
  optionA,
  optionB,
  contextMessages,
  contextSubject,
  currentItemMeta,
  selectedOption,
  notes,
  loading,
  loadingItem,
  saving,
  error,
  progress,
  hasNext,
  hasPrev,
  currentItemStatus,
  gamification,
  isMilestoneCard,
  itemsUntilNextMilestone,
  milestoneEvent,
  clearMilestone,
  loadItems,
  loadItem,
  selectOption: doSelectOption,
  saveMetadata: doSaveMetadata,
  goNext,
  goPrev
} = useComparisonEvaluation(scenarioIdRef)

// NOTE: the one-time "thank you" notice that used to live here (via
// useFirstComparisonNotice) was moved to EvaluationSession.vue, which now fires
// a universal first-evaluation thank-you for ALL scenario types on the
// completed-count 0 → ≥1 transition. Keeping it here too would double-fire.

// Reactive task question with per-item {{variable}} substitution.
// Template is read from scenario config (LocalizedString or plain string),
// variables are replaced from EvaluationItem.metadata_json.
const { t, locale } = useI18n()

// Auto-advance is a desktop-only convenience. On phones the switch is
// hidden (see <=600px media query) AND the behaviour is forced off so a
// rater who enabled it on desktop isn't stuck silently auto-advancing on
// mobile with no visible toggle to turn it back off.
const { isMobile } = useMobile()

const resolvedQuestion = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const template = _readQuestion(cfg)
  if (template) return _resolveVariables(template, currentItemMeta.value)
  return t('evaluation.comparison.contextPrompt', 'Welche der beiden möglichen nächsten Beraterantworten ist passender?')
})

// Reactive task briefing — prefers the long-form
// task_description_markdown from the scenario config (set via the
// wizard / API) and falls back to the short ``question`` so the
// rater always sees the prompt. Per-item ``{{variable}}``
// substitution from EvaluationItem.metadata_json works in both.
const resolvedTaskBriefing = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const tmpl = _readTaskDescriptionMarkdown(cfg) || _readQuestion(cfg)
  if (!tmpl) {
    return t(
      'evaluation.comparison.contextPrompt',
      'Welche der beiden möglichen nächsten Beraterantworten ist passender?',
    )
  }
  return _resolveVariables(tmpl, currentItemMeta.value)
})

// Per-item header: markdown template from config with {{variable}} substitution.
// Shown above the conversation context (or above the options if no context).
const resolvedItemHeader = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const template = _readItemHeaderTemplate(cfg)
  if (!template) return null
  return _resolveVariables(template, currentItemMeta.value)
})

// Response prompt (communication_comparison only): the localized question
// shown above the A/B options, e.g. "Wie würdest *du* hier antworten?".
// Rendered as markdown so the *emphasis* shows. Per-item {{variable}}
// substitution works like the other readers. Returns null when not configured
// so the template can hide the block entirely.
const resolvedResponsePrompt = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const template = _readResponsePrompt(cfg)
  if (!template) return null
  return _resolveVariables(template, currentItemMeta.value)
})

// Whether the per-comparison rater note textarea is shown. Reads
// eval_config.config.rater_note_enabled; default TRUE so existing scenarios
// (which never set the flag) keep the notes field they had before.
const raterNoteEnabled = computed(() => {
  const cfg = props.config || props.scenario?.config_json || {}
  const ec = cfg?.eval_config?.config || {}
  const v = ec.rater_note_enabled ?? ec.raterNoteEnabled
  if (v === undefined || v === null) return true
  return v === true
})

// -----------------------------------------------------------------------------
// Communication-Comparison mode (function_type_id=8)
// -----------------------------------------------------------------------------
// Thin specialisation of comparison(4). Same composable, persistence,
// gamification — only the UI shell differs: distinct A/B colours that
// don't collide with the counsellor/client message bubbles, a "send"-
// flavoured CTA + fly-out animation, a response-prompt + rater-note
// block under the conversation. Gated on this single computed so the
// classic comparison flow stays untouched.
const isCommunicationMode = computed(() => {
  const fnId = props.scenario?.function_type_id
  if (fnId === 8) return true
  const cfg = props.config || props.scenario?.config_json || {}
  const tType = cfg?.eval_config?.type || cfg?.type
  return tType === 'communication_comparison'
})

// Reset the send-animation state when the next item slides in.
watch(currentItem, () => {
  isSending.value = null
  sentMessage.value = null
})

// Ghost-Berater turn appended to the conversation context after a
// successful send (Sozialwissenschaften 2026-05-18). Local-only — never persisted;
// purely visual so the rater sees "their" message land in the chat
// before navigating to the next case. Cleared by the currentItem
// watcher above.
const sentMessage = ref(null)

// Conversation context augmented with the just-sent ghost message
// (if any). LMessageList consumes this combined list so the new turn
// slides in below the existing dialogue.
const displayedMessages = computed(() => {
  const base = Array.isArray(contextMessages.value) ? contextMessages.value : []
  if (!sentMessage.value) return base
  return [...base, sentMessage.value]
})

// Auto-scroll the conversation panel to the bottom when the ghost
// message lands, so the rater sees "their" turn slide into view
// instead of having to scroll manually. Tolerates the ref being null
// during initial render.
const contextBodyRef = ref(null)
watch(sentMessage, (value) => {
  if (!value) return
  nextTick(() => {
    const el = contextBodyRef.value
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  })
})


// Gamification dialog/drawer state. The reward dialog opens automatically
// when the composable fires a milestone event; the history drawer is
// user-triggered via the header button (or the dialog's "View history" CTA).
const rewardOpen = ref(false)
const historyOpen = ref(false)

watch(milestoneEvent, (val) => {
  if (val) rewardOpen.value = true
})

// Clear the milestone event once the user dismisses the popup so closing
// the dialog doesn't immediately re-open it on the next reactivity tick.
watch(rewardOpen, (open) => {
  if (!open) clearMilestone()
})

function onViewHistoryFromReward() {
  rewardOpen.value = false
  historyOpen.value = true
}

// Layout mode: 'stacked' (Verlauf above options) or 'side-by-side' (Verlauf left, options right).
// The INITIAL view is ALWAYS 'stacked' — the study wants a consistent first
// impression for every rater, so we intentionally do NOT restore a previously
// persisted 'side-by-side' choice on load. The rater can still switch to
// side-by-side per session via the header toggle (setLayout still records the
// choice for the rest of that session; it just isn't reapplied on reload).
const LAYOUT_STORAGE_KEY = 'llars-comparison-layout'
const layoutMode = ref('stacked')

// Panel swap: when true in side-by-side mode the conversation (Verlauf) appears
// on the RIGHT and the A/B options appear on the LEFT. Lets users who prefer
// reading context last keep it out of the way without losing access to it.
const SWAP_PANELS_STORAGE_KEY = 'llars-comparison-swap-panels'
const swapPanels = ref(
  typeof localStorage !== 'undefined' && localStorage.getItem(SWAP_PANELS_STORAGE_KEY) === 'true'
)
watch(swapPanels, (val) => {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(SWAP_PANELS_STORAGE_KEY, String(val))
  }
})

// Auto-advance: when ON, picking A/B/tie navigates straight to the next
// item — no manual "Next" click required. Default ON to match the
// "vote and move on" flow most assessors prefer; persisted in
// localStorage so it survives reload. Skipped on milestone items so the
// reward popup gets focus instead of being whisked away by navigation.
// v2 key — the previous key persisted user choices forever; we bumped
// the version to force everyone back to the new default-OFF behaviour
// once. New choices are remembered as usual under the v2 key.
const AUTO_ADVANCE_STORAGE_KEY = 'llars-comparison-auto-advance:v2'
// Default OFF — the rater stays on the current item after submitting
// and decides themselves when to move to the next one. Less disorienting
// for new raters and protects against accidental clicks. Toggle is
// still remembered per-user via localStorage.
const autoAdvance = ref(
  typeof localStorage !== 'undefined'
  && localStorage.getItem(AUTO_ADVANCE_STORAGE_KEY) !== null
    ? localStorage.getItem(AUTO_ADVANCE_STORAGE_KEY) === 'true'
    : false
)
watch(autoAdvance, (val) => {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(AUTO_ADVANCE_STORAGE_KEY, String(val))
  }
  // First toggle implicitly dismisses the discoverability hint.
  dismissAutoAdvanceHint()
})

// One-time attention pill that points at the auto-advance switch.
// Suppressed forever once the user has either seen the timer expire
// or toggled the switch.
const AUTO_ADVANCE_HINT_KEY = 'llars:autoAdvanceHintSeen:v2'
const autoAdvanceHintVisible = ref(
  typeof localStorage !== 'undefined'
    ? localStorage.getItem(AUTO_ADVANCE_HINT_KEY) !== '1'
    : true
)

function dismissAutoAdvanceHint() {
  if (!autoAdvanceHintVisible.value) return
  autoAdvanceHintVisible.value = false
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(AUTO_ADVANCE_HINT_KEY, '1')
  }
}

if (autoAdvanceHintVisible.value) {
  setTimeout(dismissAutoAdvanceHint, 10000)
}

// Optional rater note lives in a pop-up (opened by the small "Notiz" button)
// instead of an inline textarea. Closing the dialog persists the note.
const notesDialogOpen = ref(false)
function closeNotesDialog() {
  notesDialogOpen.value = false
  saveMetadata()
}

// If there is no conversation context, "side-by-side" doesn't make sense — fall back to stacked.
const effectiveLayout = computed(() =>
  contextMessages.value?.length ? layoutMode.value : 'stacked'
)

function setLayout(mode) {
  layoutMode.value = mode
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(LAYOUT_STORAGE_KEY, mode)
  }
}

// Side-by-side resize handle (horizontal drag) — context|options panel
// widths. Active only when both contextMessages exist and the user has
// the side-by-side layout enabled.
const { containerRef, leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 25,
  maxLeftPercent: 75,
  storageKey: 'llars-comparison-panel-width'
})

// Stacked-layout resize handle (vertical drag) — context above /
// options below. Lets the rater grow the conversation panel when the
// dialogue is long, or shrink it when they want to see both candidate
// answers without scrolling. Backed by its own storage key so the
// horizontal and vertical preferences don't overwrite each other.
const {
  containerRef: stackedContainerRef,
  leftPanelStyle: topPanelStyle,
  rightPanelStyle: bottomPanelStyle,
  startResize: startStackedResize,
} = usePanelResize({
  initialLeftPercent: 45,
  minLeftPercent: 20,
  maxLeftPercent: 75,
  storageKey: 'llars-comparison-stacked-height',
  axis: 'vertical',
})

// Emit status changes to parent
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving changes to parent
watch(saving, (isSaving) => {
  emit('saving-change', isSaving)
})

// Select option (auto-saves and optionally advances to the next item).
async function selectOption(option) {
  if (!canEvaluate.value) return
  // Communication-Comparison: play the "send" animation BEFORE the
  // composable POSTs. Paper-plane overlay (1.2 s total) + card pop +
  // fade. We wait ~900 ms here so the icon has nearly reached the
  // edge of the container before we hit the network. isSending stays
  // set until the user clicks "Weiter" (currentItem-watcher clears
  // it then), so the picked card stays faded-out instead of
  // re-rendering as selected — keeps the visual story consistent.
  if (isCommunicationMode.value && (option === 'A' || option === 'B')) {
    // Re-selection: clear any previous ghost so the conversation panel
    // shows only the new pick. The keyframe animations reset cleanly
    // because Vue toggles the .is-flying / .is-fading classes when
    // isSending changes value.
    sentMessage.value = null
    isSending.value = option
    // Schedule the ghost-Berater turn to land in the conversation just
    // before the paper-plane finishes its arc — looks like the message
    // "arrived" once the plane reaches its destination. Independent of
    // the POST: the actual evaluation payload is unchanged, the ghost
    // is purely visual and gets cleared when the next item loads.
    setTimeout(() => {
      const picked = option === 'A' ? optionA.value : optionB.value
      const content = (picked?.content
        || picked?.messages?.map(m => m?.content).filter(Boolean).join('\n\n')
        || '').trim()
      if (content) {
        // Shape must match LMessageList's expected schema (sender +
        // content + timestamp + message_id). The sender string mirrors
        // the canonical `Berater\*in` value the backend emits — with
        // the literal backslash — so the existing role-to-style mapping
        // in LMessageList picks the counsellor styling automatically.
        sentMessage.value = {
          message_id: `ghost-${option}-${Date.now()}`,
          sender: 'Berater\\*in',
          content,
          timestamp: new Date().toISOString(),
          is_sent_ghost: true,
        }
      }
    }, 700)
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  const result = await doSelectOption(option)
  if (!result.success) {
    isSending.value = null
    return
  }

  // The one-time "thank you for your first evaluation" pop-up is no longer
  // fired here. It is now owned by EvaluationSession.vue, which watches the
  // scenario's completed-count 0 → ≥1 transition and shows the notice once per
  // scenario for ALL evaluation types. Firing it here too would double-fire.
  emit('item-completed', currentItem.value?.item_id)
  if (progress.value.completed === progress.value.total) {
    emit('all-completed')
  }

  // Auto-advance only when:
  //   - the user opted in (toggle ON)
  //   - there's actually a next item to go to
  //   - this submit didn't trigger a milestone (popup needs focus first;
  //     the assessor can navigate manually after dismissing it)
  if (autoAdvance.value && !isMobile.value && hasNext.value && !milestoneEvent.value) {
    // Tiny delay so the chosen-button "selected" state flashes for a
    // moment before the next item replaces it — gives the user a
    // visual confirmation that their click registered.
    setTimeout(() => {
      goNext()
    }, 220)
  }
}

// Save metadata on blur
function saveMetadata() {
  doSaveMetadata()
}

// -----------------------------------------------------------------------------
// Mobile fullscreen read mode (Option A / B)
// -----------------------------------------------------------------------------
// On phones a long answer is hard to read inside the cramped stacked panels,
// so each option gets a fullscreen overlay (mdi-fullscreen button → v-dialog
// fullscreen). The overlay renders the option's CONTENT (not an iframe) plus
// a footer select button so the rater can pick that option without closing
// first. Desktop never shows the trigger button (v-if="isMobile").
const fullscreenOpen = ref(false)
const fullscreenOption = ref(null) // 'A' | 'B' | 'context' | null

// The content shown fullscreen — reactive so the overlay updates if the
// underlying item reloads while open. 'context' shows the conversation
// (Verlauf) as a read-only message list (no select button).
const fullscreenData = computed(() =>
  fullscreenOption.value === 'A' ? optionA.value
    : fullscreenOption.value === 'B' ? optionB.value
      : fullscreenOption.value === 'context' ? { messages: contextMessages.value }
        : null
)

function openFullscreen(option) {
  fullscreenOption.value = option
  fullscreenOpen.value = true
}

// Pick the currently-shown option from inside the overlay, then close it so
// the rater lands back on the (possibly auto-advancing) comparison view.
async function selectFromFullscreen() {
  const option = fullscreenOption.value
  if (!option) return
  fullscreenOpen.value = false
  await selectOption(option)
}

// Close the fullscreen overlay automatically when the item changes so a
// stale option isn't shown after navigating to the next case.
watch(currentItem, () => {
  fullscreenOpen.value = false
})

// Initialize on mount
onMounted(async () => {
  await loadItems()
  // Navigate to initial item if specified
  if (props.initialItemId && items.value.length > 0) {
    const targetItemId = Number(props.initialItemId)
    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
    }
  }
})

// Watch for scenario changes
watch(() => props.scenarioId, (newId) => {
  if (newId) {
    loadItems()
  }
})

// Watch for initialItemId changes (e.g., when navigating between items via URL)
watch(() => props.initialItemId, async (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetItemId = Number(newItemId)
    // Check if this item is already the current item
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetItemId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
    }
  }
})
</script>

<style scoped>
.comparison-interface {
  /* Viewport-fit (Sozialwissenschaften 2026-05-18): fill the parent shell, clip
     overflow, let the child .comparison-content stretch and the leaf
     content panels (.context-body, .option-content) handle their own
     scroll. `min-height: 0` is required so the flex child can actually
     shrink — without it, an oversized inner panel would push the
     whole interface taller than the viewport. */
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

/* Header */
.comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 8px;
}

.header-info h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

/* Layout toggle — shared mode-toggle-group look */
.mode-toggle-group {
  display: flex;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 8px;
  padding: 2px;
  margin-left: 8px;
}

.mode-btn {
  width: 30px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.15s ease;
}

.mode-btn:hover {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.mode-btn.active {
  background: rgb(var(--v-theme-surface));
  color: rgb(var(--v-theme-primary));
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Auto-advance switch: sits next to the layout segmented control,
   compact, with the custom llars:auto-advance icon + short label. The
   LSwitch keeps its signature LLARS asymmetric thumb; we only restyle
   the wrapper + label for alignment. */
.auto-advance-switch {
  margin-left: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.75);
  cursor: pointer;
  user-select: none;
}

.auto-advance-icon {
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: color 0.15s ease;
}

/* When the switch is on, tint the icon + label primary so the active
   state is visible at a glance. */
.auto-advance-switch :deep(.l-switch--checked) ~ .auto-advance-icon,
.auto-advance-switch:has(.l-switch--checked) .auto-advance-icon,
.auto-advance-switch:has(input:checked) .auto-advance-icon {
  color: rgb(var(--v-theme-primary));
}

.auto-advance-switch:has(input:checked) .auto-advance-text {
  color: rgb(var(--v-theme-primary));
}

.auto-advance-text {
  white-space: nowrap;
  letter-spacing: 0.01em;
}

/* Hide the inline label on narrow viewports so the switch + icon stay
   in one row with the layout toggle. */
@media (max-width: 720px) {
  .auto-advance-text {
    display: none;
  }
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Content container — natural height; the page itself scrolls. */
.comparison-content {
  /* Viewport-fit: grow into the remaining space below the (optional)
     task-briefing-banner, clip overflow, propagate the flex shrink
     down to the panels. */
  flex: 1 1 auto;
  min-height: 0;
  /* Extra bottom padding so the "Choose Option A/B" buttons keep a clear
     gap from the fixed Previous/Next session-footer instead of sitting
     flush against it. (Phones get a tighter value further below — there
     the thin footer + small viewport make this much look like wasted space.) */
  padding: 12px 12px 28px;
  display: flex;
  gap: 12px;
  overflow: hidden;
}

/* Gamification milestone-card highlight. Applied to the comparison-content
   wrapper for the next item that, when submitted, will trigger the reward
   popup. Asymmetric border-radius matches the LLARS signature. */
.comparison-content.milestone-frame {
  border-radius: 16px 4px 16px 4px;
  border: 2px solid rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 4px rgba(176, 202, 151, 0.18);
  margin: 4px;
  padding: 8px;
  transition: box-shadow 0.25s ease, border-color 0.25s ease;
}

/* Header badge: "X more comparisons until your next reward". Pulses
   subtly when the next click is the milestone card. */
.milestone-countdown {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  margin-right: 8px;
  border-radius: 8px 2px 8px 2px;
  background: rgba(176, 202, 151, 0.18);
  color: rgb(var(--v-theme-primary));
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  border: 1px solid rgba(176, 202, 151, 0.3);
}

.milestone-countdown-imminent {
  animation: lcountdownPulse 1.4s ease-in-out infinite;
  background: rgba(176, 202, 151, 0.28);
  border-color: rgb(var(--v-theme-primary));
}

@keyframes lcountdownPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(176, 202, 151, 0.45); }
  50%      { box-shadow: 0 0 0 5px rgba(176, 202, 151, 0); }
}

.comparison-content.layout-stacked {
  flex-direction: column;
}

.comparison-content.layout-side-by-side {
  flex-direction: row;
}

/* When the user swaps panels, visually reverse the order so the conversation
   (context panel) appears on the right and the A/B options appear on the left.
   The panel width styles are also swapped in the template so proportions stay
   consistent after a resize. */
.comparison-content.panels-swapped {
  flex-direction: row-reverse;
}

/* Task-briefing banner: pale-green primary-tinted strip above the
   comparison panels. Shows the scenario's
   ``task_description_markdown`` (or the fallback i18n prompt) so the
   rater sees what they're judging. */
.task-briefing-banner {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin: 0 16px 12px;
  padding: 10px 14px;
  border-radius: 12px 4px 12px 4px;
  background: rgba(176, 202, 151, 0.18);
  border-left: 3px solid rgb(var(--v-theme-primary));
  font-size: 0.9rem;
  line-height: 1.45;
  color: rgb(var(--v-theme-on-surface));
  flex-shrink: 0;
}

.task-briefing-banner :deep(p) {
  margin: 0;
}

.task-briefing-banner :deep(p + p) {
  margin-top: 4px;
}

/* Response prompt (communication_comparison): the question posed to the rater
   above the A/B options. Accent-tinted to read as a direct prompt, distinct
   from the green task-briefing banner. */
.response-prompt {
  margin: 0 0 8px;
  padding: 8px 12px;
  border-radius: 10px 3px 10px 3px;
  background: rgba(136, 196, 200, 0.14);
  border-left: 3px solid var(--llars-accent, #88c4c8);
  font-size: 0.92rem;
  line-height: 1.45;
  color: rgb(var(--v-theme-on-surface));
  flex-shrink: 0;
}

.response-prompt :deep(p) {
  margin: 0;
}

/* Per-item metadata strip — shown inside the context panel (above messages)
   or above the options when no context is present. Visually signals
   "this is item-specific context" without looking like a duplicate briefing. */
/* First-session attention pill (auto-advance discoverability). Shares
   the .hint-pill base class with EvaluationSession.vue; the
   --auto-advance modifier just adjusts the trailing margin so it sits
   tight against the LSwitch. */
.hint-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0 8px;
  padding: 2px 10px;
  border-radius: 12px 3px 12px 3px;
  background: rgba(136, 196, 200, 0.18);
  border: 1px solid rgba(136, 196, 200, 0.55);
  color: rgba(var(--v-theme-on-surface), 0.85);
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  white-space: nowrap;
  pointer-events: none;
  animation: hint-pill-cycle 10s ease-in-out forwards;
}
.hint-pill__arrow {
  animation: hint-arrow-nudge 1.4s ease-in-out infinite;
}
@keyframes hint-pill-cycle {
  0%   { opacity: 0; transform: translateX(-4px) scale(0.95); }
  6%   { opacity: 1; transform: translateX(0)    scale(1); }
  60%  { opacity: 1; transform: translateX(0)    scale(1); }
  100% { opacity: 0; transform: translateX(0)    scale(1); }
}
@keyframes hint-arrow-nudge {
  0%, 100% { transform: translateX(0); }
  50%      { transform: translateX(3px); }
}

/* Per-item header block — full Markdown rendered between the context-header
   bar and the conversation body. Replaces the old truncated plain-text pill. */
.item-header-block {
  padding: 10px 14px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-primary), 0.04);
  font-size: 0.875rem;
  line-height: 1.5;
}

/* Conversation Context Panel */
.context-panel {
  /* Viewport-fit: panel stretches vertically, header is flex-shrink:0,
     body gets the leftover space and scrolls. */
  flex: 1 1 auto;
  min-height: 0;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 12px 3px 12px 3px;
  background: rgba(var(--v-theme-surface-variant), 0.35);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* In side-by-side layout the context panel takes the configured left-panel width. */
.layout-side-by-side .context-panel {
  flex-shrink: 0;
}

.context-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  font-size: 0.92rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex-shrink: 0;
}

.context-subject {
  margin-left: 6px;
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.context-body {
  /* Only the conversation body scrolls; header + (optional) item-header
     stay pinned. min-height: 0 + overflow-y: auto = vertical scroll
     when the message list overflows. */
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 14px;
}

/* Resize handle — direction switches with the active layout.
   Horizontal (side-by-side): vertical bar between context|options.
   Vertical (stacked): horizontal bar between context|options stacked top/bottom. */
.resize-handle {
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s;
}
.resize-handle--horizontal {
  width: 6px;
  cursor: col-resize;
}
.resize-handle--vertical {
  height: 6px;
  width: 100%;
  cursor: row-resize;
}

.resize-handle:hover .handle-line,
.resize-handle:active .handle-line {
  background: var(--llars-primary, #b0ca97);
}

.handle-line {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 1px;
  transition: background 0.2s;
}
.resize-handle--horizontal .handle-line {
  width: 2px;
  height: 40px;
}
.resize-handle--vertical .handle-line {
  height: 2px;
  width: 80px;
}

/* Decision panel: options + tie + notes. Becomes the right column when side-by-side. */
.decision-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1 1 auto;
  min-height: 0;
  /* No `overflow: hidden` here — the comm-mode fly-out animation needs
     to escape this container's bounds. Clipping is enforced higher up
     at .comparison-content + .comparison-interface so the page still
     stays viewport-fit. */
}

/* Options Container */
.options-container {
  display: flex;
  gap: 8px;
  flex: 1 1 auto;
  min-height: 0;
}

/* In side-by-side mode the options stack vertically because horizontal width is shared with context. */
.layout-side-by-side .options-container {
  flex-direction: column;
}

.option-panel {
  flex: 1 1 0;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px 3px 12px 3px;
  cursor: pointer;
  /* No `transition: all` — it competes with the comm-mode fly-out
     keyframe and produces ghost transforms on the way back. Hover
     border/shadow updates are still snappy without it. */
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  /* `overflow: hidden` only clips the option's own children (long text);
     the panel itself can fly out beyond its parent during the
     send-animation, which is the desired effect. */
  overflow: hidden;
}

.option-panel:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.option-a.selected {
  border-color: var(--llars-primary, #b0ca97);
  box-shadow: 0 0 0 3px rgba(176, 202, 151, 0.25);
}

.option-b.selected {
  border-color: var(--llars-secondary, #D1BC8A);
  box-shadow: 0 0 0 3px rgba(209, 188, 138, 0.25);
}

.option-header {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Dev-only "DEV · <model_id>" badge. Rendered only when
   import.meta.env.DEV is true; production builds dead-code-eliminate
   the entire v-if. Striped magenta to make it obvious this isn't a
   prod-facing element. */
.dev-source-tag {
  margin-left: auto;
  padding: 1px 8px;
  border-radius: 6px 2px 6px 2px;
  background: repeating-linear-gradient(
    135deg,
    rgba(232, 160, 135, 0.18),
    rgba(232, 160, 135, 0.18) 6px,
    rgba(232, 160, 135, 0.08) 6px,
    rgba(232, 160, 135, 0.08) 12px
  );
  border: 1px dashed rgba(232, 160, 135, 0.6);
  font-family: 'JetBrains Mono', ui-monospace, monospace;
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.75);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.option-content {
  /* Same pattern as .context-body — only the response text scrolls
     inside, header (option-A/B badge) + footer (select-btn) stay
     pinned to the panel's top/bottom. */
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 12px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.empty-content {
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-align: center;
  padding: 24px;
}

.option-footer {
  padding: 10px 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.2);
  flex-shrink: 0;
}

/* Select Button */
.select-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 38px;
  padding: 10px 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px;
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.select-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.option-a .select-btn.selected {
  background: var(--llars-primary, #b0ca97);
  border-color: transparent;
  color: white;
}

.option-b .select-btn.selected {
  background: var(--llars-secondary, #D1BC8A);
  border-color: transparent;
  color: white;
}

/* VS Divider (stacked only) */
.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  flex-shrink: 0;
}

.vs-text {
  font-size: 1.2rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Tie Section */
.tie-section {
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.tie-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 10px 24px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px;
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tie-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.tie-btn.selected {
  background: var(--llars-accent, #88c4c8);
  border-color: transparent;
  color: white;
}

/* Notes Section — minimal vertical footprint when collapsed (Sozialwissenschaften
   2026-05-18). Just a thin row with a tiny chevron + label; only
   expands to show the textarea when the rater explicitly opens it. */
.notes-section {
  padding-top: 0;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  flex-shrink: 0;
}

.notes-section.expanded {
  padding-top: 4px;
}

.notes-toggle {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  cursor: pointer;
  padding: 1px 0;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: color 0.15s ease;
  line-height: 1.1;
}

.notes-toggle:hover {
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.notes-hint {
  margin-left: 6px;
  font-size: 0.75rem;
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-style: italic;
}

/* Small "Notiz" pill button that opens the note pop-up. */
.notes-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 5px 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.18);
  border-radius: 10px 3px 10px 3px;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.notes-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}
.notes-btn.has-note {
  border-color: var(--llars-accent, #88c4c8);
  color: rgb(var(--v-theme-on-surface));
  background: rgba(136, 196, 200, 0.12);
}

/* Note pop-up card. */
.notes-dialog-card {
  background: rgb(var(--v-theme-surface));
  border-radius: 14px 4px 14px 4px;
  padding: 18px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.18);
}
.notes-dialog-header {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 12px;
  color: rgb(var(--v-theme-on-surface));
}
.notes-dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

/* Rater-note icon button in the context header — accent-coloured when a note
   exists so the rater sees at a glance that something is saved. */
.notes-icon-btn.has-note :deep(.v-icon) {
  color: var(--llars-accent, #88c4c8);
}

/* Navigation Footer */
.nav-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  gap: 12px;
}

.nav-footer .nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Responsive: collapse to stacked on narrow viewports */
@media (max-width: 768px) {
  .comparison-content.layout-side-by-side,
  .comparison-content.layout-side-by-side.panels-swapped {
    flex-direction: column;
  }
  /* CRITICAL side-by-side fix: usePanelResize sets an inline `width: 50%`
     on the context + decision panels for the horizontal (row) layout. When
     the media query collapses the row to a column those inline widths stick,
     so side-by-side rendered as two stuck half-width columns — i.e. it
     "didn't work" on mobile. Force full width + auto height + equal flex so
     the panels stack cleanly top/bottom instead. !important is required to
     beat the inline style. */
  .comparison-content.layout-side-by-side .context-panel,
  .comparison-content.layout-side-by-side .decision-panel {
    width: 100% !important;
    height: auto !important;
    flex: 1 1 0 !important;
  }
  .layout-side-by-side .options-container {
    flex-direction: row;
  }
  .resize-handle {
    display: none;
  }

  /* Small-tablet chrome diet (Steigerwald 2026-06-05): in the 600-905px band
     the "Verlauf bisher" header is cramped — give the title + the fullscreen
     button the space and shed the secondary chrome. The layout mode-toggle
     (already hidden at <=600px) is extended up to <=768px because both layouts
     collapse to a vertical stack here anyway, and the auto-advance switch has
     no room. Buttons keep min-height: 38px (touch target) from base styles. */
  .context-header {
    padding: 6px 12px;
    gap: 6px;
  }
  .mode-toggle-group {
    display: none;
  }
  .auto-advance-switch {
    display: none !important;
  }
}

/* Phones: stack the two response panels vertically so each gets the FULL width
   and is actually readable. At <=768px (tablets) the options stay side-by-side,
   but on a phone two ~50%-width text columns are too cramped to compare — the
   rater scrolls between the full-width A and B panels instead. Source order
   after the 768px block makes this win at <=600px.

   Mobile chrome diet (Steigerwald 2026-06-03): the header rows, the
   "Format: …" item header and the Option A/B header rows all shed vertical
   padding so the actual mail content gets the room. The auto-advance switch
   and its discoverability pill are hidden outright — there's no space for
   them on a phone and the next-item tap is one thumb-reach away anyway. */
@media (max-width: 600px) {
  .layout-side-by-side .options-container {
    flex-direction: column;
  }
  .layout-side-by-side .options-container .option-panel {
    min-height: 160px;
  }

  /* Phones: the OPTION text gets the remaining space. The Verlauf (context)
     above is content-sized + capped so it can't eat the screen — it scrolls
     internally — and the options-container fills the rest. The side-by-side
     selector + !important here BEAT the 768px rule's `flex: 1 1 0 !important`
     (which would otherwise grow the context to an equal split and make the
     "Verlauf bisher" panel too tall on phones). */
  .context-panel,
  .comparison-content.layout-side-by-side .context-panel {
    flex: 0 1 auto !important;
    height: auto !important;
    max-height: 30vh;
  }

  .comparison-content {
    padding: 8px;
    /* Small gap above the (thin) fixed Zurück/Weiter footer bar on phones —
       the desktop 28px looks like wasted space at this viewport size. */
    padding-bottom: 12px;
    gap: 8px;
  }

  /* "Verlauf bisher" header — slim one-line strip that matches the "Aufgabe"
     briefing bar on a phone (Steigerwald 2026-06-08). The layout toggle is
     hidden outright (both modes collapse to the same vertical stack at
     <=600px), so only the title + fullscreen/notes icon-buttons remain. Trim
     the vertical padding hard and shrink the icon-buttons so the row is barely
     taller than its text — same recipe as .briefing-toggle in EvaluationSession. */
  .context-header {
    padding: 2px 10px;
    font-size: 0.78rem;
    gap: 4px;
    line-height: 1.05;
  }
  /* Shrink the fullscreen + notes icon-buttons so they don't dictate the row
     height — without this the x-small LIconBtn touch target keeps the strip
     tall even after the padding is trimmed. */
  .context-header :deep(.v-btn) {
    width: 26px;
    height: 26px;
    min-width: 26px;
    min-height: 26px;
  }
  .context-header :deep(.v-icon) {
    font-size: 16px !important;
  }
  .mode-toggle-group {
    display: none;
  }

  /* Auto-advance is disabled on mobile entirely. */
  .auto-advance-switch,
  .hint-pill--auto-advance {
    display: none !important;
  }

  /* Swap-panels button is meaningless on mobile — side-by-side collapses
     to a vertical stack, so there's no left/right to flip. */
  .mode-btn--swap {
    display: none;
  }

  /* "Format: E-Mail-Beratung" item header — much shorter. */
  .item-header-block {
    padding: 4px 8px;
    font-size: 0.78rem;
    line-height: 1.3;
  }

  /* Option A / B header rows + select buttons — slimmer footprint. */
  .option-header {
    padding: 4px 8px;
  }
  .option-label {
    padding: 2px 8px;
    font-size: 0.78rem;
  }
  /* Option text fills the panel and scrolls internally (base flex:1 +
     overflow-y:auto), so the button stays pinned at the bottom and the answer
     gets the room. Just trim the padding on phones. */
  .option-content {
    padding: 8px 12px;
  }
  .option-footer {
    padding: 4px 8px;
  }
  /* Flatter select buttons on phones (the whole panel is tappable too). */
  .select-btn {
    min-height: 34px;
    padding: 4px 12px;
    font-size: 0.8rem;
  }
  /* Compact "VS" between the stacked options — it was visually oversized. */
  .vs-divider {
    padding: 0 4px;
  }
  .vs-text {
    font-size: 0.8rem;
  }

  /* "Anmerkungen" notes bar — very slim strip on mobile (Steigerwald
     2026-06-05). The toggle row gets tight (but unbroken) padding so the
     collapsed notes section is barely taller than its text; the textarea
     stays fully functional once expanded. */
  .notes-section {
    padding-top: 0;
    margin-top: 0;
  }
  .notes-section:not(.expanded) {
    /* Collapsed: barely taller than the one-line toggle. */
    border-top-color: rgba(var(--v-theme-on-surface), 0.05);
  }
  .notes-toggle {
    /* Keep the strip thin (tight padding + line-height) but ensure the toggle
       text stays readable (>=0.78rem) — only the vertical chrome is trimmed. */
    padding: 1px 0;
    font-size: 0.8rem;
    line-height: 1.05;
  }
}

/* =========================================================================
 * Communication-Comparison mode
 *
 * Distinct neutral colours for Option A (teal) and Option B (violet) so
 * they don't collide with the message bubble palette in LMessageList
 * (counsellor = primary green-tone, client = surface-variant). The
 * rater shouldn't be biased by colour cues that match Berater/Klient.
 *
 * Animation: clicking A or B flies the panel out + fades the other one
 * before the composable POSTs. `isSending` is set in selectOption();
 * the watcher on currentItem clears it when the next item loads.
 * ========================================================================= */

/* Slightly neutral pill replacing the old LTag (variant=primary/secondary)
   used in non-communication mode. */
.option-label {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.option-label--a {
  background: rgba(123, 175, 197, 0.18);
  color: #2f6379;
  border: 1px solid rgba(123, 175, 197, 0.55);
}
.option-label--b {
  background: rgba(169, 137, 197, 0.18);
  color: #5a3d7a;
  border: 1px solid rgba(169, 137, 197, 0.55);
}

.communication-mode .option-a {
  --opt-color: #7BAFC5;
  --opt-color-strong: #2f6379;
  --opt-tint: rgba(123, 175, 197, 0.10);
}
.communication-mode .option-b {
  --opt-color: #A989C5;
  --opt-color-strong: #5a3d7a;
  --opt-tint: rgba(169, 137, 197, 0.10);
}
.communication-mode .option-a.selected,
.communication-mode .option-b.selected {
  border-color: var(--opt-color);
  background: var(--opt-tint);
  box-shadow: 0 0 0 1px var(--opt-color) inset;
}
.communication-mode .option-a .select-btn:hover,
.communication-mode .option-b .select-btn:hover {
  background: var(--opt-tint);
  border-color: var(--opt-color);
}
.communication-mode .option-a .select-btn.selected,
.communication-mode .option-b .select-btn.selected {
  background: var(--opt-color);
  border-color: var(--opt-color);
  color: #fff;
}
.communication-mode .option-a .option-label,
.communication-mode .option-b .option-label {
  font-size: 0.82rem;
}

/* Fly-out: the picked panel slides slightly up + fades; the other
   panel just fades. Both pointer-events disabled mid-animation. */
/* Only the panel currently mid-flight gets blocked from re-clicks — the
   faded/standing-by sibling stays interactive so the rater can change
   their mind by clicking the OTHER option (Sozialwissenschaften feedback 2026-05-18,
   "was machen wir wenn man sich umentscheidet?"). Switching options
   re-triggers selectOption, which clears the old ghost message and
   plays a fresh animation for the new pick. */
.communication-mode .option-panel.is-flying {
  pointer-events: none;
}
/* Picked card: brief pop + glow flash, then fade-out in place. The
   actual "send" motion is carried by the .send-flying-icon overlay
   that lives as a sibling — keeping the card stationary avoids
   clipping issues with the surrounding flex/overflow layout. */
.communication-mode .option-panel.is-flying {
  z-index: 5;
  animation: comm-pop-fade 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  transform-origin: center center;
}
.communication-mode .option-panel.is-fading {
  animation: comm-fade-back 0.6s ease-out forwards;
}
.communication-mode .option-panel.option-a.is-flying {
  box-shadow:
    0 0 0 4px rgba(123, 175, 197, 0.55),
    0 0 36px 12px rgba(123, 175, 197, 0.55),
    0 16px 36px rgba(123, 175, 197, 0.35);
}
.communication-mode .option-panel.option-b.is-flying {
  box-shadow:
    0 0 0 4px rgba(169, 137, 197, 0.55),
    0 0 36px 12px rgba(169, 137, 197, 0.55),
    0 16px 36px rgba(169, 137, 197, 0.35);
}
@keyframes comm-pop-fade {
  0%   { opacity: 1; transform: scale(1); }
  /* Phase 1 — pickup pop. Card grows briefly to read as "selected with
     conviction" before the icon launches. */
  18%  { opacity: 1; transform: scale(1.05); }
  /* Phase 2 — fade-down. Card shrinks slightly and fades while the icon
     overlay completes its flight across the container. */
  100% { opacity: 0; transform: scale(0.9); }
}
@keyframes comm-fade-back {
  0%   { opacity: 1; transform: scale(1); filter: blur(0); }
  100% { opacity: 0.18; transform: scale(0.92); filter: blur(2px); }
}

/* Paper-plane "send" overlay. Sibling of the option panels, anchored
   above whichever panel was picked, escapes the panel's overflow:hidden
   because it lives one level up in .options-container. The animation
   has three beats: appear scaled-in at the centre of the picked panel
   → arc upward-right → vanish above the container, scaled big as it
   leaves so the perspective reads as "flying away". */
.options-container {
  position: relative;
}
.send-flying-icon {
  position: absolute;
  pointer-events: none;
  z-index: 20;
  color: #7BAFC5;
  filter: drop-shadow(0 4px 12px rgba(123, 175, 197, 0.5));
}
.send-flying-icon--b {
  color: #A989C5;
  filter: drop-shadow(0 4px 12px rgba(169, 137, 197, 0.5));
}
/* Stacked layout (panels side-by-side, A=left B=right): icon starts
   centred over the picked panel. A flies up-and-right (toward the upper
   corner), B flies up-and-left so the two animations mirror each other.
   The icon itself is also horizontally flipped for B (scaleX(-1)) so
   the plane's nose always points in the direction of travel. */
.send-flying-icon--stacked.send-flying-icon--a {
  top: 50%;
  left: 25%;
  animation: send-fly-stacked-a 1.2s cubic-bezier(0.3, 0, 0.2, 1) forwards;
}
.send-flying-icon--stacked.send-flying-icon--b {
  top: 50%;
  left: 75%;
  animation: send-fly-stacked-b 1.2s cubic-bezier(0.3, 0, 0.2, 1) forwards;
}
/* Side-by-side layout (panels stacked vertically, A=top B=bottom):
   icon starts centred over the picked panel and flies toward the
   conversation panel (left side). A from the top half, B from the
   bottom half — both arcing diagonally toward the upper-left corner
   of the container. */
.send-flying-icon--side.send-flying-icon--a {
  top: 25%;
  left: 50%;
  animation: send-fly-side-a 1.2s cubic-bezier(0.3, 0, 0.2, 1) forwards;
}
.send-flying-icon--side.send-flying-icon--b {
  top: 75%;
  left: 50%;
  animation: send-fly-side-b 1.2s cubic-bezier(0.3, 0, 0.2, 1) forwards;
}
@keyframes send-fly-stacked-a {
  /* up-and-right */
  0%   { opacity: 0; transform: translate(-50%, -50%) scale(0.3); }
  15%  { opacity: 1; transform: translate(-50%, -50%) scale(1.4); }
  35%  { opacity: 1; transform: translate(-30%, -150%) scale(1.2); }
  100% { opacity: 0; transform: translate(80%, -500%) scale(0.6); }
}
@keyframes send-fly-stacked-b {
  /* up-and-left, mirrored. scaleX(-1) flips the icon horizontally so
     the paper plane's nose still points in the direction of motion. */
  0%   { opacity: 0; transform: translate(-50%, -50%) scale(-0.3, 0.3); }
  15%  { opacity: 1; transform: translate(-50%, -50%) scale(-1.4, 1.4); }
  35%  { opacity: 1; transform: translate(-70%, -150%) scale(-1.2, 1.2); }
  100% { opacity: 0; transform: translate(-180%, -500%) scale(-0.6, 0.6); }
}
@keyframes send-fly-side-a {
  /* up-and-right from the top panel */
  0%   { opacity: 0; transform: translate(-50%, -50%) scale(0.3); }
  15%  { opacity: 1; transform: translate(-50%, -50%) scale(1.4); }
  35%  { opacity: 1; transform: translate(80%, -130%) scale(1.2); }
  100% { opacity: 0; transform: translate(280%, -200%) scale(0.6); }
}
@keyframes send-fly-side-b {
  /* up-and-left mirror from the bottom panel — flipped horizontally
     so the plane still points where it's flying. */
  0%   { opacity: 0; transform: translate(-50%, -50%) scale(-0.3, 0.3); }
  15%  { opacity: 1; transform: translate(-50%, -50%) scale(-1.4, 1.4); }
  35%  { opacity: 1; transform: translate(-180%, -130%) scale(-1.2, 1.2); }
  100% { opacity: 0; transform: translate(-380%, -200%) scale(-0.6, 0.6); }
}

/* When the ghost-Berater message lands in the conversation, briefly
   highlight it so the rater sees their pick "arrive". The ghost row
   itself is rendered by LMessageList with the same styling as any
   other turn — we add a one-shot slide-in via the .has-sent-ghost
   parent class on .context-body. */
.context-body.has-sent-ghost :deep(.message-row:last-child),
.context-body.has-sent-ghost :deep(.message-item:last-child) {
  animation: sent-ghost-slide-in 0.45s ease-out;
}
@keyframes sent-ghost-slide-in {
  0%   { opacity: 0; transform: translateY(20px); }
  60%  { opacity: 1; transform: translateY(-2px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========================================================================
 * Mobile fullscreen read overlay (Option A / B)
 *
 * Mirrors AdminMailCenterSection's .fullscreen-* shell: a top bar with the
 * option label + close button, a scrolling content area, and a pinned footer
 * with the select button. Only ever rendered on mobile (the trigger is
 * v-if="isMobile"); the dialog content classes are scoped so desktop is
 * unaffected. Uses the LLARS asymmetric radius on the select button.
 * ========================================================================= */
.option-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
}
.option-fullscreen-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.4);
  flex-shrink: 0;
}
.option-fullscreen-content {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 14px;
}
.option-fullscreen-footer {
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.25);
  flex-shrink: 0;
}

/* Slim mobile fullscreen trigger — pushed to the right of the option header,
   tiny so it doesn't compete with the content. */
.option-fullscreen-btn {
  margin-left: auto;
}
</style>
