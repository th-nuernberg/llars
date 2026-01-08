<template>
  <aside
    class="app-sidebar"
    :class="{ collapsed: isCollapsed }"
  >
    <!-- Header -->
    <div class="sidebar-header">
      <div class="header-content" :class="{ 'justify-center': isCollapsed }">
        <template v-if="!isCollapsed">
          <LIcon v-if="icon" class="header-icon" size="24">{{ icon }}</LIcon>
          <div class="header-text">
            <span class="header-title">{{ title }}</span>
            <span v-if="subtitle" class="header-subtitle">{{ subtitle }}</span>
          </div>
        </template>
        <LIcon v-else class="header-icon-collapsed" size="24">{{ icon }}</LIcon>
      </div>
      <button
        class="collapse-btn"
        @click="toggleCollapse"
        :title="isCollapsed ? 'Erweitern' : 'Zuklappen'"
      >
        <LIcon size="20">{{ isCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</LIcon>
      </button>
    </div>

    <div class="sidebar-divider"></div>

    <!-- Navigation Items -->
    <nav class="sidebar-nav">
      <button
        v-for="item in items"
        :key="item.value"
        class="nav-item"
        :class="{ active: modelValue === item.value }"
        @click="selectItem(item)"
        :title="isCollapsed ? item.title : undefined"
      >
        <div class="nav-icon">
          <LIcon size="20">{{ item.icon }}</LIcon>
        </div>
        <span v-if="!isCollapsed" class="nav-label">{{ item.title }}</span>
        <v-chip
          v-if="!isCollapsed && item.badge"
          size="x-small"
          :color="item.badgeColor || 'primary'"
          variant="flat"
          class="nav-badge"
        >
          {{ item.badge }}
        </v-chip>
      </button>
    </nav>

    <!-- Footer Slot -->
    <div class="sidebar-footer">
      <div class="sidebar-divider"></div>
      <slot name="footer">
        <button
          v-if="showHomeLink"
          class="nav-item"
          @click="$router.push('/Home')"
          :title="isCollapsed ? 'Zur Startseite' : undefined"
        >
          <div class="nav-icon">
            <LIcon size="20">mdi-home</LIcon>
          </div>
          <span v-if="!isCollapsed" class="nav-label">Zur Startseite</span>
        </button>
      </slot>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  items: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: 'mdi-menu'
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  showHomeLink: {
    type: Boolean,
    default: true
  },
  storageKey: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['update:modelValue', 'update:collapsed', 'item-click']);

// Internal collapse state
const isCollapsed = ref(props.collapsed);

// Load from localStorage if storageKey provided
if (props.storageKey) {
  const stored = localStorage.getItem(`sidebar_${props.storageKey}`);
  if (stored !== null) {
    isCollapsed.value = stored === 'true';
  }
}

// Sync with prop
watch(() => props.collapsed, (val) => {
  isCollapsed.value = val;
});

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value;
  emit('update:collapsed', isCollapsed.value);

  // Persist to localStorage
  if (props.storageKey) {
    localStorage.setItem(`sidebar_${props.storageKey}`, String(isCollapsed.value));
  }
}

function selectItem(item) {
  emit('update:modelValue', item.value);
  emit('item-click', item);
}
</script>

<style scoped>
.app-sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface-variant), 0.5) 100%);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
}

.app-sidebar.collapsed {
  width: 64px;
  min-width: 64px;
  position: relative;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  padding: 12px;
  min-height: 64px;
  gap: 8px;
  position: relative;
}

.header-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  transition: justify-content 0.25s ease;
}

.header-content.justify-center {
  justify-content: center;
}

.header-icon {
  color: rgb(var(--v-theme-primary));
  flex-shrink: 0;
}

.header-icon-collapsed {
  color: rgb(var(--v-theme-primary));
}

.header-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.header-title {
  font-weight: 600;
  font-size: 15px;
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.collapse-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.collapsed .sidebar-header {
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 12px 8px;
  gap: 8px;
}

.collapsed .collapse-btn {
  position: static;
  margin-top: 4px;
}

/* Divider */
.sidebar-divider {
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  margin: 0 12px;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.8);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font-size: 14px;
  margin-bottom: 4px;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.nav-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  color: rgb(var(--v-theme-on-surface));
}

.nav-item.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.nav-item.active .nav-icon {
  color: rgb(var(--v-theme-primary));
}

.nav-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: color 0.2s ease;
}

.nav-item:hover .nav-icon {
  color: rgb(var(--v-theme-primary));
}

.nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed .nav-label {
  display: none;
}

.nav-badge {
  flex-shrink: 0;
}

.collapsed .nav-badge {
  display: none;
}

/* Footer */
.sidebar-footer {
  margin-top: auto;
  padding-bottom: 8px;
}

.sidebar-footer .sidebar-divider {
  margin-bottom: 8px;
}

.sidebar-footer .nav-item {
  margin: 0 8px 0;
  width: calc(100% - 16px);
}

.collapsed .sidebar-footer .nav-item {
  width: calc(100% - 16px);
}
</style>
