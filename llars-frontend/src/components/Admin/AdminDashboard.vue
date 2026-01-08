<template>
  <div class="admin-page" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
      temporary
      width="280"
      class="mobile-sidebar-drawer"
    >
      <div class="mobile-sidebar-header">
        <LIcon color="primary" size="24" class="mr-3">llars:admin-dashboard</LIcon>
        <div>
          <div class="text-subtitle-1 font-weight-bold">Admin</div>
          <div class="text-caption text-medium-emphasis">Dashboard</div>
        </div>
      </div>
      <v-divider />
      <v-list nav density="compact" class="pa-2">
        <v-list-item
          v-for="item in filteredNavItems"
          :key="item.value"
          :value="item.value"
          :active="activeSection === item.value"
          :prepend-icon="item.icon"
          :title="item.title"
          rounded="lg"
          @click="activeSection = item.value"
        />
      </v-list>
      <template #append>
        <v-divider />
        <v-list nav density="compact" class="pa-2">
          <v-list-item
            prepend-icon="mdi-home"
            title="Zur Startseite"
            rounded="lg"
            @click="$router.push('/Home')"
          />
        </v-list>
      </template>
    </v-navigation-drawer>

    <!-- Desktop Sidebar -->
    <AppSidebar
      v-if="!isMobile"
      v-model="activeSection"
      :items="filteredNavItems"
      title="Admin"
      subtitle="Dashboard"
      icon="llars:admin-dashboard"
      storage-key="admin"
      :show-home-link="true"
    />

    <!-- Main Content -->
    <main class="admin-main">
      <!-- Header (hidden when chatbot wizard is open) -->
      <div v-if="!isChatbotWizardOpen" class="admin-header" :class="isMobile ? 'pa-3 pb-2' : 'pa-4 pb-2'">
        <div class="d-flex align-center">
          <!-- Mobile menu button -->
          <v-btn
            v-if="isMobile"
            icon
            variant="text"
            size="small"
            class="mr-2"
            @click="mobileSidebarOpen = true"
          >
            <LIcon>mdi-menu</LIcon>
          </v-btn>
          <div v-if="currentSectionTitle" class="flex-grow-1 min-width-0">
            <h1 :class="isMobile ? 'text-h6 font-weight-bold text-truncate' : 'text-h4 font-weight-bold'">
              {{ currentSectionTitle }}
            </h1>
          </div>
          <v-spacer />
        </div>
      </div>

      <!-- Dynamic Content based on active section -->
      <div class="admin-content" :class="isChatbotWizardOpen ? 'pa-0' : 'pa-4 pt-0'">
        <v-fade-transition mode="out-in">
          <!-- Overview Section -->
          <div v-if="activeSection === 'overview'" key="overview" class="section-container">
            <AdminOverview />
          </div>

          <!-- Analytics Section -->
          <div v-else-if="activeSection === 'analytics'" key="analytics" class="section-container">
            <AdminAnalyticsSection />
          </div>

          <!-- Users Section -->
          <div v-else-if="activeSection === 'users'" key="users" class="section-container">
            <AdminUsersSection />
          </div>

          <!-- Scenarios Section -->
          <div v-else-if="activeSection === 'scenarios'" key="scenarios" class="section-container">
            <AdminScenariosSection />
          </div>

          <!-- Chatbots Section -->
          <div v-else-if="activeSection === 'chatbots'" key="chatbots" class="section-container section-container--full">
            <ChatbotManager ref="chatbotManagerRef" />
          </div>

          <!-- Web Crawler Section -->
          <div v-else-if="activeSection === 'crawler'" key="crawler" class="section-container">
            <WebCrawlerTool />
          </div>

          <!-- RAG Section -->
          <div v-else-if="activeSection === 'rag'" key="rag" class="section-container">
            <AdminRAGSection />
          </div>

          <!-- Permissions Section -->
          <div v-else-if="activeSection === 'permissions'" key="permissions" class="section-container">
            <AdminPermissionsSection />
          </div>

          <!-- LLM Providers Section -->
          <div v-else-if="activeSection === 'llm-providers'" key="llm-providers" class="section-container">
            <AdminLlmProvidersSection />
          </div>

          <!-- System Health Section -->
          <div v-else-if="activeSection === 'health'" key="health" class="section-container--full">
            <AdminSystemHealthSection />
          </div>

          <!-- System Events Section -->
          <div v-else-if="activeSection === 'system'" key="system" class="section-container--full">
            <AdminSystemMonitorSection />
          </div>

          <!-- Chatbot Activity Section -->
          <div v-else-if="activeSection === 'chatbot-activity'" key="chatbot-activity" class="section-container--full">
            <AdminChatbotActivitySection />
          </div>

          <!-- Docker Monitor Section -->
          <div v-else-if="activeSection === 'docker'" key="docker" class="section-container--full">
            <AdminDockerMonitorSection />
          </div>

          <!-- DB Explorer Section -->
          <div v-else-if="activeSection === 'db'" key="db" class="section-container--full">
            <AdminDatabaseSection />
          </div>

          <!-- System Settings Section -->
          <div v-else-if="activeSection === 'settings'" key="settings" class="section-container">
            <AdminSystemSettingsSection />
          </div>
        </v-fade-transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { usePermissions } from '@/composables/usePermissions';
import { useMobile } from '@/composables/useMobile';

// Import section components
import AdminOverview from './sections/AdminOverview.vue';
import AdminAnalyticsSection from './sections/AdminAnalyticsSection.vue';
import AdminUsersSection from './sections/AdminUsersSection.vue';
import AdminScenariosSection from './sections/AdminScenariosSection.vue';
import AdminRAGSection from './sections/AdminRAGSection.vue';
import AdminPermissionsSection from './sections/AdminPermissionsSection.vue';
import AdminLlmProvidersSection from './sections/AdminLlmProvidersSection.vue';
import AdminSystemMonitorSection from './sections/AdminSystemMonitorSection.vue';
import AdminSystemHealthSection from './sections/AdminSystemHealthSection.vue';
import AdminChatbotActivitySection from './sections/AdminChatbotActivitySection.vue';
import AdminDockerMonitorSection from './sections/AdminDockerMonitorSection.vue';
import AdminDatabaseSection from './sections/AdminDatabaseSection.vue';
import AdminSystemSettingsSection from './sections/AdminSystemSettingsSection.vue';
import ChatbotManager from './ChatbotAdmin/ChatbotManager.vue';
import WebCrawlerTool from './CrawlerAdmin/WebCrawlerTool.vue';
import AppSidebar from '@/components/common/AppSidebar.vue';

const { hasPermission, hasAnyPermission, fetchPermissions, isAdmin } = usePermissions();
const route = useRoute();
const router = useRouter();
const { isMobile, isTablet, isSmallScreen } = useMobile();

// Mobile sidebar state
const mobileSidebarOpen = ref(false);

// Active section (synced with route query)
const activeSection = ref('overview');

// Close sidebar when section changes on mobile
watch(activeSection, () => {
  if (isMobile.value) {
    mobileSidebarOpen.value = false;
  }
});

// ChatbotManager ref for wizard state
const chatbotManagerRef = ref(null);
const isChatbotWizardOpen = computed(() => {
  return activeSection.value === 'chatbots' && chatbotManagerRef.value?.wizardOpen;
});

// Navigation items
const navItems = [
  { title: 'Übersicht', value: 'overview', icon: 'mdi-view-dashboard', adminOnly: true },
  { title: 'Analytics', value: 'analytics', icon: 'mdi-chart-bar', adminOnly: true },
  { title: 'System Health', value: 'health', icon: 'mdi-heart-pulse', adminOnly: true },
  { title: 'System Events', value: 'system', icon: 'mdi-monitor-dashboard', adminOnly: true },
  { title: 'Chatbot Activity', value: 'chatbot-activity', icon: 'mdi-robot-outline', adminOnly: true },
  { title: 'Docker', value: 'docker', icon: 'mdi-docker', adminOnly: true },
  { title: 'DB', value: 'db', icon: 'mdi-database', adminOnly: true },
  { title: 'Einstellungen', value: 'settings', icon: 'mdi-cog', adminOnly: true },
  { title: 'Benutzer', value: 'users', icon: 'mdi-account-group', adminOnly: true },
  { title: 'Szenarien', value: 'scenarios', icon: 'mdi-clipboard-list', adminOnly: true },
  { title: 'Chatbots', value: 'chatbots', icon: 'llars:chatbot-manage', permission: 'feature:chatbots:view' },
  { title: 'Web Crawler', value: 'crawler', icon: 'mdi-spider-web', adminOnly: true },
  { title: 'RAG Dokumente', value: 'rag', icon: 'mdi-database-search', permission: 'feature:rag:view' },
  { title: 'Berechtigungen', value: 'permissions', icon: 'mdi-shield-lock', adminOnly: true },
  { title: 'LLM Provider', value: 'llm-providers', icon: 'mdi-connection', adminOnly: true },
];

const filteredNavItems = computed(() => {
  return navItems.filter(item => {
    if (item.adminOnly) return isAdmin.value;
    if (item.permissionsAny) return hasAnyPermission(...item.permissionsAny);
    if (item.permission) return hasPermission(item.permission);
    return true;
  });
});

const currentSectionTitle = computed(() => '');

// Route query sync for tab navigation (e.g., /admin?tab=rag)
function initFromRoute() {
  const tab = route.query.tab;
  if (tab && filteredNavItems.value.some(item => item.value === tab)) {
    activeSection.value = tab;
    return;
  }
  if (filteredNavItems.value.length > 0) {
    activeSection.value = filteredNavItems.value[0].value;
  }
}

// Update URL when section changes
watch(activeSection, (newVal) => {
  if (route.query.tab !== newVal) {
    router.replace({ query: { ...route.query, tab: newVal } });
  }
});

// Watch for route changes (e.g., from Home page tiles)
watch(() => route.query.tab, (newTab) => {
  if (newTab && filteredNavItems.value.some(item => item.value === newTab) && activeSection.value !== newTab) {
    activeSection.value = newTab;
  }
});

watch(filteredNavItems, (items) => {
  if (!items.length) return;
  // Prioritize route query tab if it's valid
  const routeTab = route.query.tab;
  if (routeTab && items.some(item => item.value === routeTab)) {
    if (activeSection.value !== routeTab) {
      activeSection.value = routeTab;
    }
    return;
  }
  // Fallback to first item if current section is not in filtered list
  if (!items.some(item => item.value === activeSection.value)) {
    activeSection.value = items[0].value;
  }
});

onMounted(async () => {
  await fetchPermissions();
  initFromRoute();
});
</script>

<style scoped>
/* Admin page fills viewport minus AppBar (64px) and Footer (30px) */
.admin-page {
  height: calc(100vh - 94px);
  display: flex;
  overflow: hidden;
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
  min-width: 0;
}

.admin-header {
  flex-shrink: 0;
}

.admin-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

/* Full-height sections that manage their own scrolling */
.section-container--full {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ========================================
   MOBILE RESPONSIVE STYLES
   ======================================== */

/* Mobile sidebar drawer */
.mobile-sidebar-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-sidebar-header {
  display: flex;
  align-items: center;
  padding: 16px;
}

/* Mobile page layout */
.admin-page.is-mobile {
  height: 100vh;
  height: 100dvh;
}

.admin-page.is-mobile .admin-main {
  width: 100%;
}

.admin-page.is-mobile .admin-content {
  padding: 12px !important;
  padding-top: 0 !important;
}

.admin-page.is-mobile .section-container {
  -webkit-overflow-scrolling: touch;
}

/* Tablet styles */
.admin-page.is-tablet .admin-main {
  flex: 1;
}

/* Min-width helper for text truncation */
.min-width-0 {
  min-width: 0;
}

/* Touch-friendly list items */
@media (max-width: 600px) {
  .admin-page .v-list-item {
    min-height: 48px;
  }
}
</style>
