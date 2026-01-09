<template>
  <div class="theme-toggle-wrapper">
    <v-menu
      v-model="menuOpen"
      :close-on-content-click="true"
      location="bottom end"
      offset="8"
    >
      <template v-slot:activator="{ props }">
        <button
          v-bind="props"
          class="theme-toggle-btn"
          :class="{ 'on-primary': onPrimary }"
          :title="currentThemeOption?.title || 'Theme'"
        >
          <LIcon size="20">{{ currentIcon }}</LIcon>
        </button>
      </template>

      <div class="theme-menu">
        <div class="theme-menu-header">Design</div>
        <button
          v-for="option in themeOptions"
          :key="option.value"
          class="theme-option"
          :class="{ active: themePreference === option.value }"
          @click="setTheme(option.value)"
        >
          <LIcon size="18" class="option-icon">{{ option.icon }}</LIcon>
          <span class="option-label">{{ option.title }}</span>
          <LIcon
            v-if="themePreference === option.value"
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
import { ref, computed } from 'vue'
import { useAppTheme } from '@/composables/useAppTheme'

const props = defineProps({
  onPrimary: {
    type: Boolean,
    default: false
  }
})

const {
  themePreference,
  themeOptions,
  currentThemeOption,
  setThemePreference,
  isDark
} = useAppTheme()

const menuOpen = ref(false)

const currentIcon = computed(() => {
  // Show the current theme option icon
  return currentThemeOption.value?.icon || 'llars:system-theme'
})

const setTheme = (value) => {
  setThemePreference(value)
  menuOpen.value = false
}
</script>

<style scoped>
.theme-toggle-wrapper {
  display: flex;
  align-items: center;
}

.theme-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px 2px 8px 2px;
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-toggle-btn:hover {
  background: rgba(0, 0, 0, 0.12);
}

.theme-toggle-btn.on-primary {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.theme-toggle-btn.on-primary:hover {
  background: rgba(255, 255, 255, 0.25);
}

.theme-menu {
  background: rgb(var(--v-theme-surface));
  border-radius: 12px 4px 12px 4px;
  padding: 8px;
  min-width: 160px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.theme-menu-header {
  padding: 8px 12px 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.theme-option {
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

.theme-option:hover {
  background: rgba(var(--v-theme-on-surface), 0.08);
}

.theme-option.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.option-icon {
  opacity: 0.7;
}

.theme-option.active .option-icon {
  opacity: 1;
  color: rgb(var(--v-theme-primary));
}

.option-label {
  flex: 1;
  font-size: 0.9rem;
}

.check-icon {
  color: rgb(var(--v-theme-primary));
}
</style>
