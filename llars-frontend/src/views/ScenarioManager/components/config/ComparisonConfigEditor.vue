<template>
  <div class="comparison-config">
    <!-- Comparison Type -->
    <v-select
      v-model="localConfig.type"
      :items="comparisonTypes"
      :label="$t('scenarioManager.evalConfig.comparison.comparisonType')"
      variant="outlined"
      density="compact"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Per-Item Header Template -->
    <div class="editor-section mb-4">
      <div class="section-toggle" @click="itemHeaderOpen = !itemHeaderOpen">
        <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.itemHeaderTemplate', 'Per-Item-Header') }}</h5>
        <v-icon class="section-chevron" :class="{ 'is-open': itemHeaderOpen }" size="18">mdi-chevron-down</v-icon>
      </div>

      <div v-show="itemHeaderOpen" class="section-body">
        <p class="hint-text mb-2">{{ itemHeaderTemplateHint }}</p>

        <!-- Variable picker: chips for each detected metadata key.
             Click → insert {{key}} at cursor.
             Drag → drop anywhere in the textarea to insert natively. -->
        <div v-if="availableVariables.length" class="variable-picker mb-2">
          <span class="variable-picker-label">Variablen:</span>
          <span
            v-for="key in availableVariables"
            :key="key"
            class="var-chip"
            draggable="true"
            :title="`Klicken oder in den Editor ziehen, um ${'{{'+ key +'}'+'}'} einzufügen`"
            @click="insertVariable(key)"
            @dragstart="onVarDragStart($event, key)"
          >
            <span class="var-chip-brace" v-text="'{{'" />{{ key }}<span class="var-chip-brace" v-text="'}}'" />
          </span>
        </div>

        <LMarkdownEditor
          ref="itemHeaderEditorRef"
          :model-value="getLocalizedText(localConfig.itemHeaderTemplate, locale)"
          :placeholder="itemHeaderPlaceholder"
          :rows="4"
          @update:modelValue="updateItemHeaderTemplate"
        />
      </div>
    </div>

    <!-- Options -->
    <div class="config-options mb-4">
      <LSwitch
        v-model="localConfig.allowTie"
        :label="$t('scenarioManager.evalConfig.comparison.allowTie')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.showConfidence"
        :label="$t('scenarioManager.evalConfig.comparison.showConfidence')"
        @update:modelValue="emitUpdate"
      />
      <LSwitch
        v-model="localConfig.gamificationEnabled"
        :label="$t('scenarioManager.evalConfig.comparison.gamificationEnabled')"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Gamification Thresholds (when enabled) -->
    <div v-if="localConfig.gamificationEnabled" class="gamification-section mb-4">
      <h5 class="subsection-title mb-2">
        {{ $t('scenarioManager.evalConfig.comparison.gamificationThresholds') }}
      </h5>
      <v-row dense>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.gamificationFirstMilestone"
            :label="$t('scenarioManager.evalConfig.comparison.gamificationFirstMilestone')"
            type="number"
            variant="outlined"
            density="compact"
            :min="2"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.gamificationRecurringMilestone"
            :label="$t('scenarioManager.evalConfig.comparison.gamificationRecurringMilestone')"
            type="number"
            variant="outlined"
            density="compact"
            :min="1"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>

      <!-- Progressive reveal: only show items up to next unlock -->
      <LSwitch
        v-model="localConfig.progressiveReveal"
        :label="$t('scenarioManager.evalConfig.comparison.progressiveReveal')"
        :hint="$t('scenarioManager.evalConfig.comparison.progressiveRevealHint')"
        persistent-hint
        class="mt-3"
        @update:modelValue="emitUpdate"
      />
    </div>

    <!-- Items per comparison -->
    <v-text-field
      v-model.number="localConfig.itemsPerComparison"
      :label="$t('scenarioManager.evalConfig.comparison.itemsPerComparison')"
      type="number"
      variant="outlined"
      density="compact"
      :min="2"
      :max="5"
      class="mb-3"
      @update:modelValue="emitUpdate"
    />

    <!-- Confidence Scale (when enabled) -->
    <div v-if="localConfig.showConfidence" class="confidence-section mb-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.confidenceScale') }}</h5>
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.min"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMin')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
        <v-col cols="6">
          <v-text-field
            v-model.number="localConfig.confidenceScale.max"
            :label="$t('scenarioManager.evalConfig.comparison.confidenceMax')"
            type="number"
            variant="outlined"
            density="compact"
            @update:modelValue="emitUpdate"
          />
        </v-col>
      </v-row>
    </div>

    <!-- Tournament Options (when tournament type) -->
    <div v-if="localConfig.type === 'tournament'" class="tournament-section mt-4">
      <h5 class="subsection-title">{{ $t('scenarioManager.evalConfig.comparison.tournamentOptions') }}</h5>
      <v-select
        v-model="localConfig.rounds"
        :items="roundOptions"
        :label="$t('scenarioManager.evalConfig.comparison.rounds')"
        variant="outlined"
        density="compact"
        @update:modelValue="emitUpdate"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  criteriaListToMarkdown,
  getLocalizedText,
  setLocalizedText
} from '@/utils/scenarioBriefing'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  // Metadata keys detected from the uploaded dataset (e.g. ['axis', 'target_pole', 'persona_name']).
  // Shown as clickable/draggable chips above the itemHeaderTemplate editor.
  availableVariables: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])
const { t, locale } = useI18n()

// Ref to the LMarkdownEditor for the itemHeaderTemplate so we can call insertText().
const itemHeaderEditorRef = ref(null)
const itemHeaderOpen = ref(false)

// Click a variable chip → insert {{key}} at the current cursor position in the editor.
function insertVariable(key) {
  itemHeaderEditorRef.value?.insertText(`{{${key}}}`)
}

// Drag a chip → set the dragged text so the browser inserts it on native textarea drop.
function onVarDragStart(event, key) {
  event.dataTransfer.setData('text/plain', `{{${key}}}`)
  event.dataTransfer.effectAllowed = 'copy'
}

const comparisonTypes = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.pairwise'), value: 'pairwise' },
  { title: t('scenarioManager.evalConfig.comparison.typeOptions.tournament'), value: 'tournament' }
])

const roundOptions = computed(() => [
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.auto'), value: 'auto' },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round1'), value: 1 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round2'), value: 2 },
  { title: t('scenarioManager.evalConfig.comparison.roundOptions.round3'), value: 3 }
])

// Hint text references {{variable}} literally — defined in script to avoid
// Vue template compiler mis-parsing it as an interpolation expression.
const itemHeaderTemplateHint = computed(() =>
  t(
    'scenarioManager.evalConfig.comparison.itemHeaderTemplateHint',
    'Wird pro Item über dem Gesprächsverlauf angezeigt. Platzhalter {{variable}} werden durch Item-Metadaten ersetzt.'
  )
)

const itemHeaderPlaceholder = computed(() => [
  locale.value === 'en'
    ? '**{{persona_name}}** — Target style: {{target_style}} (Axis: {{axis}})\n\nCase: {{hauptanliegen}}'
    : '**{{persona_name}}** — Zielstil: {{target_style}} (Achse: {{axis}})\n\nHauptanliegen: {{hauptanliegen}}'
].join('\n'))


const localConfig = ref({
  type: 'pairwise',
  question: { de: 'Welche Option ist besser?', en: 'Which option is better?' },
  taskDescriptionMarkdown: { de: '', en: '' },
  itemHeaderTemplate: { de: '', en: '' },
  criteriaMarkdown: { de: '', en: '' },
  itemsPerComparison: 2,
  // Tie is opt-in: scenario authors must explicitly enable it in the wizard.
  allowTie: false,
  showConfidence: false,
  // Gamification reward system — same opt-in flow as allowTie. When on, the
  // assessor sees a celebratory popup at the first milestone and at every
  // recurring milestone, with their preference patterns so far.
  gamificationEnabled: false,
  gamificationFirstMilestone: 10,
  gamificationRecurringMilestone: 5,
  // Progressive reveal: hide cards beyond the next unlock point so the
  // perceived task is bite-sized (10 → reward → 5 → reward → 5 → …).
  // Only takes effect when gamificationEnabled is also on.
  progressiveReveal: false,
  confidenceScale: { min: 1, max: 5 },
  criteria: [],
  rounds: 'auto'
})

function updateItemHeaderTemplate(value) {
  localConfig.value.itemHeaderTemplate = setLocalizedText(
    localConfig.value.itemHeaderTemplate,
    value,
    locale.value
  )
  emitUpdate()
}

function emitUpdate() {
  emit('update:modelValue', { ...localConfig.value })
}

function initFromProps() {
  if (props.modelValue) {
    localConfig.value = {
      ...localConfig.value,
      ...props.modelValue,
      taskDescriptionMarkdown: props.modelValue.taskDescriptionMarkdown || {
        de: getLocalizedText(props.modelValue.question, 'de'),
        en: getLocalizedText(props.modelValue.question, 'en')
      },
      itemHeaderTemplate: props.modelValue.itemHeaderTemplate || { de: '', en: '' },
      criteriaMarkdown: props.modelValue.criteriaMarkdown || {
        de: criteriaListToMarkdown(props.modelValue.criteria, 'de'),
        en: criteriaListToMarkdown(props.modelValue.criteria, 'en')
      },
      criteria: props.modelValue.criteria ? [...props.modelValue.criteria] : [],
      confidenceScale: props.modelValue.confidenceScale || { min: 1, max: 5 }
    }
  }
}

watch(() => props.modelValue, initFromProps, { deep: true })

onMounted(initFromProps)
</script>

<style scoped>
.comparison-config {
  padding: 8px 0;
}

.subsection-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin: 0;
}

.config-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.hint-text {
  font-size: 0.78rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
  line-height: 1.4;
}

.editor-section,
.confidence-section,
.criteria-section,
.tournament-section,
.gamification-section {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  padding: 12px;
}

.section-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.section-chevron {
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: transform 0.2s ease;
}

.section-chevron.is-open {
  transform: rotate(180deg);
}

.section-body {
  padding-top: 10px;
}

/* Variable picker strip above the itemHeaderTemplate editor */
.variable-picker {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.variable-picker-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  white-space: nowrap;
}

/* Each variable chip */
.var-chip {
  display: inline-flex;
  align-items: center;
  gap: 1px;
  padding: 2px 8px;
  border-radius: 6px 2px 6px 2px;
  border: 1px solid rgba(var(--v-theme-primary), 0.4);
  background: rgba(var(--v-theme-primary), 0.07);
  font-size: 0.75rem;
  font-family: 'Fira Mono', 'Consolas', monospace;
  color: rgba(var(--v-theme-on-surface), 0.8);
  cursor: grab;
  user-select: none;
  transition: background 0.15s, border-color 0.15s;
}

.var-chip:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  border-color: rgba(var(--v-theme-primary), 0.7);
  color: rgb(var(--v-theme-on-surface));
}

.var-chip:active {
  cursor: grabbing;
}

.var-chip-brace {
  color: rgba(var(--v-theme-primary), 0.6);
  font-weight: 700;
  font-size: 0.7rem;
}
</style>
