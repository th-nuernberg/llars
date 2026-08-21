<template>
  <div class="preferences-tab">
    <!-- Evaluation / Tastatur-Shortcuts -->
    <section class="settings-panel" role="group" aria-labelledby="shortcuts-title">
      <header class="panel-header">
        <LIcon size="18" class="panel-icon">mdi-keyboard-outline</LIcon>
        <h2 id="shortcuts-title" class="panel-title">{{ $t('userSettings.preferences.shortcuts.title') }}</h2>
      </header>

      <div class="panel-content">
        <p class="section-description">
          {{ $t('userSettings.preferences.shortcuts.description') }}
        </p>

        <div class="preference-row">
          <div class="preference-text">
            <div class="preference-label">
              {{ $t('userSettings.preferences.shortcuts.spacebarAdvance.label') }}
              <kbd class="kbd">{{ $t('userSettings.preferences.shortcuts.spacebarAdvance.key') }}</kbd>
            </div>
            <p class="preference-hint">
              {{ $t('userSettings.preferences.shortcuts.spacebarAdvance.hint') }}
            </p>
          </div>
          <LSwitch
            :model-value="spacebarAdvance"
            :aria-label="$t('userSettings.preferences.shortcuts.spacebarAdvance.label')"
            @update:model-value="onToggleSpacebarAdvance"
          />
        </div>
      </div>
    </section>

    <!-- Weitere Präferenzen folgen hier (dieser Tab ist als Sammelfläche
         gedacht und wird künftig erweitert). -->
  </div>
</template>

<script setup>
/**
 * PreferencesTab — Sammelfläche für persönliche UI-Präferenzen.
 *
 * Aktuell: "Leertaste = Weiter" in Evaluationen (Standard AUS, opt-in). Die
 * Präferenz wird pro User im Backend gespeichert (siehe useUserPreferences).
 * Das Umschalten meldet den Speicherstatus an die Settings-Seite ('saving' →
 * 'saved'), die ihn im Sidebar-Footer anzeigt.
 */
import LIcon from '@/components/common/LIcon.vue'
import LSwitch from '@/components/common/LSwitch.vue'
import { useUserPreferences } from '@/composables/useUserPreferences'

const emit = defineEmits(['save-status'])

const { spacebarAdvance, setSpacebarAdvance } = useUserPreferences()

async function onToggleSpacebarAdvance(value) {
  emit('save-status', 'saving')
  try {
    await setSpacebarAdvance(value)
    emit('save-status', 'saved')
  } catch {
    // Persistenz fehlgeschlagen — der optimistische lokale Wert bleibt aktiv;
    // Status zurücksetzen, damit kein falsches "gespeichert" angezeigt wird.
    emit('save-status', null)
  }
}
</script>

<style scoped>
.preferences-tab {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 760px;
}

.settings-panel {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.panel-icon {
  color: #b0ca97;
  opacity: 0.9;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.panel-content {
  padding: 18px;
}

.section-description {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.65);
  margin: 0 0 16px;
}

.preference-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
}

.preference-text {
  min-width: 0;
}

.preference-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.preference-hint {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 4px 0 0;
  max-width: 560px;
}

.kbd {
  display: inline-block;
  padding: 1px 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  line-height: 18px;
  color: rgb(var(--v-theme-on-surface));
  background: rgba(var(--v-theme-on-surface), 0.06);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.18);
  border-bottom-width: 2px;
  border-radius: 6px 2px 6px 2px;
}
</style>
