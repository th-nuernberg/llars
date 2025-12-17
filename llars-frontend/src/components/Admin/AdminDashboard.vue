<template>
  <div class="admin-page">
    <!-- Sidebar -->
    <AppSidebar
      v-model="activeSection"
      :items="navItems"
      title="Admin"
      subtitle="Dashboard"
      icon="mdi-shield-crown"
      storage-key="admin"
      :show-home-link="true"
    />

    <!-- Main Content -->
    <main class="admin-main">
      <!-- Header (hidden when chatbot wizard is open) -->
      <div v-if="!isChatbotWizardOpen" class="admin-header pa-4 pb-2">
        <div class="d-flex align-center">
          <div>
            <h1 class="text-h4 font-weight-bold">{{ currentSectionTitle }}</h1>
            <p class="text-subtitle-1 text-medium-emphasis">{{ currentSectionSubtitle }}</p>
          </div>
          <v-spacer></v-spacer>
          <v-chip color="primary" variant="flat" class="mr-2">
            <v-icon start>mdi-account</v-icon>
            {{ username }}
          </v-chip>
        </div>
      </div>

      <!-- Dynamic Content based on active section -->
      <div class="admin-content" :class="isChatbotWizardOpen ? 'pa-0' : 'pa-4 pt-0'">
        <v-fade-transition mode="out-in">
          <!-- Overview Section -->
          <div v-if="activeSection === 'overview'" key="overview" class="section-container">
            <AdminOverview />
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
        </v-fade-transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuth } from '@/composables/useAuth';

// Import section components
import AdminOverview from './sections/AdminOverview.vue';
import AdminUsersSection from './sections/AdminUsersSection.vue';
import AdminScenariosSection from './sections/AdminScenariosSection.vue';
import AdminRAGSection from './sections/AdminRAGSection.vue';
import AdminPermissionsSection from './sections/AdminPermissionsSection.vue';
import ChatbotManager from './ChatbotAdmin/ChatbotManager.vue';
import WebCrawlerTool from './CrawlerAdmin/WebCrawlerTool.vue';
import AppSidebar from '@/components/common/AppSidebar.vue';

const auth = useAuth();
const route = useRoute();
const router = useRouter();
const username = computed(() => auth.tokenParsed.value?.preferred_username || 'Admin');

// Active section (synced with route query)
const activeSection = ref('overview');

// ChatbotManager ref for wizard state
const chatbotManagerRef = ref(null);
const isChatbotWizardOpen = computed(() => {
  return activeSection.value === 'chatbots' && chatbotManagerRef.value?.wizardOpen;
});

// Navigation items
const navItems = [
  { title: 'Übersicht', value: 'overview', icon: 'mdi-view-dashboard' },
  { title: 'Benutzer', value: 'users', icon: 'mdi-account-group' },
  { title: 'Szenarien', value: 'scenarios', icon: 'mdi-clipboard-list' },
  { title: 'Chatbots', value: 'chatbots', icon: 'mdi-robot' },
  { title: 'Web Crawler', value: 'crawler', icon: 'mdi-spider-web' },
  { title: 'RAG Dokumente', value: 'rag', icon: 'mdi-database-search' },
  { title: 'Berechtigungen', value: 'permissions', icon: 'mdi-shield-lock' },
];

// Section titles and subtitles
const sectionInfo = {
  overview: { title: 'Dashboard Übersicht', subtitle: 'Schnellübersicht aller wichtigen Kennzahlen' },
  users: { title: 'Benutzerverwaltung', subtitle: 'Benutzer, Rollen und Fortschritt verwalten' },
  scenarios: { title: 'Szenario-Verwaltung', subtitle: 'Bewertungs-Szenarien erstellen und verwalten' },
  chatbots: { title: 'Chatbot-Verwaltung', subtitle: 'Chatbots mit RAG-Collections erstellen und konfigurieren' },
  crawler: { title: 'Website Crawler', subtitle: 'Websites crawlen und RAG-Collections erstellen' },
  rag: { title: 'RAG Dokumente', subtitle: 'Dokumente für die RAG-Pipeline verwalten' },
  permissions: { title: 'Berechtigungen', subtitle: 'Rollen und Berechtigungen konfigurieren' },
};

const currentSectionTitle = computed(() => sectionInfo[activeSection.value]?.title || '');
const currentSectionSubtitle = computed(() => sectionInfo[activeSection.value]?.subtitle || '');

// Route query sync for tab navigation (e.g., /admin?tab=rag)
function initFromRoute() {
  const tab = route.query.tab;
  if (tab && navItems.some(item => item.value === tab)) {
    activeSection.value = tab;
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
  if (newTab && navItems.some(item => item.value === newTab) && activeSection.value !== newTab) {
    activeSection.value = newTab;
  }
});

onMounted(() => {
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
</style>
