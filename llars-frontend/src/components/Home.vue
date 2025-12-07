<template>
  <v-container class="home-container">
    <!-- Logo und Titelbereich -->
    <v-row justify="center" class="header mb-5">
      <v-col cols="12" class="text-center">
        <img src="@/assets/logo/llars-logo.png" alt="LLars Logo" height="120" class="mb-2">
        <h1 class="header-title">Willkommen bei LLars</h1>
        <div class="subtitle-text mb-4">Ihre Plattform für Ranking, Labeling, Rating und Mail-Generierung!</div>
      </v-col>
    </v-row>
    <!-- Feature Cards -->
    <v-row class="equal-size-cards">
      <!-- Skeleton Loading -->
      <template v-if="isSkelLoading('permissions')">
        <v-col v-for="n in 6" :key="'skeleton-' + n" cols="12" sm="6" class="d-flex card-col">
          <v-skeleton-loader type="card" class="mb-4 w-100" height="200"></v-skeleton-loader>
        </v-col>
      </template>

      <!-- Actual Content -->
      <v-col
        v-else
        v-for="item in items"
        :key="item.title"
        cols="12" sm="6"
        class="d-flex card-col"
      >
        <v-card
          class="mb-4 feature-card d-flex flex-column"
          color="primary"
          dark
          @click="navigateTo(item.route)"
          :elevation="item.elevation"
          @mouseover="() => item.elevation = 5"
          @mouseleave="() => item.elevation = 1"
        >
          <div class="icon-container flex-grow-0">
            <v-icon large class="icon-center" color="white">{{ item.icon }}</v-icon>
          </div>
          <v-card-title class="text-h5 flex-grow-0">{{ item.title }}</v-card-title>
          <v-card-text class="flex-grow-1">{{ item.description }}</v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { usePermissions } from '@/composables/usePermissions';
import { useSkeletonLoading } from '@/composables/useSkeletonLoading';

const router = useRouter();
const { hasPermission, fetchPermissions, isLoading } = usePermissions();
const { isLoading: isSkelLoading, withLoading } = useSkeletonLoading(['permissions']);

// All available features with their required permissions
const allItems = ref([
  {
    title: 'Ranking',
    description: 'Ranken Sie Ihre Daten',
    route: '/Ranker',
    icon: 'mdi-chart-bar-stacked',
    elevation: 1,
    permission: 'feature:ranking:view'
  },
  {
    title: 'Verlaufsbewertung',
    description: 'Bewertung von KI generierten Mail-Verläufen (Säule 4)',
    route: '/HistoryGeneration',
    icon: 'mdi-timeline-text-outline',
    elevation: 1,
    permission: 'feature:mail_rating:view'
  },
  {
    title: 'Rating',
    description: 'Raten Sie Ihre Daten',
    route: '/Rater',
    icon: 'mdi-star-outline',
    elevation: 1,
    permission: 'feature:rating:view'
  },
  {
    title: 'Chatbot (Alpha)',
    description: "Chaten mit LLars",
    route: '/chat',
    icon: 'mdi-laptop-account',
    elevation: 1,
    permission: null  // No permission required - available to all
  },
  {
    title: 'Prompt Engineering (Beta)',
    description: "Kollaboratives entwerfen von Prompts",
    route: '/PromptEngineering',
    icon: 'mdi-text-search',
    elevation: 1,
    permission: 'feature:prompt_engineering:view'
  },
  {
    title: 'Gegenüberstellung',
    description: "Gegenüberstellung von zwei KI-Modellen und Bewertung, welches besser ist",
    route: '/comparison',
    icon: 'mdi-compare-horizontal',
    elevation: 1,
    permission: 'feature:comparison:view'
  },
  {
    title: 'LLM-as-Judge',
    description: "Automatisierte Bewertung und Vergleich von Prompt-Säulen mit KI",
    route: '/judge',
    icon: 'mdi-gavel',
    elevation: 1,
    permission: null  // Available to all authenticated users
  },
  {
    title: 'KAIMO',
    description: 'Fallvignetten durcharbeiten und als Researcher neue Fälle anlegen',
    route: '/kaimo',
    icon: 'mdi-shield-account',
    elevation: 1,
    permission: 'feature:kaimo:view'
  },
  {
    title: 'OnCoCo Analyse',
    description: "Klassifikation von Beratungsgesprächen auf Satzebene mit dem OnCoCo Modell (68 Kategorien)",
    route: '/oncoco',
    icon: 'mdi-chart-timeline-variant-shimmer',
    elevation: 1,
    permission: 'feature:comparison:view'  // Reuse comparison permission
  },
  {
    title: 'Admin Dashboard',
    description: 'Benutzer, Rollen und Berechtigungen verwalten',
    route: '/AdminPermissions',
    icon: 'mdi-shield-account',
    elevation: 1,
    permission: 'admin:permissions:manage'
  },
  {
    title: 'RAG Verwaltung',
    description: 'Dokumente für die RAG-Pipeline verwalten, hochladen und löschen',
    route: '/AdminRAG',
    icon: 'mdi-database-search',
    elevation: 1,
    permission: 'feature:rag:view'
  },
]);

// Filter items based on permissions
const items = computed(() => {
  return allItems.value.filter(item => {
    // If no permission required, show to everyone
    if (!item.permission) {
      return true;
    }
    // Check if user has the required permission
    return hasPermission(item.permission);
  });
});

function navigateTo(route) {
  router.push(route);
}

onMounted(async () => {
  // Fetch permissions on component mount
  await withLoading('permissions', async () => {
    await fetchPermissions();
  });

  equalizeCardSizes();
  window.addEventListener('resize', equalizeCardSizes);
});

function equalizeCardSizes() {
  const cardCols = document.querySelectorAll('.card-col');
  let maxWidth = 0;
  let maxHeight = 0;

  // Reset sizes and find the maximum natural width and height
  cardCols.forEach(col => {
    col.style.width = '';
    col.style.height = '';
    const width = col.offsetWidth;
    const height = col.offsetHeight;
    if (width > maxWidth) maxWidth = width;
    if (height > maxHeight) maxHeight = height;
  });

  // Set all cards to the maximum width and height
  cardCols.forEach(col => {
    col.style.width = `${maxWidth}px`;
    col.style.height = `${maxHeight}px`;
  });
}
</script>


<style scoped>
.home-container {
  padding: 16px;
  border-radius: 8px;
  max-width: 1200px;
  background-color: rgb(var(--v-theme-background));
}

.header {
  position: relative;
  z-index: 1;
  padding-top: 64px;
}

.equal-size-cards {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.card-col {
  display: flex;
  justify-content: center;
  padding: 10px;
}

.feature-card {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgb(var(--v-theme-primary));
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
  text-align: center;
  padding: 20px;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}

.feature-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
  background-color: rgba(var(--v-theme-secondary), 0.1);
}

.icon-container {
  margin-bottom: 16px;
}

.feature-card .v-card-title {
  color: rgb(var(--v-theme-on-primary));
  margin-top: 10px;
  font-family: Arial, sans-serif;
  font-weight: bold;
}

.feature-card .v-card-text {
  color: rgb(var(--v-theme-on-primary));
  flex-grow: 1;
  font-family: Arial, sans-serif;
  font-size: 0.9rem;
}

.disabled-card {
  opacity: 0.8;
  background-color: rgb(var(--v-theme-surface-variant));
}

.disabled-card:hover {
  transform: scale(1.01);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}

.disabled-card:hover .lock-overlay {
  opacity: 1;
}

.lock-icon {
  font-size: 48px;
  animation: lockBounce 1s ease-in-out infinite;
  color: rgb(var(--v-theme-grey-darken-3));
}

@keyframes lockBounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@media (max-width: 600px) {
  .header {
    padding-top: 80px;
  }

  .card-col {
    flex-basis: 100%;
  }
}

.header-title {
  color: rgb(var(--v-theme-on-background));
  font-family: Arial, sans-serif;
  font-weight: bold;
}

.subtitle-text {
  color: rgba(var(--v-theme-on-background), 0.7);
  font-family: 'Verdana', sans-serif;
  font-size: 1.1rem;
}

</style>
