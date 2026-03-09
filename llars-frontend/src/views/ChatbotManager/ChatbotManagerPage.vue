<template>
  <div class="chatbot-manager-page" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
      temporary
      width="280"
      class="mobile-sidebar-drawer"
    >
      <div class="mobile-sidebar-header">
        <LIcon color="primary" size="24" class="mr-3">llars:chatbot-manage</LIcon>
        <div>
          <div class="text-subtitle-1 font-weight-bold">{{ $t('chatbotManagerPage.title') }}</div>
          <div class="text-caption text-medium-emphasis">{{ $t('chatbotManagerPage.subtitle') }}</div>
        </div>
      </div>
      <v-divider />
      <v-list nav density="compact" class="pa-2">
        <v-list-item
          v-for="item in navItems"
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
            :title="$t('chatbotManagerPage.homeLink')"
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
      :items="navItems"
      :title="$t('chatbotManagerPage.title')"
      :subtitle="$t('chatbotManagerPage.subtitle')"
      icon="llars:chatbot-manage"
      storage-key="chatbot-manager"
      :show-home-link="true"
    />

    <!-- Main Content -->
    <main class="cm-main">
      <!-- Header (hidden when chatbot wizard is open) -->
      <div v-if="!isChatbotWizardOpen" class="cm-header" :class="isMobile ? 'pa-3 pb-2' : 'pa-4 pb-2'">
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
          <v-spacer />
        </div>
      </div>

      <!-- Dynamic Content -->
      <div class="cm-content" :class="isChatbotWizardOpen ? 'pa-0' : 'pa-4 pt-0'">
        <v-fade-transition mode="out-in">
          <!-- Chatbots Section -->
          <div v-if="activeSection === 'chatbots'" key="chatbots" class="section-container--full">
            <ChatbotManager ref="chatbotManagerRef" />
          </div>

          <!-- RAG Section -->
          <div v-else-if="activeSection === 'rag'" key="rag" class="section-container--full">
            <AdminRAGSection />
          </div>

          <!-- Web Crawler Section -->
          <div v-else-if="activeSection === 'crawler'" key="crawler" class="section-container">
            <WebCrawlerTool />
          </div>
        </v-fade-transition>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useMobile } from '@/composables/useMobile'

import ChatbotManager from '@/components/Admin/ChatbotAdmin/ChatbotManager.vue'
import AdminRAGSection from '@/components/Admin/sections/AdminRAGSection.vue'
import WebCrawlerTool from '@/components/Admin/CrawlerAdmin/WebCrawlerTool.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'

const { fetchPermissions } = usePermissions()
const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isMobile, isTablet } = useMobile()

const mobileSidebarOpen = ref(false)
const activeSection = ref(route.query.tab || 'chatbots')

// Close sidebar when section changes on mobile
watch(activeSection, () => {
  if (isMobile.value) {
    mobileSidebarOpen.value = false
  }
})

// ChatbotManager ref for wizard state
const chatbotManagerRef = ref(null)
const isChatbotWizardOpen = computed(() => {
  return activeSection.value === 'chatbots' && chatbotManagerRef.value?.wizardOpen
})

// Navigation items
const navItems = computed(() => [
  { title: t('chatbotManagerPage.nav.chatbots'), value: 'chatbots', icon: 'llars:chatbot-manage' },
  { title: t('chatbotManagerPage.nav.rag'), value: 'rag', icon: 'mdi-database-search' },
  { title: t('chatbotManagerPage.nav.crawler'), value: 'crawler', icon: 'mdi-spider-web' },
])

// Route query sync
watch(activeSection, (newVal) => {
  if (route.query.tab !== newVal) {
    router.replace({ query: { ...route.query, tab: newVal } })
  }
})

watch(() => route.query.tab, (newTab) => {
  if (newTab && navItems.value.some(item => item.value === newTab) && activeSection.value !== newTab) {
    activeSection.value = newTab
  }
})

onMounted(async () => {
  await fetchPermissions()
})
</script>

<style scoped>
.chatbot-manager-page {
  height: calc(100vh - 94px);
  display: flex;
  overflow: hidden;
}

.cm-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
  min-width: 0;
}

.cm-header {
  flex-shrink: 0;
}

.cm-content {
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

.section-container--full {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Mobile */
.mobile-sidebar-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-sidebar-header {
  display: flex;
  align-items: center;
  padding: 16px;
}

.chatbot-manager-page.is-mobile {
  height: 100vh;
  height: 100dvh;
}

.chatbot-manager-page.is-mobile .cm-main {
  width: 100%;
}

.chatbot-manager-page.is-mobile .cm-content {
  padding: 12px !important;
  padding-top: 0 !important;
}

.chatbot-manager-page.is-mobile .section-container {
  -webkit-overflow-scrolling: touch;
}

/* Tablet */
.chatbot-manager-page.is-tablet .cm-main {
  flex: 1;
}

.min-width-0 {
  min-width: 0;
}

@media (max-width: 600px) {
  .chatbot-manager-page .v-list-item {
    min-height: 48px;
  }
}
</style>
