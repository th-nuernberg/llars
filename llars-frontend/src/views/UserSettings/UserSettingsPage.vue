<template>
  <div class="settings-workspace" role="main" aria-label="Benutzereinstellungen">
    <!-- Sidebar Navigation -->
    <aside class="settings-sidebar" :class="{ collapsed: sidebarCollapsed }" role="navigation" aria-label="Einstellungs-Navigation">
      <template v-if="!sidebarCollapsed">
        <!-- Sidebar Header -->
        <div class="sidebar-header">
          <div class="header-info">
            <LAvatar
              :src="avatarUrl"
              :seed="avatarSeed"
              :username="username"
              size="lg"
              class="user-avatar"
            />
            <div class="header-text">
              <span class="header-title">{{ username }}</span>
              <span class="header-subtitle">{{ $t('userSettings.subtitle') }}</span>
            </div>
          </div>
          <button
            class="collapse-btn"
            @click="sidebarCollapsed = true"
            :aria-label="$t('common.collapse')"
          >
            <LIcon size="18">mdi-chevron-left</LIcon>
          </button>
        </div>

        <!-- Navigation Items -->
        <nav class="sidebar-nav" role="tablist" aria-label="Einstellungs-Kategorien">
          <button
            v-for="tab in availableTabs"
            :key="tab.value"
            class="nav-item"
            :class="{ active: activeTab === tab.value }"
            role="tab"
            :aria-selected="activeTab === tab.value"
            :aria-controls="`panel-${tab.value}`"
            @click="activeTab = tab.value"
          >
            <LIcon size="20" class="nav-icon">{{ tab.icon }}</LIcon>
            <span class="nav-label">{{ tab.label }}</span>
            <LIcon v-if="activeTab === tab.value" size="16" class="nav-check">mdi-check</LIcon>
          </button>
        </nav>

        <!-- Auto-save Status -->
        <div class="sidebar-footer">
          <Transition name="fade">
            <div v-if="autoSaveStatus" class="save-status" :class="autoSaveStatus">
              <LIcon size="14">{{ autoSaveStatus === 'saving' ? 'mdi-loading mdi-spin' : 'mdi-check-circle' }}</LIcon>
              <span>{{ autoSaveStatus === 'saving' ? $t('common.saving') : $t('common.saved') }}</span>
            </div>
          </Transition>
        </div>
      </template>

      <!-- Collapsed State -->
      <template v-else>
        <div class="collapsed-bar">
          <button
            class="expand-btn"
            @click="sidebarCollapsed = false"
            :aria-label="$t('common.expand')"
          >
            <LIcon size="20" color="white">mdi-chevron-right</LIcon>
          </button>
          <div class="collapsed-icons">
            <button
              v-for="tab in availableTabs"
              :key="tab.value"
              class="collapsed-icon-box"
              :class="{ active: activeTab === tab.value }"
              :aria-label="tab.label"
              @click="activeTab = tab.value"
            >
              <LIcon size="18" :color="activeTab === tab.value ? 'white' : 'rgba(255,255,255,0.7)'">{{ tab.icon }}</LIcon>
            </button>
          </div>
          <span class="collapsed-label">{{ $t('userSettings.title') }}</span>
        </div>
      </template>
    </aside>

    <!-- Resize Divider -->
    <div
      class="resize-divider vertical"
      :class="{ resizing: isResizing }"
      @mousedown="startResize"
      role="separator"
      aria-orientation="vertical"
    >
      <div class="resize-handle"></div>
    </div>

    <!-- Main Content -->
    <main class="settings-main" role="tabpanel" :id="`panel-${activeTab}`">
      <!-- Content Header -->
      <header class="content-header">
        <div class="header-left">
          <LIcon size="22" class="header-icon">{{ currentTab?.icon }}</LIcon>
          <div class="header-titles">
            <h1 class="page-title">{{ currentTab?.label }}</h1>
            <p class="page-subtitle">{{ getTabDescription(activeTab) }}</p>
          </div>
        </div>
      </header>

      <!-- Tab Content -->
      <div class="content-body">
        <Transition name="slide-fade" mode="out-in">
          <PersonalSettingsTab
            v-if="activeTab === 'personal'"
            key="personal"
            @save-status="handleSaveStatus"
          />
          <LLMProvidersTab
            v-else-if="activeTab === 'providers'"
            key="providers"
          />
          <ReferralLinksTab
            v-else-if="activeTab === 'referrals'"
            key="referrals"
          />
        </Transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import LIcon from '@/components/common/LIcon.vue'
import LAvatar from '@/components/common/LAvatar.vue'
import PersonalSettingsTab from './components/PersonalSettingsTab.vue'
import LLMProvidersTab from './components/LLMProvidersTab.vue'
import ReferralLinksTab from './components/ReferralLinksTab.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

const { t } = useI18n()
const { tokenParsed, avatarUrl, avatarSeed } = useAuth()

const activeTab = ref('personal')
const sidebarCollapsed = ref(false)
const canCreateReferrals = ref(false)
const autoSaveStatus = ref(null)

// Resize state
const isResizing = ref(false)
const sidebarWidth = ref(280)

const username = computed(() => tokenParsed.value?.preferred_username || '')

const availableTabs = computed(() => {
  const tabs = [
    { value: 'personal', label: t('userSettings.tabs.personal'), icon: 'mdi-account-cog' },
    { value: 'providers', label: t('userSettings.tabs.providers'), icon: 'mdi-api' }
  ]

  if (canCreateReferrals.value) {
    tabs.push({
      value: 'referrals',
      label: t('userSettings.tabs.referrals'),
      icon: 'mdi-share-variant'
    })
  }

  return tabs
})

const currentTab = computed(() => availableTabs.value.find(t => t.value === activeTab.value))

function getTabDescription(tab) {
  const descriptions = {
    personal: t('userSettings.personal.description', 'Passen Sie Ihr Profil und Ihre Präferenzen an'),
    providers: t('userSettings.providers.description', 'Verwalten Sie Ihre LLM-API-Keys'),
    referrals: t('userSettings.referrals.description', 'Erstellen und verwalten Sie Einladungslinks')
  }
  return descriptions[tab] || ''
}

function handleSaveStatus(status) {
  autoSaveStatus.value = status
  if (status === 'saved') {
    setTimeout(() => { autoSaveStatus.value = null }, 2000)
  }
}

// Resize functionality
function startResize(e) {
  isResizing.value = true
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
  e.preventDefault()
}

function onResize(e) {
  if (!isResizing.value) return
  const newWidth = Math.min(Math.max(e.clientX, 200), 400)
  sidebarWidth.value = newWidth
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  localStorage.setItem('settings-sidebar-width', sidebarWidth.value.toString())
}

onMounted(async () => {
  // Load saved sidebar width
  const savedWidth = localStorage.getItem('settings-sidebar-width')
  if (savedWidth) sidebarWidth.value = parseInt(savedWidth)

  try {
    const response = await axios.get('/api/user/referrals/can-create')
    canCreateReferrals.value = response.data.can_create
  } catch {
    canCreateReferrals.value = false
  }
})

onUnmounted(() => {
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
})
</script>

<style scoped>
/* ============================================
   LLARS Settings Workspace - SOTA Design
   ============================================ */

.settings-workspace {
  --llars-primary: #b0ca97;
  --llars-accent: #88c4c8;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  height: calc(100vh - 94px);
  display: flex;
  background: rgb(var(--v-theme-background));
  overflow: hidden;
}

/* ============================================
   Sidebar
   ============================================ */

.settings-sidebar {
  width: v-bind('sidebarWidth + "px"');
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  overflow: hidden;
  transition: width 0.2s ease;
}

.settings-sidebar.collapsed {
  width: 56px !important;
}

/* Sidebar Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.user-avatar {
  flex-shrink: 0;
}

.header-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-subtitle {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 6px 2px 6px 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgb(var(--v-theme-on-surface));
}

/* Sidebar Navigation */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: none;
  border-radius: var(--llars-radius-sm);
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.7);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
  width: 100%;
}

.nav-item:hover {
  background: rgba(var(--v-theme-on-surface), 0.06);
  color: rgb(var(--v-theme-on-surface));
}

.nav-item:focus {
  outline: 2px solid var(--llars-primary);
  outline-offset: 2px;
}

.nav-item.active {
  background: rgba(176, 202, 151, 0.15);
  color: var(--llars-primary);
  font-weight: 500;
}

.nav-item.active .nav-icon {
  color: var(--llars-primary);
}

.nav-icon {
  flex-shrink: 0;
  opacity: 0.8;
}

.nav-label {
  flex: 1;
  font-size: 14px;
}

.nav-check {
  color: var(--llars-primary);
  flex-shrink: 0;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-height: 48px;
}

.save-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--llars-radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.save-status.saving {
  background: rgba(var(--v-theme-info), 0.1);
  color: rgb(var(--v-theme-info));
}

.save-status.saved {
  background: rgba(152, 212, 187, 0.15);
  color: #4caf50;
}

/* Collapsed State */
.collapsed-bar {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  gap: 16px;
  background: linear-gradient(180deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
}

.expand-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px 2px 6px 2px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.collapsed-icons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.collapsed-icon-box {
  width: 36px;
  height: 36px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 6px 2px 6px 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.collapsed-icon-box:hover {
  background: rgba(255, 255, 255, 0.25);
}

.collapsed-icon-box.active {
  background: rgba(255, 255, 255, 0.35);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

.collapsed-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  font-size: 12px;
  color: white;
  letter-spacing: 1px;
  margin-top: auto;
}

/* ============================================
   Resize Divider
   ============================================ */

.resize-divider {
  width: 6px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.04);
  cursor: col-resize;
  transition: background 0.15s ease;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(176, 202, 151, 0.2);
}

.resize-handle {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 2px;
  transition: all 0.15s ease;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: var(--llars-primary);
  height: 60px;
}

/* ============================================
   Main Content
   ============================================ */

.settings-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* Content Header */
.content-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  color: var(--llars-primary);
  opacity: 0.9;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
}

.page-subtitle {
  font-size: 12px;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Content Body */
.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: rgba(var(--v-theme-surface-variant), 0.15);
}

/* ============================================
   Transitions
   ============================================ */

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-fade-enter-active {
  transition: all 0.2s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.15s ease-in;
}

.slide-fade-enter-from {
  transform: translateX(10px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateX(-10px);
  opacity: 0;
}

/* ============================================
   Mobile Responsive
   ============================================ */

@media (max-width: 768px) {
  .settings-workspace {
    height: calc(100dvh - 88px);
  }

  .settings-sidebar:not(.collapsed) {
    position: absolute;
    z-index: 100;
    height: 100%;
    box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
  }

  .resize-divider {
    display: none;
  }

  .content-header {
    padding: 12px 16px;
  }

  .content-body {
    padding: 16px;
  }
}
</style>
