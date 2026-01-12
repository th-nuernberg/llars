<template>
  <div class="language-toggle-wrapper">
    <v-menu
      v-model="menuOpen"
      :close-on-content-click="true"
      location="bottom end"
      offset="8"
    >
      <template v-slot:activator="{ props }">
        <button
          v-bind="props"
          class="language-toggle-btn"
          :class="{ 'on-primary': onPrimary }"
          :title="$t('language.select')"
        >
          <span class="language-code">{{ currentLanguageOption?.short || 'DE' }}</span>
        </button>
      </template>

      <div class="language-menu">
        <div class="language-menu-header">{{ $t('settings.language') }}</div>
        <button
          v-for="option in languageOptions"
          :key="option.value"
          class="language-option"
          :class="{ active: currentLanguage === option.value }"
          @click="selectLanguage(option.value)"
        >
          <span class="option-label">{{ option.title }}</span>
          <span class="option-code">{{ option.short }}</span>
          <LIcon
            v-if="currentLanguage === option.value"
            size="16"
            class="check-icon"
          >
            mdi-check
          </LIcon>
        </button>
      </div>
    </v-menu>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useLanguage } from '@/composables/useLanguage'

defineProps({
  onPrimary: {
    type: Boolean,
    default: false
  }
})

const {
  currentLanguage,
  languageOptions,
  currentLanguageOption,
  setLanguage
} = useLanguage()

const menuOpen = ref(false)

const selectLanguage = (value) => {
  setLanguage(value)
  menuOpen.value = false
}
</script>

<style scoped>
.language-toggle-wrapper {
  display: flex;
  align-items: center;
}

.language-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 36px;
  padding: 0 8px;
  border: none;
  border-radius: 8px 2px 8px 2px;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 600;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
}

.language-toggle-btn:hover {
  background: rgba(0, 0, 0, 0.12);
}

.language-toggle-btn.on-primary {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.language-toggle-btn.on-primary:hover {
  background: rgba(255, 255, 255, 0.25);
}

.language-code {
  text-transform: uppercase;
}

.language-menu {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  padding: 8px;
  min-width: 160px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.language-menu-header {
  padding: 8px 12px 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.language-option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 8px 2px 8px 2px;
  background: transparent;
  color: rgb(var(--v-theme-on-surface));
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}

.language-option:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
}

.language-option.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.option-label {
  flex: 1;
  font-size: 0.9rem;
}

.option-code {
  font-size: 0.75rem;
  font-weight: 600;
  opacity: 0.6;
}

.language-option.active .option-code {
  opacity: 1;
  color: rgb(var(--v-theme-primary));
}

.check-icon {
  color: rgb(var(--v-theme-primary));
}
</style>
