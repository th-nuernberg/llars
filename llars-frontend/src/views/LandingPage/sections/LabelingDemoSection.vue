<template>
  <section id="live-demo" class="demo-section" :class="{ 'dark-mode': isDarkMode }">
    <div class="section-inner">
      <h2 class="section-title" data-reveal>{{ $t('landing.demo.title') }}</h2>
      <p class="section-subtitle" data-reveal data-reveal-delay="100">
        {{ $t('landing.demo.subtitle') }}
      </p>

      <div class="demo-layout">
        <!-- Linke Spalte: Was der Co-Pilot ist (und was nicht) -->
        <div class="demo-copy" data-reveal data-reveal-delay="150">
          <h3 class="copy-title">
            <v-icon size="22" color="#c9a8e2" class="mr-1">mdi-robot-outline</v-icon>
            {{ $t('landing.demo.copilotTitle') }}
          </h3>
          <p class="copy-intro">{{ $t('landing.demo.copilotIntro') }}</p>

          <ul class="copilot-points">
            <li v-for="point in copilotPoints" :key="point.key">
              <v-icon size="18" :color="point.color">{{ point.icon }}</v-icon>
              <span>{{ $t(`landing.demo.points.${point.key}`) }}</span>
            </li>
          </ul>

          <p class="demo-hint">
            <v-icon size="16">mdi-cursor-default-click-outline</v-icon>
            {{ $t('landing.demo.tryIt') }}
          </p>
        </div>

        <!-- Rechte Spalte: interaktives Labeling-Fenster -->
        <div
          ref="win"
          v-glow
          class="app-window glow-surface"
          data-reveal
          data-reveal-delay="250"
          @mouseenter="onEnter"
          @mousemove="onMove"
          @mouseleave="onLeave"
        >
          <!-- Fenster-Chrome -->
          <div class="win-bar">
            <span class="dot dot-r" /><span class="dot dot-y" /><span class="dot dot-g" />
            <span class="win-url">llars.e-beratungsinstitut.de/scenarios/42/evaluate</span>
          </div>

          <!-- Szenario-Meta + Fortschritt -->
          <div class="win-meta">
            <span class="meta-scenario">{{ $t('landing.demo.scenario') }}</span>
            <span class="meta-progress">
              {{ $t('landing.demo.item') }} {{ 12 + currentIdx }} / 48
            </span>
          </div>
          <div class="progress-track" aria-hidden="true">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }" />
          </div>

          <Transition name="demo-item" mode="out-in">
            <div :key="currentIdx" class="win-body">
              <!-- Item-Text mit hervorgehobenem Textbeleg -->
              <div class="item-text">
                <span>{{ $t(`landing.demo.items.${itemKey}.textPre`) }}</span>
                <mark class="evidence">{{ $t(`landing.demo.items.${itemKey}.evidence`) }}</mark>
                <span>{{ $t(`landing.demo.items.${itemKey}.textPost`) }}</span>
              </div>

              <!-- Co-Pilot-Vorschlag -->
              <div class="copilot-panel">
                <div class="copilot-head">
                  <v-icon size="16" color="#c9a8e2">mdi-robot-outline</v-icon>
                  <span class="copilot-name">{{ $t('landing.demo.copilotSuggestion') }}</span>
                  <span class="confidence" :class="`confidence-${item.confidence}`">
                    {{ $t(`landing.demo.confidence.${item.confidence}`) }}
                  </span>
                </div>
                <div class="copilot-suggested">
                  {{ $t(`landing.demo.labels.${item.suggested}`) }}
                </div>
                <p class="copilot-rationale">
                  {{ $t(`landing.demo.items.${itemKey}.rationale`) }}
                </p>
                <button
                  type="button"
                  class="copilot-apply"
                  :class="{ applied: saved && acceptedFromCopilot }"
                  @click="applySuggestion"
                >
                  <v-icon size="14">
                    {{ saved && acceptedFromCopilot ? 'mdi-check' : 'mdi-arrow-down-thin' }}
                  </v-icon>
                  {{ saved && acceptedFromCopilot
                    ? $t('landing.demo.applied')
                    : $t('landing.demo.apply') }}
                </button>
              </div>

              <!-- Label-Auswahl -->
              <div class="label-row" role="group" :aria-label="$t('landing.demo.chooseLabel')">
                <button
                  v-for="label in labels"
                  :key="label"
                  type="button"
                  class="label-chip"
                  :class="{ selected: selected === label }"
                  @click="selectLabel(label)"
                >
                  {{ $t(`landing.demo.labels.${label}`) }}
                </button>
              </div>

              <!-- Autosave-Status -->
              <div class="win-foot" :class="{ visible: saved }" aria-live="polite">
                <v-icon size="14" color="#98d4bb">mdi-check-circle</v-icon>
                {{ $t('landing.demo.saved') }}
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
/**
 * Interaktive Labeling-Demo mit Co-Pilot-Vorschlag (Landing Page).
 *
 * DOM-gebautes App-Fenster nach dem Akteon-ProductShowcase-Muster: 3D-Tilt
 * zum Cursor + v-glow-Glanz, dazu ECHTE Klick-Interaktion — Besucher können
 * drei Demo-Items durchlabeln (Label wählen oder Co-Pilot-Vorschlag
 * übernehmen → Autosave-Häkchen → nächstes Item).
 *
 * Cursor-Semantik ist bewusst strikt: Nur die Label-Chips und der
 * Übernehmen-Button sind klickbar und zeigen cursor:pointer; der Rest des
 * Fensters bleibt beim Default-Cursor (Interaktivität signalisiert das
 * Fenster über Tilt/Glow, nicht über einen falschen Pointer).
 *
 * Die Demo spiegelt das reale Co-Pilot-Verhalten: Vorschlag mit Begründung,
 * Konfidenz und markiertem Textbeleg — klar gekennzeichnet und NIE
 * vorausgewählt (die Chips starten immer unselektiert).
 */
import { ref, computed, onUnmounted } from 'vue'
import { useTheme } from 'vuetify'
import { useMobile } from '@/composables/useMobile'
import { glow as vGlow } from '../directives/glow'

const theme = useTheme()
const isDarkMode = computed(() => theme.global.current.value.dark)
const { isTouchDevice } = useMobile()

const copilotPoints = [
  { key: 'evidence',   icon: 'mdi-text-search',        color: '#88c4c8' },
  { key: 'neverPre',   icon: 'mdi-account-check',      color: '#b0ca97' },
  { key: 'hiddenSet',  icon: 'mdi-eye-off-outline',    color: '#D1BC8A' },
  { key: 'logging',    icon: 'mdi-chart-timeline-variant', color: '#e8a087' },
]

// Demo-Inhalt: 3 Items, die im Kreis durchlaufen werden
const itemKeys = ['one', 'two', 'three']
const items = [
  { suggested: 'helpful',       confidence: 'high' },
  { suggested: 'notHelpful',    confidence: 'medium' },
  { suggested: 'partlyHelpful', confidence: 'low' },
]
const labels = ['helpful', 'partlyHelpful', 'notHelpful']

const currentIdx = ref(0)
const selected = ref(null)
const saved = ref(false)
const acceptedFromCopilot = ref(false)
let advanceTimer = null

const itemKey = computed(() => itemKeys[currentIdx.value])
const item = computed(() => items[currentIdx.value])
const progressPercent = computed(
  () => ((11 + currentIdx.value + (saved.value ? 1 : 0)) / 48) * 100
)

function selectLabel(label) {
  if (saved.value) return // während des Item-Wechsels nicht doppelt labeln
  selected.value = label
  saved.value = true
  // Nach kurzer Bestätigung automatisch zum nächsten Item (wie Autosave +
  // Weiter-Navigation in der echten Evaluation)
  advanceTimer = setTimeout(() => {
    currentIdx.value = (currentIdx.value + 1) % itemKeys.length
    selected.value = null
    saved.value = false
    acceptedFromCopilot.value = false
  }, 1200)
}

function applySuggestion() {
  if (saved.value) return
  acceptedFromCopilot.value = true
  selectLabel(item.value.suggested)
}

onUnmounted(() => clearTimeout(advanceTimer))

// --- 3D-Tilt (Akteon ProductShowcase-Muster) ---
const win = ref(null)

const prefersReducedMotion = () =>
  typeof window !== 'undefined'
  && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function noTilt() {
  return isTouchDevice.value || prefersReducedMotion()
}

function onEnter() {
  if (noTilt() || !win.value) return
  win.value.style.transition = 'transform 0.12s ease-out'
}

function onMove(e) {
  if (noTilt() || !win.value) return
  const r = win.value.getBoundingClientRect()
  const rx = ((r.top + r.height / 2 - e.clientY) / (r.height / 2)) * 1.6
  const ry = ((e.clientX - (r.left + r.width / 2)) / (r.width / 2)) * 1.6
  win.value.style.transform = `perspective(1400px) rotateX(${rx}deg) rotateY(${ry}deg)`
}

function onLeave() {
  if (noTilt() || !win.value) return
  win.value.style.transition = 'transform 0.5s ease'
  win.value.style.transform = 'perspective(1400px) rotateX(0) rotateY(0)'
}
</script>

<style scoped>
.demo-section {
  padding: 100px 24px;
}

.section-inner {
  max-width: 1100px;
  margin: 0 auto;
}

.section-title {
  text-align: center;
  font-size: clamp(1.5rem, 3vw, 2.25rem);
  font-weight: 300;
  color: var(--landing-text-primary);
  margin: 0 0 12px;
}

.section-subtitle {
  text-align: center;
  color: var(--landing-text-secondary);
  font-size: 1.05rem;
  margin: 0 0 48px;
  max-width: 620px;
  margin-left: auto;
  margin-right: auto;
}

.demo-layout {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 40px;
  align-items: center;
}

/* ============================================
   Linke Spalte: Co-Pilot-Erklärung
   ============================================ */
.copy-title {
  display: flex;
  align-items: center;
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  margin: 0 0 12px;
}

.copy-intro {
  color: var(--landing-text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
  margin: 0 0 20px;
}

.copilot-points {
  list-style: none;
  padding: 0;
  margin: 0 0 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.copilot-points li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--landing-text-secondary);
}

.copilot-points li .v-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.demo-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-style: italic;
  color: var(--landing-text-secondary);
  opacity: 0.8;
  margin: 0;
}

/* ============================================
   App-Fenster
   ============================================ */
.app-window {
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  background: var(--landing-card-bg);
  border: 1px solid var(--landing-card-border);
  box-shadow: 0 24px 60px -20px rgba(44, 62, 45, 0.28);
  will-change: transform;
  transform: perspective(1400px);
  /* opacity/transform in der Liste halten → data-reveal-Fade bleibt intakt */
  transition: opacity 0.6s ease, transform 0.6s ease;
}

.win-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--landing-card-border);
  background: rgba(176, 202, 151, 0.08);
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot-r { background: #e8a087; }
.dot-y { background: #e8c87a; }
.dot-g { background: #98d4bb; }

.win-url {
  margin-left: 10px;
  font-size: 0.7rem;
  color: var(--landing-text-secondary);
  background: var(--landing-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 999px;
  padding: 3px 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.win-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px 8px;
  font-size: 0.78rem;
  color: var(--landing-text-secondary);
}

.meta-scenario {
  font-weight: 500;
  color: var(--landing-text-primary);
}

.progress-track {
  height: 4px;
  margin: 0 18px;
  border-radius: 999px;
  background: var(--landing-card-border);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #b0ca97, #88c4c8);
  transition: width 0.5s cubic-bezier(0.2, 0.7, 0.2, 1);
}

.win-body {
  padding: 16px 18px 18px;
}

.item-text {
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--landing-text-primary);
  background: var(--landing-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 8px 2px 8px 2px;
  padding: 14px 16px;
  margin-bottom: 12px;
}

.evidence {
  background: rgba(201, 168, 226, 0.28);
  color: inherit;
  border-radius: 3px;
  padding: 0 2px;
}

.dark-mode .evidence {
  background: rgba(201, 168, 226, 0.22);
}

/* Co-Pilot-Panel */
.copilot-panel {
  border: 1px solid rgba(201, 168, 226, 0.45);
  background: rgba(201, 168, 226, 0.08);
  border-radius: 8px 2px 8px 2px;
  padding: 12px 14px;
  margin-bottom: 14px;
}

.copilot-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.copilot-name {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--landing-text-secondary);
}

.confidence {
  margin-left: auto;
  font-size: 0.7rem;
  border-radius: 6px 2px 6px 2px;
  padding: 2px 8px;
}

.confidence-high { background: rgba(152, 212, 187, 0.25); color: #4a7c62; }
.confidence-medium { background: rgba(232, 200, 122, 0.25); color: #8a6d2f; }
.confidence-low { background: rgba(232, 160, 135, 0.25); color: #9c5a41; }

.dark-mode .confidence-high { color: #98d4bb; }
.dark-mode .confidence-medium { color: #e8c87a; }
.dark-mode .confidence-low { color: #e8a087; }

.copilot-suggested {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--landing-text-primary);
  margin-bottom: 4px;
}

.copilot-rationale {
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--landing-text-secondary);
  margin: 0 0 10px;
}

.copilot-apply {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  background: rgba(201, 168, 226, 0.2);
  border: 1px solid rgba(201, 168, 226, 0.5);
  border-radius: 8px 2px 8px 2px;
  padding: 5px 12px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}

.copilot-apply:hover {
  background: rgba(201, 168, 226, 0.32);
  border-color: #c9a8e2;
  transform: translateY(-1px);
}

.copilot-apply.applied {
  background: rgba(152, 212, 187, 0.25);
  border-color: #98d4bb;
  cursor: default;
  transform: none;
}

/* Label-Chips */
.label-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.label-chip {
  flex: 1 1 auto;
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--landing-text-primary);
  background: var(--landing-bg);
  border: 1px solid var(--landing-card-border);
  border-radius: 8px 2px 8px 2px;
  padding: 9px 14px;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease,
              box-shadow 0.2s ease, transform 0.15s ease;
}

.label-chip:hover {
  border-color: #b0ca97;
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
}

.label-chip.selected {
  background: rgba(176, 202, 151, 0.25);
  border-color: #b0ca97;
  box-shadow: inset 0 0 0 1px #b0ca97;
}

/* Autosave-Status */
.win-foot {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--landing-text-secondary);
  min-height: 18px;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.win-foot.visible {
  opacity: 1;
}

/* Item-Wechsel: sanftes Raus-/Reinschieben */
.demo-item-enter-active,
.demo-item-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.demo-item-enter-from {
  opacity: 0;
  transform: translateX(16px);
}

.demo-item-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 960px) {
  .demo-layout {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .demo-section {
    padding: 60px 16px;
  }
}

/* Reduced motion: kein Tilt, kein Slide */
@media (prefers-reduced-motion: reduce) {
  .app-window {
    transform: none !important;
  }

  .demo-item-enter-active,
  .demo-item-leave-active {
    transition: opacity 0.2s ease;
  }

  .demo-item-enter-from,
  .demo-item-leave-to {
    transform: none;
  }

  .label-chip:hover,
  .copilot-apply:hover {
    transform: none;
  }
}
</style>
