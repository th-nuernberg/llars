<template>
  <v-app>
    <!-- Navigation Drawer (Sidebar) -->
    <v-navigation-drawer
      v-model="drawer"
      :rail="rail"
      permanent
      class="admin-drawer"
    >
      <v-list-item
        prepend-icon="mdi-shield-crown"
        :title="rail ? '' : 'Admin'"
        :subtitle="rail ? '' : 'Dashboard'"
        class="drawer-header"
      >
        <template v-slot:append>
          <v-btn
            variant="text"
            :icon="rail ? 'mdi-chevron-right' : 'mdi-chevron-left'"
            @click.stop="rail = !rail"
          ></v-btn>
        </template>
      </v-list-item>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          v-for="item in navItems"
          :key="item.value"
          :prepend-icon="item.icon"
          :title="item.title"
          :value="item.value"
          :active="activeSection === item.value"
          @click="activeSection = item.value"
          rounded="xl"
          class="nav-item"
        ></v-list-item>
      </v-list>

      <template v-slot:append>
        <v-divider></v-divider>
        <v-list-item
          prepend-icon="mdi-home"
          title="Zurück zur Home"
          @click="$router.push('/Home')"
          class="nav-item"
        ></v-list-item>
      </template>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main class="admin-main">
      <v-container fluid class="pa-6">
        <!-- Header -->
        <v-row class="mb-4">
          <v-col cols="12">
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
          </v-col>
        </v-row>

        <!-- Dynamic Content based on active section -->
        <v-fade-transition mode="out-in">
          <!-- Overview Section -->
          <div v-if="activeSection === 'overview'" key="overview">
            <AdminOverview />
          </div>

          <!-- Users Section -->
          <div v-else-if="activeSection === 'users'" key="users">
            <AdminUsersSection />
          </div>

          <!-- Scenarios Section -->
          <div v-else-if="activeSection === 'scenarios'" key="scenarios">
            <AdminScenariosSection />
          </div>

          <!-- RAG Section -->
          <div v-else-if="activeSection === 'rag'" key="rag">
            <AdminRAGSection />
          </div>

          <!-- Permissions Section -->
          <div v-else-if="activeSection === 'permissions'" key="permissions">
            <AdminPermissionsSection />
          </div>
        </v-fade-transition>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAuth } from '@/composables/useAuth';

// Import section components
import AdminOverview from './sections/AdminOverview.vue';
import AdminUsersSection from './sections/AdminUsersSection.vue';
import AdminScenariosSection from './sections/AdminScenariosSection.vue';
import AdminRAGSection from './sections/AdminRAGSection.vue';
import AdminPermissionsSection from './sections/AdminPermissionsSection.vue';

const auth = useAuth();
const username = computed(() => auth.tokenParsed.value?.preferred_username || 'Admin');

// Drawer state
const drawer = ref(true);
const rail = ref(false);

// Active section
const activeSection = ref('overview');

// Navigation items
const navItems = [
  { title: 'Übersicht', value: 'overview', icon: 'mdi-view-dashboard' },
  { title: 'Benutzer', value: 'users', icon: 'mdi-account-group' },
  { title: 'Szenarien', value: 'scenarios', icon: 'mdi-clipboard-list' },
  { title: 'RAG Dokumente', value: 'rag', icon: 'mdi-database-search' },
  { title: 'Berechtigungen', value: 'permissions', icon: 'mdi-shield-lock' },
];

// Section titles and subtitles
const sectionInfo = {
  overview: { title: 'Dashboard Übersicht', subtitle: 'Schnellübersicht aller wichtigen Kennzahlen' },
  users: { title: 'Benutzerverwaltung', subtitle: 'Benutzer, Rollen und Fortschritt verwalten' },
  scenarios: { title: 'Szenario-Verwaltung', subtitle: 'Bewertungs-Szenarien erstellen und verwalten' },
  rag: { title: 'RAG Dokumente', subtitle: 'Dokumente für die RAG-Pipeline verwalten' },
  permissions: { title: 'Berechtigungen', subtitle: 'Rollen und Berechtigungen konfigurieren' },
};

const currentSectionTitle = computed(() => sectionInfo[activeSection.value]?.title || '');
const currentSectionSubtitle = computed(() => sectionInfo[activeSection.value]?.subtitle || '');
</script>

<style scoped>
.admin-drawer {
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgb(var(--v-theme-surface-variant)) 100%);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.drawer-header {
  min-height: 64px;
}

.nav-item {
  margin: 4px 8px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.nav-item.v-list-item--active {
  background-color: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.admin-main {
  background-color: rgb(var(--v-theme-background));
  min-height: 100vh;
}
</style>
